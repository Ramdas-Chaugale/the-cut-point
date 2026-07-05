import Link from "next/link";
import { BackendStatus } from "@/components/BackendStatus";

const FEATURES = [
  {
    icon: "📐",
    title: "Face-shape analysis",
    body: "Your face shape from bone-structure geometry — works on bald and short hair, with the ratios shown.",
  },
  {
    icon: "💇",
    title: "Smart recommendations",
    body: "Flattering styles for your shape and preferences, each shown from four angles with a why-it-suits-you note.",
  },
  {
    icon: "🪞",
    title: "Virtual try-on",
    body: "See a style on your own photo — a fast 2D overlay, plus an optional photorealistic AI edit.",
  },
  {
    icon: "📅",
    title: "Book a salon",
    body: "Find nearby salons, request a slot, and let the salon confirm — with email notifications both ways.",
  },
];

export default function Home() {
  return (
    <div className="flex flex-1 flex-col">
      {/* Hero */}
      <section className="mx-auto w-full max-w-5xl px-6 pt-16 pb-10 text-center sm:pt-24">
        <span className="inline-block rounded-full border border-zinc-200 px-3 py-1 text-xs font-medium uppercase tracking-widest text-zinc-500 dark:border-zinc-800">
          AI hairstyle &amp; salon booking
        </span>
        <h1 className="mx-auto mt-5 max-w-3xl text-4xl font-semibold tracking-tight text-zinc-900 sm:text-6xl dark:text-zinc-50">
          See your next hairstyle before the chair.
        </h1>
        <p className="mx-auto mt-5 max-w-xl text-lg leading-relaxed text-zinc-600 dark:text-zinc-400">
          CutPoint reads your face shape, recommends styles that suit you, lets you try them on
          your own photo, and books you into a nearby salon.
        </p>
        <div className="mt-8 flex flex-wrap items-center justify-center gap-3">
          <Link
            href="/analyze"
            className="rounded-md bg-zinc-900 px-6 py-3 text-sm font-medium text-white transition-colors hover:bg-zinc-700 dark:bg-zinc-100 dark:text-zinc-900 dark:hover:bg-zinc-300"
          >
            Analyse my face shape →
          </Link>
          <Link
            href="/salons"
            className="rounded-md border border-zinc-300 px-6 py-3 text-sm font-medium text-zinc-700 transition-colors hover:bg-zinc-100 dark:border-zinc-700 dark:text-zinc-300 dark:hover:bg-zinc-800"
          >
            Find a salon
          </Link>
        </div>
        <div className="mt-6 flex justify-center">
          <BackendStatus />
        </div>
      </section>

      {/* Features */}
      <section className="mx-auto w-full max-w-5xl px-6 pb-16">
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          {FEATURES.map((f) => (
            <div
              key={f.title}
              className="rounded-xl border border-zinc-200 p-5 dark:border-zinc-800"
            >
              <div className="text-2xl" aria-hidden>
                {f.icon}
              </div>
              <h2 className="mt-2 font-semibold text-zinc-900 dark:text-zinc-50">{f.title}</h2>
              <p className="mt-1 text-sm leading-relaxed text-zinc-600 dark:text-zinc-400">
                {f.body}
              </p>
            </div>
          ))}
        </div>

        {/* Salon CTA */}
        <div className="mt-8 flex flex-col items-center justify-between gap-3 rounded-xl bg-zinc-900 px-6 py-5 text-center sm:flex-row sm:text-left dark:bg-zinc-100">
          <div>
            <p className="font-semibold text-white dark:text-zinc-900">Run a salon?</p>
            <p className="text-sm text-zinc-300 dark:text-zinc-600">
              List your business and manage booking requests from your dashboard.
            </p>
          </div>
          <Link
            href="/signup/salon"
            className="shrink-0 rounded-md bg-white px-5 py-2.5 text-sm font-medium text-zinc-900 hover:bg-zinc-200 dark:bg-zinc-900 dark:text-white dark:hover:bg-zinc-800"
          >
            List your salon
          </Link>
        </div>
      </section>
    </div>
  );
}
