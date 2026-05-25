
const C = {
  paper: "#F7F8F4",
  ink: "#18212B",
  muted: "#667085",
  red: "#B42318",
  blue: "#0E7490",
  green: "#2F6B4F",
  yellow: "#F2B705",
  line: "#D7DCE0",
  white: "#FFFFFF",
  softBlue: "#EAF4F3",
  softRed: "#FCEBE8",
  softYellow: "#FFF8E8"
};
const FONT = "STHeiti";

function bg(slide, ctx) {
  ctx.addShape(slide, { x: 0, y: 0, w: 1280, h: 720, fill: C.paper, line: ctx.line("#000000", 0) });
  for (let x = 72; x < 1240; x += 120) {
    ctx.addShape(slide, { x, y: 78, w: 1, h: 560, fill: "#EDF0EC", line: ctx.line("#000000", 0) });
  }
}
function title(slide, ctx, kicker, main, sub) {
  ctx.addText(slide, { text: kicker, x: 70, y: 42, w: 520, h: 34, fontSize: 20, color: C.red, bold: true, typeface: FONT });
  ctx.addText(slide, { text: main, x: 70, y: 92, w: 720, h: 120, fontSize: 44, color: C.ink, bold: true, typeface: FONT });
  if (sub) ctx.addText(slide, { text: sub, x: 72, y: 218, w: 650, h: 70, fontSize: 23, color: C.muted, typeface: FONT });
}
function footer(slide, ctx, n) {
  ctx.addShape(slide, { x: 70, y: 665, w: 1140, h: 1, fill: C.line, line: ctx.line("#000000", 0) });
  ctx.addText(slide, { text: "人民日报素材课｜城市治理与公共服务", x: 70, y: 678, w: 460, h: 24, fontSize: 15, color: C.muted, typeface: FONT });
  ctx.addText(slide, { text: String(n).padStart(2, "0"), x: 1165, y: 676, w: 50, h: 28, fontSize: 18, color: C.blue, bold: true, align: "right", typeface: FONT });
}
function box(slide, ctx, x, y, w, h, fill = C.white, line = C.line) {
  return ctx.addShape(slide, { x, y, w, h, fill, line: ctx.line(line, 1.5) });
}
function label(slide, ctx, text, x, y, color = C.blue) {
  box(slide, ctx, x, y, 112, 34, color, color);
  ctx.addText(slide, { text, x: x + 14, y: y + 8, w: 84, h: 20, fontSize: 16, color: C.white, bold: true, align: "center", typeface: FONT });
}
function bullet(slide, ctx, text, x, y, w, color = C.ink) {
  ctx.addShape(slide, { x, y: y + 10, w: 8, h: 8, fill: C.red, line: ctx.line(C.red, 0) });
  ctx.addText(slide, { text, x: x + 22, y, w, h: 32, fontSize: 21, color, typeface: FONT });
}
function bigQuote(slide, ctx, text, x, y, w, h, color = C.red) {
  box(slide, ctx, x, y, w, h, C.white, C.line);
  ctx.addText(slide, { text: "“", x: x + 20, y: y + 8, w: 60, h: 54, fontSize: 52, color, bold: true, typeface: FONT });
  ctx.addText(slide, { text, x: x + 82, y: y + 30, w: w - 120, h: h - 40, fontSize: 25, color: C.ink, bold: true, typeface: FONT });
}
export { C, FONT, bg, title, footer, box, label, bullet, bigQuote };
