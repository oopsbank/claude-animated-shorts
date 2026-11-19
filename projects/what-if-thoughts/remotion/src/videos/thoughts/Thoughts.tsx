// "What If You Could Hear Everyone's Thoughts?": flat characters in a 3D toon world (bridge look).
// One three.js world (world.ts) posed per frame from the story timeline (story.ts). Post chain (look-match pass):
//   InkPass (world ink lines, own pass) -> lens blur pre + main (thin-lens DOF per shot from dofAt) ->
//   [bloom (emissive only) + NEUTRAL tone mapping + colour grade] (one merged EffectPass), MSAA 4.
// Ink runs before the DOF so lines blur with what they belong to; bloom after the DOF so glows defocus with their
// source; the grade is display-referred, so it comes after tone mapping. Every pixel-sized parameter is specified at
// 1080x1920 and scaled with the output size, so stills at --scale 0.5 and the 1440x2560 final match.
import React, { useEffect, useMemo, useState } from "react";
import * as THREE from "three";
import { AbsoluteFill, continueRender, delayRender, getInputProps, staticFile, useCurrentFrame } from "remotion";
import { ThreeCanvas } from "@remotion/three";
import { useThree } from "@react-three/fiber";
import { EffectComposer } from "@react-three/postprocessing";
import { BlendFunction, BloomEffect, ToneMappingEffect, ToneMappingMode } from "postprocessing";
import { World } from "./world";
import { InkPass, noInkFallback } from "../bridge/ink";
import { LensBlur, GrainEffect } from "../bridge/lensblur";
import { GradeEffect, GRADES, GRADE_STRENGTH, gradeFor } from "../bridge/grade";

import { TOTAL, FPS, layersAt, dofAt, NIGHT, DAYS } from "./story";
import { spring } from "remotion";

export const THOUGHTS_FRAMES = TOTAL;

/** A/B switches for test stills only (Remotion inputProps `{ post: { ink: false, ... } }`); everything is on by default. */
type PostToggles = { ink: boolean; lens: boolean; pre: boolean; bloom: boolean; grade: boolean; grain: boolean };
const toggles = (): PostToggles => ({ ink: true, lens: true, pre: true, bloom: true, grade: true, grain: false, ...((getInputProps() as { post?: Partial<PostToggles> }).post ?? {}) });

/** Bloom for emissive sources only (depth.md 6.4). Its MIP chain always starts at 540x960 (half of 1080x1920),
 *  whatever the output size, so the glow keeps the same size relative to the frame (e-fold ~30 px at 1080p,
 *  ~1.5 % of the frame height) at 540, 1080 and 1440 widths. ADD blend: HDR-safe (SCREEN darkens values > 1). */
const makeBloom = () => {
  const b = new BloomEffect({ blendFunction: BlendFunction.ADD, intensity: 0.5, luminanceThreshold: 1.0, luminanceSmoothing: 0.2, mipmapBlur: true, levels: 6, radius: 0.6 });
  const mip = b.mipmapBlurPass;
  const setSize = mip.setSize.bind(mip);
  mip.setSize = (w: number, h: number) => setSize(Math.round((1920 * w) / Math.max(h, 1)), 1920);
  return b;
};

const fwd = new THREE.Vector3(), fpt = new THREE.Vector3();

const Inner: React.FC<{ id: number }> = ({ id }) => {
  const f = useCurrentFrame();
  const { camera, scene } = useThree();
  const world = useMemo(() => new World(), []);
  const target = useMemo(() => new THREE.Vector3(), []);
  const on = useMemo(toggles, []);
  const fx = useMemo(() => ({
    ink: new InkPass(scene, camera as THREE.PerspectiveCamera),
    lens: new LensBlur({ maxCoC: 24, nearScale: 1.2 }),
    bloom: makeBloom(),
    tone: new ToneMappingEffect({ mode: ToneMappingMode.NEUTRAL }),
    grade: new GradeEffect(GRADES.day, GRADE_STRENGTH.day),
    grain: new GrainEffect({ amount: 0.025, cellPx: 1.5 }), // film grain, OFF by default (inputProps post.grain): the reference measures no grain and it quadruples the file size
  }), [camera, scene]);
  useEffect(() => () => fx.ink.dispose(), [fx]);
  const post = useMemo(() => (
    <EffectComposer multisampling={4}>
      {on.ink ? <primitive object={fx.ink} dispose={null} /> : null}
      {on.lens && on.pre ? <primitive object={fx.lens.pre} dispose={null} /> : null}
      {on.lens ? <primitive object={fx.lens.main} dispose={null} /> : null}
      {on.bloom ? <primitive object={fx.bloom} dispose={null} /> : null}
      <primitive object={fx.tone} dispose={null} />
      {on.grade ? <primitive object={fx.grade} dispose={null} /> : null}
      {on.grain ? <primitive object={fx.grain} dispose={null} /> : null}
    </EffectComposer>
  ), [fx, on]);
  const cam = camera as THREE.PerspectiveCamera;
  target.copy(world.update(id, f, cam, scene));
  noInkFallback(world.root);
  // thin-lens focus: distance along the view axis to the shot's focus point (default: the camera's look target)
  const d = dofAt(f);
  cam.getWorldDirection(fwd);
  fpt.copy(target);
  fx.lens.focus = Math.max(0.3, fpt.sub(cam.position).dot(fwd));
  fx.lens.cInf = d.cInf;
  gradeFor(fx.grade, "day");
  fx.grain.seed = f; // deterministic per frame
  return (
    <>
      <primitive object={world.root} dispose={null} />
      {post}
    </>
  );
};

/** test stills only: inputProps `{ post: { dpr: 0.5 } }` forces the WebGL buffer size (R3F clamps dpr to >= 1 by default) */
const dprOverride = () => (getInputProps() as { post?: { dpr?: number } }).post?.dpr;
const ShotView: React.FC<{ id: number; alpha: number }> = ({ id, alpha }) => (
  <AbsoluteFill style={{ opacity: alpha }}>
    <ThreeCanvas width={1080} height={1920} {...(dprOverride() ? { dpr: dprOverride() } : {})} shadows gl={{ antialias: false, stencil: false, powerPreference: "high-performance", toneMappingExposure: 1.0 }}
      camera={{ fov: 40, near: 0.05, far: 1500 }}>
      <Inner id={id} />
    </ThreeCanvas>
  </AbsoluteFill>
);

// sign and card text is painted on canvases with CapFont: hold the first render until the font is in document.fonts
const fontReady = (() => {
  const h = delayRender("thoughts-font");
  const ff = new FontFace("CapFont", `url(${staticFile("water/InterDisplay-Black.otf")})`);
  return ff.load().then((x) => { (document as any).fonts.add(x); continueRender(h); });
})();

export const ThoughtsShort: React.FC = () => {
  const f = useCurrentFrame();
  const [ok, setOk] = useState(false);
  useEffect(() => { fontReady.then(() => setOk(true)); }, []);
  if (!ok) return <AbsoluteFill style={{ background: "#dfe6f3" }} />;
  return (
    <AbsoluteFill style={{ background: "#dfe6f3" }}>
      {layersAt(f).map((l, i) => (
        <AbsoluteFill key={i ? "over" : "base"} style={{ filter: NIGHT.has(l.id) ? "brightness(0.6) saturate(0.85) hue-rotate(-6deg) contrast(1.05)" : undefined }}>
          <ShotView id={l.id} alpha={l.alpha} />
        </AbsoluteFill>
      ))}
      <DayStickers f={f} />
    </AbsoluteFill>
  );
};

/** "DAY 1/2/3" sticker at the frame top (inside the 3:4 band, above the captions) */
const INKC = "#160b14";
const outline = (r: number) => [...Array.from({ length: 32 }, (_, i) => { const a = (i / 32) * Math.PI * 2; return `${(r * Math.cos(a)).toFixed(1)}px ${(r * Math.sin(a)).toFixed(1)}px 0 ${INKC}`; }),
  `0 ${r + 5}px 0 ${INKC}`, `0 ${r + 12}px 28px rgba(0,0,0,0.45)`].join(",");
const DayStickers: React.FC<{ f: number }> = ({ f }) => {
  const d = DAYS.find(([, a, b]) => f >= a * FPS && f < b * FPS);
  if (!d) return null;
  const [label, a, b] = d, fa = Math.round(a * FPS), fb = Math.round(b * FPS);
  const sIn = spring({ frame: f - fa, fps: FPS, config: { damping: 9, stiffness: 180 } });
  const sOut = 1 - Math.min(1, Math.max(0, (f - (fb - 6)) / 6));
  return (
    <AbsoluteFill style={{ alignItems: "center", paddingTop: 300 }}>
      <div style={{ fontFamily: "CapFont", fontWeight: 900, fontSize: 150, color: "#ffd84d", letterSpacing: -2, textShadow: outline(16),
        transform: `scale(${sIn * sOut}) rotate(-4deg)` }}>{label}</div>
    </AbsoluteFill>
  );
};
