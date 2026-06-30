"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { useAuth } from "@/lib/auth";

const INPUT =
  "w-full rounded-md border border-zinc-300 bg-white px-3 py-2 text-sm text-zinc-900 focus:border-emerald-500 focus:outline-none dark:border-zinc-700 dark:bg-zinc-900 dark:text-zinc-100";

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
    <div className="mx-auto w-full max-w-lg px-6 py-12">
      <h1 className="text-2xl font-semibold tracking-tight text-zinc-900 dark:text-zinc-50">
        List your salon
      </h1>
      <p className="mt-1 text-sm text-zinc-500">
        Create a salon account to receive and manage booking requests.
      </p>

      <form onSubmit={submit} className="mt-6 flex flex-col gap-4">
        <fieldset className="flex flex-col gap-3">
          <legend className="text-xs font-medium uppercase tracking-wide text-zinc-400">
            Your account
          </legend>
          <input required placeholder="Your name" value={form.full_name} onChange={(e) => set("full_name", e.target.value)} className={INPUT} />
          <input type="email" required placeholder="Email" value={form.email} onChange={(e) => set("email", e.target.value)} className={INPUT} autoComplete="email" />
          <input type="password" required placeholder="Password (min 8 characters)" value={form.password} onChange={(e) => set("password", e.target.value)} className={INPUT} autoComplete="new-password" />
        </fieldset>

        <fieldset className="flex flex-col gap-3">
          <legend className="text-xs font-medium uppercase tracking-wide text-zinc-400">
            Your salon
          </legend>
          <input required placeholder="Salon name" value={form.name} onChange={(e) => set("name", e.target.value)} className={INPUT} />
          <input placeholder="Short description" value={form.description} onChange={(e) => set("description", e.target.value)} className={INPUT} />
          <input required placeholder="Address" value={form.address} onChange={(e) => set("address", e.target.value)} className={INPUT} />
          <div className="grid grid-cols-2 gap-3">
            <input required placeholder="City" value={form.city} onChange={(e) => set("city", e.target.value)} className={INPUT} />
            <input required placeholder="Phone" value={form.phone} onChange={(e) => set("phone", e.target.value)} className={INPUT} />
          </div>
          <label className="flex items-center justify-between gap-3 text-sm text-zinc-600 dark:text-zinc-400">
            <span>Chairs (clients served at once)</span>
            <input
              type="number"
              min={1}
              max={20}
              value={form.chairs}
              onChange={(e) => set("chairs", Number(e.target.value))}
              className="w-20 rounded-md border border-zinc-300 px-2 py-1 text-sm dark:border-zinc-700 dark:bg-zinc-900"
            />
          </label>
          <button
            type="button"
            onClick={useMyLocation}
            className="self-start rounded-md border border-zinc-300 px-3 py-1.5 text-sm font-medium text-zinc-700 hover:bg-zinc-100 dark:border-zinc-700 dark:text-zinc-300 dark:hover:bg-zinc-800"
          >
            {located ? "📍 Location set" : "📍 Use my location"}
          </button>
          <p className="text-xs text-zinc-400">
            Sets your map pin so nearby clients can find you. Defaults to the city centre.
          </p>
        </fieldset>

        {error && <p className="text-sm text-red-600 dark:text-red-400">{error}</p>}
        <button
          type="submit"
          disabled={busy}
          className="rounded-md bg-zinc-900 px-4 py-2 text-sm font-medium text-white hover:bg-zinc-700 disabled:opacity-60 dark:bg-zinc-100 dark:text-zinc-900 dark:hover:bg-zinc-300"
        >
          {busy ? "Creating salon…" : "Create salon account"}
        </button>
      </form>

      <p className="mt-4 text-sm text-zinc-500">
        Booking as a customer instead?{" "}
        <Link href="/signup" className="font-medium text-emerald-600 hover:underline">
          Client sign-up
        </Link>
      </p>
    </div>
  );
}
