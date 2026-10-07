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
    <li className="rounded-xl border border-line p-4">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <p className="font-medium text-ink">
            {booking.service_name}{" "}
            <span className="font-normal text-ink-faint">· {formatPrice(booking.price_pennies)}</span>
          </p>
          <p className="mt-0.5 text-sm text-ink-faint">
            {booking.client_name} · {fmt(booking.start_at)}
          </p>
          {booking.look_style_id && (
            <p className="mt-0.5 text-xs text-ai">
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
              className="rounded-lg bg-positive px-3 py-1.5 text-sm font-semibold text-positive-ink transition-colors hover:bg-positive-hover disabled:opacity-60"
            >
              Accept
            </button>
            <button
              type="button"
              disabled={busy}
              onClick={() => setDeclining(true)}
              className="rounded-lg border border-line-strong px-3 py-1.5 text-sm font-medium text-ink-soft hover:bg-surface-sunken disabled:opacity-60"
            >
              Decline
            </button>
          </div>
        )}
      </div>

      {declining && (
        <div className="mt-3 rounded-lg bg-surface-sunken p-3">
          <label className="block text-sm text-ink-soft">
            Suggest an alternative time (optional)
            <input
              type="datetime-local"
              value={suggested}
              onChange={(e) => setSuggested(e.target.value)}
              className="mt-1 w-full rounded-lg border border-line-strong bg-surface-raised px-2 py-1.5 text-sm"
            />
          </label>
          <div className="mt-2 flex gap-2">
            <button
              type="button"
              disabled={busy}
              onClick={() => run(() => onDecline(booking.id, suggested || null))}
              className="rounded-lg bg-negative px-3 py-1.5 text-sm font-semibold text-negative-ink transition-colors hover:bg-negative-hover disabled:opacity-60"
            >
              Confirm decline
            </button>
            <button
              type="button"
              onClick={() => setDeclining(false)}
              className="rounded-lg border border-line-strong px-3 py-1.5 text-sm font-medium text-ink-soft hover:bg-surface-sunken"
            >
              Back
            </button>
          </div>
        </div>
      )}
    </li>
  );
}
