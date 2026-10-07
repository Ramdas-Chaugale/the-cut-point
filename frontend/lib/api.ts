/**
 * Thin client for the CutPoint FastAPI backend.
 * Base URL comes from NEXT_PUBLIC_API_BASE_URL (see .env.local / .env.example).
 */
import type { AnalyzeResponse } from "./faceTypes";
import type {
  AuthResult,
  BookingDetail,
  Me,
  Salon,
  SalonDetail,
  SalonStats,
  SlotsResponse,
} from "./bookingTypes";
import type {
  ExplainRequest,
  ExplainResponse,
  RecommendRequest,
  RecommendResponse,
} from "./recommendTypes";
import type {
  AssistantRequest,
  AssistantResponse,
  SearchHit,
  SearchRequest,
  SearchResponse,
} from "./searchTypes";

export const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

// Bearer token set by the auth provider; attached to every request when present.
let _authToken: string | null = null;
export function setAuthToken(token: string | null): void {
  _authToken = token;
}

function authHeaders(): Record<string, string> {
  return _authToken ? { Authorization: `Bearer ${_authToken}` } : {};
}

export interface HealthResponse {
  status: string;
  service: string;
  version: string;
  llm_enabled: boolean;
  ai_tryon_enabled?: boolean;
  email_enabled?: boolean;
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

async function parseError(res: Response): Promise<never> {
  let detail = `API responded ${res.status}`;
  try {
    const data = await res.json();
    if (data?.detail) detail = typeof data.detail === "string" ? data.detail : detail;
  } catch {
    /* non-JSON error body */
  }
  throw new ApiError(detail, res.status);
}

/** GET <base>/<path> and parse JSON, throwing ApiError on failure. */
export async function apiGet<T>(path: string): Promise<T> {
  let res: Response;
  try {
    res = await fetch(`${API_BASE_URL}${path}`, {
      headers: { Accept: "application/json", ...authHeaders() },
      cache: "no-store",
    });
  } catch (err) {
    throw new ApiError(`Network error reaching API: ${(err as Error).message}`);
  }
  if (!res.ok) return parseError(res);
  return (await res.json()) as T;
}

/** Fetch backend health / capability flags. */
export function getHealth(): Promise<HealthResponse> {
  return apiGet<HealthResponse>("/health");
}

/** POST <base>/<path> with an optional JSON body and parse the JSON response. */
export async function apiPost<T>(path: string, body?: unknown): Promise<T> {
  let res: Response;
  try {
    res = await fetch(`${API_BASE_URL}${path}`, {
      method: "POST",
      headers: { "Content-Type": "application/json", Accept: "application/json", ...authHeaders() },
      body: body === undefined ? undefined : JSON.stringify(body),
      cache: "no-store",
    });
  } catch (err) {
    throw new ApiError(`Network error reaching API: ${(err as Error).message}`);
  }
  if (!res.ok) return parseError(res);
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

/** Request an LLM-enriched explanation for a single style. */
export function explainStyle(req: ExplainRequest): Promise<ExplainResponse> {
  return apiPost<ExplainResponse>("/api/explain", req);
}

/** Rank the catalogue against a free-text description of what someone wants. */
export function searchStyles(req: SearchRequest): Promise<SearchResponse> {
  return apiPost<SearchResponse>("/api/search", req);
}

/** Ask a styling question; the answer is grounded in the catalogue. */
export function askStylist(req: AssistantRequest): Promise<AssistantResponse> {
  return apiPost<AssistantResponse>("/api/assistant", req);
}

/** The whole catalogue, for browsing without running a face analysis first. */
export function listStyles(): Promise<SearchHit[]> {
  return apiGet<SearchHit[]>("/api/styles");
}

/**
 * Generate a photorealistic try-on of the user wearing a style.
 *
 * Passing a mask selects the free inpainting provider, which paints hair into
 * the masked region only and therefore cannot alter the face. Without one the
 * request falls through to whole-image editing.
 */
export function generateTryOn(
  imageDataUrl: string,
  styleId: string,
  maskDataUrl?: string | null,
): Promise<{ image_url: string }> {
  return apiPost<{ image_url: string }>("/api/tryon/generate", {
    image_data_url: imageDataUrl,
    style_id: styleId,
    mask_data_url: maskDataUrl ?? null,
  });
}

// --- Auth ----------------------------------------------------------------

export function login(email: string, password: string): Promise<AuthResult> {
  return apiPost<AuthResult>("/api/auth/login", { email, password });
}

export function registerClient(body: {
  email: string;
  password: string;
  full_name: string;
  phone?: string;
}): Promise<AuthResult> {
  return apiPost<AuthResult>("/api/auth/register/client", body);
}

export function registerSaloon(body: unknown): Promise<AuthResult> {
  return apiPost<AuthResult>("/api/auth/register/saloon", body);
}

export function getMe(): Promise<Me> {
  return apiGet<Me>("/api/auth/me");
}

// --- Salons & availability (public) --------------------------------------

export function listSalons(city?: string): Promise<Salon[]> {
  return apiGet<Salon[]>(`/api/salons${city ? `?city=${encodeURIComponent(city)}` : ""}`);
}

export function getSalon(salonId: number): Promise<SalonDetail> {
  return apiGet<SalonDetail>(`/api/salons/${salonId}`);
}

export function getAvailability(
  salonId: number,
  serviceId: number,
  date: string,
): Promise<SlotsResponse> {
  return apiGet<SlotsResponse>(
    `/api/salons/${salonId}/availability?service_id=${serviceId}&date=${date}`,
  );
}

// --- Client bookings -----------------------------------------------------

export function requestBooking(body: {
  salon_id: number;
  service_id: number;
  start_at: string;
  look_style_id?: string | null;
}): Promise<BookingDetail> {
  return apiPost<BookingDetail>("/api/bookings", body);
}

export function getMyBookings(): Promise<BookingDetail[]> {
  return apiGet<BookingDetail[]>("/api/bookings/me");
}

export function cancelBooking(bookingId: number): Promise<BookingDetail> {
  return apiPost<BookingDetail>(`/api/bookings/${bookingId}/cancel`);
}

// --- Saloon (owner) — used by the Phase 9 dashboard ----------------------

export function getSalonBookings(status?: string): Promise<BookingDetail[]> {
  return apiGet<BookingDetail[]>(
    `/api/salon/bookings${status ? `?status=${status}` : ""}`,
  );
}

export function getSalonStats(): Promise<SalonStats> {
  return apiGet<SalonStats>("/api/salon/stats");
}

export function acceptBooking(bookingId: number): Promise<BookingDetail> {
  return apiPost<BookingDetail>(`/api/bookings/${bookingId}/accept`);
}

export function declineBooking(
  bookingId: number,
  suggestedStartAt?: string | null,
): Promise<BookingDetail> {
  return apiPost<BookingDetail>(`/api/bookings/${bookingId}/decline`, {
    suggested_start_at: suggestedStartAt ?? null,
  });
}
