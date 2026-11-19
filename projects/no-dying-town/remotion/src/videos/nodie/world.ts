// The no-dying town short as one three.js scene: seven small sets side by side along x (snowy road with the sign,
// the stilt-house town, a permafrost cutaway, the cemetery, the coffins-in-ice cutaway, the giant freezer, the
// airfield). Same look rules as the bridge: two-tone materials (lam/twoTone), painted textures, camera-relative sun
// frozen per shot, lit character cards on NOINK. update(id, f, camera) poses the shot and returns the focus point.
import * as THREE from "three";
import { Batch, boxGeo, V, lam, quad, tri } from "../bridge/build";
import { ctex, rep, rng } from "../bridge/paint";
import { bodyFront, Outfit, Expr, fxPuff, SKINS, Pen } from "../bridge/toon";
import { LIGHTS, LOOK } from "../bridge/lights";
import { TONE, CHAR, untone } from "../bridge/shade";
import { NOINK } from "../bridge/ink";
import { Pool, Actor, Fx } from "../bridge/cast";
import { germ, bear, person, roadSign, plate, closedStamp, thermo, ticket, counter, deathToll, arrow, LIGHT } from "./chars";
import { FPS, SHOTS, ROAD, TOWN, GROUND, CEM, CUT, FREEZER, AIR, camAt, doorAt, stampAt, planeAt, smooth, clamp01 } from "./story";

type Place = { key: string; draw: (p: Pen) => void; x: number; y: number; z: number; scale?: number; mirror?: boolean; yaw?: number; roll?: number };
type FxPlace = { key: string; cw: number; ch: number; draw: (p: Pen) => void; x: number; y: number; z: number; w: number; h: number; soft?: boolean };

const q = (v: number, n = 30) => Math.round(v * n) / n;
const tier = (d: number): [number, number, number] =>
  d < 2.2 ? [1800, 3000, 3.0] : d < 4.5 ? [1080, 1800, 1.8] : d < 12 ? [600, 1000, 1.0] : d < 24 ? [360, 600, 0.6] : [240, 400, 0.4];
const blinkAt = (f: number, i: number) => {
  const h = (k: number) => { const v = Math.sin(i * 127.1 + k * 311.7) * 43758.5453; return v - Math.floor(v); };
  let s = Math.round(-60 * h(9));
  for (let n = 0; s <= f && n < 400; n++) { const k = f - s; if (k >= 0 && k < 4) return [0.5, 1, 1, 0.5][k]; s += Math.round(15 + 54 * h(i * 31 + n)); }
  return 0;
};
const pop = (t: number, t0: number, d = 0.25) => { const u = clamp01((t - t0) / d); return u <= 0 ? 0 : 1 + 0.54 * Math.sin(Math.PI * u) * (1 - u); };

// ---------------- painted textures ----------------
const snowTex = () => ctex("snow", 1024, 1024, (g, r) => {
  g.fillStyle = "#eef3fa"; g.fillRect(0, 0, 1024, 1024);
  for (let i = 0; i < 900; i++) { g.fillStyle = `rgba(150,175,215,${0.05 + 0.07 * r()})`; g.beginPath(); g.ellipse(1024 * r(), 1024 * r(), 6 + 40 * r(), 3 + 12 * r(), r() * 3, 0, 7); g.fill(); }
  for (let i = 0; i < 400; i++) { g.fillStyle = "rgba(255,255,255,0.9)"; g.fillRect(1024 * r(), 1024 * r(), 3, 3); }
});
const roadTex = () => ctex("road", 512, 1024, (g, r) => {
  g.fillStyle = "#6a7080"; g.fillRect(0, 0, 512, 1024);
  for (let i = 0; i < 2500; i++) { g.fillStyle = `rgba(${r() < 0.5 ? "255,255,255" : "0,0,0"},0.06)`; g.fillRect(512 * r(), 1024 * r(), 4, 4); }
  for (const x of [130, 382]) { g.fillStyle = "rgba(40,44,56,0.35)"; g.fillRect(x - 30, 0, 60, 1024); }
  for (let i = 0; i < 160; i++) { g.fillStyle = "rgba(240,245,252,0.75)"; g.beginPath(); g.ellipse(r() < 0.5 ? 20 * r() : 512 - 20 * r(), 1024 * r(), 30 + 30 * r(), 10 + 20 * r(), 0, 0, 7); g.fill(); }
});
/** vertical cutaway: 6 m tall, top = surface. snow, dark active layer, then frozen ground with ice lenses */
const permaTex = () => ctex("perma", 1024, 1024, (g, r) => {
  const sn = 0.06 * 1024, so = 0.15 * 1024;
  const gr = g.createLinearGradient(0, so, 0, 1024); gr.addColorStop(0, "#8fb3d6"); gr.addColorStop(1, "#5f86bf");
  g.fillStyle = gr; g.fillRect(0, so, 1024, 1024 - so);
  for (let i = 0; i < 70; i++) { g.fillStyle = `rgba(110,110,125,${0.5 + 0.3 * r()})`; g.beginPath(); g.ellipse(1024 * r(), so + (1024 - so) * r(), 8 + 26 * r(), 6 + 16 * r(), r() * 3, 0, 7); g.fill(); }
  for (let i = 0; i < 26; i++) { // ice lenses: white streaks
    const y = so + 40 + (1024 - so - 60) * r(), x = 1024 * r(), w = 80 + 220 * r();
    g.fillStyle = `rgba(235,248,255,${0.55 + 0.35 * r()})`; g.beginPath(); g.ellipse(x, y, w, 5 + 7 * r(), (r() - 0.5) * 0.15, 0, 7); g.fill();
  }
  g.fillStyle = "#6b5040"; g.fillRect(0, sn, 1024, so - sn);
  for (let i = 0; i < 200; i++) { g.fillStyle = `rgba(40,25,20,${0.3 * r()})`; g.fillRect(1024 * r(), sn + (so - sn) * r(), 8, 5); }
  g.fillStyle = "#f2f6fb"; g.fillRect(0, 0, 1024, sn);
  g.fillStyle = "#f2f6fb"; for (let x = 0; x < 1024; x += 24) { g.beginPath(); g.arc(x + 12, sn, 12 + 6 * r(), 0, Math.PI); g.fill(); }
});
const frostTex = () => ctex("frost", 512, 512, (g, r) => {
  g.clearRect(0, 0, 512, 512);
  for (let i = 0; i < 260; i++) { g.strokeStyle = `rgba(255,255,255,${0.15 + 0.4 * r()})`; g.lineWidth = 1 + 2 * r(); const x = 512 * r(), y = 512 * r(), l = 8 + 30 * r(), a = r() * 7; g.beginPath(); g.moveTo(x, y); g.lineTo(x + l * Math.cos(a), y + l * Math.sin(a)); g.stroke(); }
});
const plankTex = (key: string, col: string) => ctex("pl" + key, 256, 256, (g, r) => {
  g.fillStyle = col; g.fillRect(0, 0, 256, 256);
  for (let x = 0; x < 256; x += 32) { g.fillStyle = "rgba(0,0,0,0.16)"; g.fillRect(x, 0, 3, 256); g.fillStyle = `rgba(255,255,255,${0.05 * r()})`; g.fillRect(x + 6, 0, 18, 256); }
});
const penTex = (key: string, w: number, h: number, draw: (p: Pen) => void) => ctex(key, w, h, (g) => { g.clearRect(0, 0, w, h); draw(new Pen(g)); });

const SKY_V = "varying vec3 vP; void main(){ vP = normalize(position); gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0); }";
const SKY_F = `uniform vec3 c0, c1, c2, c3, c4; uniform vec4 e; varying vec3 vP;
  void main(){ float el = asin(clamp(normalize(vP).y, -1.0, 1.0));
    vec3 c = mix(c0, c1, smoothstep(0.0, e.x, el)); c = mix(c, c2, smoothstep(e.x, e.y, el));
    c = mix(c, c3, smoothstep(e.y, e.z, el)); c = mix(c, c4, smoothstep(e.z, e.w, el)); gl_FragColor = vec4(c, 1.0); }`;
/** arctic sky: pale rose horizon into cold blue */
const ARCTIC = { c: ["#f4ddd4", "#ead3df", "#bccbeb", "#89a8dc", "#5d7fc6"], e: [0, 3, 8, 16, 40] };

const LOCAL: Outfit = { jacket: "#d6453d", pants: "#2f3446", boots: "#3a2a20", hat: "cap", cap: "#2d5f8a", skin: SKINS[1], buttons: "#f2efe6" };
const HUNTER: Outfit = { jacket: "#e0a630", pants: "#2f3446", boots: "#3a2a20", hat: "cap", cap: "#c0353a", skin: SKINS[2], rifle: true };
const MINER = (v: number): Outfit => ({ jacket: ["#55525a", "#4a4e5e", "#5e5248"][v % 3], pants: "#34343c", boots: "#2a221c", hat: "cap", cap: "#2b2b31", skin: SKINS[v % 4], buttons: "#c8b27a" });
const SUIT: Outfit = { jacket: "#f4f6f8", pants: "#e6ebf1", boots: "#3d6fb0", hat: "cap", cap: "#f4f6f8", skin: SKINS[0], buttons: "#9aa6b5" };
const NEIGHBOR: Outfit = { jacket: "#3f8f5a", pants: "#3b3f52", boots: "#4a3426", hat: "hair", hair: "#e8c45a", skin: SKINS[0], buttons: "#f2efe6" };
const OLD: Outfit = { jacket: "#6d6a7a", pants: "#3b3f52", boots: "#3a2a20", hat: "hair", hair: "#e9e9ee", moustache: "#e9e9ee", skin: SKINS[1], buttons: "#d9dde0", build: "stout" };
const MUM: Outfit = { jacket: "#7b5ac9", pants: "#3b3f52", boots: "#5a3b2a", hat: "hair", hair: "#5a3b2a", skin: SKINS[3], dress: "#e07a9a" };

export class World {
  root = new THREE.Group();
  private pool = new Pool();
  private actors: Actor[] = [];
  private fxs: Fx[] = [];
  private hemi = new THREE.HemisphereLight("#cfe6ff", "#6c5c8c", 1.1);
  private sun = new THREE.DirectionalLight("#fff0d6", 2.6);
  private fog = new THREE.Fog("#dfe6f3", 40, 340);
  private skyMat: THREE.ShaderMaterial; private sky: THREE.Mesh;
  private sunCache = new Map<number, THREE.Vector3>();
  private door = new THREE.Group();
  private plane = new THREE.Group();

  constructor() {
    const R = this.root;
    this.skyMat = new THREE.ShaderMaterial({
      uniforms: { c0: { value: new THREE.Color() }, c1: { value: new THREE.Color() }, c2: { value: new THREE.Color() }, c3: { value: new THREE.Color() }, c4: { value: new THREE.Color() }, e: { value: new THREE.Vector4() } },
      vertexShader: SKY_V, fragmentShader: SKY_F, side: THREE.BackSide, depthWrite: false, fog: false,
    });
    this.sky = new THREE.Mesh(new THREE.SphereGeometry(1100, 48, 24), this.skyMat);
    this.sky.renderOrder = -1; this.sky.frustumCulled = false; this.sky.layers.set(NOINK);
    R.add(this.sky);
    this.sun.castShadow = true; this.sun.shadow.mapSize.set(2048, 2048);
    R.add(this.hemi, this.sun, this.sun.target);

    const b = new Batch(), nb = new Batch(); // nb: no cast shadows (the cutaway lids)
    const snow = lam("snowM", () => ({ map: rep(snowTex(), 1, 1) }));
    const white = lam("whiteWood", () => ({ map: plankTex("w", "#f3f1ea") }));
    const wood = lam("brownWood", () => ({ map: plankTex("b", "#7a5236") }));
    const coffinM = lam("coffin", () => ({ color: "#6b4228" }));
    const post = lam("post", () => ({ color: "#5c6470" }));
    const dark = lam("darkGlass", () => ({ color: "#2b3550" }));
    const mtn = lam("mtn", () => ({ color: "#e8eef8" }));
    const rock = lam("rock", () => ({ color: "#7d8394" }));
    const box = (x0: number, y0: number, z0: number, x1: number, y1: number, z1: number, m: THREE.Material, bb: Batch = b) => bb.add(boxGeo(V(x0, y0, z0), V(x1, y1, z1)), m);
    const ground = (cx: number, w: number, z0: number, z1: number, y = 0) =>
      b.add(quad(V(cx - w / 2, y, z1), V(cx + w / 2, y, z1), V(cx + w / 2, y, z0), V(cx - w / 2, y, z0), w / 8, (z1 - z0) / 8), snow);
    const mountains = (cx: number, z: number, seed: number) => {
      const r = rng(seed);
      for (let i = 0; i < 9; i++) {
        const x = cx - 220 + i * 55 + 20 * r(), h = 45 + 55 * r(), rad = 50 + 40 * r(), zz = z - 60 * r();
        b.add(new THREE.ConeGeometry(rad, h, 7, 1).rotateY(r() * 3).translate(x, h / 2 - 2, zz), mtn);
        b.add(new THREE.ConeGeometry(rad * 1.02, h * 0.28, 7, 1).rotateY(r() * 3).translate(x, h * 0.14 - 2, zz), rock);
      }
    };
    /** a coloured house on stilts; front faces +z */
    const stiltHouse = (x: number, z: number, w: number, d: number, h: number, col: string, si: number) => {
      const y0 = 0.9, wall = lam("hw" + col, () => ({ map: plankTex(col, col) })), roof = lam("roofSnow", () => ({ color: "#f4f7fb" }));
      for (const sx of [-1, 0, 1]) for (const sz of [-1, 1]) box(x + sx * (w / 2 - 0.2) - 0.08, 0, z + sz * (d / 2 - 0.2) - 0.08, x + sx * (w / 2 - 0.2) + 0.08, y0, z + sz * (d / 2 - 0.2) + 0.08, post);
      box(x - w / 2, y0, z - d / 2, x + w / 2, y0 + h, z + d / 2, wall);
      const rh = d * 0.32, y1 = y0 + h, e = 0.3;
      b.add(quad(V(x - w / 2 - e, y1, z + d / 2 + e), V(x + w / 2 + e, y1, z + d / 2 + e), V(x + w / 2 + e, y1 + rh, z), V(x - w / 2 - e, y1 + rh, z)), roof);
      b.add(quad(V(x + w / 2 + e, y1, z - d / 2 - e), V(x - w / 2 - e, y1, z - d / 2 - e), V(x - w / 2 - e, y1 + rh, z), V(x + w / 2 + e, y1 + rh, z)), roof);
      b.add(tri(V(x - w / 2, y1, z + d / 2), V(x - w / 2, y1 + rh, z), V(x - w / 2, y1, z - d / 2)), wall);
      b.add(tri(V(x + w / 2, y1, z - d / 2), V(x + w / 2, y1 + rh, z), V(x + w / 2, y1, z + d / 2)), wall);
      const n = Math.max(2, Math.floor(w / 1.6));
      for (let i = 0; i < n; i++) {
        const wx = x - w / 2 + (w / n) * (i + 0.5);
        if (i === (si % n)) { box(wx - 0.4, y0, z + d / 2, wx + 0.4, y0 + 2.0, z + d / 2 + 0.05, white); continue; }
        box(wx - 0.42, y0 + h * 0.4, z + d / 2, wx + 0.42, y0 + h * 0.4 + 1.0, z + d / 2 + 0.05, white);
        box(wx - 0.32, y0 + h * 0.4 + 0.1, z + d / 2 + 0.03, wx + 0.32, y0 + h * 0.4 + 0.9, z + d / 2 + 0.07, dark);
      }
      box(x - 0.9, y0 - 0.05, z + d / 2, x + 0.9, y0 + 0.05, z + d / 2 + 1.2, wood); // landing
    };
    const COLS = ["#c8463d", "#e8b830", "#3f8f5a", "#3a6fb0", "#2f9c9a", "#d9773a"];
    const cross = (x: number, z: number, h = 1.0, m: THREE.Material = white, bb: Batch = b) => {
      box(x - 0.045, 0, z - 0.035, x + 0.045, h, z + 0.035, m, bb);
      box(x - 0.28, h * 0.68, z - 0.035, x + 0.28, h * 0.68 + 0.09, z + 0.035, m, bb);
    };
    const coffinGeo = (() => {
      const s = new THREE.Shape(); // top view outline, long axis along x, 2.0 m
      s.moveTo(-1.0, -0.22); s.lineTo(0.45, -0.34); s.lineTo(1.0, -0.26); s.lineTo(1.0, 0.26); s.lineTo(0.45, 0.34); s.lineTo(-1.0, 0.22); s.closePath();
      const g = new THREE.ExtrudeGeometry(s, { depth: 0.42, bevelEnabled: false });
      g.rotateX(-Math.PI / 2); // extrude upward
      return g;
    })();
    const coffin = (x: number, y: number, z: number, yaw: number, tilt: number, sc = 1, bb: Batch = b) => {
      const m = new THREE.Matrix4().compose(V(x, y, z), new THREE.Quaternion().setFromEuler(new THREE.Euler(tilt, yaw, 0.12 * Math.sin(x * 3))), V(sc, sc, sc));
      bb.add(coffinGeo, coffinM, m);
      const lid = new THREE.Matrix4().compose(V(x, y, z), new THREE.Quaternion().setFromEuler(new THREE.Euler(tilt, yaw, 0.12 * Math.sin(x * 3))), V(sc, sc, sc));
      const cr = new THREE.BoxGeometry(0.5, 0.02, 0.07).translate(0.3, 0.43, 0), cr2 = new THREE.BoxGeometry(0.07, 0.02, 0.32).translate(0.42, 0.43, 0);
      bb.add(cr, lam("brass", () => ({ color: "#d9b25a" })), lid); bb.add(cr2, lam("brass", () => ({ color: "#d9b25a" })), lid);
    };
    const signMesh = (key: string, w: number, h: number, cw: number, ch: number, draw: (p: Pen) => void, x: number, y: number, z: number, yaw = 0) => {
      const m = new THREE.MeshLambertMaterial({ map: penTex(key, cw, ch, draw), transparent: false, alphaTest: 0.5, side: THREE.DoubleSide });
      const s = new THREE.Mesh(new THREE.PlaneGeometry(w, h), m); s.position.set(x, y, z); s.rotation.y = yaw; s.layers.set(NOINK); R.add(s);
    };

    // ---- ROAD (hook + loop) ----
    ground(ROAD, 190, -300, 60);
    b.add(quad(V(ROAD - 2.6, 0.01, 40), V(ROAD + 2.6, 0.01, 40), V(ROAD + 2.6, 0.01, -260), V(ROAD - 2.6, 0.01, -260), 1, 30), lam("roadM", () => ({ map: rep(roadTex(), 1, 1) })));
    box(ROAD + 1.85, 0, -2.65, ROAD + 1.95, 2.9, -2.55, post);
    signMesh("roadSign", 1.15, 1.15, 600, 600, roadSign, ROAD + 1.9, 2.35, -2.52);
    signMesh("noDying", 1.25, 0.36, 700, 200, (p) => plate(p, "NO DYING", 700, 200), ROAD + 1.9, 1.55, -2.52);
    for (const [i, x, z] of [[0, -14, -30], [1, -6, -34], [2, 9, -32], [3, 16, -38], [4, -22, -44], [5, 24, -46]] as const) stiltHouse(ROAD + x, z, 6, 5, 3, COLS[i], i);
    mountains(ROAD, -170, 3);

    // ---- TOWN ----
    ground(TOWN, 190, -300, 60);
    {
      const front: [number, number][] = [[-12, 6], [-4.5, 7], [9.2, 5.6], [16.5, 6.5]], back: [number, number][] = [[-15, 7], [-6, 6], [2, 7], [10, 6], [18, 7]];
      front.forEach(([x, w], i) => stiltHouse(TOWN + x, -5, w, 5, 3.0 + (i % 2) * 0.6, COLS[i % 6], i));
      stiltHouse(TOWN + 2.0, -6.2, 3.2, 4, 3, COLS[4], 1); // narrow house left of the bear gap
      back.forEach(([x, w], i) => stiltHouse(TOWN + x, -16, w, 5, 3.4, COLS[(i + 3) % 6], i + 2));
      for (let i = 0; i < 8; i++) stiltHouse(TOWN - 30 + i * 9, -30, 6, 5, 3.2, COLS[(i + 1) % 6], i);
      mountains(TOWN, -160, 5);
    }

    // ---- GROUND cutaway ----
    {
      const pm = lam("permaM", () => ({ map: permaTex() }));
      const W = 6, D = 6, Y = -6;
      b.add(quad(V(GROUND - W, Y, 0), V(GROUND + W, Y, 0), V(GROUND + W, 0, 0), V(GROUND - W, 0, 0), 2, 1), pm);
      b.add(quad(V(GROUND + W, Y, 0), V(GROUND + W, Y, -D), V(GROUND + W, 0, -D), V(GROUND + W, 0, 0), 1, 1), pm);
      b.add(quad(V(GROUND - W, Y, -D), V(GROUND - W, Y, 0), V(GROUND - W, 0, 0), V(GROUND - W, 0, -D), 1, 1), pm);
      b.add(quad(V(GROUND - W, 0, 0), V(GROUND + W, 0, 0), V(GROUND + W, 0, -D), V(GROUND - W, 0, -D), 1.5, 0.75), snow);
      ground(GROUND, 190, -300, -D, 0);
      stiltHouse(GROUND - 2.2, -3.4, 4, 3.4, 2.4, COLS[0], 0);
      cross(GROUND + 2.6, -2.5, 0.9); cross(GROUND + 3.6, -2.9, 0.9);
      mountains(GROUND, -160, 7);
    }

    // ---- CEMETERY ----
    ground(CEM, 190, -300, 60);
    b.add(new THREE.SphereGeometry(30, 32, 16).scale(1.6, 0.22, 1).translate(CEM, -1.5, -40), snow);
    for (let i = 0; i < 7; i++) cross(CEM - 3.6 + i * 1.2, -3.4);
    for (let i = 0; i < 6; i++) cross(CEM - 3 + i * 1.2 + 0.3 * Math.sin(i), -5.4 - 0.4 * (i % 2), 0.95);
    for (let i = 0; i < 5; i++) cross(CEM - 2.4 + i * 1.2, -7.4, 0.9);
    for (let x = -4.6; x <= 4.6; x += 0.32) if (Math.abs(x) > 0.9) box(CEM + x - 0.04, 0, 1.15, CEM + x + 0.04, 0.85, 1.22, white);
    box(CEM - 4.6, 0.55, 1.12, CEM - 0.9, 0.63, 1.15, white); box(CEM + 0.9, 0.55, 1.12, CEM + 4.6, 0.63, 1.15, white);
    for (const s of [-1, 1]) box(CEM + s * 0.95 - 0.09, 0, 1.1, CEM + s * 0.95 + 0.09, 1.9, 1.28, white);
    box(CEM - 1.15, 1.9, 1.12, CEM + 1.15, 2.08, 1.26, white);
    for (let i = 0; i < 7; i++) box(CEM - 0.85 + i * 0.28 - 0.03, 0.1, 1.17, CEM - 0.85 + i * 0.28 + 0.03, 1.2, 1.21, white); // gate bars
    box(CEM - 0.85, 1.12, 1.16, CEM + 0.85, 1.2, 1.22, white);
    mountains(CEM, -170, 9);
    // 1998 dig: canopy on four poles, a dirt mound and the hole (shot 8 only: hidden otherwise by visibility toggles)
    this.dig = new THREE.Group();
    {
      const can = new THREE.Mesh(new THREE.ConeGeometry(1.7, 0.8, 4, 1, true).rotateY(Math.PI / 4), new THREE.MeshLambertMaterial({ color: "#f5f7fa", side: THREE.DoubleSide }));
      can.position.set(CEM + 1.2, 2.55, -3.4); can.castShadow = true;
      this.dig.add(can);
      for (const sx of [-1, 1]) for (const sz of [-1, 1]) { const p = new THREE.Mesh(new THREE.CylinderGeometry(0.03, 0.03, 2.15), new THREE.MeshLambertMaterial({ color: "#9aa3b0" })); p.position.set(CEM + 1.2 + sx * 1.15, 1.07, -3.4 + sz * 1.15); this.dig.add(p); }
      const mound = new THREE.Mesh(new THREE.SphereGeometry(0.7, 20, 10).scale(1, 0.45, 0.8), new THREE.MeshLambertMaterial({ color: "#5c4334" }));
      mound.position.set(CEM + 2.6, 0, -2.4); mound.castShadow = true; this.dig.add(mound);
      const hole = new THREE.Mesh(new THREE.CircleGeometry(0.62, 24).rotateX(-Math.PI / 2).scale(1.4, 1, 0.8), new THREE.MeshBasicMaterial({ color: "#2a1d18" }));
      hole.position.set(CEM + 1.2, 0.015, -2.85); this.dig.add(hole);
      R.add(this.dig);
    }

    // ---- CUT: coffins locked in the ice under the crosses ----
    {
      const pm = lam("permaM", () => ({ map: permaTex() })), D = 4, Y = -4.6, W = 5;
      b.add(quad(V(CUT - W, Y, -D), V(CUT + W, Y, -D), V(CUT + W, -0.6, -D), V(CUT - W, -0.6, -D), 2, 0.75, 0, 0), pm);
      b.add(quad(V(CUT - W, Y, 0), V(CUT + W, Y, 0), V(CUT + W, Y, -D), V(CUT - W, Y, -D), 2, 1), lam("iceFloor", () => ({ color: "#6f95c8" })));
      b.add(quad(V(CUT + W, Y, 0), V(CUT + W, Y, -D), V(CUT + W, 0, -D), V(CUT + W, 0, 0), 1, 1), pm);
      b.add(quad(V(CUT - W, Y, -D), V(CUT - W, Y, 0), V(CUT - W, 0, 0), V(CUT - W, 0, -D), 1, 1), pm);
      box(CUT - W, -0.6, -D, CUT + W, 0, 0, lam("lidM", () => ({ map: permaTex() })), nb);
      ground(CUT, 190, -300, -D, 0);
      for (const [x, z] of [[-W - 80, 0], [W + 80, 0]] as const) b.add(quad(V(CUT + x - 80, 0, 60), V(CUT + x + 80, 0, 60), V(CUT + x + 80, 0, -D), V(CUT + x - 80, 0, -D), 20, 8), snow);
      for (const [x, yaw, tilt, y] of [[-3, 0.15, -0.5, -2.6], [0, -0.1, -0.42, -2.2], [3, 0.2, -0.55, -2.8]] as const) { coffin(CUT + x, y, -2, yaw, tilt); cross(CUT + x, -2.2, 1.0); }
      const ice = new THREE.Mesh(new THREE.PlaneGeometry(2 * W, -Y - 0.6), new THREE.MeshPhongMaterial({ color: "#cfeaff", specular: "#ffffff", shininess: 60, transparent: true, opacity: 0.28, depthWrite: false }));
      ice.position.set(CUT, (Y - 0.6) / 2, 0.01); ice.renderOrder = 2; ice.layers.set(NOINK); R.add(ice);
      const fr = new THREE.Mesh(new THREE.PlaneGeometry(2 * W, -Y - 0.6), new THREE.MeshBasicMaterial({ map: rep(frostTex(), 2, 1), transparent: true, depthWrite: false, opacity: 0.35 }));
      fr.position.set(CUT, (Y - 0.6) / 2, 0.02); fr.renderOrder = 3; fr.layers.set(NOINK); R.add(fr);
      mountains(CUT, -170, 11);
    }

    // ---- FREEZER ----
    {
      ground(FREEZER, 190, -300, 60);
      const fw = lam("fridge", () => ({ color: "#f4f6f8" })), x0 = FREEZER - 1.5, x1 = FREEZER + 1.5, z0 = -1.2, z1 = 0.8, H = 4.6, T = 0.14;
      box(x0, 0, z0, x1, T, z1, fw); box(x0, H - T, z0, x1, H, z1, fw);
      box(x0, 0, z0, x0 + T, H, z1, fw); box(x1 - T, 0, z0, x1, H, z1, fw); box(x0, 0, z0, x1, H, z0 + T, fw);
      const glow = new THREE.Mesh(new THREE.PlaneGeometry(2.7, 4.3), new THREE.MeshBasicMaterial({ color: new THREE.Color(0.85, 1.0, 1.35) }));
      glow.position.set(FREEZER, H / 2, z0 + T + 0.01); glow.layers.set(NOINK); R.add(glow);
      for (const y of [1.45, 2.85]) box(x0 + T, y, z0 + T, x1 - T, y + 0.06, z1 - 0.1, lam("shelf", () => ({ color: "#e6f3ff" })));
      for (const [x, y] of [[-0.62, T], [0.68, T], [-0.62, 1.51], [0.68, 1.51]] as const) coffin(FREEZER + x, y, -0.35, Math.PI / 2 + 0.05 * x, 0, 0.6);
      const r = rng(4);
      for (let i = 0; i < 18; i++) { const x = x0 + 0.3 + 2.4 * r(), y = [T, 1.51, 2.91][i % 3], s = 0.08 + 0.12 * r(); box(x - s, y, z1 - 0.5 - s, x + s, y + 1.4 * s, z1 - 0.5 + s, lam("iceCube", () => ({ color: "#d6eeff" }))); }
      box(x0 - 0.05, H, z0 - 0.05, x1 + 0.05, H + 0.25, z1 + 0.05, snow); // snow cap
      // crosses stand on the snow cap
      this.capCross = new THREE.Group();
      for (const x of [-0.9, 0, 0.9]) {
        const v = new THREE.Mesh(new THREE.BoxGeometry(0.08, 0.8, 0.06), lam("whiteWood", () => ({ map: plankTex("w", "#f3f1ea") })));
        v.position.set(FREEZER + x, H + 0.25 + 0.4, -0.2); v.castShadow = true;
        const h = new THREE.Mesh(new THREE.BoxGeometry(0.5, 0.08, 0.06), v.material); h.position.set(FREEZER + x, H + 0.25 + 0.56, -0.2);
        this.capCross.add(v, h);
      }
      R.add(this.capCross);
      // door: pivots on the right edge (hinge at x1, z1)
      const dp = new THREE.Mesh(new THREE.BoxGeometry(3.0, H, 0.16), new THREE.MeshLambertMaterial({ color: "#f4f6f8" }));
      dp.position.set(1.5, H / 2, 0.08); dp.castShadow = true;
      const handle = new THREE.Mesh(new THREE.BoxGeometry(0.1, 1.6, 0.12), new THREE.MeshLambertMaterial({ color: "#9aa3b0" })); handle.position.set(2.75, H / 2 + 0.2, 0.22);
      const inner = new THREE.Mesh(new THREE.PlaneGeometry(2.8, H - 0.2), new THREE.MeshLambertMaterial({ color: "#e3f1ff", side: THREE.DoubleSide })); inner.position.set(1.5, H / 2, -0.005); inner.rotation.y = Math.PI;
      this.door.add(dp, handle, inner); this.door.position.set(x0, 0, z1); R.add(this.door);
      stiltHouse(FREEZER + 6.5, -3.5, 5, 4, 2.8, COLS[1], 2);
      mountains(FREEZER, -170, 13);
    }

    // ---- AIRFIELD ----
    {
      ground(AIR, 190, -300, 60);
      b.add(quad(V(AIR - 90, 0.01, 4), V(AIR + 90, 0.01, 4), V(AIR + 90, 0.01, -6), V(AIR - 90, 0.01, -6), 1, 18), lam("runway", () => ({ map: rep(roadTex(), 1, 1) })));
      // terminal
      box(AIR + 4, 0, -14, AIR + 16, 4, -9, lam("hw#3a6fb0", () => ({ map: plankTex("#3a6fb0", "#3a6fb0") })));
      box(AIR + 3.8, 4, -14.2, AIR + 16.2, 4.3, -8.8, lam("roofSnow", () => ({ color: "#f4f7fb" })));
      signMesh("lyrSign", 7, 0.9, 1400, 180, (p) => plate(p, "LONGYEARBYEN", 1400, 180, "#fff7e0"), AIR + 10, 3.2, -8.95);
      for (let i = 0; i < 4; i++) box(AIR + 5 + i * 2.6, 1.0, -8.98, AIR + 6.6 + i * 2.6, 2.4, -8.92, dark);
      mountains(AIR, -170, 15);
      // the plane (own group so it can take off); nose toward -x
      const pw = new THREE.MeshLambertMaterial({ color: "#f3f5f8" }), pb = new THREE.MeshLambertMaterial({ color: "#2d6fd0" }), pd = new THREE.MeshLambertMaterial({ color: "#26304a" });
      const P = this.plane;
      const body = new THREE.Mesh(new THREE.CylinderGeometry(0.85, 0.85, 8, 24).rotateZ(Math.PI / 2), pw); body.position.set(0, 1.5, 0);
      const nose = new THREE.Mesh(new THREE.SphereGeometry(0.85, 24, 12, 0, Math.PI * 2, 0, Math.PI / 2).rotateZ(Math.PI / 2), pw); nose.position.set(-4, 1.5, 0);
      const tail = new THREE.Mesh(new THREE.ConeGeometry(0.85, 2.6, 24).rotateZ(-Math.PI / 2), pw); tail.position.set(5.3, 1.75, 0); tail.scale.set(1, 1, 0.9);
      const fin = new THREE.Mesh(new THREE.BoxGeometry(1.3, 1.9, 0.12), pb); fin.position.set(5.6, 2.9, 0); fin.rotation.z = -0.35;
      const stab = new THREE.Mesh(new THREE.BoxGeometry(1.0, 0.08, 3.4), pw); stab.position.set(5.9, 1.9, 0);
      const wing = new THREE.Mesh(new THREE.BoxGeometry(1.6, 0.14, 12), pw); wing.position.set(-0.6, 2.25, 0);
      const stripe = new THREE.Mesh(new THREE.BoxGeometry(8.2, 0.22, 1.74), pb); stripe.position.set(0.2, 1.25, 0);
      P.add(body, nose, tail, fin, stab, wing, stripe);
      for (const s of [-1, 1]) {
        const eng = new THREE.Mesh(new THREE.CylinderGeometry(0.32, 0.32, 1.6, 16).rotateZ(Math.PI / 2), pb); eng.position.set(-1.2, 2.05, s * 2.6); P.add(eng);
        const prop = new THREE.Mesh(new THREE.BoxGeometry(0.05, 1.6, 0.14), pd); prop.position.set(-2.05, 2.05, s * 2.6); prop.name = "prop"; P.add(prop);
      }
      for (let i = 0; i < 9; i++) { const w = new THREE.Mesh(new THREE.BoxGeometry(0.32, 0.36, 0.05), pd); w.position.set(-3 + i * 0.75, 1.85, 0.85); P.add(w); }
      const doorM = new THREE.Mesh(new THREE.BoxGeometry(0.7, 1.3, 0.05), pd); doorM.position.set(2.6, 1.6, 0.86); P.add(doorM);
      for (const [x, z] of [[-3, 0], [1, 0.9], [1, -0.9]] as const) { const wh = new THREE.Mesh(new THREE.CylinderGeometry(0.28, 0.28, 0.2, 16).rotateX(Math.PI / 2), pd); wh.position.set(x, 0.28, z); P.add(wh); }
      P.traverse((o) => { (o as THREE.Mesh).castShadow = true; });
      R.add(P);
      // boarding stairs
      for (let i = 0; i < 6; i++) box(AIR + 1.45 - 0.35, 0, 1.0 + (5 - i) * 0.3, AIR + 1.45 + 0.35, 0.22 * (i + 1), 1.3 + (5 - i) * 0.3, lam("stairs", () => ({ color: "#d9dde3" })));
    }

    b.build(R); nb.build(R, false);
  }
  private dig: THREE.Group;
  private capCross: THREE.Group;

  private actor(i: number) { while (this.actors.length <= i) this.actors.push(new Actor(this.root)); return this.actors[i]; }
  private fx(i: number) { while (this.fxs.length <= i) this.fxs.push(new Fx(this.root)); return this.fxs[i]; }

  private shotSun(id: number) {
    let v = this.sunCache.get(id);
    if (v) return v;
    const s = SHOTS[id - 1], c = camAt(id, s.a), L = LIGHTS.day;
    const x = c.look[0] - c.pos[0], z = c.look[2] - c.pos[2], n = Math.hypot(x, z) || 1, fx = x / n, fz = z / n;
    const az = THREE.MathUtils.degToRad(L.az + 25), el = THREE.MathUtils.degToRad(s.set === "cut" ? 62 : 30);
    const hx = fx * Math.cos(az) - fz * Math.sin(az), hz = fz * Math.cos(az) + fx * Math.sin(az);
    v = new THREE.Vector3(hx * Math.cos(el), Math.sin(el), hz * Math.cos(el)).normalize();
    this.sunCache.set(id, v);
    return v;
  }

  update(id: number, f: number, cam: THREE.PerspectiveCamera, scene: THREE.Scene) {
    const t = f / FPS, s = SHOTS[id - 1], L = LIGHTS.day, K = LOOK.day;
    const c = camAt(id, f);
    cam.position.set(...c.pos); cam.up.set(0, 1, 0); cam.lookAt(...c.look); cam.rotateZ(c.roll);
    cam.fov = c.fov; cam.near = 0.05; cam.far = 1500; cam.updateProjectionMatrix(); cam.updateMatrixWorld();
    cam.layers.enable(NOINK);
    let focus = V(...c.look);
    const dist = cam.position.distanceTo(focus);
    // ---- light rig ----
    const sunDir = this.shotSun(id);
    this.hemi.color.set(L.sky); this.hemi.groundColor.set("#c9d4e8"); this.hemi.intensity = L.hemiI;
    this.sun.color.set("#fff0e4"); this.sun.intensity = L.sunI;
    const Rr = THREE.MathUtils.clamp(dist * 1.2 + 4, 6, 60);
    this.sun.position.copy(focus).addScaledVector(sunDir, 120); this.sun.target.position.copy(focus);
    const sc = this.sun.shadow.camera;
    sc.left = -Rr; sc.right = Rr; sc.top = Rr; sc.bottom = -Rr; sc.near = 20; sc.far = 260; sc.updateProjectionMatrix();
    this.sun.shadow.bias = L.bias; this.sun.shadow.normalBias = L.normalBias * (Rr / 12);
    TONE.uLitCol.value.set(...L.lit); TONE.uShadeCol.value.set(0.42, 0.45, 0.6); TONE.uShadeLift.value.set(0.07, 0.09, 0.15);
    TONE.uLambert.value = L.lambert; TONE.uSideK.value = L.sideK; TONE.uTerm.value = L.term; TONE.uBounce.value.set(...K.bounce); TONE.uSat.value = K.sat;
    CHAR.uCharTint.value.set(...L.charTint); CHAR.uCharShade.value = L.charShade; CHAR.uGrad.value = L.charGrad;
    CHAR.uBodyGrad.value = L.bodyGrad; CHAR.uSideTint.value.set(...L.sideTint);
    const su = this.skyMat.uniforms;
    ARCTIC.c.forEach((h, i) => untone(h, su["c" + i].value));
    const e = ARCTIC.e.map((deg) => THREE.MathUtils.degToRad(deg));
    su.e.value.set(e[1], e[2], e[3], e[4]);
    this.sky.position.copy(cam.position);
    untone("#e3e4f0", this.fog.color); this.fog.near = 40; this.fog.far = 340;
    scene.fog = this.fog; scene.background = null;

    // ---- props ----
    this.dig.visible = id === 8;
    this.door.rotation.y = -1.95 * doorAt(t) * (id === 6 ? 1 : 0);
    const pk = id === 10 ? planeAt(t) : 0;
    this.plane.position.set(AIR - 1 - 34 * pk * pk, 7 * Math.max(0, pk - 0.45) ** 2 * 4, -1.5);
    this.plane.rotation.z = -0.22 * smooth((pk - 0.4) / 0.4);
    this.plane.traverse((o) => { if (o.name === "prop") o.rotation.x = f * 1.3; });

    // ---- cast ----
    const P: Place[] = [], FX: FxPlace[] = [];
    const add = (key: string, draw: (p: Pen) => void, x: number, y: number, z: number, scale = 1, extra: Partial<Place> = {}) => P.push({ key, draw, x, y, z, scale, ...extra });
    const lid = (i: number) => blinkAt(f, i);
    const fig = (o: Outfit, i: number, expr: Expr, extra: Record<string, unknown> = {}, more: { belly?: boolean; cane?: boolean } = {}) => {
      const opts = { mode: "stand" as const, expr, blink: lid(i), light: LIGHT, seed: (i % 7) + 1, ...extra };
      return { key: `F|${JSON.stringify(o).length}|${o.jacket}|${o.skin}|${JSON.stringify(more)}|${JSON.stringify(opts, (_k, v) => (typeof v === "number" ? q(v) : v))}`, draw: (p: Pen) => person(p, o, opts, more) };
    };
    const card = (key: string, cw: number, ch: number, draw: (p: Pen) => void, x: number, y: number, z: number, w: number, h: number, s = 1) => {
      if (s <= 0.001) return;
      FX.push({ key, cw, ch, draw, x, y, z, w: w * s, h: h * s });
    };
    const set = s.set;

    if (set === "road") {
      const tt = id === 12 ? t - 52.1 : t; // shot 12 repeats the hook acting
      const turn = id === 1 ? tt > 2.55 && tt < 4.4 : tt > 2.1 && tt < 3.6;
      const a = fig(LOCAL, 1, turn ? "stern" : "neutral", { look: turn ? 0 : 0.8, headTilt: turn ? 0 : -0.08 });
      add(a.key, a.draw, ROAD + 0.75, 0, -1.7);
      focus = V(ROAD + 1.3, 1.85, -2.5);
    }
    if (set === "town" && id === 2) {
      const walk = clamp01((t - 5.0) / 6.0), ph = q((t * 1.4) % 1, 12);
      const scared = t > 10.2;
      const h = { key: `hunter|${ph}|${scared}|${lid(3)}`, draw: (p: Pen) => bodyFront(p, HUNTER, { mode: scared ? "stand" : "stroll", phase: ph, expr: scared ? "nervous" : "neutral", blink: lid(3), light: LIGHT, seed: 3, look: scared ? 0.8 : 0 }) };
      add(h.key, h.draw, TOWN + 0.4 + 2.2 * walk, 0, 0.6);
      const by = clamp01((t - 9.6) / 0.9);
      if (by > 0) add(`bear|${q(by, 10)}|${lid(9)}`, (p) => bear(p, -0.6 * by, lid(9)), TOWN + 4.9, 0, -6 + 2.6 * smooth(by), 1.35);
      for (let i = 0; i < 4; i++) { const a = fig(LOCAL, 20 + i, "neutral", { mode: "stroll", phase: q((t * 1.2 + i * 0.3) % 1, 12) }); add(a.key, a.draw, TOWN - 9 + i * 4.3 + 0.6 * t, 0, -1.5 - (i % 2) * 1.2, 1, { yaw: 0 }); }
    }
    if (set === "town" && id === 11) {
      for (let i = 0; i < 5; i++) { const a = fig(i % 2 ? LOCAL : NEIGHBOR, 30 + i, "neutral", { mode: "stroll", phase: q((t * 1.2 + i * 0.3) % 1, 12) }); add(a.key, a.draw, TOWN - 6 + i * 3 + 0.5 * (t - 49), 0, 0.5 - (i % 2) * 1.5); }
      card("cBorn", 900, 300, (p) => counter(p, "BORN HERE", "≈0", "#7ee08a"), TOWN + 0.4, 6.2, 2, 4.6, 1.53, pop(t, 49.9));
      card("cDied", 900, 300, (p) => counter(p, "DIED HERE", "≈0", "#ff7a7a"), TOWN + 0.4, 4.4, 2, 4.6, 1.53, pop(t, 51.35));
      focus = V(TOWN + 0.4, 4, 2);
    }
    if (set === "ground") {
      const a = fig(LOCAL, 4, "neutral", { look: 0.3 });
      add(a.key, a.draw, GROUND + 0.6, 0, -1.2, 0.9);
      card("thermo", 300, 900, thermo, GROUND + 1.5, -2.5, 0.3, 0.6, 1.8, pop(t, 13.7));
      focus = t < 12 ? V(GROUND, 0.9, 0) : V(GROUND, -2.6, 0);
    }
    if (set === "cem" && id === 4) {
      if (t < 18.55) {
        for (let i = 0; i < 3; i++) { const a = fig(MINER(i), 40 + i, t > 17.3 ? "nervous" : "neutral", { look: t > 17.3 ? -0.5 : 0 }); add(a.key, a.draw, CEM - 1.1 + i * 1.1, 0, 2.3 + 0.3 * (i % 2)); }
        for (let i = 0; i < 9; i++) {
          const u = clamp01((t - 16.0 - i * 0.12) / 2.2), x = CEM - 6 + 6.5 * u + (i % 3) * 1.1, y = 1.6 + 1.4 * ((i * 0.37) % 1) + 0.15 * Math.sin(t * 3 + i);
          if (u > 0) add(`germ|${i % 3}|${lid(50 + i)}`, (p) => germ(p, "neutral", lid(50 + i), 0, i % 3), x, y, 3.4 - (i % 3) * 0.7, 0.3);
        }
      }
      focus = t < 18.6 ? V(CEM, 1.1, 0) : V(CEM, 0.7, -3.4);
    }
    if (set === "cut") focus = V(CUT, -2.2, -2);
    if (set === "freezer") {
      const open = doorAt(t);
      if (open > 0.6) for (let i = 0; i < 3; i++) {
        const w = t > 28.1 ? (t - 28.1 + i * 0.2) : 0;
        add(`germ|${i}|${q(w % 1, 12)}|${lid(60 + i)}`, (p) => germ(p, "neutral", lid(60 + i), w > 0 ? w % 1 : 0, i), FREEZER - 0.9 + i * 0.9, 2.91, -0.1, 0.48);
      }
      const nerv = t > 28.2;
      const a = fig(NEIGHBOR, 7, t > 29.7 ? "stern" : nerv ? "nervous" : "neutral", { look: nerv ? -0.8 : 0 });
      add(a.key, a.draw, FREEZER + 2.6, 0, 1.6);
      if (open > 0 && open < 1) card(`puff|${q(open, 10)}`, 300, 300, (p) => fxPuff(p, open), FREEZER, 2.3, 1.4, 2.6, 2.6);
      focus = t < 28 ? V(FREEZER, 2.2, 0) : V(FREEZER + 1.6, 1.7, 0.4);
    }
    if (set === "cem" && id === 7) {
      const k = stampAt(t);
      if (k > 0) card("closed", 800, 300, closedStamp, CEM, 1.25, 1.42, 1.9, 0.71, 1 + 1.6 * (1 - k) * (1 - k));
      focus = V(CEM, 1.2, 1.2);
    }
    if (set === "cem" && id === 8) {
      for (const [i, x, z] of [[0, 0.55, -2.25], [1, 1.95, -2.1]] as const) {
        const st = ((t * 1.6 + i * 0.5) % 1), k = st < 0.3 ? smooth(st / 0.3) : 1 - smooth((st - 0.3) / 0.7);
        const a = fig(SUIT, 70 + i, t > 37.3 ? "shock" : "neutral", { prop: ["hammer", q(k, 10)] });
        add(a.key, a.draw, CEM + x, 0, z);
      }
      if (t > 37.2) { const u = clamp01((t - 37.2) / 0.6); add(`germ|0|${lid(80)}`, (p) => germ(p, "grin", lid(80), 0, 0), CEM + 1.2, 0.2 + 0.9 * smooth(u), -2.85, 0.45); }
      card("toll", 1000, 360, deathToll, CEM + 1.4, 3.1, -2.4, 2.4, 0.86, pop(t, 38.0));
      focus = V(CEM + 1.3, 1.0, -2.6);
    }
    if (set === "air" && id === 9) {
      const a = fig(OLD, 8, t > 44.1 ? "stern" : "neutral", { look: t > 44.1 ? 0.6 : 0 }, { cane: true });
      add(a.key, a.draw, AIR + 3.0, 0, 2.4);
      card("ticket", 900, 420, ticket, AIR + 2.25, 1.6, 2.75, 0.95, 0.44, pop(t, 43.85));
      focus = V(AIR + 3.0, 1.2, 2.4);
    }
    if (set === "air" && id === 10) {
      const u = clamp01((t - 45.0) / 1.7);
      if (u < 1) { const ph = q((t * 1.4) % 1, 12), a = fig(MUM, 9, "neutral", { mode: "stroll", phase: ph }, { belly: true }); add(a.key, a.draw, AIR + 4.6 - 3.0 * u, 0.0 + 1.0 * Math.max(0, (u - 0.6) / 0.4), 1.9 - 0.6 * u); }
      card("south", 700, 300, (p) => arrow(p, "SOUTH"), AIR - 9, 7.5, -1.5, 4.2, 1.8, pop(t, 47.5));
      focus = V(AIR + 1, 1.6, 0);
    }

    // ---- place cards ----
    let ai = 0;
    const used: Actor[] = [];
    for (const p of P) {
      const sc2 = p.scale ?? 1, d = cam.position.distanceTo(V(p.x, p.y + 1.1 * sc2, p.z)) / sc2;
      const [w, h, k] = tier(d);
      const a = this.actor(ai++);
      a.r = this.pool.req(p.key, w, h, k, p.draw);
      a.mesh.visible = true;
      a.mesh.position.set(p.x, p.y, p.z);
      a.mesh.rotation.set(0, p.yaw ?? Math.atan2(cam.position.x - p.x, cam.position.z - p.z), p.roll ?? 0);
      a.mesh.scale.set(p.mirror ? -sc2 : sc2, sc2, sc2);
      a.mesh.castShadow = true;
      used.push(a);
    }
    for (let i = ai; i < this.actors.length; i++) this.actors[i].mesh.visible = false;
    let fi = 0;
    const fused: Fx[] = [];
    for (const p of FX) {
      const e2 = this.fx(fi++);
      e2.r = this.pool.req(p.key, p.cw, p.ch, 1, p.draw);
      e2.use(!!p.soft); e2.mesh.visible = true;
      e2.mesh.position.set(p.x, p.y, p.z); e2.mesh.quaternion.copy(cam.quaternion); e2.mesh.scale.set(p.w, p.h, 1);
      fused.push(e2);
    }
    for (let i = fi; i < this.fxs.length; i++) this.fxs[i].mesh.visible = false;
    this.pool.flush();
    for (const a of used) a.bind();
    for (const e2 of fused) e2.bind();
    return focus;
  }
}
