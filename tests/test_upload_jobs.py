from __future__ import annotations

import json
import time
import unittest
from pathlib import Path
from unittest.mock import MagicMock

from src.upload_jobs import (
    AnalysisJob,
    AnalysisWorker,
    CleanupWorker,
    JobState,
    JobStore,
    QueueBusyError,
    ReviewQueue,
    create_job_from_upload,
    get_job_status,
)
from src.upload_service import PhotoGuidanceResult, ReviewState


class AnalysisJobFixturesTest(unittest.TestCase):
    """T003: Fixtures for queued, processing, completed, and failed jobs."""

    def test_queued_job_fixture(self) -> None:
        job = AnalysisJob(job_id="queued-1", upload_name="queued.jpg", state=JobState.QUEUED, queue_position=1)
        self.assertEqual(job.state, JobState.QUEUED)
        self.assertEqual(job.queue_position, 1)

    def test_processing_job_fixture(self) -> None:
        job = AnalysisJob(job_id="processing-1", upload_name="processing.jpg", state=JobState.PROCESSING)
        self.assertEqual(job.state, JobState.PROCESSING)

    def test_completed_job_fixture(self) -> None:
        result = PhotoGuidanceResult(upload_name="completed.jpg", state=ReviewState.COMPLETED, summary="A scene")
        job = AnalysisJob(
            job_id="completed-1",
            upload_name="completed.jpg",
            state=JobState.COMPLETED,
            result=result,
        )
        payload = job.to_status_payload()
        self.assertEqual(payload["state"], "completed")
        self.assertEqual(payload["result"]["summary"], "A scene")

    def test_failed_job_fixture(self) -> None:
        job = AnalysisJob(
            job_id="failed-1",
            upload_name="failed.jpg",
            state=JobState.FAILED,
            error_message="Could not analyze.",
        )
        payload = job.to_status_payload()
        self.assertEqual(payload["state"], "failed")
        self.assertEqual(payload["error_message"], "Could not analyze.")


class ReviewQueueTest(unittest.TestCase):
    """T017/T018/T019: Queue ordering, single analysis, and overflow."""

    def test_fifo_ordering(self) -> None:
        q = ReviewQueue(max_length=5)
        job1 = AnalysisJob(job_id="a", upload_name="1.jpg", state=JobState.QUEUED)
        job2 = AnalysisJob(job_id="b", upload_name="2.jpg", state=JobState.QUEUED)
        q.put(job1)
        q.put(job2)
        self.assertEqual(q.get().job_id, "a")
        self.assertEqual(q.get().job_id, "b")

    def test_queue_positions(self) -> None:
        q = ReviewQueue(max_length=5)
        job1 = AnalysisJob(job_id="a", upload_name="1.jpg", state=JobState.QUEUED)
        job2 = AnalysisJob(job_id="b", upload_name="2.jpg", state=JobState.QUEUED)
        q.put(job1)
        q.put(job2)
        positions = q.positions()
        self.assertEqual(positions["a"], 1)
        self.assertEqual(positions["b"], 2)

    def test_queue_overflow(self) -> None:
        q = ReviewQueue(max_length=1)
        q.put(AnalysisJob(job_id="a", upload_name="1.jpg", state=JobState.QUEUED))
        with self.assertRaises(QueueBusyError):
            q.put(AnalysisJob(job_id="b", upload_name="2.jpg", state=JobState.QUEUED))


class AnalysisWorkerTest(unittest.TestCase):
    """T004/T005/T006/T007/T008/T024/T027/T030: Worker behavior and cleanup."""

    def _make_worker(self, analyzer=None):
        queue = ReviewQueue(max_length=10)
        store = JobStore(retention_seconds=60)
        worker = AnalysisWorker(queue, store, analyzer=analyzer)
        worker.start()
        return queue, store, worker

    def _small_valid_jpeg_bytes(self) -> bytes:
        # Minimal valid JPEG header for validation
        return bytes.fromhex(
            "ffd8ffe000104a46494600010100000100010000ffdb00430003020203020203030303040303040508050504"
            "04050a070706080c0a0c0c0b0a0b0b0d0e12100d0e110e0b0b1016101113141515150c0f1718161418121415"
            "14ffdd0004000affc4001f0000010501010101010100000000000000000102030405060708090a0bffc400b5"
            "100002010303020403050504040000017d01020300041105122131410613516107227114328191a1082342"
            "b1c11552d1f0a2433472b11080914253f0c162b3a3443544639525e176728293a7b7c59536b7588999aa2a3"
            "a4a58697a5a6a7a7a8acadbabbbcccdceddedeeeff0f1f2f3f4f5f6f7f8f9fbffc4001f0100030101010101"
            "010101010000000000000102030405060708090a0bffc400b5110002010204040304070504040001027700"
            "0102031104052131061241510761711322328108144291a1b1c10923d1e0153362f0247282d2a344353738"
            "3c2ffda000c03010002110311003f00"
        )

    def test_worker_processes_one_job_at_a_time(self) -> None:
        processed = []

        def slow_analyzer(path: Path) -> PhotoGuidanceResult:
            time.sleep(0.1)
            processed.append(path)
            return PhotoGuidanceResult(upload_name="test.jpg", state=ReviewState.COMPLETED, summary="Done")

        queue, store, worker = self._make_worker(analyzer=slow_analyzer)
        try:
            job1 = AnalysisJob(job_id="j1", upload_name="1.jpg", state=JobState.QUEUED, temporary_path=Path("/tmp/fake1.jpg"))
            job2 = AnalysisJob(job_id="j2", upload_name="2.jpg", state=JobState.QUEUED, temporary_path=Path("/tmp/fake2.jpg"))
            store.register(job1)
            store.register(job2)
            queue.put(job1)
            queue.put(job2)
            time.sleep(0.05)
            self.assertEqual(sum(1 for j in [job1, job2] if j.state == JobState.PROCESSING), 1)
            time.sleep(0.3)
            self.assertEqual(len(processed), 2)
        finally:
            worker.stop(timeout=0.5)

    def test_worker_transitions_to_completed(self) -> None:
        def analyzer(path: Path) -> PhotoGuidanceResult:
            return PhotoGuidanceResult(upload_name="test.jpg", state=ReviewState.COMPLETED, summary="A scene")

        queue, store, worker = self._make_worker(analyzer=analyzer)
        try:
            job = AnalysisJob(job_id="j1", upload_name="1.jpg", state=JobState.QUEUED, temporary_path=Path("/tmp/fake.jpg"))
            store.register(job)
            queue.put(job)
            time.sleep(0.1)
            self.assertEqual(job.state, JobState.COMPLETED)
            self.assertIsNotNone(job.result)
            self.assertEqual(job.result.summary, "A scene")
        finally:
            worker.stop(timeout=0.5)

    def test_worker_transitions_to_failed_on_exception(self) -> None:
        def analyzer(path: Path) -> PhotoGuidanceResult:
            raise RuntimeError("boom")

        queue, store, worker = self._make_worker(analyzer=analyzer)
        try:
            job = AnalysisJob(job_id="j1", upload_name="1.jpg", state=JobState.QUEUED, temporary_path=Path("/tmp/fake.jpg"))
            store.register(job)
            queue.put(job)
            time.sleep(0.1)
            self.assertEqual(job.state, JobState.FAILED)
            self.assertIsNotNone(job.error_message)
            self.assertIn("could not be analyzed", job.error_message.lower())
        finally:
            worker.stop(timeout=0.5)

    def test_terminal_state_is_immutable(self) -> None:
        job = AnalysisJob(job_id="j1", upload_name="1.jpg", state=JobState.COMPLETED)
        with self.assertRaises(RuntimeError):
            job.transition_to(JobState.FAILED)

    def test_cleanup_removes_terminal_jobs(self) -> None:
        store = JobStore(retention_seconds=0)
        temp = Path("/tmp/upload_jobs_test_cleanup.txt")
        temp.write_text("x")
        job = AnalysisJob(
            job_id="j1",
            upload_name="1.jpg",
            state=JobState.COMPLETED,
            completed_at=datetime_for_test(),
            temporary_path=temp,
        )
        store.register(job)
        store.cleanup_expired()
        self.assertIsNone(store._jobs.get("j1"))
        self.assertFalse(temp.exists())

    def test_create_job_from_upload_rejects_invalid_file(self) -> None:
        store = JobStore()
        queue = ReviewQueue(max_length=10)
        with self.assertRaises(Exception):
            create_job_from_upload("bad.txt", b"not an image", store, queue)
        self.assertEqual(len(store._jobs), 0)
        self.assertEqual(len(queue), 0)

    def test_status_payload_never_exposes_temporary_path(self) -> None:
        temp = Path("/tmp/upload_jobs_test_not_exposed.txt")
        temp.write_text("x")
        result = PhotoGuidanceResult(upload_name="photo.jpg", state=ReviewState.COMPLETED, summary="A scene")
        job = AnalysisJob(
            job_id="j1",
            upload_name="photo.jpg",
            state=JobState.COMPLETED,
            result=result,
            temporary_path=temp,
        )
        payload = job.to_status_payload()
        self.assertNotIn("temporary_path", payload)
        self.assertNotIn("/tmp", json.dumps(payload))
        temp.unlink(missing_ok=True)


def datetime_for_test():
    from datetime import datetime, timedelta, timezone
    return datetime.now(timezone.utc) - timedelta(seconds=1)


if __name__ == "__main__":
    unittest.main()
