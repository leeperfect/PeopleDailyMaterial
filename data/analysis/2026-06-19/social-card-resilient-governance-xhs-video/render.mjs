import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { chromium } from 'playwright';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const repoRoot = path.resolve(__dirname, '../../../..');
const mediaDir = path.join(repoRoot, 'media/images/2026-06-19-resilient-governance-xhs-video');
const assetDir = path.join(mediaDir, 'assets');
const htmlPath = path.join(__dirname, 'index.html');

const out = (file) => path.join(mediaDir, file);
const rel = (file) => path.relative(__dirname, path.join(assetDir, file)).replaceAll(path.sep, '/');

const pages = [
  {
    id: 'xhs-01-cover',
    no: '01',
    tag: '人民日报材料转申论',
    title: '韧性治理怎么写\\n不是灾后救急',
    kicker: '早识别 / 早前置 / 能联动',
    quote: '不是灾后救急，而是把风险识别、资源前置、预案演练、科技支撑和群众动员提前做成体系。',
    image: 'storm-city.jpg',
    points: ['风险早识别', '资源早前置', '系统能联动'],
    layout: 'cover'
  },
  {
    id: 'xhs-02-mistake',
    no: '02',
    tag: '常见误区',
    title: '别把防灾减灾\\n写成救急清单',
    quote: '只写救援、预案、物资，容易漏掉“灾前系统怎么准备”。',
    points: ['完善应急预案', '加强救援力量', '做好物资保障', '加强宣传教育'],
    notes: ['这些话能写，但还不够高分', '关键要问：风险来之前，系统准备好了什么？'],
    layout: 'mistake'
  },
  {
    id: 'xhs-03-core-quote',
    no: '03',
    tag: '核心判断',
    title: '先换一个\\n治理视角',
    quote: '韧性治理不是灾后救急，而是把风险识别、资源前置、预案演练、科技支撑和群众动员提前做成体系。',
    image: 'flood-water.jpg',
    points: ['风险识别', '资源前置', '预案演练', '科技支撑', '群众动员'],
    layout: 'quotePhoto'
  },
  {
    id: 'xhs-04-risk-early',
    no: '04',
    tag: '第一步',
    title: '风险\\n早识别',
    quote: '把风险识别关口前移，构建监测预警、综合研判、信息共享、快速叫应的风险治理闭环。',
    image: 'weather-satellite.jpg',
    points: ['监测预警', '综合研判', '信息共享', '快速叫应'],
    layout: 'radar'
  },
  {
    id: 'xhs-05-risk-chain',
    no: '05',
    tag: '为什么要前移',
    title: '极端天气\\n不是单点风险',
    quote: '一场强降雨，可能连着内涝、山洪、交通中断、通信受阻和群众转移。',
    image: 'flooded-street.jpg',
    points: ['城市内涝', '山洪地灾', '交通中断', '通信受阻', '群众转移', '物资保障'],
    layout: 'riskChain'
  },
  {
    id: 'xhs-06-resource-front',
    no: '06',
    tag: '第二步',
    title: '资源\\n早前置',
    quote: '预警发出去后，要有人接得住、叫得醒、转得出、安得下。',
    image: 'emergency-kit.jpg',
    points: ['队伍能力', '装备能力', '场所能力', '组织能力'],
    layout: 'resource'
  },
  {
    id: 'xhs-07-plan-live',
    no: '07',
    tag: '预案要能启动',
    title: '预案不能\\n停在纸面',
    quote: '预案不是纸面文本，而是人员、物资、场所、通信、路线和报告流程都能随时启动。',
    points: ['人员', '物资', '场所', '通信', '路线', '报告流程'],
    layout: 'checklist'
  },
  {
    id: 'xhs-08-system-linkage',
    no: '08',
    tag: '第三步',
    title: '系统\\n能联动',
    quote: '韧性治理的核心，是让系统在风险来临时不断线、不失灵、不慌乱。',
    image: 'car-rain.jpg',
    points: ['气象', '应急', '水利', '自然资源', '交通', '基层组织'],
    layout: 'network'
  },
  {
    id: 'xhs-09-tech-social',
    no: '09',
    tag: '支撑层',
    title: '科技支撑\\n群众动员',
    quote: '把“发通知”变成可理解、可体验、可行动的风险教育。',
    image: 'emergency-response.jpg',
    points: ['公开课', '模拟体验', '应急广播', '入户动员', '重点帮扶'],
    layout: 'social'
  },
  {
    id: 'xhs-10-public-selfhelp',
    no: '10',
    tag: '群众能力',
    title: '宣传不是\\n发完就算',
    quote: '防灾减灾宣传的目的，不是让群众知道有风险，而是让群众在风险来临时知道往哪里走、找谁帮、怎么自救。',
    points: ['往哪里走', '找谁帮', '怎么自救'],
    layout: 'publicQuote'
  },
  {
    id: 'xhs-11-five-actions',
    no: '11',
    tag: '国考省考公式',
    title: '韧性治理\\n五个动作',
    quote: '风险早识别 → 资源早前置 → 预案早演练 → 系统能联动 → 群众会自救。',
    points: ['风险早识别', '资源早前置', '预案早演练', '系统能联动', '群众会自救'],
    layout: 'fiveActions'
  },
  {
    id: 'xhs-12-shenlun-argument',
    no: '12',
    tag: '申论总论点',
    title: '一句话\\n写出治理感',
    quote: '提升韧性治理能力，关键是把防灾减灾关口前移，推动风险识别、资源配置、基层能力、科技支撑和群众参与协同发力，构建防抗救一体的全过程治理体系。',
    points: ['关口前移', '协同发力', '防抗救一体', '全过程治理'],
    layout: 'argument'
  },
  {
    id: 'xhs-13-interview',
    no: '13',
    tag: '面试题卡',
    title: '现象认知题\\n这样拆',
    quote: '近年来，极端天气增多。有人认为，防灾减灾关键是灾后救援要快；也有人认为，关键是平时把基础工作做扎实。对此你怎么看？',
    points: ['纠正认识：不能只靠灾后救急', '监测预警：提升识别和叫应能力', '夯实基层：队伍、物资、场所下沉', '系统协同：信息共享、行动联动', '公众能力：懂预警、会避险、能互救'],
    layout: 'interview'
  },
  {
    id: 'xhs-14-closing',
    no: '14',
    tag: '收束金句',
    title: '高分表达\\n落在“平时”',
    quote: '好的韧性治理，不是灾害来了才临时加速，而是平时就让系统有准备、基层有能力、群众有意识。',
    image: 'storm-city.jpg',
    points: ['系统有准备', '基层有能力', '群众有意识'],
    layout: 'closing'
  }
];

const photoMeta = {
  'storm-city.jpg': {
    pos: 'center 47%',
    map: 'lightning sits in the upper-right sky, city skyline fills the lower half; safe title zones are upper-left and lower-left with localized dark tint.'
  },
  'flood-water.jpg': {
    pos: 'center 46%',
    map: 'satellite storm spiral occupies the lower-left and center; safe text zone is the upper-right ocean/land edge after light paper overlay.'
  },
  'weather-satellite.jpg': {
    pos: 'center 52%',
    map: 'satellite hardware sits on the right edge and cloud field fills the center; keep text on the left and lower-left.'
  },
  'flooded-street.jpg': {
    pos: 'center 58%',
    map: 'flood water occupies the foreground and village buildings sit along the upper half; avoid covering the central water line and tower.'
  },
  'emergency-kit.jpg': {
    pos: 'center 52%',
    map: 'gear is spread evenly across the frame; safe text zones are separate panels or the darker lower-left fabric areas.'
  },
  'car-rain.jpg': {
    pos: 'center 52%',
    map: 'car is centered with brake lights around the middle; text must stay in the lower-left or upper-left, away from the car body.'
  },
  'emergency-response.jpg': {
    pos: 'center 50%',
    map: 'red emergency pull button occupies center-left; use it as evidence image, not as title background.'
  }
};

const videos = [
  {
    id: 'video-cover-01',
    image: 'storm-city.jpg',
    title: '韧性治理怎么写\\n不是灾后救急',
    subtitle: '早识别 / 早前置 / 能联动',
    variant: 1
  },
  {
    id: 'video-cover-02',
    image: 'flooded-street.jpg',
    title: '防灾减灾\\n不是灾后救急',
    subtitle: '平时把基础工作做扎实',
    variant: 2
  },
  {
    id: 'video-cover-03',
    image: 'emergency-kit.jpg',
    title: '韧性治理\\n五个动作',
    subtitle: '风险早识别 → 资源早前置 → 群众会自救',
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
  const cls = len > 92 ? 'quote long' : len > 58 ? 'quote med' : 'quote';
  return `<blockquote class="${cls}">${escapeHtml(page.quote)}</blockquote>`;
}

function chips(items = []) {
  return `<div class="chips">${items.map((x) => `<span>${escapeHtml(x)}</span>`).join('')}</div>`;
}

function miniCards(items = []) {
  return `<div class="miniCards">${items.map((x, i) => `<span><b>${String(i + 1).padStart(2, '0')}</b>${escapeHtml(x)}</span>`).join('')}</div>`;
}

function renderPage(page) {
  if (page.layout === 'cover') {
    return `<section class="poster xhs cover" id="${page.id}">
      ${photo(page.image, 'bleed')}<div class="photoTint"></div><div class="grain"></div>
      <div class="content">
        ${top(page)}
        <p class="series">《人民日报》这样写</p>
        <h1>${titleHtml(page.title)}</h1>
        <div class="coverLine">不是灾后救急，而是 <b>${escapeHtml(page.kicker)}</b></div>
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
  if (page.layout === 'quotePhoto') {
    return `<section class="poster xhs quotePhoto" id="${page.id}">
      <div class="paper"></div>${photo(page.image, 'sidePhoto')}
      <div class="content">${top(page)}<h1>${titleHtml(page.title)}</h1>${quoteHtml(page)}${chips(page.points)}</div>
    </section>`;
  }
  if (page.layout === 'radar') {
    return `<section class="poster xhs radar" id="${page.id}">
      <div class="paper"></div>${photo(page.image, 'topWide')}
      <div class="content">${top(page)}<h1>${titleHtml(page.title)}</h1>${quoteHtml(page)}
      <div class="loop">${page.points.map((x, i) => `<span style="--i:${i}"><b>${String(i + 1).padStart(2, '0')}</b>${escapeHtml(x)}</span>`).join('')}</div></div>
    </section>`;
  }
  if (page.layout === 'riskChain') {
    return `<section class="poster xhs riskChain" id="${page.id}">
      <div class="paper"></div>${photo(page.image, 'bottomWide')}
      <div class="content">${top(page)}<h1>${titleHtml(page.title)}</h1>${quoteHtml(page)}
      <div class="chainGrid">${page.points.map((x, i) => `<span><b>${String(i + 1).padStart(2, '0')}</b>${escapeHtml(x)}</span>`).join('')}</div></div>
    </section>`;
  }
  if (page.layout === 'resource') {
    return `<section class="poster xhs resource" id="${page.id}">
      <div class="paper"></div>${photo(page.image, 'resourcePhoto')}
      <div class="content">${top(page)}<h1>${titleHtml(page.title)}</h1>${quoteHtml(page)}${miniCards(page.points)}</div>
    </section>`;
  }
  if (page.layout === 'checklist') {
    return `<section class="poster xhs checklist" id="${page.id}">
      <div class="paper"></div><div class="content">${top(page)}<h1>${titleHtml(page.title)}</h1>${quoteHtml(page)}
      <div class="checkRows">${page.points.map((x, i) => `<span><b>${String(i + 1).padStart(2, '0')}</b>${escapeHtml(x)}<i></i></span>`).join('')}</div></div>
    </section>`;
  }
  if (page.layout === 'network') {
    return `<section class="poster xhs network" id="${page.id}">
      <div class="paper"></div>${photo(page.image, 'networkPhoto')}
      <div class="content">${top(page)}<h1>${titleHtml(page.title)}</h1>${quoteHtml(page)}
      <div class="networkMap">${page.points.map((x, i) => `<span class="n${i + 1}">${escapeHtml(x)}</span>`).join('')}<em></em></div></div>
    </section>`;
  }
  if (page.layout === 'social') {
    return `<section class="poster xhs social" id="${page.id}">
      <div class="paper"></div>${photo(page.image, 'signalPhoto')}
      <div class="content">${top(page)}<h1>${titleHtml(page.title)}</h1>${quoteHtml(page)}
      <div class="signalStack">${page.points.map((x) => `<span>${escapeHtml(x)}</span>`).join('')}</div></div>
    </section>`;
  }
  if (page.layout === 'publicQuote') {
    return `<section class="poster xhs publicQuote" id="${page.id}">
      <div class="paper"></div><div class="content">${top(page)}<h1>${titleHtml(page.title)}</h1>${quoteHtml(page)}
      <div class="threeAnswers">${page.points.map((x) => `<span>${escapeHtml(x)}</span>`).join('')}</div></div>
    </section>`;
  }
  if (page.layout === 'fiveActions') {
    return `<section class="poster xhs fiveActions" id="${page.id}">
      <div class="paper"></div><div class="content">${top(page)}<h1>${titleHtml(page.title)}</h1>${quoteHtml(page)}
      <div class="actionFlow">${page.points.map((x, i) => `<span><b>${String(i + 1).padStart(2, '0')}</b>${escapeHtml(x)}</span>`).join('<i></i>')}</div></div>
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
      <!-- Subject map: ${meta.map} Magazine title uses documented safe area with localized ink tint. -->
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
body{background:#d9ddd7;font-family:"Avenir Next","Helvetica Neue","PingFang SC","Noto Sans SC","Microsoft YaHei",Arial,sans-serif;color:#102723}
.stage{width:max-content;display:grid;gap:34px;padding:34px}
.poster{position:relative;overflow:hidden;isolation:isolate;background:#f3efe4}
.xhs,.video{width:1080px;height:1440px}
.paper{position:absolute;inset:0;z-index:0;background:
  radial-gradient(circle at 86% 9%,rgba(46,111,115,.28),transparent 30%),
  radial-gradient(circle at 10% 94%,rgba(218,111,48,.20),transparent 32%),
  linear-gradient(90deg,rgba(16,39,35,.055) 1px,transparent 1px),
  linear-gradient(180deg,rgba(16,39,35,.052) 1px,transparent 1px),
  linear-gradient(180deg,#f8f4ea,#e8eee8);background-size:auto,auto,72px 72px,72px 72px,auto}
.grain{position:absolute;inset:0;z-index:3;opacity:.26;background:
  repeating-linear-gradient(100deg,rgba(255,255,255,.08) 0 1px,transparent 1px 5px),
  radial-gradient(circle at 22% 16%,rgba(255,255,255,.28),transparent 28%);
  mix-blend-mode:soft-light;pointer-events:none}
.content{position:relative;z-index:5;height:100%;padding:58px;display:flex;flex-direction:column}
.top{display:flex;align-items:center;justify-content:space-between;gap:24px;border-bottom:2px solid rgba(16,39,35,.22);padding-bottom:20px;font-size:24px;line-height:1;font-weight:840}
.top span:first-child{font-size:38px;color:#2f6f73;font-weight:900}
.cover .top,.closing .top{border-bottom-color:rgba(255,255,255,.48);color:#fffdf6}
.cover .top span:first-child,.closing .top span:first-child{color:#ffb35c}
.xhs h1{margin:28px 0 0;font-family:"Songti SC","STSong","Noto Serif CJK SC",serif;font-size:82px;line-height:1.04;font-weight:760;letter-spacing:0}
.quote{margin:28px 0 0;padding:24px 28px;background:rgba(255,253,245,.92);border-left:10px solid #2f6f73;font-size:36px;line-height:1.34;font-weight:820}
.quote.med{font-size:31px;line-height:1.38}
.quote.long{font-size:25px;line-height:1.43}
.photo{margin:0;overflow:hidden}
.photo img,.videoPhoto img{width:100%;height:100%;object-fit:cover;filter:saturate(.78) contrast(1.06) brightness(.91)}
.bleed{position:absolute;inset:0;z-index:1}
.photoTint{position:absolute;inset:0;z-index:2;background:
  linear-gradient(90deg,rgba(7,24,27,.82),rgba(7,24,27,.20) 62%,rgba(7,24,27,.42)),
  linear-gradient(180deg,rgba(7,24,27,.18),rgba(7,24,27,.52) 72%,rgba(7,24,27,.82))}
.series{margin:36px 0 0;color:#ffb35c;font-size:35px;line-height:1;font-weight:900}
.cover h1{margin-top:28px;color:#fffdf6;font-size:91px;max-width:890px}
.coverLine{margin-top:30px;width:890px;padding:20px 24px;background:rgba(255,253,245,.90);color:#102723;font-size:30px;font-weight:860}
.coverLine b{color:#b74f2a}
.coverNodes{margin-top:auto;display:grid;grid-template-columns:1fr 34px 1fr 34px 1fr;align-items:center}
.coverNodes span{height:152px;display:grid;place-items:center;background:#f3efe4;color:#102723;border-top:12px solid #d76f30;font-size:31px;font-weight:900}
.coverNodes span:nth-of-type(2){border-top-color:#2f6f73}.coverNodes span:nth-of-type(3){border-top-color:#d4ad45}
.coverNodes i{height:5px;background:#f3efe4}
.wrongList{margin-top:40px;display:grid;grid-template-columns:repeat(2,1fr);gap:14px}
.wrongList span{height:172px;padding:22px;display:grid;align-content:space-between;background:#fffdf5;border:2px solid rgba(16,39,35,.18);font-size:31px;font-weight:820}
.wrongList b{font-size:23px;color:#d76f30}
.aside{margin-top:auto;display:grid;grid-template-columns:1fr 1fr;gap:14px}
.aside p{min-height:128px;margin:0;padding:22px;background:#102723;color:#fffdf6;font-size:28px;line-height:1.22;font-weight:850}
.sidePhoto{position:absolute;right:0;top:0;bottom:0;width:455px;z-index:1}
.quotePhoto:after{content:"";position:absolute;right:0;top:0;bottom:0;width:620px;z-index:2;background:linear-gradient(90deg,#f8f4ea 0%,rgba(248,244,234,.84) 46%,rgba(248,244,234,.16) 100%)}
.quotePhoto .content{padding-right:420px}
.quotePhoto .quote{font-size:31px;line-height:1.38}
.chips{margin-top:auto;display:grid;grid-template-columns:1fr;gap:12px}
.chips span{height:74px;padding:0 20px;display:flex;align-items:center;background:#102723;color:#fffdf6;border-left:12px solid #d76f30;font-size:28px;font-weight:860}
.topWide{position:absolute;left:58px;right:58px;bottom:58px;height:370px;z-index:1;border:3px solid rgba(47,111,115,.32)}
.radar .content{padding-bottom:505px}
.loop{margin-top:34px;display:grid;grid-template-columns:repeat(4,1fr);gap:12px}
.loop span{height:152px;padding:18px;display:grid;align-content:space-between;background:#102723;color:#fffdf6;font-size:26px;font-weight:880}
.loop span:nth-child(2),.loop span:nth-child(4){background:#2f6f73}
.loop b{color:#ffcf8a;font-size:21px}
.bottomWide{position:absolute;left:58px;right:58px;bottom:58px;height:430px;z-index:1;border:3px solid rgba(47,111,115,.32)}
.riskChain .content{padding-bottom:560px}
.chainGrid{margin-top:38px;display:grid;grid-template-columns:repeat(3,1fr);gap:13px}
.chainGrid span{height:132px;padding:16px;display:grid;align-content:space-between;background:#fffdf5;border-top:12px solid #2f6f73;font-size:24px;font-weight:850}
.chainGrid b{color:#d76f30;font-size:20px}
.resourcePhoto{position:absolute;left:58px;right:58px;bottom:58px;height:405px;z-index:1;border:3px solid rgba(47,111,115,.32)}
.resource .content{padding-bottom:535px}
.miniCards{margin-top:40px;display:grid;grid-template-columns:repeat(4,1fr);gap:12px}
.miniCards span{height:150px;padding:16px;display:grid;align-content:space-between;text-align:center;background:#102723;color:#fffdf6;font-size:26px;font-weight:880}
.miniCards span:nth-child(2),.miniCards span:nth-child(4){background:#2f6f73}
.miniCards b{color:#ffcf8a;font-size:20px}
.checkRows{margin-top:auto;display:grid;grid-template-columns:repeat(2,1fr);gap:14px}
.checkRows span{height:156px;padding:20px 22px;display:grid;grid-template-columns:54px 1fr 38px;align-items:center;background:#fffdf5;border-left:12px solid #2f6f73;font-size:31px;font-weight:880}
.checkRows b{font-size:22px;color:#d76f30}
.checkRows i{width:30px;height:30px;border:4px solid #2f6f73;border-radius:50%;position:relative}
.checkRows i:after{content:"";position:absolute;left:6px;top:4px;width:13px;height:7px;border-left:4px solid #2f6f73;border-bottom:4px solid #2f6f73;transform:rotate(-45deg)}
.networkPhoto{position:absolute;left:58px;right:58px;bottom:58px;height:345px;z-index:1;border:3px solid rgba(47,111,115,.32)}
.network .content{padding-bottom:480px}
.networkMap{margin-top:36px;position:relative;height:345px;background:linear-gradient(135deg,rgba(16,39,35,.08),rgba(47,111,115,.16));border:2px solid rgba(16,39,35,.20)}
.networkMap span{position:absolute;width:152px;height:78px;display:grid;place-items:center;text-align:center;background:#102723;color:#fffdf6;font-size:24px;font-weight:860}
.networkMap .n1{left:46px;top:36px}.networkMap .n2{left:276px;top:22px}.networkMap .n3{right:64px;top:52px}.networkMap .n4{left:84px;bottom:52px}.networkMap .n5{left:378px;bottom:38px}.networkMap .n6{right:76px;bottom:78px;background:#2f6f73}
.networkMap em{position:absolute;left:50%;top:50%;width:190px;height:190px;margin:-95px 0 0 -95px;border:5px solid #d76f30;border-radius:50%}
.signalPhoto{position:absolute;right:58px;bottom:58px;width:420px;height:560px;z-index:1;border:3px solid rgba(47,111,115,.32)}
.social .content{padding-right:530px}
.signalStack{margin-top:auto;display:grid;gap:12px}
.signalStack span{height:82px;padding:0 22px;display:flex;align-items:center;background:#102723;color:#fffdf6;border-left:12px solid #d76f30;font-size:27px;font-weight:860}
.publicQuote h1{font-size:82px}
.publicQuote .quote{font-size:29px;line-height:1.45}
.publicQuote:after{content:"";position:absolute;left:112px;right:112px;top:660px;height:285px;z-index:1;background:
  linear-gradient(90deg,transparent 0 12%,rgba(47,111,115,.32) 12% 12.8%,transparent 12.8% 49.4%,rgba(47,111,115,.32) 49.4% 50.2%,transparent 50.2% 87%,rgba(47,111,115,.32) 87% 87.8%,transparent 87.8%),
  linear-gradient(180deg,transparent 0 48%,rgba(215,111,48,.30) 48% 50%,transparent 50%);
  border:2px solid rgba(16,39,35,.12)}
.threeAnswers{margin-top:auto;display:grid;grid-template-columns:repeat(3,1fr);gap:14px}
.threeAnswers span{height:325px;padding:26px 18px;display:grid;place-items:center;text-align:center;background:#102723;color:#fffdf6;font-size:34px;line-height:1.15;font-weight:900}
.threeAnswers span:nth-child(2){background:#2f6f73}.threeAnswers span:nth-child(3){background:#d76f30}
.fiveActions h1{font-size:86px}
.fiveActions:after{content:"防灾减灾关口前移";position:absolute;left:58px;right:58px;top:620px;height:158px;z-index:1;display:grid;place-items:center;border-top:2px solid rgba(16,39,35,.22);border-bottom:2px solid rgba(16,39,35,.22);color:rgba(16,39,35,.18);font-family:"Songti SC","STSong","Noto Serif CJK SC",serif;font-size:66px;font-weight:800}
.actionFlow{margin-top:auto;display:grid;grid-template-columns:1fr 24px 1fr 24px 1fr 24px 1fr 24px 1fr;align-items:center}
.actionFlow span{height:375px;padding:18px 10px;display:grid;align-content:space-between;text-align:center;background:#102723;color:#fffdf6;font-size:25px;line-height:1.15;font-weight:900}
.actionFlow span:nth-of-type(2),.actionFlow span:nth-of-type(4){background:#2f6f73}.actionFlow span:nth-of-type(5){background:#d76f30}
.actionFlow b{color:#ffcf8a;font-size:22px}
.actionFlow i{height:4px;background:#2f6f73}
.argument .quote{font-size:25px;line-height:1.45}
.argument:after{content:"";position:absolute;left:145px;right:145px;top:620px;height:275px;z-index:1;background:
  radial-gradient(circle at 50% 50%,transparent 0 58px,rgba(47,111,115,.28) 60px 63px,transparent 65px),
  linear-gradient(90deg,transparent 0 49%,rgba(16,39,35,.18) 49% 51%,transparent 51%),
  linear-gradient(180deg,transparent 0 49%,rgba(16,39,35,.18) 49% 51%,transparent 51%)}
.argGrid{margin-top:auto;display:grid;grid-template-columns:repeat(2,1fr);gap:14px}
.argGrid span{height:190px;display:grid;place-items:center;text-align:center;background:#fffdf5;border-top:14px solid #2f6f73;font-size:32px;font-weight:900}
.argGrid span:nth-child(2),.argGrid span:nth-child(4){border-top-color:#d76f30}
.interview .quote{font-size:24px;line-height:1.42}
.answerSteps{margin-top:32px;display:grid;gap:12px}
.answerSteps span{height:106px;padding:0 20px;display:flex;align-items:center;gap:18px;background:#fffdf5;border-left:12px solid #2f6f73;font-size:25px;line-height:1.2;font-weight:850}
.answerSteps b{font-size:21px;color:#d76f30}
.closingTint{position:absolute;inset:0;z-index:2;background:
  linear-gradient(90deg,rgba(7,24,27,.86),rgba(7,24,27,.16) 64%,rgba(7,24,27,.42)),
  linear-gradient(180deg,rgba(7,24,27,.20),rgba(7,24,27,.72))}
.closing h1{color:#fffdf6;font-size:86px}
.closing .quote{margin-top:34px;background:rgba(255,253,245,.93);font-size:30px}
.closingNodes{margin-top:auto;display:grid;grid-template-columns:repeat(3,1fr);gap:14px}
.closingNodes span{height:152px;display:grid;place-items:center;text-align:center;background:#f3efe4;color:#102723;border-top:12px solid #d76f30;font-size:30px;font-weight:900}
.closingNodes span:nth-child(2){border-top-color:#2f6f73}.closingNodes span:nth-child(3){border-top-color:#d4ad45}
.videoPhoto{position:absolute;inset:0;margin:0;z-index:1}
.videoPhoto img{filter:saturate(.82) contrast(1.08) brightness(.72)}
.videoTint{position:absolute;inset:0;z-index:2;background:
  linear-gradient(90deg,rgba(6,22,24,.88),rgba(6,22,24,.18) 70%),
  linear-gradient(180deg,rgba(6,22,24,.14),rgba(6,22,24,.26) 45%,rgba(6,22,24,.74))}
.magLines{position:absolute;inset:56px;z-index:3;border-top:2px solid rgba(255,255,255,.58);border-bottom:2px solid rgba(255,255,255,.42)}
.magLines:before{content:"";position:absolute;left:0;top:94px;width:210px;height:2px;background:rgba(255,255,255,.58)}
.magLines:after{content:"RESILIENCE";position:absolute;right:0;top:24px;color:rgba(255,255,255,.72);font-size:20px;font-weight:820}
.videoTitle{position:absolute;left:64px;right:76px;bottom:92px;z-index:4;color:#fffdf6}
.v1 .videoTitle{top:120px;bottom:auto}.v2 .videoTitle{bottom:122px}.v3 .videoTitle{top:112px;bottom:auto}
.videoTitle p{margin:0 0 28px;color:#ffb35c;font-size:34px;line-height:1;font-weight:900}
.videoTitle h2{margin:0;font-family:"Songti SC","STSong","Noto Serif CJK SC",serif;font-size:90px;line-height:1.02;font-weight:780;letter-spacing:0}
.videoTitle span{display:block;width:max-content;max-width:850px;margin-top:26px;padding:14px 18px;background:#d76f30;color:#fff;font-size:28px;font-weight:900}
.v3 .videoTitle span{font-size:24px}
.preview{width:1800px;background:#d9ddd7;padding:34px;display:grid;grid-template-columns:repeat(5,1fr);gap:18px}
.preview figure{margin:0;background:#fff;padding:8px}
.preview img{width:100%;display:block}
.preview figcaption{padding:8px 2px 0;font-size:16px;font-weight:780;color:#303030}
`;

const html = `<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>韧性治理小红书与视频号封面</title><style>${css}</style></head><body><main class="stage">${pages.map(renderPage).join('\n')}${videos.map(renderVideo).join('\n')}</main></body></html>`;
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
await page.setViewportSize({ width: 1900, height: 1550 });
await page.goto(`file://${previewPath}`, { waitUntil: 'networkidle' });
await page.locator('.preview').screenshot({ path: out('preview-grid.png') });
outputFiles.push('preview-grid.png');

await browser.close();

console.log(JSON.stringify({
  mediaDir,
  count: outputFiles.length,
  files: outputFiles
}, null, 2));
