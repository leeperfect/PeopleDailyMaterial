import { chromium } from "playwright";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const htmlPath = path.join(__dirname, "index.html");
const outDir = path.join(__dirname, "output");

const targets = [
  ["#xhs-01", "xhs-01-cover.png"],
  ["#xhs-02", "xhs-02-five-actions.png"],
  ["#xhs-03", "xhs-03-identify-advantage.png"],
  ["#xhs-04", "xhs-04-refine-industry.png"],
  ["#xhs-05", "xhs-05-complete-chain.png"],
  ["#xhs-06", "xhs-06-activate-consumption.png"],
  ["#xhs-07", "xhs-07-keep-youth.png"],
  ["#xhs-08", "xhs-08-boundary.png"],
  ["#xhs-09", "xhs-09-interview-research.png"],
  ["#xhs-10", "xhs-10-references.png"],
];

const browser = await chromium.launch({
  args: ["--use-angle=swiftshader", "--enable-unsafe-swiftshader"],
});
const page = await browser.newPage({
  viewport: { width: 1400, height: 1700 },
  deviceScaleFactor: 1,
});

await page.goto("file://" + htmlPath, { waitUntil: "networkidle" });
await page.evaluate(() => document.fonts && document.fonts.ready);
await page.waitForTimeout(800);

for (const [selector, filename] of targets) {
  const el = await page.$(selector);
  if (!el) throw new Error(`Missing target ${selector}`);
  await el.screenshot({ path: path.join(outDir, filename) });
}

await browser.close();
