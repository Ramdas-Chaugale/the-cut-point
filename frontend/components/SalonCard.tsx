"use client";

import Link from "next/link";
import type { Salon } from "@/lib/bookingTypes";

export function SalonCard({ salon, distanceKm }: { salon: Salon; distanceKm?: number }) {
  const initial = salon.name.charAt(0).toUpperCase();
  return (
    <Link
      href={`/salons/${salon.id}`}
      className="group flex flex-col overflow-hidden rounded-xl border border-zinc-200 bg-white transition-shadow hover:shadow-md dark:border-zinc-800 dark:bg-zinc-900"
    >
      <div className="relative grid h-28 place-items-center bg-gradient-to-br from-zinc-700 to-zinc-900">
        {salon.photo_url ? (
          // eslint-disable-next-line @next/next/no-img-element
          <img src={salon.photo_url} alt={salon.name} className="h-full w-full object-cover" />
        ) : (
          <span className="text-3xl font-semibold text-white/90">{initial}</span>
        )}
        {distanceKm !== undefined && (
          <span className="absolute right-2 top-2 rounded-full bg-black/55 px-2 py-0.5 text-xs font-medium text-white">
            {distanceKm < 1 ? `${Math.round(distanceKm * 1000)} m` : `${distanceKm.toFixed(1)} km`}
          </span>
        )}
      </div>
      <div className="flex flex-1 flex-col px-4 py-3">
        <h3 className="font-semibold text-zinc-900 dark:text-zinc-50">{salon.name}</h3>
        <p className="mt-0.5 line-clamp-1 text-sm text-zinc-500">{salon.address}</p>
        <p className="mt-1 line-clamp-2 text-sm text-zinc-600 dark:text-zinc-400">
          {salon.description}
        </p>
        <span className="mt-3 text-sm font-medium text-emerald-600 group-hover:underline">
          View &amp; book →
        </span>
      </div>
    </Link>
  );
}
