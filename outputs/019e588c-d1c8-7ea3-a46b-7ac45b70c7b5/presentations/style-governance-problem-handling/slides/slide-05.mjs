import { bg, footer, label, title, box, stage, C } from "./shared.mjs";

export async function slide05(presentation, ctx) {
  const slide = presentation.slides.add();

  bg(slide, ctx);
  label(slide, ctx, "申论转译");
  title(slide, ctx, "把口号改成能得分的治理表达", 145, 60, 1220);
  box(slide, ctx, { x: 95, y: 330, w: 820, h: 220, head: "不要只写", body: "加大服务企业力度。", color: C.red });
  box(slide, ctx, { x: 1005, y: 330, w: 820, h: 220, head: "可以改成", body: "让监管更精准、执法更规范、标准更统一、诉求更畅通。", color: C.teal });
  box(slide, ctx, { x: 95, y: 625, w: 820, h: 230, head: "不要只写", body: "坚持以人民为中心。", color: C.red });
  box(slide, ctx, { x: 1005, y: 625, w: 820, h: 230, head: "可以改成", body: "把群众生活中的堵点、企业经营中的痛点、基层执行中的难点纳入办理过程。", color: C.teal });
  footer(slide, ctx, 5);

  return slide;
}
