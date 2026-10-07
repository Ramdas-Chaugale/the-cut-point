"use client";

import Link from "next/link";
import { CheckCircle2 } from "lucide-react";
import { useCallback, useEffect, useMemo, useState } from "react";
import { getAvailability, requestBooking } from "@/lib/api";
import { formatPrice, type SalonDetail } from "@/lib/bookingTypes";
import { useAuth } from "@/lib/auth";
import { clearLook, getSavedLook, type SavedLook } from "@/lib/look";

function tomorrowISO(): string {
  const d = new Date();
  d.setDate(d.getDate() + 1);
  return d.toISOString().slice(0, 10);
}

function slotTime(iso: string): string {
  return new Date(iso).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
}

export function BookingPanel({ salon }: { salon: SalonDetail }) {
  const { user } = useAuth();
  const [serviceId, setServiceId] = useState<number | null>(salon.services[0]?.id ?? null);
  const [date, setDate] = useState(tomorrowISO());
  const [slots, setSlots] = useState<string[] | null>(null);
  const [slot, setSlot] = useState<string | null>(null);
  const [loadingSlots, setLoadingSlots] = useState(false);
  const [look, setLook] = useState<SavedLook | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [done, setDone] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    setLook(getSavedLook());
  }, []);

  const loadSlots = useCallback(async () => {
    if (!serviceId) return;
    setLoadingSlots(true);
    setSlot(null);
    setError("");
    try {
      const res = await getAvailability(salon.id, serviceId, date);
      setSlots(res.slots);
    } catch (e) {
      setError((e as Error).message);
      setSlots([]);
    } finally {
      setLoadingSlots(false);
    }
  }, [salon.id, serviceId, date]);

  useEffect(() => {
    // Fetch availability when the salon/service/date changes.
    void loadSlots();
  }, [loadSlots]);

  const selectedService = useMemo(
    () => salon.services.find((s) => s.id === serviceId) ?? null,
    [salon.services, serviceId],
  );

  const submit = async () => {
    if (!serviceId || !slot) return;
    setSubmitting(true);
    setError("");
    try {
      await requestBooking({
        salon_id: salon.id,
        service_id: serviceId,
        start_at: slot,
        look_style_id: look?.id ?? null,
      });
      clearLook();
      setLook(null);
      setDone(true);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setSubmitting(false);
    }
  };

  if (done) {
    return (
      <div className="rounded-xl border border-positive-line bg-positive-soft p-5">
        <h3 className="inline-flex items-center gap-2 font-semibold text-positive">
          <CheckCircle2 className="h-5 w-5" aria-hidden />
          Request sent
        </h3>
        <p className="mt-1 text-sm text-positive">
          {salon.name} will confirm your appointment shortly. You can track it in your
          appointments.
        </p>
        <Link
          href="/appointments"
          className="mt-3 inline-block rounded-lg bg-accent px-4 py-2 text-sm font-semibold text-accent-ink shadow-sm transition-colors hover:bg-accent-hover"
        >
          View my appointments
        </Link>
      </div>
    );
  }

  if (!user) {
    return (
      <div className="rounded-xl border border-line p-5 text-sm">
        <p className="text-ink-soft">Log in to request a booking.</p>
        <Link
          href={`/login?next=/salons/${salon.id}`}
          className="mt-3 inline-block px-4 py-2 rounded-lg bg-accent text-sm font-semibold text-accent-ink shadow-sm transition-colors hover:bg-accent-hover"
        >
          Log in to book
        </Link>
      </div>
    );
  }

  if (user.role !== "client") {
    return (
      <div className="rounded-xl border border-line p-5 text-sm text-ink-soft">
        You&apos;re signed in as a salon account. Use a client account to make bookings.
      </div>
    );
  }

  return (
    <div className="rounded-xl border border-line p-5">
      <h3 className="font-semibold text-ink">Book an appointment</h3>

      {look && (
        <div className="mt-3 flex items-center justify-between rounded-lg bg-ai-soft px-3 py-2 text-sm">
          <span className="text-ai">
            Bringing this look: <span className="font-medium">{look.name}</span>
          </span>
          <button
            type="button"
            onClick={() => {
              clearLook();
              setLook(null);
            }}
            className="text-xs text-ai hover:underline"
          >
            remove
          </button>
        </div>
      )}

      {/* Service */}
      <label className="mt-4 block text-sm">
        <span className="text-ink-faint">Service</span>
        <select
          value={serviceId ?? ""}
          onChange={(e) => setServiceId(Number(e.target.value))}
          className="mt-1 w-full rounded-lg border border-line-strong bg-surface-raised px-3 py-2 text-sm"
        >
          {salon.services.map((s) => (
            <option key={s.id} value={s.id}>
              {s.name} · {s.duration_minutes} min · {formatPrice(s.price_pennies)}
            </option>
          ))}
        </select>
      </label>

      {/* Date */}
      <label className="mt-3 block text-sm">
        <span className="text-ink-faint">Date</span>
        <input
          type="date"
          value={date}
          min={new Date().toISOString().slice(0, 10)}
          onChange={(e) => setDate(e.target.value)}
          className="mt-1 w-full rounded-lg border border-line-strong bg-surface-raised px-3 py-2 text-sm"
        />
      </label>

      {/* Slots */}
      <div className="mt-4">
        <span className="text-sm text-ink-faint">Available times</span>
        {loadingSlots ? (
          <p className="mt-2 text-sm text-ink-faint">Loading times…</p>
        ) : slots && slots.length > 0 ? (
          <div className="mt-2 grid grid-cols-3 gap-2 sm:grid-cols-4">
            {slots.map((s) => (
              <button
                key={s}
                type="button"
                onClick={() => setSlot(s)}
                className={`rounded-lg border px-2 py-1.5 text-sm font-medium transition-colors ${
                  slot === s
                    ? "border-accent bg-accent-soft text-accent"
                    : "border-line text-ink-soft hover:bg-surface-sunken"
                }`}
              >
                {slotTime(s)}
              </button>
            ))}
          </div>
        ) : (
          <p className="mt-2 text-sm text-ink-faint">
            No times available on this date. Try another day.
          </p>
        )}
      </div>

      {error && <p className="mt-3 text-sm text-negative">{error}</p>}

      <button
        type="button"
        onClick={submit}
        disabled={!slot || submitting}
        className="mt-4 w-full px-4 py-2 disabled:opacity-50 rounded-lg bg-accent text-sm font-semibold text-accent-ink shadow-sm transition-colors hover:bg-accent-hover"
      >
        {submitting
          ? "Sending request…"
          : slot && selectedService
            ? `Request ${slotTime(slot)} · ${formatPrice(selectedService.price_pennies)}`
            : "Select a time"}
      </button>
      <p className="mt-2 text-xs text-ink-faint">
        The salon confirms your request. You&apos;ll see the status in My appointments.
      </p>
    </div>
  );
}
