import { chromium } from "playwright";
import path from "node:path";
import { fileURLToPath } from "node:url";
import fs from "node:fs/promises";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const htmlPath = path.join(__dirname, "index.html");
const outputDir = path.join(__dirname, "output");

await fs.mkdir(outputDir, { recursive: true });

const browser = await chromium.launch({ headless: true });
const page = await browser.newPage({ viewport: { width: 1280, height: 1700 }, deviceScaleFactor: 1 });
await page.goto(`file://${htmlPath}`, { waitUntil: "networkidle" });
await page.evaluate(() => document.fonts.ready);
await page.addStyleTag({
  content: `
    body { padding: 0 !important; background: #fff !important; }
    .deck { display: block !important; }
    .poster {
      transform: none !important;
      margin: 0 !important;
      box-shadow: none !important;
    }
  `,
});

const posters = await page.locator(".poster").evaluateAll((nodes) =>
  nodes.map((node) => ({
    id: node.id,
    file: node.getAttribute("data-file") || `${node.id}.png`,
  }))
);

for (const poster of posters) {
  const locator = page.locator(`#${poster.id}`);
  await locator.screenshot({ path: path.join(outputDir, poster.file), animations: "disabled" });
  console.log(`rendered ${poster.file}`);
}

await browser.close();
