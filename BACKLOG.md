# Backlog

Take the highest-priority open item in **your area**. Tick it (`[x]`) with the commit hash when done. Add anything you discover under the right area. P1 = needed for the first video, P2 = quality, P3 = nice to have.

## scripts (`scripts/`)
- [ ] P1 Pick 10 original "Why/How" topics: an everyday physical or psychological phenomenon with a visual mechanism. Avoid the reference channel's topics. Write `scripts/TOPICS.md` with a one-line hook, the mechanism, 2+ sources and a visual-potential score for each. **The user picks one.**
- [ ] P1 For the chosen topic: `SCRIPT.md` + `shots.json`, following `QA.md` › scripts.
- [ ] P2 A list of the sets, outfits, props and FX each topic needs, forwarded to those areas' backlogs.

## sets (`blender/sets/`)
- [ ] P1 Refactor `blender/scripts/scene2.py` into `blender/sets/village/build.py`: cams `wide`, `well_close`, `street_low`, and lights `day`, `golden`, `night`, with plates and JSON.
- [ ] P1 New set `harbour` (Quaternius ships pack + water + pier): cams `pier_wide`, `deck`, and lights `day`, `storm`, `night`.
- [ ] P1 New set `road` (a modern street or highway, Quaternius street pack): cams `roadside`, `in_car`, and lights `day`, `golden`.
- [ ] P2 New set `interior` (a room, Quaternius house interior): cams `room_wide`, `table_close`.
- [ ] P2 Shared `blender/sets/common.py`: sky, lights, ink, materials and plate JSON writer, so sets stay consistent.
- [ ] P3 Parallax plates: a separate foreground layer PNG, so the engine can move it against the background.

## wardrobe (`stickman/`)
- [ ] P1 Outfits as a `draw()` argument: `shirt` (colour band on the torso), `coat`, `uniform` with buttons, `apron`. They must follow DRAWING_RULES.
- [ ] P1 Hats: cap, top hat, captain, cowboy, chef, hard hat, crown, in addition to helmet and sailor.
- [ ] P1 Held props: a hand anchor point, plus prop sprites (bag, rock, phone, lantern, sword, paper, cup).
- [ ] P1 Mouth shapes for lip sync (closed, small, open, wide, O, smile-talk) selectable on top of any expression.
- [ ] P2 Head tilt (±10°) and head turn (`look`) animated separately from the body.
- [ ] P2 A toe-roll / heel-strike foot in walks.
- [ ] P3 Run cycle and sit pose, following DRAWING_RULES.

## fx (`fx/`)
- [x] P1 `fx/fx.py` with: explosion, impact_star, dust_puff, speed_lines, sweat_drop, anger_vein, glow_eyes, sparkle, splash, question_mark, exclaim, music_note. (claude/area-fx) After 4 review rounds, 11 of 12 effects pass (every score >= 7). See `fx/RULES.md`.
- [x] P1 `fx/CATALOG.md` with preview strips (`fx/previews/`), a demo GIF, and automatic checks in `fx/scripts/catalog.py`.
- [ ] P1 glow_eyes: round 4 scored readability 6 and style 5 because the translucent blurred halo looked muddy. It now uses a solid flat outlined halo with rays, which has not been re-reviewed. Re-review it, and try a version with no halo (rays only) if it still reads as "big eyes" rather than "glow".
- [ ] P2 fx polish from review round 4: sparkle peaks at 3/12 and should leave no sub-3 px specks; exclaim's tick dashes need a visible outline at night; the splash ring should fade by alpha, not by thinning; the question_mark hook should grow with its dot at 1/12; the double note in music_note should ease in over 2-3 frames; explosion and dust_puff leave pixel debris in their last third.
- [ ] P2 engine: composite fx with `line=3.2*char_scale` so the fx outline matches the character's outline (see CATALOG.md).
- [ ] P2 Light shafts and a lens flash.

## engine (`engine/`)
- [ ] P1 `render_video.py`: read `shots.json` + `words.json`, place characters on plates (`ground_y`, `px_per_m`), drive poses and expressions from beats with the anim_v2 principles, add camera moves (push-in, ease-out glide, shake), FX, and write the mp4.
- [ ] P1 Lip sync from `words.json`: choose the mouth shape from the letters.
- [ ] P1 `engine/qa.py`: the automatic checks in `QA.md` › engine and video.
- [ ] P2 Crossfade and whip-pan transitions between shots.
- [ ] P2 Character tint from the plate JSON `tint`, plus a rim light from `light_dir`.

## audio (`audio/`)
- [ ] P1 Voice from `SCRIPT.md` via ElevenLabs (connected), and `words.json` from word timestamps.
- [ ] P1 SFX and music bed: reuse `templates/audio/`, with ducking, -14 LUFS and the exact length.

## videos (`videos/`)
- [ ] P1 Assemble the first video once scripts, sets, wardrobe, fx, engine and audio are at P1. Run QA, then **ask the user to review the draft**.
