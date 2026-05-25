import fs from "node:fs/promises";
import path from "node:path";
import { spawnSync } from "node:child_process";
import { fileURLToPath } from "node:url";
import os from "node:os";
import { chromium } from "playwright";

const PACKAGE_DIR = path.dirname(fileURLToPath(import.meta.url));
const ANALYSIS_DIR = path.resolve(PACKAGE_DIR, "../..");
const REPO_ROOT = process.cwd().endsWith("PeopleDailyMaterial")
  ? process.cwd()
  : path.resolve(PACKAGE_DIR, "../../../../..");
const TOPIC_SLUG = "style-governance-problem-handling";

const SOURCE_HTML_DIR = path.join(PACKAGE_DIR, "source-html");
const WECHAT_DIR = path.join(PACKAGE_DIR, "wechat-images-16x9");
const XHS_DIR = path.join(PACKAGE_DIR, "xiaohongshu-images-3x4");
const PPT_DIR = path.join(PACKAGE_DIR, "ppt");

const PRESENTATIONS_SKILL_DIR = path.join(
  os.homedir(),
  ".codex/plugins/cache/openai-primary-runtime/presentations/26.521.10419/skills/presentations",
);
const PRESENTATION_BUILDER = path.join(PRESENTATIONS_SKILL_DIR, "scripts/build_artifact_deck.mjs");
const PYTHON = path.join(
  os.homedir(),
  ".cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3",
);

const threadId = process.env.CODEX_THREAD_ID || "manual-20260524-style-governance";
const WORKSPACE = path.join(REPO_ROOT, "outputs", threadId, "presentations", TOPIC_SLUG);
const SLIDES_DIR = path.join(WORKSPACE, "slides");
const PREVIEW_DIR = path.join(WORKSPACE, "preview");
const LAYOUT_DIR = path.join(WORKSPACE, "layout");
const QA_DIR = path.join(WORKSPACE, "qa");
const FINAL_PPTX = path.join(PPT_DIR, "style-governance-problem-handling-class.pptx");

const colors = {
  paper: "#f6efe3",
  paper2: "#fbf7ef",
  ink: "#173044",
  muted: "#647582",
  grid: "#d8e0e6",
  blue: "#1f4f77",
  red: "#b54836",
  teal: "#1f7972",
  gold: "#c39a3b",
  line: "#b7c6d2",
  white: "#ffffff",
};

const sources = [
  "规范涉企行政执法专项行动取得明显成效｜第04版",
  "完善制度机制 更好造福于民｜第04版",
  "办酒席时当“饭店”，闲下来开农家乐｜第08版",
  "“潮汐菜场”里的治理智慧｜第08版",
  "群众的事就是我们的事｜第05版",
  "“草原运河”映初心｜第05版",
];

function esc(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;");
}

function baseCss(width, height) {
  return `
    * { box-sizing: border-box; }
    html, body { margin: 0; width: ${width}px; height: ${height}px; }
    body {
      font-family: "PingFang SC", "Noto Sans CJK SC", "Microsoft YaHei", Arial, sans-serif;
      color: ${colors.ink};
      background: ${colors.paper};
    }
    .page {
      position: relative;
      width: ${width}px;
      height: ${height}px;
      overflow: hidden;
      background:
        linear-gradient(90deg, rgba(31,79,119,.08) 1px, transparent 1px),
        linear-gradient(0deg, rgba(31,79,119,.08) 1px, transparent 1px),
        radial-gradient(circle at 15% 18%, rgba(195,154,59,.16), transparent 28%),
        linear-gradient(135deg, ${colors.paper2}, ${colors.paper});
      background-size: 48px 48px, 48px 48px, 100% 100%, 100% 100%;
    }
    .page.dark {
      color: #f7efe2;
      background:
        linear-gradient(90deg, rgba(255,255,255,.06) 1px, transparent 1px),
        linear-gradient(0deg, rgba(255,255,255,.06) 1px, transparent 1px),
        linear-gradient(135deg, #102334, #193a4e 52%, #102334);
      background-size: 48px 48px, 48px 48px, 100% 100%;
    }
    .label {
      display: inline-flex;
      align-items: center;
      min-height: 44px;
      padding: 0 18px;
      border: 1px solid ${colors.line};
      color: ${colors.blue};
      background: rgba(255,255,255,.55);
      font-size: 24px;
      font-weight: 700;
      letter-spacing: 0;
    }
    .dark .label {
      color: #f8df9c;
      border-color: rgba(248,223,156,.48);
      background: rgba(255,255,255,.06);
    }
    .caption {
      color: ${colors.muted};
      font-size: 23px;
      line-height: 1.55;
    }
    .dark .caption { color: rgba(247,239,226,.74); }
    .small {
      color: ${colors.muted};
      font-size: 20px;
      line-height: 1.55;
    }
    .dark .small { color: rgba(247,239,226,.68); }
    .title {
      margin: 0;
      font-size: 88px;
      line-height: 1.12;
      letter-spacing: 0;
      font-weight: 900;
    }
    .title strong, .accent-red { color: ${colors.red}; }
    .accent-teal { color: ${colors.teal}; }
    .accent-gold { color: ${colors.gold}; }
    .dark .accent-gold { color: #f8d77d; }
    .panel {
      border: 1.5px solid ${colors.line};
      background: rgba(255,255,255,.62);
      box-shadow: 0 18px 40px rgba(23,48,68,.08);
    }
    .dark .panel {
      border-color: rgba(248,223,156,.32);
      background: rgba(255,255,255,.07);
      box-shadow: none;
    }
    .node {
      border: 2px solid ${colors.ink};
      background: rgba(255,255,255,.72);
      padding: 24px;
    }
    .node h3 {
      margin: 0 0 10px 0;
      font-size: 34px;
      line-height: 1.2;
    }
    .node p {
      margin: 0;
      color: ${colors.muted};
      font-size: 24px;
      line-height: 1.45;
    }
    .rule {
      height: 2px;
      background: ${colors.line};
    }
    .kicker {
      font-size: 26px;
      font-weight: 800;
      color: ${colors.blue};
    }
    .dark .kicker { color: #f8d77d; }
    .source {
      position: absolute;
      left: 72px;
      right: 72px;
      bottom: 40px;
      color: ${colors.muted};
      font-size: 20px;
      line-height: 1.4;
    }
    .dark .source { color: rgba(247,239,226,.62); }
    .xhs-title {
      margin: 0;
      font-size: 72px;
      line-height: 1.15;
      letter-spacing: 0;
      font-weight: 900;
    }
    .xhs-sub {
      font-size: 34px;
      line-height: 1.45;
      color: ${colors.muted};
    }
    .xhs-card {
      position: absolute;
      left: 72px;
      right: 72px;
      border: 1.5px solid ${colors.line};
      background: rgba(255,255,255,.68);
      padding: 34px 36px;
    }
    .xhs-card h3 {
      margin: 0 0 12px 0;
      font-size: 36px;
      line-height: 1.25;
      color: ${colors.ink};
    }
    .xhs-card p {
      margin: 0;
      font-size: 29px;
      line-height: 1.48;
      color: ${colors.muted};
    }
  `;
}

function doc(width, height, body, dark = false) {
  return `<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=${width}, initial-scale=1">
<style>${baseCss(width, height)}</style>
</head>
<body><main class="page${dark ? " dark" : ""}">${body}</main></body>
</html>`;
}

function sourceLine() {
  return "来源：人民日报 2026年05月22日；本图为申论与结构化面试教研转译。";
}

function wechatCover() {
  return doc(1920, 1080, `
    <div style="position:absolute; left:92px; top:80px;" class="label">人民日报 2026-05-22 教研转译</div>
    <h1 class="title" style="position:absolute; left:92px; top:178px; width:1030px;">
      别把政绩观<br>写成<span class="accent-red">口号</span>
    </h1>
    <div style="position:absolute; left:96px; top:426px; width:900px; font-size:44px; line-height:1.4; font-weight:800;">
      真正该学的是<br><span class="accent-teal" style="font-size:68px;">“把问题接住”</span>
    </div>
    <div class="panel" style="position:absolute; left:1110px; top:150px; width:620px; height:610px; padding:44px;">
      <div class="kicker">问题进入办理链</div>
      <div style="margin-top:34px; display:grid; gap:22px;">
        ${["问题清单", "责任清单", "办理清单", "反馈长效"].map((item, idx) => `
          <div style="display:flex; align-items:center; gap:18px;">
            <div style="width:50px; height:50px; border:2px solid ${idx === 0 ? colors.red : idx === 3 ? colors.gold : colors.teal}; display:flex; align-items:center; justify-content:center; font-size:24px; font-weight:900; color:${idx === 0 ? colors.red : idx === 3 ? colors.gold : colors.teal};">${idx + 1}</div>
            <div style="font-size:40px; font-weight:900;">${item}</div>
          </div>`).join("")}
      </div>
      <div class="rule" style="margin-top:38px;"></div>
      <p class="caption" style="margin-top:30px;">申论写成治理链，面试答成处理链，材料才不会停在口号层。</p>
    </div>
    <div class="source">${sourceLine()}</div>
  `, true);
}

function wechatFramework() {
  const stages = [
    ["看见问题", "走访调研 / 数据监测"],
    ["接住问题", "不推开 / 不悬空"],
    ["拆解问题", "找环节 / 找症结"],
    ["协同解决", "谁牵头 / 谁参与"],
    ["反馈长效", "有回应 / 能固化"],
  ];
  return doc(1920, 1080, `
    <div style="position:absolute; left:88px; top:70px;" class="label">五步治理链</div>
    <h1 class="title" style="position:absolute; left:88px; top:146px; font-size:66px; width:1180px;">
      把“正确政绩观”写实：<span class="accent-teal">先把问题接住</span>
    </h1>
    <div style="position:absolute; left:86px; top:360px; right:86px; height:300px;">
      <div style="position:absolute; left:80px; right:80px; top:116px; height:6px; background:${colors.line};"></div>
      ${stages.map((stage, idx) => {
        const left = 20 + idx * 350;
        const color = idx === 1 ? colors.red : idx === 4 ? colors.gold : colors.teal;
        return `
        <div style="position:absolute; left:${left}px; top:0; width:270px; height:280px;">
          <div style="margin:auto; width:92px; height:92px; border:4px solid ${color}; background:${colors.paper2}; display:flex; align-items:center; justify-content:center; font-size:42px; font-weight:900; color:${color};">${idx + 1}</div>
          <div style="margin-top:24px; text-align:center; font-size:38px; font-weight:900;">${stage[0]}</div>
          <div style="margin-top:12px; text-align:center; font-size:24px; color:${colors.muted}; line-height:1.35;">${stage[1]}</div>
        </div>`;
      }).join("")}
    </div>
    <div class="panel" style="position:absolute; left:126px; right:126px; bottom:118px; height:210px; padding:32px 40px;">
      <div style="display:grid; grid-template-columns: repeat(5, 1fr); gap:24px;">
        ${["涉企执法", "小区微改造", "合约食堂", "潮汐菜场", "群众来论"].map((item, idx) => `
          <div>
            <div class="kicker" style="font-size:25px;">案例 ${idx + 1}</div>
            <div style="margin-top:8px; font-size:31px; font-weight:900;">${item}</div>
          </div>`).join("")}
      </div>
    </div>
    <div class="source">${sourceLine()}</div>
  `);
}

function wechatInterview() {
  return doc(1920, 1080, `
    <div style="position:absolute; left:88px; top:70px;" class="label">结构化面试转译</div>
    <h1 class="title" style="position:absolute; left:88px; top:148px; font-size:66px; width:1220px;">
      群众反映小区出入口拥堵，<span class="accent-red">你怎么接？</span>
    </h1>
    <div class="panel" style="position:absolute; left:92px; top:330px; width:560px; height:420px; padding:42px;">
      <div class="kicker">题目场景</div>
      <p style="margin:30px 0 0; font-size:38px; line-height:1.42; font-weight:800;">道路狭窄<br>早晚高峰拥堵<br>存在安全隐患</p>
      <p class="caption" style="margin-top:30px;">不要只说“加强协调”，要把问题拆清楚。</p>
    </div>
    <div style="position:absolute; left:720px; top:400px; width:180px; height:180px; border:4px solid ${colors.red}; display:flex; align-items:center; justify-content:center; text-align:center; color:${colors.red}; font-size:34px; line-height:1.25; font-weight:900; background:${colors.paper2};">先<br>接住</div>
    <div style="position:absolute; left:965px; top:310px; width:820px; display:grid; gap:18px;">
      ${["现场核实：时段、人群、隐患、停车", "多方会商：社区、物业、交警、住建", "分类处理：微改造、错峰、疏导、项目清单", "公开回应：进展、影响、时间表", "长效维护：反馈观察、责任明确"].map((item, idx) => `
        <div class="node" style="height:86px; padding:18px 24px; border-color:${idx === 4 ? colors.gold : colors.teal};">
          <div style="font-size:30px; font-weight:900;">${idx + 1}. ${item}</div>
        </div>`).join("")}
    </div>
    <div class="source">${sourceLine()}</div>
  `);
}

function xhsShell(index, label, title, subtitle, contentHtml) {
  return doc(1080, 1440, `
    <div style="position:absolute; left:64px; top:54px;" class="label">${esc(label)}</div>
    <div style="position:absolute; right:64px; top:62px; color:${colors.muted}; font-size:24px; font-weight:800;">${String(index).padStart(2, "0")} / 07</div>
    <h1 class="xhs-title" style="position:absolute; left:72px; right:72px; top:148px;">${title}</h1>
    <div class="xhs-sub" style="position:absolute; left:72px; right:72px; top:360px;">${subtitle}</div>
    ${contentHtml}
    <div class="source" style="left:72px; right:72px; bottom:54px; font-size:22px;">人民日报 2026-05-22 教研转译</div>
  `);
}

function xhsCards() {
  return [
    {
      name: "01-cover",
      html: xhsShell(
        1,
        "申论 / 面试",
        `人民日报这一天<br>真正该学的是<br><span class="accent-teal">“把问题接住”</span>`,
        "别再只背正确口号，把材料写成办事方法。",
        `<div class="xhs-card" style="top:650px;">
          <h3>一句话记住</h3>
          <p>好的治理，不是把口号说完整，而是让问题有人接、有人办、有反馈、有长效。</p>
        </div>`,
      ),
    },
    {
      name: "02-mistake",
      html: xhsShell(
        2,
        "常见误区",
        `很多同学写空<br>是因为只写<span class="accent-red">态度</span>`,
        "人民至上、真抓实干、长效机制都对，但还不够。",
        `<div class="xhs-card" style="top:640px;">
          <h3>继续追问</h3>
          <p>群众的问题怎么被看见？谁来接？怎么办？怎么反馈？能不能变成长效机制？</p>
        </div>
        <div class="xhs-card" style="top:920px;">
          <h3>考场区别</h3>
          <p>普通答案堆词，高分答案写动作。</p>
        </div>`,
      ),
    },
    {
      name: "03-case-law-enforcement",
      html: xhsShell(
        3,
        "人民日报案例",
        `涉企执法<br>不是一句<br><span class="accent-red">“服务企业”</span>`,
        "企业怕的不是正常监管，而是不规范、不稳定、不透明。",
        `<div class="xhs-card" style="top:650px;">
          <h3>把痛点拆开</h3>
          <p>乱检查、乱罚款、标准不一、趋利性执法、异地执法不规范。</p>
        </div>
        <div class="xhs-card" style="top:970px;">
          <h3>把动作写实</h3>
          <p>综合查一次、细化裁量基准、动态监测、监督平台、制度长效。</p>
        </div>`,
      ),
    },
    {
      name: "04-cases-grassroots",
      html: xhsShell(
        4,
        "基层治理",
        `治理不能只会<br><span class="accent-red">“一禁了之”</span>`,
        "合约食堂和潮汐菜场，都是在秩序和需求之间找办法。",
        `<div class="xhs-card" style="top:650px;">
          <h3>合约食堂</h3>
          <p>不是简单禁止酒席攀比，而是给群众一个能接受、能使用、能持续的替代方案。</p>
        </div>
        <div class="xhs-card" style="top:970px;">
          <h3>潮汐菜场</h3>
          <p>不是取缔和放任二选一，而是用时间错峰、区域划定、动态管理来接住两难。</p>
        </div>`,
      ),
    },
    {
      name: "05-framework",
      html: xhsShell(
        5,
        "高分框架",
        `把问题接住<br>就按这<span class="accent-teal">五步</span>`,
        "写基层治理、群众工作、政绩观，都可以迁移。",
        `<div style="position:absolute; left:92px; right:92px; top:620px; display:grid; gap:24px;">
          ${["看见问题", "接住问题", "拆解问题", "协同解决", "反馈长效"].map((item, idx) => `
            <div style="display:flex; align-items:center; gap:24px;">
              <div style="width:72px; height:72px; border:3px solid ${idx === 1 ? colors.red : idx === 4 ? colors.gold : colors.teal}; color:${idx === 1 ? colors.red : idx === 4 ? colors.gold : colors.teal}; display:flex; align-items:center; justify-content:center; font-size:34px; font-weight:900; background:rgba(255,255,255,.7);">${idx + 1}</div>
              <div style="font-size:44px; font-weight:900;">${item}</div>
            </div>`).join("")}
        </div>`,
      ),
    },
    {
      name: "06-interview",
      html: xhsShell(
        6,
        "面试示范",
        `街道协调题<br>这样答更有<br><span class="accent-teal">治理感</span>`,
        "群众反映小区出入口拥堵，不要只说“加强协调”。",
        `<div class="xhs-card" style="top:650px;">
          <h3>答题顺序</h3>
          <p>先接住诉求，再现场核实、组织会商、分类处理、公开回应、形成长效。</p>
        </div>
        <div class="xhs-card" style="top:980px;">
          <h3>关键区别</h3>
          <p>不是背流程，而是让考官听见你真的能把一个问题办下去。</p>
        </div>`,
      ),
    },
    {
      name: "07-summary",
      html: xhsShell(
        7,
        "最后记住",
        `五个追问<br>写出<span class="accent-gold">治理感</span>`,
        "以后遇到类似题，先不要急着堆大词。",
        `<div style="position:absolute; left:72px; right:72px; top:610px; display:grid; gap:22px;">
          ${["这个问题是谁的问题？", "它为什么没有及时解决？", "谁应该先把它接住？", "需要哪些部门和资源一起办？", "办完以后怎么反馈、怎么长效？"].map((item, idx) => `
            <div class="xhs-card" style="position:relative; left:0; right:0; top:auto; padding:24px 30px;">
              <h3 style="font-size:34px; margin:0;"><span class="accent-teal">${idx + 1}.</span> ${item}</h3>
            </div>`).join("")}
        </div>`,
      ),
    },
  ];
}

async function writeImages() {
  await fs.mkdir(SOURCE_HTML_DIR, { recursive: true });
  await fs.mkdir(WECHAT_DIR, { recursive: true });
  await fs.mkdir(XHS_DIR, { recursive: true });

  const pages = [
    {
      htmlName: "wechat-01-cover-problem-handling.html",
      output: path.join(WECHAT_DIR, "01-cover-problem-handling.png"),
      width: 1920,
      height: 1080,
      html: wechatCover(),
    },
    {
      htmlName: "wechat-02-framework-five-actions.html",
      output: path.join(WECHAT_DIR, "02-framework-five-actions.png"),
      width: 1920,
      height: 1080,
      html: wechatFramework(),
    },
    {
      htmlName: "wechat-03-interview-transfer.html",
      output: path.join(WECHAT_DIR, "03-interview-transfer.png"),
      width: 1920,
      height: 1080,
      html: wechatInterview(),
    },
    ...xhsCards().map((card) => ({
      htmlName: `xhs-${card.name}.html`,
      output: path.join(XHS_DIR, `${card.name}.png`),
      width: 1080,
      height: 1440,
      html: card.html,
    })),
  ];

  const browser = await chromium.launch({ headless: true });
  try {
    for (const item of pages) {
      const htmlPath = path.join(SOURCE_HTML_DIR, item.htmlName);
      await fs.writeFile(htmlPath, item.html, "utf8");
      const page = await browser.newPage({ viewport: { width: item.width, height: item.height }, deviceScaleFactor: 1 });
      await page.goto(`file://${htmlPath}`);
      await page.screenshot({ path: item.output, type: "png" });
      await page.close();
    }
  } finally {
    await browser.close();
  }

  return pages.map((item) => item.output);
}

function slideSharedModule() {
  return `
export const C = {
  paper: "${colors.paper}",
  paper2: "${colors.paper2}",
  ink: "${colors.ink}",
  muted: "${colors.muted}",
  grid: "${colors.grid}",
  blue: "${colors.blue}",
  red: "${colors.red}",
  teal: "${colors.teal}",
  gold: "${colors.gold}",
  line: "${colors.line}",
  white: "${colors.white}",
};

export function bg(slide, ctx, dark = false) {
  ctx.addShape(slide, { x: 0, y: 0, w: ctx.W, h: ctx.H, fill: dark ? "#112537" : C.paper, line: ctx.line("#00000000", 0) });
  for (let x = 0; x <= ctx.W; x += 80) {
    ctx.addShape(slide, { x, y: 0, w: 1, h: ctx.H, fill: dark ? "#ffffff12" : "#1f4f7712", line: ctx.line("#00000000", 0) });
  }
  for (let y = 0; y <= ctx.H; y += 80) {
    ctx.addShape(slide, { x: 0, y, w: ctx.W, h: 1, fill: dark ? "#ffffff12" : "#1f4f7712", line: ctx.line("#00000000", 0) });
  }
}

export function footer(slide, ctx, page) {
  ctx.addText(slide, {
    text: "人民日报 2026-05-22 教研转译",
    x: 90, y: 1015, w: 620, h: 36,
    fontSize: 24, color: C.muted, typeface: "PingFang SC",
  });
  ctx.addText(slide, {
    text: String(page).padStart(2, "0") + " / 08",
    x: 1700, y: 1015, w: 130, h: 36,
    fontSize: 24, color: C.muted, bold: true, typeface: "PingFang SC", align: "right",
  });
}

export function label(slide, ctx, text, dark = false) {
  ctx.addShape(slide, { x: 90, y: 70, w: 390, h: 54, fill: dark ? "#ffffff10" : "#ffffffa8", line: ctx.line(dark ? "#f8df9c70" : C.line, 1) });
  ctx.addText(slide, { text, x: 110, y: 84, w: 350, h: 30, fontSize: 24, color: dark ? "#f8df9c" : C.blue, bold: true, typeface: "PingFang SC" });
}

export function title(slide, ctx, text, y = 145, size = 58, w = 1250) {
  ctx.addText(slide, { text, x: 90, y, w, h: 140, fontSize: size, color: C.ink, bold: true, typeface: "PingFang SC", insets: { left: 0, right: 0, top: 0, bottom: 0 } });
}

export function box(slide, ctx, { x, y, w, h, head, body, color = C.teal }) {
  ctx.addShape(slide, { x, y, w, h, fill: "#ffffffb5", line: ctx.line(color, 2) });
  ctx.addShape(slide, { x, y, w: 8, h, fill: color, line: ctx.line("#00000000", 0) });
  ctx.addText(slide, { text: head, x: x + 28, y: y + 22, w: w - 54, h: 40, fontSize: 29, color: C.ink, bold: true, typeface: "PingFang SC" });
  ctx.addText(slide, { text: body, x: x + 28, y: y + 72, w: w - 54, h: h - 88, fontSize: 23, color: C.muted, typeface: "PingFang SC" });
}

export function stage(slide, ctx, { x, y, num, head, body, color }) {
  ctx.addShape(slide, { x, y, w: 250, h: 210, fill: "#ffffffb8", line: ctx.line(color, 2) });
  ctx.addShape(slide, { x: x + 25, y: y + 24, w: 58, h: 58, fill: "#00000000", line: ctx.line(color, 3) });
  ctx.addText(slide, { text: String(num), x: x + 39, y: y + 34, w: 30, h: 30, fontSize: 28, color, bold: true, typeface: "PingFang SC", align: "center" });
  ctx.addText(slide, { text: head, x: x + 25, y: y + 98, w: 200, h: 38, fontSize: 31, color: C.ink, bold: true, typeface: "PingFang SC", align: "center" });
  ctx.addText(slide, { text: body, x: x + 25, y: y + 145, w: 200, h: 48, fontSize: 20, color: C.muted, typeface: "PingFang SC", align: "center" });
}
`;
}

function slideModule(number, body) {
  const fn = `slide${String(number).padStart(2, "0")}`;
  return `import { bg, footer, label, title, box, stage, C } from "./shared.mjs";

export async function ${fn}(presentation, ctx) {
  const slide = presentation.slides.add();
${body}
  return slide;
}
`;
}

function slideModules() {
  return [
    slideModule(1, `
  bg(slide, ctx, true);
  label(slide, ctx, "课堂主题", true);
  ctx.addText(slide, { text: "别把政绩观\\n写成口号", x: 95, y: 188, w: 900, h: 190, fontSize: 82, color: "#f7efe2", bold: true, typeface: "PingFang SC" });
  ctx.addText(slide, { text: "人民日报这一天真正该学的是“把问题接住”", x: 100, y: 430, w: 1120, h: 70, fontSize: 42, color: "#f8d77d", bold: true, typeface: "PingFang SC" });
  ctx.addShape(slide, { x: 1160, y: 170, w: 560, h: 520, fill: "#ffffff10", line: ctx.line("#f8df9c70", 2) });
  ["问题清单", "责任清单", "办理清单", "反馈长效"].forEach((item, idx) => {
    const y = 225 + idx * 105;
    const color = idx === 0 ? "#e56a55" : idx === 3 ? "#f8d77d" : "#66c8bd";
    ctx.addShape(slide, { x: 1215, y, w: 54, h: 54, fill: "#00000000", line: ctx.line(color, 3) });
    ctx.addText(slide, { text: String(idx + 1), x: 1227, y: y + 9, w: 30, h: 30, fontSize: 27, color, bold: true, typeface: "PingFang SC", align: "center" });
    ctx.addText(slide, { text: item, x: 1300, y: y + 8, w: 280, h: 38, fontSize: 34, color: "#f7efe2", bold: true, typeface: "PingFang SC" });
  });
  ctx.addText(slide, { text: "申论写成治理链，面试答成处理链。", x: 1160, y: 740, w: 650, h: 50, fontSize: 31, color: "#f7efe2", typeface: "PingFang SC" });
  footer(slide, ctx, 1);
`),
    slideModule(2, `
  bg(slide, ctx);
  label(slide, ctx, "学员痛点");
  title(slide, ctx, "会背口号，但写不出动作", 150, 64, 980);
  box(slide, ctx, { x: 105, y: 350, w: 760, h: 360, head: "常见写法", body: "坚持人民至上\\n树牢为民情怀\\n真抓实干、久久为功\\n完善制度机制", color: C.red });
  box(slide, ctx, { x: 1050, y: 350, w: 760, h: 360, head: "需要补上的追问", body: "问题怎么被看见？\\n看见以后谁来接？\\n接住以后怎么办？\\n办完以后怎么反馈、怎么长效？", color: C.teal });
  ctx.addShape(slide, { x: 900, y: 505, w: 105, h: 6, fill: C.line, line: ctx.line("#00000000", 0) });
  ctx.addShape(slide, { x: 1000, y: 483, w: 34, h: 50, fill: C.teal, line: ctx.line("#00000000", 0) });
  ctx.addText(slide, { text: "空话的问题不是错，而是没有动作。", x: 290, y: 800, w: 1300, h: 60, fontSize: 42, color: C.ink, bold: true, typeface: "PingFang SC", align: "center" });
  footer(slide, ctx, 2);
`),
    slideModule(3, `
  bg(slide, ctx);
  label(slide, ctx, "人民日报案例");
  title(slide, ctx, "看起来是多篇文章，其实都在讲同一件事", 145, 56, 1320);
  const cases = [
    ["涉企执法", "接住企业对乱检查、乱罚款、标准不一的担忧", C.red],
    ["完善制度机制", "把群众诉求纳入清单办理和闭环反馈", C.teal],
    ["合约食堂", "给酒席攀比治理一个可接受的替代空间", C.gold],
    ["潮汐菜场", "用时间错峰接住买菜需求和道路秩序两难", C.blue],
    ["群众来论", "职责有边界，但群众找上门的问题要先接住", C.teal],
  ];
  cases.forEach((item, idx) => {
    const x = 115 + (idx % 3) * 590;
    const y = idx < 3 ? 335 : 620;
    const w = idx < 3 ? 500 : 790;
    box(slide, ctx, { x, y, w, h: 210, head: item[0], body: item[1], color: item[2] });
  });
  ctx.addText(slide, { text: "共同逻辑：不是把问题推开，而是让问题进入办理过程。", x: 210, y: 885, w: 1500, h: 54, fontSize: 38, color: C.ink, bold: true, typeface: "PingFang SC", align: "center" });
  footer(slide, ctx, 3);
`),
    slideModule(4, `
  bg(slide, ctx);
  label(slide, ctx, "核心框架");
  title(slide, ctx, "把问题接住的五步治理链", 145, 66, 1100);
  ctx.addShape(slide, { x: 215, y: 492, w: 1450, h: 6, fill: C.line, line: ctx.line("#00000000", 0) });
  [
    ["看见问题", "走访 / 诉求 / 数据", C.teal],
    ["接住问题", "不推开 / 不悬空", C.red],
    ["拆解问题", "拆环节 / 找症结", C.teal],
    ["协同解决", "牵头 / 参与 / 机制", C.blue],
    ["反馈长效", "有回应 / 能固化", C.gold],
  ].forEach((s, idx) => stage(slide, ctx, { x: 135 + idx * 330, y: 375, num: idx + 1, head: s[0], body: s[1], color: s[2] }));
  ctx.addText(slide, { text: "写申论时，它是一条对策链；答面试时，它是一条处理链。", x: 250, y: 770, w: 1420, h: 60, fontSize: 40, color: C.ink, bold: true, typeface: "PingFang SC", align: "center" });
  footer(slide, ctx, 4);
`),
    slideModule(5, `
  bg(slide, ctx);
  label(slide, ctx, "申论转译");
  title(slide, ctx, "把口号改成能得分的治理表达", 145, 60, 1220);
  box(slide, ctx, { x: 95, y: 330, w: 820, h: 220, head: "不要只写", body: "加大服务企业力度。", color: C.red });
  box(slide, ctx, { x: 1005, y: 330, w: 820, h: 220, head: "可以改成", body: "让监管更精准、执法更规范、标准更统一、诉求更畅通。", color: C.teal });
  box(slide, ctx, { x: 95, y: 625, w: 820, h: 230, head: "不要只写", body: "坚持以人民为中心。", color: C.red });
  box(slide, ctx, { x: 1005, y: 625, w: 820, h: 230, head: "可以改成", body: "把群众生活中的堵点、企业经营中的痛点、基层执行中的难点纳入办理过程。", color: C.teal });
  footer(slide, ctx, 5);
`),
    slideModule(6, `
  bg(slide, ctx);
  label(slide, ctx, "面试示范");
  title(slide, ctx, "群众反映小区出入口拥堵，你怎么处理？", 145, 58, 1320);
  box(slide, ctx, { x: 95, y: 330, w: 500, h: 360, head: "题目要点", body: "道路狭窄\\n早晚高峰拥堵\\n存在安全隐患\\n领导让你协调处理", color: C.red });
  const steps = ["接住诉求，现场核实", "多方会商，拆清问题", "分类处理，形成方案", "公开回应，说明进展", "观察反馈，长效维护"];
  steps.forEach((item, idx) => {
    const y = 300 + idx * 112;
    ctx.addShape(slide, { x: 750, y, w: 870, h: 82, fill: "#ffffffb5", line: ctx.line(idx === 4 ? C.gold : C.teal, 2) });
    ctx.addText(slide, { text: String(idx + 1), x: 780, y: y + 18, w: 42, h: 42, fontSize: 31, color: idx === 4 ? C.gold : C.teal, bold: true, typeface: "PingFang SC", align: "center" });
    ctx.addText(slide, { text: item, x: 855, y: y + 20, w: 650, h: 40, fontSize: 33, color: C.ink, bold: true, typeface: "PingFang SC" });
  });
  ctx.addText(slide, { text: "重点：不是背流程，而是让考官听见你真的能把问题办下去。", x: 240, y: 872, w: 1450, h: 54, fontSize: 36, color: C.ink, bold: true, typeface: "PingFang SC", align: "center" });
  footer(slide, ctx, 6);
`),
    slideModule(7, `
  bg(slide, ctx);
  label(slide, ctx, "课堂练习");
  title(slide, ctx, "用五步框架，把材料现场转成答案", 145, 60, 1300);
  const tasks = [
    ["练习 1", "流动摊贩占道经营，但居民有就近买菜需求。你怎么看？"],
    ["练习 2", "企业反映检查频次高、标准不一。你如何提出对策？"],
    ["练习 3", "群众求助事项不完全归你管。你会怎么处理？"],
  ];
  tasks.forEach((item, idx) => box(slide, ctx, { x: 140 + idx * 570, y: 340, w: 480, h: 340, head: item[0], body: item[1], color: idx === 0 ? C.teal : idx === 1 ? C.red : C.gold }));
  ctx.addShape(slide, { x: 230, y: 780, w: 1460, h: 90, fill: "#ffffffb8", line: ctx.line(C.line, 1) });
  ctx.addText(slide, { text: "作答要求：至少写清“谁来接、拆成哪几件事、哪些部门协同、如何反馈长效”。", x: 270, y: 804, w: 1380, h: 40, fontSize: 33, color: C.ink, bold: true, typeface: "PingFang SC", align: "center" });
  footer(slide, ctx, 7);
`),
    slideModule(8, `
  bg(slide, ctx, true);
  label(slide, ctx, "参考文章", true);
  ctx.addText(slide, { text: "本课实际使用的人民日报材料", x: 95, y: 155, w: 1150, h: 70, fontSize: 58, color: "#f7efe2", bold: true, typeface: "PingFang SC" });
  ${JSON.stringify(sources)}.forEach((item, idx) => {
    const y = 285 + idx * 92;
    ctx.addText(slide, { text: String(idx + 1).padStart(2, "0"), x: 120, y, w: 70, h: 38, fontSize: 28, color: idx < 2 ? "#f8d77d" : "#66c8bd", bold: true, typeface: "PingFang SC" });
    ctx.addText(slide, { text: item, x: 210, y, w: 1450, h: 42, fontSize: 31, color: "#f7efe2", typeface: "PingFang SC" });
  });
  ctx.addText(slide, { text: "教研转译提醒：“把问题接住”是课堂表达，不是人民日报原文标题。使用时保留具体案例动作。", x: 120, y: 890, w: 1580, h: 58, fontSize: 28, color: "#f7efe2cc", typeface: "PingFang SC" });
  footer(slide, ctx, 8);
`),
  ];
}

async function writeDeck() {
  await fs.mkdir(SLIDES_DIR, { recursive: true });
  await fs.mkdir(PREVIEW_DIR, { recursive: true });
  await fs.mkdir(LAYOUT_DIR, { recursive: true });
  await fs.mkdir(QA_DIR, { recursive: true });
  await fs.mkdir(PPT_DIR, { recursive: true });

  await fs.writeFile(path.join(WORKSPACE, "profile-plan.txt"), [
    "task mode: create",
    "primary deck-profile: strategy-leadership",
    "secondary gates: classroom teaching, public-sector exam training",
    "proof objects: People's Daily cases, five-step governance chain, interview answer sequence",
    "source requirements: use only 2026-05-22 People's Daily source articles already listed in the WeChat draft",
    "known missing inputs: no external template deck supplied",
    "",
  ].join("\\n"), "utf8");

  await fs.writeFile(path.join(WORKSPACE, "contact-sheet-plan.txt"), [
    "1 cover with dark blueprint system",
    "2 pain-point comparison",
    "3 case map",
    "4 five-step flow",
    "5 writing transfer comparison",
    "6 interview sequence",
    "7 classroom practice cards",
    "8 dark source page",
    "",
  ].join("\\n"), "utf8");

  await fs.writeFile(path.join(SLIDES_DIR, "shared.mjs"), slideSharedModule(), "utf8");
  const modules = slideModules();
  for (let index = 0; index < modules.length; index += 1) {
    await fs.writeFile(path.join(SLIDES_DIR, `slide-${String(index + 1).padStart(2, "0")}.mjs`), modules[index], "utf8");
  }

  const result = spawnSync(process.execPath, [
    PRESENTATION_BUILDER,
    "--slides-dir", SLIDES_DIR,
    "--out", FINAL_PPTX,
    "--preview-dir", PREVIEW_DIR,
    "--workspace", WORKSPACE,
    "--layout-dir", LAYOUT_DIR,
    "--manifest", path.join(QA_DIR, "artifact-build-manifest.json"),
    "--slide-size", "1920x1080",
    "--slide-count", "8",
    "--scale", "1",
  ], {
    cwd: REPO_ROOT,
    env: { ...process.env, PYTHON },
    encoding: "utf8",
  });

  if (result.status !== 0) {
    throw new Error([
      "PPT generation failed.",
      result.stdout,
      result.stderr,
    ].filter(Boolean).join("\\n"));
  }

  return FINAL_PPTX;
}

async function main() {
  await fs.mkdir(PACKAGE_DIR, { recursive: true });
  const imageOutputs = await writeImages();
  const deckOutput = await writeDeck();
  const relative = (file) => path.relative(PACKAGE_DIR, file);
  console.log(JSON.stringify({
    packageDir: PACKAGE_DIR,
    images: imageOutputs.map(relative),
    pptx: relative(deckOutput),
    htmlSources: SOURCE_HTML_DIR,
    workspace: WORKSPACE,
  }, null, 2));
}

main().catch((error) => {
  console.error(error.stack || error.message || String(error));
  process.exit(1);
});
