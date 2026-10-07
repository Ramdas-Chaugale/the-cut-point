"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";
import { cancelBooking, getMyBookings } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import { type BookingDetail, formatPrice, STATUS_BADGE } from "@/lib/bookingTypes";

function fmt(iso: string): string {
  return new Date(iso).toLocaleString([], {
    weekday: "short",
    day: "numeric",
    month: "short",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export default function AppointmentsPage() {
  const { user, loading } = useAuth();
  const [bookings, setBookings] = useState<BookingDetail[] | null>(null);
  const [error, setError] = useState("");

  const load = useCallback(async () => {
    try {
      setBookings(await getMyBookings());
    } catch (e) {
      setError((e as Error).message);
    }
  }, []);

  useEffect(() => {
    if (user?.role === "client") void load();
  }, [user, load]);

  const onCancel = async (id: number) => {
    try {
      await cancelBooking(id);
      await load();
    } catch (e) {
      setError((e as Error).message);
    }
  };

  if (loading) {
    return <div className="mx-auto max-w-3xl px-6 py-16 text-sm text-ink-faint">Loading…</div>;
  }

  if (!user) {
    return (
      <div className="mx-auto max-w-3xl px-6 py-16">
        <p className="text-lg text-ink-soft">
          Log in to see what you have booked and what each salon has said.
        </p>
        <Link
          href="/login?next=/appointments"
          className="mt-3 inline-block px-4 py-2 rounded-lg bg-accent text-sm font-semibold text-accent-ink shadow-sm transition-colors hover:bg-accent-hover"
        >
          Log in
        </Link>
      </div>
    );
  }

  if (user.role !== "client") {
    return (
      <div className="mx-auto max-w-3xl px-6 py-16 text-sm text-ink-faint">
        This page is for client accounts. Visit your{" "}
        <Link href="/dashboard" className="text-accent hover:underline">
          salon dashboard
        </Link>{" "}
        instead.
      </div>
    );
  }

  return (
    <div className="mx-auto w-full max-w-3xl px-4 py-10 sm:px-6">
      <h1 className="text-3xl font-bold text-ink sm:text-4xl">
        My appointments
      </h1>
      <p className="mt-2 text-lg leading-relaxed text-ink-soft">
        Every request you have sent, and where each one stands.
      </p>

      {error && <p className="mt-3 text-sm text-negative">{error}</p>}

      {bookings === null ? (
        <p className="mt-6 text-sm text-ink-faint">Loading…</p>
      ) : bookings.length === 0 ? (
        <div className="mt-6 rounded-xl border border-dashed border-line-strong p-8 text-center">
          <p className="font-medium text-ink">Nothing booked yet</p>
          <p className="mt-1 text-sm text-ink-faint">
            Find a salon, pick a time that suits you, and it will show up here.
          </p>
          <Link
            href="/salons"
            className="mt-3 inline-block px-4 py-2 rounded-lg bg-accent text-sm font-semibold text-accent-ink shadow-sm transition-colors hover:bg-accent-hover"
          >
            Find a salon
          </Link>
        </div>
      ) : (
        <ul className="mt-6 space-y-3">
          {bookings.map((b) => {
            const badge = STATUS_BADGE[b.status];
            const cancellable = b.status === "pending" || b.status === "confirmed";
            return (
              <li
                key={b.id}
                className="flex flex-wrap items-center justify-between gap-3 rounded-xl border border-line px-4 py-3"
              >
                <div>
                  <div className="flex items-center gap-2">
                    <p className="font-medium text-ink">{b.service_name}</p>
                    <span className={`rounded-full px-2 py-0.5 text-xs font-medium ${badge.cls}`}>
                      {badge.label}
                    </span>
                  </div>
                  <p className="mt-0.5 text-sm text-ink-faint">
                    {b.salon_name} · {fmt(b.start_at)} · {formatPrice(b.price_pennies)}
                  </p>
                  {b.look_style_id && (
                    <p className="mt-0.5 text-xs text-ai">
                      Bringing a saved look
                    </p>
                  )}
                  {b.status === "declined" && b.suggested_start_at && (
                    <p className="mt-0.5 text-xs text-caution">
                      Salon suggested {fmt(b.suggested_start_at)} instead
                    </p>
                  )}
                </div>
                {cancellable && (
                  <button
                    type="button"
                    onClick={() => onCancel(b.id)}
                    className="rounded-lg border border-line-strong px-3 py-1.5 text-sm font-medium text-ink-soft hover:bg-surface-sunken"
                  >
                    Cancel
                  </button>
                )}
              </li>
            );
          })}
        </ul>
      )}
    </div>
  );
}
