/** Types + helpers for the salon-booking domain (mirrors the backend). */

export type Role = "client" | "saloon";
export type BookingStatus = "pending" | "confirmed" | "declined" | "cancelled";

export interface User {
  id: number;
  email: string;
  full_name: string;
  role: Role;
  phone: string | null;
}

export interface AuthResult {
  access_token: string;
  token_type: string;
  user: User;
  salon_id: number | null;
}

export interface Me {
  user: User;
  salon_id: number | null;
}

export interface Service {
  id: number;
  salon_id: number;
  name: string;
  description: string;
  duration_minutes: number;
  price_pennies: number;
}

export interface Salon {
  id: number;
  name: string;
  description: string;
  address: string;
  city: string;
  latitude: number;
  longitude: number;
  phone: string;
  photo_url: string | null;
  chairs: number;
}

export interface SalonDetail extends Salon {
  services: Service[];
}

export interface SlotsResponse {
  salon_id: number;
  service_id: number;
  date: string;
  slots: string[]; // ISO datetimes
}

export interface BookingDetail {
  id: number;
  client_id: number;
  salon_id: number;
  service_id: number;
  start_at: string;
  end_at: string;
  status: BookingStatus;
  look_style_id: string | null;
  suggested_start_at: string | null;
  service_name: string;
  salon_name: string;
  client_name: string;
  price_pennies: number;
}

export interface SalonStats {
  pending_requests: number;
  upcoming_confirmed: number;
  completed: number;
  revenue_pennies: number;
  unique_clients: number;
}

/** Format pennies as GBP, e.g. 4500 -> "£45". */
export function formatPrice(pennies: number): string {
  const pounds = pennies / 100;
  return Number.isInteger(pounds) ? `£${pounds}` : `£${pounds.toFixed(2)}`;
}

/** Great-circle distance in km between two lat/lng points (Haversine). */
export function haversineKm(
  a: { lat: number; lng: number },
  b: { lat: number; lng: number },
): number {
  const R = 6371;
  const dLat = ((b.lat - a.lat) * Math.PI) / 180;
  const dLng = ((b.lng - a.lng) * Math.PI) / 180;
  const lat1 = (a.lat * Math.PI) / 180;
  const lat2 = (b.lat * Math.PI) / 180;
  const h =
    Math.sin(dLat / 2) ** 2 +
    Math.sin(dLng / 2) ** 2 * Math.cos(lat1) * Math.cos(lat2);
  return 2 * R * Math.asin(Math.sqrt(h));
}

/** Status → display label + Tailwind colour classes. */
export const STATUS_BADGE: Record<BookingStatus, { label: string; cls: string }> = {
  pending: {
    label: "Pending",
    cls: "bg-amber-100 text-amber-800 dark:bg-amber-900/40 dark:text-amber-300",
  },
  confirmed: {
    label: "Confirmed",
    cls: "bg-emerald-100 text-emerald-800 dark:bg-emerald-900/40 dark:text-emerald-300",
  },
  declined: {
    label: "Declined",
    cls: "bg-red-100 text-red-800 dark:bg-red-900/40 dark:text-red-300",
  },
  cancelled: {
    label: "Cancelled",
    cls: "bg-zinc-200 text-zinc-600 dark:bg-zinc-800 dark:text-zinc-400",
  },
};
