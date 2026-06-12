import { chromium } from "playwright";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const browser = await chromium.launch({ headless: true });
const page = await browser.newPage({ viewport: { width: 1280, height: 1700 }, deviceScaleFactor: 1 });
await page.goto(`file://${path.join(__dirname, "index.html")}`, { waitUntil: "networkidle" });
await page.evaluate(() => document.fonts.ready);
await page.addStyleTag({
  content: `
    body { padding: 0 !important; background: #fff !important; }
    .deck { display: block !important; }
    .poster { transform: none !important; margin: 0 !important; box-shadow: none !important; }
  `,
});

const report = await page.locator(".poster").evaluateAll((posters) =>
  posters.map((poster) => {
    const content = poster.querySelector(".content");
    const foot = poster.querySelector(".foot");
    const pr = poster.getBoundingClientRect();
    const cr = content.getBoundingClientRect();
    const fr = foot?.getBoundingClientRect();
    return {
      id: poster.id,
      contentHeight: Math.round(content.scrollHeight),
      contentBox: Math.round(cr.height),
      overflow: Math.round(content.scrollHeight - cr.height),
      footBottom: fr ? Math.round(fr.bottom - pr.top) : null,
    };
  })
);

for (const item of report) console.log(JSON.stringify(item));
await browser.close();
