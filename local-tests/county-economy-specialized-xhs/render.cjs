const { chromium } = require('playwright');
const path = require('path');

const TASK_DIR = __dirname;
const HTML_PATH = path.join(TASK_DIR, 'index.html');
const OUTPUT_DIR = path.join(TASK_DIR, 'output');

const targets = [
  ['xhs-01', 'xhs-01-cover.png'],
  ['xhs-02', 'xhs-02-misconception.png'],
  ['xhs-03', 'xhs-03-formula.png'],
  ['xhs-04', 'xhs-04-identify.png'],
  ['xhs-05', 'xhs-05-apple.png'],
  ['xhs-06', 'xhs-06-valuechain.png'],
  ['xhs-07', 'xhs-07-towel.png'],
  ['xhs-08', 'xhs-08-market.png'],
  ['xhs-09', 'xhs-09-cunchao.png'],
  ['xhs-10', 'xhs-10-urbanrural.png'],
  ['xhs-11', 'xhs-11-longterm.png'],
  ['xhs-12', 'xhs-12-shenlun.png'],
  ['xhs-13', 'xhs-13-interview.png'],
  ['xhs-14', 'xhs-14-summary.png'],
];

(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage();
  await page.goto(`file://${HTML_PATH}`, { waitUntil: 'networkidle' });
  // Wait for fonts to load
  await page.evaluate(() => document.fonts.ready);
  await page.waitForTimeout(800);

  for (const [id, filename] of targets) {
    const el = await page.$(`#${id}`);
    if (!el) {
      console.error(`Element #${id} not found`);
      continue;
    }
    await el.screenshot({ path: path.join(OUTPUT_DIR, filename) });
    console.log(`Rendered ${filename}`);
  }

  await browser.close();
  console.log('All done.');
})();
