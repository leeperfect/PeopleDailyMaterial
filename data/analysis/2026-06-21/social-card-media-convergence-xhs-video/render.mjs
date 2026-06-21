import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { chromium } from 'playwright';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const repoRoot = path.resolve(__dirname, '../../../..');
const mediaDir = path.join(repoRoot, 'media/images/2026-06-21-media-convergence-xhs-video');
const assetDir = path.join(mediaDir, 'assets');
const htmlPath = path.join(__dirname, 'index.html');

const out = (file) => path.join(mediaDir, file);
const rel = (file) => path.relative(__dirname, path.join(assetDir, file)).replaceAll(path.sep, '/');

const pages = [
  {
    id: 'xhs-01-cover',
    no: '01',
    tag: '人民日报材料转申论',
    title: '主流媒体融合\\n不是多开账号',
    kicker: '而是重构内容、技术和服务',
    image: 'editing-screens.jpg',
    points: ['内容表达', '技术底座', '组织机制', '服务场景'],
    layout: 'cover'
  },
  {
    id: 'xhs-02-mistake',
    no: '02',
    tag: '常见误区',
    title: '别把融合\\n写成平台搬家',
    quote: '报纸开公众号、电视台做短视频、多平台一起发，这些能写，但还没回答“融合到底融在哪里”。',
    points: ['多开账号', '矩阵转发', 'AI 海报', '数字人主播'],
    notes: ['入口不是终点', '高分要写系统性变革'],
    layout: 'mistake'
  },
  {
    id: 'xhs-03-core-judgement',
    no: '03',
    tag: '核心判断',
    title: '不是新旧媒体\\n简单相加',
    quote: '主流媒体融合不是传统媒体和新媒体的简单相加，而是内容表达、技术底座、组织机制和服务场景的整体重构。',
    image: 'newsroom-team.jpg',
    points: ['内容表达', '技术底座', '组织机制', '服务场景'],
    layout: 'quotePhoto'
  },
  {
    id: 'xhs-04-formula',
    no: '04',
    tag: '核心公式',
    title: '考场先抓\\n这条融合链',
    quote: '内容适配场景 → 技术重塑流程 → 服务延伸功能。',
    points: ['内容适配场景', '技术重塑流程', '服务延伸功能'],
    layout: 'formula'
  },
  {
    id: 'xhs-05-content-fit',
    no: '05',
    tag: '内容重构',
    title: '内容先要\\n换一种抵达方式',
    quote: '契合才能融合，匹配才能搭配。',
    image: 'video-production.jpg',
    points: ['小切口', '生活场景', '公众语言', '情绪连接'],
    layout: 'objectPhoto'
  },
  {
    id: 'xhs-06-content-core',
    no: '06',
    tag: '价值共鸣',
    title: '从“我说你听”\\n到“你愿意参与”',
    quote: '内容重构的核心，是让主流价值从“我说你听”转向“你愿意看、看得懂、愿意参与”。',
    points: ['愿意看', '看得懂', '愿意转发', '愿意参与'],
    layout: 'needMatrix'
  },
  {
    id: 'xhs-07-content-long',
    no: '07',
    tag: '申论表达',
    title: '内容为王\\n也要懂新语境',
    quote: '推进主流媒体融合，要坚持内容为王，善于用小切口呈现大主题、用生活场景转译政策话语、用分众表达提升抵达效率、用互动传播增强情感连接，让主流价值在新语境中更可感、更可信、更可亲。',
    image: 'smartphone-platform.jpg',
    points: ['小切口呈现大主题', '生活场景转译政策', '分众表达提升抵达', '互动传播增强连接'],
    layout: 'extension'
  },
  {
    id: 'xhs-08-tech-core',
    no: '08',
    tag: '技术重构',
    title: '不是会用 AI\\n而是重塑流程',
    quote: '技术重构的核心，是让主流媒体从内容生产者，升级为数智传播体系的建设者。',
    image: 'data-center.jpg',
    points: ['选题发现', '内容生产', '智能审校', '精准分发', '效果反馈'],
    layout: 'photoFeature'
  },
  {
    id: 'xhs-09-tech-long',
    no: '09',
    tag: '数智底座',
    title: '技术要嵌入\\n策采编审发全流程',
    quote: '要以数智技术提升主流媒体融合质效，推动 AI、数据中台、智能媒资、内容安全审核、传播力评估等能力嵌入策采编审发全流程，实现内容生产更高效、分发触达更精准、互动反馈更及时、主流声音更可见。',
    points: ['AI', '数据中台', '智能媒资', '内容安全审核', '传播力评估'],
    layout: 'governance'
  },
  {
    id: 'xhs-10-service-core',
    no: '10',
    tag: '服务重构',
    title: '媒体不只是\\n信息发布窗口',
    quote: '服务重构的核心，是让主流媒体从信息发布窗口，升级为连接治理、产业、文化和世界的公共平台。',
    image: 'service-office.jpg',
    points: ['治理', '产业', '文化', '世界'],
    layout: 'darkQuote'
  },
  {
    id: 'xhs-11-service-long',
    no: '11',
    tag: '公共平台',
    title: '新闻平台\\n也能变成服务端口',
    quote: '要拓展媒体融合服务边界，推动“新闻+政务服务商务”深度融合，把主流媒体平台建设成为群众诉求的响应端、城市治理的协同端、文化产业的连接端、国际传播的表达端。',
    image: 'urban-screen.jpg',
    points: ['群众诉求响应端', '城市治理协同端', '文化产业连接端', '国际传播表达端'],
    layout: 'extension'
  },
  {
    id: 'xhs-12-exam-framework',
    no: '12',
    tag: '考场框架',
    title: '遇到媒体融合\\n直接写这三步',
    quote: '内容适配场景，技术重塑流程，服务延伸功能。',
    points: ['内容适配场景', '技术重塑流程', '机制激发活力', '服务延伸功能'],
    layout: 'exam'
  },
  {
    id: 'xhs-13-interview',
    no: '13',
    tag: '面试题卡',
    title: '现象认知题\\n这样答',
    quote: '有人认为，媒体融合就是多开账号、多做短视频、扩大传播覆盖。对此你怎么看？',
    points: ['多平台传播是入口，不是融合本身', '重构内容表达，让主流价值可感可亲', '重构技术流程，打通全链条能力', '重构服务功能，连接治理产业和国际传播'],
    layout: 'interview'
  },
  {
    id: 'xhs-14-material-bank',
    no: '14',
    tag: '素材记忆',
    title: '材料怎么记\\n才不会散',
    quote: '南京看城市传播，九派新闻看小切口，咸宁看策采编发，新甘肃云看数智底座，鄂尔多斯和滨州看“新闻+服务”。',
    image: 'press-conference.jpg',
    points: ['南京：城市传播', '九派：小切口', '咸宁：全媒协同', '新甘肃云：数智平台', '滨州：新闻+服务'],
    layout: 'material'
  },
  {
    id: 'xhs-15-closing',
    no: '15',
    tag: '收束金句',
    title: '不是搬到新平台\\n而是长出新半径',
    quote: '真正的主流媒体融合，不是把旧内容搬到新平台，而是让主流价值拥有新的表达方式、新的技术底座和新的服务半径。',
    image: 'digital-network.jpg',
    points: ['新的表达方式', '新的技术底座', '新的服务半径'],
    layout: 'closing'
  }
];

const photoMeta = {
  'broadcast-studio.jpg': {
    pos: 'center 52%',
    map: 'dark broadcast switcher and screen occupy the left and center; safe title zone is lower-left with tint.'
  },
  'cultural-event.jpg': {
    pos: 'center 52%',
    map: 'concert crowd and confetti fill the lower frame; avoid covering bright center with small text.'
  },
  'data-center.jpg': {
    pos: 'center 50%',
    map: 'server racks and cables fill the frame; no faces, works as technology evidence image.'
  },
  'digital-network.jpg': {
    pos: 'center 52%',
    map: 'earth-at-night network texture fills the frame; no faces, text can sit on dark lower-left.'
  },
  'editing-screens.jpg': {
    pos: 'center 48%',
    map: 'editing timeline and screen colors span the frame; no faces, title can sit over dark left area.'
  },
  'newsroom-desk.jpg': {
    pos: 'center 52%',
    map: 'camera operator and meeting are centered; use as evidence image, do not overlay faces.'
  },
  'newsroom-team.jpg': {
    pos: 'center 52%',
    map: 'open newsroom with people across the lower half; keep text in left paper panel.'
  },
  'press-conference.jpg': {
    pos: 'center 50%',
    map: 'conference audience sits in dark lower area; use as lower evidence image or tinted background.'
  },
  'service-office.jpg': {
    pos: 'center 52%',
    map: 'bright service office with staff and desks; text should stay on dark left overlay.'
  },
  'smartphone-platform.jpg': {
    pos: 'center 50%',
    map: 'smartphone and laptop lie diagonally on bright desk; safe as right-side evidence image.'
  },
  'urban-screen.jpg': {
    pos: 'center 50%',
    map: 'public city map display and street screen sit in the center-right; keep text in left paper or dark overlay.'
  },
  'video-production.jpg': {
    pos: 'center 52%',
    map: 'clapperboard fills the center-right with open sky; text stays in paper area above.'
  }
};

const videos = [
  {
    id: 'video-cover-01',
    image: 'editing-screens.jpg',
    title: '主流媒体融合\\n不是多开账号',
    subtitle: '而是重构内容、技术和服务',
    label: 'MEDIA CONVERGENCE',
    variant: 1
  },
  {
    id: 'video-cover-02',
    image: 'digital-network.jpg',
    title: '内容适配场景\\n技术重塑流程\\n服务延伸功能',
    subtitle: '申论高分链条',
    label: 'CONTENT · TECH · SERVICE',
    variant: 2
  },
  {
    id: 'video-cover-03',
    image: 'urban-screen.jpg',
    title: '不是平台搬家\\n而是系统重构',
    subtitle: '表达方式 / 技术底座 / 服务半径',
    label: 'PUBLIC PLATFORM',
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
body{background:#d9dcdf;font-family:"Avenir Next","Helvetica Neue","PingFang SC","Noto Sans SC","Microsoft YaHei",Arial,sans-serif;color:#1b252d}
.stage{width:max-content;display:grid;gap:34px;padding:34px}
.poster{position:relative;overflow:hidden;isolation:isolate;background:#f3f1e8}
.xhs,.video{width:1080px;height:1440px}
.paper{position:absolute;inset:0;z-index:0;background:
  radial-gradient(circle at 84% 16%,rgba(36,105,160,.14),transparent 30%),
  radial-gradient(circle at 12% 90%,rgba(202,46,42,.13),transparent 34%),
  linear-gradient(116deg,rgba(27,37,45,.055) 0 1px,transparent 1px 18px),
  linear-gradient(180deg,#f7f3e8 0%,#eef2f4 56%,#e6ecf1 100%)}
.paper:after{content:"";position:absolute;inset:0;background:repeating-linear-gradient(0deg,rgba(255,255,255,.12) 0 1px,transparent 1px 6px);opacity:.70}
.grain{position:absolute;inset:0;z-index:3;opacity:.22;background:repeating-linear-gradient(105deg,rgba(255,255,255,.11) 0 1px,transparent 1px 5px),linear-gradient(180deg,rgba(255,255,255,.16),rgba(0,0,0,.10));mix-blend-mode:soft-light;pointer-events:none}
.content{position:relative;z-index:5;height:100%;padding:58px;display:flex;flex-direction:column}
.top{display:flex;align-items:center;justify-content:space-between;gap:24px;border-bottom:2px solid rgba(27,37,45,.20);padding-bottom:20px;font-size:24px;line-height:1;font-weight:840}
.top span:first-child{font-size:38px;color:#2469a0;font-weight:900}
.cover .top,.darkQuote .top,.closing .top{border-bottom-color:rgba(255,255,255,.46);color:#fff3df}
.cover .top span:first-child,.darkQuote .top span:first-child,.closing .top span:first-child{color:#e8463a}
.xhs h1{margin:28px 0 0;font-family:"Songti SC","STSong","Noto Serif CJK SC",serif;font-size:78px;line-height:1.05;font-weight:760;letter-spacing:0}
.quote{margin:28px 0 0;padding:24px 28px;background:rgba(255,249,235,.94);border-left:10px solid #2469a0;font-size:34px;line-height:1.35;font-weight:820}
.quote.med{font-size:30px;line-height:1.39}
.quote.long{font-size:25px;line-height:1.43}
.quote.xl{font-size:21px;line-height:1.46}
.quote.xxl{font-size:19px;line-height:1.44}
.photo{margin:0;overflow:hidden}
.photo img,.videoPhoto img{width:100%;height:100%;object-fit:cover;filter:saturate(.90) contrast(1.05) brightness(.94)}
.bleed{position:absolute;inset:0;z-index:1}
.coverTint{position:absolute;inset:0;z-index:2;background:linear-gradient(90deg,rgba(15,26,36,.94),rgba(15,26,36,.18) 66%,rgba(15,26,36,.44)),linear-gradient(180deg,rgba(15,26,36,.10),rgba(15,26,36,.38) 62%,rgba(15,26,36,.90))}
.series{margin:36px 0 0;color:#e8463a;font-size:36px;line-height:1;font-weight:900}
.cover h1{margin-top:28px;color:#fff3df;font-size:86px;max-width:940px}
.coverLine{margin-top:30px;width:900px;padding:20px 24px;background:rgba(255,249,235,.92);color:#1b252d;font-size:31px;font-weight:880}
.coverNodes{margin-top:auto;display:grid;grid-template-columns:1fr 28px 1fr 28px 1fr 28px 1fr;align-items:center}
.coverNodes span{height:132px;display:grid;place-items:center;text-align:center;background:#f7f3e8;color:#1b252d;border-top:12px solid #2469a0;font-size:28px;font-weight:900}
.coverNodes span:nth-of-type(2){border-top-color:#e8463a}.coverNodes span:nth-of-type(3){border-top-color:#6e7f86}.coverNodes span:nth-of-type(4){border-top-color:#1b252d}
.coverNodes i{height:4px;background:#f7f3e8}
.wrongList{margin-top:38px;display:grid;grid-template-columns:repeat(2,1fr);gap:14px}
.wrongList span{height:168px;padding:22px;display:grid;align-content:space-between;background:#fff9eb;border:2px solid rgba(27,37,45,.18);font-size:31px;font-weight:820}
.wrongList b{font-size:23px;color:#2469a0}
.aside{margin-top:auto;display:grid;grid-template-columns:1fr 1fr;gap:14px}
.aside p{min-height:128px;margin:0;padding:22px;background:#1b252d;color:#fff3df;font-size:28px;line-height:1.22;font-weight:850}
.sidePhoto{position:absolute;right:0;top:0;bottom:0;width:460px;z-index:1}
.quotePhoto:after{content:"";position:absolute;right:0;top:0;bottom:0;width:690px;z-index:2;background:linear-gradient(90deg,#f3f1e8 0%,rgba(243,241,232,.92) 50%,rgba(243,241,232,.08) 100%)}
.quotePhoto .content{padding-right:418px}
.quotePhoto .quote{font-size:22px;line-height:1.46}
.keywordRail{margin-top:auto;display:grid;grid-template-columns:repeat(4,1fr);gap:10px}
.keywordRail span{height:112px;display:grid;place-items:center;text-align:center;background:#1b252d;color:#fff3df;border-top:12px solid #2469a0;font-size:22px;font-weight:900}
.keywordRail span:nth-child(2){border-top-color:#e8463a}.keywordRail span:nth-child(3){border-top-color:#6e7f86}.keywordRail span:nth-child(4){border-top-color:#2469a0}
.formula .quote,.exam .quote{font-size:33px}
.formulaRail,.examFlow{margin-top:auto;display:grid;grid-template-columns:1fr 30px 1fr 30px 1fr;align-items:center}
.examFlow{grid-template-columns:1fr 24px 1fr 24px 1fr 24px 1fr}
.formulaRail span,.examFlow span{height:335px;padding:20px 16px;display:grid;align-content:space-between;text-align:center;background:#1b252d;color:#fff3df;font-size:29px;line-height:1.14;font-weight:900}
.examFlow span{height:300px;font-size:25px}
.formulaRail span:nth-of-type(2),.examFlow span:nth-of-type(2){background:#e8463a;color:#fff3df}.formulaRail span:nth-of-type(3),.examFlow span:nth-of-type(3){background:#2469a0}.examFlow span:nth-of-type(4){background:#6e7f86;color:#fff3df}
.formulaRail b,.examFlow b{color:#ffd4b8;font-size:22px}
.formulaRail i,.examFlow i{height:4px;background:#1b252d}
#xhs-04-formula:after{content:"表达方式  →  生产流程  →  公共服务";position:absolute;left:58px;right:58px;top:572px;height:128px;z-index:1;display:grid;place-items:center;background:rgba(36,105,160,.10);border-top:3px solid rgba(36,105,160,.42);border-bottom:3px solid rgba(232,70,58,.36);color:#1b252d;font-size:34px;font-weight:900}
.bottomWide{position:absolute;left:58px;right:58px;bottom:58px;height:410px;z-index:1;border:3px solid rgba(36,105,160,.30)}
.objectPhoto .content,.photoFeature .content,.material .content{padding-bottom:540px}
.objectPhoto .quote{font-size:30px;line-height:1.37}
.cards{margin-top:30px;display:grid;grid-template-columns:repeat(4,1fr);gap:10px}
.cards span{height:100px;padding:14px 10px;display:grid;align-content:space-between;background:#fff9eb;border-top:12px solid #2469a0;font-size:20px;line-height:1.14;font-weight:860}
.cards span:nth-child(2),.cards span:nth-child(4){border-top-color:#e8463a}.cards span:nth-child(3){border-top-color:#6e7f86}
.cards b{font-size:18px;color:#1b252d}
.matrix{margin-top:38px;display:grid;grid-template-columns:repeat(2,1fr);gap:14px}
.matrix span{height:198px;padding:20px;display:grid;place-items:center;text-align:center;background:#fff9eb;border-top:14px solid #2469a0;font-size:29px;line-height:1.16;font-weight:900}
.matrix span:nth-child(2),.matrix span:nth-child(4){border-top-color:#e8463a}.matrix span:nth-child(3){border-top-color:#6e7f86}
.needMatrix:after{content:"信息传递 → 价值共鸣 → 公共参与";position:absolute;left:58px;right:58px;bottom:88px;height:158px;z-index:1;display:grid;place-items:center;background:#1b252d;color:#fff3df;border-top:14px solid #e8463a;font-size:34px;font-weight:900}
.serviceStrip{margin-top:34px;display:grid;grid-template-columns:repeat(5,1fr);gap:10px}
.serviceStrip span{height:134px;padding:10px;display:grid;place-items:center;text-align:center;background:#1b252d;color:#fff3df;border-top:12px solid #2469a0;font-size:23px;font-weight:900}
.serviceStrip span:nth-child(2),.serviceStrip span:nth-child(4){border-top-color:#e8463a}.serviceStrip span:nth-child(3),.serviceStrip span:nth-child(5){border-top-color:#6e7f86}
.rightPhoto{position:absolute;right:58px;bottom:58px;width:410px;height:585px;z-index:1;border:3px solid rgba(36,105,160,.30)}
.extension .content{padding-right:500px}
.extension .quote{font-size:19px;line-height:1.44}
.extensionRows{margin-top:auto;display:grid;gap:12px}
.extensionRows span{height:86px;display:grid;place-items:center;text-align:center;background:#1b252d;color:#fff3df;border-left:12px solid #2469a0;font-size:22px;font-weight:900}
.extensionRows span:nth-child(2),.extensionRows span:nth-child(4){border-left-color:#e8463a}.extensionRows span:nth-child(3){border-left-color:#6e7f86}
#xhs-07-content-long:after{content:"可感 / 可信 / 可亲";position:absolute;left:58px;top:642px;width:474px;height:112px;z-index:1;display:grid;place-items:center;background:rgba(255,249,235,.86);border-left:14px solid #e8463a;color:#1b252d;font-size:30px;font-weight:900}
#xhs-11-service-long:after{content:"新闻 + 政务 + 服务 + 商务";position:absolute;left:58px;top:648px;width:474px;height:124px;z-index:1;display:grid;place-items:center;text-align:center;background:#1b252d;color:#fff3df;border-left:14px solid #e8463a;font-size:28px;line-height:1.18;font-weight:900}
.darkTint{position:absolute;inset:0;z-index:2;background:linear-gradient(90deg,rgba(15,26,36,.93),rgba(15,26,36,.18) 67%,rgba(15,26,36,.54)),linear-gradient(180deg,rgba(15,26,36,.12),rgba(15,26,36,.82))}
.darkQuote h1{color:#fff3df;font-size:78px}
.darkQuote .quote{font-size:25px;line-height:1.43}
.darkNodes{margin-top:auto;display:grid;grid-template-columns:repeat(4,1fr);gap:12px}
.darkNodes span{height:146px;display:grid;place-items:center;text-align:center;background:#f7f3e8;color:#1b252d;border-top:12px solid #2469a0;font-size:26px;font-weight:900}
.darkNodes span:nth-child(2),.darkNodes span:nth-child(4){border-top-color:#e8463a}.darkNodes span:nth-child(3){border-top-color:#6e7f86}
.governance .quote{font-size:18px;line-height:1.43}
.governGrid{margin-top:36px;display:grid;grid-template-columns:repeat(5,1fr);gap:10px}
.governGrid span{height:170px;padding:14px 10px;display:grid;place-items:center;text-align:center;background:#fff9eb;border-top:14px solid #2469a0;font-size:22px;line-height:1.16;font-weight:900}
.governGrid span:nth-child(2),.governGrid span:nth-child(4){border-top-color:#e8463a}.governGrid span:nth-child(3),.governGrid span:nth-child(5){border-top-color:#6e7f86}
.governance:after{content:"生产更高效 → 触达更精准 → 反馈更及时 → 声音更可见";position:absolute;left:58px;right:58px;bottom:88px;height:154px;z-index:1;display:grid;place-items:center;background:#1b252d;color:#fff3df;border-top:14px solid #e8463a;font-size:28px;font-weight:900}
.interview .quote{font-size:27px;line-height:1.4}
.answerSteps{margin-top:34px;display:grid;gap:14px}
.answerSteps span{height:108px;padding:0 20px;display:flex;align-items:center;gap:16px;background:#fff9eb;border-left:12px solid #2469a0;font-size:23px;line-height:1.16;font-weight:850}
.answerSteps span:nth-child(2),.answerSteps span:nth-child(4){border-left-color:#e8463a}.answerSteps span:nth-child(3){border-left-color:#6e7f86}
.answerSteps b{font-size:20px;color:#1b252d}
#xhs-12-exam-framework:after{content:"内容为王 / 技术为基 / 机制为梁 / 服务为径";position:absolute;left:58px;right:58px;top:622px;height:132px;z-index:1;display:grid;place-items:center;background:rgba(255,249,235,.86);border-left:14px solid #2469a0;border-right:14px solid #e8463a;color:#1b252d;font-size:30px;font-weight:900}
#xhs-13-interview:after{content:"账号矩阵是外形，系统重构才是融合能力";position:absolute;left:58px;right:58px;bottom:92px;height:150px;z-index:1;display:grid;place-items:center;text-align:center;background:#1b252d;color:#fff3df;border-top:14px solid #e8463a;font-size:31px;line-height:1.18;font-weight:900}
.material .quote{font-size:23px;line-height:1.42}
.materialGrid{margin-top:30px;display:grid;grid-template-columns:repeat(5,1fr);gap:10px}
.materialGrid span{height:105px;padding:10px;display:grid;place-items:center;text-align:center;background:#fff9eb;border-top:12px solid #2469a0;font-size:20px;line-height:1.14;font-weight:880}
.materialGrid span:nth-child(2),.materialGrid span:nth-child(4){border-top-color:#e8463a}.materialGrid span:nth-child(3),.materialGrid span:nth-child(5){border-top-color:#6e7f86}
.closingTint{position:absolute;inset:0;z-index:2;background:linear-gradient(90deg,rgba(15,26,36,.94),rgba(15,26,36,.20) 67%,rgba(15,26,36,.50)),linear-gradient(180deg,rgba(15,26,36,.14),rgba(15,26,36,.84))}
.closing h1{color:#fff3df;font-size:74px}
.closing .quote{font-size:25px;line-height:1.42}
.closingNodes{margin-top:auto;display:grid;grid-template-columns:repeat(3,1fr);gap:12px}
.closingNodes span{height:140px;display:grid;place-items:center;text-align:center;background:#f7f3e8;color:#1b252d;border-top:12px solid #2469a0;font-size:24px;font-weight:900}
.closingNodes span:nth-child(2){border-top-color:#e8463a}.closingNodes span:nth-child(3){border-top-color:#6e7f86}
.videoPhoto{position:absolute;inset:0;margin:0;z-index:1}
.videoPhoto img{filter:saturate(.88) contrast(1.10) brightness(.70)}
.videoTint{position:absolute;inset:0;z-index:2;background:linear-gradient(90deg,rgba(15,26,36,.92),rgba(15,26,36,.12) 70%),linear-gradient(180deg,rgba(15,26,36,.10),rgba(15,26,36,.30) 44%,rgba(15,26,36,.86))}
.magLines{position:absolute;inset:56px;z-index:3;border-top:2px solid rgba(255,255,255,.60);border-bottom:2px solid rgba(255,255,255,.42)}
.magLines:before{content:"";position:absolute;left:0;top:94px;width:210px;height:2px;background:rgba(255,255,255,.58)}
.magLines:after{content:attr(data-label);position:absolute;right:0;top:24px;color:rgba(255,255,255,.72);font-size:20px;font-weight:820;letter-spacing:0}
.videoTitle{position:absolute;left:64px;right:76px;bottom:92px;z-index:4;color:#fff3df}
.videoTitle p{margin:0 0 28px;color:#e8463a;font-size:34px;line-height:1;font-weight:900}
.videoTitle h2{margin:0;font-family:"Songti SC","STSong","Noto Serif CJK SC",serif;font-size:78px;line-height:1.04;font-weight:780;letter-spacing:0;max-width:920px}
.v2 .videoTitle h2{font-size:70px}.v3 .videoTitle h2{font-size:74px}
.videoTitle span{display:block;width:max-content;max-width:890px;margin-top:26px;padding:14px 18px;background:#2469a0;color:#fff3df;font-size:27px;font-weight:900}
.v2 .videoTitle span{background:#e8463a;color:#fff3df}.v3 .videoTitle span{background:#6e7f86;color:#fff3df}
.preview{width:1800px;background:#d9dcdf;padding:34px;display:grid;grid-template-columns:repeat(5,1fr);gap:18px}
.preview figure{margin:0;background:#fff9eb;padding:8px}
.preview img{width:100%;display:block}
.preview figcaption{padding:8px 2px 0;font-size:16px;font-weight:780;color:#303030}
`;

const html = `<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>主流媒体融合小红书与视频号封面</title><style>${css}</style></head><body><main class="stage">${pages.map(renderPage).join('\n')}${videos.map(renderVideo).join('\n')}</main></body></html>`;
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
