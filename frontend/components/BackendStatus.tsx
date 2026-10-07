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
      ? "bg-positive"
      : state.kind === "error"
        ? "bg-negative"
        : "bg-caution animate-pulse";

  return (
    <div className="inline-flex items-center gap-2 rounded-full border border-line bg-surface-raised/70 px-3 py-1.5 text-sm shadow-sm">
      <span className={`h-2.5 w-2.5 rounded-full ${dot}`} aria-hidden />
      {state.kind === "loading" && <span>Connecting to API…</span>}
      {state.kind === "ok" && (
        <span>
          API online · v{state.data.version} · LLM{" "}
          {state.data.llm_enabled ? "enabled" : "fallback"}
        </span>
      )}
      {state.kind === "error" && (
        <span>API offline. {state.message}</span>
      )}
    </div>
  );
}
