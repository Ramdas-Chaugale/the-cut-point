"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import {
  ArrowDown,
  ArrowLeft,
  ArrowRight,
  ArrowUp,
  Minus,
  Plus,
  RotateCcw,
  Sparkles,
} from "lucide-react";
import { generateTryOn, getHealth } from "@/lib/api";
import { buildHairMask } from "@/lib/hairMask";
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
      // The mask keeps the model inside the hair region, so the face in the
      // result is the original photograph rather than a regenerated one.
      const mask = buildHairMask(payload);
      const res = await generateTryOn(payload.photo, style.id, mask);
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
          ? "Realistic AI try-on runs on a paid image model (fal.ai). The integration is built and tested; it needs credits on the account to generate."
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
          <h2 className="text-xl font-semibold tracking-tight text-ink">
            Virtual try-on · {style.name}
          </h2>
          <p className="mt-1 text-sm text-ink-faint">
            {mode === "overlay"
              ? "A 2D overlay anchored to your facial landmarks (not a neural render). Nudge it for a perfect fit."
              : "A photorealistic AI edit of your own photo wearing this style."}
          </p>
        </div>
        <button
          type="button"
          onClick={onBack}
          className="inline-flex items-center gap-1.5 rounded-lg border border-line-strong px-3 py-1.5 text-sm font-medium text-ink-soft transition-colors hover:border-accent hover:text-accent"
        >
          <ArrowLeft className="h-4 w-4" aria-hidden />
          Try another
        </button>
      </div>

      {aiEnabled && (
        <div className="mt-4 inline-flex rounded-lg border border-line p-1">
          <ModeBtn active={mode === "overlay"} onClick={() => setMode("overlay")} label="2D overlay" />
          <ModeBtn
            active={mode === "ai"}
            onClick={() => setMode("ai")}
            label={
              <span className="inline-flex items-center gap-1.5">
                <Sparkles className="h-3.5 w-3.5" aria-hidden />
                Realistic AI
              </span>
            }
          />
        </div>
      )}

      {mode === "overlay" ? (
      <div className="mt-5 flex flex-col gap-5 sm:flex-row sm:items-start">
        <div className="relative overflow-hidden rounded-lg border border-line bg-surface-sunken">
          <canvas ref={canvasRef} className="block max-w-full" />
          {!ready && (
            <div className="absolute inset-0 flex items-center justify-center text-sm text-ink-faint">
              Preparing your try-on…
            </div>
          )}
        </div>

        {/* Controls */}
        <div className="flex flex-col gap-4">
          <div>
            <p className="mb-1.5 text-xs font-medium uppercase tracking-wide text-ink-faint">
              Fine-tune position
            </p>
            <div className="grid w-32 grid-cols-3 gap-1.5">
              <span />
              <NudgeBtn onClick={() => move(0, -4)} label={<ArrowUp className="h-4 w-4" />} title="Move up" />
              <span />
              <NudgeBtn onClick={() => move(-4, 0)} label={<ArrowLeft className="h-4 w-4" />} title="Move left" />
              <NudgeBtn onClick={() => setNudge(NEUTRAL)} label={<RotateCcw className="h-4 w-4" />} title="Reset position" />
              <NudgeBtn onClick={() => move(4, 0)} label={<ArrowRight className="h-4 w-4" />} title="Move right" />
              <span />
              <NudgeBtn onClick={() => move(0, 4)} label={<ArrowDown className="h-4 w-4" />} title="Move down" />
              <span />
            </div>
          </div>
          <div>
            <p className="mb-1.5 text-xs font-medium uppercase tracking-wide text-ink-faint">
              Size
            </p>
            <div className="flex gap-1.5">
              <NudgeBtn onClick={() => zoom(-0.05)} label={<Minus className="h-4 w-4" />} title="Smaller" />
              <NudgeBtn onClick={() => zoom(0.05)} label={<Plus className="h-4 w-4" />} title="Bigger" />
            </div>
          </div>
          <button
            type="button"
            onClick={download}
            className="mt-1 px-4 py-2 rounded-lg bg-accent text-sm font-semibold text-accent-ink shadow-sm transition-colors hover:bg-accent-hover"
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
                className="max-h-[480px] w-auto rounded-lg border border-line"
              />
              <div className="flex gap-2">
                <a
                  href={aiImage}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="px-4 py-2 rounded-lg bg-accent text-sm font-semibold text-accent-ink shadow-sm transition-colors hover:bg-accent-hover"
                >
                  Open full image
                </a>
                <button
                  type="button"
                  onClick={runAiTryOn}
                  disabled={aiLoading}
                  className="rounded-lg border border-line-strong px-4 py-2 text-sm font-medium text-ink-soft hover:bg-surface-sunken disabled:opacity-60"
                >
                  Regenerate
                </button>
              </div>
              <p className="text-xs text-ink-faint">
                AI-generated preview · your face is preserved; only the hair changes.
              </p>
            </div>
          ) : (
            <div className="max-w-md rounded-xl border border-line p-5">
              <span className="inline-block rounded-full bg-ai-soft px-2 py-0.5 text-[11px] font-medium uppercase tracking-wide text-ai">
                Optional add-on
              </span>
              <p className="mt-2 text-sm text-ink-soft">
                Generate a <span className="font-medium">photorealistic</span> image of you
                wearing the <span className="font-medium">{style.name}</span>, edited from your
                own photo.
              </p>
              <button
                type="button"
                onClick={runAiTryOn}
                disabled={aiLoading}
                className="mt-3 inline-flex items-center gap-2 rounded-lg bg-ai px-4 py-2 text-sm font-semibold text-ai-ink transition-colors hover:bg-ai-hover disabled:opacity-60"
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
                <p className="mt-3 text-sm text-caution">
                  Couldn&apos;t generate right now. {aiError}
                </p>
              )}
              <p className="mt-3 text-xs text-ink-faint">
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
  label: React.ReactNode;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={`rounded-lg px-3 py-1.5 text-sm font-medium transition-colors ${
        active
          ? "bg-accent-soft text-accent"
          : "text-ink-soft hover:text-ink"
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
  label: React.ReactNode;
  title: string;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      title={title}
      aria-label={title}
      className="flex h-9 items-center justify-center rounded-lg border border-line-strong text-ink-soft transition-colors hover:border-accent hover:text-accent"
    >
      {label}
    </button>
  );
}
