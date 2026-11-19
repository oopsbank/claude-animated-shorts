import React from "react";
import { Composition } from "remotion";
import { PauseShort, PAUSE_FRAMES } from "./videos/pause/Pause";
import { PauseSubs } from "./videos/pause/Subs";
export const Root: React.FC = () => (
  <>
    <Composition id="PauseShort" component={PauseShort} durationInFrames={PAUSE_FRAMES} fps={30} width={1080} height={1920} />
    <Composition id="PauseSubs" component={PauseSubs} durationInFrames={PAUSE_FRAMES} fps={30} width={1080} height={1920} />
  </>
);
