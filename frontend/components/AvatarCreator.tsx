"use client";

import { useEffect, useRef } from "react";

const SUBDOMAIN = process.env.NEXT_PUBLIC_RPM_SUBDOMAIN || "demo";

/**
 * Embeds the Ready Player Me avatar creator and listens (via its frame API)
 * for the exported avatar. On export, `onExported` receives the .glb URL.
 * RPM is free and needs no API key — just a subdomain.
 */
export function AvatarCreator({ onExported }: { onExported: (url: string) => void }) {
  const iframeRef = useRef<HTMLIFrameElement>(null);

  useEffect(() => {
    const iframe = iframeRef.current;

    const onMessage = (event: MessageEvent) => {
      let json: { source?: string; eventName?: string; data?: { url?: string } };
      try {
        json = typeof event.data === "string" ? JSON.parse(event.data) : event.data;
      } catch {
        return;
      }
      if (json?.source !== "readyplayerme") return;

      // Subscribe to all events once the frame is ready.
      if (json.eventName === "v1.frame.ready") {
        iframe?.contentWindow?.postMessage(
          JSON.stringify({ target: "readyplayerme", type: "subscribe", eventName: "v1.**" }),
          "*",
        );
      }
      // Avatar exported → hand back the .glb URL.
      if (json.eventName === "v1.avatar.exported" && json.data?.url) {
        onExported(json.data.url);
      }
    };

    window.addEventListener("message", onMessage);
    return () => window.removeEventListener("message", onMessage);
  }, [onExported]);

  const src = `https://${SUBDOMAIN}.readyplayer.me/avatar?frameApi&clearCache`;

  return (
    <iframe
      ref={iframeRef}
      src={src}
      title="Ready Player Me avatar creator"
      allow="camera *; microphone *; clipboard-write"
      className="h-[600px] w-full rounded-xl border border-line"
    />
  );
}
