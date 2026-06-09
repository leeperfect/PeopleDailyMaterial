import { chromium } from "playwright";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const htmlPath = path.join(__dirname, "index.html");
const outDir = path.join(__dirname, "output");

const browser = await chromium.launch({ headless: true });
const page = await browser.newPage({
  viewport: { width: 1200, height: 1600 },
  deviceScaleFactor: 1,
});

await page.goto(`file://${htmlPath}`, { waitUntil: "load" });
await page.waitForTimeout(500);

const posters = await page.locator(".poster.xhs").all();
for (let i = 0; i < posters.length; i += 1) {
  const id = await posters[i].getAttribute("id");
  const name = id === "xhs-01"
    ? "xhs-01-cover.png"
    : `xhs-${String(i + 1).padStart(2, "0")}.png`;
  await posters[i].screenshot({
    path: path.join(outDir, name),
    animations: "disabled",
  });
}

await browser.close();
