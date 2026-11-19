// Our cast as lit flat sprites in the 3D world (the bridge / beer-flood machinery: canvas pool, lit cards, unlit
// effect cards, contact blobs), staged for "What If Your Plane's Windscreen Blew Out?".
import * as THREE from "three";
import {
  Pen, bodyFront, bodySide, fxBurst, fxShadow, fxContact, fxPuff, fxArrow, fxSweat, Outfit, Expr, FrontOpts, SideOpts,
  fxWind, fxPaper, fxMist, fxCross, fxTick, legsUp, fxFlake, fxDot, INK,
} from "./toon";
import {
  FPS, V3, SHOTS, clamp01, smooth, CAPT, FO, FLOOR, GROUND, PANE_C, ENGINE_L, WARD, CUT, MGR,
  T_HOOK, T_BLOW, T_SUCK, T_ROOF, T_STEW, T_GRAB, T_TIRE, T_TAKE, T_DEAD, T_ENGINE, T_TD, T_ALIVE, T_THUMB,
  T_MATCH, T_WRONG, T_PUSH, T_HARD, T_FAIL, T_OFF, planePose,
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
const NAVY = "#25304f", WHITE_SHIRT = "#eef1f5";
const CAPTAIN_O: Outfit = { jacket: NAVY, pants: "#262d45", boots: "#16171b", hat: "pilot", buttons: "#e8c45a", skin: "#ffe2c2" };
const FO_O: Outfit = { jacket: NAVY, pants: "#262d45", boots: "#16171b", hat: "pilot", buttons: "#e8c45a", skin: "#f5c9a0" };
const STEW_O: Outfit = { jacket: WHITE_SHIRT, pants: "#2b3350", boots: "#16171b", hat: "hair", hair: "#6a4a2e", buttons: "#c9ccd2", skin: "#ffe2c2" };
const CREW2_O: Outfit = { jacket: WHITE_SHIRT, pants: "#2b3350", boots: "#16171b", hat: "hair", hair: "#2e2a2a", buttons: "#c9ccd2", skin: "#ecd0b6" };
const CREW3_O: Outfit = { jacket: "#b7243a", pants: "#2b3350", boots: "#16171b", hat: "hair", hair: "#c9a050", buttons: "#f1efe6", skin: "#ffe2c2" };
const MGR_O: Outfit = { jacket: "#3d5f96", pants: "#3d5f96", boots: "#3a2a22", hat: "hair", hair: "#7a7470", buttons: "#c9ccd2", build: "stout", skin: "#f5c9a0" };
const PAX_O: Outfit[] = [
  { jacket: "#d9a441", pants: "#3b3f52", boots: "#3a2a22", hat: "hair", hair: "#5a3b2a" },
  { jacket: "#5a8fc2", pants: "#3b3f52", boots: "#3a2a22", hat: "hair", hair: "#2e2a2a", skin: "#c99067" },
  { jacket: "#c25a7a", pants: "#3b3f52", boots: "#3a2a22", hat: "hair", hair: "#c9a050" },
  { jacket: "#4f9a6a", pants: "#3b3f52", boots: "#3a2a22", hat: "hair", hair: "#8a5a3a", skin: "#ecd0b6" },
  { jacket: "#e07a3a", pants: "#3b3f52", boots: "#3a2a22", hat: "hair", hair: "#3a2a22", skin: "#f5c9a0" },
  { jacket: "#7b5ac9", pants: "#3b3f52", boots: "#3a2a22", hat: "hair", hair: "#e8d6a0" },
];
const CAPTAIN: Who = { i: 1, o: CAPTAIN_O, okey: "capt" };
const FOW: Who = { i: 2, o: FO_O, okey: "fo" };
const STEW: Who = { i: 3, o: STEW_O, okey: "stew" };
const CREW2: Who = { i: 4, o: CREW2_O, okey: "crew2" };
const CREW3: Who = { i: 5, o: CREW3_O, okey: "crew3" };
const MANAGER: Who = { i: 6, o: MGR_O, okey: "mgr" };
const pax = (k: number): Who => ({ i: 20 + k, o: PAX_O[k % PAX_O.length], okey: `pax${k % PAX_O.length}` });
const FRONT = { side: false, mirror: false };

const stand = (out: Stage, cam: CamInfo, t: number, who: Who, x: number, y: number, z: number, expr: Expr, extra: Partial<FrontOpts> = {}, scale = 1, shadow = true) => {
  out.places.push(person(cam, who, x, y, z, FRONT, { mode: "stand", expr, blink: lidAt(t, who.i), ...extra }, {}, scale));
  if (shadow) blob(out, x, y, z, scale);
};
const sit = (out: Stage, cam: CamInfo, t: number, who: Who, x: number, y: number, z: number, expr: Expr, extra: Partial<FrontOpts> = {}, scale = 1) =>
  out.places.push(person(cam, who, x, y, z, FRONT, { mode: "sit", expr, blink: lidAt(t, who.i), ...extra }, {}, scale));
const walk = (out: Stage, cam: CamInfo, t: number, who: Who, x0: number, z0: number, x1: number, z1: number, t0: number, t1: number, expr: Expr, y = 0, run = false) => {
  const u = clamp01((t - t0) / (t1 - t0)), x = x0 + (x1 - x0) * u, z = z0 + (z1 - z0) * u;
  const L = Math.hypot(x1 - x0, z1 - z0) || 1, dx = (x1 - x0) / L, dz = (z1 - z0) / L, speed = L / (t1 - t0);
  const moving = t > t0 && t < t1;
  const cad = run ? 3.2 : 1.7;
  const phase = moving ? q(((t - t0) * cad / 2) % 1, 120) : 0;
  const view = viewOf(cam, x, z, dx, dz);
  const so: SideOpts = { mode: moving ? "march" : "stand", phase, expr, stomp: run ? 1.3 : 0.6, stride: Math.min(1.6, (speed / cad / 0.8) * 2) * view.fs, blink: lidAt(t, who.i) };
  const fo: FrontOpts = { mode: moving ? "stroll" : "stand", phase, expr, blink: lidAt(t, who.i), tilt: run && moving ? 6 : 0 };
  out.places.push(person(cam, who, x, y, z, moving ? view : FRONT, fo, so));
  blob(out, x, y, z);
};
const card = (out: Stage, key: string, cw: number, ch: number, draw: (p: Pen) => void, x: number, y: number, z: number, w: number, h: number, o: Partial<FxPlace> = {}) =>
  out.fx.push({ key, cw, ch, draw, x, y, z, w, h, ...o });

// ---- the wind through the open window: streaks, tumbling papers, the decompression mist ----
const gale = (out: Stage, t: number, inside: boolean, n = 3) => {
  if (t < T_BLOW) return;
  const s = t - T_BLOW;
  if (inside) {
    // mist: a burst of white right after the blow-out, thinning
    if (s < 2.2) for (let k = 0; k < 4; k++) {
      const u = s / 2.2;
      card(out, `mist${k}`, 256, 256, (p) => fxMist(p, k), -0.3 + 0.35 * k - 0.2, 0.5 + 0.15 * k, -12.2 + 0.3 * k + u * 1.5, 1.6 + u * 1.2, 1.6 + u * 1.2, { soft: true });
    }
    // papers sucked toward the window
    for (let k = 0; k < 6; k++) {
      const u = ((s * 0.9 + k / 6) % 1), x0 = 0.6 - 0.25 * k, z0 = -10.6 + 0.1 * k;
      const x = x0 + (PANE_C[0] - x0) * u ** 1.5, y = FLOOR + 0.6 + (PANE_C[1] - FLOOR - 0.6) * u ** 1.2 + 0.15 * Math.sin(k + s * 5), z = z0 + (PANE_C[2] - z0) * u ** 1.5;
      card(out, `paper${q(u * 3 + k, 8)}`, 128, 128, (p) => fxPaper(p, (u * 3 + k) % 1), x, y, z, 0.22, 0.22, { rot: s * 7 + k });
    }
  }
  for (let k = 0; k < n; k++) {
    const ph = q((t * 2.2 + k * 0.37) % 1, 20);
    card(out, `wind${k % 3}|${ph}`, 512, 256, (p) => fxWind(p, ph, k), inside ? -0.4 + 0.3 * k : -1.0 + 0.4 * k, inside ? 0.7 + 0.2 * k : 1.9 + 0.3 * k, inside ? -12.3 + 0.4 * k : -11.5 + 1.6 * k, inside ? 1.2 : 2.6, inside ? 0.6 : 1.3, { soft: true });
  }
};

// ---- the captain's ride out of the window ----
const captainOut = (out: Stage, cam: CamInfo, t: number, id: number) => {
  if (t < T_SUCK) { // still in his seat, being dragged at
    sit(out, cam, t, CAPTAIN, CAPT[0], CAPT[1] - 0.2 + 0.05, CAPT[2], "shock", { prop: ["grab", 0.4] });
    return;
  }
  const u = smooth((t - T_SUCK) / (T_ROOF - T_SUCK));
  // feet: seat -> through the window -> hooked at the aft edge of the frame; the card pivots on the feet and swings
  // back along the roof (screen right in the side views)
  const a = smooth(u * 1.6);
  const E = ROOF_FEET;
  const x = CAPT[0] + (E[0] - CAPT[0]) * a, y = CAPT[1] + (E[1] - CAPT[1]) * a, z = CAPT[2] + (E[2] - CAPT[2]) * a;
  const roll = ROOF_ROLL * smooth((u - 0.25) / 0.75) + 0.06 * Math.sin(t * 9);
  const p = person(cam, CAPTAIN, x, y, z, FRONT, { mode: "fall", expr: "shock", blink: 0 }, {}, 1);
  out.places.push({ ...p, roll });
};
const ROOF_FEET: V3 = [-0.62, 1.32, -12.45], ROOF_ROLL = -1.2;
const captainOnRoof = (out: Stage, cam: CamInfo, t: number, roll = ROOF_ROLL) => {
  const p = person(cam, CAPTAIN, ROOF_FEET[0], ROOF_FEET[1], ROOF_FEET[2], FRONT, { mode: "fall", expr: "dazed", blink: 1 }, {}, 1);
  out.places.push({ ...p, roll: roll + 0.06 * Math.sin(t * 8.3) + 0.03 * Math.sin(t * 13.1) });
};
const LEGS_AT: V3 = [-0.5, FLOOR + 0.35, -12.15];
const legs = (out: Stage, t: number) => {
  const kick = q((t * 1.3) % 1, 24);
  out.places.push({ key: `legs|${kick}`, draw: (p) => legsUp(p, kick), x: LEGS_AT[0], y: LEGS_AT[1], z: LEGS_AT[2], scale: 0.62, size: [600, 1000, 1] });
};

// ---- per shot ----
const cockpitCrew = (out: Stage, cam: CamInfo, t: number, id: number, back: boolean) => {
  const capExpr: Expr = id === 1 && t > T_HOOK ? "shock" : "neutral";
  if (id === 1 || id === 5 || id === 14) {
    if (!(id === 5 && t > T_BLOW + 0.4)) sit(out, cam, t, CAPTAIN, CAPT[0], CAPT[1] - 0.2, CAPT[2], id === 14 ? (t > T_THUMB ? "grin" : "neutral") : capExpr,
      { back, prop: id === 14 ? ["thumb", smooth((t - T_THUMB - 0.1) / 0.3)] : ["yoke", 0] });
    else sit(out, cam, t, CAPTAIN, CAPT[0], CAPT[1] - 0.2, CAPT[2] - 0.15 * smooth((t - T_BLOW - 0.4) / 0.4), "shock", { back, prop: ["grab", 0.6], tilt: -8 });
  }
  if (id !== 14) sit(out, cam, t, FOW, FO[0], FO[1] - 0.2, FO[2], id === 1 && t > T_HOOK ? "shock" : id >= 5 && t > T_BLOW ? "stern" : "neutral", { back, prop: ["yoke", 0] });
};
const cabin = (out: Stage, cam: CamInfo, t: number) => {
  // rows of passengers facing forward (the lens), a steward in the aisle
  const xs = [-1.2, -0.76, -0.32, 0.6, 1.04];
  let k = 0;
  for (let row = 0; row < 9; row++) for (let c = 0; c < 5; c++, k++) {
    if (hh(k, 3) < 0.18) continue;
    const z = -6.9 + row * 0.82 + 0.02;
    sit(out, cam, t, pax(k), xs[c], FLOOR + 0.2, z, (["neutral", "grin", "whistle", "neutral", "relief"] as Expr[])[k % 5], {}, 0.92);
  }
  stand(out, cam, t, STEW, 0.15, FLOOR, -3.6, "grin", { wave: 0.5 + 0.5 * Math.sin(t * 5) });
};
const STEW_POS: V3 = [0.08, FLOOR, -11.35];
const backWalk = (out: Stage, cam: CamInfo, t: number, who: Who, x0: number, z0: number, x1: number, z1: number, t0: number, t1: number) => {
  const u = clamp01((t - t0) / (t1 - t0)), moving = t > t0 && t < t1;
  const phase = moving ? q(((t - t0) * 1.9 / 2) % 1, 120) : 0;
  out.places.push(person(cam, who, x0 + (x1 - x0) * u, FLOOR, z0 + (z1 - z0) * u, FRONT, { mode: moving ? "stroll" : "stand", phase, back: true }, {}));
};
const steward = (out: Stage, cam: CamInfo, t: number, id: number) => {
  if (id === 8) {
    const close = t > 21.0; // the front close-up of his face
    if (t < T_GRAB - 0.45) { backWalk(out, cam, t, STEW, 0.15, -9.5, STEW_POS[0], STEW_POS[2], T_STEW, T_GRAB - 0.45); return; }
    const k = t < T_GRAB ? smooth((t - T_GRAB + 0.45) / 0.45) : 1 - 0.12 * Math.sin(t * 6);
    stand(out, cam, t, STEW, STEW_POS[0], STEW_POS[1], STEW_POS[2], t > T_GRAB + 0.6 ? "stern" : "shock", { prop: ["grab", k], tilt: close ? -3 : 3, back: !close });
    if (close && t > 21.3) card(out, "sweat", 200, 200, (p) => fxSweat(p), STEW_POS[0] + 0.26, STEW_POS[1] + 1.95, STEW_POS[2] - 0.05, 0.16, 0.16);
    return;
  }
  // 9 (from behind): he tires and slides aside; two more crew push in and take over
  const tired = smooth((t - T_TIRE) / 0.8), took = smooth((t - T_TAKE + 0.2) / 0.6);
  const sx = STEW_POS[0] + 0.62 * took, sz = STEW_POS[2] + 0.45 * took;
  stand(out, cam, t, STEW, sx, FLOOR, sz, "dazed", { prop: took > 0.5 ? ["hands", 0.2] : ["grab", 0.95 - 0.7 * tired], tilt: 3 + 6 * tired, back: true });
  const in2 = smooth((t - T_TAKE + 0.9) / 0.9);
  stand(out, cam, t, CREW2, -0.45 + 0.2 * in2, FLOOR, -10.0 - 1.25 * in2, "stern", { prop: ["grab", 0.25 + 0.75 * in2], tilt: 2, back: true });
  stand(out, cam, t, CREW3, 0.1 - 0.3 * in2, FLOOR, -9.6 - 1.1 * in2, "stern", { prop: ["grab", 0.2 + 0.5 * in2], tilt: -2, back: true });
};
const dangerPath = (out: Stage, t: number) => {
  // red dots from the body on the roof back to the left engine, laid down one by one before "engine"
  const n = 22, t0 = T_DEAD + 1.2, t1 = T_ENGINE;
  const A: V3 = [PANE_C[0] + 0.2, 1.9, -11.2], B = ENGINE_L;
  for (let k = 0; k < n; k++) {
    const tk = t0 + ((t1 - t0) * k) / n;
    if (t < tk) break;
    const u = k / (n - 1), x = A[0] + (B[0] - A[0]) * u, z = A[2] + (B[2] - A[2]) * u, y = A[1] + (B[1] - A[1]) * u + 1.6 * Math.sin(Math.PI * u);
    const pop = Math.min(1, (t - tk) * 6);
    card(out, "dot", 64, 64, fxDot, x, y, z, 0.32 * pop, 0.32 * pop);
  }
  if (t > T_ENGINE) { const u = Math.min(1, (t - T_ENGINE) * 2); card(out, `eburst${q(u, 15)}`, 512, 512, (p) => fxBurst(p, u, "#ff6b5e", 12), B[0], B[1], B[2] - 0.6, 2.4, 2.4); }
};
const ward = (out: Stage, cam: CamInfo, t: number) => {
  const alive = t > T_ALIVE - 0.05;
  sit(out, cam, t, CAPTAIN, WARD[0] - 0.05, WARD[1] + 0.52, WARD[2] - 0.45, alive ? (t > 35.3 ? "grin" : "shock") : "dazed",
    { prop: ["cast", smooth((t - 35.6) / 0.3)], ...(alive ? {} : { blink: 1 }) });
  if (t > 36.75) for (let k = 0; k < 3; k++) {
    const u = t - 36.75 - k * 0.1;
    if (u > 0) card(out, `flake${q(Math.min(1, u), 15)}`, 128, 128, (p) => fxFlake(p, Math.min(1, u)), WARD[0] - 0.05 + [-0.32, 0.3, 0.05][k], WARD[1] + 2.15 + [0, 0.12, 0.3][k], WARD[2] - 0.4, 0.2, 0.2);
  }
};
const manager = (out: Stage, cam: CamInfo, t: number, id: number) => {
  if (id === 15) stand(out, cam, t, MANAGER, MGR[0], MGR[1], MGR[2], "whistle", { prop: ["driver", q(0.5 + 0.5 * Math.sin(t * 7), 10)] });
  if (id === 18) {
    const wrong = t > T_WRONG + 0.35;
    stand(out, cam, t, MANAGER, MGR[0], MGR[1], MGR[2], wrong ? "shock" : t > T_MATCH ? "grin" : "neutral",
      { prop: ["bolts", smooth((t - T_MATCH) / 0.4)], headTilt: t > T_MATCH && !wrong ? 4 * Math.sin((t - T_MATCH) * 9) : 0 });
    if (t > T_MATCH + 0.3 && !wrong) card(out, `tick${q(Math.min(1, (t - T_MATCH - 0.3) * 2), 15)}`, 256, 256, (p) => fxTick(p, Math.min(1, (t - T_MATCH - 0.3) * 2)), MGR[0] + 0.05, MGR[1] + 2.35, MGR[2] - 0.1, 0.4, 0.4);
    if (t > T_WRONG) card(out, `cross${q(Math.min(1, (t - T_WRONG) * 1.8), 15)}`, 256, 256, (p) => fxCross(p, Math.min(1, (t - T_WRONG) * 1.8)), MGR[0] - 0.12, MGR[1] + 1.12, MGR[2] - 0.2, 0.3, 0.3);
  }
  if (id === 21) walk(out, cam, t, MANAGER, MGR[0] - 0.6, MGR[2] - 1.5, -9.5, -26, 63.2, 66.3, "whistle", GROUND);
};
const cutaway = (out: Stage, t: number, id: number) => {
  // cabin air pushing outward on the pane: arrows on the inside, growing on "pushes", bigger on "pushed harder"
  const g = smooth((t - T_PUSH + 0.15) / 0.5) * (1 + 0.6 * smooth((t - T_HARD) / 0.5)) * (t > T_FAIL + 0.2 ? 0 : 1);
  if (g <= 0) return;
  for (let k = 0; k < 5; k++) {
    const y = -1.6 + k * 0.8, L = (1.7 + 0.2 * Math.sin(t * 6 + k)) * g;
    card(out, "arrowFull", 600, 160, (p) => fxArrow(p, 1, "#fff6e8"), CUT[0] - 0.06 - L * 0.5, CUT[1] + y, CUT[2] + 0.4, Math.max(0.05, L), 0.5 * Math.min(1, 0.6 + 0.4 * g));
  }
};

/** everything with a face (and every drawn effect) in shot `id` at time t; flight + hangar shots are plane-local */
export const stage = (id: number, t: number, cam: CamInfo): Stage => {
  const out: Stage = { places: [], fx: [] };
  const s = SHOTS[id - 1];
  LNAME = s.light;
  findSun(cam, SUN);
  if (id === 1) cockpitCrew(out, cam, t, id, false);
  if (id === 4) cabin(out, cam, t);
  if (id === 5) { cockpitCrew(out, cam, t, id, true); gale(out, t, true); }
  if (id === 6) { captainOut(out, cam, t, id); gale(out, t, false); sit(out, cam, t, FOW, FO[0], FO[1] - 0.2, FO[2], "stern", { prop: ["yoke", 0] }); }
  if (id === 7) { legs(out, t); gale(out, t, true); sit(out, cam, t, FOW, FO[0], FO[1] - 0.2, FO[2], "stern", { back: true, prop: ["yoke", 0] }); }
  if (id === 8 || id === 9) { legs(out, t); steward(out, cam, t, id); gale(out, t, true, 2); sit(out, cam, t, FOW, FO[0], FO[1] - 0.2, FO[2], "stern", { prop: ["yoke", 0] }); }
  if (id === 10) { captainOnRoof(out, cam, t, -1.35); dangerPath(out, t); gale(out, t, false, 2); }
  if (id === 11) {
    sit(out, cam, t, FOW, FO[0], FO[1] - 0.2, FO[2], "stern", { prop: ["yoke", 0.5 + 0.5 * Math.sin(t * 3)] });
    card(out, "sweatfo", 200, 200, (p) => fxSweat(p), FO[0] + 0.24, FO[1] + 1.25, FO[2] + 0.02, 0.14, 0.14);
    legs(out, t); gale(out, t, true, 2);
  }
  if (id === 12 && t > T_TD) {
    const pose = planePose(12, t), u = (t - T_TD) / 1.2;
    if (u < 1) for (const sx of [-1, 1]) for (let k = 0; k < 3; k++) {
      const uu = clamp01(u - k * 0.12);
      if (uu > 0) card(out, `puff${q(uu, 15)}`, 300, 300, (p) => fxPuff(p, uu), sx * 2.2, GROUND + 0.5 + uu * 0.6, pose.pos[2] + 2.3 + uu * 3 + k * 0.6, 1.2 + uu * 1.6, 1.2 + uu * 1.6, { soft: true });
    }
  }
  if (id === 13) ward(out, cam, t);
  if (id === 14) cockpitCrew(out, cam, t, id, false);
  if (id === 15 || id === 18 || id === 21) manager(out, cam, t, id);
  if (id === 19 || id === 20) cutaway(out, t, id);
  return out;
};
export const PLANE_LOCAL = (id: number) => { const p = SHOTS[id - 1].place; return p === "flight" || p === "hangar"; };
export { FPS, INK, T_OFF, T_HOOK };
