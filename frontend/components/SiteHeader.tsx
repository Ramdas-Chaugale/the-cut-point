"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useState } from "react";
import { useAuth } from "@/lib/auth";

const NAV = [
  { href: "/analyze", label: "Try a style" },
  { href: "/avatar", label: "3D avatar" },
  { href: "/salons", label: "Find a salon" },
];

function NavLink({
  href,
  label,
  onClick,
}: {
  href: string;
  label: string;
  onClick?: () => void;
}) {
  const pathname = usePathname();
  const active = pathname === href || (href !== "/" && pathname.startsWith(href));
  return (
    <Link
      href={href}
      onClick={onClick}
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
  const [open, setOpen] = useState(false);
  const pathname = usePathname();

  // Close the mobile menu on navigation.
  useEffect(() => {
    setOpen(false);
  }, [pathname]);

  const links = [
    ...NAV,
    ...(user?.role === "client" ? [{ href: "/appointments", label: "My appointments" }] : []),
    ...(user?.role === "saloon" && salonId ? [{ href: "/dashboard", label: "Dashboard" }] : []),
  ];

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
            {links.map((l) => (
              <NavLink key={l.href} href={l.href} label={l.label} />
            ))}
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
                className="hidden rounded-md border border-zinc-300 px-3 py-1.5 text-sm font-medium text-zinc-700 hover:bg-zinc-100 sm:block dark:border-zinc-700 dark:text-zinc-300 dark:hover:bg-zinc-800"
              >
                Log out
              </button>
            </>
          ) : (
            <>
              <Link
                href="/login"
                className="hidden rounded-md px-3 py-1.5 text-sm font-medium text-zinc-700 hover:text-zinc-900 sm:block dark:text-zinc-300"
              >
                Log in
              </Link>
              <Link
                href="/signup"
                className="hidden rounded-md bg-zinc-900 px-3 py-1.5 text-sm font-medium text-white hover:bg-zinc-700 sm:block dark:bg-zinc-100 dark:text-zinc-900 dark:hover:bg-zinc-300"
              >
                Sign up
              </Link>
            </>
          )}

          {/* Mobile menu button */}
          <button
            type="button"
            aria-label="Toggle menu"
            aria-expanded={open}
            onClick={() => setOpen((v) => !v)}
            className="grid h-9 w-9 place-items-center rounded-md border border-zinc-300 text-zinc-700 sm:hidden dark:border-zinc-700 dark:text-zinc-300"
          >
            {open ? "✕" : "☰"}
          </button>
        </div>
      </div>

      {/* Mobile menu panel */}
      {open && (
        <div className="border-t border-zinc-200 px-4 py-3 sm:hidden dark:border-zinc-800">
          <nav className="flex flex-col gap-1">
            {links.map((l) => (
              <NavLink key={l.href} href={l.href} label={l.label} onClick={() => setOpen(false)} />
            ))}
          </nav>
          <div className="mt-3 flex flex-col gap-2 border-t border-zinc-100 pt-3 dark:border-zinc-800">
            {user ? (
              <button
                type="button"
                onClick={logout}
                className="rounded-md border border-zinc-300 px-3 py-2 text-sm font-medium text-zinc-700 dark:border-zinc-700 dark:text-zinc-300"
              >
                Log out ({user.full_name.split(" ")[0]})
              </button>
            ) : (
              <>
                <Link
                  href="/login"
                  className="rounded-md border border-zinc-300 px-3 py-2 text-center text-sm font-medium text-zinc-700 dark:border-zinc-700 dark:text-zinc-300"
                >
                  Log in
                </Link>
                <Link
                  href="/signup"
                  className="rounded-md bg-zinc-900 px-3 py-2 text-center text-sm font-medium text-white dark:bg-zinc-100 dark:text-zinc-900"
                >
                  Sign up
                </Link>
              </>
            )}
          </div>
        </div>
      )}
    </header>
  );
}
