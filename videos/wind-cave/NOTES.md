# Wind Cave: "This Cave Has Been Breathing Since 1881" (flat2d, claude/area-wind-cave, 2026-11-23)

Video 7. Same look, tone and pipeline as videos 3-6: white stickmen with a black outline, rich flat 2D, serious mystery, no comedy, "sentence" captions, continuous motion. Voice: Kokoro `am_adam` (the Producer's `audio/wind-cave/`, unchanged). Built on the Blood Falls formula: one hero image (the small hole in the rock BREATHING on a golden prairie), a blue-white breath motif against warm gold, a brother reacting in almost every shot, big titles. **Status: 540 preview + thumbnail done. The 1080 final has not been rendered and nothing is published.**

## Files
| file | what |
|---|---|
| `tests/preview_full_540.mp4` | 540x960 full-length preview with `audio/wind-cave/mix.wav` (no cover), 1945 frames = 64.83 s |
| `tests/sheet_2s.jpg` | 2 s contact sheet of the preview |
| `tests/stills_r1/` … `tests/stills_r11/` | the review stills per round (one per shot, 540x960, captions on) and `sheet.png` |
| `tests/review_brief.md` | what each reviewer got: every still's voice-over line and planned picture |
| `thumbnail.png` | house-style thumbnail: a caption-free s03 frame (`flat2d/wind_cave_thumb.py`, `HIDE_UI`) at the gust's peak: the hole blowing out hard, Tom's brown hat flying off, Tom recoiling. Headline THIS CAVE / IS BREATHING (key blue) / SINCE 1881 (yellow) |
| `flat2d/wind_cave.py` | the shots `s01`-`s16b`, `SHOT_LIST`, `END`, `STILL_AT`, `HIDE_UI` |
| `flat2d/prairie.py` | the new kit: painted skies (fair / morning / storm / dusk / sunset / deep), sun, flat two-tone cumulus, `storm_deck`, `thunderhead` (with a rain curtain), `lightning`, `rain`; Black Hills `pine_ridge` (cached, pine-tooth crest, haze); rolling `hill` bands (lit crest, wind-combed streaks); `grass` (bunch-grass clumps that bend with the breeze, travelling gust bands and the hole's breath via `flow_at`), `seed_heads`; `outcrop` (three stacked limestone slabs, joints, lichen, the hole with a lit lip); **the breath**: `breath` OUT (long tapered ribbons on integrated spines with curled tips, arrowheads on the leading end, a cold plume, mouth puffs, flying grass bits / leaf flakes / motes) and `breath_in` IN (a funnel: streams converge from a wide arc, narrow into the hole, big arrowheads pointing in, chevrons marching inward); `hat_layer`/`put_hat`; `paper`; `barometer`; `earth_section`, `maze_net`/`draw_maze` (Prim tree + loops, meandering tunnels, lit rims), `boxwork`, `lamp_light`; `air_blanket` (the atmosphere as wavy bands of molecules + pressing arrows, thickness = pressure); `cabin`, `chips_bag` |
| `flat2d/wind_cave_thumb.py` | the thumbnail frame |

Small shared changes: `stickman.draw(hat_col=...)` colours the cowboy hat (Tom brown, Jesse grey); `render.place_band` searches ±27% when every band within ±15% of 70% is blocked (before, it fell back onto a face); `tools/thumbnail.py` gained the colour `blue` (the breath key colour).

## Build
```
.venv/bin/python flat2d/render.py audio/wind-cave/words.json OUT.mp4 --film wind_cave --size 540x960     # 1945 frames
.venv/bin/python flat2d/stills.py audio/wind-cave/words.json OUTDIR --film wind_cave                     # review stills
.venv/bin/python flat2d/motion_qa.py OUT.mp4.frames <cuts> --impacts <beats>                            # see Motion QA
ffmpeg -i OUT.mp4 -i audio/wind-cave/mix.wav -map 0:v -map 1:a -c:v copy -c:a aac -b:a 192k -shortest videos/wind-cave/tests/preview_full_540.mp4
.venv/bin/python flat2d/wind_cave_thumb.py frame.png .1
.venv/bin/python tools/thumbnail.py frame.png videos/wind-cave/thumbnail.png --line "THIS CAVE|white|130" --line "IS BREATHING|blue|170" --line "SINCE 1881|yellow|120"
```
Shot ids follow the Producer's `scripts/wind-cave/shots.json` (one per line); splits stay inside a line (s05 → s05a/s05b at word 7, s08 → s08a/s08b at word 8, s16 → s16a/s16b at word 8), so the mix and the `sfx.json` anchors need no rebuild (s05 card_pop on "paper" lands in s05b, s08 card_pop on "sixty" in s08b, s16 thunder on "storm" in s16a, cave_breath on "breathes" in s16b, all as drawn). Final (after the Producer's pass): `render.py ... --size 1080x1920`, mux `mix.wav`, `tools/add_cover.sh <video> videos/wind-cave/thumbnail.png <master>`. 1945 frames = 64.83 s; with the 0.1 s cover ≈ 64.93 s.

## Shot list (timed to the real voice; a shot starts 0.1 s before its first word)
| shot | time s | line | picture |
|---|---|---|---|
| s01 | 0.00-5.32 | 1 | **frame 0 = the hook:** golden Black Hills prairie, sun shafts, the limestone outcrop with the small dark hole BREATHING OUT (blue-white ribbons streaming up, grass flattened around it, grass bits flying), a thunderhead building on the far left horizon (why it blows out); TOM (brown hat, holding it in the wind) and JESSE (grey hat) BINGHAM have just stopped, either side of it; **1881** + TOM & JESSE BINGHAM at frame 0; whistle arcs rise from the hole on "whistle"; Jesse points at it |
| s02 | 5.32-8.37 | 2 | close-up of the hole breathing in slow pulses; a ring finds the hole on "hole"; Jesse (big, left) leans in; THE HOLE IS / BREATHING (key blue) slams on "And … breathing" |
| s03 | 8.37-11.21 | 3 | low dutch angle into a pre-storm sky: the gust hits on "rushed" (shake), Tom flinches with both arms up, his brown hat flies off on "hat" and spins away into the sky; TOM BINGHAM |
| s04 | 11.21-14.34 | 4 | hill cross-section (strata, roots, quartz glints): the brothers small by the hole; an imagined glowing dashed tunnel draws through the hill to a second opening; air chevrons run through it; A TUNNEL?, ANOTHER OPENING?, a ? |
| s05a | 14.34-16.40 | 5 (0-6) | closer on the far end: the imagined tunnel breaks up (rubble falls through it), a red X on the second opening on "found" (shake); NEVER FOUND, NO OTHER ENTRANCE |
| s05b | 16.40-18.70 | 5 (7-15) | top view: the hole in the rock breathing up at us (rings, motes); on "sheet" Jesse's hand lays a sheet of paper beside it with the hole's own outline traced on it (it fits inside); ONE HOLE ~20 x 25 CM; SMALLER THAN / A SHEET OF PAPER |
| s06 | 18.70-22.73 | 6 | CLUE 1; another (spring-green) morning; the breath now flows IN (funnel, arrows into the hole); on "sucked" Jesse's grey hat lifts off, swings up and is pulled down into the hole by "inside"; Jesse grabs after it |
| s07 | 22.73-27.88 | 7 | CLUE 2; split screen with a lightning seam: left STORM (slate purple, rain, lightning on "storm") the hole BLOWS OUT, Tom braced; right FAIR (sun, gold) the hole PULLS IN, Jesse watching; FOLLOWS THE WEATHER |
| s08a | 27.88-30.19 | 8 (0-7) | CLUE 3; from the hole at the surface the camera pulls back and the cave maze opens below it (boxwork walls), a CAVER (orange suit, hard hat lamp) in a chamber sweeping the beam; A MAZE |
| s08b | 30.19-34.10 | 8 (8-19) | the maze in the dark around the caver's lamp; the counter runs 0 → 260+ KM from "two" to "kilometres"; OF TUNNELS; on "still not fully explored" ? marks glow at the dark unexplored ends; NOT FULLY EXPLORED |
| s09 | 34.10-36.04 | 9 | dusk (purple-orange, sun shafts): the hole breathes, a big ? rides up out of it on the breath; Tom (thinking) and Jesse wonder |
| s10 | 36.04-38.89 | 10 | the sky as a heavy blanket of air (bands of molecules, denser low down) drops onto the land on "heavy" (shake), pressing arrows on "presses"; Jesse looks up; THE AIR / IS HEAVY, AIR PRESSURE |
| s11 | 38.89-43.24 | 11 | a storm rolls in over a cutaway: the blanket thins and the barometer falls to STORM on "drops"; underground the CAVE AIR glows and pushes outward (arrows) and rushes OUT of the hole on "rushes out"; Tom braced on the surface; A STORM COMES → RUSHES OUT |
| s12 | 43.24-47.21 | 12 | the storm moves off: a low golden sun with shafts and a rainbow, the blanket thickens, the barometer rises to FAIR; the breath flows IN on "sky pushes air back in"; Jesse; BACK IN |
| s13 | 47.21-51.82 | 13 | the whole maze under a hill glowing (light hierarchy toward the shaft), air pulses run through every tunnel and up the one shaft to the tiny hole, which gets a glowing ring on "one small hole"; TINY CHANGE, A HUGE AMOUNT OF AIR, ONE SMALL HOLE |
| s14 | 51.82-55.49 | 14 | airliner cabin, warm window light: a passenger behind his seat-back tray; a sealed chips bag puffs from slack and creased to round and taut from "puffing" to "thins"; LIKE A BAG OF CHIPS / ON A PLANE, LESS AIR OUTSIDE |
| s15 | 55.49-57.82 | 15 | the flip: a turning storm sky (lit cloud bands, pressure bands swelling), the hole breathing up into it, both brothers looking up; NOT BREATHING. (slam + shake on "breathing") / THE SKY IS. (biggest title, key blue, slam + lightning on "sky") |
| s16a | 57.82-60.60 | 16 (0-7) | wide: a storm front slides in over the pine hills (lightning on "storm"), the little outcrop far off breathing out, Tom's lost hat tumbling through the foreground grass; EVERY STORM |
| s16b | 60.60-64.83 | 16 (8-17) | present day, the s01 world under the same building storm: close on the hole breathing out, the camera pulls back to the s01 framing; STILL BREATHING; on "just like in 1881" a gust of ribbons sweeps across and clears into **s01's frame 0 exactly (brothers, hats, 1881, world clock = s01's): the loop** |

Hooks (SCRIPT.md map): 0 s the breathing hole + 1881; 3.3 s the whistle; 7.6 s THE HOLE IS BREATHING; 8.7 s the gust; 10.6 s the hat flies; 12.5 s A TUNNEL?; 16 s NEVER FOUND + X; 18.4 s the paper; 18.8 s CLUE 1, 21.7 s Jesse's hat sucked in; 22.9 s CLUE 2 split; 28 s CLUE 3 maze; 31.7 s 260+ KM; 34.1 s the ?; 37.1 s the air drops; 40.6 s RUSHES OUT; 44.3 s rainbow / BACK IN; 51.1 s ONE SMALL HOLE; 53.7 s the bag puffs; 56.4 s NOT BREATHING. / THE SKY IS.; 63.6 s the gust into the loop.

## Review (stills only; one fresh sonnet reviewer per round, each still with its voice-over line and planned picture (`tests/review_brief.md`), plus the in-order sheet)
| Round | richness / readability / composition | overall | script contradiction | 3+ run | result |
|---|---|---|---|---|---|
| 1 | 7.5 / 7 / 7 | 7.2 | s06, s07, s12 (the IN breath read as OUT) | s01-s03, s05b-s07 | FAIL |
| 2 | 8 / 7 / 7 | 7.3 | none | none | FAIL |
| 3 | 7 / 7 / 7 | 7.0 | none | none (s01-s03 borderline) | FAIL |
| 4 | 7 / 8 / 7 | 7.3 | none | none | FAIL |
| 5 | 7.5 / 7.5 / 7 | 7.3 | none | none | FAIL |
| 6 | 7 / 8 / 7 | 7.3 | none | none | FAIL |
| 7 | 7 / 8 / 7 | 7.3 | none | none | FAIL |
| 8 | 7 / 7 / 7 | 7.0 | none | s10-s12 | FAIL |
| 9 | 7 / 8 / 7 | 7.3 | none | none | FAIL |
| 10 | 8 / 7 / 7 | 7.3 | none | none | FAIL |
| 11 | 7.5 / 7 / 7 | 7.2 | listed 5, all brief-wording, none against the voice-over (see below) | none | FAIL |

Fixes per round:
- R1: a new IN breath, `breath_in`, as a funnel with arrows pointing in (the old one was a swirl that still read as OUT); s03 dutch angle; s06 on a spring-green morning; s05b paper and hole outline; s14 seat and window light; bigger chips.
- R2: s13 air pulses through every tunnel (it had been a static mesh); gauge labels fixed; s05a break-up; s09 and s15 figures; s08b caver off centre; a wider caption search in `render.place_band` (the s03 caption had fallen back onto Tom's face).
- R3: the chips bag redrawn as a pillow pouch with crimped seals; s11 re-laid out (titles swap, gauge in the sky); s10 blanket stops above the land; s04/s05a camera zoomed onto the section; s05b paper larger.
- R4: painted light: sun shafts on every prairie sky, ground haze, quartz glints and depth darkening in the section, a cold tint once the tunnel is gone; the s06 hat larger with motion streaks.
- R5: s05b re-staged as a top view (it was the third rock close-up in a row); s04 throat joined to the tunnel; s15 pressure bands.
- R6: grass value contrast up; s03 pre-storm palette; s13 light hierarchy, one title; s05a camera on the far end + rubble.
- R7: out-of-focus foreground grass framing on the prairie shots; s10 bigger rock; s11 rock and Tom moved.
- R8: s12 is now a post-storm golden sunset with a rainbow (it broke the s10-s12 blue run); thicker, brighter tunnels; s06 chips merged; s15 bigger figures.
- R9: s10 painted clouds; s14 wall panels and window glow; s05b smaller hole, sun shafts; several caption avoid boxes.
- R10: about 30% fewer breath ribbons everywhere, arrowheads on alternate ribbons (the clutter note); bigger gauges.

**The gate was not reached.** Overall has sat at 7.2-7.3 for eight rounds (R2-R11, with 7.0 twice). Each fresh reviewer names a different handful of shots, and the same shot scores differently round to round. The one structural failure, IN read as OUT in R1, was fixed in R2. After that no round found a contradiction against the voice-over and no 3+ run except R8's s10-s12 (fixed). I stopped iterating under the tight shared-usage brief. **This is open, for the Director/Producer to decide.**

R11's five "contradictions" are against the brief's wording, not the voice-over:
- the passenger's shirt colour;
- the s16b still, which is taken before the loop frame;
- the s16a hat placed low;
- the s05b hand at the frame edge;
- the s05a X position.

The weakest shots reviewers repeat, as open notes:
- s05b (the top view reads a little flat);
- s14 (a plain cabin);
- s13/s08b (a busy tunnel net under the caption);
- s04/s05a (a plain lower half);
- captions over detail in s03, s11 and s13.

## Motion QA (`flat2d/motion_qa.py`)
See the section below (filled after the render).

## Sound
The Producer's mix (`audio/wind-cave/mix.wav`, `sfx.json`, `music.json`) is used unchanged. Shot ids s01-s16 keep their cue anchors (the splits are inside lines, see Build). The picture lands on them: the whistle arcs on "whistle", the title slam on "breathing", the gust on "Wind" and the hat on "hat", the inhale on "breathed", Jesse's hat on "sucked", thunder and lightning on "storm" (s07, s11, s16a), the counter pop on "sixty", the blanket slam on "heavy", the bag puff on "puffing", and the two title impacts in s15.

## Open notes
- Acting and feel are the Director's call on `tests/preview_full_540.mp4`; the Producer reviews `tests/sheet_2s.jpg` against the script before any 1080 final.
- Dramatised (as in SCRIPT.md): which brother lost which hat follows the park's traditional story; the 8 x 10 in hole is drawn to scale beside a letter sheet (slightly enlarged sheet for legibility); the tunnel to a second opening is shown only as an imagined dashed ghost; the cave is never called "discovered".
- Render cost: frames are drawn at 1080 and downscaled; the 540 preview takes about 25-30 min on 4 cores, and the 1080 final about 45-60 min.
