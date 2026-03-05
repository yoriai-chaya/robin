import { defineConfig, globalIgnores } from "eslint/config";
import nextVitals from "eslint-config-next/core-web-vitals";
import nextTs from "eslint-config-next/typescript";

import noImgElement from "./eslint-custom-rules/no-img-element.mjs";
import noTestidOnSelect from "./eslint-custom-rules/no-testid-on-select.mjs";

export default defineConfig([
  // Next.js core web vitals
  ...nextVitals,

  // Next.js TypeScript configurations
  ...nextTs,

  // Custom rules
  {
    plugins: {
      "custom-rules": {
        rules: {
          "no-img-element": noImgElement,
          "no-testid-on-select": noTestidOnSelect,
        },
      },
    },
    rules: {
      // Disable Next.js base configuration
      "@next/next/no-img-element": "off",

      // Enable Custom rules
      "custom-rules/no-img-element": "error",
      "custom-rules/no-testid-on-select": "error",
    },
  },

  // Default ignores of eslint-config-next:
  globalIgnores([
    ".next/**",
    "out/**",
    "build/**",
    "next-env.d.ts",
  ]),
]);

