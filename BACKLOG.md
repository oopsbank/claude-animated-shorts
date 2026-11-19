# Backlog

Take the highest-priority open item in **your area**. Tick it (`[x]`) with the commit hash when done. Add anything you discover under the right area. P1 = needed for the first video, P2 = quality, P3 = nice to have.

## scripts (`scripts/`)
- [x] P1 Pick 10 original "Why/How" topics: an everyday physical or psychological phenomenon with a visual mechanism. Avoid the reference channel's topics. Write `scripts/TOPICS.md` with a one-line hook, the mechanism, 2+ sources and a visual-potential score for each. **The user picks one.** Done: `scripts/TOPICS.md` v5 (4 review rounds; topics 1-5 pass every criterion; 6-7 fixed but not re-reviewed; 8-10 are below the originality bar). The Director picked #5 (bike countersteering). (a8e1727)
- [x] P1 For the chosen topic: `SCRIPT.md` + `shots.json`, following `QA.md` › scripts. Done: `scripts/bike-countersteer/` (231 words, 62 s, 18 shots; `build.py` regenerates and checks it). The Director waived script approval. The reviewer loop stopped at 4 rounds: in round 4 everything was ≥7 except clarity (6), and the clarity fixes were applied but not re-reviewed.
- [ ] P2 A list of the sets, outfits, props and FX each topic needs, forwarded to those areas' backlogs.
- [ ] P1 Put the reference channel's full title list in `references/` (titles only), so topic originality can be checked rather than guessed. Without it, reviewer originality scores drift from round to round.
- [ ] P2 Once the user picks, re-review topics 6-7 of `TOPICS.md` (fixed after review round 4), or replace 8-10 from the reserves for the next video.
- [ ] P2 Re-review `scripts/bike-countersteer` clarity after the round-4 fixes (a fresh reviewer, the QA scripts criteria).
- [ ] P2 When `audio/` produces `words.json`, check that the beat `at_word` indexes still match the spoken words (the punctuation-split rule is in the `shots.json` note).

## sets (`blender/sets/`)
- [ ] P1 Refactor `blender/scripts/scene2.py` into `blender/sets/village/build.py`: cams `wide`, `well_close`, `street_low`, and lights `day`, `golden`, `night`, with plates and JSON.
- [ ] P1 New set `harbour` (Quaternius ships pack + water + pier): cams `pier_wide`, `deck`, and lights `day`, `storm`, `night`.
- [ ] P1 New set `road` (a modern street or highway, Quaternius street pack): cams `roadside`, `in_car`, and lights `day`, `golden`.
- [ ] P2 New set `interior` (a room, Quaternius house interior): cams `room_wide`, `table_close`.
- [ ] P2 Shared `blender/sets/common.py`: sky, lights, ink, materials and plate JSON writer, so sets stay consistent.
- [ ] P3 Parallax plates: a separate foreground layer PNG, so the engine can move it against the background.
- [ ] P1 (for `bike-countersteer`) A NEW `track` set: a riding-school track with a pit lane and a grass run-off. Cams: `track_wide`, `track_med`, `track_top` (top-down), `pit_med`, `pit_ots` (over the shoulder), `bike_close`, `bike_chase` (behind the rider), `grips_close`, `rider_close`. Lights: `day` and `golden`. Signs: "BODY-STEERING CHALLENGE" banner, "CORNERS MADE: 0" lap board, and a chalkboard "PUSH LEFT → GO LEFT" with a top-view bar/wheel drawing.
- [ ] P1 (for `bike-countersteer`) `village`: a `street_med` cam (`day`, `golden`) on a street a bicycle can ride down.

## characters (`characters/`): main cast, bean-head style (Producer prototype done, waiting for user approval)
- [ ] P1 After approval: a wardrobe brief for the bean cast (more hats, outfits, props, side and 3/4 views, mouth shapes for lip sync, walk cycle following the stickman animation rules 20-29).
- [ ] P1 (for `bike-countersteer`) A `ride` arm pose plus a seated lower body; a `helmet` hat (open-face, eyes visible) and a `helmet` held prop; a `broom` balanced on the palm (`broom_flick`, `broom_tip`); bike rigs `bicycle`, `motorbike` and `nobs_bike` (a second handlebar fixed to the frame) in `side`/`front`/`rear`/`top` views; `lean` (rider and bike together), plus `body_lean`/`bike_lean` (separate) and `knee_out`; `view: rear` for the bean body. Cast specs are in `scripts/bike-countersteer/build.py` (`CAST`).

## wardrobe (`stickman/`): ON HOLD by user decision (stickman reserved for later)
- [ ] P1 Outfits as a `draw()` argument: `shirt` (colour band on the torso), `coat`, `uniform` with buttons, `apron`. They must follow DRAWING_RULES.
- [ ] P1 Hats: cap, top hat, captain, cowboy, chef, hard hat, crown, in addition to helmet and sailor.
- [ ] P1 Held props: a hand anchor point, plus prop sprites (bag, rock, phone, lantern, sword, paper, cup).
- [ ] P1 Mouth shapes for lip sync (closed, small, open, wide, O, smile-talk) selectable on top of any expression.
- [ ] P2 Head tilt (±10°) and head turn (`look`) animated separately from the body.
- [ ] P2 A toe-roll / heel-strike foot in walks.
- [ ] P3 Run cycle and sit pose, following DRAWING_RULES.

## fx (`fx/`)
- [ ] P1 `fx/fx.py` with: explosion, impact_star, dust_puff, speed_lines, sweat_drop, anger_vein, glow_eyes, sparkle, splash, question_mark, exclaim, music_note.
- [ ] P1 `fx/CATALOG.md` with preview strips.
- [ ] P2 Light shafts and a lens flash.
- [ ] P1 (for `bike-countersteer`) `steer_arrow` (a curved arrow on the grips or front wheel, `direction=left|right|blocked`; blocked = a red stop bar) and `path_line` (dashed planned path vs actual path on a top-down track: `tight_left`, `wide_arc`, `kink_right_then_left`).

## engine (`engine/`)
- [ ] P1 `render_video.py`: read `shots.json` + `words.json`, place characters on plates (`ground_y`, `px_per_m`), drive poses and expressions from beats with the anim_v2 principles, add camera moves (push-in, ease-out glide, shake), FX, and write the mp4.
- [ ] P1 Lip sync from `words.json`: choose the mouth shape from the letters.
- [ ] P1 `engine/qa.py`: the automatic checks in `QA.md` › engine and video.
- [ ] P2 Crossfade and whip-pan transitions between shots.
- [ ] P2 Character tint from the plate JSON `tint`, plus a rim light from `light_dir`.
- [ ] P1 (for `bike-countersteer`) Support the new `shots.json` fields: `rig` + `view` (bike composites), `insert` (a cut-in of another cam/rig from `at_word` to `until_word`), `camera.at_word`, `contact_shift`, `lean`/`body_lean`/`bike_lean`, `points_at`. Left/right are always the rider's own (see the note in `shots.json`).

## audio (`audio/`)
- [ ] P1 Voice from `SCRIPT.md` via ElevenLabs (connected), and `words.json` from word timestamps.
- [ ] P1 SFX and music bed: reuse `templates/audio/`, with ducking, -14 LUFS and the exact length.
- [ ] P1 (for `bike-countersteer`) Voice-over: the 18 numbered lines in `scripts/bike-countersteer/SCRIPT.md` › Voice-over (231 words, aim for about 62 s).

## videos (`videos/`)
- [ ] P1 Assemble the first video once scripts, sets, wardrobe, fx, engine and audio are at P1. Run QA, then **ask the user to review the draft**.
