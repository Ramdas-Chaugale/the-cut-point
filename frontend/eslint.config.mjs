import { defineConfig, globalIgnores } from "eslint/config";
import nextVitals from "eslint-config-next/core-web-vitals";
import nextTs from "eslint-config-next/typescript";

const eslintConfig = defineConfig([
  ...nextVitals,
  ...nextTs,
  {
    rules: {
      // We deliberately fetch data inside effects (fetch-on-mount / on-deps) and
      // drive loading state from those effects. This project doesn't use a data
      // library, so this stylistic rule is off; correctness rules stay on.
      "react-hooks/set-state-in-effect": "off",
    },
  },
  // Override default ignores of eslint-config-next.
  globalIgnores([
    // Default ignores of eslint-config-next:
    ".next/**",
    "out/**",
    "build/**",
    "next-env.d.ts",
    // Self-hosted, generated MediaPipe runtime — never lint vendored assets.
    "public/**",
  ]),
]);

export default eslintConfig;
