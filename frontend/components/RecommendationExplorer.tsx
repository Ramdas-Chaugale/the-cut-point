"use client";

import { useCallback, useEffect, useState } from "react";
import { getHealth, recommend } from "@/lib/api";
import type { FaceShape } from "@/lib/faceTypes";
import type {
  HairType,
  Length,
  Maintenance,
  Presentation,
  StyleRecommendation,
} from "@/lib/recommendTypes";
import { StyleCard } from "./StyleCard";

interface Prefs {
  presentation: Presentation | "";
  desired_length: Length | "";
  hair_type: HairType | "";
  maintenance: Maintenance | "";
}

const EMPTY: Prefs = { presentation: "", desired_length: "", hair_type: "", maintenance: "" };

function Select<T extends string>({
  label,
  value,
  onChange,
  options,
}: {
  label: string;
  value: string;
  onChange: (v: T | "") => void;
  options: { value: T; label: string }[];
}) {
  return (
    <label className="flex flex-col gap-1 text-sm">
      <span className="text-zinc-500">{label}</span>
      <select
        value={value}
        onChange={(e) => onChange(e.target.value as T | "")}
        className="rounded-md border border-zinc-300 bg-white px-2.5 py-1.5 text-sm text-zinc-800 focus:border-emerald-500 focus:outline-none dark:border-zinc-700 dark:bg-zinc-900 dark:text-zinc-100"
      >
        <option value="">No preference</option>
        {options.map((o) => (
          <option key={o.value} value={o.value}>
            {o.label}
          </option>
        ))}
      </select>
    </label>
  );
}

export function RecommendationExplorer({
  faceShape,
  onTryOn,
}: {
  faceShape: FaceShape;
  onTryOn: (style: StyleRecommendation) => void;
}) {
  const [prefs, setPrefs] = useState<Prefs>(EMPTY);
  const [items, setItems] = useState<StyleRecommendation[]>([]);
  const [status, setStatus] = useState<"loading" | "ready" | "error">("loading");
  const [error, setError] = useState("");
  const [llmEnabled, setLlmEnabled] = useState(false);

  // Detect whether the backend has an LLM key, to decide if we offer AI refine.
  useEffect(() => {
    let active = true;
    getHealth()
      .then((h) => active && setLlmEnabled(h.llm_enabled))
      .catch(() => {});
    return () => {
      active = false;
    };
  }, []);

  const cleanPrefs = {
    presentation: prefs.presentation || undefined,
    desired_length: prefs.desired_length || undefined,
    hair_type: prefs.hair_type || undefined,
    maintenance: prefs.maintenance || undefined,
  };

  const fetchRecs = useCallback(async () => {
    // Status is set to "loading" by the caller (mount = initial state, or a
    // preference-change handler) so we never setState synchronously in effect.
    try {
      const res = await recommend({
        face_shape: faceShape,
        presentation: prefs.presentation || undefined,
        desired_length: prefs.desired_length || undefined,
        hair_type: prefs.hair_type || undefined,
        maintenance: prefs.maintenance || undefined,
        limit: 8,
      });
      setItems(res.recommendations);
      setStatus("ready");
    } catch (err) {
      setError((err as Error).message);
      setStatus("error");
    }
  }, [faceShape, prefs]);

  useEffect(() => {
    // Auto-fetch on mount and whenever the face shape / preferences change.
    void fetchRecs();
  }, [fetchRecs]);

  // Update a preference and show the loading state immediately (in an event,
  // not an effect).
  const updatePref = (patch: Partial<Prefs>) => {
    setStatus("loading");
    setPrefs((p) => ({ ...p, ...patch }));
  };

  return (
    <section className="mt-12">
      <h2 className="text-xl font-semibold tracking-tight text-zinc-900 dark:text-zinc-50">
        Recommended hairstyles
      </h2>
      <p className="mt-1 text-sm text-zinc-500">
        Ranked for your{" "}
        <span className="font-medium text-zinc-700 dark:text-zinc-300">{faceShape}</span>{" "}
        face shape. Refine with your preferences below.
      </p>

      {/* Preference controls */}
      <div className="mt-4 grid grid-cols-2 gap-3 sm:grid-cols-4">
        <Select
          label="Style"
          value={prefs.presentation}
          onChange={(v) => updatePref({ presentation: v })}
          options={[
            { value: "masculine", label: "Masculine" },
            { value: "feminine", label: "Feminine" },
            { value: "unisex", label: "Unisex" },
          ]}
        />
        <Select
          label="Length"
          value={prefs.desired_length}
          onChange={(v) => updatePref({ desired_length: v })}
          options={[
            { value: "short", label: "Short" },
            { value: "medium", label: "Medium" },
            { value: "long", label: "Long" },
          ]}
        />
        <Select
          label="Hair type"
          value={prefs.hair_type}
          onChange={(v) => updatePref({ hair_type: v })}
          options={[
            { value: "straight", label: "Straight" },
            { value: "wavy", label: "Wavy" },
            { value: "curly", label: "Curly" },
            { value: "coily", label: "Coily" },
          ]}
        />
        <Select
          label="Maintenance"
          value={prefs.maintenance}
          onChange={(v) => updatePref({ maintenance: v })}
          options={[
            { value: "low", label: "Low" },
            { value: "medium", label: "Medium" },
            { value: "high", label: "High" },
          ]}
        />
      </div>

      {/* Results */}
      <div className="mt-6">
        {status === "error" && (
          <div className="rounded-lg border border-red-300 bg-red-50 px-4 py-3 text-sm text-red-800 dark:border-red-800/50 dark:bg-red-950/40 dark:text-red-200">
            Could not load recommendations — {error}
          </div>
        )}
        {status === "loading" && (
          <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-3">
            {Array.from({ length: 3 }).map((_, i) => (
              <div
                key={i}
                className="h-96 animate-pulse rounded-xl border border-zinc-200 bg-zinc-50 dark:border-zinc-800 dark:bg-zinc-900"
              />
            ))}
          </div>
        )}
        {status === "ready" && items.length === 0 && (
          <p className="text-sm text-zinc-500">
            No styles match those exact preferences. Try relaxing one of them.
          </p>
        )}
        {status === "ready" && items.length > 0 && (
          <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-3">
            {items.map((style) => (
              <StyleCard
                key={style.id}
                style={style}
                faceShape={faceShape}
                prefs={cleanPrefs}
                llmEnabled={llmEnabled}
                onTryOn={onTryOn}
              />
            ))}
          </div>
        )}
      </div>
    </section>
  );
}
