import { C, FONT, bg, title, footer, box, bullet } from "./common.mjs";
export async function slide02(presentation, ctx) {
  const slide = presentation.slides.add(); bg(slide, ctx);
  title(slide, ctx, "常见失分点", "为什么“以人为本”写不出分？", "因为理念没有被拆成可执行动作，答案就会停在口号层面。");
  box(slide, ctx, 85, 330, 500, 260, C.softRed, "#F4B8B1");
  ctx.addText(slide, { text: "空话写法", x: 120, y: 360, w: 380, h: 34, fontSize: 26, color: C.red, bold: true, typeface: FONT });
  bullet(slide, ctx, "完善基础设施", 126, 425, 360, C.ink);
  bullet(slide, ctx, "提升服务水平", 126, 482, 360, C.ink);
  bullet(slide, ctx, "坚持以人为本", 126, 539, 360, C.ink);
  box(slide, ctx, 690, 295, 475, 330, C.white, C.line);
  ctx.addText(slide, { text: "换成五个追问", x: 730, y: 334, w: 360, h: 34, fontSize: 26, color: C.blue, bold: true, typeface: FONT });
  ["问题怎么被看见？", "服务怎么送到身边？", "空间怎么重新设计？", "群众体验怎么反馈？", "机制怎么长期运行？"].forEach((t, i) => bullet(slide, ctx, t, 740, 397 + i * 45, 340, C.ink));
  footer(slide, ctx, 2); return slide;
}
