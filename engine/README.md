# Engine (🕺 Animator)

`shots.json` + `words.json` -> frames -> mp4 (picture only). The contracts are in `PIPELINE.md`.

```
.venv/bin/python engine/render_video.py scripts/<slug>/shots.json audio/<slug>/words.json out/<slug> [--plates DIR] [--frames A:B[:step]] [--workers 4] [--audio voice.wav] [--png]
.venv/bin/python engine/qa.py out/<slug> --video out/<slug>/video.mp4          # QA.md > engine and video; writes out/<slug>/qa/
.venv/bin/python engine/fake_words.py scripts/<slug>/shots.json words.json      # stand-in timings at 3.7 words/s
.venv/bin/python engine/test/make_test.py                                       # 19 s stand-in test (engine/test/bike_standin)
```

The output folder gets `frames/f_NNNNN.jpg`, `video.mp4`, and `track.json`. The track holds per-frame character feet, bboxes, poses, mouths, lids and the camera, plus every beat's landing frame. `qa.py` reads it.

## Files
- `anim.py` holds the pure timing and motion maths:
  - word -> shot spans: shot k starts 2 f before its first word;
  - beats, staged arm transitions, blinks, sustained leans and hop travel;
  - the camera.
- `rig.py` wraps `characters/scripts/bean.py`:
  - hi-res cards come from bean's 4x canvas, with no upscaling blur in medium shots;
  - cards are cached per worker;
  - lip sync (letters -> visemes) and blinks use bean's `mouth=` / `lid=` when they exist. Until then they use stand-in overlays that erase the feature (an inpainted skin patch, no seam) and redraw it.
- `render_video.py` handles plates, compositing (tint, contact shadow, feet re-planted after a lean), FX, the camera transform, transitions, the multiprocessing pool and ffmpeg.
- `qa.py` runs the automatic checks and writes contact sheets every 0.5 s.

## shots.json fields the engine reads
- **Shot fields:**
  - `set` / `cam` / `light` (or `plate`);
  - `size`: `close` allows a bottom crop;
  - `crop`;
  - `transition`: `cut` | `crossfade` (8 f) | `whip` (8 f, motion-blurred), with `whip_dir`;
  - `camera`;
  - `fx`;
  - `characters`.
- **`camera.move`:**
  - `push_in` / `pull_out` (`amount`). The default is a slow push of about 0.12 %/f, capped at 6 % per shot, and the push stops at the first kick.
  - `hold`.
  - `glide` / `follow` / `pan` (`direction`, `amount`; `pan` also takes `at_word`).
  - `tilt_up`.
  - `shake`.
  - Optional: `focus: [x, y]`, `glides: [{at_word, dur, ease: out|inout, to: {zoom, x, y, roll}}]`, and `kick: [word, ...]`.
- **Character fields:**
  - any `character()` kwarg;
  - `x`, `height_m`, `scale`, `z`, `facing` (auto-faces the partner in two-shots), `view` (`rear` flips rider-side left/right), `talk: true` (lip sync), `enter_at_word`, `insert` (a plate cut-in from `at_word` to `until_word`).
- **Beat fields:**
  - `at_word`;
  - `pose` (engine names: idle, point, wave, think, hold, hips, cheer, present ...), or `arm_pose` `[rider_left, rider_right]`;
  - `expr`, `prop`, `facing`;
  - `lean` / `body_lean` (degrees, negative = rider's left);
  - `x` (hop-steps, so feet never slide);
  - `action`: `hop` | `jolt` | `shake` | `lean`.
- **FX fields:** `name`, `at_word` (the effect peaks on the word), `x`, `y`, `size` (a fraction of the width), `dur` (s), `on: <char id>` + `anchor: head|feet` + `dx`, and `kick: true`. Every other key goes to `fx.render()`. Set `ENGINE_FX=/path/fx.py` to test another fx module. Unknown names fall back to a stub star.

## Stand-ins (until other areas ship)
- **Plates:** missing plates fall back to `engine/test/plates/village__{M,A}__day` by shot size. The stand-ins are on with `ENGINE_STANDIN=1`, the default; set it to 0 to fail hard instead.
- **Riders:** a character with `rig` uses `bikes.ride()`. Its beats drive `lean` / `body_lean` / `bike_lean`, `knee_out`, and an optional `steer`. With no explicit `steer`, the engine adds an **automatic countersteer**: before each lean change of more than 5°, the bars flick the other way (up to 10°, peaking 5 f before the lean lands), and a held lean steers gently into the turn. Cards are cached per 1° bucket. The sticker comes from a `helmet_sticker:` entry in `props`.
- **Bean faces:** `mouth=` and `blink=` come from bean.py. Only half-lid blink frames still use the engine overlay.
- **Outfits:** an outfit given as a bare string gets a default colour.
- **`contact_shift`** (rider side): the tyres slide out sideways (16 % of the figure height) while the bike tips the other way. The next lean beat takes over from it.
- **Chase cam:** for riders in `rear`/`front` view, the hips stay at `x` and the wheels swing out under a lean. Riders are exempt from the planted-feet check because the bike rolls.
- **`path`** (top view): the rider card rides the fx `path_line` actual track, in step with its drawn-on head and nose-first along the heading. A `path_line` with no `dur` lasts the rest of the shot and defaults to `size` 0.9.
- **`points_at`**: the character turns toward the target and points with the arm on its side. Targets come from the plate JSON `"targets": {name: [x, y]}` or another character's id; an unknown target is treated as off-screen past the nearer edge, with a warning.
- **Not drawn yet:** `broom_*` (wardrobe is drawing it), and `view: rear` on a standing, non-riding character.
