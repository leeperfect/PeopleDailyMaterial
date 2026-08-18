const { chromium } = require('playwright');
const path = require('path');
const fs = require('fs');

const NODE = '/Users/pf.macbookpro/Library/Application Support/Doubao/sandbox_runtime/bases/3e0684285d3c808daafe9161d4088030/bin/node';

const targets = [
  ['#xhs-01', 'xhs-01-cover.png'],
  ['#xhs-02', 'xhs-02-misconception.png'],
  ['#xhs-03', 'xhs-03-framework.png'],
  ['#xhs-04', 'xhs-04-endowment.png'],
  ['#xhs-05', 'xhs-05-apple.png'],
  ['#xhs-06', 'xhs-06-valuechain.png'],
  ['#xhs-07', 'xhs-07-textile.png'],
  ['#xhs-08', 'xhs-08-market.png'],
  ['#xhs-09', 'xhs-09-cunchao.png'],
  ['#xhs-10', 'xhs-10-urbanrural.png'],
  ['#xhs-11', 'xhs-11-persistence.png'],
  ['#xhs-12', 'xhs-12-exam.png'],
  ['#xhs-13', 'xhs-13-interview.png'],
  ['#xhs-14', 'xhs-14-summary.png'],
  ['#xhs-15', 'xhs-15-references.png'],
];

(async () => {
  const outDir = path.join(__dirname, 'output');
  fs.mkdirSync(outDir, { recursive: true });

  const browser = await chromium.launch();
  const page = await browser.newPage({
    viewport: { width: 1200, height: 1600 },
    deviceScaleFactor: 2,
  });

  const htmlPath = path.join(__dirname, 'index.html');
  await page.goto('file://' + htmlPath, { waitUntil: 'networkidle' });

  // Wait for fonts and WebGL
  await page.evaluate(() => document.fonts.ready);
  await page.waitForTimeout(1200);

  for (const [selector, filename] of targets) {
    const el = await page.$(selector);
    if (!el) {
      console.error('NOT FOUND:', selector);
      continue;
    }
    await el.screenshot({ path: path.join(outDir, filename) });
    console.log('OK:', filename);
  }

  await browser.close();
  console.log('Done.');
})();
