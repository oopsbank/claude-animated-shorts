// Cartoon cast for the Lake Nyos short, drawn with the bridge Pen in the 600 x 1000 design space (soles at y = 975):
// gas bubbles with deadpan faces, a sleeping cow, a lantern card. Same plum ink, rings and face library.
import { Pen, INK, faceFront, shade, thickAngle, Expr } from "../bridge/toon";

type P2 = [number, number];
const rad = (d: number) => (d * Math.PI) / 180;
export const LIGHT = rad(-120);
const ring = (p: Pen, pts: P2[], w = 13) => p.inkRing(pts, w, thickAngle(LIGHT));
const ellP = (cx: number, cy: number, rx: number, ry: number, n = 64): P2[] =>
  Array.from({ length: n }, (_, i) => { const a = (i / n) * Math.PI * 2; return [cx + rx * Math.cos(a), cy + ry * Math.sin(a)] as P2; });

/** a gas bubble: pale round body, glossy rim, deadpan face. squash 0..1 (packed), tint 0 grey .. 1 cold blue */
export const bubble = (p: Pen, expr: Expr = "neutral", blink = 0, squash = 0, tint = 0) => {
  const rx = 230 * (1 + 0.12 * squash), ry = 230 * (1 - 0.15 * squash), cy = 975 - ry - 10;
  const base = tint ? "#d4ecf5" : "#e6eef0", pts = ellP(300, cy, rx, ry, 72);
  p.shadedFill(pts, base, shade(base, 0.8), LIGHT, rx);
  p.ell(300 - rx * 0.45, cy - ry * 0.5, 50, 30, "rgba(255,255,255,0.85)", 0, 0, 360, -35);
  p.ell(300 + rx * 0.55, cy + ry * 0.35, 18, 12, "rgba(255,255,255,0.6)", 0, 0, 360, -35);
  ring(p, pts, 12);
  faceFront(p, 300, cy + 20, 200, expr, 0, 0, blink, false, base);
};

/** a cow lying down, side view, eyes closed */
export const cowLying = (p: Pen, v = 0) => {
  const body = ellP(300, 860, 230, 95, 72);
  p.shadedFill(body, "#f6f1e8", "#d6cfc2", LIGHT, 230);
  p.clip(body, () => {
    p.ell(220 + 60 * v, 830, 70, 50, "#2c2530", 0);
    p.ell(380 - 30 * v, 900, 60, 40, "#2c2530", 0);
  });
  ring(p, body, 12);
  for (const x of [170, 260, 360]) { p.stroke([[x, 945], [x + 70, 965]], 26, INK); p.stroke([[x, 945], [x + 70, 965]], 13, "#f6f1e8"); }
  // head resting low on the left
  const head = ellP(95, 860, 75, 58, 48);
  p.shadedFill(head, "#f6f1e8", "#d6cfc2", LIGHT, 75);
  ring(p, head, 11);
  p.ell(55, 885, 38, 26, "#f2b3b0", 9);
  p.dot(45, 882, 5, INK); p.dot(66, 886, 5, INK);
  p.stroke([[95, 842], [125, 846]], 8, INK); // closed eye
  p.poly([[140, 815], [175, 790], [160, 830]], "#f6f1e8", 9); // ear
  p.poly([[100, 805], [92, 772], [112, 800]], "#d9c9a8", 7);  // horn
  p.stroke([[525, 850], [565, 905], [560, 930]], 8, INK);      // tail
};

/** a hanging lantern (glass + frame); glow 0..1 */
export const lantern = (p: Pen, glow: number) => {
  const g = Math.max(0, Math.min(1, glow));
  if (g > 0) { p.ell(300, 640, 230, 230, `rgba(255,190,90,${0.18 * g})`, 0); p.ell(300, 640, 150, 150, `rgba(255,210,120,${0.25 * g})`, 0); }
  p.stroke([[300, 330], [300, 450]], 10, INK);
  p.poly([[230, 470], [370, 470], [340, 450], [260, 450]], "#3a3340", 10);
  const glass: P2[] = [[220, 480], [380, 480], [395, 800], [205, 800]];
  p.poly(glass, g > 0 ? `rgb(${Math.round(120 + 135 * g)},${Math.round(100 + 110 * g)},${Math.round(80 + 40 * g)})` : "#5a5a66", 12);
  if (g > 0.05) { p.ell(300, 690, 26 * g + 6, 60 * g + 10, "#fff4c8", 0); p.ell(300, 705, 14, 30 * g + 6, "#ffb347", 0); }
  for (const x of [220, 300, 380]) p.stroke([[x, 480], [x + (x - 300) * 0.08, 800]], 10, INK);
  p.poly([[195, 800], [405, 800], [405, 840], [195, 840]], "#3a3340", 10);
};
