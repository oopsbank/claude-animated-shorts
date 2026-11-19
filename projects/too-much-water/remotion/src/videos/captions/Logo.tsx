// Channel avatar: the deadpan water-drop mascot, round-crop safe, no text (avatars show at 40-100 px).
import React, { useCallback } from "react";
import { AbsoluteFill, getInputProps, staticFile, delayRender, continueRender } from "remotion";
import { Pen } from "../bridge/toon";
import { drop } from "../water/chars";

const BG: Record<string, [string, string]> = { yellow: ["#ffd84d", "#ffb02e"], pink: ["#ff9cc8", "#e65f9a"], navy: ["#2b2f5c", "#161837"] };
const font = new FontFace("CapFont", `url(${staticFile("water/InterDisplay-Black.otf")})`);
const h = delayRender("font");
font.load().then((f) => { (document as any).fonts.add(f); continueRender(h); });

export const Logo: React.FC = () => {
  const { bg = "yellow", expr = "neutral", mark = "?" } = getInputProps() as any;
  const draw = useCallback((cv: HTMLCanvasElement | null) => {
    if (!cv) return;
    const g = cv.getContext("2d")!, S = 1080;
    g.clearRect(0, 0, S, S);
    const [a, b] = BG[bg] ?? BG.yellow, gr = g.createRadialGradient(S * 0.4, S * 0.35, 50, S / 2, S / 2, S * 0.72);
    gr.addColorStop(0, a); gr.addColorStop(1, b);
    g.fillStyle = gr; g.fillRect(0, 0, S, S);
    // soft rays behind the mascot
    g.save(); g.translate(S / 2, S * 0.55); g.fillStyle = "rgba(255,255,255,0.13)";
    for (let i = 0; i < 12; i++) { g.rotate(Math.PI / 6); g.beginPath(); g.moveTo(0, 0); g.lineTo(-90, -900); g.lineTo(90, -900); g.fill(); }
    g.restore();
    // mascot: design space 600x1000, drop body spans ~x 150-450, y 440-930
    g.save(); g.translate(S / 2 - 300 * 2.05 - 40, S * 0.6 - 700 * 2.05); g.scale(2.05, 2.05);
    drop(new Pen(g), expr, 0, 0, 0);
    g.restore();
    // a big inked question mark, tilted
    g.save(); g.translate(S * 0.75, S * 0.25); g.rotate(0.22);
    g.font = "900 290px CapFont"; g.textAlign = "center"; g.textBaseline = "middle";
    g.lineJoin = "round"; g.lineWidth = 38; g.strokeStyle = "#160b14"; g.strokeText(mark, 0, 12); g.strokeText(mark, 0, 0);
    g.fillStyle = "#ffffff"; g.fillText(mark, 0, 0);
    g.restore();
  }, [bg, expr, mark]);
  return <AbsoluteFill><canvas ref={draw} width={1080} height={1080} style={{ width: "100%", height: "100%" }} /></AbsoluteFill>;
};
