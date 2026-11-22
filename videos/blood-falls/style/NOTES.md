# Blood Falls style frames (flat2d kit), 2026-11-22

Frames: `s01_style.png`, `s05_style.png`, `s11_style.png` and `s15_style.png`, at 1080x1920. Build them with `.venv/bin/python flat2d/style_frames.py videos/blood-falls/style`.

## How each frame animates (layers that move; nothing is ever frozen)
- **All outdoor frames:**
  - The sky clouds drift (`t*12` px/s).
  - The far and near ranges move with the camera pan at 0.2x and 0.45x (parallax). The foreground silhouettes move at 1.6x.
  - The haze breathes. The sun rays rotate ±2° and flicker.
  - Snow falls on 3 depth planes (`snow_particles(t)`).
  - Characters breathe and blink (DRAWING_RULES 28). Labels bob with the head.
- **s01:**
  - The geologist walks in, stops (overshoot, settle) and swings the arm into the point. The rim light rides along.
  - The highlight dashes in the falls scroll down (`blood_falls(t)`). The red glow pulses. The red fan creeps outward.
  - The title slams in (1.15 → 1.0).
- **s05:**
  - The "MYSTERY SOLVED" stamp slams in, then cracks apart at ~0.6 s.
  - The microscope view zooms out of the eyepiece (scale 0 → 1). The X draws on, then the NO ALGAE pill pops.
  - Dust motes drift in the lamp beam. Snow drifts past the window. Bubbles rise in the flasks. The scientist's arm rises with anticipation.
- **s11 (v2, close cross-section):**
  - The plane crosses (`x = 120 + 90 t`) while the radar pulses expand down its fan. The scan line sweeps the ice.
  - The brine pool glow pulses (0.9-1.0). Motes drift in the pool. Stars twinkle.
  - The scientist cut-in (round lens frame, the same motif as the s05 microscope view) pops in (scale 0 → 1). Inside it, the scientist breathes and blinks.
  - The year counter rolls up to 1,000,000+. The 400 m arrow draws downward.
- **s15:**
  - The rust stream scrolls. The O2 bubbles drift into the flow and turn orange on contact.
  - "RUSTING." slams in after "NOT BLEEDING.". The scientist's arm rises toward the falls.

## Review (fresh sonnet reviewer each round, 540x960 downscales only)
| Round | Overall | Main changes before it |
|---|---|---|
| 1 | 7 | First kit pass |
| 2 | 7 | s11 figure larger and labelled, pool lower; crack moved between the words; s05 X lighter; s15 characters apart |
| 3 | 7.5 | All-white geologist (dark trousers); light rays and foreground framing; s05 microscope moved off the caption; s11 UI merged, RADAR SCAN tag; s15 two-shot and IRON + OXYGEN = RUST chip |
| 4 | 7.5 | Labels larger; s11 one-line title, depth gauge, TO BLOOD FALLS tag; tube rack removed |
| 5 | 7.5 | s11 strata kept off the caption band, plane bigger; s15 staging; s05 lens moved; bolder crack |
| 6 | 7.5 | Scientist coat tinted; s11 two-line title back; stronger caption shadow |

**Result: stopped on the plateau rule (R4-R6 had no gain); the target was >= 8.** In R6, the per-frame scores (richness / readability / composition / character) were:
- s01: 8/8/8/8
- s05: 8/7/7/7
- s11: 7/6/6/6
- s15: 8/7/7/7

## v2 pass (claude/area-flat2d-v2, 2026-11-22)
**What changed:**
- **Stickman wardrobe:** `stickman.draw(..., goggles=None, hair=None)`.
  - `goggles=True`: lab goggles pushed up on the forehead, never over the eyes.
  - `hair='wild'` or `'tuft'`: grey tufts behind the head.
  - Defaults are off, so old calls are unchanged. `kit.stick` takes the head geometry from a hairless card.
  - The scientist now wears goggles and wild hair in s05, s11 and s15. Every reviewer could now tell the two characters apart.
- **Caption clean band (`flat2d/kit.py`):** `busy(img, box)` and `clean_band(...)`, used through `caption(..., nudge=True)`. These pick the least-detailed band within ±7% of 70% (with a small distance cost) and skip face boxes. This is the "nudge to a clean band" rule proposed for the engine, so the caption never needs a plate. s05, s11 and s15 use it. s01 keeps the fixed 70% line, because nudging pushed its caption down over the legs.
- **s11 rebuilt:**
  - Sky cut to a strip; the ice (400 m arrow) and a wide glowing brine lens (SALTY BRINE) fill the frame.
  - The scientist moved to a round cut-in at the bottom left, with a light interior.
  - The bedrock is lifted (lighter plum, lit by the pool), so the bottom third is no longer dark.
  - The band between the pool and the cut-in is kept clean for the caption.
- **s05:**
  - Scientist bigger (1.22).
  - The NO ALGAE pill moved to the top of the lens, off the microscope arm.
  - Stamp smaller. The pocket clutter and one flask removed. The microscope moved right, clear of the caption band.
- **s15:**
  - The cliff sits higher, so the snow field under the flat rust fan is the caption band.
  - Characters bigger (0.9). The equation chip sits low between them.
  - Sastrugi, cracks, footprints and rocks added to the lower snow. O2 bubbles bigger and outlined.
- **s01:** a 1911 sledge with crates added; the title moved lower (y 300); the geologist moved inward.

**Review (one fresh sonnet reviewer per round, 540x960 only; scores are richness / readability / composition / character):**

| Round | s01 | s05 | s11 | s15 | Consistency | Overall | Main changes before it |
|---|---|---|---|---|---|---|---|
| 1 | 8/8/7/8 | 8/7/6/8 | 7/7/6/7 | 8/8/8/8 | 7 | 7 | wardrobe; s11 foreground presenter; clean bands; s15 re-staged |
| 2 | 8/8/7/8 | 8/7/7/8 | 7/6/6/7 | 8/8/8/8 | 8 | 7.5 | s05 pill on top of lens, bigger scientist; s01 sledge; s11 bolder arrow, rim |
| 3 | 8/8/7/8 | 8/7/8/8 | 8/7/6/6 | 7/8/7/8 | 7 | 7 | s11 cut-in lens; s01 title lower |
| 4 | 8/8/7/8 | 8/7/7/8 | 8/7/6/7 | 8/8/7/8 | 7 | 7.5 | s11 bigger lens, layout up; s15 bottom detail |
| 5 | 8/8/7/8 | 8/7/7/8 | 7/6/6/6 | 8/8/7/8 | 8 | 7.5 | s11 bigger sea, brighter lens; one top pill |
| 6 | 8/8/7/8 | 8/7/7/8 | 8/7/6/6 | 7/7/7/8 | 8 | 7.5 | s11 bigger labels, denser strata, lens tied to counter |

**Result:** the target of >= 8 was not reached. The best frame mean was R4 (7.5). Before this pass, R6 scored s11 at 6.25 and overall 7.5; the scientist/geologist issue is now solved in every round. I stopped after R6, with 2 rounds and no gain, one round before the plateau rule. The Producer asked to save Claude usage, and the reviewers now contradict each other round to round (s11: "show the full scientist" against "cut-in"; s05: banner "too early" against the brief's stamp beat).

## Open notes
- **s11 is still the weak frame (6-7):**
  - Reviewers read it as three stacked zones: the cross-section, the brine and the cut-in.
  - Both stagings were tried: a foreground presenter (R1-R2) and a cut-in (R3-R6). Neither got past 7.
  - Next idea: split it into two shots. s11a is the pure cross-section with the caption on the bedrock. s11b is the scientist on the ice surface in a full figure. This is a Director call, because it changes the shot list.
- **s05 readability holds at 7:** reviewers keep calling the cracked MYSTERY SOLVED stamp premature or cluttered. It is the brief's beat (the old algae theory cracks). The Director should decide whether to keep it.
- **Engine:** port `clean_band` / `busy` into the engine's caption placement (per shot, on the rendered background without characters' faces), with the same ±7% window.
- **Reviewers contradict each other on s15 staging** (pull the figures in vs. separate them). This matches LESSONS: reviewer noise is about ±1. Judge it in motion instead.

## v3 pass: s11 split + first motion test (claude/area-flat2d-v3, 2026-11-22)
Director decisions: split s11 into s11a/s11b; keep the cracking MYSTERY SOLVED stamp in s05; judge the look in motion.

**New style frames:**
- `s11a_style.png`: pure X-ray cross-section. The thick ice (400 m arrow), the glowing BRINE POOL lens and the outflow channel to Blood Falls; pool light falls on a fossil sea floor. The caption sits on the bedrock band under the pool (the pool is passed as an avoid box to `caption(nudge=True)`).
- `s11b_style.png`: the scientist, full figure (scale 1.25), on the night glacier surface under an aurora. One hand points at the glowing cracks under his boots, the other is flung up. The plane and radar ring are in the sky, and the SEALED FOR 1,000,000+ YEARS counter is on top.

**Shot renderer:** `flat2d/anim.py`, `flat2d/blood_falls.py`, `flat2d/render.py` and `flat2d/motion_qa.py` (see `flat2d/README.md`). Stand-in timings come from `scripts/blood-falls/stand_in_words.py` (3.7 words/s, 64.2 s total). Lines 1-6 end at 24.1 s.

**Motion test:** `videos/blood-falls/tests/motion_s01_s06.mp4` (0-24.1 s, 540x960, 30 fps, silent, ~6 MB). The 0.5 s contact sheets and strips of the key actions are in `tests/review_r4/`. `motion_qa.py` finds no frozen frame; the only "pops" are the cut flashes and impacts.

New shots designed for the test:
- **s02:** close on the falls. The geologist winds up, steps back (the foot lifts), lands the hand to the mouth in stages, shakes his head, and flinches when the BLOOD FALLS sign drops in and plants.
- **s03:** a cold grade and a blizzard. Icicles grow and frost creeps in. The thermometer drops while the −17°C readout rolls. The geologist shivers, his breath puffs, and the sign rattles. On "Yet the red kept coming" there is a punch-in, a shake and pulse rings on the falls.
- **s04:** an explorers' camp at dusk with a tent, a lantern flicker and a flag.
  - The leader winds up and points. The RED ALGAE speech bubble grows out of his hand, and he beats on "Tiny plants".
  - The others nod, think and cheer.
  - MYSTERY SOLVED falls in with an ink ring and a shake.
- **s06:** the CLUE 1 badge slams in. The scientist raises a sloshing, glowing test tube. A SALT meter shows SEA vs. THIS WATER, and the bar overshoots past the sea. The Fe IRON tile pops, and iron specks fly from the tube into it.

**Review (one fresh sonnet reviewer per round; contact sheets plus strips at the point, recoil, stamp slam, stamp crack and microscope X; scores are motion / richness / readability / composition / acting):**

| Round | Scores | Overall | s11a | s11b | Main changes before it |
|---|---|---|---|---|---|
| 1 | 6/8/7/7/6 | 6.5 | 7 | 6.5 | First render; geologist kept in frame in s02/s03, s01 peer beat, s02 head shake |
| 2 | 6/7/7/7/5 | 6.5 | 7 | 6.5 | Bigger stamp slam + ink ring, wider crack and more shards, slower X, deeper recoil, point settle; s11a pool lower, s11b cracks |
| 3 | 6/7/7/7/6 | 6.5 | 7 | 6.5 | Longer point wind-up (lean back), real step back, idle weight shifts, beats on key words, cut punch-in + flash, crack shake + scientist flinch, X flash; s11b bigger, startled |
| 4 | 6/7/7/6/6 | 6.5 | 7 | 7 | Stamp halves fall away, slam kept in frame, NO ALGAE earlier, slower point |

**Result:** stopped on the plateau rule (R2-R4 had no gain over R1). The target was >= 8.

## Open notes (v3)
- **Acting is the ceiling (5-6).** Every round reads the holds as "static" at 0.1 s strip spacing and on 0.5 s sheets, even with breathing, blinks, weight shifts and beats on words (LESSONS: sheets score acting at ~6). Next idea: secondary actions in holds, done at the rig (a head turn that leads the body, a shoulder rise, hands that move during speech), not more camera moves.
- **Captions over the torsos in s01/s02:** `clean_band` avoids faces only, inside a ±7% window. Pass body boxes as well, or allow a wider window when a character fills the 70% band.
- **The reviewers contradict each other and misread the strips.** R2 saw "no anticipation" in a 0.3 s wind-up; R3 said NO ALGAE was "not visible" when it showed for 0.37 s (it now shows from +0.48 s). R4 wants the stamp "to stay large until the cut" while R3 wanted it faded. This matches the ±1 noise in LESSONS. Judge the mp4 itself; a human pass is needed.
- **s11a:** the pool should pulse and the channel should show rising flow; in motion, `t` already drives the scan line, the plane and the motes. **s11b:** the reviewers want the caption off his torso, and the crack spread should be animated.
- **Render cost:** ~3 s per frame at full size, so ~10 min per 24 s test on 4 procs. Frames are cached per shot only through the cards.

## v4: full video (claude/area-flat2d-v5, 2026-11-22)
All shots s01-s16 (s11, s14 and s16 split in two) were built on the real voice. The v3 open notes are fixed: secondary action at the rig, captions kept off torsos, the s11a pool pulse and rising flow, and the s11b crack spread. Stills review: 7.3 → 7.7 → 7.6 → 7.8, stopped at 7.8 (target 8; Claude usage limit). `motion_qa`: PASS. See `videos/blood-falls/NOTES.md`.
