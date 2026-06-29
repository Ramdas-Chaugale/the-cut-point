import Link from "next/link";
import { FaceAnalyzer } from "@/components/FaceAnalyzer";

export const metadata = {
  title: "Analyse your face shape — CutPoint",
};

export default function AnalyzePage() {
  return (
    <div className="mx-auto w-full max-w-5xl px-6 py-10">
      <Link
        href="/"
        className="text-sm text-zinc-500 hover:text-zinc-800 dark:hover:text-zinc-200"
      >
        ← Back
      </Link>

      <header className="mt-4 mb-8">
        <h1 className="text-2xl font-semibold tracking-tight text-zinc-900 dark:text-zinc-50">
          Face-shape analysis
        </h1>
        <p className="mt-1 max-w-prose text-sm text-zinc-600 dark:text-zinc-400">
          Upload or capture a front-facing photo. We measure your facial
          geometry from bone-structure landmarks — entirely in your browser —
          and classify your face shape. Nothing about your photo leaves your
          device except anonymous landmark coordinates.
        </p>
      </header>

      <FaceAnalyzer />
    </div>
  );
}
