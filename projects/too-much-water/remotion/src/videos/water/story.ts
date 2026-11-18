// "What if you drank too much water?" — shot timeline, cameras and lens per shot, timed to voice/words.json
// (ElevenLabs alignment, 54.47 s of voice). Every set lives in one scene at its own x offset (world.ts SETS).
export const FPS = 30;
export const TOTAL = 1660; // 55.33 s: voice + a short tail that loops back into frame 0
export type V3 = [number, number, number];
export const clamp01 = (x: number) => Math.max(0, Math.min(1, x));
export const smooth = (x: number) => { const u = clamp01(x); return u * u * (3 - 2 * u); };
export const glide = (u: number) => { const x = clamp01(u); return x * x * x * (x * (6 * x - 15) + 10); };
const lerp3 = (a: V3, b: V3, k: number): V3 => [a[0] + (b[0] - a[0]) * k, a[1] + (b[1] - a[1]) * k, a[2] + (b[2] - a[2]) * k];

// set origins (x offsets)
export const BAR = 0, OFFICE = 200, STREET = 400, CELLS = 600, SKULL = 800, KITCHEN = 1000, RADIO = 1200;

export type SetName = "bar" | "office" | "street" | "cells" | "skull" | "kitchen" | "radio";
export type ShotDef = { id: number; a: number; b: number; set: SetName };
/** cuts land 2-6 frames before the word that starts each beat */
export const SHOTS: ShotDef[] = [
  { id: 1, a: 0, b: 96, set: "bar" },          // hook: glass slides at the lens
  { id: 2, a: 96, b: 250, set: "office" },     // "guards one number like treasure": salt guard at the vault
  { id: 3, a: 250, b: 322, set: "office" },    // "Drink a glass": clerks stamp once
  { id: 4, a: 322, b: 426, set: "office" },    // "A liter in an hour? Fine. Top speed."
  { id: 5, a: 426, b: 496, set: "office" },    // "Two liters. Now there's a queue."
  { id: 6, a: 496, b: 576, set: "street" },    // "out the door and down the street"
  { id: 7, a: 576, b: 770, set: "cells" },     // dilutes the salt; cells drink (kick on "drink.")
  { id: 8, a: 770, b: 846, set: "cells" },     // "Luckily, most cells can just swell a little."
  { id: 9, a: 846, b: 924, set: "skull" },     // "Unluckily, your brain lives in a box made of bone."
  { id: 10, a: 924, b: 1160, set: "kitchen" }, // sponge in a glass jar
  { id: 11, a: 1160, b: 1356, set: "radio" },  // the real case, quiet
  { id: 12, a: 1356, b: 1528, set: "street" }, // the Army rule
  { id: 13, a: 1528, b: 1588, set: "office" }, // "So drink your water." thumbs up
  { id: 14, a: 1588, b: TOTAL, set: "bar" },   // loop: a new glass slides at the lens = frame 0
];
export const FLASH_AT = 92;
export const shotAt = (f: number) => SHOTS.find((s) => f >= s.a && f < s.b) ?? SHOTS[SHOTS.length - 1];
export const layersAt = (f: number) => [{ id: shotAt(f).id, alpha: 1 }];

// ---------------- story clocks ----------------
/** glass slide progress (0 at the far end, 1 at the lens); shot 14 restarts it so the last frame continues into f0 */
export const slideU = (f: number) => (f >= 1588 ? glide((f - TOTAL + 12) / 30) : glide((f + 12) / 30));
/** queue length (number of water drops waiting) by time */
export const queueN = (t: number) => (t < 10.8 ? 1 : t < 14.2 ? 3 + Math.floor((t - 10.8) * 1.2) : t < 16.5 ? 9 + Math.floor((t - 14.2) * 4) : 40);
/** clerk stamp 0 raised .. 1 struck, speed by beat */
export const stampAt = (t: number) => {
  const rate = t < 10.8 ? 1.2 : t < 14.2 ? 3.2 : 4.2;
  const ph = (t * rate) % 1;
  return ph < 0.25 ? smooth(ph / 0.25) : 1 - smooth((ph - 0.25) / 0.75);
};
/** cell swell 0..1: starts at "dilutes" (21.6 s), full on "drink." (24.75 s), relaxes a little for "swell a little" */
export const swellAt = (t: number) => (t < 21.6 ? 0 : t < 24.75 ? smooth((t - 21.6) / 3.15) : t < 26.9 ? 1 : 1 - 0.25 * smooth((t - 26.9) / 1));
/** salt guard swept away (seconds since 20.7 s "dilutes the salt") */
export const sweepAt = (t: number) => Math.max(0, t - 21.3);
/** brain squeeze 0..1 in the skull box */
export const brainAt = (t: number) => smooth((t - 28.6) / 1.4);
/** sponge growth 0..1 ("The sponge grows" 32.8 s .. "The jar doesn't" 34.0 s), then presses */
export const spongeAt = (t: number) => smooth((t - 32.6) / 1.6) + 0.12 * smooth((t - 34.7) / 3);
/** water level in the jar 0..1 */
export const pourAt = (t: number) => smooth((t - 31.2) / 2.2);

// ---------------- cameras ----------------
export type Cam = { pos: V3; look: V3; fov: number; roll: number };
type Key = { f: number; dur?: number; cut?: boolean; c: Cam };
const C = (pos: V3, look: V3, fov = 40, roll = 0): Cam => ({ pos, look, fov, roll });
const mixC = (a: Cam, b: Cam, k: number): Cam => ({ pos: lerp3(a.pos, b.pos, k), look: lerp3(a.look, b.look, k), fov: a.fov + (b.fov - a.fov) * k, roll: a.roll + (b.roll - a.roll) * k });
/** creeping push-in toward the look point (every hold moves; ~0.25 %/frame) */
const creep = (c: Cam, n: number, rate = 0.0025): Cam => { const k = Math.exp(-rate * Math.max(0, n)); return { ...c, pos: lerp3(c.look, c.pos, k) }; };

const BAR_A = C([BAR + 2.55, 1.5, 0.3], [BAR - 1.3, 1.22, -0.35], 40, 0.02);
const CAMS: Record<number, Key[]> = {
  1: [{ f: 0, c: BAR_A }],
  2: [{ f: 96, c: C([OFFICE - 8 + 2.2, 1.6, 5.4], [OFFICE - 7.6, 1.45, -1.4], 44, -0.06) },
      { f: 150, dur: 40, c: C([OFFICE - 8 + 1.0, 1.4, 2.9], [OFFICE - 7.2, 1.2, -0.9], 40, 0.03) }],
  3: [{ f: 250, c: C([OFFICE + 0.4, 1.85, 3.6], [OFFICE, 1.0, -0.3], 42) }],
  4: [{ f: 322, c: C([OFFICE + 2.8, 2.0, 4.6], [OFFICE - 0.2, 0.9, 0.2], 44, 0.04) },
      { f: 386, dur: 30, c: C([OFFICE + 2.0, 1.8, 3.4], [OFFICE - 0.1, 1.0, -0.1], 42, 0.06) }],
  5: [{ f: 426, cut: true, c: C([OFFICE + 3.5, 5.4, 6.5], [OFFICE + 0.3, 0.3, 2.2], 46, 0) },
      { f: 440, dur: 50, c: C([OFFICE + 2.5, 6.2, 8.2], [OFFICE + 0.5, 0.2, 3.0], 50, 0) }],
  6: [{ f: 496, c: C([STREET + 1.2, 1.6, 6], [STREET - 0.4, 1.2, -6], 42, 0) },
      { f: 506, dur: 50, c: C([STREET + 3, 14, 16], [STREET, 0.5, -14], 48, -0.03) }],
  7: [{ f: 576, c: C([CELLS + 0.4, 2.0, 8.2], [CELLS - 0.6, 1.4, -0.6], 46, 0) },
      { f: 650, dur: 36, c: C([CELLS + 0.2, 1.9, 6.6], [CELLS, 1.5, -0.4], 44, 0.03) }],
  8: [{ f: 770, c: C([CELLS - 0.8, 1.8, 5.6], [CELLS + 0.1, 1.4, -0.4], 44, -0.04) }],
  9: [{ f: 846, c: C([SKULL + 0.5, 1.5, 3.6], [SKULL, 1.15, 0], 38, 0.05) }],
  10: [{ f: 924, c: C([KITCHEN + 1.2, 1.55, 2.8], [KITCHEN, 1.05, 0], 36, 0.03) },
       { f: 980, dur: 40, c: C([KITCHEN + 0.7, 1.38, 1.9], [KITCHEN, 1.08, 0], 34, -0.02) }],
  11: [{ f: 1160, c: C([RADIO + 0.2, 1.5, 4.6], [RADIO, 1.15, -0.6], 40, 0) }],
  12: [{ f: 1356, c: C([STREET + 1.6, 1.25, -30], [STREET, 1.4, -40], 40, 0.04) },
       { f: 1440, dur: 30, c: C([STREET + 2.4, 1.6, -34.5], [STREET + 2.0, 1.45, -38.4], 38, -0.03) }],
  13: [{ f: 1528, c: C([OFFICE + 0.2, 1.5, 3.6], [OFFICE, 1.3, -0.6], 44, -0.04) }],
  14: [{ f: 1588, c: BAR_A }],
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
// impact kicks: offset flips sign every frame and decays over 7 f
const KICKS: [number, number][] = [[24.75, 1.4], [28.0, 0.4], [30.1, 0.8], [34.0, 0.5]];
export const kickAt = (t: number) => {
  let a = 0;
  for (const [t0, g] of KICKS) { const n = Math.floor((t - t0) * FPS + 1e-6); if (n >= 0 && n < 7) a += g * (n % 2 ? -1 : 1) * (1 - n / 7) ** 1.5; }
  return a;
};
export const camAt = (id: number, f: number): Cam => {
  // the loop shot plays the same camera clock as shot 1 (frame 1660 == frame 0)
  const c = id === 14 ? run(CAMS[1], f - TOTAL) : id === 1 ? run(CAMS[1], f) : run(CAMS[id], f);
  const a = kickAt(f / FPS);
  if (!a) return c;
  const d: V3 = [c.look[0] - c.pos[0], c.look[1] - c.pos[1], c.look[2] - c.pos[2]];
  const L = Math.hypot(...d), h = Math.hypot(d[0], d[2]) || 1, m = (3 / 640) * Math.tan((c.fov * Math.PI) / 360) * L * a;
  return { ...c, look: [c.look[0] - (d[2] / h) * m, c.look[1] + 0.6 * m, c.look[2] + (d[0] / h) * m], roll: c.roll + a * 0.004 };
};

// ---------------- lens blur per shot (cInf px at 1080 wide; 0 = sharp) ----------------
export const DOF: Record<number, number> = { 1: 14, 2: 11, 3: 12, 4: 10, 5: 0, 6: 0, 7: 10, 8: 12, 9: 13, 10: 15, 11: 8, 12: 10, 13: 12, 14: 14 };
export const dofAt = (f: number) => ({ cInf: DOF[shotAt(f).id], focus: undefined as undefined | ((f: number) => V3) });
