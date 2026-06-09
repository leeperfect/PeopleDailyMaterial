import { chromium } from 'playwright';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const htmlPath = path.join(__dirname, 'index.html');
const outDir = path.join(__dirname, 'output');

const targets = [
  ['#gx-interview-wechat-cover', 'wechat-cover-guangxi-interview-phenomenon.png'],
];

const browser = await chromium.launch({ headless: true });
const page = await browser.newPage({ viewport: { width: 2600, height: 1700 }, deviceScaleFactor: 1 });
await page.goto(`file://${htmlPath}`, { waitUntil: 'load', timeout: 60000 });
await page.waitForTimeout(1200);

for (const [selector, filename] of targets) {
  const locator = page.locator(selector).first();
  await locator.screenshot({ path: path.join(outDir, filename), animations: 'disabled' });
}

await browser.close();
console.log(`Rendered ${targets.length} images to ${outDir}`);
