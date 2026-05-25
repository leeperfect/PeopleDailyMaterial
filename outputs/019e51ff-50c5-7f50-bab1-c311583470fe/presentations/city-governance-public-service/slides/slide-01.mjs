import { C, FONT, bg, title, footer, bigQuote } from "./common.mjs";
export async function slide01(presentation, ctx) {
  const slide = presentation.slides.add(); bg(slide, ctx);
  title(slide, ctx, "课堂导入", "别再空喊“以人为本”", "从人民日报一条上学路，拆出城市治理高分写法");
  bigQuote(slide, ctx, "好的城市治理，不是把城市变得更好看，而是把公共服务嵌进人的日常生活。", 70, 340, 640, 150, C.red);
  await ctx.addImage(slide, { path: "/Users/pf.macbookpro/PeopleDailyMaterial/data/analysis/2026-05-17/deliverables/xiaohongshu-images/city-governance-01-cover.png", x: 820, y: 70, w: 300, h: 520, fit: "contain", alt: "小红书封面卡片" });
  footer(slide, ctx, 1); return slide;
}
