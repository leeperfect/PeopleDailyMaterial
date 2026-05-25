
export const C = {
  paper: "#f6efe3",
  paper2: "#fbf7ef",
  ink: "#173044",
  muted: "#647582",
  grid: "#d8e0e6",
  blue: "#1f4f77",
  red: "#b54836",
  teal: "#1f7972",
  gold: "#c39a3b",
  line: "#b7c6d2",
  white: "#ffffff",
};

export function bg(slide, ctx, dark = false) {
  ctx.addShape(slide, { x: 0, y: 0, w: ctx.W, h: ctx.H, fill: dark ? "#112537" : C.paper, line: ctx.line("#00000000", 0) });
  for (let x = 0; x <= ctx.W; x += 80) {
    ctx.addShape(slide, { x, y: 0, w: 1, h: ctx.H, fill: dark ? "#ffffff12" : "#1f4f7712", line: ctx.line("#00000000", 0) });
  }
  for (let y = 0; y <= ctx.H; y += 80) {
    ctx.addShape(slide, { x: 0, y, w: ctx.W, h: 1, fill: dark ? "#ffffff12" : "#1f4f7712", line: ctx.line("#00000000", 0) });
  }
}

export function footer(slide, ctx, page) {
  ctx.addText(slide, {
    text: "人民日报 2026-05-22 教研转译",
    x: 90, y: 1015, w: 620, h: 36,
    fontSize: 24, color: C.muted, typeface: "PingFang SC",
  });
  ctx.addText(slide, {
    text: String(page).padStart(2, "0") + " / 08",
    x: 1700, y: 1015, w: 130, h: 36,
    fontSize: 24, color: C.muted, bold: true, typeface: "PingFang SC", align: "right",
  });
}

export function label(slide, ctx, text, dark = false) {
  ctx.addShape(slide, { x: 90, y: 70, w: 390, h: 54, fill: dark ? "#ffffff10" : "#ffffffa8", line: ctx.line(dark ? "#f8df9c70" : C.line, 1) });
  ctx.addText(slide, { text, x: 110, y: 84, w: 350, h: 30, fontSize: 24, color: dark ? "#f8df9c" : C.blue, bold: true, typeface: "PingFang SC" });
}

export function title(slide, ctx, text, y = 145, size = 58, w = 1250) {
  ctx.addText(slide, { text, x: 90, y, w, h: 140, fontSize: size, color: C.ink, bold: true, typeface: "PingFang SC", insets: { left: 0, right: 0, top: 0, bottom: 0 } });
}

export function box(slide, ctx, { x, y, w, h, head, body, color = C.teal }) {
  ctx.addShape(slide, { x, y, w, h, fill: "#ffffffb5", line: ctx.line(color, 2) });
  ctx.addShape(slide, { x, y, w: 8, h, fill: color, line: ctx.line("#00000000", 0) });
  ctx.addText(slide, { text: head, x: x + 28, y: y + 22, w: w - 54, h: 40, fontSize: 29, color: C.ink, bold: true, typeface: "PingFang SC" });
  ctx.addText(slide, { text: body, x: x + 28, y: y + 72, w: w - 54, h: h - 88, fontSize: 23, color: C.muted, typeface: "PingFang SC" });
}

export function stage(slide, ctx, { x, y, num, head, body, color }) {
  ctx.addShape(slide, { x, y, w: 250, h: 210, fill: "#ffffffb8", line: ctx.line(color, 2) });
  ctx.addShape(slide, { x: x + 25, y: y + 24, w: 58, h: 58, fill: "#00000000", line: ctx.line(color, 3) });
  ctx.addText(slide, { text: String(num), x: x + 39, y: y + 34, w: 30, h: 30, fontSize: 28, color, bold: true, typeface: "PingFang SC", align: "center" });
  ctx.addText(slide, { text: head, x: x + 25, y: y + 98, w: 200, h: 38, fontSize: 31, color: C.ink, bold: true, typeface: "PingFang SC", align: "center" });
  ctx.addText(slide, { text: body, x: x + 25, y: y + 145, w: 200, h: 48, fontSize: 20, color: C.muted, typeface: "PingFang SC", align: "center" });
}
