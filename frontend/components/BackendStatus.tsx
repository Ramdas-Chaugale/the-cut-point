"use client";

import { useEffect, useState } from "react";
import { getHealth, type HealthResponse } from "@/lib/api";

type State =
  | { kind: "loading" }
  | { kind: "ok"; data: HealthResponse }
  | { kind: "error"; message: string };

/**
 * Live connectivity badge: pings the backend /health endpoint so the
 * Phase 0 hello-world actually proves the frontend <-> backend wire works.
 */
export function BackendStatus() {
  const [state, setState] = useState<State>({ kind: "loading" });

  useEffect(() => {
    let active = true;
    getHealth()
      .then((data) => active && setState({ kind: "ok", data }))
      .catch((err) =>
        active && setState({ kind: "error", message: err.message }),
      );
    return () => {
      active = false;
    };
  }, []);

  const dot =
    state.kind === "ok"
      ? "bg-emerald-500"
      : state.kind === "error"
        ? "bg-red-500"
        : "bg-amber-400 animate-pulse";

  return (
    <div className="inline-flex items-center gap-2 rounded-full border border-black/10 bg-white/60 px-3 py-1.5 text-sm dark:border-white/15 dark:bg-white/5">
      <span className={`h-2.5 w-2.5 rounded-full ${dot}`} aria-hidden />
      {state.kind === "loading" && <span>Connecting to API…</span>}
      {state.kind === "ok" && (
        <span>
          API online · v{state.data.version} · LLM{" "}
          {state.data.llm_enabled ? "enabled" : "fallback"}
        </span>
      )}
      {state.kind === "error" && (
        <span>API offline — {state.message}</span>
      )}
    </div>
  );
}
