import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { chromium } from 'playwright';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const repoRoot = path.resolve(__dirname, '../../../..');
const mediaDir = path.join(repoRoot, 'media/images/2026-06-23-employment-chain-xhs-video');
const assetDir = path.join(mediaDir, 'assets');
const htmlPath = path.join(__dirname, 'index.html');

const out = (file) => path.join(mediaDir, file);
const rel = (file) => path.relative(__dirname, path.join(assetDir, file)).replaceAll(path.sep, '/');

const pages = [
  {
    id: 'xhs-01-cover',
    no: '01',
    tag: '人民日报材料转申论',
    title: '就业难\\n不能只写多给岗位',
    kicker: '要写出一条就业链',
    image: 'job-fair-wide.jpg',
    points: ['产业造岗', '技能练岗', '服务送岗', '创业带岗', '权益稳岗'],
    layout: 'cover'
  },
  {
    id: 'xhs-02-mistake',
    no: '02',
    tag: '低分误区',
    title: '很多人写就业难\\n只会三句话',
    quote: '增加就业岗位、加强职业培训、鼓励自主创业。这些话不能说错，但没有讲清岗位为什么难找、能力为什么接不上、服务为什么送不到。',
    points: ['岗位多一点', '培训多一点', '创业多一点', '宣传多一点'],
    layout: 'mistake'
  },
  {
    id: 'xhs-03-core-chain',
    no: '03',
    tag: '核心判断',
    title: '真正高分框架\\n把就业写成一条链',
    quote: '破解就业难，不是单点增加岗位供给，而是把产业造岗、技能练岗、服务送岗、创业带岗、权益稳岗连成一条就业链。',
    points: ['产业造岗', '技能练岗', '服务送岗', '创业带岗', '权益稳岗'],
    layout: 'formula'
  },
  {
    id: 'xhs-04-industry',
    no: '04',
    tag: '一、产业造岗',
    title: '就业难先看\\n岗位为什么变了',
    quote: '就业难的深层问题，是产业升级带来岗位结构变化，而劳动者的技能、信息和服务还没有完全跟上。',
    image: 'data-center-server.jpg',
    points: ['数据标注员', '无人驾驶集控员', '工业软件岗位', 'AI服务商'],
    layout: 'quotePhoto'
  },
  {
    id: 'xhs-05-new-job',
    no: '05',
    tag: '岗位重塑',
    title: '技术变革\\n不只是机器替人',
    quote: '技术变革不是只有“机器替人”一面，也有“岗位重塑”一面。',
    image: 'code-laptop.jpg',
    points: ['新技术催生基础岗位', '老岗位转向数据操控', '软件嵌入千行百业'],
    layout: 'objectPhoto'
  },
  {
    id: 'xhs-06-skill',
    no: '06',
    tag: '二、技能练岗',
    title: '培训不能只写\\n加强培训',
    quote: '从学校到企业，从课程到项目，从个人技能到劳务品牌，培训的目的不是拿证，而是让劳动者更稳地进入真实岗位。',
    image: 'computer-training.jpg',
    points: ['校企协同', '微专业微课程', '项目制培养', '订单式输出'],
    layout: 'extension'
  },
  {
    id: 'xhs-07-training',
    no: '07',
    tag: '能力适配',
    title: '培训要接岗位\\n接产业接收入',
    quote: '培训不是“学过就算”，而是要能接岗位、接产业、接收入。',
    points: ['课程跟着产业走', '项目跟着企业走', '评价跟着岗位走', '就业跟着能力走'],
    layout: 'matrix'
  },
  {
    id: 'xhs-08-service',
    no: '08',
    tag: '三、服务送岗',
    title: '公共就业服务\\n不能只发布信息',
    quote: '就业服务的高质量，不只看发布了多少岗位，还要看岗位能不能被看见、被匹配、被触达、被承接。',
    image: 'call-center-hotline.jpg',
    points: ['岗位归集', '精准推送', '基层服务', '权益闭环'],
    layout: 'photoFeature'
  },
  {
    id: 'xhs-09-match',
    no: '09',
    tag: '精准匹配',
    title: '从信息发布\\n升级到精准匹配',
    quote: '公共就业服务要从“发布信息”升级为“精准匹配”。',
    points: ['专业', '技能', '地区', '群体', '政策', '维权'],
    layout: 'serviceMap'
  },
  {
    id: 'xhs-10-startup',
    no: '10',
    tag: '四、创业带岗',
    title: '创业不是\\n个体冒险',
    quote: '创业不是个体冒险，而是政策、平台、资金、导师、订单和市场共同托举的就业增量。',
    image: 'office-lobby.jpg',
    points: ['场地', '资金', '导师', '订单', '市场'],
    layout: 'darkQuote'
  },
  {
    id: 'xhs-11-grassroots',
    no: '11',
    tag: '基层就业',
    title: '基层岗位\\n也要写保障',
    quote: '基层就业要让青年愿意去、留得住、干得好，不能只靠情怀动员。',
    points: ['工作生活补贴', '岗位津贴', '食宿保障', '社会保险', '职业发展'],
    layout: 'governance'
  },
  {
    id: 'xhs-12-framework',
    no: '12',
    tag: '申论框架',
    title: '考场就记住\\n这条就业链',
    quote: '产业造岗 → 技能练岗 → 服务送岗 → 创业带岗 → 权益稳岗。',
    points: ['以产业升级拓空间', '以技能培训强适配', '以公共服务提效率', '以创业生态增岗位', '以权益保障稳预期'],
    layout: 'exam'
  },
  {
    id: 'xhs-13-argument',
    no: '13',
    tag: '总论点',
    title: '不要只说\\n多给岗位',
    quote: '破解就业难，关键不是单点增加岗位供给，而是推动产业、技能、服务、创业和保障协同发力，构建更加充分、更高质量的就业支持体系。',
    points: ['产业端拓空间', '能力端强适配', '服务端提效率', '保障端稳预期'],
    layout: 'material'
  },
  {
    id: 'xhs-14-interview',
    no: '14',
    tag: '面试题卡',
    title: '青年就业难\\n这样答',
    quote: '当前不少青年反映“就业难”，有人认为关键在于岗位不足，也有人认为关键在于求职观念和能力不匹配。对此你怎么看？',
    points: ['不能简单归因', '产业端拓空间', '能力端强适配', '服务端提效率', '保障端稳预期'],
    layout: 'interview'
  },
  {
    id: 'xhs-15-closing',
    no: '15',
    tag: '收束金句',
    title: '就业不是一张招聘海报\\n而是一条支持链',
    quote: '把岗位背后的产业变化、能力变化、服务变化和保障变化写清楚，申论里的“就业难”才真正写深。',
    image: 'job-fair-wide.jpg',
    points: ['看见岗位', '匹配岗位', '胜任岗位', '有人陪跑', '稳定发展'],
    layout: 'closing'
  }
];

const photoMeta = {
  'call-center-hotline.jpg': {
    pos: 'center 50%',
    map: 'office service staff with headsets sit in the center; keep text in upper paper panel.'
  },
  'code-laptop.jpg': {
    pos: 'center 50%',
    map: 'hands on laptop and code occupy central frame; safe evidence image, no face.'
  },
  'computer-training.jpg': {
    pos: 'center 50%',
    map: 'training room computer station with people on right; keep overlaid text on left paper panel.'
  },
  'data-center-server.jpg': {
    pos: 'center 50%',
    map: 'server rack fills the vertical frame; no face, works as new-industry evidence image.'
  },
  'job-fair-wide.jpg': {
    pos: 'center 46%',
    map: 'job fair group scene has people across the lower center; title placed on dark left overlay, faces remain background.'
  },
  'office-lobby.jpg': {
    pos: 'center 52%',
    map: 'empty modern office lobby, no faces; safe for entrepreneurship service support page.'
  }
};

const videos = [
  {
    id: 'video-cover-01',
    image: 'job-fair-wide.jpg',
    title: '就业难\\n不能只写多给岗位',
    subtitle: '产业造岗、技能练岗、服务送岗、创业带岗、权益稳岗',
    label: 'EMPLOYMENT CHAIN',
    variant: 1
  },
  {
    id: 'video-cover-02',
    image: 'data-center-server.jpg',
    title: '别只说岗位不足\\n要看产业怎么造岗',
    subtitle: '岗位结构变化，能力和服务要跟上',
    label: 'INDUSTRY CREATES JOBS',
    variant: 2
  },
  {
    id: 'video-cover-03',
    image: 'computer-training.jpg',
    title: '就业题\\n背这条五环链',
    subtitle: '产业 / 技能 / 服务 / 创业 / 权益',
    label: 'FIVE-LINK METHOD',
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
  const cls = len > 128 ? 'quote xxl' : len > 104 ? 'quote xl' : len > 78 ? 'quote long' : len > 52 ? 'quote med' : 'quote';
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
      <div class="aside"><p>这些话都对，但停在结果层面。</p><p>高分要问：链条哪一环断了？</p></div></div>
    </section>`;
  }
  if (page.layout === 'formula') {
    return `<section class="poster xhs formula" id="${page.id}">
      <div class="paper"></div><div class="content">${top(page)}<h1>${titleHtml(page.title)}</h1>${quoteHtml(page)}
      <div class="formulaRail">${page.points.map((x, i) => `<span><b>${String(i + 1).padStart(2, '0')}</b>${escapeHtml(x)}</span>`).join('<i></i>')}</div></div>
    </section>`;
  }
  if (page.layout === 'quotePhoto') {
    return `<section class="poster xhs quotePhoto" id="${page.id}">
      <div class="paper"></div>${photo(page.image, 'sidePhoto')}
      <div class="content">${top(page)}<h1>${titleHtml(page.title)}</h1>${quoteHtml(page)}
      <div class="keywordRail">${page.points.map((x) => `<span>${escapeHtml(x)}</span>`).join('')}</div></div>
    </section>`;
  }
  if (page.layout === 'objectPhoto') {
    return `<section class="poster xhs objectPhoto" id="${page.id}">
      <div class="paper"></div>${photo(page.image, 'bottomWide')}
      <div class="content">${top(page)}<h1>${titleHtml(page.title)}</h1>${quoteHtml(page)}${cards(page.points)}</div>
    </section>`;
  }
  if (page.layout === 'extension') {
    return `<section class="poster xhs extension" id="${page.id}">
      <div class="paper"></div>${photo(page.image, 'rightPhoto')}
      <div class="content">${top(page)}<h1>${titleHtml(page.title)}</h1>${quoteHtml(page)}
      <div class="extensionRows">${page.points.map((x) => `<span>${escapeHtml(x)}</span>`).join('')}</div></div>
    </section>`;
  }
  if (page.layout === 'matrix') {
    return `<section class="poster xhs matrixPage" id="${page.id}">
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
  if (page.layout === 'serviceMap') {
    return `<section class="poster xhs serviceMap" id="${page.id}">
      <div class="paper"></div><div class="content">${top(page)}<h1>${titleHtml(page.title)}</h1>${quoteHtml(page)}
      <div class="serviceBoxes">${page.points.map((x, i) => `<span><b>${String(i + 1).padStart(2, '0')}</b>${escapeHtml(x)}</span>`).join('')}</div></div>
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
      <div class="paper"></div><div class="content">${top(page)}<h1>${titleHtml(page.title)}</h1>${quoteHtml(page)}
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
body{background:#e4ddd3;font-family:"Avenir Next","Helvetica Neue","PingFang SC","Noto Sans SC","Microsoft YaHei",Arial,sans-serif;color:#201b17}
.stage{width:max-content;display:grid;gap:34px;padding:34px}
.poster{position:relative;overflow:hidden;isolation:isolate;background:#f4ecdf}
.xhs,.video{width:1080px;height:1440px}
.video{line-height:0}
.poster figure{margin:0}
.paper{position:absolute;inset:0;z-index:0;background:
  radial-gradient(circle at 86% 16%,rgba(255,105,0,.15),transparent 30%),
  radial-gradient(circle at 12% 88%,rgba(24,29,36,.12),transparent 34%),
  linear-gradient(116deg,rgba(32,27,23,.055) 0 1px,transparent 1px 18px),
  linear-gradient(180deg,#f7efe4 0%,#f4e7da 56%,#eaded2 100%)}
.paper:after{content:"";position:absolute;inset:0;background:repeating-linear-gradient(0deg,rgba(255,255,255,.13) 0 1px,transparent 1px 6px);opacity:.70}
.grain{position:absolute;inset:0;z-index:3;opacity:.22;background:repeating-linear-gradient(105deg,rgba(255,255,255,.12) 0 1px,transparent 1px 5px),linear-gradient(180deg,rgba(255,255,255,.16),rgba(0,0,0,.12));mix-blend-mode:soft-light;pointer-events:none}
.content{position:relative;z-index:5;height:100%;padding:58px;display:flex;flex-direction:column}
.top{display:flex;align-items:center;justify-content:space-between;gap:24px;border-bottom:2px solid rgba(32,27,23,.22);padding-bottom:20px;font-size:24px;line-height:1;font-weight:840}
.top span:first-child{font-size:38px;color:#ff6900;font-weight:900}
.cover .top,.darkQuote .top,.closing .top{border-bottom-color:rgba(255,255,255,.48);color:#fff3df}
.cover .top span:first-child,.darkQuote .top span:first-child,.closing .top span:first-child{color:#ff6900}
.xhs h1{margin:28px 0 0;font-family:"Songti SC","STSong","Noto Serif CJK SC",serif;font-size:76px;line-height:1.05;font-weight:760;letter-spacing:0}
.quote{margin:28px 0 0;padding:24px 28px;background:rgba(255,249,235,.94);border-left:10px solid #ff6900;font-size:34px;line-height:1.35;font-weight:820}
.quote.med{font-size:30px;line-height:1.39}
.quote.long{font-size:25px;line-height:1.43}
.quote.xl{font-size:21px;line-height:1.46}
.quote.xxl{font-size:18px;line-height:1.44}
.photo{margin:0;overflow:hidden}
.photo img,.videoPhoto img{width:100%;height:100%;object-fit:cover;filter:saturate(.88) contrast(1.06) brightness(.94)}
.bleed{position:absolute;inset:0;z-index:1}
.coverTint{position:absolute;inset:0;z-index:2;background:linear-gradient(90deg,rgba(25,23,22,.95),rgba(25,23,22,.22) 66%,rgba(25,23,22,.52)),linear-gradient(180deg,rgba(25,23,22,.12),rgba(25,23,22,.42) 62%,rgba(25,23,22,.91))}
.series{margin:36px 0 0;color:#ff6900;font-size:36px;line-height:1;font-weight:900}
.cover h1{margin-top:28px;color:#fff3df;font-size:86px;max-width:960px}
.coverLine{margin-top:30px;width:860px;padding:20px 24px;background:rgba(255,249,235,.92);color:#201b17;font-size:32px;font-weight:900}
.coverNodes{margin-top:auto;display:grid;grid-template-columns:1fr 18px 1fr 18px 1fr 18px 1fr 18px 1fr;align-items:center}
.coverNodes span{height:120px;display:grid;place-items:center;text-align:center;background:#f7efe4;color:#201b17;border-top:12px solid #ff6900;font-size:24px;font-weight:900}
.coverNodes span:nth-of-type(2){border-top-color:#333942}.coverNodes span:nth-of-type(3){border-top-color:#e7a13b}.coverNodes span:nth-of-type(4){border-top-color:#7c573a}.coverNodes span:nth-of-type(5){border-top-color:#201b17}
.coverNodes i{height:4px;background:#f7efe4}
.wrongList{margin-top:38px;display:grid;grid-template-columns:repeat(2,1fr);gap:14px}
.wrongList span{height:168px;padding:22px;display:grid;align-content:space-between;background:#fff9eb;border:2px solid rgba(32,27,23,.18);font-size:31px;font-weight:820}
.wrongList b{font-size:23px;color:#ff6900}
.aside{margin-top:auto;display:grid;grid-template-columns:1fr 1fr;gap:14px}
.aside p{min-height:128px;margin:0;padding:22px;background:#201b17;color:#fff3df;font-size:27px;line-height:1.22;font-weight:850}
.formula .quote,.exam .quote{font-size:29px}
.formulaRail,.examFlow{margin-top:auto;display:grid;grid-template-columns:1fr 18px 1fr 18px 1fr 18px 1fr 18px 1fr;align-items:center}
.formulaRail span,.examFlow span{height:280px;padding:18px 10px;display:grid;align-content:space-between;text-align:center;background:#201b17;color:#fff3df;font-size:23px;line-height:1.14;font-weight:900}
.examFlow span{height:258px;font-size:20px}
.formulaRail span:nth-of-type(2),.examFlow span:nth-of-type(2){background:#ff6900}.formulaRail span:nth-of-type(3),.examFlow span:nth-of-type(3){background:#333942}.formulaRail span:nth-of-type(4),.examFlow span:nth-of-type(4){background:#e7a13b;color:#201b17}.formulaRail span:nth-of-type(5),.examFlow span:nth-of-type(5){background:#7c573a}
.formulaRail b,.examFlow b{color:#ffd3ad;font-size:20px}.formulaRail span:nth-of-type(4) b,.examFlow span:nth-of-type(4) b{color:#201b17}
.formulaRail i,.examFlow i{height:4px;background:#201b17}
#xhs-03-core-chain:after{content:"岗位不是孤点，能力、服务、创业和保障要一起接上";position:absolute;left:58px;right:58px;top:596px;height:128px;z-index:1;display:grid;place-items:center;text-align:center;background:rgba(255,105,0,.12);border-top:3px solid rgba(255,105,0,.42);border-bottom:3px solid rgba(32,27,23,.28);color:#201b17;font-size:29px;font-weight:900}
.sidePhoto{position:absolute;right:0;top:0;bottom:0;width:460px;z-index:1}
.quotePhoto:after{content:"";position:absolute;right:0;top:0;bottom:0;width:690px;z-index:2;background:linear-gradient(90deg,#f4ecdf 0%,rgba(244,236,223,.92) 50%,rgba(244,236,223,.08) 100%)}
.quotePhoto .content{padding-right:418px}
.quotePhoto .quote{font-size:24px;line-height:1.46}
.keywordRail{margin-top:auto;display:grid;grid-template-columns:repeat(2,1fr);gap:10px}
.keywordRail span{height:108px;display:grid;place-items:center;text-align:center;background:#201b17;color:#fff3df;border-top:12px solid #ff6900;font-size:20px;font-weight:900}
.keywordRail span:nth-child(2),.keywordRail span:nth-child(4){border-top-color:#333942}
.bottomWide{position:absolute;left:58px;right:58px;bottom:58px;height:410px;z-index:1;border:3px solid rgba(255,105,0,.30)}
.objectPhoto .content,.photoFeature .content{padding-bottom:540px}
.objectPhoto .quote{font-size:28px;line-height:1.38}
.cards{margin-top:30px;display:grid;grid-template-columns:repeat(3,1fr);gap:10px}
.cards span{height:105px;padding:14px 10px;display:grid;align-content:space-between;background:#fff9eb;border-top:12px solid #ff6900;font-size:19px;line-height:1.14;font-weight:860}
.cards span:nth-child(2){border-top-color:#333942}.cards span:nth-child(3){border-top-color:#e7a13b}
.cards b{font-size:18px;color:#201b17}
.rightPhoto{position:absolute;right:58px;bottom:58px;width:410px;height:585px;z-index:1;border:3px solid rgba(255,105,0,.32)}
.extension .content{padding-right:500px}
.extension .quote{font-size:20px;line-height:1.43}
.extensionRows{margin-top:auto;display:grid;gap:12px}
.extensionRows span{height:84px;display:grid;place-items:center;text-align:center;background:#201b17;color:#fff3df;border-left:12px solid #ff6900;font-size:22px;font-weight:900}
.extensionRows span:nth-child(2),.extensionRows span:nth-child(4){border-left-color:#e7a13b}
.matrix{margin-top:34px;display:grid;grid-template-columns:repeat(2,1fr);gap:14px}
.matrix span{height:168px;padding:18px;display:grid;place-items:center;text-align:center;background:#fff9eb;border-top:14px solid #ff6900;font-size:27px;line-height:1.16;font-weight:900}
.matrix span:nth-child(2),.matrix span:nth-child(4){border-top-color:#333942}
.matrixPage:after{content:"培训的出口，是更稳地进入真实岗位";position:absolute;left:58px;right:58px;bottom:86px;height:150px;z-index:1;display:grid;place-items:center;background:#201b17;color:#fff3df;border-top:14px solid #ff6900;font-size:32px;font-weight:900}
.photoFeature .quote{font-size:20px;line-height:1.43}
.serviceStrip{margin-top:34px;display:grid;grid-template-columns:repeat(4,1fr);gap:10px}
.serviceStrip span{height:124px;padding:10px;display:grid;place-items:center;text-align:center;background:#201b17;color:#fff3df;border-top:12px solid #ff6900;font-size:23px;font-weight:900}
.serviceStrip span:nth-child(2),.serviceStrip span:nth-child(4){border-top-color:#e7a13b}
.serviceBoxes{margin-top:34px;display:grid;grid-template-columns:repeat(3,1fr);gap:14px}
.serviceBoxes span{height:148px;padding:16px;display:grid;align-content:space-between;background:#fff9eb;border-left:14px solid #ff6900;font-size:24px;line-height:1.16;font-weight:880}
.serviceBoxes span:nth-child(2),.serviceBoxes span:nth-child(5){border-left-color:#333942}.serviceBoxes span:nth-child(3),.serviceBoxes span:nth-child(6){border-left-color:#e7a13b}
.serviceBoxes b{font-size:20px;color:#7c573a}
.serviceMap:after{content:"把岗位、政策、补贴、维权和创业服务送到身边";position:absolute;left:58px;right:58px;bottom:86px;height:150px;z-index:1;display:grid;place-items:center;text-align:center;background:#201b17;color:#fff3df;border-top:14px solid #ff6900;font-size:29px;font-weight:900}
.darkTint{position:absolute;inset:0;z-index:2;background:linear-gradient(90deg,rgba(25,23,22,.94),rgba(25,23,22,.22) 66%,rgba(25,23,22,.54)),linear-gradient(180deg,rgba(25,23,22,.16),rgba(25,23,22,.82))}
.darkQuote h1{color:#fff3df;font-size:76px}
.darkQuote .quote{font-size:22px;line-height:1.43}
.darkNodes{margin-top:auto;display:grid;grid-template-columns:repeat(5,1fr);gap:10px}
.darkNodes span{height:130px;display:grid;place-items:center;text-align:center;background:#f7efe4;color:#201b17;border-top:12px solid #ff6900;font-size:21px;font-weight:900}
.darkNodes span:nth-child(2),.darkNodes span:nth-child(4){border-top-color:#e7a13b}.darkNodes span:nth-child(3),.darkNodes span:nth-child(5){border-top-color:#333942}
.governance .quote{font-size:29px;line-height:1.38}
.governGrid{margin-top:36px;display:grid;grid-template-columns:repeat(5,1fr);gap:10px}
.governGrid span{height:170px;padding:14px 10px;display:grid;place-items:center;text-align:center;background:#fff9eb;border-top:14px solid #ff6900;font-size:20px;line-height:1.16;font-weight:900}
.governGrid span:nth-child(2),.governGrid span:nth-child(4){border-top-color:#e7a13b}.governGrid span:nth-child(3),.governGrid span:nth-child(5){border-top-color:#333942}
.governance:after{content:"愿意去、留得住、干得好";position:absolute;left:58px;right:58px;bottom:88px;height:154px;z-index:1;display:grid;place-items:center;background:#201b17;color:#fff3df;border-top:14px solid #ff6900;font-size:34px;font-weight:900}
.material .quote{font-size:18px;line-height:1.43}
.materialGrid{margin-top:34px;display:grid;grid-template-columns:repeat(2,1fr);gap:14px}
.materialGrid span{height:160px;padding:16px;display:grid;place-items:center;text-align:center;background:#fff9eb;border-top:14px solid #ff6900;font-size:27px;line-height:1.16;font-weight:900}
.materialGrid span:nth-child(2),.materialGrid span:nth-child(4){border-top-color:#333942}
.interview .quote{font-size:22px;line-height:1.42}
.answerSteps{margin-top:30px;display:grid;gap:12px}
.answerSteps span{height:98px;padding:0 18px;display:flex;align-items:center;gap:16px;background:#fff9eb;border-left:12px solid #ff6900;font-size:22px;line-height:1.13;font-weight:850}
.answerSteps span:nth-child(2),.answerSteps span:nth-child(4){border-left-color:#e7a13b}.answerSteps span:nth-child(3),.answerSteps span:nth-child(5){border-left-color:#333942}
.answerSteps b{font-size:20px;color:#201b17}
#xhs-14-interview:after{content:"答题不要选边站，要看到结构性矛盾";position:absolute;left:58px;right:58px;bottom:80px;height:130px;z-index:1;display:grid;place-items:center;text-align:center;background:#201b17;color:#fff3df;border-top:14px solid #ff6900;font-size:30px;line-height:1.18;font-weight:900}
.closingTint{position:absolute;inset:0;z-index:2;background:linear-gradient(90deg,rgba(25,23,22,.94),rgba(25,23,22,.20) 67%,rgba(25,23,22,.50)),linear-gradient(180deg,rgba(25,23,22,.14),rgba(25,23,22,.84))}
.closing h1{color:#fff3df;font-size:70px}
.closing .quote{font-size:27px;line-height:1.4}
.closingNodes{margin-top:auto;display:grid;grid-template-columns:repeat(5,1fr);gap:10px}
.closingNodes span{height:130px;display:grid;place-items:center;text-align:center;background:#f7efe4;color:#201b17;border-top:12px solid #ff6900;font-size:21px;font-weight:900}
.closingNodes span:nth-child(2),.closingNodes span:nth-child(4){border-top-color:#e7a13b}.closingNodes span:nth-child(3),.closingNodes span:nth-child(5){border-top-color:#333942}
.videoPhoto{position:absolute;inset:0;margin:0;z-index:1}
.videoPhoto img{filter:saturate(.88) contrast(1.10) brightness(.66)}
.videoTint{position:absolute;inset:0;z-index:2;background:linear-gradient(90deg,rgba(25,23,22,.92),rgba(25,23,22,.12) 70%),linear-gradient(180deg,rgba(25,23,22,.10),rgba(25,23,22,.32) 44%,rgba(25,23,22,.88))}
.magLines{position:absolute;inset:56px;z-index:3;border-top:2px solid rgba(255,255,255,.60);border-bottom:2px solid rgba(255,255,255,.42)}
.magLines:before{content:"";position:absolute;left:0;top:94px;width:210px;height:2px;background:rgba(255,255,255,.58)}
.magLines:after{content:attr(data-label);position:absolute;right:0;top:24px;color:rgba(255,255,255,.72);font-size:20px;font-weight:820;letter-spacing:0}
.videoTitle{position:absolute;left:64px;right:76px;bottom:112px;z-index:4;color:#fff3df;line-height:1.2}
.videoTitle p{margin:0 0 28px;color:#ff6900;font-size:34px;line-height:1;font-weight:900}
.videoTitle h2{margin:0;font-family:"Songti SC","STSong","Noto Serif CJK SC",serif;font-size:76px;line-height:1.04;font-weight:780;letter-spacing:0;max-width:920px}
.v2 .videoTitle h2{font-size:70px}.v3 .videoTitle h2{font-size:78px}
.videoTitle span{display:block;width:max-content;max-width:890px;margin-top:26px;padding:14px 18px;background:#ff6900;color:#fff3df;font-size:24px;font-weight:900}
.v2 .videoTitle span{background:#333942}.v3 .videoTitle span{background:#e7a13b;color:#201b17}
.preview{width:1800px;background:#e4ddd3;padding:34px;display:grid;grid-template-columns:repeat(5,1fr);gap:18px}
.preview figure{margin:0;background:#fff9eb;padding:8px}
.preview img{width:100%;display:block}
.preview figcaption{padding:8px 2px 0;font-size:16px;font-weight:780;color:#303030}
`;

const html = `<!doctype html><html lang="zh-CN" data-theme="editorial"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>就业链小红书与视频号封面</title><style>${css}</style></head><body><main class="stage">${pages.map(renderPage).join('\n')}${videos.map(renderVideo).join('\n')}</main></body></html>`;
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
