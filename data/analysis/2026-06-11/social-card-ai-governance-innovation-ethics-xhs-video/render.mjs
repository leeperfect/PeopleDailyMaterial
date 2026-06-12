import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { chromium } from 'playwright';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const repoRoot = path.resolve(__dirname, '../../../..');
const mediaDir = path.join(repoRoot, 'media/images/2026-06-11-ai-governance-innovation-ethics-xhs-video');
const assetDir = path.join(mediaDir, 'assets');
const htmlPath = path.join(__dirname, 'index.html');

const out = (file) => path.join(mediaDir, file);
const rel = (file) => path.relative(__dirname, path.join(assetDir, file)).replaceAll(path.sep, '/');

const pages = [
  {
    id: 'xhs-01-cover',
    no: '01',
    tag: 'AI Governance',
    title: 'AI治理\\n怎么写',
    quote: '既给创新空间，也守伦理底线',
    points: ['发展空间', '具体风险', '治理工具'],
    image: 'robot-hand-network.jpg',
    layout: 'cover'
  },
  {
    id: 'xhs-02-misread',
    no: '02',
    tag: '常见误区',
    title: '很多人\\n把AI写偏了',
    quote: 'AI治理不是发展和监管的拼接。',
    points: ['只写赋能', '只写监管', '只写算力', '只写风险'],
    layout: 'mistake'
  },
  {
    id: 'xhs-03-mainline',
    no: '03',
    tag: '高分主线',
    title: '真正要写\\n这条线',
    quote: '让创新在清晰边界内奔跑，让风险在责任链条内闭环。',
    points: ['承认发展空间', '识别具体风险', '接入治理工具'],
    layout: 'chain'
  },
  {
    id: 'xhs-04-development',
    no: '04',
    tag: '发展端',
    title: '先写AI\\n为什么要发展',
    quote: 'AI不是抽象概念，而是技术、要素和场景的结合。',
    points: ['算法模型', '智算基础', '数据网络', '产业应用', '能源需求'],
    image: 'circuit-board.jpg',
    layout: 'photoGrid'
  },
  {
    id: 'xhs-05-energy',
    no: '05',
    tag: '能源视角',
    title: '别漏掉\\n绿色算力',
    quote: 'AI发展既要能源支撑，也要反过来赋能能源转型。',
    points: ['算力用电', '新能源预测', '电网调度', '数据挖掘'],
    image: 'solar-panels.jpg',
    layout: 'energy'
  },
  {
    id: 'xhs-06-risk',
    no: '06',
    tag: '风险端',
    title: '风险要\\n写具体',
    quote: '风险不落到具体人和具体系统上，就写不深。',
    points: ['内容风险', '模型风险', '劳动风险', '能源风险', '伦理风险'],
    image: 'data-center-server.jpg',
    layout: 'risk'
  },
  {
    id: 'xhs-07-content',
    no: '07',
    tag: '内容治理',
    title: '内容不能\\n“裸奔”',
    quote: '不是等谣言扩散后再删帖，而是把治理嵌入全流程。',
    points: ['源头标识', '分发审核', '传播核验', '用户声明'],
    layout: 'process'
  },
  {
    id: 'xhs-08-ethics',
    no: '08',
    tag: '伦理审查',
    title: '底线要\\n前置',
    quote: '伦理治理不是原则口号，而是机构、流程、标准和监测。',
    points: ['伦理委员会', '审查中心', '技术标准', '通报机制', '风险监测'],
    image: 'robot-arm-gray.jpg',
    layout: 'ethics'
  },
  {
    id: 'xhs-09-sandbox',
    no: '09',
    tag: '沙盒监管',
    title: '既包容\\n也可控',
    quote: '沙盒监管，是把试错放进规则里。',
    points: ['严格准入', '全程监测', '及时叫停', '平稳退出'],
    image: 'circuit-board.jpg',
    layout: 'sandbox'
  },
  {
    id: 'xhs-10-labor',
    no: '10',
    tag: '劳动权益',
    title: 'AI也要\\n写公平',
    quote: '技术红利不能靠牺牲劳动者权益来换。',
    points: ['前置评估', '过程监测', '协商调岗', '培训转岗', '依法救济'],
    layout: 'rights'
  },
  {
    id: 'xhs-11-global',
    no: '11',
    tag: '全球治理',
    title: '最后要\\n拉开格局',
    quote: 'AI应该成为造福人类的公共产品，而不是少数人的游戏。',
    points: ['算力流动', '算法协同', '数据规则', '防止鸿沟'],
    image: 'robot-hand-network.jpg',
    layout: 'global'
  },
  {
    id: 'xhs-12-formula',
    no: '12',
    tag: '考场公式',
    title: '申论\\n这样写',
    quote: '推进人工智能治理，要坚持发展和安全并重、创新和规范并举，把技术应用、风险识别、伦理审查、责任归属和全球协同贯通起来。',
    points: ['发展安全并重', '创新规范并举', '责任链条贯通'],
    layout: 'formula',
    sourceQuote: true
  },
  {
    id: 'xhs-13-closing',
    no: '13',
    tag: '收束金句',
    title: '记住\\n这句话',
    quote: 'AI治理不是给创新设墙，而是给创新铺轨；不是让技术停下来，而是让技术朝着有益、安全、公平的方向走下去。',
    points: ['不是设墙', '而是铺轨', '有益', '安全', '公平'],
    image: 'robot-arm-gray.jpg',
    layout: 'closing',
    sourceQuote: true
  }
];

const photoMeta = {
  'robot-hand-network.jpg': {
    pos: 'center 47%',
    map: 'robot hand sits in the lower center; upper-left and upper-middle have quiet blue network space for headline overlays.'
  },
  'data-center-server.jpg': {
    pos: 'center 50%',
    map: 'server rows fill the frame as repeating lines; text sits outside the photo well or over a dark localized panel.'
  },
  'circuit-board.jpg': {
    pos: 'center 50%',
    map: 'circuit board is a flat technical texture; safe for cropped detail wells and small overlaid captions.'
  },
  'solar-panels.jpg': {
    pos: 'center 54%',
    map: 'solar panels occupy the lower half with sky/green field above; title and data can sit in separate gray panels.'
  },
  'robot-arm-gray.jpg': {
    pos: 'center 50%',
    map: 'robot arm and torso sit on the center-right; the left third is soft dark negative space and is safe for title.'
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
  const len = page.quote.length;
  const cls = len > 88 ? 'quote long' : len > 48 ? 'quote med' : 'quote';
  return `<blockquote class="${cls}">${escapeHtml(page.quote)}</blockquote>`;
}

function chips(items = []) {
  return `<div class="chips">${items.map((x, i) => `<span><b>${String(i + 1).padStart(2, '0')}</b>${escapeHtml(x)}</span>`).join('')}</div>`;
}

function renderPage(page) {
  if (page.layout === 'cover') {
    return `<section class="poster xhs cover" id="${page.id}">
      ${photo(page.image, 'bleed')}
      <div class="cover-tint"></div><div class="grid"></div>
      <div class="content">
        ${top(page)}
        <p class="label">人民日报材料转申论</p>
        <h1>${titleHtml(page.title)}</h1>
        <div class="subtitle">${escapeHtml(page.quote)}</div>
        <div class="track">${page.points.map((x) => `<span>${escapeHtml(x)}</span>`).join('')}</div>
      </div>
    </section>`;
  }
  if (page.layout === 'mistake') {
    return `<section class="poster xhs mistake" id="${page.id}">
      <div class="grid"></div><div class="content">
        ${top(page)}<h1>${titleHtml(page.title)}</h1>${quoteHtml(page)}
        <div class="matrix">${page.points.map((x, i) => `<span><b>误区 ${String(i + 1).padStart(2, '0')}</b>${escapeHtml(x)}</span>`).join('')}</div>
      </div>
    </section>`;
  }
  if (page.layout === 'chain') {
    return `<section class="poster xhs chain" id="${page.id}">
      <div class="grid"></div><div class="content">
        ${top(page)}<h1>${titleHtml(page.title)}</h1>${quoteHtml(page)}
        <div class="chainLine">${page.points.map((x, i) => `<span><b>${String(i + 1).padStart(2, '0')}</b>${escapeHtml(x)}</span>`).join('')}</div>
        <div class="rail">创新空间 <i></i> 伦理底线</div>
      </div>
    </section>`;
  }
  if (page.layout === 'photoGrid') {
    return `<section class="poster xhs photoGrid" id="${page.id}">
      <div class="grid"></div>${photo(page.image, 'wide')}
      <div class="content">
        ${top(page)}<h1>${titleHtml(page.title)}</h1>${quoteHtml(page)}
        ${chips(page.points)}
      </div>
    </section>`;
  }
  if (page.layout === 'energy') {
    return `<section class="poster xhs energy" id="${page.id}">
      <div class="grid"></div>${photo(page.image, 'bottomPhoto')}
      <div class="content">
        ${top(page)}<h1>${titleHtml(page.title)}</h1>${quoteHtml(page)}
        <div class="loop">${page.points.map((x) => `<span>${escapeHtml(x)}</span>`).join('')}</div>
      </div>
    </section>`;
  }
  if (page.layout === 'risk') {
    return `<section class="poster xhs risk" id="${page.id}">
      <div class="grid"></div>${photo(page.image, 'sidePhoto')}
      <div class="content">
        ${top(page)}<h1>${titleHtml(page.title)}</h1>${quoteHtml(page)}
        <div class="riskMap">${page.points.map((x, i) => `<span><b>${String(i + 1).padStart(2, '0')}</b>${escapeHtml(x)}</span>`).join('')}</div>
      </div>
    </section>`;
  }
  if (page.layout === 'process') {
    return `<section class="poster xhs process" id="${page.id}">
      <div class="grid"></div><div class="content">
        ${top(page)}<h1>${titleHtml(page.title)}</h1>${quoteHtml(page)}
        <div class="processFlow">${page.points.map((x, i) => `<span><b>${String(i + 1).padStart(2, '0')}</b>${escapeHtml(x)}</span>`).join('')}</div>
      </div>
    </section>`;
  }
  if (page.layout === 'ethics') {
    return `<section class="poster xhs ethics" id="${page.id}">
      <div class="grid"></div>${photo(page.image, 'rightPhoto')}
      <div class="content">
        ${top(page)}<h1>${titleHtml(page.title)}</h1>${quoteHtml(page)}
        <div class="ethicsStack">${page.points.map((x, i) => `<span><b>${String(i + 1).padStart(2, '0')}</b>${escapeHtml(x)}</span>`).join('')}</div>
      </div>
    </section>`;
  }
  if (page.layout === 'sandbox') {
    return `<section class="poster xhs sandbox" id="${page.id}">
      <div class="grid"></div>${photo(page.image, 'texture')}
      <div class="content">
        ${top(page)}<h1>${titleHtml(page.title)}</h1>${quoteHtml(page)}
        <div class="sandboxBox">${page.points.map((x, i) => `<span><b>${String(i + 1).padStart(2, '0')}</b>${escapeHtml(x)}</span>`).join('')}</div>
      </div>
    </section>`;
  }
  if (page.layout === 'rights') {
    return `<section class="poster xhs rights" id="${page.id}">
      <div class="grid"></div><div class="content">
        ${top(page)}<h1>${titleHtml(page.title)}</h1>${quoteHtml(page)}
        <div class="rightsLane">${page.points.map((x, i) => `<span><b>${String(i + 1).padStart(2, '0')}</b>${escapeHtml(x)}</span>`).join('')}</div>
      </div>
    </section>`;
  }
  if (page.layout === 'global') {
    return `<section class="poster xhs global" id="${page.id}">
      <div class="grid"></div>${photo(page.image, 'fadePhoto')}
      <div class="content">
        ${top(page)}<h1>${titleHtml(page.title)}</h1>${quoteHtml(page)}
        <div class="globalGrid">${page.points.map((x) => `<span>${escapeHtml(x)}</span>`).join('')}</div>
      </div>
    </section>`;
  }
  if (page.layout === 'formula') {
    return `<section class="poster xhs formula" id="${page.id}">
      <div class="grid"></div><div class="content">
        ${top(page)}<h1>${titleHtml(page.title)}</h1>${quoteHtml(page)}
        <div class="formulaBlocks">${page.points.map((x) => `<span>${escapeHtml(x)}</span>`).join('')}</div>
      </div>
    </section>`;
  }
  if (page.layout === 'closing') {
    return `<section class="poster xhs closing" id="${page.id}">
      <div class="grid"></div>${photo(page.image, 'closePhoto')}
      <div class="content">
        ${top(page)}<h1>${titleHtml(page.title)}</h1>${quoteHtml(page)}
        <div class="closingWords">${page.points.map((x) => `<span>${escapeHtml(x)}</span>`).join('')}</div>
      </div>
    </section>`;
  }
  return '';
}

function renderVideo(id, image, title, subtitle, variant) {
  const meta = photoMeta[image];
  return `<section class="poster video v${variant}" id="${id}">
    <figure class="videoPhoto">
      <!-- Subject map: ${meta.map} Full-bleed cover uses localized title tint in safe zone and keeps subject visible. -->
      <img src="${rel(image)}" alt="" style="object-position:${variant === 1 ? 'center 48%' : 'center 50%'};">
    </figure>
    <div class="videoTint"></div>
    <div class="magRule"></div>
    <div class="videoTitle">
      <p>《人民日报》这样写</p>
      <h2>${titleHtml(title)}</h2>
      <span>${escapeHtml(subtitle)}</span>
    </div>
  </section>`;
}

const videos = [
  renderVideo('video-cover-01', 'robot-hand-network.jpg', 'AI治理\\n怎么写', '既给创新空间，也守伦理底线', 1),
  renderVideo('video-cover-02', 'robot-arm-gray.jpg', '不是设墙\\n而是铺轨', '创新空间 / 伦理底线 / 责任闭环', 2)
];

const css = `
*{box-sizing:border-box}html,body{margin:0;padding:0}body{background:#d2d3d3;font-family:"Inter","Avenir Next","Helvetica Neue","PingFang SC","Noto Sans SC","Microsoft YaHei",sans-serif;color:#141414}.stage{width:max-content;display:grid;gap:34px;padding:34px}.poster{position:relative;overflow:hidden;isolation:isolate;background:#e5e5e5;color:#141414}.xhs,.video{width:1080px;height:1440px}.grid{position:absolute;inset:0;z-index:0;background:linear-gradient(90deg,rgba(20,20,20,.06) 1px,transparent 1px),linear-gradient(180deg,rgba(20,20,20,.06) 1px,transparent 1px);background-size:72px 72px}.content{position:relative;z-index:4;height:100%;padding:58px;display:flex;flex-direction:column}.top{display:flex;align-items:center;justify-content:space-between;gap:24px;border-bottom:2px solid rgba(20,20,20,.22);padding-bottom:22px;font-size:24px;line-height:1;font-weight:820;text-transform:uppercase}.top span:first-child{font-size:36px;color:#ff6900;font-weight:900}.label{margin:34px 0 0;color:#5b5d5f;font-size:26px;font-weight:820}.xhs h1{margin:30px 0 0;font-size:88px;line-height:1.02;font-weight:520;letter-spacing:0}.quote{margin:28px 0 0;padding:26px 28px;border-left:10px solid #ff6900;background:rgba(247,247,244,.78);font-size:36px;line-height:1.36;font-weight:780}.quote.med{font-size:32px}.quote.long{font-size:29px;line-height:1.34}.photo{margin:0;overflow:hidden}.photo img,.videoPhoto img{width:100%;height:100%;object-fit:cover;filter:grayscale(.18) saturate(.76) contrast(1.06) brightness(.94)}.bleed{position:absolute;inset:0;z-index:1}.cover .cover-tint{position:absolute;inset:0;z-index:2;background:linear-gradient(180deg,rgba(229,229,229,.92),rgba(229,229,229,.80) 42%,rgba(229,229,229,.28)),linear-gradient(90deg,rgba(229,229,229,.96),rgba(229,229,229,.22) 72%)}.cover .grid{z-index:3}.cover .content{z-index:4}.cover h1{font-size:106px;font-weight:470}.cover .subtitle{margin-top:34px;max-width:790px;padding:22px 24px;background:#ff6900;color:#fff;font-size:36px;font-weight:880;line-height:1.18}.track{margin-top:auto;display:grid;grid-template-columns:repeat(3,1fr);gap:12px}.track span{height:176px;display:grid;place-items:center;background:#171717;color:#f7f7f4;font-size:34px;font-weight:820}.matrix{margin-top:auto;display:grid;grid-template-columns:repeat(2,1fr);gap:16px}.matrix span{height:248px;padding:24px;display:grid;align-content:space-between;background:#f7f7f4;border:2px solid rgba(20,20,20,.14);font-size:38px;font-weight:760}.matrix b{font-size:22px;color:#ff6900}.chainLine{margin-top:60px;display:grid;grid-template-columns:repeat(3,1fr);gap:14px}.chainLine span{position:relative;height:360px;padding:26px 22px;display:grid;place-items:center;text-align:center;background:#171717;color:#f7f7f4;font-size:38px;line-height:1.12;font-weight:780}.chainLine span:not(:last-child):after{content:"";position:absolute;right:-25px;top:50%;width:36px;height:4px;background:#ff6900;z-index:3}.chainLine b{display:block;margin-bottom:24px;color:#ff6900;font-size:28px}.rail{margin-top:auto;height:108px;padding:0 28px;display:flex;align-items:center;justify-content:space-between;background:#ff6900;color:#fff;font-size:34px;font-weight:900}.rail i{height:4px;flex:1;margin:0 24px;background:rgba(255,255,255,.8)}.wide{position:absolute;left:58px;right:58px;bottom:58px;height:430px;border:3px solid rgba(20,20,20,.18);z-index:1}.photoGrid .content{padding-bottom:560px}.chips{position:absolute;left:58px;right:58px;bottom:508px;display:grid;grid-template-columns:repeat(5,1fr);gap:10px}.chips span{height:130px;padding:18px 12px;display:grid;align-content:space-between;background:#171717;color:#fff;font-size:24px;line-height:1.08;font-weight:820}.chips b{display:block;color:#ff6900;font-size:18px}.bottomPhoto{position:absolute;left:58px;right:58px;bottom:58px;height:410px;border:3px solid rgba(20,20,20,.18);z-index:1}.energy .content{padding-bottom:540px}.loop{margin-top:64px;display:grid;grid-template-columns:repeat(2,1fr);gap:16px}.loop span{height:190px;display:grid;place-items:center;text-align:center;background:#f7f7f4;border-left:14px solid #ff6900;font-size:34px;font-weight:800}.sidePhoto{position:absolute;left:58px;right:58px;bottom:58px;height:360px;border:3px solid rgba(20,20,20,.18);z-index:1}.risk .content{padding-bottom:470px}.riskMap{margin-top:36px;display:grid;grid-template-columns:repeat(5,1fr);gap:10px}.riskMap span{height:260px;padding:18px 12px;display:grid;align-content:space-between;background:#171717;color:#fff;font-size:25px;line-height:1.08;font-weight:820}.riskMap b{font-size:19px;color:#ff6900}.processFlow{margin-top:auto;display:grid;grid-template-columns:1fr;gap:15px}.processFlow span{height:135px;padding:0 28px;display:flex;align-items:center;gap:24px;background:#f7f7f4;border-left:12px solid #ff6900;font-size:36px;font-weight:800}.processFlow b{font-size:24px;color:#6a6c6f}.rightPhoto{position:absolute;right:0;top:0;bottom:0;width:420px;z-index:1}.rightPhoto:after{content:"";position:absolute;inset:0;background:linear-gradient(90deg,#e5e5e5,rgba(229,229,229,.2))}.ethics .content{padding-right:440px}.ethicsStack{margin-top:auto;display:grid;gap:12px}.ethicsStack span{height:104px;padding:0 22px;display:flex;align-items:center;gap:18px;background:#f7f7f4;border-left:10px solid #ff6900;font-size:30px;font-weight:800}.ethicsStack b{font-size:22px;color:#6a6c6f}.texture{position:absolute;inset:0;z-index:1}.texture img{filter:grayscale(.35) saturate(.46) brightness(.82)}.sandbox .grid{z-index:2}.sandbox .content{z-index:3}.sandbox:after{content:"";position:absolute;inset:0;z-index:2;background:linear-gradient(180deg,rgba(229,229,229,.94),rgba(229,229,229,.82) 54%,rgba(229,229,229,.60))}.sandboxBox{margin-top:auto;display:grid;grid-template-columns:repeat(4,1fr);gap:12px}.sandboxBox span{height:420px;padding:26px 14px;display:grid;align-content:space-between;text-align:center;background:#171717;color:#fff;font-size:34px;line-height:1.1;font-weight:800}.sandboxBox b{color:#ff6900;font-size:26px}.rightsLane{margin-top:46px;display:grid;gap:12px}.rightsLane span{height:110px;padding:0 24px;display:flex;align-items:center;gap:20px;background:#f7f7f4;border-left:12px solid #ff6900;font-size:32px;font-weight:800}.rightsLane b{font-size:23px;color:#6a6c6f}.fadePhoto{position:absolute;inset:auto 58px 58px 58px;height:430px;border:3px solid rgba(20,20,20,.18);z-index:1}.fadePhoto img{object-position:center 52%;filter:grayscale(.08) saturate(.72) contrast(1.08) brightness(.9)}.global .content{padding-bottom:560px}.globalGrid{position:absolute;left:58px;right:58px;bottom:502px;display:grid;grid-template-columns:repeat(4,1fr);gap:10px}.globalGrid span{height:150px;display:grid;place-items:center;background:#171717;color:#fff;font-size:30px;font-weight:820}.formula .quote{font-size:31px}.formulaBlocks{margin-top:auto;display:grid;grid-template-columns:repeat(3,1fr);gap:14px}.formulaBlocks span{height:500px;display:grid;place-items:center;text-align:center;background:#171717;color:#fff;font-size:42px;line-height:1.08;font-weight:820}.formulaBlocks span:nth-child(2){background:#ff6900}.closePhoto{position:absolute;left:58px;right:58px;bottom:58px;height:395px;border:3px solid rgba(20,20,20,.18);z-index:1}.closing .content{padding-bottom:520px}.closing .quote{font-size:32px}.closingWords{margin-top:44px;display:grid;grid-template-columns:repeat(5,1fr);gap:10px}.closingWords span{height:160px;display:grid;place-items:center;text-align:center;background:#171717;color:#fff;font-size:28px;font-weight:820}.closingWords span:nth-child(2),.closingWords span:nth-child(5){background:#ff6900}.videoPhoto{position:absolute;inset:0;margin:0;z-index:1}.videoPhoto img{filter:grayscale(.06) saturate(.82) contrast(1.08) brightness(.84)}.videoTint{position:absolute;inset:0;z-index:2;background:linear-gradient(180deg,rgba(0,0,0,.12),rgba(0,0,0,.18) 45%,rgba(0,0,0,.54)),linear-gradient(90deg,rgba(0,0,0,.58),rgba(0,0,0,.06) 64%)}.v1 .videoTint{background:linear-gradient(180deg,rgba(0,0,0,.18),rgba(0,0,0,.18) 40%,rgba(0,0,0,.50)),linear-gradient(90deg,rgba(0,0,0,.62),rgba(0,0,0,.08) 70%)}.magRule{position:absolute;inset:56px;z-index:3;border-top:2px solid rgba(255,255,255,.66);border-bottom:2px solid rgba(255,255,255,.48)}.magRule:before{content:"";position:absolute;left:0;top:94px;width:190px;height:2px;background:rgba(255,255,255,.58)}.videoTitle{position:absolute;left:64px;right:120px;bottom:96px;z-index:4;color:#f8f5ec}.v1 .videoTitle{top:128px;bottom:auto}.videoTitle p{margin:0 0 28px;font-size:31px;line-height:1;font-weight:840}.videoTitle h2{margin:0;font-family:"Songti SC","STSong","Noto Serif CJK SC",serif;font-size:112px;line-height:.98;font-weight:740;letter-spacing:0}.videoTitle span{display:block;width:max-content;max-width:790px;margin-top:28px;padding:14px 18px;background:#ff6900;color:#fff;font-size:31px;font-weight:860}.preview{width:1800px;background:#e2e2e2;padding:34px;display:grid;grid-template-columns:repeat(5,1fr);gap:18px}.preview figure{margin:0;background:#fff;padding:8px}.preview img{width:100%;display:block}.preview figcaption{padding:8px 2px 0;font-size:16px;font-weight:780;color:#303030}
`;

const html = `<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>AI治理小红书与视频号封面</title><style>${css}</style></head><body><main class="stage">${pages.map(renderPage).join('\n')}${videos.join('\n')}</main></body></html>`;
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
