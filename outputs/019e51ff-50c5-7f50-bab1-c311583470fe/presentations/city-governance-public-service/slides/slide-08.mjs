import { C, FONT, bg, title, footer, box } from "./common.mjs";
export async function slide08(presentation, ctx) {
  const slide = presentation.slides.add(); bg(slide, ctx);
  title(slide, ctx, "参考文献", "本课所用人民日报材料", "课堂讲解、公众号文章、小红书配图均基于以下四篇材料整理。");
  const refs = [
    "窦皓：《最美上学路  成长新空间》，《人民日报》2026年5月17日第04版",
    "陈震：《城市微改造，让文化味更浓》，《人民日报》2026年5月17日第04版",
    "《地级及以上城市、县级市今年将全面开展城市体检》，《人民日报》2026年5月17日第04版",
    "潘俊强：《“零工市场让我们好找活、有保障”》，《人民日报》2026年5月17日第04版"
  ];
  refs.forEach((r, i) => {
    box(slide, ctx, 95, 310 + i * 75, 980, 48, i % 2 === 0 ? C.white : C.softBlue, i % 2 === 0 ? C.line : "#A7D5D1");
    ctx.addText(slide, { text: `${i + 1}. ${r}`, x: 125, y: 322 + i * 75, w: 900, h: 28, fontSize: 20, color: C.ink, typeface: FONT });
  });
  footer(slide, ctx, 8); return slide;
}
