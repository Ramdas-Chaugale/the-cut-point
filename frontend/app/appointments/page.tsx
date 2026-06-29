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
    return <div className="mx-auto max-w-3xl px-6 py-16 text-sm text-zinc-400">Loading…</div>;
  }

  if (!user) {
    return (
      <div className="mx-auto max-w-3xl px-6 py-16">
        <p className="text-sm text-zinc-600 dark:text-zinc-400">Log in to see your appointments.</p>
        <Link
          href="/login?next=/appointments"
          className="mt-3 inline-block rounded-md bg-zinc-900 px-4 py-2 text-sm font-medium text-white dark:bg-zinc-100 dark:text-zinc-900"
        >
          Log in
        </Link>
      </div>
    );
  }

  if (user.role !== "client") {
    return (
      <div className="mx-auto max-w-3xl px-6 py-16 text-sm text-zinc-500">
        This page is for client accounts. Visit your{" "}
        <Link href="/dashboard" className="text-emerald-600 hover:underline">
          salon dashboard
        </Link>{" "}
        instead.
      </div>
    );
  }

  return (
    <div className="mx-auto w-full max-w-3xl px-4 py-10 sm:px-6">
      <h1 className="text-2xl font-semibold tracking-tight text-zinc-900 dark:text-zinc-50">
        My appointments
      </h1>

      {error && <p className="mt-3 text-sm text-red-600 dark:text-red-400">{error}</p>}

      {bookings === null ? (
        <p className="mt-6 text-sm text-zinc-400">Loading…</p>
      ) : bookings.length === 0 ? (
        <div className="mt-6 rounded-xl border border-dashed border-zinc-300 p-8 text-center dark:border-zinc-700">
          <p className="text-sm text-zinc-500">No appointments yet.</p>
          <Link
            href="/salons"
            className="mt-3 inline-block rounded-md bg-zinc-900 px-4 py-2 text-sm font-medium text-white dark:bg-zinc-100 dark:text-zinc-900"
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
                className="flex flex-wrap items-center justify-between gap-3 rounded-xl border border-zinc-200 px-4 py-3 dark:border-zinc-800"
              >
                <div>
                  <div className="flex items-center gap-2">
                    <p className="font-medium text-zinc-900 dark:text-zinc-100">{b.service_name}</p>
                    <span className={`rounded-full px-2 py-0.5 text-xs font-medium ${badge.cls}`}>
                      {badge.label}
                    </span>
                  </div>
                  <p className="mt-0.5 text-sm text-zinc-500">
                    {b.salon_name} · {fmt(b.start_at)} · {formatPrice(b.price_pennies)}
                  </p>
                  {b.look_style_id && (
                    <p className="mt-0.5 text-xs text-violet-600 dark:text-violet-400">
                      Bringing a saved look
                    </p>
                  )}
                  {b.status === "declined" && b.suggested_start_at && (
                    <p className="mt-0.5 text-xs text-amber-600 dark:text-amber-400">
                      Salon suggested {fmt(b.suggested_start_at)} instead
                    </p>
                  )}
                </div>
                {cancellable && (
                  <button
                    type="button"
                    onClick={() => onCancel(b.id)}
                    className="rounded-md border border-zinc-300 px-3 py-1.5 text-sm font-medium text-zinc-700 hover:bg-zinc-100 dark:border-zinc-700 dark:text-zinc-300 dark:hover:bg-zinc-800"
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
