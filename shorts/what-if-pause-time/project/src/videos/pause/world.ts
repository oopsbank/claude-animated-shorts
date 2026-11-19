// The world of "What If You Could Pause Time, But Only You Got Older?": a town street (road, zebra crossing, traffic
// lights, a cake stall, a red bus), his bedroom, the classroom, a school running track and a navy studio for the maths.
// Sky, sun, two-tone shading and ink come from the bridge / beer-flood look.
import * as THREE from "three";
import { Batch, V, lam, boxGeo, quad } from "./build";
import { ctex, rep, stoneHD, planksHD, cloudHD, grassHD, facadeHD, rng } from "./paint";
import { LIGHTS, LOOK, LightPreset } from "./lights";
import { TONE, CHAR, untone } from "./shade";
import { NOINK } from "./ink";
import { Pool, Actor, Fx, stage } from "./cast";
import { FPS, SHOTS, ShotDef, ROOM, CLASS, FIELD, STUDIO, CURB, BUS_X, BUS_LEN, STALL, camAt, busFront, frozenAt, T_CAKE, T_UNPAUSE, T_CLICK4, T_BUS } from "./story";

type Mats = Record<string, THREE.Material>;

// ---------------- textures ----------------
const asphaltTex = () => ctex("asphalt", 512, 512, (g, r) => {
  g.fillStyle = "#6f717a"; g.fillRect(0, 0, 512, 512);
  for (let i = 0; i < 2600; i++) { g.fillStyle = `rgba(${r() < 0.5 ? "40,40,48" : "160,160,168"},${0.08 + r() * 0.12})`; g.fillRect(r() * 512, r() * 512, 2 + r() * 4, 2 + r() * 4); }
  for (let i = 0; i < 6; i++) { g.strokeStyle = "rgba(40,40,46,0.35)"; g.lineWidth = 2; g.beginPath(); let x = r() * 512, y = r() * 512; g.moveTo(x, y); for (let k = 0; k < 6; k++) { x += (r() - 0.5) * 60; y += r() * 40; g.lineTo(x, y); } g.stroke(); }
});
const wallpaperTex = () => ctex("wallpaper", 512, 512, (g) => {
  g.fillStyle = "#bfd8e8"; g.fillRect(0, 0, 512, 512);
  for (let x = 0; x < 512; x += 64) { g.fillStyle = "#b0cde0"; g.fillRect(x, 0, 26, 512); }
  for (let y = 0; y < 512; y += 64) for (let x = 0; x < 512; x += 64) { g.fillStyle = "#f4f8fb"; g.beginPath(); g.arc(x + 45, y + 32, 4, 0, 6.3); g.fill(); }
});
const classWallTex = () => ctex("classWall", 512, 512, (g) => {
  g.fillStyle = "#f1e5c8"; g.fillRect(0, 0, 512, 512);
  g.fillStyle = "#c9b48c"; g.fillRect(0, 380, 512, 132);
  g.fillStyle = "#a8926a"; g.fillRect(0, 372, 512, 10);
});
const windowTex = () => ctex("roomWin", 256, 320, (g) => {
  const gr = g.createLinearGradient(0, 0, 0, 320); gr.addColorStop(0, "#7fb6ef"); gr.addColorStop(1, "#cfe4f6");
  g.fillStyle = gr; g.fillRect(0, 0, 256, 320);
  g.fillStyle = "#ffffff"; for (const [x, y, s] of [[60, 90, 26], [90, 80, 34], [120, 92, 24], [190, 170, 18], [210, 162, 24]]) { g.beginPath(); g.arc(x, y, s, 0, 6.3); g.fill(); }
  g.fillStyle = "#86b86a"; g.fillRect(0, 262, 256, 58);
  g.fillStyle = "#c97a5a"; g.fillRect(30, 220, 60, 50); g.fillStyle = "#e8d6b8"; g.fillRect(150, 200, 70, 70);
  g.strokeStyle = "#f4f4f0"; g.lineWidth = 16; g.strokeRect(8, 8, 240, 304); g.lineWidth = 9;
  g.beginPath(); g.moveTo(128, 0); g.lineTo(128, 320); g.moveTo(0, 160); g.lineTo(256, 160); g.stroke();
});
const boardTex = () => ctex("blackboard", 1024, 512, (g, r) => {
  g.fillStyle = "#2f5a48"; g.fillRect(0, 0, 1024, 512);
  for (let i = 0; i < 40; i++) { g.fillStyle = `rgba(255,255,255,${0.02 + r() * 0.04})`; g.fillRect(r() * 1024, r() * 512, 60 + r() * 200, 20 + r() * 40); }
  g.strokeStyle = "rgba(245,245,235,0.85)"; g.lineWidth = 6; g.lineCap = "round";
  // chalk sums and a triangle (scribbles, no words)
  for (let row = 0; row < 4; row++) {
    let x = 80; const y = 100 + row * 95;
    for (let k = 0; k < 7; k++) { g.beginPath(); g.moveTo(x, y); for (let j = 0; j < 4; j++) g.lineTo(x + 8 + r() * 26, y - 20 + r() * 40); g.stroke(); x += 50 + r() * 30; }
  }
  g.beginPath(); g.moveTo(720, 380); g.lineTo(900, 380); g.lineTo(720, 160); g.closePath(); g.stroke();
  g.strokeStyle = "#7a5a3a"; g.lineWidth = 26; g.strokeRect(0, 0, 1024, 512);
});
const posterTex = (k: number) => ctex("poster" + k, 256, 340, (g) => {
  const bg = ["#f5c4c8", "#cfe4f6", "#f3e3c6"][k % 3];
  g.fillStyle = bg; g.fillRect(0, 0, 256, 340);
  g.fillStyle = ["#e5483f", "#3b6fb6", "#4f9a50"][k % 3];
  if (k % 3 === 0) { g.beginPath(); g.arc(128, 150, 80, 0, 6.3); g.fill(); g.fillStyle = "#ffd35a"; g.beginPath(); g.arc(128, 150, 40, 0, 6.3); g.fill(); }
  else if (k % 3 === 1) { g.beginPath(); g.moveTo(40, 260); g.lineTo(128, 60); g.lineTo(216, 260); g.fill(); g.fillStyle = "#ffffff"; g.beginPath(); g.moveTo(98, 130); g.lineTo(128, 60); g.lineTo(158, 130); g.fill(); }
  else { for (let i = 0; i < 4; i++) { g.fillRect(40 + i * 46, 260 - 40 - i * 40, 32, 40 + i * 40); } }
  g.strokeStyle = "#ffffff"; g.lineWidth = 14; g.strokeRect(0, 0, 256, 340);
});
const trackTex = () => ctex("track", 512, 512, (g, r) => {
  g.fillStyle = "#c8553d"; g.fillRect(0, 0, 512, 512);
  for (let i = 0; i < 1500; i++) { g.fillStyle = `rgba(${r() < 0.5 ? "120,40,30" : "230,120,100"},${0.15})`; g.fillRect(r() * 512, r() * 512, 3, 3); }
});
const awningTex = () => ctex("awning", 256, 128, (g) => {
  for (let i = 0; i < 8; i++) { g.fillStyle = i % 2 ? "#f6f1e6" : "#e0453c"; g.fillRect(i * 32, 0, 32, 128); }
  g.fillStyle = "rgba(0,0,0,0.12)"; g.fillRect(0, 100, 256, 28);
});
const busTex = () => ctex("busSide", 1024, 256, (g) => {
  g.fillStyle = "#d8323a"; g.fillRect(0, 0, 1024, 256);
  g.fillStyle = "#2d3a52"; for (let x = 40; x < 980; x += 118) g.fillRect(x, 44, 100, 92);
  g.fillStyle = "rgba(255,255,255,0.35)"; for (let x = 40; x < 980; x += 118) g.fillRect(x + 12, 52, 14, 76);
  g.fillStyle = "#f6f1e6"; g.fillRect(0, 150, 1024, 16);
  g.fillStyle = "#ffd35a"; g.fillRect(0, 230, 1024, 10);
});
const busFrontTex = () => ctex("busFront", 256, 320, (g) => {
  g.fillStyle = "#d8323a"; g.fillRect(0, 0, 256, 320);
  g.fillStyle = "#2d3a52"; g.fillRect(16, 30, 224, 130);
  g.fillStyle = "rgba(255,255,255,0.3)"; g.fillRect(40, 40, 20, 110);
  g.fillStyle = "#1d1e22"; g.fillRect(40, 6, 176, 20);
  g.fillStyle = "#fff3c0"; for (const x of [42, 214]) { g.beginPath(); g.arc(x, 260, 18, 0, 6.3); g.fill(); }
  g.fillStyle = "#3a3d47"; g.fillRect(70, 250, 116, 22);
  g.fillStyle = "#f6f1e6"; g.fillRect(0, 196, 256, 12);
});
const studioTex = () => ctex("studioBack", 512, 512, (g) => {
  g.fillStyle = "#283149"; g.fillRect(0, 0, 512, 512);
  g.strokeStyle = "rgba(140,170,230,0.18)"; g.lineWidth = 3;
  for (let x = 0; x <= 512; x += 64) { g.beginPath(); g.moveTo(x, 0); g.lineTo(x, 512); g.stroke(); }
  for (let y = 0; y <= 512; y += 64) { g.beginPath(); g.moveTo(0, y); g.lineTo(512, y); g.stroke(); }
});
const rugTex = () => ctex("rug", 512, 512, (g) => {
  g.fillStyle = "#e9a03b"; g.fillRect(0, 0, 512, 512);
  g.strokeStyle = "#f6e2b0"; g.lineWidth = 18; g.strokeRect(30, 30, 452, 452);
  g.fillStyle = "#c9572e"; for (let i = 0; i < 5; i++) { g.beginPath(); g.arc(256, 256, 200 - i * 40, 0, 6.3); g.fill(); g.fillStyle = i % 2 ? "#c9572e" : "#f6e2b0"; }
});

/** horizontal quad facing up at height dy covering x0..x1, z0..z1 (z0 < z1) */
function quadUp(x0: number, x1: number, z0: number, z1: number, u: number, v: number, dy = 0) {
  const y = dy, g = new THREE.BufferGeometry();
  g.setAttribute("position", new THREE.Float32BufferAttribute([x0, y, z1, x1, y, z1, x1, y, z0, x0, y, z1, x1, y, z0, x0, y, z0], 3));
  g.setAttribute("normal", new THREE.Float32BufferAttribute([0, 1, 0, 0, 1, 0, 0, 1, 0, 0, 1, 0, 0, 1, 0, 0, 1, 0], 3));
  g.setAttribute("uv", new THREE.Float32BufferAttribute([0, 0, u, 0, u, v, 0, 0, u, v, 0, v], 2));
  return g;
}
const cyl = (r: number, h: number, x: number, y: number, z: number, n = 20) => { const g = new THREE.CylinderGeometry(r, r, h, n); g.translate(x, y + h / 2, z); return g; };

export class World {
  root = new THREE.Group();
  private pool = new Pool();
  private actors: Actor[] = [];
  private fxs: Fx[] = [];
  private street = new THREE.Group(); private bus = new THREE.Group(); private cakes: THREE.Mesh[] = [];
  private redLamps: THREE.Mesh[] = [];
  private room = new THREE.Group(); private box!: THREE.Group;
  private klass = new THREE.Group(); private chair!: THREE.Mesh;
  private field = new THREE.Group();
  private studio = new THREE.Group();
  private hemi: THREE.HemisphereLight; private sun: THREE.DirectionalLight;
  private sky: THREE.Mesh; private skyMat: THREE.ShaderMaterial;
  private fog = new THREE.Fog("#bccbec", 25, 420);
  private sunCache = new Map<number, THREE.Vector3>();
  private cloudMaps: Record<"day" | "golden", THREE.Texture[]>;
  private clouds: THREE.Mesh[] = [];
  private frustum = new THREE.Frustum();
  private m4 = new THREE.Matrix4(); private v = new THREE.Vector3(); private sph = new THREE.Sphere();

  constructor() {
    const R = this.root, M: Mats = {};
    R.add(this.street, this.room, this.klass, this.field, this.studio);
    // ---- sky + light (as the bridge) ----
    this.skyMat = new THREE.ShaderMaterial({
      uniforms: { c0: { value: new THREE.Color() }, c1: { value: new THREE.Color() }, c2: { value: new THREE.Color() },
        c3: { value: new THREE.Color() }, c4: { value: new THREE.Color() }, e: { value: new THREE.Vector4() } },
      vertexShader: "varying vec3 vP; void main(){ vP = normalize(position); gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0); }",
      fragmentShader: `uniform vec3 c0, c1, c2, c3, c4; uniform vec4 e; varying vec3 vP;
        void main(){ float el = asin(clamp(normalize(vP).y, -1.0, 1.0));
          vec3 c = mix(c0, c1, smoothstep(0.0, e.x, el));
          c = mix(c, c2, smoothstep(e.x, e.y, el));
          c = mix(c, c3, smoothstep(e.y, e.z, el));
          c = mix(c, c4, smoothstep(e.z, e.w, el));
          if (el < 0.0) c = mix(c0, c0 * vec3(0.92, 0.95, 1.0), smoothstep(0.0, -0.3, el));
          gl_FragColor = vec4(c, 1.0); }`,
      side: THREE.BackSide, depthWrite: false, fog: false,
    });
    this.sky = new THREE.Mesh(new THREE.SphereGeometry(1100, 48, 24), this.skyMat);
    this.sky.renderOrder = -1; this.sky.frustumCulled = false; this.sky.layers.set(NOINK);
    R.add(this.sky);
    this.hemi = new THREE.HemisphereLight("#cfe6ff", "#6c5c8c", 1.1);
    this.sun = new THREE.DirectionalLight("#fff0d6", 2.6);
    this.sun.castShadow = true;
    this.sun.shadow.mapSize.set(2048, 2048);
    R.add(this.hemi, this.sun, this.sun.target);
    this.cloudMaps = { day: [0, 1, 2, 3].map((k) => cloudHD(k, LOOK.day.cloud)), golden: [0, 1, 2, 3].map((k) => cloudHD(k, LOOK.golden.cloud)) };
    for (let i = 0; i < 9; i++) {
      const a = (i / 9) * Math.PI * 2 + 0.3, d = 620 + (i % 3) * 60;
      const m = new THREE.Mesh(new THREE.PlaneGeometry(1, 1), new THREE.MeshBasicMaterial({ map: this.cloudMaps.day[i % 4], color: new THREE.Color(1.1, 1.1, 1.1), transparent: true, depthWrite: false, fog: false }));
      const w = 130 + (i % 4) * 30;
      m.position.set(Math.cos(a) * d, 120 + (i % 4) * 38, Math.sin(a) * d); m.scale.set(w, w / 2, 1);
      m.layers.set(NOINK); this.clouds.push(m); R.add(m);
    }

    // ---- materials ----
    M.asphalt = lam("asphalt", () => ({ map: rep(asphaltTex(), 2, 80) }));
    M.paving = lam("paving", () => ({ map: rep(stoneHD("paveHD", ["#c9c6be", "#bfbcb4", "#d3d0c8", "#b8b5ad"], "#9a978f"), 1, 60) }));
    M.kerb = lam("kerb", () => ({ color: "#a9a7a0" }));
    M.white = lam("whitePaint", () => ({ color: "#f3f2ee" }));
    M.pole = lam("pole", () => ({ color: "#3a3f4a" }));
    M.lampOff = lam("lampOff", () => ({ color: "#2a2d33" }));
    M.trunk = lam("trunk", () => ({ color: "#8a5a3c" }));
    M.leaf = lam("leafTown", () => ({ color: "#5c9a4a" }));
    M.awning = lam("awning", () => ({ map: awningTex() }));
    M.table = lam("stallTable", () => ({ color: "#f6f1e6" }));
    M.cakeBody = lam("cakeBody", () => ({ color: "#f4d9a6" }));
    M.icing = lam("icing", () => ({ color: "#ff9ec4" }));
    M.icing2 = lam("icing2", () => ({ color: "#8a5a3c" }));
    M.cherry = lam("cherry", () => ({ color: "#d8283a" }));
    M.busSide = lam("busSide", () => ({ map: busTex() }));
    M.busFront = lam("busFront", () => ({ map: busFrontTex() }));
    M.busRed = lam("busRed", () => ({ color: "#d8323a" }));
    M.rubber = lam("rubber", () => ({ color: "#1d1e22" }));
    M.wallpaper = lam("wallpaper", () => ({ map: rep(wallpaperTex(), 3, 1.5) }));
    M.floor = lam("floorWood", () => ({ map: rep(planksHD(), 1.2, 1.2) }));
    M.wood = lam("woodFurn", () => ({ color: "#b07a4a" }));
    M.woodDark = lam("woodDark", () => ({ color: "#7a4f33" }));
    M.sheet = lam("sheet", () => ({ color: "#f7f7f4" }));
    M.duvet = lam("duvet", () => ({ color: "#5b8fd6" }));
    M.rug = lam("rug", () => ({ map: rugTex() }));
    M.hall = lam("hall", () => ({ color: "#e8d6b0" }));
    M.boxBrown = lam("shoebox", () => ({ color: "#c9955a" }));
    M.classWall = lam("classWall", () => ({ map: rep(classWallTex(), 4, 1) }));
    M.classFloor = lam("classFloor", () => ({ color: "#c9b79a" }));
    M.desk = lam("deskTop", () => ({ color: "#d9b07a" }));
    M.metal = lam("deskMetal", () => ({ color: "#5a6070" }));
    M.board = lam("blackboard", () => ({ map: boardTex() }));
    M.grass = lam("grassHD", () => ({ map: rep(grassHD(), 30, 30), color: "#b9c99a" }));
    M.track = lam("track", () => ({ map: rep(trackTex(), 20, 2) }));
    M.bleacher = lam("bleacher", () => ({ color: "#9aa3b5" }));
    M.studio = lam("studioBack", () => ({ map: rep(studioTex(), 6, 2) }));
    M.studioFloor = lam("studioFloor", () => ({ color: "#3a4560" }));
    const red = new THREE.MeshBasicMaterial({ color: new THREE.Color(4.0, 0.5, 0.4) });
    const roomWin = new THREE.MeshBasicMaterial({ map: windowTex(), color: 0xeeeeee });

    // ---- the street ----
    const sb = new Batch();
    sb.add(quadUp(-4, 4, -160, 160, 1, 1, 0), M.asphalt);
    for (const s of [-1, 1]) {
      sb.add(boxGeo(V(s > 0 ? 4 : -8.2, -0.2, -160), V(s > 0 ? 8.2 : -4, CURB, 160)), M.paving);
      sb.add(boxGeo(V(s > 0 ? 4 : -4.2, -0.2, -160), V(s > 0 ? 4.2 : -4, CURB + 0.01, 160)), M.kerb);
      // centre-line dashes and edge lines
      sb.add(quadUp(s * 3.7 - 0.06, s * 3.7 + 0.06, -160, 160, 1, 1, 0.005), M.white);
    }
    for (let z = -158; z < 160; z += 6) if (Math.abs(z) > 4) sb.add(quadUp(-0.07, 0.07, z, z + 3, 1, 1, 0.005), M.white);
    // the zebra crossing
    for (let x = -3.6; x < 3.6; x += 1.0) sb.add(quadUp(x, x + 0.5, -1.6, 1.6, 1, 1, 0.006), M.white);
    // stop lines
    sb.add(quadUp(-4, 0, -3.0, -2.7, 1, 1, 0.006), M.white); sb.add(quadUp(0, 4, 2.7, 3.0, 1, 1, 0.006), M.white);
    // buildings both sides, fronts painted
    const rb = rng(31);
    const walls = ["#e8d2b0", "#d9b9a0", "#cfd8c4", "#e9c9b8", "#d6d0e4", "#f0e0b8"], shut = ["#3b6fb6", "#4f9a50", "#c25a3a", "#6a5a9a"];
    let bi = 0;
    for (const s of [-1, 1]) {
      let z = -120;
      while (z < 120) {
        const w = 7 + Math.floor(rb() * 4), h = 7.5 + Math.floor(rb() * 3) * 1.6, d = 9, x0 = s > 0 ? 8.2 : -8.2 - d, x1 = s > 0 ? 8.2 + d : -8.2;
        const bakery = s > 0 && z <= STALL[2] && z + w > STALL[2];
        const fac = lam(`fac${bi}`, () => ({ map: facadeHD(`street${bi}`, w, h, { wall: walls[bi % walls.length], shutter: shut[bi % shut.length], door: true, brick: bi % 5 === 2 }) }));
        const side = lam(`side${bi % walls.length}`, () => ({ color: walls[bi % walls.length] }));
        const fx = s > 0 ? x0 : x1;
        // the front face toward the road
        if (s > 0) sb.add(quad(V(fx, CURB, z), V(fx, CURB, z + w), V(fx, CURB + h, z + w), V(fx, CURB + h, z)), fac);
        else sb.add(quad(V(fx, CURB, z + w), V(fx, CURB, z), V(fx, CURB + h, z), V(fx, CURB + h, z + w)), fac);
        sb.add(boxGeo(V(Math.min(x0, x1) + (s > 0 ? 0.02 : 0), CURB, z + 0.02), V(Math.max(x0, x1) - (s > 0 ? 0 : 0.02), CURB + h, z + w - 0.02)), side);
        sb.add(boxGeo(V(s > 0 ? fx - 0.25 : fx - 0.01, CURB + h, z - 0.05), V(s > 0 ? fx + 0.01 : fx + 0.25, CURB + h + 0.3, z + w + 0.05)), M.white);
        if (bakery) {
          const ax = s * 1.4;
          sb.add(quad(V(fx, CURB + 3.0, z + 0.8), V(fx, CURB + 3.0, z + w - 0.8), V(fx - ax, CURB + 2.5, z + w - 0.8), V(fx - ax, CURB + 2.5, z + 0.8), 3, 1), M.awning);
          sb.add(quad(V(fx - ax, CURB + 2.5, z + 0.8), V(fx - ax, CURB + 2.5, z + w - 0.8), V(fx, CURB + 3.0, z + w - 0.8), V(fx, CURB + 3.0, z + 0.8), 3, 1), M.awning);
        }
        z += w; bi++;
      }
      // trees and lamp posts along the kerb
      for (let zz = -110; zz < 110; zz += 13) {
        if (Math.abs(zz - STALL[2]) < 3 || Math.abs(zz) < 4) continue;
        const tx = s * 7.2;
        sb.add(cyl(0.12, 2.4, tx, CURB, zz + 2, 8), M.trunk);
        sb.add(new THREE.SphereGeometry(1.25, 12, 9).scale(1, 1.15, 1).translate(tx, CURB + 3.2, zz + 2), M.leaf);
        sb.add(cyl(0.07, 4.6, s * 4.5, CURB, zz + 8.5, 8), M.pole);
        sb.add(boxGeo(V(s * 4.5 - (s > 0 ? 0.9 : 0), CURB + 4.5, zz + 8.4), V(s * 4.5 + (s > 0 ? 0 : 0.9), CURB + 4.62, zz + 8.6)), M.pole);
      }
    }
    // traffic lights at the crossing: pole + head (red lit for the bus's lane)
    for (const [x, z, face] of [[-4.5, -2.4, -1], [4.5, 2.4, 1]] as [number, number, number][]) {
      sb.add(cyl(0.08, 3.2, x, CURB, z, 10), M.pole);
      sb.add(boxGeo(V(x - 0.18, CURB + 2.4, z - 0.15), V(x + 0.18, CURB + 3.35, z + 0.15)), M.pole);
      for (let k = 0; k < 3; k++) {
        const lamp = new THREE.Mesh(new THREE.CircleGeometry(0.1, 16), k === 0 ? red : lam("lampOff", () => ({ color: "#2a2d33" })));
        lamp.position.set(x, CURB + 3.2 - k * 0.3, z + face * 0.16); if (face < 0) lamp.rotation.y = Math.PI;
        lamp.layers.set(NOINK); this.street.add(lamp); if (k === 0) this.redLamps.push(lamp);
      }
    }
    // the cake stall: table + cakes (they vanish one by one while he eats)
    const [sx, sy, sz] = STALL;
    sb.add(boxGeo(V(sx - 0.45, sy + 0.82, sz - 1.0), V(sx + 0.45, sy + 0.9, sz + 1.0)), M.table);
    sb.add(boxGeo(V(sx - 0.42, sy, sz - 0.97), V(sx + 0.42, sy + 0.82, sz + 0.97)), lam("stallCloth", () => ({ color: "#e5a0b8" })));
    sb.build(this.street);
    for (let k = 0; k < 8; k++) {
      const g = new THREE.Group(), cb = new Batch(), x = sx - 0.18 + (k % 2) * 0.36, z = sz - 0.78 + Math.floor(k / 2) * 0.52;
      cb.add(cyl(0.15, 0.14, x, sy + 0.9, z), M.cakeBody);
      cb.add(cyl(0.155, 0.04, x, sy + 1.04, z), k % 3 === 1 ? M.icing2 : M.icing);
      cb.add(new THREE.SphereGeometry(0.03, 8, 6).translate(x, sy + 1.1, z), M.cherry);
      cb.build(g); this.street.add(g); this.cakes.push(g as unknown as THREE.Mesh);
    }
    // the bus
    const bb = new Batch(), L = BUS_LEN;
    bb.add(quad(V(1.25, 0.35, 0), V(1.25, 0.35, -L), V(1.25, 3.2, -L), V(1.25, 3.2, 0)), M.busSide);
    bb.add(quad(V(-1.25, 0.35, -L), V(-1.25, 0.35, 0), V(-1.25, 3.2, 0), V(-1.25, 3.2, -L)), M.busSide);
    bb.add(quad(V(-1.25, 0.35, 0), V(1.25, 0.35, 0), V(1.25, 3.2, 0), V(-1.25, 3.2, 0)), M.busFront);
    bb.add(boxGeo(V(-1.25, 3.2, -L), V(1.25, 3.3, 0)), M.busRed);
    bb.add(quad(V(1.25, 0.35, -L), V(-1.25, 0.35, -L), V(-1.25, 3.2, -L), V(1.25, 3.2, -L)), M.busRed);
    for (const z of [-1.8, -L + 2.2]) for (const x of [-1.15, 1.15]) { const w = new THREE.CylinderGeometry(0.48, 0.48, 0.3, 20); w.rotateZ(Math.PI / 2); w.translate(x, 0.48, z); bb.add(w, M.rubber); }
    bb.build(this.bus); this.street.add(this.bus);

    // ---- the bedroom ----
    const ob = new Batch(), [rx, , rz] = ROOM, H = 3.4;
    const P = (x: number, y: number, z: number) => V(rx + x, y, rz + z);
    ob.add(quadUp(rx - 3, rx + 3, rz - 2.5, rz + 2.5, 1, 1, 0), M.floor);
    ob.add(quadUp(rx - 1.4, rx + 1.2, rz - 0.6, rz + 1.6, 1, 1, 0.005), M.rug);
    ob.add(quad(P(-3, 0, -2.5), P(3, 0, -2.5), P(3, H, -2.5), P(-3, H, -2.5)), M.wallpaper);
    ob.add(quad(P(-3, 0, 2.5), P(-3, 0, -2.5), P(-3, H, -2.5), P(-3, H, 2.5)), M.wallpaper);
    ob.add(quad(P(3, 0, -2.5), P(3, 0, 2.5), P(3, H, 2.5), P(3, H, -2.5)), M.wallpaper);
    // the door opening in the left wall (a hallway behind) and its open door leaf
    ob.add(quad(P(-2.99, 0, 2.05), P(-2.99, 0, 1.05), P(-2.99, 2.15, 1.05), P(-2.99, 2.15, 2.05)), M.hall);
    ob.add(boxGeo(P(-3.0, 0, 0.98), P(-2.92, 2.22, 1.05)), M.white); ob.add(boxGeo(P(-3.0, 0, 2.05), P(-2.92, 2.22, 2.12)), M.white);
    ob.add(boxGeo(P(-3.0, 2.15, 0.98), P(-2.92, 2.25, 2.12)), M.white);
    ob.add(boxGeo(P(-2.9, 0, 2.08), P(-2.0, 2.1, 2.13)), lam("doorLeaf", () => ({ color: "#f0e8d8" })));
    // bed: frame, mattress, pillow, a puffy duvet
    ob.add(boxGeo(P(-2.85, 0, -2.45), P(-0.75, 0.35, -0.4)), M.wood);
    ob.add(boxGeo(P(-2.85, 0.35, -2.45), P(-2.75, 1.05, -0.4)), M.wood);
    ob.add(boxGeo(P(-2.75, 0.35, -2.4), P(-0.78, 0.55, -0.45)), M.sheet);
    ob.add(boxGeo(P(-2.72, 0.55, -2.0), P(-2.25, 0.72, -0.85)), M.sheet);
    ob.add(boxGeo(P(-2.05, 0.55, -2.4), P(-0.72, 0.86, -0.42)), M.duvet);
    // nightstand, desk + chair, shelf, posters
    ob.add(boxGeo(P(-0.68, 0, -2.42), P(-0.28, 0.56, -1.95)), M.woodDark);
    ob.add(boxGeo(P(1.3, 0.74, -1.98), P(2.9, 0.8, -1.32)), M.wood);
    for (const [x, z] of [[1.35, -1.93], [2.85, -1.93], [1.35, -1.37], [2.85, -1.37]]) ob.add(boxGeo(P(x - 0.03, 0, z - 0.03), P(x + 0.03, 0.74, z + 0.03)), M.woodDark);
    ob.add(boxGeo(P(1.85, 0, -2.45), P(2.35, 0.45, -2.0)), M.woodDark);
    ob.add(boxGeo(P(1.85, 0.45, -2.48), P(2.35, 1.0, -2.42)), M.woodDark);
    ob.add(boxGeo(P(0.2, 1.6, -2.5), P(1.2, 1.66, -2.25)), M.woodDark);
    for (let k = 0; k < 6; k++) ob.add(boxGeo(P(0.25 + k * 0.15, 1.66, -2.45), P(0.36 + k * 0.15, 1.9 - (k % 3) * 0.05, -2.3)), lam(`book${k % 3}`, () => ({ color: ["#3b6fb6", "#e5683a", "#4f9a50"][k % 3] })));
    ob.build(this.room, false);
    const win = new THREE.Mesh(new THREE.PlaneGeometry(1.3, 1.5), roomWin); win.position.set(rx - 1.5, 1.95, rz - 2.49); win.layers.set(NOINK); this.room.add(win);
    for (const [k, x, y, z, ry] of [[0, 0.7, 2.2, -2.49, 0], [1, 2.99, 2.0, 0.0, -Math.PI / 2], [2, -2.99, 2.0, -1.2, Math.PI / 2]] as number[][]) {
      const pm = new THREE.Mesh(new THREE.PlaneGeometry(0.6, 0.8), new THREE.MeshBasicMaterial({ map: posterTex(k), color: 0xdddddd }));
      pm.position.set(rx + x, y, rz + z); pm.rotation.y = ry; pm.layers.set(NOINK); this.room.add(pm);
    }
    this.box = new THREE.Group();
    const xb = new Batch(); xb.add(boxGeo(P(1.65, 0.8, -1.85), P(2.1, 1.02, -1.45)), M.boxBrown); xb.build(this.box); this.room.add(this.box);

    // ---- the classroom ----
    const cb2 = new Batch(), [cx, , cz] = CLASS;
    const Q = (x: number, y: number, z: number) => V(cx + x, y, cz + z);
    cb2.add(quadUp(cx - 4.5, cx + 4.5, cz - 4, cz + 5, 1, 1, 0), M.classFloor);
    cb2.add(quad(Q(-4.5, 0, -4), Q(4.5, 0, -4), Q(4.5, H, -4), Q(-4.5, H, -4)), M.classWall);
    cb2.add(quad(Q(-4.5, 0, 5), Q(-4.5, 0, -4), Q(-4.5, H, -4), Q(-4.5, H, 5)), M.classWall);
    cb2.add(quad(Q(4.5, 0, -4), Q(4.5, 0, 5), Q(4.5, H, 5), Q(4.5, H, -4)), M.classWall);
    cb2.add(quad(Q(-2.3, 0.95, -3.98), Q(2.3, 0.95, -3.98), Q(2.3, 2.45, -3.98), Q(-2.3, 2.45, -3.98)), M.board);
    cb2.add(boxGeo(Q(-2.3, 0.9, -3.98), Q(2.3, 0.95, -3.85)), M.woodDark);
    // teacher's desk
    cb2.add(boxGeo(Q(-2.6, 0, -3.2), Q(-1.3, 0.78, -2.6)), M.wood);
    // pupils' desks (in front of each seat, toward the board) + chairs
    for (const z of [-0.8, 1.0, 2.8]) for (const x of [-2.2, 0, 2.2]) {
      cb2.add(boxGeo(Q(x - 0.55, 0.7, z - 0.75), Q(x + 0.55, 0.76, z - 0.25)), M.desk);
      cb2.add(boxGeo(Q(x - 0.5, 0, z - 0.72), Q(x + 0.5, 0.7, z - 0.66)), M.metal);
      cb2.add(boxGeo(Q(x - 0.22, 0.42, z - 0.15), Q(x + 0.22, 0.46, z + 0.25)), M.metal);
      cb2.add(boxGeo(Q(x - 0.22, 0.46, z + 0.22), Q(x + 0.22, 0.95, z + 0.26)), M.metal);
    }
    cb2.build(this.klass, false);
    for (const z of [-2.5, 0.5, 3.5]) {
      const w2 = new THREE.Mesh(new THREE.PlaneGeometry(1.6, 1.4), roomWin); w2.position.set(cx - 4.49, 1.9, cz + z); w2.rotation.y = Math.PI / 2; w2.layers.set(NOINK); this.klass.add(w2);
    }
    for (const [k, z] of [[0, -2.2], [1, 0.4], [2, 3.0]]) {
      const pm = new THREE.Mesh(new THREE.PlaneGeometry(0.7, 0.9), new THREE.MeshBasicMaterial({ map: posterTex(k), color: 0xdddddd }));
      pm.position.set(cx + 4.49, 1.9, cz + z); pm.rotation.y = -Math.PI / 2; pm.layers.set(NOINK); this.klass.add(pm);
    }
    // the chair he stands on for the moustache
    this.chair = new THREE.Mesh(boxGeo(Q(-0.22, 0, -3.15), Q(0.22, 0.45, -2.75)), M.metal); this.chair.castShadow = true; this.chair.receiveShadow = true; this.klass.add(this.chair);

    // ---- the running track ----
    const fb = new Batch(), [fx0, , fz0] = FIELD;
    fb.add(quadUp(fx0 - 400, fx0 + 400, fz0 - 400, fz0 + 400, 1, 1, -0.01), M.grass);
    fb.add(quadUp(fx0 - 120, fx0 + 120, fz0 - 2.2, fz0 + 2.6, 1, 1, 0), M.track);
    for (const z of [-2.0, -0.6, 0.85, 2.25]) fb.add(quadUp(fx0 - 120, fx0 + 120, fz0 + z - 0.03, fz0 + z + 0.03, 1, 1, 0.004), M.white);
    fb.add(quadUp(fx0 + 0.72, fx0 + 0.82, fz0 - 2.2, fz0 + 2.6, 1, 1, 0.005), M.white);
    for (const z of [-2.35, 2.75]) fb.add(cyl(0.04, 1.3, fx0 + 0.77, 0, fz0 + z, 8), M.white);
    fb.add(boxGeo(V(fx0 + 0.75, 1.0, fz0 - 2.35), V(fx0 + 0.79, 1.05, fz0 + 2.75)), M.cherry);
    for (let k = 0; k < 4; k++) fb.add(boxGeo(V(fx0 - 30, k * 0.5, fz0 - 14 - k * 0.8), V(fx0 + 30, k * 0.5 + 0.5, fz0 - 13.2 - k * 0.8)), M.bleacher);
    for (let i = 0; i < 16; i++) { const x = fx0 - 60 + i * 8, z = fz0 - 26 - (i % 3) * 4; fb.add(cyl(0.2, 2.6, x, 0, z, 8), M.trunk); fb.add(new THREE.SphereGeometry(2.2, 12, 9).translate(x, 3.8, z), M.leaf); }
    fb.build(this.field);

    // ---- the studio ----
    const tb = new Batch(), [tx, ty, tz] = STUDIO;
    tb.add(new THREE.CircleGeometry(10, 48).rotateX(-Math.PI / 2).translate(tx, ty, tz), M.studioFloor);
    const back = new THREE.CylinderGeometry(10, 10, 9, 48, 1, true, Math.PI * 0.5, Math.PI); back.translate(tx, ty + 4.5, tz);
    tb.add(back, M.studio);
    tb.build(this.studio, false);
  }

  /** camera-relative sun, frozen per shot */
  private shotSun(id: number, s: ShotDef, L: LightPreset) {
    let v = this.sunCache.get(id);
    if (v) return v;
    let fx = 0, fz = 0;
    for (let f = s.a; f < s.b; f += 3) {
      const c = camAt(id, f), x = c.look[0] - c.pos[0], z = c.look[2] - c.pos[2], n = Math.hypot(x, z) || 1;
      fx += x / n; fz += z / n;
    }
    const n = Math.hypot(fx, fz) || 1; fx /= n; fz /= n;
    const SUN_SHOT: Record<number, { az?: number; el?: number }> = { 11: { az: 150, el: 40 }, 12: { az: 160, el: 55 }, 13: { az: 160, el: 50 } };
    const az = THREE.MathUtils.degToRad(SUN_SHOT[id]?.az ?? L.az), el = THREE.MathUtils.degToRad(SUN_SHOT[id]?.el ?? L.el);
    const hx = fx * Math.cos(az) - fz * Math.sin(az), hz = fz * Math.cos(az) + fx * Math.sin(az);
    v = new THREE.Vector3(hx * Math.cos(el), Math.sin(el), hz * Math.cos(el)).normalize();
    this.sunCache.set(id, v);
    return v;
  }
  private actor(i: number) { while (this.actors.length <= i) this.actors.push(new Actor(this.root)); return this.actors[i]; }
  private fx(i: number) { while (this.fxs.length <= i) this.fxs.push(new Fx(this.root)); return this.fxs[i]; }

  update(id: number, f: number, cam: THREE.PerspectiveCamera, scene: THREE.Scene) {
    const t = f / FPS, s = SHOTS[id - 1], L = LIGHTS[s.light];
    const c = camAt(id, f);
    const cp = V(...c.pos), cl = V(...c.look);
    cam.position.copy(cp); cam.up.set(0, 1, 0); cam.lookAt(cl); cam.rotateZ(c.roll);
    cam.fov = c.fov; cam.near = 0.05; cam.far = 3000; cam.updateProjectionMatrix(); cam.updateMatrixWorld();
    const focus = cl.clone(), dist = cam.position.distanceTo(focus);
    cam.layers.enable(NOINK);
    // places
    const outdoor = s.place === "street" || s.place === "field";
    this.street.visible = s.place === "street";
    this.room.visible = s.place === "room";
    this.klass.visible = s.place === "class";
    this.field.visible = s.place === "field";
    this.studio.visible = s.place === "studio";
    this.chair.visible = id === 7;
    this.box.visible = id === 16;
    // the bus (only once it comes)
    this.bus.visible = id >= 17 && t > T_BUS - 2;
    this.bus.position.set(BUS_X, 0, busFront(t));
    this.bus.rotation.set(0, 0, 0);
    // cakes go one by one
    const eaten = id === 6 ? Math.min(6, Math.max(0, Math.floor((t - T_CAKE) * 3.5))) : 0;
    this.cakes.forEach((m, k) => { m.visible = k >= eaten; });
    void frozenAt; void T_UNPAUSE; void T_CLICK4;
    // light rig
    const K = LOOK[s.light], sunDir = this.shotSun(id, s, L);
    this.hemi.color.set(L.sky); this.hemi.groundColor.set(L.ground); this.hemi.intensity = L.hemiI;
    this.sun.color.set(L.sunCol); this.sun.intensity = L.sunI;
    const Rr = THREE.MathUtils.clamp(dist * 1.15 + 7, 10, 60);
    this.sun.position.copy(focus).addScaledVector(sunDir, 220); this.sun.target.position.copy(focus);
    const sc = this.sun.shadow.camera;
    sc.left = -Rr; sc.right = Rr; sc.top = Rr; sc.bottom = -Rr; sc.near = 20; sc.far = 480; sc.updateProjectionMatrix();
    this.sun.shadow.bias = L.bias; this.sun.shadow.normalBias = L.normalBias * (Rr / 12);
    TONE.uLitCol.value.set(...L.lit); TONE.uShadeCol.value.set(...L.shade); TONE.uShadeLift.value.set(...L.lift);
    TONE.uLambert.value = L.lambert; TONE.uSideK.value = L.sideK; TONE.uTerm.value = L.term; TONE.uBounce.value.set(...K.bounce); TONE.uSat.value = K.sat;
    CHAR.uCharTint.value.set(...L.charTint); CHAR.uCharShade.value = L.charShade; CHAR.uGrad.value = L.charGrad;
    CHAR.uBodyGrad.value = L.bodyGrad; CHAR.uSideTint.value.set(...L.sideTint);
    const su = this.skyMat.uniforms;
    K.sky.c.forEach((h, i) => untone(h, su["c" + i].value));
    const e = K.sky.e.map((deg) => THREE.MathUtils.degToRad(deg));
    su.e.value.set(e[1], e[2], e[3], e[4]);
    this.sky.position.copy(cam.position);
    this.sky.visible = outdoor;
    untone(L.fog, this.fog.color); this.fog.near = outdoor ? L.fogNear : 200; this.fog.far = outdoor ? L.fogFar : 2000;
    scene.fog = this.fog; scene.background = null;
    for (let i = 0; i < this.clouds.length; i++) {
      const m = this.clouds[i], mat = m.material as THREE.MeshBasicMaterial;
      m.lookAt(cam.position.x, m.position.y, cam.position.z);
      mat.map = this.cloudMaps[s.light][i % 4];
      m.visible = outdoor;
    }
    // cast + effects
    const right = V(0, 0, 0).setFromMatrixColumn(cam.matrixWorld, 0);
    const st = stage(id, t, { pos: cam.position.clone(), right, sun: sunDir });
    this.frustum.setFromProjectionMatrix(this.m4.multiplyMatrices(cam.projectionMatrix, cam.matrixWorldInverse));
    let ai = 0;
    const used: Actor[] = [];
    for (const p of st.places) {
      const sc2 = p.scale ?? 1;
      const wp = V(p.x, p.y, p.z);
      if (!this.frustum.intersectsSphere(this.sph.set(this.v.copy(wp).add(V(0, 1.1 * sc2, 0)), 3.5))) continue;
      const a = this.actor(ai++);
      const [w, h, k] = p.size ?? [300, 500, 0.5];
      a.r = this.pool.req(p.key, w, h, k, p.draw);
      a.mesh.visible = true;
      a.mesh.position.copy(wp);
      const yaw = p.yaw ?? Math.atan2(cam.position.x - p.x, cam.position.z - p.z);
      a.mesh.rotation.set(0, yaw, p.roll ?? 0);
      a.mesh.scale.set(p.mirror ? -sc2 : sc2, sc2, sc2);
      a.mesh.castShadow = L.actorShadow;
      used.push(a);
    }
    for (let i = ai; i < this.actors.length; i++) this.actors[i].mesh.visible = false;
    let fi = 0;
    const fused: Fx[] = [];
    for (const p of st.fx) {
      const wp = V(p.x, p.y, p.z);
      if (!this.frustum.intersectsSphere(this.sph.set(wp, Math.max(p.w, p.h)))) continue;
      const ef = this.fx(fi++);
      ef.r = this.pool.req(p.key, p.cw, p.ch, 1, p.draw);
      ef.use(!!p.soft);
      ef.mesh.visible = true;
      ef.mesh.position.copy(wp);
      if (p.flat) ef.mesh.rotation.set(-Math.PI / 2, 0, p.rot ?? 0);
      else { ef.mesh.quaternion.copy(cam.quaternion); ef.mesh.rotateZ(p.rot ?? 0); }
      ef.mesh.scale.set(p.w, p.h, 1);
      fused.push(ef);
    }
    for (let i = fi; i < this.fxs.length; i++) this.fxs[i].mesh.visible = false;
    this.pool.flush();
    for (const a of used) a.bind();
    for (const ef of fused) ef.bind();
    return focus;
  }
}
