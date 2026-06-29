/** Shared types mirroring the backend /api/face/analyze response. */

export type FaceShape =
  | "oval"
  | "round"
  | "square"
  | "oblong"
  | "heart"
  | "diamond"
  | "triangle";

export interface AnalyzeResponse {
  shape: FaceShape;
  confidence: number;
  description: string;
  scores: Record<FaceShape, number>;
  ratios: {
    length_to_width: number;
    forehead_to_cheek: number;
    jaw_to_cheek: number;
    forehead_to_jaw: number;
    jaw_angle_deg: number;
  };
  orientation: { yaw_ratio: number; is_frontal: boolean };
  quality: { face_size_ratio: number; warnings: string[] };
}

/** Human-friendly labels for the measured ratios. */
export const RATIO_LABELS: Record<keyof AnalyzeResponse["ratios"], string> = {
  length_to_width: "Face length ÷ width",
  forehead_to_cheek: "Forehead ÷ cheekbone",
  jaw_to_cheek: "Jaw ÷ cheekbone",
  forehead_to_jaw: "Forehead ÷ jaw",
  jaw_angle_deg: "Jaw angle (°)",
};
