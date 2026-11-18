import React from "react";
import { Composition } from "remotion";
import { BridgeShort, BRIDGE_FRAMES } from "./videos/bridge/Bridge";
import { WaterShort, WATER_FRAMES } from "./videos/water/Water";
export const Root: React.FC = () => (
  <>
    <Composition id="BridgeShort" component={BridgeShort} durationInFrames={BRIDGE_FRAMES} fps={30} width={1080} height={1920} />
    <Composition id="WaterShort" component={WaterShort} durationInFrames={WATER_FRAMES} fps={30} width={1080} height={1920} />
  </>
);
