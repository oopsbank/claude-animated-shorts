# Flamingo one leg: "Why Do Flamingos Stand on One Leg?" (flat2d, claude/area-flamingo-one-leg, 2026-11-24)

Video 10. Same look, tone and pipeline as videos 7-9: white stickmen with a black outline (the 2017 scientists, "you",
people in a queue), rich flat 2D, serious and curious, no comedy, "sentence" captions, continuous motion. Voice and mix:
the Producer's `audio/flamingo-one-leg/` (Kokoro `am_adam` 1.16), untouched: 1888 frames = 62.933 s. Built on the Blood
Falls formula: ONE hero image (the 2017 study flamingo standing on one leg in a lab clamp, its muscle monitor FLAT),
flamingo pink against teal water / the warm lab, the reveal flipped in the biggest title (FOR US: HARD. / FOR A
FLAMINGO: EASY.), and a loop back to the 2017 lab. **Status: fix pass + 1080 final done (see the last section). Nothing
is published.**

## Files
| file | what |
|---|---|
| `tests/preview_full_540.mp4` | 540x960 30 fps preview with `mix.wav` (1888 frames) |
| `tests/sheet_2s.jpg` | 2 s contact sheet of the preview |
| `tests/stills_r1/`, `tests/stills_r2/`, `tests/stills_r3/` | review stills per round (one per shot, 540x960, captions on) + `sheet.png` |
| `tests/review_brief.md` | what each reviewer got: every still's voice-over line and planned picture |
| `thumbnail.png` | `tools/thumbnail.py` on a caption-free frame (`flat2d/flamingo_one_leg_thumb.py`): a big flamingo asleep on one thin leg in the dawn salt lagoon (head laid on its back, the other leg folded up), the single leg softly lit, a second sleeper and the far flock behind; HOW IS IT (white) / NOT FALLING? (yellow) |
| `flat2d/flamingo.py` | **the flamingo kit (new)**. A side-view flamingo built from unit-space polygons, rasterised at 2x into part masks, each part painted on its own bounding box (gradients, lit edge, form shadow), then ONE ink outline round the silhouette, the far leg in its own darker group behind. Anatomy: a plump body graded pale back to deeper belly with soft body scallops, deep-coral wing coverts with covert rows and long scapular plumes drooping back over a wedge of black flight feathers, a long S-shaped neck (tapered), a small head with a pale bare face, a thick bill bent down halfway (pale base, black tip, gape line), a yellow eye with a pupil and catchlight (a closed-eye arc when asleep), long thin legs: the knee hidden in the belly feathers, the ANKLE (backward bend, a knob) halfway down, scales on the tarsus, a webbed foot with three toes. Poses: `sleep` 0..1 (the neck folds back and the head lies on the back, eyes shut), `fold` 0..1 (the far leg folds into a backward '<' with the foot tucked up), `fx`/`fx2` (feet), `tilt`, `drop`, `sway`, `nod`, `eye`, `breath`. Kinds: `adult` (Caribbean pink-coral), `pale`, `juv` (grey juvenile, dark legs and bill), `specimen` (the 2017 study bird: eyes closed, slightly less saturated). `put()` also does the water veil over the feet, a rippling reflection, and returns key points (knee, ankle, foot, centre, back, far leg); `ripples()`; `flock_bird()` for the distant flock |
| `flat2d/lagoon.py` | **the world kit (new)**: `lagoon` (dawn / morning / night / golden skies, low sun or moon with glow, lit cloud streaks, two hill ranges with haze, the sky mirrored in the water with reflected hills, salt bars, scattered sun glints, the far flock asleep, drifting shimmer, mist), `reeds`; the warm 2017 Atlanta `lab` (afternoon window onto the city with a blind, light panels, an AVIAN LEG poster, shelves of binders, wainscot, perspective floor tiles, a sun patch, rays and motes), `bench`, `monitor` (EMG screen: grid, a flat or noisy trace with glow, a scanning dot, a blinking light), `clamp`; `zoo` (Zoo Atlanta: tree canopy layers, big leaves, a pond, sand) + `rail`; `room` (dusk living room: window onto the city, curtains, lamp glow, sofa, rug); `street` (brick facade, awning, TICKETS window, sidewalk); `stage` (`paper` diagram plate, `blue` blueprint, `xray` lightbox) |
| `flat2d/flamingo_one_leg.py` | the shots `s01`-`s15` (+ splits), `SHOT_LIST`, `END`, `STILL_AT`, `BAND_FIX`, `HIDE_UI`; the specimen in its rig (force plate, strut, clamp), the thermal view, x-ray bones and joints, the joint dials, arrows, meters, the trace panel, the split frame |
| `flat2d/flamingo_one_leg_thumb.py` | the thumbnail frame |

## Build
```
.venv/bin/python flat2d/render.py audio/flamingo-one-leg/words.json OUT.mp4 --film flamingo_one_leg --size 540x960     # 1888 frames
.venv/bin/python flat2d/stills.py audio/flamingo-one-leg/words.json OUTDIR --film flamingo_one_leg                     # review stills
.venv/bin/python flat2d/motion_qa.py OUT.mp4.frames <cut times>                                                        # see Motion QA
ffmpeg -i OUT.mp4 -i audio/flamingo-one-leg/mix.wav -map 0:v -map 1:a -c:v copy -c:a aac -b:a 192k -shortest videos/flamingo-one-leg/tests/preview_full_540.mp4
.venv/bin/python flat2d/flamingo_one_leg_thumb.py frame.png
.venv/bin/python tools/thumbnail.py frame.png videos/flamingo-one-leg/thumbnail.png --line "HOW IS IT|white|150" --line "NOT FALLING?|yellow|170" --top 0.08
```
Final (after the Producer's pass, not done here): `render.py ... --size 1080x1920`, re-render frames 0 and 1887 in one
process if they differ (loop), mux `mix.wav`, then `tools/add_cover.sh <video> videos/flamingo-one-leg/thumbnail.png <master>`.
Shot splits (s01b, s04b, s05b, s12b) are inside lines only, so the Producer's s01-s15 `sfx.json` anchors still hold.

## Shot list (timed to the real voice; a shot starts 0.1 s before its first word)
| shot | time s | picture |
|---|---|---|
| s01 | 0.00-4.91 | **frame 0 = the hook and the loop frame**: the warm 2017 Atlanta lab, the study flamingo (eyes closed, head laid on its back) standing on one leg, its lower leg in a padded clamp on an aluminium strut, foot on a FORCE PLATE; the MUSCLE ACTIVITY monitor with a flat line, MUSCLES: OFF; two scientists in lab coats; 2017 + ATLANTA (re-slams on "2017") |
| s01b | 4.91-7.08 | closer: the bird settles into the pose on "held" (HOLDS THE POSE), the big monitor's flat line, MUSCLES: OFF, FLAT LINE |
| s02 | 7.08-10.25 | dawn salt lagoon: flamingos asleep on one leg with reflections and ripples, the far flock; HOURS clock chip; the near bird lays its head back on "asleep" (EVEN ASLEEP) |
| s03 | 10.25-12.98 | thermal-camera view (HUD, WARM/COLD scale): the body glows warm, the standing leg in the water is cold; on "tucking one leg up" the other leg folds up and warms, heat rings at the tucked foot; WARMTH? (not crossed out), TUCKED IN: WARM, LEG IN WATER: COLD |
| s04 | 12.98-15.64 | bright morning lagoon with reeds: a flamingo awake on one leg; WHY: WARMTH + check on "why", then a big HOW? and a ? at the leg on "how" |
| s04b | 15.64-19.20 | a dusk living room: YOU on one leg, eyes closed, wobbling harder (sway arcs over the head), a 0:01-0:03 timer, EYES CLOSED, WOBBLE! and a sweat drop on "wobble" |
| s05 | 19.20-23.59 | CLUE 1, x-ray lightbox: the flamingo as a glowing ghost, its leg bones (femur, tibiotarsus, ankle, tarsometatarsus, toes); NOT A KNEE + X on "knee", the ANKLE glows on "ankle"; a ghost human leg beside it (YOUR LEG, KNEE, ANKLE) with a dashed link ankle-to-ankle |
| s05b | 23.59-25.26 | push in on the body: the real knee glowing up inside the feathers next to the body; THE KNEE, HIDDEN IN THE FEATHERS |
| s06 | 25.26-29.81 | CLUE 2, golden lagoon: the bird stands on two legs, lifts one on "one leg", then slides its foot under its body centre on "moves" (arrow); a dashed line from the body centre down to the foot; FOOT UNDER THE MIDDLE |
| s07 | 29.81-33.46 | CLUE 3, Zoo Atlanta: a grey juvenile on a force plate swaying, a BODY SWAY panel (ALERT = big wiggles, EYES CLOSED = almost flat, drawn in as the eyes close); LEAST SWAY, ZOO ATLANTA; a scientist pointing |
| s08 | 33.46-36.16 | the riddle: night lagoon, moon and stars, reeds, a sleeping flamingo on one thin leg, a big yellow ?; ASLEEP, ONE THIN LEG |
| s09 | 36.16-39.56 | mechanism 1 (warm paper diagram plate): a dashed centre line from the body to the foot (FOOT UNDER THE BODY), then a big red weight arrow straight down and a glow along the leg (ALL THE WEIGHT, STRAIGHT DOWN) |
| s10 | 39.56-43.29 | mechanism 2 (blueprint): HIP and KNEE dials linked to the joints; each bone turns on its word until it hits a stop block on "end" (a flash + a small shake): END OF THE BEND, CAN'T FOLD |
| s11 | 43.29-46.23 | mechanism 3 (dusk lagoon): a GRAVITY arrow pressing down on the body, the leg glowing locked with a lock (LOCKED), the bird dozes off on "holds it"; a MUSCLES meter barely above zero (BARELY WORK) |
| s12 | 46.23-47.97 | the 2017 lab, reverse angle: the study bird steady on one leg; ONE LEG: STEADY + check |
| s12b | 47.97-49.77 | posed on two legs, the study bird wobbles and topples over on "couldn't" (a faint ghost of its upright pose, motion arcs, shake); TWO LEGS, UNSTEADY, X |
| s13 | 49.77-54.03 | a street queue at a ticket window: YOU with locked knees; an x-ray inset of the leg bones stacked straight with a weight arrow; LOCKED KNEES, BONES CARRY IT, MUSCLES RELAX |
| s14 | 54.03-58.23 | the flip, the biggest title over a split frame (left a person wobbling on one leg in the cool room, right a flamingo asleep on one leg in the dawn lagoon): FOR US: / HARD. (pink) and FOR A FLAMINGO: / EASY. (yellow, 250 px), each on its word; HARD WAY / EASY WAY |
| s15 | 58.23-62.93 | back in the 2017 lab, zoomed in on the leg and pulling back (NO WORKING MUSCLES, STILL STANDING); the title and MUSCLES: OFF fade in; **the last frame is s01's frame 0** (loop) |

## Review (stills only; one fresh sonnet reviewer per round, each still with its voice-over line and planned picture (`tests/review_brief.md`), the in-order sheet and the Wind Cave sheet as the reference; max 3 rounds)
| Round | richness / readability / composition | overall | script contradiction | 3+ run | result |
|---|---|---|---|---|---|
| 1 | 7 / 7.5 / 7 | 7.2 | s12b (the two-legged bird looked upright under UNSTEADY) | s09-s11 (same paper stage) | FAIL |
| 2 | 8 / 7 / 7 | 7.3 | none (weak: s12b topple faint, s11 arrow on the head) | none | FAIL |
| 3 | 7.5 / 7.5 / 7 | 7.3 | none | none | FAIL (< 8) |

Fixes per round:
- R1: s12b rebuilt so the bird visibly topples (rotated about its feet, ghost of the upright pose, motion arcs, shake); s10 moved to a blueprint plate and s11 to the dusk lagoon (breaks the s09-s11 run); s03 the folded leg itself warms on the thermal view, livelier water, a COLD chip; the bill's black tip made smaller; s08 reeds; s12 monitor inside the frame; captions moved to a bottom band in s09-s11 and s13.
- R2: s12b topples left (pivot on the planted foot, the other foot lifts), bird fully in frame, labels off the poster; s11 gravity arrow aimed at the body, HOLDS IT off the head, LOCKED tag; s01 poster moved clear of the title, scientists raised; bigger labels in s05, s09, s10; captions at the bottom in s05, s05b, s12b.
- After R3 (not re-reviewed, under the 3-round cap): s10 leader lines now start at the hip and knee joints (ringed); s11 arrow stops above the back; s12b ghost fainter, X beside UNSTEADY; s01b monitor moved up so the bird's head and clamped leg read.

**The gate (overall >= 8) was not reached in the 3 allowed rounds: 7.2 → 7.3 → 7.3.** Open notes from R3, for the Producer/Director:
- captions sit on subjects in a few shots (s03 the standing leg, s08 the foot, s14 the stickman's arm, s15 the FORCE PLATE label);
- s03: the cold standing leg is dim against the dark water;
- s04b: the sway arcs cross the person's face area; the room is busy;
- s07: the lower half is plain sand and the scientist is cut at the edge;
- s05: the x-ray bird is small, NOT A KNEE / ANKLE sit on the leg;
- s02, s06, s08: fewer layers and less light play than the Wind Cave reference (the far flock is tiny);
- (R1/R2) most hero frames show the bird asleep (head on the back), so the S-neck shows mainly in s04, s05, s06, s09, s10.

## Motion QA
`motion_qa.py` on the 1888 preview frames with the 18 cut times and `--impacts 41.29 48.83 56.34 57.57` (designed hits:
the s10 joints hitting their stop on "end" with a flash + shake, the s12b topple on "couldn't", the two s14 title slams)
→ **PASS**: no pops, longest frozen span 1 frame (0.03 s), median frame diff 1.42.
Fixed on the way: s01b's settle had `drop` jump from -0.02 to 0 one second after "held" (a 25 px jump of the whole bird
at 6.17 s); it now starts raised and settles smoothly (frames 147-212 re-rendered into the preview).

## Loop
Frame 1887 (the last) = frame 0: mean abs difference **0.0** (s15's last frame calls `s01_frame(0, 0)` with the idle
clock `anim.NOW` reset to 0). Frame 0 checked by eye: the full hook (2017 / ATLANTA, the clamped bird, MUSCLES: OFF, the
flat monitor, both scientists), no caption (the first word starts at 0.06 s).

**Preview**: `tests/preview_full_540.mp4` (62.93 s, `mix.wav`, 13 MB) + `tests/sheet_2s.jpg`.

## Fix pass + final (claude/fix-flamingo-one-leg, 2026-11-24)
Producer's review of the 2 s sheet, stills_r3 and the thumbnail; one fix pass, no reviewer subagents (checked by eye on
540 stills: `tests/stills_fix/`). Timing, shot ids and `audio/flamingo-one-leg` untouched.
- **Folded leg (every one-leg pose + thumbnail)** `flat2d/flamingo.py`: the tucked leg is now a compact Z under the belly:
  the knee in the belly feathers, the ankle bent fully just under the belly, the tarsus folded back up forward against the
  belly and the foot tucked into the feathers (hidden behind the body). The fold animates by joint angles and segment
  length (foreshortened), so s03/s06 lifts stay smooth. No diagonal stick, no ball end (smaller ankle knob).
- **Sleeping pose**: the neck lies flat in an S along the back with no gap under it; the head rests on the back with the
  bill angled down into the back feathers (the wing coverts overlap its front half); closed-eye line kept. The inner
  crease where the neck lies over the chest fades out at the neck base (no angular notch).
- **Body and feathers**: a new body outline (oval, fuller chest, short pointed tail), graded pale pink back to coral belly
  with faint soft contour feathers (no fish scales), a cast shadow under the wing; the wing is softer coral with
  overlapping covert rows (each feather a slim lobe with a pale fringe and a shadow under its tip, bigger toward the
  rear), long tertial plumes, and the black flight feathers as one neat dark band along the lower rear edge. Rim light /
  form shadow as before.
- **Captions** (`BAND_FIX`): s03 520 (above the body, off the standing leg), s07 1885, s08 1845 (below the foot), s14 1000
  (under EASY., off the stickman's arm), s15 1850 (below the FORCE PLATE label).
- **s03**: the standing leg in the water is painted a clear cool blue with a soft blue glow (reads COLD, not lost).
- **s07**: a Zoo Atlanta flamingo yard: a wire fence behind the bird, a shallow pool with a stone rim across the
  foreground (ripples, lily pads), big leafy plants both sides; the keeper (cap, green shirt) fully in frame on the rim.
- Thumbnail rebuilt with the fixed bird (same HOW IS IT / NOT FALLING? text).

Checks: 540 preview `tests/preview_full_540.mp4` (62.93 s, mix) + new `tests/sheet_2s.jpg`; loop: frame 1887 = frame 0
(mean abs diff 0.0 at 540 and at 1080); 1080 frame 0 checked by eye.

**Final:** `flamingo_one_leg_final_1080x1920.mp4`: `render.py --size 1080x1920` (1888 frames), mux `mix.wav`,
`tools/add_cover.sh` (thumbnail as the first 0.1 s), 2-pass libx264 high 5200k `-preset slow`, AAC 192k, +faststart →
**43.0 MB (41.0 MiB), 63.04 s, 1891 frames**, 1080x1920. Not published.
