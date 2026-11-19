// The Lake Nyos short as one three.js scene: five stage sets side by side along x (crater lake, hillside village,
// lake cutaway, soda-bottle table, hut doorway). Same look rules as the bridge: two-tone materials (lam/twoTone),
// painted textures, camera-relative sun (the moon at night) frozen per shot, lit character cards on NOINK.
import * as THREE from "three";
import { Batch, boxGeo, V, lam, quad } from "../bridge/build";
import { ctex, rep, grassHD, planksHD, rng } from "../bridge/paint";
import { Expr, fxPuff, fxSplash, Pen } from "../bridge/toon";
import { LIGHTS, LOOK, LightPreset } from "../bridge/lights";
import { TONE, CHAR, untone, twoTone } from "../bridge/shade";
import { NOINK } from "../bridge/ink";
import { Pool, Actor, Fx } from "../bridge/cast";
import { bubble, cowLying, lantern, LIGHT } from "./chars";
import {
  FPS, SHOTS, LAKE, VILLAGE, SECTION, SODA, HUT, Mood, camAt, bubbleAt, slideAt, shakeAt, popAt, fizzAt, spreadAt, rollAt,
  lampAt, burpAt, smooth, clamp01,
} from "./story";

type Place = { key: string; draw: (p: Pen) => void; x: number; y: number; z: number; scale?: number; yaw?: number; roll?: number };
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

// ---------------- light moods ----------------
const NIGHT: LightPreset = {
  ...LIGHTS.day, el: 34,
  lit: [0.34, 0.42, 0.74], shade: [0.06, 0.07, 0.16], lift: [0.02, 0.03, 0.07],
  charTint: [0.55, 0.62, 0.9], charShade: 0.8, sideTint: [0.8, 0.85, 1.0],
  fog: "#1c2a52", sunCol: "#b8c8ff", sunI: 1.4, sky: "#3a4a7a", ground: "#1a1a2a", hemiI: 0.3,
};
const DAWN: LightPreset = {
  ...LIGHTS.day, el: 22,
  lit: [1.32, 1.14, 1.08], shade: [0.34, 0.34, 0.46], lift: [0.06, 0.06, 0.12],
  charTint: [0.98, 0.9, 0.9], fog: "#d9d2da", sunCol: "#ffe2cc",
};
const PRESET: Record<Mood, LightPreset> = { night: NIGHT, dawn: DAWN, day: LIGHTS.day };
const SKY: Record<Mood, { c: string[]; e: number[] }> = {
  night: { c: ["#2c3c6c", "#24335f", "#1b2852", "#131d42", "#0b1230"], e: [0, 3, 8, 16, 40] },
  dawn: { c: ["#f4d9c6", "#e8d2d2", "#cfcfe0", "#b2c0de", "#93abd6"], e: [0, 3, 8, 16, 40] },
  day: LOOK.day.sky,
};
export const GRADE_AMT: Record<Mood, number> = { night: 0.55, dawn: 0.8, day: 1 };

// ---------------- painted textures ----------------
const thatch = () => ctex("thatch", 512, 512, (g, r) => {
  g.fillStyle = "#c9a35a"; g.fillRect(0, 0, 512, 512);
  for (let i = 0; i < 900; i++) { const x = 512 * r(), y = 512 * r(); g.strokeStyle = `rgba(${r() < 0.5 ? "120,85,40" : "235,205,140"},0.5)`; g.lineWidth = 2 + 2 * r(); g.beginPath(); g.moveTo(x, y); g.lineTo(x + 6 * (r() - 0.5), y + 30 + 30 * r()); g.stroke(); }
  for (let y = 60; y < 512; y += 90) { g.fillStyle = "rgba(110,75,35,0.55)"; g.fillRect(0, y, 512, 7); }
});
const mud = () => ctex("mud", 512, 512, (g, r) => {
  g.fillStyle = "#c98b5a"; g.fillRect(0, 0, 512, 512);
  for (let i = 0; i < 300; i++) { g.fillStyle = `rgba(${r() < 0.5 ? "150,95,55" : "225,170,120"},${0.15 + 0.2 * r()})`; g.beginPath(); g.ellipse(512 * r(), 512 * r(), 6 + 20 * r(), 4 + 10 * r(), r() * 3, 0, 7); g.fill(); }
});
const dirt = () => ctex("dirtPath", 512, 512, (g, r) => {
  g.fillStyle = "#b8865a"; g.fillRect(0, 0, 512, 512);
  for (let i = 0; i < 700; i++) { g.fillStyle = `rgba(${r() < 0.5 ? "120,80,50" : "220,180,130"},${0.2 * r()})`; g.fillRect(512 * r(), 512 * r(), 3 + 6 * r(), 3 + 4 * r()); }
});
const earthTex = (key: string, a: string, b: string) => ctex(key, 512, 512, (g, r) => {
  g.fillStyle = a; g.fillRect(0, 0, 512, 512);
  for (let i = 0; i < 260; i++) { g.fillStyle = b; g.globalAlpha = 0.25 + 0.4 * r(); g.beginPath(); g.ellipse(512 * r(), 512 * r(), 6 + 16 * r(), 4 + 8 * r(), r() * 3, 0, 7); g.fill(); }
  g.globalAlpha = 1;
});
const label = () => ctex("nyosLabel", 1024, 256, (g) => {
  g.fillStyle = "#e8443a"; g.fillRect(0, 0, 1024, 256);
  g.fillStyle = "#fff6e0"; g.fillRect(0, 22, 1024, 10); g.fillRect(0, 224, 1024, 10);
  g.font = "900 120px sans-serif"; g.textAlign = "center"; g.textBaseline = "middle";
  for (const x of [256, 768]) { g.lineWidth = 16; g.strokeStyle = "#3a1018"; g.strokeText("NYOS", x, 132); g.fillStyle = "#ffffff"; g.fillText("NYOS", x, 132); }
});

const SKY_V = "varying vec3 vP; void main(){ vP = normalize(position); gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0); }";
const SKY_F = `uniform vec3 c0, c1, c2, c3, c4; uniform vec4 e; varying vec3 vP;
  void main(){ float el = asin(clamp(normalize(vP).y, -1.0, 1.0));
    vec3 c = mix(c0, c1, smoothstep(0.0, e.x, el)); c = mix(c, c2, smoothstep(e.x, e.y, el));
    c = mix(c, c3, smoothstep(e.y, e.z, el)); c = mix(c, c4, smoothstep(e.z, e.w, el)); gl_FragColor = vec4(c, 1.0); }`;

// ---------------- terrain heights ----------------
const LAKE_R = 30;
const noise2 = (x: number, z: number) => Math.sin(x * 0.21 + Math.sin(z * 0.13) * 2) * Math.cos(z * 0.17 + x * 0.05) + 0.5 * Math.sin(x * 0.53 + z * 0.41);
/** crater: lake bed below 0 inside LAKE_R, steep green walls to a 14 m rim at ~48 m, rolling hills beyond */
export const craterH = (x: number, z: number) => {
  const r = Math.hypot(x, z);
  if (r < LAKE_R) return -2.5 * (1 - (r / LAKE_R) ** 2) - 0.2;
  const wall = 15 * smooth((r - LAKE_R + 1) / 17) + 0.6 * noise2(x, z) * smooth((r - LAKE_R) / 6);
  return r < 48 ? wall : 15 + 1.2 * noise2(x * 0.5, z * 0.5) - 0.08 * (r - 48);
};
/** village: flat valley floor, hill rising to the north (-z) */
export const villageH = (x: number, z: number) => (z < -3 ? (-z - 3) * 0.32 + 0.4 * noise2(x, z) * smooth((-z - 3) / 6) : 0) + 0.05 * noise2(x * 2, z * 2);

const terrain = (size: number, seg: number, h: (x: number, z: number) => number, cx: number, mat: THREE.Material) => {
  const g = new THREE.PlaneGeometry(size, size, seg, seg); g.rotateX(-Math.PI / 2);
  const p = g.attributes.position as THREE.BufferAttribute;
  for (let i = 0; i < p.count; i++) p.setY(i, h(p.getX(i), p.getZ(i)));
  g.computeVertexNormals(); g.translate(cx, 0, 0);
  const m = new THREE.Mesh(g, mat); m.receiveShadow = true; m.castShadow = true;
  return m;
};

export class World {
  root = new THREE.Group();
  private pool = new Pool();
  private actors: Actor[] = [];
  private fxs: Fx[] = [];
  private hemi = new THREE.HemisphereLight("#cfe6ff", "#6c5c8c", 1.1);
  private sun = new THREE.DirectionalLight("#fff0d6", 2.6);
  private fog = new THREE.Fog("#bccbec", 25, 300);
  private skyMat: THREE.ShaderMaterial; private sky: THREE.Mesh;
  private sunCache = new Map<number, THREE.Vector3>();
  private night = new THREE.Group();             // moon, stars, moon glitter
  private lakeMat: THREE.MeshLambertMaterial;
  private rocks: THREE.Mesh[] = []; private rockHome: THREE.Vector3[] = [];
  private puffs: THREE.Mesh[] = [];               // eruption column + cloud (lake) / rolling cloud (village)
  private mist: THREE.Mesh[] = [];                // low mist at the hut
  private ripples: THREE.Mesh[] = [];
  private raft = new THREE.Group(); private jet: THREE.Mesh;
  private bottle = new THREE.Group(); private cap: THREE.Mesh; private foam: THREE.Mesh[] = [];
  private flame: THREE.Mesh; private glit!: THREE.Mesh; private jetTop!: THREE.Mesh;
  private softPuff!: THREE.Material; private hardPuff!: THREE.Material;

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

    const b = new Batch();
    const box = (x0: number, y0: number, z0: number, x1: number, y1: number, z1: number, m: THREE.Material, tile = 0) => b.add(boxGeo(V(x0, y0, z0), V(x1, y1, z1), tile), m);
    const grassM = lam("nyosGrass", () => ({ map: rep(grassHD(), 30, 30) }));
    const rockM = lam("nyosRock", () => ({ map: rep(earthTex("rockT", "#8a8578", "#5f5a52"), 1, 1) }));
    const mudM = lam("mud", () => ({ map: rep(mud(), 2, 1) }));
    const thatchM = lam("thatch", () => ({ map: rep(thatch(), 3, 1) }));
    const leafM = lam("leaf", () => ({ color: "#3f8f45" })), leaf2 = lam("leaf2", () => ({ color: "#57a64a" })), bark = lam("bark", () => ({ color: "#7a5236" }));
    const white = lam("puff", () => ({ color: "#ffffff" }));
    this.softPuff = new THREE.MeshLambertMaterial({ color: "#e9eef8", transparent: true, opacity: 0.62, depthWrite: false }); this.hardPuff = white;
    const rnd = rng(11);
    const tree = (x: number, y: number, z: number, s: number) => {
      b.add(new THREE.CylinderGeometry(0.12 * s, 0.18 * s, 2.2 * s, 7).translate(x, y + 1.1 * s, z), bark);
      b.add(new THREE.IcosahedronGeometry(1.1 * s, 1).scale(1, 0.85, 1).translate(x, y + 2.6 * s, z), rnd() < 0.5 ? leafM : leaf2);
      b.add(new THREE.IcosahedronGeometry(0.8 * s, 1).translate(x + 0.6 * s, y + 2.2 * s, z + 0.3 * s), rnd() < 0.5 ? leafM : leaf2);
    };
    const hut = (x: number, y: number, z: number, s: number, yaw: number) => {
      b.add(new THREE.CylinderGeometry(1.5 * s, 1.55 * s, 2.0 * s, 20).translate(x, y + 1.0 * s, z), mudM);
      b.add(new THREE.ConeGeometry(2.1 * s, 1.9 * s, 20).translate(x, y + 2.0 * s + 0.95 * s, z), thatchM);
      const d = new THREE.BoxGeometry(0.75 * s, 1.35 * s, 0.2); d.translate(0, y + 0.675 * s, 1.47 * s); d.rotateY(yaw); d.translate(x, 0, z);
      b.add(d, lam("doorDark", () => ({ color: "#1c1418" })));
    };

    // ---- CRATER LAKE ----
    R.add(terrain(300, 200, (x, z) => craterH(x, z), LAKE, grassM));
    this.lakeMat = lam("lakeWater", () => ({ color: "#2f78b8" })) as THREE.MeshLambertMaterial;
    const lake = new THREE.Mesh(new THREE.CircleGeometry(LAKE_R + 1.5, 96).rotateX(-Math.PI / 2), this.lakeMat);
    lake.position.set(LAKE, 0, 0); lake.receiveShadow = true; R.add(lake);
    for (let i = 0; i < 46; i++) { // rocks along the shore + trees on the walls
      const a = rnd() * Math.PI * 2, r = LAKE_R + 1 + rnd() * 3;
      b.add(new THREE.DodecahedronGeometry(0.4 + rnd() * 0.9).scale(1, 0.6, 1).translate(LAKE + Math.cos(a) * r, craterH(Math.cos(a) * r, Math.sin(a) * r), Math.sin(a) * r), rockM);
    }
    for (let i = 0; i < 70; i++) {
      const a = rnd() * Math.PI * 2, r = LAKE_R + 6 + rnd() * 30, x = Math.cos(a) * r, z = Math.sin(a) * r;
      if (z > 20 && Math.abs(x) < 25) continue; // keep the camera side open
      tree(LAKE + x, craterH(x, z) - 0.2, z, 1.4 + rnd() * 1.2);
    }
    // the landslide: a bare scar on the west wall + boulders that slide in (shot 7)
    for (let i = 0; i < 7; i++) {
      const m = new THREE.Mesh(new THREE.DodecahedronGeometry(0.9 + 0.5 * rnd()), rockM as THREE.Material);
      const home = V(LAKE - 38 - 2 * rnd(), 0, -4 + 5 * rnd()); home.y = craterH(home.x - LAKE, home.z) + 0.6;
      m.position.copy(home); m.castShadow = true; R.add(m); this.rocks.push(m); this.rockHome.push(home);
    }
    // degassing raft + pipe + jet (shot 13)
    const raftM = lam("raft", () => ({ map: rep(planksHD(), 1, 1) })), pipeM = twoTone(new THREE.MeshPhongMaterial({ color: "#d8dde4", specular: "#ffffff", shininess: 40 }), 0.15);
    const raftBase = new THREE.Mesh(new THREE.BoxGeometry(3, 0.35, 3), raftM); raftBase.position.y = 0.1;
    const floats = [-1.2, 1.2].map((x) => { const f = new THREE.Mesh(new THREE.CylinderGeometry(0.3, 0.3, 3, 14).rotateX(Math.PI / 2), lam("float", () => ({ color: "#e8562f" }))); f.position.set(x, 0, 0); return f; });
    const pipe = new THREE.Mesh(new THREE.CylinderGeometry(0.16, 0.16, 2.2, 16), pipeM); pipe.position.y = 1.3;
    this.jet = new THREE.Mesh(new THREE.CylinderGeometry(0.2, 0.22, 1, 16, 1, true), lam("jet", () => ({ color: "#bfe6f7" })));
    this.jetTop = new THREE.Mesh(new THREE.IcosahedronGeometry(0.55, 2), lam("jet", () => ({ color: "#bfe6f7" })));
    this.raft.add(raftBase, ...floats, pipe, this.jet, this.jetTop); this.raft.position.set(LAKE + 1, 0, 4);
    for (const m of [raftBase, pipe, ...floats]) { m.castShadow = true; m.receiveShadow = true; }
    R.add(this.raft);
    // moon, stars, moonlight glitter
    const moon = new THREE.Mesh(new THREE.SphereGeometry(16, 24, 16), new THREE.MeshBasicMaterial({ color: new THREE.Color(2.4, 2.4, 2.1), fog: false }));
    moon.position.set(LAKE - 90, 70, -700); moon.layers.set(NOINK);
    const sp: number[] = [], sr = rng(5);
    for (let i = 0; i < 500; i++) { const a = sr() * Math.PI * 2, el = 0.12 + sr() * 1.3; sp.push(Math.cos(a) * Math.cos(el) * 900, Math.sin(el) * 900, Math.sin(a) * Math.cos(el) * 900); }
    const sg = new THREE.BufferGeometry(); sg.setAttribute("position", new THREE.Float32BufferAttribute(sp, 3));
    const stars = new THREE.Points(sg, new THREE.PointsMaterial({ color: "#ffffff", size: 2.2, sizeAttenuation: false, fog: false, transparent: true, opacity: 0.85 }));
    stars.layers.set(NOINK); stars.frustumCulled = false; stars.renderOrder = -1;
    const gtex = ctex("glitter", 256, 1024, (g, r) => { for (let i = 0; i < 90; i++) { const y = 1024 * r(), w = 40 + 160 * r() * (1 - Math.abs(y - 512) / 700); g.fillStyle = `rgba(220,230,255,${0.5 + 0.5 * r()})`; g.fillRect(128 - w / 2, y, w, 4 + 6 * r()); } });
    this.glit = new THREE.Mesh(new THREE.PlaneGeometry(9, 48).rotateX(-Math.PI / 2), new THREE.MeshBasicMaterial({ map: gtex, transparent: true, depthWrite: false, fog: false }));
    this.glit.position.set(LAKE - 3.5, 0.03, -6); this.glit.rotation.y = -0.12; this.glit.layers.set(NOINK);
    this.night.add(moon, stars); R.add(this.glit); R.add(this.night);
    // ripple rings for the single bubble (shot 2)
    for (let i = 0; i < 3; i++) {
      const m = new THREE.Mesh(new THREE.TorusGeometry(1, 0.03, 6, 48).rotateX(Math.PI / 2), new THREE.MeshBasicMaterial({ color: "#cfe0ff", transparent: true, depthWrite: false }));
      m.layers.set(NOINK); R.add(m); this.ripples.push(m);
    }
    // puffs: shared by the lake eruption and the village cloud (posed per shot)
    const pg = new THREE.IcosahedronGeometry(1, 2);
    for (let i = 0; i < 170; i++) { const m = new THREE.Mesh(pg, white); m.castShadow = false; m.receiveShadow = true; m.visible = false; R.add(m); this.puffs.push(m); }

    // ---- VILLAGE ----
    R.add(terrain(160, 120, (x, z) => villageH(x, z), VILLAGE, grassM));
    b.add(quad(V(VILLAGE - 1.3, 0.04, 30), V(VILLAGE + 1.3, 0.04, 30), V(VILLAGE + 1.3, 0.04, -3), V(VILLAGE - 1.3, 0.04, -3), 1, 12), lam("dirt", () => ({ map: rep(dirt(), 1, 1) })));
    const huts: [number, number, number, number][] = [[-4.2, -1, 1.0, 0.4], [4.0, 2, 0.95, -0.5], [-5, 7, 1.05, 0.9], [4.6, 9, 1.0, -0.9], [-3.8, -7, 0.9, 0.2], [3.5, -9, 0.95, -0.2], [-1.5, -15, 0.85, 0], [6, -16, 0.9, -0.3], [-7.5, 2.5, 0.9, 1.2]];
    for (const [x, z, s, yaw] of huts) hut(VILLAGE + x, villageH(x, z) - 0.05, z, s, yaw);
    for (let i = 0; i < 40; i++) { const x = (rnd() - 0.5) * 70, z = -6 - rnd() * 40; if (Math.abs(x) < 9 && z > -18) continue; tree(VILLAGE + x, villageH(x, z) - 0.2, z, 1 + rnd()); }
    for (let i = 0; i < 12; i++) tree(VILLAGE + (rnd() < 0.5 ? -1 : 1) * (12 + rnd() * 20), 0, 10 + rnd() * 20, 1 + rnd() * 0.8);
    for (let k = 0; k < 14; k++) { const x = 7.5 + k * 1.2; box(VILLAGE + x - 0.05, 0, 0.9, VILLAGE + x + 0.05, 1.0, 1.0, bark); } // field fence
    box(VILLAGE + 7.5, 0.7, 0.92, VILLAGE + 23.3, 0.78, 0.98, bark);

    // ---- SECTION (lake cutaway diorama facing +z) ----
    const SX = SECTION, W0 = 7, RIM = 1.5, WL = 1.0, LAYER = -0.9, BOT = -4.6, BW = 4.3;
    const bowl = (x: number) => RIM - (RIM - BOT) * Math.max(0, 1 - (x / BW) ** 2) ** 0.6;
    const ext = (pts: [number, number][], m: THREE.Material, z0: number, depth: number) => {
      const sh = new THREE.Shape(pts.map(([x, y]) => new THREE.Vector2(x, y)));
      const g = new THREE.ExtrudeGeometry(sh, { depth, bevelEnabled: false, curveSegments: 1 }); g.translate(SX, 0, z0);
      b.add(g, m);
    };
    const curve = (y0: number, y1: number, rev = false) => { // basin wall points between depths, right side then left
      const pts: [number, number][] = [];
      for (let i = 0; i <= 40; i++) { const x = BW - (2 * BW * i) / 40, y = bowl(x); if (y >= y0 && y <= y1) pts.push([x, y]); }
      return rev ? pts.reverse() : pts;
    };
    const earthM = lam("earth", () => ({ map: rep(earthTex("earthT", "#9a6b48", "#7a5036"), 2, 2) }));
    const deepRock = lam("deepRock", () => ({ map: rep(earthTex("deepT", "#5a4652", "#3e2f3a"), 2, 2) }));
    ext([[-W0, -6], [W0, -6], [W0, RIM], [BW, RIM], ...curve(-99, RIM), [-BW, RIM], [-W0, RIM]], earthM, -4, 4);
    ext([[-W0, -12], [W0, -12], [W0, -6], [-W0, -6]], deepRock, -4, 4);
    ext([[-W0, RIM], [-BW, RIM], [-BW, RIM + 0.25], [-W0, RIM + 0.25]], grassM, -4, 4);
    ext([[BW, RIM], [W0, RIM], [W0, RIM + 0.25], [BW, RIM + 0.25]], grassM, -4, 4);
    const wx = (y: number) => BW * Math.sqrt(Math.max(0, 1 - Math.max(0, (RIM - y) / (RIM - BOT)) ** (1 / 0.6))); // half-width at depth y
    const topW = lam("topWater", () => ({ color: "#86d3f2" })), deepW = lam("deepWater", () => ({ color: "#1f5e78" }));
    const layerPts = (y0: number, y1: number): [number, number][] => { const l: [number, number][] = []; for (let i = 0; i <= 16; i++) { const y = y1 - ((y1 - y0) * i) / 16; l.push([wx(y), y]); } for (let i = 0; i <= 16; i++) { const y = y0 + ((y1 - y0) * i) / 16; l.push([-wx(y), y]); } return l; };
    ext(layerPts(LAYER, WL), topW, -3.9, 3.85);
    ext(layerPts(BOT + 0.02, LAYER), deepW, -3.9, 3.85);
    // magma pocket + feeder crack (emissive, feeds the bloom)
    const hot = new THREE.MeshBasicMaterial({ color: new THREE.Color(3.2, 0.55, 0.08) });
    const mag = new THREE.Mesh(new THREE.SphereGeometry(1, 32, 16).scale(3.2, 1.4, 0.4), hot); mag.position.set(SX, -9, 0.05); mag.layers.set(NOINK); R.add(mag);
    const crack = new THREE.Mesh(new THREE.PlaneGeometry(0.35, 4.6), new THREE.MeshBasicMaterial({ color: new THREE.Color(2.0, 0.55, 0.15) })); crack.position.set(SX + 0.4, -6.4, 0.06); crack.rotation.z = 0.12; crack.layers.set(NOINK); R.add(crack);
    tree(SX - 5.6, RIM + 0.2, -2, 0.9); tree(SX + 5.8, RIM + 0.2, -2.5, 1.0);
    hut(SX - 6.2, RIM + 0.2, -3.5, 0.6, 0.3);
    R.add(terrain(120, 40, () => -12.5, SX, grassM)); // ground under the diorama

    // ---- SODA (table + bottle) ----
    const wood = lam("planksHD", () => ({ map: planksHD() }));
    b.add(quad(V(SODA - 6, 0, 3), V(SODA + 6, 0, 3), V(SODA + 6, 0, -2), V(SODA - 6, 0, -2), 3, 2), lam("sodaFloor", () => ({ color: "#5a6a8a" })));
    b.add(quad(V(SODA - 6, 0, -1.2), V(SODA + 6, 0, -1.2), V(SODA + 6, 4, -1.2), V(SODA - 6, 4, -1.2), 1, 1), lam("sodaWall", () => ({ map: rep(earthTex("sodaWallT", "#f2c94c", "#f6d878"), 4, 2) })));
    box(SODA - 1.5, 0.84, -0.8, SODA + 1.5, 0.9, 0.8, wood, 1);
    for (const x of [-1.4, 1.4]) for (const z of [-0.7, 0.7]) box(SODA + x - 0.04, 0, z - 0.04, SODA + x + 0.04, 0.84, z + 0.04, bark);
    const prof: THREE.Vector2[] = [];
    const bp: [number, number][] = [[0, 0], [0.2, 0], [0.22, 0.03], [0.22, 0.62], [0.2, 0.72], [0.12, 0.82], [0.075, 0.88], [0.075, 0.96]];
    for (const [r, y] of bp) prof.push(new THREE.Vector2(r, y));
    const glassM = new THREE.MeshPhongMaterial({ color: "#d9fff0", specular: "#ffffff", shininess: 90, transparent: true, opacity: 0.28, depthWrite: false, side: THREE.DoubleSide });
    const shell = new THREE.Mesh(new THREE.LatheGeometry(prof, 40), glassM); shell.renderOrder = 3;
    const liq = (y0: number, y1: number, col: string, _key: string) => { const m = new THREE.Mesh(new THREE.CylinderGeometry(0.205, 0.205, y1 - y0, 32), new THREE.MeshPhongMaterial({ color: col, transparent: true, opacity: 0.5, depthWrite: false, shininess: 30 })); m.renderOrder = 2; m.position.y = (y0 + y1) / 2; return m; };
    const lbl = new THREE.Mesh(new THREE.CylinderGeometry(0.224, 0.224, 0.2, 40, 1, true, Math.PI * 0.6, Math.PI * 0.8), lam("nyosLabelM", () => ({ map: label() }))); lbl.position.y = 0.45;
    this.cap = new THREE.Mesh(new THREE.CylinderGeometry(0.085, 0.085, 0.06, 20), twoTone(new THREE.MeshPhongMaterial({ color: "#e23b3b", specular: "#ffffff", shininess: 60 }), 0.15));
    this.cap.position.y = 0.975;
    this.bottle.add(liq(0.02, 0.34, "#2a6f8c", "sodaDeep"), liq(0.34, 0.66, "#9be0f5", "sodaTop"), shell, this.cap); void lbl;
    this.bottle.position.set(SODA, 0.9, 0); R.add(this.bottle);
    for (let i = 0; i < 40; i++) { const m = new THREE.Mesh(pg, white); m.visible = false; R.add(m); this.foam.push(m); }

    // ---- HUT doorway (quiet beat) ----
    R.add(terrain(60, 30, (x, z) => 0.04 * noise2(x * 3, z * 3), HUT, lam("dirtGround", () => ({ map: rep(dirt(), 8, 8) }))));
    b.add(new THREE.CylinderGeometry(2.4, 2.45, 2.6, 40).translate(HUT, 1.3, -2.4), mudM);
    b.add(new THREE.ConeGeometry(3.1, 2.4, 40).translate(HUT, 2.6 + 1.2, -2.4), thatchM);
    box(HUT - 0.42, 0, -0.1, HUT + 0.42, 1.55, 0.12, lam("doorDark", () => ({ color: "#1c1418" })));
    box(HUT - 0.5, 1.55, -0.12, HUT + 0.5, 1.65, 0.14, bark);
    for (const x of [-0.5, 0.5]) box(HUT + x - 0.05, 0, -0.12, HUT + x + 0.05, 1.65, 0.14, bark);
    box(HUT + 0.62, 1.3, -0.02, HUT + 0.66, 1.34, 0.22, bark); // lantern hook
    for (const [x, z] of [[-1.3, 0.6], [1.4, 0.4]]) b.add(new THREE.CylinderGeometry(0.22, 0.18, 0.4, 14).translate(HUT + x, 0.2, z), lam("pot", () => ({ color: "#a65a3a" })));
    this.flame = new THREE.Mesh(new THREE.SphereGeometry(0.04, 10, 8), new THREE.MeshBasicMaterial({ color: new THREE.Color(3, 2, 0.8) }));
    this.flame.position.set(HUT + 0.64, 1.12, 0.2); this.flame.layers.set(NOINK); R.add(this.flame);
    for (let i = 0; i < 26; i++) { const m = new THREE.Mesh(pg, new THREE.MeshLambertMaterial({ color: "#dfe6f2", transparent: true, opacity: 0.55, depthWrite: false })); m.renderOrder = 2; R.add(m); this.mist.push(m); }

    b.build(R);
  }

  private actor(i: number) { while (this.actors.length <= i) this.actors.push(new Actor(this.root)); return this.actors[i]; }
  private fx(i: number) { while (this.fxs.length <= i) this.fxs.push(new Fx(this.root)); return this.fxs[i]; }

  private shotSun(id: number, L: LightPreset) {
    let v = this.sunCache.get(id);
    if (v) return v;
    const s = SHOTS[id - 1], c = camAt(id, s.a);
    const x = c.look[0] - c.pos[0], z = c.look[2] - c.pos[2], n = Math.hypot(x, z) || 1, fx = x / n, fz = z / n;
    const az = THREE.MathUtils.degToRad(s.mood === "night" ? 140 : L.az + 25), el = THREE.MathUtils.degToRad(L.el);
    const hx = fx * Math.cos(az) - fz * Math.sin(az), hz = fz * Math.cos(az) + fx * Math.sin(az);
    v = new THREE.Vector3(hx * Math.cos(el), Math.sin(el), hz * Math.cos(el)).normalize();
    this.sunCache.set(id, v);
    return v;
  }

  update(id: number, f: number, cam: THREE.PerspectiveCamera, scene: THREE.Scene) {
    const t = f / FPS, s = SHOTS[id - 1], L = PRESET[s.mood], K = LOOK.day;
    const c = camAt(id, f);
    cam.position.set(...c.pos); cam.up.set(0, 1, 0); cam.lookAt(...c.look); cam.rotateZ(c.roll);
    cam.fov = c.fov; cam.near = 0.05; cam.far = 1500; cam.updateProjectionMatrix(); cam.updateMatrixWorld();
    cam.layers.enable(NOINK);
    let focus = V(...c.look);
    const dist = cam.position.distanceTo(focus);
    // ---- light rig ----
    const sunDir = this.shotSun(id, L);
    this.hemi.color.set(L.sky); this.hemi.groundColor.set(L.ground); this.hemi.intensity = L.hemiI;
    this.sun.color.set(L.sunCol); this.sun.intensity = L.sunI;
    const Rr = THREE.MathUtils.clamp(dist * 1.2 + 4, 5, 80);
    this.sun.position.copy(focus).addScaledVector(sunDir, 160); this.sun.target.position.copy(focus);
    const sc = this.sun.shadow.camera;
    sc.left = -Rr; sc.right = Rr; sc.top = Rr; sc.bottom = -Rr; sc.near = 20; sc.far = 340; sc.updateProjectionMatrix();
    this.sun.shadow.bias = L.bias; this.sun.shadow.normalBias = L.normalBias * (Rr / 12);
    TONE.uLitCol.value.set(...L.lit); TONE.uShadeCol.value.set(...L.shade); TONE.uShadeLift.value.set(...L.lift);
    TONE.uLambert.value = L.lambert; TONE.uSideK.value = L.sideK; TONE.uTerm.value = L.term; TONE.uBounce.value.set(...K.bounce); TONE.uSat.value = s.mood === "night" ? 0.6 : 0.82;
    CHAR.uCharTint.value.set(...L.charTint); CHAR.uCharShade.value = L.charShade; CHAR.uGrad.value = L.charGrad;
    CHAR.uBodyGrad.value = L.bodyGrad; CHAR.uSideTint.value.set(...L.sideTint);
    const su = this.skyMat.uniforms, sk = SKY[s.mood];
    sk.c.forEach((h, i) => untone(h, su["c" + i].value));
    const e = sk.e.map((deg) => THREE.MathUtils.degToRad(deg));
    su.e.value.set(e[1], e[2], e[3], e[4]);
    this.sky.position.copy(cam.position);
    untone(L.fog, this.fog.color);
    this.fog.near = s.mood === "night" ? 60 : 40; this.fog.far = s.mood === "night" ? 420 : 380;
    scene.fog = this.fog; scene.background = null;
    this.night.visible = s.mood === "night" && s.set === "lake"; this.glit.visible = id === 1 || id === 14 || id === 9;
    this.night.position.set(cam.position.x * 0, 0, 0);

    // ---- props ----
    this.lakeMat.color.set(id === 12 ? "#a3362a" : s.mood === "night" ? "#24467a" : "#3a8cc0");
    // single bubble ripples (shot 2)
    this.ripples.forEach((m, i) => {
      const u = id === 2 ? clamp01((t - 6.35 - i * 0.18) / 1.2) : 0;
      m.visible = u > 0 && u < 1; m.position.set(LAKE + 1, 0.04, 2); m.scale.setScalar(0.2 + 2.2 * u);
      (m.material as THREE.MeshBasicMaterial).opacity = 0.8 * (1 - u);
    });
    // landslide
    const sl = slideAt(t);
    this.rocks.forEach((m, i) => {
      const h = this.rockHome[i], k = clamp01(sl * 1.2 - i * 0.03), x = h.x + (LAKE - 28 - (h.x)) * k * k, z = h.z + 1.5 * k;
      m.position.set(x, Math.max(-0.4, craterH(x - LAKE, z) + 0.6), z); m.rotation.set(k * 6 + i, k * 3, k * 4);
    });
    // puffs: eruption (lake 8/9), rolling cloud (village 10), else hidden
    const pr = rng(3);
    this.puffs.forEach((m, i) => {
      const a = pr() * Math.PI * 2, rr = pr(), hh = pr(), sz = 0.6 + pr();
      m.visible = false; m.material = this.hardPuff; m.layers.set(0); m.renderOrder = 0;
      if (s.set === "lake" && (id === 9) ) {
        const fz = fizzAt(t), sp = spreadAt(t);
        if (i < 60) { // column above the lake centre
          const y = hh * 26 * fz; m.visible = fz > 0.02 && y < 26 * fz;
          m.position.set(LAKE + Math.cos(a) * rr * (2 + y * 0.25), y, Math.sin(a) * rr * (2 + y * 0.25)); m.scale.setScalar((1.6 + y * 0.12) * sz);
        } else { // cloud sheet flowing outward and over the rim
          const r = 4 + rr * 40 * sp, x = Math.cos(a) * r, z = Math.sin(a) * r;
          m.visible = sp > 0.02 && rr < sp + 0.1;
          m.position.set(LAKE + x, Math.max(0.6, craterH(x, z)) + 0.8 + hh * 1.6, z); m.scale.set(2.6 * sz, 1.1 * sz, 2.6 * sz);
        }
      }
      if (s.set === "village" && id === 10) {
        const rl = rollAt(t), zf = -38 + 40 * rl, z = zf - hh * 24, x = (pr() - 0.5) * 60;
        m.material = this.softPuff; m.layers.set(NOINK); m.renderOrder = 2; m.visible = true; m.position.set(VILLAGE + x, villageH(x, z) + 0.3 + 0.8 * rr, z); m.scale.set(1.6 * sz, 1.0 * sz, 1.6 * sz);
      }
    });
    // degassing raft and jet (shot 13)
    this.raft.visible = id === 13;
    const jh = 3.2 + 0.3 * Math.sin(t * 9); this.jet.scale.set(1, jh, 1); this.jet.position.y = 2.4 + jh / 2; this.jetTop.position.y = 2.4 + jh; this.jetTop.scale.set(1.1, 0.7 + 0.1 * Math.sin(t * 13), 1.1);
    // soda bottle
    const sh = id === 6 ? shakeAt(t) : 0, pop = id === 8 ? popAt(t) : 0;
    this.bottle.rotation.z = 0.12 * sh;
    this.cap.position.set(0.5 * pop, 0.975 + 1.8 * pop - 1.2 * pop * pop, 0.2 * pop); this.cap.rotation.set(pop * 9, 0, pop * 5);
    const fr = rng(9);
    this.foam.forEach((m, i) => {
      const k = fr(), a = fr() * Math.PI * 2, y = k * 1.4 * pop;
      m.visible = pop > 0.05; m.position.set(SODA + Math.cos(a) * (0.05 + y * 0.18), 1.86 + y, Math.sin(a) * (0.05 + y * 0.18)); m.scale.setScalar(0.06 + 0.07 * k + 0.05 * pop);
    });
    // hut lantern + mist
    const lamp = id === 11 ? lampAt(t) : 1;
    (this.flame.material as THREE.MeshBasicMaterial).color.setRGB(3 * lamp, 2 * lamp, 0.8 * lamp); this.flame.visible = lamp > 0.02;
    const mr = rng(21);
    this.mist.forEach((m) => {
      const x = (mr() - 0.5) * 7 + 0.25 * t, z = 0.4 + mr() * 2.2, sz = 0.5 + mr() * 0.6;
      m.visible = s.set === "hut"; m.position.set(HUT + ((x + 3.5) % 7) - 3.5, 0.08, z); m.scale.set(1.3 * sz, 0.22 * sz, 0.9 * sz);
    });

    // ---- cast ----
    const P: Place[] = [], FX: FxPlace[] = [];
    const add = (key: string, draw: (p: Pen) => void, x: number, y: number, z: number, scale = 1, extra: Partial<Place> = {}) => P.push({ key, draw, x, y, z, scale, ...extra });
    const lid = (i: number) => blinkAt(f, i);
    if (id === 2) {
      const u = bubbleAt(t);
      if (u > 0 && u < 1) { const bl = lid(3); add(`bub|neutral|${bl}`, (p) => bubble(p, "neutral", bl), LAKE + 1, -0.45 + 0.55 * u, 2, 0.42); }
      if (t > 6.2 && t < 6.9) { const k = clamp01((t - 6.2) / 0.6); FX.push({ key: `puff|${q(k, 10)}`, cw: 300, ch: 300, draw: (p) => fxPuff(p, k), x: LAKE + 1, y: 0.5, z: 2, w: 1.0, h: 1.0 }); }
      focus = V(LAKE + 1, 0.3, 2);
    }
    if (id === 7 && sl > 0.75) { const k = clamp01((sl - 0.75) / 0.25); FX.push({ key: `splash|${q(k, 10)}`, cw: 400, ch: 400, draw: (p) => fxSplash(p, k), x: LAKE - 27, y: 1.5, z: -2, w: 5, h: 5 }); }
    if (id === 4) {
      [[11, 4.5, 0], [14, 6.5, 1], [16.5, 3.8, 0], [19, 6, 1], [12.5, 8.5, 1]].forEach(([x, z, v], i) =>
        add(`cow|${v}`, (p) => cowLying(p, v), VILLAGE + x, 0, z, 1.5, { yaw: 0.25 * (i % 2 ? 1 : -1) + 0.6 }));
      focus = V(VILLAGE + 14, 0.5, 6);
    }
    if (s.set === "section") {
      // packed bubbles in the deep layer, more seep in over the shot
      const n = Math.min(8, 3 + Math.floor((t - 14.3) * 1.6));
      for (let i = 0; i < n; i++) {
        const col = i % 4, row = Math.floor(i / 4), x = -2.1 + col * 1.4 + (row % 2) * 0.6, y = -4.35 + row * 1.45, bl = lid(10 + i);
        const ex: Expr = i % 5 === 2 ? "nervous" : "neutral";
        add(`bub|${ex}|${bl}|sq`, (p) => bubble(p, ex, bl, 0.6), SECTION + x, y, 0.15, 0.9);
      }
      for (let i = 0; i < 5; i++) { // rising through the crack
        const u = ((t * 0.5 + i * 0.2) % 1);
        add(`bub|neutral|0|small`, (p) => bubble(p, "neutral", 0, 0, 0), SECTION + 0.4 - 0.3 * u, -8.2 + 3.4 * u, 0.2, 0.3);
      }
      focus = V(SECTION, c.look[1], 0);
    }
    if (s.set === "soda") {
      for (let i = 0; i < 8; i++) {
        const col = i % 4, row = Math.floor(i / 4), x = -0.14 + col * 0.093, y = 0.91 + row * 0.15, bl = lid(30 + i);
        const ex: Expr = id === 8 ? "shock" : sh !== 0 ? "nervous" : i % 3 === 1 ? "stern" : "neutral";
        if (id === 8 && pop > 0.3 && i < 4) continue;
        add(`bub|${ex}|${bl}|sq`, (p) => bubble(p, ex, bl, 0.5), SODA + x + 0.012 * sh, y, 0.06 + (row ? -0.06 : 0.04), 0.12);
      }
      if (id === 8) for (let i = 0; i < 4; i++) { const k = clamp01(pop * 1.4 - i * 0.12); if (k > 0) add(`bub|shock|0|fly`, (p) => bubble(p, "shock", 0), SODA + (i - 1.5) * 0.25 * k, 1.85 + 1.0 * k, 0.1, 0.09, { roll: (i - 1.5) * k }); }
      focus = V(SODA, id === 8 ? 1.95 : 1.25, 0.1);
    }
    if (s.set === "hut") {
      FX.push({ key: `lantern|${q(lamp, 20)}`, cw: 600, ch: 1000, draw: (p) => lantern(p, lamp), x: HUT + 0.68, y: 0.98, z: 0.24, w: 0.5, h: 0.83, soft: true });
      focus = V(HUT, 0.9, 0);
    }
    if (id === 13) {
      for (let i = 0; i < 9; i++) {
        const u = clamp01((t - burpAt(i)) / 2.4);
        if (u <= 0 || u >= 1) continue;
        const bl = lid(50 + i), ex: Expr = i % 3 === 0 ? "relief" : "neutral";
        add(`bub|${ex}|${bl}`, (p) => bubble(p, ex, bl), LAKE + 1 + (i % 2 ? 1 : -1) * 2.0 * u, 5.6 + 2.4 * u, 4 + 0.6 * Math.sin(i), 0.9);
      }
      focus = V(LAKE + 1, 3, 4);
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
      a.mesh.scale.set(sc2, sc2, sc2);
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
    void LIGHT; void smooth;
    return focus;
  }
}
