"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { analyzeFace } from "@/lib/api";
import { detectFace } from "@/lib/mediapipe";
import type { AnalysisPayload, AnalyzeResponse } from "@/lib/faceTypes";
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
  onAnalyzed?: (payload: AnalysisPayload | null) => void;
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
        // Snapshot the photo at natural size so the try-on can reuse it
        // without re-uploading.
        const snap = document.createElement("canvas");
        snap.width = naturalW;
        snap.height = naturalH;
        snap.getContext("2d")?.drawImage(source, 0, 0, naturalW, naturalH);
        const photo = snap.toDataURL("image/jpeg", 0.9);
        setStatus({ kind: "done", result });
        onAnalyzed?.({
          result,
          photo,
          points: detection.points!,
          width: naturalW,
          height: naturalH,
        });
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
            className="px-4 py-2 disabled:opacity-50 rounded-lg bg-accent text-sm font-semibold text-accent-ink shadow-sm transition-colors hover:bg-accent-hover"
          >
            Upload a photo
          </button>
          {cameraOn ? (
            <>
              <button
                type="button"
                onClick={capturePhoto}
                className="rounded-lg bg-accent px-4 py-2 text-sm font-semibold text-accent-ink shadow-sm transition-colors hover:bg-accent-hover"
              >
                Capture
              </button>
              <button
                type="button"
                onClick={stopCamera}
                className="rounded-lg border border-line-strong px-4 py-2 text-sm font-medium text-ink-soft hover:bg-surface-sunken"
              >
                Cancel
              </button>
            </>
          ) : (
            <button
              type="button"
              onClick={startCamera}
              disabled={busy}
              className="rounded-lg border border-line-strong px-4 py-2 text-sm font-medium text-ink-soft hover:bg-surface-sunken disabled:opacity-50"
            >
              Use camera
            </button>
          )}
          {hasImage && !cameraOn && (
            <button
              type="button"
              onClick={reset}
              className="rounded-lg px-4 py-2 text-sm font-medium text-ink-faint hover:text-ink"
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

        <div className="relative flex min-h-64 items-center justify-center overflow-hidden rounded-lg border border-dashed border-line-strong bg-surface-sunken">
          <video
            ref={videoRef}
            className={cameraOn ? "max-h-[460px] w-auto" : "hidden"}
            playsInline
            muted
          />
          <canvas
            ref={canvasRef}
            className={cameraOn || !hasImage ? "hidden" : "max-w-full rounded-lg"}
          />
          {!cameraOn && !hasImage && (
            <p className="px-6 text-center text-sm text-ink-faint">
              Drop a clear, front-facing photo here.
            </p>
          )}
          {busy && (
            <div className="absolute inset-0 flex items-center justify-center bg-surface/70 backdrop-blur-sm">
              <span className="flex items-center gap-2 text-sm font-medium text-ink-soft">
                <span className="h-3 w-3 animate-spin rounded-full border-2 border-accent border-t-transparent" />
                {status.kind === "working" ? status.message : "Working…"}
              </span>
            </div>
          )}
        </div>
      </div>

      {/* Right: results / messages */}
      <div className="flex flex-col">
        {status.kind === "error" && (
          <div className="rounded-lg border border-negative-line bg-negative-soft px-4 py-3 text-sm text-negative">
            {status.message}
          </div>
        )}
        {status.kind === "done" && <FaceResult result={status.result} />}
        {(status.kind === "idle" || busy) && (
          <div className="flex h-full min-h-48 items-center justify-center rounded-lg border border-line text-center text-sm text-ink-faint">
            Your face-shape analysis will appear here.
          </div>
        )}
      </div>
    </div>
  );
}
