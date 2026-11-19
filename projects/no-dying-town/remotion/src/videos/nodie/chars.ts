// Cast and printed graphics for the no-dying town short, drawn with the bridge Pen in the same 600 x 1000 design
// space (soles at y = 975): flu germs, a polar bear, the pregnant traveller and the old man (bodyFront + extras),
// and the flat graphics (road sign, CLOSED stamp, thermometer, plane ticket, counters).
import { Pen, INK, faceFront, shade, thickAngle, Expr, bodyFront, Outfit, FrontOpts } from "../bridge/toon";

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
const text = (p: Pen, s: string, x: number, y: number, size: number, fill: string, outline = 0, align: CanvasTextAlign = "center") => {
  const g = p.g;
  g.save(); g.font = `900 ${size}px ${FONT}`; g.textAlign = align; g.textBaseline = "middle";
  if (outline) { g.lineJoin = "round"; g.lineWidth = outline; g.strokeStyle = INK; g.strokeText(s, x, y); }
  g.fillStyle = fill; g.fillText(s, x, y); g.restore();
};

/** a flu germ: green ball with stubby spikes, deadpan face, little waving arm. size ~ 400 units, sits at y 975 */
export const germ = (p: Pen, expr: Expr = "neutral", blink = 0, wave = 0, hue = 0) => {
  const base = ["#8fd14f", "#6fc06a", "#b4d84a"][hue % 3], dark = shade(base, 0.68), cx = 300, cy = 760, r = 170;
  for (let k = 0; k < 12; k++) { // spikes with ball tips
    const a = (k / 12) * Math.PI * 2 + 0.13, x0 = cx + r * 0.9 * Math.cos(a), y0 = cy + r * 0.9 * Math.sin(a), x1 = cx + (r + 52) * Math.cos(a), y1 = cy + (r + 52) * Math.sin(a);
    p.stroke([[x0, y0], [x1, y1]], 22, INK); p.stroke([[x0, y0], [x1, y1]], 10, dark);
    p.ell(x1, y1, 19, 19, base, 9);
  }
  const pts = ellP(cx, cy, r, r * 0.95, 64);
  p.shadedFill(pts, base, dark, LIGHT, r);
  for (const [x, y, s] of [[-70, 60, 18], [80, 40, 14], [20, 110, 11], [-100, -20, 10]] as const) p.ell(cx + x, cy + y, s, s * 0.8, shade(base, 0.82), 0);
  ring(p, pts);
  if (wave > 0) { // arm: waves from the right side
    const sw = Math.sin(wave * Math.PI * 6) * 0.5, sh: P2 = [cx + r * 0.85, cy - 20], hand: P2 = [sh[0] + 90 * Math.cos(-1.1 + sw), sh[1] + 120 * Math.sin(-1.1 + sw)];
    p.stroke([sh, hand], 20, INK); p.stroke([sh, hand], 10, dark); p.ell(hand[0], hand[1], 20, 20, base, 9);
  }
  faceFront(p, cx, cy + 5, 200, expr, 0, 0, blink, false, base);
};

/** a polar bear standing on all fours, seen from the front, peeking: head tilt by `look` (-1..1) */
export const bear = (p: Pen, look = 0, blink = 0) => {
  const W = "#f5f3ea", D = "#cfd5dd";
  const body = ellP(300, 790, 255, 150, 64);
  p.shadedFill(body, W, D, LIGHT, 255);
  ring(p, body);
  for (const x of [150, 235, 365, 450]) { const leg = rrect(x - 42, 820, x + 42, 975, 30); p.shadedFill(leg, W, D, LIGHT, 80); ring(p, leg, 11); }
  const hx = 300 + 28 * look, hy = 640;
  for (const s of [-1, 1]) { const e = ellP(hx + s * 92, hy - 92, 34, 30, 24); p.poly(e, W, 11); p.ell(hx + s * 92, hy - 88, 15, 12, "#d8c7c0", 0); }
  const head = ellP(hx, hy, 140, 122, 64);
  p.shadedFill(head, W, D, LIGHT, 140);
  ring(p, head);
  p.ell(hx + 10 * look, hy + 48, 70, 52, "#fbfaf5", 9);
  p.ell(hx + 14 * look, hy + 22, 26, 18, INK, 0);
  p.stroke([[hx + 14 * look, hy + 40], [hx + 14 * look, hy + 62]], 8, INK);
  p.stroke([[hx - 26 + 14 * look, hy + 70], [hx + 14 * look, hy + 62], [hx + 26 + 14 * look, hy + 70]], 8, INK);
  for (const s of [-1, 1]) {
    if (blink > 0.5) p.stroke([[hx + s * 52 - 14 + 20 * look, hy - 22], [hx + s * 52 + 14 + 20 * look, hy - 22]], 9, INK);
    else p.dot(hx + s * 52 + 20 * look, hy - 22, 13, INK);
  }
};

/** a character from bodyFront with extras: pregnant belly / walking cane */
export const person = (p: Pen, o: Outfit, opts: FrontOpts, extra: { belly?: boolean; cane?: boolean } = {}) => {
  bodyFront(p, o, opts);
  if (extra.belly) {
    const pts = ellP(300, 700, 92, 82, 48);
    p.shadedFill(pts, o.dress ?? o.jacket, shade(o.dress ?? o.jacket, 0.72), LIGHT, 92);
    ring(p, pts, 11);
  }
  if (extra.cane) {
    p.stroke([[402, 700], [430, 972]], 20, INK); p.stroke([[402, 700], [430, 972]], 10, "#8a5a3a");
    p.arc(386, 702, 18, 18, 180, 360, 14, "#8a5a3a");
  }
};

// ---------------- printed graphics ----------------
/** road sign (600 x 600): red ring, a coffin, a red slash; "NO DYING" plate under it is drawn separately */
export const roadSign = (p: Pen) => {
  const g = p.g;
  g.fillStyle = "#ffffff"; g.beginPath(); g.arc(300, 300, 288, 0, 7); g.fill();
  g.strokeStyle = INK; g.lineWidth = 14; g.stroke();
  g.strokeStyle = "#d42f2f"; g.lineWidth = 58; g.beginPath(); g.arc(300, 300, 240, 0, 7); g.stroke();
  // coffin (hexagon), lid line, cross
  const cof: P2[] = [[300, 120], [362, 176], [340, 470], [260, 470], [238, 176]];
  p.poly(cof, "#6b4228", 12);
  p.stroke([[300, 210], [300, 330]], 16, "#f2e6c8"); p.stroke([[262, 250], [338, 250]], 16, "#f2e6c8");
  p.stroke([[132, 468], [468, 132]], 58, "#d42f2f");
};
export const plate = (p: Pen, s: string, w: number, h: number, bg = "#ffffff", fg = INK) => {
  p.poly(rrect(8, 8, w - 8, h - 8, 22), bg, 12);
  text(p, s, w / 2, h / 2 + 4, h * 0.56, fg);
};
/** CLOSED stamp (800 x 300) */
export const closedStamp = (p: Pen) => {
  const RED = "#d8312c";
  p.poly(rrect(20, 20, 780, 280, 30), null, 0);
  const g = p.g; g.save(); g.strokeStyle = RED; g.lineWidth = 24; g.beginPath(); p.path(rrect(30, 30, 770, 270, 26), true); g.stroke();
  g.lineWidth = 8; g.beginPath(); p.path(rrect(58, 58, 742, 242, 16), true); g.stroke(); g.restore();
  text(p, "CLOSED", 400, 158, 150, RED);
};
/** thermometer stuck below zero (300 x 900) */
export const thermo = (p: Pen) => {
  p.poly(rrect(95, 40, 205, 760, 55), "#ffffff", 12);
  p.ell(150, 790, 85, 85, "#ffffff", 12);
  p.ell(150, 790, 62, 62, "#3f86e8", 0);
  p.poly(rrect(128, 520, 172, 790, 20), "#3f86e8", 0);
  for (let i = 0; i < 9; i++) p.stroke([[205, 100 + i * 70], [240, 100 + i * 70]], 7, INK);
  p.stroke([[60, 450], [258, 450]], 10, "#d42f2f");
  text(p, "0°", 262, 452, 62, "#d42f2f", 0, "left");
};
/** plane ticket (900 x 420) */
export const ticket = (p: Pen) => {
  p.poly(rrect(14, 14, 886, 406, 30), "#fff7e0", 12);
  p.poly([[14, 60], [886, 60], [886, 14], [14, 14]], "#2d6fd0", 0);
  p.poly(rrect(14, 14, 886, 406, 30), null, 12);
  p.stroke([[650, 40], [650, 390]], 6, "#9a8f7a");
  text(p, "BOARDING PASS", 40, 112, 50, "#2d6fd0", 0, "left");
  text(p, "LYR", 40, 230, 110, INK, 0, "left");
  text(p, "→", 300, 226, 100, "#2d6fd0");
  text(p, "OSL", 380, 230, 110, INK, 0, "left");
  text(p, "ONE WAY", 40, 340, 46, "#d42f2f", 0, "left");
  p.poly([[700, 160], [840, 160], [840, 330], [700, 330]], null, 0);
  for (let i = 0; i < 14; i++) p.stroke([[700 + i * 10, 170], [700 + i * 10, 330]], i % 3 ? 4 : 8, INK);
};
/** counter board (900 x 300): label + value */
export const counter = (p: Pen, label: string, value: string, col: string) => {
  p.poly(rrect(14, 14, 886, 286, 34), "#1d2440", 12);
  text(p, label, 60, 152, 96, "#ffffff", 0, "left");
  text(p, value, 846, 152, 120, col, 0, "right");
};
/** "50,000,000" with a germ (1000 x 360) */
export const deathToll = (p: Pen) => {
  text(p, "50,000,000", 500, 190, 170, "#ffffff", 26);
};
/** big arrow with a word (700 x 300) */
export const arrow = (p: Pen, word: string) => {
  p.poly([[20, 110], [470, 110], [470, 30], [680, 150], [470, 270], [470, 190], [20, 190]], "#ffd84d", 12);
  text(p, word, 250, 152, 70, INK);
};
