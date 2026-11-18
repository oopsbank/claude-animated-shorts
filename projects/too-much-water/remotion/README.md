# Remotion project for "What if you drank too much water?"

Layout expected by the code (a Remotion project root):
- `src/videos/bridge/` = copy of `templates/bridge/` (shared look: ink, lens blur, grade, toon cast, build helpers)
- `src/videos/water/`  = this short (story.ts timeline, world.ts sets, chars.ts cast, Water.tsx composition)
- `src/Root.tsx` registers `WaterShort` (1080x1920, 30 fps, 1660 frames)

Setup: `npm install` with the pinned versions in package.json (three 0.176 / postprocessing 6.37 / @react-three/postprocessing 3.0.4;
newer three renders blank frames through the EffectComposer).

Stills: `COMP=WaterShort node scripts/bridge-stills.mjs out/x_ 40,290,740 0.5`
(edit `browserExecutable` / `gl` in the script for your machine: "angle" on a GPU, "swangle" on CPU).

Final: `npx remotion render src/index.ts WaterShort out/video.mp4 --codec h264 --crf 16 --timeout=300000`
then mux `audio/mix.wav` with `-map 0:v:0 -map 1:a:0`.
