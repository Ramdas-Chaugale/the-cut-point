"use client";

import { useState } from "react";
import { type BookingDetail, formatPrice } from "@/lib/bookingTypes";

function fmt(iso: string): string {
  return new Date(iso).toLocaleString([], {
    weekday: "short",
    day: "numeric",
    month: "short",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export function SalonRequestCard({
  booking,
  onAccept,
  onDecline,
}: {
  booking: BookingDetail;
  onAccept: (id: number) => Promise<void>;
  onDecline: (id: number, suggested: string | null) => Promise<void>;
}) {
  const [declining, setDeclining] = useState(false);
  const [suggested, setSuggested] = useState("");
  const [busy, setBusy] = useState(false);

  const run = async (fn: () => Promise<void>) => {
    setBusy(true);
    try {
      await fn();
    } finally {
      setBusy(false);
    }
  };

  return (
    <li className="rounded-xl border border-zinc-200 p-4 dark:border-zinc-800">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <p className="font-medium text-zinc-900 dark:text-zinc-100">
            {booking.service_name}{" "}
            <span className="font-normal text-zinc-500">· {formatPrice(booking.price_pennies)}</span>
          </p>
          <p className="mt-0.5 text-sm text-zinc-500">
            {booking.client_name} · {fmt(booking.start_at)}
          </p>
          {booking.look_style_id && (
            <p className="mt-0.5 text-xs text-violet-600 dark:text-violet-400">
              Client is bringing a saved look
            </p>
          )}
        </div>
        {!declining && (
          <div className="flex gap-2">
            <button
              type="button"
              disabled={busy}
              onClick={() => run(() => onAccept(booking.id))}
              className="rounded-md bg-emerald-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-emerald-500 disabled:opacity-60"
            >
              Accept
            </button>
            <button
              type="button"
              disabled={busy}
              onClick={() => setDeclining(true)}
              className="rounded-md border border-zinc-300 px-3 py-1.5 text-sm font-medium text-zinc-700 hover:bg-zinc-100 disabled:opacity-60 dark:border-zinc-700 dark:text-zinc-300 dark:hover:bg-zinc-800"
            >
              Decline
            </button>
          </div>
        )}
      </div>

      {declining && (
        <div className="mt-3 rounded-md bg-zinc-50 p-3 dark:bg-zinc-800/50">
          <label className="block text-sm text-zinc-600 dark:text-zinc-400">
            Suggest an alternative time (optional)
            <input
              type="datetime-local"
              value={suggested}
              onChange={(e) => setSuggested(e.target.value)}
              className="mt-1 w-full rounded-md border border-zinc-300 bg-white px-2 py-1.5 text-sm dark:border-zinc-700 dark:bg-zinc-900"
            />
          </label>
          <div className="mt-2 flex gap-2">
            <button
              type="button"
              disabled={busy}
              onClick={() => run(() => onDecline(booking.id, suggested || null))}
              className="rounded-md bg-red-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-red-500 disabled:opacity-60"
            >
              Confirm decline
            </button>
            <button
              type="button"
              onClick={() => setDeclining(false)}
              className="rounded-md border border-zinc-300 px-3 py-1.5 text-sm font-medium text-zinc-700 hover:bg-zinc-100 dark:border-zinc-700 dark:text-zinc-300 dark:hover:bg-zinc-800"
            >
              Back
            </button>
          </div>
        </div>
      )}
    </li>
  );
}
