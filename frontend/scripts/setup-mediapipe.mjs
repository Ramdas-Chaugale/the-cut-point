// Provisions the self-hosted MediaPipe assets so the app runs offline with no
// CDN dependency. Runs automatically on `npm install` (postinstall) and is
// idempotent. Keeps the large binaries out of git.
import { existsSync, mkdirSync, cpSync, createWriteStream } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { Readable } from "node:stream";
import { pipeline } from "node:stream/promises";

const root = join(dirname(fileURLToPath(import.meta.url)), "..");
const wasmSrc = join(root, "node_modules", "@mediapipe", "tasks-vision", "wasm");
const wasmDest = join(root, "public", "mediapipe", "wasm");
const modelDir = join(root, "public", "mediapipe", "models");
const modelPath = join(modelDir, "face_landmarker.task");
const MODEL_URL =
  "https://storage.googleapis.com/mediapipe-models/face_landmarker/face_landmarker/float16/1/face_landmarker.task";

function copyWasm() {
  if (!existsSync(wasmSrc)) {
    console.warn("[mediapipe] tasks-vision not installed yet; skipping wasm copy.");
    return;
  }
  mkdirSync(wasmDest, { recursive: true });
  cpSync(wasmSrc, wasmDest, { recursive: true });
  console.log("[mediapipe] WASM runtime copied to public/mediapipe/wasm");
}

async function downloadModel() {
  if (existsSync(modelPath)) {
    console.log("[mediapipe] model already present; skipping download.");
    return;
  }
  mkdirSync(modelDir, { recursive: true });
  console.log("[mediapipe] downloading face_landmarker.task ...");
  const res = await fetch(MODEL_URL);
  if (!res.ok || !res.body) {
    throw new Error(`Failed to download model: HTTP ${res.status}`);
  }
  await pipeline(Readable.fromWeb(res.body), createWriteStream(modelPath));
  console.log("[mediapipe] model saved to public/mediapipe/models");
}

try {
  copyWasm();
  await downloadModel();
} catch (err) {
  // Don't hard-fail install (e.g. offline CI); the app surfaces a clear error.
  console.warn(`[mediapipe] setup incomplete: ${err.message}`);
}
