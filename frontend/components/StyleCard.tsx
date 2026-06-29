"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";
import { explainStyle } from "@/lib/api";
import { saveLook } from "@/lib/look";
import type { FaceShape } from "@/lib/faceTypes";
import {
  type Angle,
  ANGLE_LABELS,
  type ExplainRequest,
  RATIONALE_LABELS,
  type StyleRecommendation,
} from "@/lib/recommendTypes";

const ANGLES: Angle[] = ["front", "left", "right", "back"];

type Prefs = Omit<ExplainRequest, "style_id" | "face_shape">;

export function StyleCard({
  style,
  faceShape,
  prefs,
  llmEnabled,
  onTryOn,
}: {
  style: StyleRecommendation;
  faceShape: FaceShape;
  prefs: Prefs;
  llmEnabled: boolean;
  onTryOn: (style: StyleRecommendation) => void;
}) {
  const router = useRouter();
  const [angle, setAngle] = useState<Angle>("front");
  const [explanation, setExplanation] = useState(style.explanation);
  const [aiActive, setAiActive] = useState(false);
  const [aiLoading, setAiLoading] = useState(false);
  const [aiError, setAiError] = useState(false);
  const matchPct = Math.round(style.match_score * 100);

  const refineWithAi = async () => {
    setAiLoading(true);
    setAiError(false);
    try {
      const res = await explainStyle({
        style_id: style.id,
        face_shape: faceShape,
        ...prefs,
      });
      setExplanation(res.explanation);
      setAiActive(res.source === "llm");
      if (res.source !== "llm") setAiError(true); // fell back server-side
    } catch {
      setAiError(true);
    } finally {
      setAiLoading(false);
    }
  };

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
        <div className="mt-2.5 grid grid-cols-2 gap-2">
          <button
            type="button"
            onClick={() => onTryOn(style)}
            className="rounded-md bg-zinc-900 px-3 py-2 text-sm font-medium text-white transition-colors hover:bg-zinc-700 dark:bg-zinc-100 dark:text-zinc-900 dark:hover:bg-zinc-300"
          >
            Try this on
          </button>
          <button
            type="button"
            onClick={() => {
              saveLook({ id: style.id, name: style.name });
              router.push("/salons");
            }}
            className="rounded-md border border-zinc-300 px-3 py-2 text-sm font-medium text-zinc-700 transition-colors hover:bg-zinc-50 dark:border-zinc-700 dark:text-zinc-300 dark:hover:bg-zinc-800"
          >
            Book this look
          </button>
        </div>
      </div>

      {/* Explanation */}
      <div className="mt-3 px-4">
        <div className="mb-1 flex items-center gap-2">
          {aiActive && (
            <span className="rounded bg-violet-100 px-1.5 py-0.5 text-[10px] font-medium uppercase tracking-wide text-violet-700 dark:bg-violet-900/40 dark:text-violet-300">
              AI
            </span>
          )}
        </div>
        <p className="text-sm leading-relaxed text-zinc-600 dark:text-zinc-300">
          {explanation}
        </p>
        {llmEnabled && !aiActive && (
          <button
            type="button"
            onClick={refineWithAi}
            disabled={aiLoading}
            className="mt-2 inline-flex items-center gap-1.5 text-xs font-medium text-violet-600 hover:text-violet-500 disabled:opacity-60 dark:text-violet-400"
          >
            {aiLoading ? (
              <>
                <span className="h-3 w-3 animate-spin rounded-full border-2 border-violet-500 border-t-transparent" />
                Writing…
              </>
            ) : (
              <>✨ Refine with AI</>
            )}
          </button>
        )}
        {aiError && (
          <p className="mt-1 text-[11px] text-amber-600 dark:text-amber-400">
            AI is unavailable right now — showing the standard explanation.
          </p>
        )}
      </div>

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
