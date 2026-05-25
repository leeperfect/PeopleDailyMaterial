import { bg, footer, label, title, box, stage, C } from "./shared.mjs";

export async function slide04(presentation, ctx) {
  const slide = presentation.slides.add();

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

  return slide;
}
