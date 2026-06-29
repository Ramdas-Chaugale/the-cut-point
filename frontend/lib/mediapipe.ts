/**
 * In-browser MediaPipe Face Landmarker loader + still-image detection.
 *
 * Heavy computer vision runs entirely on the user's device (no ML server cost).
 * Assets are self-hosted under /public/mediapipe (see scripts/setup-mediapipe.mjs).
 */
import {
  FaceLandmarker,
  FilesetResolver,
  type FaceLandmarkerResult,
} from "@mediapipe/tasks-vision";

let landmarkerPromise: Promise<FaceLandmarker> | null = null;

/** Lazily create a singleton FaceLandmarker in IMAGE mode (detects up to 2 faces). */
export function getFaceLandmarker(): Promise<FaceLandmarker> {
  if (!landmarkerPromise) {
    landmarkerPromise = (async () => {
      const fileset = await FilesetResolver.forVisionTasks("/mediapipe/wasm");
      return FaceLandmarker.createFromOptions(fileset, {
        baseOptions: {
          modelAssetPath: "/mediapipe/models/face_landmarker.task",
          delegate: "GPU",
        },
        runningMode: "IMAGE",
        numFaces: 2, // detect >1 so we can warn about multiple faces
        outputFaceBlendshapes: false,
        outputFacialTransformationMatrixes: true,
      });
    })().catch((err) => {
      landmarkerPromise = null; // allow retry after a transient failure
      throw err;
    });
  }
  return landmarkerPromise;
}

export type Landmark = { x: number; y: number; z: number };

export interface DetectionResult {
  /** Number of faces found (0, 1, or 2+). */
  faceCount: number;
  /** Flattened [x,y,z] landmarks for the primary face, or null. */
  landmarks: number[][] | null;
  /** Raw landmark objects for the primary face (used for overlay drawing). */
  points: Landmark[] | null;
}

/** Run face-landmark detection on a still image/canvas element. */
export async function detectFace(
  source: HTMLImageElement | HTMLCanvasElement,
): Promise<DetectionResult> {
  const landmarker = await getFaceLandmarker();
  const result: FaceLandmarkerResult = landmarker.detect(source);
  const faces = result.faceLandmarks ?? [];
  if (faces.length === 0) {
    return { faceCount: 0, landmarks: null, points: null };
  }
  const primary = faces[0];
  return {
    faceCount: faces.length,
    landmarks: primary.map((p) => [p.x, p.y, p.z]),
    points: primary.map((p) => ({ x: p.x, y: p.y, z: p.z })),
  };
}
