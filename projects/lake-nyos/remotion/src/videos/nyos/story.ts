// "The Lake That Killed 1,700 People in One Night" — shot timeline, cameras and lens per shot, timed to
// voice/words.json (ElevenLabs alignment, 51.5 s of voice). Every set lives in one scene at its own x offset.
export const FPS = 30;
export const TOTAL = 1560; // 52.0 s: the last line ("...one night in 1986") runs straight into frame 0
export type V3 = [number, number, number];
export const clamp01 = (x: number) => Math.max(0, Math.min(1, x));
export const smooth = (x: number) => { const u = clamp01(x); return u * u * (3 - 2 * u); };
export const glide = (u: number) => { const x = clamp01(u); return x * x * x * (x * (6 * x - 15) + 10); };
const lerp3 = (a: V3, b: V3, k: number): V3 => [a[0] + (b[0] - a[0]) * k, a[1] + (b[1] - a[1]) * k, a[2] + (b[2] - a[2]) * k];

// set origins (x offsets)
export const LAKE = 0, VILLAGE = 400, SECTION = 800, SODA = 1000, HUT = 1200;
export type SetName = "lake" | "village" | "section" | "soda" | "hut";
export type Mood = "night" | "dawn" | "day";
export type ShotDef = { id: number; a: number; b: number; set: SetName; mood: Mood };
export const SHOTS: ShotDef[] = [
  { id: 1, a: 0, b: 118, set: "lake", mood: "night" },       // hook: moonlit lake, push-in
  { id: 2, a: 118, b: 222, set: "lake", mood: "night" },     // "didn't flood / boil / breathed out": surface, one bubble
  { id: 3, a: 222, b: 330, set: "village", mood: "dawn" },   // "the villages were silent. No fire. No damage."
  { id: 4, a: 330, b: 428, set: "village", mood: "dawn" },   // cows lying in the field
  { id: 5, a: 428, b: 552, set: "section", mood: "day" },    // "Here's the crazy part": cutaway, gas seeping in
  { id: 6, a: 552, b: 682, set: "soda", mood: "day" },       // shaken soda, cold water = cap
  { id: 7, a: 682, b: 776, set: "lake", mood: "night" },     // "That night... maybe a landslide"
  { id: 8, a: 776, b: 822, set: "soda", mood: "day" },       // "popped the cap"
  { id: 9, a: 822, b: 940, set: "lake", mood: "night" },     // "fizzed. A cloud shot up"
  { id: 10, a: 940, b: 1012, set: "village", mood: "night" },// "rolled downhill, into the villages"
  { id: 11, a: 1012, b: 1172, set: "hut", mood: "night" },   // quiet: doorway, lantern goes out
  { id: 12, a: 1172, b: 1336, set: "lake", mood: "day" },    // the lake turned red
  { id: 13, a: 1336, b: 1484, set: "lake", mood: "day" },    // degassing pipe, the lake burps
  { id: 14, a: 1484, b: TOTAL, set: "lake", mood: "night" }, // loop: = frame 0
];
export const shotAt = (f: number) => SHOTS.find((s) => f >= s.a && f < s.b) ?? SHOTS[SHOTS.length - 1];
export const layersAt = (f: number) => [{ id: shotAt(f).id, alpha: 1 }];
/** music-free window (seconds) for the audio mix and the calm caption style */
export const QUIET: [number, number] = [33.75, 39.1];

// ---------------- story clocks (t in seconds) ----------------
/** the single bubble that rises and pops on "breathed out" */
export const bubbleAt = (t: number) => clamp01((t - 5.2) / 1.2);
/** rocks sliding into the lake */
export const slideAt = (t: number) => clamp01((t - 23.9) / 1.6);
/** soda: shake wobble (shot 6) and cap pop (shot 8) */
export const shakeAt = (t: number) => (t > 19.7 && t < 20.6 ? Math.sin((t - 19.7) * 40) * (1 - (t - 19.7) / 0.9) : 0);
export const popAt = (t: number) => clamp01((t - 26.05) / 0.9);
/** eruption column 0..1 and the cloud spread 0..1 */
export const fizzAt = (t: number) => smooth((t - 27.35) / 1.4);
export const spreadAt = (t: number) => smooth((t - 29.0) / 2.6);
/** village cloud front (0 = top of the hill, 1 = over the huts) */
export const rollAt = (t: number) => smooth((t - 31.0) / 2.6);
/** lantern brightness in the quiet shot */
export const lampAt = (t: number) => (t < 35.9 ? 1 : t < 36.5 ? 1 - 0.85 * smooth((t - 35.9) / 0.6) + 0.12 * Math.sin(t * 60) * (1 - smooth((t - 35.9) / 0.6)) : t < 37.0 ? 0.15 * (1 - smooth((t - 36.5) / 0.5)) : 0);
/** degassing bubbles leaving the pipe (shot 13): index i leaves at this time */
export const burpAt = (i: number) => 45.3 + i * 0.55;

// ---------------- cameras ----------------
export type Cam = { pos: V3; look: V3; fov: number; roll: number };
type Key = { f: number; dur?: number; cut?: boolean; c: Cam };
const C = (pos: V3, look: V3, fov = 40, roll = 0): Cam => ({ pos, look, fov, roll });
const mixC = (a: Cam, b: Cam, k: number): Cam => ({ pos: lerp3(a.pos, b.pos, k), look: lerp3(a.look, b.look, k), fov: a.fov + (b.fov - a.fov) * k, roll: a.roll + (b.roll - a.roll) * k });
const creep = (c: Cam, n: number, rate = 0.0025): Cam => { const k = Math.exp(-rate * Math.max(0, n)); return { ...c, pos: lerp3(c.look, c.pos, k) }; };

/** frame-0 framing: from the crater rim down over the moonlit lake */
const LAKE_A = C([LAKE + 3, 25, 52], [LAKE - 2, 6, -10], 46, 0.01);
const CAMS: Record<number, Key[]> = {
  1: [{ f: 0, c: LAKE_A }],
  2: [{ f: 118, c: C([LAKE + 2.2, 0.9, 6.2], [LAKE + 1, 0.35, 2], 40, -0.02) }],
  3: [{ f: 222, c: C([VILLAGE + 1.5, 1.6, 12], [VILLAGE - 0.5, 1.4, 0], 42, 0.02) }],
  4: [{ f: 330, c: C([VILLAGE + 13.5, 1.7, 14], [VILLAGE + 14, 0.5, 5.5], 40, -0.02) }],
  5: [{ f: 428, c: C([SECTION, 3.5, 22], [SECTION, 2.5, 0], 44, 0) },
      { f: 470, dur: 50, c: C([SECTION, -2.6, 11], [SECTION, -3.2, 0], 42, 0) }],
  6: [{ f: 552, c: C([SODA + 0.3, 1.45, 3.4], [SODA, 1.3, 0], 38, 0.02) },
      { f: 620, dur: 36, c: C([SODA + 0.2, 1.75, 2.6], [SODA, 1.7, 0], 36, -0.02) }],
  7: [{ f: 682, c: C([LAKE - 14, 6, 30], [LAKE - 20, 4, -2], 42, 0.02) }],
  8: [{ f: 776, c: C([SODA + 0.2, 1.7, 3.1], [SODA, 1.9, 0], 40, 0) }],
  9: [{ f: 822, c: C([LAKE + 5, 27, 62], [LAKE, 7, 0], 46, 0) },
      { f: 880, dur: 50, c: C([LAKE + 8, 34, 80], [LAKE, 6, 0], 52, -0.02) }],
  10: [{ f: 940, c: C([VILLAGE + 2, 2.2, 14], [VILLAGE - 2, 3.0, -6], 44, 0.02) }],
  11: [{ f: 1012, c: C([HUT + 0.6, 1.15, 5.4], [HUT + 0.2, 1.0, 0], 38, 0) }],
  12: [{ f: 1172, c: LAKE_A }],
  13: [{ f: 1336, c: C([LAKE + 4, 3.2, 14], [LAKE + 1, 3.6, 4], 42, 0.02) }],
  14: [{ f: 1484, c: LAKE_A }],
};
const run = (keys: Key[], f: number) => {
  let cur = keys[0].c, start = keys[0].f;
  for (let i = 1; i < keys.length; i++) {
    const k = keys[i];
    if (f < k.f) break;
    cur = k.cut ? k.c : mixC(cur, k.c, glide((f - k.f) / (k.dur ?? 24)));
    start = k.f + (k.cut ? 0 : k.dur ?? 24);
  }
  return creep(cur, f - start, 0.0012);
};
const KICKS: [number, number][] = [[26.05, 1.4], [27.5, 0.8], [28.3, 0.6]];
export const kickAt = (t: number) => {
  let a = 0;
  for (const [t0, g] of KICKS) { const n = Math.floor((t - t0) * FPS + 1e-6); if (n >= 0 && n < 7) a += g * (n % 2 ? -1 : 1) * (1 - n / 7) ** 1.5; }
  return a;
};
export const camAt = (id: number, f: number): Cam => {
  // shots 1 and 14 share one camera clock (frame 1560 == frame 0); shot 12 replays the frame-0 framing
  const c = id === 14 ? run(CAMS[1], f - TOTAL) : id === 12 ? run(CAMS[1], f - 1172 + 40) : run(CAMS[id], f);
  const a = kickAt(f / FPS);
  if (!a) return c;
  const d: V3 = [c.look[0] - c.pos[0], c.look[1] - c.pos[1], c.look[2] - c.pos[2]];
  const L = Math.hypot(...d), h = Math.hypot(d[0], d[2]) || 1, m = (3 / 640) * Math.tan((c.fov * Math.PI) / 360) * L * a;
  return { ...c, look: [c.look[0] - (d[2] / h) * m, c.look[1] + 0.6 * m, c.look[2] + (d[0] / h) * m], roll: c.roll + a * 0.004 };
};

export const DOF: Record<number, number> = { 1: 0, 2: 10, 3: 9, 4: 10, 5: 0, 6: 13, 7: 0, 8: 12, 9: 0, 10: 6, 11: 12, 12: 0, 13: 6, 14: 0 };
export const dofAt = (f: number) => ({ cInf: DOF[shotAt(f).id] });
