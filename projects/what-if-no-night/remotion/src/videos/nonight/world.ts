// "What If Night Never Came Again?" as one three.js scene: village, crater lake, hut doorway and a globe in space,
// side by side along x. Same look rules as the Nyos short (two-tone materials, painted textures, lit character cards).
import * as THREE from "three";
import { Batch, boxGeo, V, lam, quad } from "../bridge/build";
import { ctex, rep, grassHD, rng } from "../bridge/paint";
import { Expr, fxStars, Pen } from "../bridge/toon";
import { LIGHTS, LOOK, LightPreset } from "../bridge/lights";
import { TONE, CHAR, untone } from "../bridge/shade";
import { NOINK } from "../bridge/ink";
import { Pool, Actor, Fx } from "../bridge/cast";
import { lantern } from "../nyos/chars";
import { person, clockSign, owl, firefly, flower, thermo, SKINS } from "./chars";
import {
  FPS, SHOTS, VILLAGE, LAKE, HUT, SPACE, Mood, camAt, riseEl, sleepAt, clockSpin, bumpAt, owlAt, flyAt, droopAt, shrinkAt,
  thermoAt, turnAt, iceAt, ringGlow, crowdAt, setAt, lampAt, smooth, clamp01,
} from "./story";

type Place = { key: string; draw: (p: Pen) => void; x: number; y: number; z: number; scale?: number; yaw?: number; roll?: number };
type FxPlace = { key: string; cw: number; ch: number; draw: (p: Pen) => void; x: number; y: number; z: number; w: number; h: number; soft?: boolean };
export type GradeSpec = { a: "day" | "golden"; b?: "day" | "golden"; k: number; amount: number };

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
const HOT: LightPreset = { ...LIGHTS.day, el: 62, lit: [1.8, 1.46, 1.02], shade: [0.42, 0.3, 0.26], charTint: [1.05, 0.9, 0.78], fog: "#ead9b0" };
const SKY: Record<string, { c: string[]; e: number[] }> = {
  day: LOOK.day.sky, golden: LOOK.golden.sky,
  hot: { c: ["#f6e2a8", "#efd9a6", "#d9d2c0", "#b8c2d2", "#94afd2"], e: [0, 3, 8, 16, 40] },
  night: { c: ["#2c3c6c", "#24335f", "#1b2852", "#131d42", "#0b1230"], e: [0, 3, 8, 16, 40] },
  space: { c: ["#05060f", "#05060f", "#04050d", "#03040b", "#020309"], e: [0, 3, 8, 16, 40] },
};
const lerpN = (a: number, b: number, k: number) => a + (b - a) * k;
const lerpA = <T extends number[]>(a: T, b: T, k: number) => a.map((v, i) => lerpN(v, b[i], k)) as T;
const tmpA = new THREE.Color(), tmpB = new THREE.Color();
const lerpHex = (a: string, b: string, k: number) => "#" + tmpA.set(a).lerp(tmpB.set(b), k).getHexString();
const mixPreset = (a: LightPreset, b: LightPreset, k: number): LightPreset => {
  const o: Record<string, unknown> = { ...a };
  for (const key of Object.keys(a) as (keyof LightPreset)[]) {
    const x = a[key], y = b[key];
    if (typeof x === "number") o[key] = lerpN(x, y as number, k);
    else if (Array.isArray(x)) o[key] = lerpA(x as number[], y as number[], k);
    else if (typeof x === "string" && x.startsWith("#")) o[key] = lerpHex(x, y as string, k);
  }
  return o as LightPreset;
};
const mixSky = (a: string, b: string, k: number) => ({ c: SKY[a].c.map((h, i) => lerpHex(h, SKY[b].c[i], k)), e: SKY[a].e });

// ---------------- textures ----------------
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
const cracked = () => ctex("cracked", 1024, 1024, (g, r) => {
  g.fillStyle = "#b98a5c"; g.fillRect(0, 0, 1024, 1024);
  g.strokeStyle = "#6e4a30"; g.lineWidth = 5;
  for (let i = 0; i < 160; i++) { let x = 1024 * r(), y = 1024 * r(); g.beginPath(); g.moveTo(x, y); for (let k = 0; k < 4; k++) { x += (r() - 0.5) * 120; y += (r() - 0.5) * 120; g.lineTo(x, y); } g.stroke(); }
});
const radial = () => ctex("radialIce", 512, 512, (g) => {
  const gr = g.createRadialGradient(256, 256, 0, 256, 256, 256); gr.addColorStop(0, "#000"); gr.addColorStop(1, "#fff");
  g.fillStyle = gr; g.fillRect(0, 0, 512, 512);
});
const earthMap = () => ctex("earthMap", 1024, 512, (g, r) => {
  g.fillStyle = "#2f7fc4"; g.fillRect(0, 0, 1024, 512);
  for (let i = 0; i < 26; i++) { // continents: clusters of blobs
    const cx = 1024 * r(), cy = 110 + 290 * r(), n = 6 + Math.floor(10 * r());
    g.fillStyle = r() < 0.75 ? "#5fae4f" : "#c9b06a";
    for (let k = 0; k < n; k++) { g.beginPath(); g.ellipse(cx + (r() - 0.5) * 140, cy + (r() - 0.5) * 90, 20 + 50 * r(), 14 + 34 * r(), r() * 3, 0, 7); g.fill(); }
  }
  g.fillStyle = "#f4f8ff"; g.fillRect(0, 0, 1024, 34); g.fillRect(0, 478, 1024, 34);
});

const SKY_V = "varying vec3 vP; void main(){ vP = normalize(position); gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0); }";
const SKY_F = `uniform vec3 c0, c1, c2, c3, c4; uniform vec4 e; varying vec3 vP;
  void main(){ float el = asin(clamp(normalize(vP).y, -1.0, 1.0));
    vec3 c = mix(c0, c1, smoothstep(0.0, e.x, el)); c = mix(c, c2, smoothstep(e.x, e.y, el));
    c = mix(c, c3, smoothstep(e.y, e.z, el)); c = mix(c, c4, smoothstep(e.z, e.w, el)); gl_FragColor = vec4(c, 1.0); }`;
const GLOBE_V = `varying vec3 vN; varying vec2 vUv; varying vec3 vW;
  void main(){ vUv = uv; vN = normalize(mat3(modelMatrix) * normal); vec4 w = modelMatrix * vec4(position, 1.0); vW = w.xyz; gl_Position = projectionMatrix * viewMatrix * w; }`;
const GLOBE_F = `uniform sampler2D map; uniform vec3 sunDir; uniform float ice; uniform float ring; varying vec3 vN; varying vec2 vUv; varying vec3 vW;
  void main(){ vec3 n = normalize(vN); float d = dot(n, sunDir); vec3 base = texture2D(map, vUv).rgb;
    vec3 day = base * (0.55 + 0.75 * clamp(d, 0.0, 1.0));
    vec3 frozen = mix(base, vec3(0.9, 0.95, 1.0), 0.7 * ice * smoothstep(-0.05, -0.5, d));
    vec3 night = frozen * 0.1 + vec3(0.01, 0.015, 0.05);
    vec3 c = mix(night, day, smoothstep(-0.08, 0.08, d));
    float band = exp(-pow(d / 0.11, 2.0));
    c += ring * band * vec3(1.6, 0.75, 0.25);
    vec3 v = normalize(cameraPosition - vW); float rim = pow(1.0 - max(dot(n, v), 0.0), 3.0);
    c += rim * vec3(0.25, 0.45, 0.9) * (0.3 + 0.7 * smoothstep(-0.3, 0.3, d));
    gl_FragColor = vec4(c, 1.0); }`;

// ---------------- terrain ----------------
const LAKE_R = 30;
const noise2 = (x: number, z: number) => Math.sin(x * 0.21 + Math.sin(z * 0.13) * 2) * Math.cos(z * 0.17 + x * 0.05) + 0.5 * Math.sin(x * 0.53 + z * 0.41);
export const craterH = (x: number, z: number) => {
  const r = Math.hypot(x, z);
  if (r < LAKE_R) return -2.5 * (1 - (r / LAKE_R) ** 2) - 0.2;
  const wall = 15 * smooth((r - LAKE_R + 1) / 17) + 0.6 * noise2(x, z) * smooth((r - LAKE_R) / 6);
  return r < 48 ? wall : 15 + 1.2 * noise2(x * 0.5, z * 0.5) - 0.08 * (r - 48);
};
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
  private stars: THREE.Points; private moon: THREE.Mesh;
  private disc: THREE.Mesh; private halo: THREE.Mesh;
  private lake: THREE.Mesh; private lakeMat: THREE.MeshLambertMaterial;
  private ice: THREE.Mesh; private iceMat: THREE.MeshLambertMaterial;
  private grassM: THREE.MeshLambertMaterial; private craterT: THREE.Mesh; private snowM: THREE.MeshLambertMaterial;
  private snow: THREE.Points;
  private globe: THREE.Mesh; private globeMat: THREE.ShaderMaterial; private crowd: THREE.Points;
  private flame: THREE.Mesh;

  constructor() {
    const R = this.root;
    this.skyMat = new THREE.ShaderMaterial({
      uniforms: { c0: { value: new THREE.Color() }, c1: { value: new THREE.Color() }, c2: { value: new THREE.Color() }, c3: { value: new THREE.Color() }, c4: { value: new THREE.Color() }, e: { value: new THREE.Vector4() } },
      vertexShader: SKY_V, fragmentShader: SKY_F, side: THREE.BackSide, depthWrite: false, fog: false,
    });
    this.sky = new THREE.Mesh(new THREE.SphereGeometry(1100, 48, 24), this.skyMat);
    this.sky.renderOrder = -1; this.sky.frustumCulled = false; this.sky.layers.set(NOINK); R.add(this.sky);
    this.sun.castShadow = true; this.sun.shadow.mapSize.set(2048, 2048);
    R.add(this.hemi, this.sun, this.sun.target);
    // sun disc + halo (camera-relative, far away)
    this.disc = new THREE.Mesh(new THREE.SphereGeometry(1, 32, 16), new THREE.MeshBasicMaterial({ color: new THREE.Color(3, 2.8, 2.4), fog: false }));
    this.halo = new THREE.Mesh(new THREE.CircleGeometry(1, 48), new THREE.MeshBasicMaterial({ color: "#fff2c0", map: ctex("halo", 256, 256, (g) => { const gr = g.createRadialGradient(128, 128, 0, 128, 128, 128); gr.addColorStop(0, "rgba(255,255,255,0.55)"); gr.addColorStop(0.35, "rgba(255,255,255,0.22)"); gr.addColorStop(1, "rgba(255,255,255,0)"); g.fillStyle = gr; g.fillRect(0, 0, 256, 256); }), transparent: true, depthWrite: false, fog: false }));
    for (const m of [this.disc, this.halo]) { m.layers.set(NOINK); m.frustumCulled = false; m.renderOrder = -0.5; R.add(m); }
    // stars follow the camera; the moon hangs over the lake and the hut
    const sp: number[] = [], sr = rng(5);
    for (let i = 0; i < 700; i++) { const a = sr() * Math.PI * 2, el = -1.2 + sr() * 2.6; sp.push(Math.cos(a) * Math.cos(el) * 900, Math.sin(el) * 900, Math.sin(a) * Math.cos(el) * 900); }
    const sg = new THREE.BufferGeometry(); sg.setAttribute("position", new THREE.Float32BufferAttribute(sp, 3));
    this.stars = new THREE.Points(sg, new THREE.PointsMaterial({ color: "#ffffff", size: 2.2, sizeAttenuation: false, fog: false, transparent: true, opacity: 0.85 }));
    this.stars.layers.set(NOINK); this.stars.frustumCulled = false; this.stars.renderOrder = -1; R.add(this.stars);
    this.moon = new THREE.Mesh(new THREE.SphereGeometry(16, 24, 16), new THREE.MeshBasicMaterial({ color: new THREE.Color(2.4, 2.4, 2.1), fog: false }));
    this.moon.layers.set(NOINK); R.add(this.moon);

    const b = new Batch();
    const box = (x0: number, y0: number, z0: number, x1: number, y1: number, z1: number, m: THREE.Material, tile = 0) => b.add(boxGeo(V(x0, y0, z0), V(x1, y1, z1), tile), m);
    this.grassM = lam("nnGrass", () => ({ map: rep(grassHD(), 30, 30) })) as THREE.MeshLambertMaterial;
    this.snowM = lam("nnSnow", () => ({ color: "#e9f1fb" })) as THREE.MeshLambertMaterial;
    const grassM = this.grassM;
    const rockM = lam("nnRock", () => ({ color: "#8a8578" }));
    const mudM = lam("mud", () => ({ map: rep(mud(), 2, 1) }));
    const thatchM = lam("thatch", () => ({ map: rep(thatch(), 3, 1) }));
    const leafM = lam("leaf", () => ({ color: "#3f8f45" })), leaf2 = lam("leaf2", () => ({ color: "#57a64a" })), bark = lam("bark", () => ({ color: "#7a5236" }));
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
    const bush = (x: number, y: number, z: number, s: number) => b.add(new THREE.IcosahedronGeometry(0.6 * s, 1).scale(1.3, 0.8, 1).translate(x, y + 0.35 * s, z), rnd() < 0.5 ? leafM : leaf2);

    // ---- CRATER LAKE ----
    this.craterT = terrain(300, 200, (x, z) => craterH(x, z), LAKE, grassM); R.add(this.craterT);
    const bed = new THREE.Mesh(new THREE.CircleGeometry(LAKE_R + 1.5, 96).rotateX(-Math.PI / 2), lam("crackedMud", () => ({ map: rep(cracked(), 4, 4) })));
    bed.position.set(LAKE, -0.12, 0); bed.receiveShadow = true; R.add(bed);
    this.lakeMat = lam("nnLake", () => ({ color: "#2f78b8" })) as THREE.MeshLambertMaterial;
    this.lake = new THREE.Mesh(new THREE.CircleGeometry(LAKE_R + 1.5, 96).rotateX(-Math.PI / 2), this.lakeMat);
    this.lake.position.set(LAKE, 0, 0); this.lake.receiveShadow = true; R.add(this.lake);
    this.iceMat = new THREE.MeshLambertMaterial({ color: "#d6ecfa", alphaMap: radial(), alphaTest: 0.99 });
    this.ice = new THREE.Mesh(new THREE.CircleGeometry(LAKE_R + 1.5, 96).rotateX(-Math.PI / 2), this.iceMat);
    this.ice.position.set(LAKE, 0.03, 0); R.add(this.ice);
    for (let i = 0; i < 46; i++) { const a = rnd() * Math.PI * 2, r = LAKE_R + 1 + rnd() * 3; b.add(new THREE.DodecahedronGeometry(0.4 + rnd() * 0.9).scale(1, 0.6, 1).translate(LAKE + Math.cos(a) * r, craterH(Math.cos(a) * r, Math.sin(a) * r), Math.sin(a) * r), rockM); }
    for (let i = 0; i < 70; i++) { const a = rnd() * Math.PI * 2, r = LAKE_R + 6 + rnd() * 30, x = Math.cos(a) * r, z = Math.sin(a) * r; if (z > 20 && Math.abs(x) < 25) continue; tree(LAKE + x, craterH(x, z) - 0.2, z, 1.4 + rnd() * 1.2); }
    // snowfall (shot 13)
    const fp: number[] = [], fr = rng(8);
    for (let i = 0; i < 900; i++) fp.push(LAKE - 40 + 80 * fr(), 40 * fr(), -30 + 85 * fr());
    const fg = new THREE.BufferGeometry(); fg.setAttribute("position", new THREE.Float32BufferAttribute(fp, 3));
    this.snow = new THREE.Points(fg, new THREE.PointsMaterial({ color: "#ffffff", size: 5, sizeAttenuation: false, fog: false }));
    this.snow.layers.set(NOINK); this.snow.frustumCulled = false; R.add(this.snow);

    // ---- VILLAGE ----
    R.add(terrain(160, 120, (x, z) => villageH(x, z), VILLAGE, grassM));
    b.add(quad(V(VILLAGE - 1.3, 0.04, 30), V(VILLAGE + 1.3, 0.04, 30), V(VILLAGE + 1.3, 0.04, -3), V(VILLAGE - 1.3, 0.04, -3), 1, 12), lam("dirt", () => ({ map: rep(dirt(), 1, 1) })));
    const huts: [number, number, number, number][] = [[-4.2, -1, 1.0, 0.4], [4.0, 2, 0.95, -0.5], [-5, 7, 1.05, 0.9], [4.6, 9, 1.0, -0.9], [-3.8, -7, 0.9, 0.2], [3.5, -9, 0.95, -0.2], [-1.5, -15, 0.85, 0], [6, -16, 0.9, -0.3], [-7.5, 2.5, 0.9, 1.2]];
    for (const [x, z, s, yaw] of huts) hut(VILLAGE + x, villageH(x, z) - 0.05, z, s, yaw);
    for (let i = 0; i < 40; i++) { const x = (rnd() - 0.5) * 70, z = -6 - rnd() * 40; if (Math.abs(x) < 9 && z > -18) continue; tree(VILLAGE + x, villageH(x, z) - 0.2, z, 1 + rnd()); }
    for (let i = 0; i < 12; i++) tree(VILLAGE + (rnd() < 0.5 ? -1 : 1) * (14 + rnd() * 20), 0, 12 + rnd() * 20, 1 + rnd() * 0.8);
    // owl tree (shot 7) with a branch, firefly bushes (shot 8), flower bed (shot 9)
    tree(VILLAGE + 13, 0, 3.4, 1.7); box(VILLAGE + 13, 2.5, 3.33, VILLAGE + 16.2, 2.62, 3.47, bark);
    for (let i = 0; i < 9; i++) bush(VILLAGE - 11.5 + (rnd() - 0.5) * 6, 0, 3.6 + rnd() * 1.5 - (i % 3 === 0 ? 2 : 0), 0.8 + 0.6 * rnd());
    for (let i = 0; i < 6; i++) bush(VILLAGE + 6 + (rnd() - 0.5) * 2.4, 0, 5.2 - rnd() * 1.2, 0.4 + 0.3 * rnd());

    // ---- HUT doorway ----
    R.add(terrain(60, 30, (x, z) => 0.04 * noise2(x * 3, z * 3), HUT, lam("dirtGround", () => ({ map: rep(dirt(), 8, 8) }))));
    b.add(new THREE.CylinderGeometry(2.4, 2.45, 2.6, 40).translate(HUT, 1.3, -2.4), mudM);
    b.add(new THREE.ConeGeometry(3.1, 2.4, 40).translate(HUT, 2.6 + 1.2, -2.4), thatchM);
    box(HUT - 0.42, 0, -0.1, HUT + 0.42, 1.55, 0.12, lam("doorDark", () => ({ color: "#1c1418" })));
    box(HUT - 0.5, 1.55, -0.12, HUT + 0.5, 1.65, 0.14, bark);
    for (const x of [-0.5, 0.5]) box(HUT + x - 0.05, 0, -0.12, HUT + x + 0.05, 1.65, 0.14, bark);
    box(HUT + 0.62, 1.3, -0.02, HUT + 0.66, 1.34, 0.22, bark);
    for (const [x, z] of [[-1.3, 0.6], [1.4, 0.4]]) b.add(new THREE.CylinderGeometry(0.22, 0.18, 0.4, 14).translate(HUT + x, 0.2, z), lam("pot", () => ({ color: "#a65a3a" })));
    this.flame = new THREE.Mesh(new THREE.SphereGeometry(0.04, 10, 8), new THREE.MeshBasicMaterial({ color: new THREE.Color(3, 2, 0.8) }));
    this.flame.position.set(HUT + 0.64, 1.12, 0.2); this.flame.layers.set(NOINK); R.add(this.flame);

    // ---- SPACE: the globe ----
    this.globeMat = new THREE.ShaderMaterial({ uniforms: { map: { value: earthMap() }, sunDir: { value: new THREE.Vector3(0, 0, 1) }, ice: { value: 0 }, ring: { value: 0 } }, vertexShader: GLOBE_V, fragmentShader: GLOBE_F, fog: false });
    this.globe = new THREE.Mesh(new THREE.SphereGeometry(10, 96, 64), this.globeMat);
    this.globe.position.set(SPACE, 0, 0); this.globe.layers.set(NOINK); R.add(this.globe);
    const cp: number[] = [];
    for (let i = 0; i < 1400; i++) cp.push(Math.random(), Math.random(), Math.random());
    const cg = new THREE.BufferGeometry(); cg.setAttribute("position", new THREE.Float32BufferAttribute(new Float32Array(1400 * 3), 3));
    this.crowd = new THREE.Points(cg, new THREE.PointsMaterial({ color: new THREE.Color(2.2, 1.6, 0.8), size: 4.5, sizeAttenuation: false, fog: false }));
    this.crowd.layers.set(NOINK); this.crowd.frustumCulled = false; R.add(this.crowd);
    b.build(R);
  }

  private actor(i: number) { while (this.actors.length <= i) this.actors.push(new Actor(this.root)); return this.actors[i]; }
  private fx(i: number) { while (this.fxs.length <= i) this.fxs.push(new Fx(this.root)); return this.fxs[i]; }

  update(id: number, f: number, cam: THREE.PerspectiveCamera, scene: THREE.Scene): { focus: THREE.Vector3; grade: GradeSpec } {
    const t = f / FPS, s = SHOTS[id - 1], mood: Mood = s.mood;
    const c = camAt(id, f);
    cam.position.set(...c.pos); cam.up.set(0, 1, 0); cam.lookAt(...c.look); cam.rotateZ(c.roll);
    cam.fov = c.fov; cam.near = 0.05; cam.far = 1500; cam.updateProjectionMatrix(); cam.updateMatrixWorld();
    cam.layers.enable(NOINK);
    let focus = V(...c.look);
    const dist = cam.position.distanceTo(focus);

    // ---- mood: preset, sky, grade, visible sun disc ----
    let L: LightPreset = LIGHTS.day, sky = SKY.day, grade: GradeSpec = { a: "day", k: 0, amount: 1 };
    let disc: [number, number] | null = null, discR = 34, discCol = [3.2, 3.0, 2.6], night = false;
    if (mood === "golden") { L = LIGHTS.golden; sky = SKY.golden; grade = { a: "golden", k: 0, amount: 0.85 }; disc = [5, 8]; discR = 30; discCol = [3.2, 1.7, 0.7]; }
    if (mood === "sunset") {
      const k = setAt(t), dk = smooth((k - 0.7) / 0.3);
      L = mixPreset(LIGHTS.golden, NIGHT, 0.75 * dk); sky = mixSky("golden", "night", 0.8 * dk); grade = { a: "golden", b: "day", k: 0.6 * dk, amount: 0.85 - 0.25 * dk };
      disc = [6, 7 - 11 * k]; discR = 30; discCol = [3.2, 1.5, 0.6];
      night = dk > 0.5;
    }
    if (mood === "rise") {
      const el = riseEl(t), k = clamp01((el - 4) / 40);
      L = mixPreset(LIGHTS.golden, LIGHTS.day, k); sky = mixSky("golden", "day", k); grade = { a: "golden", b: "day", k, amount: 0.9 };
      disc = [0, el]; discR = 34; discCol = [3.2, 1.7 + 1.3 * k, 0.7 + 1.9 * k];
    }
    if (mood === "hot") { const k = id === 11 ? 1 : smooth((t - 29) / 3); L = mixPreset(LIGHTS.day, HOT, 0.4 + 0.6 * k); sky = mixSky("day", "hot", 0.4 + 0.6 * k); disc = [0, 5 + 3 * k]; discR = 60 + 30 * k; discCol = [3.4, 3.0, 2.2]; }
    if (mood === "night") { L = NIGHT; sky = SKY.night; grade = { a: "day", k: 0, amount: 0.55 }; night = true; }
    if (mood === "space") { L = NIGHT; sky = SKY.space; grade = { a: "day", k: 0, amount: 0.35 }; }

    // light direction: camera-relative (backlit when the disc is in frame, else the preset's az/el)
    const fwd = new THREE.Vector3(c.look[0] - c.pos[0], 0, c.look[2] - c.pos[2]).normalize();
    const dirAt = (azDeg: number, elDeg: number) => {
      const az = THREE.MathUtils.degToRad(azDeg), el = THREE.MathUtils.degToRad(elDeg);
      const hx = fwd.x * Math.cos(az) - fwd.z * Math.sin(az), hz = fwd.z * Math.cos(az) + fwd.x * Math.sin(az);
      return new THREE.Vector3(hx * Math.cos(el), Math.sin(el), hz * Math.cos(el)).normalize();
    };
    const lightDir = mood === "golden" || mood === "sunset" ? dirAt(disc![0] + 70, Math.max(10, disc![1] + 6)) : mood === "night" ? dirAt(140, 34) : dirAt(L.az + 25, L.el);
    this.hemi.color.set(L.sky); this.hemi.groundColor.set(L.ground); this.hemi.intensity = L.hemiI;
    this.sun.color.set(L.sunCol); this.sun.intensity = L.sunI;
    const Rr = THREE.MathUtils.clamp(dist * 1.2 + 4, 5, 80);
    this.sun.position.copy(focus).addScaledVector(lightDir, 160); this.sun.target.position.copy(focus);
    const sc = this.sun.shadow.camera; sc.left = -Rr; sc.right = Rr; sc.top = Rr; sc.bottom = -Rr; sc.near = 20; sc.far = 340; sc.updateProjectionMatrix();
    this.sun.shadow.bias = L.bias; this.sun.shadow.normalBias = L.normalBias * (Rr / 12);
    TONE.uLitCol.value.set(...L.lit); TONE.uShadeCol.value.set(...L.shade); TONE.uShadeLift.value.set(...L.lift);
    TONE.uLambert.value = L.lambert; TONE.uSideK.value = L.sideK; TONE.uTerm.value = L.term; TONE.uBounce.value.set(0, 0, 0);
    TONE.uSat.value = night ? 0.6 : mood === "hot" ? 0.9 : 0.85;
    CHAR.uCharTint.value.set(...L.charTint); CHAR.uCharShade.value = L.charShade; CHAR.uGrad.value = L.charGrad;
    CHAR.uBodyGrad.value = L.bodyGrad; CHAR.uSideTint.value.set(...L.sideTint);
    const su = this.skyMat.uniforms;
    sky.c.forEach((h, i) => untone(h, su["c" + i].value));
    const e = sky.e.map((deg) => THREE.MathUtils.degToRad(deg)); su.e.value.set(e[1], e[2], e[3], e[4]);
    this.sky.position.copy(cam.position);
    untone(L.fog, this.fog.color);
    this.fog.near = mood === "space" ? 4000 : night ? 60 : 40; this.fog.far = mood === "space" ? 5000 : night ? 420 : 380;
    scene.fog = this.fog; scene.background = null;
    // sun disc
    this.disc.visible = this.halo.visible = !!disc;
    if (disc) {
      const d = dirAt(disc[0], disc[1]);
      this.disc.position.copy(cam.position).addScaledVector(d, 900); this.disc.scale.setScalar(discR);
      (this.disc.material as THREE.MeshBasicMaterial).color.setRGB(discCol[0], discCol[1], discCol[2]);
      this.halo.position.copy(cam.position).addScaledVector(d, 905); this.halo.scale.setScalar(discR * 2.6); this.halo.quaternion.copy(cam.quaternion);
      (this.halo.material as THREE.MeshBasicMaterial).color.setRGB(discCol[0] / 3.2, discCol[1] / 3.2, discCol[2] / 3.2);
    }
    this.stars.visible = night || mood === "space"; this.stars.position.copy(cam.position);
    this.moon.visible = night && (s.set === "lake" || s.set === "hut");
    if (s.set === "lake") this.moon.position.set(LAKE - 90, 70, -700); else this.moon.position.set(HUT - 60, 140, -700);

    // ---- props ----
    const hotK = mood === "hot" ? (id === 11 ? 1 : smooth((t - 29) / 3)) : 0;
    this.grassM.color.set(lerpHex("#ffffff", "#f0cf7a", hotK));
    const frozen = id === 13;
    this.craterT.material = frozen ? this.snowM : this.grassM;
    this.lakeMat.color.set(night ? "#24467a" : mood === "hot" ? lerpHex("#3a8cc0", "#5aa0b8", hotK) : "#3a8cc0");
    const sh = id === 11 ? shrinkAt(t) : 0;
    this.lake.scale.set(1 - 0.6 * sh, 1, 1 - 0.6 * sh);
    this.ice.visible = frozen; this.iceMat.alphaTest = clamp01(1 - 0.995 * iceAt(t)) * 0.99 + 0.005;
    this.snow.visible = frozen; this.snow.position.y = -((t * 3) % 40); this.snow.position.x = Math.sin(t) * 0.5;
    this.globe.visible = this.crowd.visible = s.set === "space";
    if (s.set === "space") {
      const g = this.globeMat.uniforms;
      let sd: THREE.Vector3;
      if (id === 12) { const a = Math.PI * 0.25 + turnAt(t) * Math.PI * 0.95; sd = new THREE.Vector3(Math.sin(a), 0.15, Math.cos(a)).normalize(); g.ice.value = smooth((t - 41) / 2.5); g.ring.value = 0; }
      else { sd = new THREE.Vector3(1, 0.25, -0.55).normalize(); g.ice.value = 1; g.ring.value = ringGlow(t); }
      g.sunDir.value.copy(sd);
      this.globe.rotation.y = t * 0.05;
      // crowd: dots on the terminator circle, gathering in from the sides
      const u = new THREE.Vector3(0, 1, 0).cross(sd).normalize(), w = sd.clone().cross(u).normalize();
      const pa = this.crowd.geometry.attributes.position as THREE.BufferAttribute, cr = rng(77), k = id === 14 ? crowdAt(t) : 0;
      for (let i = 0; i < pa.count; i++) {
        const th = cr() * Math.PI * 2, off = (cr() - 0.5) * 0.16, from = (cr() - 0.5) * 1.6, d0 = off + from * (1 - k);
        const show = i < pa.count * k;
        const dir = u.clone().multiplyScalar(Math.cos(th)).addScaledVector(w, Math.sin(th)).multiplyScalar(Math.cos(d0)).addScaledVector(sd, Math.sin(d0)).normalize();
        pa.setXYZ(i, show ? SPACE + dir.x * 10.04 : 0, show ? dir.y * 10.04 : -9999, show ? dir.z * 10.04 : 0);
      }
      pa.needsUpdate = true;
    }
    const lamp = id === 17 ? lampAt(t) : 1;
    (this.flame.material as THREE.MeshBasicMaterial).color.setRGB(3 * lamp, 2 * lamp, 0.8 * lamp); this.flame.visible = lamp > 0.02 && s.set === "hut";

    // ---- cast ----
    const P: Place[] = [], FX: FxPlace[] = [];
    const add = (key: string, draw: (p: Pen) => void, x: number, y: number, z: number, scale = 1, extra: Partial<Place> = {}) => P.push({ key, draw, x, y, z, scale, ...extra });
    const lid = (i: number) => blinkAt(f, i);
    const guy = (i: number, ex: Expr, x: number, y: number, z: number, sc = 0.62, arms = 0, zz = 0, roll = 0) => {
      const bl = lid(i), col = SKINS[i % SKINS.length];
      add(`p|${col}|${ex}|${bl}|${arms}|${q(zz, 10)}`, (p) => person(p, col, ex, bl, arms, zz), x, y, z, sc, { roll });
    };
    if (id === 1 || id === 16) { // watching the sunset
      const wave = id === 16 && t > 55.5;
      [[-0.9, 7.5], [0.4, 6.2], [1.6, 7.8]].forEach(([x, z], i) => guy(i + 1, i === 1 ? "smile" : "smile_closed", VILLAGE + x, 0, z, 0.6, wave && i !== 1 ? 1 : 0));
    }
    if (id === 3) { // endless summer party
      for (let i = 0; i < 7; i++) {
        const x = -3 + i * 1.0, z = 4 + (i % 2) * 1.3, ph = i * 1.3, hop = Math.max(0, Math.sin(t * 7 + ph)) * 0.35;
        guy(i, i % 3 === 0 ? "laugh" : "grin", VILLAGE + x, hop, z, 0.6, (Math.floor(t * 3.5 + i) % 2) as 0 | 1);
      }
    }
    if (id === 4) { // kids play, one falls asleep standing up
      const sl = sleepAt(t);
      for (let i = 0; i < 3; i++) {
        const asleep = i === 1 && sl > 0;
        const hop = asleep ? 0 : Math.max(0, Math.sin(t * 9 + i * 2)) * 0.25, x = [-0.4, 0.6, 1.5][i] + (asleep ? 0 : 0.15 * Math.sin(t * 3 + i));
        guy(i + 10, asleep ? "smile_closed" : "laugh", VILLAGE + x, hop, [5.6, 5.2, 4.6][i], 0.45, asleep ? 0 : 1, asleep ? sl : 0, asleep ? 0.12 * sl : 0);
      }
      focus = V(VILLAGE + 0.6, 0.7, 5.2);
    }
    if (id === 5) { // body clock waiting for darkness
      const tired = t > 17.5;
      guy(20, tired ? "pained" : "neutral", VILLAGE, 0, 5, 0.75);
      const ang = clockSpin(t);
      FX.push({ key: `clock|${q(ang % (Math.PI * 2), 15)}`, cw: 600, ch: 600, draw: (p) => clockSign(p, ang), x: VILLAGE, y: 2.05, z: 5, w: 0.7, h: 0.7 });
      focus = V(VILLAGE, 1.3, 5);
    }
    if (id === 6) { // grumpy and clumsy: bump
      const k = clamp01((t - (bumpAt - 1.2)) / 1.2), after = t > bumpAt;
      const gap = after ? 0.52 + 0.5 * smooth((t - bumpAt) / 0.4) : 1.6 - 1.1 * k;
      guy(21, after ? "dazed" : "stern", VILLAGE - gap / 2, 0, 5.2, 0.5, 0, 0, after ? -0.15 : 0);
      guy(22, after ? "dazed" : "stern", VILLAGE + gap / 2, 0, 5.2, 0.5, 0, 0, after ? 0.15 : 0);
      guy(23, "pained", VILLAGE + 1.6, 0, 3.6, 0.5);
      if (after) { const k2 = ((t - bumpAt) * 1.2) % 1; for (const sx of [-1, 1]) FX.push({ key: `stars|${q(k2, 15)}`, cw: 420, ch: 210, draw: (p) => fxStars(p, k2), x: VILLAGE + sx * (gap / 2), y: 1.12, z: 5.25, w: 0.9, h: 0.45 }); }
      focus = V(VILLAGE, 0.7, 5.2);
    }
    if (id === 7) { const sq = t > owlAt ? 1 : 0; add(`owl|${sq}|${lid(30)}`, (p) => owl(p, sq, lid(30)), VILLAGE + 15.5, 2.6, 3.45, 0.42); focus = V(VILLAGE + 15.5, 3.05, 3.45); }
    if (id === 8) {
      for (let i = 0; i < 3; i++) {
        const x = VILLAGE - 11.5 + (i - 1) * 0.55 + 0.12 * Math.sin(t * 2 + i), y = 0.7 + 0.15 * Math.sin(t * 3 + i * 2), look = Math.sin(t * 1.5 + i * 2);
        const gl = 0.35 + 0.15 * Math.sin(t * 6 + i);
        FX.push({ key: `fly|${q(gl, 10)}|${q(look, 4)}`, cw: 400, ch: 400, draw: (p) => firefly(p, gl, look), x, y, z: 5.5 + (i - 1) * 0.3, w: 0.5, h: 0.5 });
      }
      focus = V(VILLAGE - 11.5, 0.8, 5.5);
    }
    if (id === 9) { const op = 0.08 * Math.max(0, Math.sin(t * 4)), dr = droopAt(t); add(`flower|${q(op, 30)}|${q(dr, 20)}`, (p) => flower(p, op, dr), VILLAGE + 6, 0, 6, 0.42); focus = V(VILLAGE + 6, 0.48, 6); }
    if (id === 11) {
      const lv = 0.35 + 0.6 * thermoAt(t);
      FX.push({ key: `thermo|${q(lv, 30)}`, cw: 300, ch: 900, draw: (p) => thermo(p, lv), x: LAKE + 3.2, y: 4.6, z: 26, w: 1.6, h: 4.8 });
      focus = V(LAKE, 0, 8);
    }
    if (id === 15) { // packed crowd on the golden strip
      const k = clamp01((t - 49.6) / 1.2);
      const cr = rng(31);
      for (let i = 0; i < 34; i++) {
        const x = (cr() - 0.5) * 9 * (1 - 0.35 * k), z = 1 + cr() * 7, bl = lid(40 + i), col = SKINS[i % SKINS.length], ex: Expr = i % 4 === 0 ? "nervous" : i % 3 === 0 ? "grin" : "smile";
        add(`p|${col}|${ex}|${bl}|0|0`, (p) => person(p, col, ex, bl, 0, 0), VILLAGE + x, 0, z, 0.55);
      }
    }
    if (id === 17) {
      FX.push({ key: `lantern|${q(lamp, 20)}`, cw: 600, ch: 1000, draw: (p) => lantern(p, lamp), x: HUT + 0.68, y: 0.98, z: 0.24, w: 0.5, h: 0.83, soft: true });
      const zz = clamp01((t - 59.1) / 1.0);
      guy(3, "smile_closed", HUT - 0.05, 0, 0.35, 0.48, 0, zz);
      focus = V(HUT, 0.9, 0);
    }

    // ---- place cards ----
    let ai = 0; const used: Actor[] = [];
    for (const p of P) {
      const sc2 = p.scale ?? 1, d = cam.position.distanceTo(V(p.x, p.y + 1.1 * sc2, p.z)) / sc2;
      const [w, h, k] = tier(d);
      const a = this.actor(ai++);
      a.r = this.pool.req(p.key, w, h, k, p.draw);
      a.mesh.visible = true; a.mesh.position.set(p.x, p.y, p.z);
      a.mesh.rotation.set(0, p.yaw ?? Math.atan2(cam.position.x - p.x, cam.position.z - p.z), p.roll ?? 0);
      a.mesh.scale.set(sc2, sc2, sc2); a.mesh.castShadow = true;
      used.push(a);
    }
    for (let i = ai; i < this.actors.length; i++) this.actors[i].mesh.visible = false;
    let fi = 0; const fused: Fx[] = [];
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
    void flyAt;
    return { focus, grade };
  }
}
