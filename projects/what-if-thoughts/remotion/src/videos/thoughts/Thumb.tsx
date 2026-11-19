// Cover / thumbnail for the thoughts short, same type as the water cover (Inter Display Black, thick outline).
// Text stays inside the centre 3:4 band (rows 240-1680) so the profile grid crop keeps it.
import React from "react";
import { AbsoluteFill, Img, staticFile } from "remotion";

const INKC = "#160b14";
const outline = (r: number) => [...Array.from({ length: 32 }, (_, i) => { const a = (i / 32) * Math.PI * 2; return `${(r * Math.cos(a)).toFixed(1)}px ${(r * Math.sin(a)).toFixed(1)}px 0 ${INKC}`; }),
  `0 ${r + 6}px 0 ${INKC}`, `0 ${r + 14}px 34px rgba(0,0,0,0.5)`].join(",");
const T: React.FC<{ size: number; color: string; rot?: number; children: React.ReactNode }> = ({ size, color, rot = 0, children }) => (
  <div style={{ fontFamily: "CapFont", fontWeight: 900, fontSize: size, lineHeight: 0.98, letterSpacing: -2, color, textTransform: "uppercase",
    textShadow: outline(Math.round(size / 9)), transform: `rotate(${rot}deg)`, textAlign: "center" }}>{children}</div>
);

export const ThoughtsThumb: React.FC = () => (
  <AbsoluteFill style={{ backgroundColor: "black", overflow: "hidden" }}>
    <style>{`@font-face{font-family:CapFont;src:url(${staticFile("water/InterDisplay-Black.otf")}) format("opentype");font-weight:900}`}</style>
    <Img src={staticFile("thoughts/thumb.jpg")} style={{ width: "100%", height: "100%", objectFit: "cover", transform: "scale(1.15) translate(-4%, 9%)", transformOrigin: "60% 70%" }} />
    <AbsoluteFill style={{ background: "linear-gradient(180deg, rgba(10,4,12,0.6) 0%, rgba(10,4,12,0) 42%)" }} />
    <AbsoluteFill style={{ alignItems: "center", paddingTop: 260, gap: 12 }}>
      <T size={86} color="#ffffff">What if you could</T>
      <T size={86} color="#ffffff">hear everyone's</T>
      <T size={150} color="#ffd23d" rot={-3}>thoughts?</T>
    </AbsoluteFill>
  </AbsoluteFill>
);
