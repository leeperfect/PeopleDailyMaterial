import { chromium } from 'playwright';
import path from 'path';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const htmlPath = path.join(__dirname, 'index.html');
const outDir = path.join(__dirname, 'output');

const browser = await chromium.launch();
const page = await browser.newPage({ deviceScaleFactor: 2 });

await page.goto(`file://${htmlPath}`, { waitUntil: 'networkidle' });
await page.waitForTimeout(2000); // wait for fonts

// 21:9 main cover
const wide = page.locator('#wechat-21x9');
await wide.screenshot({ path: path.join(outDir, 'wechat-21x9-cover.png') });

// 1:1 square cover
const square = page.locator('#wechat-1x1');
await square.screenshot({ path: path.join(outDir, 'wechat-1x1-cover.png') });

// Pair preview (scroll to it)
const pairPreview = page.locator('.pair-preview');
await pairPreview.scrollIntoViewIfNeeded();
await page.waitForTimeout(500);
await pairPreview.screenshot({ path: path.join(outDir, 'wechat-cover-pair-preview.png') });

await browser.close();
console.log('Done. Images saved to output/');
