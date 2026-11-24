# Moth Light: "Why Do Moths Fly Into Lights?" (flat2d, claude/area-moth-light, 2026-11-24)

Video 11. House look: white stickmen with a black outline, rich flat 2D, a serious and curious tone with no comedy, "sentence" captions, and continuous motion. Built on the Blood Falls formula. The hero image is moths orbiting a glowing violet UV lamp in a misty night cloud forest, their flight paths drawn as long-exposure light trails.

The voice is Kokoro `am_adam` 1.16. The voice and mix are the Producer's `audio/moth-light/` and are unchanged: 1915 frames = 63.83 s, about 63.9 s with the 0.1 s cover.

**Status:** three review rounds are done (the last one allowed), and the 540 preview is rendered and muxed. **No 1080 final yet, and nothing is published.**

## Files
| file | what |
|---|---|
| `tests/preview_full_540.mp4` | the 540x960 preview, 30 fps, with `audio/moth-light/mix.wav` (AAC 192k) |
| `tests/sheet_2s.jpg` | 2 s contact sheet of the preview |
| `tests/stills_r1/`, `stills_r2/`, `stills_r3/`, `stills_r4/` | review stills: one per shot, 540x960, captions on, plus `sheet.png`. r1-r3 went to reviewers; r4 has the round-3 fixes and was checked by the Animator only. `stills_dev/` holds the first-pass stills. |
| `tests/review_brief.md` | what each reviewer got: every still's voice-over line and its planned picture |
| `thumbnail.png` | a caption-free frame from `flat2d/moth_light_thumb.py` (a big hawk moth banking round the lamp, the small moths orbiting with trails) + `tools/thumbnail.py`: THEY'RE NOT (white, 160) / ATTRACTED (yellow, 210) |
| `flat2d/moth_light.py` | the shots `s01`-`s15` (s01b, s02b and s11b are splits inside a line), `SHOT_LIST`, `END`, `STILL_AT`, `BAND_FIX`, `HIDE_UI` |
| `flat2d/moth.py` | the moth kit, detailed below this table |
| `flat2d/cloudforest.py` | the world kit, detailed below this table |
| `flat2d/moth_light_thumb.py` | the thumbnail frame |

**`flat2d/moth.py`** is a 3D-projected hawk moth rendered to a sprite:
- textured forewings (olive with a pale band and fine lines), rose-orange hindwings, and a fringe;
- a fur-shaded sphere body with eyes and palps, feathery antennae, and six legs;
- views `top`/`side`/`rear` with elev/yaw/roll/pitch, a wing-beat `flap` with `blur`, and lamp light and rim;
- `small=True` (round 3) for the little orbiting moths: one sharp, inked forewing triangle near the top of the stroke over a faint ghost of the whole beat (so the blur shows at the wing tips), a soft fur-shaded abdomen without rings, and bolder feathery antennae;
- helpers: `put`, `trail` (long-exposure light trails), `back_arrow` (the yellow BACK arrow), `bank_sign`, `up_screen`, `ir_layer`.

**`flat2d/cloudforest.py`** is the world kit:
- the layered night cloud forest: trunks, moss, bromeliads, tree ferns, lianas, mist and spores;
- `uv_lamp`, `camera_rig`, `ir_lamp`, `laptop`, headlamps, `sheet` (the glowing white sheet), and `ir_view` (the grey-green infrared camera look with HUD);
- night-sky stages: stars, Milky Way, hills, treeline, moon, `night_stage`, `ancient_night`, `moon_sky`;
- `candle_room`, `street_lamp`, `desk_wall`/`desk_top`.

## Build
```
.venv/bin/python flat2d/render.py audio/moth-light/words.json OUT.mp4 --film moth_light --size 540x960        # 1915 frames
.venv/bin/python flat2d/stills.py audio/moth-light/words.json OUTDIR --film moth_light [shot ...]              # review stills
.venv/bin/python flat2d/motion_qa.py OUT.mp4.frames <cuts> --impacts <beats>                                  # see Motion QA
ffmpeg -i OUT.mp4 -i audio/moth-light/mix.wav -map 0:v -map 1:a -c:v copy -c:a aac -b:a 192k -shortest videos/moth-light/tests/preview_full_540.mp4
.venv/bin/python flat2d/moth_light_thumb.py frame.png
.venv/bin/python tools/thumbnail.py frame.png videos/moth-light/thumbnail.png --line "THEY'RE NOT|white|160" --line "ATTRACTED|yellow|210"
```
Shot ids follow the Producer's `scripts/moth-light/shots.json` (one per line). The splits stay inside a line, so the mix and the `sfx.json` anchors need no rebuild:
- s01 → s01b at word 8;
- s02 → s02b at word 8;
- s11 → s11b at word 11.

For the final, after the Producer's pass: run `render.py ... --size 1080x1920`, mux `mix.wav`, then `tools/add_cover.sh <video> videos/moth-light/thumbnail.png <master>`.

## Shot list (timed to the real voice; a shot starts 0.1 s before its first word)
| shot | time s | line | picture |
|---|---|---|---|
| s01 | 0.00-3.36 | 1 (0-7) | **frame 0 = the hook and the loop frame:** the night cloud forest, the glowing UV lamp, moths orbiting it with light trails, a big hawk moth crossing in front, two scientists with red headlamps, a camera and an IR lamp; 2024 / COSTA RICA |
| s01b | 3.36-7.08 | 1 (8-) | closer on the lamp: many long-exposure orbits, a big moth banking in slow motion, a filming camera; AROUND A LAMP, MONTEVERDE CLOUD FOREST |
| s02 | 7.08-9.34 | 2 (0-7) | an old room by candlelight, moths circling the flame, one flutters into it on "flames"; a watcher in an old hat; FLAMES |
| s02b | 9.34-12.18 | 2 (8-) | a night street lamp with moths swirling, a person shrugs; THOUSANDS OF YEARS, ? + WHY? |
| s03 | 12.18-15.46 | 3 | a big moth under a big Moon, a UV lamp below; dashed lines to the lamp (DRAWN TO THE LIGHT?) and to the Moon (THINKS IT'S THE MOON?) |
| s04 | 15.46-19.39 | 4 | infrared camera view: the straight dashed path at the lamp gets a red X (NOT AT IT); the real path draws itself as a ring round the lamp, twice (AROUND IT, AGAIN AND AGAIN) |
| s05 | 19.39-22.96 | 5 | CLUE 1, slow motion from above: a big moth banking round the lamp on its orbit ring, the BACK arrow pointing at the lamp; BACK TOWARD THE LIGHT |
| s06 | 22.96-27.40 | 6 | CLUE 2, infrared: a lamp on the ground pointing up; a moth flies over it, flips belly-up (BACK now points down) and falls into the litter; LAMP POINTING UP, FLIPS, FALLS |
| s07 | 27.40-31.74 | 7 | CLUE 3: a white sheet glowing overhead, moths fly straight through underneath with level trails, BACK up; GLOWING SHEET = SKY, NOT TRAPPED + check |
| s08 | 31.74-33.95 | 8 | the riddle: a moth beside the lamp, its back turned to it, a big ?; WHY TURN ITS BACK? |
| s09 | 33.95-38.01 | 9 | an ancient starry night, Milky Way, dark land, a moth in the sky; MILLIONS OF YEARS, NO LAMPS, SKY: BRIGHTEST, GROUND: DARK |
| s10 | 38.01-42.20 | 10 | mechanism 1 (night-sky stage): the moth from behind, its BACK arrow up to the sky, a white UP arrow; BACK = UP |
| s11 | 42.20-45.37 | 11 (0-10) | mechanism 2: a lamp beside the moth; the UP arrow swings sideways to the lamp, then the moth tilts its BACK toward it; "UP" POINTS SIDEWAYS, IT TILTS |
| s11b | 45.37-47.35 | 11 (11-) | mechanism 3, from above: the moth's path curls round the lamp onto a circle; TURNS..., ENDS UP CIRCLING |
| s12 | 47.35-50.92 | 12 | mechanism 4: a lamp below; UP swings down beside the moth, the moth rolls belly-up (BACK down) and falls; LAMP BELOW, "UP" POINTS DOWN, ROLLS OVER, FALLS |
| s13 | 50.92-55.83 | 13 | the analogy: a compass on a desk at night; a magnet slides in and the needle swings to it; a person watching; COMPASS + MAGNET, NOTHING BROKEN, WRONG WAY |
| s14 | 55.83-58.66 | 14 | the flip, the biggest title over the lamp with moths circling and a big hero moth: NOT ATTRACTED. / TRAPPED. (yellow, slam + shake on "trapped") |
| s15 | 58.66-63.83 | 15 | back in the 2024 forest, pulling back to the opening frame; THE 2024 FILMS, TRAPPED, NOT ATTRACTED; **the last frame is `s01_frame(0, 0)`, s01's frame 0 (the loop)** |

## Review (stills only)
Each round used one fresh sonnet reviewer. It got each still with its voice-over line and planned picture (`tests/review_brief.md`), the in-order sheet, and `videos/wind-cave/tests/sheet_2s.jpg` as the bar.

| Round | stills | richness / readability / composition | overall | script contradiction | 3+ run | result |
|---|---|---|---|---|---|---|
| 1 | `stills_r1` | not recorded | not recorded | not recorded | not recorded | FAIL (fixes below) |
| 2 | `stills_r2` | not recorded | not recorded | not recorded | not recorded | FAIL (fixes below) |
| 3 | `stills_r3` | 7.0 / 7.5 / 7.0 | 7.2 | none | s10-s12 (blue-purple diagram stage); forest in s14/s15 (an intended bookend) | FAIL |

Rounds 1-2 were scored in the earlier Animator session and the scores were not written down. The fixes come from the commit messages and diffs:
- **R1** (`3361e76`):
  - a spotlight on the hero moths;
  - a brighter IR moth in s06;
  - bigger moths throughout;
  - s11 moved onto a blurred forest stage with a real lamp.
- **R2** (`4127327`):
  - s03 moth 240 → 320 and the s05 orbit trail thicker;
  - s08 the forest defocused with bokeh discs;
  - s10 Milky Way and mist added;
  - s11 moth bigger;
  - s11b the full path kept and thicker;
  - s14 moths bigger and more of them;
  - fixed caption bands for s05 and s08;
  - s06 still taken earlier.
- **R3** (the reviewer's list plus the Producer's note):
  - **the small orbiting moths** (s01, s01b, s02, s02b, s04, s14, s15, thumbnail) no longer read as shrimp or larvae. `moth.render(small=True)` gives a sharp, inked triangular forewing over a faint full-beat ghost (blur only at the tips), a soft fur abdomen without stripes, and bolder feathery antennae. The orbiters are seen from a higher angle (elev 50) so the wings show as triangles. The big hero moths are unchanged.
  - s14: 14 → 6 small moths on clean rings, plus one big hero moth banking in front on its own trail (caption kept off it);
  - s11b: a clean full orbit circle, a brighter path, and the caption kept off the moth;
  - s12: the UP arrow now sits beside the moth (FALLS chip moved left);
  - s11: the UP arrow raised and shortened, clear of the lamp top;
  - s05: a faint full orbit ring and more lamp glow;
  - s06: the ground lamp 1.4x, LAMP POINTING UP moved up;
  - s09: the moth raised into the sky;
  - s04: the dashed straight path ends in an arrowhead at the lamp, and the ring's arrowhead only appears once the ring is drawn;
  - s02/s02b: bigger flame moths (104/100 px);
  - s13: the stray pencil and check removed.

  These were checked by the Animator on `stills_r4`; there was no 4th review (the brief allowed 3 rounds).

**The ≥ 8 gate was not reached** (7.2 in round 3). This is open for the Director/Producer.

The weakest areas reviewers name, as open notes:
- the mechanism shots s10-s12 share one dark blue-violet diagram look;
- s05/s08/s10 are sparse next to the Wind Cave bar;
- the s02 and s02b moths are small at phone size.

## Motion QA (`flat2d/motion_qa.py`)
On the 1915 preview frames:

`motion_qa.py FRAMES 3.36 7.08 9.34 12.18 15.46 19.39 22.96 27.4 31.74 33.95 38.01 42.2 45.37 47.35 50.92 55.83 58.66`

The result is **PASS**: median diff 2.12, the longest frozen span is 1 frame, and there are no pops. The cuts are the shot starts and nothing is listed as an impact.

- The first full render FAILED with 8 pops at 10.2-11.8 s (s02b). The street's lit-window pattern in `cloudforest.street_lamp` was keyed to the window's pixel x, so the slow camera pan flipped windows on and off every few frames. The pattern is now keyed to the window's row and column index. s02b (frames 280-366) was re-rendered with `--t0 9.3333 --t1 12.2333` and spliced in; the seams at the s02/s02b and s02b/s03 cuts are clean.
- Single near-static frames alternate in s13 (51-56 s, the compass and desk). Every other frame moves, so the frozen-span check is satisfied.
- **Loop:** s15's last frame (f 1914) is `s01_frame(0, 0)`. Its mean abs difference from frame 0 is **0.10/255** (the same picture). Frame 0 shows the forest, the lamp, the small moths, the hero moth, both scientists, the cameras and 2024 / COSTA RICA.
- Preview: `tests/preview_full_540.mp4` is 1915 frames, 63.83 s, h264 + AAC 192k, 17 MB.

## Sound
The Producer's mix (`audio/moth-light/mix.wav`, `sfx.json`, `music.json`) is used unchanged. Shot ids s01-s15 keep their cue anchors (the splits are inside lines).

## Open notes
- Acting and feel are the Director's call on `tests/preview_full_540.mp4`. The Producer reviews `tests/sheet_2s.jpg` against the script before any 1080 final.
- Simplified as in SCRIPT.md:
  - "released slow-motion films in 2024" (the paper was published in 2024; the footage was filmed earlier);
  - the IR camera HUD timestamps are illustrative;
  - the white-sheet clue is staged in the same forest.
- Render cost: frames are drawn at 1080 and downscaled. The 540 preview took about 48 min (plus the band cache) on 4 cores.
