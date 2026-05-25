import { bg, footer, label, title, box, stage, C } from "./shared.mjs";

export async function slide03(presentation, ctx) {
  const slide = presentation.slides.add();

  bg(slide, ctx);
  label(slide, ctx, "人民日报案例");
  title(slide, ctx, "看起来是多篇文章，其实都在讲同一件事", 145, 56, 1320);
  const cases = [
    ["涉企执法", "接住企业对乱检查、乱罚款、标准不一的担忧", C.red],
    ["完善制度机制", "把群众诉求纳入清单办理和闭环反馈", C.teal],
    ["合约食堂", "给酒席攀比治理一个可接受的替代空间", C.gold],
    ["潮汐菜场", "用时间错峰接住买菜需求和道路秩序两难", C.blue],
    ["群众来论", "职责有边界，但群众找上门的问题要先接住", C.teal],
  ];
  cases.forEach((item, idx) => {
    const x = 115 + (idx % 3) * 590;
    const y = idx < 3 ? 335 : 620;
    const w = idx < 3 ? 500 : 790;
    box(slide, ctx, { x, y, w, h: 210, head: item[0], body: item[1], color: item[2] });
  });
  ctx.addText(slide, { text: "共同逻辑：不是把问题推开，而是让问题进入办理过程。", x: 210, y: 885, w: 1500, h: 54, fontSize: 38, color: C.ink, bold: true, typeface: "PingFang SC", align: "center" });
  footer(slide, ctx, 3);

  return slide;
}
