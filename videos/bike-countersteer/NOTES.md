# Why Your Bike Steers Backwards First: draft v1 (engine render, 2026-11-20)

`draft_v1.mp4` is 1080x1920, 30 fps, exactly 1921 frames (64.033 s), with `audio/bike-countersteer/mix.wav` muxed in. It is **a draft for the Director's review. Not for publishing.**

- **Inputs:**
  - `scripts/bike-countersteer/shots.json` (18 shots);
  - `audio/bike-countersteer/words.json`;
  - plates from `blender/sets/track` (final) and `blender/sets/village` (final);
  - riders from `characters/scripts/bikes.py`;
  - props from bean.py;
  - effects from `fx/fx.py`.
- **Engine:** `claude/area-engine` at commit a0b7b82. Command:
  `ENGINE_STANDIN=0 .venv/bin/python engine/render_video.py scripts/bike-countersteer/shots.json audio/bike-countersteer/words.json OUT --audio audio/bike-countersteer/mix.wav` (about 8 minutes on 4 CPUs).
- **Automatic QA** (`qa/engine_qa_draft_v1.md`): all hard checks pass.
  - no black, white or frozen spans of 12 frames or more;
  - no character clipped at the frame edge;
  - feet on the ground line;
  - planted feet;
  - all 32 beats land 0-3 frames before their word;
  - length and format.
- **Contact sheet:** `qa/contact_every_2s_draft_v1.jpg`.

## Known issues
1. **Frame stats are a warning:** only 6 of 65 sampled frames meet the reference value targets. Most fail on mean luminance below 0.40, and some on saturation or edge density. This comes from the plates, so it belongs to sets.
2. **Two-shots on `pit_med`** (s05, s10, s16, s18): at the script's `x` values the characters overlapped, so the engine spread them apart. In s05, s10 and s16 it also stepped them back to 0.86x in depth. Scripts may want to set those positions.
3. **Countersteer:** `shots.json` has no `steer` values, so the engine adds an automatic countersteer flick before every lean of more than 5°. Please check that it reads clearly (s01, s12, s13, s15, s17).
4. **s14 (`pit_ots`):** the near instructor is seen from behind at 1.7x. Check that the broom on the palm reads clearly.
5. **Not reviewed:** no independent reviewer has watched this full draft yet. The engine's earlier test clip scored motion 7, acting 6, readability 7, pacing 7 and look 6.
6. **Blinks:** half-closed blink frames still use an engine overlay; bean.py has no half-lid option.
