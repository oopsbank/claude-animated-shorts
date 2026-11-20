# Backlog

Take the highest-priority open item in **your area**. Tick it (`[x]`) with the commit hash when done. Add anything you discover under the right area. P1 = needed for the first video, P2 = quality, P3 = nice to have.

## scripts (`scripts/`)
- [x] P1 Pick 10 original "Why/How" topics: an everyday physical or psychological phenomenon with a visual mechanism. Avoid the reference channel's topics. Write `scripts/TOPICS.md` with a one-line hook, the mechanism, 2+ sources and a visual-potential score for each. **The user picks one.** Done: `scripts/TOPICS.md` v5 (4 review rounds; topics 1-5 pass every criterion; 6-7 fixed but not re-reviewed; 8-10 are below the originality bar). The Director picked #5 (bike countersteering). (a8e1727)
- [x] P1 For the chosen topic: `SCRIPT.md` + `shots.json`, following `QA.md` › scripts. Done: `scripts/bike-countersteer/` (231 words, 62 s, 18 shots; `build.py` regenerates and checks it; fc77259). The Director waived script approval. The reviewer loop stopped at 4 rounds: in round 4 everything was ≥7 except clarity (6), and the clarity fixes were applied but not re-reviewed.
- [ ] P2 A list of the sets, outfits, props and FX each topic needs, forwarded to those areas' backlogs.
- [ ] P1 Put the reference channel's full title list in `references/` (titles only), so topic originality can be checked rather than guessed. Without it, reviewer originality scores drift from round to round.
- [ ] P2 Once the user picks, re-review topics 6-7 of `TOPICS.md` (fixed after review round 4), or replace 8-10 from the reserves for the next video.
- [ ] P2 Re-review `scripts/bike-countersteer` clarity after the round-4 fixes (a fresh reviewer, the QA scripts criteria).
- [ ] P2 When `audio/` produces `words.json`, check that the beat `at_word` indexes still match the spoken words (the punctuation-split rule is in the `shots.json` note).

## sets (`blender/sets/`)
- [x] P1 Refactor `blender/scripts/scene2.py` into `blender/sets/village/build.py`: cams `wide`, `well_close`, `street_low`, and lights `day`, `golden`, `night`, with plates and JSON. (Plus `square_med` and `street_med`. Review round 3: colour 7, lighting 5, ink 7, depth 6, composition 6, reads 7. Round-4 fixes were rendered, but the round-4 review did not run because of the usage limit. **Next: review the round-4 plates.**)
- [ ] P1 New set `harbour` (Quaternius ships pack + water + pier): cams `pier_wide`, `deck`, and lights `day`, `storm`, `night`.
- [ ] P1 New set `road` (a modern street or highway, Quaternius street pack): cams `roadside`, `in_car`, and lights `day`, `golden`.
- [ ] P2 New set `interior` (a room, Quaternius house interior): cams `room_wide`, `table_close`.
- [x] P2 Shared `blender/sets/common.py`: sky, lights, ink, materials and plate JSON writer, so sets stay consistent. (3781ddf; plus depth haze, warm glow + grade post, `sign()`, `--repost`, `targets`; `check.py` makes composites and contact sheets)
- [x] P1 (requested by engine) Plate JSON should include `horizon_y`, `light_dir` and `tint` (done in common.py: also `ground_x`, `stand_x`, `targets`, `view`) (scene2.py writes only ground_x/ground_y/px_per_m). The engine defaults them for now.
- [ ] P2 `track` review leftovers after 4 rounds: golden has a cream haze that flattens the warm key against cool shadow (keep the sky saturated, cool the fill), day asphalt reads lavender (go neutral blue-grey), golden bloom smears the kerb in `track_top`, a soft purple shadow blob sits in `track_wide` golden, the red pit-wall block reads hot, and `pit_ots` has a cluttered grandstand behind the head.
- [ ] P2 `harbour` and `road` have first-draft `build.py` files (ship deck raycast, pier, water per light; KayKit city street, a primitive car interior for `in_car`). They need low-res iteration, plates and review.
- [ ] P2 Ink density (`frame_stats` edge) stays at 0.01-0.03 in close-ups with DOF; the reference is about 0.05. Consider a second, thicker near-silhouette lineset, or less DOF in close cams.
- [ ] P3 Parallax plates: a separate foreground layer PNG, so the engine can move it against the background.
- [x] P1 (for `bike-countersteer`) A NEW `track` set (8ea7e8c; review round 4: colour 7, lighting 6, ink 7, depth 8, composition 6, reads 8): a riding-school track with a pit lane and a grass run-off. Cams: `track_wide`, `track_med`, `track_top` (top-down), `pit_med`, `pit_ots` (over the shoulder), `bike_close`, `bike_chase` (behind the rider), `grips_close`, `rider_close`. Lights: `day` and `golden`. Signs: "BODY-STEERING CHALLENGE" banner, "CORNERS MADE: 0" lap board, and a chalkboard "PUSH LEFT → GO LEFT" with a top-view bar/wheel drawing.
- [x] P1 (for `bike-countersteer`) `village`: a `street_med` cam (`day`, `golden`) on a street a bicycle can ride down.

## characters (`characters/`): main cast, bean-head style (owner: wardrobe session, from 2026-11-19)
- [x] P1 Side view (`view='side'`, facing left/right, spec §2.7) and a 3/4 view. (`turned()` rig; `previews/views_v1.png`; reviewer PASS 8/7/7/8/8)
- [x] P1 Riding pose on a bicycle and a motorbike (side and 3/4), with 2D bike props: steer angle on the front wheel and bars, and a lean angle for the whole bike. (`bikes.py`: bicycle, motorbike, nobs_bike; side/3q/rear/front/top; steer, lean, bike_lean + body_lean, knee_out, hold='fixed'; rear/front bean views; `helmet` hat with sticker; `previews/ride_v1.png`; reviewer PASS 7/8/7/8/8)
- [ ] P2 Riding: the near leg in side view still makes a small S-bend near the seat tube; the 3/4 motorbike steer could read stronger; rear-view far hand hides behind a hard-leaning torso. Each `ride()` takes ~3 s (full-size masks in `turned`), so crop the layers if the engine needs speed.
- [x] P1 Mouth shapes for lip sync (`mouth=` closed, small, open, wide, O, smile_talk) overriding any expression. (all views incl. legacy front; `closed` follows the expression; side = profile shapes; `previews/mouths_v1.png`; reviewer PASS 7/7/8/8/8)
- [x] P1 Animatable joints (arm/leg angles, head tilt, body lean, blink) and a foot-locked walk cycle (DRAWING_RULES 20-29). (`turned(pose=...)`, `walk.py` walk_pose/walk_track/blink_at, planted foot slides 0 px; `previews/walk_v1.png`; reviewer PASS 8/7/7/7/8)
- [ ] P2 Walk: hip highest just after passing (the up pose) rather than at passing; arms could lag a little more at passing.
- [ ] P2 Speed: `turned()` takes ~3 s per frame (full-size S=4 layers and rotations). Crop layers to the figure bbox before the engine renders long shots.
- [ ] P2 More hats, outfits and props as the script needs them: `broom` balanced on the palm (`broom_flick`, `broom_tip`), held `helmet` prop with the sticker, clipboard reading "CORNERS MADE: 0" (the `helmet` hat with sticker is done).
- [ ] P1 (for `bike-countersteer`) A `ride` arm pose plus a seated lower body; a `helmet` hat (open-face, eyes visible) and a `helmet` held prop; a `broom` balanced on the palm (`broom_flick`, `broom_tip`); bike rigs `bicycle`, `motorbike` and `nobs_bike` (a second handlebar fixed to the frame) in `side`/`front`/`rear`/`top` views; `lean` (rider and bike together), plus `body_lean`/`bike_lean` (separate) and `knee_out`; `view: rear` for the bean body. Cast specs are in `scripts/bike-countersteer/build.py` (`CAST`).

- [ ] P1 (requested by engine) In `bean.py character()`: `mouth=` (closed, small, open, wide, O, smile) and `lid=` (0..1, with 0.5 = half-shut) so the engine can drop its overlays; arm in-betweens (`arm_pose` accepting a blend, e.g. `('hang', 'point', 0.4)`, or explicit elbow/hand offsets) so gestures can ease and overshoot; optional `res=` (output scale) instead of the engine grabbing the 4x canvas.

## wardrobe (`stickman/`): ON HOLD by user decision (stickman reserved for later)
- [x] P1 Outfits as a `draw()` argument: `shirt` (colour band on the torso), `coat`, `uniform` with buttons, `apron`. They must follow DRAWING_RULES. (+ `pants`, `outfit=` presets; sheet `stick_outfits.png`, 66ded12)
- [ ] P2 Think pose: a tiny dark ink sliver under the right elbow (already in the original pose). In the think pose with a coat, the left sleeve merges with the coat body.
- [ ] P3 Side-on back sleeve in a light colour merges with a same-colour torso at the shoulder.
> State at the pause: hats, held props (`prop=`, `hand_anchors()`, `hold` pose) and lip-sync mouths exist in `stickman.py` but are NOT reviewed. The hat check fails for the `cap` and `captain` visors (they touch hy-49) and for the worried sweat drop over hats. Hat/prop/mouth sheets are not built.
- [ ] P1 Hats: cap, top hat, captain, cowboy, chef, hard hat, crown, in addition to helmet and sailor.
- [ ] P1 Held props: a hand anchor point, plus prop sprites (bag, rock, phone, lantern, sword, paper, cup).
- [ ] P1 Mouth shapes for lip sync (closed, small, open, wide, O, smile-talk) selectable on top of any expression.
- [ ] P2 Head tilt (±10°) and head turn (`look`) animated separately from the body.
- [ ] P2 A toe-roll / heel-strike foot in walks.
- [ ] P3 Run cycle and sit pose, following DRAWING_RULES.

## fx (`fx/`)
- [x] P1 `fx/fx.py` with: explosion, impact_star, dust_puff, speed_lines, sweat_drop, anger_vein, glow_eyes, sparkle, splash, question_mark, exclaim, music_note. (claude/area-fx) After 4 review rounds, 11 of 12 effects pass (every score >= 7). See `fx/RULES.md`.
- [x] P1 `fx/CATALOG.md` with preview strips (`fx/previews/`), a demo GIF, and automatic checks in `fx/scripts/catalog.py`.
- [x] Restyled the fx to the bean-head cast (plum ink #241726, 3:1 thick/thin weight, crescent shading), as the Producer asked. An independent review passed all 12 effects at 7 or higher (glow_eyes 8/7/7). The previews are `fx/previews/with_cast.png`.
- [ ] P2 fx polish from the cast review:
  - glow_eyes: scale in from a slit, sit it about 70% smaller and below the brows when placed on a face;
  - anger_vein and question_mark: ease the exit over 2-3 more frames;
  - splash: give the ripple ring the 3:1 ink weight;
  - speed_lines: taper the tails;
  - sweat_drop: default scale about 1.3x;
  - sparkle: fade the minis out instead of shrinking them below 10 px;
  - dust_puff: a darker crescent on day plates.
- [ ] P2 fx polish from review round 4: sparkle peaks at 3/12 and should leave no sub-3 px specks; exclaim's tick dashes need a visible outline at night; the splash ring should fade by alpha, not by thinning; the question_mark hook should grow with its dot at 1/12; the double note in music_note should ease in over 2-3 frames; explosion and dust_puff leave pixel debris in their last third.
- [x] P1 FX for `bike-countersteer`: `steer_arrow` (`direction=left|right|blocked`), `path_line` (`tight_left`, `wide_arc`, `kink_right_then_left`), `lean_arc`, `wobble_lines`, `whoosh`, all in the bean style.
  - Review: steer_arrow, wobble_lines and whoosh passed at 8. lean_arc and path_line passed in round 2 at 7.
  - Round 3 asked for timing polish on blocked, path_line and lean_arc (the 'no' shake, the exit, and the wedge at the pivot). I fixed these and checked them on a dense sheet, but did not re-review them, to save usage.
- [ ] P2 engine: composite fx with `line=3.2*char_scale` so the fx outline matches the character's outline (see CATALOG.md).
- [ ] P2 Light shafts and a lens flash.
- [ ] P1 (for `bike-countersteer`) `steer_arrow` (a curved arrow on the grips or front wheel, `direction=left|right|blocked`; blocked = a red stop bar) and `path_line` (dashed planned path vs actual path on a top-down track: `tight_left`, `wide_arc`, `kink_right_then_left`).

## engine (`engine/`)
- [x] P1 (650c8f7) `render_video.py`: read `shots.json` + `words.json`, place characters on plates (`ground_y`, `px_per_m`), drive poses and expressions from beats with the anim_v2 principles, add camera moves (push-in, ease-out glide, shake), FX, and write the mp4.
- [x] P1 (650c8f7, stand-in overlay until bean.py has `mouth=`) Lip sync from `words.json`: choose the mouth shape from the letters.
- [x] P1 (650c8f7) `engine/qa.py`: the automatic checks in `QA.md` › engine and video.
- [x] P2 (650c8f7) Crossfade and whip-pan transitions between shots.
- [ ] P1 Review round 2 left (stopped at 2 rounds, Producer budget): acting 6, look 6. (a) Arm poses are 1-frame swaps, so a held point reads stiff: needs arm in-betweens from wardrobe, then anticipation/overshoot on the arm itself. (b) Crossfades between very different sizes ghost a giant head: prefer cuts or a matched position for those (scripts can set `transition`). (c) Wide stand-in plate: characters sit in the top half even at zoom 1.5, because the camera clamps to the plate; real `*_wide` cams should put the ground line lower.
- [ ] P2 Frame stats: punched-in shots of the stand-in village plate fail lum/sat (12-18 of 20 frames pass). Re-check on the real `track` plates.
- [ ] P2 Walk cycle with foot locking once wardrobe ships legs; until then x moves are hop-steps.
- [x] P2 Bike rigs wired: `bikes.ride()` with eased lean/body_lean/bike_lean, knee_out, auto countersteer, bean `mouth=`/`blink=` (shots 6-9 test passes QA). Remaining: `contact_shift`, `points_at`, `broom_*`, `path` (s09 top-view arc), walk via `walk.py`.
- [ ] P2 Character tint from the plate JSON `tint`, plus a rim light from `light_dir`.
- [~] P1 (for `bike-countersteer`, 650c8f7: arm_pose rider-side, lean/body_lean, prop beats, insert, glide/follow/pan/tilt/shake/hold done; `rig`/`view`/`bike_lean`/`knee_out`/`contact_shift`/`points_at`/`broom_*`/`path` wait for wardrobe) Support the new `shots.json` fields: `rig` + `view` (bike composites), `insert` (a cut-in of another cam/rig from `at_word` to `until_word`), `camera.at_word`, `contact_shift`, `lean`/`body_lean`/`bike_lean`, `points_at`. Left/right are always the rider's own (see the note in `shots.json`).

## audio (`audio/`)
- [x] P1 (for `bike-countersteer`) Voice-over: the 18 numbered lines in `scripts/bike-countersteer/SCRIPT.md` › Voice-over (231 words, aim for about 62 s).
- [x] P1 Voice from `SCRIPT.md` via ElevenLabs (connected), and `words.json` from word timestamps. Done: the voice is Liam (`audio/VOICE.md`), `audio/tts.py`, and `audio/bike-countersteer/` (231 words, 63.2 s, 3.66 words/s, 3 breath gaps of 0.32 s = 0.96 s total). Quota used: 1,251/10,000.
- [x] P1 SFX and music bed: reuse `templates/audio/`, with ducking, -14 LUFS and the exact length. Done: `audio/build_mix.py`, `lib/score.py` and `lib/sfx_x.py`. The bike mix is -14.0 LUFS, -1.2 dBTP, 1921 frames = 64.033 s, with the bed 8.5-11.3 LU under the speech (median). Two review rounds: round 2 PASS on condition of 2 fixes, both applied (no automatic impact on camera shakes; breaths kept after the quote and before "Wait,"/"You see,"), plus the SFX cluster at 57 s thinned.
- [ ] P1 When the engine fixes the picture length, re-run `build_mix.py --frames N` (free: no TTS). The current mix assumes **1921 frames** (`audio/bike-countersteer/length.json`).
- [ ] P2 Re-run `build_mix.py` whenever `shots.json` changes (the fx entries drive the SFX). New fx names need an entry in `lib/sfx_x.py` GEN or SILENT.
- [ ] P2 The limiter peaks at 3.7 dB gain reduction on voice consonants (active on 9% of samples). Try a fast voice peak stage before the mix. LRA is 1.2 vs the reference 2.4; ease the voice compression if the draft sounds squashed.
- [ ] P2 A motorbike engine/rev SFX for the track shots (s06-s09) once the picture shows which bike is moving.
- [ ] P2 Mystery and payoff sit 11.0 / 11.3 LU under the speech (reference 5-10): fine for clarity, but check by ear on the draft.
- [ ] P3 A human listening pass by the Director on the draft video (the checks so far are numbers and waveforms only).

## videos (`videos/`)
- [ ] P1 Assemble the first video once scripts, sets, wardrobe, fx, engine and audio are at P1. Run QA, then **ask the user to review the draft**.
