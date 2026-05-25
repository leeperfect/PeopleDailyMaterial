import { bg, footer, label, title, box, stage, C } from "./shared.mjs";

export async function slide01(presentation, ctx) {
  const slide = presentation.slides.add();

  bg(slide, ctx, true);
  label(slide, ctx, "课堂主题", true);
  ctx.addText(slide, { text: "别把政绩观\n写成口号", x: 95, y: 188, w: 900, h: 190, fontSize: 82, color: "#f7efe2", bold: true, typeface: "PingFang SC" });
  ctx.addText(slide, { text: "人民日报这一天真正该学的是“把问题接住”", x: 100, y: 430, w: 1120, h: 70, fontSize: 42, color: "#f8d77d", bold: true, typeface: "PingFang SC" });
  ctx.addShape(slide, { x: 1160, y: 170, w: 560, h: 520, fill: "#ffffff10", line: ctx.line("#f8df9c70", 2) });
  ["问题清单", "责任清单", "办理清单", "反馈长效"].forEach((item, idx) => {
    const y = 225 + idx * 105;
    const color = idx === 0 ? "#e56a55" : idx === 3 ? "#f8d77d" : "#66c8bd";
    ctx.addShape(slide, { x: 1215, y, w: 54, h: 54, fill: "#00000000", line: ctx.line(color, 3) });
    ctx.addText(slide, { text: String(idx + 1), x: 1227, y: y + 9, w: 30, h: 30, fontSize: 27, color, bold: true, typeface: "PingFang SC", align: "center" });
    ctx.addText(slide, { text: item, x: 1300, y: y + 8, w: 280, h: 38, fontSize: 34, color: "#f7efe2", bold: true, typeface: "PingFang SC" });
  });
  ctx.addText(slide, { text: "申论写成治理链，面试答成处理链。", x: 1160, y: 740, w: 650, h: 50, fontSize: 31, color: "#f7efe2", typeface: "PingFang SC" });
  footer(slide, ctx, 1);

  return slide;
}
