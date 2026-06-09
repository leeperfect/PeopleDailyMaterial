import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { chromium } from 'playwright';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const outDir = path.join(__dirname, 'output');
const htmlPath = path.join(__dirname, 'index.html');

const asset = (name) => `assets/${name}`;

const pages = [
  {
    id: 'xhs-01-cover',
    file: 'xhs-01-cover.png',
    mode: 'cover',
    label: 'COVER',
    title: '新就业群体\n不是边缘人',
    subtitle: '从服务对象到城市伙伴',
    image: asset('delivery-cyclist-motion.jpg'),
    pos: 'center 54%',
    quote: '新就业群体不是城市治理的边缘人，而是城市运转离不开的劳动者，也是可以参与治理的城市伙伴。',
    chips: ['权益托底', '服务融入', '城市共治'],
  },
  {
    id: 'xhs-02-logic',
    file: 'xhs-02-logic.png',
    mode: 'flow',
    label: 'LOGIC',
    title: '不是关怀题\n是治理题',
    quote: '先让他们安心工作，再让他们融入城市，最后让他们参与治理。',
    steps: [
      ['01', '安心工作', '规则托底，让劳动者有安全感'],
      ['02', '融入城市', '服务进入工作半径与生活半径'],
      ['03', '参与治理', '从被服务者变成共治伙伴'],
    ],
  },
  {
    id: 'xhs-03-problem',
    file: 'xhs-03-problem.png',
    mode: 'matrix',
    label: 'DIAGNOSIS',
    title: '先把难点\n看准',
    kicker: '新就业群体不是单一职业，而是一组新的城市劳动场景。',
    cells: [
      ['劳动关系', '复杂'],
      ['工作场景', '分散'],
      ['收入状态', '波动'],
      ['平台规则', '影响强'],
      ['维权证据', '不易固定'],
      ['城市服务', '够得到才有用'],
    ],
    bottom: '只写“多关心”会停在温情层；高分写法要进入规则、服务和共治。',
  },
  {
    id: 'xhs-04-rights',
    file: 'xhs-04-rights.png',
    mode: 'photoQuote',
    label: 'RIGHTS',
    title: '保障不是\n送一杯水',
    image: asset('delivery-snow-protection.jpg'),
    pos: 'center 58%',
    quote: '保障不是送一杯水，而是让劳动者知道：收入有规则，休息有边界，受伤有保障，纠纷有出口。',
    chips: ['劳动报酬', '休息权益', '职业伤害', '纠纷出口'],
  },
  {
    id: 'xhs-05-rights-chain',
    file: 'xhs-05-rights-chain.png',
    mode: 'chain',
    label: 'MECHANISM',
    title: '把维权路\n修到身边',
    quote: '新就业群体的权益保障，不能靠个体硬扛，而要靠制度把维权路修到他们身边。',
    steps: [
      ['入口', '驿站 / 热线 / 服务中心'],
      ['证据', '配送记录 / 工资流水 / 就医凭证'],
      ['调解', '平台 / 站点 / 人社 / 工会'],
      ['衔接', '仲裁 / 法援 / 速裁庭'],
      ['规范', '协议 / 薪酬 / 投诉机制'],
    ],
  },
  {
    id: 'xhs-06-service',
    file: 'xhs-06-service.png',
    mode: 'photoQuote',
    label: 'SERVICE',
    title: '服务不是\n临时慰问',
    image: asset('package-handover-service.jpg'),
    pos: 'center 50%',
    quote: '服务新就业群体，不只是给他们一个歇脚点，更是给他们一个被城市接纳的位置。',
    chips: ['歇脚', '就餐', '住房', '培训', '归属'],
  },
  {
    id: 'xhs-07-work-radius',
    file: 'xhs-07-work-radius.png',
    mode: 'kpi',
    label: 'RADIUS',
    title: '让岗位、保障\n进入工作半径',
    quote: '好的就业服务，不是让劳动者追着岗位跑，而是让岗位、保障和规则一起进入劳动者的工作半径。',
    stats: [
      ['8400万', '全国新就业群体总量'],
      ['29.13万', '马驹桥累计接待零工人次'],
      ['22.38万', '成功撮合上岗人次'],
      ['76.8%', '撮合成功率'],
    ],
  },
  {
    id: 'xhs-08-service-net',
    file: 'xhs-08-service-net.png',
    mode: 'imageMatrix',
    label: 'NETWORK',
    title: '真正有用的服务\n是一张网',
    image: asset('parcels-work-radius.jpg'),
    pos: 'center 52%',
    kicker: '服务不只靠一个暖心点位，而要能持续接住流动的人。',
    cells: [
      ['接诉求', '手机端、驿站、中心都能进'],
      ['调资源', '部门联动，现场办公'],
      ['办实事', '把乱放点变成规范点'],
      ['能运转', '区级中心、行业调解、服务点位'],
    ],
  },
  {
    id: 'xhs-09-co-governance',
    file: 'xhs-09-co-governance.png',
    mode: 'photoQuote',
    label: 'CO-GOV',
    title: '共治不是\n额外加任务',
    image: asset('night-delivery-city.jpg'),
    pos: 'center 54%',
    quote: '共治不是把任务压给骑手，而是让他们进入问题发现、规则讨论和方案形成的过程。',
    chips: ['发现问题', '参与议事', '形成规则', '共享结果'],
  },
  {
    id: 'xhs-10-precondition',
    file: 'xhs-10-precondition.png',
    mode: 'roles',
    label: 'PRECONDITION',
    title: '先被城市接住\n再一起治理',
    quote: '先让劳动者被城市接住，城市才能进一步请他们一起治理。',
    roles: [
      ['食品安全', '流动监督员'],
      ['城市隐患', '前端发现者'],
      ['社区服务', '志愿参与者'],
      ['基层议事', '真实表达者'],
      ['平台规则', '直接反馈者'],
    ],
  },
  {
    id: 'xhs-11-exam-rights',
    file: 'xhs-11-exam-rights.png',
    mode: 'exam',
    label: 'EXAM 01',
    title: '外卖骑手摔伤\n维权难怎么办',
    question: '题目：某地一名外卖骑手送餐途中摔伤，但站点认为其不是正式员工，不愿承担医疗费用，还克扣工资。你作为相关部门工作人员，会怎么处理？',
    answer: '处理这类问题，不能只解决一笔赔偿，更要把个案变成规范站点用工、完善维权通道、预防同类纠纷的契机。',
    points: ['接住诉求', '固定证据', '协同化解', '源头规范'],
    logic: ['权益受损', '证据固定', '多元化解', '用工规范'],
  },
  {
    id: 'xhs-12-exam-labor',
    file: 'xhs-12-exam-labor.png',
    mode: 'exam',
    label: 'EXAM 02',
    title: '零工路边聚集\n秩序混乱怎么办',
    question: '题目：你所在辖区有不少零工在路边等活，存在交通拥堵、用工不规范、欠薪纠纷等问题。领导让你牵头治理，你怎么办？',
    answer: '治理零工聚集，不是把人赶走，而是把无序等待变成有组织、有保障、有成长空间的就业服务。',
    points: ['摸清需求', '规范场景', '线上匹配', '权益兜底', '技能提升'],
    logic: ['路边等待', '就业市场', '线上平台', '服务兜底'],
  },
  {
    id: 'xhs-13-exam-governance',
    file: 'xhs-13-exam-governance.png',
    mode: 'exam',
    label: 'EXAM 03',
    title: '如何引导他们\n参与城市治理',
    question: '题目：快递员、外卖骑手、网约车司机等每天穿梭城市一线，熟悉基层情况。你认为应如何引导他们参与城市治理？',
    answer: '新就业群体参与治理，前提是城市先善待他们，关键是给他们制度化入口，目标是把城市一线的流动感知转化为基层治理的及时响应。',
    points: ['保障先行', '搭建平台', '明确规则', '及时反馈', '正向激励'],
    logic: ['先善待', '给入口', '有反馈', '成响应'],
  },
  {
    id: 'xhs-14-essay',
    file: 'xhs-14-essay.png',
    mode: 'essay',
    label: 'ESSAY',
    title: '申论总结句\n这样落笔',
    quote: '新就业群体治理，不能停留在“关心关爱”的温情表达上，而要构建权益保障、公共服务和社会共治相衔接的治理体系。以法治规则托底劳动权益，以服务网络提升城市归属，以协商平台激活治理参与，才能让新就业群体从服务对象成长为城市伙伴。',
    pillars: [
      ['权益保障', '法治规则托底劳动权益'],
      ['公共服务', '服务网络提升城市归属'],
      ['社会共治', '协商平台激活治理参与'],
    ],
    axis: ['托底', '融入', '共治'],
  },
  {
    id: 'xhs-15-closing',
    file: 'xhs-15-closing.png',
    mode: 'closing',
    label: 'TAKEAWAY',
    title: '高分写法\n不是只写辛苦',
    quote: '新就业群体的高分写法，不是只写“他们很辛苦”，而是写清城市如何保障他们、服务他们，并邀请他们一起把城市治理得更好。',
    steps: ['看见他们', '接住他们', '成就他们', '邀请他们'],
  },
  {
    id: 'xhs-16-references',
    file: 'xhs-16-references.png',
    mode: 'refs',
    label: 'REFERENCES',
    title: '参考文献',
    refs: [
      '邱超奕：《以“共赢思维”服务好新就业群体（人民时评）》，《人民日报》2026年3月23日第05版。',
      '胡杰成：《提升新就业群体服务水平（专题深思）》，《人民日报》2026年3月23日第09版。',
      '《中共中央办公厅国务院办公厅关于加强新就业群体服务管理的意见》，《人民日报》2026年4月27日第01版。',
      '金歆：《破解数字时代劳动权益保护新问题（金台锐评）》，《人民日报》2026年4月30日第19版。',
      '潘俊强：《“零工市场让我们好找活、有保障”（稳就业·我的求职故事）》，《人民日报》2026年5月17日第04版。',
      '巨云鹏：《从“小哥议事厅”看共建共享（现场评论）》，《人民日报》2026年5月19日第05版。',
      '刘晓宇：《构建新就业形态劳动者维权服务网络》，《人民日报》2026年5月20日第04版。',
      '王沛：《为新就业形态劳动者撑腰打气》，《人民日报》2026年5月30日第04版。',
    ],
  },
];

const esc = (str = '') =>
  String(str).replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));

const lines = (str = '') => esc(str).replace(/\n/g, '<br>');

function topbar(page, index) {
  return `<div class="topbar"><span>${esc(page.label)} · ${String(index + 1).padStart(2, '0')}</span><span>《人民日报》这样写</span></div>`;
}

function quote(text, extra = '') {
  return `<div class="quote ${extra}">> ${esc(text)}</div>`;
}

function footer(page) {
  return `<div class="foot"><span>NEW EMPLOYMENT GROUP</span><span>城市伙伴 / 治理表达</span></div>`;
}

function image(page, cls = '') {
  return `<figure class="photo ${cls}"><img src="${page.image}" style="object-position:${page.pos || 'center 50%'}" alt=""></figure>`;
}

function renderPage(page, index) {
  if (page.mode === 'cover') {
    return `<section class="poster cover" id="${page.id}">
      ${topbar(page, index)}
      ${image(page, 'cover-img')}
      <div class="title-zone">
        <div class="eyebrow">${esc(page.subtitle)}</div>
        <h1 class="h-cover">${lines(page.title)}</h1>
      </div>
      ${quote(page.quote, 'cover-quote')}
      <div class="chip-row">${page.chips.map((c) => `<span>${esc(c)}</span>`).join('')}</div>
      ${footer(page)}
    </section>`;
  }

  if (page.mode === 'flow') {
    return `<section class="poster" id="${page.id}">
      ${topbar(page, index)}
      <h1 class="h-xl">${lines(page.title)}</h1>
      ${quote(page.quote)}
      <div class="flow3">${page.steps.map(([num, title, sub]) => `
        <div class="flow-item">
          <div class="flow-num">${esc(num)}</div>
          <div class="flow-title">${esc(title)}</div>
          <div class="flow-sub">${esc(sub)}</div>
        </div>`).join('')}</div>
      ${footer(page)}
    </section>`;
  }

  if (page.mode === 'matrix') {
    return `<section class="poster" id="${page.id}">
      ${topbar(page, index)}
      <h1 class="h-xl">${lines(page.title)}</h1>
      <p class="lead">${esc(page.kicker)}</p>
      <div class="matrix">${page.cells.map(([a, b]) => `
        <div class="matrix-cell"><span>${esc(a)}</span><strong>${esc(b)}</strong></div>`).join('')}</div>
      <div class="bottom-call">${esc(page.bottom)}</div>
      ${footer(page)}
    </section>`;
  }

  if (page.mode === 'photoQuote') {
    return `<section class="poster" id="${page.id}">
      ${topbar(page, index)}
      <h1 class="h-lg">${lines(page.title)}</h1>
      ${image(page)}
      ${quote(page.quote)}
      <div class="chip-row">${page.chips.map((c) => `<span>${esc(c)}</span>`).join('')}</div>
      ${footer(page)}
    </section>`;
  }

  if (page.mode === 'chain') {
    return `<section class="poster" id="${page.id}">
      ${topbar(page, index)}
      <h1 class="h-lg">${lines(page.title)}</h1>
      ${quote(page.quote)}
      <div class="chain">${page.steps.map(([title, desc], i) => `
        <div class="chain-row">
          <div class="chain-num">${String(i + 1).padStart(2, '0')}</div>
          <div class="chain-title">${esc(title)}</div>
          <div class="chain-desc">${esc(desc)}</div>
        </div>`).join('')}</div>
      ${footer(page)}
    </section>`;
  }

  if (page.mode === 'kpi') {
    return `<section class="poster" id="${page.id}">
      ${topbar(page, index)}
      <h1 class="h-lg">${lines(page.title)}</h1>
      ${quote(page.quote, 'small')}
      <div class="kpis">${page.stats.map(([num, lbl]) => `
        <div class="kpi"><div class="kpi-num">${esc(num)}</div><div class="kpi-label">${esc(lbl)}</div></div>`).join('')}</div>
      ${footer(page)}
    </section>`;
  }

  if (page.mode === 'imageMatrix') {
    return `<section class="poster" id="${page.id}">
      ${topbar(page, index)}
      <h1 class="h-lg">${lines(page.title)}</h1>
      ${image(page, 'short-img')}
      <p class="lead">${esc(page.kicker)}</p>
      <div class="service-grid">${page.cells.map(([a, b]) => `
        <div><strong>${esc(a)}</strong><span>${esc(b)}</span></div>`).join('')}</div>
      ${footer(page)}
    </section>`;
  }

  if (page.mode === 'roles') {
    return `<section class="poster" id="${page.id}">
      ${topbar(page, index)}
      <h1 class="h-lg">${lines(page.title)}</h1>
      ${quote(page.quote)}
      <div class="roles">${page.roles.map(([a, b]) => `
        <div class="role"><span>${esc(a)}</span><strong>${esc(b)}</strong></div>`).join('')}</div>
      ${footer(page)}
    </section>`;
  }

  if (page.mode === 'exam') {
    return `<section class="poster exam" id="${page.id}">
      ${topbar(page, index)}
      <h1 class="h-md">${lines(page.title)}</h1>
      ${quote(page.question, 'question')}
      <div class="point-strip">${page.points.map((p, i) => `<span><b>${String(i + 1).padStart(2, '0')}</b>${esc(p)}</span>`).join('')}</div>
      ${quote(page.answer, 'answer')}
      <div class="exam-logic">${page.logic.map((p, i) => `<div><span>${String(i + 1).padStart(2, '0')}</span><strong>${esc(p)}</strong></div>`).join('')}</div>
      ${footer(page)}
    </section>`;
  }

  if (page.mode === 'essay') {
    return `<section class="poster essay" id="${page.id}">
      ${topbar(page, index)}
      <h1 class="h-md">${lines(page.title)}</h1>
      ${quote(page.quote, 'long')}
      <div class="pillars">${page.pillars.map(([a, b]) => `
        <div><strong>${esc(a)}</strong><span>${esc(b)}</span></div>`).join('')}</div>
      <div class="essay-axis">${page.axis.map((p, i) => `<div><span>${String(i + 1).padStart(2, '0')}</span><strong>${esc(p)}</strong></div>`).join('')}</div>
      ${footer(page)}
    </section>`;
  }

  if (page.mode === 'closing') {
    return `<section class="poster closing" id="${page.id}">
      ${topbar(page, index)}
      <h1 class="h-xl">${lines(page.title)}</h1>
      ${quote(page.quote, 'closing-quote')}
      <div class="closing-steps">${page.steps.map((s, i) => `<div><span>${String(i + 1).padStart(2, '0')}</span><strong>${esc(s)}</strong></div>`).join('')}</div>
      ${footer(page)}
    </section>`;
  }

  if (page.mode === 'refs') {
    return `<section class="poster refs" id="${page.id}">
      ${topbar(page, index)}
      <h1 class="h-md">${esc(page.title)}</h1>
      <div class="refs-list">${page.refs.map((r, i) => `<div><span>${String(i + 1).padStart(2, '0')}</span><p>${esc(r)}</p></div>`).join('')}</div>
      ${footer(page)}
    </section>`;
  }
}

const css = `
  :root {
    --paper: #fafaf8;
    --ink: #090909;
    --muted: #707070;
    --line: #d6d6d2;
    --soft: #f0f0ed;
    --accent: #002FA7;
    --accent-on: #ffffff;
    --sans: "Inter", "Helvetica Neue", Helvetica, "Noto Sans SC", -apple-system, BlinkMacSystemFont, "PingFang SC", "Microsoft YaHei UI", sans-serif;
    --mono: "IBM Plex Mono", "SFMono-Regular", Consolas, monospace;
  }
  * { box-sizing: border-box; }
  html, body { margin: 0; padding: 0; }
  body { background: #191919; padding: 56px 0; font-family: var(--sans); color: var(--ink); }
  .sheet { display: flex; flex-direction: column; align-items: center; gap: 46px; }
  .poster {
    position: relative;
    width: 1080px;
    height: 1440px;
    padding: 76px 80px 64px;
    background:
      linear-gradient(rgba(9,9,9,.038) 1px, transparent 1px),
      linear-gradient(90deg, rgba(9,9,9,.038) 1px, transparent 1px),
      var(--paper);
    background-size: 64px 64px, 64px 64px, auto;
    display: flex;
    flex-direction: column;
    gap: 30px;
    overflow: hidden;
    isolation: isolate;
  }
  .poster::before {
    content: "";
    position: absolute;
    inset: 0 auto 0 0;
    width: 22px;
    background: var(--accent);
    z-index: 0;
  }
  .poster > * { position: relative; z-index: 1; }
  .topbar {
    display: flex;
    justify-content: space-between;
    align-items: center;
    border-bottom: 1px solid var(--line);
    padding-bottom: 20px;
    font-family: var(--mono);
    font-size: 19px;
    line-height: 1;
    letter-spacing: .17em;
    color: var(--muted);
    text-transform: uppercase;
  }
  .foot {
    margin-top: auto;
    border-top: 1px solid var(--line);
    padding-top: 20px;
    display: flex;
    justify-content: space-between;
    font-family: var(--mono);
    font-size: 17px;
    letter-spacing: .15em;
    color: var(--muted);
    text-transform: uppercase;
  }
  h1 { margin: 0; letter-spacing: 0; }
  .h-cover {
    font-weight: 200;
    font-size: 106px;
    line-height: 1.05;
  }
  .h-xl {
    font-weight: 200;
    font-size: 112px;
    line-height: 1.06;
  }
  .h-lg {
    font-weight: 200;
    font-size: 96px;
    line-height: 1.08;
  }
  .h-md {
    font-weight: 200;
    font-size: 82px;
    line-height: 1.1;
  }
  .eyebrow {
    font-family: var(--mono);
    font-size: 22px;
    letter-spacing: .16em;
    color: var(--accent);
    text-transform: uppercase;
    margin-bottom: 18px;
  }
  .quote {
    border-left: 10px solid var(--accent);
    background: rgba(240,240,237,.93);
    padding: 24px 28px;
    font-size: 31px;
    line-height: 1.45;
    font-weight: 550;
  }
  .quote.small { font-size: 28px; }
  .quote.long { font-size: 27px; line-height: 1.46; padding: 28px 30px; }
  .quote.question { font-size: 27px; line-height: 1.48; background: #fff; border: 1px solid var(--line); border-left: 10px solid var(--accent); }
  .quote.answer { font-size: 29px; background: var(--accent); color: var(--accent-on); border-left-color: var(--ink); }
  .quote.cover-quote { font-size: 29px; }
  .photo {
    width: 100%;
    height: 430px;
    border: 1px solid var(--line);
    background: var(--soft);
    margin: 0;
    overflow: hidden;
  }
  .photo img { width: 100%; height: 100%; object-fit: cover; display: block; }
  .cover-img { height: 470px; }
  .short-img { height: 330px; }
  .title-zone { margin-top: 4px; }
  .chip-row {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 14px;
  }
  .chip-row span {
    background: var(--accent);
    color: var(--accent-on);
    padding: 20px 18px 22px;
    text-align: center;
    font-size: 28px;
    font-weight: 650;
  }
  .flow3 { display: grid; grid-template-columns: 1fr; gap: 18px; margin-top: 8px; }
  .flow-item {
    display: grid;
    grid-template-columns: 116px 1fr;
    gap: 22px;
    align-items: center;
    border-bottom: 1px solid var(--line);
    padding: 26px 0;
  }
  .flow-num {
    font-family: var(--sans);
    font-size: 72px;
    font-weight: 200;
    color: var(--accent);
    line-height: 1;
  }
  .flow-title { font-size: 43px; font-weight: 650; line-height: 1.1; }
  .flow-sub { grid-column: 2; font-size: 26px; color: var(--muted); margin-top: -16px; }
  .lead {
    margin: 0;
    font-size: 31px;
    line-height: 1.45;
    color: var(--muted);
  }
  .matrix {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 16px;
  }
  .matrix-cell {
    min-height: 150px;
    border: 1px solid var(--line);
    background: rgba(250,250,248,.88);
    padding: 24px 26px;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
  }
  .matrix-cell span {
    font-family: var(--mono);
    font-size: 18px;
    letter-spacing: .14em;
    color: var(--muted);
    text-transform: uppercase;
  }
  .matrix-cell strong { font-size: 40px; }
  .bottom-call {
    background: var(--ink);
    color: #fff;
    padding: 30px 34px;
    font-size: 34px;
    line-height: 1.4;
    font-weight: 650;
  }
  .chain { display: flex; flex-direction: column; border-top: 1px solid var(--line); }
  .chain-row {
    display: grid;
    grid-template-columns: 92px 148px 1fr;
    gap: 22px;
    align-items: baseline;
    border-bottom: 1px solid var(--line);
    padding: 28px 0;
  }
  .chain-num { font-family: var(--mono); color: var(--accent); font-size: 24px; letter-spacing: .12em; }
  .chain-title { font-size: 37px; font-weight: 650; }
  .chain-desc { font-size: 27px; color: var(--muted); line-height: 1.35; }
  .kpis {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 18px;
    margin-top: 10px;
  }
  .kpi {
    min-height: 220px;
    background: #fff;
    border: 1px solid var(--line);
    padding: 28px;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
  }
  .kpi:nth-child(1) { background: var(--accent); color: var(--accent-on); border-color: var(--accent); }
  .kpi-num { font-size: 66px; line-height: 1; font-weight: 200; letter-spacing: -.02em; }
  .kpi-label { font-size: 27px; line-height: 1.35; font-weight: 560; color: currentColor; opacity: .82; }
  .service-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 16px;
  }
  .service-grid div {
    border: 1px solid var(--line);
    background: rgba(250,250,248,.9);
    padding: 24px 26px;
    min-height: 132px;
  }
  .service-grid strong { display: block; font-size: 34px; margin-bottom: 10px; }
  .service-grid span { font-size: 24px; line-height: 1.35; color: var(--muted); }
  .roles {
    display: flex;
    flex-direction: column;
    border-top: 1px solid var(--line);
  }
  .role {
    display: grid;
    grid-template-columns: 210px 1fr;
    gap: 24px;
    align-items: baseline;
    padding: 29px 0;
    border-bottom: 1px solid var(--line);
  }
  .role span {
    font-family: var(--mono);
    color: var(--accent);
    font-size: 22px;
    letter-spacing: .13em;
  }
  .role strong { font-size: 42px; }
  .point-strip {
    display: flex;
    flex-wrap: wrap;
    gap: 12px;
  }
  .point-strip span {
    padding: 16px 18px;
    border: 1px solid var(--line);
    background: rgba(250,250,248,.9);
    font-size: 26px;
    font-weight: 600;
  }
  .point-strip b {
    font-family: var(--mono);
    color: var(--accent);
    font-size: 18px;
    margin-right: 10px;
  }
  .exam-logic {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 16px;
  }
  .exam-logic div {
    min-height: 152px;
    padding: 22px 24px;
    background: rgba(250,250,248,.95);
    border: 1px solid var(--line);
    display: flex;
    flex-direction: column;
    justify-content: space-between;
  }
  .exam-logic span {
    font-family: var(--mono);
    font-size: 19px;
    letter-spacing: .13em;
    color: var(--accent);
  }
  .exam-logic strong {
    font-size: 34px;
    line-height: 1.15;
  }
  .pillars {
    display: grid;
    grid-template-columns: 1fr;
    gap: 14px;
  }
  .pillars div {
    display: grid;
    grid-template-columns: 210px 1fr;
    gap: 24px;
    background: #fff;
    border: 1px solid var(--line);
    padding: 22px 26px;
    align-items: baseline;
  }
  .pillars strong { font-size: 31px; color: var(--accent); }
  .pillars span { font-size: 27px; color: var(--muted); }
  .essay-axis {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 16px;
  }
  .essay-axis div {
    min-height: 210px;
    background: var(--accent);
    color: var(--accent-on);
    padding: 24px 26px;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
  }
  .essay-axis span {
    font-family: var(--mono);
    font-size: 20px;
    letter-spacing: .13em;
    opacity: .7;
  }
  .essay-axis strong {
    font-size: 42px;
    line-height: 1.1;
  }
  .closing .quote { font-size: 32px; }
  .closing-steps {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 16px;
  }
  .closing-steps div {
    min-height: 150px;
    background: var(--accent);
    color: var(--accent-on);
    padding: 24px 26px;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
  }
  .closing-steps span { font-family: var(--mono); font-size: 22px; letter-spacing: .15em; opacity: .7; }
  .closing-steps strong { font-size: 40px; }
  .refs-list {
    display: flex;
    flex-direction: column;
    border-top: 1px solid var(--line);
  }
  .refs-list div {
    display: grid;
    grid-template-columns: 64px 1fr;
    gap: 18px;
    padding: 22px 0;
    border-bottom: 1px solid var(--line);
  }
  .refs-list span {
    font-family: var(--mono);
    color: var(--accent);
    font-size: 22px;
    letter-spacing: .1em;
  }
  .refs-list p {
    margin: 0;
    font-size: 23px;
    line-height: 1.35;
  }
`;

const html = `<!doctype html>
<html lang="zh-CN" data-accent="ikb">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>新就业群体治理 · 小红书图文</title>
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

fs.mkdirSync(outDir, { recursive: true });
fs.writeFileSync(htmlPath, html);

const browser = await chromium.launch({ headless: true });
const page = await browser.newPage({ viewport: { width: 1280, height: 1600 }, deviceScaleFactor: 1 });
await page.goto(`file://${htmlPath}`, { waitUntil: 'load', timeout: 60000 });
await page.waitForTimeout(1200);

for (const item of pages) {
  await page.locator(`#${item.id}`).screenshot({
    path: path.join(outDir, item.file),
    animations: 'disabled',
  });
}

await browser.close();
console.log(`Rendered ${pages.length} images to ${outDir}`);
