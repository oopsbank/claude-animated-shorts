// "What If You Could Hear Everyone's Thoughts?" — shot timeline, cameras and lens per shot, timed to words.json
// (ElevenLabs alignment, 63.81 s of voice). Every set lives in one scene at its own x offset (world.ts).
export const FPS = 30;
export const TOTAL = 1935; // 64.5 s: voice + a short tail
export type V3 = [number, number, number];
export const clamp01 = (x: number) => Math.max(0, Math.min(1, x));
export const smooth = (x: number) => { const u = clamp01(x); return u * u * (3 - 2 * u); };
export const glide = (u: number) => { const x = clamp01(u); return x * x * x * (x * (6 * x - 15) + 10); };
const lerp3 = (a: V3, b: V3, k: number): V3 => [a[0] + (b[0] - a[0]) * k, a[1] + (b[1] - a[1]) * k, a[2] + (b[2] - a[2]) * k];

// set origins (x offsets)
export const BED = 0, CAFE = 100, OFFICE = 200, PARK = 300, CLASS = 400, KITCHEN = 500, BUS = 600, CITY = 800, WOODS = 1100;

export type SetName = "bed" | "cafe" | "office" | "park" | "class" | "kitchen" | "bus" | "city" | "woods";
export type ShotDef = { id: number; a: number; b: number; set: SetName };
export const SHOTS: ShotDef[] = [
  { id: 1, a: 0, b: 92, set: "bed" },          // hook: wake up, thoughts pour in
  { id: 2, a: 92, b: 206, set: "cafe" },       // DAY 1: barista thinks the haircut is brave
  { id: 3, a: 206, b: 300, set: "office" },    // boss thinks about tacos, during the meeting
  { id: 4, a: 300, b: 426, set: "park" },      // dog: ball ball ball
  { id: 5, a: 426, b: 603, set: "class" },     // the test: the smart kid thinks every answer loudly
  { id: 6, a: 603, b: 720, set: "kitchen" },   // DAY 2: friend thinks the cooking is terrible
  { id: 7, a: 720, b: 819, set: "kitchen" },   // mom still thinks about the vase
  { id: 8, a: 819, b: 948, set: "bus" },       // forty strangers humming the same song
  { id: 9, a: 948, b: 1206, set: "city" },     // DAY 3: eight million thoughts at once
  { id: 10, a: 1206, b: 1296, set: "bed" },    // night: can't sleep
  { id: 11, a: 1296, b: 1449, set: "woods" },  // run into the woods
  { id: 12, a: 1449, b: 1524, set: "woods" },  // silence, peace, bliss
  { id: 13, a: 1524, b: 1611, set: "woods" },  // a tiny voice: a squirrel
  { id: 14, a: 1611, b: 1857, set: "woods" },  // every squirrel: where did I bury my nuts?
  { id: 15, a: 1857, b: TOTAL, set: "city" },  // people were the quiet ones
];
export const NIGHT = new Set([10]);
export const shotAt = (f: number) => SHOTS.find((s) => f >= s.a && f < s.b) ?? SHOTS[SHOTS.length - 1];
export const layersAt = (f: number) => [{ id: shotAt(f).id, alpha: 1 }];

/** title stickers in the frame top: [text, start s, end s] */
export const DAYS: [string, number, number][] = [["DAY 1", 3.1, 5.4], ["DAY 2", 20.15, 22.4], ["DAY 3", 31.7, 34.0]];

// ---------------- cameras ----------------
export type Cam = { pos: V3; look: V3; fov: number; roll: number };
type Key = { f: number; dur?: number; cut?: boolean; c: Cam };
const C = (pos: V3, look: V3, fov = 40, roll = 0): Cam => ({ pos, look, fov, roll });
const mixC = (a: Cam, b: Cam, k: number): Cam => ({ pos: lerp3(a.pos, b.pos, k), look: lerp3(a.look, b.look, k), fov: a.fov + (b.fov - a.fov) * k, roll: a.roll + (b.roll - a.roll) * k });
const creep = (c: Cam, n: number, rate = 0.0025): Cam => { const k = Math.exp(-rate * Math.max(0, n)); return { ...c, pos: lerp3(c.look, c.pos, k) }; };

const CAMS: Record<number, Key[]> = {
  1: [{ f: 0, c: C([BED + 0.6, 1.7, 3.6], [BED - 0.4, 1.3, -2.6], 40, 0.02) },
      { f: 50, dur: 30, c: C([BED + 0.2, 1.75, 1.8], [BED - 0.45, 1.45, -2.6], 44, 0) }],
  2: [{ f: 92, c: C([CAFE + 0.3, 1.75, 5.6], [CAFE - 0.1, 1.55, -1.6], 40, 0) },
      { f: 150, dur: 30, c: C([CAFE + 0.2, 1.8, 3.4], [CAFE + 0.2, 1.85, -2.2], 40, -0.02) }],
  3: [{ f: 206, c: C([OFFICE + 0.2, 1.8, 5.0], [OFFICE, 1.6, -2.4], 42, 0) },
      { f: 268, dur: 16, cut: false, c: C([OFFICE + 0.1, 2.0, 1.8], [OFFICE, 2.1, -3.0], 42, 0.03) }],
  4: [{ f: 300, c: C([PARK + 0.4, 1.0, 4.4], [PARK + 0.1, 1.1, -0.6], 40, 0) },
      { f: 360, dur: 20, c: C([PARK + 0.45, 0.9, 3.2], [PARK + 0.55, 1.2, -0.4], 44, 0) }],
  5: [{ f: 426, c: C([CLASS + 0.2, 1.6, 4.0], [CLASS + 0.1, 1.1, -1.6], 42, 0) },
      { f: 500, dur: 30, c: C([CLASS + 0.6, 1.9, 3.2], [CLASS + 0.3, 1.9, -2.6], 44, 0) },
      { f: 566, dur: 6, c: C([CLASS + 0.5, 2.0, 4.6], [CLASS + 0.3, 2.0, -2.6], 52, 0.02) }],
  6: [{ f: 603, c: C([KITCHEN + 0.0, 1.6, 4.6], [KITCHEN - 0.1, 1.2, -2.0], 40, 0) },
      { f: 680, dur: 24, c: C([KITCHEN - 0.5, 1.7, 2.6], [KITCHEN - 0.6, 1.6, -2.0], 40, -0.02) }],
  7: [{ f: 720, c: C([KITCHEN + 1.4, 1.6, 3.2], [KITCHEN + 0.6, 1.5, -2.0], 40, 0.02) },
      { f: 770, dur: 30, c: C([KITCHEN + 1.0, 1.65, 2.8], [KITCHEN + 0.75, 1.55, -2.0], 42, 0) }],
  8: [{ f: 819, c: C([BUS + 0.15, 1.95, 2.2], [BUS, 1.15, -6], 48, 0) },
      { f: 900, dur: 30, c: C([BUS + 0.25, 1.6, 1.8], [BUS - 0.75, 1.2, -0.6], 44, 0.02) }],
  9: [{ f: 948, c: C([CITY + 0.2, 1.7, 7.0], [CITY, 1.5, -6], 42, 0) },
      { f: 1052, dur: 60, c: C([CITY + 2, 16, 26], [CITY, 4, -16], 50, 0) },
      { f: 1140, dur: 50, c: C([CITY + 0.4, 2.0, 4.6], [CITY, 1.4, -1], 44, 0) }],
  10: [{ f: 1206, c: C([BED + 0.2, 1.5, 1.6], [BED - 0.4, 1.35, -2.6], 44, 0) }],
  11: [{ f: 1296, c: C([WOODS + 6, 1.5, 9], [WOODS + 4, 1.1, 0], 42, 0) },
       { f: 1310, dur: 120, c: C([WOODS + 0.5, 1.6, 6.5], [WOODS - 1, 1.1, -3], 42, 0) }],
  12: [{ f: 1449, c: C([WOODS + 0.4, 1.2, 4.6], [WOODS + 0.1, 1.0, -1.0], 40, 0) }],
  13: [{ f: 1524, c: C([WOODS + 0.5, 0.95, 3.0], [WOODS + 0.45, 0.95, -1.0], 40, 0) }],
  14: [{ f: 1611, c: C([WOODS + 0.5, 0.95, 3.0], [WOODS + 0.45, 0.95, -1.0], 40, 0) },
       { f: 1640, dur: 70, c: C([WOODS + 0.5, 2.6, 10], [WOODS + 0.3, 2.0, -3], 46, 0) }],
  15: [{ f: 1857, c: C([CITY + 0.4, 1.8, 3.6], [CITY + 0.0, 1.55, -1], 42, 0) }],
};
const run = (keys: Key[], f: number) => {
  let cur = keys[0].c, start = keys[0].f;
  for (let i = 1; i < keys.length; i++) {
    const k = keys[i];
    if (f < k.f) break;
    cur = k.cut ? k.c : mixC(cur, k.c, glide((f - k.f) / (k.dur ?? 24)));
    start = k.f + (k.cut ? 0 : k.dur ?? 24);
  }
  return creep(cur, f - start);
};
const KICKS: [number, number][] = [[18.96, 0.9], [35.4, 0.6], [58.4, 0.9], [60.1, 0.7]];
export const kickAt = (t: number) => {
  let a = 0;
  for (const [t0, g] of KICKS) { const n = Math.floor((t - t0) * FPS + 1e-6); if (n >= 0 && n < 7) a += g * (n % 2 ? -1 : 1) * (1 - n / 7) ** 1.5; }
  return a;
};
export const camAt = (id: number, f: number): Cam => {
  const c = run(CAMS[id], f);
  const a = kickAt(f / FPS);
  if (!a) return c;
  const d: V3 = [c.look[0] - c.pos[0], c.look[1] - c.pos[1], c.look[2] - c.pos[2]];
  const L = Math.hypot(...d), h = Math.hypot(d[0], d[2]) || 1, m = (3 / 640) * Math.tan((c.fov * Math.PI) / 360) * L * a;
  return { ...c, look: [c.look[0] - (d[2] / h) * m, c.look[1] + 0.6 * m, c.look[2] + (d[0] / h) * m], roll: c.roll + a * 0.004 };
};

// ---------------- lens blur per shot (cInf px at 1080 wide; 0 = sharp) ----------------
export const DOF: Record<number, number> = { 1: 8, 2: 8, 3: 8, 4: 10, 5: 8, 6: 8, 7: 10, 8: 6, 9: 5, 10: 8, 11: 6, 12: 10, 13: 12, 14: 6, 15: 10 };
export const dofAt = (f: number) => ({ cInf: DOF[shotAt(f).id] });
