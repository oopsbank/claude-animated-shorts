# flat2d: rich flat-2D scene kit

Pillow + numpy helpers for 1080x1920 "rich flat 2D" scenes (the Director's look level, 2026-11-22: layered depth, haze, gradients, texture, faceted light/shadow planes, glow, rim light, contact shadows, particles, vignette). Every call draws one **layer**, back to front; its arguments (offset, seed, `t`, phase) are the animation parameters.

- `kit.py`: the layers.
  - **Sky and light:** `vgrad`, `radial` (sun/lamp/pool light), `light_rays`, `cloud_bands`, `haze`, `depth_fade`.
  - **Terrain:** `peak_range` (faceted lit/shadow planes and snow caps), `ice_cliff` (faceted glacier wall, crevasse seams, strata, icicles), `snow_ground`, `rocks`.
  - **Post:** `snow_particles` (3 depth planes, driven by `t`), `dust`, `grain` (paper and grain), `vignette`, `foreground_frame` (out-of-focus silhouettes).
  - **Characters:** `stick` (white stickman `#f6f6f2`, black outline), `place` (contact shadow, coloured aura, **rim light** on the light side; returns head geometry).
  - **Text and UI:** `label` (role pill), `title` (house headline), `caption` (PIPELINE "sentence" style; `nudge=True` moves it to the cleanest band near 70%), `pill`.
  - **Caption placement for the engine:** `busy(img, box)` is the edge energy under a box. `clean_band(img, w, size, avoid=faces)` returns the least-busy baseline within ±7% of 70%, at a small cost per px of travel. It is the no-plate answer to captions over busy areas.
- `props.py`:
  - **Wardrobe and tools:** fur hat, ice axe, footprints.
  - **Lab:** microscope, flasks/tubes/bottles (glowing).
  - **Graphics:** a stamp (with `cracked=True`, split between words), a big X, an algae chain, a survey plane.
- `style_frames.py OUTDIR [--small DIR] [s01 s05 s11 s15]`: the blood-falls style frames. Every scene takes `t` (seconds), and the comment on each layer says how it moves.
- `sheet.py DIR`: joins the 540x960 review downscales into one sheet.
- `style_frames.py` also builds **s11a** (pure X-ray cross-section, caption on the bedrock band) and **s11b** (the scientist full figure on the ice surface, reacting), from the Director's split of s11 (2026-11-22).

## Shot renderer (motion)
- `anim.py`: motion helpers.
  - **Easing:** `smooth`, `out_back`, `slam`, `pop`, `shake`, `damp` (follow-through).
  - **Poses:** `mix`/`add`/`chain` give pose in-betweens (anticipation, then the action, then overshoot and settle).
  - **Walk:** `walk_pose` + `walk_track` (foot-locked).
  - **Characters:** `card` (cached stickman cards). `actor` places a character with breathing, blinks, lean and hop, and returns head and hand positions.
  - **Camera and post:** `camera` (push, pan, shake). Cached `vignette` and `grain` (the grain boils every 2 frames).
- `blood_falls.py`: the shots as `sNN(u, D, cue) -> (img, info)`. u is the shot-local time, D the shot length, and `cue(i)` the time of word i of the shot's line, so actions land on the voice.
  - **Parallax:** background layers are drawn shifted by `cam*(1-f)`, then the whole frame is panned and pushed.
  - Every shot has particles, glow pulses and a moving hold; nothing is frozen.
- `render.py WORDS.json OUT.mp4 [--t0 --t1 --size 540x960 --sheet DIR --strip NAME:T:N]` renders frames in parallel (4 procs, ~3 s per frame at full size, then downscaled).
  - **Captions:** house "sentence" captions from `words.json`, with a pop. The band is picked once per shot with `clean_band`, avoiding faces; s01 stays at a fixed 70%.
  - **Cuts:** each cut gets a 6-frame punch-in settle and a 3-frame light flash.
  - **Output:** ffmpeg writes the mp4. It also makes 0.5 s contact sheets and consecutive-frame strips.
- `motion_qa.py FRAMES_DIR [cut s ...]` reports frozen frames (consecutive diff < 0.25) and pops (> 4x the local median, not on a cut).
- Stand-in timings: `scripts/blood-falls/stand_in_words.py` turns SCRIPT.md into `words.json` at 3.7 words/s (no voice yet).

Rules kept: blur masks only, never straight RGBA (LESSONS); glow sits behind characters, never on faces (DRAWING_RULES 19); captions follow PIPELINE › Captions.

## v4 (full blood-falls video)
- `blood_falls_2.py` holds s07-s16 and the `SHOT_LIST` [(shot, line, first word)]. It splits lines across shots (s11a/b, s14a/b, s16a/b), and `END` fixes the film length (1965 frames).
- `anim.secondary` adds secondary action in holds on every `actor`:
  - the head leads, and the lean follows 0.35 s later;
  - the shoulders rise with the breath;
  - the forearms beat on stressed voice-over words (`anim.BEATS`, global time `anim.NOW`, both set by render.py).
- `render.place_band` sets the caption baseline per shot:
  - faces and role labels are always avoided;
  - torsos are avoided unless no band within ±15% is free, and legs cost extra;
  - info['avoid'] boxes are kept clear;
  - the width is the widest caption of the shot.
- render.py tags words.json with the SCRIPT.md line of each word when tts.py left none.
- `stills.py WORDS OUTDIR`: one captioned still per shot (at `STILL_AT` or 0.7 of the shot) plus a sheet, as input for the review gate.
- `motion_qa.py`: the cut window is −1..+6 frames (the cut punch-in settle), `--impacts` lists designed beats, and it prints a PASS/FAIL line.
