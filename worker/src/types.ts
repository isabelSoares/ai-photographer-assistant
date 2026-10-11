export interface DetectedObject {
  label: string;
  score: number;
  box: {
    xmin: number;
    ymin: number;
    xmax: number;
    ymax: number;
  };
}

export interface SceneLabel {
  label: string;
  score: number;
}

export interface GuidanceTip {
  category: string;
  text: string;
  reason?: string;
}

export interface PhotoGuidanceResult {
  summary: string;
  subjects: DetectedObject[];
  scenes: SceneLabel[];
  tips: GuidanceTip[];
  uncertain: boolean;
  notice: string | null;
  error_message: string | null;
}

export interface PhotoUploadRequest {
  image: string;
  width: number;
  height: number;
  filename: string;
}
