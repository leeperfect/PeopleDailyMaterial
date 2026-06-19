import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { chromium } from 'playwright';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const repoRoot = path.resolve(__dirname, '../../../..');
const mediaDir = path.join(repoRoot, 'media/images/2026-06-19-resource-circulation-xhs-video');
const assetDir = path.join(mediaDir, 'assets');
const htmlPath = path.join(__dirname, 'index.html');

const out = (file) => path.join(mediaDir, file);
const rel = (file) => path.relative(__dirname, path.join(assetDir, file)).replaceAll(path.sep, '/');

const pages = [
  {
    id: 'xhs-01-cover',
    no: '01',
    tag: '人民日报材料转申论',
    title: '资源循环怎么写\\n不是回收旧物',
    kicker: '绿色消费 / 绿色生产 / 产业链再造',
    quote: '不是回收旧物，而是让资源重新进入消费、生产和产业链。',
    image: 'reuse-goods.jpg',
    points: ['绿色消费', '绿色生产', '再生利用', '产业链再造'],
    layout: 'cover'
  },
  {
    id: 'xhs-02-mistake',
    no: '02',
    tag: '常见误区',
    title: '别只写\\n垃圾分类',
    quote: '只写回收、节约、再利用，文章就停在了末端处理。',
    points: ['推进垃圾分类', '加强废品回收', '倡导节约资源', '提高再利用效率'],
    notes: ['这些能写，但不是主线', '高分要写出：消费、生产、场景、产业如何连起来'],
    layout: 'mistake'
  },
  {
    id: 'xhs-03-value-chain',
    no: '03',
    tag: '核心公式',
    title: '先抓住\\n这条价值链',
    quote: '消费更新牵引需求 → 绿色生产重塑供给 → 再生利用延长价值 → 产业链再造形成增长点。',
    image: 'reuse-goods.jpg',
    points: ['消费更新', '绿色生产', '再生利用', '产业链再造'],
    layout: 'formulaPhoto'
  },
  {
    id: 'xhs-04-consumption',
    no: '04',
    tag: '消费端',
    title: '以旧换新\\n不只是买新换旧',
    quote: '以旧换新不是简单的新老交替，而是以绿色消费牵引产品升级、服务延伸和资源循环。',
    image: 'ev-charging.jpg',
    points: ['降低换新门槛', '激活改善型需求', '牵引绿色智能产品', '带动回收服务'],
    layout: 'consumer'
  },
  {
    id: 'xhs-05-consumption-chain',
    no: '05',
    tag: '消费牵引',
    title: '换新背后\\n是产业链延伸',
    quote: '从新车销售到二手车评估、电池回收，从家电换新到研发升级，消费端正在倒逼供给端变化。',
    image: 'ev-charging.jpg',
    points: ['消费者：降低成本', '企业：产品升级', '产业链：回收评估拆解', '后市场：服务延伸'],
    layout: 'chainCards'
  },
  {
    id: 'xhs-06-production',
    no: '06',
    tag: '生产端',
    title: '绿色产品\\n也要绿色生产',
    quote: '绿色制造不是末端减排，而是能源供给、生产工艺、资源循环、数字管碳和供应链协同的全链条再造。',
    image: 'manufacturing-line.jpg',
    points: ['能源要绿', '工艺要改', '资源要循环', '数据要管', '供应链协同'],
    layout: 'production'
  },
  {
    id: 'xhs-07-green-manufacture',
    no: '07',
    tag: '生产链条',
    title: '把“节能减排”\\n写具体',
    quote: '绿电、节水、中水回用、固废资源化、能碳平台，才构成绿色制造的完整链条。',
    image: 'solar-factory.jpg',
    points: ['绿电供能', '节能技改', '中水回用', '固废资源化', '能碳平台'],
    layout: 'productionMap'
  },
  {
    id: 'xhs-08-zero-carbon',
    no: '08',
    tag: '场景端',
    title: '零碳不是\\n一个项目',
    quote: '零碳场景的价值，不只在于少排放，更在于把能源、交通、固废、建筑、产业和生活方式重新组织起来。',
    image: 'wind-turbine.jpg',
    points: ['能源', '交通', '固废', '建筑', '产业', '生活方式'],
    layout: 'zeroCarbon'
  },
  {
    id: 'xhs-09-scene-extension',
    no: '09',
    tag: '场景延伸',
    title: '循环要进\\n园区城市乡村',
    quote: '资源循环不是孤立动作，而是一个地方发展方式的变化。',
    image: 'solar-field.jpg',
    points: ['零碳园区', '零碳岛', '无废城市', '绿色交通', '农旅融合'],
    layout: 'scene'
  },
  {
    id: 'xhs-10-industry',
    no: '10',
    tag: '产业端',
    title: '再生资源\\n不是低端回收',
    quote: '再生资源不是低端回收，而是推动资源型产业延链补链、城市治理绿色转型和新增长点培育的重要抓手。',
    image: 'recycling-plant.jpg',
    points: ['延链补链', '精深加工', '无废城市', '绿色金融', '数字治理'],
    layout: 'industry'
  },
  {
    id: 'xhs-11-system-governance',
    no: '11',
    tag: '系统治理',
    title: '从回收利用\\n走向系统治理',
    quote: '资源循环不是企业单点行为，也要靠无废城市、绿色金融、监测感知和闭环处置一起发力。',
    image: 'industrial-factory.jpg',
    points: ['产业链再造', '城市治理再造', '金融支持再造', '数字治理再造'],
    layout: 'governance'
  },
  {
    id: 'xhs-12-exam-formula',
    no: '12',
    tag: '考场公式',
    title: '考场直接\\n套这条线',
    quote: '消费更新牵引需求 → 绿色生产重塑供给 → 再生利用延长价值 → 产业链再造形成增长点。',
    points: ['消费端：绿色消费牵引需求', '生产端：绿色制造重塑供给', '场景端：零碳无废嵌入生活', '产业端：再生资源培育增长点'],
    layout: 'examFormula'
  },
  {
    id: 'xhs-13-argument',
    no: '13',
    tag: '申论总论点',
    title: '一句话\\n写出深度',
    quote: '推动资源循环利用，不能停留在末端回收，而要以绿色消费牵引需求升级，以绿色制造推动供给升级，以再生资源利用促进产业链升级，形成节约资源、减少排放、扩大内需和培育新动能的系统工程。',
    points: ['需求升级', '供给升级', '产业链升级', '系统工程'],
    layout: 'argument'
  },
  {
    id: 'xhs-14-interview',
    no: '14',
    tag: '面试题卡',
    title: '现象认知题\\n这样拆',
    quote: '有人说，资源循环就是把旧东西回收再利用。对此你怎么看？',
    points: ['旧物回收只是末端环节', '消费端要发挥牵引作用', '生产端和产业端要形成闭环', '地方治理要提供系统支撑'],
    layout: 'interview'
  },
  {
    id: 'xhs-15-closing',
    no: '15',
    tag: '收束金句',
    title: '不是结束生命\\n而是重新创造价值',
    quote: '资源循环不是让旧物结束生命，而是让资源在新的消费、新的生产和新的产业链中重新创造价值。',
    image: 'wind-turbine.jpg',
    points: ['新的消费', '新的生产', '新的产业链'],
    layout: 'closing'
  }
];

const photoMeta = {
  'reuse-goods.jpg': {
    pos: 'center 48%',
    map: 'aerial circular park pattern sits in the middle; safe title zones are the upper-left and lower-left paths after soft mint tint.'
  },
  'ev-charging.jpg': {
    pos: 'center 52%',
    map: 'EV charging plug occupies the center-right; keep text in the left column or upper-left panel.'
  },
  'manufacturing-line.jpg': {
    pos: 'center 56%',
    map: 'manufacturing line and engineers sit in the lower-right; use image as bottom well or keep title upper-left.'
  },
  'solar-factory.jpg': {
    pos: 'center 52%',
    map: 'solar panels form diagonal fields across the frame; safe text zone is upper-left and separate card blocks.'
  },
  'solar-field.jpg': {
    pos: 'center 58%',
    map: 'solar panels and blue sky create a low horizon; title can sit in upper sky or in separate panels.'
  },
  'wind-turbine.jpg': {
    pos: 'center 50%',
    map: 'wind turbines are small across lower-mid fields with clouds above; safe title zone is left and lower-left under dark tint.'
  },
  'recycling-plant.jpg': {
    pos: 'center 54%',
    map: 'baled recyclable material occupies the right and center, worker silhouette lower-left; title should stay above or in panels.'
  },
  'industrial-factory.jpg': {
    pos: 'center 52%',
    map: 'industrial catwalk and cranes occupy left and right; center-right light area works as atmospheric background under tint.'
  }
};

const videos = [
  {
    id: 'video-cover-01',
    image: 'reuse-goods.jpg',
    title: '资源循环\\n不是回收旧物',
    subtitle: '绿色消费 / 绿色生产 / 产业链再造',
    variant: 1
  },
  {
    id: 'video-cover-02',
    image: 'ev-charging.jpg',
    title: '以旧换新\\n不只是买新换旧',
    subtitle: '绿色消费牵引产品升级和资源循环',
    variant: 2
  },
  {
    id: 'video-cover-03',
    image: 'industrial-factory.jpg',
    title: '资源循环\\n写成产业链再造',
    subtitle: '再生利用 / 延链补链 / 新增长点',
    variant: 3
  }
];

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

function top(page) {
  return `<div class="top"><span>${page.no}</span><span>${escapeHtml(page.tag)}</span></div>`;
}

function photo(file, cls = '') {
  const meta = photoMeta[file];
  return `<figure class="photo ${cls}">
    <!-- Subject map: ${meta.map} -->
    <img src="${rel(file)}" alt="" style="object-position:${meta.pos};">
  </figure>`;
}

function quoteHtml(page) {
  const len = page.quote.length;
  const cls = len > 110 ? 'quote xl' : len > 82 ? 'quote long' : len > 54 ? 'quote med' : 'quote';
  return `<blockquote class="${cls}">${escapeHtml(page.quote)}</blockquote>`;
}

function chipLine(items = []) {
  return `<div class="chipLine">${items.map((x) => `<span>${escapeHtml(x)}</span>`).join('')}</div>`;
}

function numbered(items = []) {
  return `<div class="numbered">${items.map((x, i) => `<span><b>${String(i + 1).padStart(2, '0')}</b>${escapeHtml(x)}</span>`).join('')}</div>`;
}

function renderPage(page) {
  if (page.layout === 'cover') {
    return `<section class="poster xhs cover" id="${page.id}">
      ${photo(page.image, 'bleed')}<div class="coverTint"></div><div class="grain"></div>
      <div class="content">${top(page)}
        <p class="series">《人民日报》这样写</p>
        <h1>${titleHtml(page.title)}</h1>
        <div class="coverLine">${escapeHtml(page.kicker)}</div>
        <div class="coverNodes">${page.points.map((x) => `<span>${escapeHtml(x)}</span>`).join('<i></i>')}</div>
      </div>
    </section>`;
  }
  if (page.layout === 'mistake') {
    return `<section class="poster xhs mistake" id="${page.id}">
      <div class="paper"></div><div class="content">${top(page)}<h1>${titleHtml(page.title)}</h1>${quoteHtml(page)}
      <div class="wrongList">${page.points.map((x, i) => `<span><b>0${i + 1}</b>${escapeHtml(x)}</span>`).join('')}</div>
      <div class="aside">${page.notes.map((x) => `<p>${escapeHtml(x)}</p>`).join('')}</div></div>
    </section>`;
  }
  if (page.layout === 'formulaPhoto') {
    return `<section class="poster xhs formulaPhoto" id="${page.id}">
      <div class="paper"></div>${photo(page.image, 'sidePhoto')}
      <div class="content">${top(page)}<h1>${titleHtml(page.title)}</h1>${quoteHtml(page)}
      <div class="valueChain">${page.points.map((x) => `<span>${escapeHtml(x)}</span>`).join('<i></i>')}</div></div>
    </section>`;
  }
  if (page.layout === 'consumer') {
    return `<section class="poster xhs consumer" id="${page.id}">
      <div class="paper"></div>${photo(page.image, 'bottomWide')}
      <div class="content">${top(page)}<h1>${titleHtml(page.title)}</h1>${quoteHtml(page)}${numbered(page.points)}</div>
    </section>`;
  }
  if (page.layout === 'chainCards') {
    return `<section class="poster xhs chainCards" id="${page.id}">
      <div class="paper"></div>${photo(page.image, 'rightPhoto')}
      <div class="content">${top(page)}<h1>${titleHtml(page.title)}</h1>${quoteHtml(page)}${numbered(page.points)}</div>
    </section>`;
  }
  if (page.layout === 'production') {
    return `<section class="poster xhs production" id="${page.id}">
      <div class="paper"></div>${photo(page.image, 'bottomWide')}
      <div class="content">${top(page)}<h1>${titleHtml(page.title)}</h1>${quoteHtml(page)}
      <div class="productionWheel">${page.points.map((x, i) => `<span class="p${i + 1}">${escapeHtml(x)}</span>`).join('')}<em></em></div></div>
    </section>`;
  }
  if (page.layout === 'productionMap') {
    return `<section class="poster xhs productionMap" id="${page.id}">
      <div class="paper"></div>${photo(page.image, 'topWide')}
      <div class="content">${top(page)}<h1>${titleHtml(page.title)}</h1>${quoteHtml(page)}
      <div class="mapRows">${page.points.map((x, i) => `<span><b>${String(i + 1).padStart(2, '0')}</b>${escapeHtml(x)}<i></i></span>`).join('')}</div></div>
    </section>`;
  }
  if (page.layout === 'zeroCarbon') {
    return `<section class="poster xhs zeroCarbon" id="${page.id}">
      <div class="paper"></div>${photo(page.image, 'bleed softBleed')}<div class="softTint"></div>
      <div class="content">${top(page)}<h1>${titleHtml(page.title)}</h1>${quoteHtml(page)}
      <div class="sceneNodes">${page.points.map((x) => `<span>${escapeHtml(x)}</span>`).join('')}</div></div>
    </section>`;
  }
  if (page.layout === 'scene') {
    return `<section class="poster xhs scene" id="${page.id}">
      <div class="paper"></div>${photo(page.image, 'bottomWide')}
      <div class="content">${top(page)}<h1>${titleHtml(page.title)}</h1>${quoteHtml(page)}${chipLine(page.points)}</div>
    </section>`;
  }
  if (page.layout === 'industry') {
    return `<section class="poster xhs industry" id="${page.id}">
      <div class="paper"></div>${photo(page.image, 'sidePhoto wideSide')}
      <div class="content">${top(page)}<h1>${titleHtml(page.title)}</h1>${quoteHtml(page)}
      <div class="industryGrid">${page.points.map((x) => `<span>${escapeHtml(x)}</span>`).join('')}</div></div>
    </section>`;
  }
  if (page.layout === 'governance') {
    return `<section class="poster xhs governance" id="${page.id}">
      <div class="paper"></div>${photo(page.image, 'bottomWide')}
      <div class="content">${top(page)}<h1>${titleHtml(page.title)}</h1>${quoteHtml(page)}
      <div class="governanceGrid">${page.points.map((x) => `<span>${escapeHtml(x)}</span>`).join('')}</div></div>
    </section>`;
  }
  if (page.layout === 'examFormula') {
    return `<section class="poster xhs examFormula" id="${page.id}">
      <div class="paper"></div><div class="content">${top(page)}<h1>${titleHtml(page.title)}</h1>${quoteHtml(page)}
      <div class="examFlow">${page.points.map((x, i) => `<span><b>${String(i + 1).padStart(2, '0')}</b>${escapeHtml(x)}</span>`).join('<i></i>')}</div></div>
    </section>`;
  }
  if (page.layout === 'argument') {
    return `<section class="poster xhs argument" id="${page.id}">
      <div class="paper"></div><div class="content">${top(page)}<h1>${titleHtml(page.title)}</h1>${quoteHtml(page)}
      <div class="argGrid">${page.points.map((x) => `<span>${escapeHtml(x)}</span>`).join('')}</div></div>
    </section>`;
  }
  if (page.layout === 'interview') {
    return `<section class="poster xhs interview" id="${page.id}">
      <div class="paper"></div><div class="content">${top(page)}<h1>${titleHtml(page.title)}</h1>${quoteHtml(page)}
      <div class="answerSteps">${page.points.map((x, i) => `<span><b>${String(i + 1).padStart(2, '0')}</b>${escapeHtml(x)}</span>`).join('')}</div></div>
    </section>`;
  }
  if (page.layout === 'closing') {
    return `<section class="poster xhs closing" id="${page.id}">
      ${photo(page.image, 'bleed')}<div class="closingTint"></div><div class="grain"></div>
      <div class="content">${top(page)}<h1>${titleHtml(page.title)}</h1>${quoteHtml(page)}
      <div class="closingNodes">${page.points.map((x) => `<span>${escapeHtml(x)}</span>`).join('')}</div></div>
    </section>`;
  }
  return '';
}

function renderVideo(item) {
  const meta = photoMeta[item.image];
  return `<section class="poster video v${item.variant}" id="${item.id}">
    <figure class="videoPhoto">
      <!-- Subject map: ${meta.map} Magazine title uses safe zone with localized dark tint. -->
      <img src="${rel(item.image)}" alt="" style="object-position:${meta.pos};">
    </figure>
    <div class="videoTint"></div><div class="magLines"></div>
    <div class="videoTitle">
      <p>《人民日报》这样写</p>
      <h2>${titleHtml(item.title)}</h2>
      <span>${escapeHtml(item.subtitle)}</span>
    </div>
  </section>`;
}

const css = `
*{box-sizing:border-box}
html,body{margin:0;padding:0}
body{background:#d7ded9;font-family:"Avenir Next","Helvetica Neue","PingFang SC","Noto Sans SC","Microsoft YaHei",Arial,sans-serif;color:#12231e}
.stage{width:max-content;display:grid;gap:34px;padding:34px}
.poster{position:relative;overflow:hidden;isolation:isolate;background:#f3f1e8}
.xhs,.video{width:1080px;height:1440px}
.paper{position:absolute;inset:0;z-index:0;background:
  radial-gradient(circle at 86% 12%,rgba(76,130,150,.24),transparent 31%),
  radial-gradient(circle at 9% 93%,rgba(223,125,82,.20),transparent 34%),
  linear-gradient(90deg,rgba(18,35,30,.052) 1px,transparent 1px),
  linear-gradient(180deg,rgba(18,35,30,.050) 1px,transparent 1px),
  linear-gradient(180deg,#f8f4ea,#dfeee5);background-size:auto,auto,72px 72px,72px 72px,auto}
.grain{position:absolute;inset:0;z-index:3;opacity:.26;background:repeating-linear-gradient(105deg,rgba(255,255,255,.10) 0 1px,transparent 1px 5px),radial-gradient(circle at 24% 18%,rgba(255,255,255,.28),transparent 28%);mix-blend-mode:soft-light;pointer-events:none}
.content{position:relative;z-index:5;height:100%;padding:58px;display:flex;flex-direction:column}
.top{display:flex;align-items:center;justify-content:space-between;gap:24px;border-bottom:2px solid rgba(18,35,30,.22);padding-bottom:20px;font-size:24px;line-height:1;font-weight:840}
.top span:first-child{font-size:38px;color:#3f8c6b;font-weight:900}
.cover .top,.closing .top,.zeroCarbon .top{border-bottom-color:rgba(255,255,255,.45);color:#fffdf6}
.cover .top span:first-child,.closing .top span:first-child,.zeroCarbon .top span:first-child{color:#ffbd74}
.xhs h1{margin:28px 0 0;font-family:"Songti SC","STSong","Noto Serif CJK SC",serif;font-size:82px;line-height:1.04;font-weight:760;letter-spacing:0}
.quote{margin:28px 0 0;padding:24px 28px;background:rgba(255,253,245,.92);border-left:10px solid #3f8c6b;font-size:35px;line-height:1.34;font-weight:820}
.quote.med{font-size:30px;line-height:1.39}
.quote.long{font-size:25px;line-height:1.43}
.quote.xl{font-size:22px;line-height:1.45}
.photo{margin:0;overflow:hidden}
.photo img,.videoPhoto img{width:100%;height:100%;object-fit:cover;filter:saturate(.82) contrast(1.06) brightness(.91)}
.bleed{position:absolute;inset:0;z-index:1}
.coverTint{position:absolute;inset:0;z-index:2;background:linear-gradient(90deg,rgba(7,23,18,.86),rgba(7,23,18,.18) 66%,rgba(7,23,18,.40)),linear-gradient(180deg,rgba(7,23,18,.10),rgba(7,23,18,.40) 72%,rgba(7,23,18,.82))}
.series{margin:36px 0 0;color:#ffbd74;font-size:35px;line-height:1;font-weight:900}
.cover h1{margin-top:28px;color:#fffdf6;font-size:91px;max-width:910px}
.coverLine{margin-top:30px;width:910px;padding:20px 24px;background:rgba(255,253,245,.90);color:#12231e;font-size:30px;font-weight:860}
.coverNodes{margin-top:auto;display:grid;grid-template-columns:1fr 28px 1fr 28px 1fr 28px 1fr;align-items:center}
.coverNodes span{height:132px;display:grid;place-items:center;text-align:center;background:#f3f1e8;color:#12231e;border-top:12px solid #df7d52;font-size:28px;font-weight:900}
.coverNodes span:nth-of-type(2){border-top-color:#3f8c6b}.coverNodes span:nth-of-type(3){border-top-color:#4c8296}.coverNodes span:nth-of-type(4){border-top-color:#c4aa52}
.coverNodes i{height:4px;background:#f3f1e8}
.wrongList{margin-top:40px;display:grid;grid-template-columns:repeat(2,1fr);gap:14px}
.wrongList span{height:172px;padding:22px;display:grid;align-content:space-between;background:#fffdf5;border:2px solid rgba(18,35,30,.18);font-size:31px;font-weight:820}
.wrongList b{font-size:23px;color:#df7d52}
.aside{margin-top:auto;display:grid;grid-template-columns:1fr 1fr;gap:14px}
.aside p{min-height:128px;margin:0;padding:22px;background:#12231e;color:#fffdf6;font-size:28px;line-height:1.22;font-weight:850}
.sidePhoto{position:absolute;right:0;top:0;bottom:0;width:455px;z-index:1}
.formulaPhoto:after,.industry:after{content:"";position:absolute;right:0;top:0;bottom:0;width:620px;z-index:2;background:linear-gradient(90deg,#f8f4ea 0%,rgba(248,244,234,.86) 46%,rgba(248,244,234,.18) 100%)}
.formulaPhoto .content,.industry .content{padding-right:420px}
.formulaPhoto .quote{font-size:30px;line-height:1.38}
.valueChain{margin-top:auto;display:grid;gap:12px}
.valueChain span{height:78px;padding:0 20px;display:flex;align-items:center;background:#12231e;color:#fffdf6;border-left:12px solid #df7d52;font-size:27px;font-weight:880}
.valueChain i{display:none}
.bottomWide{position:absolute;left:58px;right:58px;bottom:58px;height:405px;z-index:1;border:3px solid rgba(63,140,107,.32)}
.consumer .content,.production .content,.scene .content,.governance .content{padding-bottom:535px}
.numbered{margin-top:38px;display:grid;grid-template-columns:repeat(2,1fr);gap:14px}
.numbered span{height:125px;padding:18px;display:grid;align-content:space-between;background:#fffdf5;border-top:12px solid #3f8c6b;font-size:25px;line-height:1.16;font-weight:850}
.numbered b{font-size:20px;color:#df7d52}
.rightPhoto{position:absolute;right:58px;bottom:58px;width:420px;height:560px;z-index:1;border:3px solid rgba(63,140,107,.32)}
.chainCards .content{padding-right:520px}
.chainCards .numbered{grid-template-columns:1fr;margin-top:auto}
.chainCards .numbered span{height:94px}
.productionWheel{margin-top:32px;position:relative;height:310px;background:linear-gradient(135deg,rgba(18,35,30,.08),rgba(63,140,107,.16));border:2px solid rgba(18,35,30,.20)}
.productionWheel span{position:absolute;width:150px;height:74px;display:grid;place-items:center;text-align:center;background:#12231e;color:#fffdf6;font-size:23px;font-weight:860}
.productionWheel .p1{left:54px;top:34px}.productionWheel .p2{left:316px;top:24px}.productionWheel .p3{right:54px;top:62px}.productionWheel .p4{left:170px;bottom:46px}.productionWheel .p5{right:170px;bottom:38px;background:#3f8c6b}
.productionWheel em{position:absolute;left:50%;top:50%;width:142px;height:142px;margin:-71px 0 0 -71px;border:5px solid #df7d52;border-radius:50%}
.topWide{position:absolute;left:58px;right:58px;bottom:58px;height:365px;z-index:1;border:3px solid rgba(63,140,107,.32)}
.productionMap .content{padding-bottom:495px}
.mapRows{margin-top:34px;display:grid;grid-template-columns:repeat(5,1fr);gap:10px}
.mapRows span{height:165px;padding:16px 10px;display:grid;align-content:space-between;text-align:center;background:#12231e;color:#fffdf6;font-size:23px;line-height:1.16;font-weight:880}
.mapRows span:nth-child(2),.mapRows span:nth-child(4){background:#3f8c6b}.mapRows span:nth-child(5){background:#df7d52}
.mapRows b{color:#ffda9c;font-size:19px}.mapRows i{height:4px;background:rgba(255,255,255,.25)}
.softBleed img{filter:saturate(.75) contrast(1.08) brightness(.72)}
.softTint{position:absolute;inset:0;z-index:2;background:linear-gradient(90deg,rgba(8,25,21,.86),rgba(8,25,21,.18) 68%),linear-gradient(180deg,rgba(8,25,21,.08),rgba(8,25,21,.72))}
.zeroCarbon h1{color:#fffdf6;font-size:84px}
.zeroCarbon .quote{font-size:27px;line-height:1.42}
.sceneNodes{margin-top:auto;display:grid;grid-template-columns:repeat(3,1fr);gap:14px}
.sceneNodes span{height:132px;display:grid;place-items:center;text-align:center;background:#f3f1e8;color:#12231e;border-top:12px solid #df7d52;font-size:29px;font-weight:900}
.sceneNodes span:nth-child(2),.sceneNodes span:nth-child(5){border-top-color:#3f8c6b}.sceneNodes span:nth-child(3),.sceneNodes span:nth-child(6){border-top-color:#4c8296}
.chipLine{margin-top:auto;display:grid;grid-template-columns:repeat(5,1fr);gap:10px}
.chipLine span{height:178px;padding:14px 8px;display:grid;place-items:center;text-align:center;background:#12231e;color:#fffdf6;font-size:24px;font-weight:900}
.chipLine span:nth-child(2),.chipLine span:nth-child(4){background:#3f8c6b}.chipLine span:nth-child(5){background:#df7d52}
.wideSide{width:485px}
.industry .content{padding-right:470px}
.industry .quote{font-size:27px;line-height:1.42}
.industryGrid{margin-top:auto;display:grid;grid-template-columns:1fr;gap:11px}
.industryGrid span{height:76px;padding:0 20px;display:flex;align-items:center;background:#12231e;color:#fffdf6;border-left:12px solid #df7d52;font-size:26px;font-weight:860}
.governanceGrid{margin-top:36px;display:grid;grid-template-columns:repeat(2,1fr);gap:14px}
.governanceGrid span{height:140px;display:grid;place-items:center;text-align:center;background:#fffdf5;border-top:12px solid #3f8c6b;font-size:29px;font-weight:900}
.governanceGrid span:nth-child(2),.governanceGrid span:nth-child(4){border-top-color:#df7d52}
.examFormula h1{font-size:83px}
.examFormula:after{content:"价值链";position:absolute;left:58px;right:58px;top:620px;height:160px;z-index:1;display:grid;place-items:center;border-top:2px solid rgba(18,35,30,.20);border-bottom:2px solid rgba(18,35,30,.20);color:rgba(18,35,30,.18);font-family:"Songti SC","STSong","Noto Serif CJK SC",serif;font-size:72px;font-weight:800}
.examFlow{margin-top:auto;display:grid;grid-template-columns:1fr 24px 1fr 24px 1fr 24px 1fr;align-items:center}
.examFlow span{height:335px;padding:20px 12px;display:grid;align-content:space-between;text-align:center;background:#12231e;color:#fffdf6;font-size:24px;line-height:1.18;font-weight:900}
.examFlow span:nth-of-type(2),.examFlow span:nth-of-type(4){background:#3f8c6b}.examFlow span:nth-of-type(3){background:#4c8296}
.examFlow b{color:#ffda9c;font-size:22px}
.examFlow i{height:4px;background:#3f8c6b}
.argument .quote{font-size:22px;line-height:1.47}
.argument:after{content:"";position:absolute;left:150px;right:150px;top:620px;height:255px;z-index:1;background:radial-gradient(circle at 50% 50%,transparent 0 58px,rgba(63,140,107,.28) 60px 63px,transparent 65px),linear-gradient(90deg,transparent 0 49%,rgba(18,35,30,.18) 49% 51%,transparent 51%),linear-gradient(180deg,transparent 0 49%,rgba(18,35,30,.18) 49% 51%,transparent 51%)}
.argGrid{margin-top:auto;display:grid;grid-template-columns:repeat(2,1fr);gap:14px}
.argGrid span{height:180px;display:grid;place-items:center;text-align:center;background:#fffdf5;border-top:14px solid #3f8c6b;font-size:32px;font-weight:900}
.argGrid span:nth-child(2),.argGrid span:nth-child(4){border-top-color:#df7d52}
.interview .quote{font-size:35px}
.answerSteps{margin-top:38px;display:grid;gap:14px}
.answerSteps span{height:118px;padding:0 22px;display:flex;align-items:center;gap:18px;background:#fffdf5;border-left:12px solid #3f8c6b;font-size:27px;line-height:1.18;font-weight:850}
.answerSteps b{font-size:22px;color:#df7d52}
.closingTint{position:absolute;inset:0;z-index:2;background:linear-gradient(90deg,rgba(7,23,18,.86),rgba(7,23,18,.18) 66%,rgba(7,23,18,.40)),linear-gradient(180deg,rgba(7,23,18,.18),rgba(7,23,18,.76))}
.closing h1{color:#fffdf6;font-size:78px}
.closing .quote{margin-top:34px;background:rgba(255,253,245,.93);font-size:29px}
.closingNodes{margin-top:auto;display:grid;grid-template-columns:repeat(3,1fr);gap:14px}
.closingNodes span{height:152px;display:grid;place-items:center;text-align:center;background:#f3f1e8;color:#12231e;border-top:12px solid #df7d52;font-size:30px;font-weight:900}
.closingNodes span:nth-child(2){border-top-color:#3f8c6b}.closingNodes span:nth-child(3){border-top-color:#4c8296}
.videoPhoto{position:absolute;inset:0;margin:0;z-index:1}
.videoPhoto img{filter:saturate(.82) contrast(1.08) brightness(.72)}
.videoTint{position:absolute;inset:0;z-index:2;background:linear-gradient(90deg,rgba(6,22,18,.90),rgba(6,22,18,.16) 70%),linear-gradient(180deg,rgba(6,22,18,.14),rgba(6,22,18,.28) 44%,rgba(6,22,18,.74))}
.magLines{position:absolute;inset:56px;z-index:3;border-top:2px solid rgba(255,255,255,.58);border-bottom:2px solid rgba(255,255,255,.42)}
.magLines:before{content:"";position:absolute;left:0;top:94px;width:210px;height:2px;background:rgba(255,255,255,.58)}
.magLines:after{content:"CIRCULAR";position:absolute;right:0;top:24px;color:rgba(255,255,255,.72);font-size:20px;font-weight:820}
.videoTitle{position:absolute;left:64px;right:76px;bottom:92px;z-index:4;color:#fffdf6}
.v1 .videoTitle{top:116px;bottom:auto}.v2 .videoTitle{bottom:120px}.v3 .videoTitle{top:118px;bottom:auto}
.videoTitle p{margin:0 0 28px;color:#ffbd74;font-size:34px;line-height:1;font-weight:900}
.videoTitle h2{margin:0;font-family:"Songti SC","STSong","Noto Serif CJK SC",serif;font-size:90px;line-height:1.02;font-weight:780;letter-spacing:0}
.videoTitle span{display:block;width:max-content;max-width:850px;margin-top:26px;padding:14px 18px;background:#df7d52;color:#fff;font-size:27px;font-weight:900}
.preview{width:1800px;background:#d7ded9;padding:34px;display:grid;grid-template-columns:repeat(5,1fr);gap:18px}
.preview figure{margin:0;background:#fff;padding:8px}
.preview img{width:100%;display:block}
.preview figcaption{padding:8px 2px 0;font-size:16px;font-weight:780;color:#303030}
`;

const html = `<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>资源循环小红书与视频号封面</title><style>${css}</style></head><body><main class="stage">${pages.map(renderPage).join('\n')}${videos.map(renderVideo).join('\n')}</main></body></html>`;
fs.writeFileSync(htmlPath, html, 'utf8');

const browser = await chromium.launch({ headless: true });
const page = await browser.newPage({ viewport: { width: 1200, height: 1600 }, deviceScaleFactor: 1 });
await page.goto(`file://${htmlPath}`, { waitUntil: 'networkidle' });

const outputFiles = [];
for (const item of pages) {
  const file = `${item.id}.png`;
  await page.locator(`#${item.id}`).screenshot({ path: out(file) });
  outputFiles.push(file);
}

for (const item of videos) {
  const file = `${item.id}.png`;
  await page.locator(`#${item.id}`).screenshot({ path: out(file) });
  outputFiles.push(file);
}

const previewPath = path.join(__dirname, 'preview.html');
fs.writeFileSync(previewPath, `<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><style>${css}</style></head><body><section class="preview">${outputFiles.map((file) => `<figure><img src="${path.relative(__dirname, out(file)).replaceAll(path.sep, '/')}" alt=""><figcaption>${file}</figcaption></figure>`).join('')}</section></body></html>`, 'utf8');
await page.setViewportSize({ width: 1900, height: 1700 });
await page.goto(`file://${previewPath}`, { waitUntil: 'networkidle' });
await page.locator('.preview').screenshot({ path: out('preview-grid.png') });
outputFiles.push('preview-grid.png');

await browser.close();

console.log(JSON.stringify({
  mediaDir,
  count: outputFiles.length,
  files: outputFiles
}, null, 2));
