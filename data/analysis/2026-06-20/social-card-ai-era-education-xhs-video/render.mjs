import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { chromium } from 'playwright';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const repoRoot = path.resolve(__dirname, '../../../..');
const mediaDir = path.join(repoRoot, 'media/images/2026-06-20-ai-era-education-xhs-video');
const assetDir = path.join(mediaDir, 'assets');
const htmlPath = path.join(__dirname, 'index.html');

const out = (file) => path.join(mediaDir, file);
const rel = (file) => path.relative(__dirname, path.join(assetDir, file)).replaceAll(path.sep, '/');

const pages = [
  {
    id: 'xhs-01-cover',
    no: '01',
    tag: '人民日报材料转申论',
    title: 'AI时代教育怎么写\\n不是人人学工具',
    kicker: '重塑思维 / 终身学习 / 协同育人',
    image: 'data-center.jpg',
    points: ['会提问', '会判断', '会协作', '终身学习'],
    layout: 'cover'
  },
  {
    id: 'xhs-02-mistake',
    no: '02',
    tag: '常见误区',
    title: '别把AI教育\\n写成工具培训',
    quote: '写“开设AI课、推广AI工具、建设智慧课堂”，只能说明技术进校园，不能说明教育怎么变。',
    points: ['工具会用', '流程会点', '平台会登', '答案会抄'],
    notes: ['这些能写，但不是主线', '高分要写出：思维、判断、迁移和终身学习'],
    layout: 'mistake'
  },
  {
    id: 'xhs-03-core-judgement',
    no: '03',
    tag: '核心判断',
    title: '先把立意\\n抬高一层',
    quote: 'AI时代教育的重点，不是人人学工具，而是让人更会提问、更会判断、更会协作、更能持续学习。',
    image: 'students-laptop.jpg',
    points: ['不是工具操作', '而是育人目标', '不是一次培训', '而是能力更新'],
    layout: 'quotePhoto'
  },
  {
    id: 'xhs-04-core-formula',
    no: '04',
    tag: '核心公式',
    title: '考场直接\\n抓这条链',
    quote: '工具会用 → 问题会提 → 信息会辨 → 能力会迁移 → 终身会学习。',
    points: ['工具会用', '问题会提', '信息会辨', '能力会迁移', '终身会学习'],
    layout: 'formula'
  },
  {
    id: 'xhs-05-student-side',
    no: '05',
    tag: '学生端',
    title: 'AI能给答案\\n教育更要培养问题',
    quote: '真正重要的，是让AI成为思维的脚手架，而不是替代思考的拐杖。',
    image: 'robotics-class.jpg',
    points: ['提出问题', '拆解问题', '验证答案', '表达观点'],
    layout: 'photoFeature'
  },
  {
    id: 'xhs-06-thinking-traps',
    no: '06',
    tag: '思维训练',
    title: '要防住\\n三个新陷阱',
    quote: 'AI会让答案更快出现，也会让懒思考更容易发生。',
    points: ['流畅性陷阱', '认知外包', '标准答案惯性', '复杂问题能力下降'],
    notes: ['能问、能辨、能改，才是AI时代的学习力'],
    layout: 'trapGrid'
  },
  {
    id: 'xhs-07-digital-reading',
    no: '07',
    tag: '阅读端',
    title: '刷到信息\\n不等于读懂世界',
    quote: '会问AI，等于会学习吗？会刷信息，等于会阅读吗？会复制答案，等于会理解吗？',
    image: 'digital-reading.jpg',
    points: ['会检索', '会筛选', '会吸收', '会创造'],
    layout: 'questionPhoto'
  },
  {
    id: 'xhs-08-judgement',
    no: '08',
    tag: '判断力',
    title: '数字阅读能力\\n就是判断力',
    quote: '数字阅读能力，本质上是AI时代的判断力。',
    points: ['面对海量信息有价值定力', '面对算法推荐有辨别力', '面对碎片内容有创造力', '面对未知技术有敬畏力'],
    layout: 'skillMatrix'
  },
  {
    id: 'xhs-09-lifelong-learning',
    no: '09',
    tag: '成人端',
    title: '教育不能\\n停在毕业那天',
    quote: 'AI时代的教育，不再只是一次性学历供给，而是贯穿全生命周期的能力更新服务。',
    image: 'adult-learning.jpg',
    points: ['在校学习', '岗位学习', '转岗学习', '终身学习'],
    layout: 'lifePhoto'
  },
  {
    id: 'xhs-10-system-support',
    no: '10',
    tag: '体系支撑',
    title: '终身学习\\n要有制度入口',
    quote: '写成人教育，不能只写“鼓励学习”，要写出制度、平台和场景。',
    points: ['国家资历框架', '学分银行', '高校开放课程', '智慧学习平台', '基层学习中心'],
    layout: 'supportMap'
  },
  {
    id: 'xhs-11-social-side',
    no: '11',
    tag: '社会端',
    title: '岗位变了\\n学习体系也要变',
    quote: 'AI时代教育的社会意义，是让学习体系跟上岗位变化，让劳动者不被技术甩下。',
    image: 'vocational-training.jpg',
    points: ['产业升级', '岗位重塑', '技能更新', '就业韧性'],
    layout: 'socialPhoto'
  },
  {
    id: 'xhs-12-exam-formula',
    no: '12',
    tag: '考场框架',
    title: '答题就按\\n这五步展开',
    quote: '工具会用 → 问题会提 → 信息会辨 → 能力会迁移 → 终身会学习。',
    points: ['工具是入口，不是终点', '问题意识是学习起点', '信息辨别决定判断质量', '能力迁移适应岗位变化', '终身学习托住人的发展'],
    layout: 'examFlow'
  },
  {
    id: 'xhs-13-argument',
    no: '13',
    tag: '申论总论点',
    title: '一句话\\n写出深度',
    quote: 'AI时代教育的关键，不是简单普及工具操作，而是推动育人目标从知识传授转向能力提升，从阶段性学习转向终身学习，从单一课堂转向学校、社会、产业协同育人。',
    points: ['知识传授', '能力提升', '终身学习', '协同育人'],
    layout: 'argument'
  },
  {
    id: 'xhs-14-interview',
    no: '14',
    tag: '面试题卡',
    title: '现象认知题\\n这样答',
    quote: '有人认为，AI时代教育的重点就是让学生尽快学会使用各种AI工具。对此你怎么看？',
    points: ['肯定工具学习的必要性', '指出只会工具会造成浅层学习', '强调问题意识、判断力和创造力', '落到学校、社会、产业协同培养'],
    layout: 'interview'
  },
  {
    id: 'xhs-15-closing',
    no: '15',
    tag: '收束金句',
    title: '不是让人\\n追着机器跑',
    quote: 'AI时代教育的价值，是用技术释放人、发展人、成就人。',
    image: 'online-learning.jpg',
    points: ['释放人', '发展人', '成就人'],
    layout: 'closing'
  }
];

const photoMeta = {
  'adult-learning.jpg': {
    pos: 'center 50%',
    map: 'writing hand and laptop stay in the left and center; use top text blocks and keep lower-right photo visible.'
  },
  'data-center.jpg': {
    pos: 'center 52%',
    map: 'earth horizon and lights are low and wide; title can sit on the left without covering a face or object.'
  },
  'digital-reading.jpg': {
    pos: 'center 52%',
    map: 'tablet reader occupies center-left; keep headline in the upper-left dark field and preserve the screen.'
  },
  'online-learning.jpg': {
    pos: 'center 48%',
    map: 'laptops and notes occupy the right and lower center; closing title should sit in the left safe zone.'
  },
  'robotics-class.jpg': {
    pos: 'center 50%',
    map: 'robotics materials spread across the table, with clean top-down composition; text can overlay separated panels.'
  },
  'students-laptop.jpg': {
    pos: 'center 54%',
    map: 'students sit around center-right; keep large title on left and avoid covering faces.'
  },
  'vocational-training.jpg': {
    pos: 'center 53%',
    map: 'workers and sparks occupy lower and right areas; video title uses lower-left dark zone.'
  }
};

const videos = [
  {
    id: 'video-cover-01',
    image: 'data-center.jpg',
    title: 'AI时代教育\\n不是人人学工具',
    subtitle: '重塑思维 / 终身学习 / 协同育人',
    variant: 1
  },
  {
    id: 'video-cover-02',
    image: 'students-laptop.jpg',
    title: '让AI成为\\n思维脚手架',
    subtitle: '不是替代思考的拐杖',
    variant: 2
  },
  {
    id: 'video-cover-03',
    image: 'vocational-training.jpg',
    title: 'AI时代教育\\n写成能力更新体系',
    subtitle: '工具会用 → 问题会提 → 终身会学习',
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
  const cls = len > 105 ? 'quote xl' : len > 78 ? 'quote long' : len > 48 ? 'quote med' : 'quote';
  return `<blockquote class="${cls}">${escapeHtml(page.quote)}</blockquote>`;
}

function numberCards(items = []) {
  return `<div class="numberCards">${items.map((x, i) => `<span><b>${String(i + 1).padStart(2, '0')}</b>${escapeHtml(x)}</span>`).join('')}</div>`;
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
      <div class="miniCompare">${page.points.map((x) => `<span>${escapeHtml(x)}</span>`).join('')}</div></div>
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
      <div class="content">${top(page)}<h1>${titleHtml(page.title)}</h1>${quoteHtml(page)}${numberCards(page.points)}</div>
    </section>`;
  }
  if (page.layout === 'trapGrid') {
    return `<section class="poster xhs trapGrid" id="${page.id}">
      <div class="paper"></div><div class="content">${top(page)}<h1>${titleHtml(page.title)}</h1>${quoteHtml(page)}
      <div class="trapCards">${page.points.map((x, i) => `<span><b>${String(i + 1).padStart(2, '0')}</b>${escapeHtml(x)}</span>`).join('')}</div>
      <p class="note">${escapeHtml(page.notes[0])}</p></div>
    </section>`;
  }
  if (page.layout === 'questionPhoto') {
    return `<section class="poster xhs questionPhoto" id="${page.id}">
      <div class="paper"></div>${photo(page.image, 'rightPhoto')}
      <div class="content">${top(page)}<h1>${titleHtml(page.title)}</h1>${quoteHtml(page)}
      <div class="questionSteps">${page.points.map((x) => `<span>${escapeHtml(x)}</span>`).join('')}</div></div>
    </section>`;
  }
  if (page.layout === 'skillMatrix') {
    return `<section class="poster xhs skillMatrix" id="${page.id}">
      <div class="paper"></div><div class="content">${top(page)}<h1>${titleHtml(page.title)}</h1>${quoteHtml(page)}
      <div class="matrix">${page.points.map((x, i) => `<span><b>${['价值定力', '辨别力', '创造力', '敬畏力'][i]}</b>${escapeHtml(x)}</span>`).join('')}</div></div>
    </section>`;
  }
  if (page.layout === 'lifePhoto') {
    return `<section class="poster xhs lifePhoto" id="${page.id}">
      <div class="paper"></div>${photo(page.image, 'bottomWide')}
      <div class="content">${top(page)}<h1>${titleHtml(page.title)}</h1>${quoteHtml(page)}
      <div class="lifeLine">${page.points.map((x) => `<span>${escapeHtml(x)}</span>`).join('<i></i>')}</div></div>
    </section>`;
  }
  if (page.layout === 'supportMap') {
    return `<section class="poster xhs supportMap" id="${page.id}">
      <div class="paper"></div><div class="content">${top(page)}<h1>${titleHtml(page.title)}</h1>${quoteHtml(page)}
      <div class="supportNodes">${page.points.map((x) => `<span>${escapeHtml(x)}</span>`).join('')}</div></div>
    </section>`;
  }
  if (page.layout === 'socialPhoto') {
    return `<section class="poster xhs socialPhoto" id="${page.id}">
      <div class="paper"></div>${photo(page.image, 'bottomWide')}
      <div class="content">${top(page)}<h1>${titleHtml(page.title)}</h1>${quoteHtml(page)}
      <div class="socialChain">${page.points.map((x) => `<span>${escapeHtml(x)}</span>`).join('<i></i>')}</div></div>
    </section>`;
  }
  if (page.layout === 'examFlow') {
    return `<section class="poster xhs examFlow" id="${page.id}">
      <div class="paper"></div><div class="content">${top(page)}<h1>${titleHtml(page.title)}</h1>${quoteHtml(page)}
      <div class="examRows">${page.points.map((x, i) => `<span><b>${String(i + 1).padStart(2, '0')}</b>${escapeHtml(x)}</span>`).join('')}</div></div>
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
      <!-- Subject map: ${meta.map} Magazine title uses safe lower-left or upper-left editorial zone. -->
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
body{background:#d6d9d3;font-family:"Avenir Next","Helvetica Neue","PingFang SC","Noto Sans SC","Microsoft YaHei",Arial,sans-serif;color:#101421}
.stage{width:max-content;display:grid;gap:34px;padding:34px}
.poster{position:relative;overflow:hidden;isolation:isolate;background:#f4f0e8}
.xhs,.video{width:1080px;height:1440px}
.paper{position:absolute;inset:0;z-index:0;background:
  radial-gradient(circle at 86% 12%,rgba(0,180,216,.23),transparent 30%),
  radial-gradient(circle at 9% 91%,rgba(217,70,143,.18),transparent 34%),
  radial-gradient(circle at 75% 78%,rgba(245,184,75,.22),transparent 30%),
  linear-gradient(90deg,rgba(16,20,33,.052) 1px,transparent 1px),
  linear-gradient(180deg,rgba(16,20,33,.048) 1px,transparent 1px),
  linear-gradient(180deg,#fbf7ec,#e6eef0);background-size:auto,auto,auto,72px 72px,72px 72px,auto}
.grain{position:absolute;inset:0;z-index:3;opacity:.24;background:repeating-linear-gradient(105deg,rgba(255,255,255,.10) 0 1px,transparent 1px 5px),radial-gradient(circle at 24% 18%,rgba(255,255,255,.30),transparent 28%);mix-blend-mode:soft-light;pointer-events:none}
.content{position:relative;z-index:5;height:100%;padding:58px;display:flex;flex-direction:column}
.top{display:flex;align-items:center;justify-content:space-between;gap:24px;border-bottom:2px solid rgba(16,20,33,.22);padding-bottom:20px;font-size:24px;line-height:1;font-weight:840}
.top span:first-child{font-size:38px;color:#00a6c8;font-weight:900}
.cover .top,.closing .top{border-bottom-color:rgba(255,255,255,.48);color:#fffdf6}
.cover .top span:first-child,.closing .top span:first-child{color:#f5b84b}
.xhs h1{margin:28px 0 0;font-family:"Songti SC","STSong","Noto Serif CJK SC",serif;font-size:82px;line-height:1.04;font-weight:760;letter-spacing:0}
.quote{margin:28px 0 0;padding:24px 28px;background:rgba(255,253,245,.94);border-left:10px solid #00a6c8;font-size:35px;line-height:1.34;font-weight:820}
.quote.med{font-size:30px;line-height:1.39}
.quote.long{font-size:25px;line-height:1.43}
.quote.xl{font-size:22px;line-height:1.46}
.photo{margin:0;overflow:hidden}
.photo img,.videoPhoto img{width:100%;height:100%;object-fit:cover;filter:saturate(.86) contrast(1.06) brightness(.92)}
.bleed{position:absolute;inset:0;z-index:1}
.coverTint{position:absolute;inset:0;z-index:2;background:linear-gradient(90deg,rgba(8,12,24,.90),rgba(8,12,24,.14) 67%,rgba(8,12,24,.42)),linear-gradient(180deg,rgba(8,12,24,.12),rgba(8,12,24,.44) 70%,rgba(8,12,24,.88))}
.series{margin:36px 0 0;color:#f5b84b;font-size:35px;line-height:1;font-weight:900}
.cover h1{margin-top:28px;color:#fffdf6;font-size:88px;max-width:925px}
.coverLine{margin-top:30px;width:900px;padding:20px 24px;background:rgba(255,253,245,.92);color:#101421;font-size:30px;font-weight:860}
.coverNodes{margin-top:auto;display:grid;grid-template-columns:1fr 28px 1fr 28px 1fr 28px 1fr;align-items:center}
.coverNodes span{height:132px;display:grid;place-items:center;text-align:center;background:#f4f0e8;color:#101421;border-top:12px solid #00a6c8;font-size:28px;font-weight:900}
.coverNodes span:nth-of-type(2){border-top-color:#d9468f}.coverNodes span:nth-of-type(3){border-top-color:#f5b84b}.coverNodes span:nth-of-type(4){border-top-color:#101421}
.coverNodes i{height:4px;background:#f4f0e8}
.wrongList{margin-top:38px;display:grid;grid-template-columns:repeat(2,1fr);gap:14px}
.wrongList span{height:168px;padding:22px;display:grid;align-content:space-between;background:#fffdf5;border:2px solid rgba(16,20,33,.18);font-size:31px;font-weight:820}
.wrongList b{font-size:23px;color:#d9468f}
.aside{margin-top:auto;display:grid;grid-template-columns:1fr 1fr;gap:14px}
.aside p{min-height:128px;margin:0;padding:22px;background:#101421;color:#fffdf6;font-size:28px;line-height:1.22;font-weight:850}
.sidePhoto{position:absolute;right:0;top:0;bottom:0;width:455px;z-index:1}
.quotePhoto:after{content:"";position:absolute;right:0;top:0;bottom:0;width:640px;z-index:2;background:linear-gradient(90deg,#fbf7ec 0%,rgba(251,247,236,.88) 47%,rgba(251,247,236,.10) 100%)}
.quotePhoto .content{padding-right:420px}
.quotePhoto .quote{font-size:28px;line-height:1.42}
.miniCompare{margin-top:auto;display:grid;grid-template-columns:1fr 1fr;gap:12px}
.miniCompare span{height:108px;padding:15px;display:grid;place-items:center;text-align:center;background:#101421;color:#fffdf6;border-top:12px solid #00a6c8;font-size:24px;font-weight:880}
.miniCompare span:nth-child(2),.miniCompare span:nth-child(4){border-top-color:#d9468f}
.formula .quote{font-size:32px}
.formulaRail{margin-top:auto;display:grid;grid-template-columns:1fr 24px 1fr 24px 1fr 24px 1fr 24px 1fr;align-items:center}
.formulaRail span{height:310px;padding:20px 10px;display:grid;align-content:space-between;text-align:center;background:#101421;color:#fffdf6;font-size:25px;line-height:1.14;font-weight:900}
.formulaRail span:nth-of-type(2),.formulaRail span:nth-of-type(4){background:#00a6c8}.formulaRail span:nth-of-type(3){background:#d9468f}.formulaRail span:nth-of-type(5){background:#f5b84b;color:#101421}
.formulaRail b{color:#fff0bf;font-size:22px}
.formulaRail i{height:4px;background:#101421}
.bottomWide{position:absolute;left:58px;right:58px;bottom:58px;height:405px;z-index:1;border:3px solid rgba(0,166,200,.32)}
.photoFeature .content,.lifePhoto .content,.socialPhoto .content{padding-bottom:535px}
.numberCards{margin-top:34px;display:grid;grid-template-columns:repeat(2,1fr);gap:14px}
.numberCards span{height:124px;padding:18px;display:grid;align-content:space-between;background:#fffdf5;border-top:12px solid #00a6c8;font-size:25px;line-height:1.16;font-weight:850}
.numberCards span:nth-child(2),.numberCards span:nth-child(3){border-top-color:#d9468f}
.numberCards b{font-size:20px;color:#101421}
.trapCards{margin-top:38px;display:grid;grid-template-columns:repeat(2,1fr);gap:14px}
.trapCards span{height:205px;padding:22px;display:grid;align-content:space-between;background:#fffdf5;border:2px solid rgba(16,20,33,.18);font-size:30px;line-height:1.15;font-weight:890}
.trapCards b{font-size:23px;color:#d9468f}
.note{margin:auto 0 0;padding:26px 28px;background:#101421;color:#fffdf6;font-size:30px;line-height:1.25;font-weight:880}
.rightPhoto{position:absolute;right:58px;bottom:58px;width:410px;height:560px;z-index:1;border:3px solid rgba(0,166,200,.32)}
.questionPhoto .content{padding-right:500px}
.questionPhoto .quote{font-size:28px;line-height:1.42}
.questionSteps{margin-top:auto;display:grid;gap:12px}
.questionSteps span{height:86px;padding:0 20px;display:flex;align-items:center;background:#101421;color:#fffdf6;border-left:12px solid #00a6c8;font-size:27px;font-weight:860}
.questionSteps span:nth-child(2),.questionSteps span:nth-child(4){border-left-color:#d9468f}
.matrix{margin-top:38px;display:grid;grid-template-columns:repeat(2,1fr);gap:14px}
.matrix span{min-height:235px;padding:22px;display:grid;align-content:space-between;background:#fffdf5;border-top:14px solid #00a6c8;font-size:26px;line-height:1.22;font-weight:840}
.matrix span:nth-child(2),.matrix span:nth-child(3){border-top-color:#d9468f}.matrix span:nth-child(4){border-top-color:#f5b84b}
.matrix b{font-size:35px;color:#101421;font-family:"Songti SC","STSong","Noto Serif CJK SC",serif}
.lifeLine,.socialChain{margin-top:auto;display:grid;grid-template-columns:1fr 28px 1fr 28px 1fr 28px 1fr;align-items:center}
.lifeLine span,.socialChain span{height:138px;display:grid;place-items:center;text-align:center;background:#101421;color:#fffdf6;border-top:12px solid #00a6c8;font-size:28px;font-weight:900}
.lifeLine span:nth-of-type(2),.socialChain span:nth-of-type(2){border-top-color:#d9468f}.lifeLine span:nth-of-type(3),.socialChain span:nth-of-type(3){border-top-color:#f5b84b}.lifeLine span:nth-of-type(4),.socialChain span:nth-of-type(4){border-top-color:#00a6c8}
.lifeLine i,.socialChain i{height:4px;background:#101421}
.supportNodes{margin-top:auto;display:grid;grid-template-columns:repeat(5,1fr);gap:10px}
.supportNodes span{height:255px;padding:14px 10px;display:grid;place-items:center;text-align:center;background:#101421;color:#fffdf6;font-size:25px;line-height:1.15;font-weight:900}
.supportNodes span:nth-child(2),.supportNodes span:nth-child(4){background:#00a6c8}.supportNodes span:nth-child(3){background:#d9468f}.supportNodes span:nth-child(5){background:#f5b84b;color:#101421}
.socialPhoto .quote{font-size:27px;line-height:1.42}
.examFlow .quote{font-size:32px}
.examRows{margin-top:34px;display:grid;gap:12px}
.examRows span{height:105px;padding:0 22px;display:flex;align-items:center;gap:18px;background:#fffdf5;border-left:12px solid #00a6c8;font-size:26px;line-height:1.16;font-weight:860}
.examRows span:nth-child(2),.examRows span:nth-child(4){border-left-color:#d9468f}.examRows span:nth-child(5){border-left-color:#f5b84b}
.examRows b{font-size:22px;color:#101421}
.argument .quote{font-size:23px;line-height:1.47}
.argument:after{content:"";position:absolute;left:150px;right:150px;top:625px;height:240px;z-index:1;background:radial-gradient(circle at 50% 50%,transparent 0 58px,rgba(0,166,200,.28) 60px 63px,transparent 65px),linear-gradient(90deg,transparent 0 49%,rgba(16,20,33,.18) 49% 51%,transparent 51%),linear-gradient(180deg,transparent 0 49%,rgba(16,20,33,.18) 49% 51%,transparent 51%)}
.argGrid{margin-top:auto;display:grid;grid-template-columns:repeat(2,1fr);gap:14px}
.argGrid span{height:180px;display:grid;place-items:center;text-align:center;background:#fffdf5;border-top:14px solid #00a6c8;font-size:32px;font-weight:900}
.argGrid span:nth-child(2),.argGrid span:nth-child(4){border-top-color:#d9468f}
.interview .quote{font-size:30px;line-height:1.4}
.answerSteps{margin-top:38px;display:grid;gap:14px}
.answerSteps span{height:118px;padding:0 22px;display:flex;align-items:center;gap:18px;background:#fffdf5;border-left:12px solid #00a6c8;font-size:27px;line-height:1.18;font-weight:850}
.answerSteps span:nth-child(2),.answerSteps span:nth-child(4){border-left-color:#d9468f}
.answerSteps b{font-size:22px;color:#101421}
.closingTint{position:absolute;inset:0;z-index:2;background:linear-gradient(90deg,rgba(8,12,24,.90),rgba(8,12,24,.18) 67%,rgba(8,12,24,.44)),linear-gradient(180deg,rgba(8,12,24,.22),rgba(8,12,24,.80))}
.closing h1{color:#fffdf6;font-size:80px}
.closing .quote{margin-top:34px;background:rgba(255,253,245,.94);font-size:31px}
.closingNodes{margin-top:auto;display:grid;grid-template-columns:repeat(3,1fr);gap:14px}
.closingNodes span{height:152px;display:grid;place-items:center;text-align:center;background:#f4f0e8;color:#101421;border-top:12px solid #00a6c8;font-size:30px;font-weight:900}
.closingNodes span:nth-child(2){border-top-color:#d9468f}.closingNodes span:nth-child(3){border-top-color:#f5b84b}
.videoPhoto{position:absolute;inset:0;margin:0;z-index:1}
.videoPhoto img{filter:saturate(.84) contrast(1.08) brightness(.72)}
.videoTint{position:absolute;inset:0;z-index:2;background:linear-gradient(90deg,rgba(6,10,20,.92),rgba(6,10,20,.16) 70%),linear-gradient(180deg,rgba(6,10,20,.10),rgba(6,10,20,.28) 44%,rgba(6,10,20,.78))}
.magLines{position:absolute;inset:56px;z-index:3;border-top:2px solid rgba(255,255,255,.58);border-bottom:2px solid rgba(255,255,255,.42)}
.magLines:before{content:"";position:absolute;left:0;top:94px;width:210px;height:2px;background:rgba(255,255,255,.58)}
.magLines:after{content:"AI EDUCATION";position:absolute;right:0;top:24px;color:rgba(255,255,255,.72);font-size:20px;font-weight:820}
.videoTitle{position:absolute;left:64px;right:76px;bottom:92px;z-index:4;color:#fffdf6}
.v1 .videoTitle{bottom:100px}.v2 .videoTitle{bottom:104px}.v3 .videoTitle{bottom:94px}
.videoTitle p{margin:0 0 28px;color:#f5b84b;font-size:34px;line-height:1;font-weight:900}
.videoTitle h2{margin:0;font-family:"Songti SC","STSong","Noto Serif CJK SC",serif;font-size:86px;line-height:1.03;font-weight:780;letter-spacing:0;max-width:880px}
.v3 .videoTitle h2{font-size:79px}
.videoTitle span{display:block;width:max-content;max-width:850px;margin-top:26px;padding:14px 18px;background:#d9468f;color:#fff;font-size:27px;font-weight:900}
.v1 .videoTitle span{background:#00a6c8}.v3 .videoTitle span{background:#f5b84b;color:#101421;font-size:25px}
.preview{width:1800px;background:#d6d9d3;padding:34px;display:grid;grid-template-columns:repeat(5,1fr);gap:18px}
.preview figure{margin:0;background:#fff;padding:8px}
.preview img{width:100%;display:block}
.preview figcaption{padding:8px 2px 0;font-size:16px;font-weight:780;color:#303030}
`;

const html = `<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>AI时代教育小红书与视频号封面</title><style>${css}</style></head><body><main class="stage">${pages.map(renderPage).join('\n')}${videos.map(renderVideo).join('\n')}</main></body></html>`;
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
