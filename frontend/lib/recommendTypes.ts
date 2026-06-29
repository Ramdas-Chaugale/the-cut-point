/** Types + labels mirroring the backend /api/recommend contract. */

import type { FaceShape } from "./faceTypes";

export type Presentation = "masculine" | "feminine" | "unisex";
export type Length = "short" | "medium" | "long";
export type HairType = "straight" | "wavy" | "curly" | "coily";
export type Maintenance = "low" | "medium" | "high";
export type Angle = "front" | "left" | "right" | "back";

export interface RecommendRequest {
  face_shape: FaceShape;
  presentation?: Presentation;
  desired_length?: Length;
  hair_type?: HairType;
  maintenance?: Maintenance;
  limit?: number;
}

export interface AngleAssets {
  front: string;
  left: string;
  right: string;
  back: string;
}

export interface StyleRecommendation {
  id: string;
  name: string;
  length: Length;
  maintenance: Maintenance;
  presentations: Presentation[];
  hair_types: HairType[];
  rationale_tags: string[];
  description: string;
  angle_assets: AngleAssets;
  match_score: number;
  matched_on: string[];
  explanation: string;
}

export interface RecommendResponse {
  face_shape: FaceShape;
  count: number;
  recommendations: StyleRecommendation[];
}

export interface ExplainRequest {
  style_id: string;
  face_shape: FaceShape;
  presentation?: Presentation;
  desired_length?: Length;
  hair_type?: HairType;
  maintenance?: Maintenance;
}

export interface ExplainResponse {
  style_id: string;
  explanation: string;
  source: "llm" | "fallback";
  cached: boolean;
}

/** Short, human-friendly chip labels for rationale tags. */
export const RATIONALE_LABELS: Record<string, string> = {
  "adds-height": "Adds height",
  elongates: "Elongates",
  "softens-angles": "Softens angles",
  "adds-width": "Adds width",
  "balances-forehead": "Balances forehead",
  "balances-jaw": "Balances jaw",
  "frames-face": "Frames face",
  "highlights-bone-structure": "Bone structure",
  "adds-texture": "Adds texture",
  "adds-volume": "Adds volume",
  "low-upkeep": "Low upkeep",
  "shortens-face": "Shortens face",
};

export const ANGLE_LABELS: Record<Angle, string> = {
  front: "Front",
  left: "Left",
  right: "Right",
  back: "Back",
};
