import { C, FONT, bg, title, footer, box } from "./common.mjs";
export async function slide04(presentation, ctx) {
  const slide = presentation.slides.add(); bg(slide, ctx);
  title(slide, ctx, "核心框架", "把案例拆成五步治理动作", "这套框架可以同时服务申论对策段和结构化面试组织题。");
  const items = [
    ["发现问题", "城市体检\n群众调查"], ["确定优先", "安全底线\n高频需求"], ["协同改造", "部门联动\n场景治理"], ["功能复合", "通行+教育\n文化+审美"], ["反馈长效", "评估效果\n维护责任"]
  ];
  items.forEach((it, i) => {
    const x = 82 + i * 225;
    box(slide, ctx, x, 340, 178, 178, i % 2 === 0 ? C.white : C.softBlue, i % 2 === 0 ? C.line : "#A7D5D1");
    ctx.addText(slide, { text: it[0], x: x + 24, y: 372, w: 130, h: 30, fontSize: 25, color: i === 1 ? C.red : C.ink, bold: true, align: "center", typeface: FONT });
    ctx.addText(slide, { text: it[1], x: x + 26, y: 428, w: 126, h: 70, fontSize: 20, color: C.muted, align: "center", typeface: FONT });
    if (i < 4) {
      ctx.addShape(slide, { x: x + 187, y: 424, w: 45, h: 5, fill: C.red, line: ctx.line(C.red, 0) });
      ctx.addShape(slide, { x: x + 227, y: 414, w: 16, h: 24, fill: C.red, line: ctx.line(C.red, 0) });
    }
  });
  footer(slide, ctx, 4); return slide;
}
