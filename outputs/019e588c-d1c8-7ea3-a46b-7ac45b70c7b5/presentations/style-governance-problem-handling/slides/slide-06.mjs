import { bg, footer, label, title, box, stage, C } from "./shared.mjs";

export async function slide06(presentation, ctx) {
  const slide = presentation.slides.add();

  bg(slide, ctx);
  label(slide, ctx, "面试示范");
  title(slide, ctx, "群众反映小区出入口拥堵，你怎么处理？", 145, 58, 1320);
  box(slide, ctx, { x: 95, y: 330, w: 500, h: 360, head: "题目要点", body: "道路狭窄\n早晚高峰拥堵\n存在安全隐患\n领导让你协调处理", color: C.red });
  const steps = ["接住诉求，现场核实", "多方会商，拆清问题", "分类处理，形成方案", "公开回应，说明进展", "观察反馈，长效维护"];
  steps.forEach((item, idx) => {
    const y = 300 + idx * 112;
    ctx.addShape(slide, { x: 750, y, w: 870, h: 82, fill: "#ffffffb5", line: ctx.line(idx === 4 ? C.gold : C.teal, 2) });
    ctx.addText(slide, { text: String(idx + 1), x: 780, y: y + 18, w: 42, h: 42, fontSize: 31, color: idx === 4 ? C.gold : C.teal, bold: true, typeface: "PingFang SC", align: "center" });
    ctx.addText(slide, { text: item, x: 855, y: y + 20, w: 650, h: 40, fontSize: 33, color: C.ink, bold: true, typeface: "PingFang SC" });
  });
  ctx.addText(slide, { text: "重点：不是背流程，而是让考官听见你真的能把问题办下去。", x: 240, y: 872, w: 1450, h: 54, fontSize: 36, color: C.ink, bold: true, typeface: "PingFang SC", align: "center" });
  footer(slide, ctx, 6);

  return slide;
}
