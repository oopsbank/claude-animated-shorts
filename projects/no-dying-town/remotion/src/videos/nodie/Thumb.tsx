// Cover / thumbnail for the no-dying-town short, same type as the water cover (Inter Display Black, thick outline).
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

export const NoDieThumb: React.FC = () => (
  <AbsoluteFill style={{ backgroundColor: "black", overflow: "hidden" }}>
    <style>{`@font-face{font-family:CapFont;src:url(${staticFile("water/InterDisplay-Black.otf")}) format("opentype");font-weight:900}`}</style>
    <Img src={staticFile("nodie/thumb.jpg")} style={{ width: "100%", height: "100%", objectFit: "cover", transform: "scale(1.3) translate(-3%, 10%)", transformOrigin: "60% 60%" }} />
    <AbsoluteFill style={{ background: "linear-gradient(180deg, rgba(10,4,12,0.55) 0%, rgba(10,4,12,0) 40%)" }} />
    <AbsoluteFill style={{ alignItems: "center", paddingTop: 250, gap: 10 }}>
      <T size={84} color="#ffffff">The town where</T>
      <T size={84} color="#ffffff">you're</T>
      <T size={124} color="#ff4a3d" rot={-3}>not allowed</T>
      <T size={170} color="#ff4a3d" rot={-3}>to die</T>
    </AbsoluteFill>
  </AbsoluteFill>
);
