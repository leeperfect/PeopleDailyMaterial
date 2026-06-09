import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { chromium } from 'playwright';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const repoRoot = path.resolve(__dirname, '../../../..');
const mediaDir = path.join(repoRoot, 'media/images/2026-06-07-digital-governance-xhs');
const assetDir = path.join(mediaDir, 'assets');
const htmlPath = path.join(__dirname, 'index.html');

const asset = (name) => path.relative(__dirname, path.join(assetDir, name)).replaceAll(path.sep, '/');

const pages = [
  {
    id: 'xhs-01-cover',
    file: 'xhs-01-cover.png',
    mode: 'cover',
    label: 'COVER',
    title: '数字治理\n不是上系统',
    subtitle: '流程再造 / 线下兜底 / 责任闭环',
    image: asset('tablet-stylus-process.jpg'),
    pos: 'center 52%',
    quotes: [
      '数字治理不是把服务搬到线上，而是用数据重塑流程，同时保留人工服务和责任闭环。',
    ],
    chips: ['少跑腿', '少填表', '有人负责'],
  },
  {
    id: 'xhs-02-shift',
    file: 'xhs-02-shift.png',
    mode: 'flow',
    label: 'SHIFT',
    title: '从有没有平台\n转向有没有办成',
    quotes: [
      '数字治理要从“有没有平台”，转向“流程有没有改、责任有没有接、群众有没有真正办成”。',
    ],
    steps: [
      ['01', '流程有没有改', '跨部门事项重做工作流'],
      ['02', '责任有没有接', '牵头、协同、反馈要清楚'],
      ['03', '群众有没有办成', '线上线下都要有出口'],
    ],
  },
  {
    id: 'xhs-03-process',
    file: 'xhs-03-process.png',
    mode: 'photoQuote',
    label: 'PROCESS',
    title: '群众跑的路\n让数据在后台跑',
    image: asset('server-racks-data.jpg'),
    pos: 'center 48%',
    quotes: [
      '真正的数字治理，不是把线下表格搬到线上，而是把群众要跑的路，变成数据和部门在统一后台跑。',
    ],
    chips: ['数据共享', '后台核验', '部门协同'],
  },
  {
    id: 'xhs-04-loop',
    file: 'xhs-04-loop.png',
    mode: 'loop',
    label: 'LOOP',
    title: '没有闭环\n就只是展示屏',
    quotes: [
      '数字技术的价值，不在于替治理贴上智能标签，而在于把问题发现、责任分派、协同处置和结果反馈接成闭环。',
    ],
    loop: ['数据采集', '智能识别', '风险预警', '调度处置', '结果反馈', '复盘优化'],
  },
  {
    id: 'xhs-05-anti-formalism',
    file: 'xhs-05-anti-formalism.png',
    mode: 'doubleQuote',
    label: 'ANTI-FORM',
    title: '防形式\n不是反数字化',
    quotes: [
      '数字服务如果没有围绕人的真实需求改流程，就可能把“跑腿难”变成“操作难”，把“排队难”变成“等待难”。',
      '防形式，不是不发展数字化，而是防止“系统上线了、流程没变；平台建起来了、群众用不好；技术更先进了、责任更模糊了”。',
    ],
  },
  {
    id: 'xhs-06-platform',
    file: 'xhs-06-platform.png',
    mode: 'matrix',
    label: 'PLATFORM',
    title: '好平台\n不是功能越多越好',
    quotes: [
      '好的数字平台，不是功能越多越好，而是让最常用、最急需、最容易卡住的服务更容易抵达。',
    ],
    cells: [
      ['高频事项', '一键直达'],
      ['特殊群体', '关爱模式'],
      ['卡住环节', '呼叫帮助'],
      ['线上线下', '服务衔接'],
    ],
    stat: ['66%', '患者等候时间缩短'],
  },
  {
    id: 'xhs-07-rules',
    file: 'xhs-07-rules.png',
    mode: 'rules',
    label: 'RULES',
    title: '技术越强\n责任越要前置',
    quotePlain: '技术越强，规则越要清楚；应用越广，责任越要前置。',
    cells: ['源头标识', '分发审核', '传播核验', '用户声明', '风险追溯', '结果纠偏'],
  },
  {
    id: 'xhs-08-hotline',
    file: 'xhs-08-hotline.png',
    mode: 'photoQuote',
    label: 'HOTLINE',
    title: '群众卡住时\n要能找到人',
    image: asset('call-center-hotline.jpg'),
    pos: 'center 48%',
    quotes: [
      '数字治理的温度，不在于机器回答得多快，而在于群众卡住的时候，能不能找到负责的人。',
    ],
    chips: ['人工座席', '一单直达', '督办回访'],
  },
  {
    id: 'xhs-09-fairness',
    file: 'xhs-09-fairness.png',
    mode: 'photoQuote',
    label: 'FAIRNESS',
    title: '公平不是\n所有人同一种办事方式',
    image: asset('tablet-help-service.jpg'),
    pos: 'center 58%',
    quotes: [
      '真正公平的数字治理，不是让所有人都用同一种线上方式，而是让每个人都能找到适合自己的办事通道。',
    ],
    chips: ['线下窗口', '人工帮办', '电话服务'],
  },
  {
    id: 'xhs-10-exam-platform',
    file: 'xhs-10-exam-platform.png',
    mode: 'exam',
    label: 'EXAM 01',
    title: '系统上线了\n群众还是办不成',
    quotes: [
      '题目：某地政务服务平台已经上线，但群众反映仍要重复提交材料，线上流程复杂，线下窗口也解释不清。领导让你牵头整改，你怎么办？',
      '整改数字政务，不能只修页面，而要从群众办事路径出发，重塑部门协同流程。',
    ],
    points: ['查堵点', '改流程', '通数据', '强帮办', '建闭环'],
  },
  {
    id: 'xhs-11-exam-hospital',
    file: 'xhs-11-exam-hospital.png',
    mode: 'examPhoto',
    label: 'EXAM 02',
    title: '互联网医院\n体验差怎么办',
    image: asset('doctor-tablet-hospital.jpg'),
    pos: 'center 42%',
    quotes: [
      '题目：群众反映互联网医院挂号容易，但医生回复慢、老人不会操作、医保结算和药品配送不顺畅。你认为应如何改进？',
      '互联网医院不是把门诊搬到手机上，而是围绕患者完整就医链条重做服务。',
    ],
    points: ['明确标准', '优化分流', '适老改造', '打通环节', '强化监管'],
  },
  {
    id: 'xhs-12-exam-offline',
    file: 'xhs-12-exam-offline.png',
    mode: 'exam',
    label: 'EXAM 03',
    title: '不会用线上平台\n如何兜底',
    quotes: [
      '题目：某地推进政务服务线上办理，但部分老年人、残障人士和文化程度较低群众反映不会用、不敢用、办不了。你会怎么做？',
      '数字化不能以牺牲服务可及性为代价。越是推进线上办理，越要把线下兜底和人工帮办做扎实。',
    ],
    points: ['保留窗口', '人工帮办', '热线直达', '简化界面', '闭环反馈'],
  },
  {
    id: 'xhs-13-three-lines',
    file: 'xhs-13-three-lines.png',
    mode: 'three',
    label: 'MEMORY',
    title: '国考省考\n记住三句话',
    rows: [
      ['效率', '来自流程再造', '数据共享、部门协同、后台核验减少群众成本'],
      ['质量', '来自防止形式', '服务标准、用户体验、风险边界同步跟上'],
      ['公平', '来自线下兜底', '线上线下融合，特殊群体也能办得成'],
    ],
  },
  {
    id: 'xhs-14-essay',
    file: 'xhs-14-essay.png',
    mode: 'essay',
    label: 'ESSAY',
    title: '申论总结句\n这样写',
    quotes: [
      '数字治理不能停留在“上系统”的表层，而要回到群众办事的真实路径。以数据共享推动流程再造，以规则标准防止数字形式主义，以线下窗口和人工帮办兜住服务公平，才能让数字技术真正转化为群众可感可及的治理效能。',
    ],
    pillars: [
      ['流程再造', '数据共享推动部门协同'],
      ['防止形式', '规则标准约束技术应用'],
      ['线下兜底', '窗口和帮办守住公平'],
    ],
  },
  {
    id: 'xhs-15-closing',
    file: 'xhs-15-closing.png',
    mode: 'closing',
    label: 'TAKEAWAY',
    title: '判断成效\n看群众省不省心',
    quotes: [
      '判断数字治理有没有成效，不看系统有多先进，而看群众有没有少跑腿、少填表、少等待，遇到问题有没有人负责。',
    ],
    chips: ['少跑腿', '少填表', '少等待', '有人负责'],
  },
  {
    id: 'xhs-16-references',
    file: 'xhs-16-references.png',
    mode: 'refs',
    label: 'REFERENCES',
    title: '参考文献',
    refs: [
      '初程程：《以数智技术赋能“高效办成一件事”（治理之道）》，《人民日报》2026年5月11日第09版。',
      '陆凡冰、窦皓、游仪：《互联网医院，离建好用好还有多远（健康焦点）》，《人民日报》2026年5月15日第19版。',
      '《重庆以人工智能为抓手，探索超大城市现代化治理新路子》，《人民日报》2026年4月24日第10版。',
      '武少民、陆凡冰：《善用善治 促进人工智能内容规范发展》，《人民日报》2026年4月3日第11版。',
      '罗阳奇：《热线接入提速 政务服务升温》，《人民日报》2026年5月25日第10版。',
    ],
  },
];

const esc = (str = '') => String(str).replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
const lines = (str = '') => esc(str).replace(/\n/g, '<br>');
const q = (text, cls = '') => `<div class="quote ${cls}">> ${esc(text)}</div>`;
const top = (page, i) => `<div class="top"><span>${esc(page.label)} · ${String(i + 1).padStart(2, '0')}</span><span>《人民日报》这样写</span></div>`;
const foot = () => `<div class="foot"><span>DIGITAL GOVERNANCE</span><span>流程再造 / 线下兜底</span></div>`;
const photo = (page, cls = '') => `<figure class="photo ${cls}"><img src="${page.image}" style="object-position:${page.pos || 'center 50%'}" alt=""></figure>`;
const quoteBlock = (page, cls = '') => page.quotes.map((item, idx) => q(item, `${cls} ${idx > 0 ? 'secondary' : ''}`)).join('');

function renderPage(page, i) {
  if (page.mode === 'cover') {
    return `<section class="poster cover" id="${page.id}">
      ${top(page, i)}
      ${photo(page, 'cover-photo')}
      <div class="eyebrow">${esc(page.subtitle)}</div>
      <h1 class="h-cover">${lines(page.title)}</h1>
      ${quoteBlock(page, 'cover-quote')}
      <div class="chips">${page.chips.map((c) => `<span>${esc(c)}</span>`).join('')}</div>
      ${foot()}
    </section>`;
  }
  if (page.mode === 'flow') {
    return `<section class="poster" id="${page.id}">
      ${top(page, i)}
      <h1 class="h-xl">${lines(page.title)}</h1>
      ${quoteBlock(page)}
      <div class="flow">${page.steps.map(([num, title, sub]) => `<div><b>${esc(num)}</b><strong>${esc(title)}</strong><span>${esc(sub)}</span></div>`).join('')}</div>
      ${foot()}
    </section>`;
  }
  if (page.mode === 'photoQuote') {
    return `<section class="poster" id="${page.id}">
      ${top(page, i)}
      <h1 class="h-lg">${lines(page.title)}</h1>
      ${photo(page)}
      ${quoteBlock(page)}
      <div class="chips">${page.chips.map((c) => `<span>${esc(c)}</span>`).join('')}</div>
      ${foot()}
    </section>`;
  }
  if (page.mode === 'loop') {
    return `<section class="poster" id="${page.id}">
      ${top(page, i)}
      <h1 class="h-lg">${lines(page.title)}</h1>
      ${quoteBlock(page)}
      <div class="loop">${page.loop.map((item, idx) => `<div><span>${String(idx + 1).padStart(2, '0')}</span><strong>${esc(item)}</strong></div>`).join('')}</div>
      ${foot()}
    </section>`;
  }
  if (page.mode === 'doubleQuote') {
    return `<section class="poster" id="${page.id}">
      ${top(page, i)}
      <h1 class="h-lg">${lines(page.title)}</h1>
      ${quoteBlock(page, 'large')}
      <div class="contrast"><div>跑腿难<br>操作难</div><div>排队难<br>等待难</div><div>技术强<br>责任清</div></div>
      ${foot()}
    </section>`;
  }
  if (page.mode === 'matrix') {
    return `<section class="poster" id="${page.id}">
      ${top(page, i)}
      <h1 class="h-lg">${lines(page.title)}</h1>
      ${quoteBlock(page)}
      <div class="matrix">${page.cells.map(([a, b]) => `<div><span>${esc(a)}</span><strong>${esc(b)}</strong></div>`).join('')}</div>
      <div class="stat"><strong>${esc(page.stat[0])}</strong><span>${esc(page.stat[1])}</span></div>
      ${foot()}
    </section>`;
  }
  if (page.mode === 'rules') {
    return `<section class="poster" id="${page.id}">
      ${top(page, i)}
      <h1 class="h-lg">${lines(page.title)}</h1>
      ${q(page.quotePlain)}
      <div class="rule-grid">${page.cells.map((c, idx) => `<div><b>${String(idx + 1).padStart(2, '0')}</b><strong>${esc(c)}</strong></div>`).join('')}</div>
      ${foot()}
    </section>`;
  }
  if (page.mode === 'exam' || page.mode === 'examPhoto') {
    return `<section class="poster exam" id="${page.id}">
      ${top(page, i)}
      <h1 class="h-md">${lines(page.title)}</h1>
      ${page.mode === 'examPhoto' ? photo(page, 'exam-photo') : ''}
      ${q(page.quotes[0], 'question')}
      <div class="points">${page.points.map((p, idx) => `<span><b>${String(idx + 1).padStart(2, '0')}</b>${esc(p)}</span>`).join('')}</div>
      ${q(page.quotes[1], 'answer')}
      ${foot()}
    </section>`;
  }
  if (page.mode === 'three') {
    return `<section class="poster" id="${page.id}">
      ${top(page, i)}
      <h1 class="h-lg">${lines(page.title)}</h1>
      <div class="three">${page.rows.map(([a, b, c]) => `<div><b>${esc(a)}</b><strong>${esc(b)}</strong><span>${esc(c)}</span></div>`).join('')}</div>
      ${foot()}
    </section>`;
  }
  if (page.mode === 'essay') {
    return `<section class="poster essay" id="${page.id}">
      ${top(page, i)}
      <h1 class="h-md">${lines(page.title)}</h1>
      ${quoteBlock(page, 'long')}
      <div class="pillars">${page.pillars.map(([a, b]) => `<div><strong>${esc(a)}</strong><span>${esc(b)}</span></div>`).join('')}</div>
      <div class="axis"><span>DATA</span><span>RULE</span><span>OFFLINE</span></div>
      ${foot()}
    </section>`;
  }
  if (page.mode === 'closing') {
    return `<section class="poster closing" id="${page.id}">
      ${top(page, i)}
      <h1 class="h-xl">${lines(page.title)}</h1>
      ${quoteBlock(page, 'closing-q')}
      <div class="closing-chips">${page.chips.map((c, idx) => `<div><span>${String(idx + 1).padStart(2, '0')}</span><strong>${esc(c)}</strong></div>`).join('')}</div>
      ${foot()}
    </section>`;
  }
  if (page.mode === 'refs') {
    return `<section class="poster refs" id="${page.id}">
      ${top(page, i)}
      <h1 class="h-md">${esc(page.title)}</h1>
      <div class="refs-list">${page.refs.map((r, idx) => `<div><span>${String(idx + 1).padStart(2, '0')}</span><p>${esc(r)}</p></div>`).join('')}</div>
      ${foot()}
    </section>`;
  }
}

const css = `
  :root {
    --paper: #fcfbf6;
    --ink: #151515;
    --muted: #77736e;
    --line: #d8d4ca;
    --mint: #bfe8d5;
    --butter: #f6df8f;
    --peach: #f5b7a6;
    --lavender: #c9c3f2;
    --sky: #afd9f5;
    --accent: #7fcdb4;
    --accent2: #f4c7b9;
    --accent3: #c9c3f2;
    --accent4: #f3df98;
    --sans: "Inter", "Helvetica Neue", Helvetica, "Noto Sans SC", -apple-system, BlinkMacSystemFont, "PingFang SC", "Microsoft YaHei UI", sans-serif;
    --mono: "IBM Plex Mono", "SFMono-Regular", Consolas, monospace;
  }
  * { box-sizing: border-box; }
  html, body { margin: 0; padding: 0; }
  body { background: #1b1b1b; padding: 56px 0; font-family: var(--sans); color: var(--ink); }
  .sheet { display: flex; flex-direction: column; align-items: center; gap: 46px; }
  .poster {
    width: 1080px;
    height: 1440px;
    position: relative;
    overflow: hidden;
    background:
      linear-gradient(rgba(21,21,21,.035) 1px, transparent 1px),
      linear-gradient(90deg, rgba(21,21,21,.035) 1px, transparent 1px),
      var(--paper);
    background-size: 64px 64px, 64px 64px, auto;
    padding: 76px 80px 64px;
    display: flex;
    flex-direction: column;
    gap: 28px;
  }
  .poster::before { content: ""; position: absolute; inset: 0 auto 0 0; width: 22px; background: var(--accent); }
  .poster:nth-child(2n)::before { background: var(--accent2); }
  .poster:nth-child(3n)::before { background: var(--accent3); }
  .poster:nth-child(5n)::before { background: var(--accent4); }
  .poster > * { position: relative; z-index: 1; }
  .top, .foot {
    display: flex; justify-content: space-between; align-items: center;
    font-family: var(--mono); font-size: 19px; letter-spacing: .16em; color: var(--muted); text-transform: uppercase;
  }
  .top { border-bottom: 1px solid var(--line); padding-bottom: 20px; }
  .foot { margin-top: auto; border-top: 1px solid var(--line); padding-top: 20px; }
  h1 { margin: 0; letter-spacing: 0; font-weight: 200; }
  .h-cover { font-size: 116px; line-height: 1.03; }
  .h-xl { font-size: 104px; line-height: 1.06; }
  .h-lg { font-size: 92px; line-height: 1.08; }
  .h-md { font-size: 78px; line-height: 1.12; }
  .eyebrow { font-family: var(--mono); color: var(--muted); letter-spacing: .12em; font-size: 22px; text-transform: uppercase; }
  .photo { margin: 0; width: 100%; height: 390px; border: 1px solid var(--line); overflow: hidden; background: #eee; }
  .cover-photo { height: 420px; }
  .exam-photo { height: 270px; }
  .photo img { width: 100%; height: 100%; object-fit: cover; display: block; }
  .quote {
    border-left: 10px solid var(--accent);
    background: rgba(255,255,255,.72);
    padding: 24px 28px;
    font-size: 29px;
    line-height: 1.45;
    font-weight: 560;
  }
  .quote.secondary { border-left-color: var(--accent2); background: rgba(255,255,255,.58); }
  .quote.large { font-size: 30px; }
  .quote.question { font-size: 25px; line-height: 1.46; border: 1px solid var(--line); border-left: 10px solid var(--accent); }
  .quote.answer { background: var(--mint); border-left-color: var(--ink); font-size: 28px; }
  .quote.long { font-size: 27px; line-height: 1.45; }
  .chips { display: grid; grid-template-columns: repeat(3, 1fr); gap: 14px; }
  .chips span, .closing-chips div {
    background: var(--mint); padding: 20px 18px; text-align: center; font-size: 28px; font-weight: 650;
  }
  .chips span:nth-child(2) { background: var(--butter); }
  .chips span:nth-child(3) { background: var(--lavender); }
  .chips span:nth-child(4) { background: var(--peach); }
  .flow { display: grid; gap: 18px; }
  .flow div {
    border: 1px solid var(--line); background: rgba(255,255,255,.74); padding: 26px 28px; min-height: 178px;
    display: grid; grid-template-columns: 82px 1fr; align-items: baseline; gap: 18px;
  }
  .flow b, .rule-grid b, .points b, .closing-chips span { font-family: var(--mono); color: var(--muted); font-size: 21px; letter-spacing: .12em; }
  .flow strong { font-size: 42px; }
  .flow span { grid-column: 2; font-size: 25px; color: var(--muted); margin-top: -12px; }
  .loop, .rule-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }
  .loop div, .rule-grid div {
    min-height: 154px; border: 1px solid var(--line); padding: 24px 26px; background: rgba(255,255,255,.72);
    display: flex; flex-direction: column; justify-content: space-between;
  }
  .loop div:nth-child(1), .loop div:nth-child(4), .rule-grid div:nth-child(2), .rule-grid div:nth-child(5) { background: var(--sky); }
  .loop div:nth-child(2), .loop div:nth-child(5), .rule-grid div:nth-child(3), .rule-grid div:nth-child(6) { background: var(--butter); }
  .loop span { font-family: var(--mono); font-size: 20px; color: var(--muted); letter-spacing: .12em; }
  .loop strong, .rule-grid strong { font-size: 34px; line-height: 1.16; }
  .contrast { display: grid; grid-template-columns: repeat(3, 1fr); gap: 16px; }
  .contrast div { min-height: 210px; padding: 26px; font-size: 44px; line-height: 1.2; font-weight: 650; background: var(--mint); }
  .contrast div:nth-child(2) { background: var(--peach); }
  .contrast div:nth-child(3) { background: var(--lavender); }
  .matrix { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }
  .matrix div, .pillars div {
    border: 1px solid var(--line); background: rgba(255,255,255,.72); padding: 24px 26px; min-height: 138px;
    display: flex; flex-direction: column; justify-content: space-between;
  }
  .matrix span { font-family: var(--mono); color: var(--muted); font-size: 19px; letter-spacing: .13em; }
  .matrix strong { font-size: 38px; }
  .stat { background: var(--butter); padding: 28px 32px; display: grid; grid-template-columns: 240px 1fr; align-items: baseline; }
  .stat strong { font-size: 92px; font-weight: 200; line-height: 1; }
  .stat span { font-size: 32px; color: var(--muted); font-weight: 600; }
  .points { display: flex; flex-wrap: wrap; gap: 12px; }
  .points span { padding: 15px 17px; border: 1px solid var(--line); background: rgba(255,255,255,.72); font-size: 25px; font-weight: 650; }
  .points b { margin-right: 10px; }
  .three { display: grid; gap: 18px; }
  .three div { min-height: 210px; padding: 30px; background: var(--mint); display: flex; flex-direction: column; justify-content: space-between; }
  .three div:nth-child(2) { background: var(--butter); }
  .three div:nth-child(3) { background: var(--lavender); }
  .three b { font-size: 38px; }
  .three strong { font-size: 48px; }
  .three span { font-size: 25px; color: var(--muted); line-height: 1.35; }
  .pillars { display: grid; gap: 14px; }
  .pillars div { min-height: 116px; display: grid; grid-template-columns: 190px 1fr; align-items: baseline; }
  .pillars strong { font-size: 30px; color: #326a5c; }
  .pillars span { font-size: 27px; color: var(--muted); }
  .axis { display: grid; grid-template-columns: repeat(3, 1fr); gap: 16px; }
  .axis span { background: var(--peach); padding: 28px; font-family: var(--mono); font-size: 25px; letter-spacing: .14em; text-align: center; }
  .axis span:nth-child(2) { background: var(--sky); }
  .axis span:nth-child(3) { background: var(--butter); }
  .closing-chips { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }
  .closing-chips div { min-height: 170px; text-align: left; display: flex; flex-direction: column; justify-content: space-between; }
  .closing-chips div:nth-child(2) { background: var(--butter); }
  .closing-chips div:nth-child(3) { background: var(--peach); }
  .closing-chips div:nth-child(4) { background: var(--lavender); }
  .closing-chips strong { font-size: 40px; }
  .refs-list { display: flex; flex-direction: column; border-top: 1px solid var(--line); }
  .refs-list div { display: grid; grid-template-columns: 64px 1fr; gap: 18px; padding: 28px 0; border-bottom: 1px solid var(--line); }
  .refs-list span { font-family: var(--mono); color: #326a5c; font-size: 22px; letter-spacing: .1em; }
  .refs-list p { margin: 0; font-size: 25px; line-height: 1.38; }
`;

const html = `<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>数字治理 · 小红书图文</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Inter:wght@200;300;400;500;600;700&family=Noto+Sans+SC:wght@300;400;500;600;700&family=IBM+Plex+Mono:wght@400;500;600&display=swap">
  <style>${css}</style>
</head>
<body>
  <main class="sheet">
    ${pages.map(renderPage).join('\n')}
  </main>
</body>
</html>`;

fs.mkdirSync(mediaDir, { recursive: true });
fs.writeFileSync(htmlPath, html);

const browser = await chromium.launch({ headless: true });
const page = await browser.newPage({ viewport: { width: 1280, height: 1600 }, deviceScaleFactor: 1 });
await page.goto(`file://${htmlPath}`, { waitUntil: 'load', timeout: 60000 });
await page.waitForTimeout(1200);

for (const item of pages) {
  await page.locator(`#${item.id}`).screenshot({
    path: path.join(mediaDir, item.file),
    animations: 'disabled',
  });
}

await browser.close();
console.log(`Rendered ${pages.length} images to ${mediaDir}`);
