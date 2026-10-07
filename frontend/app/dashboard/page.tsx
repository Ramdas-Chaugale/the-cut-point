"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";
import {
  CalendarClock,
  CheckCircle2,
  Clock,
  Inbox,
  PoundSterling,
  Users,
} from "lucide-react";
import { acceptBooking, declineBooking, getSalonBookings, getSalonStats } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import { type BookingDetail, formatPrice, type SalonStats } from "@/lib/bookingTypes";
import { SalonRequestCard } from "@/components/SalonRequestCard";
import { salonGradient, salonInitials } from "@/lib/salonLook";

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

function StatCard({
  label,
  value,
  Icon,
  highlight,
}: {
  label: string;
  value: string | number;
  Icon: React.ComponentType<{ className?: string }>;
  highlight?: boolean;
}) {
  return (
    <div
      className={`rounded-xl border bg-surface-raised px-4 py-3.5 shadow-sm ${
        highlight ? "border-accent" : "border-line"
      }`}
    >
      <div className="flex items-center gap-2">
        <Icon className={`h-4 w-4 ${highlight ? "text-accent" : "text-ink-faint"}`} />
        <p className="text-xs font-medium uppercase tracking-wide text-ink-faint">{label}</p>
      </div>
      <p className="mt-1.5 text-2xl font-bold text-ink">{value}</p>
    </div>
  );
}

/** A coloured disc with someone's initials, so rows are scannable. */
function Avatar({ name }: { name: string }) {
  return (
    <span
      className="grid h-9 w-9 shrink-0 place-items-center rounded-full text-xs font-bold text-white/95"
      style={{ backgroundImage: salonGradient(name) }}
      aria-hidden
    >
      {salonInitials(name)}
    </span>
  );
}

/** Section heading with a count, so a busy section is obvious at a glance. */
function SectionTitle({ children, count }: { children: React.ReactNode; count?: number }) {
  return (
    <h2 className="flex items-center gap-2 text-lg font-semibold text-ink">
      {children}
      {count ? (
        <span className="rounded-full bg-accent-soft px-2 py-0.5 text-xs font-semibold text-accent">
          {count}
        </span>
      ) : null}
    </h2>
  );
}

function BookingRow({ b, done }: { b: BookingDetail; done?: boolean }) {
  return (
    <li className="flex items-center gap-3 rounded-lg border border-line bg-surface-raised px-3 py-2.5 text-sm shadow-sm">
      <Avatar name={b.client_name} />
      <span className="min-w-0 flex-1">
        <span className="block truncate font-medium text-ink">{b.service_name}</span>
        <span className="block truncate text-xs text-ink-faint">{b.client_name}</span>
      </span>
      <span className="inline-flex shrink-0 items-center gap-1.5 text-xs text-ink-faint">
        {done ? (
          <CheckCircle2 className="h-3.5 w-3.5 text-positive" aria-hidden />
        ) : (
          <Clock className="h-3.5 w-3.5" aria-hidden />
        )}
        {fmt(b.start_at)}
      </span>
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
    return <div className="mx-auto max-w-5xl px-6 py-16 text-sm text-ink-faint">Loading…</div>;
  }
  if (!user || user.role !== "saloon" || !salonId) {
    return (
      <div className="mx-auto max-w-3xl px-6 py-16">
        <p className="text-sm text-ink-soft">
          This dashboard is for salon accounts. Log in with one to manage your
          booking requests.
        </p>
        <Link
          href="/login"
          className="mt-3 inline-block px-4 py-2 rounded-lg bg-accent text-sm font-semibold text-accent-ink shadow-sm transition-colors hover:bg-accent-hover"
        >
          Log in as a salon
        </Link>
      </div>
    );
  }

  const v = view ?? EMPTY_VIEW;

  return (
    <div className="mx-auto w-full max-w-5xl px-4 py-10 sm:px-6">
      <h1 className="text-3xl font-bold text-ink sm:text-4xl">
        Salon dashboard
      </h1>
      <p className="mt-1 text-sm text-ink-faint">Welcome back, {user.full_name.split(" ")[0]}.</p>

      {error && <p className="mt-3 text-sm text-negative">{error}</p>}

      {/* Stats */}
      <div className="mt-6 grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-5">
        <StatCard
          label="Requests"
          value={stats?.pending_requests ?? "—"}
          Icon={Inbox}
          highlight={Boolean(stats?.pending_requests)}
        />
        <StatCard label="Upcoming" value={stats?.upcoming_confirmed ?? "—"} Icon={CalendarClock} />
        <StatCard label="Completed" value={stats?.completed ?? "—"} Icon={CheckCircle2} />
        <StatCard
          label="Revenue"
          value={stats ? formatPrice(stats.revenue_pennies) : "—"}
          Icon={PoundSterling}
        />
        <StatCard label="Clients" value={stats?.unique_clients ?? "—"} Icon={Users} />
      </div>

      <div className="mt-8 grid gap-8 lg:grid-cols-[1fr_320px]">
        <div className="space-y-8">
          {/* Requests */}
          <section>
            <SectionTitle count={v.pending.length}>Booking requests</SectionTitle>
            {view === null ? (
              <p className="mt-2 text-sm text-ink-faint">Loading…</p>
            ) : v.pending.length === 0 ? (
              <p className="mt-3 rounded-lg border border-dashed border-line-strong px-4 py-6 text-center text-sm text-ink-faint">No requests waiting. New ones appear here the moment a client sends them.</p>
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

          {/* Upcoming appointments */}
          <section>
            <SectionTitle count={v.upcoming.length}>Upcoming appointments</SectionTitle>
            {v.upcoming.length === 0 ? (
              <p className="mt-3 rounded-lg border border-dashed border-line-strong px-4 py-6 text-center text-sm text-ink-faint">Nothing booked ahead. Requests you accept move here automatically.</p>
            ) : (
              <ul className="mt-3 space-y-2">
                {v.upcoming.map((b) => (
                  <BookingRow key={b.id} b={b} />
                ))}
              </ul>
            )}
          </section>

          {/* Completed */}
          {v.completed.length > 0 && (
            <section>
              <SectionTitle count={v.completed.length}>Completed</SectionTitle>
              <ul className="mt-3 space-y-2">
                {v.completed.slice(0, 10).map((b) => (
                  <BookingRow key={b.id} b={b} done />
                ))}
              </ul>
            </section>
          )}
        </div>

        {/* Clients */}
        <aside>
          <SectionTitle count={v.clients.length}>Clients</SectionTitle>
          {v.clients.length === 0 ? (
            <p className="mt-3 rounded-lg border border-dashed border-line-strong px-4 py-6 text-center text-sm text-ink-faint">No clients yet. Anyone who books with you shows up here.</p>
          ) : (
            <ul className="mt-3 space-y-2">
              {v.clients.map((c) => (
                <li
                  key={c.name + c.last}
                  className="flex items-center gap-3 rounded-lg border border-line bg-surface-raised px-3 py-2 text-sm shadow-sm"
                >
                  <Avatar name={c.name} />
                  <span className="min-w-0 flex-1 truncate font-medium text-ink">{c.name}</span>
                  <span className="shrink-0 text-xs text-ink-faint">
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
