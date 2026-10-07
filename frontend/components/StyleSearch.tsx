"use client";

import Image from "next/image";
import { useCallback, useEffect, useState } from "react";
import { Loader2, Search, Sparkles, X } from "lucide-react";
import { listStyles, searchStyles } from "@/lib/api";
import type { ParsedQuery, SearchHit } from "@/lib/searchTypes";

// Starter queries, chosen to show what the parser can pull out of ordinary
// phrasing rather than to flatter it.
const EXAMPLES = [
  "low maintenance and works with curls",
  "something soft that lengthens a round face",
  "sharp barbershop cut, nothing to style in the morning",
  "long layers I can still tie up",
];

function Badge({ children, tone = "neutral" }: { children: React.ReactNode; tone?: "neutral" | "ai" }) {
  const styles =
    tone === "ai"
      ? "border-ai-line bg-ai-soft text-ai"
      : "border-line bg-surface-sunken text-ink-soft";
  return (
    <span className={`inline-flex items-center gap-1 rounded-full border px-2 py-0.5 text-xs font-medium ${styles}`}>
      {children}
    </span>
  );
}

function StyleTile({ hit }: { hit: SearchHit }) {
  return (
    <article className="flex flex-col overflow-hidden rounded-xl border border-line bg-surface-raised shadow-sm transition-shadow hover:shadow-md">
      <div className="bg-surface-sunken">
        <Image
          src={hit.angle_assets.front}
          alt={hit.name}
          width={240}
          height={240}
          className="mx-auto h-auto w-full max-w-[180px]"
        />
      </div>
      <div className="flex flex-1 flex-col px-4 py-3.5">
        <h3 className="font-semibold text-ink">{hit.name}</h3>
        <p className="mt-1 line-clamp-2 text-sm leading-relaxed text-ink-soft">{hit.description}</p>
        <div className="mt-3 flex flex-wrap gap-1.5">
          <Badge>{hit.length}</Badge>
          <Badge>{hit.maintenance} upkeep</Badge>
        </div>
        {hit.reasons.length > 0 && (
          // Why this result is here, in the same words the query used.
          <ul className="mt-3 space-y-1 border-t border-line pt-2.5">
            {hit.reasons.map((r) => (
              <li key={r} className="flex items-start gap-1.5 text-xs text-ink-faint">
                <span className="mt-1.5 h-1 w-1 shrink-0 rounded-full bg-accent" aria-hidden />
                {r}
              </li>
            ))}
          </ul>
        )}
      </div>
    </article>
  );
}

function Understood({ parsed }: { parsed: ParsedQuery }) {
  if (parsed.summary.length === 0) {
    return (
      <p className="text-sm text-ink-faint">
        No specific requirements were picked out, so these are ranked on wording alone.
      </p>
    );
  }
  return (
    <div className="flex flex-wrap items-center gap-2">
      <span className="text-sm text-ink-faint">Understood as</span>
      {parsed.summary.map((s) => (
        <Badge key={s}>{s}</Badge>
      ))}
      {parsed.source === "llm" && (
        <Badge tone="ai">
          <Sparkles className="h-3 w-3" aria-hidden />
          AI parsed
        </Badge>
      )}
    </div>
  );
}

export function StyleSearch() {
  const [query, setQuery] = useState("");
  const [catalogue, setCatalogue] = useState<SearchHit[] | null>(null);
  const [results, setResults] = useState<SearchHit[] | null>(null);
  const [parsed, setParsed] = useState<ParsedQuery | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  // The full catalogue is what you see before searching anything.
  useEffect(() => {
    let active = true;
    listStyles()
      .then((s) => active && setCatalogue(s))
      .catch((e) => active && setError((e as Error).message));
    return () => {
      active = false;
    };
  }, []);

  const run = useCallback(async (q: string) => {
    const trimmed = q.trim();
    if (trimmed.length < 2) return;
    setBusy(true);
    setError("");
    try {
      const body = await searchStyles({ query: trimmed, limit: 12 });
      setResults(body.results);
      setParsed(body.parsed);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }, []);

  const clear = () => {
    setQuery("");
    setResults(null);
    setParsed(null);
    setError("");
  };

  const shown = results ?? catalogue;

  return (
    <section>
      <form
        onSubmit={(e) => {
          e.preventDefault();
          void run(query);
        }}
        className="rounded-2xl border border-line bg-surface-raised p-4 shadow-sm sm:p-5"
      >
        <label htmlFor="style-search" className="text-sm font-medium text-ink">
          Describe the cut you want
        </label>
        <div className="mt-2 flex flex-col gap-2 sm:flex-row">
          <div className="relative flex-1">
            <Search
              className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-ink-faint"
              aria-hidden
            />
            <input
              id="style-search"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="something low maintenance that works with curly hair"
              className="w-full rounded-lg border border-line-strong bg-surface py-2.5 pl-9 pr-9 text-sm text-ink placeholder:text-ink-faint transition-colors focus:border-accent focus:outline-none focus:ring-2 focus:ring-accent/20"
            />
            {query && (
              <button
                type="button"
                onClick={clear}
                aria-label="Clear search"
                className="absolute right-2 top-1/2 grid h-6 w-6 -translate-y-1/2 place-items-center rounded-full text-ink-faint transition-colors hover:bg-surface-sunken hover:text-ink"
              >
                <X className="h-3.5 w-3.5" aria-hidden />
              </button>
            )}
          </div>
          <button
            type="submit"
            disabled={busy || query.trim().length < 2}
            className="inline-flex shrink-0 items-center justify-center gap-2 px-5 py-2.5 disabled:opacity-50 rounded-lg bg-accent text-sm font-semibold text-accent-ink shadow-sm transition-colors hover:bg-accent-hover"
          >
            {busy ? (
              <Loader2 className="h-4 w-4 animate-spin" aria-hidden />
            ) : (
              <Sparkles className="h-4 w-4" aria-hidden />
            )}
            {busy ? "Searching" : "Search"}
          </button>
        </div>

        <div className="mt-3 flex flex-wrap gap-1.5">
          {EXAMPLES.map((e) => (
            <button
              key={e}
              type="button"
              onClick={() => {
                setQuery(e);
                void run(e);
              }}
              className="rounded-full border border-line px-2.5 py-1 text-xs text-ink-soft transition-colors hover:border-accent hover:text-accent"
            >
              {e}
            </button>
          ))}
        </div>
      </form>

      {error && (
        <div className="mt-4 rounded-lg border border-negative-line bg-negative-soft px-4 py-3 text-sm text-negative">
          {error}
        </div>
      )}

      <div className="mt-6 flex flex-wrap items-center justify-between gap-3">
        <h2 className="text-lg font-semibold text-ink">
          {results ? `${results.length} matches` : "All styles"}
          {!results && catalogue && (
            <span className="ml-2 text-sm font-normal text-ink-faint">{catalogue.length} in the catalogue</span>
          )}
        </h2>
        {results && (
          <button
            type="button"
            onClick={clear}
            className="text-sm font-medium text-accent hover:underline"
          >
            Show all styles
          </button>
        )}
      </div>

      {parsed && <div className="mt-2">{<Understood parsed={parsed} />}</div>}

      {shown === null ? (
        <div className="mt-5 grid grid-cols-2 gap-4 lg:grid-cols-4">
          {Array.from({ length: 8 }).map((_, i) => (
            <div key={i} className="h-64 animate-pulse rounded-xl border border-line bg-surface-sunken" />
          ))}
        </div>
      ) : shown.length === 0 ? (
        <p className="mt-5 rounded-lg border border-dashed border-line-strong px-4 py-10 text-center text-sm text-ink-faint">
          Nothing matched that. Try describing the length or the upkeep you want.
        </p>
      ) : (
        <div className="mt-5 grid grid-cols-2 gap-4 lg:grid-cols-4">
          {shown.map((hit) => (
            <StyleTile key={hit.id} hit={hit} />
          ))}
        </div>
      )}
    </section>
  );
}
