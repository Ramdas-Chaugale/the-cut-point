"use client";

import { useEffect, useState } from "react";
import { AvatarCreator } from "@/components/AvatarCreator";

export default function AvatarPage() {
  const [glb, setGlb] = useState<string | null>(null);

  // Register the <model-viewer> web component on the client.
  useEffect(() => {
    void import("@google/model-viewer");
  }, []);

  return (
    <div className="mx-auto w-full max-w-4xl px-4 py-10 sm:px-6">
      <h1 className="text-3xl font-bold text-ink sm:text-4xl">
        Your 3D avatar
      </h1>
      <p className="mt-1 max-w-prose text-sm text-ink-soft">
        Build a 3D avatar of yourself with Ready Player Me, starting from a selfie if you like.
        This is a standalone showcase; the avatar uses Ready Player Me&apos;s own hair
        options, so it doesn&apos;t wear CutPoint&apos;s 2D hairstyle catalog.
      </p>

      <div className="mt-6">
        {!glb ? (
          <AvatarCreator onExported={setGlb} />
        ) : (
          <div className="flex flex-col items-start gap-4">
            <div className="w-full overflow-hidden rounded-xl border border-line bg-gradient-to-b from-surface-sunken to-surface-sunken">
              <model-viewer
                src={glb}
                alt="Your 3D avatar"
                camera-controls
                auto-rotate
                shadow-intensity="1"
                exposure="1"
                camera-orbit="0deg 80deg 2.4m"
                style={{ width: "100%", height: "520px" }}
              />
            </div>
            <div className="flex gap-2">
              <button
                type="button"
                onClick={() => setGlb(null)}
                className="rounded-lg border border-line-strong px-4 py-2 text-sm font-medium text-ink-soft hover:bg-surface-sunken"
              >
                Create another
              </button>
              <a
                href={glb}
                target="_blank"
                rel="noopener noreferrer"
                className="px-4 py-2 rounded-lg bg-accent text-sm font-semibold text-accent-ink shadow-sm transition-colors hover:bg-accent-hover"
              >
                Download .glb
              </a>
            </div>
            <p className="text-xs text-ink-faint">
              Drag to rotate · scroll to zoom. Powered by Ready Player Me &amp; model-viewer.
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
