"use client";

import Link from "next/link";

export default function Error({ reset }: { error: Error & { digest?: string }; reset: () => void }) {
  return (
    <div className="mx-auto flex max-w-md flex-1 flex-col items-center justify-center px-6 py-24 text-center">
      <p className="text-5xl font-semibold text-surface-raised">Oops</p>
      <h1 className="mt-4 text-xl font-semibold text-ink">
        Something went wrong
      </h1>
      <p className="mt-2 text-sm text-ink-faint">
        An unexpected error occurred. Please try again.
      </p>
      <div className="mt-6 flex gap-2">
        <button
          type="button"
          onClick={reset}
          className="px-5 py-2.5 rounded-lg bg-accent text-sm font-semibold text-accent-ink shadow-sm transition-colors hover:bg-accent-hover"
        >
          Try again
        </button>
        <Link
          href="/"
          className="rounded-lg border border-line-strong px-5 py-2.5 text-sm font-medium text-ink-soft hover:bg-surface-sunken"
        >
          Back home
        </Link>
      </div>
    </div>
  );
}
