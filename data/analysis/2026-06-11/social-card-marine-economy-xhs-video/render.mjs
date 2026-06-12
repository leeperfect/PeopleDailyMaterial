import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { chromium } from 'playwright';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const repoRoot = path.resolve(__dirname, '../../../..');
const mediaDir = path.join(repoRoot, 'media/images/2026-06-11-marine-economy-xhs-video');
const assetDir = path.join(mediaDir, 'assets');
const htmlPath = path.join(__dirname, 'index.html');

const out = (file) => path.join(mediaDir, file);
const rel = (file) => path.relative(__dirname, path.join(assetDir, file)).replaceAll(path.sep, '/');

const pages = [
  {
    id: 'xhs-01-cover',
    no: '01',
    tag: '向海图强',
    title: '向海图强\\n不是靠海吃海',
    quote: '科技、生态和产业链',
    points: ['科技向海', '产业成链', '生态托底'],
    image: 'offshore-wind.jpg',
    layout: 'cover'
  },
  {
    id: 'xhs-02-mistake',
    no: '02',
    tag: '常见误区',
    title: '很多人\\n把海洋经济写浅了',
    quote: '这些话都对，但太像概念。',
    points: ['海洋资源丰富', '发展海洋产业', '加强海洋保护', '建设海洋强国'],
    layout: 'mistake'
  },
  {
    id: 'xhs-03-mainline',
    no: '03',
    tag: '核心主线',
    title: '人民日报\\n真正教的是这条线',
    quote: '不是写海里有什么，而是写我们有什么能力。',
    points: ['科技打开深海空间', '产业链提升资源价值', '生态修复托住长期发展'],
    layout: 'mainline'
  },
  {
    id: 'xhs-04-tech',
    no: '04',
    tag: '第一层',
    title: '科技\\n向海',
    quote: '海洋经济首先是能力题，不只是资源题。',
    points: ['深海装备', '部件国产', '成本下降', '能力下潜'],
    image: 'underwater-robot.jpg',
    layout: 'tech'
  },
  {
    id: 'xhs-05-guard',
    no: '05',
    tag: '科技守护',
    title: '科技不只开发\\n也守护',
    quote: '科技不是向海索取的工具，也是守护蔚蓝的能力。',
    points: ['水下机器人', '无人机巡护', 'AI生态模型', '动态生态地图'],
    image: 'coral-reef.jpg',
    layout: 'guard'
  },
  {
    id: 'xhs-06-industry',
    no: '06',
    tag: '第二层',
    title: '产业\\n向海',
    quote: '好产业不是单点突破，而是全链条服务。',
    points: ['种源自主', '育繁推闭环', '塘头服务', '市场反馈'],
    image: 'freight-containers.jpg',
    layout: 'chain'
  },
  {
    id: 'xhs-07-salt',
    no: '07',
    tag: '资源增值',
    title: '一粒海盐\\n也能成链',
    quote: '资源只有进入链条，才会真正增值。',
    points: ['海盐', '纯碱', '纤维 / PVC', '电池级碳酸钠', '精细化工'],
    layout: 'salt'
  },
  {
    id: 'xhs-08-port',
    no: '08',
    tag: '港口枢纽',
    title: '港口\\n不是终点',
    quote: '港口不只是装卸点，而是产业组织平台。',
    points: ['通道流量', '园区承接', '就地查验', '加工冷链', '产业留量'],
    image: 'logistics-port.jpg',
    layout: 'port'
  },
  {
    id: 'xhs-09-ecology',
    no: '09',
    tag: '第三层',
    title: '生态\\n向海',
    quote: '生态不是成本，而是海洋经济的底盘。',
    points: ['四级湾长制', '一湾一策', '智慧监管', '荒滩变绿道'],
    image: 'mangrove-coast.jpg',
    layout: 'ecology'
  },
  {
    id: 'xhs-10-coast',
    no: '10',
    tag: '幸福海岸',
    title: '海岸线\\n长成幸福线',
    quote: '生态修复不是发展暂停键，而是发展换挡器。',
    points: ['红树林', '蓝海驿站', '海洋EOD', '人工鱼礁', '海岛限流'],
    image: 'mangrove-coast.jpg',
    layout: 'coast'
  },
  {
    id: 'xhs-11-resource',
    no: '11',
    tag: '资源恢复',
    title: '斑海豹\\n来“安家”',
    quote: '海洋生态好了，渔业资源和文旅空间才会回来。',
    points: ['退养还湿', '取缔排污口', '恢复自然岸线', '资源回归'],
    image: 'coral-reef.jpg',
    layout: 'resource'
  },
  {
    id: 'xhs-12-formula',
    no: '12',
    tag: '申论公式',
    title: '申论\\n这样写',
    quote: '推进海洋经济高质量发展，要从资源利用转向能力建设、链条增值和生态共生。',
    points: ['能力建设', '链条增值', '生态共生'],
    layout: 'formula',
    sourceQuote: true
  },
  {
    id: 'xhs-13-interview',
    no: '13',
    tag: '面试答法',
    title: '面试\\n这样答',
    quote: '有人说，发展海洋经济就是靠海吃海。你怎么看？',
    points: ['先辨析：不是单向索取', '谈科技：装备和数据下海', '谈产业：资源进入链条', '谈生态：修复托住长期发展'],
    layout: 'interview'
  },
  {
    id: 'xhs-14-closing',
    no: '14',
    tag: '收束金句',
    title: '记住\\n这句话',
    quote: '向海图强，不是靠海索取，而是向海创新；不是只看资源多少，而是看科技能力、产业链能力和生态治理能力有多强。',
    points: ['不是索取', '而是创新', '看科技能力', '看链条能力', '看生态治理'],
    image: 'offshore-wind.jpg',
    layout: 'closing',
    sourceQuote: true
  }
];

const photoMeta = {
  'underwater-robot.jpg': {
    pos: 'center 54%',
    map: 'underwater robot sits in the lower middle; the upper-left water field is the safest title zone, avoiding the machine body and bubbles.'
  },
  'offshore-wind.jpg': {
    pos: 'center 48%',
    map: 'offshore wind turbines stand along the horizon; title can sit in the lower-left or upper-left water/sky field without covering the main turbine.'
  },
  'coral-reef.jpg': {
    pos: 'center 58%',
    map: 'coral texture fills the lower half; use upper dark-water area for short labels or keep text in separate panels.'
  },
  'mangrove-coast.jpg': {
    pos: 'center 50%',
    map: 'diagonal coastline and mangrove clusters run across the frame; text is kept in separate navy panels or lower-left safe zone.'
  },
  'logistics-port.jpg': {
    pos: 'center 56%',
    map: 'port cranes and containers form dense horizontal lines; text should be outside the photo well or on a localized dark tint.'
  },
  'freight-containers.jpg': {
    pos: 'center 52%',
    map: 'container train line moves horizontally; text is separated into cards above the photo.'
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
  const cls = page.quote.length > 72 ? 'quote long' : page.quote.length > 40 ? 'quote med' : 'quote';
  return `<blockquote class="${cls}">${escapeHtml(page.quote)}</blockquote>`;
}

function pills(items = []) {
  return `<div class="pills">${items.map((x, i) => `<span><b>${String(i + 1).padStart(2, '0')}</b>${escapeHtml(x)}</span>`).join('')}</div>`;
}

function renderPage(page) {
  if (page.layout === 'cover') {
    return `<section class="poster xhs cover" id="${page.id}">
      ${photo(page.image, 'bleed')}<div class="coverTint"></div><div class="scan"></div>
      <div class="content">
        ${top(page)}
        <p class="eyebrow">人民日报材料转申论</p>
        <h1>${titleHtml(page.title)}</h1>
        <div class="subtitle">${escapeHtml(page.quote)}</div>
        <div class="triad">${page.points.map((x) => `<span>${escapeHtml(x)}</span>`).join('')}</div>
      </div>
    </section>`;
  }
  if (page.layout === 'mistake') {
    return `<section class="poster xhs mistake" id="${page.id}">
      <div class="scan"></div><div class="content">
        ${top(page)}<h1>${titleHtml(page.title)}</h1>${quoteHtml(page)}
        <div class="mistakeGrid">${page.points.map((x, i) => `<span><b>误区 ${String(i + 1).padStart(2, '0')}</b>${escapeHtml(x)}</span>`).join('')}</div>
      </div>
    </section>`;
  }
  if (page.layout === 'mainline') {
    return `<section class="poster xhs mainline" id="${page.id}">
      <div class="scan"></div><div class="content">
        ${top(page)}<h1>${titleHtml(page.title)}</h1>${quoteHtml(page)}
        <div class="seaLanes">${page.points.map((x, i) => `<span><b>0${i + 1}</b>${escapeHtml(x)}</span>`).join('')}</div>
        <div class="axis"><em>向海索取</em><i></i><em>向海创新</em></div>
      </div>
    </section>`;
  }
  if (page.layout === 'tech') {
    return `<section class="poster xhs tech" id="${page.id}">
      <div class="scan"></div>${photo(page.image, 'heroWell')}
      <div class="content">${top(page)}<h1>${titleHtml(page.title)}</h1>${quoteHtml(page)}
      <div class="meter"><span>6000m</span><i></i><span>国产部件</span><i></i><span>成本 -40%</span></div></div>
    </section>`;
  }
  if (page.layout === 'guard') {
    return `<section class="poster xhs guard" id="${page.id}">
      <div class="scan"></div>${photo(page.image, 'sidePhoto')}
      <div class="content">${top(page)}<h1>${titleHtml(page.title)}</h1>${quoteHtml(page)}
      <div class="radar">${page.points.map((x) => `<span>${escapeHtml(x)}</span>`).join('')}</div></div>
    </section>`;
  }
  if (page.layout === 'chain') {
    return `<section class="poster xhs chain" id="${page.id}">
      <div class="scan"></div>${photo(page.image, 'bottomPhoto')}
      <div class="content">${top(page)}<h1>${titleHtml(page.title)}</h1>${quoteHtml(page)}
      <div class="flow">${page.points.map((x) => `<span>${escapeHtml(x)}</span>`).join('<i></i>')}</div></div>
    </section>`;
  }
  if (page.layout === 'salt') {
    return `<section class="poster xhs salt" id="${page.id}">
      <div class="scan"></div><div class="content">${top(page)}<h1>${titleHtml(page.title)}</h1>${quoteHtml(page)}
      <div class="ladder">${page.points.map((x, i) => `<span style="--w:${48 + i * 11}%"><b>${String(i + 1).padStart(2, '0')}</b>${escapeHtml(x)}</span>`).join('')}</div></div>
    </section>`;
  }
  if (page.layout === 'port') {
    return `<section class="poster xhs port" id="${page.id}">
      <div class="scan"></div>${photo(page.image, 'portPhoto')}
      <div class="content">${top(page)}<h1>${titleHtml(page.title)}</h1>${quoteHtml(page)}
      <div class="portFlow">${page.points.map((x) => `<span>${escapeHtml(x)}</span>`).join('')}</div></div>
    </section>`;
  }
  if (page.layout === 'ecology') {
    return `<section class="poster xhs ecology" id="${page.id}">
      <div class="scan"></div>${photo(page.image, 'ecoPhoto')}
      <div class="content">${top(page)}<h1>${titleHtml(page.title)}</h1>${quoteHtml(page)}
      ${pills(page.points)}</div>
    </section>`;
  }
  if (page.layout === 'coast') {
    return `<section class="poster xhs coast" id="${page.id}">
      <div class="scan"></div>${photo(page.image, 'coastPhoto')}
      <div class="content">${top(page)}<h1>${titleHtml(page.title)}</h1>${quoteHtml(page)}
      <div class="coastGrid">${page.points.map((x) => `<span>${escapeHtml(x)}</span>`).join('')}</div></div>
    </section>`;
  }
  if (page.layout === 'resource') {
    return `<section class="poster xhs resource" id="${page.id}">
      <div class="scan"></div>${photo(page.image, 'reefPhoto')}
      <div class="content">${top(page)}<h1>${titleHtml(page.title)}</h1>${quoteHtml(page)}
      <div class="returnLoop">${page.points.map((x) => `<span>${escapeHtml(x)}</span>`).join('<i></i>')}</div></div>
    </section>`;
  }
  if (page.layout === 'formula') {
    return `<section class="poster xhs formula" id="${page.id}">
      <div class="scan"></div><div class="content">${top(page)}<h1>${titleHtml(page.title)}</h1>${quoteHtml(page)}
      <div class="formulaBlocks">${page.points.map((x) => `<span>${escapeHtml(x)}</span>`).join('')}</div></div>
    </section>`;
  }
  if (page.layout === 'interview') {
    return `<section class="poster xhs interview" id="${page.id}">
      <div class="scan"></div><div class="content">${top(page)}<h1>${titleHtml(page.title)}</h1>${quoteHtml(page)}
      <div class="answerSteps">${page.points.map((x, i) => `<span><b>${String(i + 1).padStart(2, '0')}</b>${escapeHtml(x)}</span>`).join('')}</div></div>
    </section>`;
  }
  if (page.layout === 'closing') {
    return `<section class="poster xhs closing" id="${page.id}">
      <div class="scan"></div>${photo(page.image, 'closePhoto')}
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
      <!-- Subject map: ${meta.map} Magazine title sits in a safe zone with localized navy tint. -->
      <img src="${rel(image)}" alt="" style="object-position:${variant === 1 ? 'center 54%' : 'center 56%'};">
    </figure>
    <div class="videoTint"></div><div class="magFrame"></div>
    <div class="videoTitle">
      <p>《人民日报》这样写</p>
      <h2>${titleHtml(title)}</h2>
      <span>${escapeHtml(subtitle)}</span>
    </div>
  </section>`;
}

const videos = [
  renderVideo('video-cover-01', 'offshore-wind.jpg', '向海图强\\n不是靠海吃海', '科技 / 生态 / 产业链', 1),
  renderVideo('video-cover-02', 'mangrove-coast.jpg', '向海图强\\n不是靠海吃海', '而是向海创新', 2)
];

const css = `
*{box-sizing:border-box}html,body{margin:0;padding:0}body{background:#d8e6ea;font-family:"Avenir Next","Helvetica Neue","PingFang SC","Noto Sans SC","Microsoft YaHei",Arial,sans-serif;color:#eaf6f6}.stage{width:max-content;display:grid;gap:34px;padding:34px}.poster{position:relative;overflow:hidden;isolation:isolate;background:#071d33}.xhs,.video{width:1080px;height:1440px}.scan{position:absolute;inset:0;z-index:0;background:linear-gradient(90deg,rgba(255,255,255,.055) 1px,transparent 1px),linear-gradient(180deg,rgba(255,255,255,.05) 1px,transparent 1px),radial-gradient(circle at 74% 10%,rgba(65,210,196,.18),transparent 30%),linear-gradient(180deg,#0b2744,#061827);background-size:72px 72px,72px 72px,auto,auto}.content{position:relative;z-index:4;height:100%;padding:58px;display:flex;flex-direction:column}.top{display:flex;align-items:center;justify-content:space-between;gap:24px;border-bottom:2px solid rgba(234,246,246,.28);padding-bottom:22px;font-size:24px;line-height:1;font-weight:820;color:#d4ecea}.top span:first-child{font-size:36px;color:#7ce0d3;font-weight:900}.eyebrow{margin:34px 0 0;color:#9ecbd0;font-size:26px;font-weight:820}.xhs h1{margin:30px 0 0;font-size:88px;line-height:1.03;font-weight:520;letter-spacing:0;color:#f4fbf9}.quote{margin:28px 0 0;padding:25px 28px;border-left:10px solid #49b7ad;background:rgba(231,243,241,.94);color:#061827;font-size:37px;line-height:1.34;font-weight:820}.quote.med{font-size:33px}.quote.long{font-size:28px;line-height:1.38}.photo{margin:0;overflow:hidden}.photo img,.videoPhoto img{width:100%;height:100%;object-fit:cover;filter:saturate(.82) contrast(1.06) brightness(.9)}.bleed{position:absolute;inset:0;z-index:1}.coverTint{position:absolute;inset:0;z-index:2;background:linear-gradient(180deg,rgba(6,24,39,.25),rgba(6,24,39,.64)),linear-gradient(90deg,rgba(6,24,39,.92),rgba(6,24,39,.25) 72%)}.cover .scan{z-index:3;background:linear-gradient(90deg,rgba(255,255,255,.08) 1px,transparent 1px),linear-gradient(180deg,rgba(255,255,255,.07) 1px,transparent 1px);background-size:72px 72px}.cover h1{font-size:104px;font-weight:480}.subtitle{margin-top:32px;max-width:890px;padding:22px 26px;background:#49b7ad;color:#061827;font-size:34px;font-weight:900}.triad{margin-top:auto;display:grid;grid-template-columns:repeat(3,1fr);gap:13px}.triad span{height:170px;display:grid;place-items:center;background:rgba(234,246,246,.94);color:#061827;font-size:34px;font-weight:900}.triad span:nth-child(2){background:#0e365c;color:#f4fbf9}.triad span:nth-child(3){background:#f2a65a;color:#061827}.mistakeGrid{margin-top:auto;display:grid;grid-template-columns:repeat(2,1fr);gap:16px}.mistakeGrid span{height:240px;padding:24px;display:grid;align-content:space-between;background:#eaf6f6;color:#061827;border:2px solid rgba(124,224,211,.45);font-size:35px;font-weight:790}.mistakeGrid b{font-size:22px;color:#0e6b75}.seaLanes{margin-top:54px;display:grid;gap:16px}.seaLanes span{height:185px;padding:0 30px;display:flex;align-items:center;gap:28px;background:#eaf6f6;color:#061827;font-size:36px;font-weight:860}.seaLanes b{display:grid;place-items:center;width:82px;height:82px;background:#0e365c;color:#7ce0d3;font-size:30px}.axis{margin-top:auto;height:112px;padding:0 28px;display:flex;align-items:center;justify-content:space-between;background:#49b7ad;color:#061827;font-size:31px;font-weight:900}.axis i{flex:1;height:4px;margin:0 24px;background:#061827}.heroWell{position:absolute;left:58px;right:58px;bottom:58px;height:440px;border:3px solid rgba(124,224,211,.45);z-index:1}.tech .content{padding-bottom:570px}.meter{margin-top:38px;display:grid;grid-template-columns:1fr 36px 1fr 36px 1fr;align-items:center}.meter span{height:145px;display:grid;place-items:center;text-align:center;background:#eaf6f6;color:#061827;font-size:31px;font-weight:900}.meter i{height:4px;background:#7ce0d3}.sidePhoto{position:absolute;right:0;top:0;bottom:0;width:430px;z-index:1}.sidePhoto img{filter:saturate(.76) contrast(1.08) brightness(.8)}.guard:after{content:"";position:absolute;right:0;top:0;bottom:0;width:540px;z-index:2;background:linear-gradient(90deg,#071d33 0%,rgba(7,29,51,.74) 44%,rgba(7,29,51,.1) 100%)}.guard .content{padding-right:420px}.radar{margin-top:auto;display:grid;gap:12px}.radar span{height:92px;padding:0 22px;display:flex;align-items:center;background:#eaf6f6;color:#061827;border-left:12px solid #49b7ad;font-size:28px;font-weight:850}.bottomPhoto{position:absolute;left:58px;right:58px;bottom:58px;height:395px;border:3px solid rgba(124,224,211,.45);z-index:1}.chain .content{padding-bottom:520px}.flow{margin-top:46px;display:grid;grid-template-columns:1fr 34px 1fr 34px 1fr 34px 1fr;align-items:center}.flow span{height:142px;display:grid;place-items:center;text-align:center;background:#eaf6f6;color:#061827;font-size:27px;font-weight:900}.flow i,.returnLoop i{height:4px;background:#7ce0d3}.ladder{margin-top:auto;display:grid;gap:15px;align-items:end}.ladder span{width:var(--w);height:98px;padding:0 24px;display:flex;align-items:center;gap:22px;background:#eaf6f6;color:#061827;font-size:30px;font-weight:870;border-left:14px solid #49b7ad}.ladder b{color:#0e6b75;font-size:24px}.portPhoto{position:absolute;left:58px;right:58px;bottom:58px;height:420px;border:3px solid rgba(124,224,211,.45);z-index:1}.port .content{padding-bottom:550px}.portFlow{margin-top:45px;display:grid;grid-template-columns:repeat(5,1fr);gap:10px}.portFlow span{height:170px;padding:0 10px;display:grid;place-items:center;text-align:center;background:#eaf6f6;color:#061827;font-size:25px;font-weight:870}.portFlow span:first-child,.portFlow span:last-child{background:#49b7ad}.ecoPhoto{position:absolute;left:58px;right:58px;bottom:58px;height:430px;border:3px solid rgba(124,224,211,.45);z-index:1}.ecology .content{padding-bottom:560px}.pills{margin-top:42px;display:grid;grid-template-columns:repeat(2,1fr);gap:14px}.pills span{height:136px;padding:18px;display:grid;align-content:space-between;background:#eaf6f6;color:#061827;font-size:27px;line-height:1.12;font-weight:860}.pills b{font-size:20px;color:#0e6b75}.coastPhoto{position:absolute;inset:0;z-index:1}.coastPhoto img{filter:saturate(.75) contrast(1.02) brightness(.68)}.coast:after{content:"";position:absolute;inset:0;z-index:2;background:linear-gradient(180deg,rgba(7,29,51,.18),rgba(7,29,51,.9) 78%),linear-gradient(90deg,rgba(7,29,51,.9),rgba(7,29,51,.12) 78%)}.coast .content{z-index:3}.coastGrid{margin-top:auto;display:grid;grid-template-columns:repeat(5,1fr);gap:10px}.coastGrid span{height:150px;padding:12px 8px;display:grid;place-items:center;text-align:center;background:rgba(234,246,246,.96);color:#061827;font-size:24px;font-weight:900}.reefPhoto{position:absolute;left:58px;right:58px;bottom:58px;height:380px;border:3px solid rgba(124,224,211,.45);z-index:1}.resource .content{padding-bottom:510px}.returnLoop{margin-top:52px;display:grid;grid-template-columns:1fr 28px 1fr 28px 1fr 28px 1fr;align-items:center}.returnLoop span{height:150px;padding:0 12px;display:grid;place-items:center;text-align:center;background:#eaf6f6;color:#061827;font-size:26px;font-weight:900}.formula h1{font-size:98px}.formula .quote{font-size:35px;line-height:1.42;margin-top:42px}.formulaBlocks{margin-top:52px;display:grid;grid-template-columns:repeat(3,1fr);gap:14px}.formulaBlocks span{height:280px;display:grid;place-items:center;text-align:center;background:#eaf6f6;color:#061827;border-top:18px solid #49b7ad;font-size:34px;font-weight:900}.answerSteps{margin-top:42px;display:grid;gap:14px}.answerSteps span{height:128px;padding:0 24px;display:flex;align-items:center;gap:20px;background:#eaf6f6;color:#061827;border-left:12px solid #49b7ad;font-size:28px;font-weight:850}.answerSteps b{font-size:22px;color:#0e6b75}.closePhoto{position:absolute;left:58px;right:58px;bottom:58px;height:390px;border:3px solid rgba(124,224,211,.45);z-index:1}.closing .content{padding-bottom:520px}.closing .quote{font-size:29px;line-height:1.4}.closingWords{margin-top:42px;display:grid;grid-template-columns:repeat(5,1fr);gap:10px}.closingWords span{height:155px;padding:0 8px;display:grid;place-items:center;text-align:center;background:#eaf6f6;color:#061827;font-size:24px;font-weight:900}.closingWords span:nth-child(2),.closingWords span:nth-child(5){background:#49b7ad}.videoPhoto{position:absolute;inset:0;margin:0;z-index:1}.videoPhoto img{filter:saturate(.78) contrast(1.08) brightness(.78)}.videoTint{position:absolute;inset:0;z-index:2;background:linear-gradient(180deg,rgba(2,12,23,.1),rgba(2,12,23,.22) 42%,rgba(2,12,23,.72)),linear-gradient(90deg,rgba(2,12,23,.82),rgba(2,12,23,.1) 74%)}.magFrame{position:absolute;inset:56px;z-index:3;border-top:2px solid rgba(255,255,255,.62);border-bottom:2px solid rgba(255,255,255,.42)}.magFrame:before{content:"";position:absolute;left:0;top:94px;width:190px;height:2px;background:rgba(255,255,255,.54)}.videoTitle{position:absolute;left:64px;right:108px;bottom:96px;z-index:4;color:#f4fbf9}.v1 .videoTitle{top:120px;bottom:auto}.videoTitle p{margin:0 0 28px;font-size:31px;line-height:1;font-weight:840}.videoTitle h2{margin:0;font-family:"Songti SC","STSong","Noto Serif CJK SC",serif;font-size:112px;line-height:.99;font-weight:760;letter-spacing:0}.videoTitle span{display:block;width:max-content;max-width:820px;margin-top:28px;padding:14px 18px;background:#49b7ad;color:#061827;font-size:31px;font-weight:900}.preview{width:1800px;background:#d8e6ea;padding:34px;display:grid;grid-template-columns:repeat(5,1fr);gap:18px}.preview figure{margin:0;background:#fff;padding:8px}.preview img{width:100%;display:block}.preview figcaption{padding:8px 2px 0;font-size:16px;font-weight:780;color:#303030}
`;

const html = `<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>向海图强小红书与视频号封面</title><style>${css}</style></head><body><main class="stage">${pages.map(renderPage).join('\n')}${videos.join('\n')}</main></body></html>`;
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
