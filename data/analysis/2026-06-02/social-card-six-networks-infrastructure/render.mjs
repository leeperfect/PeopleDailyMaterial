import { chromium } from 'playwright';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const htmlPath = path.join(__dirname, 'index.html');
const outDir = path.join(__dirname, 'output');

const targets = [
  ['#xhs-01-cover', 'xhs-01-cover.png'],
  ['#xhs-02-shift', 'xhs-02-shift.png'],
  ['#xhs-03-six-networks', 'xhs-03-six-networks.png'],
  ['#xhs-04-water', 'xhs-04-water.png'],
  ['#xhs-05-grid', 'xhs-05-grid.png'],
  ['#xhs-06-compute', 'xhs-06-compute.png'],
  ['#xhs-07-communication', 'xhs-07-communication.png'],
  ['#xhs-08-pipe', 'xhs-08-pipe.png'],
  ['#xhs-09-logistics', 'xhs-09-logistics.png'],
  ['#xhs-10-abilities', 'xhs-10-abilities.png'],
  ['#xhs-11-exam', 'xhs-11-exam.png'],
  ['#xhs-12-boundary', 'xhs-12-boundary.png'],
  ['#xhs-13-golden-lines', 'xhs-13-golden-lines.png'],
  ['#xhs-14-references', 'xhs-14-references.png'],
  ['#wechat-21x9-cover', 'wechat-21x9-cover.png'],
  ['#wechat-1x1-cover', 'wechat-1x1-cover.png'],
  ['#wechat-cover-pair-preview', 'wechat-cover-pair-preview.png'],
];

const browser = await chromium.launch({ headless: true });
const page = await browser.newPage({ viewport: { width: 2600, height: 1700 }, deviceScaleFactor: 1 });
await page.goto(`file://${htmlPath}`, { waitUntil: 'networkidle' });
await page.waitForTimeout(900);

for (const [selector, filename] of targets) {
  const locator = page.locator(selector).first();
  await locator.screenshot({ path: path.join(outDir, filename), animations: 'disabled' });
}

await browser.close();
console.log(`Rendered ${targets.length} images to ${outDir}`);
