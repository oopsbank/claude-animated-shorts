# Backlog (open work only)

Take the highest-priority open item in **your area**. When it is done, delete it here and name it in the commit message; git history keeps the record. Add what you discover under the right area.
P1 = needed before the next video, P2 = quality, P3 = nice to have. Video 1 (bike-countersteer) is final: its leftovers are in `videos/bike-countersteer/NOTES.md`.

## scripts (`scripts/`)
- [ ] P1 `sailing-stones`: G2 storyboard once the `playa`/`inserts` plates exist; preflight staging checks (heights, overlaps) only run with plates. Before voicing, someone with access to journals.plos.org reads the full paper once to confirm F6-F9 in `SCRIPT.md`.
- [ ] P1 Shot grammar for every new script (`references/reports/channels_2026-11.md` §6): at least one extreme close-up, one POV or prop insert, one Dutch or low angle, one crowd or depth-layered shot, and one visual-metaphor set piece for the mechanism. Add a count of these to `tools/preflight.py`. (`scripts/sailing-stones/build.py` counts them from per-shot `grammar` tags; preflight could read the same tags.)
- [ ] P2 `scripts/TOPICS.md`: re-review topics 6-7 (fixed after round 4) or replace 8-10 from the reserves before the next pick.

## sets (`blender/sets/`)
- [ ] P1 **Video 2 (`sailing-stones`), set `playa`** (shots in `scripts/sailing-stones/shots.json`; G1 fails on these plates until built). A dry lake bed (Racetrack Playa style, not a copy of a photo): flat, pale tan clay cracked into polygons, low mountains in dark brown/purple all around, a few dark rocks each with a long, shallow groove trail behind it. 4 lights: `day` (high sun, blue sky), `golden` (low warm sun, long rock shadows), `night` (deep blue, stars, one warm van light), `frost` (late-morning sun on a sheet of thin ice/shallow water with mirror reflections of the mountains; for the mechanism). 5 cams, each needs `--depth`:
  - `playa_wide`: depth-layered wide; a hero rock + trail in the near foreground, playa mid, mountains far; ground space 0.35-0.65 W for two small characters.
  - `playa_med`: eye-level medium at the cousins' camp: a dome tent, a time-lapse camera on a tripod, a weather-station mast, two folding chairs, a row of ~15 rocks; room for a two-shot. Also used for the 1948/1960s flashbacks (the engine adds a sepia grade).
  - `rock_low`: low angle at ground level beside one hero rock (fills ~1/3 W) and its trail running away from camera; must hold a 1.7x zoom as an extreme close-up of the rock edge.
  - `playa_top`: straight top-down on one rock and trail, cracked clay pattern; used with the ice fx (pond → ice → panes → drift). Needs a `targets` entry for the rock.
  - `overlook_med`: a gravel pull-out at the playa edge: a parked tour van (no brand), a hand-painted sign board on two posts (`common.sign()` text: ALIEN ROCK TOURS; variants $40, SOLD OUT, NIGHT ONLY, and ICE TOURS $40 with ALIEN crossed out), a plywood alien cut-out; `targets` for `tour_sign`. Room for 4 characters at 0.8x.
- [ ] P1 **Video 2 insert set `inserts`** (one light, `day`; 2D in PIL is fine; our palette, plum ink, no brands): `ticket` (unused in v17 final, skip), `alien_cam` (FANTASY panels in a thought-bubble frame with a cheesy green ALIEN CAM filter, clearly fantasy: `leaf_blower_aliens`, `rock_racing_league` (rocks in tiny helmets and numbered bibs, a cheering alien stadium), `alien_air_hockey_final` (neon rink, a boulder puck, a referee that is itself a rock in a striped shirt with a whistle, a scoreboard); `price_card` overlays $30/$40/$50), `gps_screen` reused as `livestream_screen` (LIVE · 1.2M, comments "ICE??" "REFUND", rocks sliding in sunshine).
- [ ] P1 Video 2 props on the plates or as engine props (v17 final): `gps_box` (small grey box with an antenna), `gary_rock` (a MID-SIZE rock with googly eyes; also `gary_buried`: one eye poking out of dust), `rock_row_15`, `rock_trail_hero`, `tent`, `tent_floating`, `timelapse_cam`, `cooler` (+ `cooler_trophy` on a plinth), `flood_water`, `pond_water`, `ice_sheet` (the frost light), `fridge_silhouette` and `phone_silhouette` (scale cues), `air_hockey_overlay` (rink lines/goal flickering over the real ice), `tour_van`, `tour_sign` variants (ALIEN ROCK TOURS · NIGHT ONLY · $20 / SOLD OUT; ICE TOURS $5 with ALIEN crossed out), `tour_sign_free` (the NIGHT ONLY sign as a separate sprite that splits and topples), `banner` (FINAL FAIL · LIVE), `livestream_counter`, `flying_bills`. Keep the van and fans at the road edge, never on the playa.
- [ ] P1 **Look test before the playa set:** one hero prop, e.g. the tour van or a rock with a GPS box, in the playbook §3b recipe (stylised PBR, bevel highlights, gold trim, AO, soft key, little or no ink). Render it next to a reference crop and have the panel score it (≥ 9). Then bake the recipe into `common.py` materials.
- [ ] P2 `playa` (built, `blender/sets/playa/build.py`; 5 cams x 4 lights + depth; targets rock, tour_sign, camp_rocks, tent). Review rounds 1-3 (low res): 6.6 → 6.8 → 6.9. Open notes:
  - overlook_med: the foreground gravel is large and plain;
  - night: the playa_top pond reads as flat dark water (the engine's rain rings and frost fx carry the shot);
  - frost: playa_top is washed out;
  - the camp is small in playa_wide and rock_low;
  - in playa_med, the mast and chairs sit behind a centred character.
- [ ] P2 `inserts` (built, `blender/sets/inserts/build.py`, PIL). Frozen after 8 rounds at 6.8 → 6.8 → 7.0 → 7.2 → 7.3 → 7.4 → 7.5 → 7.3 (plateau). Open notes:
  - air hockey: the scoreboard and crowd crowd the bubble top;
  - leaf blowers: the desert reads muddy under the green filter;
  - racing: the trophy is small;
  - livestream: the comments could be bigger.
- [ ] P2 Look test (`blender/sets/playa/looktest.py`) stopped at a plateau of about 7/10 (19 rounds, best 7.1; the recipe is in `common.py`: `pbr`, `gold`, `glass`, `soften`/`rbox`/`rcyl`, `rock(facet=)`, `contact_blob`, `softbox`, presets `sky_refl` and `sun_from`). The reviewers' recurring blockers:
  - Contact shadows and AO read weak under vehicles. Try Cycles AO or a baked AO multiply in `pbr`.
  - Rocks and the tracker read matte or plasticky. Try roughness variation and edge wear.
  - The low-angle groove trail is hard to read. The flat painted strip (`ground.trail`) works best so far.
  - The cracked ground is busy behind characters.
  - The warm key / cool fill split is not strong enough at midday.
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
- [ ] P2 Video 2 wardrobe was frozen at ~7/10 after 8 review rounds (the ≥ 8 check moves to the storyboard and draft, G3). Open notes from the reviewers:
  - Grips on chest-held two-hand props (phone, camera, laptop) still read as "pasted on". Try forearms drawn over the prop edge, or a mitten hand.
  - The seated pose reads OK but stiff: knees could bend over the lid.
  - Prop text (ADMIT 1, LIVE, ICE TOURS) is small at phone size.
  - Night legs sink into navy: the engine rim light should fix this.
  - The antenna droop has no spring compression.
- [ ] P1 Video 2 (`sailing-stones`): hat `antennae` (a headband with two springy green antenna balls, for the guide and his tourists) with an `antennae="droop"` state; a `seated="cooler"` pose; held props `gps_box`, `screwdriver`, `googly_eyes`, `mug`, `laptop`, `frying_pan`, `ticket`, `cash_fan`, `camera`, `flashlight`, `phone`, `selfie_stick`, `megaphone`, `flag`, `air_hockey_mallet`, `gary_rock`. Cast ids and colours are in `scripts/sailing-stones/build.py` (CAST).
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
- [ ] P1 Video 2 fx frozen at ~5.8/10 after 3 rounds (6.2, 5.8, 5.8) on 180 px dense sheets. All 9 fx exist, are registered in CATALOG and `sfx_x.py`, and pass `catalog.py`. Judge them next in the storyboard; the reviewers' open notes:
  - **Mechanism (`ice_pane stage=drift`):**
    - top view: the push contact must read in one glance. Use a bigger pane travel, an impact star on contact, and wind as 3-4 plum-outlined streak arrows (now white dashes).
    - side view: reads as near-static at tile size. Use a bigger shove, a pane tilt-back anticipation, and a rock jolt.
  - **`sliding_rock path='away'`:** the crowd reads as mushrooms or stalks; try a flat groove with pebble ridges and no vertical stem.
  - **`dust_storm` / `flash_flood`:** the full cover holds ~40% of the life; cut it to ~15%. The flood body is a flat slab: add moving foam and debris, and a camp item bobbing for the gag.
  - **Stage chaining:** `ice_pane` water, freeze and panes end on a full sheet before their 8% fade, by design. The engine should chain the stages in one framing (fade only the last).
  - **Style:** thin lines (rain, crack edges, rink lines) want plum ink weight.
- [ ] P1 Video 2 (`sailing-stones`) new effects, same flat style: `ice_pane` (kw `stage`=water|freeze|panes|drift, `direction`, `view`=top|side: a pale cyan translucent sheet with white edge glints), `ice_crack` (white crack lines racing across the sheet), `sliding_rock` (a rock sprite sliding along `path` with a groove trail; `count`, `sprite`=rock|fridge, `path`='away' shrinks toward the horizon), `gps_ping` (expanding radar rings + a dot), `year_badge` (a UI tag in the top third: white Poppins Bold on a plum pill, kw `label`), `dust_storm` (a brown wall of dust rolling across, then settling), `flash_flood` (a brown wall of water, kw direction), `rain` (slanted streaks).
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
- [ ] P1 Video 2 asset wiring (`claude/area-assets`):
  - **Character kwargs:** `hat='antennae'` with `antennae='up'|'droop'|0..1` (ease 0→1 on "Fine. It's ice.") and `antennae_sway` (deg, spring wobble on hops); `seated='cooler'` (draws its own cooler) or `'bare'` (place the `cooler` sprite yourself; the seat top is `bean.seat_top(build)`).
  - **Held props** use arm pose `'hold'`. `('hold', 'hold')` with a one-hand prop puts it in the right hand.
  - **Sprites** (`characters/scripts/sprites.py`, `sprite(name, t, k)`, anchor in `im.info['anchor']`, `k` = the character card scale):
    - `gary_rock` (`eyes='askew'`), `gary_buried`, `gps_box`, `cooler`, `cooler_trophy`;
    - `tent`, `tent_floating` (t bobs);
    - `timelapse_cam`;
    - `tour_sign` and `tour_sign_free` (t 0..1: shudder, crack, topple);
    - `flying_bills` (t, gone by 0.9);
    - `banner`, `livestream_counter`, `price_card`;
    - `fridge_silhouette` and `phone_silhouette`.
    - The `shots.json` prop strings (with notes in parentheses) are parsed as-is.
  - **FX coordinates:** `sliding_rock` `path` points are canvas fractions (0..1 of the fx square), so convert from frame fractions. `dust_storm`, `flash_flood` and `rain` are full-frame (`size` = the frame width, centred).
  - **`air_hockey_overlay`** is a new fx (silent).
- [ ] P1 Video 2 (`sailing-stones`): a per-shot `grade: "sepia"` for flashbacks (shots s10-s11), and the `seated` character placement (s29).
- [ ] P1 Play fly-through clips (image sequences) as shots or transitions, with directional motion blur, plus fast punch-ins and whip pans with blur, so the picture changes every ≤ 1.5 s.
- [~] P1 Depth-tested compositing: DONE in the engine (`occlude()` in render_video.py: plate pixels nearer than the character's ground point are drawn back over it; off on riding shots and with `"no_occlusion": true`). Verify it on the playa plates (rocks and the sign in front of characters).
- [ ] P1 Video 2 (`sailing-stones`): a per-shot `grade: "sepia"` for flashbacks (shots s10-s11), and the `seated` character placement (s29).
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

- [ ] P1 Video 2 (`sailing-stones`) sprites the engine composites (they are NOT on the plates; sets built the plates without them):
  - Ready in `blender/sets/inserts/sprites/`: `price_card_30/40/50.png` (flip in the corner of the alien_cam plates; each plate JSON has `price_card_xy`), `tour_sign_ice.png` and `tour_sign_ice_strike.png` (ALIEN crossed out; s22 on `playa_med` day), `tour_sign_free.png` (the NIGHT ONLY sign that splits and topples, s20 on `rock_low` frost).
  - Still to draw (characters or engine): `googly_eyes` on the hero rock (anchor at the plate `targets.rock`; that rock becomes Gary in s02/s11/s20), `gary_buried` (one eye in dust, s08), `tent_floating` (s10), `cooler` + `cooler_trophy` (s11, s22), `flood_water` (fx `flash_flood`), `fridge_silhouette` (s03) and `phone_silhouette` (s17) scale cues, `air_hockey_overlay` (s18), `livestream_counter` (s14; the gps_screen plate JSON has `counter_xy`), `flying_bills` (s21).
  - Baked into the plates: tour van and sign (overlook_med; day/golden = NIGHT ONLY · $20, night = SOLD OUT, van lamps lit at night), FINAL FAIL · LIVE banner (overlook_med frost), tent, time-lapse camera, weather mast, chairs, cooler, lantern and the 15-rock row (playa_med), hero rock + trail (playa_wide, rock_low, playa_top), ice sheet (every frost plate), pond water (playa_top night).

## audio (`audio/`)
- [ ] P2 Re-run `build_mix.py` whenever `shots.json` changes (fx entries drive the SFX). New fx names need an entry in `lib/sfx_x.py` GEN or SILENT.
- [ ] P2 The limiter peaks at 3.7 dB of gain reduction on voice consonants. Try a fast voice peak stage before the mix. LRA is 1.2 vs the reference 2.4: ease the voice compression if it sounds squashed.
- [ ] P2 Mystery and payoff sections sit 11 LU under the speech (reference 5-10). Check by ear.
- [ ] P2 A motorbike engine/rev SFX for riding shots.
- [ ] P3 A listening pass by the Director (all checks so far are numbers and waveforms).
- [x] P1 sailing-stones voice + mix: `audio/sailing-stones/` (Liam, voiced ONCE, 1,390 characters; quota 2,641/10,000). 65.7 s = **1971 frames** (`length.json`), 3.60 words/s, -14.0 LUFS, -1.2 dBTP, breaths per the voicing notes, loop ending. Preflight: 0 length/word errors. Audio review round 7 (sonnet): **8.0, PASS** (rounds 1-6: 7.2-7.8).
- [ ] P1 Producer: bike-countersteer `words.json` was corrected (it drifted up to 0.26 s late by the end; the audio is unchanged). Re-render video 1's captions and lip sync only if the Director wants it.
- [ ] P2 sailing-stones: listen to the 1.24x time-stretched voice on the draft for flutter or "phasey" artefacts (the checks so far are numbers and waveforms). If it flutters, try `--gap-scale 0.8` with a lower `--target` stretch, or ask for a second take next month.
- [ ] P2 sailing-stones: when the engine's picture differs, re-run `build_mix.py audio/sailing-stones --shots scripts/sailing-stones/shots.json --ring 0.35` (free); `music.json` and `sfx.json` hold the plan.
- [ ] P3 A snore/zzz SFX for sleeping gags (`zzz` is silent for now).
