"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useAuth } from "@/lib/auth";

function NavLink({ href, label }: { href: string; label: string }) {
  const pathname = usePathname();
  const active = pathname === href || (href !== "/" && pathname.startsWith(href));
  return (
    <Link
      href={href}
      className={`rounded-md px-3 py-1.5 text-sm font-medium transition-colors ${
        active
          ? "bg-zinc-100 text-zinc-900 dark:bg-zinc-800 dark:text-zinc-100"
          : "text-zinc-600 hover:text-zinc-900 dark:text-zinc-400 dark:hover:text-zinc-100"
      }`}
    >
      {label}
    </Link>
  );
}

export function SiteHeader() {
  const { user, salonId, logout, loading } = useAuth();

  return (
    <header className="sticky top-0 z-20 border-b border-zinc-200 bg-white/80 backdrop-blur dark:border-zinc-800 dark:bg-black/70">
      <div className="mx-auto flex h-14 w-full max-w-6xl items-center justify-between px-4 sm:px-6">
        <div className="flex items-center gap-1 sm:gap-2">
          <Link href="/" className="mr-2 flex items-center gap-2 font-semibold tracking-tight">
            <span className="grid h-7 w-7 place-items-center rounded-md bg-zinc-900 text-sm text-white dark:bg-zinc-100 dark:text-zinc-900">
              C
            </span>
            <span className="text-zinc-900 dark:text-zinc-50">CutPoint</span>
          </Link>
          <nav className="hidden items-center gap-0.5 sm:flex">
            <NavLink href="/analyze" label="Try a style" />
            <NavLink href="/salons" label="Find a salon" />
            {user?.role === "client" && <NavLink href="/appointments" label="My appointments" />}
            {user?.role === "saloon" && salonId && <NavLink href="/dashboard" label="Dashboard" />}
          </nav>
        </div>

        <div className="flex items-center gap-2">
          {loading ? (
            <span className="h-4 w-16 animate-pulse rounded bg-zinc-200 dark:bg-zinc-800" />
          ) : user ? (
            <>
              <span className="hidden text-sm text-zinc-500 sm:inline">
                {user.full_name.split(" ")[0]}
              </span>
              <button
                type="button"
                onClick={logout}
                className="rounded-md border border-zinc-300 px-3 py-1.5 text-sm font-medium text-zinc-700 hover:bg-zinc-100 dark:border-zinc-700 dark:text-zinc-300 dark:hover:bg-zinc-800"
              >
                Log out
              </button>
            </>
          ) : (
            <>
              <Link
                href="/login"
                className="rounded-md px-3 py-1.5 text-sm font-medium text-zinc-700 hover:text-zinc-900 dark:text-zinc-300"
              >
                Log in
              </Link>
              <Link
                href="/signup"
                className="rounded-md bg-zinc-900 px-3 py-1.5 text-sm font-medium text-white hover:bg-zinc-700 dark:bg-zinc-100 dark:text-zinc-900 dark:hover:bg-zinc-300"
              >
                Sign up
              </Link>
            </>
          )}
        </div>
      </div>
    </header>
  );
}
