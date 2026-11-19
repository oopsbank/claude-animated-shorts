// Cover for the Lake Nyos short, same type as the water thumbnail.
import React from "react";
import { AbsoluteFill, Img, staticFile, getInputProps } from "remotion";

const INKC = "#0b0a1a";
const outline = (r: number) => [...Array.from({ length: 32 }, (_, i) => { const a = (i / 32) * Math.PI * 2; return `${(r * Math.cos(a)).toFixed(1)}px ${(r * Math.sin(a)).toFixed(1)}px 0 ${INKC}`; }),
  `0 ${r + 6}px 0 ${INKC}`, `0 ${r + 14}px 34px rgba(0,0,0,0.5)`].join(",");
const T: React.FC<{ size: number; color: string; rot?: number; children: React.ReactNode }> = ({ size, color, rot = 0, children }) => (
  <div style={{ fontFamily: "CapFont", fontWeight: 900, fontSize: size, lineHeight: 0.98, letterSpacing: -2, color, textTransform: "uppercase",
    textShadow: outline(Math.round(size / 9)), transform: `rotate(${rot}deg)`, textAlign: "center" }}>{children}</div>
);

export const NyosThumb: React.FC = () => {
  const red = (getInputProps() as any).v === "red";
  return (
    <AbsoluteFill style={{ backgroundColor: "black", overflow: "hidden" }}>
      <style>{`@font-face{font-family:CapFont;src:url(${staticFile("water/InterDisplay-Black.otf")}) format("opentype");font-weight:900}`}</style>
      <Img src={staticFile(red ? "nyos/thumb_red.jpg" : "nyos/thumb_erupt.jpg")}
        style={{ width: "100%", height: "100%", objectFit: "cover", transform: red ? "scale(1.1)" : "scale(1.15) translateY(7%)", transformOrigin: "50% 60%" }} />
      <AbsoluteFill style={{ background: "linear-gradient(180deg, rgba(4,4,16,0.7) 0%, rgba(4,4,16,0) 45%)" }} />
      <AbsoluteFill style={{ alignItems: "center", paddingTop: 270, gap: 16 }}>
        <T size={100} color="#ffffff">The lake that</T>
        <T size={190} color="#ff4a3d" rot={-2}>killed</T>
        <T size={124} color="#ffb03a" rot={-2}>1,700 people</T>
        <T size={96} color="#ffffff">in one night</T>
      </AbsoluteFill>
    </AbsoluteFill>
  );
};
