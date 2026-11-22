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
- **s11:**
  - The plane crosses (`x = 120 + 90 t`) while the radar pulses expand down its fan. The scan line sweeps the ice.
  - The brine pool glow pulses (0.9-1.0). Motes drift in the pool. Stars twinkle.
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

## Open notes
- **s11 is the weak frame:**
  - The scientist is small next to the diagram.
  - The caption crosses the ice and diagram area.
  - The bottom third is dark.
  - Next: a closer framing (crop to ice + pool), or move the scientist to a cut-in.
- **Reviewers want the scientist told apart from the geologist** (hair, goggles, a hat). The stickman wardrobe has no lab hat or goggles yet: this is a wardrobe item for `stickman/`.
- **Caption over busy areas:** reviewers keep asking for a plate. The house style forbids one, so the fix belongs in the engine's "nudge off" placement (pick a clean band), not in the frames.
- **Reviewers contradict each other on s15 staging** (pull the figures in vs. separate them). This matches LESSONS: reviewer noise is about ±1. Judge it in motion instead.
