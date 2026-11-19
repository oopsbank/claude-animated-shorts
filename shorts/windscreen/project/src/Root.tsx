import React from "react";
import { Composition } from "remotion";
import { PlaneShort, PLANE_FRAMES } from "./videos/plane/Plane";
import { PlaneSubs } from "./videos/plane/Subs";
export const Root: React.FC = () => (
  <>
    <Composition id="PlaneShort" component={PlaneShort} durationInFrames={PLANE_FRAMES} fps={30} width={1080} height={1920} />
    <Composition id="PlaneSubs" component={PlaneSubs} durationInFrames={PLANE_FRAMES} fps={30} width={1080} height={1920} />
  </>
);
