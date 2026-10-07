"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { useAuth } from "@/lib/auth";
import { AuthShell, ErrorNote, Field, INPUT } from "@/components/AuthShell";

export default function SignupPage() {
  const { registerClient } = useAuth();
  const router = useRouter();
  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [phone, setPhone] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (password.length < 8) {
      setError("Password must be at least 8 characters.");
      return;
    }
    setBusy(true);
    setError("");
    try {
      await registerClient({
        email,
        password,
        full_name: fullName,
        phone: phone || undefined,
      });
      router.push("/salons");
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setBusy(false);
    }
  };

  return (
    <AuthShell
      title="Create your account"
      subtitle="Book hairstyles and salon appointments in one place."
      footer={
        <div className="flex flex-col gap-1 text-ink-faint">
          <span>
            Already have an account?{" "}
            <Link href="/login" className="font-medium text-accent hover:underline">
              Log in
            </Link>
          </span>
          <span>
            Run a salon?{" "}
            <Link href="/signup/salon" className="font-medium text-accent hover:underline">
              List your business
            </Link>
          </span>
        </div>
      }
    >
      <form onSubmit={submit} className="mt-6 flex flex-col gap-4">
        <Field label="Full name">
          <input
            required
            placeholder="Alex Morgan"
            value={fullName}
            onChange={(e) => setFullName(e.target.value)}
            className={INPUT}
            autoComplete="name"
          />
        </Field>
        <Field label="Email">
          <input
            type="email"
            required
            placeholder="you@example.com"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            className={INPUT}
            autoComplete="email"
          />
        </Field>
        <Field label="Phone" hint="Optional. Salons use it if they need to reach you.">
          <input
            placeholder="07700 900000"
            value={phone}
            onChange={(e) => setPhone(e.target.value)}
            className={INPUT}
            autoComplete="tel"
          />
        </Field>
        <Field label="Password" hint="At least 8 characters.">
          <input
            type="password"
            required
            placeholder="••••••••"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            className={INPUT}
            autoComplete="new-password"
          />
        </Field>
        {error && <ErrorNote>{error}</ErrorNote>}
        <button
          type="submit"
          disabled={busy}
          className="mt-1 w-full px-4 py-2.5 disabled:opacity-60 rounded-lg bg-accent text-sm font-semibold text-accent-ink shadow-sm transition-colors hover:bg-accent-hover"
        >
          {busy ? "Creating account…" : "Create account"}
        </button>
      </form>
    </AuthShell>
  );
}
