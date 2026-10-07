import Link from "next/link";
import Image from "next/image";
import {
  ArrowRight,
  CalendarCheck,
  Ruler,
  ScanFace,
  Scissors,
  Sparkles,
} from "lucide-react";
import { BackendStatus } from "@/components/BackendStatus";

// Real icon components rather than emoji. The previous emoji set rendered
// inconsistently across platforms, and the mirror glyph showed as an empty box
// on Windows.
const FEATURES = [
  {
    Icon: Ruler,
    title: "Face-shape analysis",
    body: "Your face shape from bone-structure geometry, so it holds on bald and short hair. The ratios are shown.",
  },
  {
    Icon: Scissors,
    title: "Smart recommendations",
    body: "Flattering styles for your shape and preferences, each shown from four angles with a why-it-suits-you note.",
  },
  {
    Icon: Sparkles,
    title: "Virtual try-on",
    body: "See a style on your own photo: a fast 2D overlay, plus an optional photorealistic AI edit.",
  },
  {
    Icon: CalendarCheck,
    title: "Book a salon",
    body: "Find nearby salons, request a slot, and let the salon confirm. Email notifications go out both ways.",
  },
];

// Four visually distinct cuts from the catalogue, used as the hero visual.
// These are the same rendered images the recommendation results use, so the
// landing page shows the actual product rather than stock imagery.
const SHOWCASE = [
  { id: "burst-fade", name: "Burst Fade" },
  { id: "curtain-bangs-lob", name: "Curtain Bangs Lob" },
  { id: "wolf-cut", name: "Wolf Cut" },
  { id: "buzz-skin-fade", name: "Buzz Skin Fade" },
];

const STATS = [
  { value: "21", label: "curated cuts" },
  { value: "7", label: "face shapes" },
  { value: "4", label: "angles each" },
];

export default function Home() {
  return (
    <div className="flex flex-1 flex-col">
      {/* Hero: text on the left, product visual on the right. */}
      <section className="mx-auto w-full max-w-6xl px-6 pt-12 pb-12 sm:pt-20">
        <div className="grid items-center gap-12 lg:grid-cols-2 lg:gap-16">
          {/* Copy */}
          <div className="text-center lg:text-left">
            <span className="inline-flex items-center gap-1.5 rounded-full border border-line bg-accent-soft px-3 py-1 text-xs font-medium uppercase tracking-widest text-accent">
              <Sparkles className="h-3.5 w-3.5" aria-hidden />
              AI hairstyle &amp; salon booking
            </span>

            <h1 className="mt-5 text-4xl font-bold text-ink sm:text-5xl lg:text-6xl">
              See your next hairstyle{" "}
              <span className="text-accent">before the chair.</span>
            </h1>

            <p className="mt-5 max-w-xl text-lg leading-relaxed text-ink-soft lg:mx-0 mx-auto">
              CutPoint reads your face shape from bone structure, recommends cuts that actually
              suit it, lets you try them on your own photo, and books you into a nearby salon.
            </p>

            <div className="mt-8 flex flex-wrap items-center justify-center gap-3 lg:justify-start">
              <Link
                href="/analyze"
                className="inline-flex items-center gap-2 px-6 py-3 rounded-lg bg-accent text-sm font-semibold text-accent-ink shadow-md transition-colors hover:bg-accent-hover"
              >
                Analyse my face shape
                <ArrowRight className="h-4 w-4" aria-hidden />
              </Link>
              <Link
                href="/salons"
                className="rounded-lg border border-line-strong bg-surface-raised px-6 py-3 text-sm font-semibold text-ink-soft shadow-sm transition-colors hover:bg-surface-sunken hover:text-ink"
              >
                Find a salon
              </Link>
            </div>

            {/* Scale of the catalogue, stated plainly. */}
            <dl className="mt-8 flex items-center justify-center gap-8 lg:justify-start">
              {STATS.map((s) => (
                <div key={s.label}>
                  <dt className="sr-only">{s.label}</dt>
                  <dd>
                    <span className="font-display text-2xl font-bold text-ink">{s.value}</span>
                    <span className="ml-1.5 text-sm text-ink-faint">{s.label}</span>
                  </dd>
                </div>
              ))}
            </dl>

            <div className="mt-6 flex justify-center lg:justify-start">
              <BackendStatus />
            </div>
          </div>

          {/* Visual */}
          <div className="relative">
            {/* Soft accent wash behind the card, so it sits on the page rather
                than floating on flat white. */}
            <div
              aria-hidden
              className="absolute -inset-4 rounded-3xl bg-accent-soft/60 blur-2xl"
            />
            <div className="relative rounded-2xl border border-line bg-surface-raised p-5 shadow-lg">
              <div className="flex items-center justify-between">
                <span className="inline-flex items-center gap-1.5 text-xs font-medium text-ink-faint">
                  <ScanFace className="h-4 w-4 text-accent" aria-hidden />
                  Detected shape
                </span>
                <span className="rounded-full bg-accent-soft px-2.5 py-0.5 text-xs font-semibold text-accent">
                  Oval
                </span>
              </div>

              <div className="mt-4 grid grid-cols-2 gap-3">
                {SHOWCASE.map((s) => (
                  <figure
                    key={s.id}
                    className="overflow-hidden rounded-xl border border-line bg-surface-sunken"
                  >
                    <Image
                      src={`/assets/hair/${s.id}/front.webp`}
                      alt={s.name}
                      width={240}
                      height={240}
                      className="h-auto w-full"
                    />
                    <figcaption className="px-3 py-2 text-xs font-medium text-ink-soft">
                      {s.name}
                    </figcaption>
                  </figure>
                ))}
              </div>

              <p className="mt-4 text-center text-xs text-ink-faint">
                Four recommended cuts, shown front, left, right and back.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Features */}
      <section className="mx-auto w-full max-w-6xl px-6 pb-16">
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {FEATURES.map(({ Icon, title, body }) => (
            <div
              key={title}
              className="rounded-xl border border-line bg-surface-raised p-5 shadow-sm transition-shadow hover:shadow-md"
            >
              <span className="inline-flex h-10 w-10 items-center justify-center rounded-lg bg-accent-soft text-accent">
                <Icon className="h-5 w-5" aria-hidden />
              </span>
              <h2 className="mt-3 font-semibold text-ink">{title}</h2>
              <p className="mt-1 text-sm leading-relaxed text-ink-soft">{body}</p>
            </div>
          ))}
        </div>

        {/* Salon CTA */}
        <div className="mt-8 flex flex-col items-center justify-between gap-3 rounded-xl bg-ink px-6 py-5 text-center shadow-md sm:flex-row sm:text-left">
          <div>
            <p className="font-semibold text-surface-raised">Run a salon?</p>
            <p className="text-sm text-ink-faint">
              List your business and manage booking requests from your dashboard.
            </p>
          </div>
          <Link
            href="/signup/salon"
            className="shrink-0 px-5 py-2.5 rounded-lg bg-accent text-sm font-semibold text-accent-ink shadow-sm transition-colors hover:bg-accent-hover"
          >
            List your salon
          </Link>
        </div>
      </section>
    </div>
  );
}
