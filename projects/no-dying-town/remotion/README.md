# Remotion project for "The Town Where You're Not Allowed to Die"

Same layout as `projects/too-much-water/remotion` (see its README):
- `src/videos/bridge/` = copy of `templates/bridge/`
- `src/videos/water/` + `src/videos/captions/` = from `projects/too-much-water/remotion/src` (Root.tsx still registers them)
- `src/videos/nodie/` = this short: `story.ts` timeline/cameras, `world.ts` sets, `chars.ts` cast + printed graphics,
  `Town.tsx` composition `NoDieShort` (1080x1920, 30 fps, 1665 frames), `Captions.tsx` `NoDieCaptioned`
- `public/water/InterDisplay-Black.otf` (Inter 4.1, rsms/inter release) for sign text and captions

Stills: `COMP=NoDieShort node scripts/bridge-stills.mjs out/x_ 60,300 0.5`
Frames (CPU, ~2 h): `./scripts/render_nd.sh` (JPEG chunks in out/nd), then encode with `../audio/mix.wav`.
