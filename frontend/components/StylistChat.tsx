"use client";

import { useState } from "react";
import { Bot, BookOpen, Loader2, Send, Sparkles } from "lucide-react";
import { askStylist } from "@/lib/api";
import type { AssistantResponse } from "@/lib/searchTypes";
import type { FaceShape } from "@/lib/faceTypes";

const PROMPTS = [
  "Is a wolf cut hard to look after?",
  "What works with coily hair and a square jaw?",
  "I want something I can grow out. Ideas?",
];

/**
 * A question box answered from the hairstyle catalogue.
 *
 * The styles the answer drew on are listed underneath it. That is the point of
 * the panel: an ungrounded model will confidently describe a haircut the salon
 * does not offer, and showing the sources makes that visible rather than
 * asking the reader to take the answer on trust.
 */
export function StylistChat({ faceShape }: { faceShape?: FaceShape }) {
  const [question, setQuestion] = useState("");
  const [answer, setAnswer] = useState<AssistantResponse | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  const ask = async (q: string) => {
    const trimmed = q.trim();
    if (trimmed.length < 2) return;
    setBusy(true);
    setError("");
    try {
      setAnswer(await askStylist({ question: trimmed, face_shape: faceShape }));
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  };

  return (
    <section className="rounded-2xl border border-ai-line bg-ai-soft p-5 sm:p-6">
      <div className="flex items-center gap-2.5">
        <span className="grid h-9 w-9 place-items-center rounded-xl bg-ai text-ai-ink">
          <Bot className="h-4.5 w-4.5" aria-hidden />
        </span>
        <div>
          <h2 className="font-semibold text-ink">Ask the stylist</h2>
          <p className="text-xs text-ink-soft">
            Answers come from the style catalogue, and cite what they used.
          </p>
        </div>
      </div>

      <form
        onSubmit={(e) => {
          e.preventDefault();
          void ask(question);
        }}
        className="mt-4 flex flex-col gap-2 sm:flex-row"
      >
        <input
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          placeholder="Will a bob work with curly hair?"
          aria-label="Your question"
          className="flex-1 rounded-lg border border-line-strong bg-surface-raised px-3 py-2.5 text-sm text-ink placeholder:text-ink-faint transition-colors focus:border-ai focus:outline-none focus:ring-2 focus:ring-ai/20"
        />
        <button
          type="submit"
          disabled={busy || question.trim().length < 2}
          className="inline-flex shrink-0 items-center justify-center gap-2 rounded-lg bg-ai px-5 py-2.5 text-sm font-semibold text-ai-ink shadow-sm transition-colors hover:bg-ai-hover disabled:opacity-50"
        >
          {busy ? (
            <Loader2 className="h-4 w-4 animate-spin" aria-hidden />
          ) : (
            <Send className="h-4 w-4" aria-hidden />
          )}
          {busy ? "Thinking" : "Ask"}
        </button>
      </form>

      {!answer && !busy && (
        <div className="mt-3 flex flex-wrap gap-1.5">
          {PROMPTS.map((p) => (
            <button
              key={p}
              type="button"
              onClick={() => {
                setQuestion(p);
                void ask(p);
              }}
              className="rounded-full border border-ai-line bg-surface-raised px-2.5 py-1 text-xs text-ink-soft transition-colors hover:border-ai hover:text-ai"
            >
              {p}
            </button>
          ))}
        </div>
      )}

      {error && (
        <p className="mt-4 rounded-lg border border-negative-line bg-negative-soft px-3 py-2 text-sm text-negative">
          {error}
        </p>
      )}

      {answer && (
        <div className="mt-4 rounded-xl border border-ai-line bg-surface-raised p-4">
          <p className="text-sm leading-relaxed text-ink">{answer.answer}</p>

          <div className="mt-3 border-t border-line pt-3">
            <p className="flex items-center gap-1.5 text-xs font-medium text-ink-faint">
              <BookOpen className="h-3.5 w-3.5" aria-hidden />
              Based on these catalogue entries
            </p>
            <ul className="mt-2 flex flex-wrap gap-1.5">
              {answer.sources.map((s) => (
                <li
                  key={s.id}
                  title={s.description}
                  className="rounded-full border border-line bg-surface-sunken px-2.5 py-0.5 text-xs font-medium text-ink-soft"
                >
                  {s.name}
                </li>
              ))}
            </ul>
            {answer.source === "fallback" && (
              // Worth saying plainly: the answer is still correct, it is just
              // assembled from the catalogue rather than written by a model.
              <p className="mt-2.5 text-xs text-ink-faint">
                Written from the catalogue directly, without the language model.
              </p>
            )}
            {answer.source === "llm" && (
              <p className="mt-2.5 inline-flex items-center gap-1 text-xs text-ai">
                <Sparkles className="h-3 w-3" aria-hidden />
                Written by the language model, grounded in the entries above.
              </p>
            )}
          </div>
        </div>
      )}
    </section>
  );
}
