import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { chromium } from 'playwright';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const repoRoot = path.resolve(__dirname, '../../../..');
const mediaDir = path.join(repoRoot, 'media/images/2026-06-08-unified-market-xhs-video');
const assetDir = path.join(mediaDir, 'assets');
const htmlPath = path.join(__dirname, 'index.html');

const rel = (file) => path.relative(__dirname, path.join(assetDir, file)).replaceAll(path.sep, '/');

const refs = [
  '窦皓：《从一条跨省高速，看长三角互联互通》，《人民日报》2026年3月23日第03版。',
  '王乐文、方敏：《河南加快建设全国统一大市场循环枢纽》，《人民日报》2026年3月29日第01版。',
  '张安宇：《建设全国统一大市场，大家都受益》，《人民日报》2026年4月3日第01版。',
  '邵玉姿：《一毫秒，京冀间完成一次“握手”》，《人民日报》2026年4月10日第02版。',
  '王东辉：《超大规模市场优势如何成为发展优势》，《人民日报》2026年4月20日第01版。',
  '程志强、蒋承：《纵深推进全国统一大市场建设》，《人民日报》2026年4月22日第09版。'
];

const pages = [
  {
    id: 'xhs-01-cover',
    no: '01',
    title: '统一大市场\\n别只写“大”',
    tag: '规则 · 设施 · 要素',
    quote: '全国统一大市场不是把“全国”写成一个词，而是把规则、设施、要素和监管协同接成一条流动链。',
    points: ['规则要同', '设施要通', '要素要活'],
    image: 'logistics-xiamen-port.jpg',
    layout: 'hero',
    color: 'mint'
  },
  {
    id: 'xhs-02-three-actions',
    no: '02',
    title: '写具体\\n就抓三件事',
    tag: '总公式',
    quote: '统一大市场要写具体，就抓三件事：规则要同、设施要通、要素要活。',
    points: ['同一把尺子', '通一张网络', '活一池资源'],
    layout: 'formula',
    color: 'lemon'
  },
  {
    id: 'xhs-03-big-to-through',
    no: '03',
    title: '不是市场更大\\n而是市场更通',
    tag: '先破误区',
    quote: '建设全国统一大市场，关键不是把市场做“大”，而是把市场做“通”；不是让各地少发展，而是让各地在统一规则下更公平、更高效地发展。',
    points: ['破地方保护', '破市场分割', '破隐形门槛'],
    layout: 'contrast',
    color: 'blue'
  },
  {
    id: 'xhs-04-rule-attract',
    no: '04',
    title: '地方发展\\n靠环境吸引',
    tag: '规则统一',
    quote: '好的地方发展，不是用壁垒把资源留下来，而是用公平规则和优质环境把企业吸引来。',
    points: ['不拼违规优惠', '不拼隐形门槛', '拼透明规则'],
    image: 'logistics-warehouse.jpg',
    layout: 'photo',
    color: 'peach'
  },
  {
    id: 'xhs-05-rule-supervision',
    no: '05',
    title: '规则统一\\n先破市场分割',
    tag: '监管协同',
    quote: '推进全国统一大市场建设，要以规则统一破除市场分割，以监管协同维护公平竞争，让企业在可预期、可比较、可持续的制度环境中布局发展。',
    points: ['规范招投标', '规范招商引资', '规范涉企执法'],
    layout: 'matrix',
    color: 'lavender'
  },
  {
    id: 'xhs-06-infrastructure-interface',
    no: '06',
    title: '路不只是路\\n还要接口统一',
    tag: '设施互联',
    quote: '统一大市场里的基础设施，不只是看得见的路，更是路背后的标准、接口和协作机制。',
    points: ['省际连接点', '技术标准', '建设时序', '协同机制'],
    image: 'infrastructure-city-bridge.jpg',
    layout: 'photo',
    color: 'mint'
  },
  {
    id: 'xhs-07-digital-infra',
    no: '07',
    title: '设施互联\\n也包括算力网络',
    tag: '数字基础设施',
    quote: '设施互联不只有高速公路和物流通道，也包括算力、电力、数据网络和运维半径。',
    points: ['低时延', '低电价', '稳定供电', '运维便利'],
    image: 'datacenter-server-racks.jpg',
    layout: 'photo',
    color: 'blue'
  },
  {
    id: 'xhs-08-factor-flow',
    no: '08',
    title: '要素流动\\n不是地图位移',
    tag: '进入价值场景',
    quote: '所谓要素流动，不是让资源在地图上移动，而是让资源进入更能创造价值的场景。',
    points: ['资金流', '人才流', '数据流', '企业迁移'],
    image: 'freight-train-containers.jpg',
    layout: 'photo',
    color: 'pink'
  },
  {
    id: 'xhs-09-scale-advantage',
    no: '09',
    title: '规模只是底盘\\n流动才是能力',
    tag: '发展优势',
    quote: '规模只是底盘，流动才是能力；市场只有流得顺、竞争公、场景多，才能从体量优势变成发展优势。',
    points: ['需求被看见', '企业能响应', '技术能试验', '成本能摊薄'],
    image: 'logistics-xiamen-port.jpg',
    layout: 'photo',
    color: 'lemon'
  },
  {
    id: 'xhs-10-exam-formula',
    no: '10',
    title: '申论分论点\\n直接这样写',
    tag: '总公式',
    quote: '以规则统一破壁垒，以设施互联降成本，以要素流动增活力，以监管协同护公平。',
    points: ['破壁垒', '降成本', '增活力', '护公平'],
    layout: 'formula',
    color: 'peach'
  },
  {
    id: 'xhs-11-interview-question',
    no: '11',
    title: '面试题\\n怎么设问',
    tag: '题目原型',
    quote: '某地提出融入全国统一大市场，但企业反映仍存在地方保护、物流成本高、跨区域办事不便、招投标不够公平等问题。领导让你调研并提出建议，你会怎么做？',
    points: ['地方保护', '物流成本高', '办事不便', '招投标不公平'],
    layout: 'question',
    color: 'lavender'
  },
  {
    id: 'xhs-12-answer-close',
    no: '12',
    title: '收束句\\n要落到治理',
    tag: '答题结尾',
    quote: '建设全国统一大市场，不能只停在“让市场更大”，更要让规则更清、设施更通、要素更活、监管更公平。',
    points: ['规则更清', '设施更通', '要素更活', '监管更公平'],
    layout: 'matrix',
    color: 'blue'
  },
  {
    id: 'xhs-13-final-line',
    no: '13',
    title: '最后记住\\n这句高分写法',
    tag: '一句话带走',
    quote: '全国统一大市场的高分写法，不是把市场写大，而是把规则写清、把设施写通、把要素写活。',
    points: ['写清规则', '写通设施', '写活要素'],
    layout: 'closing',
    color: 'mint'
  }
];

const palette = {
  mint: ['#dcf7ef', '#35b89d', '#10251f'],
  lemon: ['#fff5bf', '#e5c73a', '#2f2709'],
  blue: ['#dcefff', '#61a5d8', '#102437'],
  peach: ['#ffe1d2', '#f08a72', '#3a1710'],
  lavender: ['#ece2ff', '#9b80d8', '#21163b'],
  pink: ['#ffe3ed', '#ef85aa', '#3b1422']
};

function cssVars(color) {
  const [bg, accent, ink] = palette[color] || palette.mint;
  return `--bg:${bg};--accent:${accent};--ink:${ink};`;
}

function escapeHtml(s) {
  return String(s)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

function titleHtml(title) {
  return escapeHtml(title).replaceAll('\\n', '<br>');
}

function photoBlock(page) {
  if (!page.image) return '';
  return `<figure class="photo ${page.layout === 'hero' ? 'photo-hero' : ''}">
    <!-- Subject map: ${page.image.includes('port') ? 'container port fills the frame; title sits in the upper-left quiet sky/overlay zone.' : page.image.includes('bridge') ? 'road and rail lines run through center; text panel stays above/lower side without covering key route lines.' : page.image.includes('server') ? 'server racks form repeating texture; text panel uses the left quiet zone.' : page.image.includes('train') ? 'containers occupy right side; text panel stays in left sky/road zone.' : 'warehouse shelves are background evidence; text remains in the card panel.'} -->
    <img src="${rel(page.image)}" alt="" style="object-position:center ${page.image.includes('port') ? '55%' : page.image.includes('bridge') ? '50%' : page.image.includes('server') ? '50%' : page.image.includes('train') ? '54%' : '52%'};">
  </figure>`;
}

function pointsHtml(points = []) {
  return `<div class="points">${points.map((p, i) => `<span><b>${String(i + 1).padStart(2, '0')}</b>${escapeHtml(p)}</span>`).join('')}</div>`;
}

function chainVisual(points = []) {
  const items = points.slice(0, 4);
  return `<div class="chain-visual">${items.map((p, i) => `<span><b>${String(i + 1).padStart(2, '0')}</b>${escapeHtml(p)}</span>`).join('')}</div>`;
}

function renderPage(page) {
  const photo = photoBlock(page);
  if (page.layout === 'hero') {
    return `<section class="poster xhs hero-card" id="${page.id}" style="${cssVars(page.color)}">
      ${photo}<div class="tint"></div><div class="grid"></div>
      <div class="content">
        <div class="top"><span>${page.no}</span><span>统一大市场</span></div>
        <h1>${titleHtml(page.title)}</h1>
        <div class="tag">${escapeHtml(page.tag)}</div>
        <blockquote>${escapeHtml(page.quote)}</blockquote>
        ${pointsHtml(page.points)}
      </div>
    </section>`;
  }
  if (page.layout === 'photo') {
    return `<section class="poster xhs photo-card" id="${page.id}" style="${cssVars(page.color)}">
      <div class="grid"></div>${photo}
      <div class="content">
        <div class="top"><span>${page.no}</span><span>${escapeHtml(page.tag)}</span></div>
        <h1>${titleHtml(page.title)}</h1>
        <blockquote>${escapeHtml(page.quote)}</blockquote>
        ${pointsHtml(page.points)}
      </div>
    </section>`;
  }
  if (page.layout === 'contrast') {
    return `<section class="poster xhs contrast-card" id="${page.id}" style="${cssVars(page.color)}">
      <div class="grid"></div>
      <div class="content">
        <div class="top"><span>${page.no}</span><span>${escapeHtml(page.tag)}</span></div>
        <h1>${titleHtml(page.title)}</h1>
        <div class="duo"><div>写“大”<small>停在结果层</small></div><div>写“通”<small>落到治理链</small></div></div>
        <blockquote>${escapeHtml(page.quote)}</blockquote>
        ${pointsHtml(page.points)}
      </div>
    </section>`;
  }
  if (page.layout === 'question') {
    return `<section class="poster xhs question-card" id="${page.id}" style="${cssVars(page.color)}">
      <div class="grid"></div>
      <div class="content">
        <div class="top"><span>${page.no}</span><span>${escapeHtml(page.tag)}</span></div>
        <h1>${titleHtml(page.title)}</h1>
        <blockquote>${escapeHtml(page.quote)}</blockquote>
        <div class="answer-path">
          <span>查壁垒</span><span>统规则</span><span>通设施</span><span>活要素</span><span>强监管</span>
        </div>
      </div>
    </section>`;
  }
  if (page.layout === 'closing') {
    return `<section class="poster xhs closing-card" id="${page.id}" style="${cssVars(page.color)}">
      <div class="grid"></div>
      <div class="content">
        <div class="top"><span>${page.no}</span><span>${escapeHtml(page.tag)}</span></div>
        <h1>${titleHtml(page.title)}</h1>
        <blockquote>${escapeHtml(page.quote)}</blockquote>
        <div class="big-words"><span>规则清</span><span>设施通</span><span>要素活</span></div>
      </div>
    </section>`;
  }
  return `<section class="poster xhs formula-card" id="${page.id}" style="${cssVars(page.color)}">
    <div class="grid"></div>
    <div class="content">
      <div class="top"><span>${page.no}</span><span>${escapeHtml(page.tag)}</span></div>
      <h1>${titleHtml(page.title)}</h1>
      <blockquote>${escapeHtml(page.quote)}</blockquote>
      ${chainVisual(page.points)}
      ${pointsHtml(page.points)}
    </div>
  </section>`;
}

function renderRefs() {
  return `<section class="poster xhs refs-card" id="xhs-14-references" style="${cssVars('lemon')}">
    <div class="grid"></div>
    <div class="content">
      <div class="top"><span>14</span><span>References</span></div>
      <h1>参考文章</h1>
      <ol>${refs.map((r) => `<li>${escapeHtml(r)}</li>`).join('')}</ol>
    </div>
  </section>`;
}

const html = `<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>全国统一大市场小红书与视频号封面</title>
  <style>
    * { box-sizing: border-box; }
    html, body { margin: 0; padding: 0; }
    body {
      background: #eff2f5;
      font-family: "Inter", "Avenir Next", "Helvetica Neue", "PingFang SC", "Noto Sans SC", "Microsoft YaHei", sans-serif;
      color: var(--ink);
    }
    .stage { width: max-content; display: grid; gap: 36px; padding: 36px; }
    .poster {
      position: relative;
      overflow: hidden;
      isolation: isolate;
      background: var(--bg);
      color: var(--ink);
    }
    .xhs { width: 1080px; height: 1440px; }
    .grid {
      position: absolute;
      inset: 0;
      background:
        linear-gradient(90deg, rgba(20,31,42,.075) 1px, transparent 1px),
        linear-gradient(180deg, rgba(20,31,42,.075) 1px, transparent 1px);
      background-size: 72px 72px;
      z-index: 0;
    }
    .content {
      position: relative;
      z-index: 4;
      height: 100%;
      padding: 58px;
      display: flex;
      flex-direction: column;
    }
    .top {
      display: flex;
      justify-content: space-between;
      align-items: center;
      gap: 28px;
      padding-bottom: 22px;
      border-bottom: 2px solid rgba(0,0,0,.20);
      font-size: 24px;
      line-height: 1;
      font-weight: 850;
      letter-spacing: .02em;
      text-transform: uppercase;
    }
    h1 {
      margin: 34px 0 0;
      font-size: 88px;
      line-height: 1.02;
      letter-spacing: 0;
      font-weight: 780;
    }
    .tag {
      width: fit-content;
      margin-top: 24px;
      padding: 14px 18px;
      background: var(--accent);
      color: #fff;
      font-size: 30px;
      font-weight: 850;
    }
    blockquote {
      margin: 34px 0 0;
      padding: 26px 28px 28px;
      border-left: 10px solid var(--accent);
      background: rgba(255,255,255,.64);
      font-size: 34px;
      line-height: 1.38;
      font-weight: 760;
      letter-spacing: 0;
    }
    .points {
      margin-top: 34px;
      display: grid;
      grid-template-columns: repeat(2, 1fr);
      gap: 18px;
    }
    .points span {
      min-height: 112px;
      padding: 20px 20px;
      display: grid;
      align-content: space-between;
      background: rgba(255,255,255,.56);
      border: 2px solid rgba(0,0,0,.14);
      font-size: 28px;
      line-height: 1.16;
      font-weight: 820;
    }
    .points b {
      display: block;
      margin-bottom: 14px;
      color: var(--accent);
      font-size: 23px;
      font-family: "Avenir Next", "Helvetica Neue", Arial, sans-serif;
    }
    .photo {
      position: absolute;
      inset: auto 58px 58px 58px;
      height: 500px;
      overflow: hidden;
      border: 3px solid rgba(0,0,0,.16);
      z-index: 1;
    }
    .photo img {
      width: 100%;
      height: 100%;
      object-fit: cover;
      filter: saturate(.82) contrast(1.04) brightness(.96);
    }
    .photo-card .content { padding-bottom: 598px; }
    .photo-card blockquote { font-size: 31px; }
    .photo-card .points { position: absolute; left: 58px; right: 58px; bottom: 590px; grid-template-columns: repeat(2, 1fr); }
    .hero-card .photo {
      inset: 0;
      height: 100%;
      border: 0;
    }
    .hero-card .photo img { filter: saturate(.78) contrast(1.02) brightness(.86); }
    .hero-card .tint {
      position: absolute;
      inset: 0;
      z-index: 2;
      background:
        linear-gradient(180deg, rgba(220,247,239,.94) 0%, rgba(220,247,239,.82) 48%, rgba(220,247,239,.25) 100%),
        linear-gradient(90deg, rgba(220,247,239,.96), rgba(220,247,239,.38));
    }
    .hero-card .grid { z-index: 3; }
    .hero-card .content { z-index: 4; }
    .hero-card h1 { font-size: 96px; }
    .hero-card blockquote { max-width: 850px; background: rgba(255,255,255,.76); }
    .duo {
      margin-top: 44px;
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 22px;
    }
    .duo div {
      min-height: 250px;
      padding: 30px;
      display: grid;
      align-content: space-between;
      background: rgba(255,255,255,.56);
      border: 2px solid rgba(0,0,0,.14);
      font-size: 58px;
      font-weight: 780;
    }
    .duo small {
      display: block;
      color: var(--accent);
      font-size: 28px;
      font-weight: 850;
    }
    .formula-card blockquote { font-size: 39px; }
    .chain-visual {
      margin-top: 44px;
      min-height: 300px;
      display: flex;
      gap: 14px;
      align-items: stretch;
    }
    .chain-visual span {
      position: relative;
      flex: 1 1 0;
      display: grid;
      align-content: center;
      justify-items: center;
      text-align: center;
      padding: 20px 16px;
      background: var(--accent);
      color: #fff;
      font-size: 36px;
      line-height: 1.12;
      font-weight: 900;
    }
    .hero-card .points { margin-top: auto; }
    .chain-visual span:not(:last-child)::after {
      content: "";
      position: absolute;
      right: -23px;
      top: 50%;
      transform: translateY(-50%);
      width: 32px;
      height: 4px;
      background: var(--ink);
      z-index: 2;
    }
    .chain-visual b {
      display: block;
      margin-bottom: 20px;
      color: rgba(255,255,255,.68);
      font-size: 26px;
      font-family: "Avenir Next", "Helvetica Neue", Arial, sans-serif;
    }
    .formula-card .points { margin-top: 26px; }
    .formula-card .points span { min-height: 120px; font-size: 31px; }
    .matrix-card .points, .formula-card .points { grid-template-columns: repeat(2, 1fr); }
    .question-card blockquote { font-size: 31px; }
    .answer-path {
      margin-top: auto;
      display: grid;
      grid-template-columns: 1fr;
      gap: 14px;
    }
    .answer-path span {
      padding: 19px 24px;
      background: rgba(255,255,255,.58);
      border-left: 10px solid var(--accent);
      font-size: 34px;
      font-weight: 850;
    }
    .closing-card h1 { font-size: 92px; }
    .closing-card blockquote { font-size: 42px; }
    .big-words {
      margin-top: 80px;
      display: grid;
      grid-template-columns: repeat(3, 1fr);
      gap: 16px;
    }
    .big-words span {
      min-height: 560px;
      display: grid;
      place-items: center;
      background: var(--accent);
      color: #fff;
      font-size: 44px;
      font-weight: 900;
    }
    .refs-card h1 { font-size: 88px; }
    .refs-card ol {
      margin: 40px 0 0;
      padding-left: 40px;
      display: grid;
      gap: 19px;
      font-size: 28px;
      line-height: 1.34;
      font-weight: 700;
    }
    .refs-card li::marker { color: var(--accent); font-weight: 900; }

    .video {
      width: 1080px;
      height: 1440px;
      background: #111;
      color: #fff8ea;
    }
    .video img {
      position: absolute;
      inset: 0;
      width: 100%;
      height: 100%;
      object-fit: cover;
      object-position: center 56%;
      filter: saturate(.88) contrast(1.08) brightness(.78);
      z-index: 0;
    }
    .video::before {
      content: "";
      position: absolute;
      inset: 0;
      z-index: 1;
      background:
        linear-gradient(90deg, rgba(9,14,21,.78) 0%, rgba(9,14,21,.36) 50%, rgba(9,14,21,.08) 100%),
        linear-gradient(180deg, rgba(9,14,21,.52) 0%, rgba(9,14,21,.14) 42%, rgba(9,14,21,.70) 100%);
    }
    .video::after {
      content: "";
      position: absolute;
      inset: 0;
      z-index: 2;
      background-image: radial-gradient(rgba(255,255,255,.18) .55px, transparent .8px);
      background-size: 4px 4px;
      opacity: .24;
      mix-blend-mode: soft-light;
    }
    .video .v-content {
      position: relative;
      z-index: 3;
      height: 100%;
      padding: 68px 72px 62px;
      display: flex;
      flex-direction: column;
    }
    .mast {
      display: flex;
      justify-content: space-between;
      padding-bottom: 18px;
      border-bottom: 1px solid rgba(255,248,234,.58);
      font-family: "Avenir Next", Arial, sans-serif;
      text-transform: uppercase;
      letter-spacing: .12em;
      font-size: 24px;
      font-weight: 850;
    }
    .video h1 {
      margin-top: auto;
      font-family: "Songti SC", "STSong", serif;
      font-size: 118px;
      line-height: .98;
      font-weight: 900;
      color: #fff8ea;
      text-shadow: 0 4px 28px rgba(0,0,0,.42);
    }
    .video .v-tag {
      margin-top: 26px;
      width: fit-content;
      padding: 16px 22px 18px;
      background: rgba(255,248,234,.92);
      color: #111820;
      font-size: 34px;
      font-weight: 900;
    }
    .video .v-bottom {
      margin-top: 48px;
      padding-top: 18px;
      border-top: 1px solid rgba(255,248,234,.50);
      display: flex;
      justify-content: space-between;
      color: rgba(255,248,234,.70);
      font-family: "Avenir Next", Arial, sans-serif;
      text-transform: uppercase;
      letter-spacing: .10em;
      font-size: 16px;
      font-weight: 800;
    }
  </style>
</head>
<body>
  <main class="stage">
    ${pages.map(renderPage).join('\\n')}
    ${renderRefs()}
    <section class="poster video" id="video-cover">
      <!-- Subject map: Xiamen port cranes and containers fill the frame; there are no faces. The main title sits in the left-lower darkened zone, avoiding the dense crane cluster on the right. -->
      <img src="${rel('logistics-xiamen-port.jpg')}" alt="">
      <div class="v-content">
        <div class="mast"><span>Editorial Cover</span><span>3:4</span></div>
        <h1>全国统一<br>大市场</h1>
        <div class="v-tag">规则、设施和要素一起通</div>
        <div class="v-bottom"><span>People Daily Method</span><span>1080×1440</span></div>
      </div>
    </section>
  </main>
</body>
</html>`;

fs.mkdirSync(mediaDir, { recursive: true });
fs.writeFileSync(htmlPath, html);

const browser = await chromium.launch({ headless: true });
const page = await browser.newPage({ viewport: { width: 1180, height: 1540 }, deviceScaleFactor: 1 });
await page.goto(`file://${htmlPath}`, { waitUntil: 'load', timeout: 60000 });
await page.waitForTimeout(1200);

const targets = [
  ...pages.map((page) => [page.id, `${page.id}.png`]),
  ['xhs-14-references', 'xhs-14-references.png'],
  ['video-cover', 'video-cover-unified-market.png']
];

for (const [id, filename] of targets) {
  await page.locator(`#${id}`).screenshot({
    path: path.join(mediaDir, filename),
    animations: 'disabled',
  });
}

await browser.close();
console.log(`Rendered ${targets.length} images to ${mediaDir}`);
