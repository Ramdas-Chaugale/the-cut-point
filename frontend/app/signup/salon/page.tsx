"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { Check, MapPin } from "lucide-react";
import { useAuth } from "@/lib/auth";
import { AuthShell, ErrorNote, Field, INPUT } from "@/components/AuthShell";

export default function SalonSignupPage() {
  const { registerSaloon } = useAuth();
  const router = useRouter();

  const [form, setForm] = useState({
    full_name: "",
    email: "",
    password: "",
    name: "",
    description: "",
    address: "",
    city: "London",
    phone: "",
    chairs: 2,
    latitude: 51.5074,
    longitude: -0.1278,
  });
  const [located, setLocated] = useState(false);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  const set = (k: keyof typeof form, v: string | number) =>
    setForm((f) => ({ ...f, [k]: v }));

  const useMyLocation = () => {
    if (!navigator.geolocation) return;
    navigator.geolocation.getCurrentPosition(
      (pos) => {
        setForm((f) => ({ ...f, latitude: pos.coords.latitude, longitude: pos.coords.longitude }));
        setLocated(true);
      },
      () => setError("Couldn't get your location; using the city centre."),
    );
  };

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (form.password.length < 8) {
      setError("Password must be at least 8 characters.");
      return;
    }
    setBusy(true);
    setError("");
    try {
      await registerSaloon({
        email: form.email,
        password: form.password,
        full_name: form.full_name,
        salon: {
          name: form.name,
          description: form.description,
          address: form.address,
          city: form.city,
          latitude: form.latitude,
          longitude: form.longitude,
          phone: form.phone,
          chairs: Number(form.chairs),
        },
      });
      router.push("/dashboard");
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setBusy(false);
    }
  };

  return (
    <AuthShell
      wide
      title="List your salon"
      subtitle="Create a salon account to receive and manage booking requests."
      footer={
        <span className="text-ink-faint">
          Booking as a customer instead?{" "}
          <Link href="/signup" className="font-medium text-accent hover:underline">
            Client sign-up
          </Link>
        </span>
      }
    >
      <form onSubmit={submit} className="mt-6 flex flex-col gap-6">
        <fieldset className="flex flex-col gap-4">
          <legend className="mb-1 text-xs font-semibold uppercase tracking-wide text-ink-faint">
            Your account
          </legend>
          <Field label="Your name">
            <input
              required
              placeholder="Alex Morgan"
              value={form.full_name}
              onChange={(e) => set("full_name", e.target.value)}
              className={INPUT}
              autoComplete="name"
            />
          </Field>
          <Field label="Email">
            <input
              type="email"
              required
              placeholder="you@example.com"
              value={form.email}
              onChange={(e) => set("email", e.target.value)}
              className={INPUT}
              autoComplete="email"
            />
          </Field>
          <Field label="Password" hint="At least 8 characters.">
            <input
              type="password"
              required
              placeholder="••••••••"
              value={form.password}
              onChange={(e) => set("password", e.target.value)}
              className={INPUT}
              autoComplete="new-password"
            />
          </Field>
        </fieldset>

        <fieldset className="flex flex-col gap-4 border-t border-line pt-6">
          <legend className="mb-1 text-xs font-semibold uppercase tracking-wide text-ink-faint">
            Your salon
          </legend>
          <Field label="Salon name">
            <input
              required
              placeholder="The Cut Point"
              value={form.name}
              onChange={(e) => set("name", e.target.value)}
              className={INPUT}
            />
          </Field>
          <Field label="Short description" hint="One line clients see on your card.">
            <input
              placeholder="Modern barbering and colour, walk-ins welcome."
              value={form.description}
              onChange={(e) => set("description", e.target.value)}
              className={INPUT}
            />
          </Field>
          <Field label="Address">
            <input
              required
              placeholder="12 Botanic Avenue"
              value={form.address}
              onChange={(e) => set("address", e.target.value)}
              className={INPUT}
              autoComplete="street-address"
            />
          </Field>
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <Field label="City">
              <input
                required
                placeholder="Belfast"
                value={form.city}
                onChange={(e) => set("city", e.target.value)}
                className={INPUT}
              />
            </Field>
            <Field label="Phone">
              <input
                required
                placeholder="028 9000 0000"
                value={form.phone}
                onChange={(e) => set("phone", e.target.value)}
                className={INPUT}
                autoComplete="tel"
              />
            </Field>
          </div>
          <Field label="Chairs" hint="How many clients you can serve at once.">
            <input
              type="number"
              min={1}
              max={20}
              value={form.chairs}
              onChange={(e) => set("chairs", Number(e.target.value))}
              className={`${INPUT} sm:max-w-28`}
            />
          </Field>

          {/* Sets the map pin used for distance sorting on the salon list. */}
          <div className="flex flex-wrap items-center gap-3 rounded-lg bg-surface p-3">
            <button
              type="button"
              onClick={useMyLocation}
              className={`inline-flex items-center gap-1.5 rounded-lg border px-3 py-1.5 text-sm font-medium transition-colors ${
                located
                  ? "border-positive-line bg-positive-soft text-positive"
                  : "border-line-strong text-ink-soft hover:border-accent hover:text-accent"
              }`}
            >
              {located ? (
                <Check className="h-4 w-4" aria-hidden />
              ) : (
                <MapPin className="h-4 w-4" aria-hidden />
              )}
              {located ? "Location set" : "Use my location"}
            </button>
            <p className="text-xs text-ink-faint">
              Places your pin so nearby clients can find you. Defaults to the city centre.
            </p>
          </div>
        </fieldset>

        {error && <ErrorNote>{error}</ErrorNote>}
        <button
          type="submit"
          disabled={busy}
          className="w-full px-4 py-2.5 disabled:opacity-60 rounded-lg bg-accent text-sm font-semibold text-accent-ink shadow-sm transition-colors hover:bg-accent-hover"
        >
          {busy ? "Creating salon…" : "Create salon account"}
        </button>
      </form>
    </AuthShell>
  );
}
