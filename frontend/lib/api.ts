/**
 * Thin client for the CutPoint FastAPI backend.
 * Base URL comes from NEXT_PUBLIC_API_BASE_URL (see .env.local / .env.example).
 */
import type { AnalyzeResponse } from "./faceTypes";
import type { RecommendRequest, RecommendResponse } from "./recommendTypes";

export const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

export interface HealthResponse {
  status: string;
  service: string;
  version: string;
  llm_enabled: boolean;
}

export class ApiError extends Error {
  constructor(
    message: string,
    readonly status?: number,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

/** GET <base>/<path> and parse JSON, throwing ApiError on failure. */
export async function apiGet<T>(path: string): Promise<T> {
  let res: Response;
  try {
    res = await fetch(`${API_BASE_URL}${path}`, {
      headers: { Accept: "application/json" },
      cache: "no-store",
    });
  } catch (err) {
    throw new ApiError(
      `Network error reaching API: ${(err as Error).message}`,
    );
  }
  if (!res.ok) {
    throw new ApiError(`API responded ${res.status}`, res.status);
  }
  return (await res.json()) as T;
}

/** Fetch backend health / capability flags. */
export function getHealth(): Promise<HealthResponse> {
  return apiGet<HealthResponse>("/health");
}

/** POST <base>/<path> with a JSON body and parse the JSON response. */
export async function apiPost<T>(path: string, body: unknown): Promise<T> {
  let res: Response;
  try {
    res = await fetch(`${API_BASE_URL}${path}`, {
      method: "POST",
      headers: { "Content-Type": "application/json", Accept: "application/json" },
      body: JSON.stringify(body),
      cache: "no-store",
    });
  } catch (err) {
    throw new ApiError(`Network error reaching API: ${(err as Error).message}`);
  }
  if (!res.ok) {
    let detail = `API responded ${res.status}`;
    try {
      const data = await res.json();
      if (data?.detail) detail = typeof data.detail === "string" ? data.detail : detail;
    } catch {
      /* non-JSON error body */
    }
    throw new ApiError(detail, res.status);
  }
  return (await res.json()) as T;
}

/** Send MediaPipe landmarks to the backend for face-shape classification. */
export function analyzeFace(
  landmarks: number[][],
  imageWidth: number,
  imageHeight: number,
): Promise<AnalyzeResponse> {
  return apiPost<AnalyzeResponse>("/api/face/analyze", {
    landmarks,
    image_width: imageWidth,
    image_height: imageHeight,
  });
}

/** Fetch ranked hairstyle recommendations for a face shape + preferences. */
export function recommend(req: RecommendRequest): Promise<RecommendResponse> {
  return apiPost<RecommendResponse>("/api/recommend", req);
}
