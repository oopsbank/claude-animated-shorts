// Timeline of "What If You Could Pause Time, But Only You Got Older?": shots timed to the voice words
// (shorts/what-if-pause-time/voice/words.json), the freeze state of the world, and the camera grammar of the bridge
// short (continuous slow push-ins, smootherstep glides, big reframes as cuts, 7-frame impact kicks).
// Places: STREET at the origin (road along z, x in -4..4, pavements to |x| 7.5), ROOM, CLASS, FIELD, STUDIO far away.
import { getInputProps } from "remotion";
export const FPS = 30;
export const TOTAL = 1935;
export const D0 = 0;
export type V3 = [number, number, number];

export const clamp01 = (x: number) => Math.max(0, Math.min(1, x));
export const smooth = (x: number) => { const u = clamp01(x); return u * u * (3 - 2 * u); };
export const easeOut = (u: number) => 1 - (1 - clamp01(u)) ** 4;

/** thumbnail stills only: inputProps `{ thumb: { id, pos, look, fov } }` replaces that shot's camera */
export type Thumb = { id?: number; pos: V3; look: V3; fov?: number; roll?: number };
let THUMB_C: Thumb | undefined | null = null;
export const thumbProps = (): Thumb | undefined => { if (THUMB_C === null) THUMB_C = (getInputProps() as { thumb?: Thumb }).thumb; return THUMB_C; };

// ---------------- word-locked story times (seconds, from words.json) ----------------
export const T_OLD = 2.69;     // "older?" the hook: he ages in a second
export const T_MON = 3.56;     // "Monday."
export const T_ALARM = 4.42;   // "Alarm."
export const T_CLICK1 = 5.02;  // "Click." first pause
export const T_STOPS = 6.0;    // "The whole world stops."
export const T_SLEEP = 7.4;    // "You sleep nine more hours."
export const T_NOBODY = 8.78;  // "Nobody notices."
export const T_HOME = 10.14;   // "You pause to finish your homework."
export const T_RACE = 12.3;    // "To win every race."
export const T_CAKE = 13.29;   // "To eat every cake in the bakery."
export const T_DRAW = 15.24;   // "To draw a moustache on your teacher."
export const T_MOUST = 15.63;
export const T_TEST = 17.14;   // "Test tomorrow?"
export const T_PAUSE2 = 18.14; // "Pause."
export const T_STUDY = 18.79;  // "Study for a week."
export const T_TOP = 19.54;    // "Top marks."
export const T_LATE = 20.4;    // "Late for school?"
export const T_PAUSE3 = 21.33; // "Pause."
export const T_STROLL = 21.87; // "Stroll in."
export const T_EARLY = 22.73;  // "Early."
export const T_PERFECT = 23.35; // "It's perfect. For a while."
export const T_WHILE = 24.44;
export const T_MORNING = 25.41; // "Then one morning, in the mirror..."
export const T_GREY = 27.05;   // "a grey hair."
export const T_MATHS = 28.08;  // "You do the maths."
export const T_FROZEN = 29.35; // "The world was frozen."
export const T_WERENT = 30.61; // "You weren't."
export const T_NINE = 31.6;    // "Nine hours here,"
export const T_WEEK = 32.35;   // "a week there."
export const T_SIXTEEN = 33.42; // "You're sixteen on paper."
export const T_BODY = 34.87;   // "Your body is twenty-six."
export const T_FRIENDS = 35.65; // "Your friends laugh at jokes you heard years ago."
export const T_MUM = 37.83;    // "Your mum asks why you look so tired."
export const T_TIRED = 39.15;
export const T_STOP = 40.03;   // "So you stop."
export const T_NOMORE = 41.09; // "No more pausing."
export const T_BUS = 42.14;    // "Until a bus runs a red light,"
export const T_SISTER = 43.47; // "straight at your little sister."
export const T_CLICK4 = 44.93; // "Click."
export const T_FREEZE = 45.79; // "Everything freezes."
export const T_RUN = 46.84;    // "You run out,"
export const T_CARRY = 47.37;  // "and carry her to the pavement."
export const T_ACROSS = 49.04; // "And across the frozen street..."
export const T_MOVING = 50.49; // "someone else is moving."
export const T_OLDMAN = 51.71; // "An old man."
export const T_GREY2 = 52.58;  // "Grey."
export const T_WRINK = 53.16;  // "Wrinkled."
export const T_DRAWN = 53.83;  // "A moustache drawn on his face."
export const T_TEACH = 55.95;  // "Your teacher."
export const T_34 = 56.87;     // "He's thirty-four."
export const T_80 = 57.84;     // "He looks eighty."
export const T_POINT = 58.79;  // "He points at the moustache."
export const T_SAW = 60.39;    // "I saw that," he says.
export const T_UNPAUSE = 62.4; // the old teacher presses play: the world moves again

/** is the world frozen at story time t (for the tint, the bus, the pigeons) */
export const frozenAt = (t: number) =>
  (t < T_MON - 0.05) || (t >= T_CLICK1 + 0.08 && t < T_MORNING - 0.05 && !(t >= T_TEST - 0.05 && t < T_PAUSE2 + 0.08) && !(t >= T_LATE - 0.05 && t < T_PAUSE3 + 0.08))
  || (t >= T_CLICK4 + 0.08 && t < T_UNPAUSE + 0.05);
export const CLICKS = [T_CLICK1, T_PAUSE2, T_PAUSE3, T_CLICK4];

// ---------------- places ----------------
export const ROOM: V3 = [-300, 0, 0];
export const CLASS: V3 = [300, 0, 0];
export const FIELD: V3 = [0, 0, 300];
export const STUDIO: V3 = [0, 0, -300];
export const CURB = 0.15;               // pavement height
export const HERO_HOME: V3 = [-5.4, CURB, 3.2];  // where he waits at the crossing (street, left pavement)
export const SIS_AT: V3 = [-1.9, 0, 0.4];         // the little sister on the zebra crossing (in the bus's lane)
export const SIS_SAFE: V3 = [-5.9, CURB, 1.4];    // where he puts her down
export const BUS_X = -2.0;                        // the bus's lane
/** z of the bus's front bumper (the bus drives toward +z): frozen 1.3 m short of the sister */
export const busFront = (t: number) => {
  const stop = SIS_AT[2] - 1.35, v = 15;
  if (t < T_CLICK4) return stop - v * (T_CLICK4 - t);
  if (t < T_UNPAUSE) return stop;
  return stop + v * (t - T_UNPAUSE) + 3 * (t - T_UNPAUSE) ** 2;
};
export const BUS_LEN = 11;
export const OLD_PATH: V3[] = [[6.2, CURB, 16], [5.6, CURB, 4.2], [-4.5, CURB, 3.7]]; // the old man: up the far pavement, then across
/** the old man's position along OLD_PATH */
export const oldAt = (t: number): V3 => {
  const a = clamp01((t - T_MOVING + 0.4) / (T_DRAWN - 0.3 - T_MOVING + 0.4)), b = clamp01((t - 57.0) / 1.6);
  const p = OLD_PATH, A = [p[0][0] + (p[1][0] - p[0][0]) * a, p[0][2] + (p[1][2] - p[0][2]) * a];
  const x = A[0] + (p[2][0] - A[0]) * b, z = A[1] + (p[2][2] - A[1]) * b;
  return [x, b > 0.08 && b < 0.95 ? 0 : CURB, z];
};

// ---------------- shots ----------------
export type Light = "day" | "golden";
export type Place = "street" | "room" | "class" | "field" | "studio";
export type ShotDef = { id: number; a: number; b: number; light: Light; place: Place };
export const SHOTS: ShotDef[] = [
  { id: 1, a: 0, b: 105, light: "day", place: "street" },     // hook: frozen street, he ages in a second
  { id: 2, a: 105, b: 263, light: "day", place: "room" },     // Monday. Alarm. Click. He goes back to sleep
  { id: 3, a: 263, b: 302, light: "day", place: "room" },     // nobody notices: mum frozen mid-shout at the door
  { id: 4, a: 302, b: 365, light: "day", place: "room" },     // homework at the desk
  { id: 5, a: 365, b: 397, light: "day", place: "field" },    // every race
  { id: 6, a: 397, b: 455, light: "day", place: "street" },   // every cake in the bakery
  { id: 7, a: 455, b: 513, light: "day", place: "class" },    // a moustache on the teacher
  { id: 8, a: 513, b: 610, light: "day", place: "class" },    // test tomorrow? study for a week. top marks
  { id: 9, a: 610, b: 698, light: "day", place: "street" },   // late for school? stroll in. early
  { id: 10, a: 698, b: 760, light: "day", place: "room" },    // it's perfect. for a while
  { id: 11, a: 760, b: 840, light: "day", place: "room" },    // the mirror: a grey hair
  { id: 12, a: 840, b: 1000, light: "day", place: "studio" }, // the maths: frozen clocks, hourglasses
  { id: 13, a: 1000, b: 1066, light: "day", place: "studio" }, // sixteen on paper, twenty-six in the body
  { id: 14, a: 1066, b: 1132, light: "day", place: "class" },  // friends laugh at old jokes
  { id: 15, a: 1132, b: 1198, light: "day", place: "room" },   // mum: why so tired?
  { id: 16, a: 1198, b: 1262, light: "day", place: "room" },   // so you stop: the remote goes in the bin
  { id: 17, a: 1262, b: 1302, light: "day", place: "street" }, // a bus runs the red light
  { id: 18, a: 1302, b: 1345, light: "day", place: "street" }, // straight at your little sister
  { id: 19, a: 1345, b: 1372, light: "day", place: "street" }, // click
  { id: 20, a: 1372, b: 1470, light: "day", place: "street" }, // everything freezes: he carries her to the pavement
  { id: 21, a: 1470, b: 1548, light: "day", place: "street" }, // across the frozen street, someone is moving
  { id: 22, a: 1548, b: 1612, light: "day", place: "street" }, // an old man. grey. wrinkled
  { id: 23, a: 1612, b: 1675, light: "day", place: "street" }, // a moustache drawn on his face
  { id: 24, a: 1675, b: 1703, light: "day", place: "class" },  // your teacher (the moustache, back then)
  { id: 25, a: 1703, b: 1760, light: "day", place: "street" }, // he's thirty-four. he looks eighty
  { id: 26, a: 1760, b: TOTAL, light: "day", place: "street" }, // he points: "I saw that." ...and presses play
];
export const XFADE: Record<number, number> = { 12: 10, 14: 8 };
export const FLASH_AT = 105;

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
const mixC = (a: Cam, b: Cam, k: number): Cam => ({
  pos: a.pos.map((v, i) => v + (b.pos[i] - v) * k) as V3, look: a.look.map((v, i) => v + (b.look[i] - v) * k) as V3,
  fov: a.fov + (b.fov - a.fov) * k, roll: a.roll + (b.roll - a.roll) * k,
});
const full = (c: Shot): Cam => ({ fov: 40, roll: 0, ...c });
const run = (keys: Key[], f: number) => {
  let cur = full(keys[0].s(f));
  for (let i = 1; i < keys.length; i++) {
    const k = keys[i];
    if (f < k.f) break;
    cur = k.cut ? full(k.s(f)) : mixC(cur, full(k.s(f)), glide((f - k.f) / (k.dur ?? 24)));
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
export const at = (p: V3, d: V3): V3 => [p[0] + d[0], p[1] + d[1], p[2] + d[2]];
/** orbit round a point: angle a (rad, 0 = from +z), radius r, height h */
const orbit = (c: V3, a: number, r: number, h: number): V3 => [c[0] + r * Math.sin(a), c[1] + h, c[2] + r * Math.cos(a)];
const F_ = (t: number) => Math.round(t * FPS);

export const HOOK_AT: V3 = [0.6, 0, 22];     // the hook: him standing in the frozen road
export const STALL: V3 = [5.5, CURB, -14];   // the cake stall on the right pavement
export const LATE_Z0 = 44, LATE_Z1 = 31;     // the stroll to school along the left pavement

const CAMS: Record<number, Key[]> = {
  // 1 hook: a slow orbit round him in the frozen road, people and a pigeon stopped mid-air
  1: [{ f: 0, s: (f) => ({ pos: orbit(at(HOOK_AT, [0, 0, 0]), -0.75 + 0.55 * (f / 105), 4.6 - 0.9 * (f / 105), 1.55), look: at(HOOK_AT, [0, 1.25, 0]), fov: 40 }) }],
  // 2 the bedroom: the bed and the alarm; he sits up, clicks, flops back
  2: [{ f: 105, s: (f) => dolly(at(ROOM, [1.4, 2.2, 2.3]), at(ROOM, [-1.6, 0.85, -1.0]), pushK(f, 105, 0.0025), { fov: 44 }) },
    { f: 150, dur: 8, s: (f) => dolly(at(ROOM, [0.9, 1.75, 1.9]), at(ROOM, [-1.6, 0.95, -0.6]), pushK(f, 150, 0.003, 0.012, 20), { fov: 42, roll: 0.02 }) },
    { f: F_(T_SLEEP), dur: 30, s: (f) => dolly(at(ROOM, [0.9, 2.4, 1.8]), at(ROOM, [-1.7, 0.85, -1.2]), pushK(f, 222, 0.002), { fov: 44 }) }],
  // 3 mum frozen at the door mid-shout
  3: [{ f: 263, s: (f) => dolly(at(ROOM, [-1.4, 1.55, 1.75]), at(ROOM, [-2.85, 1.45, 1.55]), pushK(f, 263, 0.004), { fov: 44, roll: -0.03 }) }],
  // 4 homework: papers flying off the desk
  4: [{ f: 302, s: (f) => dolly(at(ROOM, [1.9, 1.6, 0.7]), at(ROOM, [2.05, 1.1, -2.0]), pushK(f, 302, 0.003), { fov: 46 }) }],
  // 5 the race: side-on at the tape
  5: [{ f: 365, s: (f) => dolly(at(FIELD, [0.6, 1.1, 6.5]), at(FIELD, [0.2, 0.95, 0]), pushK(f, 365, 0.003), { fov: 42 }) }],
  // 6 the cake stall
  6: [{ f: 397, s: (f) => dolly(at(STALL, [-3.0, 1.5, 2.3]), at(STALL, [-0.1, 1.15, 0.1]), pushK(f, 397, 0.0035), { fov: 40 }) }],
  // 7 the moustache: teacher frozen at the board, he draws
  7: [{ f: 455, s: (f) => dolly(at(CLASS, [0.45, 1.75, -0.7]), at(CLASS, [0.4, 1.65, -3.1]), pushK(f, 455, 0.004), { fov: 40 }) }],
  // 8 test tomorrow? at his desk; study; top marks
  8: [{ f: 513, s: (f) => dolly(at(CLASS, [0.6, 1.5, -0.9]), at(CLASS, [0.0, 1.0, 1.4]), pushK(f, 513, 0.003), { fov: 50 }) },
    { f: F_(T_TOP) - 4, cut: true, s: (f) => dolly(at(CLASS, [0.15, 1.5, -0.7]), at(CLASS, [0.0, 1.3, 1.1]), pushK(f, F_(T_TOP) - 4, 0.004, 0.012, 20), { fov: 46 }) }],
  // 9 late for school: running along the pavement, then the smug stroll past frozen kids
  9: [{ f: 610, s: (f) => { const z = heroLateZ(T(f)); return { pos: [-2.2, 1.45, z - 4.6], look: [-5.4, 1.15, z + 0.4], fov: 42 }; } }],
  // 10 it's perfect: lying back on the bed, hands behind the head
  10: [{ f: 698, s: (f) => dolly(at(ROOM, [-0.4, 1.7, 0.9]), at(ROOM, [-1.8, 0.75, -1.4]), pushK(f, 698, 0.0015), { fov: 40 }) }],
  // 11 the mirror: from inside the mirror frame, a CU of him brushing his teeth
  11: [{ f: 760, s: (f) => dolly(at(ROOM, [2.9, 1.5, 1.2]), at(ROOM, [1.1, 1.38, 1.2]), pushK(f, 760, 0.002, 0.01, 20), { fov: 40 }) },
    { f: F_(T_GREY) - 3, cut: true, s: (f) => dolly(at(ROOM, [2.9, 1.62, 1.2]), at(ROOM, [1.1, 1.55, 1.2]), pushK(f, F_(T_GREY) - 3, 0.0025, 0.016, 20), { fov: 30 }) }],
  // 12 the maths: the studio, clocks and hourglasses round him
  12: [{ f: 840, s: (f) => dolly(at(STUDIO, [0.0, 1.6, 6.8]), at(STUDIO, [0, 1.25, 0]), pushK(f, 840, 0.0018), { fov: 42 }) },
    { f: F_(T_NINE) - 10, dur: 30, s: (f) => dolly(at(STUDIO, [1.6, 1.5, 5.6]), at(STUDIO, [0.7, 1.05, 0]), pushK(f, 840, 0.0018), { fov: 42 }) }],
  // 13 a cake with 16 candles... and the face of a 26-year-old
  13: [{ f: 1000, s: (f) => dolly(at(STUDIO, [0.0, 1.3, 3.6]), at(STUDIO, [0, 1.2, 0]), pushK(f, 1000, 0.002), { fov: 40 }) },
    { f: F_(T_BODY) - 3, cut: true, s: (f) => dolly(at(STUDIO, [0.0, 1.85, 1.8]), at(STUDIO, [0, 1.78, 0]), pushK(f, F_(T_BODY) - 3, 0.003, 0.014, 20), { fov: 40 }) }],
  // 14 friends laughing round him in class
  14: [{ f: 1066, s: (f) => dolly(at(CLASS, [0.3, 1.5, -0.4]), at(CLASS, [0.0, 1.1, 1.1]), pushK(f, 1066, 0.0025), { fov: 46 }) }],
  // 15 mum at the door: why so tired?
  15: [{ f: 1132, s: (f) => dolly(at(ROOM, [0.9, 1.5, 2.0]), at(ROOM, [-2.3, 1.2, 1.3]), pushK(f, 1132, 0.0025), { fov: 46 }) }],
  // 16 the remote goes in the bin
  16: [{ f: 1198, s: (f) => dolly(at(ROOM, [-0.4, 1.55, 0.7]), at(ROOM, [1.35, 1.0, -1.3]), pushK(f, 1198, 0.003), { fov: 46 }) }],
  // 17 the street, wide: the light turns red, a bus comes on fast
  17: [{ f: 1262, s: (f) => dolly([-6.8, 2.4, 9.5], [-2.2, 1.0, -6], pushK(f, 1262, 0.0015), { fov: 42 }) }],
  // 18 the little sister on the crossing, the bus filling the frame behind her
  18: [{ f: 1302, s: (f) => dolly([-2.6, 0.95, 3.2], [-1.3, 0.7, 0.0], pushK(f, 1302, 0.003), { fov: 42 }) }],
  // 19 click: his thumb on the remote, CU
  19: [{ f: 1345, s: (f) => dolly(at(HERO_HOME, [0.55, 1.75, 1.6]), at(HERO_HOME, [0, 1.55, 0]), pushK(f, 1345, 0.003, 0.014, 20), { fov: 38 }) }],
  // 20 frozen: he runs out and carries her to the pavement
  20: [{ f: 1372, s: (f) => dolly([-7.6, 2.1, 7.2], [-3.4, 0.7, 0.6], pushK(f, 1372, 0.0015), { fov: 44 }) }],
  // 21 across the street: over his shoulder, a figure moving among the frozen people on the far side
  21: [{ f: 1470, s: (f) => dolly(at(SIS_SAFE, [-1.2, 1.75, 2.6]), [3.4, 1.0, 9], pushK(f, 1470, 0.0015), { fov: 40 }) },
    { f: F_(T_MOVING), dur: 30, s: (f) => dolly(at(SIS_SAFE, [-1.0, 1.75, 2.4]), [4.4, 1.2, 10], pushK(f, F_(T_MOVING), 0.003), { fov: 34 }) }],
  // 22 the old man walking toward us on the far pavement
  22: [{ f: 1548, s: (f) => { const p = oldAt(T(f)); return dolly(at(p, [-1.5, 1.45, -3.6]), at(p, [0, 1.25, 0]), pushK(f, 1548, 0.004), { fov: 40 }); } }],
  // 23 CU: the moustache drawn on his face
  23: [{ f: 1612, s: (f) => { const p = oldAt(T(f)); return dolly(at(p, [-0.35, 1.72, -1.5]), at(p, [0, 1.7, 0]), pushK(f, 1612, 0.003, 0.012, 25), { fov: 38 }); } }],
  // 24 back then: the young teacher frozen at the board with the moustache he drew
  24: [{ f: 1675, s: (f) => dolly(at(CLASS, [0.6, 1.5, -1.5]), at(CLASS, [0.72, 1.42, -3.3]), pushK(f, 1675, 0.005), { fov: 40 }) }],
  // 25 he's thirty-four, he looks eighty: crossing the frozen road toward him
  25: [{ f: 1703, s: (f) => { const p = oldAt(T(f)); return dolly(at(p, [-1.9, 1.55, -2.8]), at(p, [0, 1.3, 0]), pushK(f, 1703, 0.003), { fov: 42 }); } }],
  // 26 two-shot: he points at the moustache; "I saw that." Then he presses play and the bus whooshes past behind them
  26: [{ f: 1760, s: (f) => dolly([-4.6, 1.55, 7.4], [-4.9, 1.15, 2.7], pushK(f, 1760, 0.002), { fov: 42 }) },
    { f: F_(T_SAW) - 3, cut: true, s: (f) => dolly([-4.2, 1.72, 5.0], [-4.5, 1.62, 3.7], pushK(f, F_(T_SAW) - 3, 0.003, 0.012, 20), { fov: 40 }) },
    { f: F_(T_UNPAUSE) - 12, cut: true, s: (f) => dolly([-4.9, 1.45, 8.6], [-4.6, 1.1, 2.8], pushK(f, F_(T_UNPAUSE) - 12, 0.0015), { fov: 60 }) }],
};
/** his z on the left pavement in shot 9: running until the pause, then a slow stroll */
export const heroLateZ = (t: number) => {
  if (t < T_PAUSE3) return LATE_Z0 - 3.2 * (t - T_LATE + 0.3);
  const z0 = LATE_Z0 - 3.2 * (T_PAUSE3 - T_LATE + 0.3);
  return z0 - 1.4 * Math.max(0, t - T_STROLL + 0.2);
};

const KICKS: [number, number][] = [[T_OLD, 0.8], [T_ALARM, 0.6], [T_CLICK1, 1.0], [T_PAUSE2, 0.8], [T_PAUSE3, 0.8], [T_TOP, 0.6], [T_GREY, 0.9],
  [T_BODY, 0.8], [T_CLICK4, 1.6], [T_SAW, 0.8], [T_UNPAUSE, 1.0]];
export const kickAt = (t: number) => {
  let a = 0;
  for (const [t0, g] of KICKS) {
    const n = Math.floor((t - t0) * FPS + 1e-6);
    if (n >= 0 && n < 7) a += g * (n % 2 ? -1 : 1) * (1 - n / 7) ** 1.5;
  }
  return a;
};
/** a buzz while the alarm rings */
const shakeAt = (id: number, t: number) => (id === 2 && t > T_ALARM && t < T_CLICK1 ? 0.25 * Math.sin(t * 61) : 0);
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
  { f: 0, cInf: 7 },
  { f: 105, cInf: 8 },
  { f: 263, cInf: 12 },
  { f: 302, cInf: 9 },
  { f: 365, cInf: 8 },
  { f: 397, cInf: 10 },
  { f: 455, cInf: 9 },
  { f: 610, cInf: 8 },
  { f: 698, cInf: 7 },
  { f: 760, cInf: 13 },
  { f: 840, cInf: 6 },
  { f: 1000, cInf: 10 },
  { f: 1066, cInf: 9 },
  { f: 1262, cInf: 0 },
  { f: 1302, cInf: 8 },
  { f: 1345, cInf: 13 },
  { f: 1372, cInf: 3 },
  { f: 1470, cInf: 6, focus: (f) => oldAt(f / FPS) },
  { f: 1548, cInf: 10 },
  { f: 1675, cInf: 10 },
  { f: 1760, cInf: 7 },
];
export const dofAt = (f: number) => {
  let i = 0; while (i + 1 < DOF.length && f >= DOF[i + 1].f) i++;
  const d = DOF[i], p = DOF[Math.max(0, i - 1)];
  const k = d.dur ? Math.min(1, (f - d.f) / d.dur) : 1;
  return { cInf: p.cInf + (d.cInf - p.cInf) * k, focus: d.focus };
};
