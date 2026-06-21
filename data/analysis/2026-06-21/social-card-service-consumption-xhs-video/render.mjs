import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { chromium } from 'playwright';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const repoRoot = path.resolve(__dirname, '../../../..');
const mediaDir = path.join(repoRoot, 'media/images/2026-06-21-service-consumption-xhs-video');
const assetDir = path.join(mediaDir, 'assets');
const htmlPath = path.join(__dirname, 'index.html');

const out = (file) => path.join(mediaDir, file);
const rel = (file) => path.relative(__dirname, path.join(assetDir, file)).replaceAll(path.sep, '/');

const pages = [
  {
    id: 'xhs-01-cover',
    no: '01',
    tag: '人民日报材料转申论',
    title: '服务消费\\n不是发券促销',
    kicker: '把好服务嵌入生活半径',
    image: 'night-market.jpg',
    points: ['生活半径', '新场景', '长期留量', '优供给'],
    layout: 'cover'
  },
  {
    id: 'xhs-02-mistake',
    no: '02',
    tag: '常见误区',
    title: '别只写\\n发券打折夜市',
    quote: '这些能带来一次购买，但很难自动变成稳定消费意愿。',
    points: ['发消费券', '打折促销', '夜市活动', '网红商圈'],
    notes: ['短期刺激有用', '但高分要写：服务供给、场景运营、质量规范'],
    layout: 'mistake'
  },
  {
    id: 'xhs-03-core-judgement',
    no: '03',
    tag: '核心判断',
    title: '不是把人拉来\\n而是让人愿意留下',
    quote: '服务消费不是靠一次性刺激把人拉来，而是把优质服务嵌入生活半径，把新场景做成可停留、可参与、可复购的长期供给。',
    image: 'community-table.jpg',
    points: ['可停留', '可参与', '可复购', '长期供给'],
    layout: 'quotePhoto'
  },
  {
    id: 'xhs-04-formula',
    no: '04',
    tag: '核心公式',
    title: '考场先抓\\n这条供给链',
    quote: '服务进入生活半径 → 场景承接新需求 → 质量沉淀长期留量。',
    points: ['生活半径', '新需求', '长期留量'],
    layout: 'formula'
  },
  {
    id: 'xhs-05-radius',
    no: '05',
    tag: '生活半径',
    title: '真正增量\\n就在家门口',
    quote: '服务消费的真正增量，不只在远方的打卡点，也在群众每天能走到、办到、体验到的生活半径里。',
    image: 'neighborhood-cafe.jpg',
    points: ['走到', '办到', '体验到'],
    layout: 'photoFeature'
  },
  {
    id: 'xhs-06-embedded-service',
    no: '06',
    tag: '社区嵌入',
    title: '一刻钟生活圈\\n不是画半径',
    quote: '提振服务消费，要推动优质服务向社区延伸、向生活嵌入、向品质升级，让养老、托幼、医疗、政务、文化、休闲等服务跟着人的日常半径走。',
    image: 'community-center.jpg',
    points: ['养老', '托幼', '医疗', '政务', '文化', '休闲'],
    layout: 'serviceMap'
  },
  {
    id: 'xhs-07-scene-upgrade',
    no: '07',
    tag: '场景升级',
    title: '消费升级\\n不是多买商品',
    quote: '从商品到服务，从价格到体验，从流量到留量，这是服务消费的三次升级。',
    image: 'live-performance.jpg',
    points: ['商品 → 服务', '价格 → 体验', '流量 → 留量'],
    layout: 'darkQuote'
  },
  {
    id: 'xhs-08-new-scenes',
    no: '08',
    tag: '新需求',
    title: '把城市\\n组织成体验链',
    quote: '服务消费不能只写“卖东西”，要写“组织体验”。',
    image: 'theme-park-night.jpg',
    points: ['文旅演艺', '赛事票根', '夜游市集', '康养疗愈', '手作社群', '主题乐园'],
    layout: 'sceneGrid'
  },
  {
    id: 'xhs-09-quality',
    no: '09',
    tag: '长期留量',
    title: '爆红之后\\n要靠质量长红',
    quote: '服务消费从爆红到长红，拼的不是热闹，而是内容供给、运营能力和服务质量。',
    image: 'craft-workshop.jpg',
    points: ['内容供给', '运营能力', '服务质量'],
    layout: 'quality'
  },
  {
    id: 'xhs-10-good-supply',
    no: '10',
    tag: '高分写法',
    title: '把促消费\\n写成优供给',
    quote: '服务消费的高分写法，是把“促消费”写成“优供给”。',
    image: 'healthcare.jpg',
    points: ['尊重新需求', '扩大新供给', '守住质量安全', '引导理性消费'],
    layout: 'supply'
  },
  {
    id: 'xhs-11-exam-framework',
    no: '11',
    tag: '考场框架',
    title: '遇到服务消费\\n直接套这三步',
    quote: '服务进入生活半径，场景承接新需求，质量沉淀长期留量。',
    points: ['服务进入生活半径', '场景承接新需求', '质量沉淀长期留量'],
    layout: 'exam'
  },
  {
    id: 'xhs-12-interview',
    no: '12',
    tag: '面试题卡',
    title: '现象认知题\\n这样答',
    quote: '有人认为，提振消费主要靠发放消费券、开展促销活动。对此你怎么看？',
    points: ['短期刺激有必要', '但不能替代长期供给', '服务要靠近群众生活', '新场景承接新需求', '质量规范支撑长效发展'],
    layout: 'interview'
  },
  {
    id: 'xhs-13-answer-logic',
    no: '13',
    tag: '答题逻辑',
    title: '四句话\\n把层次答出来',
    quote: '消费券降低一次门槛，好服务形成长期意愿。',
    points: ['便利性：把服务送到身边', '体验感：把场景做得可参与', '品质感：把内容运营做扎实', '安全感：把标准监管补上'],
    layout: 'answer'
  },
  {
    id: 'xhs-14-material-bank',
    no: '14',
    tag: '素材记忆',
    title: '材料怎么记\\n才不会散',
    quote: '重庆看一刻钟生活圈，长沙看票根联动，萍乡看中医夜市，乐山看体卫融合，主题乐园看内容运营，情绪消费看规范监管。',
    image: 'night-market.jpg',
    points: ['重庆：生活圈', '长沙：票根联动', '萍乡：中医夜市', '乐山：体卫融合', '主题乐园：运营', '情绪消费：监管'],
    layout: 'material'
  },
  {
    id: 'xhs-15-closing',
    no: '15',
    tag: '收束金句',
    title: '不是让人\\n多买一点',
    quote: '提振服务消费，不是让人多买一点，而是让生活更方便、更有趣、更健康、更有品质。',
    image: 'night-market.jpg',
    points: ['更方便', '更有趣', '更健康', '更有品质'],
    layout: 'closing'
  }
];

const photoMeta = {
  'community-center.jpg': {
    pos: 'center 52%',
    map: 'people sit around a meeting table across the frame; use as image well, avoid placing text over faces.'
  },
  'community-table.jpg': {
    pos: 'center 52%',
    map: 'group dining scene with faces around center; keep text in left paper panel and image on the right.'
  },
  'craft-workshop.jpg': {
    pos: 'center 45%',
    map: 'craft table and plants are viewed from above, people at edges; safe text zones are paper panels or upper-left overlay.'
  },
  'healthcare.jpg': {
    pos: 'center 52%',
    map: 'bright hospital beds with clean empty space; use as bottom evidence image or soft background for quality and health service.'
  },
  'live-performance.jpg': {
    pos: 'center 56%',
    map: 'concert stage sits center-lower with crowd below; title can sit on left dark area without covering performers.'
  },
  'neighborhood-cafe.jpg': {
    pos: 'center 56%',
    map: 'small coffee table and street texture occupy right side; safe title zone is left and upper-left.'
  },
  'night-market.jpg': {
    pos: 'center 54%',
    map: 'busy night market signage and crowd across lower half; keep title in left dark zone and avoid covering bright shop signs.'
  },
  'theme-park-night.jpg': {
    pos: 'center 58%',
    map: 'amusement rides and skyline occupy lower and right half; left sky and lower-left tint are safe for title.'
  }
};

const videos = [
  {
    id: 'video-cover-01',
    image: 'night-market.jpg',
    title: '服务消费\\n不是发券促销',
    subtitle: '把好服务嵌入生活半径',
    variant: 1
  },
  {
    id: 'video-cover-02',
    image: 'live-performance.jpg',
    title: '从流量到留量\\n要靠场景和质量',
    subtitle: '生活半径 / 体验场景 / 长期供给',
    variant: 2
  },
  {
    id: 'video-cover-03',
    image: 'theme-park-night.jpg',
    title: '把促消费\\n写成优供给',
    subtitle: '可停留 / 可参与 / 可复购',
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
  const cls = len > 110 ? 'quote xl' : len > 78 ? 'quote long' : len > 48 ? 'quote med' : 'quote';
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
  if (page.layout === 'serviceMap') {
    return `<section class="poster xhs serviceMap" id="${page.id}">
      <div class="paper"></div>${photo(page.image, 'bottomWide')}
      <div class="content">${top(page)}<h1>${titleHtml(page.title)}</h1>${quoteHtml(page)}
      <div class="serviceNodes">${page.points.map((x) => `<span>${escapeHtml(x)}</span>`).join('')}</div></div>
    </section>`;
  }
  if (page.layout === 'darkQuote') {
    return `<section class="poster xhs darkQuote" id="${page.id}">
      ${photo(page.image, 'bleed')}<div class="darkTint"></div><div class="grain"></div>
      <div class="content">${top(page)}<h1>${titleHtml(page.title)}</h1>${quoteHtml(page)}
      <div class="darkNodes">${page.points.map((x) => `<span>${escapeHtml(x)}</span>`).join('')}</div></div>
    </section>`;
  }
  if (page.layout === 'sceneGrid') {
    return `<section class="poster xhs sceneGrid" id="${page.id}">
      <div class="paper"></div>${photo(page.image, 'topWide')}
      <div class="content">${top(page)}<h1>${titleHtml(page.title)}</h1>${quoteHtml(page)}
      <div class="sceneNodes">${page.points.map((x) => `<span>${escapeHtml(x)}</span>`).join('')}</div></div>
    </section>`;
  }
  if (page.layout === 'quality') {
    return `<section class="poster xhs quality" id="${page.id}">
      <div class="paper"></div>${photo(page.image, 'rightPhoto')}
      <div class="content">${top(page)}<h1>${titleHtml(page.title)}</h1>${quoteHtml(page)}
      <div class="qualityTriad">${page.points.map((x) => `<span>${escapeHtml(x)}</span>`).join('')}</div></div>
    </section>`;
  }
  if (page.layout === 'supply') {
    return `<section class="poster xhs supply" id="${page.id}">
      <div class="paper"></div>${photo(page.image, 'bottomWide')}
      <div class="content">${top(page)}<h1>${titleHtml(page.title)}</h1>${quoteHtml(page)}${cards(page.points)}</div>
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
  if (page.layout === 'answer') {
    return `<section class="poster xhs answer" id="${page.id}">
      <div class="paper"></div><div class="content">${top(page)}<h1>${titleHtml(page.title)}</h1>${quoteHtml(page)}
      <div class="answerGrid">${page.points.map((x) => `<span>${escapeHtml(x)}</span>`).join('')}</div></div>
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
body{background:#d7cec5;font-family:"Avenir Next","Helvetica Neue","PingFang SC","Noto Sans SC","Microsoft YaHei",Arial,sans-serif;color:#26322d}
.stage{width:max-content;display:grid;gap:34px;padding:34px}
.poster{position:relative;overflow:hidden;isolation:isolate;background:#f4e7dc}
.xhs,.video{width:1080px;height:1440px}
.paper{position:absolute;inset:0;z-index:0;background:
  radial-gradient(circle at 82% 12%,rgba(240,107,79,.22),transparent 30%),
  radial-gradient(circle at 12% 88%,rgba(79,141,116,.22),transparent 35%),
  radial-gradient(circle at 78% 80%,rgba(225,162,71,.22),transparent 30%),
  repeating-linear-gradient(100deg,rgba(255,255,255,.08) 0 1px,transparent 1px 5px),
  linear-gradient(180deg,#fbefe4,#eadccf);background-size:auto,auto,auto,auto,auto}
.grain{position:absolute;inset:0;z-index:3;opacity:.24;background:repeating-linear-gradient(105deg,rgba(255,255,255,.10) 0 1px,transparent 1px 5px),radial-gradient(circle at 24% 18%,rgba(255,255,255,.28),transparent 28%);mix-blend-mode:soft-light;pointer-events:none}
.content{position:relative;z-index:5;height:100%;padding:58px;display:flex;flex-direction:column}
.top{display:flex;align-items:center;justify-content:space-between;gap:24px;border-bottom:2px solid rgba(38,50,45,.22);padding-bottom:20px;font-size:24px;line-height:1;font-weight:840}
.top span:first-child{font-size:38px;color:#f06b4f;font-weight:900}
.cover .top,.darkQuote .top,.closing .top{border-bottom-color:rgba(255,255,255,.46);color:#fff8ef}
.cover .top span:first-child,.darkQuote .top span:first-child,.closing .top span:first-child{color:#ffd085}
.xhs h1{margin:28px 0 0;font-family:"Songti SC","STSong","Noto Serif CJK SC",serif;font-size:82px;line-height:1.04;font-weight:760;letter-spacing:0}
.quote{margin:28px 0 0;padding:24px 28px;background:rgba(255,248,239,.94);border-left:10px solid #f06b4f;font-size:35px;line-height:1.34;font-weight:820}
.quote.med{font-size:30px;line-height:1.39}
.quote.long{font-size:25px;line-height:1.43}
.quote.xl{font-size:22px;line-height:1.46}
.photo{margin:0;overflow:hidden}
.photo img,.videoPhoto img{width:100%;height:100%;object-fit:cover;filter:saturate(.88) contrast(1.04) brightness(.93)}
.bleed{position:absolute;inset:0;z-index:1}
.coverTint{position:absolute;inset:0;z-index:2;background:linear-gradient(90deg,rgba(22,31,28,.88),rgba(22,31,28,.16) 68%,rgba(22,31,28,.42)),linear-gradient(180deg,rgba(22,31,28,.18),rgba(22,31,28,.40) 58%,rgba(22,31,28,.88))}
.series{margin:36px 0 0;color:#ffd085;font-size:35px;line-height:1;font-weight:900}
.cover h1{margin-top:28px;color:#fff8ef;font-size:91px;max-width:880px}
.coverLine{margin-top:30px;width:880px;padding:20px 24px;background:rgba(255,248,239,.92);color:#26322d;font-size:30px;font-weight:860}
.coverNodes{margin-top:auto;display:grid;grid-template-columns:1fr 28px 1fr 28px 1fr 28px 1fr;align-items:center}
.coverNodes span{height:132px;display:grid;place-items:center;text-align:center;background:#fbefe4;color:#26322d;border-top:12px solid #f06b4f;font-size:28px;font-weight:900}
.coverNodes span:nth-of-type(2){border-top-color:#4f8d74}.coverNodes span:nth-of-type(3){border-top-color:#e1a247}.coverNodes span:nth-of-type(4){border-top-color:#26322d}
.coverNodes i{height:4px;background:#fbefe4}
.wrongList{margin-top:38px;display:grid;grid-template-columns:repeat(2,1fr);gap:14px}
.wrongList span{height:168px;padding:22px;display:grid;align-content:space-between;background:#fff8ef;border:2px solid rgba(38,50,45,.18);font-size:31px;font-weight:820}
.wrongList b{font-size:23px;color:#f06b4f}
.aside{margin-top:auto;display:grid;grid-template-columns:1fr 1fr;gap:14px}
.aside p{min-height:128px;margin:0;padding:22px;background:#26322d;color:#fff8ef;font-size:28px;line-height:1.22;font-weight:850}
.sidePhoto{position:absolute;right:0;top:0;bottom:0;width:470px;z-index:1}
.quotePhoto:after{content:"";position:absolute;right:0;top:0;bottom:0;width:670px;z-index:2;background:linear-gradient(90deg,#fbefe4 0%,rgba(251,239,228,.90) 49%,rgba(251,239,228,.10) 100%)}
.quotePhoto .content{padding-right:430px}
.quotePhoto .quote{font-size:25px;line-height:1.43}
.keywordRail{margin-top:auto;display:grid;grid-template-columns:repeat(4,1fr);gap:12px}
.keywordRail span{height:132px;display:grid;place-items:center;text-align:center;background:#26322d;color:#fff8ef;border-top:12px solid #f06b4f;font-size:26px;font-weight:900}
.keywordRail span:nth-child(2),.keywordRail span:nth-child(4){border-top-color:#4f8d74}.keywordRail span:nth-child(3){border-top-color:#e1a247}
.formula .quote{font-size:32px}
.formulaRail{margin-top:auto;display:grid;grid-template-columns:1fr 30px 1fr 30px 1fr;align-items:center}
.formulaRail span{height:335px;padding:20px 16px;display:grid;align-content:space-between;text-align:center;background:#26322d;color:#fff8ef;font-size:31px;line-height:1.14;font-weight:900}
.formulaRail span:nth-of-type(2){background:#4f8d74}.formulaRail span:nth-of-type(3){background:#f06b4f}
.formulaRail b{color:#ffe1ad;font-size:22px}
.formulaRail i{height:4px;background:#26322d}
.bottomWide{position:absolute;left:58px;right:58px;bottom:58px;height:405px;z-index:1;border:3px solid rgba(240,107,79,.32)}
.photoFeature .content,.serviceMap .content,.supply .content,.material .content{padding-bottom:535px}
.triad{margin-top:36px;display:grid;grid-template-columns:repeat(3,1fr);gap:14px}
.triad span{height:150px;display:grid;place-items:center;text-align:center;background:#26322d;color:#fff8ef;border-top:12px solid #f06b4f;font-size:29px;font-weight:900}
.triad span:nth-child(2){border-top-color:#4f8d74}.triad span:nth-child(3){border-top-color:#e1a247}
.serviceMap .quote{font-size:23px;line-height:1.45}
.serviceNodes{margin-top:32px;display:grid;grid-template-columns:repeat(3,1fr);gap:12px}
.serviceNodes span{height:104px;display:grid;place-items:center;text-align:center;background:#fff8ef;border-top:12px solid #f06b4f;font-size:25px;font-weight:900}
.serviceNodes span:nth-child(2),.serviceNodes span:nth-child(5){border-top-color:#4f8d74}.serviceNodes span:nth-child(3),.serviceNodes span:nth-child(6){border-top-color:#e1a247}
.darkTint{position:absolute;inset:0;z-index:2;background:linear-gradient(90deg,rgba(21,29,27,.90),rgba(21,29,27,.16) 67%,rgba(21,29,27,.46)),linear-gradient(180deg,rgba(21,29,27,.16),rgba(21,29,27,.82))}
.darkQuote h1{color:#fff8ef;font-size:82px}
.darkQuote .quote{font-size:30px;line-height:1.4}
.darkNodes{margin-top:auto;display:grid;grid-template-columns:repeat(3,1fr);gap:14px}
.darkNodes span{height:155px;display:grid;place-items:center;text-align:center;background:#fbefe4;color:#26322d;border-top:12px solid #f06b4f;font-size:28px;font-weight:900}
.darkNodes span:nth-child(2){border-top-color:#4f8d74}.darkNodes span:nth-child(3){border-top-color:#e1a247}
.topWide{position:absolute;left:58px;right:58px;bottom:58px;height:375px;z-index:1;border:3px solid rgba(240,107,79,.32)}
.sceneGrid .content{padding-bottom:505px}
.sceneNodes{margin-top:30px;display:grid;grid-template-columns:repeat(3,1fr);gap:12px}
.sceneNodes span{height:110px;padding:12px;display:grid;place-items:center;text-align:center;background:#fff8ef;border-top:12px solid #f06b4f;font-size:24px;line-height:1.14;font-weight:880}
.sceneNodes span:nth-child(2),.sceneNodes span:nth-child(5){border-top-color:#4f8d74}.sceneNodes span:nth-child(3),.sceneNodes span:nth-child(6){border-top-color:#e1a247}
.rightPhoto{position:absolute;right:58px;bottom:58px;width:410px;height:585px;z-index:1;border:3px solid rgba(240,107,79,.32)}
.quality .content{padding-right:500px}
.quality .quote{font-size:28px;line-height:1.4}
.qualityTriad{margin-top:auto;display:grid;gap:12px}
.qualityTriad span{height:92px;display:grid;place-items:center;text-align:center;background:#26322d;color:#fff8ef;border-left:12px solid #f06b4f;font-size:26px;font-weight:900}
.qualityTriad span:nth-child(2){border-left-color:#4f8d74}.qualityTriad span:nth-child(3){border-left-color:#e1a247}
.cards{margin-top:34px;display:grid;grid-template-columns:repeat(2,1fr);gap:14px}
.cards span{height:118px;padding:18px;display:grid;align-content:space-between;background:#fff8ef;border-top:12px solid #f06b4f;font-size:25px;line-height:1.16;font-weight:850}
.cards span:nth-child(2),.cards span:nth-child(3){border-top-color:#4f8d74}.cards span:nth-child(4){border-top-color:#e1a247}
.cards b{font-size:20px;color:#26322d}
.exam .quote{font-size:32px}
.examFlow{margin-top:auto;display:grid;grid-template-columns:1fr 30px 1fr 30px 1fr;align-items:center}
.examFlow span{height:335px;padding:20px 16px;display:grid;align-content:space-between;text-align:center;background:#26322d;color:#fff8ef;font-size:28px;line-height:1.14;font-weight:900}
.examFlow span:nth-of-type(2){background:#4f8d74}.examFlow span:nth-of-type(3){background:#f06b4f}
.examFlow b{color:#ffe1ad;font-size:22px}
.examFlow i{height:4px;background:#26322d}
.interview .quote{font-size:30px;line-height:1.4}
.answerSteps{margin-top:34px;display:grid;gap:12px}
.answerSteps span{height:94px;padding:0 20px;display:flex;align-items:center;gap:16px;background:#fff8ef;border-left:12px solid #f06b4f;font-size:25px;line-height:1.16;font-weight:850}
.answerSteps span:nth-child(2),.answerSteps span:nth-child(4){border-left-color:#4f8d74}.answerSteps span:nth-child(3),.answerSteps span:nth-child(5){border-left-color:#e1a247}
.answerSteps b{font-size:20px;color:#26322d}
.answerGrid{margin-top:40px;display:grid;grid-template-columns:repeat(2,1fr);gap:14px}
.answerGrid span{height:198px;padding:20px;display:grid;place-items:center;text-align:center;background:#fff8ef;border-top:14px solid #f06b4f;font-size:29px;line-height:1.16;font-weight:900}
.answerGrid span:nth-child(2),.answerGrid span:nth-child(3){border-top-color:#4f8d74}.answerGrid span:nth-child(4){border-top-color:#e1a247}
.material .quote{font-size:25px;line-height:1.42}
.materialGrid{margin-top:30px;display:grid;grid-template-columns:repeat(3,1fr);gap:12px}
.materialGrid span{height:112px;padding:12px;display:grid;place-items:center;text-align:center;background:#fff8ef;border-top:12px solid #f06b4f;font-size:23px;line-height:1.14;font-weight:880}
.materialGrid span:nth-child(2),.materialGrid span:nth-child(5){border-top-color:#4f8d74}.materialGrid span:nth-child(3),.materialGrid span:nth-child(6){border-top-color:#e1a247}
.closingTint{position:absolute;inset:0;z-index:2;background:linear-gradient(90deg,rgba(21,29,27,.90),rgba(21,29,27,.16) 67%,rgba(21,29,27,.46)),linear-gradient(180deg,rgba(21,29,27,.18),rgba(21,29,27,.80))}
.closing h1{color:#fff8ef;font-size:82px}
.closing .quote{font-size:29px;line-height:1.4}
.closingNodes{margin-top:auto;display:grid;grid-template-columns:repeat(4,1fr);gap:12px}
.closingNodes span{height:146px;display:grid;place-items:center;text-align:center;background:#fbefe4;color:#26322d;border-top:12px solid #f06b4f;font-size:27px;font-weight:900}
.closingNodes span:nth-child(2),.closingNodes span:nth-child(4){border-top-color:#4f8d74}.closingNodes span:nth-child(3){border-top-color:#e1a247}
.videoPhoto{position:absolute;inset:0;margin:0;z-index:1}
.videoPhoto img{filter:saturate(.86) contrast(1.08) brightness(.72)}
.videoTint{position:absolute;inset:0;z-index:2;background:linear-gradient(90deg,rgba(21,29,27,.92),rgba(21,29,27,.12) 70%),linear-gradient(180deg,rgba(21,29,27,.12),rgba(21,29,27,.30) 44%,rgba(21,29,27,.80))}
.magLines{position:absolute;inset:56px;z-index:3;border-top:2px solid rgba(255,255,255,.58);border-bottom:2px solid rgba(255,255,255,.42)}
.magLines:before{content:"";position:absolute;left:0;top:94px;width:210px;height:2px;background:rgba(255,255,255,.58)}
.magLines:after{content:"SERVICE";position:absolute;right:0;top:24px;color:rgba(255,255,255,.72);font-size:20px;font-weight:820}
.videoTitle{position:absolute;left:64px;right:76px;bottom:96px;z-index:4;color:#fff8ef}
.videoTitle p{margin:0 0 28px;color:#ffd085;font-size:34px;line-height:1;font-weight:900}
.videoTitle h2{margin:0;font-family:"Songti SC","STSong","Noto Serif CJK SC",serif;font-size:84px;line-height:1.03;font-weight:780;letter-spacing:0;max-width:900px}
.v2 .videoTitle h2{font-size:76px}.v3 .videoTitle h2{font-size:86px}
.videoTitle span{display:block;width:max-content;max-width:875px;margin-top:26px;padding:14px 18px;background:#f06b4f;color:#fff8ef;font-size:27px;font-weight:900}
.v2 .videoTitle span{background:#4f8d74;color:#fff8ef}.v3 .videoTitle span{background:#e1a247;color:#26322d}
.preview{width:1800px;background:#d7cec5;padding:34px;display:grid;grid-template-columns:repeat(5,1fr);gap:18px}
.preview figure{margin:0;background:#fff8ef;padding:8px}
.preview img{width:100%;display:block}
.preview figcaption{padding:8px 2px 0;font-size:16px;font-weight:780;color:#303030}
`;

const html = `<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>服务消费小红书与视频号封面</title><style>${css}</style></head><body><main class="stage">${pages.map(renderPage).join('\n')}${videos.map(renderVideo).join('\n')}</main></body></html>`;
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
