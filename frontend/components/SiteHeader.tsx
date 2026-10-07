"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useState } from "react";
import { Menu, Scissors, X } from "lucide-react";
import { useAuth } from "@/lib/auth";

const NAV = [
  { href: "/analyze", label: "Try a style" },
  { href: "/styles", label: "Catalogue" },
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
      // The active tab is marked with the accent rather than a grey fill, so
      // there is one obvious "you are here" signal on every page.
      className={`relative rounded-lg px-3 py-1.5 text-sm font-medium transition-colors ${
        active
          ? "bg-accent-soft text-accent"
          : "text-ink-soft hover:bg-surface-sunken hover:text-ink"
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
    <header className="sticky top-0 z-20 border-b border-line bg-surface/85 backdrop-blur-md">
      <div className="mx-auto flex h-16 w-full max-w-6xl items-center justify-between px-4 sm:px-6">
        <div className="flex items-center gap-1 sm:gap-2">
          <Link href="/" className="mr-2 flex items-center gap-2.5">
            <span className="grid h-9 w-9 place-items-center rounded-xl bg-accent text-accent-ink shadow-sm">
              <Scissors className="h-4.5 w-4.5" aria-hidden />
            </span>
            <span className="font-display text-lg font-bold tracking-tight text-ink">
              CutPoint
            </span>
          </Link>
          <nav className="hidden items-center gap-0.5 sm:flex">
            {links.map((l) => (
              <NavLink key={l.href} href={l.href} label={l.label} />
            ))}
          </nav>
        </div>

        <div className="flex items-center gap-2">
          {loading ? (
            <span className="h-4 w-16 animate-pulse rounded bg-surface-sunken" />
          ) : user ? (
            <>
              <span className="hidden text-sm text-ink-faint sm:inline">
                {user.full_name.split(" ")[0]}
              </span>
              <button
                type="button"
                onClick={logout}
                className="hidden rounded-lg border border-line-strong px-3 py-1.5 text-sm font-medium text-ink-soft transition-colors hover:bg-surface-sunken hover:text-ink sm:block"
              >
                Log out
              </button>
            </>
          ) : (
            <>
              <Link
                href="/login"
                className="hidden rounded-lg px-3 py-1.5 text-sm font-medium text-ink-soft transition-colors hover:text-ink sm:block"
              >
                Log in
              </Link>
              <Link
                href="/signup"
                className="hidden px-4 py-1.5 sm:block rounded-lg bg-accent text-sm font-semibold text-accent-ink shadow-sm transition-colors hover:bg-accent-hover"
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
            className="grid h-10 w-10 place-items-center rounded-lg border border-line-strong text-ink-soft transition-colors hover:bg-surface-sunken sm:hidden"
          >
            {open ? (
              <X className="h-5 w-5" aria-hidden />
            ) : (
              <Menu className="h-5 w-5" aria-hidden />
            )}
          </button>
        </div>
      </div>

      {/* Mobile menu panel */}
      {open && (
        <div className="border-t border-line bg-surface-raised px-4 py-3 sm:hidden">
          <nav className="flex flex-col gap-1">
            {links.map((l) => (
              <NavLink key={l.href} href={l.href} label={l.label} onClick={() => setOpen(false)} />
            ))}
          </nav>
          <div className="mt-3 flex flex-col gap-2 border-t border-line pt-3">
            {user ? (
              <button
                type="button"
                onClick={logout}
                className="rounded-lg border border-line-strong px-3 py-2 text-sm font-medium text-ink-soft"
              >
                Log out ({user.full_name.split(" ")[0]})
              </button>
            ) : (
              <>
                <Link
                  href="/login"
                  className="rounded-lg border border-line-strong px-3 py-2 text-center text-sm font-medium text-ink-soft"
                >
                  Log in
                </Link>
                <Link
                  href="/signup"
                  className="px-3 py-2 text-center rounded-lg bg-accent text-sm font-semibold text-accent-ink shadow-sm transition-colors hover:bg-accent-hover"
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
