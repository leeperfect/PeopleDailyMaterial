import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { chromium } from 'playwright';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const repoRoot = path.resolve(__dirname, '../../../..');
const mediaDir = path.join(repoRoot, 'media/images/2026-06-09-city-renewal-xhs-video');
const assetDir = path.join(mediaDir, 'assets');
const htmlPath = path.join(__dirname, 'index.html');

const rel = (file) => path.relative(__dirname, path.join(assetDir, file)).replaceAll(path.sep, '/');
const out = (file) => path.join(mediaDir, file);

const refs = [
  '龚相娟、姚雪青、郑洋洋：《当地铁与文物相遇（人民眼·历史文化保护传承）》，《人民日报》2026年5月15日第13版。',
  '窦皓：《最美上学路  成长新空间（奋进“十五五”·一线见闻）》，《人民日报》2026年5月17日第04版。',
  '陈震：《城市微改造，让文化味更浓（编辑手记）》，《人民日报》2026年5月17日第04版。',
  '李心萍：《地级及以上城市、县级市今年将全面开展城市体检》，《人民日报》2026年5月17日第04版。',
  '王云娜：《“一米视角”呵护成长（探访）》，《人民日报》2026年5月26日第07版。',
  '张广汉：《城市更新，兼顾民生改善与风貌保护（建言）》，《人民日报》2026年5月28日第18版。',
  '新华社：《国务院印发〈城市更新“十五五”规划〉》，《人民日报》2026年5月29日第01版。'
];

const pages = [
  {
    id: 'xhs-01-cover',
    no: '01',
    title: '城市更新\\n别急着拆',
    kicker: '人民日报这样写',
    quote: '城市更新别急着拆。先体检，找到真实问题；再保护，守住文脉底线；再服务，把人的日常体验补上。',
    chips: ['先体检', '再保护', '再服务'],
    image: 'urban-street-crossing.jpg',
    layout: 'cover',
    tone: 'graphite'
  },
  {
    id: 'xhs-02-high-score',
    no: '02',
    title: '高分写法\\n不看工程量',
    kicker: '破题',
    quote: '城市更新的高分写法，不是拆了多少、建了多少，而是发现了什么问题，守住了什么文脉，改善了谁的生活。',
    chips: ['发现问题', '守住文脉', '改善生活'],
    layout: 'triad',
    tone: 'stone'
  },
  {
    id: 'xhs-03-checkup-first',
    no: '03',
    title: '第一步\\n先体检',
    kicker: '问题导向',
    quote: '先体检后更新、无体检不更新。',
    chips: ['住房', '小区', '街区', '城区'],
    layout: 'imperative',
    tone: 'slate'
  },
  {
    id: 'xhs-04-feeling-to-list',
    no: '04',
    title: '把群众感受\\n变成清单',
    kicker: '体检的意义',
    quote: '城市体检不是为了证明城市有问题，而是为了把群众的感受变成更新的清单。',
    chips: ['急难愁盼', '安全隐患', '服务短板', '治理堵点'],
    layout: 'funnel',
    tone: 'warm'
  },
  {
    id: 'xhs-05-problem-chain',
    no: '05',
    title: '体检之后\\n才开方',
    kicker: '申论表达',
    quote: '推进城市更新，要坚持先体检后更新，把住房、小区、街区、城区中的安全隐患、服务短板和群众急难愁盼问题找准，再把问题清单转化为项目清单、责任清单和效果清单。',
    chips: ['问题清单', '项目清单', '责任清单', '效果清单'],
    layout: 'layers',
    tone: 'graphite'
  },
  {
    id: 'xhs-06-memory-visible',
    no: '06',
    title: '更新不是\\n覆盖旧记忆',
    kicker: '文脉保护',
    quote: '城市更新不是让新建筑覆盖旧记忆，而是让旧文脉在新空间里继续被看见。',
    chips: ['遗址入站厅', '街巷留肌理', '文物进日常'],
    image: 'historic-street.jpg',
    layout: 'photoQuote',
    tone: 'slate'
  },
  {
    id: 'xhs-07-balance',
    no: '07',
    title: '保护与改善\\n不是二选一',
    kicker: '边界',
    quote: '城市更新不能以保护为名忽视民生，也不能以改善民生为名切断文脉。',
    chips: ['保护第一', '民生改善', '机制平衡'],
    layout: 'balance',
    tone: 'stone'
  },
  {
    id: 'xhs-08-rulebook',
    no: '08',
    title: '把文脉\\n写进规则',
    kicker: '申论表达',
    quote: '推进城市更新，要坚持保护第一、应保尽保、以用促保，把文物保护、街区风貌、原住居民和生活场景纳入更新规则，通过微更新、可逆式改造、居民共治和精细化管理，实现民生改善与文脉延续相统一。',
    chips: ['微更新', '可逆式改造', '居民共治', '精细化管理'],
    image: 'old-town-walkway.jpg',
    layout: 'rulebook',
    tone: 'warm'
  },
  {
    id: 'xhs-09-road-life',
    no: '09',
    title: '好更新\\n不只把路修平',
    kicker: '服务体验',
    quote: '好的城市更新，不是只让路更平，而是让路上的生活更丰富。',
    chips: ['通行安全', '等候空间', '文化长廊', '自然角'],
    image: 'school-street-children.jpg',
    layout: 'photoService',
    tone: 'graphite'
  },
  {
    id: 'xhs-10-one-meter',
    no: '10',
    title: '用一米视角\\n重新看城市',
    kicker: '儿童友好',
    quote: '城市更新的温度，往往藏在最小的使用者身上。',
    chips: ['出行安全', '心理服务', '参与赋能'],
    layout: 'oneMeter',
    tone: 'mist'
  },
  {
    id: 'xhs-11-life-radius',
    no: '11',
    title: '成果要进入\\n生活半径',
    kicker: '服务谁',
    quote: '推进城市更新，要把群众体验作为治理尺度，围绕儿童、居民、游客等不同群体的日常需求，完善出行、教育、文化、心理、休闲和参与机制，让更新成果真正进入生活半径。',
    chips: ['儿童', '居民', '游客', '治理'],
    image: 'urban-public-space.jpg',
    layout: 'audienceMap',
    tone: 'stone'
  },
  {
    id: 'xhs-12-exam-chain',
    no: '12',
    title: '考场总公式\\n直接记',
    kicker: '方法链',
    quote: '以城市体检发现问题，以文脉保护守住底线，以公共服务改善体验，以群众参与校准尺度。',
    chips: ['发现问题', '守住底线', '改善体验', '校准尺度'],
    layout: 'chain',
    tone: 'slate'
  },
  {
    id: 'xhs-13-interview',
    no: '13',
    title: '面试题\\n这样转化',
    kicker: '题目原型',
    quote: '某老城区准备开展城市更新，居民希望改善居住条件，但也担心历史风貌被破坏、儿童活动空间不足、游客体验同质化。领导让你参与前期调研和方案设计，你会怎么做？',
    chips: ['做体检', '划底线', '共同设计', '分类微改', '回访评估'],
    layout: 'question',
    tone: 'warm'
  },
  {
    id: 'xhs-14-governance',
    no: '14',
    title: '不是工程突击\\n是持续治理',
    kicker: '收束',
    quote: '城市更新不是一次工程突击，而是一套从发现问题、守住底线到改善体验的持续治理方法。',
    chips: ['发现问题', '守住底线', '改善体验', '持续治理'],
    layout: 'lifecycle',
    tone: 'graphite'
  },
  {
    id: 'xhs-15-final',
    no: '15',
    title: '关键词\\n不是“拆”',
    kicker: '一句话带走',
    quote: '城市更新的关键词，不是“拆”，而是“人”；不是急着换新，而是先诊断问题、守住记忆、服务生活。',
    chips: ['诊断问题', '守住记忆', '服务生活'],
    image: 'city-building-facade.jpg',
    layout: 'close',
    tone: 'mist'
  }
];

const tones = {
  graphite: { bg: '#e3e5e5', panel: '#f6f6f3', ink: '#111315', muted: '#6e7376', line: '#22272a', accent: '#c44d3f', soft: '#d1d4d4' },
  slate: { bg: '#dfe3e4', panel: '#f7f7f4', ink: '#101418', muted: '#687178', line: '#273038', accent: '#53616b', soft: '#cbd1d4' },
  stone: { bg: '#e7e5df', panel: '#f8f7f2', ink: '#171512', muted: '#746f67', line: '#2a2823', accent: '#9a8a72', soft: '#d8d4ca' },
  warm: { bg: '#e4e1dc', panel: '#faf8f2', ink: '#171513', muted: '#746d65', line: '#2b2925', accent: '#a85643', soft: '#d8d1c8' },
  mist: { bg: '#dde2df', panel: '#f7f8f4', ink: '#111716', muted: '#68736f', line: '#25302d', accent: '#60766f', soft: '#cbd5d0' }
};

const photoMeta = {
  'urban-street-crossing.jpg': {
    pos: 'center 52%',
    map: 'old urban street recedes through center; darker buildings sit right; left sky and lower-left road are the safest zones for type.'
  },
  'historic-street.jpg': {
    pos: 'center 52%',
    map: 'historic residential facades fill the middle; the lower-left edge is textured but non-critical; avoid covering central balconies and street depth.'
  },
  'old-town-walkway.jpg': {
    pos: 'center 50%',
    map: 'old-town passage runs vertically through center; keep captions in a separate panel and crop to preserve the walking line.'
  },
  'school-street-children.jpg': {
    pos: 'center 48%',
    map: 'children occupy center-right of the horizontal frame; this card uses a separate photo well so no title covers faces or bodies.'
  },
  'urban-public-space.jpg': {
    pos: 'center 54%',
    map: 'public-space architecture fills the vertical frame; photo is evidence area only, with text outside the image well.'
  },
  'city-building-facade.jpg': {
    pos: 'center 52%',
    map: 'building facade is a repeated texture with strongest lines in the center; text is placed in a separate editorial slab.'
  }
};

function vars(tone) {
  const t = tones[tone] || tones.graphite;
  return Object.entries(t).map(([k, v]) => `--${k}:${v}`).join(';');
}

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

function quoteClass(quote) {
  if (quote.length > 120) return 'q xs';
  if (quote.length > 88) return 'q sm';
  if (quote.length > 56) return 'q md';
  return 'q';
}

function chipsHtml(chips = []) {
  return `<div class="chips">${chips.map((chip, i) => `<span><b>${String(i + 1).padStart(2, '0')}</b>${escapeHtml(chip)}</span>`).join('')}</div>`;
}

function topbar(page) {
  return `<div class="topbar"><span>${page.no}</span><span>${escapeHtml(page.kicker)}</span></div>`;
}

function quote(page) {
  return `<blockquote class="${quoteClass(page.quote)}">${escapeHtml(page.quote)}</blockquote>`;
}

function photo(file, cls = '') {
  const meta = photoMeta[file] || { pos: 'center 50%', map: 'image subject is centered; text sits outside the photo.' };
  return `<figure class="photo ${cls}">
    <!-- Subject map: ${meta.map} -->
    <img src="${rel(file)}" alt="" style="object-position:${meta.pos};">
  </figure>`;
}

function renderPage(page) {
  const style = vars(page.tone);
  if (page.layout === 'cover') {
    return `<section class="poster xhs cover" id="${page.id}" style="${style}">
      ${photo(page.image, 'bleed')}
      <div class="cover-tint"></div><div class="grid"></div>
      <div class="content">
        ${topbar(page)}
        <p class="eyebrow">城市更新 / Urban Renewal</p>
        <h1>${titleHtml(page.title)}</h1>
        ${quote(page)}
        <div class="cover-chain">${page.chips.map((x) => `<span>${escapeHtml(x)}</span>`).join('')}</div>
      </div>
    </section>`;
  }
  if (page.layout === 'triad') {
    return `<section class="poster xhs triad" id="${page.id}" style="${style}">
      <div class="grid"></div><div class="content">
        ${topbar(page)}<h1>${titleHtml(page.title)}</h1>${quote(page)}
        <div class="three-panels">${page.chips.map((x, i) => `<div><b>${String(i + 1).padStart(2, '0')}</b><strong>${escapeHtml(x)}</strong><em>${['为什么改', '什么不能乱改', '改完谁更好'][i]}</em></div>`).join('')}</div>
      </div>
    </section>`;
  }
  if (page.layout === 'imperative') {
    return `<section class="poster xhs imperative" id="${page.id}" style="${style}">
      <div class="grid"></div><div class="content">
        ${topbar(page)}<h1>${titleHtml(page.title)}</h1>
        <div class="mega-rule"><span>无体检</span><i></i><span>不更新</span></div>
        ${quote(page)}
        <div class="layer-list">${page.chips.map((x) => `<span>${escapeHtml(x)}</span>`).join('')}</div>
      </div>
    </section>`;
  }
  if (page.layout === 'funnel') {
    return `<section class="poster xhs funnel" id="${page.id}" style="${style}">
      <div class="grid"></div><div class="content">
        ${topbar(page)}<h1>${titleHtml(page.title)}</h1>${quote(page)}
        <div class="funnel-shape">
          <span>群众感受</span><span>调查与数据</span><span>问题清单</span><span>更新项目</span>
        </div>
        ${chipsHtml(page.chips)}
      </div>
    </section>`;
  }
  if (page.layout === 'layers') {
    return `<section class="poster xhs layers" id="${page.id}" style="${style}">
      <div class="grid"></div><div class="content">
        ${topbar(page)}<h1>${titleHtml(page.title)}</h1>${quote(page)}
        <div class="stack">
          ${['住房：安全隐患', '小区：服务短板', '街区：风貌秩序', '城区：运行韧性'].map((x, i) => `<div><b>${String(i + 1).padStart(2, '0')}</b>${escapeHtml(x)}</div>`).join('')}
        </div>
        <div class="list-flow">${page.chips.map((x) => `<span>${escapeHtml(x)}</span>`).join('')}</div>
      </div>
    </section>`;
  }
  if (page.layout === 'photoQuote') {
    return `<section class="poster xhs photo-quote" id="${page.id}" style="${style}">
      <div class="grid"></div>${photo(page.image, 'side')}
      <div class="content">
        ${topbar(page)}<h1>${titleHtml(page.title)}</h1>${quote(page)}
        ${chipsHtml(page.chips)}
      </div>
    </section>`;
  }
  if (page.layout === 'balance') {
    return `<section class="poster xhs balance" id="${page.id}" style="${style}">
      <div class="grid"></div><div class="content">
        ${topbar(page)}<h1>${titleHtml(page.title)}</h1>${quote(page)}
        <div class="balance-scale">
          <div><span>保护</span><small>文物 / 街区 / 风貌 / 生活场景</small></div>
          <i></i>
          <div><span>改善</span><small>居住 / 服务 / 安全 / 公共空间</small></div>
        </div>
        ${chipsHtml(page.chips)}
      </div>
    </section>`;
  }
  if (page.layout === 'rulebook') {
    return `<section class="poster xhs rulebook" id="${page.id}" style="${style}">
      <div class="grid"></div>${photo(page.image, 'small')}
      <div class="content">
        ${topbar(page)}<h1>${titleHtml(page.title)}</h1>${quote(page)}
        <div class="rule-grid">${page.chips.map((x, i) => `<span><b>${String(i + 1).padStart(2, '0')}</b>${escapeHtml(x)}</span>`).join('')}</div>
      </div>
    </section>`;
  }
  if (page.layout === 'photoService') {
    return `<section class="poster xhs photo-service" id="${page.id}" style="${style}">
      <div class="grid"></div>${photo(page.image, 'wide')}
      <div class="content">
        ${topbar(page)}<h1>${titleHtml(page.title)}</h1>${quote(page)}
        <div class="service-grid">${page.chips.map((x) => `<span>${escapeHtml(x)}</span>`).join('')}</div>
      </div>
    </section>`;
  }
  if (page.layout === 'oneMeter') {
    return `<section class="poster xhs one-meter" id="${page.id}" style="${style}">
      <div class="grid"></div><div class="content">
        ${topbar(page)}<h1>${titleHtml(page.title)}</h1>${quote(page)}
        <div class="meter-visual">
          <b>1m</b><span>儿童视角</span><i></i><em>道路 / 街角 / 公园 / 学校 / 社区</em>
        </div>
        ${chipsHtml(page.chips)}
      </div>
    </section>`;
  }
  if (page.layout === 'audienceMap') {
    return `<section class="poster xhs audience" id="${page.id}" style="${style}">
      <div class="grid"></div>${photo(page.image, 'strip')}
      <div class="content">
        ${topbar(page)}<h1>${titleHtml(page.title)}</h1>${quote(page)}
        <div class="audience-map">${page.chips.map((x) => `<span>${escapeHtml(x)}</span>`).join('')}</div>
      </div>
    </section>`;
  }
  if (page.layout === 'chain') {
    return `<section class="poster xhs chain" id="${page.id}" style="${style}">
      <div class="grid"></div><div class="content">
        ${topbar(page)}<h1>${titleHtml(page.title)}</h1>${quote(page)}
        <div class="chain-steps">${page.chips.map((x, i) => `<span><b>${String(i + 1).padStart(2, '0')}</b>${escapeHtml(x)}</span>`).join('')}</div>
      </div>
    </section>`;
  }
  if (page.layout === 'question') {
    return `<section class="poster xhs question" id="${page.id}" style="${style}">
      <div class="grid"></div><div class="content">
        ${topbar(page)}<h1>${titleHtml(page.title)}</h1>${quote(page)}
        <div class="answer-ladder">${page.chips.map((x, i) => `<span><b>${String(i + 1).padStart(2, '0')}</b>${escapeHtml(x)}</span>`).join('')}</div>
      </div>
    </section>`;
  }
  if (page.layout === 'lifecycle') {
    return `<section class="poster xhs lifecycle" id="${page.id}" style="${style}">
      <div class="grid"></div><div class="content">
        ${topbar(page)}<h1>${titleHtml(page.title)}</h1>${quote(page)}
        <div class="loop">${page.chips.map((x) => `<span>${escapeHtml(x)}</span>`).join('')}</div>
      </div>
    </section>`;
  }
  if (page.layout === 'close') {
    return `<section class="poster xhs close" id="${page.id}" style="${style}">
      <div class="grid"></div>${photo(page.image, 'close-photo')}
      <div class="content">
        ${topbar(page)}<h1>${titleHtml(page.title)}</h1>${quote(page)}
        <div class="not-word"><span>不是拆</span><b>是人</b></div>
      </div>
    </section>`;
  }
  return '';
}

function renderRefs() {
  return `<section class="poster xhs refs" id="xhs-16-references" style="${vars('stone')}">
    <div class="grid"></div><div class="content">
      <div class="topbar"><span>16</span><span>References</span></div>
      <h1>参考文章</h1>
      <ol>${refs.map((r) => `<li>${escapeHtml(r)}</li>`).join('')}</ol>
    </div>
  </section>`;
}

function renderVideoCover(id, file, title, subtitle, variant) {
  const meta = photoMeta[file];
  const cls = variant === 2 ? 'cover-v2' : 'cover-v1';
  return `<section class="poster video ${cls}" id="${id}" style="${vars(variant === 2 ? 'warm' : 'graphite')}">
    <figure class="video-photo">
      <!-- Subject map: ${meta.map} Text block sits in lower-left safe zone, away from the primary street/building depth. -->
      <img src="${rel(file)}" alt="" style="object-position:${meta.pos};">
    </figure>
    <div class="video-tint"></div>
    <div class="mag-lines"></div>
    <div class="video-title">
      <p>《人民日报》这样写</p>
      <h2>${titleHtml(title)}</h2>
      <span>${escapeHtml(subtitle)}</span>
    </div>
  </section>`;
}

const videoCovers = [
  renderVideoCover('video-cover-01', 'urban-street-crossing.jpg', '城市更新\\n别急着拆', '先体检 / 再保护 / 再服务', 1),
  renderVideoCover('video-cover-02', 'historic-street.jpg', '不是“拆”\\n而是“人”', '城市更新的申论写法', 2)
];

const posters = [...pages.map(renderPage), renderRefs(), ...videoCovers].join('\n');

const css = `
*{box-sizing:border-box}html,body{margin:0;padding:0}body{background:#cfd3d4;font-family:"Inter","Helvetica Neue","Avenir Next","PingFang SC","Noto Sans SC","Microsoft YaHei",sans-serif;color:#111315}.stage{width:max-content;display:grid;gap:34px;padding:34px}.poster{position:relative;overflow:hidden;isolation:isolate;background:var(--bg);color:var(--ink)}.xhs,.video{width:1080px;height:1440px}.grid{position:absolute;inset:0;z-index:0;background:linear-gradient(90deg,rgba(20,24,28,.07) 1px,transparent 1px),linear-gradient(180deg,rgba(20,24,28,.07) 1px,transparent 1px);background-size:90px 90px}.content{position:relative;z-index:5;height:100%;padding:60px;display:flex;flex-direction:column}.topbar{display:flex;align-items:center;justify-content:space-between;gap:28px;border-bottom:2px solid rgba(17,19,21,.28);padding-bottom:22px;font-size:24px;line-height:1;font-weight:760;text-transform:uppercase}.topbar span:first-child{font-size:34px;font-weight:860;color:var(--accent)}h1{margin:34px 0 0;font-size:86px;line-height:1.03;font-weight:520;letter-spacing:0}.eyebrow{margin:38px 0 0;font-size:24px;line-height:1;font-weight:800;color:var(--muted);text-transform:uppercase}.q{margin:34px 0 0;padding:30px 32px;border-left:10px solid var(--accent);background:rgba(248,248,244,.82);font-size:39px;line-height:1.35;font-weight:760;letter-spacing:0}.q.md{font-size:34px}.q.sm{font-size:29px;line-height:1.35}.q.xs{font-size:26px;line-height:1.34}.chips{margin-top:auto;display:grid;grid-template-columns:repeat(2,1fr);gap:16px}.chips span{min-height:118px;padding:20px 22px;display:grid;align-content:space-between;background:rgba(248,248,244,.7);border:2px solid rgba(17,19,21,.16);font-size:28px;line-height:1.12;font-weight:820}.chips b{display:block;margin-bottom:16px;color:var(--accent);font-size:22px}.photo{margin:0;overflow:hidden}.photo img,.video-photo img{width:100%;height:100%;object-fit:cover;filter:grayscale(.18) saturate(.72) contrast(1.06) brightness(.95)}.bleed{position:absolute;inset:0;z-index:1}.cover .cover-tint{position:absolute;inset:0;z-index:2;background:linear-gradient(180deg,rgba(227,229,229,.94),rgba(227,229,229,.82) 45%,rgba(227,229,229,.28)),linear-gradient(90deg,rgba(227,229,229,.96),rgba(227,229,229,.28) 72%)}.cover .grid{z-index:3}.cover .content{z-index:4}.cover h1{font-size:104px;line-height:.98;font-weight:480}.cover .q{max-width:850px;background:rgba(246,246,243,.8);font-size:35px}.cover-chain{margin-top:auto;display:grid;grid-template-columns:repeat(3,1fr);gap:12px}.cover-chain span{min-height:178px;display:grid;place-items:center;background:rgba(17,19,21,.88);color:#f7f7f4;font-size:38px;font-weight:780}.three-panels{margin-top:auto;display:grid;grid-template-columns:repeat(3,1fr);gap:14px}.three-panels div{min-height:500px;padding:28px 22px;display:flex;flex-direction:column;justify-content:space-between;background:var(--panel);border-top:18px solid var(--accent)}.three-panels b{font-size:28px;color:var(--muted)}.three-panels strong{font-size:44px;line-height:1.05;font-weight:760}.three-panels em{font-style:normal;font-size:24px;color:var(--muted);font-weight:760}.mega-rule{margin:72px 0 44px;display:grid;grid-template-columns:1fr 112px 1fr;align-items:center;gap:24px}.mega-rule span{height:300px;display:grid;place-items:center;background:var(--line);color:#f7f7f4;font-size:56px;font-weight:800}.mega-rule i{height:6px;background:var(--accent);position:relative}.mega-rule i:after{content:"";position:absolute;right:-2px;top:50%;width:28px;height:28px;border-top:6px solid var(--accent);border-right:6px solid var(--accent);transform:translateY(-50%) rotate(45deg)}.layer-list{margin-top:auto;display:grid;grid-template-columns:repeat(4,1fr);gap:12px}.layer-list span{height:210px;display:grid;place-items:center;text-align:center;background:var(--panel);border:2px solid rgba(17,19,21,.18);font-size:34px;font-weight:780}.funnel-shape{margin:50px 0 24px;display:grid;gap:12px}.funnel-shape span{height:104px;display:grid;place-items:center;background:var(--line);color:#fff;font-size:34px;font-weight:800}.funnel-shape span:nth-child(1){margin:0 0}.funnel-shape span:nth-child(2){margin:0 60px;background:var(--accent)}.funnel-shape span:nth-child(3){margin:0 132px}.funnel-shape span:nth-child(4){margin:0 220px;background:var(--accent)}.stack{margin-top:36px;display:grid;gap:14px}.stack div{height:108px;padding:0 28px;display:flex;align-items:center;gap:24px;background:var(--panel);border-left:12px solid var(--accent);font-size:32px;font-weight:780}.stack b{font-size:26px;color:var(--muted)}.list-flow{margin-top:auto;display:grid;grid-template-columns:repeat(4,1fr);gap:10px}.list-flow span{min-height:170px;display:grid;place-items:center;text-align:center;background:var(--line);color:#fff;font-size:31px;font-weight:800}.photo-quote .side{position:absolute;left:60px;right:60px;bottom:60px;height:510px;z-index:1;border:3px solid rgba(17,19,21,.22)}.photo-quote .content{padding-bottom:610px}.photo-quote .chips{position:absolute;left:60px;right:60px;bottom:588px;grid-template-columns:repeat(3,1fr)}.balance-scale{margin:60px 0 36px;display:grid;grid-template-columns:1fr 90px 1fr;align-items:center;gap:20px}.balance-scale div{height:420px;padding:34px;display:grid;align-content:space-between;background:var(--panel);border:2px solid rgba(17,19,21,.18)}.balance-scale span{font-size:60px;font-weight:760}.balance-scale small{font-size:26px;line-height:1.3;color:var(--muted);font-weight:760}.balance-scale i{height:6px;background:var(--accent)}.rulebook .small{position:absolute;left:60px;right:60px;bottom:60px;height:392px;border:3px solid rgba(17,19,21,.18);z-index:1}.rulebook .content{padding-bottom:500px}.rule-grid{position:absolute;left:60px;right:60px;bottom:476px;display:grid;grid-template-columns:repeat(4,1fr);gap:12px}.rule-grid span{height:150px;padding:18px 14px;display:grid;align-content:space-between;background:var(--line);color:#fff;font-size:27px;line-height:1.08;font-weight:800}.rule-grid b{color:rgba(255,255,255,.64);font-size:21px}.photo-service .wide{position:absolute;left:60px;right:60px;top:468px;height:450px;z-index:1;border:3px solid rgba(17,19,21,.18)}.photo-service .content{padding-bottom:60px}.photo-service .q{margin-top:516px}.service-grid{margin-top:auto;display:grid;grid-template-columns:repeat(4,1fr);gap:12px}.service-grid span{height:170px;display:grid;place-items:center;text-align:center;background:var(--panel);border:2px solid rgba(17,19,21,.18);font-size:29px;font-weight:800}.meter-visual{margin:54px 0 36px;min-height:500px;display:grid;grid-template-columns:280px 1fr;grid-template-rows:1fr 120px;gap:16px}.meter-visual b{grid-row:1/3;display:grid;place-items:center;background:var(--line);color:#fff;font-size:122px;font-weight:460}.meter-visual span{display:grid;place-items:center;background:var(--panel);font-size:56px;font-weight:760}.meter-visual i{background:repeating-linear-gradient(90deg,var(--accent) 0 8px,transparent 8px 28px);height:16px;align-self:center}.meter-visual em{grid-column:2;font-style:normal;background:var(--panel);display:grid;place-items:center;padding:20px;text-align:center;font-size:28px;line-height:1.2;font-weight:780;color:var(--muted)}.audience .strip{position:absolute;left:60px;right:60px;bottom:60px;height:330px;border:3px solid rgba(17,19,21,.18);z-index:1}.audience .content{padding-bottom:488px}.audience-map{position:absolute;left:60px;right:60px;bottom:418px;display:grid;grid-template-columns:repeat(4,1fr);gap:12px}.audience-map span{height:160px;display:grid;place-items:center;background:var(--line);color:#fff;font-size:36px;font-weight:780}.chain-steps{margin-top:auto;display:grid;grid-template-columns:repeat(4,1fr);gap:14px}.chain-steps span{position:relative;min-height:560px;padding:28px 18px;display:grid;align-content:center;justify-items:center;text-align:center;background:var(--panel);border:2px solid rgba(17,19,21,.18);font-size:42px;line-height:1.04;font-weight:780}.chain-steps span:not(:last-child):after{content:"";position:absolute;right:-24px;top:50%;width:34px;height:4px;background:var(--accent);z-index:3}.chain-steps b{display:block;margin-bottom:28px;font-size:28px;color:var(--accent)}.question .q{font-size:28px}.answer-ladder{margin-top:30px;display:grid;gap:12px}.answer-ladder span{height:104px;padding:0 26px;display:flex;align-items:center;gap:20px;background:var(--panel);border-left:12px solid var(--accent);font-size:31px;font-weight:820}.answer-ladder b{font-size:24px;color:var(--muted)}.loop{margin-top:auto;display:grid;grid-template-columns:repeat(2,1fr);gap:18px}.loop span{height:330px;display:grid;place-items:center;text-align:center;background:var(--line);color:#fff;font-size:46px;font-weight:760}.loop span:nth-child(2),.loop span:nth-child(3){background:var(--accent)}.close .close-photo{position:absolute;left:60px;right:60px;bottom:60px;height:420px;border:3px solid rgba(17,19,21,.18);z-index:1}.close .content{padding-bottom:550px}.close h1{font-size:96px}.close .q{font-size:33px}.not-word{margin-top:38px;display:grid;grid-template-columns:1fr 1fr;gap:14px}.not-word span,.not-word b{height:220px;display:grid;place-items:center;background:var(--panel);font-size:52px;font-weight:740}.not-word b{background:var(--line);color:#fff}.refs h1{font-size:94px}.refs ol{margin:50px 0 0;padding-left:38px;display:grid;gap:20px;font-size:25px;line-height:1.34;font-weight:720}.refs li::marker{color:var(--accent);font-weight:900}.video-photo{position:absolute;inset:0;margin:0;z-index:1}.video-photo img{filter:grayscale(.08) saturate(.74) contrast(1.1) brightness(.82)}.video-tint{position:absolute;inset:0;z-index:2;background:linear-gradient(180deg,rgba(0,0,0,.08),rgba(0,0,0,.22) 48%,rgba(0,0,0,.56)),linear-gradient(90deg,rgba(0,0,0,.58),rgba(0,0,0,.10) 64%)}.mag-lines{position:absolute;inset:54px;z-index:3;border-top:2px solid rgba(255,255,255,.68);border-bottom:2px solid rgba(255,255,255,.42)}.mag-lines:before{content:"";position:absolute;left:0;top:92px;width:190px;height:2px;background:rgba(255,255,255,.62)}.video-title{position:absolute;left:64px;right:110px;bottom:98px;z-index:4;color:#f8f5ec}.video-title p{margin:0 0 26px;font-size:31px;line-height:1;font-weight:820;letter-spacing:0}.video-title h2{margin:0;font-family:"Songti SC","STSong","Noto Serif CJK SC",serif;font-size:112px;line-height:.98;font-weight:700;letter-spacing:0}.video-title span{display:block;width:max-content;max-width:760px;margin-top:28px;padding:14px 18px;background:#f8f5ec;color:#151515;font-size:31px;font-weight:860}.cover-v2 .video-photo img{filter:grayscale(.02) saturate(.82) contrast(1.05) brightness(.86)}.cover-v2 .video-tint{background:linear-gradient(180deg,rgba(0,0,0,.03),rgba(0,0,0,.12) 44%,rgba(0,0,0,.60)),linear-gradient(90deg,rgba(0,0,0,.50),rgba(0,0,0,.04) 62%)}.cover-v2 .video-title h2{font-size:104px}.cover-v2 .video-title{bottom:104px;right:120px}.preview{width:1800px;background:#e6e7e7;padding:34px;display:grid;grid-template-columns:repeat(6,1fr);gap:18px}.preview figure{margin:0;background:#fff;padding:8px}.preview img{width:100%;display:block}.preview figcaption{padding:8px 2px 0;font-size:16px;font-weight:700;color:#303436}
`;

const html = `<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>城市更新小红书与视频号封面</title><style>${css}</style></head><body><main class="stage">${posters}</main></body></html>`;

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
await page.locator('#xhs-16-references').screenshot({ path: out('xhs-16-references.png') });
outputFiles.push('xhs-16-references.png');
await page.locator('#video-cover-01').screenshot({ path: out('video-cover-01.png') });
await page.locator('#video-cover-02').screenshot({ path: out('video-cover-02.png') });
outputFiles.push('video-cover-01.png', 'video-cover-02.png');

const previewHtml = `<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><style>${css}</style></head><body><section class="preview">${outputFiles.map((file) => `<figure><img src="${path.relative(__dirname, out(file)).replaceAll(path.sep, '/')}" alt=""><figcaption>${file}</figcaption></figure>`).join('')}</section></body></html>`;
const previewPath = path.join(__dirname, 'preview.html');
fs.writeFileSync(previewPath, previewHtml, 'utf8');
await page.setViewportSize({ width: 1900, height: 1400 });
await page.goto(`file://${previewPath}`, { waitUntil: 'networkidle' });
await page.locator('.preview').screenshot({ path: out('preview-grid.png') });
outputFiles.push('preview-grid.png');

await browser.close();

console.log(JSON.stringify({
  mediaDir,
  count: outputFiles.length,
  files: outputFiles
}, null, 2));
