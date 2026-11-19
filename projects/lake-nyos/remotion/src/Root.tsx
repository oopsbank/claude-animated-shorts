import React from "react";
import { Composition } from "remotion";
import { BridgeShort, BRIDGE_FRAMES } from "./videos/bridge/Bridge";
import { NyosShort, NYOS_FRAMES } from "./videos/nyos/Nyos";
import { CaptionedNyos } from "./videos/captions/CaptionsNyos";
import { Logo } from "./videos/captions/Logo";
import { WaterThumb } from "./videos/captions/Thumb";
import { CaptionedWater } from "./videos/captions/Captions";
import { WaterShort, WATER_FRAMES } from "./videos/water/Water";
export const Root: React.FC = () => (
  <>
    <Composition id="BridgeShort" component={BridgeShort} durationInFrames={BRIDGE_FRAMES} fps={30} width={1080} height={1920} />
    <Composition id="WaterShort" component={WaterShort} durationInFrames={WATER_FRAMES} fps={30} width={1080} height={1920} />
    <Composition id="WaterCaptioned" component={CaptionedWater} durationInFrames={WATER_FRAMES} fps={30} width={1080} height={1920} />
    <Composition id="WaterThumb" component={WaterThumb} durationInFrames={1} fps={30} width={1080} height={1920} />
    <Composition id="Logo" component={Logo} durationInFrames={1} fps={30} width={1080} height={1080} />
    <Composition id="NyosShort" component={NyosShort} durationInFrames={NYOS_FRAMES} fps={30} width={1080} height={1920} />
    <Composition id="NyosCaptioned" component={CaptionedNyos} durationInFrames={NYOS_FRAMES} fps={30} width={1080} height={1920} />
  </>
);
