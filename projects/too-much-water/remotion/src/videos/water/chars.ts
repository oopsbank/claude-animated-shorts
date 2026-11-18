// Our own cartoon cast for the water short, drawn with the bridge Pen in the same 600 x 1000 design space (soles at
// y = 975): water drops, the salt-shaker guard, body cells, the brain, a canteen. Same plum ink, thick-thin rings,
// painted crescents and face library as the bridge characters.
import { Pen, INK, faceFront, shade, mix, thickAngle, Expr } from "../bridge/toon";

type P2 = [number, number];
const rad = (d: number) => (d * Math.PI) / 180;
export const LIGHT = rad(-120); // key light from the upper left, like the bridge default

const ring = (p: Pen, pts: P2[], w = 13) => p.inkRing(pts, w, thickAngle(LIGHT));
const ellP = (cx: number, cy: number, rx: number, ry: number, n = 64): P2[] =>
  Array.from({ length: n }, (_, i) => { const a = (i / n) * Math.PI * 2; return [cx + rx * Math.cos(a), cy + ry * Math.sin(a)] as P2; });
const legs = (p: Pen, cx: number, hipY: number, phase: number, col: string, spread = 34) => {
  const s = Math.sin(phase * Math.PI * 2);
  for (const k of [-1, 1]) {
    const fx = cx + k * spread + k * s * 22, top: P2 = [cx + k * spread * 0.7, hipY];
    p.stroke([top, [fx, 958]], 22, INK); p.stroke([top, [fx, 958]], 11, col);
    p.ell(fx + k * 8, 962, 24, 14, INK, 0);
  }
};

/** a water drop: teardrop body, stick legs, deadpan face. phase = walk cycle (0..1), hop = 0..1 bounce */
export const drop = (p: Pen, expr: Expr = "neutral", phase = 0, blink = 0, tint = 0) => {
  const base = mix("#7fd0f6", "#5aa8f0", tint), dark = shade(base, 0.7), bob = 8 * Math.abs(Math.cos(phase * Math.PI * 2));
  const cy = 780 - bob, r = 150;
  legs(p, 300, cy + 120, phase, "#3f86c6");
  const pts: P2[] = [];
  for (let i = 0; i < 72; i++) {
    const a = (i / 72) * Math.PI * 2 - Math.PI / 2; // start at the top
    const top = Math.max(0, -Math.sin(a)); // 1 at the top
    const rr = r * (1 - 0.1 * top);
    pts.push([300 + rr * Math.cos(a) * (1 - 0.55 * top ** 2.2), cy + rr * Math.sin(a) - 170 * top ** 3.2]);
  }
  p.shadedFill(pts, base, dark, LIGHT, r);
  p.ell(240, cy - 70, 26, 48, "rgba(255,255,255,0.55)", 0, 0, 360, -25); // glossy highlight
  ring(p, pts);
  faceFront(p, 300, cy + 10, 200, expr, 0, 0, blink, false, base);
};

/** the salt-shaker guard: glass body full of salt, steel cap with holes, a spear; sweep = rotation in radians */
export const saltGuard = (p: Pen, expr: Expr = "stern", blink = 0, salute = 0) => {
  const x0 = 205, x1 = 395, y0 = 470, y1 = 935;
  const body: P2[] = [];
  const rr = 46;
  for (const [cx, cy, a] of [[x1 - rr, y0 + rr, -90], [x1 - rr, y1 - rr, 0], [x0 + rr, y1 - rr, 90], [x0 + rr, y0 + rr, 180]] as const)
    for (let i = 0; i <= 8; i++) body.push([cx + rr * Math.cos(rad(a + (90 * i) / 8)), cy + rr * Math.sin(rad(a + (90 * i) / 8))]);
  legs(p, 300, 925, 0, "#555a66", 40);
  p.shadedFill(body, "#f4f6f8", "#c9d2e0", LIGHT, 240);
  // salt grains
  for (let i = 0; i < 70; i++) { const x = x0 + 22 + ((i * 53) % 150), y = 640 + ((i * 97) % 270); p.dot(x, y, 4.5, "#dfe3ea"); }
  ring(p, body);
  p.poly([[196, 470], [196, 438], ...ellP(300, 438, 104, 76).filter(([, y]) => y <= 438).sort((a, b) => a[0] - b[0]), [404, 438], [404, 470]], "#aeb6c4", 12);
  for (const [hx, hy] of [[270, 395], [300, 385], [330, 395], [285, 415], [315, 415]]) p.dot(hx, hy, 7, INK);
  faceFront(p, 300, 600, 180, expr, 0, 0, blink, false, "#f4f6f8");
  // arm + spear
  const hand: P2 = [430, 700 - 140 * salute];
  p.stroke([[395, 700], hand], 18, INK); p.stroke([[395, 700], hand], 9, "#555a66");
  p.band([[452, 965], [452, 300]], "#8a5a3c", 12, 4);
  p.poly([[452, 250], [474, 312], [430, 312]], "#c8ced8", 8);
  p.dot(hand[0] + 10, hand[1], 14, INK);
};

/** a body cell: membrane, nucleus, face. swell 0 = relaxed oval, 1 = round and taut */
export const cell = (p: Pen, swell = 0, expr: Expr = "neutral", blink = 0, hue = 0) => {
  const rx = 215 + 55 * swell, ry = 165 + 105 * swell, cy = 975 - ry - 12;
  const base = mix(["#ffb9a3", "#ffc6a0", "#f7a9b8"][hue % 3], "#ffd8cc", 0.25 * swell), dark = shade(base, 0.78);
  const pts = ellP(300, cy, rx, ry, 72);
  p.shadedFill(pts, base, dark, LIGHT, Math.max(rx, ry));
  p.ell(300 + rx * 0.5, cy - ry * 0.45, 52, 42, "#b38ad6", 9);
  p.dot(300 + rx * 0.5 - 8, cy - ry * 0.47, 12, "#8e62b8");
  if (swell > 0.5) p.ell(300 - rx * 0.55, cy - ry * 0.55, 34, 18, "rgba(255,255,255,0.6)", 0, 0, 360, -35);
  ring(p, pts, 13 - 3 * swell);
  faceFront(p, 300 - 40, cy - ry * 0.15, 190, expr, 0, 0, blink, false, base);
};

/** the brain: pink, folded, with a face; squeeze widens it and flattens the top */
export const brain = (p: Pen, squeeze = 0, expr: Expr = "nervous", blink = 0) => {
  const rx = 250 + 30 * squeeze, ry = 175 - 25 * squeeze, cy = 975 - ry - 20;
  const pts: P2[] = [];
  for (let i = 0; i < 90; i++) {
    const a = (i / 90) * Math.PI * 2, bump = 1 + 0.05 * Math.sin(a * 9) * (1 - 0.6 * squeeze);
    pts.push([300 + rx * Math.cos(a) * bump, cy + ry * Math.sin(a) * bump * (Math.sin(a) < 0 ? 1 - 0.25 * squeeze : 1)]);
  }
  p.shadedFill(pts, "#f6a8c0", "#d77c9c", LIGHT, rx);
  p.clip(pts, () => {
    for (let k = 0; k < 9; k++) {
      const sx = 90 + k * 55, s: P2[] = [];
      for (let j = 0; j <= 14; j++) s.push([sx + 22 * Math.sin(j * 1.1 + k), cy - ry + j * (2 * ry) / 14]);
      p.stroke(s, 7, "#c46a8c");
    }
    p.stroke([[300, cy - ry], [300, cy + ry * 0.2]], 8, "#b05a7c");
  });
  ring(p, pts);
  faceFront(p, 300, cy + 35, 220, expr, 0, 0, blink, false, "#f6a8c0");
};

/** canteen with a fill line at 60 % */
export const canteen = (p: Pen, mark = 1) => {
  const pts = ellP(300, 560, 210, 260);
  p.shadedFill(pts, "#6f8355", "#4b5c3a", LIGHT, 260);
  p.band([[110, 560 - 260 * 0.2], [490, 560 - 260 * 0.2]], "#f3efe2", 16 * mark, 5);
  ring(p, pts, 16);
  p.poly([[255, 300], [345, 300], [345, 250], [255, 250]], "#8a6a4a", 12);
};

/** a thumbs-up hand (effect card) */
export const thumb = (p: Pen) => {
  p.poly([[180, 620], [420, 620], [430, 860], [190, 860]], "#c4554d", 14);
  p.poly([[250, 620], [250, 420], [300, 380], [330, 420], [330, 620]], "#c4554d", 14);
  for (const y of [680, 740, 800]) p.stroke([[200, y], [400, y]], 8, INK);
};
