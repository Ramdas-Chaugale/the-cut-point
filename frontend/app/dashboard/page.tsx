"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";
import { acceptBooking, declineBooking, getSalonBookings, getSalonStats } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import { type BookingDetail, formatPrice, type SalonStats } from "@/lib/bookingTypes";
import { SalonRequestCard } from "@/components/SalonRequestCard";

function fmt(iso: string): string {
  return new Date(iso).toLocaleString([], {
    weekday: "short",
    day: "numeric",
    month: "short",
    hour: "2-digit",
    minute: "2-digit",
  });
}

interface ClientRow {
  name: string;
  visits: number;
  last: string;
}
interface DashboardView {
  pending: BookingDetail[];
  upcoming: BookingDetail[];
  completed: BookingDetail[];
  clients: ClientRow[];
}

const EMPTY_VIEW: DashboardView = { pending: [], upcoming: [], completed: [], clients: [] };

/** Partition bookings into the dashboard sections (now passed in, kept pure). */
function partition(list: BookingDetail[], now: number): DashboardView {
  const confirmed = list.filter((b) => b.status === "confirmed");
  const byClient = new Map<number, ClientRow>();
  for (const b of list) {
    if (b.status === "cancelled" || b.status === "declined") continue;
    const prev = byClient.get(b.client_id);
    byClient.set(b.client_id, {
      name: b.client_name,
      visits: (prev?.visits ?? 0) + 1,
      last: !prev || b.start_at > prev.last ? b.start_at : prev.last,
    });
  }
  return {
    pending: list.filter((b) => b.status === "pending"),
    upcoming: confirmed
      .filter((b) => new Date(b.start_at).getTime() > now)
      .sort((a, b) => +new Date(a.start_at) - +new Date(b.start_at)),
    completed: confirmed
      .filter((b) => new Date(b.end_at).getTime() <= now)
      .sort((a, b) => +new Date(b.start_at) - +new Date(a.start_at)),
    clients: [...byClient.values()].sort((a, b) => b.visits - a.visits),
  };
}

function StatCard({ label, value }: { label: string; value: string | number }) {
  return (
    <div className="rounded-xl border border-zinc-200 px-4 py-3 dark:border-zinc-800">
      <p className="text-xs uppercase tracking-wide text-zinc-400">{label}</p>
      <p className="mt-1 text-2xl font-semibold text-zinc-900 dark:text-zinc-50">{value}</p>
    </div>
  );
}

function BookingRow({ b }: { b: BookingDetail }) {
  return (
    <li className="flex items-center justify-between gap-3 py-2.5 text-sm">
      <span className="text-zinc-700 dark:text-zinc-300">
        {b.service_name} · {b.client_name}
      </span>
      <span className="text-zinc-500">{fmt(b.start_at)}</span>
    </li>
  );
}

export default function DashboardPage() {
  const { user, salonId, loading } = useAuth();
  const [view, setView] = useState<DashboardView | null>(null);
  const [stats, setStats] = useState<SalonStats | null>(null);
  const [error, setError] = useState("");

  const load = useCallback(async () => {
    try {
      const [bookings, s] = await Promise.all([getSalonBookings(), getSalonStats()]);
      setView(partition(bookings, Date.now()));
      setStats(s);
    } catch (e) {
      setError((e as Error).message);
    }
  }, []);

  useEffect(() => {
    if (user?.role === "saloon") void load();
  }, [user, load]);

  const onAccept = async (id: number) => {
    await acceptBooking(id);
    await load();
  };
  const onDecline = async (id: number, suggested: string | null) => {
    await declineBooking(id, suggested);
    await load();
  };

  if (loading) {
    return <div className="mx-auto max-w-5xl px-6 py-16 text-sm text-zinc-400">Loading…</div>;
  }
  if (!user || user.role !== "saloon" || !salonId) {
    return (
      <div className="mx-auto max-w-3xl px-6 py-16">
        <p className="text-sm text-zinc-600 dark:text-zinc-400">
          This dashboard is for salon accounts.
        </p>
        <Link
          href="/login"
          className="mt-3 inline-block rounded-md bg-zinc-900 px-4 py-2 text-sm font-medium text-white dark:bg-zinc-100 dark:text-zinc-900"
        >
          Log in as a salon
        </Link>
      </div>
    );
  }

  const v = view ?? EMPTY_VIEW;

  return (
    <div className="mx-auto w-full max-w-5xl px-4 py-10 sm:px-6">
      <h1 className="text-2xl font-semibold tracking-tight text-zinc-900 dark:text-zinc-50">
        Salon dashboard
      </h1>
      <p className="mt-1 text-sm text-zinc-500">Welcome back, {user.full_name.split(" ")[0]}.</p>

      {error && <p className="mt-3 text-sm text-red-600 dark:text-red-400">{error}</p>}

      {/* Stats */}
      <div className="mt-6 grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-5">
        <StatCard label="Requests" value={stats?.pending_requests ?? "—"} />
        <StatCard label="Upcoming" value={stats?.upcoming_confirmed ?? "—"} />
        <StatCard label="Completed" value={stats?.completed ?? "—"} />
        <StatCard label="Revenue" value={stats ? formatPrice(stats.revenue_pennies) : "—"} />
        <StatCard label="Clients" value={stats?.unique_clients ?? "—"} />
      </div>

      <div className="mt-8 grid gap-8 lg:grid-cols-[1fr_320px]">
        <div className="space-y-8">
          {/* Requests */}
          <section>
            <h2 className="text-lg font-semibold text-zinc-900 dark:text-zinc-50">
              Booking requests
            </h2>
            {view === null ? (
              <p className="mt-2 text-sm text-zinc-400">Loading…</p>
            ) : v.pending.length === 0 ? (
              <p className="mt-2 text-sm text-zinc-500">No pending requests right now.</p>
            ) : (
              <ul className="mt-3 space-y-3">
                {v.pending.map((b) => (
                  <SalonRequestCard
                    key={b.id}
                    booking={b}
                    onAccept={onAccept}
                    onDecline={onDecline}
                  />
                ))}
              </ul>
            )}
          </section>

          {/* Time book — upcoming */}
          <section>
            <h2 className="text-lg font-semibold text-zinc-900 dark:text-zinc-50">
              Upcoming appointments
            </h2>
            {v.upcoming.length === 0 ? (
              <p className="mt-2 text-sm text-zinc-500">Nothing booked ahead yet.</p>
            ) : (
              <ul className="mt-2 divide-y divide-zinc-100 dark:divide-zinc-800">
                {v.upcoming.map((b) => (
                  <BookingRow key={b.id} b={b} />
                ))}
              </ul>
            )}
          </section>

          {/* Completed */}
          {v.completed.length > 0 && (
            <section>
              <h2 className="text-lg font-semibold text-zinc-900 dark:text-zinc-50">Completed</h2>
              <ul className="mt-2 divide-y divide-zinc-100 dark:divide-zinc-800">
                {v.completed.slice(0, 10).map((b) => (
                  <BookingRow key={b.id} b={b} />
                ))}
              </ul>
            </section>
          )}
        </div>

        {/* Clients */}
        <aside>
          <h2 className="text-lg font-semibold text-zinc-900 dark:text-zinc-50">Clients</h2>
          {v.clients.length === 0 ? (
            <p className="mt-2 text-sm text-zinc-500">No clients yet.</p>
          ) : (
            <ul className="mt-2 space-y-1.5">
              {v.clients.map((c) => (
                <li
                  key={c.name + c.last}
                  className="flex items-center justify-between rounded-md border border-zinc-200 px-3 py-2 text-sm dark:border-zinc-800"
                >
                  <span className="text-zinc-800 dark:text-zinc-200">{c.name}</span>
                  <span className="text-xs text-zinc-500">
                    {c.visits} visit{c.visits > 1 ? "s" : ""}
                  </span>
                </li>
              ))}
            </ul>
          )}
        </aside>
      </div>
    </div>
  );
}
