import { C, FONT, bg, title, footer, box, bullet } from "./common.mjs";
export async function slide03(presentation, ctx) {
  const slide = presentation.slides.add(); bg(slide, ctx);
  title(slide, ctx, "人民日报案例", "孩子每天走过的路，也是一道治理题", "宁波“最美上学路”：把校门口最后 100 米，从通行空间做成成长空间。");
  await ctx.addImage(slide, { path: "/Users/pf.macbookpro/PeopleDailyMaterial/data/analysis/2026-05-17/deliverables/xiaohongshu-images/city-governance-02-case.png", x: 78, y: 310, w: 245, h: 326, fit: "contain", alt: "案例卡片" });
  box(slide, ctx, 380, 320, 345, 230, C.white, C.line);
  ctx.addText(slide, { text: "关键事实", x: 415, y: 350, w: 240, h: 32, fontSize: 26, color: C.red, bold: true, typeface: FONT });
  bullet(slide, ctx, "累计投入 4700 多万元", 420, 415, 260, C.ink);
  bullet(slide, ctx, "完成 69 条上学路改造", 420, 474, 260, C.ink);
  box(slide, ctx, 780, 310, 350, 270, C.softBlue, "#A7D5D1");
  ctx.addText(slide, { text: "教学转译", x: 815, y: 350, w: 240, h: 32, fontSize: 26, color: C.blue, bold: true, typeface: FONT });
  bullet(slide, ctx, "小切口：上学路", 820, 415, 260, C.ink);
  bullet(slide, ctx, "真问题：安全与拥堵", 820, 474, 260, C.ink);
  bullet(slide, ctx, "大服务：阅读与文化", 820, 533, 260, C.ink);
  footer(slide, ctx, 3); return slide;
}
