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

## Video 2 wiring (sailing-stones)
- **Prop sprites** (`props.py`, from `characters/scripts/sprites.py`): string entries in `props` are sprites on the sets in `SPRITE_SETS` (playa, inserts), so video 1 frames stay identical; dict entries work anywhere: `{"name", "x", "y" (anchor, frame fractions), "scale", "layer": back|front, "at_word", "until_word", "dur", "path": [[x, y], ...], "t", "flip", "kw"}`. Placement defaults are in `props.DEFAULTS` per (name, cam); a plate JSON `"<name>_xy"` (px) wins for string entries. Props the plate shows (`props.BAKED`) and props a character holds in the shot are skipped. Scale = the character-card scale at that ground row (perspective from `horizon_y`).
- **Plate variants:** a `fantasy:<tag>` prop (or `"variant": tag`) picks `<set>__<cam>__<light>__<tag>.png` when it exists.
- **Antennae** (`hat: "antennae"`): `antennae` on the character or a beat (`up`|`droop`|0..1) eases in over 10 f from the beat's word; the balls spring (damped, ~11 f period) after every body beat and hop.
- **Seated:** `seated: "cooler"` goes straight to bean (soles stay on the ground line); the `cooler` sprite is skipped in that shot.
- **Environment fx:** `dust_storm`, `flash_flood`, `rain` are drawn full-frame (an H-sized square, centred). These and `ice_pane` / `air_hockey_overlay` start on their word and last to the end of the shot unless `dur` is given. `air_hockey_overlay` listed in `props` becomes an fx.
- **`ice_pane` chaining:** several `ice_pane` entries in a shot play as one: each stage but the last holds its full sheet (t 0.91, before its fade) until the next starts.
- **`sliding_rock` `path`:** written in frame fractions in shots.json; the engine converts them to the fx canvas and sizes the canvas to fit the path.
- **Sepia:** `"grade": "sepia"` on a shot (flashbacks) goes through `GRADE.finish(sepia=True)`.

## Stand-ins (until other areas ship)
- **Plates:** missing plates fall back to `engine/test/plates/village__{M,A}__day` by shot size. The stand-ins are on with `ENGINE_STANDIN=1`, the default; set it to 0 to fail hard instead.
- **Riders:** a character with `rig` uses `bikes.ride()`. Its beats drive `lean` / `body_lean` / `bike_lean`, `knee_out`, and an optional `steer`. With no explicit `steer`, the engine adds an **automatic countersteer**: before each lean change of more than 5°, the bars flick the other way (up to 10°, peaking 5 f before the lean lands), and a held lean steers gently into the turn. Cards are cached per 1° bucket. The sticker comes from a `helmet_sticker:` entry in `props`.
- **Bean faces:** `mouth=` and `blink=` come from bean.py. Only half-lid blink frames still use the engine overlay.
- **Outfits:** an outfit given as a bare string gets a default colour.
- **`contact_shift`** (rider side): the tyres slide out sideways (16 % of the figure height) while the bike tips the other way. The next lean beat takes over from it.
- **Chase cam:** for riders in `rear`/`front` view, the hips stay at `x` and the wheels swing out under a lean. Riders are exempt from the planted-feet check because the bike rolls.
- **`path`** (top view): the rider card rides the fx `path_line` actual track, in step with its drawn-on head and nose-first along the heading. A `path_line` with no `dur` lasts the rest of the shot and defaults to `size` 0.9.
- **`points_at`**: the character turns toward the target and points with the arm on its side. Targets come from the plate JSON `"targets": {name: [x, y]}` or another character's id; an unknown target is treated as off-screen past the nearer edge, with a warning.
- **Broom** (wardrobe props): `broom_flick: right|left` tips the broom 8° the other way with a jolt; `broom_tip: left|right` -> `broom_tip_<side>`. While a broom is held, `hold` arms become `palm`.
- **Helmet sticker:** a `helmet_sticker:<text>` prop goes on a worn helmet (riders) and on a held `helmet` prop.
- **Over the shoulder** (`*ots*` cams): a standing `view: rear` character is the near one, drawn at 1.7x with feet below the frame.
- **Two-shots:** standing characters closer than their body widths are spread apart symmetrically (logged as `[layout]`).
- **Bike-only shots:** a shot with no characters and a bike in `props` shows `bikes.draw_bike()` at the plate's `stand_x`.
- Plate `targets` may be px or fractions.

## Captions (`captions.py`, PIPELINE.md > Captions)
- Captions come from `words.json`, one word at a time. A word of 2 letters or fewer, said quickly, rides along with the next word.
- Each caption shows 1 f before its word and clears in silences over 0.4 s.
- **Style:** Inter Black at 6.8 % of the frame height (keywords 7.8 %), an outline at 11 % of the font size, a soft shadow, and the baseline at 66 % of the height. Set `ENGINE_CAPTION_FONT` to use another font.
- **Pop:** 1.25 (keywords 1.4) -> 1.0 over 4 f, with an ease-out and a slight overshoot.
- **Keywords** are yellow #ffd23f. They are picked automatically:
  - numbers;
  - left/right;
  - the title's content words;
  - the last content word of the script (the payoff);
  - `captions.keywords` (shots.json top level or per shot).
- **Faces:** a caption never covers a face. Placement is tested at the largest pop size, with a 6 px margin, and the caption nudges up or down past the face.
- **Options:** `captions: {"enabled": false, "case": "upper"|"as_is"}`.
- `qa.py` checks sync (0-2 f early), silences and face cover.

## Grade (`grade.py`)
- The main process renders each shot's middle frame, and each cut-in's, then solves a tone curve:
  - gamma toward mean luminance 0.43-0.51 (golden 0.42-0.49);
  - a highlight lift so p98 stays at 0.88 or more;
  - a soft shoulder at 0.96 so white faces never clip;
  - a slight warm balance when the cool share is over 0.28;
  - a saturation trim into 0.33-0.50.
- The parameters are written to `out/grade.json`, and the workers apply them as a LUT. `--no-grade` turns it off.
