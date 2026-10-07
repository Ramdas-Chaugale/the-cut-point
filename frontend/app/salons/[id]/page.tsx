"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { ArmchairIcon, ArrowLeft, MapPin, Phone } from "lucide-react";
import { useEffect, useState } from "react";
import { getSalon } from "@/lib/api";
import { formatPrice, type SalonDetail } from "@/lib/bookingTypes";
import { BookingPanel } from "@/components/BookingPanel";
import { salonGradient, salonInitials } from "@/lib/salonLook";

export default function SalonDetailPage() {
  const params = useParams<{ id: string }>();
  const salonId = Number(params.id);
  const [salon, setSalon] = useState<SalonDetail | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    let active = true;
    getSalon(salonId)
      .then((s) => active && setSalon(s))
      .catch((e) => active && setError((e as Error).message));
    return () => {
      active = false;
    };
  }, [salonId]);

  if (error) {
    return (
      <div className="mx-auto w-full max-w-5xl px-6 py-16">
        <p className="text-sm text-negative">Couldn&apos;t load this salon. {error}</p>
        <Link
          href="/salons"
          className="mt-3 inline-flex items-center gap-1.5 text-sm font-medium text-accent hover:underline"
        >
          <ArrowLeft className="h-4 w-4" aria-hidden />
          Back to salons
        </Link>
      </div>
    );
  }

  if (!salon) {
    return (
      <div className="mx-auto w-full max-w-5xl px-6 py-16">
        <div className="h-40 animate-pulse rounded-xl bg-surface-sunken" />
      </div>
    );
  }

  return (
    <div className="mx-auto w-full max-w-5xl px-4 py-8 sm:px-6">
      <Link
        href="/salons"
        className="inline-flex items-center gap-1.5 text-sm text-ink-faint transition-colors hover:text-ink"
      >
        <ArrowLeft className="h-4 w-4" aria-hidden />
        All salons
      </Link>

      {/* Banner */}
      <div
        className="mt-3 grid h-40 place-items-center rounded-xl shadow-sm sm:h-48"
        style={{ backgroundImage: salonGradient(salon.name) }}
      >
        <span className="text-4xl font-bold tracking-wide text-white/95">
          {salonInitials(salon.name)}
        </span>
      </div>

      <div className="mt-5 grid gap-8 lg:grid-cols-[1fr_360px]">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight text-ink">
            {salon.name}
          </h1>
          <p className="mt-1 text-sm text-ink-soft">{salon.description}</p>
          <dl className="mt-3 flex flex-wrap gap-x-6 gap-y-1.5 text-sm text-ink-faint">
            <span className="inline-flex items-center gap-1.5">
              <MapPin className="h-4 w-4 text-accent" aria-hidden />
              {salon.address}
            </span>
            <span className="inline-flex items-center gap-1.5">
              <Phone className="h-4 w-4 text-accent" aria-hidden />
              {salon.phone}
            </span>
            <span className="inline-flex items-center gap-1.5">
              <ArmchairIcon className="h-4 w-4 text-accent" aria-hidden />
              {salon.chairs} chair{salon.chairs > 1 ? "s" : ""}
            </span>
          </dl>

          <h2 className="mt-6 text-sm font-medium uppercase tracking-wide text-ink-faint">
            Menu &amp; rates
          </h2>
          <ul className="mt-2 divide-y divide-line">
            {salon.services.map((s) => (
              <li key={s.id} className="flex items-start justify-between gap-4 py-3">
                <div>
                  <p className="font-medium text-ink">{s.name}</p>
                  <p className="text-sm text-ink-faint">
                    {s.description} · {s.duration_minutes} min
                  </p>
                </div>
                <span className="shrink-0 font-medium text-ink">
                  {formatPrice(s.price_pennies)}
                </span>
              </li>
            ))}
          </ul>
        </div>

        {/* Booking aside */}
        <aside className="lg:sticky lg:top-20 lg:self-start">
          <BookingPanel salon={salon} />
        </aside>
      </div>
    </div>
  );
}
