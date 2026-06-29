"use client";

import {
  type AnalyzeResponse,
  type FaceShape,
  RATIO_LABELS,
} from "@/lib/faceTypes";

const SHAPE_LABEL: Record<FaceShape, string> = {
  oval: "Oval",
  round: "Round",
  square: "Square",
  oblong: "Oblong",
  heart: "Heart",
  diamond: "Diamond",
  triangle: "Triangle",
};

export function FaceResult({ result }: { result: AnalyzeResponse }) {
  const ranked = (Object.entries(result.scores) as [FaceShape, number][]).sort(
    (a, b) => b[1] - a[1],
  );
  const confidencePct = Math.round(result.confidence * 100);

  return (
    <div className="flex flex-col gap-6">
      {/* Headline result */}
      <div>
        <p className="text-sm uppercase tracking-widest text-zinc-500">
          Predicted face shape
        </p>
        <div className="mt-1 flex items-baseline gap-3">
          <h2 className="text-3xl font-semibold text-zinc-900 dark:text-zinc-50">
            {SHAPE_LABEL[result.shape]}
          </h2>
          <span className="rounded-full bg-emerald-100 px-2.5 py-0.5 text-sm font-medium text-emerald-800 dark:bg-emerald-900/40 dark:text-emerald-300">
            {confidencePct}% confidence
          </span>
        </div>
        <p className="mt-2 max-w-prose text-sm leading-relaxed text-zinc-600 dark:text-zinc-400">
          {result.description}
        </p>
      </div>

      {/* Warnings */}
      {result.quality.warnings.length > 0 && (
        <ul className="space-y-2">
          {result.quality.warnings.map((w) => (
            <li
              key={w}
              className="rounded-md border border-amber-300 bg-amber-50 px-3 py-2 text-sm text-amber-900 dark:border-amber-700/50 dark:bg-amber-950/40 dark:text-amber-200"
            >
              {w}
            </li>
          ))}
        </ul>
      )}

      {/* Score breakdown */}
      <div>
        <p className="mb-2 text-sm font-medium text-zinc-700 dark:text-zinc-300">
          How every shape scored
        </p>
        <ul className="space-y-1.5">
          {ranked.map(([shape, score]) => {
            const pct = Math.round(score * 100);
            const isTop = shape === result.shape;
            return (
              <li key={shape} className="flex items-center gap-3 text-sm">
                <span className="w-20 shrink-0 text-zinc-600 dark:text-zinc-400">
                  {SHAPE_LABEL[shape]}
                </span>
                <span className="relative h-2.5 flex-1 overflow-hidden rounded-full bg-zinc-200 dark:bg-zinc-800">
                  <span
                    className={`absolute inset-y-0 left-0 rounded-full ${
                      isTop ? "bg-emerald-500" : "bg-zinc-400 dark:bg-zinc-600"
                    }`}
                    style={{ width: `${Math.max(pct, 2)}%` }}
                  />
                </span>
                <span className="w-9 shrink-0 text-right tabular-nums text-zinc-500">
                  {pct}%
                </span>
              </li>
            );
          })}
        </ul>
      </div>

      {/* Measured ratios — transparency */}
      <div>
        <p className="mb-2 text-sm font-medium text-zinc-700 dark:text-zinc-300">
          Measured facial geometry
        </p>
        <dl className="grid grid-cols-2 gap-x-6 gap-y-2 text-sm sm:grid-cols-3">
          {(
            Object.keys(RATIO_LABELS) as (keyof AnalyzeResponse["ratios"])[]
          ).map((key) => (
            <div key={key} className="flex flex-col">
              <dt className="text-zinc-500">{RATIO_LABELS[key]}</dt>
              <dd className="font-mono text-zinc-800 dark:text-zinc-200">
                {result.ratios[key]}
              </dd>
            </div>
          ))}
        </dl>
        <p className="mt-3 text-xs text-zinc-400">
          Measured from facial bone-structure landmarks only (jaw, cheekbones,
          forehead, chin) — so the result is unaffected by hair, baldness, or a
          covered forehead.
        </p>
      </div>
    </div>
  );
}
