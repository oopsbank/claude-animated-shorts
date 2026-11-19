// The world of "The Street That Drowned in Beer": the Horse Shoe Brewery yard (vats of porter, the 25 ft brick wall),
// the St Giles street beyond it, the cutaway vat of the explanation and a panelled room (dinner + court). Built once;
// posed every frame from story.ts: vats bulge, burst and fly apart, the breach topples into the street, the beer is a
// height field rebuilt per frame from beerDepth(). Sky, sun, two-tone shading and ink come from the bridge look.
import * as THREE from "three";
import { Batch, V, lam, boxGeo, quad, house, setSight, Ray } from "./build";
import { ctex, rep, cobbleHD, stoneHD, beam, beamHD, planksHD, cloudHD, rng } from "./paint";
import { Pen, INK, BEER, FOAM } from "./toon";
import { LIGHTS, LOOK, LightPreset } from "./lights";
import { TONE, CHAR, twoTone, untone } from "./shade";
import { NOINK } from "./ink";
import { Pool, Actor, Fx, stage, BALCONIES, CELLAR } from "./cast";
import {
  FPS, SHOTS, ShotDef, V3, VATS, Vat, SLIP_HOOP, YARD, WALL_H, WALL_T, BREACH, STREET, OFFICE, EXP, ROOM, TABLE, BENCH,
  camAt, beerDepth, beerFoam, vatState, wallFall, smooth, clamp01,
} from "./story";

type Mats = Record<string, THREE.Material>;
const SUN_SHOT: Record<number, { az?: number; el?: number }> = { 14: { az: 150, el: 24 } };
const smokeTex = () => ctex("smoke", 256, 256, (g) => {
  const p = new Pen(g);
  for (const [x, y, r, c] of [[90, 150, 60, "#8f8d96"], [150, 120, 70, "#a3a1aa"], [170, 165, 55, "#8f8d96"], [120, 100, 50, "#b4b2ba"]] as const) p.ell(x, y, r, r * 0.85, c, 0);
});
/** the brewery's sign: a horseshoe on a cream roundel (a picture, no lettering) */
const horseshoeTex = () => ctex("horseshoe", 512, 512, (g) => {
  const p = new Pen(g);
  p.ell(256, 256, 236, 236, "#f1e6c8", 18);
  p.ell(256, 256, 204, 204, null, 6);
  g.lineCap = "round";
  const arc = (r: number, w: number, col: string) => { g.beginPath(); g.arc(256, 238, r, Math.PI * 0.82, Math.PI * 2.18, false); g.strokeStyle = col; g.lineWidth = w; g.stroke(); };
  arc(120, 78, INK); arc(120, 58, "#7d848c");
  for (let i = 0; i < 7; i++) { const a = Math.PI * (0.88 + (1.24 * i) / 6); p.dot(256 + 120 * Math.cos(a), 238 + 120 * Math.sin(a), 8, INK); }
});
/** wood panelling for the room: wainscot, panels, a dado rail */
const panelTex = () => ctex("panel", 1024, 512, (g, r) => {
  g.fillStyle = "#8a5a36"; g.fillRect(0, 0, 1024, 512);
  for (let i = 0; i < 4; i++) {
    const x = 20 + i * 256;
    g.fillStyle = "#9c6a42"; g.fillRect(x, 40, 216, 250);
    g.fillStyle = "#7a4c2c"; g.fillRect(x, 330, 216, 150);
    g.strokeStyle = "rgba(30,15,10,.55)"; g.lineWidth = 6; g.strokeRect(x, 40, 216, 250); g.strokeRect(x, 330, 216, 150);
    g.fillStyle = "rgba(255,230,190,.08)"; g.fillRect(x + 8, 48, 18, 234);
  }
  g.fillStyle = "#5e3a22"; g.fillRect(0, 300, 1024, 18);
  for (let i = 0; i < 60; i++) { g.fillStyle = `rgba(60,30,15,${0.04 + r() * 0.05})`; g.fillRect(r() * 1024, r() * 512, 2 + r() * 40, 2); }
});
/** the court's crest: a shield with a crown above (no lettering) */
const crestTex = () => ctex("crest", 512, 512, (g) => {
  const p = new Pen(g);
  p.poly([[136, 170], [376, 170], [376, 320], [256, 440], [136, 320]], "#c8323a", 14);
  p.poly([[180, 200], [332, 200], [332, 300], [256, 392], [180, 300]], "#e8c45a", 10);
  p.poly([[176, 140], [196, 70], [226, 120], [256, 60], [286, 120], [316, 70], [336, 140]], "#e8c45a", 12);
});
const windowTex = () => ctex("roomWin", 256, 384, (g) => {
  g.fillStyle = "#bcd8f0"; g.fillRect(0, 0, 256, 384);
  g.fillStyle = "rgba(255,255,255,.35)"; g.beginPath(); g.moveTo(30, 380); g.lineTo(120, 0); g.lineTo(170, 0); g.lineTo(80, 380); g.fill();
  g.strokeStyle = "#5e3a22"; g.lineWidth = 18; g.strokeRect(9, 9, 238, 366);
  g.lineWidth = 10; g.beginPath(); g.moveTo(128, 0); g.lineTo(128, 384); g.moveTo(0, 130); g.lineTo(256, 130); g.moveTo(0, 256); g.lineTo(256, 256); g.stroke();
});

/** every lens of the yard and street shots looking at its subject (houses in the way are left out) */
const sightLines = (): Ray[] => {
  const out: Ray[] = [];
  for (const s of SHOTS) {
    if (s.place !== "yard" && s.place !== "street") continue;
    for (let f = s.a - 8; f < s.b + 8; f += 3) {
      const c = camAt(s.id, Math.max(s.a, Math.min(s.b - 1, f))), o = V(...c.pos), look = V(...c.look);
      const fw = look.clone().sub(o), len = fw.length();
      fw.normalize();
      const rt = fw.clone().cross(V(0, 1, 0)).normalize(), up = rt.clone().cross(fw);
      const ty = Math.tan((c.fov * Math.PI) / 360), tx = ty * (9 / 16);
      for (const [sx, sy] of [[0, 0], [-0.6, 0], [0.6, 0], [0, 0.6], [0, -0.4]])
        out.push({ o, d: fw.clone().addScaledVector(rt, sx * tx).addScaledVector(up, sy * ty), len, core: sx === 0 && sy === 0 });
    }
  }
  return out;
};

// ---------------- vats ----------------
type VatObj = { v: Vat; grp: THREE.Group; staves: THREE.InstancedMesh; n: number; hoops: THREE.Mesh[]; lid: THREE.Mesh; seeds: number[]; open: boolean };
const STAVE_T = 0.17;
const makeVat = (parent: THREE.Object3D, v: Vat, M: Mats, open = false): VatObj => {
  const grp = new THREE.Group(); parent.add(grp);
  const n = Math.max(16, Math.round((2 * Math.PI * v.r) / 0.45));
  const w = ((2 * Math.PI * v.r) / n) * 1.03;
  const staves = new THREE.InstancedMesh(new THREE.BoxGeometry(w, v.h, STAVE_T), M.stave, n);
  staves.castShadow = true; staves.receiveShadow = true; staves.frustumCulled = false;
  const r = rng(Math.abs(Math.round(v.x * 13 + v.z * 7)) + 101), cols = ["#ffffff", "#f4ebe2", "#fff4e8", "#ebe1d6"].map((c) => new THREE.Color(c));
  for (let i = 0; i < n; i++) staves.setColorAt(i, cols[Math.floor(r() * 4) % 4]);
  grp.add(staves);
  const arc = open ? (Math.PI * 4) / 3 : Math.PI * 2;
  const hoops = v.hoops.map(() => {
    const g = new THREE.TorusGeometry(v.r + STAVE_T * 0.5 + 0.03, 0.07, 6, 64, arc);
    g.rotateX(Math.PI / 2);
    if (open) g.rotateY((-5 * Math.PI) / 6); // gap toward +z (the lens)
    const m = new THREE.Mesh(g, M.iron); m.castShadow = true; m.receiveShadow = true; grp.add(m); return m;
  });
  const lid = new THREE.Mesh(new THREE.CylinderGeometry(v.r + 0.12, v.r + 0.12, 0.22, 40), M.lid);
  lid.castShadow = true; lid.receiveShadow = true; lid.visible = !open; grp.add(lid);
  const seeds = Array.from({ length: n }, () => r());
  return { v, grp, staves, n, hoops, lid, seeds, open };
};
const m4 = new THREE.Matrix4(), qt = new THREE.Quaternion(), eu = new THREE.Euler(), pv = new THREE.Vector3(), sv = new THREE.Vector3(1, 1, 1);
/** pose a vat: whole (bulge, slipped hoop, falling hoop) or burst (s seconds after) */
const poseVat = (o: VatObj, st: { burst: number; bulge: number; slip: number; drop: number }) => {
  const v = o.v, s = st.burst;
  for (let i = 0; i < o.n; i++) {
    const a = (i / o.n) * Math.PI * 2;
    const hide = o.open && Math.cos(a) > 0.45;
    let x = v.x + Math.sin(a) * v.r, z = v.z + Math.cos(a) * v.r, y = v.h / 2, rx = 0, ry = a, rz = 0;
    if (hide) { o.staves.setMatrixAt(i, m4.makeScale(0, 0, 0)); continue; }
    if (s >= 0) {
      const sd = o.seeds[i], out = 4.5 + 4 * sd, up = 2.5 + 3.5 * ((sd * 7.3) % 1), spin = (2.2 + 2.5 * ((sd * 3.1) % 1)) * (sd > 0.5 ? 1 : -1);
      const tl = Math.min(s, (up + Math.sqrt(up * up + 2 * 9.8 * (v.h / 2 - 0.1))) / 9.8); // airborne until it lands
      x += Math.sin(a) * out * tl; z += Math.cos(a) * out * tl;
      y = Math.max(0.12, v.h / 2 + up * tl - 4.9 * tl * tl);
      const tip = Math.min(Math.PI / 2, Math.abs(spin) * tl) * Math.sign(spin);
      rx = s > tl ? Math.PI / 2 * Math.sign(spin) : tip; // lying flat once landed
      if (s > tl) y = 0.1;
      rz = 0.4 * (sd - 0.5) * Math.min(1, s * 3);
    } else if (st.bulge > 0) {
      const wob = 1 + 0.35 * Math.sin(i * 2.3);
      x += Math.sin(a) * 0.12 * st.bulge * wob; z += Math.cos(a) * 0.12 * st.bulge * wob;
    }
    eu.set(rx, ry, rz, "YXZ"); qt.setFromEuler(eu);
    o.staves.setMatrixAt(i, m4.compose(pv.set(x, y, z), qt, sv.set(1, 1, 1)));
  }
  o.staves.instanceMatrix.needsUpdate = true;
  o.hoops.forEach((h, k) => {
    let y = v.hoops[k], sc = 1 + (st.bulge > 0 ? 0.035 * st.bulge : 0), tilt = 0;
    if (k === SLIP_HOOP && st.slip > 0) { y -= 0.62 * st.slip; tilt = 0.075 * st.slip; }
    if (k === SLIP_HOOP && st.drop > 0) { y = v.hoops[k] + (0.09 - v.hoops[k]) * st.drop * st.drop; tilt = 0.05 * st.drop; }
    if (s >= 0) {
      const tl = Math.min(s, 0.55);
      sc = 1 + 0.55 * Math.min(1, s * 2.5);
      y = Math.max(0.09 + k * 0.03, y - 4.9 * tl * tl * (1 + k * 0.4));
      tilt = 0.25 * Math.sin(k * 1.7) * Math.min(1, s * 2);
    }
    h.position.set(v.x, y, v.z); h.scale.set(sc, 1, sc); h.rotation.set(tilt, 0, tilt * 0.4);
  });
  if (s >= 0) {
    const tl = Math.min(s, 1.25);
    o.lid.position.set(v.x + 1.5 * tl, Math.max(0.12, v.h + 6 * tl - 4.9 * tl * tl), v.z - 1.0 * tl);
    o.lid.rotation.set(2.5 * tl, 0, 1.2 * tl);
  } else { o.lid.position.set(v.x, v.h + 0.11 + 0.05 * st.bulge, v.z); o.lid.rotation.set(0, 0, 0); }
};

// ---------------- beer height field ----------------
type Field = { geo: THREE.BufferGeometry; nx: number; nz: number; xs: number[]; zs: number[]; mesh: THREE.Mesh };
const makeField = (parent: THREE.Object3D, mat: THREE.Material, x0: number, x1: number, z0: number, z1: number, dx: number, dz: number): Field => {
  const nx = Math.round((x1 - x0) / dx) + 1, nz = Math.round((z1 - z0) / dz) + 1;
  const xs = Array.from({ length: nx }, (_, i) => x0 + ((x1 - x0) * i) / (nx - 1)), zs = Array.from({ length: nz }, (_, j) => z0 + ((z1 - z0) * j) / (nz - 1));
  const geo = new THREE.BufferGeometry();
  geo.setAttribute("position", new THREE.BufferAttribute(new Float32Array(nx * nz * 3), 3));
  geo.setAttribute("normal", new THREE.BufferAttribute(new Float32Array(nx * nz * 3), 3));
  geo.setAttribute("color", new THREE.BufferAttribute(new Float32Array(nx * nz * 3), 3));
  geo.setAttribute("uv", new THREE.BufferAttribute(new Float32Array(nx * nz * 2), 2));
  const idx: number[] = [];
  for (let j = 0; j < nz - 1; j++) for (let i = 0; i < nx - 1; i++) {
    const a = j * nx + i, b = a + 1, c = a + nx, d = c + 1;
    idx.push(a, c, b, b, c, d);
  }
  geo.setIndex(idx);
  const mesh = new THREE.Mesh(geo, mat);
  mesh.frustumCulled = false; mesh.receiveShadow = true; mesh.castShadow = false;
  parent.add(mesh);
  return { geo, nx, nz, xs, zs, mesh };
};
const cBeer = new THREE.Color(), cFoam = new THREE.Color(), cLit = new THREE.Color(), ctmp = new THREE.Color();
const poseField = (F: Field, tau: number, t: number) => {
  const P = F.geo.attributes.position.array as Float32Array, C = F.geo.attributes.color.array as Float32Array;
  let wet = false;
  for (let j = 0; j < F.nz; j++) for (let i = 0; i < F.nx; i++) {
    const x = F.xs[i], z = F.zs[j], k = j * F.nx + i;
    const d = beerDepth(x, z, tau);
    const y = d > 0.015 ? d + 0.02 : -0.35;
    if (d > 0.015) wet = true;
    P[k * 3] = x; P[k * 3 + 1] = y + (d > 0.015 ? 0.03 * Math.sin(x * 1.7 + t * 2.4) * Math.sin(z * 1.3 - t * 1.9) : 0); P[k * 3 + 2] = z;
    const fo = beerFoam(x, z, tau);
    ctmp.copy(cBeer).lerp(cLit, clamp01((d - 0.6) * 0.25)).lerp(cFoam, Math.min(1, fo * 1.25));
    C[k * 3] = ctmp.r; C[k * 3 + 1] = ctmp.g; C[k * 3 + 2] = ctmp.b;
  }
  F.mesh.visible = wet;
  if (!wet) return;
  F.geo.attributes.position.needsUpdate = true; F.geo.attributes.color.needsUpdate = true;
  F.geo.computeVertexNormals();
};

// ---------------- the breach: bricks of the wall section that falls ----------------
const BCOLS = 10, BROWS = 8;
const BW = (BREACH.x1 - BREACH.x0) / BCOLS, BH = WALL_H / BROWS;

export class World {
  root = new THREE.Group();
  private yard = new THREE.Group(); private exp = new THREE.Group(); private room = new THREE.Group();
  private dinnerProps = new THREE.Group(); private courtProps = new THREE.Group();
  private pool = new Pool();
  private actors: Actor[] = [];
  private fxs: Fx[] = [];
  private hemi: THREE.HemisphereLight; private sun: THREE.DirectionalLight;
  private sky: THREE.Mesh; private skyMat: THREE.ShaderMaterial;
  private fog = new THREE.Fog("#bccbec", 25, 420);
  private sunDisc: THREE.Sprite;
  private sunCache = new Map<number, THREE.Vector3>();
  private cloudMaps: Record<"day" | "golden", THREE.Texture[]>;
  private clouds: THREE.Mesh[] = [];
  private smoke: { m: THREE.Mesh; mat: THREE.MeshLambertMaterial; top: V3; k: number }[] = [];
  private vats: VatObj[] = [];
  private expVat: VatObj;
  private bricks: THREE.InstancedMesh; private brickSeeds: number[] = [];
  private fields: Field[] = [];
  private frustum = new THREE.Frustum();
  private m4 = new THREE.Matrix4(); private v = new THREE.Vector3(); private sph = new THREE.Sphere();

  constructor() {
    const R = this.root, M: Mats = {};
    R.add(this.yard, this.exp, this.room);
    this.room.add(this.dinnerProps, this.courtProps);
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
          gl_FragColor = vec4(c, 1.0); }`,
      side: THREE.BackSide, depthWrite: false, fog: false,
    });
    this.sky = new THREE.Mesh(new THREE.SphereGeometry(1100, 48, 24), this.skyMat);
    this.sky.renderOrder = -1; this.sky.frustumCulled = false; this.sky.layers.set(NOINK);
    R.add(this.sky);
    const disc = ctex("sunDisc", 128, 128, (g) => {
      const gr = g.createRadialGradient(64, 64, 58, 64, 64, 64); gr.addColorStop(0, "rgba(255,255,255,1)"); gr.addColorStop(1, "rgba(255,255,255,0)");
      g.fillStyle = gr; g.fillRect(0, 0, 128, 128);
    });
    this.sunDisc = new THREE.Sprite(new THREE.SpriteMaterial({ map: disc, color: new THREE.Color(6.0, 4.4, 2.4), fog: false, depthWrite: false }));
    this.sunDisc.renderOrder = -0.5; this.sunDisc.frustumCulled = false; this.sunDisc.layers.set(NOINK); R.add(this.sunDisc);
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
    M.cobble = lam("cobbleHD", () => ({ map: cobbleHD() }));
    M.yardStone = lam("yardStone", () => ({ map: rep(stoneHD("yardStone", ["#cdbfa9", "#c3b49d", "#d6c9b4", "#bcae97"], "#9a8c78"), 1, 1) }));
    M.brick = lam("brickWall", () => ({ map: stoneHD("brickWall", ["#b4553a", "#a64d34", "#bd6043", "#9c4630"], "#d9c2a0") }));
    M.cope = lam("copeHD", () => ({ map: stoneHD("copeHD", ["#e6dccd", "#ddd3c3", "#ece4d6", "#d6cbba"], "#aea293") }));
    M.iron = twoTone(new THREE.MeshPhongMaterial({ color: "#3d414c", specular: "#8a8a8a", shininess: 60 }), 0.15);
    M.wood = lam("wood", () => ({ map: beam() }));
    M.stave = lam("staveHD", () => ({ map: beamHD(), color: "#f2d2a8" }));
    M.lid = lam("lidHD", () => ({ map: rep(planksHD(), 0.4, 0.4) }));
    M.dark = lam("cellarDark", () => ({ color: "#2a2230" }));
    M.planks = lam("planksHD", () => ({ map: planksHD() }));
    M.panel = lam("panel", () => ({ map: panelTex() }));
    M.cloth = lam("tablecloth", () => ({ color: "#f2ead8" }));
    M.plate = lam("plate", () => ({ color: "#f7f4ee" }));
    M.roast = lam("roast", () => ({ color: "#b8642e" }));
    M.green = lam("greenBaize", () => ({ color: "#3f6a4a" }));
    M.beerSolid = lam("beerSolid", () => ({ color: BEER }));
    M.foam = lam("foamSolid", () => ({ color: FOAM }));
    const signM = new THREE.MeshBasicMaterial({ map: horseshoeTex(), color: 0xe6e6e6 });
    const crestM = new THREE.MeshBasicMaterial({ map: crestTex(), alphaTest: 0.5, color: 0xdddddd });
    const winM = new THREE.MeshBasicMaterial({ map: windowTex(), color: 0xe8e8e8 });

    // ---- yard + street (static) ----
    const b = new Batch();
    b.add(quadUp(-400, 400, -400, 400, 200, 200, -0.02), M.cobble);
    b.add(quadUp(YARD.x0, YARD.x1, YARD.z0, YARD.z1, 12, 8.5, 0.0), M.yardStone);
    // yard walls: the street wall (both sides of the breach), side walls, coping
    const wallBox = (x0: number, x1: number, z0: number, z1: number, h = WALL_H) => {
      b.add(boxGeo(V(x0, 0, z0), V(x1, h, z1), 3), M.brick);
      b.add(boxGeo(V(x0 - 0.06, h, z0 - 0.06), V(x1 + 0.06, h + 0.25, z1 + 0.06), 2), M.cope);
    };
    wallBox(YARD.x0, BREACH.x0, 0, WALL_T); wallBox(BREACH.x1, YARD.x1, 0, WALL_T);
    wallBox(YARD.x0 - WALL_T, YARD.x0, YARD.z0, WALL_T); wallBox(YARD.x1, YARD.x1 + WALL_T, YARD.z0, WALL_T);
    // the brewery: a long brick block behind the yard, the horseshoe roundel, a tall chimney
    b.add(boxGeo(V(-26, 0, -50), V(26, 15, YARD.z0), 4), M.brick);
    b.add(boxGeo(V(-26.3, 15, -50.3), V(26.3, 15.6, YARD.z0 + 0.3), 2), M.cope);
    for (let i = 0; i < 9; i++) for (let fl = 0; fl < 3; fl++) {
      const x = -22 + i * 5.5, y = 2.2 + fl * 4.3;
      if (fl === 2 && Math.abs(x) < 4) continue;
      b.add(boxGeo(V(x - 0.9, y, YARD.z0 + 0.01), V(x + 0.9, y + 2.4, YARD.z0 + 0.06)), M.dark);
      b.add(boxGeo(V(x - 1.05, y - 0.18, YARD.z0), V(x + 1.05, y, YARD.z0 + 0.22)), M.cope);
    }
    b.add(boxGeo(V(-3.2, 0, YARD.z0), V(3.2, 4.8, YARD.z0 + 0.08)), M.wood); // the great doors
    b.add(boxGeo(V(12, 15, -46), V(15.4, 30, -42.6), 3), M.brick);
    b.add(boxGeo(V(11.7, 30, -46.3), V(15.7, 30.7, -42.3), 2), M.cope);
    const sign = new THREE.Mesh(new THREE.CircleGeometry(2.6, 48), signM);
    sign.position.set(0, 11.3, YARD.z0 + 0.08); sign.layers.set(NOINK); this.yard.add(sign);
    const signRim = new THREE.Mesh(new THREE.TorusGeometry(2.62, 0.12, 8, 64), M.iron); signRim.position.copy(sign.position); this.yard.add(signRim);
    // barrels stacked by the brewery doors and along the side wall
    const barrel = (x: number, z: number, y = 0, lying = false) => {
      const g = new THREE.CylinderGeometry(0.42, 0.42, 1.05, 18);
      const mm = new THREE.Matrix4().compose(V(x, y + (lying ? 0.42 : 0.525), z), new THREE.Quaternion().setFromEuler(new THREE.Euler(lying ? Math.PI / 2 : 0, 0, 0)), V(1, 1, 1));
      b.add(g, M.stave, mm);
      for (const k of [-0.32, 0.32]) {
        const h = new THREE.TorusGeometry(0.44, 0.035, 5, 24); h.rotateX(Math.PI / 2); h.translate(0, k, 0);
        b.add(h, M.iron, mm);
      }
    };
    for (let i = 0; i < 5; i++) barrel(-8 + i * 0.95, YARD.z0 + 1.3, 0, true);
    for (let i = 0; i < 4; i++) barrel(-7.5 + i * 0.95, YARD.z0 + 1.3, 0.8, true);
    for (let i = 0; i < 6; i++) barrel(YARD.x1 - 1.3, -6 - i * 1.0);
    // George's office: a one-storey cottage beside the vats (fronts the yard, +x)
    setSight([]);
    house(b, OFFICE.x, OFFICE.z, Math.PI / 2, 5.5, 4.6, 3.4, 4);
    // St Giles (no sight-line culling along the street: the street lenses look down it, the houses only frame it)
    setSight([]);
    // St Giles: houses both sides of the street, fronts on the street; a row along the far end; rows behind the wall
    const r = rng(23), pick = <T,>(a: T[]) => a[Math.floor(r() * a.length) % a.length];
    for (const sx of [-1, 1]) {
      let z = WALL_T + 0.1;
      while (z < STREET.z1 - 2) {
        const w = pick([5, 6, 7]), h = pick([5.6, 7, 7, 8.4]), d = 7;
        house(b, sx * (STREET.x1 + d / 2), z + w / 2, sx < 0 ? Math.PI / 2 : -Math.PI / 2, w, d, h, Math.floor(r() * 8));
        // cellar window well at the foot of every front
        for (const k of [-0.28, 0.28]) {
          const cz = z + w / 2 + k * w;
          b.add(boxGeo(V(sx * STREET.x1 - (sx > 0 ? 0 : 0.02), 0.02, cz - 0.55), V(sx * STREET.x1 + (sx > 0 ? 0.02 : 0), 0.62, cz + 0.55)), M.dark);
          b.add(boxGeo(V(sx * STREET.x1 - 0.06, 0.6, cz - 0.62), V(sx * STREET.x1 + 0.06, 0.7, cz + 0.62)), M.cope);
        }
        z += w + 0.05;
      }
      setSight(sightLines());
      for (let x = 13; x < 34; x += 6.5) house(b, sx * x, WALL_T + 4.2, Math.PI, 6.3, 7, pick([7, 8.4]), Math.floor(r() * 8));
      setSight([]);
      for (let z = -32; z < -2; z += 7) house(b, sx * (YARD.x1 + 4.5), z + 3.3, sx < 0 ? Math.PI / 2 : -Math.PI / 2, 6.6, 7, pick([7, 8.4, 9.8]), Math.floor(r() * 8));
    }
    for (let x = -14; x < 15; x += 7) house(b, x, STREET.z1 + 3.6, Math.PI, 6.8, 7, pick([7, 8.4]), Math.floor(r() * 8));
    // balconies the residents watch from (shot 13)
    for (const [x, y, z] of BALCONIES) {
      const out = x < 0 ? -1 : 1, x0 = out < 0 ? x - 0.65 : x - 0.65, x1 = x + 0.65;
      b.add(boxGeo(V(Math.min(x0, x1), y - 0.15, z - 1.2), V(Math.max(x0, x1), y, z + 1.2)), M.wood);
      const xr = x + out * 0.55;
      b.add(boxGeo(V(xr - 0.05, y + 0.85, z - 1.2), V(xr + 0.05, y + 0.95, z + 1.2)), M.wood);
      for (let k = -2; k <= 2; k++) b.add(boxGeo(V(xr - 0.035, y, z + k * 0.58 - 0.035), V(xr + 0.035, y + 0.9, z + k * 0.58 + 0.035)), M.wood);
    }
    b.build(this.yard);
    // the vats
    VATS.forEach((v) => this.vats.push(makeVat(this.yard, v, M)));
    // the breach bricks (instanced: they topple and scatter)
    this.bricks = new THREE.InstancedMesh(new THREE.BoxGeometry(BW * 0.98, BH * 0.98, WALL_T), M.brick, BCOLS * BROWS + BCOLS);
    this.bricks.castShadow = true; this.bricks.receiveShadow = true; this.bricks.frustumCulled = false;
    const rb = rng(5);
    for (let i = 0; i < BCOLS * BROWS + BCOLS; i++) this.brickSeeds.push(rb());
    this.yard.add(this.bricks);
    // the beer: yard field and street field
    // a little self-light keeps porter brown in the street's shade (the blue-violet shade turned it navy)
    const beerM = new THREE.MeshLambertMaterial({ vertexColors: true, color: 0xffffff, emissive: new THREE.Color("#2a1407") });
    cBeer.set("#5e3216"); cLit.set("#73401c"); cFoam.set("#f0e2be");
    this.fields.push(makeField(this.yard, beerM, YARD.x0, YARD.x1, YARD.z0, WALL_T + 0.3, 0.5, 0.5));
    this.fields.push(makeField(this.yard, beerM, STREET.x0, STREET.x1, 0.3, STREET.z1, 0.4, 0.5));
    // chimney smoke over the brewery
    const smokeT = smokeTex();
    for (let k = 0; k < 7; k++) {
      const mat = new THREE.MeshLambertMaterial({ map: smokeT, transparent: true, depthWrite: false });
      const m = new THREE.Mesh(new THREE.PlaneGeometry(1, 1), mat);
      m.layers.set(NOINK);
      this.smoke.push({ m, mat, top: [13.7, 31, -44.3], k: k / 7 }); this.yard.add(m);
    }

    // ---- the explanation: a cutaway vat full of porter against a brick backdrop ----
    const e = new Batch();
    e.add(quadUp(EXP[0] - 60, EXP[0] + 60, EXP[2] - 40, EXP[2] + 40, 30, 20, 0), M.yardStone);
    e.add(boxGeo(V(EXP[0] - 40, 0, EXP[2] - 14), V(EXP[0] + 40, 14, EXP[2] - 13)), M.brick);
    e.build(this.exp);
    const ev: Vat = { x: EXP[0], z: EXP[2], r: 2.9, h: 6.4, hoops: [0.55, 1.75, 2.95, 4.15, 5.35, 6.1] };
    this.expVat = makeVat(this.exp, ev, M, true);
    poseVat(this.expVat, { burst: -1, bulge: 0, slip: 0, drop: 0 });
    const beerCol = new THREE.Mesh(new THREE.CylinderGeometry(ev.r - 0.12, ev.r - 0.12, 5.7, 48), M.beerSolid);
    beerCol.position.set(EXP[0], 5.7 / 2, EXP[2]); beerCol.castShadow = true; beerCol.receiveShadow = true; this.exp.add(beerCol);
    const head = new THREE.Mesh(new THREE.CylinderGeometry(ev.r - 0.1, ev.r - 0.1, 0.25, 48), M.foam);
    head.position.set(EXP[0], 5.7 + 0.12, EXP[2]); this.exp.add(head);

    // ---- the room (dinner + court) ----
    const rr = new Batch(), [rx, , rz] = ROOM;
    rr.add(quadUp(rx - 7, rx + 7, rz - 6, rz + 9, 3.5, 3.75, 0), M.planks);
    rr.add(quad(V(rx - 7, 0, rz - 6), V(rx + 7, 0, rz - 6), V(rx + 7, 7, rz - 6), V(rx - 7, 7, rz - 6), 3.5, 1.75), M.panel);
    rr.add(quad(V(rx - 7, 0, rz + 9), V(rx - 7, 0, rz - 6), V(rx - 7, 7, rz - 6), V(rx - 7, 7, rz + 9), 3.75, 1.75), M.panel);
    rr.add(quad(V(rx + 7, 0, rz - 6), V(rx + 7, 0, rz + 9), V(rx + 7, 7, rz + 9), V(rx + 7, 7, rz - 6), 3.75, 1.75), M.panel);
    rr.add(boxGeo(V(rx - 7.2, 7, rz - 6.2), V(rx + 7.2, 7.4, rz + 9)), M.wood);
    rr.build(this.room);
    for (const wx of [-4.6, 4.6]) {
      const w = new THREE.Mesh(new THREE.PlaneGeometry(1.7, 2.55), winM);
      w.position.set(rx + wx, 3.7, rz - 5.97); w.layers.set(NOINK); this.room.add(w);
    }
    const crest = new THREE.Mesh(new THREE.PlaneGeometry(1.8, 1.8), crestM);
    crest.position.set(rx, 4.9, rz - 5.96); crest.layers.set(NOINK); this.courtProps.add(crest);
    // court: the judge's raised bench, a clerk's desk for the money
    const cb = new Batch(), [bx, , bz] = BENCH;
    cb.add(boxGeo(V(bx - 2.6, 0, bz - 1.4), V(bx + 2.6, 1.25, bz + 0.4)), M.wood);
    cb.add(boxGeo(V(bx - 2.6, 0, bz + 0.4), V(bx + 2.6, 2.0, bz + 0.75), 0, true), M.panel);
    cb.add(boxGeo(V(bx - 2.7, 2.0, bz + 0.3), V(bx + 2.7, 2.13, bz + 0.85)), M.wood);
    cb.add(boxGeo(V(bx + 0.8, 0.82, bz + 3.0), V(bx + 1.75, 0.9, bz + 3.85)), M.green);
    for (const [dx, dz] of [[0.85, 3.05], [1.7, 3.05], [0.85, 3.8], [1.7, 3.8]]) cb.add(boxGeo(V(bx + dx - 0.04, 0, bz + dz - 0.04), V(bx + dx + 0.04, 0.82, bz + dz + 0.04)), M.wood);
    cb.build(this.courtProps);
    // dinner: a table with a cloth, plates, a roast, a jug of porter
    const db = new Batch(), [tx, , tz] = TABLE;
    db.add(boxGeo(V(tx - 1.3, 0.72, tz - 0.6), V(tx + 1.3, 0.8, tz + 0.6)), M.cloth);
    db.add(boxGeo(V(tx - 1.32, 0.42, tz + 0.58), V(tx + 1.32, 0.8, tz + 0.62)), M.cloth);
    for (const [dx, dz] of [[-1.2, -0.5], [1.2, -0.5], [-1.2, 0.5], [1.2, 0.5]]) db.add(boxGeo(V(tx + dx - 0.05, 0, tz + dz - 0.05), V(tx + dx + 0.05, 0.72, tz + dz + 0.05)), M.wood);
    for (const dx of [-0.75, 0.0, 0.75]) db.add(new THREE.CylinderGeometry(0.22, 0.18, 0.03, 24), M.plate, new THREE.Matrix4().makeTranslation(tx + dx, 0.815, tz + 0.15));
    const roast = new THREE.SphereGeometry(0.22, 18, 12); roast.scale(1.35, 0.8, 1);
    db.add(roast, M.roast, new THREE.Matrix4().makeTranslation(tx, 0.95, tz + 0.15));
    db.add(new THREE.CylinderGeometry(0.11, 0.13, 0.32, 16), M.lid, new THREE.Matrix4().makeTranslation(tx + 0.7, 0.96, tz - 0.15));
    db.build(this.dinnerProps);
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
    const az = THREE.MathUtils.degToRad(SUN_SHOT[id]?.az ?? L.az), el = THREE.MathUtils.degToRad(SUN_SHOT[id]?.el ?? L.el);
    const hx = fx * Math.cos(az) - fz * Math.sin(az), hz = fz * Math.cos(az) + fx * Math.sin(az);
    v = new THREE.Vector3(hx * Math.cos(el), Math.sin(el), hz * Math.cos(el)).normalize();
    this.sunCache.set(id, v);
    return v;
  }
  private actor(i: number) { while (this.actors.length <= i) this.actors.push(new Actor(this.root)); return this.actors[i]; }
  private fx(i: number) { while (this.fxs.length <= i) this.fxs.push(new Fx(this.root)); return this.fxs[i]; }

  update(id: number, f: number, cam: THREE.PerspectiveCamera, scene: THREE.Scene) {
    const t = f / FPS, s = SHOTS[id - 1], tau = s.tau(t), L = LIGHTS[s.light];
    const c = camAt(id, f);
    cam.position.set(...c.pos); cam.up.set(0, 1, 0); cam.lookAt(...c.look); cam.rotateZ(c.roll);
    cam.fov = c.fov; cam.near = 0.15; cam.far = 1500; cam.updateProjectionMatrix(); cam.updateMatrixWorld();
    const focus = V(...c.look), dist = cam.position.distanceTo(focus);
    cam.layers.enable(NOINK);
    // places
    this.yard.visible = s.place === "yard" || s.place === "street";
    this.exp.visible = s.place === "exp";
    this.room.visible = s.place === "room";
    this.dinnerProps.visible = id === 16 || id === 17;
    this.courtProps.visible = id >= 18 && id <= 20;
    // light rig
    const K = LOOK[s.light], sunDir = this.shotSun(id, s, L);
    this.hemi.color.set(L.sky); this.hemi.groundColor.set(L.ground); this.hemi.intensity = L.hemiI;
    this.sun.color.set(L.sunCol); this.sun.intensity = L.sunI;
    let Rr = THREE.MathUtils.clamp(dist * 1.15 + 7, 12, 70);
    if (s.light === "golden") Rr = Math.max(Rr, 34);
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
    untone(L.fog, this.fog.color); this.fog.near = L.fogNear; this.fog.far = L.fogFar;
    scene.fog = this.fog; scene.background = null;
    this.sunDisc.visible = s.light === "golden";
    if (this.sunDisc.visible) {
      this.sunDisc.position.copy(cam.position).addScaledVector(sunDir, 900);
      this.sunDisc.scale.setScalar(2 * 900 * Math.tan(THREE.MathUtils.degToRad(1.7)));
    }
    for (let i = 0; i < this.clouds.length; i++) {
      const m = this.clouds[i], mat = m.material as THREE.MeshBasicMaterial;
      m.lookAt(cam.position.x, m.position.y, cam.position.z);
      mat.map = this.cloudMaps[s.light][i % 4];
    }
    // the yard
    if (this.yard.visible) {
      this.vats.forEach((o, i) => poseVat(o, vatState(id, i, tau)));
      const ftau = id >= 21 ? 0 : tau; // "today": the yard is dry and the wall stands
      this.poseBreach(ftau);
      for (const F of this.fields) poseField(F, ftau, t);
      for (const sm of this.smoke) {
        const u = (t * 0.11 + sm.k) % 1, sz = 3 + u * 9;
        sm.m.position.set(sm.top[0] - u * 18, sm.top[1] + u * 13 + u * u * 4, sm.top[2] + u * 3);
        sm.m.scale.set(sz, sz, 1); sm.m.quaternion.copy(cam.quaternion);
        sm.mat.opacity = 0.85 * (1 - u) ** 1.2;
      }
    }
    // cast + effects
    const right = V(0, 0, 0).setFromMatrixColumn(cam.matrixWorld, 0);
    const st = stage(id, t, tau, { pos: cam.position, right, sun: sunDir });
    this.frustum.setFromProjectionMatrix(this.m4.multiplyMatrices(cam.projectionMatrix, cam.matrixWorldInverse));
    let ai = 0;
    const used: Actor[] = [];
    for (const p of st.places) {
      const sc2 = p.scale ?? 1;
      if (!this.frustum.intersectsSphere(this.sph.set(this.v.set(p.x, p.y + 1.1 * sc2, p.z), 3.5))) continue;
      const a = this.actor(ai++);
      const [w, h, k] = p.size ?? [300, 500, 0.5];
      a.r = this.pool.req(p.key, w, h, k, p.draw);
      a.mesh.visible = true;
      a.mesh.position.set(p.x, p.y, p.z);
      a.mesh.rotation.set(0, p.yaw ?? Math.atan2(cam.position.x - p.x, cam.position.z - p.z), p.roll ?? 0);
      a.mesh.scale.set(p.mirror ? -sc2 : sc2, sc2, sc2);
      a.mesh.castShadow = L.actorShadow;
      used.push(a);
    }
    for (let i = ai; i < this.actors.length; i++) this.actors[i].mesh.visible = false;
    let fi = 0;
    const fused: Fx[] = [];
    for (const p of st.fx) {
      if (!this.frustum.intersectsSphere(this.sph.set(this.v.set(p.x, p.y, p.z), Math.max(p.w, p.h)))) continue;
      const ef = this.fx(fi++);
      ef.r = this.pool.req(p.key, p.cw, p.ch, 1, p.draw);
      ef.use(!!p.soft);
      ef.mesh.visible = true;
      ef.mesh.position.set(p.x, p.y, p.z);
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

  /** the breach topples outward about its foot, breaking up as it goes, and lies in the street */
  private poseBreach(tau: number) {
    const s = wallFall(tau);
    const th = (Math.PI / 2) * Math.min(1, (s / 0.95) ** 2);
    const brk = smooth((s - 0.25) / 0.7);
    let k = 0;
    for (let row = 0; row < BROWS; row++) for (let col = 0; col < BCOLS; col++, k++) {
      const sd = this.brickSeeds[k];
      const x = BREACH.x0 + (col + 0.5) * BW + (row % 2 ? 0.12 : -0.12) * 0;
      const yc = (row + 0.5) * BH;
      // rotate the panel point (y = yc, z = WALL_T/2) about the hinge (y 0, z WALL_T) toward +z
      const hz = WALL_T, ly = yc, lz = WALL_T / 2 - hz;
      let y = ly * Math.cos(th) - lz * Math.sin(th), z = hz + ly * Math.sin(th) + lz * Math.cos(th);
      let rx = th;
      // break-up: bricks spread along the street and tumble
      const spread = brk * (0.6 + 1.8 * sd);
      z += spread * (0.5 + row * 0.25); y = Math.max(0.3 * (1 - brk) + BH * 0.5 * brk * (0.4 + sd), y * (1 - 0.3 * brk));
      rx += brk * (sd - 0.5) * 1.6;
      const xj = x + brk * (sd - 0.5) * 1.4;
      eu.set(rx, brk * (sd - 0.5) * 1.2, 0, "XYZ"); qt.setFromEuler(eu);
      this.bricks.setMatrixAt(k, m4.compose(pv.set(xj, y, z), qt, sv.set(1, 1, 1)));
    }
    // coping on top of the breach rides with the top row
    for (let col = 0; col < BCOLS; col++, k++) {
      const x = BREACH.x0 + (col + 0.5) * BW, ly = WALL_H + 0.1, lz = -WALL_T / 2;
      const y = ly * Math.cos(th) - lz * Math.sin(th), z = WALL_T + ly * Math.sin(th) + lz * Math.cos(th) + brk * 2.5;
      eu.set(th, 0, 0, "XYZ"); qt.setFromEuler(eu);
      this.bricks.setMatrixAt(k, m4.compose(pv.set(x, Math.max(0.2, y), z), qt, sv.set(1, 0.25 / BH, 1.1)));
    }
    this.bricks.instanceMatrix.needsUpdate = true;
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
