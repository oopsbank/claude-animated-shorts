// The thoughts short as one three.js scene: nine small sets side by side along x (bedroom, cafe, office, park,
// classroom, kitchen, bus, city street, woods). Same look rules as the bridge/no-dying shorts: two-tone materials,
// painted textures, camera-relative sun frozen per shot, lit character cards on NOINK, thought bubbles as unlit cards.
// update(id, f, camera) poses the shot and returns the focus point.
import * as THREE from "three";
import { Batch, boxGeo, V, lam, quad } from "../bridge/build";
import { ctex, rep, rng } from "../bridge/paint";
import { bodyFront, Outfit, Expr, SKINS, Pen, INK } from "../bridge/toon";
import { LIGHTS, LOOK } from "../bridge/lights";
import { TONE, CHAR, untone } from "../bridge/shade";
import { NOINK } from "../bridge/ink";
import { Pool, Actor, Fx } from "../bridge/cast";
import {
  bubble, words, taco, ball, answers, yuck, vase, notes, worry, grocery, cringe, money, deadline, nuts, dots, question,
  dog, squirrel, counter, board, plate, text, LIGHT,
} from "./chars";
import { FPS, SHOTS, BED, CAFE, OFFICE, PARK, CLASS, KITCHEN, BUS, CITY, WOODS, camAt, smooth, clamp01 } from "./story";

type Place = { key: string; draw: (p: Pen) => void; x: number; y: number; z: number; scale?: number; mirror?: boolean; yaw?: number };
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
const hsh = (i: number, k = 0) => { const v = Math.sin(i * 91.7 + k * 47.3 + 3.1) * 43758.5453; return v - Math.floor(v); };

// ---------------- painted textures ----------------
const plankTex = (key: string, col: string) => ctex("pl" + key, 256, 256, (g, r) => {
  g.fillStyle = col; g.fillRect(0, 0, 256, 256);
  for (let x = 0; x < 256; x += 32) { g.fillStyle = "rgba(0,0,0,0.14)"; g.fillRect(x, 0, 3, 256); g.fillStyle = `rgba(255,255,255,${0.06 * r()})`; g.fillRect(x + 6, 0, 18, 256); }
});
const tileTex = (key: string, a: string, b: string) => ctex("tile" + key, 256, 256, (g) => {
  for (let i = 0; i < 4; i++) for (let j = 0; j < 4; j++) { g.fillStyle = (i + j) % 2 ? a : b; g.fillRect(i * 64, j * 64, 64, 64); }
  g.strokeStyle = "rgba(0,0,0,0.12)"; g.lineWidth = 3; for (let i = 0; i <= 4; i++) { g.beginPath(); g.moveTo(i * 64, 0); g.lineTo(i * 64, 256); g.moveTo(0, i * 64); g.lineTo(256, i * 64); g.stroke(); }
});
const grassTex = (key: string, col: string) => ctex("grass" + key, 512, 512, (g, r) => {
  g.fillStyle = col; g.fillRect(0, 0, 512, 512);
  for (let i = 0; i < 1400; i++) { g.strokeStyle = `rgba(${r() < 0.5 ? "255,255,200" : "0,40,0"},${0.06 + 0.08 * r()})`; g.lineWidth = 2; const x = 512 * r(), y = 512 * r(); g.beginPath(); g.moveTo(x, y); g.lineTo(x + 4 * (r() - 0.5), y - 8 - 8 * r()); g.stroke(); }
});
const asphaltTex = () => ctex("asphalt", 512, 1024, (g, r) => {
  g.fillStyle = "#5d6270"; g.fillRect(0, 0, 512, 1024);
  for (let i = 0; i < 2500; i++) { g.fillStyle = `rgba(${r() < 0.5 ? "255,255,255" : "0,0,0"},0.06)`; g.fillRect(512 * r(), 1024 * r(), 4, 4); }
  g.fillStyle = "#f2e6a0"; for (let y = 0; y < 1024; y += 128) g.fillRect(248, y, 16, 70);
});
const facadeTex = (key: string, col: string, win: string) => ctex("fac" + key, 256, 256, (g, r) => {
  g.fillStyle = col; g.fillRect(0, 0, 256, 256);
  for (let i = 0; i < 4; i++) for (let j = 0; j < 4; j++) {
    g.fillStyle = "rgba(0,0,0,0.18)"; g.fillRect(i * 64 + 12, j * 64 + 12, 40, 44);
    g.fillStyle = r() < 0.3 ? "#ffe9a8" : win; g.fillRect(i * 64 + 14, j * 64 + 14, 36, 40);
  }
});
const wallpaperTex = (key: string, col: string, dot: string) => ctex("wp" + key, 256, 256, (g) => {
  g.fillStyle = col; g.fillRect(0, 0, 256, 256);
  g.fillStyle = dot; for (let i = 0; i < 4; i++) for (let j = 0; j < 4; j++) { g.beginPath(); g.arc(i * 64 + 32 + (j % 2) * 32, j * 64 + 32, 7, 0, 7); g.fill(); }
});
const penTex = (key: string, w: number, h: number, draw: (p: Pen) => void) => ctex(key, w, h, (g) => { g.clearRect(0, 0, w, h); draw(new Pen(g)); });

const SKY_V = "varying vec3 vP; void main(){ vP = normalize(position); gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0); }";
const SKY_F = `uniform vec3 c0, c1, c2, c3, c4; uniform vec4 e; varying vec3 vP;
  void main(){ float el = asin(clamp(normalize(vP).y, -1.0, 1.0));
    vec3 c = mix(c0, c1, smoothstep(0.0, e.x, el)); c = mix(c, c2, smoothstep(e.x, e.y, el));
    c = mix(c, c3, smoothstep(e.y, e.z, el)); c = mix(c, c4, smoothstep(e.z, e.w, el)); gl_FragColor = vec4(c, 1.0); }`;

// ---------------- outfits ----------------
const HERO: Outfit = { jacket: "#2f9c9a", pants: "#3b3f52", boots: "#f4f1ea", hat: "hair", hair: "#ff6fae", skin: SKINS[1] };
const BARISTA: Outfit = { jacket: "#2f6b4f", pants: "#2f3446", boots: "#3a2a20", hat: "cap", cap: "#2f6b4f", skin: SKINS[3], buttons: "#f2efe6" };
const BOSS: Outfit = { jacket: "#3b4256", pants: "#2b2f3d", boots: "#241726", hat: "hair", hair: "#6b6b72", moustache: "#4a3a30", skin: SKINS[0], build: "stout", buttons: "#e8c45a" };
const SMART: Outfit = { jacket: "#3f6fd0", pants: "#2f3446", boots: "#f4f1ea", hat: "hair", hair: "#2a2230", skin: SKINS[2], build: "kid", buttons: "#ffffff" };
const FRIEND: Outfit = { jacket: "#e8b830", pants: "#3b3f52", boots: "#5a3b2a", hat: "hair", hair: "#5a3b2a", skin: SKINS[3] };
const MOM: Outfit = { jacket: "#7b5ac9", pants: "#3b3f52", boots: "#5a3b2a", hat: "hair", hair: "#3a2a2a", skin: SKINS[1], buttons: "#f2efe6" };
const JK = ["#c8463d", "#e8b830", "#3f8f5a", "#3a6fb0", "#d9773a", "#7b5ac9", "#6d6a7a", "#2f9c9a", "#e07a9a"];
const HAIR = ["#5a3b2a", "#2a2230", "#e8c45a", "#a0522d", "#6b6b72", "#3a2a2a"];
const folk = (v: number): Outfit => ({
  jacket: JK[v % JK.length], pants: ["#3b3f52", "#2f3446", "#4a4e5e"][v % 3], boots: ["#3a2a20", "#241726", "#f4f1ea"][v % 3],
  hat: v % 4 === 1 ? "cap" : "hair", cap: JK[(v + 3) % JK.length], hair: HAIR[v % HAIR.length], skin: SKINS[(v * 3) % 4],
  build: v % 5 === 2 ? "stout" : undefined, buttons: v % 2 ? "#f2efe6" : undefined,
});
const CITY_THOUGHTS = [worry, grocery, cringe, money, deadline, (p: Pen) => notes(p, 0), question, worry, grocery];

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
  private glass: THREE.MeshBasicMaterial;
  private lampGlow: THREE.Mesh;
  private squirrelSpots: [number, number, number][] = [];

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

    const b = new Batch(), nb = new Batch();
    const M = (key: string, color: string) => lam(key, () => ({ color }));
    const T = (key: string, tex: () => THREE.Texture, x = 1, y = 1) => lam(key, () => ({ map: rep(tex(), x, y) }));
    const box = (x0: number, y0: number, z0: number, x1: number, y1: number, z1: number, m: THREE.Material, bb: Batch = b) => bb.add(boxGeo(V(x0, y0, z0), V(x1, y1, z1)), m);
    const floor = (cx: number, x0: number, x1: number, z0: number, z1: number, m: THREE.Material, tile = 1, y = 0) =>
      b.add(quad(V(cx + x0, y, z1), V(cx + x1, y, z1), V(cx + x1, y, z0), V(cx + x0, y, z0), (x1 - x0) / tile, (z1 - z0) / tile), m);
    const backWall = (cx: number, x0: number, x1: number, z: number, h: number, m: THREE.Material, tile = 1) =>
      b.add(quad(V(cx + x0, 0, z), V(cx + x1, 0, z), V(cx + x1, h, z), V(cx + x0, h, z), (x1 - x0) / tile, h / tile), m);
    const sideWall = (x: number, z0: number, z1: number, h: number, m: THREE.Material, tile = 1) =>
      b.add(quad(V(x, 0, z0), V(x, 0, z1), V(x, h, z1), V(x, h, z0), (z1 - z0) / tile, h / tile), m);
    const signMesh = (key: string, w: number, h: number, cw: number, ch: number, draw: (p: Pen) => void, x: number, y: number, z: number, yaw = 0) => {
      const m = new THREE.MeshLambertMaterial({ map: penTex(key, cw, ch, draw), transparent: false, alphaTest: 0.5, side: THREE.DoubleSide });
      const s = new THREE.Mesh(new THREE.PlaneGeometry(w, h), m); s.position.set(x, y, z); s.rotation.y = yaw; s.layers.set(NOINK); R.add(s);
    };
    const cyl = (x: number, y: number, z: number, r0: number, r1: number, h: number, m: THREE.Material, seg = 16, bb: Batch = b) =>
      bb.add(new THREE.CylinderGeometry(r0, r1, h, seg).translate(x, y + h / 2, z), m);
    const table = (cx: number, x0: number, x1: number, z0: number, z1: number, top: number, m: THREE.Material, leg: THREE.Material) => {
      box(cx + x0, top - 0.06, z0, cx + x1, top, z1, m);
      for (const x of [x0 + 0.06, x1 - 0.06]) for (const z of [z0 + 0.06, z1 - 0.06]) box(cx + x - 0.03, 0, z - 0.03, cx + x + 0.03, top - 0.06, z + 0.03, leg);
    };
    const wood = T("woodFloor", () => plankTex("wf", "#c48a5a"));
    const white = M("whitePaint", "#f3f1ea");
    const metal = M("metal", "#9aa3b0");
    const darkM = M("darkM", "#2b2b31");
    const trunkM = M("trunk", "#7a5236");
    const leafM = M("leaf", "#3f8f5a"), leaf2 = M("leaf2", "#2f7a52"), leaf3 = M("leaf3", "#5aa35a");
    const grass = T("grassM", () => grassTex("g", "#7cc25a"), 1, 1);
    const tree = (x: number, z: number, h: number, kind: number) => {
      if (kind === 0) { cyl(x, 0, z, 0.16, 0.22, h * 0.35, trunkM, 8); b.add(new THREE.ConeGeometry(h * 0.3, h * 0.75, 8).translate(x, h * 0.35 + h * 0.37, z), [leafM, leaf2][Math.floor(h * 10) % 2]); }
      else { cyl(x, 0, z, 0.14, 0.2, h * 0.5, trunkM, 8); b.add(new THREE.IcosahedronGeometry(h * 0.32, 1).translate(x, h * 0.62, z), leaf3); }
    };
    this.glass = new THREE.MeshBasicMaterial({ color: new THREE.Color(0.75, 0.88, 1.15) });

    // ---- BED ----
    {
      floor(BED, -4, 4, -4.4, 4, wood, 1.2);
      const wp = T("wpBed", () => wallpaperTex("bed", "#a9c4e8", "#c6d8f1"), 1, 1);
      backWall(BED, -4, 4, -4.4, 3.2, wp, 0.8); sideWall(BED - 4, -4.4, 4, 3.2, wp, 0.8);
      box(BED + 0.05, 1.25, -4.42, BED + 1.25, 2.55, -4.32, white);
      const gl = new THREE.Mesh(new THREE.PlaneGeometry(1.0, 1.1), this.glass); gl.position.set(BED + 0.65, 1.9, -4.31); gl.layers.set(NOINK); R.add(gl);
      box(BED + 0.6, 1.3, -4.31, BED + 0.7, 2.5, -4.29, white);
      for (const x of [-0.12, 1.42]) box(BED + x - 0.14, 1.1, -4.3, BED + x + 0.14, 2.7, -4.24, M("curtain", "#e86a8c"));
      const bw = M("bedWood", "#8a5a3a");
      box(BED - 1.75, 0, -4.35, BED + 0.55, 0.42, -1.35, bw);
      box(BED - 1.75, 0, -4.38, BED + 0.55, 1.15, -4.2, bw);
      box(BED - 1.7, 0.42, -4.2, BED + 0.5, 0.6, -1.4, white);
      box(BED - 1.3, 0.6, -4.15, BED + 0.1, 0.78, -3.65, M("pillow", "#fbfaf5"));
      box(BED - 1.76, 0.58, -2.9, BED + 0.56, 0.74, -1.33, M("blanket", "#e8b830"));
      box(BED + 0.8, 0, -4.25, BED + 1.45, 0.62, -3.65, bw);
      cyl(BED + 1.12, 0.62, -3.95, 0.07, 0.1, 0.35, metal);
      b.add(new THREE.CylinderGeometry(0.14, 0.24, 0.26, 16, 1, true).translate(BED + 1.12, 1.05, -3.95), M("shade", "#f6e3b0"));
      this.lampGlow = new THREE.Mesh(new THREE.SphereGeometry(0.09, 12, 8), new THREE.MeshBasicMaterial({ color: new THREE.Color(2.2, 1.8, 1.1) }));
      this.lampGlow.position.set(BED + 1.12, 0.98, -3.95); this.lampGlow.layers.set(NOINK); R.add(this.lampGlow);
      signMesh("poster", 0.9, 1.2, 450, 600, (p) => { p.poly([[10, 10], [440, 10], [440, 590], [10, 590]], "#ffd84d", 12); text(p, "★", 225, 260, 260, "#e0463c"); text(p, "DREAM", 225, 480, 90, INK); }, BED - 2.8, 1.9, -4.38);
    }

    // ---- CAFE ----
    {
      floor(CAFE, -5, 5, -3.6, 6, T("cafeTile", () => tileTex("cafe", "#e9e2d6", "#cfc5b5")), 0.8);
      backWall(CAFE, -5, 5, -3.6, 3.4, M("cafeWall", "#f0c99a"));
      sideWall(CAFE - 5, -3.6, 6, 3.4, M("cafeWall", "#f0c99a"));
      signMesh("menu", 2.0, 1.3, 1000, 650, (p) => board(p, ["MENU", "COFFEE  3", "LATTE  4", "TEA  2"], 1000, 650, "#2b2b31"), CAFE + 1.1, 2.45, -3.55);
      box(CAFE - 2.2, 0, -2.0, CAFE + 2.2, 1.02, -1.3, M("counterWood", "#7a5236"));
      box(CAFE - 2.25, 1.02, -2.05, CAFE + 2.25, 1.1, -1.25, darkM);
      box(CAFE - 1.6, 1.1, -1.95, CAFE - 0.95, 1.62, -1.55, metal);
      box(CAFE - 1.55, 1.62, -1.95, CAFE - 1.0, 1.68, -1.6, darkM);
      for (const x of [0.6, 0.85, 1.6]) cyl(CAFE + x, 1.1, -1.55, 0.06, 0.05, 0.12, white);
      box(CAFE - 4.9, 0, -3.5, CAFE - 3.6, 2.2, -3.0, M("shelfWood", "#8a5a3a"));
      for (let i = 0; i < 4; i++) cyl(CAFE + 3.0 + (i % 2) * 0.9, 0, 0.8 - i * 1.2, 0.35, 0.35, 0.72, M("cafeTable", "#d9dde3"));
    }

    // ---- OFFICE ----
    {
      floor(OFFICE, -5, 5, -4, 6, M("carpet", "#8a93a6"));
      backWall(OFFICE, -5, 5, -4, 3.4, M("offWall", "#dfe7ee")); sideWall(OFFICE - 5, -4, 6, 3.4, M("offWall", "#dfe7ee"));
      signMesh("wb", 1.9, 1.15, 950, 575, (p) => {
        p.poly([[10, 10], [940, 10], [940, 565], [10, 565]], "#ffffff", 14); text(p, "Q3 PLAN", 475, 90, 80, INK);
        p.stroke([[120, 470], [330, 380], [520, 420], [800, 180]], 18, "#2fa84f"); p.poly([[800, 180], [740, 190], [790, 240]], "#2fa84f", 0);
        p.stroke([[100, 160], [100, 500], [860, 500]], 10, INK);
      }, OFFICE - 1.0, 2.0, -3.95);
      for (const x of [1.4, 2.6]) { box(OFFICE + x - 0.5, 1.2, -4.02, OFFICE + x + 0.5, 2.6, -3.96, white); const g = new THREE.Mesh(new THREE.PlaneGeometry(0.88, 1.28), this.glass); g.position.set(OFFICE + x, 1.9, -3.95); g.layers.set(NOINK); R.add(g); }
      table(OFFICE, -1.7, 1.7, -2.5, -0.8, 0.78, M("offTable", "#ece7dc"), metal);
      for (const x of [-1.0, 0.0, 1.0]) box(OFFICE + x - 0.25, 0.78, -1.3, OFFICE + x + 0.25, 0.79, -0.95, white);
      cyl(OFFICE - 4.3, 0, -3.3, 0.25, 0.2, 0.5, M("pot", "#d9773a")); b.add(new THREE.IcosahedronGeometry(0.45, 1).translate(OFFICE - 4.3, 0.95, -3.3), leaf3);
    }

    // ---- PARK ----
    {
      floor(PARK, -90, 90, -200, 60, grass, 3);
      b.add(quad(V(PARK - 1.1, 0.01, 60), V(PARK + 1.1, 0.01, 60), V(PARK + 1.1, 0.01, -60), V(PARK - 1.1, 0.01, -60), 1, 30), M("path", "#e3cfa6"));
      const r = rng(21);
      for (let i = 0; i < 40; i++) { const x = (r() - 0.5) * 60, z = -6 - 50 * r(); if (Math.abs(x) < 1.6) continue; tree(PARK + x, z, 3 + 3 * r(), i % 3 ? 1 : 0); }
      box(PARK - 3.6, 0.42, -4.3, PARK - 1.8, 0.5, -3.9, M("bench", "#a0522d")); box(PARK - 3.6, 0.5, -4.35, PARK - 1.8, 0.95, -4.28, M("bench", "#a0522d"));
      for (const x of [-3.5, -1.9]) box(PARK + x - 0.04, 0, -4.3, PARK + x + 0.04, 0.42, -3.95, darkM);
      b.add(new THREE.SphereGeometry(0.11, 16, 10).translate(PARK + 1.25, 0.11, 0.35), M("tball", "#d8f04a"));
    }

    // ---- CLASS ----
    {
      floor(CLASS, -5, 5, -4.6, 6, wood, 1.2);
      backWall(CLASS, -5, 5, -4.6, 3.4, M("clWall", "#f1e3c4")); sideWall(CLASS - 5, -4.6, 6, 3.4, M("clWall", "#f1e3c4"));
      signMesh("chalk", 2.8, 1.25, 1120, 500, (p) => board(p, ["TEST", "1) ?   2) ?   3) ?"], 1120, 500), CLASS - 0.2, 2.15, -4.55);
      signMesh("clock", 0.5, 0.5, 200, 200, (p) => { p.ell(100, 100, 88, 88, "#ffffff", 10); p.stroke([[100, 100], [100, 40]], 9); p.stroke([[100, 100], [145, 110]], 9); }, CLASS + 2.2, 2.7, -4.55);
      const desk = M("desk", "#d9a35b");
      for (const [x, z] of [[0, -0.9], [-1.5, -0.9], [1.5, -0.9], [0.3, -2.7], [-1.3, -2.7], [1.8, -2.7]] as const) {
        table(CLASS + x, -0.5, 0.5, z, z + 0.6, 0.72, desk, metal);
        box(CLASS + x - 0.18, 0.72, z + 0.2, CLASS + x + 0.18, 0.725, z + 0.48, white);
      }
    }

    // ---- KITCHEN ----
    {
      floor(KITCHEN, -5, 5, -4, 6, T("kTile", () => tileTex("k", "#f4f1ea", "#9fc6d9")), 0.6);
      backWall(KITCHEN, -5, 5, -4, 3.4, M("kWall", "#f6e9a8")); sideWall(KITCHEN - 5, -4, 6, 3.4, M("kWall", "#f6e9a8"));
      const cab = M("cab", "#5aa3a0");
      box(KITCHEN - 4.6, 0, -4, KITCHEN - 1.4, 0.9, -3.4, cab); box(KITCHEN - 4.65, 0.9, -4, KITCHEN - 1.35, 0.96, -3.35, M("worktop", "#f4f1ea"));
      box(KITCHEN - 4.6, 1.8, -4, KITCHEN - 1.4, 2.6, -3.65, cab);
      box(KITCHEN + 2.6, 0, -4, KITCHEN + 3.5, 2.2, -3.3, M("fridgeW", "#e9eef3"));
      box(KITCHEN + 1.0, 1.55, -4, KITCHEN + 2.2, 1.6, -3.75, M("shelfWood", "#8a5a3a"));
      b.add(new THREE.LatheGeometry([new THREE.Vector2(0.0, 0), new THREE.Vector2(0.09, 0), new THREE.Vector2(0.13, 0.12), new THREE.Vector2(0.08, 0.3), new THREE.Vector2(0.06, 0.36)], 16).translate(KITCHEN + 1.6, 1.6, -3.88), M("vase", "#4f8fe0"));
      table(KITCHEN, -1.6, 1.6, -1.6, -0.6, 0.76, M("cloth", "#f4f4f4"), M("tLeg", "#8a5a3a"));
      for (const x of [-0.6, 0.65]) {
        cyl(KITCHEN + x, 0.76, -1.1, 0.24, 0.2, 0.03, white, 24);
        b.add(new THREE.IcosahedronGeometry(0.12, 0).scale(1.2, 0.6, 1).translate(KITCHEN + x, 0.83, -1.1), M("glop", "#7c8a3a"));
      }
      cyl(KITCHEN, 0.76, -1.0, 0.07, 0.06, 0.22, M("jug", "#e8b830"));
    }

    // ---- BUS ----
    {
      const W = 1.3;
      floor(BUS, -W, W, -11, 3, M("busFloor", "#7a8090"));
      floor(BUS, -60, 60, -100, 60, M("street", "#6a7080"), 1, -0.6);
      const side = M("busSide", "#d9dde3"), seat = M("seat", "#3a6fb0"), pole = M("pole", "#e8b830");
      for (const s of [-1, 1]) {
        const x = BUS + s * W;
        b.add(quad(V(x, 0, s < 0 ? -11 : 3), V(x, 0, s < 0 ? 3 : -11), V(x, 1.0, s < 0 ? 3 : -11), V(x, 1.0, s < 0 ? -11 : 3)), side);
        b.add(quad(V(x, 1.95, s < 0 ? -11 : 3), V(x, 1.95, s < 0 ? 3 : -11), V(x, 2.5, s < 0 ? 3 : -11), V(x, 2.5, s < 0 ? -11 : 3)), side);
        const gl = new THREE.Mesh(new THREE.PlaneGeometry(14, 0.95), this.glass); gl.position.set(x - s * 0.01, 1.475, -4); gl.rotation.y = s < 0 ? Math.PI / 2 : -Math.PI / 2; gl.layers.set(NOINK); R.add(gl);
        for (let z = 2.4; z > -11; z -= 1.3) box(x - 0.05, 1.0, z - 0.06, x + 0.05, 1.95, z + 0.06, side);
      }
      backWall(BUS, -W, W, -11, 2.5, M("busBack", "#c9ced6"));
      box(BUS - W, 2.5, -11, BUS + W, 2.6, 3, M("busRoof", "#eef0f3"), nb);
      for (let i = 0; i < 8; i++) {
        const z = -0.6 - i * 1.2;
        for (const s of [-1, 1]) {
          const x0 = BUS + s * 0.35, x1 = BUS + s * 1.25;
          box(Math.min(x0, x1), 0, z - 0.25, Math.max(x0, x1), 0.46, z + 0.25, seat);
          box(Math.min(x0, x1), 0.46, z - 0.32, Math.max(x0, x1), 1.15, z - 0.22, seat);
        }
        if (i % 2) cyl(BUS + 0.3, 0, z + 0.5, 0.025, 0.025, 2.5, pole, 8);
      }
      box(BUS - 0.4, 2.2, -11, BUS - 0.37, 2.24, 3, pole); box(BUS + 0.37, 2.2, -11, BUS + 0.4, 2.24, 3, pole);
    }

    // ---- CITY ----
    {
      floor(CITY, -4, 4, -120, 20, T("asph", () => asphaltTex(), 1, 1), 8);
      for (const s of [-1, 1]) box(CITY + Math.min(s * 4, s * 7.5), 0, -120, CITY + Math.max(s * 4, s * 7.5), 0.15, 20, M("sidewalk", "#c9ced6"));
      floor(CITY, -200, 200, -300, 60, M("cityGround", "#8a8f9c"), 1, -0.02);
      const facs = [["#e8b8a0", "#7fa8d8"], ["#c9d6e8", "#5a7fb0"], ["#f0d79a", "#6f95c8"], ["#b8d8c0", "#5a8fa0"], ["#e0c0d8", "#7a7fc0"], ["#d9a07a", "#8fb3d6"]];
      const r = rng(31);
      for (const s of [-1, 1]) for (let z = 16, i = 0; z > -120; i++) {
        const d = 6 + 6 * r(), h = 8 + 26 * r(), [c, w] = facs[(i + (s > 0 ? 3 : 0)) % facs.length];
        const m = lam(`fac${c}`, () => ({ map: rep(facadeTex(c, c, w), 1, 1) }));
        const x0 = CITY + s * 7.5, x1 = CITY + s * (7.5 + 10);
        b.add(boxGeo(V(Math.min(x0, x1), 0, z - d), V(Math.max(x0, x1), h, z), 3), m);
        z -= d + 0.3;
      }
      for (let i = 0; i < 6; i++) { const [c, w] = facs[i]; const m = lam(`fac${c}`, () => ({ map: rep(facadeTex(c, c, w), 1, 1) })); const h = 20 + 30 * r(); b.add(boxGeo(V(CITY - 30 + i * 10, 0, -132), V(CITY - 21 + i * 10, h, -122), 3), m); }
      for (let z = 10; z > -100; z -= 12) for (const s of [-1, 1]) { cyl(CITY + s * 4.6, 0.15, z, 0.06, 0.06, 4.2, darkM, 8); box(CITY + s * 4.6 - 0.05, 4.2, z - 0.05, CITY + s * 3.9, 4.3, z + 0.05, darkM); }
      for (let i = 0; i < 6; i++) box(CITY - 4 + i * 1.4, 0.005, -3.4, CITY - 3.2 + i * 1.4, 0.01, -2.4, white);
    }

    // ---- WOODS ----
    {
      floor(WOODS, -120, 120, -200, 60, T("grassW", () => grassTex("w", "#6aae4c"), 1, 1), 3);
      const r = rng(41);
      for (let i = 0; i < 160; i++) {
        const a = r() * Math.PI * 2, d = 4 + 40 * r() ** 1.3, x = d * Math.cos(a), z = -2 + d * Math.sin(a);
        if (z > -3.2 && x > -4 && x < 10) continue;
        if (z > 0 && Math.abs(x) < 5) continue;
        tree(WOODS + x, z, 4 + 4 * r(), r() < 0.7 ? 0 : 1);
      }
      cyl(WOODS, 0, -1.0, 0.38, 0.42, 0.45, trunkM, 20);
      b.add(new THREE.CylinderGeometry(0.36, 0.36, 0.01, 20).translate(WOODS, 0.455, -1.0), M("stumpTop", "#e3c08a"));
      b.add(new THREE.CylinderGeometry(0.2, 0.2, 2.2, 12).rotateZ(Math.PI / 2).rotateY(0.3).translate(WOODS - 2.2, 0.2, -2.4), trunkM);
      for (const [x, z] of [[-2.6, -4.2], [2.9, -4.6], [-0.9, -6.6], [1.4, -7.2], [4.2, -3.6], [-4.0, -5.4]] as const) {
        cyl(WOODS + x, 0, z, 0.2, 0.26, 4.6, trunkM, 10);
        b.add(new THREE.IcosahedronGeometry(1.6, 1).translate(WOODS + x, 5.4, z), leaf2);
        for (const [y, s] of [[1.5, -1], [2.5, 1], [3.5, -1]] as const) {
          box(WOODS + x + Math.min(0, s * 1.0), y - 0.07, z - 0.07, WOODS + x + Math.max(0, s * 1.0), y + 0.07, z + 0.07, trunkM);
          this.squirrelSpots.push([WOODS + x + s * 0.65, y + 0.07, z + 0.12]);
        }
      }
      for (let i = 0; i < 12; i++) { const a = -0.3 - (i / 11) * 2.5, d = 1.6 + 1.6 * hsh(i, 2); this.squirrelSpots.push([WOODS + 0.3 + d * Math.cos(a) * 1.4, 0, -1.4 + d * Math.sin(a)]); }
      for (let i = 0; i < 25; i++) { const x = (r() - 0.5) * 14, z = -2 - 8 * r(); b.add(new THREE.IcosahedronGeometry(0.25 + 0.25 * r(), 0).scale(1, 0.6, 1).translate(WOODS + x, 0.1, z), leaf3); }
    }

    b.build(R); nb.build(R, false);
  }

  private actor(i: number) { while (this.actors.length <= i) this.actors.push(new Actor(this.root)); return this.actors[i]; }
  private fx(i: number) { while (this.fxs.length <= i) this.fxs.push(new Fx(this.root)); return this.fxs[i]; }

  private shotSun(id: number) {
    let v = this.sunCache.get(id);
    if (v) return v;
    const s = SHOTS[id - 1], c = camAt(id, s.a), L = LIGHTS.day;
    const x = c.look[0] - c.pos[0], z = c.look[2] - c.pos[2], n = Math.hypot(x, z) || 1, fx = x / n, fz = z / n;
    const inside = ["bed", "cafe", "office", "class", "kitchen", "bus"].includes(s.set);
    const az = THREE.MathUtils.degToRad(L.az + (inside ? 60 : 25)), el = THREE.MathUtils.degToRad(inside ? 58 : 34);
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
    const sunDir = this.shotSun(id);
    this.hemi.color.set(L.sky); this.hemi.groundColor.set("#c9c4d8"); this.hemi.intensity = L.hemiI;
    this.sun.color.set("#fff0e4"); this.sun.intensity = L.sunI;
    const Rr = THREE.MathUtils.clamp(dist * 1.2 + 4, 6, 60);
    this.sun.position.copy(focus).addScaledVector(sunDir, 120); this.sun.target.position.copy(focus);
    const sc = this.sun.shadow.camera;
    sc.left = -Rr; sc.right = Rr; sc.top = Rr; sc.bottom = -Rr; sc.near = 20; sc.far = 260; sc.updateProjectionMatrix();
    this.sun.shadow.bias = L.bias; this.sun.shadow.normalBias = L.normalBias * (Rr / 12);
    TONE.uLitCol.value.set(...L.lit); TONE.uShadeCol.value.set(0.4, 0.42, 0.55); TONE.uShadeLift.value.set(0.07, 0.08, 0.13);
    TONE.uLambert.value = L.lambert; TONE.uSideK.value = L.sideK; TONE.uTerm.value = L.term; TONE.uBounce.value.set(...K.bounce); TONE.uSat.value = K.sat;
    CHAR.uCharTint.value.set(...L.charTint); CHAR.uCharShade.value = L.charShade; CHAR.uGrad.value = L.charGrad;
    CHAR.uBodyGrad.value = L.bodyGrad; CHAR.uSideTint.value.set(...L.sideTint);
    const su = this.skyMat.uniforms;
    K.sky.c.forEach((h, i) => untone(h, su["c" + i].value));
    const e = K.sky.e.map((deg) => THREE.MathUtils.degToRad(deg));
    su.e.value.set(e[1], e[2], e[3], e[4]);
    this.sky.position.copy(cam.position);
    untone("#d6e2f2", this.fog.color); this.fog.near = 40; this.fog.far = 340;
    scene.fog = this.fog; scene.background = null;
    const night = id === 10;
    if (night) this.glass.color.setRGB(0.05, 0.07, 0.2); else this.glass.color.setRGB(0.75, 0.88, 1.15);
    this.lampGlow.visible = !night;

    // ---- cast ----
    const P: Place[] = [], FX: FxPlace[] = [];
    const add = (key: string, draw: (p: Pen) => void, x: number, y: number, z: number, scale = 1, extra: Partial<Place> = {}) => P.push({ key, draw, x, y, z, scale, ...extra });
    const lid = (i: number) => blinkAt(f, i);
    const fig = (o: Outfit, i: number, expr: Expr, extra: Record<string, unknown> = {}) => {
      const opts = { mode: "stand" as const, expr, blink: lid(i), light: LIGHT, seed: (i % 7) + 1, ...extra };
      return { key: `F|${o.jacket}|${o.hair}|${o.skin}|${o.build}|${JSON.stringify(opts, (_k, v) => (typeof v === "number" ? q(v) : v))}`, draw: (p: Pen) => bodyFront(p, o, opts as any) };
    };
    const put = (o: Outfit, i: number, expr: Expr, x: number, y: number, z: number, extra: Record<string, unknown> = {}, scale = 1) => { const a = fig(o, i, expr, extra); add(a.key, a.draw, x, y, z, scale); };
    const card = (key: string, cw: number, ch: number, draw: (p: Pen) => void, x: number, y: number, z: number, w: number, h: number, sc2 = 1) => {
      if (sc2 <= 0.001) return;
      FX.push({ key, cw, ch, draw, x, y, z, w: w * sc2, h: h * sc2 });
    };
    /** a thought bubble that pops at t0; size = width in metres; bob makes it float */
    const think = (key: string, content: (p: Pen) => void, x: number, y: number, z: number, t0: number, size = 1.4, tail: -1 | 1 = -1, k = 1, t1 = 1e9) => {
      if (t > t1) return;
      const sc2 = pop(t, t0) * k, bob = 0.03 * size * Math.sin(t * 2.2 + x * 3 + z);
      card(`bub|${key}|${tail}`, 800, 600, (p) => bubble(p, content, tail), x, y + bob, z, size, size * 0.75, sc2);
    };
    const set = s.set;

    if (set === "bed") {
      if (!night) {
        const awake = t > 1.5;
        put(HERO, 1, t > 2.0 ? "shock" : awake ? "neutral" : "dazed", BED - 0.6, 0.62, -3.15, { mode: "sit", blink: awake ? lid(1) : 1, look: t > 2.0 ? 0.5 : 0 });
        think("q1", question, BED - 1.45, 2.2, -2.9, 1.75, 0.95, 1);
        think("d1", dots, BED + 0.35, 2.35, -3.0, 2.05, 0.9, -1);
        think("m1", money, BED - 0.5, 2.75, -3.3, 2.3, 0.85, -1);
        focus = V(BED - 0.6, 1.3, -3.15);
      } else {
        put(HERO, 1, t > 42.0 ? "dazed" : "pained", BED - 0.6, 0.62, -3.15, { mode: "sit" });
        for (let i = 0; i < 9; i++) {
          const t0 = 40.25 + i * 0.22, u = smooth((t - t0) / 0.8);
          if (u <= 0) continue;
          const tx = BED - 1.7 + 2.4 * hsh(i, 1), ty = 1.7 + 1.2 * hsh(i, 2), tz = -3.6 + 0.9 * hsh(i, 3);
          think(`n${i}`, CITY_THOUGHTS[i % CITY_THOUGHTS.length], BED + 0.65 + (tx - BED - 0.65) * u, 1.9 + (ty - 1.9) * u, -4.1 + (tz + 4.1) * u, t0, 0.75 + 0.2 * hsh(i, 4), i % 2 ? 1 : -1);
        }
        think("own", dots, BED - 0.45, 1.75, -2.7, 42.2, 0.42, -1);
        focus = V(BED - 0.6, 1.3, -3.15);
      }
    }
    if (set === "cafe") {
      put(BARISTA, 2, t > 4.9 ? "smile" : "neutral", CAFE + 0.25, 0, -2.6);
      put(HERO, 1, t > 6.1 ? "nervous" : "grin", CAFE - 0.85, 0, -0.3, { look: t > 6.1 ? 0.6 : 0.3 });
      think("brave", words(["THAT HAIR...", "BRAVE."], INK, 100), CAFE + 0.75, 2.75, -2.4, 4.95, 1.55, -1);
      focus = t < 5 ? V(CAFE - 0.3, 1.5, -1.2) : V(CAFE + 0.4, 2.0, -2.4);
    }
    if (set === "office") {
      put(BOSS, 3, t > 7.9 ? "smile_closed" : "stern", OFFICE + 0.35, 0, -3.05);
      put(folk(4), 4, "neutral", OFFICE - 1.15, 0.0, -1.9, { mode: "sit" });
      put(HERO, 1, t > 9.3 ? "grin" : "neutral", OFFICE + 1.2, 0.0, -1.75, { mode: "sit", look: -0.6 });
      think("taco", taco, OFFICE + 0.75, 2.95, -3.1, 7.9, 1.2, -1);
      think("tacos2", words(["TACOS...", "TACOS..."], "#d29a2a", 100), OFFICE - 0.55, 3.25, -3.3, 9.05, 1.1, 1);
      focus = V(OFFICE + 0.4, 2.0, -3.0);
    }
    if (set === "park") {
      put(HERO, 1, t > 13.3 ? "neutral" : "smile", PARK - 0.15, 0, -0.9, { look: 0.5 });
      add(`dog|${lid(5)}|${q((t * 3) % 1, 6)}`, (p) => dog(p, lid(5), Math.abs(Math.sin(t * 9)), -0.3), PARK + 0.65, 0, -0.35, 0.45);
      const ballWord = (p: Pen) => { ball(p, 230, 275, 90); text(p, "BALL", 470, 280, 120, INK); };
      think("b1", ballWord, PARK + 0.95, 1.0, -0.3, 12.2, 0.65, -1);
      think("b2", ballWord, PARK + 0.5, 1.6, -0.5, 12.75, 0.75, 1);
      think("b3", ballWord, PARK + 0.8, 2.25, -0.6, 13.35, 0.9, -1);
      focus = t < 11.5 ? V(PARK, 1.0, -0.6) : V(PARK + 0.55, 0.6, -0.35);
    }
    if (set === "class") {
      put(HERO, 1, t > 15.4 ? "grin" : "nervous", CLASS, 0, -1.1, { mode: "sit", look: t > 15.4 && t < 17 ? 0.5 : 0 });
      put(SMART, 6, t > 18.9 ? "shock" : "stern", CLASS + 0.3, 0, -2.95, { mode: "sit" });
      for (const [x, z, v] of [[-1.5, -1.1, 7], [1.5, -1.1, 8], [-1.3, -2.95, 9], [1.8, -2.95, 10]] as const) put(folk(v), v, "neutral", CLASS + x, 0, z, { mode: "sit" });
      const loud = t > 18.9 ? 1 + 0.45 * smooth((t - 18.9) / 0.25) : 1;
      const sh = t > 18.9 ? 0.03 * Math.sin(t * 60) : 0;
      think("ans", answers, CLASS + 0.95 + sh, 2.5 + 0.25 * (loud - 1), -3.0, 16.85, 1.3, -1, loud);
      if (t > 19.0) card("loud", 500, 300, (p) => text(p, "!!!", 250, 150, 230, "#e0463c", 22), CLASS - 0.35, 3.0, -3.0, 0.9, 0.54, pop(t, 19.0));
      focus = t < 16.5 ? V(CLASS, 1.1, -1.1) : V(CLASS + 0.4, 1.8, -2.9);
    }
    if (set === "kitchen" && id === 6) {
      put(FRIEND, 11, t > 23.2 ? "smile" : "grin", KITCHEN - 0.6, 0, -2.0, { mode: "sit" });
      put(HERO, 1, t > 23.6 ? "shock" : "grin", KITCHEN + 0.7, 0, -2.0, { mode: "sit", look: -0.5 });
      think("yuck", yuck, KITCHEN - 0.9, 2.45, -2.3, 23.25, 1.25, 1);
      focus = t < 22.5 ? V(KITCHEN, 1.2, -2) : V(KITCHEN - 0.7, 1.7, -2.1);
    }
    if (set === "kitchen" && id === 7) {
      put(MOM, 12, "smile", KITCHEN + 0.65, 0, -2.0, { mode: "sit", look: -0.4 });
      put(HERO, 1, t > 26.4 ? "nervous" : "neutral", KITCHEN - 0.6, 0, -2.0, { mode: "sit", look: 0.5 });
      think("vase", vase, KITCHEN + 1.05, 2.5, -2.3, 25.45, 1.25, -1);
      focus = V(KITCHEN + 0.6, 1.6, -2.0);
    }
    if (set === "bus") {
      put(HERO, 1, t > 29.6 ? "pained" : "neutral", BUS - 0.8, 0.36, -0.6, { mode: "sit", look: 0.4 });
      let k = 0;
      for (let i = 0; i < 8; i++) for (const sd of [-1, 1]) {
        if (i === 0 && sd < 0) continue;
        if ((i + (sd > 0 ? 1 : 0)) % 3 === 2) continue;
        const v = 20 + k++, x = BUS + sd * 0.8, z = -0.6 - i * 1.2;
        put(folk(v), v, "whistle", x, 0.36, z, { mode: "sit", headTilt: 0.06 * Math.sin(t * 5 + v) });
        const t0 = 28.15 + 0.1 * k;
        think(`nt${k % 2}`, (p) => notes(p, k % 2), x + sd * -0.15, 1.95 + 0.04 * Math.sin(t * 6 + k), z - 0.05, t0, 0.55, sd > 0 ? -1 : 1);
      }
      focus = t < 29.9 ? V(BUS, 1.2, -3) : V(BUS - 0.8, 1.2, -0.6);
    }
    if (set === "city") {
      const end = id === 15;
      const heroE: Expr = end ? (t > 62.3 ? "smile_closed" : "relief") : t > 39.2 ? "shock" : t > 35 ? "pained" : "nervous";
      put(HERO, 1, heroE, CITY, 0, 0, { look: end ? 0 : 0.3 * Math.sin(t * 2) });
      for (let i = 0; i < 26; i++) {
        const sd = i % 2 ? 1 : -1, z = 3 - i * 2.6 + 1.2 * hsh(i, 1), x = CITY + sd * (4.6 + 2.4 * hsh(i, 2)), walk = (t * 0.6 + i) % 1;
        const dir = hsh(i, 3) < 0.5 ? 1 : -1;
        put(folk(i), 40 + i, end ? "neutral" : "nervous", x, 0.15, z + dir * ((t * 0.9 + 10 * hsh(i, 5)) % 6 - 3), { mode: "stroll", phase: q(walk, 12) });
      }
      for (let i = 0; i < 6; i++) put(folk(70 + i), 70 + i, "neutral", CITY - 2.5 + i * 1.0, 0, -7 - 3 * hsh(i, 6), { mode: "stroll", phase: q((t * 0.7 + i * 0.3) % 1, 12) });
      const N = end ? 44 : Math.floor(44 * smooth((t - 33.4) / 2.6));
      for (let i = 0; i < N; i++) {
        const z = 2 - 50 * hsh(i, 7), x = CITY + (hsh(i, 8) - 0.5) * 18, y = 2.6 + (hsh(i, 9) * 10) * (1 - z / 60);
        if (Math.abs(x - CITY) < 1.5 && z > -4) continue;
        const sz = 1.2 + 1.2 * hsh(i, 10) + Math.max(0, -z) * 0.04;
        think(`c${i % CITY_THOUGHTS.length}`, CITY_THOUGHTS[i % CITY_THOUGHTS.length], x, y, z, end ? -1 : 33.4 + (2.6 * i) / 44, sz, x > CITY ? -1 : 1);
      }
      if (!end) {
        if (t < 38) card("8m", 900, 300, (p) => counter(p, "", "8,000,000", "#ffd84d"), CITY, 5.4, -6, 4.0, 1.33, pop(t, 33.95));
        think("cr", cringe, CITY + 0.95, 2.85, -0.8, 39.2, 1.25, -1);
      } else {
        think("calm", words(["AH...", "QUIET."], "#2f9c9a", 110), CITY + 0.35, 2.6, -0.6, 62.4, 0.85, -1);
      }
      focus = end || t > 38 ? V(CITY, 1.6, 0) : t > 35 ? V(CITY, 4, -12) : V(CITY, 1.6, 0);
    }
    if (set === "woods") {
      if (id === 11) {
        const u = clamp01((t - 43.2) / 3.6), ph = q((t * 2.6) % 1, 12);
        const x = WOODS + 6.2 - 6.2 * smooth(u), z = 1.6 - 2.2 * smooth(u);
        if (u < 1) put(HERO, 1, "pained", x, 0, z, { mode: "stroll", phase: ph, tilt: -0.08 });
        else put(HERO, 1, t > 47.5 ? "relief" : "neutral", WOODS - 0.05, 0, -0.6);
        for (let i = 0; i < 5; i++) { const k = 1 - smooth((t - 44.6 - i * 0.25) / 1.4); think(`w${i}`, CITY_THOUGHTS[i], x + 0.9 + 0.7 * i, 2.1 + 0.35 * (i % 2), z + 0.5 * i, 43.2, 0.85, -1, k, 47); }
        focus = V(x, 1.1, z);
      } else {
        const sq = id >= 13;
        const shock = t > 53.15, dz = id === 14 && t > 58.9;
        put(HERO, 1, dz ? "dazed" : shock ? "shock" : t > 48.4 ? "smile_closed" : "relief", WOODS, 0.37, -1.0, { mode: "sit", look: shock ? 0.6 : 0 });
        if (sq) {
          const y0 = -0.32 + 0.32 * smooth((t - 51.0) / 0.35);
          add(`sq|0|${lid(90)}|${shock}`, (p) => squirrel(p, lid(90), shock ? "neutral" : "neutral", 0), WOODS + 0.62, y0, -0.9, 0.24);
          think("hear", words(["CAN YOU", "HEAR US?"], INK, 110), WOODS + 0.85, 0.95, -1.0, 52.4, 0.62, -1, 1, id === 14 ? 57.0 : 1e9);
        }
        if (id === 14) {
          const spots = this.squirrelSpots;
          for (let i = 0; i < spots.length; i++) {
            const [x, y, z] = spots[i], t0 = 54.7 + 0.09 * i, u = smooth((t - t0) / 0.3);
            if (u <= 0) continue;
            add(`sq|${i % 3}|${lid(100 + i)}`, (p) => squirrel(p, lid(100 + i), "neutral", i % 3), x, y - 0.3 * (1 - u), z, 0.22);
            const nut = t > 58.3, c = nut ? (i % 3 === 0 ? words(["WHERE ARE", "MY NUTS?"], "#7a5232", 100) : nuts) : dots;
            const pulse = t > 60.05 ? 1 + 0.18 * Math.max(0, Math.sin((t - 60.05) * 9)) * Math.exp(-(t - 60.05) * 1.5) : 1;
            think(`s${nut ? (i % 3 === 0 ? "w" : "n") : "d"}`, c, x + (x > WOODS ? 0.35 : -0.35), y + 0.75, z, nut ? 58.3 + 0.03 * i : 56.6 + 0.04 * i, 0.85, x > WOODS ? -1 : 1, pulse);
          }
        }
        focus = id === 14 && t > 55 ? V(WOODS + 0.3, 1.5, -3) : V(WOODS + 0.3, 0.9, -1.0);
      }
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
      a.mesh.rotation.set(0, p.yaw ?? Math.atan2(cam.position.x - p.x, cam.position.z - p.z), 0);
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
    void plate;
    return focus;
  }
}
