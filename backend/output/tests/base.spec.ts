import {
  test as base,
  expect as baseExpect,
  Page,
  Response,
} from "@playwright/test";
import path from "path";
import fs from "fs/promises";
import config from "../playwright.customconfig.json" assert { type: "json" };
const { results, base_url, playwright_info_file } = config;

let sharedPage: Page | undefined;
let url: string | undefined;
let status: number | undefined;

const info_file = path.join(results, playwright_info_file);

function formatDateTime(d: Date) {
  const y = d.getFullYear().toString();
  const m = String(d.getMonth() + 1).padStart(2, "0");
  const dd = String(d.getDate()).padStart(2, "0");
  const h = String(d.getHours()).padStart(2, "0");
  const min = String(d.getMinutes()).padStart(2, "0");
  const s = String(d.getSeconds()).padStart(2, "0");
  return `${y}${m}${dd}_${h}${min}${s}`;
}

async function ensureDirs() {
  await fs.mkdir(results, { recursive: true });
}

async function updateInfoFile(data: Record<string, unknown>) {
  let current: Record<string, unknown> = {};
  try {
    const content = await fs.readFile(info_file, "utf-8");
    current = JSON.parse(content);
  } catch (err: unknown) {
    if (
      err instanceof Error &&
      (err as NodeJS.ErrnoException).code === "ENOENT"
    ) {
      current = {};
    } else {
      throw err;
    }
  }
  const merged = { ...current, ...data };
  await fs.writeFile(info_file, JSON.stringify(merged, null, 2));
}

export const test = base.extend<{ page: Page }>({
  page: async ({ browser, baseURL }, run, testInfo) => {
    let finalURL = baseURL ?? base_url;
    if (baseURL?.startsWith("/")) {
      finalURL = `${base_url}${baseURL}`;
    }
    if (!sharedPage) {
      sharedPage = await browser.newPage();
      const response: Response | null = await sharedPage.goto(finalURL);
      url = response?.url();
      status = response?.status();
    }

    // run tests
    await run(sharedPage);

    try {
      const titlePath = testInfo.titlePath;
      const describeName =
        titlePath.length > 0 ? titlePath[0] : "(no describe)";
      await updateInfoFile({
        url,
        status,
        describe: describeName,
      });
    } catch (err) {
      console.error("Failed to update info file from fixture: ", err);
    }
  },
});

test.beforeAll(async () => {
  await ensureDirs();
  const startTime = formatDateTime(new Date());
  await updateInfoFile({ startTime });
});

test.afterAll(async () => {
  const endTime = formatDateTime(new Date());
  await updateInfoFile({ endTime });
});

export const expect = baseExpect;
