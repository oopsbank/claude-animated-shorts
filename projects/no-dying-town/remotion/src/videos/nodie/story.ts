// "The Town Where You're Not Allowed to Die" — shot timeline, cameras and lens per shot, timed to voice/words.json
// (ElevenLabs alignment, 54.98 s of voice). Every set lives in one scene at its own x offset (world.ts).
export const FPS = 30;
export const TOTAL = 1665; // 55.5 s: voice + a short tail that loops back into frame 0
export type V3 = [number, number, number];
export const clamp01 = (x: number) => Math.max(0, Math.min(1, x));
export const smooth = (x: number) => { const u = clamp01(x); return u * u * (3 - 2 * u); };
export const glide = (u: number) => { const x = clamp01(u); return x * x * x * (x * (6 * x - 15) + 10); };
const lerp3 = (a: V3, b: V3, k: number): V3 => [a[0] + (b[0] - a[0]) * k, a[1] + (b[1] - a[1]) * k, a[2] + (b[2] - a[2]) * k];

// set origins (x offsets)
export const ROAD = 0, TOWN = 200, GROUND = 400, CEM = 600, CUT = 700, FREEZER = 800, AIR = 1000;

export type SetName = "road" | "town" | "ground" | "cem" | "cut" | "freezer" | "air";
export type ShotDef = { id: number; a: number; b: number; set: SetName };
export const SHOTS: ShotDef[] = [
  { id: 1, a: 0, b: 148, set: "road" },        // hook: the NO DYING road sign
  { id: 2, a: 148, b: 326, set: "town" },      // Longyearbyen, rifles, polar bear
  { id: 3, a: 326, b: 476, set: "ground" },    // the ground never thaws (cutaway)
  { id: 4, a: 476, b: 642, set: "cem" },       // 1918 (sepia): flu germs, miners, crosses
  { id: 5, a: 642, b: 766, set: "cut" },       // coffins locked in the ice under the crosses
  { id: 6, a: 766, b: 928, set: "freezer" },   // a giant freezer; not a great neighbour
  { id: 7, a: 928, b: 1004, set: "cem" },      // 1950: CLOSED
  { id: 8, a: 1004, b: 1182, set: "cem" },     // 1998: scientists dig; 50,000,000
  { id: 9, a: 1182, b: 1350, set: "air" },     // old/sick: plane ticket
  { id: 10, a: 1350, b: 1466, set: "air" },    // pregnant women fly south
  { id: 11, a: 1466, b: 1560, set: "town" },   // births ~0, deaths ~0
  { id: 12, a: 1560, b: TOTAL, set: "road" },  // loop: the sign again = frame 0
];
export const SEPIA = new Set([4]);
export const shotAt = (f: number) => SHOTS.find((s) => f >= s.a && f < s.b) ?? SHOTS[SHOTS.length - 1];
export const layersAt = (f: number) => [{ id: shotAt(f).id, alpha: 1 }];

// ---------------- story clocks (t in seconds) ----------------
/** freezer door 0 shut .. 1 open ("like a giant freezer" 26.6 s) */
export const doorAt = (t: number) => smooth((t - 26.3) / 0.7);
/** CLOSED stamp 0..1 ("stopped burying" 32.4 s) */
export const stampAt = (t: number) => clamp01((t - 32.35) / 0.18);
/** plane: 0 parked .. 1 gone (shot 10) */
export const planeAt = (t: number) => smooth((t - 47.0) / 2.0);

// ---------------- cameras ----------------
export type Cam = { pos: V3; look: V3; fov: number; roll: number };
type Key = { f: number; dur?: number; cut?: boolean; c: Cam };
const C = (pos: V3, look: V3, fov = 40, roll = 0): Cam => ({ pos, look, fov, roll });
const mixC = (a: Cam, b: Cam, k: number): Cam => ({ pos: lerp3(a.pos, b.pos, k), look: lerp3(a.look, b.look, k), fov: a.fov + (b.fov - a.fov) * k, roll: a.roll + (b.roll - a.roll) * k });
const creep = (c: Cam, n: number, rate = 0.0025): Cam => { const k = Math.exp(-rate * Math.max(0, n)); return { ...c, pos: lerp3(c.look, c.pos, k) }; };

const ROAD_A = C([ROAD - 0.6, 1.25, 5.2], [ROAD + 1.3, 1.85, -3], 40, 0.02);
const CAMS: Record<number, Key[]> = {
  1: [{ f: 0, c: ROAD_A }],
  2: [{ f: 148, c: C([TOWN - 2, 5.5, 22], [TOWN + 1, 2.6, -4], 44, 0) },
      { f: 246, dur: 34, c: C([TOWN + 0.6, 1.5, 7.4], [TOWN + 2.6, 1.15, -1.0], 40, 0.03) }],
  3: [{ f: 326, c: C([GROUND + 0.4, 2.3, 7], [GROUND, 0.9, 0], 42, 0) },
      { f: 362, dur: 40, c: C([GROUND + 0.5, -1.4, 8.8], [GROUND + 0.2, -1.9, 0], 46, 0) }],
  4: [{ f: 476, c: C([CEM + 1.2, 1.7, 9], [CEM - 0.5, 1.1, -2], 42, -0.02) },
      { f: 560, dur: 40, c: C([CEM + 1.2, 1.6, -0.2], [CEM - 0.2, 0.7, -3.4], 42, 0.03) }],
  5: [{ f: 642, c: C([CUT + 0.6, 0.2, 9.5], [CUT, -1.3, 0], 44, 0) },
      { f: 700, dur: 50, c: C([CUT + 0.3, -1.1, 5.4], [CUT, -1.9, 0], 40, -0.02) }],
  6: [{ f: 766, c: C([FREEZER + 1.0, 2.2, 9.5], [FREEZER, 2.2, 0], 42, 0) },
      { f: 840, dur: 30, c: C([FREEZER + 1.4, 2.0, 10.4], [FREEZER + 1.3, 1.8, 0], 48, 0.03) }],
  7: [{ f: 928, c: C([CEM + 0.2, 1.6, 9.2], [CEM, 1.6, 4.5], 40, 0) }],
  8: [{ f: 1004, c: C([CEM + 4.5, 2.6, 4.4], [CEM + 1.6, 0.9, -3.0], 42, 0.02) },
      { f: 1110, dur: 36, c: C([CEM + 5.2, 3.4, 4.2], [CEM + 1.4, 1.9, -2.6], 46, 0) }],
  9: [{ f: 1182, c: C([AIR + 5.0, 1.6, 9.4], [AIR + 3.0, 1.3, 2.2], 38, 0.02) }],
  10: [{ f: 1350, c: C([AIR + 7.5, 2.0, 11], [AIR + 1.0, 1.6, 0], 44, 0) },
       { f: 1400, dur: 60, c: C([AIR + 10, 3.5, 17], [AIR - 4, 5, -2], 48, 0) }],
  11: [{ f: 1466, c: C([TOWN + 0.4, 3.0, 17], [TOWN + 0.4, 3.3, -3], 44, 0) }],
  12: [{ f: 1560, c: ROAD_A }],
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
const KICKS: [number, number][] = [[32.4, 1.3], [38.05, 0.5]];
export const kickAt = (t: number) => {
  let a = 0;
  for (const [t0, g] of KICKS) { const n = Math.floor((t - t0) * FPS + 1e-6); if (n >= 0 && n < 7) a += g * (n % 2 ? -1 : 1) * (1 - n / 7) ** 1.5; }
  return a;
};
export const camAt = (id: number, f: number): Cam => {
  // the loop shot plays shot 1's camera clock (frame TOTAL == frame 0)
  const c = id === 12 ? run(CAMS[1], f - TOTAL) : run(CAMS[id], f);
  const a = kickAt(f / FPS);
  if (!a) return c;
  const d: V3 = [c.look[0] - c.pos[0], c.look[1] - c.pos[1], c.look[2] - c.pos[2]];
  const L = Math.hypot(...d), h = Math.hypot(d[0], d[2]) || 1, m = (3 / 640) * Math.tan((c.fov * Math.PI) / 360) * L * a;
  return { ...c, look: [c.look[0] - (d[2] / h) * m, c.look[1] + 0.6 * m, c.look[2] + (d[0] / h) * m], roll: c.roll + a * 0.004 };
};

// ---------------- lens blur per shot (cInf px at 1080 wide; 0 = sharp) ----------------
export const DOF: Record<number, number> = { 1: 12, 2: 6, 3: 4, 4: 9, 5: 6, 6: 8, 7: 12, 8: 8, 9: 12, 10: 4, 11: 5, 12: 12 };
export const dofAt = (f: number) => ({ cInf: DOF[shotAt(f).id] });
