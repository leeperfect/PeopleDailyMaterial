import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { chromium } from 'playwright';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const repoRoot = path.resolve(__dirname, '../../../..');
const mediaDir = path.join(repoRoot, 'media/images/2026-06-21-westward-development-xhs-video');
const assetDir = path.join(mediaDir, 'assets');
const htmlPath = path.join(__dirname, 'index.html');

const out = (file) => path.join(mediaDir, file);
const rel = (file) => path.relative(__dirname, path.join(assetDir, file)).replaceAll(path.sep, '/');

const pages = [
  {
    id: 'xhs-01-cover',
    no: '01',
    tag: '人民日报材料转申论',
    title: '大国向西\\n不是区域口号',
    kicker: '通道 / 算力 / 产业 / 安全腹地',
    image: 'freight-rail.jpg',
    points: ['开放通道', '算力节点', '产业支点', '战略腹地'],
    layout: 'cover'
  },
  {
    id: 'xhs-02-mistake',
    no: '02',
    tag: '常见误区',
    title: '别只写\\n西部要发展',
    quote: '只写“补短板、强基础、因地制宜”，文章就停在被扶持区域。',
    points: ['西部大开发', '区域协调', '补齐短板', '特色产业'],
    notes: ['这些能写，但不是主线', '高分要写出：西部承担什么国家功能'],
    layout: 'mistake'
  },
  {
    id: 'xhs-03-strategic-point',
    no: '03',
    tag: '总判断',
    title: '西部不是远方\\n而是战略支点',
    quote: '大国向西，不是把发展口号往西部贴，而是把通道、算力、产业、生态和人才组织成国家韧性的战略支点。',
    image: 'xinjiang-mountains.jpg',
    points: ['通道', '算力', '产业', '生态', '人才'],
    layout: 'quotePhoto'
  },
  {
    id: 'xhs-04-core-formula',
    no: '04',
    tag: '核心公式',
    title: '先记住\\n这四段逻辑',
    quote: '通道向西打开空间 → 算力向西重组要素 → 产业向西形成支点 → 安全向西托底韧性。',
    points: ['通道向西', '算力向西', '产业向西', '安全向西'],
    layout: 'formula'
  },
  {
    id: 'xhs-05-channel',
    no: '05',
    tag: '通道',
    title: '打通的\\n不只是一条路',
    quote: '打通的不只是隧道，而是交通瓶颈、民生距离和区域发展空间。',
    image: 'rail-tunnel.jpg',
    points: ['交通瓶颈', '民生距离', '发展空间'],
    layout: 'photoFeature'
  },
  {
    id: 'xhs-06-channel-system',
    no: '06',
    tag: '开放空间',
    title: '通道背后\\n是市场产业规则',
    quote: '推动西部发展，要以通道建设重塑开放空间，把交通物流、陆海联动、产业承载和制度型开放贯通起来，让内陆地区从地理腹地走向开放前沿。',
    image: 'logistics-warehouse.jpg',
    points: ['交通物流', '陆海联动', '产业承载', '制度型开放'],
    layout: 'systemPhoto'
  },
  {
    id: 'xhs-07-computing',
    no: '07',
    tag: '算力',
    title: '西部不只输出资源\\n也能输出新能力',
    quote: '算力向西，本质上是新型基础设施向能源富集区、空间承载区和绿色转型区重新布局。',
    image: 'data-center.jpg',
    points: ['能源富集区', '空间承载区', '绿色转型区'],
    layout: 'darkQuote'
  },
  {
    id: 'xhs-08-industry',
    no: '08',
    tag: '产业',
    title: '不是低端搬家\\n而是价值链重组',
    quote: '西部产业升级，不是低端产业搬家，而是用算力、能源、制造、服务和场景重组价值链。',
    image: 'industrial-workers.jpg',
    points: ['算力', '能源', '制造', '服务', '场景'],
    layout: 'industry'
  },
  {
    id: 'xhs-09-security',
    no: '09',
    tag: '安全腹地',
    title: '西部不是后方\\n而是韧性底盘',
    quote: '战略腹地不是“躲在后方”，而是在关键时刻能供给能源、承载产业、守住生态、稳住边疆、托住韧性。',
    image: 'qinghai-lake.jpg',
    points: ['供给能源', '承载产业', '守住生态', '稳住边疆', '托住韧性'],
    layout: 'security'
  },
  {
    id: 'xhs-10-exam-framework',
    no: '10',
    tag: '考场框架',
    title: '遇到西部发展\\n别再只写补短板',
    quote: '通道向西打开空间，算力向西重组要素，产业向西形成支点，安全向西托底韧性。',
    points: ['开放空间', '重组要素', '形成支点', '托底韧性'],
    layout: 'exam'
  },
  {
    id: 'xhs-11-application',
    no: '11',
    tag: '申论转译',
    title: '把区域题\\n写成国家能力题',
    quote: '真正要写的不是“西部要发展”，而是“西部在国家现代化布局中承担什么功能”。',
    points: ['开放功能', '要素功能', '产业功能', '安全功能'],
    layout: 'matrix'
  },
  {
    id: 'xhs-12-interview',
    no: '12',
    tag: '面试题卡',
    title: '现象认知题\\n这样拆',
    quote: '有人说，推动西部发展，关键是继续补短板、强基础。也有人说，西部正在成为国家发展的新支点。对此你怎么看？',
    points: ['补短板仍然必要', '但不能停在补短板', '通道让内陆成为开放前沿', '算力能源产业承载新质生产力', '生态边疆人才托住大国韧性'],
    layout: 'interview'
  },
  {
    id: 'xhs-13-answer-logic',
    no: '13',
    tag: '答题逻辑',
    title: '四句话\\n把层次答出来',
    quote: '从条件改善到功能重塑，从资源优势到能力供给，从区域发展到国家布局。',
    points: ['补基础：改善发展条件', '拓通道：扩大开放空间', '重产业：提升价值创造', '托安全：增强国家韧性'],
    layout: 'answer'
  },
  {
    id: 'xhs-14-material-bank',
    no: '14',
    tag: '素材记忆',
    title: '材料怎么记\\n才不会散',
    quote: '重庆看通道，庆阳看算力，青海看生态，贵州看产业，新疆看联通，人才看产教融合。',
    image: 'solar-desert.jpg',
    points: ['重庆：通道枢纽', '庆阳：东数西算', '青海：生态屏障', '贵州：富矿精开', '新疆：边疆联通', '高校：产教融合'],
    layout: 'material'
  },
  {
    id: 'xhs-15-closing',
    no: '15',
    tag: '收束金句',
    title: '不要把西部\\n写成远方',
    quote: '西部发展的高分写法，是看见西部如何在通道、算力、产业和安全中成为现代化中国的战略支点。',
    image: 'freight-rail.jpg',
    points: ['连接陆海', '承接算力', '重塑产业', '托住韧性'],
    layout: 'closing'
  }
];

const photoMeta = {
  'data-center.jpg': {
    pos: 'center 52%',
    map: 'server racks fill the frame with dark vertical lines; safe text zone is left and lower-left under a localized dark tint.'
  },
  'freight-rail.jpg': {
    pos: 'center 56%',
    map: 'train sits near the lower center on a straight rail line, mountains behind; title is safest in upper-left and lower-left margins.'
  },
  'industrial-workers.jpg': {
    pos: 'center 52%',
    map: 'factory line and workers fill the right and lower half; use image well or left text overlay, avoid covering upper-right faces.'
  },
  'logistics-warehouse.jpg': {
    pos: 'center 52%',
    map: 'warehouse shelves form strong diagonals with no faces; safe as a bottom image well or muted full-width evidence.'
  },
  'qinghai-lake.jpg': {
    pos: 'center 54%',
    map: 'yellow field in foreground, lake and sky in middle; safe title zone is upper-left sky or left margin.'
  },
  'rail-tunnel.jpg': {
    pos: 'center 50%',
    map: 'railway tunnel is centered with dark edges and bright exit; keep titles outside center vanishing point.'
  },
  'solar-desert.jpg': {
    pos: 'center 52%',
    map: 'solar panels occupy lower and center, sky is open; safe text zone sits in upper-left or separate panels.'
  },
  'xinjiang-mountains.jpg': {
    pos: 'center 50%',
    map: 'snow mountains are high in the frame, forest at bottom; keep text in left paper panel, preserve peaks.'
  }
};

const videos = [
  {
    id: 'video-cover-01',
    image: 'freight-rail.jpg',
    title: '大国向西\\n不是区域口号',
    subtitle: '通道 / 算力 / 产业 / 安全腹地',
    variant: 1
  },
  {
    id: 'video-cover-02',
    image: 'data-center.jpg',
    title: '通道算力产业安全\\n一起向西布局',
    subtitle: '把西部写成国家能力布局',
    variant: 2
  },
  {
    id: 'video-cover-03',
    image: 'qinghai-lake.jpg',
    title: '西部不是后方\\n而是战略支点',
    subtitle: '生态 / 能源 / 边疆 / 人才托住韧性',
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
  const cls = len > 105 ? 'quote xl' : len > 76 ? 'quote long' : len > 48 ? 'quote med' : 'quote';
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
  if (page.layout === 'photoFeature') {
    return `<section class="poster xhs photoFeature" id="${page.id}">
      <div class="paper"></div>${photo(page.image, 'bottomWide')}
      <div class="content">${top(page)}<h1>${titleHtml(page.title)}</h1>${quoteHtml(page)}
      <div class="triad">${page.points.map((x) => `<span>${escapeHtml(x)}</span>`).join('')}</div></div>
    </section>`;
  }
  if (page.layout === 'systemPhoto') {
    return `<section class="poster xhs systemPhoto" id="${page.id}">
      <div class="paper"></div>${photo(page.image, 'bottomWide')}
      <div class="content">${top(page)}<h1>${titleHtml(page.title)}</h1>${quoteHtml(page)}${cards(page.points)}</div>
    </section>`;
  }
  if (page.layout === 'darkQuote') {
    return `<section class="poster xhs darkQuote" id="${page.id}">
      ${photo(page.image, 'bleed')}<div class="darkTint"></div><div class="grain"></div>
      <div class="content">${top(page)}<h1>${titleHtml(page.title)}</h1>${quoteHtml(page)}
      <div class="darkNodes">${page.points.map((x) => `<span>${escapeHtml(x)}</span>`).join('')}</div></div>
    </section>`;
  }
  if (page.layout === 'industry') {
    return `<section class="poster xhs industry" id="${page.id}">
      <div class="paper"></div>${photo(page.image, 'rightPhoto')}
      <div class="content">${top(page)}<h1>${titleHtml(page.title)}</h1>${quoteHtml(page)}
      <div class="valueWheel">${page.points.map((x, i) => `<span class="p${i + 1}">${escapeHtml(x)}</span>`).join('')}<em>价值链</em></div></div>
    </section>`;
  }
  if (page.layout === 'security') {
    return `<section class="poster xhs security" id="${page.id}">
      ${photo(page.image, 'bleed')}<div class="securityTint"></div><div class="grain"></div>
      <div class="content">${top(page)}<h1>${titleHtml(page.title)}</h1>${quoteHtml(page)}
      <div class="securityGrid">${page.points.map((x) => `<span>${escapeHtml(x)}</span>`).join('')}</div></div>
    </section>`;
  }
  if (page.layout === 'exam') {
    return `<section class="poster xhs exam" id="${page.id}">
      <div class="paper"></div><div class="content">${top(page)}<h1>${titleHtml(page.title)}</h1>${quoteHtml(page)}
      <div class="examFlow">${page.points.map((x, i) => `<span><b>${String(i + 1).padStart(2, '0')}</b>${escapeHtml(x)}</span>`).join('<i></i>')}</div></div>
    </section>`;
  }
  if (page.layout === 'matrix') {
    return `<section class="poster xhs matrixPage" id="${page.id}">
      <div class="paper"></div><div class="content">${top(page)}<h1>${titleHtml(page.title)}</h1>${quoteHtml(page)}
      <div class="matrix">${page.points.map((x) => `<span>${escapeHtml(x)}</span>`).join('')}</div></div>
    </section>`;
  }
  if (page.layout === 'interview') {
    return `<section class="poster xhs interview" id="${page.id}">
      <div class="paper"></div><div class="content">${top(page)}<h1>${titleHtml(page.title)}</h1>${quoteHtml(page)}
      <div class="answerSteps">${page.points.map((x, i) => `<span><b>${String(i + 1).padStart(2, '0')}</b>${escapeHtml(x)}</span>`).join('')}</div></div>
    </section>`;
  }
  if (page.layout === 'answer') {
    return `<section class="poster xhs answer" id="${page.id}">
      <div class="paper"></div><div class="content">${top(page)}<h1>${titleHtml(page.title)}</h1>${quoteHtml(page)}
      <div class="answerGrid">${page.points.map((x) => `<span>${escapeHtml(x)}</span>`).join('')}</div></div>
    </section>`;
  }
  if (page.layout === 'material') {
    return `<section class="poster xhs material" id="${page.id}">
      <div class="paper"></div>${photo(page.image, 'topWide')}
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
body{background:#d8cdbd;font-family:"Avenir Next","Helvetica Neue","PingFang SC","Noto Sans SC","Microsoft YaHei",Arial,sans-serif;color:#172033}
.stage{width:max-content;display:grid;gap:34px;padding:34px}
.poster{position:relative;overflow:hidden;isolation:isolate;background:#efe3cf}
.xhs,.video{width:1080px;height:1440px}
.paper{position:absolute;inset:0;z-index:0;background:
  radial-gradient(circle at 85% 10%,rgba(191,53,39,.20),transparent 30%),
  radial-gradient(circle at 14% 92%,rgba(54,111,90,.22),transparent 35%),
  radial-gradient(circle at 78% 80%,rgba(199,129,43,.22),transparent 30%),
  repeating-linear-gradient(100deg,rgba(255,255,255,.06) 0 1px,transparent 1px 5px),
  linear-gradient(180deg,#f6ead6,#e7d9c3);background-size:auto,auto,auto,auto,auto}
.grain{position:absolute;inset:0;z-index:3;opacity:.26;background:repeating-linear-gradient(105deg,rgba(255,255,255,.10) 0 1px,transparent 1px 5px),radial-gradient(circle at 24% 18%,rgba(255,255,255,.28),transparent 28%);mix-blend-mode:soft-light;pointer-events:none}
.content{position:relative;z-index:5;height:100%;padding:58px;display:flex;flex-direction:column}
.top{display:flex;align-items:center;justify-content:space-between;gap:24px;border-bottom:2px solid rgba(23,32,51,.22);padding-bottom:20px;font-size:24px;line-height:1;font-weight:840}
.top span:first-child{font-size:38px;color:#bc3327;font-weight:900}
.cover .top,.darkQuote .top,.security .top,.closing .top{border-bottom-color:rgba(255,255,255,.46);color:#fff8e7}
.cover .top span:first-child,.darkQuote .top span:first-child,.security .top span:first-child,.closing .top span:first-child{color:#f1b45b}
.xhs h1{margin:28px 0 0;font-family:"Songti SC","STSong","Noto Serif CJK SC",serif;font-size:82px;line-height:1.04;font-weight:760;letter-spacing:0}
.quote{margin:28px 0 0;padding:24px 28px;background:rgba(255,248,231,.94);border-left:10px solid #bc3327;font-size:35px;line-height:1.34;font-weight:820}
.quote.med{font-size:30px;line-height:1.39}
.quote.long{font-size:25px;line-height:1.43}
.quote.xl{font-size:22px;line-height:1.46}
.photo{margin:0;overflow:hidden}
.photo img,.videoPhoto img{width:100%;height:100%;object-fit:cover;filter:saturate(.86) contrast(1.06) brightness(.92)}
.bleed{position:absolute;inset:0;z-index:1}
.coverTint{position:absolute;inset:0;z-index:2;background:linear-gradient(90deg,rgba(14,20,32,.90),rgba(14,20,32,.18) 70%,rgba(14,20,32,.44)),linear-gradient(180deg,rgba(14,20,32,.12),rgba(14,20,32,.40) 62%,rgba(14,20,32,.88))}
.series{margin:36px 0 0;color:#f1b45b;font-size:35px;line-height:1;font-weight:900}
.cover h1{margin-top:28px;color:#fff8e7;font-size:92px;max-width:880px}
.coverLine{margin-top:30px;width:885px;padding:20px 24px;background:rgba(255,248,231,.92);color:#172033;font-size:30px;font-weight:860}
.coverNodes{margin-top:auto;display:grid;grid-template-columns:1fr 28px 1fr 28px 1fr 28px 1fr;align-items:center}
.coverNodes span{height:132px;display:grid;place-items:center;text-align:center;background:#f6ead6;color:#172033;border-top:12px solid #bc3327;font-size:28px;font-weight:900}
.coverNodes span:nth-of-type(2){border-top-color:#c7812b}.coverNodes span:nth-of-type(3){border-top-color:#366f5a}.coverNodes span:nth-of-type(4){border-top-color:#172033}
.coverNodes i{height:4px;background:#f6ead6}
.wrongList{margin-top:38px;display:grid;grid-template-columns:repeat(2,1fr);gap:14px}
.wrongList span{height:168px;padding:22px;display:grid;align-content:space-between;background:#fff8e7;border:2px solid rgba(23,32,51,.18);font-size:31px;font-weight:820}
.wrongList b{font-size:23px;color:#bc3327}
.aside{margin-top:auto;display:grid;grid-template-columns:1fr 1fr;gap:14px}
.aside p{min-height:128px;margin:0;padding:22px;background:#172033;color:#fff8e7;font-size:28px;line-height:1.22;font-weight:850}
.sidePhoto{position:absolute;right:0;top:0;bottom:0;width:470px;z-index:1}
.quotePhoto:after{content:"";position:absolute;right:0;top:0;bottom:0;width:660px;z-index:2;background:linear-gradient(90deg,#f6ead6 0%,rgba(246,234,214,.90) 48%,rgba(246,234,214,.10) 100%)}
.quotePhoto .content{padding-right:420px}
.quotePhoto .quote{font-size:27px;line-height:1.42}
.keywordRail{margin-top:auto;display:grid;grid-template-columns:repeat(5,1fr);gap:10px}
.keywordRail span{height:126px;display:grid;place-items:center;text-align:center;background:#172033;color:#fff8e7;border-top:12px solid #bc3327;font-size:25px;font-weight:900}
.keywordRail span:nth-child(2),.keywordRail span:nth-child(4){border-top-color:#c7812b}.keywordRail span:nth-child(3),.keywordRail span:nth-child(5){border-top-color:#366f5a}
.formula .quote{font-size:32px}
.formulaRail{margin-top:auto;display:grid;grid-template-columns:1fr 28px 1fr 28px 1fr 28px 1fr;align-items:center}
.formulaRail span{height:330px;padding:20px 14px;display:grid;align-content:space-between;text-align:center;background:#172033;color:#fff8e7;font-size:28px;line-height:1.14;font-weight:900}
.formulaRail span:nth-of-type(2){background:#c7812b}.formulaRail span:nth-of-type(3){background:#366f5a}.formulaRail span:nth-of-type(4){background:#bc3327}
.formulaRail b{color:#ffe0a5;font-size:22px}
.formulaRail i{height:4px;background:#172033}
.bottomWide{position:absolute;left:58px;right:58px;bottom:58px;height:405px;z-index:1;border:3px solid rgba(188,51,39,.32)}
.photoFeature .content,.systemPhoto .content,.material .content{padding-bottom:535px}
.triad{margin-top:36px;display:grid;grid-template-columns:repeat(3,1fr);gap:14px}
.triad span{height:150px;display:grid;place-items:center;text-align:center;background:#172033;color:#fff8e7;border-top:12px solid #bc3327;font-size:29px;font-weight:900}
.triad span:nth-child(2){border-top-color:#c7812b}.triad span:nth-child(3){border-top-color:#366f5a}
.cards{margin-top:34px;display:grid;grid-template-columns:repeat(2,1fr);gap:14px}
.cards span{height:118px;padding:18px;display:grid;align-content:space-between;background:#fff8e7;border-top:12px solid #bc3327;font-size:25px;line-height:1.16;font-weight:850}
.cards span:nth-child(2),.cards span:nth-child(3){border-top-color:#c7812b}.cards span:nth-child(4){border-top-color:#366f5a}
.cards b{font-size:20px;color:#172033}
.darkTint{position:absolute;inset:0;z-index:2;background:linear-gradient(90deg,rgba(10,15,26,.90),rgba(10,15,26,.18) 67%,rgba(10,15,26,.52)),linear-gradient(180deg,rgba(10,15,26,.18),rgba(10,15,26,.82))}
.darkQuote h1{color:#fff8e7;font-size:79px}
.darkQuote .quote{font-size:28px;line-height:1.4}
.darkNodes{margin-top:auto;display:grid;grid-template-columns:repeat(3,1fr);gap:14px}
.darkNodes span{height:152px;display:grid;place-items:center;text-align:center;background:#f6ead6;color:#172033;border-top:12px solid #bc3327;font-size:29px;font-weight:900}
.darkNodes span:nth-child(2){border-top-color:#c7812b}.darkNodes span:nth-child(3){border-top-color:#366f5a}
.rightPhoto{position:absolute;right:58px;bottom:58px;width:410px;height:585px;z-index:1;border:3px solid rgba(188,51,39,.32)}
.industry .content{padding-right:500px}
.industry .quote{font-size:27px;line-height:1.42}
.valueWheel{margin-top:auto;position:relative;height:338px;background:linear-gradient(135deg,rgba(23,32,51,.10),rgba(199,129,43,.16));border:2px solid rgba(23,32,51,.22)}
.valueWheel span{position:absolute;width:142px;height:78px;display:grid;place-items:center;text-align:center;background:#172033;color:#fff8e7;font-size:23px;font-weight:880}
.valueWheel .p1{left:40px;top:38px}.valueWheel .p2{right:40px;top:34px}.valueWheel .p3{left:40px;bottom:42px}.valueWheel .p4{right:40px;bottom:38px}.valueWheel .p5{left:50%;top:50%;transform:translate(-50%,-50%);background:#bc3327}
.valueWheel em{position:absolute;left:50%;top:50%;width:138px;height:138px;margin:-69px 0 0 -69px;border:5px solid #c7812b;border-radius:50%;display:grid;place-items:center;color:#172033;font-size:22px;font-weight:900;font-style:normal}
.securityTint{position:absolute;inset:0;z-index:2;background:linear-gradient(90deg,rgba(14,20,32,.86),rgba(14,20,32,.10) 70%,rgba(14,20,32,.36)),linear-gradient(180deg,rgba(14,20,32,.10),rgba(14,20,32,.42) 60%,rgba(14,20,32,.86))}
.security h1{color:#fff8e7;font-size:80px}
.security .quote{font-size:25px;line-height:1.43}
.securityGrid{margin-top:auto;display:grid;grid-template-columns:repeat(5,1fr);gap:10px}
.securityGrid span{height:165px;padding:10px;display:grid;place-items:center;text-align:center;background:#f6ead6;color:#172033;border-top:12px solid #bc3327;font-size:24px;font-weight:900}
.securityGrid span:nth-child(2),.securityGrid span:nth-child(4){border-top-color:#c7812b}.securityGrid span:nth-child(3),.securityGrid span:nth-child(5){border-top-color:#366f5a}
.exam .quote{font-size:31px}
.examFlow{margin-top:auto;display:grid;grid-template-columns:1fr 28px 1fr 28px 1fr 28px 1fr;align-items:center}
.examFlow span{height:330px;padding:20px 14px;display:grid;align-content:space-between;text-align:center;background:#172033;color:#fff8e7;font-size:28px;line-height:1.14;font-weight:900}
.examFlow span:nth-of-type(2){background:#c7812b}.examFlow span:nth-of-type(3){background:#366f5a}.examFlow span:nth-of-type(4){background:#bc3327}
.examFlow b{color:#ffe0a5;font-size:22px}
.examFlow i{height:4px;background:#172033}
.matrix{margin-top:42px;display:grid;grid-template-columns:repeat(2,1fr);gap:14px}
.matrix span{height:215px;display:grid;place-items:center;text-align:center;background:#fff8e7;border-top:14px solid #bc3327;font-size:31px;font-weight:900}
.matrix span:nth-child(2),.matrix span:nth-child(3){border-top-color:#c7812b}.matrix span:nth-child(4){border-top-color:#366f5a}
.interview .quote{font-size:27px;line-height:1.42}
.answerSteps{margin-top:34px;display:grid;gap:12px}
.answerSteps span{height:94px;padding:0 20px;display:flex;align-items:center;gap:16px;background:#fff8e7;border-left:12px solid #bc3327;font-size:25px;line-height:1.16;font-weight:850}
.answerSteps span:nth-child(2),.answerSteps span:nth-child(4){border-left-color:#c7812b}.answerSteps span:nth-child(3),.answerSteps span:nth-child(5){border-left-color:#366f5a}
.answerSteps b{font-size:20px;color:#172033}
.answerGrid{margin-top:40px;display:grid;grid-template-columns:repeat(2,1fr);gap:14px}
.answerGrid span{height:198px;padding:20px;display:grid;place-items:center;text-align:center;background:#fff8e7;border-top:14px solid #bc3327;font-size:29px;line-height:1.16;font-weight:900}
.answerGrid span:nth-child(2),.answerGrid span:nth-child(3){border-top-color:#c7812b}.answerGrid span:nth-child(4){border-top-color:#366f5a}
.topWide{position:absolute;left:58px;right:58px;bottom:58px;height:375px;z-index:1;border:3px solid rgba(188,51,39,.32)}
.materialGrid{margin-top:30px;display:grid;grid-template-columns:repeat(3,1fr);gap:12px}
.materialGrid span{height:112px;padding:12px;display:grid;place-items:center;text-align:center;background:#fff8e7;border-top:12px solid #bc3327;font-size:23px;line-height:1.14;font-weight:880}
.materialGrid span:nth-child(2),.materialGrid span:nth-child(5){border-top-color:#c7812b}.materialGrid span:nth-child(3),.materialGrid span:nth-child(6){border-top-color:#366f5a}
.closingTint{position:absolute;inset:0;z-index:2;background:linear-gradient(90deg,rgba(14,20,32,.90),rgba(14,20,32,.16) 67%,rgba(14,20,32,.46)),linear-gradient(180deg,rgba(14,20,32,.18),rgba(14,20,32,.80))}
.closing h1{color:#fff8e7;font-size:80px}
.closing .quote{font-size:28px;line-height:1.42}
.closingNodes{margin-top:auto;display:grid;grid-template-columns:repeat(4,1fr);gap:12px}
.closingNodes span{height:146px;display:grid;place-items:center;text-align:center;background:#f6ead6;color:#172033;border-top:12px solid #bc3327;font-size:27px;font-weight:900}
.closingNodes span:nth-child(2),.closingNodes span:nth-child(4){border-top-color:#c7812b}.closingNodes span:nth-child(3){border-top-color:#366f5a}
.videoPhoto{position:absolute;inset:0;margin:0;z-index:1}
.videoPhoto img{filter:saturate(.86) contrast(1.08) brightness(.72)}
.videoTint{position:absolute;inset:0;z-index:2;background:linear-gradient(90deg,rgba(10,15,26,.92),rgba(10,15,26,.12) 70%),linear-gradient(180deg,rgba(10,15,26,.12),rgba(10,15,26,.30) 44%,rgba(10,15,26,.80))}
.magLines{position:absolute;inset:56px;z-index:3;border-top:2px solid rgba(255,255,255,.58);border-bottom:2px solid rgba(255,255,255,.42)}
.magLines:before{content:"";position:absolute;left:0;top:94px;width:210px;height:2px;background:rgba(255,255,255,.58)}
.magLines:after{content:"WESTWARD";position:absolute;right:0;top:24px;color:rgba(255,255,255,.72);font-size:20px;font-weight:820}
.videoTitle{position:absolute;left:64px;right:76px;bottom:96px;z-index:4;color:#fff8e7}
.v2 .videoTitle{bottom:104px}.v3 .videoTitle{bottom:96px}
.videoTitle p{margin:0 0 28px;color:#f1b45b;font-size:34px;line-height:1;font-weight:900}
.videoTitle h2{margin:0;font-family:"Songti SC","STSong","Noto Serif CJK SC",serif;font-size:86px;line-height:1.03;font-weight:780;letter-spacing:0;max-width:900px}
.v2 .videoTitle h2{font-size:73px}.v3 .videoTitle h2{font-size:82px}
.videoTitle span{display:block;width:max-content;max-width:875px;margin-top:26px;padding:14px 18px;background:#bc3327;color:#fff8e7;font-size:27px;font-weight:900}
.v2 .videoTitle span{background:#c7812b;color:#172033}.v3 .videoTitle span{background:#366f5a;color:#fff8e7}
.preview{width:1800px;background:#d8cdbd;padding:34px;display:grid;grid-template-columns:repeat(5,1fr);gap:18px}
.preview figure{margin:0;background:#fff8e7;padding:8px}
.preview img{width:100%;display:block}
.preview figcaption{padding:8px 2px 0;font-size:16px;font-weight:780;color:#303030}
`;

const html = `<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>大国向西小红书与视频号封面</title><style>${css}</style></head><body><main class="stage">${pages.map(renderPage).join('\n')}${videos.map(renderVideo).join('\n')}</main></body></html>`;
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
