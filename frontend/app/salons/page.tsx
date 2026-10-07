"use client";

import { useEffect, useMemo, useState } from "react";
import { MapPin } from "lucide-react";
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
        setGeoError("Couldn't get your location, so every salon is shown.");
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
          <h1 className="text-3xl font-bold text-ink sm:text-4xl">
            Find a salon
          </h1>
          <p className="mt-2 max-w-xl text-lg leading-relaxed text-ink-soft">
            {coords
              ? "Closest to you first. Pick one to see its menu and book a time."
              : "Browse every salon on CutPoint, or sort by how near they are to you."}
          </p>
        </div>
        <button
          type="button"
          onClick={useMyLocation}
          disabled={locating}
          className="inline-flex items-center gap-1.5 rounded-lg border border-line-strong bg-surface-raised px-3 py-1.5 text-sm font-medium text-ink-soft shadow-sm transition-colors hover:border-accent hover:text-accent disabled:opacity-60"
        >
          <MapPin className="h-4 w-4" aria-hidden />
          {locating ? "Locating…" : "Use my location"}
        </button>
      </div>

      {geoError && <p className="mt-3 text-sm text-caution">{geoError}</p>}
      {error && (
        <div className="mt-6 rounded-lg border border-negative-line bg-negative-soft px-4 py-3 text-sm text-negative">
          Couldn&apos;t load salons. {error}
        </div>
      )}

      <div className="mt-6 grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-3">
        {sorted === null && !error
          ? Array.from({ length: 6 }).map((_, i) => (
              <div
                key={i}
                className="h-64 animate-pulse rounded-xl border border-line bg-surface-sunken"
              />
            ))
          : sorted?.map(({ salon, distanceKm }) => (
              <SalonCard key={salon.id} salon={salon} distanceKm={distanceKm} />
            ))}
      </div>
    </div>
  );
}
