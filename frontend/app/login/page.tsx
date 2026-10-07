"use client";

import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { Suspense, useState } from "react";
import { useAuth } from "@/lib/auth";
import { AuthShell, ErrorNote, Field, INPUT } from "@/components/AuthShell";

function LoginForm() {
  const { login } = useAuth();
  const router = useRouter();
  const params = useSearchParams();
  const next = params.get("next");

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setBusy(true);
    setError("");
    try {
      const user = await login(email, password);
      router.push(next ?? (user.role === "saloon" ? "/dashboard" : "/salons"));
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setBusy(false);
    }
  };

  const fillDemo = (e: string) => {
    setEmail(e);
    setPassword("password123");
  };

  return (
    <AuthShell
      title="Welcome back"
      subtitle="Log in to book and manage appointments."
      footer={
        <span className="text-ink-faint">
          New here?{" "}
          <Link href="/signup" className="font-medium text-accent hover:underline">
            Create an account
          </Link>
        </span>
      }
    >
      <form onSubmit={submit} className="mt-6 flex flex-col gap-4">
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
        <Field label="Password">
          <input
            type="password"
            required
            placeholder="••••••••"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            className={INPUT}
            autoComplete="current-password"
          />
        </Field>
        {error && <ErrorNote>{error}</ErrorNote>}
        <button
          type="submit"
          disabled={busy}
          className="mt-1 w-full px-4 py-2.5 disabled:opacity-60 rounded-lg bg-accent text-sm font-semibold text-accent-ink shadow-sm transition-colors hover:bg-accent-hover"
        >
          {busy ? "Logging in…" : "Log in"}
        </button>
      </form>

      {/* Seeded accounts, so the app can be tried without signing up first. */}
      <div className="mt-6 rounded-lg border border-dashed border-line-strong bg-surface p-4">
        <p className="text-sm font-medium text-ink-soft">Demo accounts</p>
        <p className="mt-0.5 text-xs text-ink-faint">Password for both: password123</p>
        <div className="mt-2.5 flex flex-wrap gap-2">
          <button
            type="button"
            onClick={() => fillDemo("client@cutpoint.demo")}
            className="rounded-lg border border-line-strong bg-surface-raised px-2.5 py-1 text-xs font-medium text-ink-soft transition-colors hover:border-accent hover:text-accent"
          >
            Client
          </button>
          <button
            type="button"
            onClick={() => fillDemo("alex@cutpoint.demo")}
            className="rounded-lg border border-line-strong bg-surface-raised px-2.5 py-1 text-xs font-medium text-ink-soft transition-colors hover:border-accent hover:text-accent"
          >
            Salon owner
          </button>
        </div>
      </div>
    </AuthShell>
  );
}

export default function LoginPage() {
  return (
    <Suspense>
      <LoginForm />
    </Suspense>
  );
}
