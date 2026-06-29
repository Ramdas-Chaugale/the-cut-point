"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { analyzeFace } from "@/lib/api";
import { detectFace } from "@/lib/mediapipe";
import type { AnalyzeResponse } from "@/lib/faceTypes";
import { FaceResult } from "./FaceResult";

// The 8 bone-structure landmarks the classifier actually measures
// (chin, forehead-top, cheeks, jaw corners, forehead corners).
const KEY_INDICES = [152, 10, 234, 454, 172, 397, 54, 284];
const MAX_DISPLAY_W = 460;

type Status =
  | { kind: "idle" }
  | { kind: "working"; message: string }
  | { kind: "done"; result: AnalyzeResponse }
  | { kind: "error"; message: string };

export function FaceAnalyzer({
  onAnalyzed,
}: {
  onAnalyzed?: (result: AnalyzeResponse | null) => void;
}) {
  const [status, setStatus] = useState<Status>({ kind: "idle" });
  const [cameraOn, setCameraOn] = useState(false);
  const [hasImage, setHasImage] = useState(false);

  const canvasRef = useRef<HTMLCanvasElement>(null);
  const videoRef = useRef<HTMLVideoElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const streamRef = useRef<MediaStream | null>(null);

  const stopCamera = useCallback(() => {
    streamRef.current?.getTracks().forEach((t) => t.stop());
    streamRef.current = null;
    setCameraOn(false);
  }, []);

  useEffect(() => () => stopCamera(), [stopCamera]);

  /** Draw the source image and the landmark overlay onto the display canvas. */
  const renderToCanvas = useCallback(
    (source: CanvasImageSource, naturalW: number, naturalH: number, points: { x: number; y: number }[] | null) => {
      const canvas = canvasRef.current;
      if (!canvas) return;
      const scale = Math.min(1, MAX_DISPLAY_W / naturalW);
      const w = Math.round(naturalW * scale);
      const h = Math.round(naturalH * scale);
      canvas.width = w;
      canvas.height = h;
      const ctx = canvas.getContext("2d");
      if (!ctx) return;
      ctx.drawImage(source, 0, 0, w, h);
      if (points) {
        // Faint full mesh for context.
        ctx.fillStyle = "rgba(16, 185, 129, 0.45)";
        for (const p of points) ctx.fillRect(p.x * w - 0.5, p.y * h - 0.5, 1.5, 1.5);
        // Highlight the measured bone-structure points.
        ctx.fillStyle = "rgba(5, 150, 105, 1)";
        ctx.strokeStyle = "white";
        ctx.lineWidth = 1.5;
        for (const idx of KEY_INDICES) {
          const p = points[idx];
          if (!p) continue;
          ctx.beginPath();
          ctx.arc(p.x * w, p.y * h, 4, 0, Math.PI * 2);
          ctx.fill();
          ctx.stroke();
        }
      }
    },
    [],
  );

  /** Run detection + classification on a still source. */
  const process = useCallback(
    async (source: HTMLImageElement | HTMLCanvasElement, naturalW: number, naturalH: number) => {
      setStatus({ kind: "working", message: "Loading the face model…" });
      setHasImage(true);
      onAnalyzed?.(null); // clear any previous recommendations
      // Show the image immediately while the model loads.
      renderToCanvas(source, naturalW, naturalH, null);
      try {
        setStatus({ kind: "working", message: "Detecting facial landmarks…" });
        const detection = await detectFace(source);

        if (detection.faceCount === 0) {
          renderToCanvas(source, naturalW, naturalH, null);
          setStatus({
            kind: "error",
            message:
              "No face detected. Use a clear, front-facing photo with the whole face visible and good lighting.",
          });
          return;
        }
        if (detection.faceCount > 1) {
          renderToCanvas(source, naturalW, naturalH, detection.points);
          setStatus({
            kind: "error",
            message:
              "More than one face detected. Please use a photo containing only your face.",
          });
          return;
        }

        renderToCanvas(source, naturalW, naturalH, detection.points);
        setStatus({ kind: "working", message: "Analysing face shape…" });
        const result = await analyzeFace(detection.landmarks!, naturalW, naturalH);
        setStatus({ kind: "done", result });
        onAnalyzed?.(result);
      } catch (err) {
        const message = (err as Error).message ?? "Something went wrong.";
        setStatus({
          kind: "error",
          message: message.includes("model") || message.includes("wasm")
            ? "Could not load the face model. Run `npm run setup:mediapipe` in /frontend and reload."
            : message,
        });
      }
    },
    [renderToCanvas, onAnalyzed],
  );

  const onFile = useCallback(
    (file: File) => {
      stopCamera();
      const url = URL.createObjectURL(file);
      const img = new Image();
      img.onload = () => {
        void process(img, img.naturalWidth, img.naturalHeight);
        URL.revokeObjectURL(url);
      };
      img.onerror = () => {
        URL.revokeObjectURL(url);
        setStatus({ kind: "error", message: "Could not read that image file." });
      };
      img.src = url;
    },
    [process, stopCamera],
  );

  const startCamera = useCallback(async () => {
    setStatus({ kind: "idle" });
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: "user", width: { ideal: 720 }, height: { ideal: 720 } },
        audio: false,
      });
      streamRef.current = stream;
      setCameraOn(true);
      const video = videoRef.current;
      if (video) {
        video.srcObject = stream;
        await video.play();
      }
    } catch {
      setStatus({
        kind: "error",
        message: "Could not access the camera. Check browser permissions, or upload a photo instead.",
      });
    }
  }, []);

  const capturePhoto = useCallback(() => {
    const video = videoRef.current;
    if (!video || !video.videoWidth) return;
    const snap = document.createElement("canvas");
    snap.width = video.videoWidth;
    snap.height = video.videoHeight;
    snap.getContext("2d")?.drawImage(video, 0, 0);
    stopCamera();
    void process(snap, snap.width, snap.height);
  }, [process, stopCamera]);

  const reset = useCallback(() => {
    stopCamera();
    setHasImage(false);
    setStatus({ kind: "idle" });
    onAnalyzed?.(null);
    const canvas = canvasRef.current;
    canvas?.getContext("2d")?.clearRect(0, 0, canvas.width, canvas.height);
  }, [stopCamera, onAnalyzed]);

  const busy = status.kind === "working";

  return (
    <div className="grid gap-8 md:grid-cols-2">
      {/* Left: capture / preview */}
      <div className="flex flex-col gap-4">
        <div className="flex flex-wrap gap-3">
          <button
            type="button"
            onClick={() => fileInputRef.current?.click()}
            disabled={busy}
            className="rounded-md bg-zinc-900 px-4 py-2 text-sm font-medium text-white hover:bg-zinc-700 disabled:opacity-50 dark:bg-zinc-100 dark:text-zinc-900 dark:hover:bg-zinc-300"
          >
            Upload a photo
          </button>
          {cameraOn ? (
            <>
              <button
                type="button"
                onClick={capturePhoto}
                className="rounded-md bg-emerald-600 px-4 py-2 text-sm font-medium text-white hover:bg-emerald-500"
              >
                Capture
              </button>
              <button
                type="button"
                onClick={stopCamera}
                className="rounded-md border border-zinc-300 px-4 py-2 text-sm font-medium text-zinc-700 hover:bg-zinc-100 dark:border-zinc-700 dark:text-zinc-300"
              >
                Cancel
              </button>
            </>
          ) : (
            <button
              type="button"
              onClick={startCamera}
              disabled={busy}
              className="rounded-md border border-zinc-300 px-4 py-2 text-sm font-medium text-zinc-700 hover:bg-zinc-100 disabled:opacity-50 dark:border-zinc-700 dark:text-zinc-300"
            >
              Use camera
            </button>
          )}
          {hasImage && !cameraOn && (
            <button
              type="button"
              onClick={reset}
              className="rounded-md px-4 py-2 text-sm font-medium text-zinc-500 hover:text-zinc-800 dark:hover:text-zinc-200"
            >
              Start over
            </button>
          )}
        </div>

        <input
          ref={fileInputRef}
          type="file"
          accept="image/*"
          className="hidden"
          onChange={(e) => {
            const file = e.target.files?.[0];
            if (file) onFile(file);
            e.target.value = "";
          }}
        />

        <div className="relative flex min-h-64 items-center justify-center overflow-hidden rounded-lg border border-dashed border-zinc-300 bg-zinc-50 dark:border-zinc-700 dark:bg-zinc-900/40">
          <video
            ref={videoRef}
            className={cameraOn ? "max-h-[460px] w-auto" : "hidden"}
            playsInline
            muted
          />
          <canvas
            ref={canvasRef}
            className={cameraOn || !hasImage ? "hidden" : "max-w-full rounded-md"}
          />
          {!cameraOn && !hasImage && (
            <p className="px-6 text-center text-sm text-zinc-400">
              Upload or capture a clear, front-facing photo. Works on bald and
              short-haired faces.
            </p>
          )}
          {busy && (
            <div className="absolute inset-0 flex items-center justify-center bg-white/70 backdrop-blur-sm dark:bg-black/60">
              <span className="flex items-center gap-2 text-sm font-medium text-zinc-700 dark:text-zinc-200">
                <span className="h-3 w-3 animate-spin rounded-full border-2 border-emerald-500 border-t-transparent" />
                {status.kind === "working" ? status.message : "Working…"}
              </span>
            </div>
          )}
        </div>
      </div>

      {/* Right: results / messages */}
      <div className="flex flex-col">
        {status.kind === "error" && (
          <div className="rounded-lg border border-red-300 bg-red-50 px-4 py-3 text-sm text-red-800 dark:border-red-800/50 dark:bg-red-950/40 dark:text-red-200">
            {status.message}
          </div>
        )}
        {status.kind === "done" && <FaceResult result={status.result} />}
        {(status.kind === "idle" || busy) && (
          <div className="flex h-full min-h-48 items-center justify-center rounded-lg border border-zinc-200 text-center text-sm text-zinc-400 dark:border-zinc-800">
            Your face-shape analysis will appear here.
          </div>
        )}
      </div>
    </div>
  );
}
