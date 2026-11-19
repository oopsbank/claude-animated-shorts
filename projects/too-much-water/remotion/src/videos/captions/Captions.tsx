// Animated English word captions over the finished water short. Timed to voice/words.json (ElevenLabs alignment).
// Chunks of 1-3 words pop in on a spring; the spoken word turns yellow and bumps; key words carry their own colour.
// The real 2007 case (39.0-45.7 s) uses a calm style: plain white, soft fade, no pop, matching the quiet beat.
import React from "react";
import { AbsoluteFill, OffthreadVideo, staticFile, useCurrentFrame, useVideoConfig, spring, interpolate } from "remotion";
import WORDS from "./words.json";

type W = { word: string; start: number; end: number };
const words = WORDS as W[];
const QUIET: [number, number] = [39.0, 45.7];
const KEY: Record<string, string> = {
  water: "#5fd0ff", whiskey: "#ffb347", dangerous: "#ff5a5a", salt: "#ffffff", salty: "#ffffff", kidneys: "#ff8a7a",
  brain: "#ff9cc8", bone: "#e8e0c8", sponge: "#ffe066", queue: "#5fd0ff", drink: "#5fd0ff", army: "#9bd36a",
};
const clean = (s: string) => s.toLowerCase().replace(/[^a-z0-9.]/g, "").replace(/\.$/, "");

type Chunk = { w: W[]; a: number; b: number };
const chunks: Chunk[] = [];
{
  let cur: W[] = [];
  const flush = () => { if (cur.length) chunks.push({ w: cur, a: cur[0].start, b: cur[cur.length - 1].end }); cur = []; };
  words.forEach((w, i) => {
    cur.push(w);
    const nx = words[i + 1], chars = cur.map((x) => x.word).join(" ").length;
    if (!nx || /[.,?!:]$/.test(w.word) || cur.length >= 3 || chars >= 13 || nx.start - w.end > 0.25 || (nx.word.length + chars) > 16) flush();
  });
  // each chunk stays until the next one starts (or 0.45 s after its last word in a pause)
  chunks.forEach((c, i) => { const n = chunks[i + 1]; c.b = n ? Math.min(n.a, c.b + 0.45) : c.b + 0.6; });
}

const OUTLINE = [...Array.from({ length: 24 }, (_, i) => { const a = (i / 24) * Math.PI * 2; return `${(10 * Math.cos(a)).toFixed(1)}px ${(10 * Math.sin(a)).toFixed(1)}px 0 #160b14`; }),
  "0 12px 0 #160b14", "0 18px 28px rgba(0,0,0,0.45)"].join(",");
const fontFace = `@font-face{font-family:CapFont;src:url(${staticFile("water/InterDisplay-Black.otf")}) format("opentype");font-weight:900}`;

export const CaptionLayer: React.FC = () => {
  const f = useCurrentFrame(), { fps } = useVideoConfig(), t = f / fps;
  const c = chunks.find((x) => t >= x.a - 0.05 && t < x.b);
  if (!c) return null;
  const quiet = c.a >= QUIET[0] && c.a < QUIET[1];
  const f0 = Math.round((c.a - 0.05) * fps), age = f - f0;
  const pop = spring({ frame: age, fps, config: { damping: 11, stiffness: 220, mass: 0.6 } });
  const scale = quiet ? 1 : interpolate(pop, [0, 1], [0.55, 1]);
  const lift = quiet ? 0 : interpolate(pop, [0, 1], [40, 0]);
  const opacity = quiet ? interpolate(age, [0, 6], [0, 1], { extrapolateRight: "clamp" }) : Math.min(1, age / 2 + 0.3);
  const tilt = quiet ? 0 : ((chunks.indexOf(c) % 2) ? 1.5 : -1.5) * (1 - pop);
  return (
    <AbsoluteFill style={{ justifyContent: "flex-start", alignItems: "center" }}>
      <div style={{ position: "absolute", top: "61%", width: "90%", display: "flex", flexWrap: "wrap", justifyContent: "center", columnGap: "0.6em", rowGap: 6, transform: `translateY(${lift}px) scale(${scale}) rotate(${tilt}deg)`, opacity,
        fontFamily: "CapFont", fontWeight: 900, fontSize: quiet ? 76 : 92, lineHeight: 1.08, letterSpacing: -1, textTransform: "uppercase" }}>
        {c.w.map((w, i) => {
          const on = t >= w.start - 0.03, speaking = on && t < w.end + 0.06;
          const k = KEY[clean(w.word)];
          const bump = quiet || !on ? 0 : spring({ frame: f - Math.round((w.start - 0.03) * fps), fps, config: { damping: 9, stiffness: 300, mass: 0.5 } });
          const color = quiet ? "#ffffff" : k ? k : speaking ? "#ffe14d" : "#ffffff";
          return (
            <span key={i} style={{ position: "relative", display: "inline-block", opacity: quiet && !on ? 0.45 : 1,
              transform: `scale(${1 + 0.1 * bump * (speaking ? 1 : 0.4)})` }}>
              <span style={{ position: "absolute", left: 0, top: 0, color: "#160b14", textShadow: OUTLINE }}>{w.word.replace(/[.,:]$/, "")}</span>
              <span style={{ position: "relative", color }}>{w.word.replace(/[.,:]$/, "")}</span>
            </span>
          );
        })}
      </div>
    </AbsoluteFill>
  );
};

export const CaptionedWater: React.FC = () => (
  <AbsoluteFill style={{ backgroundColor: "black" }}>
    <style>{fontFace}</style>
    <OffthreadVideo src={staticFile("water/base.mp4")} />
    <CaptionLayer />
  </AbsoluteFill>
);
