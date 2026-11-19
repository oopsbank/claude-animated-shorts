// The world of "What If Your Plane's Windscreen Blew Out?": a cartoon twin-jet airliner (rear engines, T-tail, generic
// livery, no logos) with its cockpit and cabin inside; the sky at 17,000 ft (cloud deck + streaming clouds); an airport
// runway; the hangar the night before; a hospital room; the bolt macro and the windscreen cutaway of the explanation.
// Sky, sun, two-tone shading and ink come from the bridge / beer-flood look.
import * as THREE from "three";
import { Batch, V, lam, boxGeo, quad, tri } from "./build";
import { ctex, rep, stoneHD, planksHD, cloudHD, grassHD, rng } from "./paint";
import { Pen } from "./toon";
import { LIGHTS, LOOK, LightPreset } from "./lights";
import { TONE, CHAR, twoTone, untone } from "./shade";
import { NOINK } from "./ink";
import { Pool, Actor, Fx, stage, PLANE_LOCAL } from "./cast";
import {
  FPS, SHOTS, ShotDef, V3, RF, NOSE, TAIL, WS, FLOOR, CAPT, FO, GROUND, WARD, EXP, CUT, MGR, PANE_C,
  profile, skin, camAt, planePose, paneOff, boltMark, smooth, clamp01, T_SHORT, T_FAIL, T_MM,
} from "./story";

type Mats = Record<string, THREE.Material>;
const D2R = Math.PI / 180;

// ---------------- textures ----------------
const LIV_W = 2048, LIV_H = 1024;
const zx = (z: number) => ((z - NOSE) / (TAIL - NOSE)) * LIV_W;        // texture x along the fuselage
const thy = (th: number) => (1 - (th + 180) / 360) * LIV_H;             // texture y around (canvas down)
/** generic livery: white top, a navy belly, a red cheatline, cabin windows, cockpit side windows, door outlines */
const liveryTex = () => ctex("livery", LIV_W, LIV_H, (g) => {
  g.fillStyle = "#f4f5f7"; g.fillRect(0, 0, LIV_W, LIV_H);
  for (const s of [-1, 1]) {
    const yb0 = thy(s * 104), yb1 = thy(s * 180);
    g.fillStyle = "#24345f"; g.fillRect(0, Math.min(yb0, yb1), LIV_W, Math.abs(yb1 - yb0));
    const yr0 = thy(s * 96), yr1 = thy(s * 102);
    g.fillStyle = "#c8323a"; g.fillRect(0, Math.min(yr0, yr1), LIV_W, Math.abs(yr1 - yr0));
    // cabin windows
    for (let z = -8.4; z < 7.6; z += 0.55) {
      const x0 = zx(z), x1 = zx(z + 0.3), y0 = thy(s * 72), y1 = thy(s * 82);
      g.fillStyle = "#2d3a52"; g.beginPath(); g.roundRect(Math.min(x0, x1), Math.min(y0, y1), Math.abs(x1 - x0), Math.abs(y1 - y0), 8); g.fill();
    }
    // cockpit side windows
    g.fillStyle = "#2d3a52";
    g.beginPath(); g.moveTo(zx(-12.35), thy(s * 58)); g.lineTo(zx(-11.25), thy(s * 60)); g.lineTo(zx(-11.25), thy(s * 80)); g.lineTo(zx(-12.35), thy(s * 76)); g.fill();
    // doors
    g.strokeStyle = "#a9b0bd"; g.lineWidth = 5;
    g.strokeRect(zx(-9.3), Math.min(thy(s * 52), thy(s * 100)), zx(-8.4) - zx(-9.3), Math.abs(thy(s * 100) - thy(s * 52)));
  }
  // panel lines
  g.strokeStyle = "rgba(120,130,150,.35)"; g.lineWidth = 3;
  for (let z = -10; z < 12; z += 2.5) { g.beginPath(); g.moveTo(zx(z), 0); g.lineTo(zx(z), LIV_H); g.stroke(); }
});
/** the inside lining: cream panels with window shades in the cabin, grey in the cockpit */
const liningTex = () => ctex("lining", LIV_W, LIV_H, (g) => {
  g.fillStyle = "#ebe5d6"; g.fillRect(0, 0, LIV_W, LIV_H);
  g.fillStyle = "#7c828c"; g.fillRect(0, 0, zx(-9.6), LIV_H);
  for (const s of [-1, 1]) for (let z = -8.4; z < 7.6; z += 0.55) {
    const x0 = zx(z), x1 = zx(z + 0.3), y0 = thy(s * 72), y1 = thy(s * 82);
    g.fillStyle = "#d4cbb6"; g.beginPath(); g.roundRect(Math.min(x0, x1) - 6, Math.min(y0, y1) - 6, Math.abs(x1 - x0) + 12, Math.abs(y1 - y0) + 12, 12); g.fill();
    g.fillStyle = "#9fd0f2"; g.beginPath(); g.roundRect(Math.min(x0, x1), Math.min(y0, y1), Math.abs(x1 - x0), Math.abs(y1 - y0), 9); g.fill();
  }
  for (const s of [-1, 1]) { // cockpit side windows from inside
    g.fillStyle = "#9fd0f2";
    g.beginPath(); g.moveTo(zx(-12.35), thy(s * 58)); g.lineTo(zx(-11.25), thy(s * 60)); g.lineTo(zx(-11.25), thy(s * 80)); g.lineTo(zx(-12.35), thy(s * 76)); g.fill();
  }
});
/** instrument panel face: dials and screens */
const panelTex = () => ctex("instPanel", 1024, 256, (g) => {
  g.fillStyle = "#2b2f38"; g.fillRect(0, 0, 1024, 256);
  const p = new Pen(g);
  for (const [cx, cy, r] of [[110, 90, 46], [220, 90, 46], [330, 90, 46], [110, 190, 36], [220, 190, 36], [330, 190, 36], [700, 90, 46], [810, 90, 46], [920, 90, 46], [700, 190, 36], [810, 190, 36], [920, 190, 36]]) {
    p.ell(cx, cy, r, r, "#151820", 4); p.ell(cx, cy, r - 8, r - 8, "#e9edf2", 0);
    p.stroke([[cx, cy], [cx + (r - 14) * Math.cos(cx * 0.03), cy - (r - 14) * Math.sin(cx * 0.05 + 1)]], 5, "#d9412f");
  }
  g.fillStyle = "#3c4250"; g.fillRect(430, 40, 160, 180);
  for (let i = 0; i < 6; i++) for (let k = 0; k < 4; k++) { g.fillStyle = (i + k) % 3 ? "#e8c45a" : "#6fd08a"; g.fillRect(450 + i * 24, 60 + k * 40, 12, 12); }
});
/** runway: asphalt with edge lines, a dashed centreline and threshold bars */
const runwayTex = () => ctex("runway", 256, 1024, (g, r) => {
  g.fillStyle = "#6c6f78"; g.fillRect(0, 0, 256, 1024);
  for (let i = 0; i < 900; i++) { g.fillStyle = `rgba(${r() < 0.5 ? "40,40,48" : "150,150,160"},${0.1 + r() * 0.12})`; g.fillRect(r() * 256, r() * 1024, 2 + r() * 4, 2 + r() * 4); }
  g.fillStyle = "#f2f2ee"; g.fillRect(10, 0, 8, 1024); g.fillRect(238, 0, 8, 1024);
  for (let y = 0; y < 1024; y += 256) g.fillRect(122, y + 40, 12, 150);
});
const concreteTex = () => stoneHD("hangarFloor", ["#a7a59f", "#9e9c96", "#aeaca6", "#999791"], "#8a8882");
/** the cloud deck far below: soft white heaps on blue-grey */
const deckTex = () => ctex("cloudDeck", 1024, 1024, (g, r) => {
  g.fillStyle = "#c9d8ee"; g.fillRect(0, 0, 1024, 1024);
  for (let i = 0; i < 260; i++) {
    const x = r() * 1024, y = r() * 1024, s = 30 + r() * 90;
    for (const [dx, dy] of [[0, 0], [1024, 0], [-1024, 0], [0, 1024], [0, -1024]]) {
      const gr = g.createRadialGradient(x + dx, y + dy, 0, x + dx, y + dy, s);
      gr.addColorStop(0, "rgba(255,255,255,0.95)"); gr.addColorStop(0.6, "rgba(246,248,252,0.7)"); gr.addColorStop(1, "rgba(246,248,252,0)");
      g.fillStyle = gr; g.fillRect(x + dx - s, y + dy - s, 2 * s, 2 * s);
    }
  }
});
const wardWallTex = () => ctex("wardWall", 512, 512, (g) => {
  g.fillStyle = "#cfe5dc"; g.fillRect(0, 0, 512, 512);
  g.fillStyle = "#b8d6c9"; g.fillRect(0, 330, 512, 182);
  g.fillStyle = "#9fc4b4"; g.fillRect(0, 322, 512, 10);
});
const windowTex = () => ctex("wardWin", 256, 320, (g) => {
  g.fillStyle = "#a9d4f5"; g.fillRect(0, 0, 256, 320);
  g.fillStyle = "rgba(255,255,255,.4)"; g.beginPath(); g.moveTo(30, 320); g.lineTo(120, 0); g.lineTo(160, 0); g.lineTo(70, 320); g.fill();
  g.strokeStyle = "#f4f4f0"; g.lineWidth = 16; g.strokeRect(8, 8, 240, 304); g.lineWidth = 9;
  g.beginPath(); g.moveTo(128, 0); g.lineTo(128, 320); g.stroke();
});
const cardTex = () => ctex("getWell", 128, 160, (g) => {
  const p = new Pen(g);
  g.fillStyle = "#fff6e0"; g.fillRect(0, 0, 128, 160);
  p.poly([[64, 120], [24, 76], [34, 46], [64, 60], [94, 46], [104, 76]], "#e5545f", 5); // a heart
});

// ---------------- geometry ----------------
/** convex prism: polygon in x-z (y0..y1) */
const prismXZ = (pts: [number, number][], y0: number, y1: number) => {
  const parts: THREE.BufferGeometry[] = [];
  const n = pts.length;
  for (let i = 1; i < n - 1; i++) {
    parts.push(tri(V(pts[0][0], y1, pts[0][1]), V(pts[i + 1][0], y1, pts[i + 1][1]), V(pts[i][0], y1, pts[i][1])));
    parts.push(tri(V(pts[0][0], y0, pts[0][1]), V(pts[i][0], y0, pts[i][1]), V(pts[i + 1][0], y0, pts[i + 1][1])));
  }
  for (let i = 0; i < n; i++) {
    const [ax, az] = pts[i], [bx, bz] = pts[(i + 1) % n];
    parts.push(quad(V(ax, y0, az), V(bx, y0, bz), V(bx, y1, bz), V(ax, y1, az)));
  }
  return parts;
};
/** convex prism: polygon in z-y (x0..x1) */
const prismZY = (pts: [number, number][], x0: number, x1: number) => {
  const parts: THREE.BufferGeometry[] = [];
  const n = pts.length;
  for (let i = 1; i < n - 1; i++) {
    parts.push(tri(V(x1, pts[0][1], pts[0][0]), V(x1, pts[i][1], pts[i][0]), V(x1, pts[i + 1][1], pts[i + 1][0])));
    parts.push(tri(V(x0, pts[0][1], pts[0][0]), V(x0, pts[i + 1][1], pts[i + 1][0]), V(x0, pts[i][1], pts[i][0])));
  }
  for (let i = 0; i < n; i++) {
    const [az, ay] = pts[i], [bz, by] = pts[(i + 1) % n];
    parts.push(quad(V(x0, ay, az), V(x0, by, bz), V(x1, by, bz), V(x1, ay, az)));
  }
  return parts;
};
/** z samples along the fuselage: fine at the nose (with the windscreen edges exact) and the tail */
const ZS = (() => {
  const z: number[] = [];
  for (let v = NOSE; v < WS.z0 - 0.01; v += 0.2) z.push(v);
  for (let k = 0; k <= 4; k++) z.push(WS.z0 + ((WS.z1 - WS.z0) * k) / 4);
  for (let v = WS.z1 + 0.25; v < -10; v += 0.25) z.push(v);
  for (let v = -10; v < 8.5; v += 0.5) z.push(v);
  for (let v = 8.5; v <= TAIL + 1e-6; v += 0.25) z.push(v);
  return z;
})();
const NT = 72; // 5 degree cells
const inPane = (th0: number, th1: number, z0: number, z1: number, side: number) => {
  const a = Math.min(th0, th1) * side, b = Math.max(th0, th1) * side, lo = Math.min(a, b), hi = Math.max(a, b);
  return z0 >= WS.z0 - 1e-6 && z1 <= WS.z1 + 1e-6 && lo >= WS.th0 - 1e-6 && hi <= WS.th1 + 1e-6;
};
/** the fuselage skin (dr = 0) or lining (dr < 0) as a parametric surface; holes where `keep` says no */
const fuselageGeo = (dr: number, keep: (th0: number, th1: number, z0: number, z1: number) => boolean, flip = false) => {
  const pos: number[] = [], uv: number[] = [];
  for (let j = 0; j < ZS.length - 1; j++) for (let i = 0; i < NT; i++) {
    const t0 = -180 + (i * 360) / NT, t1 = t0 + 360 / NT, z0 = ZS[j], z1 = ZS[j + 1];
    if (!keep(t0, t1, z0, z1)) continue;
    const a = skin(t0, z0, dr), b = skin(t1, z0, dr), c = skin(t1, z1, dr), d = skin(t0, z1, dr);
    const ua = [(z0 - NOSE) / (TAIL - NOSE), (t0 + 180) / 360], ub = [(z0 - NOSE) / (TAIL - NOSE), (t1 + 180) / 360];
    const uc = [(z1 - NOSE) / (TAIL - NOSE), (t1 + 180) / 360], ud = [(z1 - NOSE) / (TAIL - NOSE), (t0 + 180) / 360];
    const tris = flip ? [a, c, b, a, d, c] : [a, b, c, a, c, d], uvs = flip ? [ua, uc, ub, ua, ud, uc] : [ua, ub, uc, ua, uc, ud];
    for (const p of tris) pos.push(...p);
    for (const u of uvs) uv.push(...u);
  }
  const g = new THREE.BufferGeometry();
  g.setAttribute("position", new THREE.Float32BufferAttribute(pos, 3));
  g.setAttribute("uv", new THREE.Float32BufferAttribute(uv, 2));
  g.computeVertexNormals();
  return g;
};
/** a bolt standing on its head: hex head, shank with thread rings */
const boltGeo = (r: number, L: number, headR: number, headH: number) => {
  const parts: THREE.BufferGeometry[] = [];
  const head = new THREE.CylinderGeometry(headR, headR, headH, 6); head.translate(0, headH / 2, 0); parts.push(head);
  const shank = new THREE.CylinderGeometry(r, r, L, 32); shank.translate(0, headH + L / 2, 0); parts.push(shank);
  for (let k = 0; k < Math.floor((L * 0.85) / (r * 0.45)); k++) {
    const ring = new THREE.TorusGeometry(r, r * 0.08, 6, 32); ring.rotateX(Math.PI / 2); ring.translate(0, headH + L - r * 0.3 - k * r * 0.45, 0); parts.push(ring);
  }
  return parts;
};

type Cloud = { m: THREE.Mesh; x: number; y: number; z: number; w: number };

export class World {
  root = new THREE.Group();
  private pool = new Pool();
  private actors: Actor[] = [];
  private fxs: Fx[] = [];
  private plane = new THREE.Group();
  private planeIn = new THREE.Group();   // cockpit + cabin interior
  private gear = new THREE.Group();
  private skinMesh!: THREE.Mesh; private lining!: THREE.Mesh;
  private paneL = new THREE.Group(); private paneR!: THREE.Mesh;
  private bolts!: THREE.InstancedMesh; private boltPts: { p: THREE.Vector3; n: THREE.Vector3 }[] = [];
  private flightEnv = new THREE.Group(); private deck!: THREE.Mesh; private deckMap!: THREE.Texture; private puffs: Cloud[] = [];
  private airport = new THREE.Group();
  private hangar = new THREE.Group();
  private ward = new THREE.Group();
  private exp = new THREE.Group(); private expShort!: THREE.Group;
  private cut = new THREE.Group(); private cutPane = new THREE.Group(); private cutBolts: THREE.Group[] = [];
  private hemi: THREE.HemisphereLight; private sun: THREE.DirectionalLight;
  private sky: THREE.Mesh; private skyMat: THREE.ShaderMaterial;
  private fog = new THREE.Fog("#bccbec", 25, 420);
  private sunCache = new Map<number, THREE.Vector3>();
  private cloudMaps: Record<"day" | "golden", THREE.Texture[]>;
  private clouds: THREE.Mesh[] = [];
  private frustum = new THREE.Frustum();
  private m4 = new THREE.Matrix4(); private v = new THREE.Vector3(); private sph = new THREE.Sphere();
  private pm = new THREE.Matrix4();

  constructor() {
    const R = this.root, M: Mats = {};
    R.add(this.plane, this.flightEnv, this.airport, this.hangar, this.ward, this.exp, this.cut);
    this.plane.add(this.planeIn, this.gear);
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
    M.livery = lam("livery", () => ({ map: liveryTex() }));
    M.lining = new THREE.MeshLambertMaterial({ map: liningTex(), side: THREE.BackSide }); twoTone(M.lining as THREE.MeshLambertMaterial);
    M.navy = lam("navyPaint", () => ({ color: "#24345f" }));
    M.white = lam("whitePaint", () => ({ color: "#f1f2f4" }));
    M.grey = lam("greyMetal", () => ({ color: "#9aa1ab" }));
    M.dark = lam("darkMetal", () => ({ color: "#2f333c" }));
    M.black = lam("rubber", () => ({ color: "#1d1e22" }));
    M.inst = lam("instPanel", () => ({ map: panelTex() }));
    M.cockpit = lam("cockpitGrey", () => ({ color: "#6d737d" }));
    M.seatC = lam("cockpitSeat", () => ({ color: "#3b4150" }));
    M.seat = lam("cabinSeat", () => ({ color: "#2f5d9e" }));
    M.seatHead = lam("seatHead", () => ({ color: "#e9e4d6" }));
    M.carpet = lam("carpet", () => ({ color: "#5a4a6a" }));
    M.bins = lam("bins", () => ({ color: "#f0ebde" }));
    M.grass = lam("grassHD", () => ({ map: rep(grassHD(), 60, 60), color: "#b9c99a" }));
    M.runway = lam("runway", () => ({ map: rep(runwayTex(), 1, 18) }));
    M.building = lam("terminal", () => ({ color: "#d8d4ca" }));
    M.glassB = lam("termGlass", () => ({ color: "#5b7fa8" }));
    M.concrete = lam("hangarFloor", () => ({ map: rep(concreteTex(), 8, 8) }));
    M.hangarWall = lam("hangarWall", () => ({ color: "#7d8a99" }));
    M.truss = lam("truss", () => ({ color: "#4b5260" }));
    M.yellow = lam("safetyYellow", () => ({ color: "#e8b830" }));
    M.wardWall = lam("wardWall", () => ({ map: wardWallTex() }));
    M.wardFloor = lam("wardFloor", () => ({ color: "#d9cfbd" }));
    M.sheet = lam("sheet", () => ({ color: "#f7f7f4" }));
    M.blanket = lam("blanket", () => ({ color: "#9cc3e6" }));
    M.bedFrame = lam("bedFrame", () => ({ color: "#c7ccd4" }));
    M.wood = lam("woodWard", () => ({ map: rep(planksHD(), 0.3, 0.3) }));
    M.flower = lam("flowers", () => ({ color: "#e65a6a" }));
    M.leaf = lam("leaves", () => ({ color: "#4f9a50" }));
    M.studio = lam("studio", () => ({ color: "#283149" }));
    M.studioFloor = lam("studioFloor", () => ({ color: "#3a4560" }));
    M.steel = twoTone(new THREE.MeshPhongMaterial({ color: "#c3c8d0", specular: "#ffffff", shininess: 70 }), 0.2);
    M.steelThin = twoTone(new THREE.MeshPhongMaterial({ color: "#c3c8d0", specular: "#ffffff", shininess: 70 }), 0.2);
    M.frame = lam("frameMetal", () => ({ color: "#8e96a3" }));
    M.nut = lam("anchorNut", () => ({ color: "#b48a3a" }));
    M.cabinSide = lam("cabinSide", () => ({ color: "#efe3c8" }));
    M.skySide = lam("skySide", () => ({ color: "#8fc0ec" }));
    const glass = new THREE.MeshLambertMaterial({ color: "#bfe0f6", transparent: true, opacity: 0.32, depthWrite: false, side: THREE.DoubleSide });
    const glassCut = lam("glassCut", () => ({ color: "#a6d3f0" }));
    const lampM = new THREE.MeshBasicMaterial({ color: new THREE.Color(3.2, 2.6, 1.7) });

    // ---- the plane ----
    const isWin = (t0: number, t1: number, z0: number, z1: number) => inPane(t0, t1, z0, z1, -1) || inPane(t0, t1, z0, z1, 1);
    this.skinMesh = new THREE.Mesh(fuselageGeo(0, (a, b, c, d) => !isWin(a, b, c, d), true), M.livery);
    this.skinMesh.castShadow = true; this.skinMesh.receiveShadow = true;
    this.plane.add(this.skinMesh);
    this.lining = new THREE.Mesh(fuselageGeo(-0.06, (a, b, c, d) => !isWin(a, b, c, d), true), M.lining);
    this.lining.receiveShadow = true; this.lining.castShadow = false; this.lining.layers.set(NOINK);
    this.planeIn.add(this.lining);
    // windscreen panes: the left one in its own group (it leaves); a frame strip of bolts round its edge
    const paneGeo = (side: number) => fuselageGeo(0.005, (a, b, c, d) => inPane(a, b, c, d, side), true);
    const pl = new THREE.Mesh(paneGeo(-1), glass); pl.position.set(-PANE_C[0], -PANE_C[1], -PANE_C[2]);
    this.paneL.add(pl); this.paneL.position.set(...PANE_C); this.plane.add(this.paneL);
    this.paneR = new THREE.Mesh(paneGeo(1), glass); this.plane.add(this.paneR);
    // the windscreen frame: dark strips round both panes
    const fb = new Batch();
    for (const side of [-1, 1]) {
      for (const z of [WS.z0, WS.z1]) for (let th = WS.th0; th < WS.th1; th += 5) {
        const a = skin(side * th, z, 0.01), b = skin(side * (th + 5), z, 0.01), a2 = skin(side * th, z + (z === WS.z0 ? -0.06 : 0.06), 0.01), b2 = skin(side * (th + 5), z + (z === WS.z0 ? -0.06 : 0.06), 0.01);
        fb.add(quad(V(...a), V(...b), V(...b2), V(...a2)), M.dark);
        fb.add(quad(V(...a), V(...a2), V(...b2), V(...b)), M.dark);
      }
      for (const th of [WS.th0, WS.th1]) for (let k = 0; k < 4; k++) {
        const z0 = WS.z0 + ((WS.z1 - WS.z0) * k) / 4, z1 = WS.z0 + ((WS.z1 - WS.z0) * (k + 1)) / 4, d = th === WS.th0 ? -3 : 3;
        const a = skin(side * th, z0, 0.01), b = skin(side * th, z1, 0.01), a2 = skin(side * (th + d), z0, 0.01), b2 = skin(side * (th + d), z1, 0.01);
        fb.add(quad(V(...a), V(...b), V(...b2), V(...a2)), M.dark);
        fb.add(quad(V(...a), V(...a2), V(...b2), V(...b)), M.dark);
      }
    }
    fb.build(this.plane);
    // the 90 bolts round the captain's pane (hex heads on the skin)
    const per: { p: THREE.Vector3; n: THREE.Vector3 }[] = [];
    const ptAt = (th: number, z: number) => {
      const p = V(...skin(th, z, 0.012)), q = V(...skin(th, z, 0.2));
      return { p, n: q.sub(p).normalize() };
    };
    const edges: [number, number, number, number][] = [[-WS.th0, WS.z0 + 0.04, -WS.th1, WS.z0 + 0.04], [-WS.th1 + 1.5, WS.z0, -WS.th1 + 1.5, WS.z1], [-WS.th1, WS.z1 - 0.04, -WS.th0, WS.z1 - 0.04], [-WS.th0 - 1.5, WS.z1, -WS.th0 - 1.5, WS.z0]];
    const counts = [28, 17, 28, 17];
    edges.forEach(([ta, za, tb, zb], e) => { for (let k = 0; k < counts[e]; k++) { const u = (k + 0.5) / counts[e]; per.push(ptAt(ta + (tb - ta) * u, za + (zb - za) * u)); } });
    this.boltPts = per;
    const hex = new THREE.CylinderGeometry(0.03, 0.03, 0.018, 6);
    this.bolts = new THREE.InstancedMesh(hex, lam("boltHead", () => ({ color: "#ffffff" })), per.length);
    this.bolts.frustumCulled = false;
    const up = V(0, 1, 0), qq = new THREE.Quaternion(), mm = new THREE.Matrix4();
    per.forEach(({ p, n }, i) => { qq.setFromUnitVectors(up, n); this.bolts.setMatrixAt(i, mm.compose(p, qq, V(1, 1, 1))); this.bolts.setColorAt(i, new THREE.Color("#c8ccd4")); });
    this.plane.add(this.bolts);

    const pb = new Batch();
    // wings (low, swept), tailplane on top of the fin (T-tail), fin
    for (const s of [-1, 1]) {
      for (const g of prismXZ([[s * 1.2, -2.6], [s * 14, 3.3], [s * 14, 4.8], [s * 1.2, 3.2]].map(([x, z]) => [x, z]) as [number, number][], -1.18, -0.92)) pb.add(g, M.white);
      for (const g of prismXZ([[s * 0.1, 11.9], [s * 4.8, 13.7], [s * 4.8, 14.7], [s * 0.1, 14.3]] as [number, number][], 6.05, 6.25)) pb.add(g, M.white);
      // engines on the rear fuselage
      const nac = new THREE.CylinderGeometry(0.74, 0.66, 4.4, 28); nac.rotateX(Math.PI / 2); nac.translate(s * 2.55, 0.55, 8.6);
      pb.add(nac, M.white);
      const lip = new THREE.TorusGeometry(0.72, 0.06, 8, 28); lip.translate(s * 2.55, 0.55, 6.42); pb.add(lip, M.grey);
      const intake = new THREE.CircleGeometry(0.68, 28); intake.rotateY(Math.PI); intake.translate(s * 2.55, 0.55, 6.5); pb.add(intake, M.black);
      const ex = new THREE.CircleGeometry(0.6, 28); ex.translate(s * 2.55, 0.55, 10.78); pb.add(ex, M.black);
      pb.add(boxGeo(V(Math.min(s * 1.2, s * 1.95), 0.35, 7.6), V(Math.max(s * 1.2, s * 1.95), 0.75, 9.6)), M.white);
    }
    for (const g of prismZY([[9.6, 1.1], [14.3, 1.1], [14.8, 6.25], [12.4, 6.25]], -0.13, 0.13)) pb.add(g, M.navy);
    pb.build(this.plane);
    // landing gear
    const gb = new Batch();
    const wheel = (x: number, z: number, r: number) => { const w = new THREE.CylinderGeometry(r, r, 0.3, 20); w.rotateZ(Math.PI / 2); w.translate(x, GROUND + r, z); gb.add(w, M.black); };
    gb.add(boxGeo(V(-0.06, GROUND + 0.3, -11.0), V(0.06, -1.1, -10.85)), M.grey); wheel(-0.17, -10.92, 0.3); wheel(0.17, -10.92, 0.3);
    for (const s of [-1, 1]) { gb.add(boxGeo(V(s * 2.3 - 0.08, GROUND + 0.4, 1.7), V(s * 2.3 + 0.08, -1.0, 1.9)), M.grey); wheel(s * 2.3 - 0.2, 1.8, 0.4); wheel(s * 2.3 + 0.2, 1.8, 0.4); }
    gb.build(this.gear);

    // ---- cockpit + cabin interior ----
    const ib = new Batch();
    ib.add(boxGeo(V(-1.3, FLOOR - 0.1, -13.3), V(1.3, FLOOR, 9.5)), M.carpet);
    // instrument panel, glareshield, pedestal, overhead
    ib.add(boxGeo(V(-0.98, FLOOR, -13.05), V(0.98, 0.18, -12.62)), M.cockpit);
    ib.add(quad(V(-0.98, FLOOR + 0.35, -12.615), V(0.98, FLOOR + 0.35, -12.615), V(0.98, 0.15, -12.615), V(-0.98, 0.15, -12.615)), M.inst);
    ib.add(boxGeo(V(-1.0, 0.18, -13.1), V(1.0, 0.3, -12.55)), M.dark);
    ib.add(boxGeo(V(-0.17, FLOOR, -12.62), V(0.17, -0.2, -11.3)), M.cockpit);
    ib.add(boxGeo(V(-0.6, 1.22, -12.4), V(0.6, 1.36, -10.6)), M.cockpit);
    for (const [x, z] of [[CAPT[0], CAPT[2]], [FO[0], FO[2]]]) {
      ib.add(boxGeo(V(x - 0.27, FLOOR, z - 0.25), V(x + 0.27, FLOOR + 0.42, z + 0.28)), M.seatC);
      ib.add(boxGeo(V(x - 0.27, FLOOR + 0.42, z + 0.28), V(x + 0.27, FLOOR + 0.98, z + 0.42)), M.seatC);
      // control column and horned wheel
      ib.add(boxGeo(V(x - 0.04, FLOOR, -12.3), V(x + 0.04, -0.2, -12.22)), M.dark);
      ib.add(boxGeo(V(x - 0.19, -0.22, -12.3), V(x + 0.19, -0.14, -12.2)), M.dark);
      for (const s of [-1, 1]) ib.add(boxGeo(V(x + s * 0.19 - 0.03, -0.22, -12.3), V(x + s * 0.19 + 0.03, -0.02, -12.2)), M.dark);
    }
    // the bulkhead with its door, then the cabin: seats 3 + 2, overhead bins
    const bh = new THREE.Shape(); bh.absarc(0, 0, RF - 0.07, 0, Math.PI * 2, false);
    const door = new THREE.Path(); door.moveTo(-0.38, FLOOR); door.lineTo(0.38, FLOOR); door.lineTo(0.38, 1.15); door.lineTo(-0.38, 1.15); door.lineTo(-0.38, FLOOR); bh.holes.push(door);
    const bhg = new THREE.ShapeGeometry(bh, 48); bhg.translate(0, 0, -9.6);
    const bhMesh = new THREE.Mesh(bhg, new THREE.MeshLambertMaterial({ color: "#d9d2c2", side: THREE.DoubleSide })); twoTone(bhMesh.material as THREE.MeshLambertMaterial);
    bhMesh.receiveShadow = true; this.planeIn.add(bhMesh);
    const xs = [-1.2, -0.76, -0.32, 0.6, 1.04];
    for (let row = 0; row < 19; row++) {
      const z = -6.9 + row * 0.82;
      for (const x of xs) {
        ib.add(boxGeo(V(x - 0.2, FLOOR, z - 0.18), V(x + 0.2, FLOOR + 0.42, z + 0.22)), M.seat);
        ib.add(boxGeo(V(x - 0.2, FLOOR + 0.42, z + 0.22), V(x + 0.2, FLOOR + 1.15, z + 0.32)), M.seat);
        ib.add(boxGeo(V(x - 0.17, FLOOR + 1.02, z + 0.18), V(x + 0.17, FLOOR + 1.15, z + 0.22)), M.seatHead);
      }
    }
    for (const s of [-1, 1]) ib.add(boxGeo(V(s > 0 ? 0.75 : -1.45, 1.0, -8.6), V(s > 0 ? 1.45 : -0.75, 1.3, 9.0)), M.bins);
    ib.build(this.planeIn);

    // ---- flight: cloud deck far below, clouds streaming past ----
    this.deckMap = deckTex(); this.deckMap.wrapS = this.deckMap.wrapT = THREE.RepeatWrapping; this.deckMap.repeat.set(6, 6);
    this.deck = new THREE.Mesh(new THREE.PlaneGeometry(3000, 3000), new THREE.MeshBasicMaterial({ map: this.deckMap, fog: false }));
    this.deck.rotation.x = -Math.PI / 2; this.deck.position.y = -140; this.deck.layers.set(NOINK); this.flightEnv.add(this.deck);
    const rc = rng(17);
    for (let i = 0; i < 26; i++) {
      const m = new THREE.Mesh(new THREE.PlaneGeometry(1, 1), new THREE.MeshBasicMaterial({ map: this.cloudMaps.day[i % 4], transparent: true, depthWrite: false, fog: false, color: new THREE.Color(1.08, 1.08, 1.08) }));
      m.layers.set(NOINK); this.flightEnv.add(m);
      let x = (rc() - 0.5) * 360, y = -90 + rc() * 110;
      if (Math.abs(x) < 40 && y > -30) y -= 50; // keep the plane's tube clear
      this.puffs.push({ m, x, y, z: -500 + rc() * 900, w: 40 + rc() * 70 });
    }

    // ---- the airport ----
    const ab = new Batch();
    ab.add(quadUp(-1500, 1500, -2500, 1200, 1, 1, GROUND - 0.03), M.grass);
    ab.add(quadUp(-22, 22, -2400, 900, 1, 1, GROUND), M.runway);
    for (let z = -2000; z < 800; z += 120) ab.add(boxGeo(V(70, GROUND, z), V(118, GROUND + 9 + (z % 3) * 2, z + 90), 0), M.building);
    for (let z = -2000; z < 800; z += 120) ab.add(boxGeo(V(69.8, GROUND + 3, z + 8), V(70, GROUND + 7, z + 82)), M.glassB);
    ab.add(new THREE.CylinderGeometry(2.4, 3, 26, 16), M.building, new THREE.Matrix4().makeTranslation(60, GROUND + 13, -260));
    ab.add(boxGeo(V(55, GROUND + 26, -265), V(65, GROUND + 31, -255)), M.glassB);
    ab.add(boxGeo(V(54.5, GROUND + 31, -265.5), V(65.5, GROUND + 32, -254.5)), M.building);
    ab.build(this.airport);
    const trees = new THREE.InstancedMesh(new THREE.SphereGeometry(3.2, 10, 8), lam("treeLeaf", () => ({ color: "#5c9a4a" })), 140);
    const rt = rng(5);
    for (let i = 0; i < 140; i++) {
      const z = -2200 + i * 22 + rt() * 10, x = -90 - rt() * 160, s = 0.8 + rt() * 0.8;
      trees.setMatrixAt(i, new THREE.Matrix4().compose(V(x, GROUND + 2.6 * s, z), new THREE.Quaternion(), V(s, s * 1.1, s)));
    }
    trees.castShadow = true; trees.receiveShadow = true; this.airport.add(trees);

    // ---- the hangar (night): walls and roof cast no shadow, so the "sun" works as the work lamps ----
    const hb = new Batch();
    hb.add(quadUp(-30, 30, -34, 30, 1, 1, GROUND), M.concrete);
    hb.add(boxGeo(V(-30, GROUND, -34), V(-29.4, GROUND + 16, 30)), M.hangarWall);
    hb.add(boxGeo(V(29.4, GROUND, -34), V(30, GROUND + 16, 30)), M.hangarWall);
    hb.add(boxGeo(V(-30, GROUND, 29.4), V(30, GROUND + 16, 30)), M.hangarWall);
    hb.add(boxGeo(V(-30, GROUND, -34), V(30, GROUND + 16, -33.4)), M.hangarWall);
    hb.add(boxGeo(V(-30, GROUND + 16, -34), V(30, GROUND + 16.4, 30), 0, true), M.hangarWall);
    for (let z = -30; z < 30; z += 6) hb.add(boxGeo(V(-29.4, GROUND + 14.6, z - 0.2), V(29.4, GROUND + 15.2, z + 0.2)), M.truss);
    // yellow floor lines, a tool chest, the manager's platform at the nose
    hb.add(quadUp(-6, -5.8, -30, 26, 1, 1, GROUND + 0.01), M.yellow); hb.add(quadUp(5.8, 6, -30, 26, 1, 1, GROUND + 0.01), M.yellow);
    hb.add(boxGeo(V(-12, GROUND, -20), V(-10.6, GROUND + 1.2, -18.8)), lam("toolChest", () => ({ color: "#c8323a" })));
    const [mx, my, mz] = MGR;
    hb.add(boxGeo(V(mx - 0.7, my - 0.08, mz - 0.6), V(mx + 0.7, my, mz + 0.6)), M.yellow);
    for (const [dx, dz] of [[-0.65, -0.55], [0.65, -0.55], [-0.65, 0.55], [0.65, 0.55]]) hb.add(boxGeo(V(mx + dx - 0.04, GROUND, mz + dz - 0.04), V(mx + dx + 0.04, my - 0.08, mz + dz + 0.04)), M.truss);
    hb.add(boxGeo(V(mx - 0.7, my, mz - 0.62), V(mx - 0.66, my + 1.0, mz + 0.62)), M.yellow);
        hb.build(this.hangar, false);
    for (const [x, z] of [[-6, -14], [6, -14], [-6, 0], [6, 0], [-6, 14], [6, 14]]) {
      const lamp = new THREE.Mesh(new THREE.BoxGeometry(2.4, 0.2, 0.6), lampM); lamp.position.set(x, GROUND + 13.5, z); lamp.layers.set(NOINK); this.hangar.add(lamp);
    }
    // a bolt carousel on a trolley by the platform
    const cb = new Batch();
    cb.add(boxGeo(V(mx - 1.8, GROUND, mz - 2.0), V(mx - 1.0, GROUND + 0.9, mz - 1.4)), M.grey);
    for (let k = 0; k < 6; k++) cb.add(new THREE.CylinderGeometry(0.06, 0.06, 0.08, 10), M.yellow, new THREE.Matrix4().makeTranslation(mx - 1.7 + k * 0.12, GROUND + 0.94, mz - 1.7));
    cb.build(this.hangar, false);

    // ---- the ward ----
    const wb = new Batch(), [wx, wy, wz] = WARD;
    wb.add(quadUp(wx - 4, wx + 4, wz - 3, wz + 5, 1, 1, wy), M.wardFloor);
    wb.add(quad(V(wx - 4, wy, wz - 3), V(wx + 4, wy, wz - 3), V(wx + 4, wy + 3.2, wz - 3), V(wx - 4, wy + 3.2, wz - 3), 3, 1), M.wardWall);
    wb.add(quad(V(wx - 4, wy, wz + 5), V(wx - 4, wy, wz - 3), V(wx - 4, wy + 3.2, wz - 3), V(wx - 4, wy + 3.2, wz + 5), 3, 1), M.wardWall);
    wb.add(quad(V(wx + 4, wy, wz - 3), V(wx + 4, wy, wz + 5), V(wx + 4, wy + 3.2, wz + 5), V(wx + 4, wy + 3.2, wz - 3), 3, 1), M.wardWall);
    // the bed: frame, mattress, pillow, a blanket over his legs
    wb.add(boxGeo(V(wx - 0.55, wy, wz - 1.2), V(wx + 0.55, wy + 0.5, wz + 1.0)), M.bedFrame);
    wb.add(boxGeo(V(wx - 0.5, wy + 0.5, wz - 1.15), V(wx + 0.5, wy + 0.66, wz + 0.95)), M.sheet);
    wb.add(boxGeo(V(wx - 0.55, wy + 0.5, wz - 1.25), V(wx + 0.55, wy + 1.15, wz - 1.15)), M.bedFrame);
    wb.add(boxGeo(V(wx - 0.38, wy + 0.66, wz - 1.1), V(wx + 0.38, wy + 0.9, wz - 0.7)), M.sheet);
    wb.add(boxGeo(V(wx - 0.52, wy + 0.62, wz - 0.02), V(wx + 0.52, wy + 0.78, wz + 0.98)), M.blanket);
    wb.add(boxGeo(V(wx + 0.8, wy, wz - 1.0), V(wx + 1.3, wy + 0.65, wz - 0.5)), M.wood);
    wb.add(new THREE.CylinderGeometry(0.08, 0.07, 0.22, 12), M.sheet, new THREE.Matrix4().makeTranslation(wx + 1.05, wy + 0.76, wz - 0.75));
    for (let k = 0; k < 5; k++) wb.add(new THREE.SphereGeometry(0.06, 8, 6), M.flower, new THREE.Matrix4().makeTranslation(wx + 1.05 + 0.07 * Math.cos(k * 1.3), wy + 0.95 + 0.04 * (k % 2), wz - 0.75 + 0.07 * Math.sin(k * 1.3)));
    wb.build(this.ward);
    const win = new THREE.Mesh(new THREE.PlaneGeometry(1.3, 1.6), new THREE.MeshBasicMaterial({ map: windowTex(), color: 0xeeeeee }));
    win.position.set(wx - 1.6, wy + 1.75, wz - 2.98); win.layers.set(NOINK); this.ward.add(win);
    const gw = new THREE.Mesh(new THREE.PlaneGeometry(0.16, 0.2), new THREE.MeshBasicMaterial({ map: cardTex(), color: 0xeeeeee }));
    gw.position.set(wx + 1.18, wy + 0.76, wz - 0.82); gw.rotation.y = -0.3; gw.layers.set(NOINK); this.ward.add(gw);

    // ---- the bolt macro: right, thin, short on a studio floor ----
    const eb = new Batch(), [ex, ey, ez] = EXP;
    eb.add(new THREE.CircleGeometry(9, 48).rotateX(-Math.PI / 2).translate(ex, ey, ez), M.studioFloor);
    const back = new THREE.CylinderGeometry(9, 9, 8, 48, 1, true, Math.PI * 0.5, Math.PI); back.translate(ex, ey + 4, ez);
    eb.add(back, M.studio);
    const B0 = boltGeo(0.32, 1.7, 0.56, 0.3), B1 = boltGeo(0.32 * 0.86, 1.7, 0.56, 0.3);
    for (const g of B0) eb.add(g, M.steel, new THREE.Matrix4().makeTranslation(ex - 0.75, ey, ez));
    for (const g of B1) eb.add(g, M.steelThin, new THREE.Matrix4().makeTranslation(ex + 0.75, ey, ez));
    eb.build(this.exp);
    this.expShort = new THREE.Group(); this.exp.add(this.expShort);
    const sb = new Batch();
    for (const g of boltGeo(0.32 * 0.86, 1.7 * 0.8, 0.56, 0.3)) sb.add(g, M.steelThin);
    sb.build(this.expShort);
    this.expShort.position.set(ex + 2.25, ey, ez);

    // ---- the cutaway: frame (inside, x < 0), the pane outside it (x > 0), bolts through both ----
    const kb = new Batch(), [cx, cy, cz] = CUT;
    kb.add(quad(V(cx - 14, cy - 8, cz - 3), V(cx, cy - 8, cz - 3), V(cx, cy + 8, cz - 3), V(cx - 14, cy + 8, cz - 3)), M.cabinSide);
    kb.add(quad(V(cx, cy - 8, cz - 3), V(cx + 14, cy - 8, cz - 3), V(cx + 14, cy + 8, cz - 3), V(cx, cy + 8, cz - 3)), M.skySide);
    for (const s of [-1, 1]) {
      kb.add(boxGeo(V(cx - 0.75, cy + s * 1.9 - (s < 0 ? 4 : 0), cz - 2), V(cx, cy + s * 1.9 + (s > 0 ? 4 : 0), cz), 0, true), M.frame);
      // the anchor nut the bolt should bite into: two jaws with a gap (thin bolt: daylight round the shank)
      const by = cy + s * 2.5;
      kb.add(boxGeo(V(cx - 0.72, by + 0.25, cz - 0.3), V(cx - 0.32, by + 0.42, cz + 0.02)), M.nut);
      kb.add(boxGeo(V(cx - 0.72, by - 0.42, cz - 0.3), V(cx - 0.32, by - 0.25, cz + 0.02)), M.nut);
    }
    kb.build(this.cut);
    this.cut.add(this.cutPane);
    const pg = boxGeo(V(0, -2.95, -2), V(0.55, 2.95, 0), 0, true);
    const pm = new THREE.Mesh(pg, glassCut); pm.castShadow = true; pm.receiveShadow = true; this.cutPane.add(pm);
    this.cutPane.position.set(cx, cy, cz);
    for (const s of [-1, 1]) {
      const g = new THREE.Group(), bb = new Batch();
      for (const p of boltGeo(0.19, 1.3, 0.34, 0.18)) bb.add(p, M.steelThin);
      bb.build(g);
      g.rotation.z = Math.PI / 2; // shank toward -x (into the frame), head outside the pane
      g.userData.base = V(cx + 0.55 + 0.18, cy + s * 2.5, cz - 0.15);
      g.position.copy(g.userData.base);
      this.cut.add(g); this.cutBolts.push(g);
    }
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
    const SUN_SHOT: Record<number, { az?: number; el?: number }> = { 16: { az: 175, el: 55 }, 15: { az: 150, el: 60 }, 18: { az: 120, el: 55 }, 21: { az: 160, el: 60 }, 13: { az: 110, el: 40 } };
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
    // the plane's pose
    const pose = planePose(id, t);
    this.plane.position.set(...pose.pos);
    this.plane.rotation.set(pose.pitch, 0, pose.roll, "YXZ");
    this.plane.updateMatrixWorld(true);
    this.pm.copy(this.plane.matrixWorld);
    const local = PLANE_LOCAL(id);
    // camera (inside shots ride with the plane)
    const c = camAt(id, f);
    const cp = V(...c.pos), cl = V(...c.look), cu = V(0, 1, 0);
    if (s.inside) { cp.applyMatrix4(this.pm); cl.applyMatrix4(this.pm); cu.transformDirection(this.pm); }
    cam.position.copy(cp); cam.up.copy(cu); cam.lookAt(cl); cam.rotateZ(c.roll);
    cam.fov = c.fov; cam.near = s.inside ? 0.05 : 0.15; cam.far = 3000; cam.updateProjectionMatrix(); cam.updateMatrixWorld();
    const focus = cl.clone(), dist = cam.position.distanceTo(focus);
    cam.layers.enable(NOINK);
    // places
    const flight = s.place === "flight";
    this.plane.visible = flight || s.place === "ground" || s.place === "hangar";
    this.flightEnv.visible = flight;
    this.airport.visible = s.place === "ground";
    this.hangar.visible = s.place === "hangar";
    this.ward.visible = s.place === "ward";
    this.exp.visible = s.place === "exp" && id === 17;
    this.cut.visible = s.place === "exp" && id !== 17;
    this.gear.visible = pose.gear;
    this.planeIn.visible = !!s.inside || id === 1 || s.place === "hangar" || id === 6;
    this.skinMesh.castShadow = !s.inside;
    // the captain's pane: on, or flying off up and back over the roof
    const off = paneOff(id, t);
    if (off < 0) { this.paneL.visible = true; this.paneL.position.set(...PANE_C); this.paneL.rotation.set(0, 0, 0); }
    else if (off > 3) this.paneL.visible = false;
    else {
      const n = V(PANE_C[0], PANE_C[1] - profile(PANE_C[2]).c, 0).normalize();
      this.paneL.visible = true;
      this.paneL.position.set(PANE_C[0] + n.x * 3 * off, PANE_C[1] + n.y * 3 * off + 4 * off, PANE_C[2] + 28 * off * off + 2 * off);
      this.paneL.rotation.set(9 * off, 3 * off, 6 * off);
    }
    // bolts: steel / red (too thin) / orange (too short)
    if (id === 16) {
      const cols = [new THREE.Color("#c8ccd4"), new THREE.Color("#ff3b3b"), new THREE.Color("#ffa51f")];
      this.boltPts.forEach((_, i) => this.bolts.setColorAt(i, cols[boltMark(id, t, i)]));
      this.bolts.instanceColor!.needsUpdate = true;
      this.bolts.scale.setScalar(1);
    }
    this.bolts.visible = s.place === "hangar";
    (this.paneR.material as THREE.MeshLambertMaterial).opacity = id === 16 ? 0.6 : 0.32;
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
    this.sky.visible = s.place !== "hangar" && s.place !== "exp";
    untone(L.fog, this.fog.color); this.fog.near = flight ? 200 : L.fogNear; this.fog.far = flight ? 2000 : s.place === "ground" ? 900 : L.fogFar;
    scene.fog = this.fog; scene.background = null;
    for (let i = 0; i < this.clouds.length; i++) {
      const m = this.clouds[i], mat = m.material as THREE.MeshBasicMaterial;
      m.lookAt(cam.position.x, m.position.y, cam.position.z);
      mat.map = this.cloudMaps[s.light][i % 4];
      m.visible = s.place === "flight" || s.place === "ground" || s.place === "ward";
    }
    // flight: deck scrolls, clouds stream past
    if (flight) {
      this.deckMap.offset.set(0, -t * 0.02);
      for (const p of this.puffs) {
        let z = p.z + t * 70;
        z = ((z + 500) % 900 + 900) % 900 - 500;
        p.m.position.set(p.x, p.y, z); p.m.scale.set(p.w, p.w * 0.5, 1);
        p.m.quaternion.copy(cam.quaternion);
      }
    }
    // the bolt macro: the short bolt rises into view
    if (this.exp.visible) this.expShort.position.y = EXP[1] - 2.2 * (1 - smooth((t - T_SHORT + 0.1) / 0.45));
    // the cutaway: bolts pull out and the pane flies off when it fails
    if (this.cut.visible) {
      const u = Math.max(0, t - T_FAIL);
      this.cutBolts.forEach((g, k) => {
        const b = g.userData.base as THREE.Vector3, d = Math.max(0, u - 0.05 * k);
        g.position.set(b.x + 6 * d * d + 2.5 * d, b.y + (k ? -1 : 1) * 1.5 * d, b.z);
        g.rotation.set(0, 0, Math.PI / 2 + (k ? -1 : 1) * 4 * d);
      });
      this.cutPane.position.set(CUT[0] + 9 * u * u + 3 * u, CUT[1] + 1.5 * u, CUT[2]);
      this.cutPane.rotation.set(0, 0, -1.5 * u);
      // "thinner bolts, less grip": a tiny wobble in the nut once the cabin pushes
      if (u === 0 && t > 57.9) this.cutBolts.forEach((g, k) => { const b = g.userData.base as THREE.Vector3; g.position.y = b.y + 0.02 * Math.sin(t * 25 + k); g.position.x = b.x + 0.05 * smooth((t - 59.9) / 2.5) * (0.6 + 0.4 * Math.sin(t * 9 + k)); });
    }
    // cast + effects
    const right = V(0, 0, 0).setFromMatrixColumn(cam.matrixWorld, 0);
    // staging speaks plane-local for flight + hangar: give it the camera in plane space
    const inv = new THREE.Matrix4().copy(this.pm).invert();
    const camLocal = local ? cam.position.clone().applyMatrix4(inv) : cam.position.clone();
    const rightLocal = local ? right.clone().transformDirection(inv) : right;
    const sunLocal = local ? sunDir.clone().transformDirection(inv) : sunDir;
    const st = stage(id, t, { pos: camLocal, right: rightLocal, sun: sunLocal });
    this.frustum.setFromProjectionMatrix(this.m4.multiplyMatrices(cam.projectionMatrix, cam.matrixWorldInverse));
    let ai = 0;
    const used: Actor[] = [];
    const yawQ = new THREE.Quaternion(), planeQ = new THREE.Quaternion().setFromRotationMatrix(this.pm);
    for (const p of st.places) {
      const sc2 = p.scale ?? 1;
      const wp = V(p.x, p.y, p.z); if (local) wp.applyMatrix4(this.pm);
      if (!this.frustum.intersectsSphere(this.sph.set(this.v.copy(wp).add(V(0, 1.1 * sc2, 0)), 3.5))) continue;
      const a = this.actor(ai++);
      const [w, h, k] = p.size ?? [300, 500, 0.5];
      a.r = this.pool.req(p.key, w, h, k, p.draw);
      a.mesh.visible = true;
      a.mesh.position.copy(wp);
      const yaw = p.yaw ?? Math.atan2(camLocal.x - p.x, camLocal.z - p.z);
      a.mesh.rotation.set(0, yaw, p.roll ?? 0);
      if (local) { yawQ.setFromEuler(a.mesh.rotation); a.mesh.quaternion.copy(planeQ).multiply(yawQ); }
      a.mesh.scale.set(p.mirror ? -sc2 : sc2, sc2, sc2);
      a.mesh.castShadow = L.actorShadow;
      used.push(a);
    }
    for (let i = ai; i < this.actors.length; i++) this.actors[i].mesh.visible = false;
    let fi = 0;
    const fused: Fx[] = [];
    for (const p of st.fx) {
      const wp = V(p.x, p.y, p.z); if (local) wp.applyMatrix4(this.pm);
      if (!this.frustum.intersectsSphere(this.sph.set(wp, Math.max(p.w, p.h)))) continue;
      const ef = this.fx(fi++);
      ef.r = this.pool.req(p.key, p.cw, p.ch, 1, p.draw);
      ef.use(!!p.soft);
      ef.mesh.visible = true;
      ef.mesh.position.copy(wp);
      if (p.flat) { ef.mesh.rotation.set(-Math.PI / 2, 0, p.rot ?? 0); if (local) ef.mesh.quaternion.premultiply(planeQ); }
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

/** horizontal quad facing up at height dy covering x0..x1, z0..z1 (z0 < z1) */
function quadUp(x0: number, x1: number, z0: number, z1: number, u: number, v: number, dy = 0) {
  const y = dy, g = new THREE.BufferGeometry();
  g.setAttribute("position", new THREE.Float32BufferAttribute([x0, y, z1, x1, y, z1, x1, y, z0, x0, y, z1, x1, y, z0, x0, y, z0], 3));
  g.setAttribute("normal", new THREE.Float32BufferAttribute([0, 1, 0, 0, 1, 0, 0, 1, 0, 0, 1, 0, 0, 1, 0, 0, 1, 0], 3));
  g.setAttribute("uv", new THREE.Float32BufferAttribute([0, 0, u, 0, u, v, 0, 0, u, v, 0, v], 2));
  return g;
}
