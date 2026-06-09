import { chromium } from 'playwright';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const htmlPath = path.join(__dirname, 'index.html');
const outDir = path.join(__dirname, 'output');

const targets = [
  ['#nq-xhs-01-cover', 'xhs-01-cover.png'],
  ['#nq-xhs-02-not-empty', 'xhs-02-not-empty.png'],
  ['#nq-xhs-03-token', 'xhs-03-token.png'],
  ['#nq-xhs-04-patent', 'xhs-04-patent.png'],
  ['#nq-xhs-05-criteria', 'xhs-05-criteria.png'],
  ['#nq-xhs-06-machinery', 'xhs-06-machinery.png'],
  ['#nq-xhs-07-field-ai', 'xhs-07-field-ai.png'],
  ['#nq-xhs-08-chain', 'xhs-08-chain.png'],
  ['#nq-xhs-09-platform', 'xhs-09-platform.png'],
  ['#nq-xhs-10-beidou', 'xhs-10-beidou.png'],
  ['#nq-xhs-11-framework', 'xhs-11-framework.png'],
  ['#nq-xhs-12-interview', 'xhs-12-interview.png'],
  ['#nq-xhs-13-closing', 'xhs-13-closing.png'],
  ['#nq-xhs-14-references', 'xhs-14-references.png'],
  ['#nq-wechat-21x9-cover', 'wechat-21x9-cover.png'],
  ['#nq-wechat-1x1-cover', 'wechat-1x1-cover.png'],
  ['#nq-wechat-cover-pair-preview', 'wechat-cover-pair-preview.png'],
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
