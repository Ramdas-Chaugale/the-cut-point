/**
 * Build the hair-region mask that the inpainting try-on paints into.
 *
 * White means "replace this", black means "keep the original photo". So the
 * face is protected by construction: eyes, nose and mouth sit outside the mask
 * and the model is never able to touch them. That is the structural advantage
 * over whole-image editing, which relies on asking a model to leave the face
 * alone.
 *
 * The region is derived from the MediaPipe landmarks the analysis already
 * produced, so no extra detection runs:
 *
 *   white  a generous ellipse around the skull, wider and taller than the face
 *          because hair sits outside the head's outline and long styles fall
 *          past the jaw
 *   black  an ellipse over the face from the eyebrows to the chin
 *
 * The forehead above the brows stays white on purpose. A fringe has to be able
 * to fall onto it, and cutting the mask at the hairline would make every style
 * render swept back.
 */

import type { AnalysisPayload } from "./faceTypes";

// MediaPipe FaceMesh indices.
const CHEEK_R = 234; // subject's right, image left
const CHEEK_L = 454; // subject's left, image right
const FOREHEAD_TOP = 10;
const CHIN = 152;
const BROWS = [105, 334, 70, 300, 46, 276]; // inner and outer, both sides

/** How far the hair region extends beyond the face, as multiples of face size. */
const HAIR_RX = 0.95; // half-width
const HAIR_RY = 1.0; // half-height
const FACE_RX = 0.46; // protected half-width
const FEATHER = 0.02; // blur radius as a fraction of face height

function point(payload: AnalysisPayload, i: number, w: number, h: number) {
  const p = payload.points[i];
  return { x: p.x * w, y: p.y * h };
}

/**
 * A PNG data URL the same size as the photo, white where hair should be
 * generated. Returns null if the landmarks needed are missing.
 */
export function buildHairMask(payload: AnalysisPayload): string | null {
  const w = payload.width;
  const h = payload.height;
  if (!w || !h || !payload.points?.length) return null;

  const needed = [CHEEK_R, CHEEK_L, FOREHEAD_TOP, CHIN, ...BROWS];
  if (needed.some((i) => !payload.points[i])) return null;

  const canvas = document.createElement("canvas");
  canvas.width = w;
  canvas.height = h;
  const ctx = canvas.getContext("2d");
  if (!ctx) return null;

  const right = point(payload, CHEEK_R, w, h);
  const left = point(payload, CHEEK_L, w, h);
  const top = point(payload, FOREHEAD_TOP, w, h);
  const chin = point(payload, CHIN, w, h);

  const faceW = Math.hypot(left.x - right.x, left.y - right.y);
  const faceH = Math.hypot(chin.x - top.x, chin.y - top.y);
  if (faceW < 4 || faceH < 4) return null;

  const cx = (right.x + left.x) / 2;
  const browY = Math.min(...BROWS.map((i) => point(payload, i, w, h).y));

  // Head tilt, so the mask turns with the head instead of staying upright.
  const tilt = Math.atan2(left.y - right.y, left.x - right.x);

  ctx.fillStyle = "#000";
  ctx.fillRect(0, 0, w, h);

  // Soften both edges so the painted region does not end on a hard line.
  ctx.filter = `blur(${Math.max(2, faceH * FEATHER)}px)`;

  // Where the hair goes.
  ctx.save();
  ctx.translate(cx, top.y);
  ctx.rotate(tilt);
  ctx.fillStyle = "#fff";
  ctx.beginPath();
  ctx.ellipse(0, 0, faceW * HAIR_RX, faceH * HAIR_RY, 0, 0, Math.PI * 2);
  ctx.fill();
  ctx.restore();

  // Put the face back. Brows to chin, so the fringe area above stays paintable.
  const faceCy = (browY + chin.y) / 2;
  const faceRy = Math.max(8, (chin.y - browY) / 2) * 1.04;
  ctx.save();
  ctx.translate(cx, faceCy);
  ctx.rotate(tilt);
  ctx.fillStyle = "#000";
  ctx.beginPath();
  ctx.ellipse(0, 0, faceW * FACE_RX, faceRy, 0, 0, Math.PI * 2);
  ctx.fill();
  ctx.restore();

  ctx.filter = "none";
  return canvas.toDataURL("image/png");
}
