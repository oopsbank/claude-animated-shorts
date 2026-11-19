// Our cast as lit flat sprites in the 3D world (the bridge / beer-flood machinery: canvas pool, lit cards, unlit
// effect cards, contact blobs), staged for "What If You Could Pause Time, But Only You Got Older?".
import * as THREE from "three";
import {
  Pen, bodyFront, bodySide, fxBurst, fxShadow, fxContact, fxSweat, fxPaper, Outfit, Expr, FrontOpts, SideOpts, INK, mix,
  fxPause, fxClock, fxZ, fxPigeon, fxBall, fxCoffee, fxHourglass, fxCalendar, fxBooks, fxCake16, fxHair, fxSpark, fxRemote, fxStars,
} from "./toon";
import {
  FPS, V3, SHOTS, clamp01, smooth, at, frozenAt, CLICKS, ROOM, CLASS, FIELD, STUDIO, CURB, HERO_HOME, SIS_AT, SIS_SAFE, STALL, HOOK_AT,
  LATE_Z0, heroLateZ, oldAt, busFront,
  T_OLD, T_MON, T_ALARM, T_CLICK1, T_STOPS, T_SLEEP, T_HOME, T_RACE, T_CAKE, T_DRAW, T_MOUST, T_TEST, T_PAUSE2, T_STUDY, T_TOP,
  T_LATE, T_PAUSE3, T_STROLL, T_EARLY, T_WHILE, T_GREY, T_FROZEN, T_WERENT, T_NINE, T_WEEK, T_SIXTEEN, T_BODY, T_FRIENDS, T_MUM,
  T_STOP, T_NOMORE, T_BUS, T_CLICK4, T_RUN, T_CARRY, T_MOVING, T_WRINK, T_DRAWN, T_POINT, T_SAW, T_UNPAUSE,
} from "./story";
import { LIGHTS } from "./lights";
import { NOINK } from "./ink";
import { cardShade, blobMaterial, CARD_K } from "./cardshade";

// ---------------- canvas pool ----------------
type Entry = { cv: HTMLCanvasElement; tex: THREE.CanvasTexture; w: number; h: number };
export type Req = { key: string; w: number; h: number; k: number; draw: (p: Pen) => void; tex?: THREE.CanvasTexture };
const makeEntry = (w: number, h: number): Entry => {
  const cv = document.createElement("canvas");
  cv.width = w; cv.height = h;
  const tex = new THREE.CanvasTexture(cv);
  tex.colorSpace = THREE.SRGBColorSpace; tex.anisotropy = 8;
  return { cv, tex, w, h };
};
export class Pool {
  private live = new Map<string, Entry>();
  private free: Entry[] = [];
  private reqs: Req[] = [];
  req(key: string, w: number, h: number, k: number, draw: (p: Pen) => void) {
    const r: Req = { key: `${w}x${h}|${key}`, w, h, k, draw };
    this.reqs.push(r);
    return r;
  }
  flush() {
    const want = new Map<string, Req[]>();
    for (const r of this.reqs) { const l = want.get(r.key); if (l) l.push(r); else want.set(r.key, [r]); }
    for (const [key, e] of this.live) if (!want.has(key)) { this.live.delete(key); this.free.push(e); }
    for (const [key, rs] of want) {
      let e = this.live.get(key);
      if (!e) {
        const r = rs[0], i = this.free.findIndex((x) => x.w === r.w && x.h === r.h);
        e = i >= 0 ? this.free.splice(i, 1)[0] : makeEntry(r.w, r.h);
        const g = e.cv.getContext("2d")!;
        g.setTransform(1, 0, 0, 1, 0, 0); g.clearRect(0, 0, e.w, e.h); g.setTransform(r.k, 0, 0, r.k, 0, 0);
        r.draw(new Pen(g));
        e.tex.needsUpdate = true;
        this.live.set(key, e);
      }
      for (const r of rs) r.tex = e.tex;
    }
    this.reqs = [];
  }
}

// ---------------- sprite meshes ----------------
const blank = (() => { const c = document.createElement("canvas"); c.width = c.height = 2; return new THREE.CanvasTexture(c); })();
export const SU = 0.00216; // metres per design unit: 1000 units = 2.16 m
const BODY = (() => { const g = new THREE.PlaneGeometry(600 * SU, 1000 * SU); g.translate(0, (975 - 500) * SU, 0); return g; })();
const CARD = new THREE.PlaneGeometry(1, 1);
/** world roots that hold actors (to find the scene's sun when world.ts does not pass it) */
const ROOTS = new Set<THREE.Object3D>();

/** lit flat character: cardShade() material, receives shadows (dims to the bright floor only), casts its silhouette
 *  when world.ts says so (golden). Drawn after the contact blobs (renderOrder 1). */
export class Actor {
  mesh: THREE.Mesh; mat: THREE.MeshLambertMaterial; dmat: THREE.MeshDepthMaterial; r: Req | null = null;
  constructor(parent: THREE.Object3D, geo: THREE.BufferGeometry = BODY) {
    this.mat = cardShade(new THREE.MeshLambertMaterial({ map: blank, alphaTest: 0.5, side: THREE.DoubleSide }));
    this.mat.alphaToCoverage = false; // A2C + MSAA left 1 px sky-depth seams on blurred far cards (POST)
    this.dmat = new THREE.MeshDepthMaterial({ depthPacking: THREE.RGBADepthPacking, map: blank, alphaTest: 0.5, side: THREE.DoubleSide });
    this.mesh = new THREE.Mesh(geo, this.mat);
    this.mesh.customDepthMaterial = this.dmat;
    // rim width is in output pixels: tell the card shader the render height (1920 = 1080 x 1920 frame)
    this.mesh.onBeforeRender = (r) => { const rt = r.getRenderTarget(); CARD_K.uPx.value = (rt ? rt.height : r.domElement.height) / 1920; };
    this.mesh.castShadow = false; this.mesh.receiveShadow = true; this.mesh.visible = false;
    this.mesh.rotation.order = "YXZ"; this.mesh.renderOrder = 1; this.mesh.layers.set(NOINK);
    parent.add(this.mesh);
    ROOTS.add(parent);
  }
  bind() { const t = this.r?.tex; if (t) { this.mat.map = t; this.dmat.map = t; } }
}
/** unlit effect card: hard cut-out (ink drawings), soft see-through (dust, mist) or a multiply ground blob */
export class Fx {
  mesh: THREE.Mesh; mat: THREE.MeshBasicMaterial; soft: THREE.MeshBasicMaterial; blob: THREE.MeshBasicMaterial; r: Req | null = null;
  constructor(parent: THREE.Object3D) {
    this.mat = new THREE.MeshBasicMaterial({ map: blank, alphaTest: 0.5, side: THREE.DoubleSide });
    this.mat.alphaToCoverage = false; // A2C + MSAA left 1 px sky-depth seams on blurred far cards (POST)
    this.soft = new THREE.MeshBasicMaterial({ map: blank, transparent: true, depthWrite: false, side: THREE.DoubleSide });
    this.blob = blobMaterial(blank);
    this.mesh = new THREE.Mesh(CARD, this.mat);
    this.mesh.visible = false; this.mesh.layers.set(NOINK);
    parent.add(this.mesh);
  }
  use(soft: boolean) { this.mesh.material = soft ? this.soft : this.mat; }
  bind() {
    const t = this.r?.tex;
    if (!t) return;
    if (this.r!.key.includes("|blob|")) {
      // no mipmaps: at grazing views the mip chain averages the blob with its white surround and it fades out
      if (t.generateMipmaps) { t.generateMipmaps = false; t.minFilter = THREE.LinearFilter; t.needsUpdate = true; }
      this.blob.map = t; this.mesh.material = this.blob; this.mesh.renderOrder = 0.5;
    }
    else { this.mat.map = t; this.soft.map = t; this.mesh.renderOrder = 0; }
  }
}

// ---------------- placements ----------------
export type Place = {
  key: string; draw: (p: Pen) => void; x: number; y: number; z: number;
  scale?: number; mirror?: boolean; yaw?: number; geo?: "body" | "swing"; roll?: number; size?: [number, number, number];
};
export type FxPlace = { key: string; cw: number; ch: number; draw: (p: Pen) => void; x: number; y: number; z: number; w: number; h: number; flat?: boolean; rot?: number; soft?: boolean };
/** sun = world direction TOWARD the sun (optional: when absent the scene's shadow-casting light is used) */
export type CamInfo = { pos: THREE.Vector3; right: THREE.Vector3; sun?: THREE.Vector3 };

const hh = (i: number, s = 0) => { const v = Math.sin(i * 127.1 + s * 311.7) * 43758.5453; return v - Math.floor(v); };
const q = (v: number, n = 120) => Math.round(v * n) / n;
/** head-shape seed: 7 shapes, so marching soldiers in step still share canvases */
const seedOf = (i: number) => ((i * 5 + 3) % 7) + 1;
/** drawing resolution by distance: [canvas w, h, scale from the 600 x 1000 design]; sized for the 1440 x 2560 final */
const tier = (d: number): [number, number, number] =>
  d < 3.2 ? [1800, 3000, 3.0] : d < 6.5 ? [1080, 1800, 1.8] : d < 16 ? [480, 800, 0.8] : [240, 400, 0.4];

// ---------------- light ----------------
const SUN = new THREE.Vector3(0.5, 0.75, -0.4).normalize();
const tmp = new THREE.Vector3();
let LNAME: "day" | "golden" = "day";
const sunOf = (root: THREE.Object3D) => {
  let s: THREE.DirectionalLight | null = null;
  root.traverse((o) => { if (!s && o instanceof THREE.DirectionalLight && o.castShadow) s = o; });
  return s as THREE.DirectionalLight | null;
};
/** the sun of the world that is calling: the attached root whose sun target sits on this camera's view axis */
const findSun = (cam: CamInfo, out: THREE.Vector3) => {
  if (cam.sun) return out.copy(cam.sun).normalize();
  let best: THREE.DirectionalLight | null = null, err = Infinity;
  for (const r of ROOTS) {
    if (!r.parent) continue;
    const s = sunOf(r);
    if (!s) continue;
    const d = tmp.copy(s.target.position).sub(cam.pos), e = Math.abs(d.dot(cam.right)) / (d.length() || 1);
    if (e < err) { err = e; best = s; }
  }
  return best ? out.copy(best.position).sub(best.target.position).normalize() : out;
};
/** canvas angle the sun comes FROM on an upright card facing the camera, in 45-degree steps (small texture cache) */
const light2D = (cam: CamInfo, mirror: boolean) => {
  const sx = SUN.dot(cam.right) * (mirror ? -1 : 1), sy = -SUN.y;
  return Math.round(Math.atan2(sy, sx) / (Math.PI / 4)) * (Math.PI / 4);
};

/** front / side view and mirroring for someone at (x, z) walking along (dx, dz); fs = foreshortening of the walk */
const viewOf = (cam: CamInfo, x: number, z: number, dx: number, dz: number) => {
  const tx = cam.pos.x - x, tz = cam.pos.z - z, tl = Math.hypot(tx, tz) || 1;
  const c = (tx * dx + tz * dz) / tl;
  return { side: c < 0.57, mirror: dx * cam.right.x + dz * cam.right.z < 0, fs: Math.round(Math.sqrt(Math.max(0, 1 - c * c)) * 20) / 20 };
};

// ---------------- life: blinks and reaction timing ----------------
/** reference expression and action changes land 0-3 f before the word onset */
const LEAD = 2 / FPS;
/** eyelid 0 open .. 1 shut. Reference: gaps 0.5-2.3 s, 4-frame blink half / shut / shut / half, plus a blink across
 *  every expression swap (the shut frames hide the swap) */
const LID = [0.5, 1, 1, 0.5];
const SWAPS: Record<number, number[]> = {};
const lidAt = (t: number, i: number, swaps: number[] = []) => {
  const f = Math.round(t * FPS);
  for (const ts of swaps) { const k = f - Math.round((ts - LEAD) * FPS) + 1; if (k >= 0 && k < 4) return LID[k]; }
  let s = Math.round(-60 * hh(i, 9));
  for (let n = 0; s <= f && n < 400; n++) {
    const k = f - s;
    if (k >= 0 && k < 4) return LID[k];
    s += Math.round(15 + 54 * hh(i * 31 + n, 13)); // next blink 0.5-2.3 s later
  }
  return 0;
};
const fkey = (o: object) => JSON.stringify(o, (_k, v) => (typeof v === "number" ? q(v) : v));

type Who = { i: number; o: Outfit; okey: string };
/** one character drawing in the 600 x 1000 design space, sized by distance, lit from the scene's sun */
const person = (cam: CamInfo, who: Who, x: number, y: number, z: number, view: { side: boolean; mirror: boolean }, fo: FrontOpts, so: SideOpts, scale = 1): Place & { tierKey: string } => {
  const d = cam.pos.distanceTo(tmp.set(x, y + 1.2, z)) / scale;
  const [w, h, k] = tier(d);
  const mirror = view.side && view.mirror, light = light2D(cam, mirror), seed = seedOf(who.i);
  const f2: FrontOpts = { ...fo, light, seed }, s2: SideOpts = { ...so, light, seed };
  const key = view.side ? `S|${who.okey}|${fkey(s2)}` : `F|${who.okey}|${fkey(f2)}`;
  return {
    key, x, y, z, scale, mirror, tierKey: `${w}`,
    draw: (p) => (view.side ? bodySide(p, who.o, s2) : bodyFront(p, who.o, f2)),
    size: [w, h, k],
  };
};

/** ground shadow under a standing / sitting card (review rounds 2-4), multiply, blue-violet: a TIGHT contact pool right under
 *  the feet (~.5 on screen at the core) so nobody floats, plus by day (cards cast no real shadow) a lighter soft tail
 *  stretched AWAY from the sun, length ~1.6 m / tan(sun elevation), capped. Golden: world.ts casts real card shadows. */
const CONTACT: Record<"day" | "golden", [number, number, number]> = { day: [0.2, 0.21, 0.33], golden: [0.24, 0.2, 0.33] };
const TAIL: [number, number, number] = [0.42, 0.44, 0.62];
const toSrgb = (v: number) => { const c = clamp01(v); return c <= 0.0031308 ? 12.92 * c : 1.055 * c ** (1 / 2.4) - 0.055; };
const hexOf = (c: [number, number, number], k: number) => "#" + c.map((v) => Math.round(255 * toSrgb(1 - (1 - v) * k)).toString(16).padStart(2, "0")).join("");
const blob = (out: Stage, x: number, y: number, z: number, sc = 1, k = 1) => {
  const hl = Math.hypot(SUN.x, SUN.z) || 1, ox = -SUN.x / hl, oz = -SUN.z / hl, rot = Math.atan2(-ox, -oz);
  if (LNAME === "day") {
    const el = Math.asin(Math.min(0.99, Math.max(0.1, SUN.y)));
    const len = Math.min(2.4, Math.max(0.5, 1.6 / Math.tan(el))) * sc, h = len + 0.55 * sc, c = 0.3 * h; // feet at v = .2 of the card
    const tc = hexOf(TAIL, k);
    out.fx.push({ key: `blob|shadow|${tc}`, cw: 128, ch: 256, draw: (p) => fxShadow(p, tc), x: x + ox * c, y: y + 0.018, z: z + oz * c,
      w: 0.72 * sc, h, flat: true, rot });
  }
  const cc = hexOf(CONTACT[LNAME], k);
  out.fx.push({ key: `blob|contact|${cc}`, cw: 128, ch: 128, draw: (p) => fxContact(p, cc), x: x + ox * 0.03 * sc, y: y + 0.022, z: z + oz * 0.03 * sc,
    w: 0.52 * sc, h: 0.4 * sc, flat: true, rot });
};


export type Stage = { places: Place[]; fx: FxPlace[] };

// ---------------- our cast ----------------
const HAIR_YOUNG = "#5a3b2a", HAIR_GREY = "#d9d6d0";
/** the hero (16): orange hoodie, jeans; `age` 0..1 greys the hair and lines the face, stubble from his "26" */
const heroO = (age = 0, stubble = false): Outfit => ({
  jacket: "#e5683a", pants: "#3b5b9a", boots: "#f4f1ea", hat: "hair", hair: mix(HAIR_YOUNG, HAIR_GREY, Math.min(1, age * 1.15)),
  buttons: "#f6c9a8", skin: "#ffe2c2", age, stubble,
});
const TEACH_YOUNG: Outfit = { jacket: "#7a5a3a", pants: "#3d3a44", boots: "#2e2420", hat: "hair", hair: "#2e2a2a", buttons: "#d9c28a", skin: "#f5c9a0" };
const teacherO = (marker: number, old: boolean): Outfit => old
  ? { ...TEACH_YOUNG, hair: "#eeece6", age: 1, marker, build: "stout" }
  : { ...TEACH_YOUNG, marker };
const MUM_O: Outfit = { jacket: "#7b5ac9", pants: "#3b3f52", boots: "#5a3b2a", hat: "hair", hair: "#8a5a3a", dress: "#7b5ac9", skin: "#ffe2c2" };
const SIS_O: Outfit = { jacket: "#ffd35a", pants: "#3b5b9a", boots: "#f4f1ea", hat: "hair", hair: "#5a3b2a", dress: "#ffd35a", build: "kid", skin: "#ffe2c2" };
const BAKER_O: Outfit = { jacket: "#f4f1ea", pants: "#3d3a44", boots: "#2e2420", hat: "hair", hair: "#c9a050", build: "stout", buttons: "#c9ccd2", skin: "#f5c9a0", moustache: "#a0782a" };
const FRIEND_O: Outfit[] = [
  { jacket: "#3b8fd0", pants: "#33363f", boots: "#f4f1ea", hat: "hair", hair: "#2e2a2a", skin: "#c99067" },
  { jacket: "#4f9a50", pants: "#3b3f52", boots: "#f4f1ea", hat: "hair", hair: "#c9a050", skin: "#ffe2c2" },
];
const FOLK_O: Outfit[] = [
  { jacket: "#d9a441", pants: "#3b3f52", boots: "#3a2a22", hat: "hair", hair: "#5a3b2a" },
  { jacket: "#5a8fc2", pants: "#3b3f52", boots: "#3a2a22", hat: "hair", hair: "#2e2a2a", skin: "#c99067" },
  { jacket: "#c25a7a", pants: "#3b3f52", boots: "#3a2a22", hat: "hair", hair: "#c9a050", dress: "#c25a7a" },
  { jacket: "#4f9a6a", pants: "#3b3f52", boots: "#3a2a22", hat: "hair", hair: "#8a5a3a", skin: "#ecd0b6" },
  { jacket: "#7b5ac9", pants: "#3b3f52", boots: "#3a2a22", hat: "hair", hair: "#e8d6a0" },
  { jacket: "#3e6f86", pants: "#33363f", boots: "#2a2422", hat: "hair", hair: "#3a2a22", skin: "#f5c9a0", moustache: "#3a2a22" },
];
const KID_O: Outfit[] = [
  { jacket: "#f08a2c", pants: "#3b5b9a", boots: "#f4f1ea", hat: "cap", cap: "#e2453c", build: "kid" },
  { jacket: "#3b8fd0", pants: "#3b3f52", boots: "#f4f1ea", hat: "hair", hair: "#2e2a2a", build: "kid", skin: "#c99067" },
  { jacket: "#c25a7a", pants: "#3b5b9a", boots: "#f4f1ea", hat: "hair", hair: "#c9a050", build: "kid", dress: "#c25a7a" },
  { jacket: "#4f9a50", pants: "#3b3f52", boots: "#f4f1ea", hat: "cap", cap: "#3b6fb6", build: "kid", skin: "#ecd0b6" },
];
const okey = (o: Outfit) => JSON.stringify(o);
const W = (i: number, o: Outfit): Who => ({ i, o, okey: okey(o) });
const FRONT = { side: false, mirror: false };

const stand = (out: Stage, cam: CamInfo, t: number, who: Who, x: number, y: number, z: number, expr: Expr, extra: Partial<FrontOpts> = {}, scale = 1, shadow = true) => {
  out.places.push(person(cam, who, x, y, z, FRONT, { mode: "stand", expr, blink: lidAt(t, who.i), ...extra }, {}, scale));
  if (shadow) blob(out, x, y, z, scale);
};
const sit = (out: Stage, cam: CamInfo, t: number, who: Who, x: number, y: number, z: number, expr: Expr, extra: Partial<FrontOpts> = {}, scale = 1) =>
  out.places.push(person(cam, who, x, y, z, FRONT, { mode: "sit", expr, blink: lidAt(t, who.i), ...extra }, {}, scale));
/** lying down: a front card rolled onto its side (head to screen-left), pivoting on the soles */
const lie = (out: Stage, cam: CamInfo, t: number, who: Who, x: number, y: number, z: number, expr: Expr, extra: Partial<FrontOpts> = {}) => {
  const p = person(cam, who, x, y, z, FRONT, { mode: "stand", expr, blink: lidAt(t, who.i), ...extra }, {}, 1);
  out.places.push({ ...p, roll: Math.PI / 2 });
};
/** walking from (x0,z0) to (x1,z1) between t0 and t1 (side view when crossing the frame, front when coming at us) */
const walk = (out: Stage, cam: CamInfo, t: number, who: Who, x0: number, z0: number, x1: number, z1: number, t0: number, t1: number, expr: Expr, y = 0, run = false, extra: Partial<FrontOpts> = {}) => {
  const u = clamp01((t - t0) / (t1 - t0)), x = x0 + (x1 - x0) * u, z = z0 + (z1 - z0) * u;
  const L = Math.hypot(x1 - x0, z1 - z0) || 1, dx = (x1 - x0) / L, dz = (z1 - z0) / L, speed = L / (t1 - t0);
  const moving = t > t0 && t < t1;
  const cad = run ? 3.2 : 1.7;
  const phase = moving ? q(((t - t0) * cad / 2) % 1, 120) : 0;
  const view = viewOf(cam, x, z, dx, dz);
  const so: SideOpts = { mode: moving ? "march" : "stand", phase, expr, stomp: run ? 1.3 : 0.6, stride: Math.min(1.6, (speed / cad / 0.8) * 2) * view.fs, blink: lidAt(t, who.i) };
  const fo: FrontOpts = { mode: moving ? "stroll" : "stand", phase, expr, blink: lidAt(t, who.i), tilt: run && moving ? 6 : 0, ...extra };
  out.places.push(person(cam, who, x, y, z, moving ? view : FRONT, fo, so));
  blob(out, x, y, z);
};
/** someone stopped mid-stride (frozen in time): a side view at a fixed walk phase; moves while the world plays */
const strider = (out: Stage, cam: CamInfo, t: number, who: Who, x: number, y: number, z: number, dx: number, dz: number, phase: number, expr: Expr, run = false, scale = 1) => {
  let s = 0;
  if (t < T_CLICK4 && !frozenAt(t)) s = (t - T_CLICK4) * (run ? 3 : 1.25);
  if (t >= T_UNPAUSE) s = (t - T_UNPAUSE) * (run ? 3 : 1.25);
  const moving = !frozenAt(t), ph = moving ? q((phase + s / 1.4) % 1 + 1, 120) % 1 : phase;
  const X = x + dx * s, Z = z + dz * s;
  const view = viewOf(cam, X, Z, dx, dz);
  const so: SideOpts = { mode: "march", phase: ph, expr, stomp: run ? 1.3 : 0.6, stride: (run ? 1.5 : 1.0) * Math.max(0.35, view.fs), blink: frozenAt(t) ? 0 : lidAt(t, who.i) };
  const fo: FrontOpts = { mode: "stroll", phase: ph, expr, blink: frozenAt(t) ? 0 : lidAt(t, who.i), tilt: run ? 6 : 0 };
  out.places.push(person(cam, who, X, y, Z, view, fo, so, scale));
  blob(out, X, y, Z, scale);
};
const card = (out: Stage, key: string, cw: number, ch: number, draw: (p: Pen) => void, x: number, y: number, z: number, w: number, h: number, o: Partial<FxPlace> = {}) =>
  out.fx.push({ key, cw, ch, draw, x, y, z, w, h, ...o });
/** the pause ring at a point, for 0.5 s after each click */
const ring = (out: Stage, t: number, p: V3, size = 2.2) => {
  for (const tc of [...CLICKS, T_UNPAUSE]) {
    const u = (t - tc) / 0.5;
    if (u >= 0 && u < 1) card(out, `pause${q(u, 15)}`, 512, 512, (pp) => fxPause(pp, u), p[0], p[1], p[2], size * (0.6 + 0.6 * u), size * (0.6 + 0.6 * u), { soft: true });
  }
};

// ---- the frozen street: people mid-stride, pigeons and a ball in the air ----
type Folk = { x: number; z: number; dx: number; dz: number; ph: number; o: number; kid?: boolean; run?: boolean; expr?: Expr };
const FOLK: Folk[] = [
  { x: 5.8, z: 8, dx: 0, dz: -1, ph: 0.25, o: 0 }, { x: 6.5, z: 11.5, dx: 0, dz: 1, ph: 0.6, o: 1 },
  { x: 5.3, z: 14.5, dx: 0, dz: -1, ph: 0.1, o: 2 }, { x: -6.2, z: 8.5, dx: 0, dz: 1, ph: 0.4, o: 3 },
  { x: -5.6, z: 12.4, dx: 0, dz: -1, ph: 0.75, o: 4 }, { x: 6.0, z: -4.5, dx: 0, dz: 1, ph: 0.5, o: 5 },
  { x: -6.6, z: -3.6, dx: 0, dz: -1, ph: 0.3, o: 0 }, { x: 6.6, z: 1.2, dx: 0, dz: -1, ph: 0.85, o: 3 },
  // round the hook spot
  { x: 2.0, z: 20.6, dx: 1, dz: 0, ph: 0.35, o: 1 }, { x: -1.4, z: 24.2, dx: -1, dz: 0, ph: 0.8, o: 2 },
  { x: 5.9, z: 22.5, dx: 0, dz: -1, ph: 0.15, o: 5 }, { x: -5.9, z: 19.5, dx: 0, dz: 1, ph: 0.55, o: 4 },
  { x: 3.1, z: 25.5, dx: 0.7, dz: -0.7, ph: 0.65, o: 0, kid: true, run: true, expr: "grin" },
  // schoolkids dashing along the left pavement (shot 9)
  { x: -5.0, z: 37, dx: 0, dz: -1, ph: 0.2, o: 0, kid: true, run: true, expr: "nervous" }, { x: -6.0, z: 34.5, dx: 0, dz: -1, ph: 0.7, o: 1, kid: true, run: true, expr: "shock" },
  { x: -5.3, z: 31.5, dx: 0, dz: -1, ph: 0.45, o: 2, kid: true, run: true, expr: "nervous" }, { x: -6.3, z: 29, dx: 0, dz: -1, ph: 0.9, o: 3, kid: true, run: true, expr: "stern" },
];
const PIGEONS: [number, number, number, number][] = [[1.8, 2.4, 21.0, 0.8], [-0.6, 3.1, 23.4, 0.2], [4.3, 2.8, 5.5, 0.6], [-3.4, 3.4, 9.5, 0.9], [2.6, 3.0, -3.0, 0.3]];
const street = (out: Stage, cam: CamInfo, t: number, near: (x: number, z: number) => boolean) => {
  FOLK.forEach((f, i) => {
    if (!near(f.x, f.z)) return;
    const o = f.kid ? KID_O[f.o % KID_O.length] : FOLK_O[f.o % FOLK_O.length];
    strider(out, cam, t, W(40 + i, o), f.x, Math.abs(f.x) > 4 ? CURB : 0, f.z, f.dx, f.dz, f.ph, f.expr ?? (["neutral", "smile", "whistle", "neutral", "grin", "stern"] as Expr[])[i % 6], !!f.run);
  });
  PIGEONS.forEach(([x, y, z, w], i) => {
    if (!near(x, z)) return;
    const fly = frozenAt(t) ? 0 : t >= T_UNPAUSE ? t - T_UNPAUSE : t - T_CLICK4;
    const wing = frozenAt(t) ? w : q(0.5 + 0.5 * Math.sin(t * 22 + i), 6);
    card(out, `pigeon${wing}`, 256, 256, (p) => fxPigeon(p, wing), x + 2.5 * fly, y + 1.5 * Math.abs(fly), z - 1.2 * fly, 0.42, 0.42);
  });
};

// ---- per shot ----
const HERO = (age = 0, stub = false) => W(1, heroO(q(age, 20), stub));
const SIS = W(2, SIS_O), MUM = W(3, MUM_O), BAKER = W(4, BAKER_O);
const TEACH = (marker: number, old: boolean) => W(old ? 6 : 5, teacherO(q(marker, 20), old));
const R = (d: V3) => at(ROOM, d), C = (d: V3) => at(CLASS, d), Fd = (d: V3) => at(FIELD, d), S = (d: V3) => at(STUDIO, d);

const hook = (out: Stage, cam: CamInfo, t: number) => {
  const k = smooth((t - T_OLD - 0.05) / 0.7);
  stand(out, cam, t, HERO(0.95 * k, k > 0.5), HOOK_AT[0], HOOK_AT[1], HOOK_AT[2], k > 0.05 ? "shock" : "smile", { prop: ["remote", 0], tilt: 3 * k });
  street(out, cam, t, (x, z) => z > 12);
  card(out, "ball", 128, 128, fxBall, HOOK_AT[0] - 1.5, 1.15, HOOK_AT[2] + 1.6, 0.36, 0.36);
  card(out, "coffee", 256, 256, fxCoffee, 2.8, 1.35, 20.8, 0.55, 0.55);
  if (t > T_OLD && t < T_OLD + 0.6) card(out, `hstar${q((t - T_OLD) / 0.6, 12)}`, 256, 256, (p) => fxStars(p, (t - T_OLD) / 0.6), HOOK_AT[0], 2.0, HOOK_AT[2], 0.9, 0.9);
};
const BED_FEET: V3 = R([-0.85, 0.86, -1.35]), BED_SIT: V3 = R([-1.6, 0.36, -0.25]);
const CLOCK_AT: V3 = R([-0.48, 0.73, -2.15]);
const bedroom = (out: Stage, cam: CamInfo, t: number) => {
  const ringing = t > T_ALARM && t < T_CLICK1 + 0.1, frozen = t > T_STOPS - 0.4;
  const sh = ringing ? q(Math.sin(t * 60), 4) : frozen ? 0.6 : 0;
  card(out, `clock${sh}`, 256, 256, (p) => fxClock(p, 7 / 12, 0, ringing || frozen ? 0.5 + 0.5 * sh : 0), CLOCK_AT[0] + (ringing ? 0.01 * sh : 0), CLOCK_AT[1], CLOCK_AT[2], 0.32, 0.32);
  if (t < T_ALARM + 0.15) lie(out, cam, t, HERO(), ...BED_FEET, "whistle", { blink: 1 });
  else if (t < T_SLEEP) sit(out, cam, t, HERO(), ...BED_SIT, t < T_CLICK1 ? "stern" : "smile", { prop: ["remote", t > T_CLICK1 - 0.05 ? 1 : 0] });
  else lie(out, cam, t, HERO(), ...BED_FEET, t < T_SLEEP + 0.5 ? "smile_closed" : "whistle", { blink: 1 });
  ring(out, t, R([-1.4, 1.2, -1.2]), 2.6);
  // a pigeon stopped outside the window
  if (t > T_STOPS - 0.3) card(out, "pigeon0.5", 256, 256, (p) => fxPigeon(p, 0.5), R([-1.5, 1.95, -2.45])[0], 1.95, R([0, 0, -2.45])[2], 0.4, 0.4);
  if (t > T_SLEEP + 0.4) for (let k = 0; k < 3; k++) {
    const u = ((t - T_SLEEP - 0.4) * 0.6 + k / 3) % 1;
    card(out, "zzz", 128, 128, fxZ, R([-2.2 + 0.3 * u, 1.05 + 0.8 * u, -1.25])[0], 1.05 + 0.8 * u, R([0, 0, -1.25])[2], 0.12 + 0.12 * u, 0.12 + 0.12 * u);
  }
};
const DOOR: V3 = [-2.82, 0, 1.55];
const mumDoor = (out: Stage, cam: CamInfo, t: number, id: number) => {
  if (id === 3) stand(out, cam, t, MUM, ...R(DOOR), "shout", { prop: ["hands", 0.8], blink: 0 });
  else stand(out, cam, t, MUM, ...R(DOOR), t > T_MUM + 0.3 ? "nervous" : "neutral", { prop: t > T_MUM + 0.4 ? ["hands", 0.5] : null });
};
const homework = (out: Stage, cam: CamInfo, t: number) => {
  sit(out, cam, t, HERO(), ...R([2.1, 0.08, -2.2]), "grin", { prop: ["note", q((t * 4) % 1, 12)] });
  const n = Math.min(9, Math.floor((t - T_HOME) * 4));
  if (n > 0) card(out, `books${n}`, 256, 256, (p) => fxBooks(p, n), ...R([1.55, 1.0, -1.5]), 0.4, 0.4);
  for (let k = 0; k < 5; k++) {
    const u = ((t - T_HOME) * 1.6 + k / 5) % 1;
    card(out, `paper${q(u * 3 + k, 8)}`, 128, 128, (p) => fxPaper(p, (u * 3 + k) % 1), ...R([2.1 - 0.6 * u, 1.0 + 0.6 * Math.sin(u * 3.1), -1.65 + 0.4 * u]), 0.2, 0.2, { rot: u * 7 + k });
  }
};
const race = (out: Stage, cam: CamInfo, t: number) => {
  const runners: [number, number, number][] = [[0.15, -1.1, 0.3], [-0.25, 0.25, 0.75], [0.35, 1.5, 0.55]];
  runners.forEach(([x, z, ph], i) => strider(out, cam, t, W(60 + i, KID_O[i]), ...Fd([x, 0, z]), 1, 0, ph, i === 1 ? "shock" : "stern", true));
  walk(out, cam, t, HERO(), ...([Fd([-1.0, 0, 0.8])[0], Fd([0, 0, 0.8])[2], Fd([1.8, 0, 0.8])[0], Fd([0, 0, 0.8])[2]] as [number, number, number, number]), T_RACE - 0.3, T_CAKE + 0.2, "whistle", 0);
};
const cakes = (out: Stage, cam: CamInfo, t: number) => {
  stand(out, cam, t, BAKER, ...at(STALL, [0.95, 0, -0.1]), "smile", { prop: ["hands", 0.6], blink: 0 });
  const bite = q(0.5 + 0.5 * Math.sin((t - T_CAKE) * 7), 8);
  stand(out, cam, t, HERO(), ...at(STALL, [-0.75, 0, 0.75]), bite > 0.7 ? "lick" : "grin", { prop: ["cake", bite] });
};
const BOARD_T: V3 = [0.75, 0, -3.3];
const moustache = (out: Stage, cam: CamInfo, t: number) => {
  stand(out, cam, t, TEACH(smooth((t - T_MOUST + 0.1) / 0.8), false), ...C(BOARD_T), "neutral", { prop: ["switch", 0.6], blink: 0 });
  stand(out, cam, t, HERO(), ...C([0.0, 0.45, -2.95]), "grin", { prop: ["pen", (t * 3) % 1] }, 1, false);
};
const HERO_DESK: V3 = [0, 0.05, 1.0];
const classmates = (out: Stage, cam: CamInfo, t: number, frozen: boolean) => {
  const seats: V3[] = [[-2.2, 0.05, 1.0], [2.2, 0.05, 1.0], [-2.2, 0.05, 2.8], [0, 0.05, 2.8], [2.2, 0.05, 2.8]];
  seats.forEach((s, i) => sit(out, cam, t, W(70 + i, FOLK_O[i % FOLK_O.length]), ...C(s), (["neutral", "whistle", "smile", "nervous", "neutral"] as Expr[])[i], frozen ? { blink: 0 } : {}, 0.95));
};
const test = (out: Stage, cam: CamInfo, t: number, f: number) => {
  classmates(out, cam, t, t > T_PAUSE2);
  const top = t > T_TOP - 0.15;
  (top ? stand : sit)(out, cam, t, HERO(), ...C(top ? [0, 0, 1.15] : HERO_DESK), top ? "relief_open" : t < T_PAUSE2 ? "shock" : "stern",
    { prop: top ? ["paper", smooth((t - T_TOP + 0.15) / 0.25)] : t < T_PAUSE2 - 0.1 ? ["hands", 0.7] : t < T_STUDY ? ["remote", t > T_PAUSE2 - 0.05 ? 1 : 0] : ["note", q((t * 5) % 1, 12)] });
  ring(out, t, C([0, 1.3, 1.0]), 2.0);
  if (t > T_STUDY && !top) {
    const n = Math.min(10, 1 + Math.floor((t - T_STUDY) * 12));
    card(out, `books${n}`, 256, 256, (p) => fxBooks(p, n), ...C([-0.55, 1.05, 0.75]), 0.5, 0.5);
    for (let k = 0; k < 6; k++) {
      const u = ((t - T_STUDY) * 2.2 + k / 6) % 1;
      card(out, `cal${k % 4}`, 256, 256, (p) => fxCalendar(p, k), ...C([0.6 - 1.2 * u + 0.2 * k, 1.6 + 0.7 * Math.sin(u * 3.1 + k), 0.9]), 0.26, 0.26, { rot: u * 5 + k });
    }
  }
  if (top) { const u = clamp01((t - T_TOP) / 0.6); card(out, `spark${q(u, 12)}`, 256, 256, (p) => fxSpark(p, u), ...C([0.0, 1.35, 0.95]), 0.8, 0.8); }
};
const late = (out: Stage, cam: CamInfo, t: number) => {
  street(out, cam, t, (x, z) => z > 22 && x < 0);
  const z = heroLateZ(t), running = t < T_PAUSE3 - 0.05;
  const phase = q((running ? t * 1.6 : t * 0.85) % 1, 60);
  out.places.push(person(cam, HERO(), -5.4, CURB, z, FRONT,
    { mode: "stroll", phase, expr: running ? "shock" : t > T_EARLY ? "smile_closed" : "whistle", blink: lidAt(t, 1), tilt: running ? 7 : 0, prop: t > T_PAUSE3 - 0.4 && t < T_STROLL ? ["remote", t > T_PAUSE3 - 0.05 ? 1 : 0] : null }, {}));
  blob(out, -5.4, CURB, z);
  ring(out, t, [-5.4, 1.3, z], 2.0);
  if (t > T_EARLY) { const u = clamp01((t - T_EARLY) / 0.6); card(out, `spark${q(u, 12)}`, 256, 256, (p) => fxSpark(p, u), -5.4, 1.9, z, 0.9, 0.9); }
};
const perfect = (out: Stage, cam: CamInfo, t: number) => sit(out, cam, t, HERO(), ...BED_SIT, t > T_WHILE + 0.2 ? "smile" : "smile_closed", { prop: ["lounge", 1] });
const MIRROR_AT: V3 = [1.1, 0, 1.2];
const mirror = (out: Stage, cam: CamInfo, t: number) => {
  const grey = t > T_GREY - 0.05;
  stand(out, cam, t, HERO(0.08), ...R(MIRROR_AT), grey ? (t > T_GREY + 0.35 ? "shock" : "neutral") : "neutral", { prop: grey && t > T_GREY + 0.35 ? ["brush", 0.6] : ["brush", t] }, 1, false);
  if (grey) { const u = clamp01((t - T_GREY) / 1.0); card(out, `hair${q(u, 20)}`, 128, 256, (p) => fxHair(p, u), ...R([MIRROR_AT[0] + 0.02, 1.76, MIRROR_AT[2] - 0.03]), 0.07, 0.14); }
};
const maths = (out: Stage, cam: CamInfo, t: number) => {
  const nerv = t > T_WERENT;
  stand(out, cam, t, HERO(0.15), ...S([0, 0, 0]), nerv ? "nervous" : "neutral", {});
  // frozen clocks all round him from "frozen"; his own clock behind him spins from "you weren't"
  const CL: V3[] = [[-1.6, 2.2, -0.6], [1.7, 2.4, -0.8], [-2.3, 1.1, -1.2], [2.4, 1.2, -1.4], [-0.9, 3.0, -1.6], [1.0, 3.2, -1.9]];
  CL.forEach((c, i) => {
    const pop = clamp01((t - T_FROZEN + 0.1 - 0.06 * i) * 5);
    if (pop > 0) card(out, `fclock${i}`, 256, 256, (p) => fxClock(p, (i * 0.13) % 1, (i * 0.37) % 1, 0, "#e8f4ff", "#7fb4e0"), ...S(c), 0.7 * pop, 0.7 * pop);
  });
  if (t > T_WERENT - 0.1) {
    const sp = (t - T_WERENT) * 1.5, pop = clamp01((t - T_WERENT + 0.1) * 5);
    card(out, `myclock${q(sp % 1, 24)}`, 256, 256, (p) => fxClock(p, (sp / 12) % 1, sp % 1, 0), ...S([0, 2.35, -0.3]), 0.9 * pop, 0.9 * pop);
  }
  // hourglasses: nine hours here, a week there
  const HG: [number, number][] = [[T_NINE, 0], [T_NINE + 0.25, 1], [T_WEEK, 2], [T_WEEK + 0.15, 3], [T_WEEK + 0.3, 4], [T_WEEK + 0.45, 5]];
  HG.forEach(([tk, i]) => {
    const pop = clamp01((t - tk) * 6);
    if (pop > 0) card(out, "hglass", 256, 256, (p) => fxHourglass(p, 1), ...S([0.9 + 0.45 * (i % 3), 0.32 + 0.62 * Math.floor(i / 3), 0.3]), 0.6 * pop, 0.6 * pop);
  });
};
const cake16 = (out: Stage, cam: CamInfo, t: number) => {
  const old = t > T_BODY - 0.1;
  stand(out, cam, t, HERO(old ? 0.38 : 0.15, old), ...S([0, 0, -0.2]), old ? "dazed" : "smile", { blink: old ? 0.45 : lidAt(t, 1) });
  if (!old) card(out, `cake16_${q(t % 1, 10)}`, 512, 512, (p) => fxCake16(p, t), ...S([0, 0.95, 0.9]), 1.1, 1.1);
};
const friends = (out: Stage, cam: CamInfo, t: number) => {
  sit(out, cam, t, HERO(0.4, true), ...C(HERO_DESK), "neutral", { blink: 0.45 });
  const lf = q(0.5 + 0.5 * Math.sin(t * 14), 4);
  stand(out, cam, t, W(80, FRIEND_O[0]), ...C([-0.95, 0, 1.35]), "laugh", { tilt: -4 + 6 * lf, prop: ["hands", lf] });
  stand(out, cam, t, W(81, FRIEND_O[1]), ...C([0.95, 0, 1.3]), "laugh", { tilt: 5 - 6 * lf, headTilt: 3 * lf });
};
const tired = (out: Stage, cam: CamInfo, t: number) => {
  mumDoor(out, cam, t, 15);
  stand(out, cam, t, HERO(0.5, true), ...R([-1.3, 0, 1.0]), "neutral", { blink: 0.5, tilt: -3 });
};
const stop = (out: Stage, cam: CamInfo, t: number) => {
  const drop = t > T_STOP + 0.35;
  stand(out, cam, t, HERO(0.5, true), ...R([1.15, 0, -1.0]), t > T_NOMORE ? "stern" : "neutral", { prop: drop ? null : ["remote", 0], blink: t > T_NOMORE ? lidAt(t, 1) : 0.4 });
  if (drop) {
    const u = clamp01((t - T_STOP - 0.35) / 0.45);
    if (u < 1) card(out, "remote", 256, 256, (p) => fxRemote(p, 0), ...R([1.45 + 0.4 * u, 1.25 - 0.5 * u * u, -1.15 - 0.5 * u]), 0.3, 0.3, { rot: 2 * u });
  }
};
// ---- the bus, the sister and the old man ----
const sisterAt = (t: number): V3 => {
  if (t < T_CARRY) { const u = clamp01((t - T_BUS) / (T_CLICK4 - T_BUS)); return [0.5 + (SIS_AT[0] - 0.5) * u, 0, SIS_AT[2]]; }
  return SIS_AT;
};
const sister = (out: Stage, cam: CamInfo, t: number) => {
  if (t < T_CARRY + 0.05) {
    const p = sisterAt(t);
    if (frozenAt(t)) strider(out, cam, t, SIS, p[0], 0, p[2], -1, 0, 0.3, "lick");
    else walk(out, cam, t, SIS, 0.5, SIS_AT[2], SIS_AT[0], SIS_AT[2], T_BUS, T_CLICK4, "lick", 0, false, { prop: "icecream" });
  } else if (t < T_CARRY + 1.2) return; // carried: drawn with him
  else strider(out, cam, t, SIS, SIS_SAFE[0], CURB, SIS_SAFE[2], -1, 0, 0.3, "lick");
};
const heroStreet = (out: Stage, cam: CamInfo, t: number) => {
  const H = HERO(0.55, true);
  if (t < T_RUN) { stand(out, cam, t, H, ...HERO_HOME, t > T_CLICK4 - 0.6 ? "shock" : "neutral", { prop: ["remote", t > T_CLICK4 - 0.04 ? 1 : 0] }); return; }
  if (t < T_CARRY) { walk(out, cam, t, H, HERO_HOME[0], HERO_HOME[2], SIS_AT[0] - 0.35, SIS_AT[2] + 0.2, T_RUN, T_CARRY, "stern", 0, true); return; }
  const u = clamp01((t - T_CARRY - 0.1) / 1.1), x = SIS_AT[0] - 0.35 + (SIS_SAFE[0] + 0.55 - SIS_AT[0] + 0.35) * u, z = SIS_AT[2] + 0.2 + (SIS_SAFE[2] + 0.35 - SIS_AT[2] - 0.2) * u;
  if (u < 1) {
    out.places.push(person(cam, H, x, u > 0.85 ? CURB : 0, z, FRONT, { mode: "stroll", phase: q((t * 1.8) % 1, 60), expr: "stern", blink: lidAt(t, 1), prop: ["carry", 1] }, {}));
    blob(out, x, 0, z);
    const sp = person(cam, SIS, x, (u > 0.85 ? CURB : 0) + 0.62, z, FRONT, { mode: "stroll", phase: 0.3, expr: "lick", blink: 0, prop: "icecream" }, {}, 0.95);
    // a little toward the lens so she sits in his arms
    const dx = cam.pos.x - x, dz = cam.pos.z - z, l = Math.hypot(dx, dz) || 1;
    out.places.push({ ...sp, x: x + (dx / l) * 0.12, z: z + (dz / l) * 0.12, roll: -1.25 });
  } else stand(out, cam, t, H, SIS_SAFE[0] + 0.55, CURB, SIS_SAFE[2] + 0.35, t > T_MOVING + 0.25 ? "shock" : "relief", {});
};
const OLD_END: V3 = [-4.5, CURB, 3.7];
const oldMan = (out: Stage, cam: CamInfo, t: number, id: number) => {
  const M = TEACH(1, true);
  if (id === 26) {
    const pt = clamp01((t - T_POINT + 0.1) / 0.3), rm = t > T_UNPAUSE - 0.6;
    stand(out, cam, t, M, ...OLD_END, t > T_SAW - 0.05 ? "stern" : "smile", { prop: rm ? ["remote", t > T_UNPAUSE - 0.04 ? 1 : 0] : t > T_POINT - 0.1 ? ["point", pt] : null, tilt: 4 });
    return;
  }
  const p = oldAt(t), moving = (t > T_MOVING - 0.4 && t < T_DRAWN - 0.3) || (t > 57.0 && t < 58.6);
  if (moving) {
    const p2 = oldAt(t + 0.05), dx = p2[0] - p[0], dz = p2[2] - p[2], l = Math.hypot(dx, dz) || 1;
    const view = viewOf(cam, p[0], p[2], dx / l, dz / l);
    const phase = q((t * 0.8) % 1, 60);
    out.places.push(person(cam, M, p[0], p[1], p[2], view, { mode: "stroll", phase, expr: "smile", blink: lidAt(t, 6), tilt: 5 },
      { mode: "march", phase, expr: "smile", stomp: 0.4, stride: 0.7 * Math.max(0.35, view.fs), blink: lidAt(t, 6) }));
    blob(out, p[0], p[1], p[2]);
  } else stand(out, cam, t, M, ...p, t > T_WRINK ? "smile" : "neutral", { tilt: 4 });
};

/** everything with a face (and every drawn effect) in shot `id` at time t */
export const stage = (id: number, t: number, cam: CamInfo): Stage => {
  const out: Stage = { places: [], fx: [] };
  const s = SHOTS[id - 1];
  LNAME = s.light;
  findSun(cam, SUN);
  if (id === 1) hook(out, cam, t);
  if (id === 2) bedroom(out, cam, t);
  if (id === 3) { mumDoor(out, cam, t, 3); lie(out, cam, t, HERO(), ...BED_FEET, "whistle", { blink: 1 }); }
  if (id === 4) homework(out, cam, t);
  if (id === 5) race(out, cam, t);
  if (id === 6) { cakes(out, cam, t); street(out, cam, t, (x, z) => z < -2 && z > -30); }
  if (id === 7 || id === 24) {
    if (id === 7) moustache(out, cam, t);
    else stand(out, cam, t, TEACH(1, false), ...C(BOARD_T), "neutral", { prop: ["switch", 0.6], blink: 0 });
  }
  if (id === 8) test(out, cam, t, Math.round(t * FPS));
  if (id === 9) late(out, cam, t);
  if (id === 10) perfect(out, cam, t);
  if (id === 11) mirror(out, cam, t);
  if (id === 12) maths(out, cam, t);
  if (id === 13) cake16(out, cam, t);
  if (id === 14) { friends(out, cam, t); classmates(out, cam, t, false); }
  if (id === 15) tired(out, cam, t);
  if (id === 16) stop(out, cam, t);
  if (id >= 17) {
    street(out, cam, t, (x, z) => z < 18 && z > -12);
    sister(out, cam, t);
    heroStreet(out, cam, t);
    if (id >= 21) oldMan(out, cam, t, id);
    if (id === 19) ring(out, t, at(HERO_HOME, [0, 1.4, 0]), 2.4);
    if (id === 26) ring(out, t, at(OLD_END, [0, 1.4, 0]), 2.4);
  }
  return out;
};
export { FPS, INK };
