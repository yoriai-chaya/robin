import { Page } from "@playwright/test";
import fs from "fs";
import path from "path";
import customConfig from "../playwright.customconfig.json";

export async function captureScreenshot(
  page: Page,
  filename: string,
): Promise<void> {
  const parentDir = path.dirname(__dirname);
  const screenshotDir = path.join(
    parentDir,
    customConfig.results,
    "screenshot",
  );

  if (!fs.existsSync(screenshotDir)) {
    fs.mkdirSync(screenshotDir, { recursive: true });
  }

  const filePath = path.join(screenshotDir, filename);

  await page.screenshot({
    path: filePath,
    fullPage: true,
  });
}
