# Tunguska: "The Explosion With No Crater" (flat2d, claude/area-tunguska, 2026-11-22)

Video 4. Same look, tone and pipeline as video 3 (blood-falls): white stickmen with a black outline, rich flat 2D, serious mystery, no comedy, "sentence" captions, continuous motion. Status: **v2 (Producer's fixes to s08, s10 and the ending) rendered; 1080x1920 posting copy committed.** Not published.

## Files
| file | what |
|---|---|
| `tunguska_final_1080x1920.mp4` | **the posting copy** (committed, under 45 MB): 1080x1920, captions, the mix, 0.1 s cover in front. See "Final cut" |
| `tests/preview_full_540.mp4` | 540x960 full-length preview with the mix (no cover), downscaled from the v2 1080 render |
| `tests/sheet_2s.jpg` | 2 s contact sheet of the preview |
| `tests/stills_r1/` | the review stills (one per shot, 540x960) and `sheet.png` |
| `tests/stills_r2/` | v2 review stills of the changed shots (s08, s10 before/after the burst, the s14b last frame) |
| `thumbnail.png` | house-style thumbnail (caption-free s05 frame, CLUE badge hidden: Kulik and the crossed-out crater ring) |
| `flat2d/tunguska.py` | the shots `s01a`-`s14b`, `SHOT_LIST`, `END` |
| `flat2d/taiga.py` | new kit layers: spruce/forest rows, bare upright trunks, fallen trees (side and top views), radial treefall, fireball, shock ring, smoke, altitude ruler, space rock, building, hairdryer, grass in an airflow |
| `audio/tunguska/music.json`, `sfx.json`, `mix.wav`, `cues.md`, `length.json` | soundtrack plan, the mix, the cue sheet |
| `scripts/tunguska/shots.json` | minimal shot list for `build_mix.py`, exported from `SHOT_LIST` |

## Build
```
.venv/bin/python audio/build_mix.py audio/tunguska --shots scripts/tunguska/shots.json --frames 1962
.venv/bin/python flat2d/render.py audio/tunguska/words.json OUT.mp4 --film tunguska --size 540x960 --sheet DIR   # 1962 frames
.venv/bin/python flat2d/stills.py audio/tunguska/words.json OUTDIR --film tunguska                                # review stills
.venv/bin/python flat2d/motion_qa.py OUT.mp4.frames <cut times> --impacts <designed beats>
ffmpeg -i OUT.mp4 -i audio/tunguska/mix.wav -map 0:v -map 1:a -c:v copy -c:a aac -b:a 192k -shortest videos/tunguska/tests/preview_full_540.mp4
```
`render.py` and `stills.py` now take `--film MODULE` (or `FLAT2D_FILM`), default `blood_falls`.
Final (after the Producer's pass): `render.py ... --film tunguska --size 1080x1920`, mux `mix.wav`, `tools/add_cover.sh <video> videos/tunguska/thumbnail.png <master>`, then the 2-pass posting encode as in `videos/blood-falls/NOTES.md`. 1962 frames = 65.40 s; with the 0.1 s cover **65.5 s** (62-66 s rule).

## Shot list (timed to the real voice; last word ends 64.81 s; a shot starts 0.1 s before its first word)
| shot | time s | line | picture |
|---|---|---|---|
| s01a | 0.00-4.27 | 1 | Siberian dawn over the taiga; the bolide is already streaking in at frame 0; white flash on "blast", fire column, shock ring, the near forest bends away; 1908 · SIBERIA, A BLAST, 1,000× HIROSHIMA |
| s01b | 4.27-5.56 | 1 | smoky ground after the blast: burnt trunks, logs lying away from the centre, a dashed ring where a crater should be; NO CRATER slams |
| s02 | 5.56-9.10 | 2 | top-down: the blast front sweeps outward and lays the trees flat radially; 80,000,000 TREES FLATTENED counter; the London outline (smaller) on "London" |
| s03 | 9.10-13.50 | 3 | Vanavara trading post, flash on the horizon, 60 KM; the dust wall arrives, the window bursts, TRADER · 60 KM (red shirt and cap) is thrown off the porch, lands, his shirt glows and steams |
| s04a | 13.50-17.41 | 4 | 1927 / 19 YEARS LATER; KULIK · 1927 (fur hat, backpack, compass) walks through the taiga (foot-locked, parallax); METEORITE target |
| s04b | 17.41-19.87 | 4 | night camp, campfire, tent; thought bubble CRATER → IRON |
| s05 | 19.87-22.95 | 5 | CLUE 1: Kulik with his probe shovel on the flat bog; red X over the dashed crater ring; NO HOLE, NO ROCK |
| s06 | 22.95-26.87 | 6 | CLUE 2: the 1927 survey map; the pencil maps the trunks ring by ring; red arrows shoot outward; ONE SPOT pin |
| s07 | 26.87-31.87 | 7 | CLUE 3: low angle up the bare upright trunks (overcast), Kulik looks up and points; STILL STANDING; trunk = telegraph pole card |
| s08 | 31.87-35.43 | 8 | navy diagram, phone-readable: a fireball burst above a ground disc; a ring of thick fallen logs pointing outward glows on "flattens" (FLAT), a clear gap, then tall upright bare trunks with branch stubs glow on "standing" (STANDING); big red ?; Kulik large, full figure, bottom left, thinking |
| s09 | 35.43-38.79 | 9 | purple dusk: three townspeople, bubbles COMET, ANTIMATTER, ALIEN SHIP pop on their words, each stamped ? |
| s10 | 38.79-43.20 | 10 | atmosphere cross-section, tightened to 0-10 KM (8 KM line near frame centre); THE ANSWER; a big glowing rock streaks in diagonally with a long fiery trail, the camera riding with it; on "the size of a building" it slows and a same-scale building pops in beside it, ~50-60 M ≈ A BUILDING; on "burst" it dives to the centre and bursts on the 8 KM line: white flash, shake, a flat-2D fireball, two shock rings, fragments; the 8 KM line lights up and 8 KM UP on "eight" |
| s11 | 43.20-45.55 | 11 | ground view under an orange sky: the burst in the air, the pieces burn out, only the shock sphere comes down and bends the trees; IT NEVER HIT THE GROUND |
| s12a | 45.55-49.57 | 12 | blueprint: arrows straight down onto the centre tree, its branches fly off on "lost their branches", the trunk stays; STRAIGHT DOWN, STILL STANDING |
| s12b | 49.57-52.20 | 12 | the same blueprint, panned out: slanted arrows hit the trees sideways, they fall flat on "knocked them flat"; SIDEWAYS, FLAT |
| s13 | 52.20-57.53 | 13 | a hairdryer (no brand) held over grass: airflow down then out, the blades right under it stay up, the rest bend outward; STAYS UP, BLOWN OUTWARD; a top view inset (FROM ABOVE) that rhymes with the forest map |
| s14a | 57.53-60.66 | 14 | Kulik among the bare trunks at dusk; IRON crossed out in his thought; looks up at the empty sky on "the rock never touched the ground" |
| s14b | 60.66-65.40 | 14 | 3/4 aerial: the ring of fallen trees around bare trunks, Kulik tiny at the centre; NO CRATER; a 0.3 s whip-tilt on "ones," finishes before "pointing" and lands in the s01a opening framing; "pointing at the sky." plays over s01a's own lead-in (u < 0), so the last frame is s01a one frame before frame 0 (the loop). No caption during the wipe (render.py: `info['seam']`) |

Hooks (SCRIPT.md map): 0 s bolide + flash; 4.8 s NO CRATER; 11.2 s the trader thrown; 20 s CLUE 1; 24 s outward arrows; 28 s CLUE 3 standing trunks; 32 s the big ?; 36 s the guesses; 41.4 s the burst 8 km up; 43.4 s IT NEVER HIT THE GROUND; 52.5 s the hairdryer; 61 s NO CRATER and the loop.

## Review (stills only; one fresh sonnet reviewer per round, each still with its voice-over line and shot-table row, plus an in-order sequence sheet)
| Round | richness / readability / composition | per shot (s01a … s14b) | Overall | script contradiction | 3+ run | result |
|---|---|---|---|---|---|---|
| 1 | 8.5 / 8 / 8 | 8 7.5 8 8 8 8 8 9 8 8.5 8 7 8 8 8 8.5 7.5 8 | **8.2** | none | none | **PASS** |

### v2 review (Producer's notes on the 540 preview: s10, s08, ending)
Stills of the changed shots only (`tests/stills_r2/`: s08, s10 at "building", s10 at "kilometres", the s14b last frame), each with its line; a fresh sonnet reviewer per round.
| Round | richness / readability / composition | overall | script contradiction | fixes after |
|---|---|---|---|---|
| v2-1 | 7.6 / 7.4 / 7.4 | 7.5 | none | bigger building and burst, s08 Kulik not cropped |
| v2-2..6 | 7.0-7.75 / 7.4-8.5 / 7.4-7.75 | 7.6-8.0 | none | s10 flat-2D fireball instead of the star icon, 8 KM ruler label, chip and caption off the fireball; s08 relaid (diagram up, fireball burst, Kulik larger) |
| v2-7 | 7.75 / 8.5 / 7.75 | **8.0** | none | accepted |
Per shot in v2-7: s08 8/8/7, s10a 8/8/8, s10b 8/9/8, s14b last frame 7/9/8. The last frame is s01a's opening frame by design (the loop), so its richness is the opening's. Readers keep noting that "pointing at the sky" shows no one pointing; that is the deliberate loop frame, not a contradiction.

Changes after R1 (from its fix list, gate already passed): s10 still moved before the burst, the rock is ~1.7x bigger with a longer trail, a faint 8 KM guide line from the start, the scale inset moved off the ANSWER chip; s02 London outline solid with a fill and a bigger label; s14a IRON pill in the crossed-out thought (still at 0.5 so it shows); s03 stronger heat glow on the trader's shirt. Not done: s14b Kulik stays tiny (it is a wide shot by design).

## Motion QA (`flat2d/motion_qa.py`)
v2 (1080 render, 1962 frames): same cuts, `--impacts 1.02 11.12 41.36 44.79 63.73` → **PASS** (longest frozen span 2 frames; 63.73 s is the designed 0.3 s whip-tilt into the loop frame, whose 4 high-diff frames are the only pops). The last frame differs from frame 0 by 1.17/255 (grain only).

v1: run on the 1962 rendered frames: `motion_qa.py FRAMES 4.27 5.56 9.10 13.50 17.41 19.87 22.95 26.87 31.87 35.43 38.79 43.20 45.55 49.57 52.20 57.53 60.66 --impacts 1.02 11.12 41.36 44.79` → **PASS**.
- Frozen: the longest frozen span is 1 frame (0.03 s); no span near the 0.4 s limit.
- Designed beats passed as `--impacts`: the s01a blast flash (1.02 s), the shockwave hitting the trading post (11.12 s), the burst 8 km up (41.36 s), the blast wave reaching the trees in s11 (44.79 s). Each is a white flash + shake on the word.
- First run FAILed on two non-designed pops: the s04b thought bubble (17.7 s) and the s09 COMET bubble (36.1 s) popped in too hard; both now ease in over 0.5 s with a small 6% swell, and the re-rendered ranges pass.
- Characters in holds go through `anim.actor` (breath, blinks, `anim.secondary`). Acting and feel are the Director's call on the preview.
- After the 2 s sheet check, the s03 60 KM chip was moved off the TRADER label (s03 re-rendered).

## Final cut (v2)
- `videos/tunguska/tunguska_final_1080x1920.mp4` (**committed, the posting copy**): 1080x1920, 30 fps, H.264 High, yuv420p, 2-pass 5.2 Mb/s, AAC 192k, faststart. 1965 frames (3 cover frames from `thumbnail.png` + 1962), **65.51 s**, 44.3 MB, −14.2 LUFS / −1.2 dBTP.
- Rebuild: `render.py audio/tunguska/words.json OUT.mp4 --film tunguska --size 1080x1920` (~45 min on 4 cores), mux `audio/tunguska/mix.wav` (`-c:v copy -c:a aac -b:a 192k -shortest`), `tools/add_cover.sh <muxed> videos/tunguska/thumbnail.png <master>`, then 2-pass `libx264 -profile:v high -b:v 5200k -pix_fmt yuv420p -c:a aac -b:a 192k -movflags +faststart`.
- `tests/preview_full_540.mp4` is the muxed v2 render scaled to 540x960 (no cover). `tests/sheet_2s.jpg` is still the v1 sheet.

## Sound
Serious mystery, no comedy stings. `mystery` (sus pad, ticking glock) for the event and the hunt, `explain` for the clues, `mystery` for the riddle and the guesses, `explain` for the answer, `payoff` (thin) for the hairdryer analogy, `mystery` into a loop end (a riser into the last frame, no sting). New cues in `audio/lib/sfx_x.py`: `deep_boom` (sub thump + 4 s rolling rumble) for the blast and the burst, `glass_shatter` (the trader's window), `blower` (the hairdryer), and an `amb_taiga` bed (wind in conifers, no birds; set `taiga`). Other cues: a fast whoosh on the bolide, impacts on the title slams, boom on the shockwave at the trading post and the blast wave in s11, card pops on 1927 and the CLUE badges, pings on the meteorite target and ONE SPOT, pops on the three guesses, risers into the ? and the burst, whooshes on the arrows, a puff when the trees fall flat.
Mix: −14.05 LUFS integrated, −1.20 dBTP, voice 10.2-11.5 LU over the bed per section; 1962 frames = 65.40 s (`length.json`).

## Publishing text (draft; never posted without the Director's OK)
**Title:** A Blast 1,000x Hiroshima… and No Crater ☄️ #shorts

**YouTube description:**
On 30 June 1908, something exploded over Siberia with roughly a thousand times the energy of the Hiroshima bomb. It flattened about 80 million trees over some 2,150 km² — a bigger area than Greater London — and threw a man off his porch 60 km away. When Leonid Kulik finally reached the site in 1927, hunting for a meteorite, he found no crater and no rock: only trees lying outward from one spot, and bare trunks still standing at the centre. The answer: a space rock roughly the size of a building burst apart about 5-10 km up. Only its blast reached the ground — straight down at the centre, sideways further out.

Sources: Tunguska event (Wikipedia, incl. eyewitness accounts) https://en.wikipedia.org/wiki/Tunguska_event · NASA, "The Tunguska Impact – 100 Years Later" https://science.nasa.gov/science-research/planetary-science/the-tunguska-impact-100-years-later/ · Greater London area https://en.wikipedia.org/wiki/Greater_London
Kulik's "find the crater, find the iron" is a paraphrase of his meteorite-iron hunt, not a quote.

#tunguska #siberia #science #space #mystery #shorts

**FB/TikTok caption (193 bytes, ≤ 255):**
Kulik hunted the meteorite for years. 1908: a blast ~1,000x Hiroshima flattened 80 million Siberian trees and left no crater. A space rock burst ~8 km up. ☄️🌲 #tunguska #science #mystery

## Open notes
- The acting and the feel are the Director's call on `tests/preview_full_540.mp4`.
- s14b → s01a loop: a vertical tilt from the ring into the exact s01a frame 0 (bolide already in frame), so the restart has no pose jump.
- Render cost is about 3-4 frames/s on 4 cores at 540 output (frames are drawn at 1080 and downscaled), about 10 min for the preview.
