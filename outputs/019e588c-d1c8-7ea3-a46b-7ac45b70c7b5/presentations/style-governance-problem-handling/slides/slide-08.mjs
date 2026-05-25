import { bg, footer, label, title, box, stage, C } from "./shared.mjs";

export async function slide08(presentation, ctx) {
  const slide = presentation.slides.add();

  bg(slide, ctx, true);
  label(slide, ctx, "参考文章", true);
  ctx.addText(slide, { text: "本课实际使用的人民日报材料", x: 95, y: 155, w: 1150, h: 70, fontSize: 58, color: "#f7efe2", bold: true, typeface: "PingFang SC" });
  ["规范涉企行政执法专项行动取得明显成效｜第04版","完善制度机制 更好造福于民｜第04版","办酒席时当“饭店”，闲下来开农家乐｜第08版","“潮汐菜场”里的治理智慧｜第08版","群众的事就是我们的事｜第05版","“草原运河”映初心｜第05版"].forEach((item, idx) => {
    const y = 285 + idx * 92;
    ctx.addText(slide, { text: String(idx + 1).padStart(2, "0"), x: 120, y, w: 70, h: 38, fontSize: 28, color: idx < 2 ? "#f8d77d" : "#66c8bd", bold: true, typeface: "PingFang SC" });
    ctx.addText(slide, { text: item, x: 210, y, w: 1450, h: 42, fontSize: 31, color: "#f7efe2", typeface: "PingFang SC" });
  });
  ctx.addText(slide, { text: "教研转译提醒：“把问题接住”是课堂表达，不是人民日报原文标题。使用时保留具体案例动作。", x: 120, y: 890, w: 1580, h: 58, fontSize: 28, color: "#f7efe2cc", typeface: "PingFang SC" });
  footer(slide, ctx, 8);

  return slide;
}
