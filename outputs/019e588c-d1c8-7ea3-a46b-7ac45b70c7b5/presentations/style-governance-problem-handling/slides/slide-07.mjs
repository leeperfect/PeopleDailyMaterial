import { bg, footer, label, title, box, stage, C } from "./shared.mjs";

export async function slide07(presentation, ctx) {
  const slide = presentation.slides.add();

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

  return slide;
}
