import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { chromium } from 'playwright';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const repoRoot = path.resolve(__dirname, '../../../..');
const mediaDir = path.join(repoRoot, 'media/images/2026-06-22-modern-agriculture-xhs-video');
const assetDir = path.join(mediaDir, 'assets');
const htmlPath = path.join(__dirname, 'index.html');

const out = (file) => path.join(mediaDir, file);
const rel = (file) => path.relative(__dirname, path.join(assetDir, file)).replaceAll(path.sep, '/');

const pages = [
  {
    id: 'xhs-01-cover',
    no: '01',
    tag: '人民日报材料转申论',
    title: '现代农业\\n不是只靠苦干',
    kicker: '科技体检、田保姆和青年农机手一起上',
    image: 'field-drone.jpg',
    points: ['科技识田', '服务入田', '专家跟田', '青年到田'],
    layout: 'cover'
  },
  {
    id: 'xhs-02-mistake',
    no: '02',
    tag: '常见误区',
    title: '别再只写\\n农民辛苦',
    quote: '“辛苦”只能说明态度，“增产”只能说明结果。真正能拉开分差的，是写清农业生产方式正在怎么变。',
    points: ['只写苦干', '只写增产', '只写口号', '只写投入'],
    notes: ['要写土地如何被精准识别', '要写农户如何接上服务体系'],
    layout: 'mistake'
  },
  {
    id: 'xhs-03-core',
    no: '03',
    tag: '核心判断',
    title: '不是更辛苦\\n而是支撑更强',
    quote: '现代农业不是让农民更辛苦，而是让土地被精准识别、农活被专业服务、人才被持续培养。',
    image: 'wheat-field.jpg',
    points: ['土地被精准识别', '农活被专业服务', '人才被持续培养'],
    layout: 'quotePhoto'
  },
  {
    id: 'xhs-04-chain',
    no: '04',
    tag: '高分链条',
    title: '先把现代农业\\n写成一条链',
    quote: '现代农业高分表达 = 科技识田 + 服务入田 + 专家跟田 + 青年到田。',
    points: ['科技识田', '服务入田', '专家跟田', '青年到田'],
    layout: 'formula'
  },
  {
    id: 'xhs-05-tech',
    no: '05',
    tag: '一、科技识田',
    title: '先给土地\\n做一次科技体检',
    quote: '申论可用表达：推进农业现代化，不能只写“因地制宜”，更要写清如何用遥感监测、数据画像、处方管理和智能农机，把土地差异转化为精准管护方案。',
    image: 'soil-hands.jpg',
    points: ['遥感监测', '数据画像', '处方管理', '智能农机'],
    layout: 'objectPhoto'
  },
  {
    id: 'xhs-06-precision',
    no: '06',
    tag: '科技落点',
    title: '土地先被看见\\n管理才会精准',
    quote: '手机上的“处方图”显示土壤类型、坡度、推荐施肥用量，再发送到农机，配合变量施肥和北斗导航。',
    points: ['土壤类型', '坡度差异', '施肥用量', '北斗导航', '变量作业', '污染减量'],
    layout: 'matrix'
  },
  {
    id: 'xhs-07-service',
    no: '07',
    tag: '二、服务入田',
    title: '小农户接上现代农业\\n靠服务体系',
    quote: '申论可用表达：农业现代化不能只依靠单个农户扩大投入，而要完善农业社会化服务体系，通过农机作业、农资供应、金融支持、储运销售、防灾预警等全链条服务，促进小农户和现代农业有机衔接。',
    image: 'tractor-field.jpg',
    points: ['农机作业', '农资供应', '金融支持', '储运销售', '防灾预警'],
    layout: 'extension'
  },
  {
    id: 'xhs-08-service-chain',
    no: '08',
    tag: '服务链',
    title: '不是单户硬扛\\n而是全链托举',
    quote: '“田保姆”不是简单替农户干活，而是把技术、装备、管理和关键农时服务送到户、送到田。',
    points: ['干不了：装备资金门槛高', '干不好：灾害农时要专业判断', '不划算：单户投入成本高', '接得上：服务体系降低门槛'],
    layout: 'serviceMap'
  },
  {
    id: 'xhs-09-expert',
    no: '09',
    tag: '三、专家跟田',
    title: '技术不能停在屏幕上\\n还要跟着问题走',
    quote: '申论可用表达：农业科技不能停在实验室和屏幕上，必须围绕苗情、墒情、灾情、病虫害和农时变化，推动专家下田、农技到户、服务到点，把不确定性转化为稳产能力。',
    image: 'smart-farm.jpg',
    points: ['苗情', '墒情', '灾情', '病虫害', '农时变化'],
    layout: 'photoFeature'
  },
  {
    id: 'xhs-10-risk',
    no: '10',
    tag: '稳产能力',
    title: '数据看趋势\\n专家看现场',
    quote: '晚播、弱苗、病虫害、抢收抢烘，都不是一句“加强管理”能解决的，要把措施落实到田。',
    points: ['返青拔节期追肥', '一喷三防', '分类指导', '包市包县', '下沉一线'],
    layout: 'governance'
  },
  {
    id: 'xhs-11-youth',
    no: '11',
    tag: '四、青年到田',
    title: '装备升级以后\\n还要有人会用',
    quote: '申论可用表达：现代农业不仅要推动装备升级，更要培养懂技术、会经营、能组织的新农人队伍，让青年农机手、农技人员和社会化服务主体成为粮食稳产保供的重要力量。',
    image: 'young-farmer.jpg',
    points: ['懂技术', '会经营', '能组织', '会调度'],
    layout: 'darkQuote'
  },
  {
    id: 'xhs-12-people',
    no: '12',
    tag: '人才结构',
    title: '年轻人到田间\\n带来新组织方式',
    quote: '青年农机手不只是会开机器，还能用平台接单、用系统调度、用无人机植保、用数字化平台统筹地块和农时。',
    points: ['组织管理规范化', '作业接单网络化', '农机调配共享化', '平台服务协同化'],
    layout: 'exam'
  },
  {
    id: 'xhs-13-interview',
    no: '13',
    tag: '面试题卡',
    title: '农户担心跟不上\\n这样答',
    quote: '有地方推进农业现代化，一些农户觉得新技术成本高、不会用，也担心小农户跟不上。对此你怎么看？',
    points: ['不能把现代农业理解成单纯上设备', '科技要到田：精准识别和分类管理', '服务要到户：解决一家一户干不了', '人才要到位：技术有人推广、平台有人运营', '风险要兜住：防灾预警、抢收抢烘、金融保险'],
    layout: 'interview'
  },
  {
    id: 'xhs-14-material',
    no: '14',
    tag: '素材记忆',
    title: '材料怎么记\\n才不会散',
    quote: '黑土地体检看科技识田，“田保姆”看服务入田，“郭小麦”看专家跟田，青年农机手看人才到田。',
    image: 'farmer-tablet.jpg',
    points: ['黑土地体检', '变量施肥', '田保姆', '郭小麦', '青年农机手'],
    layout: 'material'
  },
  {
    id: 'xhs-15-closing',
    no: '15',
    tag: '收束金句',
    title: '真正的现代农业\\n是多一套支撑系统',
    quote: '科技看见土地，服务接住农户，专家解决问题，青年承接未来。',
    image: 'harvest-machine.jpg',
    points: ['科技下田', '服务入田', '人才到田'],
    layout: 'closing'
  }
];

const photoMeta = {
  'farmer-tablet.jpg': {
    pos: 'center 46%',
    map: 'aerial farm machines line up across the upper field; safe text zone is left paper panel.'
  },
  'field-drone.jpg': {
    pos: 'center 50%',
    map: 'green field rows fill the image, bright horizon at top; title can sit on dark left overlay.'
  },
  'harvest-machine.jpg': {
    pos: 'center 50%',
    map: 'wide wheat field with broad sky, no close face; safe for full bleed closing.'
  },
  'smart-farm.jpg': {
    pos: 'center 54%',
    map: 'corn seedlings and soil close-up occupy the lower frame; use as evidence image.'
  },
  'soil-hands.jpg': {
    pos: 'center 48%',
    map: 'hands and soil sit near the center; keep text in upper paper area.'
  },
  'tractor-field.jpg': {
    pos: 'center 52%',
    map: 'tractor is center-right in the field; text stays in the left paper panel.'
  },
  'wheat-field.jpg': {
    pos: 'center 50%',
    map: 'wheat close-up fills lower frame, open sky at top; safe right-side evidence image.'
  },
  'young-farmer.jpg': {
    pos: 'center 50%',
    map: 'young farmer stands on right-center; title is placed on dark left overlay.'
  }
};

const videos = [
  {
    id: 'video-cover-01',
    image: 'field-drone.jpg',
    title: '现代农业\\n不是只靠苦干',
    subtitle: '科技体检、田保姆和青年农机手一起上',
    label: 'MODERN AGRICULTURE',
    variant: 1
  },
  {
    id: 'video-cover-02',
    image: 'wheat-field.jpg',
    title: '科技识田\\n服务入田\\n青年到田',
    subtitle: '农业现代化高分表达链条',
    label: 'TECH · SERVICE · YOUTH',
    variant: 2
  },
  {
    id: 'video-cover-03',
    image: 'young-farmer.jpg',
    title: '不是农民更辛苦\\n而是系统更会托举',
    subtitle: '土地 / 服务 / 专家 / 青年',
    label: 'FIELD SUPPORT SYSTEM',
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
  const cls = len > 138 ? 'quote xxl' : len > 110 ? 'quote xl' : len > 82 ? 'quote long' : len > 54 ? 'quote med' : 'quote';
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
  if (page.layout === 'matrix') {
    return `<section class="poster xhs matrixPage" id="${page.id}">
      <div class="paper"></div><div class="content">${top(page)}<h1>${titleHtml(page.title)}</h1>${quoteHtml(page)}
      <div class="matrix">${page.points.map((x) => `<span>${escapeHtml(x)}</span>`).join('')}</div></div>
    </section>`;
  }
  if (page.layout === 'extension') {
    return `<section class="poster xhs extension" id="${page.id}">
      <div class="paper"></div>${photo(page.image, 'rightPhoto')}
      <div class="content">${top(page)}<h1>${titleHtml(page.title)}</h1>${quoteHtml(page)}
      <div class="extensionRows">${page.points.map((x) => `<span>${escapeHtml(x)}</span>`).join('')}</div></div>
    </section>`;
  }
  if (page.layout === 'serviceMap') {
    return `<section class="poster xhs serviceMap" id="${page.id}">
      <div class="paper"></div><div class="content">${top(page)}<h1>${titleHtml(page.title)}</h1>${quoteHtml(page)}
      <div class="serviceBoxes">${page.points.map((x, i) => `<span><b>${String(i + 1).padStart(2, '0')}</b>${escapeHtml(x)}</span>`).join('')}</div></div>
    </section>`;
  }
  if (page.layout === 'photoFeature') {
    return `<section class="poster xhs photoFeature" id="${page.id}">
      <div class="paper"></div>${photo(page.image, 'bottomWide')}
      <div class="content">${top(page)}<h1>${titleHtml(page.title)}</h1>${quoteHtml(page)}
      <div class="serviceStrip">${page.points.map((x) => `<span>${escapeHtml(x)}</span>`).join('')}</div></div>
    </section>`;
  }
  if (page.layout === 'governance') {
    return `<section class="poster xhs governance" id="${page.id}">
      <div class="paper"></div><div class="content">${top(page)}<h1>${titleHtml(page.title)}</h1>${quoteHtml(page)}
      <div class="governGrid">${page.points.map((x) => `<span>${escapeHtml(x)}</span>`).join('')}</div></div>
    </section>`;
  }
  if (page.layout === 'darkQuote') {
    return `<section class="poster xhs darkQuote" id="${page.id}">
      ${photo(page.image, 'bleed')}<div class="darkTint"></div><div class="grain"></div>
      <div class="content">${top(page)}<h1>${titleHtml(page.title)}</h1>${quoteHtml(page)}
      <div class="darkNodes">${page.points.map((x) => `<span>${escapeHtml(x)}</span>`).join('')}</div></div>
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
body{background:#d6dac6;font-family:"Avenir Next","Helvetica Neue","PingFang SC","Noto Sans SC","Microsoft YaHei",Arial,sans-serif;color:#17281f}
.stage{width:max-content;display:grid;gap:34px;padding:34px}
.poster{position:relative;overflow:hidden;isolation:isolate;background:#f5f0df}
.xhs,.video{width:1080px;height:1440px}
.video{line-height:0}
.poster figure{margin:0}
.paper{position:absolute;inset:0;z-index:0;background:
  radial-gradient(circle at 84% 16%,rgba(77,123,56,.17),transparent 30%),
  radial-gradient(circle at 12% 90%,rgba(216,166,58,.22),transparent 34%),
  linear-gradient(116deg,rgba(23,40,31,.055) 0 1px,transparent 1px 18px),
  linear-gradient(180deg,#f7f1de 0%,#edf0d7 56%,#dfe7ca 100%)}
.paper:after{content:"";position:absolute;inset:0;background:repeating-linear-gradient(0deg,rgba(255,255,255,.12) 0 1px,transparent 1px 6px);opacity:.70}
.grain{position:absolute;inset:0;z-index:3;opacity:.22;background:repeating-linear-gradient(105deg,rgba(255,255,255,.12) 0 1px,transparent 1px 5px),linear-gradient(180deg,rgba(255,255,255,.15),rgba(0,0,0,.12));mix-blend-mode:soft-light;pointer-events:none}
.content{position:relative;z-index:5;height:100%;padding:58px;display:flex;flex-direction:column}
.top{display:flex;align-items:center;justify-content:space-between;gap:24px;border-bottom:2px solid rgba(23,40,31,.22);padding-bottom:20px;font-size:24px;line-height:1;font-weight:840}
.top span:first-child{font-size:38px;color:#4d7b38;font-weight:900}
.cover .top,.darkQuote .top,.closing .top{border-bottom-color:rgba(255,255,255,.46);color:#f5f0df}
.cover .top span:first-child,.darkQuote .top span:first-child,.closing .top span:first-child{color:#d8a63a}
.xhs h1{margin:28px 0 0;font-family:"Songti SC","STSong","Noto Serif CJK SC",serif;font-size:76px;line-height:1.05;font-weight:760;letter-spacing:0}
.quote{margin:28px 0 0;padding:24px 28px;background:rgba(255,249,235,.94);border-left:10px solid #4d7b38;font-size:34px;line-height:1.35;font-weight:820}
.quote.med{font-size:30px;line-height:1.39}
.quote.long{font-size:25px;line-height:1.43}
.quote.xl{font-size:21px;line-height:1.46}
.quote.xxl{font-size:18px;line-height:1.44}
.photo{margin:0;overflow:hidden}
.photo img,.videoPhoto img{width:100%;height:100%;object-fit:cover;filter:saturate(.94) contrast(1.06) brightness(.94)}
.bleed{position:absolute;inset:0;z-index:1}
.coverTint{position:absolute;inset:0;z-index:2;background:linear-gradient(90deg,rgba(19,34,25,.94),rgba(19,34,25,.18) 66%,rgba(19,34,25,.46)),linear-gradient(180deg,rgba(19,34,25,.12),rgba(19,34,25,.38) 62%,rgba(19,34,25,.90))}
.series{margin:36px 0 0;color:#d8a63a;font-size:36px;line-height:1;font-weight:900}
.cover h1{margin-top:28px;color:#f7f1de;font-size:88px;max-width:940px}
.coverLine{margin-top:30px;width:900px;padding:20px 24px;background:rgba(255,249,235,.92);color:#17281f;font-size:30px;font-weight:880}
.coverNodes{margin-top:auto;display:grid;grid-template-columns:1fr 28px 1fr 28px 1fr 28px 1fr;align-items:center}
.coverNodes span{height:132px;display:grid;place-items:center;text-align:center;background:#f7f1de;color:#17281f;border-top:12px solid #4d7b38;font-size:28px;font-weight:900}
.coverNodes span:nth-of-type(2){border-top-color:#d8a63a}.coverNodes span:nth-of-type(3){border-top-color:#8a5a2b}.coverNodes span:nth-of-type(4){border-top-color:#17281f}
.coverNodes i{height:4px;background:#f7f1de}
.wrongList{margin-top:38px;display:grid;grid-template-columns:repeat(2,1fr);gap:14px}
.wrongList span{height:168px;padding:22px;display:grid;align-content:space-between;background:#fff9eb;border:2px solid rgba(23,40,31,.18);font-size:31px;font-weight:820}
.wrongList b{font-size:23px;color:#4d7b38}
.aside{margin-top:auto;display:grid;grid-template-columns:1fr 1fr;gap:14px}
.aside p{min-height:128px;margin:0;padding:22px;background:#17281f;color:#f7f1de;font-size:28px;line-height:1.22;font-weight:850}
.sidePhoto{position:absolute;right:0;top:0;bottom:0;width:460px;z-index:1}
.quotePhoto:after{content:"";position:absolute;right:0;top:0;bottom:0;width:690px;z-index:2;background:linear-gradient(90deg,#f5f0df 0%,rgba(245,240,223,.92) 50%,rgba(245,240,223,.08) 100%)}
.quotePhoto .content{padding-right:418px}
.quotePhoto .quote{font-size:24px;line-height:1.46}
.keywordRail{margin-top:auto;display:grid;grid-template-columns:repeat(3,1fr);gap:10px}
.keywordRail span{height:124px;display:grid;place-items:center;text-align:center;background:#17281f;color:#f7f1de;border-top:12px solid #4d7b38;font-size:22px;font-weight:900}
.keywordRail span:nth-child(2){border-top-color:#d8a63a}.keywordRail span:nth-child(3){border-top-color:#8a5a2b}
.formula .quote,.exam .quote{font-size:31px}
.formulaRail,.examFlow{margin-top:auto;display:grid;grid-template-columns:1fr 24px 1fr 24px 1fr 24px 1fr;align-items:center}
.formulaRail span,.examFlow span{height:300px;padding:20px 14px;display:grid;align-content:space-between;text-align:center;background:#17281f;color:#f7f1de;font-size:27px;line-height:1.14;font-weight:900}
.examFlow span{height:260px;font-size:22px}
.formulaRail span:nth-of-type(2),.examFlow span:nth-of-type(2){background:#d8a63a;color:#17281f}.formulaRail span:nth-of-type(3),.examFlow span:nth-of-type(3){background:#4d7b38}.formulaRail span:nth-of-type(4),.examFlow span:nth-of-type(4){background:#8a5a2b}
.formulaRail b,.examFlow b{color:#f6d58a;font-size:22px}.formulaRail span:nth-of-type(2) b,.examFlow span:nth-of-type(2) b{color:#17281f}
.formulaRail i,.examFlow i{height:4px;background:#17281f}
#xhs-04-chain:after{content:"土地  →  农户  →  风险  →  未来";position:absolute;left:58px;right:58px;top:596px;height:128px;z-index:1;display:grid;place-items:center;background:rgba(216,166,58,.18);border-top:3px solid rgba(77,123,56,.45);border-bottom:3px solid rgba(138,90,43,.38);color:#17281f;font-size:34px;font-weight:900}
.bottomWide{position:absolute;left:58px;right:58px;bottom:58px;height:410px;z-index:1;border:3px solid rgba(77,123,56,.32)}
.objectPhoto .content,.photoFeature .content,.material .content{padding-bottom:540px}
.objectPhoto .quote{font-size:19px;line-height:1.44}
.cards{margin-top:30px;display:grid;grid-template-columns:repeat(4,1fr);gap:10px}
.cards span{height:100px;padding:14px 10px;display:grid;align-content:space-between;background:#fff9eb;border-top:12px solid #4d7b38;font-size:20px;line-height:1.14;font-weight:860}
.cards span:nth-child(2),.cards span:nth-child(4){border-top-color:#d8a63a}.cards span:nth-child(3){border-top-color:#8a5a2b}
.cards b{font-size:18px;color:#17281f}
.matrix{margin-top:34px;display:grid;grid-template-columns:repeat(3,1fr);gap:14px}
.matrix span{height:178px;padding:18px;display:grid;place-items:center;text-align:center;background:#fff9eb;border-top:14px solid #4d7b38;font-size:28px;line-height:1.16;font-weight:900}
.matrix span:nth-child(2),.matrix span:nth-child(5){border-top-color:#d8a63a}.matrix span:nth-child(3),.matrix span:nth-child(6){border-top-color:#8a5a2b}
.matrixPage:after{content:"看数据 / 按处方 / 精准管护";position:absolute;left:58px;right:58px;bottom:86px;height:150px;z-index:1;display:grid;place-items:center;background:#17281f;color:#f7f1de;border-top:14px solid #d8a63a;font-size:34px;font-weight:900}
.rightPhoto{position:absolute;right:58px;bottom:58px;width:410px;height:585px;z-index:1;border:3px solid rgba(77,123,56,.32)}
.extension .content{padding-right:500px}
.extension .quote{font-size:17px;line-height:1.43}
.extensionRows{margin-top:auto;display:grid;gap:12px}
.extensionRows span{height:78px;display:grid;place-items:center;text-align:center;background:#17281f;color:#f7f1de;border-left:12px solid #4d7b38;font-size:22px;font-weight:900}
.extensionRows span:nth-child(2),.extensionRows span:nth-child(4){border-left-color:#d8a63a}.extensionRows span:nth-child(3),.extensionRows span:nth-child(5){border-left-color:#8a5a2b}
#xhs-07-service:after{content:"小农户不是独自追赶，而是被服务体系接上来";position:absolute;left:58px;top:620px;width:474px;height:118px;z-index:1;display:grid;place-items:center;text-align:center;background:#fff9eb;border-left:14px solid #d8a63a;color:#17281f;font-size:27px;line-height:1.18;font-weight:900}
.serviceBoxes{margin-top:34px;display:grid;grid-template-columns:repeat(2,1fr);gap:14px}
.serviceBoxes span{height:178px;padding:18px;display:grid;align-content:space-between;background:#fff9eb;border-left:14px solid #4d7b38;font-size:26px;line-height:1.16;font-weight:880}
.serviceBoxes span:nth-child(2),.serviceBoxes span:nth-child(4){border-left-color:#d8a63a}
.serviceBoxes b{font-size:20px;color:#8a5a2b}
.serviceMap:after{content:"农机作业 / 农资供应 / 金融支持 / 储运销售 / 防灾预警";position:absolute;left:58px;right:58px;bottom:86px;height:150px;z-index:1;display:grid;place-items:center;text-align:center;background:#17281f;color:#f7f1de;border-top:14px solid #4d7b38;font-size:29px;font-weight:900}
.serviceStrip{margin-top:34px;display:grid;grid-template-columns:repeat(5,1fr);gap:10px}
.serviceStrip span{height:124px;padding:10px;display:grid;place-items:center;text-align:center;background:#17281f;color:#f7f1de;border-top:12px solid #4d7b38;font-size:23px;font-weight:900}
.serviceStrip span:nth-child(2),.serviceStrip span:nth-child(4){border-top-color:#d8a63a}.serviceStrip span:nth-child(3),.serviceStrip span:nth-child(5){border-top-color:#8a5a2b}
.photoFeature .quote{font-size:18px;line-height:1.43}
.governance .quote{font-size:27px;line-height:1.39}
.governGrid{margin-top:36px;display:grid;grid-template-columns:repeat(5,1fr);gap:10px}
.governGrid span{height:170px;padding:14px 10px;display:grid;place-items:center;text-align:center;background:#fff9eb;border-top:14px solid #4d7b38;font-size:22px;line-height:1.16;font-weight:900}
.governGrid span:nth-child(2),.governGrid span:nth-child(4){border-top-color:#d8a63a}.governGrid span:nth-child(3),.governGrid span:nth-child(5){border-top-color:#8a5a2b}
.governance:after{content:"把不确定性转化为稳产能力";position:absolute;left:58px;right:58px;bottom:88px;height:154px;z-index:1;display:grid;place-items:center;background:#17281f;color:#f7f1de;border-top:14px solid #d8a63a;font-size:34px;font-weight:900}
.darkTint{position:absolute;inset:0;z-index:2;background:linear-gradient(90deg,rgba(19,34,25,.94),rgba(19,34,25,.22) 66%,rgba(19,34,25,.52)),linear-gradient(180deg,rgba(19,34,25,.16),rgba(19,34,25,.82))}
.darkQuote h1{color:#f7f1de;font-size:76px}
.darkQuote .quote{font-size:18px;line-height:1.43}
.darkNodes{margin-top:auto;display:grid;grid-template-columns:repeat(4,1fr);gap:12px}
.darkNodes span{height:146px;display:grid;place-items:center;text-align:center;background:#f7f1de;color:#17281f;border-top:12px solid #4d7b38;font-size:26px;font-weight:900}
.darkNodes span:nth-child(2),.darkNodes span:nth-child(4){border-top-color:#d8a63a}.darkNodes span:nth-child(3){border-top-color:#8a5a2b}
.interview .quote{font-size:27px;line-height:1.4}
.answerSteps{margin-top:30px;display:grid;gap:12px}
.answerSteps span{height:98px;padding:0 18px;display:flex;align-items:center;gap:16px;background:#fff9eb;border-left:12px solid #4d7b38;font-size:22px;line-height:1.13;font-weight:850}
.answerSteps span:nth-child(2),.answerSteps span:nth-child(4){border-left-color:#d8a63a}.answerSteps span:nth-child(3),.answerSteps span:nth-child(5){border-left-color:#8a5a2b}
.answerSteps b{font-size:20px;color:#17281f}
#xhs-13-interview:after{content:"设备是工具，配套体系才是现代农业能力";position:absolute;left:58px;right:58px;bottom:80px;height:130px;z-index:1;display:grid;place-items:center;text-align:center;background:#17281f;color:#f7f1de;border-top:14px solid #d8a63a;font-size:30px;line-height:1.18;font-weight:900}
.material .quote{font-size:26px;line-height:1.4}
.materialGrid{margin-top:30px;display:grid;grid-template-columns:repeat(5,1fr);gap:10px}
.materialGrid span{height:105px;padding:10px;display:grid;place-items:center;text-align:center;background:#fff9eb;border-top:12px solid #4d7b38;font-size:20px;line-height:1.14;font-weight:880}
.materialGrid span:nth-child(2),.materialGrid span:nth-child(4){border-top-color:#d8a63a}.materialGrid span:nth-child(3),.materialGrid span:nth-child(5){border-top-color:#8a5a2b}
.closingTint{position:absolute;inset:0;z-index:2;background:linear-gradient(90deg,rgba(19,34,25,.94),rgba(19,34,25,.20) 67%,rgba(19,34,25,.50)),linear-gradient(180deg,rgba(19,34,25,.14),rgba(19,34,25,.84))}
.closing h1{color:#f7f1de;font-size:72px}
.closing .quote{font-size:32px;line-height:1.35}
.closingNodes{margin-top:auto;display:grid;grid-template-columns:repeat(3,1fr);gap:12px}
.closingNodes span{height:140px;display:grid;place-items:center;text-align:center;background:#f7f1de;color:#17281f;border-top:12px solid #4d7b38;font-size:24px;font-weight:900}
.closingNodes span:nth-child(2){border-top-color:#d8a63a}.closingNodes span:nth-child(3){border-top-color:#8a5a2b}
.videoPhoto{position:absolute;inset:0;margin:0;z-index:1}
.videoPhoto img{filter:saturate(.92) contrast(1.10) brightness(.70)}
.videoTint{position:absolute;inset:0;z-index:2;background:linear-gradient(90deg,rgba(19,34,25,.92),rgba(19,34,25,.12) 70%),linear-gradient(180deg,rgba(19,34,25,.10),rgba(19,34,25,.32) 44%,rgba(19,34,25,.88))}
.magLines{position:absolute;inset:56px;z-index:3;border-top:2px solid rgba(255,255,255,.60);border-bottom:2px solid rgba(255,255,255,.42)}
.magLines:before{content:"";position:absolute;left:0;top:94px;width:210px;height:2px;background:rgba(255,255,255,.58)}
.magLines:after{content:attr(data-label);position:absolute;right:0;top:24px;color:rgba(255,255,255,.72);font-size:20px;font-weight:820;letter-spacing:0}
.videoTitle{position:absolute;left:64px;right:76px;bottom:112px;z-index:4;color:#f7f1de;line-height:1.2}
.videoTitle p{margin:0 0 28px;color:#d8a63a;font-size:34px;line-height:1;font-weight:900}
.videoTitle h2{margin:0;font-family:"Songti SC","STSong","Noto Serif CJK SC",serif;font-size:78px;line-height:1.04;font-weight:780;letter-spacing:0;max-width:920px}
.v2 .videoTitle h2{font-size:72px}.v3 .videoTitle h2{font-size:68px}
.videoTitle span{display:block;width:max-content;max-width:890px;margin-top:26px;padding:14px 18px;background:#4d7b38;color:#f7f1de;font-size:26px;font-weight:900}
.v2 .videoTitle span{background:#d8a63a;color:#17281f}.v3 .videoTitle span{background:#8a5a2b;color:#f7f1de}
.preview{width:1800px;background:#d6dac6;padding:34px;display:grid;grid-template-columns:repeat(5,1fr);gap:18px}
.preview figure{margin:0;background:#fff9eb;padding:8px}
.preview img{width:100%;display:block}
.preview figcaption{padding:8px 2px 0;font-size:16px;font-weight:780;color:#303030}
`;

const html = `<!doctype html><html lang="zh-CN" data-theme="editorial"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>现代农业小红书与视频号封面</title><style>${css}</style></head><body><main class="stage">${pages.map(renderPage).join('\n')}${videos.map(renderVideo).join('\n')}</main></body></html>`;
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
