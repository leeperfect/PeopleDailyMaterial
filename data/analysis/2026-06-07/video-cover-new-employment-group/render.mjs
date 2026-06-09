import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { chromium } from 'playwright';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const repoRoot = path.resolve(__dirname, '../../../..');
const mediaDir = path.join(repoRoot, 'media/images/2026-06-07-new-employment-group-video-cover');
const imagePath = path
  .relative(__dirname, path.join(mediaDir, 'assets/delivery-snow-protection.jpg'))
  .replaceAll(path.sep, '/');
const htmlPath = path.join(__dirname, 'index.html');
const outPath = path.join(mediaDir, 'video-cover-new-employment-group.png');

const html = `<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>新就业群体治理视频号封面</title>
  <style>
    * { box-sizing: border-box; }
    html, body { margin: 0; padding: 0; }
    body {
      min-height: 100vh;
      display: grid;
      place-items: center;
      background: #111;
      font-family: "PingFang SC", "Noto Sans SC", "Microsoft YaHei", sans-serif;
    }
    .cover {
      width: 1080px;
      height: 1440px;
      position: relative;
      overflow: hidden;
      color: #fff8ea;
      background: #0e1114;
      isolation: isolate;
    }
    .cover img {
      position: absolute;
      inset: 0;
      width: 100%;
      height: 100%;
      object-fit: cover;
      object-position: center 52%;
      transform: scale(1.015);
      filter: saturate(.92) contrast(1.06) brightness(.88);
      z-index: 0;
    }
    .cover::before {
      content: "";
      position: absolute;
      inset: 0;
      background:
        radial-gradient(ellipse at 24% 78%, rgba(8,12,16,.76) 0%, rgba(8,12,16,.52) 30%, transparent 58%),
        linear-gradient(105deg, rgba(8,12,16,.72) 0%, rgba(8,12,16,.34) 36%, rgba(8,12,16,.06) 62%),
        linear-gradient(180deg, rgba(8,12,16,.64) 0%, rgba(8,12,16,.14) 47%, rgba(8,12,16,.64) 100%);
      z-index: 1;
    }
    .cover::after {
      content: "";
      position: absolute;
      inset: 0;
      background:
        radial-gradient(circle at 78% 59%, rgba(255,116,46,.42), transparent 16%),
        linear-gradient(90deg, rgba(255,248,234,.10), transparent 26%, transparent 74%, rgba(255,248,234,.08));
      mix-blend-mode: screen;
      opacity: .8;
      z-index: 2;
    }
    .grain {
      position: absolute;
      inset: 0;
      background-image:
        linear-gradient(rgba(255,255,255,.035) 1px, transparent 1px),
        radial-gradient(rgba(255,255,255,.22) .55px, transparent .8px);
      background-size: 100% 6px, 4px 4px;
      opacity: .32;
      mix-blend-mode: soft-light;
      z-index: 3;
    }
    .content {
      position: relative;
      z-index: 4;
      width: 100%;
      height: 100%;
      padding: 70px 72px 64px;
      display: flex;
      flex-direction: column;
    }
    .masthead {
      display: grid;
      grid-template-columns: 1fr auto;
      align-items: start;
      gap: 36px;
      padding-bottom: 18px;
      border-bottom: 1px solid rgba(255,248,234,.62);
      font-family: "Avenir Next", "Helvetica Neue", Arial, sans-serif;
      text-transform: uppercase;
    }
    .brand {
      font-size: 56px;
      line-height: .9;
      font-weight: 800;
      letter-spacing: .02em;
    }
    .brand span {
      display: block;
      margin-top: 7px;
      font-size: 19px;
      line-height: 1.3;
      font-weight: 700;
      letter-spacing: .16em;
      color: rgba(255,248,234,.73);
    }
    .issue {
      text-align: right;
      font-size: 18px;
      line-height: 1.42;
      letter-spacing: .12em;
      color: rgba(255,248,234,.76);
      font-weight: 700;
    }
    .rail {
      position: absolute;
      top: 222px;
      right: 70px;
      writing-mode: vertical-rl;
      font-family: "Avenir Next", "Helvetica Neue", Arial, sans-serif;
      font-size: 17px;
      letter-spacing: .2em;
      color: rgba(255,248,234,.68);
      text-transform: uppercase;
    }
    .title-block {
      position: absolute;
      left: 72px;
      bottom: 172px;
      width: 620px;
    }
    .kicker {
      display: inline-flex;
      align-items: center;
      gap: 16px;
      margin-bottom: 18px;
      font-size: 24px;
      line-height: 1;
      font-weight: 700;
      color: #ff8a3d;
      letter-spacing: .04em;
    }
    .kicker::before {
      content: "";
      display: inline-block;
      width: 78px;
      height: 3px;
      background: #ff8a3d;
    }
    h1 {
      margin: 0;
      font-family: "Songti SC", "STSong", "Noto Serif CJK SC", serif;
      font-size: 82px;
      line-height: 1.02;
      font-weight: 900;
      letter-spacing: 0;
      text-shadow: 0 3px 24px rgba(0,0,0,.44);
    }
    .footer {
      position: absolute;
      left: 72px;
      right: 72px;
      bottom: 64px;
      padding-top: 18px;
      border-top: 1px solid rgba(255,248,234,.52);
      display: flex;
      align-items: end;
      justify-content: space-between;
      gap: 28px;
      font-family: "Avenir Next", "Helvetica Neue", Arial, sans-serif;
      font-size: 16px;
      line-height: 1.35;
      letter-spacing: .12em;
      text-transform: uppercase;
      color: rgba(255,248,234,.68);
      font-weight: 700;
    }
    .seal {
      position: absolute;
      right: 76px;
      bottom: 224px;
      width: 150px;
      height: 150px;
      border: 2px solid rgba(255,248,234,.72);
      border-radius: 50%;
      display: grid;
      place-items: center;
      text-align: center;
      color: rgba(255,248,234,.78);
      font-family: "Avenir Next", "Helvetica Neue", Arial, sans-serif;
      font-size: 16px;
      line-height: 1.25;
      letter-spacing: .13em;
      text-transform: uppercase;
      transform: rotate(-8deg);
    }
  </style>
</head>
<body>
  <section class="cover" id="video-cover">
    <!-- Subject map: rider and orange delivery backpack sit in the middle-lower center; the title is placed in the left-lower dark zone, away from the backpack and helmet. -->
    <img src="${imagePath}" alt="">
    <div class="grain"></div>
    <div class="content">
      <div class="masthead">
        <div class="brand">CITY<br>PARTNERS<span>People Daily Writing Method</span></div>
        <div class="issue">ISSUE 06<br>VIDEO CHANNEL<br>3:4 COVER</div>
      </div>
      <div class="rail">SERVICE / PROTECTION / CO-GOVERNANCE</div>
      <div class="title-block">
        <div class="kicker">《人民日报》这样写</div>
        <h1>就业新群体，<br>不是边缘人</h1>
      </div>
      <div class="seal">Editorial<br>Cover<br>2026</div>
      <div class="footer">
        <span>New Employment Group Governance</span>
        <span>1080×1440</span>
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
