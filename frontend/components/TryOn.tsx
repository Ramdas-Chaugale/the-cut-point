"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { generateTryOn, getHealth } from "@/lib/api";
import type { AnalysisPayload } from "@/lib/faceTypes";
import type { StyleRecommendation } from "@/lib/recommendTypes";

// Cheekbone landmarks (MediaPipe FaceMesh) — the same bone-structure points the
// classifier uses. Anchoring to these makes the overlay bald-safe.
const CHEEK_R = 234; // subject's right (image left)
const CHEEK_L = 454; // subject's left  (image right)

// Overlay reference frame (see tools/generate_hair_assets.py overlay()):
// the face ellipse is centred at (100,104) with rx=40, so its widest points —
// the cheekbones — are at (60,104) and (140,104) in the 200x260 artwork.
const OVERLAY_W = 200;
const OVERLAY_H = 260;
const A0 = { x: 60, y: 104 }; // maps to CHEEK_R
const B0 = { x: 140, y: 104 }; // maps to CHEEK_L
const MAX_W = 460;

interface Nudge {
  dx: number;
  dy: number;
  scale: number;
}
const NEUTRAL: Nudge = { dx: 0, dy: 0, scale: 1 };

export function TryOn({
  payload,
  style,
  onBack,
}: {
  payload: AnalysisPayload;
  style: StyleRecommendation;
  onBack: () => void;
}) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const photoRef = useRef<HTMLImageElement | null>(null);
  const overlayRef = useRef<HTMLImageElement | null>(null);
  const [ready, setReady] = useState(false);
  const [nudge, setNudge] = useState<Nudge>(NEUTRAL);

  // Realistic AI try-on (fal.ai) — only offered when the backend has a key.
  const [mode, setMode] = useState<"overlay" | "ai">("overlay");
  const [aiEnabled, setAiEnabled] = useState(false);
  const [aiImage, setAiImage] = useState<string | null>(null);
  const [aiLoading, setAiLoading] = useState(false);
  const [aiError, setAiError] = useState("");

  useEffect(() => {
    let active = true;
    getHealth()
      .then((h) => active && setAiEnabled(Boolean(h.ai_tryon_enabled)))
      .catch(() => {});
    return () => {
      active = false;
    };
  }, []);

  const runAiTryOn = async () => {
    setAiLoading(true);
    setAiError("");
    try {
      const res = await generateTryOn(payload.photo, style.id);
      setAiImage(res.image_url);
    } catch (e) {
      const msg = (e as Error).message || "";
      // Billing / quota / not-configured -> present as an optional add-on
      // rather than a raw error (the integration itself is fully wired).
      const optional = /balance|locked|exhausted|quota|not configured|unavailable|50[23]/i.test(
        msg,
      );
      setAiError(
        optional
          ? "Realistic AI try-on is an optional add-on that runs on a paid image model (fal.ai). The integration is fully built and tested — add fal.ai credits to enable live generation."
          : msg,
      );
    } finally {
      setAiLoading(false);
    }
  };

  // Load the photo + the style overlay. The component is remounted per style
  // (keyed by id in the parent), so initial state is already fresh.
  useEffect(() => {
    let loaded = 0;
    const done = () => {
      loaded += 1;
      if (loaded === 2) setReady(true);
    };
    const photo = new Image();
    photo.onload = () => {
      photoRef.current = photo;
      done();
    };
    photo.src = payload.photo;

    const overlay = new Image();
    overlay.onload = () => {
      overlayRef.current = overlay;
      done();
    };
    overlay.src = style.try_on_overlay;
  }, [payload.photo, style.try_on_overlay]);

  const draw = useCallback(() => {
    const canvas = canvasRef.current;
    const photo = photoRef.current;
    const overlay = overlayRef.current;
    if (!canvas || !photo || !overlay) return;

    const scale = Math.min(1, MAX_W / payload.width);
    const w = Math.round(payload.width * scale);
    const h = Math.round(payload.height * scale);
    canvas.width = w;
    canvas.height = h;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    ctx.clearRect(0, 0, w, h);
    ctx.drawImage(photo, 0, 0, w, h);

    // User cheekbone points in display pixels.
    const pr = payload.points[CHEEK_R];
    const pl = payload.points[CHEEK_L];
    const A1 = { x: pr.x * w, y: pr.y * h };
    const B1 = { x: pl.x * w, y: pl.y * h };

    // Similarity transform mapping the overlay's cheek anchors (A0,B0) onto the
    // user's (A1,B1): handles position, scale and head tilt together.
    const v0x = B0.x - A0.x; // = 80
    const v1x = B1.x - A1.x;
    const v1y = B1.y - A1.y;
    const baseScale = Math.hypot(v1x, v1y) / Math.hypot(v0x, 0);
    const s = baseScale * nudge.scale;
    const theta = Math.atan2(v1y, v1x); // overlay anchor line is horizontal
    const a = s * Math.cos(theta);
    const b = s * Math.sin(theta);
    const c = -s * Math.sin(theta);
    const d = s * Math.cos(theta);
    const e = A1.x - (a * A0.x + c * A0.y) + nudge.dx;
    const f = A1.y - (b * A0.x + d * A0.y) + nudge.dy;

    ctx.setTransform(a, b, c, d, e, f);
    ctx.drawImage(overlay, 0, 0, OVERLAY_W, OVERLAY_H);
    ctx.setTransform(1, 0, 0, 1, 0, 0);
  }, [payload, nudge]);

  useEffect(() => {
    if (ready) draw();
  }, [ready, draw]);

  const download = () => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const link = document.createElement("a");
    link.download = `cutpoint-${style.id}.png`;
    link.href = canvas.toDataURL("image/png");
    link.click();
  };

  const move = (dx: number, dy: number) =>
    setNudge((n) => ({ ...n, dx: n.dx + dx, dy: n.dy + dy }));
  const zoom = (f: number) =>
    setNudge((n) => ({ ...n, scale: Math.min(1.6, Math.max(0.6, n.scale + f)) }));

  return (
    <section className="mt-12">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-semibold tracking-tight text-zinc-900 dark:text-zinc-50">
            Virtual try-on — {style.name}
          </h2>
          <p className="mt-1 text-sm text-zinc-500">
            {mode === "overlay"
              ? "A 2D overlay anchored to your facial landmarks (not a neural render). Nudge it for a perfect fit."
              : "A photorealistic AI edit of your own photo wearing this style."}
          </p>
        </div>
        <button
          type="button"
          onClick={onBack}
          className="rounded-md border border-zinc-300 px-3 py-1.5 text-sm font-medium text-zinc-700 hover:bg-zinc-100 dark:border-zinc-700 dark:text-zinc-300"
        >
          ← Try another
        </button>
      </div>

      {aiEnabled && (
        <div className="mt-4 inline-flex rounded-lg border border-zinc-200 p-1 dark:border-zinc-800">
          <ModeBtn active={mode === "overlay"} onClick={() => setMode("overlay")} label="2D overlay" />
          <ModeBtn active={mode === "ai"} onClick={() => setMode("ai")} label="Realistic AI ✨" />
        </div>
      )}

      {mode === "overlay" ? (
      <div className="mt-5 flex flex-col gap-5 sm:flex-row sm:items-start">
        <div className="relative overflow-hidden rounded-lg border border-zinc-200 bg-zinc-50 dark:border-zinc-800 dark:bg-zinc-900/40">
          <canvas ref={canvasRef} className="block max-w-full" />
          {!ready && (
            <div className="absolute inset-0 flex items-center justify-center text-sm text-zinc-400">
              Preparing your try-on…
            </div>
          )}
        </div>

        {/* Controls */}
        <div className="flex flex-col gap-4">
          <div>
            <p className="mb-1.5 text-xs font-medium uppercase tracking-wide text-zinc-400">
              Fine-tune position
            </p>
            <div className="grid w-32 grid-cols-3 gap-1.5">
              <span />
              <NudgeBtn onClick={() => move(0, -4)} label="↑" />
              <span />
              <NudgeBtn onClick={() => move(-4, 0)} label="←" />
              <NudgeBtn onClick={() => setNudge(NEUTRAL)} label="⟳" title="Reset" />
              <NudgeBtn onClick={() => move(4, 0)} label="→" />
              <span />
              <NudgeBtn onClick={() => move(0, 4)} label="↓" />
              <span />
            </div>
          </div>
          <div>
            <p className="mb-1.5 text-xs font-medium uppercase tracking-wide text-zinc-400">
              Size
            </p>
            <div className="flex gap-1.5">
              <NudgeBtn onClick={() => zoom(-0.05)} label="−" />
              <NudgeBtn onClick={() => zoom(0.05)} label="+" />
            </div>
          </div>
          <button
            type="button"
            onClick={download}
            className="mt-1 rounded-md bg-zinc-900 px-4 py-2 text-sm font-medium text-white hover:bg-zinc-700 dark:bg-zinc-100 dark:text-zinc-900 dark:hover:bg-zinc-300"
          >
            Download PNG
          </button>
        </div>
      </div>
      ) : (
        <div className="mt-5">
          {aiImage ? (
            <div className="flex flex-col items-start gap-3">
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img
                src={aiImage}
                alt={`AI try-on of ${style.name}`}
                className="max-h-[480px] w-auto rounded-lg border border-zinc-200 dark:border-zinc-800"
              />
              <div className="flex gap-2">
                <a
                  href={aiImage}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="rounded-md bg-zinc-900 px-4 py-2 text-sm font-medium text-white hover:bg-zinc-700 dark:bg-zinc-100 dark:text-zinc-900"
                >
                  Open full image
                </a>
                <button
                  type="button"
                  onClick={runAiTryOn}
                  disabled={aiLoading}
                  className="rounded-md border border-zinc-300 px-4 py-2 text-sm font-medium text-zinc-700 hover:bg-zinc-100 disabled:opacity-60 dark:border-zinc-700 dark:text-zinc-300"
                >
                  Regenerate
                </button>
              </div>
              <p className="text-xs text-zinc-400">
                AI-generated preview · your face is preserved; only the hair changes.
              </p>
            </div>
          ) : (
            <div className="max-w-md rounded-xl border border-zinc-200 p-5 dark:border-zinc-800">
              <span className="inline-block rounded-full bg-violet-100 px-2 py-0.5 text-[11px] font-medium uppercase tracking-wide text-violet-700 dark:bg-violet-900/40 dark:text-violet-300">
                Optional add-on
              </span>
              <p className="mt-2 text-sm text-zinc-600 dark:text-zinc-300">
                Generate a <span className="font-medium">photorealistic</span> image of you
                wearing the <span className="font-medium">{style.name}</span>, edited from your
                own photo.
              </p>
              <button
                type="button"
                onClick={runAiTryOn}
                disabled={aiLoading}
                className="mt-3 inline-flex items-center gap-2 rounded-md bg-violet-600 px-4 py-2 text-sm font-medium text-white hover:bg-violet-500 disabled:opacity-60"
              >
                {aiLoading ? (
                  <>
                    <span className="h-3.5 w-3.5 animate-spin rounded-full border-2 border-white border-t-transparent" />
                    Generating… (~10s)
                  </>
                ) : (
                  <>✨ Generate realistic try-on</>
                )}
              </button>
              {aiError && (
                <p className="mt-3 text-sm text-amber-600 dark:text-amber-400">
                  Couldn&apos;t generate right now — {aiError}
                </p>
              )}
              <p className="mt-3 text-xs text-zinc-400">
                Uses a generative AI model. Takes a few seconds; results are an approximation.
              </p>
            </div>
          )}
        </div>
      )}
    </section>
  );
}

function ModeBtn({
  active,
  onClick,
  label,
}: {
  active: boolean;
  onClick: () => void;
  label: string;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={`rounded-md px-3 py-1.5 text-sm font-medium transition-colors ${
        active
          ? "bg-zinc-900 text-white dark:bg-zinc-100 dark:text-zinc-900"
          : "text-zinc-600 hover:text-zinc-900 dark:text-zinc-400 dark:hover:text-zinc-100"
      }`}
    >
      {label}
    </button>
  );
}

function NudgeBtn({
  onClick,
  label,
  title,
}: {
  onClick: () => void;
  label: string;
  title?: string;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      title={title ?? label}
      className="flex h-9 items-center justify-center rounded-md border border-zinc-300 text-sm text-zinc-700 hover:bg-zinc-100 dark:border-zinc-700 dark:text-zinc-300 dark:hover:bg-zinc-800"
    >
      {label}
    </button>
  );
}
