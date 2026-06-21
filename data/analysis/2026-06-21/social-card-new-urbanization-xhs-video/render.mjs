import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { chromium } from 'playwright';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const repoRoot = path.resolve(__dirname, '../../../..');
const mediaDir = path.join(repoRoot, 'media/images/2026-06-21-new-urbanization-xhs-video');
const assetDir = path.join(mediaDir, 'assets');
const htmlPath = path.join(__dirname, 'index.html');

const out = (file) => path.join(mediaDir, file);
const rel = (file) => path.relative(__dirname, path.join(assetDir, file)).replaceAll(path.sep, '/');

const pages = [
  {
    id: 'xhs-01-cover',
    no: '01',
    tag: '人民日报材料转申论',
    title: '新型城镇化\\n不是进城落脚',
    kicker: '而是服务跟着人走',
    image: 'urban-community.jpg',
    points: ['对象识别', '资源配置', '风险兜底', '发展空间'],
    layout: 'cover'
  },
  {
    id: 'xhs-02-mistake',
    no: '02',
    tag: '常见误区',
    title: '别只写\\n人进了城',
    quote: '只写放开户籍、提高城镇化率、修路建房，文章就停在“人进了城”。',
    points: ['放开放宽落户', '提高城镇化率', '修路建房扩城', '农民进城聚集'],
    notes: ['这些能写，但不是终点', '高分要写出：城市有没有把人接住'],
    layout: 'mistake'
  },
  {
    id: 'xhs-03-core-judgement',
    no: '03',
    tag: '核心判断',
    title: '不是统计进城市\\n而是服务重新配置',
    quote: '新型城镇化不是把人统计进城市，而是让教育、就业、住房、养老、医疗和权益保障沿着人的常住地、生活半径和职业风险重新配置。',
    image: 'residential-buildings.jpg',
    points: ['教育', '就业', '住房', '养老', '医疗', '权益保障'],
    layout: 'quotePhoto'
  },
  {
    id: 'xhs-04-formula',
    no: '04',
    tag: '核心公式',
    title: '考场先抓\\n这条服务链',
    quote: '对象跟着人识别 → 资源跟着需求配置 → 治理跟着风险兜底。',
    points: ['对象识别', '资源配置', '风险兜底'],
    layout: 'formula'
  },
  {
    id: 'xhs-05-object',
    no: '05',
    tag: '对象识别',
    title: '第一步\\n不是看户籍簿',
    quote: '推进以人为本的新型城镇化，要以常住人口为基本尺度，把新市民、随迁子女、新就业群体、老年人等纳入公共服务视野，让服务对象从“户籍上是谁”转向“实际在哪里生活、在哪里工作、在哪里需要服务”。',
    image: 'public-transport.jpg',
    points: ['新市民', '随迁子女', '新就业群体', '老年人'],
    layout: 'objectPhoto'
  },
  {
    id: 'xhs-06-real-people',
    no: '06',
    tag: '真实人群',
    title: '从抽象人口\\n看到真实需求',
    quote: '公共服务不再只按户籍人口识别对象，而要按常住人口识别真实需求。',
    points: ['孩子能否就近上学', '孕产妇能否常住地享服务', '外来务工人员能否申请住房保障', '新就业群体能否获得权益保护'],
    layout: 'needMatrix'
  },
  {
    id: 'xhs-07-radius',
    no: '07',
    tag: '生活半径',
    title: '第二层能力\\n让服务够得到',
    quote: '新型城镇化的第二层能力，是让公共服务进入人的生活半径和发展半径。',
    image: 'classroom.jpg',
    points: ['教育', '住房', '医疗', '养老', '就业'],
    layout: 'photoFeature'
  },
  {
    id: 'xhs-08-service-extension',
    no: '08',
    tag: '资源配置',
    title: '服务不是平均铺摊子\\n而是精准进半径',
    quote: '要推动教育、住房、医疗、养老、就业等服务从户籍地延伸到常住地，从行政窗口延伸到社区网点，从单一供给延伸到精准匹配，让新市民在工作地、居住地、生活圈内享有稳定可及的基本服务。',
    image: 'clinic.jpg',
    points: ['户籍地 → 常住地', '行政窗口 → 社区网点', '单一供给 → 精准匹配'],
    layout: 'extension'
  },
  {
    id: 'xhs-09-risk',
    no: '09',
    tag: '风险兜底',
    title: '第三层能力\\n把风险接住',
    quote: '新型城镇化的第三层能力，是让治理跟着风险走，把新市民从“住得下”推向“稳得住、融得进、发展好”。',
    image: 'delivery-rider.jpg',
    points: ['住得下', '稳得住', '融得进', '发展好'],
    layout: 'darkQuote'
  },
  {
    id: 'xhs-10-governance',
    no: '10',
    tag: '治理兜底',
    title: '服务扩面以后\\n更要防断档',
    quote: '要以风险治理提升城镇化质量，围绕资源紧平衡、跨域服务断档、平台劳动权益、数字服务门槛等问题，完善协同机制、数据共享、权益保障和线下兜底，让公共服务扩面不失序、提质不断档。',
    points: ['资源紧平衡', '跨域服务断档', '平台劳动权益', '数字服务门槛'],
    layout: 'governance'
  },
  {
    id: 'xhs-11-exam-framework',
    no: '11',
    tag: '考场框架',
    title: '遇到城镇化\\n直接写这三步',
    quote: '对象跟着人识别，资源跟着需求配置，治理跟着风险兜底。',
    points: ['对象跟着人识别', '资源跟着需求配置', '治理跟着风险兜底'],
    layout: 'exam'
  },
  {
    id: 'xhs-12-interview',
    no: '12',
    tag: '面试题卡',
    title: '现象认知题\\n这样答',
    quote: '有人认为，新型城镇化关键是让更多人进城落户；也有人认为，更关键的是让服务跟着人走。对此你怎么看？',
    points: ['进城落户是前提，不是终点', '服务跟常住人口走，才能真正融入', '资源跟真实需求走，提升承接能力', '治理跟新风险走，提升城镇化质量'],
    layout: 'interview'
  },
  {
    id: 'xhs-13-answer-logic',
    no: '13',
    tag: '答题逻辑',
    title: '四句话\\n把层次答出来',
    quote: '人来了，城市要看见他；需求来了，资源要跟上去；风险来了，治理要接得住。',
    points: ['看见人：以常住人口为尺度', '接住人：服务进入生活半径', '托住人：风险治理及时兜底', '发展人：公共服务转化为城市活力'],
    layout: 'answer'
  },
  {
    id: 'xhs-14-material-bank',
    no: '14',
    tag: '素材记忆',
    title: '材料怎么记\\n才不会散',
    quote: '南昌看产检服务，温州看随迁子女入学，长沙看公租房保障，养老看助餐和管家，骑手看算法协商，就业看人岗智配。',
    image: 'job-training.jpg',
    points: ['南昌：产检服务', '温州：普惠入学', '长沙：公租房', '养老：助餐管家', '骑手：算法协商', '就业：人岗智配'],
    layout: 'material'
  },
  {
    id: 'xhs-15-closing',
    no: '15',
    tag: '收束金句',
    title: '不是让人\\n进城落脚',
    quote: '新型城镇化不是让人进城落脚，而是让服务跟着人走，让城市真正成为人的发展空间。',
    image: 'urban-community.jpg',
    points: ['服务跟着人走', '城市接得住人', '人融得进城市', '发展有空间'],
    layout: 'closing'
  }
];

const photoMeta = {
  'city-housing.jpg': {
    pos: 'center 52%',
    map: 'bright residential towers fill the upper frame with sky; safe title zone is left or separate paper block.'
  },
  'classroom.jpg': {
    pos: 'center 52%',
    map: 'children and teacher sit across the center; use as lower image well and do not place text over faces.'
  },
  'clinic.jpg': {
    pos: 'center 52%',
    map: 'clinic entrance and building facade fill frame with cars below; use as evidence image or muted right photo.'
  },
  'delivery-rider.jpg': {
    pos: 'center 54%',
    map: 'delivery rider is on the right with snowy street; safe title zone is left dark area.'
  },
  'elderly-care.jpg': {
    pos: 'center 50%',
    map: 'hands fill the center-left, intimate caregiving detail; best as small evidence image or soft page background.'
  },
  'job-training.jpg': {
    pos: 'center 52%',
    map: 'training room participants face front, focal person near center; use as bottom image well.'
  },
  'public-transport.jpg': {
    pos: 'center 50%',
    map: 'tram and riders sit in lower-middle of a tall street; text should stay in paper panel or top-left.'
  },
  'residential-buildings.jpg': {
    pos: 'center 50%',
    map: 'apartment tower rises on the right with pale sky; large text can sit in left paper column.'
  },
  'senior-service.jpg': {
    pos: 'center 52%',
    map: 'elderly person with wheelchair is silhouetted on left in open field; title can sit upper-right.'
  },
  'urban-community.jpg': {
    pos: 'center 54%',
    map: 'aerial neighborhood grid fills the frame; no faces, title can sit on a localized left dark tint.'
  }
};

const videos = [
  {
    id: 'video-cover-01',
    image: 'urban-community.jpg',
    title: '新型城镇化\\n不是进城落脚',
    subtitle: '而是服务跟着人走',
    variant: 1
  },
  {
    id: 'video-cover-02',
    image: 'residential-buildings.jpg',
    title: '城市有没有\\n把人接住',
    subtitle: '教育 / 就业 / 住房 / 养老 / 医疗',
    variant: 2
  },
  {
    id: 'video-cover-03',
    image: 'delivery-rider.jpg',
    title: '对象资源治理\\n都要跟着人走',
    subtitle: '对象识别 / 资源配置 / 风险兜底',
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
  const cls = len > 115 ? 'quote xl' : len > 82 ? 'quote long' : len > 50 ? 'quote med' : 'quote';
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
body{background:#cfd8d2;font-family:"Avenir Next","Helvetica Neue","PingFang SC","Noto Sans SC","Microsoft YaHei",Arial,sans-serif;color:#173136}
.stage{width:max-content;display:grid;gap:34px;padding:34px}
.poster{position:relative;overflow:hidden;isolation:isolate;background:#edf1e7}
.xhs,.video{width:1080px;height:1440px}
.paper{position:absolute;inset:0;z-index:0;background:
  radial-gradient(circle at 82% 12%,rgba(47,111,115,.22),transparent 30%),
  radial-gradient(circle at 14% 88%,rgba(125,168,123,.24),transparent 35%),
  radial-gradient(circle at 78% 80%,rgba(240,179,92,.20),transparent 30%),
  repeating-linear-gradient(100deg,rgba(255,255,255,.08) 0 1px,transparent 1px 5px),
  linear-gradient(180deg,#f4f5eb,#e1eadf);background-size:auto,auto,auto,auto,auto}
.grain{position:absolute;inset:0;z-index:3;opacity:.24;background:repeating-linear-gradient(105deg,rgba(255,255,255,.10) 0 1px,transparent 1px 5px),radial-gradient(circle at 24% 18%,rgba(255,255,255,.28),transparent 28%);mix-blend-mode:soft-light;pointer-events:none}
.content{position:relative;z-index:5;height:100%;padding:58px;display:flex;flex-direction:column}
.top{display:flex;align-items:center;justify-content:space-between;gap:24px;border-bottom:2px solid rgba(23,49,54,.22);padding-bottom:20px;font-size:24px;line-height:1;font-weight:840}
.top span:first-child{font-size:38px;color:#2f6f73;font-weight:900}
.cover .top,.darkQuote .top,.closing .top{border-bottom-color:rgba(255,255,255,.46);color:#f7f5e7}
.cover .top span:first-child,.darkQuote .top span:first-child,.closing .top span:first-child{color:#f0b35c}
.xhs h1{margin:28px 0 0;font-family:"Songti SC","STSong","Noto Serif CJK SC",serif;font-size:82px;line-height:1.04;font-weight:760;letter-spacing:0}
.quote{margin:28px 0 0;padding:24px 28px;background:rgba(250,248,236,.94);border-left:10px solid #2f6f73;font-size:35px;line-height:1.34;font-weight:820}
.quote.med{font-size:30px;line-height:1.39}
.quote.long{font-size:25px;line-height:1.43}
.quote.xl{font-size:21px;line-height:1.46}
.photo{margin:0;overflow:hidden}
.photo img,.videoPhoto img{width:100%;height:100%;object-fit:cover;filter:saturate(.88) contrast(1.04) brightness(.93)}
.bleed{position:absolute;inset:0;z-index:1}
.coverTint{position:absolute;inset:0;z-index:2;background:linear-gradient(90deg,rgba(16,37,43,.90),rgba(16,37,43,.16) 68%,rgba(16,37,43,.44)),linear-gradient(180deg,rgba(16,37,43,.18),rgba(16,37,43,.36) 58%,rgba(16,37,43,.88))}
.series{margin:36px 0 0;color:#f0b35c;font-size:35px;line-height:1;font-weight:900}
.cover h1{margin-top:28px;color:#f7f5e7;font-size:88px;max-width:895px}
.coverLine{margin-top:30px;width:870px;padding:20px 24px;background:rgba(250,248,236,.92);color:#173136;font-size:30px;font-weight:860}
.coverNodes{margin-top:auto;display:grid;grid-template-columns:1fr 28px 1fr 28px 1fr 28px 1fr;align-items:center}
.coverNodes span{height:132px;display:grid;place-items:center;text-align:center;background:#edf1e7;color:#173136;border-top:12px solid #2f6f73;font-size:28px;font-weight:900}
.coverNodes span:nth-of-type(2){border-top-color:#7da87b}.coverNodes span:nth-of-type(3){border-top-color:#f0b35c}.coverNodes span:nth-of-type(4){border-top-color:#173136}
.coverNodes i{height:4px;background:#edf1e7}
.wrongList{margin-top:38px;display:grid;grid-template-columns:repeat(2,1fr);gap:14px}
.wrongList span{height:168px;padding:22px;display:grid;align-content:space-between;background:#faf8ec;border:2px solid rgba(23,49,54,.18);font-size:31px;font-weight:820}
.wrongList b{font-size:23px;color:#2f6f73}
.aside{margin-top:auto;display:grid;grid-template-columns:1fr 1fr;gap:14px}
.aside p{min-height:128px;margin:0;padding:22px;background:#173136;color:#f7f5e7;font-size:28px;line-height:1.22;font-weight:850}
.sidePhoto{position:absolute;right:0;top:0;bottom:0;width:455px;z-index:1}
.quotePhoto:after{content:"";position:absolute;right:0;top:0;bottom:0;width:670px;z-index:2;background:linear-gradient(90deg,#edf1e7 0%,rgba(237,241,231,.90) 49%,rgba(237,241,231,.10) 100%)}
.quotePhoto .content{padding-right:410px}
.quotePhoto .quote{font-size:22px;line-height:1.46}
.keywordRail{margin-top:auto;display:grid;grid-template-columns:repeat(3,1fr);gap:12px}
.keywordRail span{height:108px;display:grid;place-items:center;text-align:center;background:#173136;color:#f7f5e7;border-top:12px solid #2f6f73;font-size:23px;font-weight:900}
.keywordRail span:nth-child(2),.keywordRail span:nth-child(5){border-top-color:#7da87b}.keywordRail span:nth-child(3),.keywordRail span:nth-child(6){border-top-color:#f0b35c}
.formula .quote{font-size:32px}
.formulaRail,.examFlow{margin-top:auto;display:grid;grid-template-columns:1fr 30px 1fr 30px 1fr;align-items:center}
.formulaRail span,.examFlow span{height:335px;padding:20px 16px;display:grid;align-content:space-between;text-align:center;background:#173136;color:#f7f5e7;font-size:29px;line-height:1.14;font-weight:900}
.formulaRail span:nth-of-type(2),.examFlow span:nth-of-type(2){background:#7da87b;color:#173136}.formulaRail span:nth-of-type(3),.examFlow span:nth-of-type(3){background:#2f6f73}
.formulaRail b,.examFlow b{color:#ffe1ad;font-size:22px}
.formulaRail i,.examFlow i{height:4px;background:#173136}
.bottomWide{position:absolute;left:58px;right:58px;bottom:58px;height:405px;z-index:1;border:3px solid rgba(47,111,115,.32)}
.objectPhoto .content,.photoFeature .content,.material .content{padding-bottom:535px}
.objectPhoto .quote{font-size:20px;line-height:1.45}
.cards{margin-top:30px;display:grid;grid-template-columns:repeat(2,1fr);gap:12px}
.cards span{height:92px;padding:14px;display:grid;align-content:space-between;background:#faf8ec;border-top:12px solid #2f6f73;font-size:22px;line-height:1.14;font-weight:860}
.cards span:nth-child(2),.cards span:nth-child(3){border-top-color:#7da87b}.cards span:nth-child(4){border-top-color:#f0b35c}
.cards b{font-size:18px;color:#173136}
.matrix{margin-top:40px;display:grid;grid-template-columns:repeat(2,1fr);gap:14px}
.matrix span{height:200px;padding:20px;display:grid;place-items:center;text-align:center;background:#faf8ec;border-top:14px solid #2f6f73;font-size:28px;line-height:1.16;font-weight:900}
.matrix span:nth-child(2),.matrix span:nth-child(3){border-top-color:#7da87b}.matrix span:nth-child(4){border-top-color:#f0b35c}
.needMatrix:after{content:"户籍人口 → 常住人口 → 真实需求";position:absolute;left:58px;right:58px;bottom:86px;height:158px;z-index:1;display:grid;place-items:center;background:rgba(250,248,236,.78);border-top:3px solid rgba(47,111,115,.45);border-bottom:3px solid rgba(47,111,115,.24);color:#173136;font-size:34px;font-weight:900}
.serviceStrip{margin-top:36px;display:grid;grid-template-columns:repeat(5,1fr);gap:10px}
.serviceStrip span{height:136px;padding:10px;display:grid;place-items:center;text-align:center;background:#173136;color:#f7f5e7;border-top:12px solid #2f6f73;font-size:25px;font-weight:900}
.serviceStrip span:nth-child(2),.serviceStrip span:nth-child(4){border-top-color:#7da87b}.serviceStrip span:nth-child(3),.serviceStrip span:nth-child(5){border-top-color:#f0b35c}
.rightPhoto{position:absolute;right:58px;bottom:58px;width:410px;height:585px;z-index:1;border:3px solid rgba(47,111,115,.32)}
.extension .content{padding-right:500px}
.extension .quote{font-size:20px;line-height:1.45}
.extensionRows{margin-top:auto;display:grid;gap:12px}
.extensionRows span{height:88px;display:grid;place-items:center;text-align:center;background:#173136;color:#f7f5e7;border-left:12px solid #2f6f73;font-size:24px;font-weight:900}
.extensionRows span:nth-child(2){border-left-color:#7da87b}.extensionRows span:nth-child(3){border-left-color:#f0b35c}
.darkTint{position:absolute;inset:0;z-index:2;background:linear-gradient(90deg,rgba(16,37,43,.90),rgba(16,37,43,.16) 67%,rgba(16,37,43,.48)),linear-gradient(180deg,rgba(16,37,43,.14),rgba(16,37,43,.82))}
.darkQuote h1{color:#f7f5e7;font-size:82px}
.darkQuote .quote{font-size:25px;line-height:1.43}
.darkNodes{margin-top:auto;display:grid;grid-template-columns:repeat(4,1fr);gap:12px}
.darkNodes span{height:146px;display:grid;place-items:center;text-align:center;background:#edf1e7;color:#173136;border-top:12px solid #2f6f73;font-size:27px;font-weight:900}
.darkNodes span:nth-child(2),.darkNodes span:nth-child(4){border-top-color:#7da87b}.darkNodes span:nth-child(3){border-top-color:#f0b35c}
.governance .quote{font-size:20px;line-height:1.45}
.governGrid{margin-top:38px;display:grid;grid-template-columns:repeat(2,1fr);gap:14px}
.governGrid span{height:205px;padding:20px;display:grid;place-items:center;text-align:center;background:#faf8ec;border-top:14px solid #2f6f73;font-size:30px;line-height:1.16;font-weight:900}
.governGrid span:nth-child(2),.governGrid span:nth-child(3){border-top-color:#7da87b}.governGrid span:nth-child(4){border-top-color:#f0b35c}
.governance:after{content:"协同机制 · 数据共享 · 权益保障 · 线下兜底";position:absolute;left:58px;right:58px;bottom:94px;height:154px;z-index:1;display:grid;place-items:center;background:#173136;color:#f7f5e7;border-top:14px solid #f0b35c;font-size:31px;font-weight:900}
.exam .quote{font-size:32px}
.interview .quote{font-size:28px;line-height:1.4}
.answerSteps{margin-top:34px;display:grid;gap:14px}
.answerSteps span{height:108px;padding:0 20px;display:flex;align-items:center;gap:16px;background:#faf8ec;border-left:12px solid #2f6f73;font-size:25px;line-height:1.16;font-weight:850}
.answerSteps span:nth-child(2),.answerSteps span:nth-child(4){border-left-color:#7da87b}.answerSteps span:nth-child(3){border-left-color:#f0b35c}
.answerSteps b{font-size:20px;color:#173136}
.answerGrid{margin-top:40px;display:grid;grid-template-columns:repeat(2,1fr);gap:14px}
.answerGrid span{height:198px;padding:20px;display:grid;place-items:center;text-align:center;background:#faf8ec;border-top:14px solid #2f6f73;font-size:27px;line-height:1.16;font-weight:900}
.answerGrid span:nth-child(2),.answerGrid span:nth-child(3){border-top-color:#7da87b}.answerGrid span:nth-child(4){border-top-color:#f0b35c}
.material .quote{font-size:24px;line-height:1.42}
.materialGrid{margin-top:30px;display:grid;grid-template-columns:repeat(3,1fr);gap:12px}
.materialGrid span{height:112px;padding:12px;display:grid;place-items:center;text-align:center;background:#faf8ec;border-top:12px solid #2f6f73;font-size:23px;line-height:1.14;font-weight:880}
.materialGrid span:nth-child(2),.materialGrid span:nth-child(5){border-top-color:#7da87b}.materialGrid span:nth-child(3),.materialGrid span:nth-child(6){border-top-color:#f0b35c}
.closingTint{position:absolute;inset:0;z-index:2;background:linear-gradient(90deg,rgba(16,37,43,.90),rgba(16,37,43,.14) 67%,rgba(16,37,43,.46)),linear-gradient(180deg,rgba(16,37,43,.18),rgba(16,37,43,.80))}
.closing h1{color:#f7f5e7;font-size:82px}
.closing .quote{font-size:28px;line-height:1.4}
.closingNodes{margin-top:auto;display:grid;grid-template-columns:repeat(4,1fr);gap:12px}
.closingNodes span{height:146px;display:grid;place-items:center;text-align:center;background:#edf1e7;color:#173136;border-top:12px solid #2f6f73;font-size:25px;font-weight:900}
.closingNodes span:nth-child(2),.closingNodes span:nth-child(4){border-top-color:#7da87b}.closingNodes span:nth-child(3){border-top-color:#f0b35c}
.videoPhoto{position:absolute;inset:0;margin:0;z-index:1}
.videoPhoto img{filter:saturate(.86) contrast(1.08) brightness(.72)}
.videoTint{position:absolute;inset:0;z-index:2;background:linear-gradient(90deg,rgba(16,37,43,.92),rgba(16,37,43,.12) 70%),linear-gradient(180deg,rgba(16,37,43,.12),rgba(16,37,43,.30) 44%,rgba(16,37,43,.82))}
.magLines{position:absolute;inset:56px;z-index:3;border-top:2px solid rgba(255,255,255,.58);border-bottom:2px solid rgba(255,255,255,.42)}
.magLines:before{content:"";position:absolute;left:0;top:94px;width:210px;height:2px;background:rgba(255,255,255,.58)}
.magLines:after{content:"URBANIZATION";position:absolute;right:0;top:24px;color:rgba(255,255,255,.72);font-size:20px;font-weight:820}
.videoTitle{position:absolute;left:64px;right:76px;bottom:96px;z-index:4;color:#f7f5e7}
.videoTitle p{margin:0 0 28px;color:#f0b35c;font-size:34px;line-height:1;font-weight:900}
.videoTitle h2{margin:0;font-family:"Songti SC","STSong","Noto Serif CJK SC",serif;font-size:82px;line-height:1.03;font-weight:780;letter-spacing:0;max-width:900px}
.v3 .videoTitle h2{font-size:76px}
.videoTitle span{display:block;width:max-content;max-width:875px;margin-top:26px;padding:14px 18px;background:#2f6f73;color:#f7f5e7;font-size:27px;font-weight:900}
.v2 .videoTitle span{background:#7da87b;color:#173136}.v3 .videoTitle span{background:#f0b35c;color:#173136}
.preview{width:1800px;background:#cfd8d2;padding:34px;display:grid;grid-template-columns:repeat(5,1fr);gap:18px}
.preview figure{margin:0;background:#faf8ec;padding:8px}
.preview img{width:100%;display:block}
.preview figcaption{padding:8px 2px 0;font-size:16px;font-weight:780;color:#303030}
`;

const html = `<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>新型城镇化小红书与视频号封面</title><style>${css}</style></head><body><main class="stage">${pages.map(renderPage).join('\n')}${videos.map(renderVideo).join('\n')}</main></body></html>`;
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
