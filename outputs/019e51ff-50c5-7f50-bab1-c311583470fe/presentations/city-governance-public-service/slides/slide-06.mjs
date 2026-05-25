import { C, FONT, bg, title, footer, box, bullet } from "./common.mjs";
export async function slide06(presentation, ctx) {
  const slide = presentation.slides.add(); bg(slide, ctx);
  title(slide, ctx, "反面提醒", "城市更新不是大拆大建", "微改造也不是摆样子。要写清楚“好看”背后的真实服务。");
  await ctx.addImage(slide, { path: "/Users/pf.macbookpro/PeopleDailyMaterial/data/analysis/2026-05-17/deliverables/xiaohongshu-images/city-governance-05-warning.png", x: 70, y: 305, w: 245, h: 326, fit: "contain", alt: "反面提醒卡片" });
  const rows = [["面子和里子", "颜值可以提升，但安全、通行、便利才是里子。"], ["建设和运营", "建起来只是第一步，能不能长期维护更关键。"], ["管理和服务", "不要只看秩序问题，要看见背后的服务需求。"]];
  rows.forEach((r, i) => {
    const y = 320 + i * 92;
    box(slide, ctx, 390, y, 720, 78, i === 1 ? C.softBlue : C.white, i === 1 ? "#A7D5D1" : C.line);
    ctx.addText(slide, { text: r[0], x: 420, y: y + 16, w: 160, h: 28, fontSize: 23, color: C.red, bold: true, typeface: FONT });
    ctx.addText(slide, { text: r[1], x: 610, y: y + 16, w: 455, h: 44, fontSize: 21, color: C.ink, typeface: FONT });
  });
  footer(slide, ctx, 6); return slide;
}
