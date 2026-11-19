// Cast and printed graphics for the thoughts short, drawn with the bridge Pen in the 600 x 1000 design space
// (soles at y = 975): a dog and a squirrel, the thought bubble (800 x 600 card) and the little icons that go in it.
import { Pen, INK, faceFront, shade, thickAngle } from "../bridge/toon";

type P2 = [number, number];
const rad = (d: number) => (d * Math.PI) / 180;
export const LIGHT = rad(-120);
export const FONT = "CapFont, 'DejaVu Sans', sans-serif";

const ring = (p: Pen, pts: P2[], w = 13) => p.inkRing(pts, w, thickAngle(LIGHT));
const ellP = (cx: number, cy: number, rx: number, ry: number, n = 64): P2[] =>
  Array.from({ length: n }, (_, i) => { const a = (i / n) * Math.PI * 2; return [cx + rx * Math.cos(a), cy + ry * Math.sin(a)] as P2; });
const rrect = (x0: number, y0: number, x1: number, y1: number, r: number): P2[] => {
  const o: P2[] = [];
  for (const [cx, cy, a] of [[x1 - r, y0 + r, -90], [x1 - r, y1 - r, 0], [x0 + r, y1 - r, 90], [x0 + r, y0 + r, 180]] as const)
    for (let i = 0; i <= 6; i++) o.push([cx + r * Math.cos(rad(a + (90 * i) / 6)), cy + r * Math.sin(rad(a + (90 * i) / 6))]);
  return o;
};
export const text = (p: Pen, s: string, x: number, y: number, size: number, fill: string, outline = 0, align: CanvasTextAlign = "center") => {
  const g = p.g;
  g.save(); g.font = `900 ${size}px ${FONT}`; g.textAlign = align; g.textBaseline = "middle";
  if (outline) { g.lineJoin = "round"; g.lineWidth = outline; g.strokeStyle = INK; g.strokeText(s, x, y); }
  g.fillStyle = fill; g.fillText(s, x, y); g.restore();
};
/** fit text to a max width */
const fitText = (p: Pen, s: string, x: number, y: number, size: number, maxW: number, fill: string) => {
  const g = p.g; g.save(); g.font = `900 ${size}px ${FONT}`; const w = g.measureText(s).width; g.restore();
  text(p, s, x, y, w > maxW ? (size * maxW) / w : size, fill);
};

// ---------------- the thought bubble ----------------
const LOBES: [number, number, number][] = [[250, 200, 120], [380, 150, 135], [520, 180, 120], [610, 280, 105], [530, 370, 115], [380, 395, 125], [240, 360, 115], [180, 270, 105], [400, 270, 200]];
/** thought bubble on an 800 x 600 canvas: cloud lobes + two trailing dots toward (tail = -1 left / +1 right) the bottom */
export const bubble = (p: Pen, content: (p: Pen) => void, tail: -1 | 1 = -1, tint = "#ffffff") => {
  const g = p.g;
  const tx = (x: number) => (tail < 0 ? x : 800 - x);
  g.save(); g.fillStyle = INK;
  for (const [x, y, r] of LOBES) { g.beginPath(); g.ellipse(x, y, r + 12, (r + 12) * 0.86, 0, 0, 7); g.fill(); }
  for (const [x, y, r] of [[tx(170), 500, 40], [tx(105), 565, 24]] as const) { g.beginPath(); g.arc(x, y, r + 11, 0, 7); g.fill(); }
  g.fillStyle = tint;
  for (const [x, y, r] of LOBES) { g.beginPath(); g.ellipse(x, y, r, r * 0.86, 0, 0, 7); g.fill(); }
  for (const [x, y, r] of [[tx(170), 500, 40], [tx(105), 565, 24]] as const) { g.beginPath(); g.arc(x, y, r, 0, 7); g.fill(); }
  g.fillStyle = "rgba(120,140,190,0.16)";
  for (const [x, y, r] of LOBES.slice(4, 7)) { g.beginPath(); g.ellipse(x + 10, y + 18, r * 0.8, r * 0.5, 0, 0, Math.PI); g.fill(); }
  g.restore();
  content(p);
};
/** words in a bubble: 1-3 lines */
export const words = (lines: string[], col = INK, size = 110) => (p: Pen) => {
  const n = lines.length, lh = size * 1.02, y0 = 275 - ((n - 1) * lh) / 2;
  lines.forEach((s, i) => fitText(p, s, 400, y0 + i * lh, size, 470, Array.isArray(col) ? col[i] : col));
};

// ---------------- icons (drawn inside the bubble, centre ~ (400, 270)) ----------------
export const taco = (p: Pen) => {
  const cx = 400, cy = 230;
  for (let i = 0; i < 7; i++) p.ell(cx - 150 + i * 50, cy - 8 - 14 * Math.sin(i * 1.7), 34, 26, "#62b84a", 8);
  for (let i = 0; i < 4; i++) p.ell(cx - 110 + i * 72, cy + 2, 22, 18, "#e0463c", 7);
  const shell: P2[] = []; for (let i = 0; i <= 32; i++) { const a = (i / 32) * Math.PI; shell.push([cx + 200 * Math.cos(a), cy + 20 + 170 * Math.sin(a)]); }
  p.poly(shell, "#f2c14e", 12);
  for (let i = 0; i < 5; i++) p.dot(cx - 120 + i * 60, cy + 90 + 25 * Math.sin(i * 2), 9, "#d29a2a");
};
export const ball = (p: Pen, x = 400, y = 270, r = 120) => {
  p.ell(x, y, r, r, "#d8f04a", 12);
  p.arc(x - r * 0.9, y, r * 0.55, r * 0.95, -80, 80, 10, "#ffffff");
  p.arc(x + r * 0.9, y, r * 0.55, r * 0.95, 100, 260, 10, "#ffffff");
};
export const answers = (p: Pen) => {
  text(p, "1. B", 270, 175, 92, INK, 0, "left"); text(p, "2. C", 270, 275, 92, INK, 0, "left"); text(p, "3. A", 270, 375, 92, INK, 0, "left");
  text(p, "✓", 520, 175, 80, "#2fa84f"); text(p, "✓", 520, 275, 80, "#2fa84f"); text(p, "✓", 520, 375, 80, "#2fa84f");
};
export const yuck = (p: Pen) => {
  p.ell(300, 275, 105, 105, "#9fd65a", 12);
  p.stroke([[255, 245], [285, 255]], 12); p.stroke([[345, 245], [315, 255]], 12);
  p.stroke([[255, 320], [275, 305], [300, 320], [325, 305], [345, 320]], 12);
  text(p, "YUCK", 520, 275, 104, "#4f9a2c");
};
export const vase = (p: Pen) => {
  const v: P2[] = [[220, 160], [300, 160], [290, 200], [340, 270], [320, 380], [200, 380], [180, 270], [230, 200]];
  p.poly(v, "#4f8fe0", 12);
  p.stroke([[262, 170], [250, 230], [280, 270], [255, 330], [275, 380]], 10);
  p.poly([[120, 405], [400, 405], [400, 420], [120, 420]], INK, 0);
  text(p, "AGE 8", 520, 230, 88, "#d8312c"); text(p, "!!!", 520, 330, 88, "#d8312c");
};
export const notes = (p: Pen, k = 0) => {
  const nt = (x: number, y: number, s: number, two: boolean) => {
    p.ell(x, y, 34 * s, 26 * s, INK, 0, 0, 360, -20);
    p.stroke([[x + 30 * s, y - 6 * s], [x + 30 * s, y - 120 * s]], 12 * s);
    if (two) { p.ell(x + 85 * s, y - 15 * s, 34 * s, 26 * s, INK, 0, 0, 360, -20); p.stroke([[x + 115 * s, y - 21 * s], [x + 115 * s, y - 135 * s]], 12 * s); p.poly([[x + 30 * s, y - 120 * s], [x + 115 * s, y - 135 * s], [x + 115 * s, y - 105 * s], [x + 30 * s, y - 90 * s]], INK, 0); }
    else p.poly([[x + 30 * s, y - 120 * s], [x + 80 * s, y - 90 * s], [x + 80 * s, y - 65 * s], [x + 30 * s, y - 92 * s]], INK, 0);
  };
  nt(250, 340 - 20 * k, 1.1, true); nt(470, 330 + 20 * k, 1.0, false);
};
export const worry = (p: Pen) => { text(p, "!", 400, 275, 260, "#e0463c"); };
export const grocery = (p: Pen) => {
  p.poly(rrect(230, 110, 570, 440, 18), "#fffdf2", 10);
  text(p, "MILK", 400, 175, 64, INK); text(p, "EGGS", 400, 260, 64, INK); text(p, "BREAD", 400, 345, 64, INK);
  p.stroke([[290, 260], [510, 255]], 8, "#d8312c");
};
export const cringe = (p: Pen) => {
  text(p, "2009", 400, 200, 120, "#7b5ac9");
  p.ell(400, 345, 70, 60, "#ffd2c0", 10);
  p.stroke([[370, 330], [385, 335]], 9); p.stroke([[430, 330], [415, 335]], 9);
  p.stroke([[370, 372], [430, 372]], 9);
  for (const s of [-1, 1]) p.ell(400 + s * 50, 360, 14, 9, "#ff8a8a", 0);
};
export const money = (p: Pen) => { text(p, "$$$", 400, 275, 170, "#2fa84f"); };
export const deadline = (p: Pen) => { text(p, "DEADLINE", 400, 230, 84, "#d8312c"); text(p, "5 PM", 400, 330, 84, INK); };
export const acorn = (p: Pen, x = 400, y = 280, s = 1) => {
  p.ell(x, y + 40 * s, 80 * s, 95 * s, "#c9873e", 11);
  p.ell(x, y - 40 * s, 100 * s, 50 * s, "#7a5232", 11);
  for (let i = -2; i <= 2; i++) p.stroke([[x + i * 30 * s, y - 70 * s], [x + i * 34 * s, y - 15 * s]], 5, shade("#7a5232", 0.7));
  p.stroke([[x, y - 88 * s], [x + 10 * s, y - 125 * s]], 14 * s, "#5a3a22");
};
export const nuts = (p: Pen) => { acorn(p, 260, 290, 0.95); text(p, "???", 520, 275, 120, "#c9873e"); };
export const dots = (p: Pen) => { for (const x of [310, 400, 490]) p.dot(x, 275, 22, INK); };
export const question = (p: Pen) => { text(p, "?", 400, 280, 250, "#3f86e8"); };

// ---------------- animals ----------------
/** a sitting dog, front view, tongue out; `pant` 0..1 bobs the tongue */
export const dog = (p: Pen, blink = 0, pant = 0, look = 0) => {
  const B = "#d9a35b", D = shade(B, 0.7), W = "#f6ead8";
  const body = ellP(300, 830, 150, 150, 48); p.shadedFill(body, B, D, LIGHT, 150); ring(p, body);
  p.ell(300, 860, 80, 100, W, 0);
  for (const s of [-1, 1]) { const paw = ellP(300 + s * 70, 950, 45, 28, 24); p.poly(paw, W, 10); }
  const hx = 300 + 18 * look, hy = 600;
  for (const s of [-1, 1]) { const ear: P2[] = [[hx + s * 70, hy - 85], [hx + s * 150, hy - 40], [hx + s * 140, hy + 70], [hx + s * 95, hy + 40]]; p.poly(ear, shade(B, 0.6), 11); }
  const head = ellP(hx, hy, 125, 112, 64); p.shadedFill(head, B, D, LIGHT, 125); ring(p, head);
  p.ell(hx, hy + 52, 72, 52, W, 9);
  p.ell(hx, hy + 22, 26, 18, INK, 0);
  const tl = 30 + 10 * pant;
  p.poly([[hx - 20, hy + 78], [hx + 20, hy + 78], [hx + 18, hy + 78 + tl], [hx - 18, hy + 78 + tl]], "#f07c8c", 8);
  p.stroke([[hx - 34, hy + 72], [hx, hy + 60], [hx + 34, hy + 72]], 8, INK);
  for (const s of [-1, 1]) {
    if (blink > 0.5) p.stroke([[hx + s * 48 - 14, hy - 20], [hx + s * 48 + 14, hy - 20]], 9, INK);
    else { p.dot(hx + s * 48, hy - 20, 15, INK); p.dot(hx + s * 48 + 5, hy - 26, 5, "#ffffff"); }
  }
};
/** a squirrel sitting up, front view, big tail behind; size in the same 600 x 1000 space but small (scale it ~0.25) */
export const squirrel = (p: Pen, blink = 0, expr: "neutral" | "shock" = "neutral", hue = 0) => {
  const B = ["#c8743a", "#b8692f", "#d4813f"][hue % 3], D = shade(B, 0.68), W = "#f7e6cf";
  const tail: P2[] = []; for (let i = 0; i <= 40; i++) { const a = rad(200 + i * 6.5), r = 230 - 40 * Math.sin(i / 6); tail.push([400 + r * 0.8 * Math.cos(a) + 60, 560 + r * 1.3 * Math.sin(a) + 160]); }
  p.poly([...tail, [430, 900], [380, 900]], shade(B, 1.08), 12);
  const body = ellP(300, 790, 130, 170, 48); p.shadedFill(body, B, D, LIGHT, 150); ring(p, body);
  p.ell(300, 820, 75, 120, W, 0);
  for (const s of [-1, 1]) p.ell(300 + s * 60, 955, 50, 26, B, 10);
  for (const s of [-1, 1]) p.ell(300 + s * 40, 720, 26, 34, B, 9);
  const hx = 300, hy = 520;
  for (const s of [-1, 1]) p.poly([[hx + s * 50, hy - 90], [hx + s * 95, hy - 175], [hx + s * 110, hy - 70]], B, 11);
  const head = ellP(hx, hy, 120, 105, 64); p.shadedFill(head, B, D, LIGHT, 120); ring(p, head);
  for (const s of [-1, 1]) p.ell(hx + s * 60, hy + 45, 48, 38, W, 0);
  p.ell(hx, hy + 22, 16, 12, INK, 0);
  if (expr === "shock") p.ell(hx, hy + 65, 16, 20, INK, 0);
  else { p.stroke([[hx - 20, hy + 52], [hx, hy + 44], [hx + 20, hy + 52]], 7, INK); p.poly([[hx - 12, hy + 52], [hx + 12, hy + 52], [hx + 10, hy + 74], [hx - 10, hy + 74]], "#ffffff", 5); }
  for (const s of [-1, 1]) {
    if (blink > 0.5) p.stroke([[hx + s * 45 - 14, hy - 15], [hx + s * 45 + 14, hy - 15]], 9, INK);
    else { const r = expr === "shock" ? 22 : 18; p.dot(hx + s * 45, hy - 15, r, INK); p.dot(hx + s * 45 + 6, hy - 22, 6, "#ffffff"); }
  }
};
export { faceFront };
/** counter board (900 x 300): label + value */
export const counter = (p: Pen, label: string, value: string, col: string) => {
  p.poly(rrect(14, 14, 886, 286, 34), "#1d2440", 12);
  if (label) { text(p, label, 60, 152, 84, "#ffffff", 0, "left"); text(p, value, 846, 152, 110, col, 0, "right"); }
  else text(p, value, 450, 156, 150, col);
};
export const plate = (p: Pen, s: string, w: number, h: number, bg = "#ffffff", fg = INK) => {
  p.poly(rrect(8, 8, w - 8, h - 8, 22), bg, 12);
  text(p, s, w / 2, h / 2 + 4, h * 0.56, fg);
};
export const board = (p: Pen, lines: string[], w: number, h: number, bg = "#2f5d48", fg = "#f4f1e6") => {
  p.poly(rrect(8, 8, w - 8, h - 8, 16), bg, 14);
  const lh = (h - 60) / (lines.length + 0.4);
  lines.forEach((s, i) => text(p, s, w / 2, 40 + lh * (i + 0.7), lh * 0.62, fg));
};
