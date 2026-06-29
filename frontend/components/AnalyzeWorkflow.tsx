"use client";

import { useState } from "react";
import type { AnalyzeResponse } from "@/lib/faceTypes";
import { FaceAnalyzer } from "./FaceAnalyzer";
import { RecommendationExplorer } from "./RecommendationExplorer";

/**
 * Client workflow: face analysis -> (once a shape is found) hairstyle
 * recommendations for that shape.
 */
export function AnalyzeWorkflow() {
  const [analysis, setAnalysis] = useState<AnalyzeResponse | null>(null);

  return (
    <>
      <FaceAnalyzer onAnalyzed={setAnalysis} />
      {analysis && <RecommendationExplorer faceShape={analysis.shape} />}
    </>
  );
}
