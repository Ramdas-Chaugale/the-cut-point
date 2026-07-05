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
      <h1 className="text-2xl font-semibold tracking-tight text-zinc-900 dark:text-zinc-50">
        Your 3D avatar
      </h1>
      <p className="mt-1 max-w-prose text-sm text-zinc-600 dark:text-zinc-400">
        Build a 3D avatar of yourself with Ready Player Me — you can start from a selfie.
        This is a standalone showcase; the avatar uses Ready Player Me&apos;s own hair
        options, so it doesn&apos;t wear CutPoint&apos;s 2D hairstyle catalog.
      </p>

      <div className="mt-6">
        {!glb ? (
          <AvatarCreator onExported={setGlb} />
        ) : (
          <div className="flex flex-col items-start gap-4">
            <div className="w-full overflow-hidden rounded-xl border border-zinc-200 bg-gradient-to-b from-zinc-50 to-zinc-100 dark:border-zinc-800 dark:from-zinc-900 dark:to-zinc-950">
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
                className="rounded-md border border-zinc-300 px-4 py-2 text-sm font-medium text-zinc-700 hover:bg-zinc-100 dark:border-zinc-700 dark:text-zinc-300"
              >
                Create another
              </button>
              <a
                href={glb}
                target="_blank"
                rel="noopener noreferrer"
                className="rounded-md bg-zinc-900 px-4 py-2 text-sm font-medium text-white hover:bg-zinc-700 dark:bg-zinc-100 dark:text-zinc-900"
              >
                Download .glb
              </a>
            </div>
            <p className="text-xs text-zinc-400">
              Drag to rotate · scroll to zoom. Powered by Ready Player Me &amp; model-viewer.
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
