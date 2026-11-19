// Cover / thumbnail for the water short, same type as the captions (Inter Display Black, thick plum outline).
// Text stays inside the centre 3:4 band (rows 240-1680) so the TikTok profile grid crop keeps it.
import React from "react";
import { AbsoluteFill, Img, staticFile, getInputProps } from "remotion";

const INKC = "#160b14";
const outline = (r: number) => [...Array.from({ length: 32 }, (_, i) => { const a = (i / 32) * Math.PI * 2; return `${(r * Math.cos(a)).toFixed(1)}px ${(r * Math.sin(a)).toFixed(1)}px 0 ${INKC}`; }),
  `0 ${r + 6}px 0 ${INKC}`, `0 ${r + 14}px 34px rgba(0,0,0,0.5)`].join(",");
const T: React.FC<{ size: number; color: string; rot?: number; children: React.ReactNode }> = ({ size, color, rot = 0, children }) => (
  <div style={{ fontFamily: "CapFont", fontWeight: 900, fontSize: size, lineHeight: 0.98, letterSpacing: -2, color, textTransform: "uppercase",
    textShadow: outline(Math.round(size / 9)), transform: `rotate(${rot}deg)`, textAlign: "center" }}>{children}</div>
);

export const WaterThumb: React.FC = () => {
  const v = (getInputProps() as any).v ?? "brain";
  const brain = v === "brain";
  return (
    <AbsoluteFill style={{ backgroundColor: "black", overflow: "hidden" }}>
      <style>{`@font-face{font-family:CapFont;src:url(${staticFile("water/InterDisplay-Black.otf")}) format("opentype");font-weight:900}`}</style>
      <Img src={staticFile(brain ? "water/thumb_brain.jpg" : "water/thumb_glass.jpg")}
        style={{ width: "100%", height: "100%", objectFit: "cover", transform: brain ? "scale(1.4) translateY(-6%)" : "scale(1.25) translate(6%, -6%)", transformOrigin: "50% 70%" }} />
      <AbsoluteFill style={{ background: "linear-gradient(180deg, rgba(10,4,12,0.55) 0%, rgba(10,4,12,0) 42%)" }} />
      <AbsoluteFill style={{ alignItems: "center", paddingTop: 300, gap: 18 }}>
        {brain ? (<>
          <T size={92} color="#ffffff">What if you drank</T>
          <T size={150} color="#5fd0ff" rot={-2}>too much</T>
          <T size={190} color="#5fd0ff" rot={-2}>water?</T>
        </>) : (<>
          <T size={96} color="#ffffff">The deadliest drink</T>
          <T size={96} color="#ffffff">in this bar is…</T>
          <T size={200} color="#5fd0ff" rot={-3}>water</T>
        </>)}
      </AbsoluteFill>
    </AbsoluteFill>
  );
};
