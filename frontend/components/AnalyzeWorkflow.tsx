"use client";

import { useRef, useState } from "react";
import type { AnalysisPayload } from "@/lib/faceTypes";
import type { StyleRecommendation } from "@/lib/recommendTypes";
import { FaceAnalyzer } from "./FaceAnalyzer";
import { RecommendationExplorer } from "./RecommendationExplorer";
import { TryOn } from "./TryOn";

/**
 * Client workflow: face analysis -> recommendations -> virtual try-on.
 * The analysis payload (photo + landmarks) is kept so the try-on never needs
 * a re-upload, and switching styles is instant.
 */
export function AnalyzeWorkflow() {
  const [analysis, setAnalysis] = useState<AnalysisPayload | null>(null);
  const [tryOnStyle, setTryOnStyle] = useState<StyleRecommendation | null>(null);
  const tryOnRef = useRef<HTMLDivElement>(null);

  const handleTryOn = (style: StyleRecommendation) => {
    setTryOnStyle(style);
    // Bring the try-on into view (it renders above the recommendation grid).
    requestAnimationFrame(() =>
      tryOnRef.current?.scrollIntoView({ behavior: "smooth", block: "start" }),
    );
  };

  return (
    <>
      <FaceAnalyzer
        onAnalyzed={(p) => {
          setAnalysis(p);
          setTryOnStyle(null);
        }}
      />

      {analysis && (
        <>
          <div ref={tryOnRef}>
            {tryOnStyle && (
              <TryOn
                key={tryOnStyle.id}
                payload={analysis}
                style={tryOnStyle}
                onBack={() => setTryOnStyle(null)}
              />
            )}
          </div>
          <RecommendationExplorer
            faceShape={analysis.result.shape}
            onTryOn={handleTryOn}
          />
        </>
      )}
    </>
  );
}
