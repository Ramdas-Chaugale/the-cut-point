"use client";

import Link from "next/link";
import { ArrowRight, MapPin } from "lucide-react";
import type { Salon } from "@/lib/bookingTypes";
import { salonGradient, salonInitials } from "@/lib/salonLook";

export function SalonCard({ salon, distanceKm }: { salon: Salon; distanceKm?: number }) {
  return (
    <Link
      href={`/salons/${salon.id}`}
      className="group flex flex-col overflow-hidden rounded-xl border border-line bg-surface-raised shadow-sm transition-all hover:-translate-y-0.5 hover:border-line-strong hover:shadow-md"
    >
      <div
        className="relative grid h-28 place-items-center"
        style={{ backgroundImage: salonGradient(salon.name) }}
      >
        {salon.photo_url ? (
          // eslint-disable-next-line @next/next/no-img-element
          <img src={salon.photo_url} alt={salon.name} className="h-full w-full object-cover" />
        ) : (
          <span className="text-2xl font-bold tracking-wide text-white/95">
            {salonInitials(salon.name)}
          </span>
        )}
        {distanceKm !== undefined && (
          <span className="absolute right-2 top-2 inline-flex items-center gap-1 rounded-full bg-black/55 px-2 py-0.5 text-xs font-medium text-white backdrop-blur-sm">
            <MapPin className="h-3 w-3" aria-hidden />
            {distanceKm < 1 ? `${Math.round(distanceKm * 1000)} m` : `${distanceKm.toFixed(1)} km`}
          </span>
        )}
      </div>
      <div className="flex flex-1 flex-col px-4 py-3.5">
        <h3 className="font-semibold text-ink">{salon.name}</h3>
        <p className="mt-0.5 line-clamp-1 text-sm text-ink-faint">{salon.address}</p>
        <p className="mt-1.5 line-clamp-2 text-sm leading-relaxed text-ink-soft">
          {salon.description}
        </p>
        {/* Pushed to the bottom so every card's link sits on the same line. */}
        <span className="mt-auto inline-flex items-center gap-1 pt-3 text-sm font-semibold text-accent">
          View &amp; book
          <ArrowRight
            className="h-3.5 w-3.5 transition-transform group-hover:translate-x-0.5"
            aria-hidden
          />
        </span>
      </div>
    </Link>
  );
}
