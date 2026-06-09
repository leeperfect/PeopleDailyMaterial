import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { chromium } from 'playwright';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const repoRoot = path.resolve(__dirname, '../../../..');
const mediaDir = path.join(repoRoot, 'media/images/2026-06-07-digital-governance-video-cover');
const imagePath = path.relative(__dirname, path.join(repoRoot, 'media/images/2026-06-07-digital-governance-xhs/assets/server-racks-data.jpg')).replaceAll(path.sep, '/');
const htmlPath = path.join(__dirname, 'index.html');
const outPath = path.join(mediaDir, 'video-cover-digital-governance.png');

const html = `<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>数字治理视频号封面</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Noto+Serif+SC:wght@500;600;700;800&family=Noto+Sans+SC:wght@400;500;600;700&family=IBM+Plex+Mono:wght@400;500;600&display=swap">
  <style>
    * { box-sizing: border-box; }
    html, body { margin: 0; padding: 0; }
    body {
      min-height: 100vh;
      display: grid;
      place-items: center;
      background: #111;
      font-family: "Noto Sans SC", -apple-system, BlinkMacSystemFont, "PingFang SC", sans-serif;
    }
    .cover {
      width: 1080px;
      height: 1440px;
      position: relative;
      overflow: hidden;
      color: #fff9ef;
      background: #111;
      isolation: isolate;
    }
    .cover img {
      position: absolute;
      inset: 0;
      width: 100%;
      height: 100%;
      object-fit: cover;
      object-position: center 48%;
      transform: scale(1.015);
      filter: saturate(.82) contrast(1.04) brightness(.92);
      z-index: 0;
    }
    .cover::before {
      content: "";
      position: absolute;
      inset: 0;
      background:
        linear-gradient(90deg, rgba(11,15,19,.28) 0%, rgba(11,15,19,.10) 42%, rgba(11,15,19,.52) 100%),
        linear-gradient(180deg, rgba(11,15,19,.22) 0%, transparent 35%, rgba(11,15,19,.72) 100%);
      z-index: 1;
    }
    .cover::after {
      content: "";
      position: absolute;
      left: -120px;
      bottom: 150px;
      width: 840px;
      height: 640px;
      background: radial-gradient(circle at 25% 50%, rgba(248,237,213,.48), rgba(248,237,213,.08) 55%, transparent 72%);
      mix-blend-mode: screen;
      z-index: 1;
    }
    .grain {
      position: absolute;
      inset: 0;
      background-image: radial-gradient(rgba(255,255,255,.16) .6px, transparent .8px);
      background-size: 4px 4px;
      opacity: .28;
      mix-blend-mode: soft-light;
      z-index: 2;
    }
    .content {
      position: relative;
      z-index: 3;
      width: 100%;
      height: 100%;
      padding: 72px 74px 68px;
      display: flex;
      flex-direction: column;
    }
    .masthead {
      display: grid;
      grid-template-columns: 1fr auto;
      align-items: start;
      gap: 34px;
      padding-bottom: 18px;
      border-bottom: 1px solid rgba(255,249,239,.55);
      font-family: "IBM Plex Mono", monospace;
      letter-spacing: .13em;
      text-transform: uppercase;
    }
    .masthead .brand {
      font-size: 34px;
      line-height: 1.05;
      font-weight: 600;
    }
    .masthead .issue {
      text-align: right;
      font-size: 19px;
      line-height: 1.35;
      color: rgba(255,249,239,.74);
    }
    .side {
      position: absolute;
      top: 208px;
      right: 72px;
      writing-mode: vertical-rl;
      font-family: "IBM Plex Mono", monospace;
      font-size: 17px;
      letter-spacing: .22em;
      color: rgba(255,249,239,.70);
      text-transform: uppercase;
    }
    .title-block {
      margin-top: auto;
      max-width: 830px;
    }
    .label {
      display: inline-flex;
      align-items: center;
      gap: 14px;
      margin-bottom: 28px;
      font-family: "IBM Plex Mono", monospace;
      font-size: 20px;
      letter-spacing: .14em;
      color: rgba(255,249,239,.78);
      text-transform: uppercase;
    }
    .label::before {
      content: "";
      display: inline-block;
      width: 78px;
      height: 2px;
      background: #fff9ef;
    }
    h1 {
      margin: 0;
      font-family: "Noto Serif SC", serif;
      font-size: 136px;
      line-height: .98;
      letter-spacing: 0;
      font-weight: 800;
      text-shadow: 0 2px 18px rgba(0,0,0,.28);
    }
    .subtitle {
      margin-top: 34px;
      width: fit-content;
      padding: 15px 22px 17px;
      background: rgba(255,249,239,.88);
      color: #121212;
      font-size: 36px;
      line-height: 1.25;
      font-weight: 700;
      letter-spacing: .02em;
    }
    .dek {
      margin-top: 26px;
      display: grid;
      grid-template-columns: repeat(3, auto);
      justify-content: start;
      gap: 18px;
      font-size: 24px;
      color: rgba(255,249,239,.82);
      font-weight: 600;
    }
    .dek span {
      border: 1px solid rgba(255,249,239,.42);
      padding: 10px 14px 12px;
      backdrop-filter: blur(4px);
      background: rgba(16,18,22,.18);
    }
    .bottom {
      margin-top: 46px;
      display: flex;
      justify-content: space-between;
      align-items: end;
      border-top: 1px solid rgba(255,249,239,.50);
      padding-top: 18px;
      font-family: "IBM Plex Mono", monospace;
      letter-spacing: .12em;
      text-transform: uppercase;
      font-size: 16px;
      color: rgba(255,249,239,.68);
    }
  </style>
</head>
<body>
  <section class="cover" id="video-cover">
    <!-- Subject map: server rack texture and colored cables sit on the right; left-lower corridor is a quiet zone for the large Chinese title. -->
    <img src="${imagePath}" alt="">
    <div class="grain"></div>
    <div class="content">
      <div class="masthead">
        <div class="brand">DIGITAL<br>GOVERNANCE</div>
        <div class="issue">ISSUE 07<br>PEOPLE DAILY METHOD<br>2026</div>
      </div>
      <div class="side">PROCESS REDESIGN / OFFLINE SAFEGUARD</div>
      <div class="title-block">
        <div class="label">E-MAGAZINE COVER</div>
        <h1>数字治理<br>不是上系统</h1>
        <div class="subtitle">关键是流程再造和线下兜底</div>
        <div class="dek">
          <span>少跑腿</span>
          <span>少填表</span>
          <span>有人负责</span>
        </div>
        <div class="bottom">
          <span>VIDEO CHANNEL COVER</span>
          <span>3:4 / 1080×1440</span>
        </div>
      </div>
    </div>
  </section>
</body>
</html>`;

fs.mkdirSync(mediaDir, { recursive: true });
fs.writeFileSync(htmlPath, html);

const browser = await chromium.launch({ headless: true });
const page = await browser.newPage({ viewport: { width: 1180, height: 1520 }, deviceScaleFactor: 1 });
await page.goto(`file://${htmlPath}`, { waitUntil: 'load', timeout: 60000 });
await page.waitForTimeout(1200);
await page.locator('#video-cover').screenshot({ path: outPath, animations: 'disabled' });
await browser.close();
console.log(`Rendered cover to ${outPath}`);
