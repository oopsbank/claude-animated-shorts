# Backlog (open work only)

Take the highest-priority open item in **your area**. When it is done, delete it here and name it in the commit message; git history keeps the record. Add what you discover under the right area.
P1 = needed before the next video, P2 = quality, P3 = nice to have. Video 1 (bike-countersteer) is final: its leftovers are in `videos/bike-countersteer/NOTES.md`.

## scripts (`scripts/`)
- [ ] P1 Shot grammar for every new script (`references/reports/channels_2026-11.md` §6): at least one extreme close-up, one POV or prop insert, one Dutch or low angle, one crowd or depth-layered shot, and one visual-metaphor set piece for the mechanism. Add a count of these to `tools/preflight.py`.
- [ ] P2 `scripts/TOPICS.md`: re-review topics 6-7 (fixed after round 4) or replace 8-10 from the reserves before the next pick.

## sets (`blender/sets/`)
- [ ] P1 **Look test before the playa set:** one hero prop, e.g. the tour van or a rock with a GPS box, in the playbook §3b recipe (stylised PBR, bevel highlights, gold trim, AO, soft key, little or no ink). Render it next to a reference crop and have the panel score it (≥ 9). Then bake the recipe into `common.py` materials.
- [ ] P1 Camera fly-through clips: `build.py --fly <cam_a> <cam_b> --frames 15-45` renders a short Blender camera move at low res and low samples, without ink. The engine adds heavy motion blur and uses it as a transition or a follow-the-object shot. This is the leaders' main pacing device (retention study).
- [ ] P2 `harbour` and `road` have first-draft `build.py` files (ship deck raycast, pier, water per light; KayKit street, primitive car interior). They need low-res iteration, plates, `--depth`, and review.
- [ ] P2 New set `interior` (Quaternius house interior): cams `room_wide`, `table_close`.
- [ ] P2 Every cam a character rides or walks in needs a depth map (`build.py --depth --cams …`); top-down cams that show a route need racing lines (see `track/paths.py`).
- [ ] P2 Lighting, from the Segment Zero study: one motivated practical light per interior, a low sun with long shadows for exteriors, and light steam/dust volumetrics where the story has them.
- [ ] P2 `village` round-4 plates were rendered but never reviewed.
- [ ] P2 `track` leftovers:
  - golden cream haze flattens warm against cool (keep the sky saturated, cool the fill);
  - day asphalt reads lavender (go neutral blue-grey);
  - golden bloom smears the kerb in `track_top`;
  - a purple shadow blob sits in `track_wide` golden;
  - the red pit-wall block reads hot;
  - `pit_ots` has a cluttered grandstand behind the head.
- [ ] P2 Ink density (`frame_stats` edge) stays at 0.01-0.03 in close-ups with DOF (the reference is about 0.05). Try a thicker near-silhouette lineset, or less DOF in close cams.
- [ ] P2 A procedural material library in `common.py` (tufted cushion, tiles, brick, planks, wallpaper, shelf stock) and 3-5 labelled hero props per set (playbook §3D).
- [ ] P3 Foreground occluder props near the camera (window frames, logs, railings) for the engine to depth-test against.

## characters (`characters/`, bean-head cast)
- [ ] P1 (for the engine) In `character()`:
  - `lid=` (0..1, with 0.5 = half-shut) so the engine can drop its blink overlay;
  - arm in-betweens (`arm_pose=('hang', 'point', 0.4)` or elbow/hand offsets) so gestures ease and overshoot;
  - `res=` (output scale) instead of the engine grabbing the 4x canvas.
- [ ] P2 A bars close-up rig view from behind or above (hands, bars and front tyre, with the steer angle from the rig), so a countersteer is seen, not only signalled by an arrow.
- [ ] P2 Brush ink (variable width ±12% with a slight wobble, rounded caps, inner lines at 0.6x) and a bigger face library: joy arcs, a toothy grin, crying, gritted teeth, shocked pupils (playbook §3C).
- [ ] P3 A costume library per period or job, and crowds by seed variation.
- [ ] P2 Speed: `turned()` and `ride()` take about 3 s each (full-size S=4 layers). Crop the layers to the figure bbox.
- [ ] P2 Riding: the near leg in side view makes a small S-bend near the seat tube; the 3/4 motorbike steer could read stronger; the rear-view far hand hides behind a hard-leaning torso.
- [ ] P2 Walk: the hip should be highest just after passing (the up pose), and the arms could lag a little more at passing.
- [ ] P3 Rear view: show the nobs fixed-bar clamps below the torso, and clearer boots on the pegs. A broom tipped 18° toward the head crosses the back of the head (keep the hand at about x=150 or tip it outward). The tipping broom's handle grazes the cap brim in front view.
- Stickman (`stickman/`) is **on hold**. Its open items (unreviewed hats/props/mouths, think-pose sliver, sleeve merge, head turn, toe-roll, run/sit) are in git history before 2026-11-21.

## fx (`fx/`)
- [ ] P2 Polish from the cast review and review round 4:
  - glow_eyes: scale in from a slit, about 70% smaller, below the brows;
  - anger_vein and question_mark: ease the exit over 2-3 more frames;
  - splash: ring at the 3:1 ink weight, fading by alpha;
  - speed_lines: taper the tails;
  - sweat_drop: default scale about 1.3x;
  - sparkle: fade the minis instead of shrinking them under 10 px, and leave no sub-3 px specks;
  - dust_puff: a darker crescent on day plates;
  - exclaim: tick dashes need an outline at night;
  - question_mark: the hook should grow with its dot at 1/12;
  - music_note: ease the double note in;
  - explosion and dust_puff: pixel debris in their last third.
- [ ] P2 Light shafts and a lens flash.
- [ ] P3 `path_line`: a thicker "actual" stroke and a longer hold on the kink.

## engine (`engine/`)
- [ ] P1 Play fly-through clips (image sequences) as shots or transitions, with directional motion blur, plus fast punch-ins and whip pans with blur, so the picture changes every ≤ 1.5 s.
- [ ] P1 Grade: a vignette to a corner/centre ratio of about 0.80, plus split toning (warm highlights R-B ≈ +0.08, neutral or cool shadows). Today ours has no vignette and an inverted split (`references/reports/replication_playbook_2026-11.md` §3A).
- [ ] P1 Depth-tested compositing (the biggest gap in the channel study): give each character a depth (its ground point in the plate's depth map) and draw nearer plate pixels over it, so characters stand behind posts, sit inside cabs and sink into snow (Segment Zero study).
- [ ] P2 Depth of field for far characters, from the plate depth.
- [ ] P2 Arm in-betweens with anticipation and overshoot once `character()` has them. Today arm poses are 1-frame swaps, so a held point reads stiff (acting 6).
- [ ] P2 Crossfades between very different character sizes ghost a giant head: prefer a cut or a matched position there.
- [ ] P2 Walks with foot locking via `characters/scripts/walk.py`. Today x moves are hop-steps.
- [ ] P1 Scene light on characters: tint from the plate JSON `tint`, plus a rim light from `light_dir`, so characters sit in the set's light.
- [ ] P2 Characters sitting or leaning on props (chairs, counters, cab windows), and near characters cut by the frame edge.
- [ ] P2 Composite fx with `line=3.2*char_scale` so fx outlines match the characters.
- [ ] P3 Smear frames or motion blur for fast prop and limb moves, and for wheels.
- [ ] P3 Our own retention overlay (a small chapter-dot row in our palette) and a faint watermark from `channel/logo/`. Design our own.

## audio (`audio/`)
- [ ] P2 Re-run `build_mix.py` whenever `shots.json` changes (fx entries drive the SFX). New fx names need an entry in `lib/sfx_x.py` GEN or SILENT.
- [ ] P2 The limiter peaks at 3.7 dB of gain reduction on voice consonants. Try a fast voice peak stage before the mix. LRA is 1.2 vs the reference 2.4: ease the voice compression if it sounds squashed.
- [ ] P2 Mystery and payoff sections sit 11 LU under the speech (reference 5-10). Check by ear.
- [ ] P2 A motorbike engine/rev SFX for riding shots.
- [ ] P3 A listening pass by the Director (all checks so far are numbers and waveforms).
