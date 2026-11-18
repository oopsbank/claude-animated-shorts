// Our cast as lit flat sprites in the 3D world. Each frame every character asks for a drawing (a key + a draw call);
// the pool keeps one canvas per distinct drawing, so soldiers marching in step share canvases (7 head shapes x 4
// outfits). Characters are yaw-only billboards shaded by cardShade() (scene tint, bright floor, side gradient toward
// the sun, painted crescent in the drawing); standing ones get a soft multiply contact blob. Effects are unlit cards.
// Cards, effects and blobs live on the NOINK layer so the world ink pass never outlines their quads.
import * as THREE from "three";
import {
  Pen, bodyFront, bodySide, fxBurst, fxStars, fxCreak, fxShadow, fxContact, Outfit, Expr, FrontOpts, SideOpts,
  GEORGE_O, BOSS_O, JUDGE_O, OFFICIAL_O, worker, resident, fxBeerSplash, fxSpurt, fxFoam, fxArrow, fxBelt, fxCoins, fxSweat, fxSheet, fxBucket, bagAt,
} from "./toon";
import {
  FPS, V3, SHOTS, smooth, clamp01, TB, T_WALL, TW, T_SLIP, T_NOTICE, T_WRITE, T_FINE, T_POP, T_GAVEL, T_BLAME, T_HAND, T_SEVEN, T_FALL, T_RUN,
  VATS, GEORGE, BOSS, EXP, TABLE, BENCH, STREET, WALL_T, beerDepth, vatState,
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
const WORKERS = [0, 1, 2, 3].map((v) => worker(v));
const RESIDENTS = [0, 1, 2, 3].map((v) => resident(v));
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

// ---------------- our cast by shot ----------------
export type Stage = { places: Place[]; fx: FxPlace[] };
const GEO: Who = { i: 1, o: GEORGE_O, okey: "geo" };
const BOSSW: Who = { i: 2, o: BOSS_O, okey: "boss" };
const JUDGE: Who = { i: 3, o: JUDGE_O, okey: "judge" };
const OFFICIAL: Who = { i: 4, o: OFFICIAL_O, okey: "off" };
const wk = (k: number): Who => ({ i: 10 + k, o: WORKERS[k % 4], okey: `w${k % 4}` });
const rs = (k: number): Who => ({ i: 20 + k, o: RESIDENTS[k % 4], okey: `r${k % 4}` });
const FRONT = { side: false, mirror: false };
const LEAD_S = 2 / FPS;
/** a standing figure facing the camera */
const stand = (out: Stage, cam: CamInfo, t: number, who: Who, x: number, y: number, z: number, expr: Expr, extra: Partial<FrontOpts> = {}, scale = 1, shadow = true) => {
  out.places.push(person(cam, who, x, y, z, FRONT, { mode: "stand", expr, blink: lidAt(t, who.i), ...extra }, {}, scale));
  if (shadow) blob(out, x, y, z, scale);
};
/** a walking / running figure from (x0, z0) toward (x1, z1) between t0 and t1 (stride from the speed) */
const walk = (out: Stage, cam: CamInfo, t: number, who: Who, x0: number, z0: number, x1: number, z1: number, t0: number, t1: number, expr: Expr, run = false) => {
  const u = clamp01((t - t0) / (t1 - t0)), x = x0 + (x1 - x0) * u, z = z0 + (z1 - z0) * u;
  const L = Math.hypot(x1 - x0, z1 - z0) || 1, dx = (x1 - x0) / L, dz = (z1 - z0) / L, speed = L / (t1 - t0);
  const moving = t > t0 && t < t1;
  const cad = run ? 3.2 : 1.7; // steps per second
  const phase = moving ? q(((t - t0) * cad / 2) % 1, 120) : 0;
  const view = viewOf(cam, x, z, dx, dz);
  const so: SideOpts = { mode: moving ? "march" : "stand", phase, expr, stomp: run ? 1.3 : 0.6, stride: Math.min(1.6, (speed / cad / 0.8) * 2) * view.fs, blink: lidAt(t, who.i) };
  const fo: FrontOpts = { mode: moving ? "stroll" : "stand", phase, expr, blink: lidAt(t, who.i), tilt: run && moving ? 6 : 0 };
  out.places.push(person(cam, who, x, 0, z, moving ? view : FRONT, fo, so));
  blob(out, x, 0, z);
};
const card = (out: Stage, key: string, cw: number, ch: number, draw: (p: Pen) => void, x: number, y: number, z: number, w: number, h: number, o: Partial<FxPlace> = {}) =>
  out.fx.push({ key, cw, ch, draw, x, y, z, w, h, ...o });

// ---- yard life before the burst ----
const yardCrew = (out: Stage, cam: CamInfo, t: number, id: number) => {
  // a worker crossing the yard, two at the far vats, George at his office door
  walk(out, cam, t, wk(0), -7, -3.5, 7, -4.5, 3.6, 11.6, "neutral");
  stand(out, cam, t, wk(1), VATS[1].x + 2.6, 0, VATS[1].z + 2.4, "smile_closed");
  stand(out, cam, t, wk(2), VATS[2].x - 2.9, 0, VATS[2].z + 2.2, "neutral", { look: -1 });
  if (id === 2 || id === 3) stand(out, cam, t, GEO, -7.0, 0, -9.0, "neutral");
};

const georgeNotices = (out: Stage, cam: CamInfo, t: number) => {
  const expr: Expr = t < T_NOTICE - LEAD_S ? "smile_closed" : t < 15.95 ? "nervous" : "shock";
  if (t <= T_NOTICE - 0.1) walk(out, cam, t, GEO, GEORGE[0] + 4.0, GEORGE[2] + 0.4, GEORGE[0], GEORGE[2], 12.6, T_NOTICE - 0.1, expr);
  else stand(out, cam, t, GEO, GEORGE[0], 0, GEORGE[2], expr, { headTilt: -8, look: -1 });
};

const writing = (out: Stage, cam: CamInfo, t: number) =>
  stand(out, cam, t, GEO, GEORGE[0], 0, GEORGE[2], "neutral", { prop: ["note", q((t * 1.7) % 1, 12)], headTilt: 6 });

const toldFine = (out: Stage, cam: CamInfo, t: number) => {
  const waving = t > 19.5 && t < 20.6;
  stand(out, cam, t, BOSSW, BOSS[0], 0, BOSS[2], t < 19.45 ? "neutral" : "smile_closed", waving ? { wave: q(Math.sin(t * 11), 20) } : {});
  stand(out, cam, t, GEO, BOSS[0] + 1.9, 0, BOSS[2] - 0.9, t < T_FINE ? "nervous" : "pained", { prop: ["note", 0] });
};

// ---- the burst ----
const vatTop = (i: number): V3 => [VATS[i].x, VATS[i].h, VATS[i].z];
const burstFx = (out: Stage, i: number, tau: number) => {
  const v = VATS[i], tb = TB[v.burst!];
  const u = (tau - tb) / 1.3;
  if (u >= 0 && u < 1) {
    for (let k = 0; k < 6; k++) {
      const a = (k / 6) * Math.PI * 2 + 0.4, R = v.r + 1.2;
      card(out, `bsplash${k % 3}|${q(u, 30)}`, 800, 800, (p) => fxBeerSplash(p, q(u, 30), k % 3), v.x + Math.cos(a) * R, 0, v.z + Math.sin(a) * R, 5.5, 5.5);
      const last = out.fx[out.fx.length - 1]; last.y = 5.5 / 2 - 0.25;
    }
    const ub = clamp01((tau - tb) / 0.35);
    if (ub < 1) card(out, `burst${q(ub, 30)}`, 500, 500, (p) => fxBurst(p, q(ub, 30), "#f6e2b0", 12), v.x, v.h * 0.5, v.z + v.r + 0.3, 7, 7);
  }
};
const creaks = (out: Stage, i: number, t: number, n = 3) => {
  const v = VATS[i];
  for (let k = 0; k < n; k++) {
    const u = q((t * 1.4 + k * 0.37) % 1, 30), a = -0.9 + k * 0.9;
    card(out, `creak${u}`, 300, 300, (p) => fxCreak(p, u), v.x + Math.sin(a) * (v.r + 0.4), v.hoops[k + 2] + 0.1, v.z + Math.cos(a) * (v.r + 0.4), 1.1, 1.1, { rot: k * 0.6 - 0.6 });
  }
};
const spurts = (out: Stage, i: number, t: number, t0: number) => {
  const v = VATS[i];
  for (let k = 0; k < 3; k++) {
    const u = clamp01((t - t0 - k * 0.12) / 0.5);
    if (u <= 0) continue;
    const a = -0.6 + k * 0.6, y = 1.2 + k * 1.1;
    card(out, `spurt${q(u, 20)}`, 500, 260, (p) => fxSpurt(p, q(u, 20)), v.x + Math.sin(a) * (v.r + 0.9), y, v.z + Math.cos(a) * (v.r + 0.9), 2.0, 1.04, { rot: k % 2 ? 0.2 : -0.1 });
  }
};

// ---- the street ----
export const BALCONIES: V3[] = [[-STREET.x1 - 0.65, 3.0, 22], [STREET.x1 + 0.65, 3.0, 17.5], [-STREET.x1 - 0.65, 3.0, 13]];
export const CELLAR: V3 = [STREET.x1 + 0.02, 0, 36.0]; // the cellar window of shot 13c (right-hand house front)
const zFront = (tau: number) => (tau < TW ? -99 : WALL_T + 6.6 * (tau - TW) ** 0.95);
const streetLife = (out: Stage, cam: CamInfo, t: number, tau: number, id: number) => {
  // laundry across the street
  // foam riding the wave front
  const zf = zFront(tau);
  if (zf > 1 && zf < 70) for (let k = 0; k < 5; k++) {
    const x = -3.4 + k * 1.7, s = q((t * 2 + k * 0.3) % 1, 6);
    card(out, `foam${s}`, 500, 260, (p) => fxFoam(p, s * 10 + k), x, beerDepth(x, zf - 0.6, tau) + 0.15, zf - 0.4, 2.2, 1.15);
  }
  // brown splashes breaking on the crest
  if (id === 1 && zf > 3 && zf < 60) for (let k = 0; k < 3; k++) {
    const u = q(((t * 1.3 + k * 0.33) % 1) * 0.8 + 0.1, 15), x = -2.6 + k * 2.6;
    card(out, `bsplash${k}|${u}`, 800, 800, (p) => fxBeerSplash(p, u, k), x, beerDepth(x, zf - 1.2, tau) - 0.3 + 1.6, zf - 0.6, 3.4, 3.4);
  }
  // a bucket riding the beer
  if (tau > TW + 1.5) {
    const bz = Math.min(zf - 2.5, 30 + 0.4 * (tau - TW)), bx = 1.4;
    card(out, "bucket", 300, 300, fxBucket, bx, beerDepth(bx, bz, tau) + 0.18 + 0.05 * Math.sin(t * 2.3), bz, 0.75, 0.75, { rot: 0.2 * Math.sin(t * 1.7) });
  }
  if (id === 13) BALCONIES.forEach(([x, y, z], k) => {
    const passed = zf > z - 2;
    stand(out, cam, t, rs(k), x + (x < 0 ? -0.25 : 0.25), y, z, passed ? (k === 1 ? "shock" : "nervous") : "neutral", passed ? { prop: ["hands", 0.8] } : {}, 1, false);
  });
};
const breachFx = (out: Stage, tau: number) => {
  const u = (tau - TW) / 1.6;
  if (u >= 0 && u < 1) for (let k = 0; k < 4; k++)
    card(out, `bsplash${k % 3}|${q(u, 30)}`, 800, 800, (p) => fxBeerSplash(p, q(u, 30), k % 3), -3 + k * 2, 2.6, 1.6, 6, 6);
};
const cellarFx = (out: Stage, t: number) => {
  // beer pouring over the sill into the cellar window
  for (let k = 0; k < 3; k++) {
    const u = q((t * 1.6 + k * 0.33) % 1, 12);
    card(out, `pour${u}`, 500, 260, (p) => fxSpurt(p, 0.35 + 0.3 * u), CELLAR[0] - 0.25, 0.75 - 0.08 * k, CELLAR[2] - 0.5 + k * 0.45, 1.1, 0.6, { rot: -0.9 });
  }
};

// ---- explanation ----
const ARROW_Y = [5.0, 3.85, 2.7, 1.55, 0.6];
const BEER_TOP = 5.7;
const arrows = (out: Stage, t: number) => {
  const g = smooth((t - 39.25) / 0.45) * (0.4 + 0.6 * smooth((t - 40.25) / 0.9)) * (1 + 0.15 * smooth((t - 41.0) / 0.5));
  if (g <= 0.01) return;
  for (const y of ARROW_Y) {
    const L = q(g * (BEER_TOP - y) / BEER_TOP + 0.08 * g, 30);
    for (const s of [-1, 1]) {
      const w = 0.5 + 2.0 * L;
      card(out, `arrow${L}`, 600, 160, (p) => fxArrow(p, L), EXP[0] + s * (0.4 + w / 2), y, EXP[2] + 3.05, w, w * (160 / 600), { rot: s < 0 ? Math.PI : 0 });
    }
  }
};

// ---- dinner, court ----
const forkK = (t: number) => q(0.5 - 0.5 * Math.cos(t * 4.2), 10);
const dinner = (out: Stage, cam: CamInfo, t: number, id: number) => {
  const popped = t >= T_POP;
  const expr: Expr = popped ? "shock" : t > 44.3 ? "nervous" : "grin";
  stand(out, cam, t, BOSSW, TABLE[0], 0.42, TABLE[2] - 0.75, expr, popped ? { prop: ["hands", 0.9] } : { prop: ["fork", forkK(t)] }, 1, false);
  if (id === 17 && t < T_POP + 0.1) {
    const notch = q(smooth((t - 44.36) / 0.3), 15), strain = 0;
    card(out, `belt${notch}|0`, 1000, 700, (p) => fxBelt(p, notch, strain), TABLE[0], 0.98, TABLE[2] + 0.35, 1.25, 0.875);
  }
  if (popped && t < T_POP + 0.5) {
    const u = q((t - T_POP) / 0.5, 15);
    card(out, `belt1|${u}`, 1000, 700, (p) => fxBelt(p, 1, Math.max(0.01, u)), TABLE[0], 0.98, TABLE[2] + 0.35, 1.25, 0.875);
    card(out, `burst${q(u, 15)}`, 500, 500, (p) => fxBurst(p, q(u, 15)), TABLE[0] + 0.3, 1.1, TABLE[2] + 0.45, 1.3, 1.3);
  }
};
const hammerK = (t: number) => {
  let k = 1;
  for (const th of [T_GAVEL, T_BLAME]) {
    const n = (t - th) * FPS;
    if (n >= -11 && n < -7) k = Math.min(k, 1 - smooth((n + 11) / 4));
    else if (n >= -7 && n < 0) k = 0;
  }
  return k;
};
const court = (out: Stage, cam: CamInfo, t: number, id: number) => {
  stand(out, cam, t, JUDGE, BENCH[0], 1.3, BENCH[2] - 0.2, "stern", { prop: ["hammer", q(hammerK(t), 30)] }, 1, false);
  for (const th of [T_GAVEL, T_BLAME]) if (t >= th && t < th + 5 / FPS) {
    const u = q((t - th) / (5 / FPS), 30);
    card(out, `burst${u}`, 500, 500, (p) => fxBurst(p, u), BENCH[0] + 0.6, 2.25, BENCH[2] + 0.9, 0.9, 0.9);
  }
  const bx = BENCH[0] + 0.9, bz = BENCH[2] + 3.3;
  if (id === 18) {
    stand(out, cam, t, BOSSW, BENCH[0] - 1.0, 0, BENCH[2] + 2.6, t < 49.1 ? "nervous" : "grin");
    stand(out, cam, t, GEO, BENCH[0] + 1.25, 0, BENCH[2] + 2.9, t < 49.1 ? "neutral" : "pained");
  } else {
    const got = t >= T_HAND + 0.15;
    const offExpr: Expr = t < 54.15 ? "smile_closed" : "nervous";
    stand(out, cam, t, OFFICIAL, BENCH[0] - 1.45, 0, BENCH[2] + 3.4, offExpr, got ? {} : { prop: ["bag", q(smooth((t - 51.2) / 0.6), 20)] });
    stand(out, cam, t, BOSSW, bx, 0, bz, got ? "laugh" : t > 50.9 ? "grin" : "smile_closed", got ? { prop: ["bag", 1] } : { prop: ["hands", q(smooth((t - 51.4) / 0.5), 10)] });
    if (id === 20 && t < 55.6) for (let k = 0; k < 2; k++) {
      const u = (t * 0.8 + k * 0.5) % 1;
      card(out, "sweat", 200, 180, fxSweat, BENCH[0] - 1.45 + (k ? 0.32 : -0.3), 1.95 - 0.25 * u, BENCH[2] + 3.55, 0.13, 0.12);
    }
    if (id === 20) {
      const n = Math.round(4 + 26 * smooth((t - T_SEVEN + 0.1) / 0.9));
      card(out, `coins${n}`, 600, 400, (p) => fxCoins(p, n), bx + 0.35, 0.95, bz + 0.25, 0.9, 0.6);
    }
  }
};

// ---- the lesson ----
const lesson = (out: Stage, cam: CamInfo, t: number, id: number) => {
  const shocked = t > T_FALL + 0.2;
  const v = VATS[0];
  if (t < T_RUN) {
    stand(out, cam, t, GEO, GEORGE[0], 0, GEORGE[2], shocked ? "shock" : "smile_closed", shocked ? { prop: ["hands", 1] } : {});
    stand(out, cam, t, BOSSW, GEORGE[0] - 1.3, 0, GEORGE[2] - 0.2, shocked ? "shock" : "grin");
    stand(out, cam, t, wk(0), 0.6, 0, -6.6, shocked ? "shock" : "smile");
    stand(out, cam, t, wk(1), -1.6, 0, -8.0, shocked ? "nervous" : "neutral");
  } else {
    // everybody runs for it (to screen right, out of the yard)
    walk(out, cam, t, GEO, GEORGE[0], GEORGE[2], GEORGE[0] + 14, GEORGE[2] + 4.5, T_RUN, T_RUN + 2.4, "shock", true);
    walk(out, cam, t, BOSSW, GEORGE[0] - 1.3, GEORGE[2] - 0.2, GEORGE[0] + 11, GEORGE[2] + 4.5, T_RUN + 0.08, T_RUN + 3.0, "shock", true);
    walk(out, cam, t, wk(0), 0.6, -6.6, 15, -2, T_RUN + 0.04, T_RUN + 2.2, "shock", true);
    walk(out, cam, t, wk(1), -1.6, -8.0, 12, -2.5, T_RUN + 0.12, T_RUN + 2.6, "nervous", true);
  }
  if (id === 22 && t >= T_FALL + 0.3 && t < T_FALL + 0.6) {
    const u = q((t - T_FALL - 0.3) / 0.3, 15);
    card(out, `burst${u}`, 500, 500, (p) => fxBurst(p, u, "#fff3b0", 10), v.x + 0.6, 0.35, v.z + v.r + 0.6, 1.6, 1.6);
  }
};

/** everything with a face (and every drawn effect) in shot `id` at time t */
export const stage = (id: number, t: number, tau: number, cam: CamInfo): Stage => {
  const out: Stage = { places: [], fx: [] };
  const s = SHOTS[id - 1];
  LNAME = s.light;
  findSun(cam, SUN);
  if (id >= 2 && id <= 4) yardCrew(out, cam, t, id);
  if (id === 4 && t < 10.7) stand(out, cam, t, wk(3), VATS[0].x + 2.2, 0, VATS[0].z + VATS[0].r + 1.0, "neutral", { look: -1 });
  if (id === 5) georgeNotices(out, cam, t);
  if (id === 7) writing(out, cam, t);
  if (id === 8) toldFine(out, cam, t);
  if (id === 9) { creaks(out, 0, t); spurts(out, 0, t, 21.15); }
  if (id >= 9 && id <= 11) for (const i of [0, 1, 2]) burstFx(out, i, tau);
  if (id === 10 && tau > 22.2 && tau < TB[1]) creaks(out, 1, t, 2);
  if (id === 11 && tau < TB[2]) creaks(out, 2, t, 2);
  if (s.place === "street") { streetLife(out, cam, t, tau, id); breachFx(out, tau); }
  if (id === 13 && t > 30.85) cellarFx(out, t);
  if (id === 15) arrows(out, t);
  if (id === 16 || id === 17) dinner(out, cam, t, id);
  if (id >= 18 && id <= 20) court(out, cam, t, id);
  if (id >= 21) lesson(out, cam, t, id);
  return out;
};
export { FPS, bagAt, vatTop };
