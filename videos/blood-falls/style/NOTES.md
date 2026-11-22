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
