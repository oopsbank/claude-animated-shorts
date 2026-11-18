// Timeline of "The Street That Drowned in Beer": shots timed to the voice words (shorts/beer-flood/voice/words.json),
// story physics (vat bursts, the brick wall, the beer flood as a height field) and the camera grammar of the bridge
// short: continuous slow push-ins, symmetric smootherstep glides, big reframes as cuts, 7-frame impact kicks.
export const FPS = 30;
export const TOTAL = 1948;
export const D0 = 0; // ground level (build.ts houses stand on D0)
export type V3 = [number, number, number];

export const clamp01 = (x: number) => Math.max(0, Math.min(1, x));
export const smooth = (x: number) => { const u = clamp01(x); return u * u * (3 - 2 * u); };
export const easeOut = (u: number) => 1 - (1 - clamp01(u)) ** 4;

// ---------------- word-locked story times (seconds, from words.json) ----------------
export const T_SLIP = 17.6;   // "iron." the slipped hoop clunks a little lower
export const T_NOTICE = 14.75; // "noticed"
export const T_WRITE = 18.3;  // "wrote"
export const T_FINE = 19.95;  // "fine."
export const TB = [21.7, 22.74, 24.8]; // "burst." / "smashed" / "next": vat 0, 1, 2 burst
export const T_WALL = 26.06;  // "came down": the breach starts to fall
export const TW = 26.3;       // beer leaves the yard through the breach
export const T_POP = 46.74;   // "pop."
export const T_GAVEL = 48.68; // "God,"
export const T_BLAME = 49.62; // "blame."
export const T_HAND = 51.98;  // "refunded"
export const T_SEVEN = 55.98; // "seven thousand pounds"
export const T_FALL = 61.38;  // "falls"
export const T_RUN = 62.3;    // "it is not fine."

// ---------------- the yard ----------------
export type Vat = { x: number; z: number; r: number; h: number; hoops: number[]; burst?: number };
export const VATS: Vat[] = [
  { x: 0, z: -12, r: 3.3, h: 6.7, hoops: [0.55, 1.75, 2.95, 4.15, 5.35, 6.35], burst: 0 }, // the 22 ft vat
  { x: -9.6, z: -15.5, r: 2.7, h: 5.6, hoops: [0.5, 1.55, 2.6, 3.65, 4.7, 5.35], burst: 1 },
  { x: 9.6, z: -16.5, r: 2.7, h: 5.6, hoops: [0.5, 1.55, 2.6, 3.65, 4.7, 5.35], burst: 2 },
  { x: -17, z: -25.5, r: 2.5, h: 5.2, hoops: [0.5, 1.5, 2.5, 3.5, 4.4, 4.95] },
  { x: 17, z: -26, r: 2.5, h: 5.2, hoops: [0.5, 1.5, 2.5, 3.5, 4.4, 4.95] },
  { x: -1, z: -28, r: 2.4, h: 5.0, hoops: [0.5, 1.5, 2.5, 3.5, 4.3, 4.75] },
];
export const SLIP_HOOP = 1; // index of the hoop that slipped on the big vat
export const YARD = { x0: -24, x1: 24, z0: -34, z1: 0 };
export const WALL_H = 7.6, WALL_T = 0.6;
export const BREACH = { x0: -5, x1: 5 }; // wall section that falls into the street
export const STREET = { x0: -4.4, x1: 4.4, z0: WALL_T, z1: 78 };
export const OFFICE = { x: -10, z: -9.5 }; // George's office: a one-storey cottage beside the vats (scale: "taller than a house")
export const EXP: V3 = [220, 0, 0];     // the cutaway vat of the explanation
export const ROOM: V3 = [-220, 0, 0];   // panelled room: dinner (16-17) and court (18-20)

// ---------------- flood physics (tau = story seconds) ----------------
/** height of the beer surface above the ground at (x, z), 0 = dry. Everything visible about the flood comes from here. */
export const beerDepth = (x: number, z: number, tau: number): number => {
  if (tau < TB[0]) return 0;
  let d = 0;
  const inYard = z < 0.2 && x > YARD.x0 && x < YARD.x1 && z > YARD.z0;
  const inStreet = z >= 0 && x > STREET.x0 - 0.05 && x < STREET.x1 + 0.05;
  const inBreach = z >= -0.2 && z <= WALL_T + 0.2 && x > BREACH.x0 && x < BREACH.x1;
  if (inYard || (inBreach && tau > T_WALL)) {
    // yard pond: rises with every burst, drains through the breach after TW
    const fill = 0.55 * smooth((tau - TB[0]) / 1.6) + 0.35 * smooth((tau - TB[1]) / 1.4) + 0.3 * smooth((tau - TB[2]) / 1.4);
    const drain = 1 - 0.45 * smooth((tau - TW) / 5);
    d = fill * drain;
    // per vat: the collapsing column and the ring wave rolling outward
    for (const v of VATS) {
      if (v.burst === undefined) continue;
      const tb = TB[v.burst], s = tau - tb;
      if (s < 0) continue;
      const r = Math.hypot(x - v.x, z - v.z);
      const col = (v.h * 0.85) * Math.exp(-s / 0.32) * Math.exp(-((r / (v.r + 4 * s)) ** 2));
      const R = v.r + 8.5 * s ** 0.75, crest = 1.7 * Math.exp(-s / 1.4) + 0.15;
      const ring = crest * Math.exp(-(((r - R) / (1.1 + 0.4 * s)) ** 2)) * (r < R + 3 ? 1 : 0);
      const inside = r < R ? 0.25 * Math.exp(-s / 2) : 0;
      d = Math.max(d, col, d + ring + inside);
    }
  }
  if (inStreet && tau > TW) {
    const s = tau - TW, zf = WALL_T + 6.6 * s ** 0.95;
    const base = 1.15 - 0.3 * smooth(s / 8);
    const crest = 1.25 * Math.exp(-s / 6) + 0.25;
    const w = 0.12 * Math.sin(z * 1.3 - tau * 5 + x * 0.7) + 0.06 * Math.sin(x * 2.1 + tau * 3);
    let sd = 0;
    if (z < zf) sd = base + crest * Math.exp(-(((z - zf) / 2.2) ** 2)) + w * smooth((zf - z) / 2);
    else sd = (base + crest) * Math.exp(-(((z - zf) / 0.7) ** 2));
    d = Math.max(d, sd);
  }
  return d;
};
/** foam: 1 on the steep crest of a running wave, a little everywhere it moves fast */
export const beerFoam = (x: number, z: number, tau: number): number => {
  if (tau < TB[0]) return 0;
  let f = 0;
  if (z >= 0 && tau > TW) {
    const s = tau - TW, zf = WALL_T + 6.6 * s ** 0.95;
    const band = Math.exp(-(((z - zf + 0.9) / 0.45) ** 2)) * (0.7 + 0.3 * Math.exp(-s / 6));
    const fleck = z < zf - 1 ? 0.35 * Math.max(0, Math.sin(x * 3.1 + z * 1.7 - tau * 2) * Math.sin(x * 1.3 - z * 2.3)) * Math.exp(-(zf - z) / 6) : 0;
    f = Math.max(f, band, fleck);
  }
  for (const v of VATS) {
    if (v.burst === undefined) continue;
    const s = tau - TB[v.burst];
    if (s < 0) continue;
    const r = Math.hypot(x - v.x, z - v.z), R = v.r + 8.5 * s ** 0.75;
    f = Math.max(f, Math.exp(-(((r - R + 0.5) / 0.45) ** 2)) * Math.exp(-s / 3));
  }
  return clamp01(f);
};

// ---------------- vats and wall per shot ----------------
export type VatState = { burst: number; bulge: number; slip: number; drop: number }; // burst: seconds since it burst (-1 = whole)
export const vatState = (id: number, i: number, tau: number): VatState => {
  const v = VATS[i];
  const late = id >= 21; // "today": a new vat, every hoop where it belongs, until the last one falls
  if (late) return { burst: -1, bulge: 0, slip: i === 0 ? 0 : 0, drop: i === 0 ? clamp01((tau - T_FALL) / 0.32) : 0 };
  const b = v.burst === undefined ? -1 : tau >= TB[v.burst] ? tau - TB[v.burst] : -1;
  const bulge = v.burst === 0 ? smooth((tau - 20.85) / 0.85) : v.burst !== undefined ? smooth((tau - TB[v.burst] + 0.25) / 0.25) : 0;
  return { burst: b, bulge: b >= 0 ? 0 : bulge, slip: i === 0 ? (tau < T_SLIP ? 0.75 : 1) : 0, drop: 0 };
};
/** 0 standing .. 1 down: the breach falls outward into the street */
export const wallFall = (tau: number) => (tau < T_WALL ? 0 : tau - T_WALL);

// ---------------- shots ----------------
export type Light = "day" | "golden";
export type ShotDef = { id: number; a: number; b: number; light: Light; tau: (t: number) => number; place: "yard" | "street" | "exp" | "room" };
const now = (t: number) => t;
export const SHOTS: ShotDef[] = [
  { id: 1, a: 0, b: 132, light: "day", tau: (t) => t + TW + 0.85, place: "street" }, // hook: flash-forward of the wave
  { id: 2, a: 132, b: 211, light: "day", tau: now, place: "yard" },     // the brewery
  { id: 3, a: 211, b: 268, light: "day", tau: now, place: "yard" },     // vats taller than a house
  { id: 4, a: 268, b: 386, light: "day", tau: now, place: "yard" },     // 22 ft, iron hoops
  { id: 5, a: 386, b: 503, light: "day", tau: now, place: "yard" },     // George notices
  { id: 6, a: 503, b: 547, light: "day", tau: now, place: "yard" },     // 700 lb of iron
  { id: 7, a: 547, b: 581, light: "day", tau: now, place: "yard" },     // he wrote a note
  { id: 8, a: 581, b: 625, light: "day", tau: now, place: "yard" },     // told it was fine
  { id: 9, a: 625, b: 651, light: "day", tau: now, place: "yard" },     // an hour later: creaking
  { id: 10, a: 651, b: 736, light: "day", tau: now, place: "yard" },    // burst, the vat beside it
  { id: 11, a: 736, b: 766, light: "day", tau: now, place: "yard" },    // then the next one
  { id: 12, a: 766, b: 804, light: "day", tau: now, place: "street" },  // the wall comes down
  { id: 13, a: 804, b: 990, light: "day", tau: now, place: "street" },  // into St Giles, cellars
  { id: 14, a: 990, b: 1115, light: "golden", tau: (t) => t + 20, place: "street" }, // the quiet after
  { id: 15, a: 1115, b: 1263, light: "day", tau: () => 0, place: "exp" }, // why one hoop mattered
  { id: 16, a: 1263, b: 1331, light: "day", tau: () => 0, place: "room" }, // a belt after a huge dinner
  { id: 17, a: 1331, b: 1428, light: "day", tau: () => 0, place: "room" }, // lose one notch... pop
  { id: 18, a: 1428, b: 1512, light: "day", tau: () => 0, place: "room" }, // Act of God
  { id: 19, a: 1512, b: 1626, light: "day", tau: () => 0, place: "room" }, // tax refunded
  { id: 20, a: 1626, b: 1727, light: "day", tau: () => 0, place: "room" }, // seven thousand pounds
  { id: 21, a: 1727, b: 1803, light: "day", tau: now, place: "yard" },  // the lesson
  { id: 22, a: 1803, b: 1869, light: "day", tau: now, place: "yard" },  // the hoop falls
  { id: 23, a: 1869, b: TOTAL, light: "day", tau: now, place: "yard" }, // not fine: everyone runs
];
/** crossfades (frames) at place / time changes; a white 4-frame flash after the hook */
export const XFADE: Record<number, number> = { 14: 12, 15: 12, 16: 8, 18: 8, 21: 10 };
export const FLASH_AT = 132;

export const shotAt = (f: number) => SHOTS.find((s) => f >= s.a && f < s.b) ?? SHOTS[SHOTS.length - 1];
export const layersAt = (f: number): { id: number; alpha: number }[] => {
  for (const s of SHOTS) {
    const x = XFADE[s.id];
    if (x && f >= s.a - x / 2 && f < s.a + x / 2) return [{ id: s.id - 1, alpha: 1 }, { id: s.id, alpha: (f - (s.a - x / 2) + 1) / (x + 1) }];
  }
  return [{ id: shotAt(f).id, alpha: 1 }];
};

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
const zoom = (pos: V3, look: V3, fov: number, k: number, rest: Partial<Cam> = {}): Shot =>
  ({ pos, look, fov: (360 / Math.PI) * Math.atan(Math.tan((fov * Math.PI) / 360) * k), ...rest });
const rolled = (s: (f: number) => Shot, roll: number) => (f: number): Shot => ({ ...s(f), roll });
const at = (p: V3, d: V3): V3 => [p[0] + d[0], p[1] + d[1], p[2] + d[2]];

const V0 = VATS[0], V1 = VATS[1], V2 = VATS[2];
const vatFront = (v: Vat, y: number, dz = 0): V3 => [v.x, y, v.z + v.r + dz];
export const GEORGE: V3 = [-4.6, 0, -5.2];   // where George stops to look up at the big vat
export const BOSS: V3 = [-6.6, 0, -6.4];
export const EX = EXP, RM = ROOM;
export const TABLE: V3 = [ROOM[0], 0, ROOM[2] - 1.0];
export const BENCH: V3 = [ROOM[0], 0, ROOM[2] - 3.4];

const CAMS: Record<number, Key[]> = {
  // 1 hook: down the street at the wave, then a low close-up as the foaming crest arrives ("Of beer.")
  1: [
    { f: 0, s: (f) => dolly([1.3, 0.9, 33], [0, 2.1, 10], pushK(f, 0, 0.0022), { fov: 46 }) },
    { f: 93, cut: true, s: (f) => dolly([1.0, 0.8, 34.5], [-0.2, 1.5, 27], pushK(f, 93, 0.004, 0.008, 30), { fov: 40, roll: -0.04 }) },
  ],
  // 2 the brewery: high over the wall corner, the yard, the vats and the brewery facade with its horseshoe
  2: [{ f: 126, s: (f) => zoom([15, 10.5, 7], [0, 5.5, -30], 44, pushK(f, 126, 0.0022)) }],
  // 3 vats taller than a house: low, the office cottage next to the big vat
  3: [{ f: 211, s: (f) => dolly([9.5, 1.5, -0.9], [-4.6, 3.4, -9.4], pushK(f, 211, 0.0025), { fov: 44 }) }],
  // 4 22 ft: tilt up the big vat from its foot, then the hoops close
  4: [
    { f: 268, s: (f) => dolly(vatFront(V0, 1.2, 7.5), vatFront(V0, 1.6, 0), pushK(f, 268, 0.002), { fov: 44 }) },
    { f: 280, dur: 40, s: (f) => dolly(vatFront(V0, 1.2, 7.5), vatFront(V0, 6.4, 0), pushK(f, 280, 0.002), { fov: 44 }) },
    { f: 325, cut: true, s: (f) => dolly(at(vatFront(V0, 3.2, 0), [3.0, -0.2, 3.6]), at(vatFront(V0, 3.4, 0), [-0.6, 0, -0.4]), pushK(f, 325, 0.003), { fov: 40, roll: 0.035 }) },
  ],
  // 5 George walks in, stops and looks up; then the slipped hoop
  5: [
    { f: 386, s: (f) => dolly([GEORGE[0] + 2.4, 1.55, GEORGE[2] + 9], [GEORGE[0] + 2.0, 1.45, GEORGE[2]], pushK(f, 386, 0.0025), { fov: 46 }) },
    { f: 440, dur: 26, s: (f) => dolly([GEORGE[0] + 2.0, 1.2, GEORGE[2] + 3.0], [GEORGE[0] - 0.1, 1.75, GEORGE[2]], pushK(f, 440, 0.003), { fov: 38, roll: -0.035 }) },
    { f: 477, cut: true, s: (f) => dolly(at(vatFront(V0, 1.6, 0), [-1.0, 0.4, 3.3]), at(vatFront(V0, 1.15, 0), [0.4, 0, 0]), pushK(f, 477, 0.003), { fov: 38 }) },
  ],
  // 6 seven hundred pounds of iron: punch in on the hoop
  6: [{ f: 503, s: (f) => dolly(at(vatFront(V0, 0.9, 0), [1.2, 0.25, 2.4]), at(vatFront(V0, 1.0, 0), [0.2, 0, 0]), pushK(f, 503, 0.003, 0.007, 30), { fov: 36, roll: 0.04 }) }],
  // 7 he wrote a note
  7: [{ f: 547, s: (f) => dolly([GEORGE[0] + 1.3, 1.75, GEORGE[2] + 2.4], [GEORGE[0], 1.55, GEORGE[2]], pushK(f, 547, 0.003), { fov: 36 }) }],
  // 8 he was told it was fine: the boss waves it off, George behind
  8: [{ f: 581, s: (f) => dolly([BOSS[0] + 1.3, 1.55, BOSS[2] + 6.4], [BOSS[0] + 0.95, 1.45, BOSS[2] - 0.45], pushK(f, 581, 0.0025, 0.005, 25), { fov: 40 }) }],
  // 9 an hour later: the empty yard, the big vat groaning
  9: [{ f: 625, s: (f) => dolly([V0.x + 7.5, 2.4, V0.z + 13], [V0.x, 3.6, V0.z], pushK(f, 625, 0.004), { fov: 42, roll: -0.03 }) }],
  // 10 the burst (wide, high), then the ring wave smashing the vat beside it
  10: [
    { f: 651, s: (f) => dolly([12, 8.5, -1.2], [-1, 2.6, -13], pushK(f, 651, 0.002), { fov: 46 }) },
    { f: 672, cut: true, s: (f) => dolly([V1.x + 7, 3.2, V1.z + 10], [V1.x + 0.5, 2.6, V1.z], pushK(f, 672, 0.0025), { fov: 42, roll: 0.04 }) },
  ],
  // 11 then the next one
  11: [{ f: 736, s: (f) => dolly([V2.x - 6.5, 3.0, V2.z + 10], [V2.x, 2.8, V2.z], pushK(f, 736, 0.003), { fov: 42, roll: -0.04 }) }],
  // 12 the wall comes down: from the street, low, looking at the wall
  12: [{ f: 766, s: (f) => dolly([2.4, 1.5, 15], [0, 3.6, 0.5], pushK(f, 766, 0.0025), { fov: 46 }) }],
  // 13 aerial down the street; street level as the wave passes the houses; a cellar window
  13: [
    { f: 804, s: (f) => zoom([0.5, 21, 42], [0, 0, 10], 44, pushK(f, 804, 0.0018)) },
    { f: 881, cut: true, s: (f) => dolly([-3.0, 4.6, 34], [1.5, 2.6, 22], pushK(f, 881, 0.0025), { fov: 44 }) },
    { f: 927, cut: true, s: (f) => dolly([-1.8, 2.1, 34.2], [STREET.x1 + 0.1, 0.6, 30.0], pushK(f, 927, 0.003), { fov: 42 }) },
  ],
  // 14 golden: the quiet street after, slow push
  14: [{ f: 984, s: (f) => dolly([0.8, 2.3, 38], [0, 2.4, 6], pushK(f, 984, 0.0012), { fov: 42 }) }],
  // 15 the cutaway vat: arrows of pressure growing with depth
  15: [
    { f: 1109, s: (f) => dolly(at(EXP, [0, 3.6, 19]), at(EXP, [0, 3.4, 0]), pushK(f, 1109, 0.0012), { fov: 42 }) },
    { f: 1200, dur: 36, s: (f) => dolly(at(EXP, [0.4, 2.9, 16.5]), at(EXP, [0, 2.9, 0]), pushK(f, 1200, 0.0012), { fov: 42 }) },
  ],
  // 16 dinner: the boss at the table
  16: [{ f: 1259, s: (f) => dolly(at(TABLE, [1.4, 1.5, 4.4]), at(TABLE, [0, 1.15, -0.6]), pushK(f, 1259, 0.0025), { fov: 40 }) }],
  // 17 the belt, then pop
  17: [
    { f: 1331, s: (f) => dolly(at(TABLE, [0.25, 1.0, 2.0]), at(TABLE, [0, 0.95, -0.55]), pushK(f, 1331, 0.003, 0.006, 30), { fov: 36 }) },
    { f: 1402, cut: true, s: (f) => dolly(at(TABLE, [0.9, 1.35, 3.3]), at(TABLE, [0, 1.25, -0.6]), pushK(f, 1402, 0.003), { fov: 40, roll: 0.04 }) },
  ],
  // 18 the court: wide, the judge high at the back
  18: [
    { f: 1424, s: (f) => dolly(at(BENCH, [0.3, 2.1, 10.5]), at(BENCH, [0, 1.9, 1.0]), pushK(f, 1424, 0.0022), { fov: 44 }) },
    { f: 1478, dur: 22, s: (f) => dolly(at(BENCH, [-1.4, 1.75, 7.6]), at(BENCH, [-1.0, 1.5, 2.6]), pushK(f, 1478, 0.0025), { fov: 40, roll: -0.035 }) },
  ],
  // 19 the refund
  19: [{ f: 1512, s: (f) => dolly(at(BENCH, [-0.25, 1.6, 11.6]), at(BENCH, [-0.25, 1.35, 3.4]), pushK(f, 1512, 0.0022, 0.005, 30), { fov: 48 }) }],
  // 20 unluckily: the official's face, then the money
  20: [
    { f: 1626, s: (f) => dolly(at(BENCH, [-1.2, 1.75, 5.6]), at(BENCH, [-1.45, 1.75, 3.4]), pushK(f, 1626, 0.003), { fov: 36, roll: 0.035 }) },
    { f: 1675, cut: true, s: (f) => dolly(at(BENCH, [1.6, 1.6, 5.6]), at(BENCH, [1.25, 1.05, 3.5]), pushK(f, 1675, 0.003, 0.007, 30), { fov: 36 }) },
  ],
  // 21 the lesson: the yard again, a new vat, everyone at work
  21: [{ f: 1722, s: (f) => dolly([10, 2.0, -3.0], [-4, 2.2, -8], pushK(f, 1722, 0.0018), { fov: 48 }) }],
  // 22 the hoop falls: close on it, then the faces
  22: [
    { f: 1803, s: (f) => dolly(at(vatFront(V0, 3.0, 0), [1.6, 0.2, 4.6]), at(vatFront(V0, 2.4, 0), [0, 0, 0]), pushK(f, 1803, 0.003), { fov: 42 }) },
    { f: 1850, cut: true, s: (f) => dolly([GEORGE[0] + 0.9, 1.6, GEORGE[2] + 3.6], [GEORGE[0] - 0.9, 1.6, GEORGE[2] - 0.4], pushK(f, 1850, 0.003, 0.007, 20), { fov: 38 }) },
  ],
  // 23 not fine: everyone runs out of frame, the vat looms
  23: [{ f: 1869, s: (f) => dolly([8.5, 1.8, -0.8], [-2.5, 2.4, -9], pushK(f, 1869, 0.002), { fov: 46, roll: 0.03 }) }],
};

// impact kicks: image offset flips sign every frame, decays to 0 in 7 f
const KICKS: [number, number][] = [[T_SLIP, 0.5], [TB[0], 1.6], [TB[1], 1.1], [TB[2], 1.0], [T_WALL + 0.5, 1.3], [3.27, 0.8], [T_POP, 0.7], [T_GAVEL, 0.6], [T_FALL + 0.3, 1.2]];
export const kickAt = (t: number) => {
  let a = 0;
  for (const [t0, g] of KICKS) {
    const n = Math.floor((t - t0) * FPS + 1e-6);
    if (n >= 0 && n < 7) a += g * (n % 2 ? -1 : 1) * (1 - n / 7) ** 1.5;
  }
  return a;
};
export const camAt = (id: number, f: number): Cam => {
  const c = run(CAMS[id], f), a = kickAt(T(f));
  if (!a) return c;
  const d: V3 = [c.look[0] - c.pos[0], c.look[1] - c.pos[1], c.look[2] - c.pos[2]];
  const L = Math.hypot(...d), h = Math.hypot(d[0], d[2]) || 1;
  const m = (3 / 640) * Math.tan((c.fov * Math.PI) / 360) * L * a;
  return { ...c, look: [c.look[0] - (d[2] / h) * m, c.look[1] + 0.6 * m, c.look[2] + (d[0] / h) * m], roll: c.roll + a * 0.004 };
};

// ---------------- lens ----------------
export type Dof = { f: number; dur?: number; cInf: number; focus?: (f: number) => V3 };
export const DOF: Dof[] = [
  { f: 0, cInf: 0 },                         // hook wide down the street
  { f: 93, cInf: 12 },                       // crest close-up
  { f: 132, cInf: 0 },                       // brewery wide, vats
  { f: 325, cInf: 12 },                      // hoops close
  { f: 386, cInf: 10, focus: () => [GEORGE[0], 1.75, GEORGE[2]] }, // George
  { f: 477, cInf: 13 },                      // slipped hoop / 700 lb
  { f: 547, cInf: 12, focus: () => [GEORGE[0], 1.75, GEORGE[2]] }, // note
  { f: 581, cInf: 10, focus: () => [BOSS[0], 1.8, BOSS[2]] },      // fine
  { f: 625, cInf: 0 },                       // groan, burst, smash, next, wall, aerial
  { f: 927, cInf: 12 },                      // cellar window
  { f: 990, cInf: 4 },                       // golden aftermath
  { f: 1115, cInf: 8 },                      // cutaway vat against a soft backdrop
  { f: 1263, cInf: 10 },                     // dinner
  { f: 1331, cInf: 13 },                     // belt
  { f: 1402, cInf: 10 },                     // pop
  { f: 1428, cInf: 6 },                      // court wide
  { f: 1512, cInf: 9 },                      // refund
  { f: 1626, cInf: 13 },                     // official close-up, money
  { f: 1727, cInf: 0 },                      // lesson wide
  { f: 1803, cInf: 10 },                     // hoop falls
  { f: 1850, cInf: 12, focus: () => [GEORGE[0] - 0.9, 1.75, GEORGE[2] - 0.4] },
  { f: 1869, cInf: 0 },                      // run
];
export const dofAt = (f: number) => {
  let i = 0; while (i + 1 < DOF.length && f >= DOF[i + 1].f) i++;
  const d = DOF[i], p = DOF[Math.max(0, i - 1)];
  const k = d.dur ? Math.min(1, (f - d.f) / d.dur) : 1;
  return { cInf: p.cInf + (d.cInf - p.cInf) * k, focus: d.focus };
};
