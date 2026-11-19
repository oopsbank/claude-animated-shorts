# What If You Could Hear Everyone's Thoughts?

A "what if" short (made-up, no sources needed). Day one is fun, day two gets weird, day three is unbearable; the hero
runs to the woods for silence and finds the squirrels are even louder. Punchline: people were the quiet ones.

- Length: 64.5 s base (voice 63.8 s + tail), finals 64.6 s with the 3-frame cover in front. 1080x1920, 30 fps.
- Voice: ElevenLabs George, see `voice/`.
- Look: same 3D cartoon world as the channel's other shorts (flat ink characters in a toon-lit three.js world),
  thought bubbles as camera-facing cards, "DAY 1/2/3" stickers in the frame top.
- Audio: `audio/audio.py` (original music + synthesized SFX), -14 LUFS, true peak <= -1 dBTP.

## Shots
| # | time (s) | set | beat |
|---|---|---|---|
| 1 | 0.0-3.1 | bedroom | wake up, the first thoughts pop in |
| 2 | 3.1-6.9 | cafe | DAY 1: the barista thinks the pink haircut is "brave" |
| 3 | 6.9-10.0 | office | boss thinks about tacos, during the meeting |
| 4 | 10.0-14.2 | park | the dog: BALL, BALL, BALL |
| 5 | 14.2-20.1 | classroom | the smart kid thinks every answer, really loudly |
| 6 | 20.1-24.0 | kitchen | DAY 2: friend thinks the cooking is terrible |
| 7 | 24.0-27.3 | kitchen | mom still thinks about the vase (age 8) |
| 8 | 27.3-31.6 | bus | everyone hums the same song in their heads |
| 9 | 31.6-40.2 | city | DAY 3: 8,000,000 people thinking at once |
| 10 | 40.2-43.2 | bedroom, night | can't sleep, can't hear own thoughts |
| 11 | 43.2-48.3 | woods | run away from people |
| 12 | 48.3-50.8 | woods | silence, peace, bliss |
| 13 | 50.8-53.7 | woods | a squirrel: "can you hear us?" |
| 14 | 53.7-61.9 | woods | every squirrel: "where did I bury my nuts?" |
| 15 | 61.9-64.5 | city | people were the quiet ones |

## Final
- `final/what-if-thoughts_captioned_1080x1920.mp4`: 1938 frames, 64.6 s, 30 fps. The first 3 frames are the thumbnail, and the audio is delayed by 0.1 s. Loudness is −14.1 LUFS, true peak −1.2 dBTP.
- `final/what-if-thoughts_thumbnail_1080x1920.png`
- `remotion/`: the scene source (src/videos/thoughts, Root.tsx, render/encode scripts). It drops into the no-dying-town Remotion project.
