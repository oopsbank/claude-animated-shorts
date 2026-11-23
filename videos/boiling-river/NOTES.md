# The Boiling River: "The River That Boils With No Volcano" (flat2d, claude/area-boiling-river, 2026-11-23)

Video 6. Same look, tone and pipeline as videos 3-5: white stickmen with a black outline, rich flat 2D, serious mystery, no comedy, "sentence" captions, continuous motion. Voice: Kokoro `am_adam` (the Producer's `audio/boiling-river/`, unchanged). Status: **v2 (the Director's fixes) rendered at 1080: final cut below. Nothing published.**

## Files
| file | what |
|---|---|
| `boiling_river_final_1080x1920.mp4` | v2 posting copy (see Final cut) |
| `tests/preview_full_540.mp4` | 540x960 full-length preview of the v2 1080 render with `audio/boiling-river/mix.wav` (no cover), 1946 frames = 64.87 s |
| `tests/sheet_2s.jpg` | 2 s contact sheet of the preview |
| `tests/stills_r1/` … `tests/stills_r6/` | the review stills per round (one per shot, 540x960, captions on) and `sheet.png` |
| `thumbnail.png` | house-style thumbnail: caption-free frame (`flat2d/boiling_river_thumb.py`, `HIDE_UI`): the GEOLOGIST with his probe in the steaming river, a thermometer at ~100°C, a small volcano far away on the horizon crossed out; headline THIS RIVER / BOILS (v2: the NO VOLCANO line dropped) |
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
.venv/bin/python tools/thumbnail.py frame.png videos/boiling-river/thumbnail.png --line "THIS RIVER|white|120" --line "BOILS|yellow|220"
```
Shot ids follow the Producer's `scripts/boiling-river/shots.json` one per line; the only split is s03 → s03a/s03b inside line 3, so the mix and the `sfx.json` anchors did not need rebuilding. Final (after the Producer's pass): `render.py ... --size 1080x1920`, mux `mix.wav`, `tools/add_cover.sh <video> videos/boiling-river/thumbnail.png <master>`. 1946 frames = 64.87 s; with the 0.1 s cover ≈ 64.97 s (62-66 s rule).

## Shot list (timed to the real voice; a shot starts 0.1 s before its first word)
| shot | time s | line | picture |
|---|---|---|---|
| s01 | 0.00-4.44 | 1 | **frame 0 = the hook:** a jungle river boiling (v2: cloudy heat-darkened water with pulsing orange-red heat pools under it, 15 big rolling domes, ~170 swelling/bursting bubbles, thicker steam), a green tree frog on a mossy root over the water, THIS RIVER / BOILS already on screen at frame 0 (punch + shake on "river"). The frog slips on "animals", scrabbles, lets go after "cooked" and falls; **the shot cuts at 4.44 s while it is still in the air above the steam (no contact)** |
| s02 | 4.44-6.52 | 2 | a study (bookshelves, old AMAZON chart, drawers, papers): the SCIENTIST shakes his head, reaches and shuts an open book with a steaming-river sketch; LEGEND stamps on the cover on "legend"; FOR YEARS |
| s03a | 6.52-9.94 | 3 (0-9) | jungle trail, light shafts, the steaming river glimpsed ahead; the GEOLOGIST (wide-brim hat, khaki shirt) walks in (foot-locked walk), stops; 2011 slams; ANDRÉS RUZO chip on "Andrés" |
| s03b | 9.94-13.45 | 3 (10-18) | on the bank: he dips a probe into the boiling water on "dipped" (ripple rings); a big thermometer climbs from "thermometer" to just under 100°C on "hundred" (impact + shake); NEARLY 100°C; he startles |
| s04 | 13.45-15.96 | 4 | dark rock cutaway: the river channel at the top; on "volcano" an imagined ghost volcano (translucent, dashed outline, magma chamber, a glowing pipe up to the river bed) glows in; VOLCANO? |
| s05 | 15.96-19.74 | 5 | stylised Peru map: BOILING RIVER pin with the ghost volcano beside it; NEAREST ACTIVE VOLCANO pops far south on "volcano"; a dashed ruler draws on "seven hundred", ≈ 700 KM; on "away." the ghost breaks (shards) and a red X lands on it |
| s06 | 19.74-24.91 | 6 | CLUE 1. Top-down canopy, the river from a thin blue stream (top) to a wide orange, steaming river (bottom); COLD STREAM on "cold", HOT on "hot"; the camera starts close on the source and pulls back down the river on "farther down" |
| s07 | 24.91-29.54 | 7 | CLUE 2. Section: the river channel (cold blue left → hot right), jagged faults open and glow on "cracks", hot water blobs rise along them into the river, which bubbles and steams; CRACKS, FAULTS (shake on "faults") |
| s08 | 29.54-33.14 | 8 | CLUE 3. Lab: the SCIENTIST holds up a glowing tube of river water; the RIVER WATER TEST screen scans VOLCANIC GASES / MAGMA MINERALS → NONE; a red X over the volcano icon on "no"; NO SIGN OF / A VOLCANO (v2: at the bottom, y 1650, below the caption band) |
| s09 | 33.14-36.12 | 9 | dusk: purple-orange sky, the sun's broken reflection, the river boiling pink; a big ? rises out of the steam on "how"; the GEOLOGIST thinking on the bank |
| s10 | 36.12-41.14 | 10 | space, a slowly turning cutaway globe (crust, mantle, glowing core); THE EARTH IS / THE STOVE on "is the stove"; an arrow dives from the crust toward the core, cooling blue → hot red, on "deeper … hotter"; DEEPER = HOTTER; VOLCANO OR NOT |
| s11 | 41.14-45.59 | 11 | rain from a storm cloud on mountains (left), the steaming river (right); below, a water path sinks from the mountain foot kilometres deep (KM ruler), blue turning red; RAIN, KILOMETRES DEEP, THE ROCK HEATS IT; a dashed hint rises toward the river |
| s12 | 45.59-49.01 | 12 | close section: a wide glowing crack from the deep up to the river bed, hot water racing up it, PRESSURE arrows pulsing upward, BACK UP; on "river." the river bursts into a boil (flash, shake, steam surge) |
| s13 | 49.01-53.85 | 13 | kitchen: a cutaway coffee machine; cold blue water runs from the tank on "cold water goes in", the hot plate glows on "runs past something hot", hot water rises and drips into the carafe; the mug steams on "steaming"; LIKE A COFFEE MACHINE, COLD IN, SOMETHING HOT (v2: below the machine with a leader line up to the hot plate, clear of the caption), STEAMING |
| s14 | 53.85-55.69 | 14 | the camera dives into the glowing hot plate, a warm flash, and it becomes a cutaway Earth with a glowing core; the hot-plate inset (top left) → arrow → the river pinned on the crust; THE HOT PLATE, = THE PLANET |
| s15 | 55.69-59.08 | 15 | golden-hour aerial: canopy rows to the hazy horizon, the river ribbon glowing and steaming through it (v2: orange → red ribbon with a hot core glow, denser steam and wisps along it); BIGGEST KNOWN, HOT RIVER · NO VOLCANO |
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

## v2: the Director's fixes (2026-11-23)
1. s01 (the hook): the water read as a calm teal pond. Now unmistakably boiling: cloudy, heat-darkened water (`S01_WATER`), orange-red heat pools pulsing up under it (`S01_HEAT`, clipped to the river) plus a hot glow over the whole river, 15 bigger rolling domes with a strong red-orange glow (`S01_BOIL`, `J.boil(heat_a=)`), ~170 bigger bursting bubbles, thicker warmer steam. Frog, THIS RIVER BOILS at frame 0 and the cut before contact unchanged. s16 still ends in `s01_world` at w = 0, so the loop frame matches s01 frame 0 (checked side by side).
2. s08: NO SIGN OF / A VOLCANO moved to the bottom (y 1650, over the bench); its avoid box keeps the caption above it (caption ~1330, clear of the screen and the title).
3. s13: SOMETHING HOT moved below the machine (y 1780) with a leader line up to the hot plate; the machine's lower half is an avoid box, so the caption sits on the counter between them.
4. s15: the river ribbon is orange (far) → red (near) with a red outer glow and a hot core, steam rises along it every 3rd path point plus wisps through the canopy.
5. Thumbnail: the NO VOLCANO line removed (THIS RIVER / BOILS; the crossed-out volcano picture kept).
Checked on 540 stills of s01, s08, s13, s15 (and the loop frame): no title or label under a caption. No reviewer round (tight usage).

## Motion QA (`flat2d/motion_qa.py`)
On the 1946 rendered preview frames: `motion_qa.py FRAMES 4.442 6.521 9.94 13.448 15.955 19.743 24.907 29.535 33.137 36.116 41.135 45.589 49.009 53.851 55.686 59.082 --impacts 1.53 19.32 28.55 36.96 37.12 48.51` → **PASS** (longest frozen span 1 frame; median diff 2.46; no pops).
- The impacts are designed beats on the word: the title punch on "river" (1.53), the ghost breaking + X on "away." (19.32), the shake on "faults" (28.55), THE EARTH IS / THE STOVE slams (36.96, 37.12), the river burst on "river." (48.51).
- The first run also flagged real pops, now fixed in `jungle.py`: steam puffs were drawn with overwrite, so a faint puff vanishing over a bright one jumped (now drawn brightest-last); globe continents popped at the limb and shifted the random stream (now shrink to the limb); `rising` blobs popped in/out at the path ends (now grow/shrink). s10 got a slow globe spin and camera drift (it was near-static for 2 s).
- Loop: the last frame is the s01 world at its own frame 0 with the title (after a steam surge that hides the change), so the restart has no jump.
- The frog slips right along the root and drops partly behind the right-hand fronds; the shot cuts at 4.44 s with it in the air (`strip` checked).

## Final cut (v2)
- `boiling_river_final_1080x1920.mp4` (**committed, the posting copy**): 1080x1920, 30 fps, H.264 High, yuv420p, 2-pass 5.2 Mb/s, AAC 192k, faststart. 1949 frames (3 cover frames from `thumbnail.png` + 1946), **64.98 s**, 44.6 MB (44,576,386 bytes), −14.1 LUFS / −1.1 dBTP after AAC (the mix itself: −14.0 LUFS / −1.2 dBTP).
- `boiling_river_yt_1080x1920.mp4` (YouTube hand-upload copy, same master, 1080x1920, no upscale): **not committed** — CRF 16 came out at 146 MB and the CRF 18 fallback at 127 MB, both over the 95 MB limit (and GitHub's 100 MB file cap). Rebuild locally from the master with `-c:v libx264 -preset slow -crf 18 -profile:v high -pix_fmt yuv420p -c:a aac -b:a 192k -movflags +faststart`, or upload the posting copy.
- Rebuild: `render.py audio/boiling-river/words.json OUT.mp4 --film boiling_river --size 1080x1920` (~45 min on 4 cores), mux `audio/boiling-river/mix.wav` (`-c:v copy -c:a aac -b:a 192k -shortest`), `tools/add_cover.sh <muxed> videos/boiling-river/thumbnail.png <master>`, then 2-pass `libx264 -profile:v high -b:v 5200k -pix_fmt yuv420p -c:a aac -b:a 192k -movflags +faststart`.
- Motion QA on the 1080 frames (same cuts and impacts as below): **PASS** (longest frozen span 1 frame, median diff 2.44, no pops).
- `tests/preview_full_540.mp4` is the muxed v2 render scaled to 540x960 (no cover); `tests/sheet_2s.jpg` is the v2 2 s sheet from the 1080 frames.

## Sound
The Producer's mix (`audio/boiling-river/mix.wav`, `sfx.json`, `music.json`) is used unchanged; shot ids s01-s16 keep their cue anchors (the s03 split is inside line 3: `sfx.json` s03 word anchors 14 "thermometer" and 17 "hundred" land in s03b, as drawn).

## Open notes
- Acting and feel are the Director's call on `tests/preview_full_540.mp4`; the Producer reviews `tests/sheet_2s.jpg` against the script before any 1080 final.
- The frog never touches the water: s01 cuts with it mid-air; in s16 it sits on its root.
- Render cost: frames drawn at 1080 and downscaled; the 540 preview takes ~15-20 min on 4 cores.
