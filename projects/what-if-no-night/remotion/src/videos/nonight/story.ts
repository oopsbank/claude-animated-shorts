// "What If Night Never Came Again?" — shot timeline, cameras and story clocks. Scene time t = voice time + VO.
export const FPS = 30;
export const VO = 0.25;           // voice starts 0.25 s into the scene
export const TOTAL = 1875;        // 62.5 s
export type V3 = [number, number, number];
export const clamp01 = (x: number) => Math.max(0, Math.min(1, x));
export const smooth = (x: number) => { const u = clamp01(x); return u * u * (3 - 2 * u); };
export const glide = (u: number) => { const x = clamp01(u); return x * x * x * (x * (6 * x - 15) + 10); };
const lerp3 = (a: V3, b: V3, k: number): V3 => [a[0] + (b[0] - a[0]) * k, a[1] + (b[1] - a[1]) * k, a[2] + (b[2] - a[2]) * k];
const T = (v: number) => v + VO; // voice time -> scene time

export const VILLAGE = 0, LAKE = 400, HUT = 1200, SPACE = 3000;
export type SetName = "village" | "lake" | "hut" | "space";
export type Mood = "golden" | "rise" | "day" | "hot" | "night" | "space" | "sunset";
export type ShotDef = { id: number; a: number; b: number; set: SetName; mood: Mood };
export const SHOTS: ShotDef[] = [
  { id: 1, a: 0, b: 68, set: "village", mood: "golden" },     // hook: village at sunset
  { id: 2, a: 68, b: 240, set: "lake", mood: "rise" },        // the sun climbs to noon and stops
  { id: 3, a: 240, b: 355, set: "village", mood: "day" },     // day one: party
  { id: 4, a: 355, b: 440, set: "village", mood: "day" },     // kids play, one falls asleep standing
  { id: 5, a: 440, b: 561, set: "village", mood: "day" },     // body clock
  { id: 6, a: 561, b: 650, set: "village", mood: "day" },     // grumpy, clumsy, seeing things
  { id: 7, a: 650, b: 717, set: "village", mood: "day" },     // owl in the sun
  { id: 8, a: 717, b: 773, set: "village", mood: "day" },     // fireflies
  { id: 9, a: 773, b: 860, set: "village", mood: "day" },     // night flower stays shut
  { id: 10, a: 860, b: 1010, set: "lake", mood: "hot" },      // sun cooking one side
  { id: 11, a: 1010, b: 1124, set: "lake", mood: "hot" },     // lake shrinks, thermometer
  { id: 12, a: 1124, b: 1238, set: "space", mood: "space" },  // the globe turns to its night side
  { id: 13, a: 1238, b: 1343, set: "lake", mood: "night" },   // frozen lake
  { id: 14, a: 1343, b: 1490, set: "space", mood: "space" },  // ring of forever-sunset
  { id: 15, a: 1490, b: 1596, set: "village", mood: "golden" }, // crowd on the golden strip
  { id: 16, a: 1596, b: 1763, set: "village", mood: "sunset" }, // a normal sunset again
  { id: 17, a: 1763, b: TOTAL, set: "hut", mood: "night" },   // go to sleep: lantern out
];
export const shotAt = (f: number) => SHOTS.find((s) => f >= s.a && f < s.b) ?? SHOTS[SHOTS.length - 1];
export const QUIET: [number, number] = [T(58.4), 99];

// ---------------- story clocks (scene seconds) ----------------
/** sun elevation (deg) in shot 2: climbs, overshoots, freezes */
export const riseEl = (t: number) => {
  const a = T(3.05), b = T(4.85);
  if (t < a) return 4;
  if (t < b) return 4 + 48 * glide((t - a) / (b - a));
  const k = t - b; return 52 + 4 * Math.exp(-k * 5) * Math.sin(k * 22);
};
export const stopAt = T(4.79);
export const sleepAt = (t: number) => smooth((t - T(12.69)) / 0.5);
export const clockSpin = (t: number) => t * 2.2;
export const bumpAt = T(20.0);
export const owlAt = T(22.8);
export const flyAt = T(23.88);
export const droopAt = (t: number) => smooth((t - T(27.4)) / 0.6);
export const shrinkAt = (t: number) => smooth((t - T(33.9)) / 2.6);
export const thermoAt = (t: number) => smooth((t - T(34.9)) / 2.2);
export const turnAt = (t: number) => smooth((t - T(38.2)) / 2.6);
export const iceAt = (t: number) => smooth((t - T(42.6)) / 1.8);
export const ringGlow = (t: number) => smooth((t - T(45.6)) / 1.0);
export const crowdAt = (t: number) => smooth((t - T(47.4)) / 1.6);
export const setAt = (t: number) => smooth((t - T(53.5)) / 4.5);
export const lampAt = (t: number) => (t < T(60.3) ? 1 : t < T(60.75) ? 1 - 0.9 * smooth((t - T(60.3)) / 0.45) : 0.1 * (1 - smooth((t - T(60.75)) / 0.4)));

// ---------------- cameras ----------------
export type Cam = { pos: V3; look: V3; fov: number; roll: number };
type Key = { f: number; dur?: number; c: Cam };
const C = (pos: V3, look: V3, fov = 40, roll = 0): Cam => ({ pos, look, fov, roll });
const mixC = (a: Cam, b: Cam, k: number): Cam => ({ pos: lerp3(a.pos, b.pos, k), look: lerp3(a.look, b.look, k), fov: a.fov + (b.fov - a.fov) * k, roll: a.roll + (b.roll - a.roll) * k });
const creep = (c: Cam, n: number, rate: number): Cam => { const k = Math.exp(-rate * Math.max(0, n)); return { ...c, pos: lerp3(c.look, c.pos, k) }; };
const V = VILLAGE;
const CAMS: Record<number, Key[]> = {
  1: [{ f: 0, c: C([V + 0.4, 3.0, -5], [V, 1.6, 20], 44, 0.01) }],
  2: [{ f: 68, c: C([LAKE + 4, 16.5, 46], [LAKE + 1, 20, 0], 50, 0) }],
  3: [{ f: 240, c: C([V + 0.5, 2.0, 15], [V, 1.2, 4], 42, 0.02) }],
  4: [{ f: 355, c: C([V + 1.8, 1.0, 9.6], [V + 0.6, 0.75, 5.2], 38, -0.02) }],
  5: [{ f: 440, c: C([V + 0.2, 1.2, 8.4], [V, 1.25, 5], 38, 0) }],
  6: [{ f: 561, c: C([V - 0.6, 1.0, 9.2], [V, 0.75, 5.2], 38, 0.02) }],
  7: [{ f: 650, c: C([V + 15.7, 2.9, 7.4], [V + 15.5, 3.0, 3.4], 36, 0) }],
  8: [{ f: 717, c: C([V - 11, 0.9, 9.5], [V - 11.5, 0.8, 5.5], 38, 0.02) }],
  9: [{ f: 773, c: C([V + 6.15, 0.6, 8.3], [V + 6, 0.48, 6], 34, 0) }],
  10: [{ f: 860, c: C([LAKE + 3, 25, 52], [LAKE - 2, 9, -10], 48, 0.01) }],
  11: [{ f: 1010, c: C([LAKE + 6, 9, 40], [LAKE, 0, 8], 44, 0) }],
  12: [{ f: 1124, c: C([SPACE, 0, 46], [SPACE, 0, 0], 40, 0) }],
  13: [{ f: 1238, c: C([LAKE + 3, 22, 52], [LAKE - 2, 4, -10], 46, 0.01) }],
  14: [{ f: 1343, c: C([SPACE, 4, 48], [SPACE, 0, 0], 40, 0) }],
  15: [{ f: 1490, c: C([V + 0.5, 3.6, -6], [V, 1.0, 6], 42, 0.01) }],
  16: [{ f: 1596, c: C([V + 0.4, 1.5, -2], [V, 1.9, 20], 44, 0.01) }],
  17: [{ f: 1763, c: C([HUT + 0.6, 1.15, 5.4], [HUT + 0.2, 1.0, 0], 38, 0) }],
};
const RATE: Record<number, number> = { 2: 0, 12: 0, 14: 0.0006 };
const run = (keys: Key[], f: number, rate: number) => {
  let cur = keys[0].c, start = keys[0].f;
  for (let i = 1; i < keys.length; i++) {
    const k = keys[i]; if (f < k.f) break;
    cur = mixC(cur, k.c, glide((f - k.f) / (k.dur ?? 24))); start = k.f + (k.dur ?? 24);
  }
  return creep(cur, f - start, rate);
};
export const kickAt = (t: number) => {
  let a = 0;
  for (const [t0, g] of [[stopAt, 1.2], [bumpAt, 0.9]] as [number, number][]) { const n = Math.floor((t - t0) * FPS + 1e-6); if (n >= 0 && n < 7) a += g * (n % 2 ? -1 : 1) * (1 - n / 7) ** 1.5; }
  return a;
};
export const camAt = (id: number, f: number): Cam => {
  const c = run(CAMS[id], f, RATE[id] ?? 0.0014);
  if (id === 2) { // tilt up following the sun a little
    const t = f / FPS, k = clamp01((riseEl(t) - 4) / 48);
    c.look = [c.look[0], c.look[1] + 34 * k, c.look[2]];
  }
  const a = kickAt(f / FPS);
  if (!a) return c;
  const d: V3 = [c.look[0] - c.pos[0], c.look[1] - c.pos[1], c.look[2] - c.pos[2]];
  const L = Math.hypot(...d), h = Math.hypot(d[0], d[2]) || 1, m = (3 / 640) * Math.tan((c.fov * Math.PI) / 360) * L * a;
  return { ...c, look: [c.look[0] - (d[2] / h) * m, c.look[1] + 0.6 * m, c.look[2] + (d[0] / h) * m], roll: c.roll + a * 0.004 };
};
export const DOF: Record<number, number> = { 1: 0, 2: 0, 3: 7, 4: 10, 5: 12, 6: 10, 7: 12, 8: 12, 9: 14, 10: 0, 11: 4, 12: 0, 13: 0, 14: 0, 15: 6, 16: 0, 17: 12 };
export const dofAt = (f: number) => ({ cInf: DOF[shotAt(f).id] });
