import Link from "next/link";

export default function NotFound() {
  return (
    <div className="mx-auto flex max-w-md flex-1 flex-col items-center justify-center px-6 py-24 text-center">
      <p className="text-7xl font-semibold text-surface-raised">404</p>
      <h1 className="mt-4 text-xl font-semibold text-ink">
        Page not found
      </h1>
      <p className="mt-2 text-sm text-ink-faint">
        The page you&apos;re looking for doesn&apos;t exist or has moved.
      </p>
      <Link
        href="/"
        className="mt-6 px-5 py-2.5 rounded-lg bg-accent text-sm font-semibold text-accent-ink shadow-sm transition-colors hover:bg-accent-hover"
      >
        Back home
      </Link>
    </div>
  );
}
