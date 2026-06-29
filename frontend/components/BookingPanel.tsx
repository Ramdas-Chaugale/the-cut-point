"use client";

import Link from "next/link";
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
      <div className="rounded-xl border border-emerald-300 bg-emerald-50 p-5 dark:border-emerald-800/50 dark:bg-emerald-950/30">
        <h3 className="font-semibold text-emerald-900 dark:text-emerald-200">Request sent ✓</h3>
        <p className="mt-1 text-sm text-emerald-800 dark:text-emerald-300">
          {salon.name} will confirm your appointment shortly. You can track it in your
          appointments.
        </p>
        <Link
          href="/appointments"
          className="mt-3 inline-block rounded-md bg-emerald-600 px-4 py-2 text-sm font-medium text-white hover:bg-emerald-500"
        >
          View my appointments
        </Link>
      </div>
    );
  }

  if (!user) {
    return (
      <div className="rounded-xl border border-zinc-200 p-5 text-sm dark:border-zinc-800">
        <p className="text-zinc-600 dark:text-zinc-400">Log in to request a booking.</p>
        <Link
          href={`/login?next=/salons/${salon.id}`}
          className="mt-3 inline-block rounded-md bg-zinc-900 px-4 py-2 text-sm font-medium text-white hover:bg-zinc-700 dark:bg-zinc-100 dark:text-zinc-900"
        >
          Log in to book
        </Link>
      </div>
    );
  }

  if (user.role !== "client") {
    return (
      <div className="rounded-xl border border-zinc-200 p-5 text-sm text-zinc-600 dark:border-zinc-800 dark:text-zinc-400">
        You&apos;re signed in as a salon account. Use a client account to make bookings.
      </div>
    );
  }

  return (
    <div className="rounded-xl border border-zinc-200 p-5 dark:border-zinc-800">
      <h3 className="font-semibold text-zinc-900 dark:text-zinc-50">Book an appointment</h3>

      {look && (
        <div className="mt-3 flex items-center justify-between rounded-md bg-violet-50 px-3 py-2 text-sm dark:bg-violet-950/30">
          <span className="text-violet-800 dark:text-violet-300">
            Bringing this look: <span className="font-medium">{look.name}</span>
          </span>
          <button
            type="button"
            onClick={() => {
              clearLook();
              setLook(null);
            }}
            className="text-xs text-violet-500 hover:underline"
          >
            remove
          </button>
        </div>
      )}

      {/* Service */}
      <label className="mt-4 block text-sm">
        <span className="text-zinc-500">Service</span>
        <select
          value={serviceId ?? ""}
          onChange={(e) => setServiceId(Number(e.target.value))}
          className="mt-1 w-full rounded-md border border-zinc-300 bg-white px-3 py-2 text-sm dark:border-zinc-700 dark:bg-zinc-900"
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
        <span className="text-zinc-500">Date</span>
        <input
          type="date"
          value={date}
          min={new Date().toISOString().slice(0, 10)}
          onChange={(e) => setDate(e.target.value)}
          className="mt-1 w-full rounded-md border border-zinc-300 bg-white px-3 py-2 text-sm dark:border-zinc-700 dark:bg-zinc-900"
        />
      </label>

      {/* Slots */}
      <div className="mt-4">
        <span className="text-sm text-zinc-500">Available times</span>
        {loadingSlots ? (
          <p className="mt-2 text-sm text-zinc-400">Loading times…</p>
        ) : slots && slots.length > 0 ? (
          <div className="mt-2 grid grid-cols-3 gap-2 sm:grid-cols-4">
            {slots.map((s) => (
              <button
                key={s}
                type="button"
                onClick={() => setSlot(s)}
                className={`rounded-md border px-2 py-1.5 text-sm font-medium transition-colors ${
                  slot === s
                    ? "border-emerald-500 bg-emerald-50 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-300"
                    : "border-zinc-200 text-zinc-700 hover:bg-zinc-50 dark:border-zinc-700 dark:text-zinc-300 dark:hover:bg-zinc-800"
                }`}
              >
                {slotTime(s)}
              </button>
            ))}
          </div>
        ) : (
          <p className="mt-2 text-sm text-zinc-400">
            No times available on this date. Try another day.
          </p>
        )}
      </div>

      {error && <p className="mt-3 text-sm text-red-600 dark:text-red-400">{error}</p>}

      <button
        type="button"
        onClick={submit}
        disabled={!slot || submitting}
        className="mt-4 w-full rounded-md bg-zinc-900 px-4 py-2 text-sm font-medium text-white hover:bg-zinc-700 disabled:opacity-50 dark:bg-zinc-100 dark:text-zinc-900 dark:hover:bg-zinc-300"
      >
        {submitting
          ? "Sending request…"
          : slot && selectedService
            ? `Request ${slotTime(slot)} · ${formatPrice(selectedService.price_pennies)}`
            : "Select a time"}
      </button>
      <p className="mt-2 text-xs text-zinc-400">
        The salon confirms your request — you&apos;ll see the status in My appointments.
      </p>
    </div>
  );
}
