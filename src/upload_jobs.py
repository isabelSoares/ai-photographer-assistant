from __future__ import annotations

import threading
import time
import uuid
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import StrEnum
from pathlib import Path
from typing import Callable

from .upload_service import (
    DEFAULT_MODEL_PATH,
    MAX_UPLOAD_BYTES,
    PhotoGuidanceResult,
    ReviewState,
    UploadValidationError,
    analyze_image,
    validate_upload,
)


MAX_QUEUE_LENGTH = 10
JOB_RETENTION_SECONDS = 600
POLL_INTERVAL_SECONDS = 0.5
CLEANUP_INTERVAL_SECONDS = 60.0


class JobState(StrEnum):
    ACCEPTED = "accepted"
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class QueueBusyError(Exception):
    """Raised when the review queue cannot accept another job."""


class JobNotFoundError(Exception):
    """Raised when a requested job ID does not exist."""


@dataclass
class AnalysisJob:
    """Represents one uploaded photo from acceptance through result."""

    job_id: str
    upload_name: str
    state: JobState
    queue_position: int | None = None
    result: PhotoGuidanceResult | None = None
    error_message: str | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    started_at: datetime | None = None
    completed_at: datetime | None = None
    temporary_path: Path | None = None
    _state_lock: threading.Lock = field(default_factory=threading.Lock, repr=False)

    def transition_to(self, new_state: JobState, **kwargs) -> None:
        """Move the job to a new state, enforcing immutable terminal states."""
        with self._state_lock:
            if self.state in (JobState.COMPLETED, JobState.FAILED):
                raise RuntimeError(f"Cannot transition from terminal state {self.state}")
            self.state = new_state
            for key, value in kwargs.items():
                setattr(self, key, value)

    def _status_message(self) -> str:
        if self.state == JobState.QUEUED and self.queue_position is not None:
            if self.queue_position == 1:
                return f"{self.upload_name} is next in line for review."
            return f"{self.upload_name} is number {self.queue_position} in line for review."
        if self.state == JobState.PROCESSING:
            return f"Reviewing {self.upload_name}..."
        if self.state == JobState.COMPLETED:
            return f"Review complete for {self.upload_name}."
        if self.state == JobState.FAILED:
            return f"Could not review {self.upload_name}."
        return f"{self.upload_name} has been accepted."

    def to_status_payload(self) -> dict:
        """Return a JSON-serializable status view of the job."""
        payload = {
            "job_id": self.job_id,
            "upload_name": self.upload_name,
            "state": self.state.value,
            "queue_position": self.queue_position,
            "message": self._status_message(),
            "result": None,
            "error_message": None,
        }
        if self.state == JobState.COMPLETED and self.result is not None:
            payload["result"] = {
                "state": self.result.state.value,
                "upload_name": self.result.upload_name,
                "summary": self.result.summary,
                "subjects": self.result.subjects or [],
                "scenes": self.result.scenes or [],
                "tips": self.result.tips or [],
                "uncertain": self.result.uncertain,
                "notice": self.result.notice,
            }
        if self.state == JobState.FAILED and self.error_message is not None:
            payload["error_message"] = self.error_message
        return payload


class ReviewQueue:
    """FIFO queue of analysis jobs waiting for the single worker."""

    def __init__(self, max_length: int = MAX_QUEUE_LENGTH) -> None:
        self.max_length = max_length
        self._jobs: deque[AnalysisJob] = deque()
        self._condition = threading.Condition()

    def __len__(self) -> int:
        with self._condition:
            return len(self._jobs)

    def put(self, job: AnalysisJob) -> None:
        """Add a job to the queue. Raises QueueBusyError if full."""
        with self._condition:
            if len(self._jobs) >= self.max_length:
                raise QueueBusyError("The server is busy. Please try again in a moment.")
            self._jobs.append(job)
            self._condition.notify()

    def get(self) -> AnalysisJob:
        """Block until a job is available and return it."""
        with self._condition:
            while not self._jobs:
                self._condition.wait()
            return self._jobs.popleft()

    def positions(self) -> dict[str, int]:
        """Return a mapping of job_id to current queue position (1-based)."""
        with self._condition:
            return {job.job_id: index + 1 for index, job in enumerate(self._jobs)}


class JobStore:
    """In-memory registry of analysis jobs with bounded retention."""

    def __init__(self, retention_seconds: float = JOB_RETENTION_SECONDS) -> None:
        self.retention_seconds = retention_seconds
        self._jobs: dict[str, AnalysisJob] = {}
        self._lock = threading.Lock()

    def register(self, job: AnalysisJob) -> None:
        with self._lock:
            self._jobs[job.job_id] = job

    def get(self, job_id: str) -> AnalysisJob:
        with self._lock:
            if job_id not in self._jobs:
                raise JobNotFoundError(f"No review found for {job_id}.")
            return self._jobs[job_id]

    def remove(self, job_id: str) -> None:
        with self._lock:
            job = self._jobs.pop(job_id, None)
        if job is not None and job.temporary_path is not None:
            job.temporary_path.unlink(missing_ok=True)

    def cleanup_expired(self) -> None:
        """Remove terminal jobs whose retention window has passed."""
        cutoff = datetime.now(timezone.utc) - timedelta(seconds=self.retention_seconds)
        expired_ids: list[str] = []
        with self._lock:
            for job_id, job in self._jobs.items():
                if job.state in (JobState.COMPLETED, JobState.FAILED):
                    completed_at = job.completed_at
                    if completed_at is not None and completed_at < cutoff:
                        expired_ids.append(job_id)
        for job_id in expired_ids:
            self.remove(job_id)


def _safe_failed_result(upload_name: str) -> PhotoGuidanceResult:
    return PhotoGuidanceResult(
        upload_name=upload_name,
        state=ReviewState.ERROR,
        error_message="The photo could not be analyzed. Try again or choose another photo.",
    )


class AnalysisWorker:
    """Single background worker that processes one analysis job at a time."""

    def __init__(
        self,
        queue: ReviewQueue,
        store: JobStore,
        analyzer: Callable[[Path], PhotoGuidanceResult] | None = None,
    ) -> None:
        self.queue = queue
        self.store = store
        self.analyzer = analyzer or analyze_image
        self._thread: threading.Thread | None = None
        self._shutdown = threading.Event()

    def start(self) -> None:
        if self._thread is not None and self._thread.is_alive():
            return
        self._shutdown.clear()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self, timeout: float | None = None) -> None:
        self._shutdown.set()
        if self._thread is not None and self._thread.is_alive():
            self._thread.join(timeout=timeout)

    def _run(self) -> None:
        while not self._shutdown.is_set():
            try:
                job = self.queue.get()
            except Exception:
                continue
            if self._shutdown.is_set():
                break
            self._process_job(job)

    def _process_job(self, job: AnalysisJob) -> None:
        try:
            job.transition_to(JobState.PROCESSING, started_at=datetime.now(timezone.utc))
            result = self.analyzer(job.temporary_path)
            result.upload_name = job.upload_name
            result.state = ReviewState.COMPLETED
            job.transition_to(
                JobState.COMPLETED,
                result=result,
                completed_at=datetime.now(timezone.utc),
            )
        except Exception:
            job.transition_to(
                JobState.FAILED,
                result=_safe_failed_result(job.upload_name),
                error_message="The photo could not be analyzed. Try again or choose another photo.",
                completed_at=datetime.now(timezone.utc),
            )
        finally:
            if job.temporary_path is not None:
                job.temporary_path.unlink(missing_ok=True)


class CleanupWorker:
    """Periodic cleanup of expired terminal jobs."""

    def __init__(
        self,
        store: JobStore,
        interval_seconds: float = CLEANUP_INTERVAL_SECONDS,
    ) -> None:
        self.store = store
        self.interval_seconds = interval_seconds
        self._thread: threading.Thread | None = None
        self._shutdown = threading.Event()

    def start(self) -> None:
        if self._thread is not None and self._thread.is_alive():
            return
        self._shutdown.clear()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self, timeout: float | None = None) -> None:
        self._shutdown.set()
        if self._thread is not None and self._thread.is_alive():
            self._thread.join(timeout=timeout)

    def _run(self) -> None:
        while not self._shutdown.wait(self.interval_seconds):
            self.store.cleanup_expired()


def create_job_from_upload(
    filename: str,
    content: bytes,
    store: JobStore,
    queue: ReviewQueue,
) -> AnalysisJob:
    """Validate an upload, persist a temporary file, and enqueue a job."""
    upload = validate_upload(filename, content)
    from .upload_service import _write_normalized_image

    temporary_path = _write_normalized_image(content)
    job = AnalysisJob(
        job_id=uuid.uuid4().hex,
        upload_name=upload.original_name,
        state=JobState.ACCEPTED,
        temporary_path=temporary_path,
    )
    store.register(job)
    try:
        queue.put(job)
        job.transition_to(JobState.QUEUED)
    except QueueBusyError:
        store.remove(job.job_id)
        raise
    return job


def get_job_status(job_id: str, store: JobStore, queue: ReviewQueue) -> dict:
    """Return the current status payload for a job, including queue position."""
    job = store.get(job_id)
    if job.state == JobState.QUEUED:
        positions = queue.positions()
        job.queue_position = positions.get(job.job_id)
    else:
        job.queue_position = None
    return job.to_status_payload()


def estimate_wait_seconds(queue_position: int) -> int:
    """Return a rough wait estimate based on queue position."""
    return queue_position * 60
