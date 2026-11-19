// Cover for "What If Night Never Came Again?", same type as the other covers.
import React from "react";
import { AbsoluteFill, Img, staticFile } from "remotion";

const INKC = "#120a1c";
const outline = (r: number) => [...Array.from({ length: 32 }, (_, i) => { const a = (i / 32) * Math.PI * 2; return `${(r * Math.cos(a)).toFixed(1)}px ${(r * Math.sin(a)).toFixed(1)}px 0 ${INKC}`; }),
  `0 ${r + 6}px 0 ${INKC}`, `0 ${r + 14}px 34px rgba(0,0,0,0.5)`].join(",");
const T: React.FC<{ size: number; color: string; rot?: number; children: React.ReactNode }> = ({ size, color, rot = 0, children }) => (
  <div style={{ fontFamily: "CapFont", fontWeight: 900, fontSize: size, lineHeight: 0.98, letterSpacing: -2, color, textTransform: "uppercase",
    textShadow: outline(Math.round(size / 9)), transform: `rotate(${rot}deg)`, textAlign: "center" }}>{children}</div>
);

export const NoNightThumb: React.FC = () => (
  <AbsoluteFill style={{ backgroundColor: "black", overflow: "hidden" }}>
    <style>{`@font-face{font-family:CapFont;src:url(${staticFile("water/InterDisplay-Black.otf")}) format("opentype");font-weight:900}`}</style>
    <Img src={staticFile("nonight/thumb_bg.jpg")} style={{ width: "100%", height: "100%", objectFit: "cover", transform: "scale(1.1) translateY(3%)", transformOrigin: "50% 60%" }} />
    <AbsoluteFill style={{ background: "linear-gradient(180deg, rgba(8,4,20,0.55) 0%, rgba(8,4,20,0) 45%)" }} />
    <AbsoluteFill style={{ alignItems: "center", paddingTop: 270, gap: 16 }}>
      <T size={110} color="#ffffff">What if</T>
      <T size={200} color="#9fb4ff" rot={-2}>night</T>
      <T size={150} color="#ff5a4d" rot={-2}>never</T>
      <T size={110} color="#ffffff">came again?</T>
    </AbsoluteFill>
  </AbsoluteFill>
);
