import { C, FONT, bg, title, footer, box, bigQuote } from "./common.mjs";
export async function slide07(presentation, ctx) {
  const slide = presentation.slides.add(); bg(slide, ctx);
  title(slide, ctx, "课堂练习", "让学生现场把框架用起来", "这页可以直接作为课堂提问，也可以作为课后写作训练。");
  box(slide, ctx, 90, 318, 520, 210, C.white, C.line);
  ctx.addText(slide, { text: "练习题", x: 130, y: 350, w: 160, h: 32, fontSize: 26, color: C.red, bold: true, typeface: FONT });
  ctx.addText(slide, { text: "某老旧小区周边道路狭窄、停车混乱、老人出行不便。请你提出城市微改造建议。", x: 130, y: 405, w: 420, h: 92, fontSize: 24, color: C.ink, typeface: FONT });
  box(slide, ctx, 700, 310, 420, 235, C.softYellow, "#F2B705");
  ctx.addText(slide, { text: "要求学生答出", x: 740, y: 345, w: 240, h: 32, fontSize: 26, color: C.ink, bold: true, typeface: FONT });
  ctx.addText(slide, { text: "体检识别\n底线保障\n协同供给\n功能复合\n评估长效", x: 760, y: 400, w: 280, h: 128, fontSize: 24, color: C.ink, typeface: FONT });
  bigQuote(slide, ctx, "这个城市，究竟让谁的哪一段日常，变得更好了？", 250, 560, 780, 90, C.blue);
  footer(slide, ctx, 7); return slide;
}
