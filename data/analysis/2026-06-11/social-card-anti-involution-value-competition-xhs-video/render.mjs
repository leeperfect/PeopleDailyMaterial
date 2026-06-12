import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { chromium } from 'playwright';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const repoRoot = path.resolve(__dirname, '../../../..');
const mediaDir = path.join(repoRoot, 'media/images/2026-06-11-anti-involution-value-competition-xhs-video');
const assetDir = path.join(mediaDir, 'assets');
const htmlPath = path.join(__dirname, 'index.html');

const out = (file) => path.join(mediaDir, file);
const rel = (file) => path.relative(__dirname, path.join(assetDir, file)).replaceAll(path.sep, '/');

const pages = [
  {
    id: 'xhs-01-cover',
    no: '01',
    tag: '价值竞争',
    title: '反内卷\\n不是反竞争',
    quote: '人民日报讲的是：让竞争回到价值创造',
    points: ['低价低质', '创新', '质量', '服务'],
    image: 'open-road-track.jpg',
    layout: 'cover'
  },
  {
    id: 'xhs-02-mistake',
    no: '02',
    tag: '常见误区',
    title: '很多人\\n把“反内卷”写错了',
    quote: '反内卷不是反竞争，而是纠偏跑歪的竞争。',
    points: ['不让降价', '不让竞争', '保护企业', '只靠监管'],
    layout: 'mistake'
  },
  {
    id: 'xhs-03-mainline',
    no: '03',
    tag: '核心公式',
    title: '记住\\n这条主线',
    quote: '反低水平内耗，立价值创造竞争。',
    points: ['反什么', '靠什么反', '立什么'],
    layout: 'mainline'
  },
  {
    id: 'xhs-04-low-price',
    no: '04',
    tag: '反什么 01',
    title: '第一\\n反低价低质',
    quote: '能带来更好产品的降价是竞争，牺牲质量换来的低价是内耗。',
    points: ['偷工减料', '压缩质量', '牺牲安全', '伤害长期竞争力'],
    image: 'market-shelves.jpg',
    layout: 'photo'
  },
  {
    id: 'xhs-05-platform',
    no: '05',
    tag: '反什么 02',
    title: '第二\\n反平台规则滥用',
    quote: '规则便利不能变成规则伤害。',
    points: ['全网最低价', '调价助手', '恶意仅退款', '成本转嫁'],
    image: 'logistics-warehouse.jpg',
    layout: 'panelPhoto'
  },
  {
    id: 'xhs-06-same',
    no: '06',
    tag: '反什么 03',
    title: '第三\\n反同质化内耗',
    quote: '没有创新增量，价格战就容易变成消耗战。',
    points: ['创新不足', '产品同质', '服务相似', '越卷越亏'],
    image: 'freight-containers.jpg',
    layout: 'photo'
  },
  {
    id: 'xhs-07-law',
    no: '07',
    tag: '靠什么反 01',
    title: '靠法治\\n划红线',
    quote: '法治既是防火墙，也是定心丸。',
    points: ['知识产权', '反不正当竞争', '反垄断', '恶意诉讼规制'],
    image: 'law-gavel.jpg',
    layout: 'law'
  },
  {
    id: 'xhs-08-standard',
    no: '08',
    tag: '靠什么反 02',
    title: '靠标准\\n立尺子',
    quote: '走出内卷，需要一把向上的尺子。',
    points: ['安全标准', '质量标准', '技术标准', '国家标准'],
    layout: 'ruler'
  },
  {
    id: 'xhs-09-market',
    no: '09',
    tag: '靠什么反 03',
    title: '靠统一市场\\n破壁垒',
    quote: '小市场容易卷消耗，大市场才能拼价值。',
    points: ['要素流动', '破地方保护', '破市场分割', '好产品跑出来'],
    image: 'logistics-port.jpg',
    layout: 'market'
  },
  {
    id: 'xhs-10-value',
    no: '10',
    tag: '立什么',
    title: '从卷价格\\n到优价值',
    quote: '优质优价，才能形成研发和质量提升的良性循环。',
    points: ['合理利润', '持续研发', '质量提升', '服务优化'],
    image: 'freight-containers.jpg',
    layout: 'value'
  },
  {
    id: 'xhs-11-company',
    no: '11',
    tag: '企业怎么做',
    title: '不是躺平\\n是向上竞争',
    quote: '反内卷不是让企业少竞争，而是换一种竞争。',
    points: ['技术创新', '产品品质', '服务体验', '品牌信用', '长期价值'],
    layout: 'upward'
  },
  {
    id: 'xhs-12-formula',
    no: '12',
    tag: '申论公式',
    title: '申论\\n这样写',
    quote: '综合整治“内卷式”竞争，要用法治划底线、用标准立尺度、用监管纠偏差、用统一市场破壁垒、用知识产权护创新。',
    points: ['法治划底线', '标准立尺度', '监管纠偏差', '统一市场破壁垒', '知识产权护创新'],
    layout: 'formula',
    sourceQuote: true
  },
  {
    id: 'xhs-13-interview',
    no: '13',
    tag: '面试答法',
    title: '题目\\n这样答',
    quote: '有人说反内卷会限制竞争。你怎么看？',
    points: ['先辨析：不是反竞争', '再分析：反低水平内耗', '再对策：法治、标准、监管、统一市场', '最后落点：价值创造'],
    layout: 'interview'
  },
  {
    id: 'xhs-14-closing',
    no: '14',
    tag: '收束金句',
    title: '最后记住\\n一句话',
    quote: '反内卷不是把竞争按住，而是把竞争扶正；不是少竞争，而是更高质量地竞争。',
    points: ['不是按住', '而是扶正', '不是少竞争', '更高质量竞争'],
    image: 'open-road-track.jpg',
    layout: 'closing',
    sourceQuote: true
  }
];

const photoMeta = {
  'open-road-track.jpg': {
    pos: 'center 56%',
    map: 'urban road lanes run toward the center horizon; safe title zones are upper-left sky and left mid-area, avoiding dense cars in lower center.'
  },
  'market-shelves.jpg': {
    pos: 'center 52%',
    map: 'market shelf texture fills the frame; no person subject; use as evidence well with text outside.'
  },
  'logistics-warehouse.jpg': {
    pos: 'center 52%',
    map: 'warehouse aisles and boxes fill the frame; text stays in separate rule panel.'
  },
  'law-gavel.jpg': {
    pos: 'center 48%',
    map: 'gavel and justice figure sit in the lower/middle area; text is placed in upper-left and separate panels.'
  },
  'logistics-port.jpg': {
    pos: 'center 56%',
    map: 'port cranes and containers stretch horizontally; title sits above a separate panel and does not cover the container lines.'
  },
  'freight-containers.jpg': {
    pos: 'center 52%',
    map: 'container train lines create directional value flow; text is separated into a top content area.'
  }
};

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
  const cls = page.quote.length > 82 ? 'quote long' : page.quote.length > 46 ? 'quote med' : 'quote';
  return `<blockquote class="${cls}">${escapeHtml(page.quote)}</blockquote>`;
}

function chips(items = []) {
  return `<div class="chips">${items.map((x, i) => `<span><b>${String(i + 1).padStart(2, '0')}</b>${escapeHtml(x)}</span>`).join('')}</div>`;
}

function renderPage(page) {
  if (page.layout === 'cover') {
    return `<section class="poster xhs cover" id="${page.id}">
      ${photo(page.image, 'bleed')}<div class="coverTint"></div><div class="grid"></div>
      <div class="content">
        ${top(page)}
        <p class="label">人民日报材料转申论</p>
        <h1>${titleHtml(page.title)}</h1>
        <div class="subtitle">${escapeHtml(page.quote)}</div>
        <div class="dualTrack"><span>低价低质</span><i></i><span>创新 · 质量 · 服务</span></div>
      </div>
    </section>`;
  }
  if (page.layout === 'mistake') {
    return `<section class="poster xhs mistake" id="${page.id}">
      <div class="grid"></div><div class="content">
        ${top(page)}<h1>${titleHtml(page.title)}</h1>${quoteHtml(page)}
        <div class="mistakeGrid">${page.points.map((x, i) => `<span><b>误区 ${String(i + 1).padStart(2, '0')}</b>${escapeHtml(x)}</span>`).join('')}</div>
      </div>
    </section>`;
  }
  if (page.layout === 'mainline') {
    return `<section class="poster xhs mainline" id="${page.id}">
      <div class="grid"></div><div class="content">
        ${top(page)}<h1>${titleHtml(page.title)}</h1>${quoteHtml(page)}
        <div class="threeQ">${page.points.map((x, i) => `<span><b>${String(i + 1).padStart(2, '0')}</b>${escapeHtml(x)}</span>`).join('')}</div>
        <div class="axis"><em>低水平内耗</em><i></i><em>价值创造竞争</em></div>
      </div>
    </section>`;
  }
  if (page.layout === 'photo') {
    return `<section class="poster xhs photoPage" id="${page.id}">
      <div class="grid"></div>${photo(page.image, 'wide')}
      <div class="content">${top(page)}<h1>${titleHtml(page.title)}</h1>${quoteHtml(page)}${chips(page.points)}</div>
    </section>`;
  }
  if (page.layout === 'panelPhoto') {
    return `<section class="poster xhs panelPhoto" id="${page.id}">
      <div class="grid"></div>${photo(page.image, 'side')}
      <div class="content">${top(page)}<h1>${titleHtml(page.title)}</h1>${quoteHtml(page)}
      <div class="panelList">${page.points.map((x) => `<span>${escapeHtml(x)}</span>`).join('')}</div></div>
    </section>`;
  }
  if (page.layout === 'law') {
    return `<section class="poster xhs law" id="${page.id}">
      <div class="grid"></div>${photo(page.image, 'lawPhoto')}
      <div class="content">${top(page)}<h1>${titleHtml(page.title)}</h1>${quoteHtml(page)}${chips(page.points)}</div>
    </section>`;
  }
  if (page.layout === 'ruler') {
    return `<section class="poster xhs ruler" id="${page.id}">
      <div class="grid"></div><div class="content">${top(page)}<h1>${titleHtml(page.title)}</h1>${quoteHtml(page)}
      <div class="rulerBar">${page.points.map((x, i) => `<span><b>${String(i + 1).padStart(2, '0')}</b>${escapeHtml(x)}</span>`).join('')}</div></div>
    </section>`;
  }
  if (page.layout === 'market') {
    return `<section class="poster xhs market" id="${page.id}">
      <div class="grid"></div>${photo(page.image, 'bottomPhoto')}
      <div class="content">${top(page)}<h1>${titleHtml(page.title)}</h1>${quoteHtml(page)}
      <div class="marketFlow">${page.points.map((x) => `<span>${escapeHtml(x)}</span>`).join('')}</div></div>
    </section>`;
  }
  if (page.layout === 'value') {
    return `<section class="poster xhs value" id="${page.id}">
      <div class="grid"></div>${photo(page.image, 'stripPhoto')}
      <div class="content">${top(page)}<h1>${titleHtml(page.title)}</h1>${quoteHtml(page)}
      <div class="valueLoop">${page.points.map((x) => `<span>${escapeHtml(x)}</span>`).join('')}</div></div>
    </section>`;
  }
  if (page.layout === 'upward') {
    return `<section class="poster xhs upward" id="${page.id}">
      <div class="grid"></div><div class="content">${top(page)}<h1>${titleHtml(page.title)}</h1>${quoteHtml(page)}
      <div class="upBars">${page.points.map((x, i) => `<span style="--h:${160 + i * 70}px"><b>${String(i + 1).padStart(2, '0')}</b>${escapeHtml(x)}</span>`).join('')}</div></div>
    </section>`;
  }
  if (page.layout === 'formula') {
    return `<section class="poster xhs formula" id="${page.id}">
      <div class="grid"></div><div class="content">${top(page)}<h1>${titleHtml(page.title)}</h1>${quoteHtml(page)}
      <div class="formulaBlocks">${page.points.map((x) => `<span>${escapeHtml(x)}</span>`).join('')}</div></div>
    </section>`;
  }
  if (page.layout === 'interview') {
    return `<section class="poster xhs interview" id="${page.id}">
      <div class="grid"></div><div class="content">${top(page)}<h1>${titleHtml(page.title)}</h1>${quoteHtml(page)}
      <div class="answerSteps">${page.points.map((x, i) => `<span><b>${String(i + 1).padStart(2, '0')}</b>${escapeHtml(x)}</span>`).join('')}</div></div>
    </section>`;
  }
  if (page.layout === 'closing') {
    return `<section class="poster xhs closing" id="${page.id}">
      <div class="grid"></div>${photo(page.image, 'closePhoto')}
      <div class="content">${top(page)}<h1>${titleHtml(page.title)}</h1>${quoteHtml(page)}
      <div class="closingWords">${page.points.map((x) => `<span>${escapeHtml(x)}</span>`).join('')}</div></div>
    </section>`;
  }
  return '';
}

function renderVideo(id, image, title, subtitle, variant) {
  const meta = photoMeta[image];
  return `<section class="poster video v${variant}" id="${id}">
    <figure class="videoPhoto">
      <!-- Subject map: ${meta.map} Magazine title sits in documented safe zone with localized tint, keeping the full-bleed image readable. -->
      <img src="${rel(image)}" alt="" style="object-position:${variant === 1 ? 'center 56%' : 'center 54%'};">
    </figure>
    <div class="videoTint"></div><div class="magLines"></div>
    <div class="videoTitle">
      <p>《人民日报》这样写</p>
      <h2>${titleHtml(title)}</h2>
      <span>${escapeHtml(subtitle)}</span>
    </div>
  </section>`;
}

const videos = [
  renderVideo('video-cover-01', 'open-road-track.jpg', '反内卷\\n不是反竞争', '让竞争回到价值创造', 1),
  renderVideo('video-cover-02', 'logistics-port.jpg', '不是按住\\n而是扶正', '法治 / 标准 / 统一市场', 2)
];

const css = `
*{box-sizing:border-box}html,body{margin:0;padding:0}body{margin:0;background:#cbd8d5;font-family:"Inter","Avenir Next","Helvetica Neue","PingFang SC","Noto Sans SC","Microsoft YaHei",sans-serif;color:#162825}.stage{width:max-content;display:grid;gap:34px;padding:34px}.poster{position:relative;overflow:hidden;isolation:isolate;background:#dbe8e5;color:#162825}.xhs,.video{width:1080px;height:1440px}.grid{position:absolute;inset:0;z-index:0;background:linear-gradient(90deg,rgba(22,40,37,.065) 1px,transparent 1px),linear-gradient(180deg,rgba(22,40,37,.065) 1px,transparent 1px);background-size:72px 72px}.content{position:relative;z-index:4;height:100%;padding:58px;display:flex;flex-direction:column}.top{display:flex;align-items:center;justify-content:space-between;gap:24px;border-bottom:2px solid rgba(22,40,37,.24);padding-bottom:22px;font-size:24px;line-height:1;font-weight:820}.top span:first-child{font-size:36px;color:#496f68;font-weight:900}.label{margin:34px 0 0;color:#5f7671;font-size:26px;font-weight:820}.xhs h1{margin:30px 0 0;font-size:86px;line-height:1.03;font-weight:520;letter-spacing:0}.quote{margin:28px 0 0;padding:26px 28px;border-left:10px solid #6f918a;background:rgba(248,248,243,.78);font-size:37px;line-height:1.34;font-weight:780}.quote.med{font-size:33px}.quote.long{font-size:29px;line-height:1.34}.photo{margin:0;overflow:hidden}.photo img,.videoPhoto img{width:100%;height:100%;object-fit:cover;filter:grayscale(.10) saturate(.66) contrast(1.04) brightness(.96)}.bleed{position:absolute;inset:0;z-index:1}.coverTint{position:absolute;inset:0;z-index:2;background:linear-gradient(180deg,rgba(219,232,229,.93),rgba(219,232,229,.84) 42%,rgba(219,232,229,.38)),linear-gradient(90deg,rgba(219,232,229,.96),rgba(219,232,229,.24) 74%)}.cover .grid{z-index:3}.cover h1{font-size:102px;font-weight:470}.subtitle{margin-top:34px;max-width:850px;padding:22px 26px;background:#496f68;color:#fff;font-size:35px;font-weight:860}.dualTrack{margin-top:auto;display:grid;grid-template-columns:1fr 90px 1fr;gap:16px;align-items:center}.dualTrack span{height:180px;display:grid;place-items:center;background:#162825;color:#f8f8f3;font-size:34px;font-weight:820}.dualTrack span:last-child{background:#6f918a}.dualTrack i{height:5px;background:#496f68}.mistakeGrid{margin-top:auto;display:grid;grid-template-columns:repeat(2,1fr);gap:16px}.mistakeGrid span{height:245px;padding:24px;display:grid;align-content:space-between;background:#f8f8f3;border:2px solid rgba(22,40,37,.14);font-size:36px;font-weight:760}.mistakeGrid b{font-size:22px;color:#496f68}.threeQ{margin-top:54px;display:grid;grid-template-columns:repeat(3,1fr);gap:14px}.threeQ span{height:360px;display:grid;place-items:center;text-align:center;background:#162825;color:#fff;font-size:42px;font-weight:780}.threeQ b{display:block;margin-bottom:24px;color:#9eb9b3;font-size:26px}.axis{margin-top:auto;height:105px;padding:0 28px;display:flex;align-items:center;justify-content:space-between;background:#496f68;color:#fff;font-size:31px;font-weight:860}.axis i{flex:1;height:4px;margin:0 24px;background:#fff}.wide{position:absolute;left:58px;right:58px;bottom:58px;height:420px;border:3px solid rgba(22,40,37,.18);z-index:1}.photoPage .content{padding-bottom:545px}.photoPage .chips{position:absolute;left:58px;right:58px;bottom:506px}.chips{display:grid;grid-template-columns:repeat(4,1fr);gap:10px}.chips span{height:130px;padding:18px 12px;display:grid;align-content:space-between;background:#162825;color:#fff;font-size:23px;line-height:1.08;font-weight:820}.chips b{display:block;color:#9eb9b3;font-size:18px}.side{position:absolute;left:58px;right:58px;bottom:58px;height:410px;border:3px solid rgba(22,40,37,.18);z-index:1}.panelPhoto .content{padding-bottom:520px}.panelList{margin-top:38px;display:grid;grid-template-columns:repeat(2,1fr);gap:14px}.panelList span{height:150px;display:grid;place-items:center;background:#f8f8f3;border-left:12px solid #496f68;font-size:30px;font-weight:800}.lawPhoto{position:absolute;right:0;top:0;bottom:0;width:425px;z-index:1}.lawPhoto img{filter:grayscale(.22) saturate(.58) contrast(1.05) brightness(.92)}.law:after{content:"";position:absolute;right:0;top:0;bottom:0;width:520px;z-index:2;background:linear-gradient(90deg,#dbe8e5 0%,rgba(219,232,229,.65) 36%,rgba(219,232,229,.08) 100%)}.law .content{padding-right:430px}.law .chips{margin-top:auto;grid-template-columns:1fr}.law .chips span{height:92px;display:flex;align-items:center;gap:18px;padding:0 20px}.rulerBar{margin-top:auto;display:grid;grid-template-columns:repeat(4,1fr);gap:12px}.rulerBar span{position:relative;height:560px;padding:28px 16px;display:grid;align-content:end;text-align:center;background:#f8f8f3;border-top:18px solid #496f68;font-size:33px;line-height:1.08;font-weight:820}.rulerBar span:before{content:"";position:absolute;left:0;right:0;top:76px;height:2px;background:repeating-linear-gradient(90deg,#496f68 0 10px,transparent 10px 24px)}.rulerBar b{position:absolute;top:28px;left:18px;color:#496f68;font-size:25px}.bottomPhoto{position:absolute;left:58px;right:58px;bottom:58px;height:400px;border:3px solid rgba(22,40,37,.18);z-index:1}.market .content{padding-bottom:530px}.marketFlow{margin-top:48px;display:grid;grid-template-columns:repeat(4,1fr);gap:12px}.marketFlow span{height:170px;display:grid;place-items:center;text-align:center;background:#162825;color:#fff;font-size:28px;font-weight:820}.stripPhoto{position:absolute;left:58px;right:58px;bottom:58px;height:390px;border:3px solid rgba(22,40,37,.18);z-index:1}.value .content{padding-bottom:520px}.valueLoop{margin-top:44px;display:grid;grid-template-columns:repeat(2,1fr);gap:14px}.valueLoop span{height:150px;display:grid;place-items:center;text-align:center;background:#f8f8f3;border-left:12px solid #496f68;font-size:30px;font-weight:820}.upBars{margin-top:auto;display:flex;align-items:end;gap:13px}.upBars span{height:var(--h);flex:1;padding:18px 10px;display:grid;align-content:space-between;text-align:center;background:#162825;color:#fff;font-size:25px;font-weight:820}.upBars span:nth-child(5){background:#496f68}.upBars b{color:#9eb9b3;font-size:19px}.formula .quote{font-size:29px}.formulaBlocks{margin-top:42px;display:grid;gap:12px}.formulaBlocks span{height:105px;padding:0 24px;display:flex;align-items:center;background:#f8f8f3;border-left:12px solid #496f68;font-size:31px;font-weight:820}.answerSteps{margin-top:42px;display:grid;gap:14px}.answerSteps span{height:128px;padding:0 24px;display:flex;align-items:center;gap:20px;background:#f8f8f3;border-left:12px solid #496f68;font-size:29px;font-weight:820}.answerSteps b{font-size:22px;color:#5f7671}.closePhoto{position:absolute;left:58px;right:58px;bottom:58px;height:390px;border:3px solid rgba(22,40,37,.18);z-index:1}.closing .content{padding-bottom:520px}.closing .quote{font-size:32px}.closingWords{margin-top:42px;display:grid;grid-template-columns:repeat(4,1fr);gap:12px}.closingWords span{height:160px;display:grid;place-items:center;text-align:center;background:#162825;color:#fff;font-size:28px;font-weight:820}.closingWords span:nth-child(2),.closingWords span:nth-child(4){background:#496f68}.videoPhoto{position:absolute;inset:0;margin:0;z-index:1}.videoPhoto img{filter:grayscale(.04) saturate(.76) contrast(1.08) brightness(.82)}.videoTint{position:absolute;inset:0;z-index:2;background:linear-gradient(180deg,rgba(0,0,0,.08),rgba(0,0,0,.18) 44%,rgba(0,0,0,.56)),linear-gradient(90deg,rgba(0,0,0,.58),rgba(0,0,0,.08) 70%)}.magLines{position:absolute;inset:56px;z-index:3;border-top:2px solid rgba(255,255,255,.62);border-bottom:2px solid rgba(255,255,255,.42)}.magLines:before{content:"";position:absolute;left:0;top:94px;width:190px;height:2px;background:rgba(255,255,255,.54)}.videoTitle{position:absolute;left:64px;right:116px;bottom:96px;z-index:4;color:#f8f8f3}.v1 .videoTitle{top:120px;bottom:auto}.videoTitle p{margin:0 0 28px;font-size:31px;line-height:1;font-weight:840}.videoTitle h2{margin:0;font-family:"Songti SC","STSong","Noto Serif CJK SC",serif;font-size:108px;line-height:.98;font-weight:740;letter-spacing:0}.videoTitle span{display:block;width:max-content;max-width:790px;margin-top:28px;padding:14px 18px;background:#496f68;color:#fff;font-size:31px;font-weight:860}.preview{width:1800px;background:#d3dfdc;padding:34px;display:grid;grid-template-columns:repeat(5,1fr);gap:18px}.preview figure{margin:0;background:#fff;padding:8px}.preview img{width:100%;display:block}.preview figcaption{padding:8px 2px 0;font-size:16px;font-weight:780;color:#303030}
`;

const html = `<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>反内卷小红书与视频号封面</title><style>${css}</style></head><body><main class="stage">${pages.map(renderPage).join('\n')}${videos.join('\n')}</main></body></html>`;
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
await page.locator('#video-cover-01').screenshot({ path: out('video-cover-01.png') });
await page.locator('#video-cover-02').screenshot({ path: out('video-cover-02.png') });
outputFiles.push('video-cover-01.png', 'video-cover-02.png');

const previewPath = path.join(__dirname, 'preview.html');
fs.writeFileSync(previewPath, `<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><style>${css}</style></head><body><section class="preview">${outputFiles.map((file) => `<figure><img src="${path.relative(__dirname, out(file)).replaceAll(path.sep, '/')}" alt=""><figcaption>${file}</figcaption></figure>`).join('')}</section></body></html>`, 'utf8');
await page.setViewportSize({ width: 1900, height: 1500 });
await page.goto(`file://${previewPath}`, { waitUntil: 'networkidle' });
await page.locator('.preview').screenshot({ path: out('preview-grid.png') });
outputFiles.push('preview-grid.png');

await browser.close();

console.log(JSON.stringify({
  mediaDir,
  count: outputFiles.length,
  files: outputFiles
}, null, 2));
