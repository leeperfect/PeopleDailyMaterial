import { C, FONT, bg, title, footer, box, bullet } from "./common.mjs";
export async function slide05(presentation, ctx) {
  const slide = presentation.slides.add(); bg(slide, ctx);
  title(slide, ctx, "面试示范", "同一道题，差距在“拆细”", "题目：校门口拥堵、雨天通行不便，领导让你推进“最美上学路”改造。");
  box(slide, ctx, 80, 320, 500, 275, C.softRed, "#F4B8B1");
  ctx.addText(slide, { text: "普通答法", x: 120, y: 350, w: 250, h: 32, fontSize: 27, color: C.red, bold: true, typeface: FONT });
  bullet(slide, ctx, "加强调研", 125, 420, 330, C.ink);
  bullet(slide, ctx, "完善设施", 125, 475, 330, C.ink);
  bullet(slide, ctx, "加强宣传", 125, 530, 330, C.ink);
  box(slide, ctx, 670, 285, 520, 340, C.white, C.line);
  ctx.addText(slide, { text: "高分答法", x: 710, y: 325, w: 250, h: 32, fontSize: 27, color: C.blue, bold: true, typeface: FONT });
  ["现场体检：找点位、找时段、找风险", "安全优先：拓宽、防滑、护栏、分流", "空间优化：雨棚、等候区、导向标识", "文化赋能：阅读角、作品墙、文化展板", "长效维护：问卷反馈、责任到人"].forEach((t, i) => bullet(slide, ctx, t, 715, 390 + i * 45, 390, C.ink));
  footer(slide, ctx, 5); return slide;
}
