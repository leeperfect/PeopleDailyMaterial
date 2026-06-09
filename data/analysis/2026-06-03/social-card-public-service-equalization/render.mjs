import { chromium } from 'playwright';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const htmlPath = path.join(__dirname, 'index.html');
const outDir = path.join(__dirname, 'output');

const targets = [
  ['#xhs-01-cover', 'xhs-01-cover.png'],
  ['#xhs-02-question', 'xhs-02-question.png'],
  ['#xhs-03-actions', 'xhs-03-actions.png'],
  ['#xhs-04-people', 'xhs-04-people.png'],
  ['#xhs-05-data', 'xhs-05-data.png'],
  ['#xhs-06-radius', 'xhs-06-radius.png'],
  ['#xhs-07-medical', 'xhs-07-medical.png'],
  ['#xhs-08-elderly', 'xhs-08-elderly.png'],
  ['#xhs-09-process', 'xhs-09-process.png'],
  ['#xhs-10-digital', 'xhs-10-digital.png'],
  ['#xhs-11-framework', 'xhs-11-framework.png'],
  ['#xhs-12-interview', 'xhs-12-interview.png'],
  ['#xhs-13-golden', 'xhs-13-golden.png'],
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
