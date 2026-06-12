import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { chromium } from 'playwright';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const repoRoot = path.resolve(__dirname, '../../../..');
const mediaDir = path.join(repoRoot, 'media/images/2026-06-12-arrears-payment-confidence-chain-xhs-video');
const assetDir = path.join(mediaDir, 'assets');
const htmlPath = path.join(__dirname, 'index.html');

const out = (file) => path.join(mediaDir, file);
const rel = (file) => path.relative(__dirname, path.join(assetDir, file)).replaceAll(path.sep, '/');

const pages = [
  {
    id: 'xhs-01-cover',
    no: '01',
    tag: '清欠账款',
    title: '清欠账款怎么写\\n账款链也是信心链',
    quote: '不是财务小事，而是稳企业、稳就业、稳预期。',
    points: ['旧账', '现金流', '信用', '预期'],
    image: 'accounting-documents.jpg',
    layout: 'cover'
  },
  {
    id: 'xhs-02-mistake',
    no: '02',
    tag: '常见误区',
    title: '很多人\\n把清欠写小了',
    quote: '这些话都对，但太像空泛对策。',
    points: ['开展专项整治', '加强督查问责', '及时支付欠款', '优化营商环境'],
    layout: 'mistake'
  },
  {
    id: 'xhs-03-chain',
    no: '03',
    tag: '核心主线',
    title: '记住\\n这条信心链',
    quote: '账款链也是信心链。',
    points: ['旧账不清：损害政府公信力', '款项拖欠：压住企业现金流', '承诺兑现：稳住市场预期'],
    layout: 'chain'
  },
  {
    id: 'xhs-04-performance',
    no: '04',
    tag: '第一层',
    title: '新官\\n要理旧账',
    quote: '理旧账，不是替前任收尾，而是为发展清障。',
    points: ['履职条件', '企业账款', '群众承诺', '政府信用'],
    image: 'business-building.jpg',
    layout: 'photoTop'
  },
  {
    id: 'xhs-05-cashflow',
    no: '05',
    tag: '第二层',
    title: '账款拖欠\\n压住的是现金流',
    quote: '对小微企业来说，账款不是数字，是工资、材料款、贷款和订单。',
    points: ['6000余万元', '51万余元', '70万元', '140余万元'],
    image: 'cash-flow.jpg',
    layout: 'cash'
  },
  {
    id: 'xhs-06-classify',
    no: '06',
    tag: '分类清欠',
    title: '清欠不能\\n一刀切',
    quote: '能付快付，应审快审，有争议就依法处理。',
    points: ['无争议款项：先行支付', '待审计款项：加快审计', '争议款项：依法解纷', '困难企业：同步纾困'],
    layout: 'classify'
  },
  {
    id: 'xhs-07-rule',
    no: '07',
    tag: '第三层',
    title: '营商环境\\n看兑现',
    quote: '合同能履行、承诺能兑现、权益能救济，才是真营商环境。',
    points: ['依法核实解决', '行政允诺不随意变', '不转嫁付款风险'],
    image: 'law-gavel.jpg',
    layout: 'rule'
  },
  {
    id: 'xhs-08-execution',
    no: '08',
    tag: '第四层',
    title: '执行也要\\n托住信心',
    quote: '执行既要实现债权，也要尽量保住经营能力。',
    points: ['观察期', '分期还款', '执行和解', '恢复经营'],
    image: 'logistics-warehouse.jpg',
    layout: 'execution'
  },
  {
    id: 'xhs-09-finance',
    no: '09',
    tag: '第五层',
    title: '金融适配\\n缓解周转',
    quote: '金融支持不能替代付款责任。',
    points: ['供应链金融', '应收账款融资', '订单贷', '信用贷款'],
    image: 'warehouse-supply-chain.jpg',
    layout: 'finance'
  },
  {
    id: 'xhs-10-formula',
    no: '10',
    tag: '申论公式',
    title: '申论\\n这样写',
    quote: '解决拖欠企业账款，要把“清旧账”和“建新信”结合起来：以正确政绩观接续履责，以政务诚信兑现承诺，以规范执行保障权益，以金融适配缓解周转，以长效制度防止新增拖欠。',
    points: ['清旧账', '建新信', '接续履责', '兑现承诺', '防新增拖欠'],
    layout: 'formula',
    sourceQuote: true
  },
  {
    id: 'xhs-11-interview',
    no: '11',
    tag: '面试答法',
    title: '面试\\n这样答',
    quote: '企业反映政府投资项目拖欠账款，你牵头协调怎么办？',
    points: ['先核账：合同、金额、主体、争议', '再分类：无争议快付，待审计快审', '再协同：财政、审计、主管部门、清欠办', '再闭环：台账销号，反馈进度，防止新增'],
    layout: 'interview'
  },
  {
    id: 'xhs-12-closing',
    no: '12',
    tag: '收束金句',
    title: '最后记住\\n一句话',
    quote: '清旧账，不只是解决过去的问题；建新信，才是托住未来发展的关键。',
    points: ['修复政府信用', '稳定企业经营', '保护合法权益', '缓解周转压力'],
    image: 'finance-ledger.jpg',
    layout: 'closing'
  }
];

const photoMeta = {
  'accounting-documents.jpg': {
    pos: 'center 56%',
    map: 'calculator and tax documents sit around the center-lower area; safe title zone is upper-left dark table and left-middle overlay.'
  },
  'finance-ledger.jpg': {
    pos: 'center 54%',
    map: 'stacked folders fill the lower and right side; safe title zone is upper-left light negative space.'
  },
  'business-building.jpg': {
    pos: 'center 50%',
    map: 'high-rise buildings converge upward; safe text zones are lower-left and upper sky after localized dark tint.'
  },
  'cash-flow.jpg': {
    pos: 'center 52%',
    map: 'cash texture fills the frame; no person subject; keep text in separate dark panels.'
  },
  'law-gavel.jpg': {
    pos: 'center 50%',
    map: 'gavel and justice figure sit middle-lower; keep titles left and do not cover focal object.'
  },
  'logistics-warehouse.jpg': {
    pos: 'center 52%',
    map: 'warehouse shelves and boxes fill the frame; use as business-flow evidence below text.'
  },
  'warehouse-supply-chain.jpg': {
    pos: 'center 52%',
    map: 'warehouse rows fill the frame; keep text in upper-left panel or separate blocks.'
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
  const cls = page.quote.length > 92 ? 'quote long' : page.quote.length > 48 ? 'quote med' : 'quote';
  return `<blockquote class="${cls}">${escapeHtml(page.quote)}</blockquote>`;
}

function smallCards(items = []) {
  return `<div class="smallCards">${items.map((x, i) => `<span><b>${String(i + 1).padStart(2, '0')}</b>${escapeHtml(x)}</span>`).join('')}</div>`;
}

function renderPage(page) {
  if (page.layout === 'cover') {
    return `<section class="poster xhs cover" id="${page.id}">
      ${photo(page.image, 'bleed')}<div class="coverTint"></div><div class="paper"></div>
      <div class="content">
        ${top(page)}
        <p class="eyebrow">人民日报材料转申论</p>
        <h1>${titleHtml(page.title)}</h1>
        <div class="subtitle">${escapeHtml(page.quote)}</div>
        <div class="chainNodes">${page.points.map((x) => `<span>${escapeHtml(x)}</span>`).join('<i></i>')}</div>
      </div>
    </section>`;
  }
  if (page.layout === 'mistake') {
    return `<section class="poster xhs mistake" id="${page.id}">
      <div class="paper"></div><div class="content">
        ${top(page)}<h1>${titleHtml(page.title)}</h1>${quoteHtml(page)}
        <div class="mistakeGrid">${page.points.map((x, i) => `<span><b>误区 ${String(i + 1).padStart(2, '0')}</b>${escapeHtml(x)}</span>`).join('')}</div>
      </div>
    </section>`;
  }
  if (page.layout === 'chain') {
    return `<section class="poster xhs confidence" id="${page.id}">
      <div class="paper"></div><div class="content">
        ${top(page)}<h1>${titleHtml(page.title)}</h1>${quoteHtml(page)}
        <div class="confidenceChain">${page.points.map((x, i) => `<span><b>0${i + 1}</b>${escapeHtml(x)}</span>`).join('<i></i>')}</div>
        <div class="footLine"><em>旧账不清</em><strong>信心链受损</strong><em>承诺兑现</em></div>
      </div>
    </section>`;
  }
  if (page.layout === 'photoTop') {
    return `<section class="poster xhs photoTop" id="${page.id}">
      <div class="paper"></div>${photo(page.image, 'topPhoto')}
      <div class="content">${top(page)}<h1>${titleHtml(page.title)}</h1>${quoteHtml(page)}${smallCards(page.points)}</div>
    </section>`;
  }
  if (page.layout === 'cash') {
    return `<section class="poster xhs cash" id="${page.id}">
      <div class="paper"></div>${photo(page.image, 'cashPhoto')}
      <div class="content">${top(page)}<h1>${titleHtml(page.title)}</h1>${quoteHtml(page)}
      <div class="moneyStrip">${page.points.map((x) => `<span>${escapeHtml(x)}</span>`).join('')}</div></div>
    </section>`;
  }
  if (page.layout === 'classify') {
    return `<section class="poster xhs classify" id="${page.id}">
      <div class="paper"></div><div class="content">${top(page)}<h1>${titleHtml(page.title)}</h1>${quoteHtml(page)}
      <div class="classGrid">${page.points.map((x, i) => `<span><b>${String(i + 1).padStart(2, '0')}</b>${escapeHtml(x)}</span>`).join('')}</div></div>
    </section>`;
  }
  if (page.layout === 'rule') {
    return `<section class="poster xhs rule" id="${page.id}">
      <div class="paper"></div>${photo(page.image, 'rulePhoto')}
      <div class="content">${top(page)}<h1>${titleHtml(page.title)}</h1>${quoteHtml(page)}
      <div class="ruleList">${page.points.map((x) => `<span>${escapeHtml(x)}</span>`).join('')}</div></div>
    </section>`;
  }
  if (page.layout === 'execution') {
    return `<section class="poster xhs execution" id="${page.id}">
      <div class="paper"></div>${photo(page.image, 'bottomPhoto')}
      <div class="content">${top(page)}<h1>${titleHtml(page.title)}</h1>${quoteHtml(page)}
      <div class="execFlow">${page.points.map((x) => `<span>${escapeHtml(x)}</span>`).join('<i></i>')}</div></div>
    </section>`;
  }
  if (page.layout === 'finance') {
    return `<section class="poster xhs finance" id="${page.id}">
      <div class="paper"></div>${photo(page.image, 'financePhoto')}
      <div class="content">${top(page)}<h1>${titleHtml(page.title)}</h1>${quoteHtml(page)}
      <div class="financeGrid">${page.points.map((x) => `<span>${escapeHtml(x)}</span>`).join('')}</div></div>
    </section>`;
  }
  if (page.layout === 'formula') {
    return `<section class="poster xhs formula" id="${page.id}">
      <div class="paper"></div><div class="content">${top(page)}<h1>${titleHtml(page.title)}</h1>${quoteHtml(page)}
      <div class="formulaBlocks">${page.points.map((x) => `<span>${escapeHtml(x)}</span>`).join('')}</div></div>
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
      <div class="paper"></div>${photo(page.image, 'closePhoto')}
      <div class="content">${top(page)}<h1>${titleHtml(page.title)}</h1>${quoteHtml(page)}
      <div class="closingGrid">${page.points.map((x) => `<span>${escapeHtml(x)}</span>`).join('')}</div></div>
    </section>`;
  }
  return '';
}

function renderVideo(id, image, title, subtitle, variant) {
  const meta = photoMeta[image];
  return `<section class="poster video v${variant}" id="${id}">
    <figure class="videoPhoto">
      <!-- Subject map: ${meta.map} Magazine title sits in a safe zone with localized green-black tint. -->
      <img src="${rel(image)}" alt="" style="object-position:${variant === 2 ? 'center 58%' : 'center 52%'};">
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
  renderVideo('video-cover-01', 'accounting-documents.jpg', '清欠账款怎么写\\n账款链也是信心链', '不是财务小事，而是稳企业、稳就业、稳预期', 1),
  renderVideo('video-cover-02', 'business-building.jpg', '清欠账款怎么写\\n账款链也是信心链', '清旧账 / 建新信', 2),
  renderVideo('video-cover-03', 'warehouse-supply-chain.jpg', '清欠账款怎么写\\n账款链也是信心链', '现金流 / 政务诚信 / 长效制度', 3)
];

const css = `
*{box-sizing:border-box}html,body{margin:0;padding:0}body{background:#dce4dd;font-family:"Avenir Next","Helvetica Neue","PingFang SC","Noto Sans SC","Microsoft YaHei",Arial,sans-serif;color:#18231d}.stage{width:max-content;display:grid;gap:34px;padding:34px}.poster{position:relative;overflow:hidden;isolation:isolate;background:#f6f5ec}.xhs,.video{width:1080px;height:1440px}.paper{position:absolute;inset:0;z-index:0;background:linear-gradient(90deg,rgba(24,35,29,.055) 1px,transparent 1px),linear-gradient(180deg,rgba(24,35,29,.052) 1px,transparent 1px),radial-gradient(circle at 80% 14%,rgba(65,147,117,.22),transparent 30%),linear-gradient(180deg,#f6f5ec,#e8eee8);background-size:72px 72px,72px 72px,auto,auto}.content{position:relative;z-index:4;height:100%;padding:58px;display:flex;flex-direction:column}.top{display:flex;align-items:center;justify-content:space-between;gap:24px;border-bottom:2px solid rgba(24,35,29,.22);padding-bottom:22px;font-size:24px;line-height:1;font-weight:820}.top span:first-child{font-size:36px;color:#419375;font-weight:900}.eyebrow{margin:34px 0 0;color:#49635a;font-size:26px;font-weight:820}.xhs h1{margin:30px 0 0;font-size:80px;line-height:1.04;font-weight:560;letter-spacing:0}.quote{margin:28px 0 0;padding:25px 28px;border-left:10px solid #419375;background:rgba(255,255,250,.9);font-size:37px;line-height:1.34;font-weight:820}.quote.med{font-size:32px}.quote.long{font-size:26px;line-height:1.42}.photo{margin:0;overflow:hidden}.photo img,.videoPhoto img{width:100%;height:100%;object-fit:cover;filter:saturate(.78) contrast(1.06) brightness(.92)}.bleed{position:absolute;inset:0;z-index:1}.coverTint{position:absolute;inset:0;z-index:2;background:linear-gradient(180deg,rgba(246,245,236,.88),rgba(246,245,236,.72) 36%,rgba(15,44,36,.50)),linear-gradient(90deg,rgba(246,245,236,.96),rgba(246,245,236,.25) 74%)}.cover .paper{z-index:3;background:linear-gradient(90deg,rgba(24,35,29,.07) 1px,transparent 1px),linear-gradient(180deg,rgba(24,35,29,.065) 1px,transparent 1px);background-size:72px 72px}.cover h1{font-size:83px;font-weight:540;max-width:930px}.subtitle{margin-top:30px;max-width:900px;padding:22px 26px;background:#419375;color:#fff;font-size:32px;font-weight:900}.chainNodes{margin-top:auto;display:grid;grid-template-columns:1fr 36px 1fr 36px 1fr 36px 1fr;align-items:center}.chainNodes span{height:150px;display:grid;place-items:center;text-align:center;background:#0f2c24;color:#fff;font-size:31px;font-weight:900}.chainNodes span:nth-of-type(2){background:#c7a15d;color:#18231d}.chainNodes span:nth-of-type(4){background:#419375}.chainNodes i{height:5px;background:#419375}.mistakeGrid{margin-top:auto;display:grid;grid-template-columns:repeat(2,1fr);gap:16px}.mistakeGrid span{height:238px;padding:24px;display:grid;align-content:space-between;background:#fffdf6;border:2px solid rgba(65,147,117,.22);font-size:34px;font-weight:790}.mistakeGrid b{font-size:22px;color:#419375}.confidenceChain{margin-top:50px;display:grid;grid-template-columns:1fr 34px 1fr 34px 1fr;align-items:center}.confidenceChain span{height:355px;padding:24px;display:grid;align-content:space-between;text-align:left;background:#0f2c24;color:#fff;font-size:32px;line-height:1.24;font-weight:850}.confidenceChain span:nth-of-type(2){background:#419375}.confidenceChain b{display:block;color:#cbe7dc;font-size:28px}.confidenceChain i{height:5px;background:#419375}.footLine{margin-top:auto;height:110px;padding:0 28px;display:flex;align-items:center;justify-content:space-between;background:#419375;color:#fff;font-size:28px;font-weight:880}.footLine strong{color:#ffe0a3}.topPhoto{position:absolute;left:58px;right:58px;bottom:58px;height:430px;border:3px solid rgba(65,147,117,.35);z-index:1}.photoTop .content{padding-bottom:560px}.smallCards{margin-top:42px;display:grid;grid-template-columns:repeat(4,1fr);gap:12px}.smallCards span{height:142px;padding:16px;display:grid;align-content:space-between;text-align:center;background:#0f2c24;color:#fff;font-size:24px;font-weight:850}.smallCards b{color:#9bd2bf;font-size:18px}.cashPhoto{position:absolute;left:58px;right:58px;bottom:58px;height:390px;border:3px solid rgba(65,147,117,.35);z-index:1}.cash .content{padding-bottom:520px}.moneyStrip{margin-top:42px;display:grid;grid-template-columns:repeat(4,1fr);gap:12px}.moneyStrip span{height:142px;display:grid;place-items:center;text-align:center;background:#0f2c24;color:#fff;font-size:27px;font-weight:900}.moneyStrip span:nth-child(1){background:#b85f54}.moneyStrip span:nth-child(4){background:#419375}.classGrid{margin-top:auto;display:grid;grid-template-columns:repeat(2,1fr);gap:14px}.classGrid span{height:230px;padding:24px;display:grid;align-content:space-between;background:#fffdf6;border-top:14px solid #419375;font-size:31px;line-height:1.2;font-weight:850}.classGrid b{font-size:24px;color:#419375}.rulePhoto{position:absolute;right:0;top:0;bottom:0;width:430px;z-index:1}.rulePhoto img{filter:saturate(.62) contrast(1.05) brightness(.85)}.rule:after{content:"";position:absolute;right:0;top:0;bottom:0;width:560px;z-index:2;background:linear-gradient(90deg,#f6f5ec 0%,rgba(246,245,236,.74) 42%,rgba(246,245,236,.08) 100%)}.rule .content{padding-right:410px}.ruleList{margin-top:auto;display:grid;gap:12px}.ruleList span{height:96px;padding:0 22px;display:flex;align-items:center;background:#0f2c24;color:#fff;border-left:12px solid #419375;font-size:27px;font-weight:850}.bottomPhoto{position:absolute;left:58px;right:58px;bottom:58px;height:390px;border:3px solid rgba(65,147,117,.35);z-index:1}.execution .content{padding-bottom:520px}.execFlow{margin-top:42px;display:grid;grid-template-columns:1fr 28px 1fr 28px 1fr 28px 1fr;align-items:center}.execFlow span{height:145px;padding:0 12px;display:grid;place-items:center;text-align:center;background:#0f2c24;color:#fff;font-size:26px;font-weight:900}.execFlow i{height:4px;background:#419375}.financePhoto{position:absolute;left:58px;right:58px;bottom:58px;height:395px;border:3px solid rgba(65,147,117,.35);z-index:1}.finance .content{padding-bottom:525px}.financeGrid{margin-top:44px;display:grid;grid-template-columns:repeat(2,1fr);gap:14px}.financeGrid span{height:138px;display:grid;place-items:center;text-align:center;background:#fffdf6;border-left:12px solid #419375;font-size:29px;font-weight:850}.formula h1{font-size:94px}.formula .quote{font-size:28px;line-height:1.42;margin-top:40px}.formulaBlocks{margin-top:40px;display:grid;grid-template-columns:repeat(5,1fr);gap:10px}.formulaBlocks span{height:260px;padding:0 8px;display:grid;place-items:center;text-align:center;background:#0f2c24;color:#fff;font-size:25px;font-weight:880}.formulaBlocks span:nth-child(2){background:#419375}.formulaBlocks span:nth-child(5){background:#c7a15d;color:#18231d}.answerSteps{margin-top:42px;display:grid;gap:14px}.answerSteps span{height:128px;padding:0 24px;display:flex;align-items:center;gap:20px;background:#fffdf6;border-left:12px solid #419375;font-size:27px;line-height:1.22;font-weight:850}.answerSteps b{font-size:22px;color:#419375}.closePhoto{position:absolute;left:58px;right:58px;bottom:58px;height:385px;border:3px solid rgba(65,147,117,.35);z-index:1}.closing .content{padding-bottom:515px}.closing .quote{font-size:32px}.closingGrid{margin-top:44px;display:grid;grid-template-columns:repeat(4,1fr);gap:12px}.closingGrid span{height:150px;padding:0 12px;display:grid;place-items:center;text-align:center;background:#0f2c24;color:#fff;font-size:25px;font-weight:880}.closingGrid span:nth-child(2),.closingGrid span:nth-child(4){background:#419375}.videoPhoto{position:absolute;inset:0;margin:0;z-index:1}.videoPhoto img{filter:saturate(.78) contrast(1.08) brightness(.72)}.videoTint{position:absolute;inset:0;z-index:2;background:linear-gradient(180deg,rgba(10,24,18,.08),rgba(10,24,18,.18) 42%,rgba(10,24,18,.72)),linear-gradient(90deg,rgba(10,24,18,.82),rgba(10,24,18,.12) 75%)}.magFrame{position:absolute;inset:56px;z-index:3;border-top:2px solid rgba(255,255,255,.64);border-bottom:2px solid rgba(255,255,255,.44)}.magFrame:before{content:"";position:absolute;left:0;top:96px;width:190px;height:2px;background:rgba(255,255,255,.54)}.videoTitle{position:absolute;left:64px;right:88px;bottom:92px;z-index:4;color:#fffdf6}.v1 .videoTitle{top:118px;bottom:auto}.v2 .videoTitle{bottom:118px}.videoTitle p{margin:0 0 28px;font-size:31px;line-height:1;font-weight:840}.videoTitle h2{margin:0;font-family:"Songti SC","STSong","Noto Serif CJK SC",serif;font-size:88px;line-height:1.02;font-weight:760;letter-spacing:0}.videoTitle span{display:block;width:max-content;max-width:850px;margin-top:26px;padding:14px 18px;background:#419375;color:#fff;font-size:28px;font-weight:900}.preview{width:1800px;background:#dce4dd;padding:34px;display:grid;grid-template-columns:repeat(5,1fr);gap:18px}.preview figure{margin:0;background:#fff;padding:8px}.preview img{width:100%;display:block}.preview figcaption{padding:8px 2px 0;font-size:16px;font-weight:780;color:#303030}
`;

const html = `<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>清欠账款小红书与视频号封面</title><style>${css}</style></head><body><main class="stage">${pages.map(renderPage).join('\n')}${videos.join('\n')}</main></body></html>`;
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

for (const id of ['video-cover-01', 'video-cover-02', 'video-cover-03']) {
  await page.locator(`#${id}`).screenshot({ path: out(`${id}.png`) });
  outputFiles.push(`${id}.png`);
}

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
