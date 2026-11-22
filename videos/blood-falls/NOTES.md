# Blood Falls: full video (flat2d v5, claude/area-flat2d-v6, 2026-11-22)

## Files
| file | what |
|---|---|
| `tests/preview_full_540.mp4` | 540x960 full-length preview with the mix (for the Director's motion/acting pass) |
| `blood-falls_final_1080x1920.mp4` | **the posting copy** (committed, under 45 MB): 1080x1920, captions, the mix, 0.1 s cover in front; 65.6 s. See "Final cut" below |
| `blood-falls_captions_cover_1080x1920.mp4` | the high-bitrate master of the same cut (over 50 MB, **not committed**) |
| `thumbnail.png` | house-style thumbnail (`tools/thumbnail.py` on a caption-free s02 frame) |
| `tests/stills_v4/` | the review stills (one per shot, 540x960) and `sheet.png` |
| `audio/blood-falls/music.json`, `sfx.json`, `mix.wav`, `cues.md`, `length.json` | the soundtrack plan, the mix and the cue sheet |
| `scripts/blood-falls/shots.json` | minimal shot list for `build_mix.py` (ids, sets, words), exported from `flat2d/blood_falls_2.py` `SHOT_LIST` |

Build:
```
.venv/bin/python audio/build_mix.py audio/blood-falls --shots scripts/blood-falls/shots.json --frames 1965
.venv/bin/python flat2d/render.py audio/blood-falls/words.json OUT.mp4 --size 1080x1920        # 1965 frames
.venv/bin/python flat2d/stills.py audio/blood-falls/words.json OUTDIR                            # review stills
.venv/bin/python flat2d/motion_qa.py OUT.mp4.frames <cut times>
```

## Shot list (timed to the real voice, `words.json`; last word ends 64.81 s)
A shot starts 0.1 s before its first word. s11, s14 and s16 are split in two.

| shot | time s | line | picture |
|---|---|---|---|
| s01 | 0.00-4.73 | 1 | 1911 geologist walks in, stops, points; THE GLACIER IS BLEEDING slams |
| s02 | 4.73-10.19 | 2 | close on the falls; recoil, hand to mouth; BLOOD FALLS sign drops |
| s03 | 10.19-14.66 | 3 | cold grade, −17°C thermometer, frost; hook punch-in on "Yet the red kept coming" |
| s04 | 14.66-18.20 | 4 | explorers' camp, RED ALGAE bubble, MYSTERY SOLVED stamp |
| s05 | 18.20-20.98 | 5 | lab: the stamp cracks, microscope view, X, NO ALGAE |
| s06 | 20.98-24.42 | 6 | CLUE 1: test tube, SALT meter (sea vs this water), Fe tile |
| s07 | 24.42-26.57 | 7 | the room darkens; plant badge crossed out; the scientist scratches his head; a big red "?" slams |
| s08 | 26.57-32.70 | 8 | CLUE 2: magnified drop, microbes pop in, sun and O2 crossed out, Fe and S stream into the microbes, which swell |
| s09 | 32.70-36.59 | 9 | CLUE 3: the crack at the foot; the water at the mouth is clear (pale blue-white, cyan edges, glinting) and only turns orange, then red, lower down after it meets the air; magnifier, CLEAR! |
| s10 | 36.59-39.19 | 10 | a big, close survey plane towing a sensor loop; a scan cone with rings sweeps down through the X-ray band of the ice; the pool lights up where the rings land; the scientist shades his eyes, then startles and points down |
| s11a | 39.19-43.06 | 11 | cross-section: 400 m arrow draws, the pool lights up and pulses, brine rises up the outflow channel |
| s11b | 43.06-45.00 | 11 | night surface: cracks spread under the scientist's boots; SEALED FOR 1,000,000+ YEARS rolls up |
| s12 | 45.00-48.14 | 12 | inside the pool, **warm amber-violet palette, canted ceiling, macro scale**: big SALT cubes, crystals freeze on the ceiling and send HEAT waves down; STILL LIQUID |
| s13 | 48.14-51.28 | 13 | **indigo** pool, big ghost Fe ions close to the lens, INVISIBLE; hook on "Until it escapes": a fast cross-fade into a cross-section of a crack in the ice, and the brine surges up toward a bright, warm surface (speed lines, spray, Fe ions, orange up-arrows) |
| s14a | 51.28-55.22 | 14 | outlet: O2 bubbles hit the stream, which rusts orange; Fe + O2 = RUST |
| s14b | 55.22-56.85 | 14 | timelapse: a wet nail rusts orange on a table (window flicks day/night) |
| s15 | 56.85-58.98 | 15 | two-shot at the rust falls: NOT BLEEDING. / RUSTING. |
| s16a | 58.98-62.51 | 16 | the RED ALGAE bubble pops on "Never"; iris dive into the sealed world of microbes |
| s16b | 62.51-65.50 | 16 | loop back to the s01 set and framing (camera eases to s01's opening values); 1911 chip |

Hooks (SCRIPT.md map): 0 s bleeding glacier; 13.5 s "yet the red kept coming" punch-in; 17-20 s stamp → NO ALGAE; 26 s "?"; 28-31 s life without sun/oxygen; 36 s CLEAR!; 41.4 s hidden pool lights; 50.4 s "Until it escapes"; 54.7 s rust flash; 57-58.5 s NOT BLEEDING / RUSTING; 62.5 s loop to 1911.

## v5 changes (the Director's three approved fixes from the Producer's review)
1. **s09 CLUE 3:** `outlet_scene(..., glints=True, clear_len=250)`. The stream is wider and clear at the crack mouth (pale white-blue core, cyan edges, twinkling glints, a cold glow). It turns orange about 250 px down, and red on the snow. s14a uses the old defaults, unchanged.
2. **40-50 s sameness:** `pool_room` takes a palette (`POOL_TEAL`, `POOL_WARM`, `POOL_INDIGO`) and a `tilt`. s12 is now warm and canted at macro scale. s13 is indigo with fewer, bigger ions. "Until it escapes" is a new composition (`escape_crack`): the brine squeezes up a crack toward warm daylight. The 0.16 s cross-fade at about 50.3 s counts as a designed beat in motion QA.
3. **s10 air scan:** the plane is ~1.8x bigger and closer. A glowing scan cone with rings sweeps down to the pool, which fills and lights up. The scientist is larger and has a reaction beat on "glacier": a startle hop, then pointing down.

## v3 open notes fixed
- **Secondary action in holds (`anim.secondary`, applied in `anim.actor` to every character):** the head leads with a slow look drift and the body lean follows 0.35 s later; the shoulders rise on each in-breath (upper arms open with the breath); the forearms beat on each stressed voice-over word (`anim.BEATS`, words of 5+ letters, set by `render.py` from words.json).
- **Captions off torsos (`render.place_band`):** body boxes (torso, legs) are derived under each face box. Faces and role labels are hard limits. Torsos are hard limits too unless no band within ±15% is free; legs cost extra. The caption width is the widest caption of the shot. s01 now nudges like the others.
- **s11a:** the pool lights up on "hidden pool" and pulses (0.85-1.0); brine blobs travel up the outflow channel toward Blood Falls; the 400 m arrow draws down on "four hundred metres".
- **s11b:** the cracks spread out from his boots (draw-on), the glow pulses, the counter rolls up.

## Review (stills only; one fresh sonnet reviewer per round, 540x960)
| Round | richness / readability / composition | per shot (s01 … s16b) | Overall | Changes before it |
|---|---|---|---|---|
| 1 | 7.5 / 7 / 7 | 8 8 8 6 8 8 7 8 7 7 7 8 7 7 6 8 7 7 8 | 7.3 | first full set |
| 2 | 8 / 7 / 7 | 8 7 8 7 9 8 7 8 8 7 8 8 8 8 8 7 8 8 7 | 7.7 | role labels as caption avoid boxes; s09 lens up; s11a plane/tag off the title; s12-s13 light shafts and bubbles; s14b window, shelf, lamp; s16a floor, rays; s16b badge moved, lighter sepia |
| 3 | 8 / 7 / 7 | 8 8 8 7 8 8 7 8 7 7 8 7 8 7 7 8 8 8 8 | 7.6 | torsos are hard caption limits (unless no band is free); s04 label over the bubble tail; s02 geologist inward; s11b scientist smaller and off centre; s15 chip moved up |
| 4 | 8 / 8 / 7 | 8 8 8 8 8 8 7 8 7 8 8 8 8 7 7 8 8 8 8 | **7.8** | s04 smaller bubble; s14a scientist inward; s12 brine glow |

**Result: 7.8, under the 8 target.** I stopped after R4, the best round so far: Claude usage is near the weekly limit, and the fix lists now repeat or misread (R3 and R4 credit captions and props to the wrong shot ids, e.g. "isn't red" under s10, the nail under s13). The weakest stills are s07, s09, s13 and s14a (7). The final render uses the R4 code.

## Motion QA (`flat2d/motion_qa.py`)
Run on the 1965 rendered frames: `motion_qa.py FRAMES 4.729 10.186 14.664 18.199 20.982 24.416 26.574 32.703 36.586 39.19 43.058 45.0 48.138 51.282 55.221 56.847 58.977 62.513 --impacts 54.59 60.73` → **PASS**:
- frozen frames: none (the minimum consecutive-frame diff is 0.41; the longest frozen span is 0 s);
- pops: none outside the cuts and the two designed beats (the s14a "rusts" flash + shake at 54.59 s, the s16a iris dive at 60.73 s).
- `motion_qa.py` change: the cut window is now −1..+6 frames, because render.py's cut punch-in settles over 6 frames. With ±1, the settle frames 2-4 after each cut were flagged as pops.
- Characters in holds: every actor goes through `anim.actor`, so breath, blinks and `secondary` (head drift, lean, shoulder rise, beats on speech) run on every frame. The acting itself is the Director's call on the preview.

## Sound
Serious mystery tone, no comedy stings (no boing, ka-ching or pizzicato "hmm?"): `mystery` (sus pad, ticking glock, no drums) for the setup and the hidden sea, `explain` (vibes arpeggio) for the clues and the rust reveal, `payoff` for the punchline, `mystery` again into a loop end (a riser into the last frame, no sting). New ambience beds in `audio/lib/sfx_x.py`: `polar` (wind and a low howl, no birds) and `under` (muffled rumble with sparse low bubbles); the lab uses the room tone. SFX: title and stamp impacts, ice cracks (frost, stamp crack, cracks under the boots, the brine squeezing out), card pops on the CLUE badges, sonar pings on the scan and the pool, risers into "what is?" and "escapes", sparkles on the microbes and "clear", a pop on the algae bubble, a whoosh on the iris dive.
Mix: −14.05 LUFS integrated, −1.20 dBTP, voice 10.3-13.3 LU over the bed per section; 1965 frames = 65.50 s (`length.json`). With the 0.1 s cover the posted cut is **65.6 s** (62-66 s rule).

## Final cut
- `videos/blood-falls/blood-falls_captions_cover_1080x1920.mp4`: 1080x1920, 30 fps, 1968 frames (3 cover frames + 1965), **65.61 s**, AAC 192k. It is 98 MB, so it is **not committed** (the limit is 50 MB). It exists only in this session's container. To rebuild it, render with `flat2d/render.py ... --size 1080x1920` (~45 min on 4 cores), mux `audio/blood-falls/mix.wav`, then run `tools/add_cover.sh <video> videos/blood-falls/thumbnail.png <out>`.
- `thumbnail.png`: a caption-free s02 frame (t = 8.9 s, zoom 1.15) with THIS GLACIER / IS BLEEDING (red) / SINCE 1911 (yellow).

## Publishing text (not posted)
**Title:** This Glacier Has Been "Bleeding" Since 1911 🩸 #shorts

**YouTube description:**
In 1911, geologist Griffith Taylor found an Antarctic glacier pouring blood-red water onto the snow. Explorers blamed red algae, but there was no algae. The real answer was sealed under 400 m of ice: a hidden pool of ancient seawater, salty and full of iron, kept liquid for over a million years and home to microbes that live without sunlight or oxygen. The water comes out clear, and the moment its iron meets the air, it rusts. The glacier isn't bleeding. It's rusting.

Sources: Mikucki et al. 2009 (Science); Badgeley et al. 2017 (Journal of Glaciology); Mikucki et al. 2015 (Nature Communications).

#bloodfalls #antarctica #science #glacier #mystery #shorts

**FB/IG caption (≤ 255 bytes):**
This Antarctic glacier has "bled" red since 1911. It's not algae and it's not blood: it's a million-year-old sealed sea of iron-rich brine that rusts the moment it meets air. 🩸🧊 #bloodfalls #antarctica #science

## Open notes
- **Stills plateaued at 7.8** (target 8). For a further pass, the reviewers keep naming these: s07 (lab clutter around the "?"), s09 and s14a (the lower third is sparse snow; the outlet set is thin), s13 (the dark pool is plain). The caption collisions are now solved by `place_band`.
- **Acting and feel are the Director's call** on `tests/preview_full_540.mp4`. Two things to watch: the secondary-action amplitude (`anim.secondary`, amt=1.0), and whether the speech beats on every 5+-letter word read as busy.
- **Loop:** s16b ends on the s01 set at s01's opening camera, but the geologist is standing and pointing while s01 opens with him walking in, so the restart has a pose jump.
- **Render cost:** ~5 s per frame per process at 1080, because of the per-frame stickman cards from the idle motion; the full render took ~45 min on 4 cores. Caching cards on quantised idle angles would cut this.
- The new ambience beds (`polar`, `under`) are in `audio/lib/sfx_x.py` BEDS; other polar videos can use them.
