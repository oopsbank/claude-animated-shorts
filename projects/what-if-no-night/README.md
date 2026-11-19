# What If Night Never Came Again?

Pure "what if" short (no sources needed), about 62.6 s, 1080x1920, 30 fps. Built on the bridge / Lake Nyos look
(flat bean characters in a 3D toon world, ink pass, lens blur, bloom, grade).

- `voice/`: ElevenLabs George (eleven_multilingual_v2, stability 0.6, similarity 0.75, speed 1.15), `words.json` from /with-timestamps.
- `audio/audio.py`: original score and SFX, voice placed at 0.25 s; `mix.wav` at -14 LUFS.
- `remotion/src/videos/nonight/`: story (shots, cameras, clocks), world (village, crater lake, hut, globe), chars.
- `remotion/scripts/encode_nonight.sh`: frames -> scene mp4 -> captioned mp4 -> both with the cover as the first 3 frames.
- `final/`: finished videos and cover.

These files live in the shared scratch Remotion project (`src/videos/bridge` etc. come from the bridge short).
