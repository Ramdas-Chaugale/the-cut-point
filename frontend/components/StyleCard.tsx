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
    <div className="flex flex-col overflow-hidden rounded-xl border border-line bg-surface-raised">
      {/* Header */}
      <div className="flex items-start justify-between gap-2 px-4 pt-4">
        <h3 className="text-base font-semibold text-ink">
          {style.name}
        </h3>
        <span
          className="shrink-0 rounded-full bg-accent-soft px-2 py-0.5 text-xs font-medium text-accent"
          title="How well this style matches your stated preferences"
        >
          {matchPct}% match
        </span>
      </div>

      {/* Multi-angle style preview */}
      <div className="mt-3 px-4">
        <div className="mb-1.5 flex items-center justify-between">
          <span className="text-[11px] font-medium uppercase tracking-wide text-ink-faint">
            Style preview · all angles
          </span>
          <span className="text-[11px] text-ink-faint">reference, not your photo</span>
        </div>
        <div className="flex items-center justify-center rounded-lg bg-surface-sunken py-2">
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
              className={`rounded-lg border px-2 py-1 text-xs font-medium transition-colors ${
                a === angle
                  ? "border-accent bg-accent-soft text-accent"
                  : "border-line text-ink-faint hover:bg-surface-sunken"
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
            className="px-3 py-2 rounded-lg bg-accent text-sm font-semibold text-accent-ink shadow-sm transition-colors hover:bg-accent-hover"
          >
            Try this on
          </button>
          <button
            type="button"
            onClick={() => {
              saveLook({ id: style.id, name: style.name });
              router.push("/salons");
            }}
            className="rounded-lg border border-line-strong px-3 py-2 text-sm font-medium text-ink-soft transition-colors hover:bg-surface-sunken"
          >
            Book this look
          </button>
        </div>
      </div>

      {/* Explanation */}
      <div className="mt-3 px-4">
        <div className="mb-1 flex items-center gap-2">
          {aiActive && (
            <span className="rounded bg-ai-soft px-1.5 py-0.5 text-[10px] font-medium uppercase tracking-wide text-ai">
              AI
            </span>
          )}
        </div>
        <p className="text-sm leading-relaxed text-ink-soft">
          {explanation}
        </p>
        {llmEnabled && !aiActive && (
          <button
            type="button"
            onClick={refineWithAi}
            disabled={aiLoading}
            className="mt-2 inline-flex items-center gap-1.5 text-xs font-medium text-ai hover:text-ai-hover disabled:opacity-60"
          >
            {aiLoading ? (
              <>
                <span className="h-3 w-3 animate-spin rounded-full border-2 border-ai border-t-transparent" />
                Writing…
              </>
            ) : (
              <>✨ Refine with AI</>
            )}
          </button>
        )}
        {aiError && (
          <p className="mt-1 text-[11px] text-caution">
            AI is unavailable right now, so this is the standard explanation.
          </p>
        )}
      </div>

      {/* Rationale chips */}
      <div className="mt-3 flex flex-wrap gap-1.5 px-4">
        {style.rationale_tags.map((t) => (
          <span
            key={t}
            className="rounded-full bg-surface-sunken px-2 py-0.5 text-[11px] text-ink-soft"
          >
            {RATIONALE_LABELS[t] ?? t}
          </span>
        ))}
      </div>

      {/* Meta footer */}
      <div className="mt-4 flex flex-wrap gap-x-4 gap-y-1 border-t border-line px-4 py-3 text-xs text-ink-faint">
        <span className="capitalize">Length: {style.length}</span>
        <span className="capitalize">Upkeep: {style.maintenance}</span>
        <span className="capitalize">Hair: {style.hair_types.join(", ")}</span>
      </div>
    </div>
  );
}
