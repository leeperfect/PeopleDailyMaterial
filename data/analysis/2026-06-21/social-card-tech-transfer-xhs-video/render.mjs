import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { chromium } from 'playwright';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const repoRoot = path.resolve(__dirname, '../../../..');
const mediaDir = path.join(repoRoot, 'media/images/2026-06-21-tech-transfer-xhs-video');
const assetDir = path.join(mediaDir, 'assets');
const htmlPath = path.join(__dirname, 'index.html');

const out = (file) => path.join(mediaDir, file);
const rel = (file) => path.relative(__dirname, path.join(assetDir, file)).replaceAll(path.sep, '/');

const pages = [
  {
    id: 'xhs-01-cover',
    no: '01',
    tag: '人民日报材料转申论',
    title: '科技成果转化\\n别只写“产学研”',
    kicker: '关键是打通最后一公里',
    image: 'manufacturing-tech.jpg',
    points: ['场景找需求', '服务补断点', '人才接产业', '市场验价值'],
    layout: 'cover'
  },
  {
    id: 'xhs-02-mistake',
    no: '02',
    tag: '常见误区',
    title: '只写合作\\n还没写到转化',
    quote: '加强产学研合作、推动高校和企业对接，这些都对，但还没有回答：门在哪里，路怎么走，堵点谁来清。',
    points: ['主体相加', '论文出校门', '企业来对接', '链条喊得响'],
    notes: ['高分要写：真实场景如何验证', '还要写：服务链如何托举'],
    layout: 'mistake'
  },
  {
    id: 'xhs-03-core-judgement',
    no: '03',
    tag: '核心判断',
    title: '不是论文\\n自然变产品',
    quote: '科技成果转化不是论文自然变产品，而是让技术在真实场景中验证，在服务链中被托举，在人才和市场中变成产业机会。',
    image: 'lab-hero.jpg',
    points: ['真实场景验证', '服务链托举', '人才市场承接'],
    layout: 'quotePhoto'
  },
  {
    id: 'xhs-04-formula',
    no: '04',
    tag: '核心公式',
    title: '考场先记\\n这条转化链',
    quote: '场景找需求 → 服务补断点 → 人才接产业。',
    points: ['场景找需求', '服务补断点', '人才接产业'],
    layout: 'formula'
  },
  {
    id: 'xhs-05-scene-path',
    no: '05',
    tag: '场景牵引',
    title: '第一步\\n先走进真实需求',
    quote: '推动科技成果转化，要让技术在真实场景中找需求、在中试验证中找问题、在产业链配套中找路径。',
    image: 'engineering-prototype.jpg',
    points: ['真实场景', '中试验证', '产业链配套'],
    layout: 'objectPhoto'
  },
  {
    id: 'xhs-06-first-layer',
    no: '06',
    tag: '能力拆解',
    title: '把“有什么技术”\\n改写成“解决什么问题”',
    quote: '科技成果转化的第一层能力，是把“有什么技术”改写成“解决什么问题”。',
    points: ['企业痛点', '行业难题', '公共服务场景', '市场反馈'],
    layout: 'needMatrix'
  },
  {
    id: 'xhs-07-scene-long',
    no: '07',
    tag: '申论表达',
    title: '场景不是陪衬\\n是转化入口',
    quote: '要坚持应用场景牵引科技成果转化，围绕企业需求、产业痛点和公共服务场景，推动科研成果在中试验证、数据供给、供应链配套和市场反馈中持续迭代，让实验室成果真正走向生产线。',
    image: 'engineer-laptop.jpg',
    points: ['中试验证', '数据供给', '供应链配套', '市场反馈'],
    layout: 'extension'
  },
  {
    id: 'xhs-08-service-relay',
    no: '08',
    tag: '服务链',
    title: '最后一公里\\n不是自己扛过去',
    quote: '打通科技成果转化最后一公里，靠的不是单点突破，而是政策、平台、资金、保险、技术经理人共同组成的服务接力。',
    image: 'incubator-meeting.jpg',
    points: ['政策松绑', '平台支撑', '金融助力', '保险分险', '专业撮合'],
    layout: 'photoFeature'
  },
  {
    id: 'xhs-09-service-long',
    no: '09',
    tag: '系统支撑',
    title: '服务补断点\\n才有转得稳',
    quote: '要完善科技成果转化服务链，既在政策端松绑赋能，也在平台端提供设备和中试支撑，在金融端补充长期资本和风险保障，在市场端发挥技术经理人作用，推动成果从“能不能转”走向“转得快、转得稳、转得好”。',
    points: ['政策端', '平台端', '金融端', '市场端'],
    layout: 'governance'
  },
  {
    id: 'xhs-10-ecosystem',
    no: '10',
    tag: '生态承接',
    title: '第三层能力\\n把创新链写到就业链',
    quote: '科技成果转化的第三层能力，是把创新链写到就业链，把产品机会写成产业机会和人才机会。',
    image: 'startup-team.jpg',
    points: ['新企业', '新产业', '新岗位', '新人才'],
    layout: 'darkQuote'
  },
  {
    id: 'xhs-11-talent-market',
    no: '11',
    tag: '产业机会',
    title: '成果要变成\\n企业岗位和人才',
    quote: '要推动科技成果转化与创业就业联动，健全“科技成果+创业”模式，完善智能供需对接、创业孵化、微专业建设、校企协同和数智就业服务，让科技创新不仅形成新产品，也形成新企业、新岗位和新人才。',
    image: 'university-students.jpg',
    points: ['智能供需对接', '创业孵化', '微专业建设', '数智就业服务'],
    layout: 'extension'
  },
  {
    id: 'xhs-12-exam-framework',
    no: '12',
    tag: '考场框架',
    title: '别背散句\\n就背这一链',
    quote: '场景找需求，服务补断点，人才接产业。',
    points: ['场景找需求', '服务补断点', '人才接产业', '市场验价值'],
    layout: 'exam'
  },
  {
    id: 'xhs-13-interview',
    no: '13',
    tag: '面试题卡',
    title: '现象认知题\\n这样切入',
    quote: '有人认为，科技成果转化关键在于加强产学研合作。对此你怎么看？',
    points: ['合作是基础，但不是主体相加', '用场景牵引，让技术真实迭代', '用服务链补齐产权、资金、中试断点', '用人才和创业接住产业机会'],
    layout: 'interview'
  },
  {
    id: 'xhs-14-material-bank',
    no: '14',
    tag: '素材记忆',
    title: '材料怎么记\\n才不会散',
    quote: '隧道无人机看场景，生物医药看服务链，技术经理人看市场翻译，微专业看人才承接，AI 初创看行业落地。',
    image: 'robotics-lab.jpg',
    points: ['场景：隧道运维', '服务：设备资金保险', '市场：技术经理人', '人才：微专业', '应用：AI 初创'],
    layout: 'material'
  },
  {
    id: 'xhs-15-closing',
    no: '15',
    tag: '收束金句',
    title: '不是搬出实验室\\n而是跑通一条路',
    quote: '真正的科技成果转化，不是把成果从实验室搬出来，而是把技术、场景、资本、服务、人才和市场接成一条能跑通的路。',
    image: 'ai-technology.jpg',
    points: ['技术', '场景', '资本', '服务', '人才', '市场'],
    layout: 'closing'
  }
];

const photoMeta = {
  'ai-technology.jpg': {
    pos: 'center 50%',
    map: 'AI chip and circuit texture fill the frame; no faces, title can sit on lower-left dark panel.'
  },
  'biotech-lab.jpg': {
    pos: 'center 50%',
    map: 'bright laboratory benches and equipment; safe as wide evidence image, avoid overlaying small lab details.'
  },
  'engineer-laptop.jpg': {
    pos: 'center 52%',
    map: 'engineer with laptop sits near center-left; use as side image and keep text in paper panel.'
  },
  'engineering-prototype.jpg': {
    pos: 'center 52%',
    map: 'students and equipment concentrate on the right and center; keep text above or separate from photo.'
  },
  'incubator-meeting.jpg': {
    pos: 'center 52%',
    map: 'open office and small team spread across frame; use as lower evidence image, do not cover faces.'
  },
  'lab-equipment.jpg': {
    pos: 'center 50%',
    map: 'laboratory equipment fills the lower frame; good background texture without human faces.'
  },
  'lab-hero.jpg': {
    pos: 'center 46%',
    map: 'researcher hands and pipette sit in the center; use as side photo, not as text overlay.'
  },
  'laptop-learning.jpg': {
    pos: 'center 50%',
    map: 'hands around laptop form a central cluster; use as lower image well with no overlay.'
  },
  'manufacturing-tech.jpg': {
    pos: 'center 53%',
    map: 'factory line and equipment fill frame with open left aisle; title can sit in left dark zone.'
  },
  'robotics-lab.jpg': {
    pos: 'center 53%',
    map: 'orange industrial robot arms dominate the lower-middle; title should stay in paper block or upper-left.'
  },
  'startup-team.jpg': {
    pos: 'center 50%',
    map: 'speaker stands near center, audience lower frame; keep text panel separate or at bottom-left over tint.'
  },
  'university-students.jpg': {
    pos: 'center 50%',
    map: 'students in library cluster at lower-right; use as side/lower image and keep text in panel.'
  }
};

const videos = [
  {
    id: 'video-cover-01',
    image: 'manufacturing-tech.jpg',
    title: '科技成果转化\\n别只写“产学研”',
    subtitle: '关键是打通最后一公里',
    label: 'TECH TRANSFER',
    variant: 1
  },
  {
    id: 'video-cover-02',
    image: 'ai-technology.jpg',
    title: '场景找需求\\n服务补断点\\n人才接产业',
    subtitle: '申论高分链条',
    label: 'LAST MILE',
    variant: 2
  },
  {
    id: 'video-cover-03',
    image: 'robotics-lab.jpg',
    title: '不是论文变产品\\n而是跑通一条路',
    subtitle: '技术 / 场景 / 资本 / 服务 / 人才 / 市场',
    label: 'FROM LAB TO MARKET',
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
  const cls = len > 145 ? 'quote xxl' : len > 112 ? 'quote xl' : len > 82 ? 'quote long' : len > 54 ? 'quote med' : 'quote';
  return `<blockquote class="${cls}">${escapeHtml(page.quote)}</blockquote>`;
}

function cards(items = []) {
  return `<div class="cards">${items.map((x, i) => `<span><b>${String(i + 1).padStart(2, '0')}</b>${escapeHtml(x)}</span>`).join('')}</div>`;
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
  if (page.layout === 'quotePhoto') {
    return `<section class="poster xhs quotePhoto" id="${page.id}">
      <div class="paper"></div>${photo(page.image, 'sidePhoto')}
      <div class="content">${top(page)}<h1>${titleHtml(page.title)}</h1>${quoteHtml(page)}
      <div class="keywordRail">${page.points.map((x) => `<span>${escapeHtml(x)}</span>`).join('')}</div></div>
    </section>`;
  }
  if (page.layout === 'formula') {
    return `<section class="poster xhs formula" id="${page.id}">
      <div class="paper"></div><div class="content">${top(page)}<h1>${titleHtml(page.title)}</h1>${quoteHtml(page)}
      <div class="formulaRail">${page.points.map((x, i) => `<span><b>${String(i + 1).padStart(2, '0')}</b>${escapeHtml(x)}</span>`).join('<i></i>')}</div></div>
    </section>`;
  }
  if (page.layout === 'objectPhoto') {
    return `<section class="poster xhs objectPhoto" id="${page.id}">
      <div class="paper"></div>${photo(page.image, 'bottomWide')}
      <div class="content">${top(page)}<h1>${titleHtml(page.title)}</h1>${quoteHtml(page)}${cards(page.points)}</div>
    </section>`;
  }
  if (page.layout === 'needMatrix') {
    return `<section class="poster xhs needMatrix" id="${page.id}">
      <div class="paper"></div><div class="content">${top(page)}<h1>${titleHtml(page.title)}</h1>${quoteHtml(page)}
      <div class="matrix">${page.points.map((x) => `<span>${escapeHtml(x)}</span>`).join('')}</div></div>
    </section>`;
  }
  if (page.layout === 'photoFeature') {
    return `<section class="poster xhs photoFeature" id="${page.id}">
      <div class="paper"></div>${photo(page.image, 'bottomWide')}
      <div class="content">${top(page)}<h1>${titleHtml(page.title)}</h1>${quoteHtml(page)}
      <div class="serviceStrip">${page.points.map((x) => `<span>${escapeHtml(x)}</span>`).join('')}</div></div>
    </section>`;
  }
  if (page.layout === 'extension') {
    return `<section class="poster xhs extension" id="${page.id}">
      <div class="paper"></div>${photo(page.image, 'rightPhoto')}
      <div class="content">${top(page)}<h1>${titleHtml(page.title)}</h1>${quoteHtml(page)}
      <div class="extensionRows">${page.points.map((x) => `<span>${escapeHtml(x)}</span>`).join('')}</div></div>
    </section>`;
  }
  if (page.layout === 'darkQuote') {
    return `<section class="poster xhs darkQuote" id="${page.id}">
      ${photo(page.image, 'bleed')}<div class="darkTint"></div><div class="grain"></div>
      <div class="content">${top(page)}<h1>${titleHtml(page.title)}</h1>${quoteHtml(page)}
      <div class="darkNodes">${page.points.map((x) => `<span>${escapeHtml(x)}</span>`).join('')}</div></div>
    </section>`;
  }
  if (page.layout === 'governance') {
    return `<section class="poster xhs governance" id="${page.id}">
      <div class="paper"></div><div class="content">${top(page)}<h1>${titleHtml(page.title)}</h1>${quoteHtml(page)}
      <div class="governGrid">${page.points.map((x) => `<span>${escapeHtml(x)}</span>`).join('')}</div></div>
    </section>`;
  }
  if (page.layout === 'exam') {
    return `<section class="poster xhs exam" id="${page.id}">
      <div class="paper"></div><div class="content">${top(page)}<h1>${titleHtml(page.title)}</h1>${quoteHtml(page)}
      <div class="examFlow">${page.points.map((x, i) => `<span><b>${String(i + 1).padStart(2, '0')}</b>${escapeHtml(x)}</span>`).join('<i></i>')}</div></div>
    </section>`;
  }
  if (page.layout === 'interview') {
    return `<section class="poster xhs interview" id="${page.id}">
      <div class="paper"></div><div class="content">${top(page)}<h1>${titleHtml(page.title)}</h1>${quoteHtml(page)}
      <div class="answerSteps">${page.points.map((x, i) => `<span><b>${String(i + 1).padStart(2, '0')}</b>${escapeHtml(x)}</span>`).join('')}</div></div>
    </section>`;
  }
  if (page.layout === 'material') {
    return `<section class="poster xhs material" id="${page.id}">
      <div class="paper"></div>${photo(page.image, 'bottomWide')}
      <div class="content">${top(page)}<h1>${titleHtml(page.title)}</h1>${quoteHtml(page)}
      <div class="materialGrid">${page.points.map((x) => `<span>${escapeHtml(x)}</span>`).join('')}</div></div>
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
      <!-- Subject map: ${meta.map} Magazine title uses documented safe zone. -->
      <img src="${rel(item.image)}" alt="" style="object-position:${meta.pos};">
    </figure>
    <div class="videoTint"></div><div class="magLines" data-label="${escapeHtml(item.label)}"></div>
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
body{background:#d8ddd8;font-family:"Avenir Next","Helvetica Neue","PingFang SC","Noto Sans SC","Microsoft YaHei",Arial,sans-serif;color:#1e2c34}
.stage{width:max-content;display:grid;gap:34px;padding:34px}
.poster{position:relative;overflow:hidden;isolation:isolate;background:#f1f3ec}
.xhs,.video{width:1080px;height:1440px}
.paper{position:absolute;inset:0;z-index:0;background:
  linear-gradient(116deg,rgba(19,38,50,.055) 0 1px,transparent 1px 18px),
  linear-gradient(180deg,#f5f4ea 0%,#edf2ef 54%,#e4ecec 100%)}
.paper:after{content:"";position:absolute;inset:0;background:linear-gradient(90deg,rgba(19,38,50,.08),transparent 28%,transparent 72%,rgba(230,115,42,.10)),repeating-linear-gradient(0deg,rgba(255,255,255,.10) 0 1px,transparent 1px 6px);opacity:.72}
.grain{position:absolute;inset:0;z-index:3;opacity:.22;background:repeating-linear-gradient(105deg,rgba(255,255,255,.10) 0 1px,transparent 1px 5px),linear-gradient(180deg,rgba(255,255,255,.16),rgba(0,0,0,.10));mix-blend-mode:soft-light;pointer-events:none}
.content{position:relative;z-index:5;height:100%;padding:58px;display:flex;flex-direction:column}
.top{display:flex;align-items:center;justify-content:space-between;gap:24px;border-bottom:2px solid rgba(30,44,52,.20);padding-bottom:20px;font-size:24px;line-height:1;font-weight:840}
.top span:first-child{font-size:38px;color:#1f6f8b;font-weight:900}
.cover .top,.darkQuote .top,.closing .top{border-bottom-color:rgba(255,255,255,.46);color:#fbf3df}
.cover .top span:first-child,.darkQuote .top span:first-child,.closing .top span:first-child{color:#f1783c}
.xhs h1{margin:28px 0 0;font-family:"Songti SC","STSong","Noto Serif CJK SC",serif;font-size:78px;line-height:1.05;font-weight:760;letter-spacing:0}
.quote{margin:28px 0 0;padding:24px 28px;background:rgba(255,251,238,.94);border-left:10px solid #1f6f8b;font-size:34px;line-height:1.35;font-weight:820}
.quote.med{font-size:30px;line-height:1.39}
.quote.long{font-size:25px;line-height:1.43}
.quote.xl{font-size:21px;line-height:1.46}
.quote.xxl{font-size:19px;line-height:1.44}
.photo{margin:0;overflow:hidden}
.photo img,.videoPhoto img{width:100%;height:100%;object-fit:cover;filter:saturate(.88) contrast(1.04) brightness(.94)}
.bleed{position:absolute;inset:0;z-index:1}
.coverTint{position:absolute;inset:0;z-index:2;background:linear-gradient(90deg,rgba(17,34,45,.93),rgba(17,34,45,.18) 66%,rgba(17,34,45,.40)),linear-gradient(180deg,rgba(17,34,45,.10),rgba(17,34,45,.36) 62%,rgba(17,34,45,.88))}
.series{margin:36px 0 0;color:#f1783c;font-size:36px;line-height:1;font-weight:900}
.cover h1{margin-top:28px;color:#fbf3df;font-size:86px;max-width:940px}
.coverLine{margin-top:30px;width:850px;padding:20px 24px;background:rgba(255,251,238,.92);color:#1e2c34;font-size:31px;font-weight:880}
.coverNodes{margin-top:auto;display:grid;grid-template-columns:1fr 28px 1fr 28px 1fr 28px 1fr;align-items:center}
.coverNodes span{height:132px;display:grid;place-items:center;text-align:center;background:#f5f4ea;color:#1e2c34;border-top:12px solid #1f6f8b;font-size:28px;font-weight:900}
.coverNodes span:nth-of-type(2){border-top-color:#f1783c}.coverNodes span:nth-of-type(3){border-top-color:#5e8b7e}.coverNodes span:nth-of-type(4){border-top-color:#1e2c34}
.coverNodes i{height:4px;background:#f5f4ea}
.wrongList{margin-top:38px;display:grid;grid-template-columns:repeat(2,1fr);gap:14px}
.wrongList span{height:168px;padding:22px;display:grid;align-content:space-between;background:#fffbee;border:2px solid rgba(30,44,52,.18);font-size:31px;font-weight:820}
.wrongList b{font-size:23px;color:#1f6f8b}
.aside{margin-top:auto;display:grid;grid-template-columns:1fr 1fr;gap:14px}
.aside p{min-height:128px;margin:0;padding:22px;background:#1e2c34;color:#fbf3df;font-size:28px;line-height:1.22;font-weight:850}
.sidePhoto{position:absolute;right:0;top:0;bottom:0;width:460px;z-index:1}
.quotePhoto:after{content:"";position:absolute;right:0;top:0;bottom:0;width:690px;z-index:2;background:linear-gradient(90deg,#f1f3ec 0%,rgba(241,243,236,.92) 50%,rgba(241,243,236,.08) 100%)}
.quotePhoto .content{padding-right:418px}
.quotePhoto .quote{font-size:22px;line-height:1.46}
.keywordRail{margin-top:auto;display:grid;grid-template-columns:repeat(3,1fr);gap:12px}
.keywordRail span{height:118px;display:grid;place-items:center;text-align:center;background:#1e2c34;color:#fbf3df;border-top:12px solid #1f6f8b;font-size:25px;font-weight:900}
.keywordRail span:nth-child(2){border-top-color:#f1783c}.keywordRail span:nth-child(3){border-top-color:#5e8b7e}
.formula .quote,.exam .quote{font-size:33px}
.formulaRail,.examFlow{margin-top:auto;display:grid;grid-template-columns:1fr 30px 1fr 30px 1fr;align-items:center}
.examFlow{grid-template-columns:1fr 24px 1fr 24px 1fr 24px 1fr}
.formulaRail span,.examFlow span{height:335px;padding:20px 16px;display:grid;align-content:space-between;text-align:center;background:#1e2c34;color:#fbf3df;font-size:29px;line-height:1.14;font-weight:900}
.examFlow span{height:300px;font-size:26px}
.formulaRail span:nth-of-type(2),.examFlow span:nth-of-type(2){background:#f1783c;color:#1e2c34}.formulaRail span:nth-of-type(3),.examFlow span:nth-of-type(3){background:#1f6f8b}.examFlow span:nth-of-type(4){background:#5e8b7e;color:#1e2c34}
.formulaRail b,.examFlow b{color:#ffddb5;font-size:22px}
.formulaRail i,.examFlow i{height:4px;background:#1e2c34}
#xhs-04-formula:after{content:"论文 / 专利  →  样品 / 中试  →  产品 / 订单";position:absolute;left:58px;right:58px;top:572px;height:128px;z-index:1;display:grid;place-items:center;background:rgba(31,111,139,.10);border-top:3px solid rgba(31,111,139,.42);border-bottom:3px solid rgba(241,120,60,.36);color:#1e2c34;font-size:34px;font-weight:900}
.bottomWide{position:absolute;left:58px;right:58px;bottom:58px;height:410px;z-index:1;border:3px solid rgba(31,111,139,.30)}
.objectPhoto .content,.photoFeature .content,.material .content{padding-bottom:540px}
.objectPhoto .quote{font-size:25px;line-height:1.42}
.cards{margin-top:30px;display:grid;grid-template-columns:repeat(3,1fr);gap:12px}
.cards span{height:100px;padding:14px;display:grid;align-content:space-between;background:#fffbee;border-top:12px solid #1f6f8b;font-size:22px;line-height:1.14;font-weight:860}
.cards span:nth-child(2){border-top-color:#f1783c}.cards span:nth-child(3){border-top-color:#5e8b7e}
.cards b{font-size:18px;color:#1e2c34}
.matrix{margin-top:38px;display:grid;grid-template-columns:repeat(2,1fr);gap:14px}
.matrix span{height:198px;padding:20px;display:grid;place-items:center;text-align:center;background:#fffbee;border-top:14px solid #1f6f8b;font-size:29px;line-height:1.16;font-weight:900}
.matrix span:nth-child(2),.matrix span:nth-child(3){border-top-color:#f1783c}.matrix span:nth-child(4){border-top-color:#5e8b7e}
.needMatrix:after{content:"技术清单 → 问题清单 → 场景清单";position:absolute;left:58px;right:58px;bottom:88px;height:158px;z-index:1;display:grid;place-items:center;background:#1e2c34;color:#fbf3df;border-top:14px solid #f1783c;font-size:34px;font-weight:900}
.serviceStrip{margin-top:34px;display:grid;grid-template-columns:repeat(5,1fr);gap:10px}
.serviceStrip span{height:134px;padding:10px;display:grid;place-items:center;text-align:center;background:#1e2c34;color:#fbf3df;border-top:12px solid #1f6f8b;font-size:24px;font-weight:900}
.serviceStrip span:nth-child(2),.serviceStrip span:nth-child(4){border-top-color:#f1783c}.serviceStrip span:nth-child(3),.serviceStrip span:nth-child(5){border-top-color:#5e8b7e}
.rightPhoto{position:absolute;right:58px;bottom:58px;width:410px;height:585px;z-index:1;border:3px solid rgba(31,111,139,.30)}
.extension .content{padding-right:500px}
.extension .quote{font-size:19px;line-height:1.44}
.extensionRows{margin-top:auto;display:grid;gap:12px}
.extensionRows span{height:86px;display:grid;place-items:center;text-align:center;background:#1e2c34;color:#fbf3df;border-left:12px solid #1f6f8b;font-size:23px;font-weight:900}
.extensionRows span:nth-child(2),.extensionRows span:nth-child(4){border-left-color:#f1783c}.extensionRows span:nth-child(3){border-left-color:#5e8b7e}
#xhs-07-scene-long:after{content:"真实需求 → 中试验证 → 生产线";position:absolute;left:58px;top:642px;width:474px;height:112px;z-index:1;display:grid;place-items:center;background:rgba(255,251,238,.86);border-left:14px solid #f1783c;color:#1e2c34;font-size:27px;font-weight:900}
#xhs-11-talent-market:after{content:"科技成果 + 创业 = 新企业 / 新岗位 / 新人才";position:absolute;left:58px;top:648px;width:474px;height:124px;z-index:1;display:grid;place-items:center;text-align:center;background:#1e2c34;color:#fbf3df;border-left:14px solid #f1783c;font-size:26px;line-height:1.18;font-weight:900}
.darkTint{position:absolute;inset:0;z-index:2;background:linear-gradient(90deg,rgba(17,34,45,.92),rgba(17,34,45,.18) 67%,rgba(17,34,45,.52)),linear-gradient(180deg,rgba(17,34,45,.12),rgba(17,34,45,.82))}
.darkQuote h1{color:#fbf3df;font-size:78px}
.darkQuote .quote{font-size:24px;line-height:1.43}
.darkNodes{margin-top:auto;display:grid;grid-template-columns:repeat(4,1fr);gap:12px}
.darkNodes span{height:146px;display:grid;place-items:center;text-align:center;background:#f5f4ea;color:#1e2c34;border-top:12px solid #1f6f8b;font-size:26px;font-weight:900}
.darkNodes span:nth-child(2),.darkNodes span:nth-child(4){border-top-color:#f1783c}.darkNodes span:nth-child(3){border-top-color:#5e8b7e}
.governance .quote{font-size:19px;line-height:1.43}
.governGrid{margin-top:36px;display:grid;grid-template-columns:repeat(2,1fr);gap:14px}
.governGrid span{height:190px;padding:20px;display:grid;place-items:center;text-align:center;background:#fffbee;border-top:14px solid #1f6f8b;font-size:31px;line-height:1.16;font-weight:900}
.governGrid span:nth-child(2),.governGrid span:nth-child(3){border-top-color:#f1783c}.governGrid span:nth-child(4){border-top-color:#5e8b7e}
.governance:after{content:"能不能转 → 转得快 → 转得稳 → 转得好";position:absolute;left:58px;right:58px;bottom:88px;height:154px;z-index:1;display:grid;place-items:center;background:#1e2c34;color:#fbf3df;border-top:14px solid #f1783c;font-size:31px;font-weight:900}
.interview .quote{font-size:27px;line-height:1.4}
.answerSteps{margin-top:34px;display:grid;gap:14px}
.answerSteps span{height:108px;padding:0 20px;display:flex;align-items:center;gap:16px;background:#fffbee;border-left:12px solid #1f6f8b;font-size:24px;line-height:1.16;font-weight:850}
.answerSteps span:nth-child(2),.answerSteps span:nth-child(4){border-left-color:#f1783c}.answerSteps span:nth-child(3){border-left-color:#5e8b7e}
.answerSteps b{font-size:20px;color:#1e2c34}
#xhs-12-exam-framework:after{content:"企业痛点  /  公共服务  /  产业链  /  市场订单";position:absolute;left:58px;right:58px;top:622px;height:132px;z-index:1;display:grid;place-items:center;background:rgba(255,251,238,.86);border-left:14px solid #1f6f8b;border-right:14px solid #f1783c;color:#1e2c34;font-size:30px;font-weight:900}
#xhs-13-interview:after{content:"产学研合作是入口，转化成效要看链条能不能跑通";position:absolute;left:58px;right:58px;bottom:92px;height:150px;z-index:1;display:grid;place-items:center;text-align:center;background:#1e2c34;color:#fbf3df;border-top:14px solid #f1783c;font-size:31px;line-height:1.18;font-weight:900}
.material .quote{font-size:23px;line-height:1.42}
.materialGrid{margin-top:30px;display:grid;grid-template-columns:repeat(5,1fr);gap:10px}
.materialGrid span{height:105px;padding:10px;display:grid;place-items:center;text-align:center;background:#fffbee;border-top:12px solid #1f6f8b;font-size:20px;line-height:1.14;font-weight:880}
.materialGrid span:nth-child(2),.materialGrid span:nth-child(4){border-top-color:#f1783c}.materialGrid span:nth-child(3),.materialGrid span:nth-child(5){border-top-color:#5e8b7e}
.closingTint{position:absolute;inset:0;z-index:2;background:linear-gradient(90deg,rgba(17,34,45,.93),rgba(17,34,45,.20) 67%,rgba(17,34,45,.48)),linear-gradient(180deg,rgba(17,34,45,.14),rgba(17,34,45,.82))}
.closing h1{color:#fbf3df;font-size:74px}
.closing .quote{font-size:25px;line-height:1.42}
.closingNodes{margin-top:auto;display:grid;grid-template-columns:repeat(6,1fr);gap:9px}
.closingNodes span{height:128px;display:grid;place-items:center;text-align:center;background:#f5f4ea;color:#1e2c34;border-top:12px solid #1f6f8b;font-size:22px;font-weight:900}
.closingNodes span:nth-child(2),.closingNodes span:nth-child(5){border-top-color:#f1783c}.closingNodes span:nth-child(3),.closingNodes span:nth-child(6){border-top-color:#5e8b7e}
.videoPhoto{position:absolute;inset:0;margin:0;z-index:1}
.videoPhoto img{filter:saturate(.86) contrast(1.08) brightness(.72)}
.videoTint{position:absolute;inset:0;z-index:2;background:linear-gradient(90deg,rgba(17,34,45,.92),rgba(17,34,45,.12) 70%),linear-gradient(180deg,rgba(17,34,45,.10),rgba(17,34,45,.30) 44%,rgba(17,34,45,.84))}
.magLines{position:absolute;inset:56px;z-index:3;border-top:2px solid rgba(255,255,255,.60);border-bottom:2px solid rgba(255,255,255,.42)}
.magLines:before{content:"";position:absolute;left:0;top:94px;width:210px;height:2px;background:rgba(255,255,255,.58)}
.magLines:after{content:attr(data-label);position:absolute;right:0;top:24px;color:rgba(255,255,255,.72);font-size:20px;font-weight:820;letter-spacing:0}
.videoTitle{position:absolute;left:64px;right:76px;bottom:92px;z-index:4;color:#fbf3df}
.videoTitle p{margin:0 0 28px;color:#f1783c;font-size:34px;line-height:1;font-weight:900}
.videoTitle h2{margin:0;font-family:"Songti SC","STSong","Noto Serif CJK SC",serif;font-size:78px;line-height:1.04;font-weight:780;letter-spacing:0;max-width:900px}
.v2 .videoTitle h2{font-size:74px}.v3 .videoTitle h2{font-size:72px}
.videoTitle span{display:block;width:max-content;max-width:890px;margin-top:26px;padding:14px 18px;background:#1f6f8b;color:#fbf3df;font-size:27px;font-weight:900}
.v2 .videoTitle span{background:#f1783c;color:#1e2c34}.v3 .videoTitle span{background:#5e8b7e;color:#fbf3df}
.preview{width:1800px;background:#d8ddd8;padding:34px;display:grid;grid-template-columns:repeat(5,1fr);gap:18px}
.preview figure{margin:0;background:#fffbee;padding:8px}
.preview img{width:100%;display:block}
.preview figcaption{padding:8px 2px 0;font-size:16px;font-weight:780;color:#303030}
`;

const html = `<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>科技成果转化小红书与视频号封面</title><style>${css}</style></head><body><main class="stage">${pages.map(renderPage).join('\n')}${videos.map(renderVideo).join('\n')}</main></body></html>`;
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
