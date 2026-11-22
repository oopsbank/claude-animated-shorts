# Blood Falls: full video (flat2d v4, claude/area-flat2d-v5, 2026-11-22)

## Files
| file | what |
|---|---|
| `tests/preview_full_540.mp4` | 540x960 full-length preview with the mix (for the Director's motion/acting pass) |
| `blood-falls_captions_cover_1080x1920.mp4` | the posting cut: 1080x1920, captions, 0.1 s cover in front; 65.6 s. Over 50 MB, so it is **not committed**; see "Final cut" below |
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
| s09 | 32.70-36.59 | 9 | CLUE 3: the crack at the foot; clear water turning orange then red; magnifier, CLEAR! |
| s10 | 36.59-39.19 | 10 | survey plane towing a sensor loop; scan pulses into an X-ray band of the ice; the pool starts to glow |
| s11a | 39.19-43.06 | 11 | cross-section: 400 m arrow draws, the pool lights up and pulses, brine rises up the outflow channel |
| s11b | 43.06-45.00 | 11 | night surface: cracks spread under the scientist's boots; SEALED FOR 1,000,000+ YEARS rolls up |
| s12 | 45.00-48.14 | 12 | inside the pool: SALT cubes, crystals freeze on the ceiling and send HEAT waves down; STILL LIQUID |
| s13 | 48.14-51.28 | 13 | dark pool: ghost Fe ions, INVISIBLE; hook: the crack opens and they rush up ("Until it escapes") |
| s14a | 51.28-55.22 | 14 | outlet: O2 bubbles hit the stream, which rusts orange; Fe + O2 = RUST |
| s14b | 55.22-56.85 | 14 | timelapse: a wet nail rusts orange on a table (window flicks day/night) |
| s15 | 56.85-58.98 | 15 | two-shot at the rust falls: NOT BLEEDING. / RUSTING. |
| s16a | 58.98-62.51 | 16 | the RED ALGAE bubble pops on "Never"; iris dive into the sealed world of microbes |
| s16b | 62.51-65.50 | 16 | loop back to the s01 set and framing (camera eases to s01's opening values); 1911 chip |

Hooks (SCRIPT.md map): 0 s bleeding glacier; 13.5 s "yet the red kept coming" punch-in; 17-20 s stamp → NO ALGAE; 26 s "?"; 28-31 s life without sun/oxygen; 36 s CLEAR!; 41.4 s hidden pool lights; 50.4 s "Until it escapes"; 54.7 s rust flash; 57-58.5 s NOT BLEEDING / RUSTING; 62.5 s loop to 1911.

## v3 open notes fixed
- **Secondary action in holds (`anim.secondary`, applied in `anim.actor` to every character):** the head leads with a slow look drift and the body lean follows 0.35 s later; the shoulders rise on each in-breath (upper arms open with the breath); the forearms beat on each stressed voice-over word (`anim.BEATS`, words of 5+ letters, set by `render.py` from words.json).
- **Captions off torsos (`render.place_band`):** body boxes (torso, legs) are derived under each face box. Faces and role labels are hard limits. Torsos are hard limits too unless no band within ±15% is free; legs cost extra. The caption width is the widest caption of the shot. s01 now nudges like the others.
- **s11a:** the pool lights up on "hidden pool" and pulses (0.85-1.0); brine blobs travel up the outflow channel toward Blood Falls; the 400 m arrow draws down on "four hundred metres".
- **s11b:** the cracks spread out from his boots (draw-on), the glow pulses, the counter rolls up.

## Review (stills only; one fresh sonnet reviewer per round, 540x960)
REVIEW_TABLE

## Motion QA (`flat2d/motion_qa.py`)
MOTION_QA

## Sound
Serious mystery tone, no comedy stings (no boing, ka-ching or pizzicato "hmm?"): `mystery` (sus pad, ticking glock, no drums) for the setup and the hidden sea, `explain` (vibes arpeggio) for the clues and the rust reveal, `payoff` for the punchline, `mystery` again into a loop end (a riser into the last frame, no sting). New ambience beds in `audio/lib/sfx_x.py`: `polar` (wind and a low howl, no birds) and `under` (muffled rumble with sparse low bubbles); the lab uses the room tone. SFX: title and stamp impacts, ice cracks (frost, stamp crack, cracks under the boots, the brine squeezing out), card pops on the CLUE badges, sonar pings on the scan and the pool, risers into "what is?" and "escapes", sparkles on the microbes and "clear", a pop on the algae bubble, a whoosh on the iris dive.
Mix: −14.05 LUFS integrated, −1.20 dBTP, voice 10.3-13.3 LU over the bed per section; 1965 frames = 65.50 s (`length.json`). With the 0.1 s cover the posted cut is **65.6 s** (62-66 s rule).

## Final cut
FINAL

## Publishing text (not posted)
**Title:** This Glacier Has Been "Bleeding" Since 1911 🩸 #shorts

**YouTube description:**
In 1911, geologist Griffith Taylor found an Antarctic glacier pouring blood-red water onto the snow. Explorers blamed red algae, but there was no algae. The real answer was sealed under 400 m of ice: a hidden pool of ancient seawater, salty and full of iron, kept liquid for over a million years and home to microbes that live without sunlight or oxygen. The water comes out clear, and the moment its iron meets the air, it rusts. The glacier isn't bleeding. It's rusting.

Sources: Mikucki et al. 2009 (Science); Badgeley et al. 2017 (Journal of Glaciology); Mikucki et al. 2015 (Nature Communications).

#bloodfalls #antarctica #science #glacier #mystery #shorts

**FB/IG caption (≤ 255 bytes):**
This Antarctic glacier has "bled" red since 1911. It's not algae and it's not blood: it's a million-year-old sealed sea of iron-rich brine that rusts the moment it meets air. 🩸🧊 #bloodfalls #antarctica #science

## Open notes
OPEN
