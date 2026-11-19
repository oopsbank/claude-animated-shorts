// Animated English subtitles (added on request, overriding the skill's no-caption default): a transparent 1080x1920
// layer composited over the finished film. Word timings come from the ElevenLabs alignment (voice/words.json).
// Each phrase (<= 3 words, broken at punctuation and pauses) springs in; the word being spoken pops up and turns
// gold; the phrase drops away when the next one arrives.
import React from "react";
import { AbsoluteFill, continueRender, delayRender, interpolate, spring, staticFile, useCurrentFrame, useVideoConfig } from "remotion";
import WORDS from "./words.json";

type W = { w: string; s: number; e: number };
type Chunk = { words: W[]; s: number; e: number };

const MAX_WORDS = 3, MAX_CHARS = 15, GAP = 0.32, TAIL = 0.45;

const chunks: Chunk[] = (() => {
  const out: Chunk[] = [];
  let cur: W[] = [];
  const flush = () => { if (cur.length) out.push({ words: cur, s: cur[0].s, e: cur[cur.length - 1].e }); cur = []; };
  (WORDS as W[]).forEach((w, i, all) => {
    const len = cur.map((c) => c.w).join(" ").length + w.w.length + 1;
    if (cur.length && (cur.length >= MAX_WORDS || len > MAX_CHARS || w.s - cur[cur.length - 1].e > GAP)) flush();
    cur.push(w);
    const next = all[i + 1];
    if (/[.,!?;:]$/.test(w.w) || !next) flush();
  });
  // hold each phrase until the next one starts (or a short tail after its last word if there is a pause)
  out.forEach((c, i) => { const n = out[i + 1]; c.e = n ? Math.min(n.s, c.e + TAIL) : c.e + TAIL; });
  return out;
})();

const GOLD = "#ffc531", INK = "#2a1407";
const FONT = "SubsInter";
// a solid outline from a ring of hard shadows (WebKit text-stroke eats into the glyphs), then a drop shadow
const RING = Array.from({ length: 24 }, (_, i) => { const a = (i / 24) * 2 * Math.PI; return `${(10 * Math.cos(a)).toFixed(1)}px ${(10 * Math.sin(a)).toFixed(1)}px 0 ${INK}`; }).join(", ");

const useFont = () => {
  const [h] = React.useState(() => delayRender("font"));
  React.useEffect(() => {
    const f = new FontFace(FONT, `url(${staticFile("Inter-ExtraBold.otf")})`);
    f.load().then((ff) => { (document.fonts as unknown as Set<FontFace>).add(ff); continueRender(h); });
  }, [h]);
};

export const PauseSubs: React.FC = () => {
  useFont();
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const t = frame / fps;
  const c = chunks.find((k) => t >= k.s - 0.03 && t < k.e);
  if (!c) return <AbsoluteFill />;
  const f0 = Math.round((c.s - 0.03) * fps);
  const inK = spring({ frame: frame - f0, fps, config: { damping: 11, stiffness: 220, mass: 0.6 } });
  const outK = interpolate(t, [c.e - 0.1, c.e], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const tilt = (chunks.indexOf(c) % 2 ? 1 : -1) * 1.6 * (1 - inK);
  return (
    <AbsoluteFill style={{ justifyContent: "flex-start", alignItems: "center" }}>
      <div style={{
        position: "absolute", top: 1260, width: 980, display: "flex", flexWrap: "wrap", justifyContent: "center",
        transform: `translateY(${(1 - inK) * 40 + outK * 18}px) scale(${0.7 + 0.3 * inK - 0.12 * outK}) rotate(${tilt}deg)`,
        opacity: Math.min(1, inK * 1.6) * (1 - outK),
      }}>
        {c.words.map((w, i) => {
          const fw = Math.round(w.s * fps);
          const pop = spring({ frame: frame - fw, fps, config: { damping: 9, stiffness: 260, mass: 0.5 } });
          const spoken = t >= w.s - 0.02;
          const active = t >= w.s - 0.02 && t < Math.max(w.e, w.s + 0.18);
          const lift = active ? pop : spoken ? 1 : 0;
          const hit = frame >= fw ? Math.max(0, 1 - (frame - fw) / 8) : 0; // brief overshoot on the beat
          return (
            <span key={i} style={{
              fontFamily: FONT, fontSize: 112, lineHeight: 1.2, letterSpacing: 0, margin: "0 18px",
              color: active ? GOLD : "#fffaf0",
              textShadow: `${RING}, 0 12px 0 ${INK}, 0 18px 26px rgba(0,0,0,0.45)`,
              display: "inline-block",
              transform: `translateY(${-14 * (active ? pop : 0)}px) scale(${1 + (active ? 0.12 * hit + 0.06 : 0) * Math.min(1, lift)})`,
            }}>{w.w}</span>
          );
        })}
      </div>
    </AbsoluteFill>
  );
};
