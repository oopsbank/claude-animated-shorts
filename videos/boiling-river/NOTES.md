# The Boiling River: "The River That Boils With No Volcano" (flat2d, claude/area-boiling-river, 2026-11-23)

Video 6. Same look, tone and pipeline as videos 3-5: white stickmen with a black outline, rich flat 2D, serious mystery, no comedy, "sentence" captions, continuous motion. Voice: Kokoro `am_adam` (the Producer's `audio/boiling-river/`, unchanged). Status: **540 preview + thumbnail rendered for the Producer's pass. No 1080 final, nothing published.**

## Files
| file | what |
|---|---|
| `tests/preview_full_540.mp4` | 540x960 full-length preview with `audio/boiling-river/mix.wav` (no cover), 1946 frames = 64.87 s |
| `tests/sheet_2s.jpg` | 2 s contact sheet of the preview |
| `tests/stills_r1/` … `tests/stills_r6/` | the review stills per round (one per shot, 540x960, captions on) and `sheet.png` |
| `thumbnail.png` | house-style thumbnail: caption-free frame (`flat2d/boiling_river_thumb.py`, `HIDE_UI`): the GEOLOGIST with his probe in the steaming river, a thermometer at ~100°C, a small volcano far away on the horizon crossed out; headline THIS RIVER / BOILS / NO VOLCANO |
| `flat2d/boiling_river.py` | the shots `s01`-`s16` (s03 split into s03a/s03b), `SHOT_LIST`, `END`, `BAND_AT`, `STILL_AT`, `HIDE_UI` |
| `flat2d/jungle.py` | new kit layers: rainforest back (sky, far ridge, cached canopy bands, haze, god rays), palm fronds, broad leaves, vines, side foliage walls, banks; the perspective river band; rolling `boil` domes and `bubbles`; thick `steam` (quarter-res mask, puffs drawn brightest-last so overlaps never flicker) and `wisps`; the tree frog (sitting / splayed); a big thermometer; the Peru map + pins; volcano icon (solid or imagined ghost); earth section with depth-heat bands (`dark` variant), faults, travelling hot-water blobs (`rising`), arrows; rain + storm cloud; cutaway coffee machine + mug; cutaway globe |
| `flat2d/boiling_river_thumb.py` | the thumbnail frame |

## Build
```
.venv/bin/python flat2d/render.py audio/boiling-river/words.json OUT.mp4 --film boiling_river --size 540x960     # 1946 frames
.venv/bin/python flat2d/stills.py audio/boiling-river/words.json OUTDIR --film boiling_river                     # review stills
.venv/bin/python flat2d/motion_qa.py OUT.mp4.frames <cuts> --impacts <designed beats>                           # see Motion QA
ffmpeg -i OUT.mp4 -i audio/boiling-river/mix.wav -map 0:v -map 1:a -c:v copy -c:a aac -b:a 192k -shortest videos/boiling-river/tests/preview_full_540.mp4
.venv/bin/python flat2d/boiling_river_thumb.py frame.png
.venv/bin/python tools/thumbnail.py frame.png videos/boiling-river/thumbnail.png --line "THIS RIVER|white|120" --line "BOILS|yellow|220" --line "NO VOLCANO|red|110"
```
Shot ids follow the Producer's `scripts/boiling-river/shots.json` one per line; the only split is s03 → s03a/s03b inside line 3, so the mix and the `sfx.json` anchors did not need rebuilding. Final (after the Producer's pass): `render.py ... --size 1080x1920`, mux `mix.wav`, `tools/add_cover.sh <video> videos/boiling-river/thumbnail.png <master>`. 1946 frames = 64.87 s; with the 0.1 s cover ≈ 64.97 s (62-66 s rule).

## Shot list (timed to the real voice; a shot starts 0.1 s before its first word)
| shot | time s | line | picture |
|---|---|---|---|
| s01 | 0.00-4.44 | 1 | **frame 0 = the hook:** a jungle river boiling (rolling white domes, bubbles, thick steam, orange heat glow), a green tree frog on a mossy root over the water, THIS RIVER / BOILS already on screen at frame 0 (punch + shake on "river"). The frog slips on "animals", scrabbles, lets go after "cooked" and falls; **the shot cuts at 4.44 s while it is still in the air above the steam (no contact)** |
| s02 | 4.44-6.52 | 2 | a study (bookshelves, old AMAZON chart, drawers, papers): the SCIENTIST shakes his head, reaches and shuts an open book with a steaming-river sketch; LEGEND stamps on the cover on "legend"; FOR YEARS |
| s03a | 6.52-9.94 | 3 (0-9) | jungle trail, light shafts, the steaming river glimpsed ahead; the GEOLOGIST (wide-brim hat, khaki shirt) walks in (foot-locked walk), stops; 2011 slams; ANDRÉS RUZO chip on "Andrés" |
| s03b | 9.94-13.45 | 3 (10-18) | on the bank: he dips a probe into the boiling water on "dipped" (ripple rings); a big thermometer climbs from "thermometer" to just under 100°C on "hundred" (impact + shake); NEARLY 100°C; he startles |
| s04 | 13.45-15.96 | 4 | dark rock cutaway: the river channel at the top; on "volcano" an imagined ghost volcano (translucent, dashed outline, magma chamber, a glowing pipe up to the river bed) glows in; VOLCANO? |
| s05 | 15.96-19.74 | 5 | stylised Peru map: BOILING RIVER pin with the ghost volcano beside it; NEAREST ACTIVE VOLCANO pops far south on "volcano"; a dashed ruler draws on "seven hundred", ≈ 700 KM; on "away." the ghost breaks (shards) and a red X lands on it |
| s06 | 19.74-24.91 | 6 | CLUE 1. Top-down canopy, the river from a thin blue stream (top) to a wide orange, steaming river (bottom); COLD STREAM on "cold", HOT on "hot"; the camera starts close on the source and pulls back down the river on "farther down" |
| s07 | 24.91-29.54 | 7 | CLUE 2. Section: the river channel (cold blue left → hot right), jagged faults open and glow on "cracks", hot water blobs rise along them into the river, which bubbles and steams; CRACKS, FAULTS (shake on "faults") |
| s08 | 29.54-33.14 | 8 | CLUE 3. Lab: the SCIENTIST holds up a glowing tube of river water; the RIVER WATER TEST screen scans VOLCANIC GASES / MAGMA MINERALS → NONE; a red X over the volcano icon on "no"; NO SIGN OF / A VOLCANO |
| s09 | 33.14-36.12 | 9 | dusk: purple-orange sky, the sun's broken reflection, the river boiling pink; a big ? rises out of the steam on "how"; the GEOLOGIST thinking on the bank |
| s10 | 36.12-41.14 | 10 | space, a slowly turning cutaway globe (crust, mantle, glowing core); THE EARTH IS / THE STOVE on "is the stove"; an arrow dives from the crust toward the core, cooling blue → hot red, on "deeper … hotter"; DEEPER = HOTTER; VOLCANO OR NOT |
| s11 | 41.14-45.59 | 11 | rain from a storm cloud on mountains (left), the steaming river (right); below, a water path sinks from the mountain foot kilometres deep (KM ruler), blue turning red; RAIN, KILOMETRES DEEP, THE ROCK HEATS IT; a dashed hint rises toward the river |
| s12 | 45.59-49.01 | 12 | close section: a wide glowing crack from the deep up to the river bed, hot water racing up it, PRESSURE arrows pulsing upward, BACK UP; on "river." the river bursts into a boil (flash, shake, steam surge) |
| s13 | 49.01-53.85 | 13 | kitchen: a cutaway coffee machine; cold blue water runs from the tank on "cold water goes in", the hot plate glows on "runs past something hot", hot water rises and drips into the carafe; the mug steams on "steaming"; LIKE A COFFEE MACHINE, COLD IN, SOMETHING HOT, STEAMING |
| s14 | 53.85-55.69 | 14 | the camera dives into the glowing hot plate, a warm flash, and it becomes a cutaway Earth with a glowing core; the hot-plate inset (top left) → arrow → the river pinned on the crust; THE HOT PLATE, = THE PLANET |
| s15 | 55.69-59.08 | 15 | golden-hour aerial: canopy rows to the hazy horizon, the river ribbon glowing and steaming through it; BIGGEST KNOWN, HOT RIVER · NO VOLCANO |
| s16 | 59.08-64.87 | 16 | the opening world: the GEOLOGIST on a near bank (right), the frog back on its root; a red heat glow pulses up from under the jungle on "deep under the jungle"; after "cooking." a steam surge fills the frame and clears into **the s01 composition (world clock meets s01's frame 0), THIS RIVER BOILS fading in: the loop**. No caption during the surge (`seam`) |

Hooks (SCRIPT.md map): 0 s boiling river + THIS RIVER BOILS + the frog; 3.1 s the frog slips; 6.1 s LEGEND; 7.2 s 2011; 12.6 s NEARLY 100°C; 14.9 s the ghost volcano; 18.1 s ≈ 700 KM, 19.4 s X; 19.8 s CLUE 1; 25 s CLUE 2; 29.6 s CLUE 3; 33.4 s the ?; 37.4 s THE STOVE; 46 s PRESSURE, 48.7 s the burst; 49.5 s coffee machine; 55.3 s = THE PLANET; 56.3 s BIGGEST KNOWN; 63.7 s the surge into the loop.

## Review (stills only; one fresh sonnet reviewer per round, each still with its voice-over line and planned picture, plus the in-order sheet)
| Round | richness / readability / composition | overall | script contradiction | 3+ run | result |
|---|---|---|---|---|---|
| 1 | 7.4 / 7.9 / 7.1 | 7.5 | none | none | FAIL |
| 2 | 7.4 / 7.7 / 7.5 | 7.5 | none | none | FAIL |
| 3 | 7.65 / 8.0 / 7.8 | 7.8 | none (s05 X ambiguous) | flagged s03a-s07 green | FAIL |
| 4 | 8.3 / 8.3 / 7.9 | 8.2 | none | none | FAIL (composition 7.9) |
| 5 | 7.9 / 8.4 / 7.9 | 8.0 | none | none | FAIL (marginal) |
| 6 | 8.0 / 8.0 / 7.6 | 7.9 | none | none | FAIL (composition) |

Fixes per round: R1 → s06 whole river in one frame (blue → orange), bigger geologist in s03a/s09, s14 inset of the hot plate (no longer a repeat of s10), s04 ghost volcano filled, labels moved off overlaps (s08, s11, s12, s13), s02 desk detail, s16 geologist off the root, s07 extra faults. R2 → rolling-boil domes in the river shots, jagged faults, s05 ghost beside the pin and crossed on its own, decluttered s06/s11/s12, golden s15, s03a trail + light shafts. R3 → s04 dark rock (breaks the green run), s05 ghost stays visible under the X, s09 reflection + boil, globe clouds/atmosphere, s11 wider river, s03a steam ahead. R4 → s03a river glimpse + bigger geologist, s04 volcano silhouette + glowing pipe, s11 path under the river, s15 ribbon glow. R5 → s04 title off the volcano, thermometer to the line, label placements.
**Plateau rule (LESSONS: 3 rounds without improvement) reached at R4-R6 (overall 8.2 / 8.0 / 7.9; composition 7.9 / 7.9 / 7.6, just under the 8 gate). Stopped iterating on the Producer's tight-usage brief; no script contradiction and no 3+ run in any of the last four rounds.** Open notes from R6 (not done): s11 "far away" (mountains and river share one ground line), s13 label crowding, s08 caption under the title, s05 small map labels near the pin, s15 ribbon still pale, s14 inset tilted/cropped.

## Motion QA (`flat2d/motion_qa.py`)
MOTION_QA_PLACEHOLDER

## Sound
The Producer's mix (`audio/boiling-river/mix.wav`, `sfx.json`, `music.json`) is used unchanged; shot ids s01-s16 keep their cue anchors (the s03 split is inside line 3: `sfx.json` s03 word anchors 14 "thermometer" and 17 "hundred" land in s03b, as drawn).

## Open notes
- Acting and feel are the Director's call on `tests/preview_full_540.mp4`; the Producer reviews `tests/sheet_2s.jpg` against the script before any 1080 final.
- The frog never touches the water: s01 cuts with it mid-air; in s16 it sits on its root.
- Render cost: frames drawn at 1080 and downscaled; the 540 preview takes ~15-20 min on 4 cores.
