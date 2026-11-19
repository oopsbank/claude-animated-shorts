// Cast for "What If Night Never Came Again?": round bean people, an owl, a firefly, a night flower, clock and
// thermometer signs. Pen drawings in the 600 x 1000 design space (soles at y = 975) unless noted.
import { Pen, INK, faceFront, shade, thickAngle, Expr } from "../bridge/toon";

type P2 = [number, number];
const rad = (d: number) => (d * Math.PI) / 180;
export const LIGHT = rad(-120);
const ring = (p: Pen, pts: P2[], w = 13) => p.inkRing(pts, w, thickAngle(LIGHT));
const ellP = (cx: number, cy: number, rx: number, ry: number, n = 64): P2[] =>
  Array.from({ length: n }, (_, i) => { const a = (i / n) * Math.PI * 2; return [cx + rx * Math.cos(a), cy + ry * Math.sin(a)] as P2; });

export const SKINS = ["#ffb4a2", "#9ad0f5", "#ffd66b", "#b7e38a", "#d7b4f3", "#ff9e7a", "#8fe0d0"];

/** bean person. arms: 0 down, 1 up (cheer), 2 out (wobble). lean in radians. */
export const person = (p: Pen, col: string, expr: Expr, blink = 0, arms = 0, zz = 0) => {
  const cy = 640, rx = 175, ry = 225;
  // legs + shoes
  for (const x of [245, 355]) { p.line([[x, 840], [x, 935]], col, 34); p.ell(x + (x < 300 ? -14 : 14), 950, 46, 26, "#3a3340", 9); }
  // arms
  const armPts: Record<number, [P2, P2][]> = {
    0: [[[135, 650], [95, 790]], [[465, 650], [505, 790]]],
    1: [[[140, 560], [70, 410]], [[460, 560], [530, 410]]],
    2: [[[135, 620], [40, 600]], [[465, 620], [560, 650]]],
  };
  for (const [a, b] of armPts[arms]) { p.line([a, b], col, 30); p.dot(b[0], b[1], 22, col); }
  const pts = ellP(300, cy, rx, ry, 72);
  p.shadedFill(pts, col, shade(col, 0.78), LIGHT, rx);
  p.ell(300 - rx * 0.45, cy - ry * 0.55, 34, 22, "rgba(255,255,255,0.55)", 0, 0, 360, -35);
  ring(p, pts, 12);
  faceFront(p, 300, cy - 30, 200, expr, 0, 0, blink, false, col);
  if (zz > 0) for (let i = 0; i < 3; i++) {
    const k = Math.max(0, Math.min(1, zz * 3 - i)), x = 430 + i * 45, y = 380 - i * 70, s = 22 + i * 8;
    if (k > 0) p.stroke([[x - s, y - s], [x + s, y - s], [x - s, y + s], [x + s, y + s]], 11 * k, "#ffffff");
  }
};

/** round alarm clock sign on a 600 x 600 canvas; ang = hand angle (rad) */
export const clockSign = (p: Pen, ang: number) => {
  p.ell(170, 120, 60, 50, "#e8443a", 10); p.ell(430, 120, 60, 50, "#e8443a", 10);
  p.ell(300, 320, 230, 230, "#fff6e0", 14);
  for (let i = 0; i < 12; i++) { const a = (i / 12) * Math.PI * 2; p.stroke([[300 + 185 * Math.cos(a), 320 + 185 * Math.sin(a)], [300 + 205 * Math.cos(a), 320 + 205 * Math.sin(a)]], 10); }
  // moon in the clock face (the body waits for night)
  p.ell(300, 230, 46, 46, "#5a6ab8", 8); p.ell(322, 214, 40, 40, "#fff6e0", 0);
  p.stroke([[300, 320], [300 + 150 * Math.cos(ang), 320 + 150 * Math.sin(ang)]], 16);
  p.stroke([[300, 320], [300 + 100 * Math.cos(ang / 12 + 1), 320 + 100 * Math.sin(ang / 12 + 1)]], 20);
  p.dot(300, 320, 18);
};

/** owl on a branch stub, 600 x 1000. squint 0..1 (eyes shut tight against the sun) */
export const owl = (p: Pen, squint: number, blink = 0) => {
  const body = ellP(300, 640, 190, 250, 64);
  p.shadedFill(body, "#a07450", "#7a5236", LIGHT, 190);
  p.ell(300, 720, 120, 150, "#e9d2a8", 0);
  for (let i = 0; i < 5; i++) p.arc(250 + (i % 3) * 50, 650 + Math.floor(i / 3) * 60 + 30, 18, 12, 20, 160, 7, "#b08a5c");
  ring(p, body, 12);
  p.poly([[150, 440], [170, 330], [230, 420]], "#a07450", 10); p.poly([[450, 440], [430, 330], [370, 420]], "#a07450", 10);
  for (const x of [225, 375]) {
    p.ell(x, 520, 70, 70, "#f6efe0", 10);
    const s = Math.max(squint, blink);
    if (s > 0.5) { p.stroke([[x - 40, 505], [x, 530], [x + 40, 505]], 12); }
    else { p.ell(x, 520, 40, 40 * (1 - s), "#ffb52e", 6); p.dot(x, 520, 20 * (1 - s)); }
  }
  p.poly([[280, 570], [320, 570], [300, 615]], "#f2a32e", 8);
  if (squint > 0.5) { p.stroke([[160, 455], [255, 480]], 12); p.stroke([[440, 455], [345, 480]], 12); }
  for (const x of [250, 350]) p.stroke([[x - 20, 890], [x, 910], [x + 20, 890]], 10, "#f2a32e");
};

/** firefly on a 400 x 400 canvas. glow 0..1 (a faint tail lamp lost in daylight), look -1..1 */
export const firefly = (p: Pen, glow: number, look = 0) => {
  if (glow > 0) p.ell(150, 250, 90 * glow, 90 * glow, `rgba(255,240,120,${0.3 * glow})`, 0);
  p.ell(150, 250, 55, 45, glow > 0.5 ? "#fff38a" : "#d8d07a", 8);
  p.ell(240, 220, 85, 60, "#4a3f55", 10);
  p.ell(225, 160, 60, 30, "rgba(220,240,255,0.8)", 6, 0, 360, -25); p.ell(265, 160, 60, 30, "rgba(220,240,255,0.8)", 6, 0, 360, 25);
  p.ell(320, 215, 45, 42, "#4a3f55", 9);
  p.ell(330 + 6 * look, 205, 14, 16, "#ffffff", 4); p.dot(333 + 8 * look, 207, 7);
  p.stroke([[330, 175], [350, 120], [375, 115]], 7); p.stroke([[315, 178], [315, 118], [338, 105]], 7);
  for (const x of [210, 250, 285]) p.stroke([[x, 270], [x - 10, 310]], 7);
};

/** night flower on a stem, 600 x 1000. open 0..1, droop 0..1 */
export const flower = (p: Pen, open: number, droop: number) => {
  const hx = 300 + 120 * droop, hy = 330 + 150 * droop;
  p.line([[300, 975], [300, 700], [hx - 30 * droop, hy + 120]], "#4f9a45", 22);
  p.ell(220, 780, 80, 30, "#5fae4f", 9, 0, 360, -25); p.ell(380, 720, 80, 30, "#5fae4f", 9, 0, 360, 25);
  const n = 6;
  for (let i = 0; i < n; i++) {
    const a = rad(-90 + (i - (n - 1) / 2) * (12 + 40 * open) + 60 * droop), L = 150;
    const tip: P2 = [hx + L * Math.cos(a), hy + L * Math.sin(a)];
    p.poly([[hx, hy + 30], [hx + 40 * Math.cos(a + 1.2), hy + 40 * Math.sin(a + 1.2)], tip, [hx + 40 * Math.cos(a - 1.2), hy + 40 * Math.sin(a - 1.2)]], i % 2 ? "#f3f0ff" : "#e4dcff", 9);
  }
  p.ell(hx, hy + 40, 60, 40, "#5fae4f", 9);
};

/** thermometer sign on a 300 x 900 canvas; level 0..1 */
export const thermo = (p: Pen, level: number) => {
  p.ell(150, 760, 95, 95, "#e8443a", 12);
  p.poly([[110, 680], [110, 90], [190, 90], [190, 680]], "#fff6e0", 12);
  p.ell(150, 90, 40, 40, "#fff6e0", 12); p.poly([[112, 680], [112, 90], [188, 90], [188, 680]], "#fff6e0", 0);
  const top = 660 - 560 * level;
  p.poly([[128, 700], [128, top], [172, top], [172, 700]], "#e8443a", 0);
  for (let i = 0; i < 8; i++) p.stroke([[190, 140 + i * 70], [215, 140 + i * 70]], 8);
};

/** snowflake on a 200 x 200 canvas */
export const flake = (p: Pen) => { for (let i = 0; i < 3; i++) { const a = (i * Math.PI) / 3; p.stroke([[100 - 80 * Math.cos(a), 100 - 80 * Math.sin(a)], [100 + 80 * Math.cos(a), 100 + 80 * Math.sin(a)]], 12, "#ffffff"); } };
void INK;
