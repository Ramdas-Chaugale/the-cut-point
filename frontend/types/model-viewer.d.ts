// Type declaration so the <model-viewer> web component (from @google/model-viewer)
// can be used in JSX. Attributes are typed loosely.
import type { DetailedHTMLProps, HTMLAttributes } from "react";

type ModelViewerAttributes = DetailedHTMLProps<
  HTMLAttributes<HTMLElement>,
  HTMLElement
> & {
  src?: string;
  alt?: string;
  poster?: string;
  "camera-controls"?: boolean;
  "auto-rotate"?: boolean;
  "shadow-intensity"?: string | number;
  exposure?: string | number;
  "camera-orbit"?: string;
  ar?: boolean;
};

declare module "react" {
  namespace JSX {
    interface IntrinsicElements {
      "model-viewer": ModelViewerAttributes;
    }
  }
}
