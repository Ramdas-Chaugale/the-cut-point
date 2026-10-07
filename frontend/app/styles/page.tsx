import Link from "next/link";
import { ArrowRight, ScanFace } from "lucide-react";
import { StyleSearch } from "@/components/StyleSearch";
import { StylistChat } from "@/components/StylistChat";

export const metadata = {
  title: "Style catalogue · CutPoint",
  description:
    "Browse the hairstyle catalogue, search it in plain English, and ask a stylist assistant grounded in it.",
};

export default function StylesPage() {
  return (
    <div className="mx-auto w-full max-w-6xl px-4 py-10 sm:px-6">
      <header className="max-w-2xl">
        <h1 className="text-3xl font-bold text-ink sm:text-4xl">Style catalogue</h1>
        <p className="mt-2 text-lg leading-relaxed text-ink-soft">
          Every cut CutPoint knows, searchable in your own words. Describe what you are after
          and the catalogue is ranked against it, with the reasons shown.
        </p>
      </header>

      <div className="mt-8">
        <StyleSearch />
      </div>

      <div className="mt-10">
        <StylistChat />
      </div>

      {/* The catalogue is the browse path; face analysis is the guided one. */}
      <div className="mt-10 flex flex-col items-center justify-between gap-3 rounded-xl border border-line bg-surface-raised px-6 py-5 text-center shadow-sm sm:flex-row sm:text-left">
        <div className="flex items-center gap-3">
          <span className="grid h-10 w-10 shrink-0 place-items-center rounded-lg bg-accent-soft text-accent">
            <ScanFace className="h-5 w-5" aria-hidden />
          </span>
          <div>
            <p className="font-semibold text-ink">Want it narrowed down for you?</p>
            <p className="text-sm text-ink-soft">
              Analyse your face shape and get these ranked for your bone structure.
            </p>
          </div>
        </div>
        <Link
          href="/analyze"
          className="inline-flex shrink-0 items-center gap-2 px-5 py-2.5 rounded-lg bg-accent text-sm font-semibold text-accent-ink shadow-sm transition-colors hover:bg-accent-hover"
        >
          Analyse my face shape
          <ArrowRight className="h-4 w-4" aria-hidden />
        </Link>
      </div>
    </div>
  );
}
