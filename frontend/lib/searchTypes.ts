/** Types mirroring the backend /api/search, /api/assistant and /api/styles contracts. */

import type { FaceShape } from "./faceTypes";
import type { AngleAssets, HairType, Length, Maintenance, Presentation } from "./recommendTypes";

export interface SearchRequest {
  query: string;
  limit?: number;
}

/** What the backend understood the query to mean, shown back to the user. */
export interface ParsedQuery {
  presentation: Presentation | null;
  length: Length | null;
  hair_type: HairType | null;
  maintenance: Maintenance | null;
  face_shape: FaceShape | null;
  summary: string[];
  /** "llm" when a model parsed it, "keywords" when the built-in table did. */
  source: "llm" | "keywords";
}

export interface SearchHit {
  id: string;
  name: string;
  length: Length;
  maintenance: Maintenance;
  presentations: Presentation[];
  hair_types: HairType[];
  description: string;
  angle_assets: AngleAssets;
  try_on_overlay: string;
  score: number;
  /** Which constraints this style satisfied, in plain words. */
  reasons: string[];
}

export interface SearchResponse {
  query: string;
  parsed: ParsedQuery;
  count: number;
  results: SearchHit[];
}

export interface AssistantRequest {
  question: string;
  face_shape?: FaceShape;
}

/** A catalogue entry the answer was drawn from. */
export interface AssistantSource {
  id: string;
  name: string;
  description: string;
}

export interface AssistantResponse {
  answer: string;
  sources: AssistantSource[];
  source: "llm" | "fallback";
}
