import { chromium } from "playwright";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const htmlPath = path.join(__dirname, "index.html");
const outDir = path.join(__dirname, "output");

const targets = [
  ["#xhs-01", "xhs-01-cover.png"],
  ["#xhs-02", "xhs-02-policy-to-answer.png"],
  ["#xhs-03", "xhs-03-six-keywords.png"],
  ["#xhs-04", "xhs-04-food-security.png"],
  ["#xhs-05", "xhs-05-tech-agriculture.png"],
  ["#xhs-06", "xhs-06-rural-industry.png"],
  ["#xhs-07", "xhs-07-public-services.png"],
  ["#xhs-08", "xhs-08-rural-governance.png"],
  ["#xhs-09", "xhs-09-farmer-income.png"],
  ["#xhs-10", "xhs-10-answer-path.png"],
  ["#xhs-11", "xhs-11-exam-transfer.png"],
  ["#xhs-12", "xhs-12-golden-lines.png"],
  ["#xhs-13", "xhs-13-references.png"],
  ["#wechat-21x9", "wechat-21x9-cover.png"],
  ["#wechat-1x1", "wechat-1x1-share.png"],
];

const browser = await chromium.launch({
  args: ["--use-angle=swiftshader", "--enable-unsafe-swiftshader"],
});
const page = await browser.newPage({
  viewport: { width: 2300, height: 1700 },
  deviceScaleFactor: 1,
});

await page.goto("file://" + htmlPath, { waitUntil: "networkidle" });
await page.evaluate(() => document.fonts && document.fonts.ready);
await page.waitForTimeout(1100);

for (const [selector, filename] of targets) {
  const el = await page.$(selector);
  if (!el) throw new Error(`Missing target ${selector}`);
  await el.screenshot({ path: path.join(outDir, filename) });
}

await browser.close();
