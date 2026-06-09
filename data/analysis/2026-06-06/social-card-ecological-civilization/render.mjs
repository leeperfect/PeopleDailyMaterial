import { chromium } from 'playwright';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const htmlPath = path.join(__dirname, 'index.html');
const outDir = path.join(__dirname, 'output');

const targets = [
  ['#eco-xhs-01-cover', 'xhs-01-cover.png'],
  ['#eco-xhs-02-chain', 'xhs-02-chain.png'],
  ['#eco-xhs-03-law', 'xhs-03-law.png'],
  ['#eco-xhs-04-livelihood', 'xhs-04-livelihood.png'],
  ['#eco-xhs-05-three-accounts', 'xhs-05-three-accounts.png'],
  ['#eco-xhs-06-governance', 'xhs-06-governance.png'],
  ['#eco-xhs-07-longterm', 'xhs-07-longterm.png'],
  ['#eco-xhs-08-monitor', 'xhs-08-monitor.png'],
  ['#eco-xhs-09-exam', 'xhs-09-exam.png'],
  ['#eco-xhs-10-essay', 'xhs-10-essay.png'],
  ['#eco-xhs-11-interview', 'xhs-11-interview.png'],
  ['#eco-xhs-12-closing', 'xhs-12-closing.png'],
  ['#eco-xhs-13-references', 'xhs-13-references.png'],
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
