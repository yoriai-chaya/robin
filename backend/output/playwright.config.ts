import { defineConfig, devices } from "@playwright/test";
import path from "path";
import customConfig from "./playwright.customconfig.json";
const base_url = customConfig.base_url;
const screenshot_dir = customConfig.screenshot_dir;
const results = path.join(__dirname, customConfig.results);
const playwright_report_file = customConfig.playwright_report_file;

const url = new URL(base_url);
const port = url.port || "3000";

export default defineConfig({
  testDir: "tests",
  snapshotPathTemplate: path.join(results, screenshot_dir + "/{arg}{ext}"),
  timeout: 9_000,
  use: {
    baseURL: base_url,
    headless: false,
    navigationTimeout: 12_000,
  },

  projects: [
    {
      name: "chromium-main",
      use: {
        browserName: "chromium",
        launchOptions: {
          args: ["--window-size=1280,800"],
        },
        // @ts-expect-error viewport is duplicated intentionally
        viewport: null,
        ...devices["Desktop Chrome"],
      },
    },
    {
      name: "chromium-mobile",
      use: {
        browserName: "chromium",
        launchOptions: {
          args: ["--window-size=393,852"],
        },
        // @ts-expect-error viewport is duplicated intentionally
        viewport: null,
        ...devices["iPhone 16"],
      },
    },
  ],

  webServer: {
    command: `npm run dev -- -p ${port}`,
    url: base_url,
    reuseExistingServer: false,
  },

  reporter: [
    [
      "json",
      {
        outputFile: path.join(results, playwright_report_file),
      },
    ],
  ],
});
