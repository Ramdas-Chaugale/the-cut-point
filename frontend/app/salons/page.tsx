"use client";

import { useEffect, useMemo, useState } from "react";
import { listSalons } from "@/lib/api";
import { haversineKm, type Salon } from "@/lib/bookingTypes";
import { SalonCard } from "@/components/SalonCard";

type Coords = { lat: number; lng: number };

export default function SalonsPage() {
  const [salons, setSalons] = useState<Salon[] | null>(null);
  const [error, setError] = useState("");
  const [coords, setCoords] = useState<Coords | null>(null);
  const [locating, setLocating] = useState(false);
  const [geoError, setGeoError] = useState("");

  useEffect(() => {
    let active = true;
    listSalons()
      .then((s) => active && setSalons(s))
      .catch((e) => active && setError((e as Error).message));
    return () => {
      active = false;
    };
  }, []);

  const useMyLocation = () => {
    if (!navigator.geolocation) {
      setGeoError("Geolocation isn't available in this browser.");
      return;
    }
    setLocating(true);
    setGeoError("");
    navigator.geolocation.getCurrentPosition(
      (pos) => {
        setCoords({ lat: pos.coords.latitude, lng: pos.coords.longitude });
        setLocating(false);
      },
      () => {
        setGeoError("Couldn't get your location — showing all salons instead.");
        setLocating(false);
      },
      { enableHighAccuracy: false, timeout: 8000 },
    );
  };

  const sorted = useMemo(() => {
    if (!salons) return null;
    if (!coords) return salons.map((s) => ({ salon: s, distanceKm: undefined as number | undefined }));
    return salons
      .map((s) => ({
        salon: s,
        distanceKm: haversineKm(coords, { lat: s.latitude, lng: s.longitude }),
      }))
      .sort((a, b) => (a.distanceKm ?? 0) - (b.distanceKm ?? 0));
  }, [salons, coords]);

  return (
    <div className="mx-auto w-full max-w-6xl px-4 py-10 sm:px-6">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight text-zinc-900 dark:text-zinc-50">
            Find a salon
          </h1>
          <p className="mt-1 text-sm text-zinc-500">
            {coords
              ? "Sorted by distance from you."
              : "Browse our partner salons, or sort by distance."}
          </p>
        </div>
        <button
          type="button"
          onClick={useMyLocation}
          disabled={locating}
          className="rounded-md border border-zinc-300 px-3 py-1.5 text-sm font-medium text-zinc-700 hover:bg-zinc-100 disabled:opacity-60 dark:border-zinc-700 dark:text-zinc-300 dark:hover:bg-zinc-800"
        >
          {locating ? "Locating…" : "📍 Use my location"}
        </button>
      </div>

      {geoError && <p className="mt-3 text-sm text-amber-600 dark:text-amber-400">{geoError}</p>}
      {error && (
        <div className="mt-6 rounded-lg border border-red-300 bg-red-50 px-4 py-3 text-sm text-red-800 dark:border-red-800/50 dark:bg-red-950/40 dark:text-red-200">
          Couldn&apos;t load salons — {error}
        </div>
      )}

      <div className="mt-6 grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-3">
        {sorted === null && !error
          ? Array.from({ length: 6 }).map((_, i) => (
              <div
                key={i}
                className="h-64 animate-pulse rounded-xl border border-zinc-200 bg-zinc-50 dark:border-zinc-800 dark:bg-zinc-900"
              />
            ))
          : sorted?.map(({ salon, distanceKm }) => (
              <SalonCard key={salon.id} salon={salon} distanceKm={distanceKm} />
            ))}
      </div>
    </div>
  );
}
