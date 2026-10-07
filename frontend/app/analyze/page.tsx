import Link from "next/link";
import { ArrowLeft } from "lucide-react";
import { AnalyzeWorkflow } from "@/components/AnalyzeWorkflow";

export const metadata = {
  title: "Analyse your face shape · CutPoint",
};

export default function AnalyzePage() {
  return (
    <div className="mx-auto w-full max-w-5xl px-6 py-10">
      <Link
        href="/"
        className="inline-flex items-center gap-1.5 text-sm text-ink-faint transition-colors hover:text-ink"
      >
        <ArrowLeft className="h-4 w-4" aria-hidden />
        Back
      </Link>

      <header className="mt-6 mb-10">
        <h1 className="text-3xl font-bold text-ink sm:text-4xl">
          Face-shape analysis
        </h1>
        <p className="mt-3 max-w-2xl text-lg leading-relaxed text-ink-soft">
          Upload or take a front-facing photo. Your face shape is measured from
          bone-structure landmarks, which is why it works on bald and
          short-haired faces where hair-based guesses fail.
        </p>
        <p className="mt-2 max-w-2xl text-sm text-ink-faint">
          All of it runs in your browser. The photo never leaves your device.
        </p>
      </header>

      <AnalyzeWorkflow />
    </div>
  );
}
