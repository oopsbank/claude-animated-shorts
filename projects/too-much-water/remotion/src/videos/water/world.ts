// The water short as one three.js scene: seven small stage sets side by side along x (bar, body office, street,
// inside-the-body cells, the skull box, kitchen table, radio studio). Same look rules as the bridge: two-tone
// materials (lam/twoTone), painted textures, camera-relative sun frozen per shot, lit character cards on NOINK.
// update(id, f, camera) poses everything for shot id at frame f and returns the lens focus point.
import * as THREE from "three";
import { Batch, boxGeo, V, lam, house, quad } from "../bridge/build";
import { ctex, rep, planksHD, stoneHD, cobbleHD, grassHD, rng } from "../bridge/paint";
import { bodyFront, bodySide, soldier, OFFICER, Outfit, Expr, fxCreak, fxPuff, SKINS, Pen } from "../bridge/toon";
import { LIGHTS, LOOK } from "../bridge/lights";
import { TONE, CHAR, untone, twoTone } from "../bridge/shade";
import { NOINK } from "../bridge/ink";
import { Pool, Actor, Fx } from "../bridge/cast";
import { drop, saltGuard, cell, brain, canteen, LIGHT } from "./chars";
import {
  FPS, SHOTS, BAR, OFFICE, STREET, CELLS, SKULL, KITCHEN, RADIO, V3, camAt, slideU, queueN, stampAt, swellAt, sweepAt,
  brainAt, spongeAt, pourAt, smooth, clamp01, TOTAL,
} from "./story";

type Place = { key: string; draw: (p: Pen) => void; x: number; y: number; z: number; scale?: number; mirror?: boolean; yaw?: number; roll?: number };
type FxPlace = { key: string; cw: number; ch: number; draw: (p: Pen) => void; x: number; y: number; z: number; w: number; h: number };

const q = (v: number, n = 30) => Math.round(v * n) / n;
const tier = (d: number): [number, number, number] =>
  d < 2.2 ? [1800, 3000, 3.0] : d < 4.5 ? [1080, 1800, 1.8] : d < 12 ? [600, 1000, 1.0] : d < 24 ? [360, 600, 0.6] : [240, 400, 0.4];
/** blinks: 4-frame blink every 0.5-2.3 s, seeded per character */
const blinkAt = (f: number, i: number) => {
  const h = (k: number) => { const v = Math.sin(i * 127.1 + k * 311.7) * 43758.5453; return v - Math.floor(v); };
  let s = Math.round(-60 * h(9));
  for (let n = 0; s <= f && n < 400; n++) { const k = f - s; if (k >= 0 && k < 4) return [0.5, 1, 1, 0.5][k]; s += Math.round(15 + 54 * h(i * 31 + n)); }
  return 0;
};

// ---------------- painted textures ----------------
const wallpaper = () => ctex("wp_bar", 512, 512, (g) => {
  g.fillStyle = "#2f6b5e"; g.fillRect(0, 0, 512, 512);
  for (let x = 0; x < 512; x += 64) { g.fillStyle = "#3a7a6c"; g.fillRect(x, 0, 30, 512); g.fillStyle = "rgba(240,210,140,.35)"; g.fillRect(x + 30, 0, 4, 512); }
});
const tiles = (key: string, a: string, b: string, n = 8, grout = "#8f8577") => ctex(key, 512, 512, (g, r) => {
  const s = 512 / n;
  for (let i = 0; i < n; i++) for (let j = 0; j < n; j++) { g.fillStyle = (i + j) % 2 ? a : b; g.fillRect(i * s, j * s, s, s); g.fillStyle = `rgba(255,255,255,${0.04 * r()})`; g.fillRect(i * s + 6, j * s + 6, s - 12, s / 3); }
  g.strokeStyle = grout; g.lineWidth = 5; for (let k = 0; k <= n; k++) { g.beginPath(); g.moveTo(k * s, 0); g.lineTo(k * s, 512); g.moveTo(0, k * s); g.lineTo(512, k * s); g.stroke(); }
});
const flesh = (key: string, base: string, vein: string) => ctex(key, 1024, 1024, (g, r) => {
  g.fillStyle = base; g.fillRect(0, 0, 1024, 1024);
  for (let i = 0; i < 260; i++) { g.fillStyle = `rgba(255,255,255,${0.05 + 0.05 * r()})`; g.beginPath(); g.arc(1024 * r(), 1024 * r(), 8 + 30 * r(), 0, 7); g.fill(); }
  g.strokeStyle = vein; g.lineCap = "round";
  for (let k = 0; k < 9; k++) {
    let x = 1024 * r(), y = 0; g.lineWidth = 6 + 10 * r(); g.beginPath(); g.moveTo(x, y);
    while (y < 1024) { x += (r() - 0.5) * 90; y += 40 + 40 * r(); g.lineTo(x, y); }
    g.stroke();
  }
});
const bone = () => ctex("bone", 1024, 1024, (g, r) => {
  g.fillStyle = "#eee0c2"; g.fillRect(0, 0, 1024, 1024);
  for (let i = 0; i < 500; i++) { g.fillStyle = `rgba(150,120,80,${0.05 * r()})`; g.beginPath(); g.arc(1024 * r(), 1024 * r(), 3 + 12 * r(), 0, 7); g.fill(); }
  g.strokeStyle = "rgba(90,70,50,.55)"; g.lineWidth = 5;
  for (let k = 0; k < 3; k++) { let x = 0, y = 200 + 300 * k + 100 * r(); g.beginPath(); g.moveTo(x, y); while (x < 1024) { x += 18 + 20 * r(); y += (r() - 0.5) * 40; g.lineTo(x, y); } g.stroke(); }
});
const foam = () => ctex("foam", 512, 512, (g) => {
  for (let i = 0; i < 8; i++) for (let j = 0; j < 8; j++) {
    const x = i * 64, y = j * 64, v = (i + j) % 2;
    const gr = g.createLinearGradient(x, y, v ? x + 64 : x, v ? y : y + 64);
    gr.addColorStop(0, "#4a4f63"); gr.addColorStop(0.5, "#5d6378"); gr.addColorStop(1, "#383c4d");
    g.fillStyle = gr; g.fillRect(x, y, 64, 64);
    g.strokeStyle = "rgba(20,20,30,.6)"; g.lineWidth = 3; g.strokeRect(x, y, 64, 64);
  }
});
const carpet = () => ctex("carpet", 512, 512, (g, r) => {
  g.fillStyle = "#3b4466"; g.fillRect(0, 0, 512, 512);
  for (let i = 0; i < 4000; i++) { g.fillStyle = `rgba(${r() < 0.5 ? "255,255,255" : "0,0,0"},0.05)`; g.fillRect(512 * r(), 512 * r(), 3, 3); }
});
const spongeTex = () => ctex("sponge", 512, 512, (g, r) => {
  g.fillStyle = "#f6d44a"; g.fillRect(0, 0, 512, 512);
  for (let i = 0; i < 380; i++) { g.fillStyle = `rgba(170,120,20,${0.35 + 0.3 * r()})`; g.beginPath(); g.ellipse(512 * r(), 512 * r(), 4 + 9 * r(), 3 + 7 * r(), r() * 3, 0, 7); g.fill(); }
});

const SKY_V = "varying vec3 vP; void main(){ vP = normalize(position); gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0); }";
const SKY_F = `uniform vec3 c0, c1, c2, c3, c4; uniform vec4 e; varying vec3 vP;
  void main(){ float el = asin(clamp(normalize(vP).y, -1.0, 1.0));
    vec3 c = mix(c0, c1, smoothstep(0.0, e.x, el)); c = mix(c, c2, smoothstep(e.x, e.y, el));
    c = mix(c, c3, smoothstep(e.y, e.z, el)); c = mix(c, c4, smoothstep(e.z, e.w, el)); gl_FragColor = vec4(c, 1.0); }`;

const CLERK = (v: number): Outfit => ({ jacket: "#f2efe6", pants: "#3b3f52", boots: "#4a3426", hat: "cap", cap: v ? "#2f7a5a" : "#2d5f8a", skin: v ? "#c4554d" : "#b84a48", belt: null, buttons: "#d9dde0" });
const BARTENDER: Outfit = { jacket: "#2f2a3a", pants: "#2a2a33", boots: "#3a2a20", hat: "hair", hair: "#3a2a20", moustache: "#3a2a20", skin: SKINS[1], buttons: "#e8c45a", build: "stout" };

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
  private glass = new THREE.Group();
  private sponge: THREE.Mesh; private waterLvl: THREE.Mesh;
  private onAir: THREE.MeshBasicMaterial;

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
    const wood = lam("planksHD", () => ({ map: planksHD() }));
    const dark = lam("darkwood", () => ({ color: "#5a3826" }));
    const brass = twoTone(new THREE.MeshPhongMaterial({ color: "#d9a640", specular: "#fff0b0", shininess: 50 }), 0.2);
    const steel = twoTone(new THREE.MeshPhongMaterial({ color: "#8d95a3", specular: "#d0d4dc", shininess: 40 }), 0.15);
    const box = (x0: number, y0: number, z0: number, x1: number, y1: number, z1: number, m: THREE.Material, tile = 0) => b.add(boxGeo(V(x0, y0, z0), V(x1, y1, z1), tile), m);
    const floor = (cx: number, w: number, d: number, m: THREE.Material, rx: number, ry: number, z0 = -d / 2) =>
      b.add(quad(V(cx - w / 2, 0, z0 + d), V(cx + w / 2, 0, z0 + d), V(cx + w / 2, 0, z0), V(cx - w / 2, 0, z0), rx, ry), m);
    const wall = (x0: number, x1: number, z: number, h: number, m: THREE.Material, rx: number, ry: number) =>
      b.add(quad(V(x0, 0, z), V(x1, 0, z), V(x1, h, z), V(x0, h, z), rx, ry), m);

    // ---- BAR ----
    floor(BAR, 14, 10, wood, 3.5, 2.5);
    wall(BAR - 7, BAR + 7, -2.4, 4.2, lam("wp_bar", () => ({ map: rep(wallpaper(), 4, 1.5) })), 1, 1);
    const wpM = lam("wp_bar", () => ({ map: rep(wallpaper(), 4, 1.5) }));
    b.add(quad(V(BAR - 7, 0, 5), V(BAR - 7, 0, -2.4), V(BAR - 7, 4.2, -2.4), V(BAR - 7, 4.2, 5), 1, 1), wpM);   // end wall (faces +x)
    b.add(quad(V(BAR + 7, 0, 5), V(BAR - 7, 0, 5), V(BAR - 7, 4.2, 5), V(BAR + 7, 4.2, 5), 1, 1), wpM);       // side wall (faces -z)
    box(BAR - 3.6, 0, -0.38, BAR + 2.0, 1.02, 0.38, dark);                 // counter body
    box(BAR - 3.7, 1.02, -0.45, BAR + 2.1, 1.1, 0.45, wood, 1);            // counter top
    box(BAR - 3.6, 0.08, 0.38, BAR + 2.0, 0.14, 0.5, brass);               // foot rail
    for (const y of [1.6, 2.25, 2.9]) box(BAR - 6, y, -2.4, BAR + 6, y + 0.05, -2.05, wood, 1);
    const bottleCols = ["#8a4b1e", "#2f6b3a", "#b8862a", "#6a2f3a", "#d9c690", "#3a5a7a"];
    const rnd = rng(7);
    for (const y of [1.65, 2.3, 2.95]) for (let x = BAR - 5.6; x < BAR + 5.6; x += 0.32 + 0.2 * rnd()) {
      const h = 0.3 + 0.18 * rnd(), col = bottleCols[Math.floor(rnd() * 6)];
      b.add(new THREE.CylinderGeometry(0.055, 0.065, h, 10).translate(x, y + h / 2, -2.22), lam("bt" + col, () => ({ color: col })));
      b.add(new THREE.CylinderGeometry(0.02, 0.03, 0.1, 8).translate(x, y + h + 0.05, -2.22), lam("bt" + col, () => ({ color: col })));
    }
    for (const x of [BAR - 3, BAR - 0.5, BAR + 2]) { // pendant lamps (HDR bulbs feed the bloom)
      b.add(new THREE.CylinderGeometry(0.008, 0.008, 1.2).translate(x, 3.6, 0), dark);
      b.add(new THREE.ConeGeometry(0.28, 0.24, 16, 1, true).translate(x, 2.92, 0), brass);
      const bulb = new THREE.Mesh(new THREE.SphereGeometry(0.09, 12, 8), new THREE.MeshBasicMaterial({ color: new THREE.Color(3.2, 2.5, 1.4) }));
      bulb.position.set(x, 2.78, 0); bulb.layers.set(NOINK); R.add(bulb);
    }
    // the glass: its own group so it can slide
    const gl = lam("glassBody", () => ({ color: "#d6f1ff" })), wt = lam("glassWater", () => ({ color: "#62bde9" }));
    const gb = new THREE.Mesh(new THREE.CylinderGeometry(0.062, 0.05, 0.16, 20), gl); gb.position.y = 0.08;
    const gw = new THREE.Mesh(new THREE.CylinderGeometry(0.0625, 0.0505, 0.115, 20), wt); gw.position.y = 0.06; gw.scale.set(1.01, 1, 1.01);
    const hi = new THREE.Mesh(new THREE.BoxGeometry(0.012, 0.11, 0.004), new THREE.MeshBasicMaterial({ color: "#ffffff" })); hi.position.set(-0.03, 0.09, 0.052); hi.layers.set(NOINK);
    for (const m of [gb, gw]) { m.castShadow = true; m.receiveShadow = true; }
    this.glass.add(gb, gw, hi); R.add(this.glass);

    // ---- BODY OFFICE (kidney counter + vault) ----
    floor(OFFICE - 3, 26, 22, lam("officeTiles", () => ({ map: rep(tiles("officeT", "#e9d8c4", "#d9bfa8"), 1, 1) })), 13, 11, -6);
    wall(OFFICE - 16, OFFICE + 10, -2.3, 4.5, lam("officeWall", () => ({ map: rep(flesh("officeW", "#e7a99a", "#c97f78"), 3, 1) })), 1, 1);
    box(OFFICE - 1.7, 0, -0.38, OFFICE + 1.7, 1.02, 0.38, lam("deskPaint", () => ({ color: "#3d6f8f" })));
    box(OFFICE - 1.8, 1.02, -0.45, OFFICE + 1.8, 1.08, 0.45, wood, 1);
    for (const x of [-1.1, -0.6, 0.6, 1.1]) box(OFFICE + x - 0.15, 1.08, -0.1, OFFICE + x + 0.15, 1.12 + 0.03 * Math.abs(x), 0.12, lam("paper", () => ({ color: "#f7f3e8" })));
    // rope barrier posts along the queue
    for (const z of [3.2, 4.8]) for (const x of [-0.7, 0.7]) {
      b.add(new THREE.CylinderGeometry(0.03, 0.03, 0.95).translate(OFFICE + x, 0.475, z), brass);
      b.add(new THREE.CylinderGeometry(0.16, 0.18, 0.05).translate(OFFICE + x, 0.025, z), brass);
    }
    // vault door on the back wall
    const vx = OFFICE - 8;
    const door = new THREE.CylinderGeometry(1.25, 1.25, 0.25, 40); door.rotateX(Math.PI / 2);
    b.add(door.translate(vx, 1.45, -2.15), steel);
    const rim = new THREE.TorusGeometry(1.32, 0.09, 10, 48); b.add(rim.translate(vx, 1.45, -2.05), steel);
    for (let k = 0; k < 3; k++) { const s = new THREE.CylinderGeometry(0.035, 0.035, 1.2); s.rotateZ((k * Math.PI) / 3); b.add(s.translate(vx, 1.45, -1.93), brass); }
    b.add(new THREE.TorusGeometry(0.5, 0.04, 8, 32).translate(vx, 1.45, -1.93), brass);
    for (let k = 0; k < 8; k++) { const a = (k / 8) * Math.PI * 2; b.add(new THREE.SphereGeometry(0.06, 8, 6).translate(vx + Math.cos(a) * 1.05, 1.45 + Math.sin(a) * 1.05, -2.0), brass); }

    // ---- STREET ----
    const cob = lam("cobbleHD", () => ({ map: cobbleHD() }));
    floor(STREET, 9, 120, cob, 2.25, 30, -90);
    const pave = lam("paveHD", () => ({ map: stoneHD("paveHD", ["#d8cdbb", "#cfc3b0", "#e0d6c6", "#c6b9a5"], "#9d907f") }));
    for (const s of [-1, 1]) {
      box(STREET + s * 4.5 - (s < 0 ? 2.5 : 0), 0, -90, STREET + s * 4.5 + (s > 0 ? 2.5 : 0), 0.14, 30, pave, 2);
      for (let z = 24, i = 0; z > -86; i++) {
        const w = 7 + (i % 3) * 1.4, d = 7, h = [7, 8.4, 9.8][i % 3];
        house(b, STREET + s * (7 + d / 2), z - w / 2, s < 0 ? Math.PI / 2 : -Math.PI / 2, w, d, h, i * 3 + (s > 0 ? 1 : 0), 0.14);
        z -= w + 0.4;
      }
    }
    b.add(quad(V(STREET - 400, -0.02, 300), V(STREET + 400, -0.02, 300), V(STREET + 400, -0.02, -500), V(STREET - 400, -0.02, -500), 200, 200),
      lam("grassHD", () => ({ map: grassHD() })));

    // ---- CELLS (inside the body) ----
    floor(CELLS, 40, 30, lam("cellFloor", () => ({ map: rep(flesh("cellF", "#f0b7a8", "#d98e86"), 2, 2) })), 1, 1);
    wall(CELLS - 20, CELLS + 20, -4, 12, lam("cellWall", () => ({ map: rep(flesh("cellW", "#e48f8f", "#b9545e"), 4, 1.5) })), 1, 1);
    for (const [x, z, r] of [[-6, -2.5, 1.2], [5.5, -3, 1.6], [-3.5, -3.2, 0.8], [7.5, -1.5, 0.7]] as const) // soft background blobs
      b.add(new THREE.SphereGeometry(r, 24, 16).scale(1, 0.8, 0.6).translate(CELLS + x, r * 0.6, z), lam("blob" + r, () => ({ color: r > 1 ? "#f2a493" : "#e9b3c6" })));

    // ---- SKULL BOX ----
    floor(SKULL, 30, 30, lam("skullFloor", () => ({ map: rep(flesh("skF", "#9b6d8f", "#7d4f74"), 2, 2) })), 1, 1);
    wall(SKULL - 15, SKULL + 15, -3, 10, lam("skullWall", () => ({ map: rep(flesh("skW", "#6f4a7a", "#4f3260"), 3, 1) })), 1, 1);
    const bm = lam("bone", () => ({ map: bone() })), T = 0.14;
    box(SKULL - 0.95, 0, -0.6, SKULL + 0.95, T, 0.6, bm);                 // floor slab
    box(SKULL - 0.95, 1.12, -0.6, SKULL + 0.95, 1.12 + T, 0.6, bm);      // lid
    box(SKULL - 0.95, T, -0.6, SKULL - 0.95 + T, 1.12, 0.6, bm);         // left
    box(SKULL + 0.95 - T, T, -0.6, SKULL + 0.95, 1.12, 0.6, bm);         // right
    box(SKULL - 0.95, T, -0.6, SKULL + 0.95, 1.12, -0.6 + T, bm);        // back
    for (const x of [-0.95, 0.95]) for (const y of [0, 1.12 + T]) b.add(new THREE.SphereGeometry(0.13, 12, 8).translate(SKULL + x, y, 0.6), bm); // bony knobs

    // ---- KITCHEN ----
    floor(KITCHEN, 10, 8, lam("kFloor", () => ({ map: rep(tiles("kFloorT", "#d9d2c3", "#3e4a5c", 6), 1, 1) })), 4, 3);
    wall(KITCHEN - 5, KITCHEN + 5, -0.95, 3.2, lam("kWall", () => ({ map: rep(tiles("kWallT", "#f3f1ea", "#e6f0ee", 10, "#b9c2c0"), 1, 1) })), 4, 1.3);
    box(KITCHEN - 1.4, 0.84, -0.75, KITCHEN + 1.4, 0.9, 0.75, wood, 1);
    for (const x of [-1.3, 1.3]) for (const z of [-0.65, 0.65]) box(KITCHEN + x - 0.04, 0, z - 0.04, KITCHEN + x + 0.04, 0.84, z + 0.04, dark);
    box(KITCHEN - 0.9, 0.9, -0.5, KITCHEN - 0.62, 0.92, -0.3, lam("plate", () => ({ color: "#f7f7f2" })));
    b.add(new THREE.CylinderGeometry(0.05, 0.06, 0.2, 14).translate(KITCHEN + 0.75, 1.0, -0.35), lam("mug", () => ({ color: "#d9534f" })));
    // the jar (see-through) + its water + the sponge
    const jarM = new THREE.MeshPhongMaterial({ color: "#dff6ff", specular: "#ffffff", shininess: 90, transparent: true, opacity: 0.32, depthWrite: false, side: THREE.DoubleSide });
    const jar = new THREE.Mesh(new THREE.CylinderGeometry(0.17, 0.17, 0.34, 32, 1, true), jarM); jar.position.set(KITCHEN, 0.9 + 0.17, 0); jar.renderOrder = 2;
    const jarRim = new THREE.Mesh(new THREE.TorusGeometry(0.17, 0.008, 8, 40), new THREE.MeshBasicMaterial({ color: "#ffffff" })); jarRim.rotation.x = Math.PI / 2; jarRim.position.set(KITCHEN, 1.24, 0);
    const jarBase = new THREE.Mesh(new THREE.CylinderGeometry(0.17, 0.17, 0.012, 32), jarM); jarBase.position.set(KITCHEN, 0.906, 0);
    R.add(jar, jarRim, jarBase);
    this.waterLvl = new THREE.Mesh(new THREE.CylinderGeometry(0.162, 0.162, 1, 32), new THREE.MeshPhongMaterial({ color: "#7cc8f0", transparent: true, opacity: 0.55, depthWrite: false }));
    this.waterLvl.renderOrder = 1; R.add(this.waterLvl);
    this.sponge = new THREE.Mesh(new THREE.BoxGeometry(1, 1, 1, 6, 6, 6), lam("spongeM", () => ({ map: spongeTex() })));
    this.sponge.castShadow = true; R.add(this.sponge);

    // ---- RADIO STUDIO ----
    floor(RADIO, 12, 10, lam("carpet", () => ({ map: rep(carpet(), 4, 4) })), 1, 1);
    wall(RADIO - 6, RADIO + 6, -2, 4, lam("foam", () => ({ map: rep(foam(), 6, 2) })), 1, 1);
    box(RADIO - 1.5, 0, -1.3, RADIO + 1.5, 0.76, -0.45, dark);
    box(RADIO - 1.6, 0.76, -1.35, RADIO + 1.6, 0.81, -0.4, wood, 1);
    const black = lam("blackGear", () => ({ color: "#26262e" }));
    for (const x of [-0.6, 0.6]) {
      b.add(new THREE.CylinderGeometry(0.012, 0.012, 0.42).translate(RADIO + x, 1.02, -0.85), steel);
      b.add(new THREE.CapsuleGeometry(0.05, 0.1, 6, 12).rotateX(-0.6).translate(RADIO + x, 1.26, -0.8), black);
    }
    box(RADIO - 0.35, 0.81, -1.25, RADIO + 0.35, 0.86, -0.95, black); // mixing desk
    for (let i = 0; i < 9; i++) { // the row of water bottles
      const x = RADIO - 1.2 + i * 0.3;
      b.add(new THREE.CylinderGeometry(0.04, 0.045, 0.26, 14).translate(x, 0.81 + 0.13, -0.52), lam("bottle", () => ({ color: "#a9dcf3" })));
      b.add(new THREE.CylinderGeometry(0.022, 0.022, 0.05, 10).translate(x, 0.81 + 0.285, -0.52), lam("cap", () => ({ color: "#f2f2f2" })));
    }
    this.onAir = new THREE.MeshBasicMaterial({ color: new THREE.Color(0.95, 0.04, 0.03), fog: false });
    const lamp = new THREE.Mesh(new THREE.BoxGeometry(0.7, 0.24, 0.06), this.onAir); lamp.position.set(RADIO, 2.4, -1.96); lamp.layers.set(NOINK); R.add(lamp);
    box(RADIO - 0.4, 2.26, -2, RADIO + 0.4, 2.54, -1.99, black);

    b.build(R);
  }

  private actor(i: number) { while (this.actors.length <= i) this.actors.push(new Actor(this.root)); return this.actors[i]; }
  private fx(i: number) { while (this.fxs.length <= i) this.fxs.push(new Fx(this.root)); return this.fxs[i]; }

  /** camera-relative sun frozen per shot (az from the shot's view axis toward screen right, el up) */
  private shotSun(id: number) {
    let v = this.sunCache.get(id);
    if (v) return v;
    const s = SHOTS[id - 1], c = camAt(id, s.a), L = LIGHTS.day;
    const x = c.look[0] - c.pos[0], z = c.look[2] - c.pos[2], n = Math.hypot(x, z) || 1, fx = x / n, fz = z / n;
    const az = THREE.MathUtils.degToRad(L.az + 25), el = THREE.MathUtils.degToRad(s.set === "street" ? L.el : 58);
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
    this.hemi.color.set(L.sky); this.hemi.groundColor.set(L.ground); this.hemi.intensity = L.hemiI;
    this.sun.color.set(L.sunCol); this.sun.intensity = L.sunI;
    const Rr = THREE.MathUtils.clamp(dist * 1.2 + 4, 5, 60);
    this.sun.position.copy(focus).addScaledVector(sunDir, 120); this.sun.target.position.copy(focus);
    const sc = this.sun.shadow.camera;
    sc.left = -Rr; sc.right = Rr; sc.top = Rr; sc.bottom = -Rr; sc.near = 20; sc.far = 260; sc.updateProjectionMatrix();
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
    untone(L.fog, this.fog.color); this.fog.near = 30; this.fog.far = 320;
    scene.fog = this.fog; scene.background = null;

    // ---- props ----
    const u = slideU(f);
    this.glass.position.set(BAR - 2.3 + 3.4 * u, 1.1, 0.02 * Math.sin(u * 3));
    this.glass.rotation.z = -0.06 * Math.sin(Math.PI * u) * (1 - u);
    if (s.set === "bar") focus = this.glass.position.clone().add(V(0, 0.08, 0));
    const sp = spongeAt(t), grow = Math.min(1, sp), press = Math.max(0, sp - 1);
    const sw = 0.13 + 0.19 * grow, sh = 0.06 + 0.2 * grow + 0.35 * press;
    this.sponge.scale.set(Math.min(0.31, sw) * (1 + 0.6 * press), sh, Math.min(0.31, sw * 0.8) * (1 + 0.6 * press));
    this.sponge.position.set(KITCHEN, 0.912 + sh / 2, 0);
    const wl = 0.005 + 0.12 * pourAt(t) * (1 - 0.8 * grow);
    this.waterLvl.scale.set(1, wl, 1); this.waterLvl.position.set(KITCHEN, 0.912 + wl / 2, 0);
    this.onAir.color.setRGB(0.95, 0.04, 0.03);

    // ---- cast ----
    const P: Place[] = [], FX: FxPlace[] = [];
    const add = (key: string, draw: (p: Pen) => void, x: number, y: number, z: number, scale = 1, extra: Partial<Place> = {}) => P.push({ key, draw, x, y, z, scale, ...extra });
    const lid = (i: number) => blinkAt(f, i);
    const stand = (o: Outfit, i: number, expr: Expr, extra: Record<string, unknown> = {}) => {
      const opts = { mode: "stand" as const, expr, blink: lid(i), light: LIGHT, seed: (i % 7) + 1, ...extra };
      return { key: `F|${JSON.stringify(o).length}|${o.jacket}|${o.skin}|${JSON.stringify(opts, (_k, v) => (typeof v === "number" ? q(v) : v))}`, draw: (p: Pen) => bodyFront(p, o, opts) };
    };
    const set = s.set;
    if (set === "bar") {
      const a = stand(BARTENDER, 1, t > 1.6 && t < 3.4 ? "stern" : "neutral", { look: 0.6 });
      add(a.key, a.draw, BAR - 1.6, 0, -1.0);
    }
    if (set === "office") {
      const thumbs = id === 13, early = id === 3;
      for (const [k, x] of [[0, -0.7], [1, 0.7]] as const) {
        const st = stampAt(t + k * 0.13);
        const expr: Expr = thumbs ? "grin" : id >= 5 ? "nervous" : id === 4 ? "stern" : "neutral";
        const a = stand(CLERK(k), 10 + k, expr, thumbs ? { wave: 1 } : { prop: ["hammer", early ? (t > 9.4 ? 1 : 0) : st] });
        add(a.key, a.draw, OFFICE + x, 0, -0.95);
      }
      // the queue: drops along a snaking path in front of the counter
      const n = id === 13 ? 1 : id === 2 ? 0 : queueN(t);
      const path: V3[] = [[0, 0, 0.75], [0, 0, 5.6], [1.4, 0, 5.6], [1.4, 0, 1.0], [2.8, 0, 1.0], [2.8, 0, 7.5], [4.4, 0, 7.5], [4.4, 0, 2.0], [5.8, 0, 2.0], [5.8, 0, 12]];
      const at = (d: number): V3 => {
        for (let i = 0; i + 1 < path.length; i++) {
          const a = path[i], b2 = path[i + 1], l = Math.hypot(b2[0] - a[0], b2[2] - a[2]);
          if (d <= l || i + 2 === path.length) { const k = d / l; return [a[0] + (b2[0] - a[0]) * k, 0, a[2] + (b2[2] - a[2]) * k]; }
          d -= l;
        }
        return path[path.length - 1];
      };
      for (let i = 0; i < n; i++) {
        const shuffle = 0.15 * Math.sin(t * 3 + i), p3 = at(i * 0.72 + Math.max(0, shuffle));
        const ph = q((t * 1.6 + i * 0.37) % 1, 8), expr: Expr = i === 0 ? "neutral" : n > 8 && i % 3 === 1 ? "nervous" : i % 4 === 2 ? "whistle" : "neutral";
        const bl = lid(30 + i);
        add(`drop|${expr}|${ph}|${bl}|${i % 3}`, (p) => drop(p, expr, ph, bl, (i % 3) / 2), OFFICE + p3[0], 0, p3[2], 0.85);
      }
      // salt guard at the vault (shot 2), salutes on "treasure"
      if (id === 2) {
        const sal = smooth((t - 5.7) / 0.3) * (1 - smooth((t - 7.4) / 0.3)), bl = lid(5);
        add(`salt|${q(sal, 8)}|${bl}`, (p) => saltGuard(p, "stern", bl, sal), OFFICE - 6.9, 0, -0.8, 1.15);
      }
    }
    if (set === "street" && id === 6) {
      const n = 46;
      for (let i = 0; i < n; i++) {
        const ph = q((t * 1.6 + i * 0.37) % 1, 8), expr: Expr = i % 5 === 1 ? "nervous" : i % 7 === 3 ? "whistle" : "neutral", bl = lid(60 + i);
        add(`drop|${expr}|${ph}|${bl}|${i % 3}`, (p) => drop(p, expr, ph, bl, (i % 3) / 2), STREET + 0.6 * Math.sin(i * 1.7), 0.0, 4 - i * 1.3, 0.9);
      }
    }
    if (set === "street" && id === 12) {
      const zF = -47 + 1.6 * Math.min(t - 45.2, 3.6), halted = t - 45.2 > 3.6;
      for (let r = 0; r < 4; r++) for (const [k, x] of [[0, -0.85], [1, 0], [2, 0.85]] as const) {
        const i = r * 3 + k, o = soldier(i % 4), bl = lid(80 + i);
        const opts = { mode: halted ? ("stand" as const) : ("march" as const), phase: q((t + (halted ? 0 : 0)) % 1, 16), expr: (halted ? "stern" : "neutral") as Expr, blink: bl, light: LIGHT, seed: (i % 7) + 1 };
        add(`sol|${i % 4}|${JSON.stringify(opts, (_k, v) => (typeof v === "number" ? q(v) : v))}`, (p) => bodyFront(p, o, opts), STREET + x - 0.4, 0, zF - r * 1.3);
      }
      const sg = stand(OFFICER, 99, t > 49 ? "stern" : "neutral", { look: t > 47.3 ? -0.5 : 0 });
      add(sg.key, sg.draw, STREET + 2.0, 0.14, -38.6);
      const tap = t > 49.3 && t < 50.6 ? 0.03 * Math.sin((t - 49.3) * 20) : 0;
      FX.push({ key: "canteen", cw: 600, ch: 1000, draw: (p) => canteen(p), x: STREET + 2.36, y: 0.98 + tap + 0.14, z: -38.5, w: 0.2, h: 0.33 });
    }
    if (set === "cells") {
      const swell = swellAt(t), sweep = sweepAt(t);
      const cells: [number, number, number, number][] = [[-1.5, 0, 0.1, 0], [0.15, 0, -0.4, 1], [1.7, 0, 0.3, 2], [-0.7, 0, -2.3, 2], [1.1, 0, -2.5, 0], [-2.8, 0, -1.4, 1]];
      cells.forEach(([x, y, z, hue], i) => {
        const sw = q(swell * (0.85 + 0.15 * ((i * 7) % 3) / 2), 12);
        const expr: Expr = id === 8 ? (t < 28.1 ? "relief" : "nervous") : sw > 0.7 ? "shock" : sw > 0.3 ? "nervous" : "neutral";
        const bl = lid(40 + i);
        add(`cell|${sw}|${expr}|${bl}|${hue}`, (p) => cell(p, sw, expr, bl, hue), CELLS + x, y, z, 0.95 + 0.35 * sw);
      });
      // incoming water drops rush past from the left (20.0 - 24.6 s)
      if (t > 19.6 && t < 25) for (let i = 0; i < 9; i++) {
        const u2 = (t - 19.6 - i * 0.35) / 1.8;
        if (u2 < 0 || u2 > 1) continue;
        const ph = q((t * 2.4 + i * 0.3) % 1, 8);
        add(`drop|neutral|${ph}|0|${i % 3}`, (p) => drop(p, "neutral", ph, 0, (i % 3) / 2), CELLS - 5 + 7 * u2, 0, 1.2 - (i % 3) * 0.9, 0.55);
      }
      // salt guard swept away
      if (id === 7 && t < 23.5) {
        const k = clamp01(sweep / 1.4), bl = lid(5);
        add(`salt|0|${bl}|shock`, (p) => saltGuard(p, sweep > 0 ? "shock" : "stern", bl, 0), CELLS - 2.4 + 6 * k * k, 0.6 * Math.sin(Math.PI * k), 1.0, 0.75, { roll: -3.5 * k });
      }
      if (id === 7 && t > 24.6 && t < 25.6) FX.push({ key: `puff|${q(clamp01((t - 24.6) / 0.6), 10)}`, cw: 300, ch: 300, draw: (p) => fxPuff(p, clamp01((t - 24.6) / 0.6)), x: CELLS + 1.1, y: 2.4, z: 0.8, w: 0.9, h: 0.9 });
    }
    if (set === "skull") {
      const sq = brainAt(t), bl = lid(70), expr: Expr = sq > 0.6 ? "pained" : "nervous";
      add(`brain|${q(sq, 12)}|${expr}|${bl}`, (p) => brain(p, sq, expr, bl), SKULL, 0.14, 0.05, 0.95 + 0.42 * sq);
      if (sq > 0.5) for (const [x, y] of [[-0.95, 0.75], [0.95, 0.6], [0.2, 1.27]] as const)
        FX.push({ key: `creak|${q((t * 4) % 1, 6)}`, cw: 300, ch: 300, draw: (p) => fxCreak(p, (t * 4) % 1), x: SKULL + x, y, z: 0.62, w: 0.3, h: 0.3 });
    }
    if (set === "kitchen" && t > 34.0) FX.push({ key: `creak|${q((t * 4) % 1, 6)}`, cw: 300, ch: 300, draw: (p) => fxCreak(p, (t * 4) % 1), x: KITCHEN + 0.2, y: 1.12, z: 0.12, w: 0.12, h: 0.12 });

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
      e2.use(false); e2.mesh.visible = true;
      e2.mesh.position.set(p.x, p.y, p.z); e2.mesh.quaternion.copy(cam.quaternion); e2.mesh.scale.set(p.w, p.h, 1);
      fused.push(e2);
    }
    for (let i = fi; i < this.fxs.length; i++) this.fxs[i].mesh.visible = false;
    this.pool.flush();
    for (const a of used) a.bind();
    for (const e2 of fused) e2.bind();
    void bodySide; void TOTAL;
    return focus;
  }
}
