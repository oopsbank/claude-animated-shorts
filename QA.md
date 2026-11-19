# QA checklists

Every task ends with these checks: first the automatic checks, then your own look, then an independent reviewer. A criterion passes at **7/10 or higher**, and all automatic checks must pass.

## Reviewer protocol
Spawn a fresh agent. Give it:
- 1-4 preview images, plus zoomed crops of the risky areas: joints, crossings, edges and faces.
- The rules that apply: `stickman/DRAWING_RULES.md` and/or the area section below.
- 1-2 reference frames from `references/frames/` for the look.

Ask it for a **score per criterion out of 10**, then a **numbered fix list with locations**, then "PASS" or "FAIL", in 200 words or fewer. Do not show it your earlier attempts or explain your intent. Map every fix to a change, and re-review after fixing.

## scripts
- [ ] The hook is sentence 1, states a paradox as fact, and has 10-16 words.
- [ ] Every fact has a source URL at the top of `SCRIPT.md`. Mark anything uncertain.
- [ ] It follows the formula: hook, setting, 3-6 escalation beats, a mystery beat, "You see,", the mechanism with an everyday analogy, and an ironic payoff.
- [ ] 170-240 words (about 3.7 words/s gives 45-65 s). Plain spoken English.
- [ ] The story, characters and jokes are original, with no overlap with the reference channel's videos (check titles in `references/` and the channel list).
- [ ] Every sentence has a visual in `shots.json`, and each shot uses an existing set, cam and light, or adds the set to `BACKLOG.md`.
- [ ] Reviewer scores: hook, clarity, humour, accuracy and visual potential.

## sets
- [ ] `build.py` rebuilds the set from scratch with no manual steps, and renders every cam × light plate.
- [ ] Every plate is 1080x1920 with no character in it, and has a `.json` with ground_y, px_per_m, horizon_y and tint.
- [ ] Style: stylised CC0 models (not photo scans), thin dark ink lines, saturated colour, readable silhouettes, depth haze or DOF, and at least 2 depth layers.
- [ ] Night and golden lights carry warm practicals against cool shadows. Emissives keep their colour, never washing out to white.
- [ ] Composition leaves clear ground space at roughly 0.35-0.65 of the frame width for characters.
- [ ] Reviewer scores: colour, lighting, ink, depth, composition and "would a character read clearly here".

## wardrobe (stickman)
- [ ] Every rule in `stickman/DRAWING_RULES.md` is met, especially 1, 8, 9, 12 and 14.
- [ ] Outfits follow the body: front view stays symmetric, and side poses layer front over back.
- [ ] Hats never cover the eyes. Props are held at the hand, never floating.
- [ ] `sheets.py` regenerates the sheets and every new item appears on a sheet.
- [ ] Old calls to `draw()` still work.
- [ ] Reviewer scores at 2x zoom on joints and crossings: silhouette, joints, colour, face and outfit.

## fx
- [ ] Every effect animates over t=0..1 with anticipation, a peak and a fade, with no pops.
- [ ] Flat 2D style with a thin dark outline and colours that sit in a night scene and a day scene.
- [ ] `CATALOG.md` has a preview strip per effect at t = 0, .25, .5, .75 and 1.
- [ ] Reviewer scores: readability, style match and timing.

## engine and video
- [ ] Automatic: no black, white or frozen spans of 12 frames or more, no character clipped at the frame edge, and characters' feet on the plate's ground line (±4 px).
- [ ] In walks, a planted foot moves ≤2 px while planted (foot locking).
- [ ] Beats land 0-3 frames before their word.
- [ ] Audio: -14 LUFS integrated, the voice is never masked, and the length matches the picture to the frame.
- [ ] Reviewer watches a contact sheet every 0.5 s and scores motion, acting, readability, pacing and look.
