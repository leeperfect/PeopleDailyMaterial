import { bg, footer, label, title, box, stage, C } from "./shared.mjs";

export async function slide02(presentation, ctx) {
  const slide = presentation.slides.add();

  bg(slide, ctx);
  label(slide, ctx, "学员痛点");
  title(slide, ctx, "会背口号，但写不出动作", 150, 64, 980);
  box(slide, ctx, { x: 105, y: 350, w: 760, h: 360, head: "常见写法", body: "坚持人民至上\n树牢为民情怀\n真抓实干、久久为功\n完善制度机制", color: C.red });
  box(slide, ctx, { x: 1050, y: 350, w: 760, h: 360, head: "需要补上的追问", body: "问题怎么被看见？\n看见以后谁来接？\n接住以后怎么办？\n办完以后怎么反馈、怎么长效？", color: C.teal });
  ctx.addShape(slide, { x: 900, y: 505, w: 105, h: 6, fill: C.line, line: ctx.line("#00000000", 0) });
  ctx.addShape(slide, { x: 1000, y: 483, w: 34, h: 50, fill: C.teal, line: ctx.line("#00000000", 0) });
  ctx.addText(slide, { text: "空话的问题不是错，而是没有动作。", x: 290, y: 800, w: 1300, h: 60, fontSize: 42, color: C.ink, bold: true, typeface: "PingFang SC", align: "center" });
  footer(slide, ctx, 2);

  return slide;
}
