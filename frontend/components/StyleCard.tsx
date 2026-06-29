"use client";

import { useState } from "react";
import {
  type Angle,
  ANGLE_LABELS,
  RATIONALE_LABELS,
  type StyleRecommendation,
} from "@/lib/recommendTypes";

const ANGLES: Angle[] = ["front", "left", "right", "back"];

export function StyleCard({ style }: { style: StyleRecommendation }) {
  const [angle, setAngle] = useState<Angle>("front");
  const matchPct = Math.round(style.match_score * 100);

  return (
    <div className="flex flex-col overflow-hidden rounded-xl border border-zinc-200 bg-white dark:border-zinc-800 dark:bg-zinc-900">
      {/* Header */}
      <div className="flex items-start justify-between gap-2 px-4 pt-4">
        <h3 className="text-base font-semibold text-zinc-900 dark:text-zinc-50">
          {style.name}
        </h3>
        <span
          className="shrink-0 rounded-full bg-emerald-100 px-2 py-0.5 text-xs font-medium text-emerald-800 dark:bg-emerald-900/40 dark:text-emerald-300"
          title="How well this style matches your stated preferences"
        >
          {matchPct}% match
        </span>
      </div>

      {/* Multi-angle style preview */}
      <div className="mt-3 px-4">
        <div className="mb-1.5 flex items-center justify-between">
          <span className="text-[11px] font-medium uppercase tracking-wide text-zinc-400">
            Style preview · all angles
          </span>
          <span className="text-[11px] text-zinc-400">reference, not your photo</span>
        </div>
        <div className="flex items-center justify-center rounded-lg bg-zinc-50 py-2 dark:bg-zinc-800/50">
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img
            src={style.angle_assets[angle]}
            alt={`${style.name}, ${ANGLE_LABELS[angle]} view`}
            width={140}
            height={182}
            className="h-44 w-auto"
          />
        </div>
        <div className="mt-2 grid grid-cols-4 gap-1.5">
          {ANGLES.map((a) => (
            <button
              key={a}
              type="button"
              onClick={() => setAngle(a)}
              aria-pressed={a === angle}
              className={`rounded-md border px-2 py-1 text-xs font-medium transition-colors ${
                a === angle
                  ? "border-emerald-500 bg-emerald-50 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-300"
                  : "border-zinc-200 text-zinc-500 hover:bg-zinc-50 dark:border-zinc-700 dark:hover:bg-zinc-800"
              }`}
            >
              {ANGLE_LABELS[a]}
            </button>
          ))}
        </div>
      </div>

      {/* Explanation */}
      <p className="mt-3 px-4 text-sm leading-relaxed text-zinc-600 dark:text-zinc-300">
        {style.explanation}
      </p>

      {/* Rationale chips */}
      <div className="mt-3 flex flex-wrap gap-1.5 px-4">
        {style.rationale_tags.map((t) => (
          <span
            key={t}
            className="rounded-full bg-zinc-100 px-2 py-0.5 text-[11px] text-zinc-600 dark:bg-zinc-800 dark:text-zinc-300"
          >
            {RATIONALE_LABELS[t] ?? t}
          </span>
        ))}
      </div>

      {/* Meta footer */}
      <div className="mt-4 flex flex-wrap gap-x-4 gap-y-1 border-t border-zinc-100 px-4 py-3 text-xs text-zinc-500 dark:border-zinc-800">
        <span className="capitalize">Length: {style.length}</span>
        <span className="capitalize">Upkeep: {style.maintenance}</span>
        <span className="capitalize">Hair: {style.hair_types.join(", ")}</span>
      </div>
    </div>
  );
}
