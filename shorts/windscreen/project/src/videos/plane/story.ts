// Timeline of "What If Your Plane's Windscreen Blew Out?" (British Airways Flight 5390, 10 June 1990): shots timed to
// the voice words (shorts/windscreen/voice/words.json), the plane's poses, the windscreen's state and the camera grammar
// of the bridge short (continuous slow push-ins, smootherstep glides, big reframes as cuts, 7-frame impact kicks).
// Plane-local axes: nose toward -z, y up, x to starboard (the captain sits on the left, x < 0).
import { getInputProps } from "remotion";
export const FPS = 30;
export const TOTAL = 1990;
export const D0 = 0;
export type V3 = [number, number, number];

export const clamp01 = (x: number) => Math.max(0, Math.min(1, x));
export const smooth = (x: number) => { const u = clamp01(x); return u * u * (3 - 2 * u); };
export const easeOut = (u: number) => 1 - (1 - clamp01(u)) ** 4;

/** thumbnail stills only: inputProps `{ thumb: { id, f, pos, look, fov } }` replaces that shot's camera */
export type Thumb = { id?: number; pos: V3; look: V3; fov?: number; roll?: number };
let THUMB_C: Thumb | undefined | null = null;
export const thumbProps = (): Thumb | undefined => { if (THUMB_C === null) THUMB_C = (getInputProps() as { thumb?: Thumb }).thumb; return THUMB_C; };

// ---------------- word-locked story times (seconds, from words.json) ----------------
export const T_HOOK = 2.33;   // "left?" the pane pops off (the hook)
export const T_BLOW = 11.66;  // "blows" the windscreen goes
export const T_SUCK = 14.2;   // "sucked"
export const T_ROOF = 15.5;   // "roof"
export const T_STEW = 19.0;   // "A steward" bursts in
export const T_GRAB = 20.25;  // "grabs"
export const T_TIRE = 22.9;   // "give out"
export const T_TAKE = 24.15;  // "take over"
export const T_DEAD = 25.95;  // "dead"
export const T_ENGINE = 28.45; // "engine"
export const T_TD = 30.6;     // touchdown on "lands at Southampton"
export const T_ALIVE = 34.55; // "Alive."
export const T_THUMB = 37.6;  // "He went back to flying"
export const T_RED = 43.15;   // "Eighty-four"
export const T_MM = 44.6;     // "by less than a millimetre"
export const T_SHORT = 46.1;  // "Six were too short"
export const T_MATCH = 48.75; // "matched"
export const T_WRONG = 50.45; // "The old ones were wrong too"
export const T_OUT = 53.6;    // "outside"
export const T_PUSH = 55.65;  // "pushes"
export const T_THIN = 57.9;   // "Thinner bolts"
export const T_HARD = 61.6;   // "pushed harder"
export const T_FAIL = 62.55;  // "could hold"
export const T_OFF = 64.2;    // "work." lights out

// ---------------- the plane (plane-local, metres) ----------------
export const RF = 1.65;           // fuselage radius
export const NOSE = -15, TAIL = 15;
export const WS = { z0: -13.55, z1: -12.45, th0: 5, th1: 56 }; // windscreen panes: z range, |theta| from the top (deg)
export const FLOOR = -0.8;        // cockpit + cabin floor
export const CAPT: V3 = [-0.5, FLOOR + 0.42, -11.55]; // captain's seat (card origin: seat level)
export const FO: V3 = [0.5, FLOOR + 0.42, -11.55];    // first officer
export const GROUND = -2.85;      // runway / hangar floor below the fuselage axis (gear down)
/** fuselage radius and axis height along z (nose droops, tail cone sweeps up) */
export const profile = (z: number): { r: number; c: number } => {
  if (z < -10) { const u = (-10 - z) / 5; return { r: RF * Math.sqrt(Math.max(0, 1 - u ** 2.2)), c: -0.32 * u * u }; }
  if (z > 8.5) { const u = (z - 8.5) / 6.5; return { r: RF * (1 - 0.72 * u ** 1.3), c: 0.85 * u ** 1.4 }; }
  return { r: RF, c: 0 };
};
/** a point on the fuselage skin: theta in degrees from the top, toward +x */
export const skin = (thDeg: number, z: number, dr = 0): V3 => {
  const { r, c } = profile(z), a = (thDeg * Math.PI) / 180;
  return [(r + dr) * Math.sin(a), c + (r + dr) * Math.cos(a), z];
};
export const PANE_C: V3 = skin(-30, -13.0); // the captain's (left) pane centre
export const ENGINE_L: V3 = [-2.55, 0.55, 6.6]; // left engine intake

// ---------------- shots ----------------
export type Light = "day" | "golden";
export type Place = "flight" | "ground" | "hangar" | "exp" | "ward";
export type ShotDef = { id: number; a: number; b: number; light: Light; place: Place; inside?: boolean };
export const SHOTS: ShotDef[] = [
  { id: 1, a: 0, b: 96, light: "day", place: "flight" },                // hook: the pane just leaves
  { id: 2, a: 96, b: 140, light: "day", place: "ground" },              // June 1990: rolling at Birmingham
  { id: 3, a: 140, b: 228, light: "day", place: "ground" },             // climbing out, off to Spain
  { id: 4, a: 228, b: 292, light: "day", place: "flight", inside: true }, // 81 passengers, 6 crew
  { id: 5, a: 292, b: 378, light: "day", place: "flight", inside: true }, // 17,000 ft: the windscreen blows out
  { id: 6, a: 378, b: 508, light: "day", place: "flight" },             // the captain is sucked out onto the roof
  { id: 7, a: 508, b: 568, light: "day", place: "flight", inside: true }, // only his legs are still inside
  { id: 8, a: 568, b: 676, light: "day", place: "flight", inside: true }, // a steward grabs his legs
  { id: 9, a: 676, b: 750, light: "day", place: "flight", inside: true }, // two more crew take over
  { id: 10, a: 750, b: 874, light: "day", place: "flight" },            // they hold on: the body and the engine
  { id: 11, a: 874, b: 912, light: "day", place: "flight", inside: true }, // the co-pilot flies alone
  { id: 12, a: 912, b: 998, light: "day", place: "ground" },            // lands at Southampton
  { id: 13, a: 998, b: 1128, light: "day", place: "ward" },             // alive: arm, wrist, frostbite
  { id: 14, a: 1128, b: 1170, light: "day", place: "flight", inside: true }, // back to flying
  { id: 15, a: 1170, b: 1272, light: "golden", place: "hangar" },       // the day before: the manager replaces it
  { id: 16, a: 1272, b: 1338, light: "golden", place: "hangar" },       // ninety bolts, 84 too thin
  { id: 17, a: 1338, b: 1425, light: "day", place: "exp" },             // less than a millimetre; six too short
  { id: 18, a: 1425, b: 1554, light: "golden", place: "hangar" },       // he matched them to the old ones
  { id: 19, a: 1554, b: 1735, light: "day", place: "exp" },             // fitted from the outside; the cabin pushes
  { id: 20, a: 1735, b: 1890, light: "day", place: "exp" },             // thinner bolts, less grip... it goes
  { id: 21, a: 1890, b: TOTAL, light: "golden", place: "hangar" },      // nobody had checked his work
];
export const XFADE: Record<number, number> = { 13: 10, 15: 12, 17: 8, 19: 10, 21: 10 };
export const FLASH_AT = 96;

export const shotAt = (f: number) => SHOTS.find((s) => f >= s.a && f < s.b) ?? SHOTS[SHOTS.length - 1];
export const layersAt = (f: number): { id: number; alpha: number }[] => {
  for (const s of SHOTS) {
    const x = XFADE[s.id];
    if (x && f >= s.a - x / 2 && f < s.a + x / 2) return [{ id: s.id - 1, alpha: 1 }, { id: s.id, alpha: (f - (s.a - x / 2) + 1) / (x + 1) }];
  }
  return [{ id: shotAt(f).id, alpha: 1 }];
};

// ---------------- state ----------------
/** the plane's pose in the world: position, pitch (nose up +), roll; gear down? */
export type Pose = { pos: V3; pitch: number; roll: number; gear: boolean };
export const planePose = (id: number, t: number): Pose => {
  if (id === 2) { const s = t - 3.2; return { pos: [0, 0, 60 - 22 * s - 2 * s * s], pitch: 0, roll: 0, gear: true }; }
  if (id === 3) {
    const s = t - 4.67, y = 2.2 * s * s + 1.5 * s;
    return { pos: [0, y, -20 - 38 * s], pitch: Math.min(0.17, 0.06 + 0.06 * s), roll: 0, gear: s < 1.6 };
  }
  if (id === 12) {
    const s = t - T_TD;
    if (s < 0) return { pos: [0, -2.1 * s, -38 * s], pitch: 0.07, roll: 0.02 * Math.sin(t * 2), gear: true };
    const z = -38 * s + 7 * s * s;
    return { pos: [0, 0, z], pitch: 0.07 * (1 - smooth(s / 0.7)), roll: 0, gear: true };
  }
  const shot = SHOTS[id - 1];
  if (shot.place === "hangar") return { pos: [0, 0, 0], pitch: 0, roll: 0, gear: true };
  // in flight: a gentle bob and sway (and a lurch when the windscreen goes)
  const lurch = id >= 5 && id <= 11 && t > T_BLOW ? 0.03 * Math.exp(-(t - T_BLOW) / 1.2) * Math.sin((t - T_BLOW) * 14) : 0;
  return { pos: [0, 0.12 * Math.sin(t * 1.1), 0], pitch: 0.012 * Math.sin(t * 0.7) + lurch, roll: 0.02 * Math.sin(t * 0.53) + lurch * 0.6, gear: false };
};
/** seconds since the captain's pane left (-1 = still on); "gone" once off screen */
export const paneOff = (id: number, t: number): number => {
  if (id === 1) return t >= T_HOOK ? t - T_HOOK : -1;
  if (id === 5) return t >= T_BLOW ? t - T_BLOW : -1;
  if (id >= 6 && id <= 11) return 99;
  return -1;
};
/** windscreen bolt heads: 0 steel, 1 too thin (red), 2 too short (orange) */
export const boltMark = (id: number, t: number, i: number): number => {
  if (id !== 16) return 0;
  if (i % 15 === 7) return t >= T_SHORT + 0.04 * (i / 15) ? 2 : 0; // 6 of 90
  return t >= T_RED + 0.012 * i ? 1 : 0;
};

// ---------------- places ----------------
export const WARD: V3 = [300, 0, 0];
export const EXP: V3 = [-300, 0, 0];     // the bolt macro
export const CUT: V3 = [-300, 0, 80];    // the windscreen cutaway
export const MGR: V3 = [-2.05, 0.05, -13.15]; // the manager on his platform at the nose (hangar)

// ---------------- camera ----------------
export type Cam = { pos: V3; look: V3; fov: number; roll: number };
type Shot = Partial<Cam> & { pos: V3; look: V3 };
type Key = { f: number; dur?: number; cut?: boolean; s: (f: number) => Shot };
export const glide = (u: number) => { const x = clamp01(u); return x * x * x * (x * (6 * x - 15) + 10); };
const mix = (a: Cam, b: Cam, k: number): Cam => ({
  pos: a.pos.map((v, i) => v + (b.pos[i] - v) * k) as V3, look: a.look.map((v, i) => v + (b.look[i] - v) * k) as V3,
  fov: a.fov + (b.fov - a.fov) * k, roll: a.roll + (b.roll - a.roll) * k,
});
const full = (c: Shot): Cam => ({ fov: 40, roll: 0, ...c });
const run = (keys: Key[], f: number) => {
  let cur = full(keys[0].s(f));
  for (let i = 1; i < keys.length; i++) {
    const k = keys[i];
    if (f < k.f) break;
    cur = k.cut ? full(k.s(f)) : mix(cur, full(k.s(f)), glide((f - k.f) / (k.dur ?? 24)));
  }
  return cur;
};
const T = (f: number) => f / FPS;
const pushK = (f: number, f0: number, rate: number, punch = 0, n = 35) => {
  const x = Math.max(0, f - f0);
  let s = rate * x;
  if (punch > rate) for (let i = 0; i < Math.min(x, n); i++) s += (punch - rate) * Math.max(0, Math.min(1, (i + 0.5) / 8, (n - i - 0.5) / 8));
  return Math.exp(-s);
};
const dolly = (pos: V3, look: V3, k: number, rest: Partial<Cam> = {}): Shot =>
  ({ pos: [look[0] + (pos[0] - look[0]) * k, look[1] + (pos[1] - look[1]) * k, look[2] + (pos[2] - look[2]) * k], look, ...rest });
const at = (p: V3, d: V3): V3 => [p[0] + d[0], p[1] + d[1], p[2] + d[2]];
const P = (id: number, f: number) => planePose(id, T(f)).pos;

const CAMS: Record<number, Key[]> = {
  // 1 hook: front-left of the nose, both pilots behind the glass; the left pane pops off toward the lens
  1: [{ f: 0, s: (f) => dolly([-2.5, 0.95, -16.9], [-0.15, 0.85, -12.5], pushK(f, 0, 0.0025, 0.009, 30), { fov: 38 }) },
    { f: 66, dur: 10, s: (f) => dolly([-2.7, 1.25, -17.8], [-0.35, 1.0, -12.7], pushK(f, 0, 0.0025, 0.009, 30), { fov: 42, roll: -0.03 }) }],
  // 2 June 1990, Birmingham: low on the grass, the jet rolls past
  2: [{ f: 96, s: (f) => ({ pos: [-22, GROUND + 1.3, -18], look: at(P(2, f), [0, 0.8, -4]), fov: 36 }) }],
  // 3 climbing out: tracking alongside, the ground falling away
  3: [{ f: 140, s: (f) => { const p = P(3, f), s = (f - 140) / 88; return { pos: at(p, [-30 + 4 * s, -7 + 2 * s, 22 - 4 * s]), look: at(p, [0, 0.4, -5]), fov: 38 }; } }],
  // 4 the cabin: down the aisle from the front, rows of passengers
  4: [{ f: 228, s: (f) => dolly([0.15, 0.85, -8.6], [0.1, 0.2, 2], pushK(f, 228, 0.0025), { fov: 52 }) }],
  // 5 the cockpit from behind the pilots; the left pane blows out
  5: [{ f: 292, s: (f) => dolly([0.05, 0.75, -9.9], [-0.2, 0.35, -13.2], pushK(f, 292, 0.002), { fov: 62 }) }],
  // 6 outside, high on the left: the captain comes out of the window and folds over the roof
  6: [{ f: 378, s: (f) => dolly([-6.2, 3.1, -9.2], [-0.5, 1.25, -12.2], pushK(f, 378, 0.0015), { fov: 40 }) },
    { f: 452, dur: 30, s: (f) => dolly([-5.6, 3.6, -8.2], [-0.4, 1.55, -11.6], pushK(f, 378, 0.0015), { fov: 38 }) }],
  // 7 inside: only his legs at the empty window
  7: [{ f: 508, s: (f) => dolly([0.15, 0.6, -10.4], [-0.5, 0.5, -12.6], pushK(f, 508, 0.003), { fov: 56 }) }],
  // 8 a steward bursts in and grabs his legs: from behind him, the legs in the window ahead; then his face, straining
  8: [{ f: 568, s: (f) => dolly([0.3, 1.0, -9.6], [-0.4, 0.75, -12.3], pushK(f, 568, 0.003), { fov: 56 }) },
    { f: 630, cut: true, s: (f) => dolly([0.5, 1.1, -12.75], [-0.18, 1.05, -11.4], pushK(f, 630, 0.004), { fov: 44, roll: 0.02 }) }],
  // 9 his arms give out, two more crew take over (from behind)
  9: [{ f: 676, s: (f) => dolly([0.6, 1.05, -9.85], [-0.3, 0.75, -12.3], pushK(f, 676, 0.002), { fov: 62, roll: 0.02 }) }],
  // 10 the whole plane from above and behind: the body on the roof, the engines behind it
  10: [{ f: 750, s: (f) => dolly([-11, 9.5, 14], [-0.3, 0.6, -3.5], pushK(f, 750, 0.0015), { fov: 40 }) },
    { f: 800, dur: 60, s: (f) => dolly([-9.5, 7.5, 10], [-1.0, 0.8, -1.0], pushK(f, 750, 0.0015), { fov: 40 }) }],
  // 11 the co-pilot alone at the controls, the wind roaring past
  11: [{ f: 874, s: (f) => dolly([0.42, 0.75, -12.75], [0.5, 0.55, -11.4], pushK(f, 874, 0.004), { fov: 58, roll: -0.02 }) }],
  // 12 Southampton: low beside the runway as it touches down
  12: [{ f: 912, s: (f) => ({ pos: [-30, GROUND + 0.9, -12], look: at(P(12, f), [0, 0.2, 0]), fov: 34 }) }],
  // 13 the hospital: the captain in bed, alive
  13: [{ f: 998, s: (f) => dolly(at(WARD, [0.9, 1.75, 3.0]), at(WARD, [0, 1.15, -0.3]), pushK(f, 998, 0.0022), { fov: 42 }) },
    { f: 1060, dur: 30, s: (f) => dolly(at(WARD, [0.6, 1.6, 2.3]), at(WARD, [-0.05, 1.2, -0.3]), pushK(f, 998, 0.0022), { fov: 42 }) }],
  // 14 back in the left seat: thumbs up
  14: [{ f: 1128, s: (f) => dolly([-0.05, 0.62, -12.85], [-0.5, 0.35, -11.5], pushK(f, 1128, 0.003), { fov: 62 }) }],
  // 15 the night before, in the hangar: the manager on his platform at the nose
  15: [{ f: 1170, s: (f) => dolly([-8.5, 0.9, -20.5], [-1.0, 0.3, -12.6], pushK(f, 1170, 0.0018), { fov: 42 }) }],
  // 16 the pane and its ninety bolts, close
  16: [{ f: 1272, s: (f) => dolly(at(skin(-30, -13.0), [-1.1, 1.75, -1.3]), skin(-30, -13.0), pushK(f, 1272, 0.002), { fov: 46 }) }],
  // 17 the bolt macro: right one, thin one... and a short one
  17: [{ f: 1338, s: (f) => dolly(at(EXP, [0.0, 1.4, 8.0]), at(EXP, [0.0, 1.0, 0]), pushK(f, 1338, 0.002), { fov: 40 }) },
    { f: 1375, dur: 20, s: (f) => dolly(at(EXP, [1.5, 1.3, 7.6]), at(EXP, [1.5, 0.9, 0]), pushK(f, 1338, 0.002), { fov: 40 }) }],
  // 18 the manager matches new bolts to old ones
  18: [{ f: 1425, s: (f) => dolly(at(MGR, [-1.1, 1.0, -2.6]), at(MGR, [0, 1.15, 0]), pushK(f, 1425, 0.0025), { fov: 40 }) },
    { f: 1513, cut: true, s: (f) => dolly(at(MGR, [-0.7, 1.15, -1.6]), at(MGR, [0, 1.3, 0]), pushK(f, 1513, 0.004, 0.01, 25), { fov: 38 }) }],
  // 19 the cutaway: pane outside the frame, the cabin pushing out
  19: [{ f: 1554, s: (f) => dolly(at(CUT, [-0.8, 0.4, 13]), at(CUT, [-0.9, 0, 0]), pushK(f, 1554, 0.0015), { fov: 40 }) }],
  // 20 one bolt close: less grip... then they all go
  20: [{ f: 1735, s: (f) => dolly(at(CUT, [0.9, 2.6, 4.6]), at(CUT, [0.3, 2.5, 0]), pushK(f, 1735, 0.0025), { fov: 38 }) },
    { f: 1848, cut: true, s: (f) => dolly(at(CUT, [0.2, 0.4, 14]), at(CUT, [0.4, 0, 0]), pushK(f, 1848, 0.0015), { fov: 42 }) }],
  // 21 nobody checked: the hangar, wide; he walks off, the lights go out
  21: [{ f: 1890, s: (f) => dolly([-12, 1.4, -24], [-1.5, 0.2, -11], pushK(f, 1890, 0.0015), { fov: 40 }) }],
};

const KICKS: [number, number][] = [[T_HOOK, 1.0], [T_BLOW, 1.8], [T_SUCK + 0.1, 1.0], [T_GRAB, 0.6], [T_TD, 1.2], [T_WRONG + 0.3, 0.6], [T_FAIL, 1.4]];
export const kickAt = (t: number) => {
  let a = 0;
  for (const [t0, g] of KICKS) {
    const n = Math.floor((t - t0) * FPS + 1e-6);
    if (n >= 0 && n < 7) a += g * (n % 2 ? -1 : 1) * (1 - n / 7) ** 1.5;
  }
  return a;
};
/** a constant buffet while the window is open (cockpit + outside shots) */
const shakeAt = (id: number, t: number) => (id >= 5 && id <= 11 && t > T_BLOW ? 0.35 * (Math.sin(t * 37) * 0.6 + Math.sin(t * 23.3) * 0.4) : 0);
export const camAt = (id: number, f: number): Cam => {
  const th = thumbProps();
  if (th && (th.id ?? 1) === id) return { pos: th.pos, look: th.look, fov: th.fov ?? 46, roll: th.roll ?? 0 };
  const c = run(CAMS[id], f), a = kickAt(T(f)) + shakeAt(id, T(f));
  if (!a) return c;
  const d: V3 = [c.look[0] - c.pos[0], c.look[1] - c.pos[1], c.look[2] - c.pos[2]];
  const L = Math.hypot(...d), h = Math.hypot(d[0], d[2]) || 1;
  const m = (3 / 640) * Math.tan((c.fov * Math.PI) / 360) * L * a;
  return { ...c, look: [c.look[0] - (d[2] / h) * m, c.look[1] + 0.6 * m, c.look[2] + (d[0] / h) * m], roll: c.roll + a * 0.004 };
};

// ---------------- lens ----------------
export type Dof = { f: number; dur?: number; cInf: number; focus?: (f: number) => V3 };
export const DOF: Dof[] = [
  { f: 0, cInf: 6 },
  { f: 96, cInf: 0 },
  { f: 228, cInf: 8 },
  { f: 292, cInf: 6 },
  { f: 378, cInf: 4 },
  { f: 508, cInf: 8 },
  { f: 750, cInf: 0 },
  { f: 874, cInf: 9 },
  { f: 912, cInf: 0 },
  { f: 998, cInf: 9 },
  { f: 1170, cInf: 5 },
  { f: 1272, cInf: 10 },
  { f: 1338, cInf: 12 },
  { f: 1425, cInf: 10 },
  { f: 1554, cInf: 6 },
  { f: 1735, cInf: 12 },
  { f: 1848, cInf: 6 },
  { f: 1890, cInf: 3 },
];
export const dofAt = (f: number) => {
  let i = 0; while (i + 1 < DOF.length && f >= DOF[i + 1].f) i++;
  const d = DOF[i], p = DOF[Math.max(0, i - 1)];
  const k = d.dur ? Math.min(1, (f - d.f) / d.dur) : 1;
  return { cInf: p.cInf + (d.cInf - p.cInf) * k, focus: d.focus };
};
