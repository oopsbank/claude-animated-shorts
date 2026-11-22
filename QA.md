# QA checklists

Every task ends with these checks: first the automatic checks, then your own look, then an independent reviewer.

**Updated standard (the Director, 2026-11-21, evening): every stage's OVERALL score (the mean of its criteria) must be ≥ 8/10.** **Scripts are exempt (the Director, 2026-11-22): no score gate on scripts; the Director reads and approves them directly. The ≥ 8 bar stays for all visuals (sets, plates, characters, fx, storyboards, style frames, drafts, thumbnails).** Fix and re-review until it passes, and keep going until there is a finished video. This applies to sets, plates, characters, props, fx, the engine, audio, storyboards, drafts, thumbnails.
- The overall score of each stage is ≥ 8, and all automatic checks pass. Scripts have no facts score (dropped by the Director, 2026-11-22); facts still need sources.
- Fix and re-review with fresh reviewers until it passes. There is no round cap.
- Report progress to the Producer every 3 rounds, so the Director can step in.
- Reviewers never see earlier drafts or the target score.

## Reviewer protocol
Spawn a fresh agent. Give it:
- 1-4 preview images, plus zoomed crops of the risky areas: joints, crossings, edges and faces.
- The rules that apply: `references/reports/characters.md` §2 (cast style), `stickman/DRAWING_RULES.md` (anatomy and animation) and/or the area section below.
- 1-2 reference frames from `references/frames/` for the look.

Ask it for a **score per criterion out of 10**, then a **numbered fix list with locations**, then "PASS" or "FAIL", in 200 words or fewer. Do not show it your earlier attempts or explain your intent. Map every fix to a change, and re-review after fixing.

## scripts
- [ ] `tools/preflight.py` has 0 ERROR, and `tools/storyboard.py` was reviewed (PIPELINE › Stage gates, G1-G2), before the voice-over.
- [ ] The hook is sentence 1, states a paradox as fact, and has 10-16 words.
- [ ] **A hook every ~10 s** (the Director, 2026-11-22): at about 0, 10, 20, 30, 40, 50 and 60 s there is a new question, twist, reveal or striking image. Mark them in `SCRIPT.md` (a hook map).
- [ ] Every fact has a source URL at the top of `SCRIPT.md`. Mark anything uncertain.
- [ ] It follows the leaders' story engine (`references/reports/retention_2026-11.md` §8):
  - line 1: a person doing something that looks wrong (past tense, a fact);
  - line 2: "You see," plus the stakes;
  - a mocking rival in quoted dialogue, whose way wins first;
  - 3 escalating stages with markers;
  - the mechanism late and short, with one everyday analogy;
  - the rival's way fails spectacularly;
  - a punchline or a loop line back into line 1.
- [ ] **225-240 words**, so the voice runs 62-66 s at about 3.6-3.7 words/s: always a little over 1 minute, never under 61 s. Plain spoken English.
- [ ] The story, characters and jokes are original: no topic angle or title overlaps `references/titles.md`.
- [ ] Every sentence has a visual in `shots.json`, and each shot uses an existing set, cam and light, or adds the set to `BACKLOG.md`.
- [ ] Reviewer scores: hook, clarity, humour, accuracy and visual potential.
- [ ] **Engagement review** (a second, separate reviewer that plays a bored phone viewer, not an editor). It gets only the voice-over with the time of each sentence (about 3.7 words/s), and answers:
  - At each 5 s mark, would I keep watching, and why? (a new question, a twist, a laugh, a stake)
  - Where is the first moment I would swipe?
  - Is there an open question I need answered at 15 s, 30 s and 45 s?
  - Is the ending a payoff or a loop that makes me rewatch?
  - Score "would watch to the end" out of 10, compared with the leaders' story engine (`references/reports/retention_2026-11.md` §8).

  **Bar raised by the Director (2026-11-21): a panel of 3 fresh engagement reviewers, each a different viewer:**
  1. a 16-year-old TikTok scroller;
  2. a curious adult on YouTube Shorts;
  3. a regular viewer of the leading channels, who compares directly with their story engine.

  Plus one **comedy reviewer** (are the gags actually funny, in the Director's preferred **absurd** style: absurd escalation and imagined cutaways, framed as a character's fantasy, never as fact?) and one **fact checker** (is every claim true and sourced?).
  - **Pass** (the Director, 2026-11-21, option B, after 8 rounds showed that fresh reviewers disagree by about ±1):
    - **the median of the 5 panel scores ≥ 8**; (**suspended 2026-11-22: scripts have no score gate; a panel, if run, is advisory only**)
    - **no swipe point before 50 s** from any engagement reviewer;
    - (no facts score: dropped by the Director, 2026-11-22).
  - Every round uses fresh reviewers with no view of earlier drafts or of the target score. Stop as soon as the panel passes; if it plateaus for 3 rounds, report to the Producer.
  - The real test is the posted video's retention.
  - Story-engine conventions (for example "You see," as line 2) are tools, not rules: drop one if the panel says it hurts.

## sets
- [ ] `build.py` rebuilds the set from scratch with no manual steps, and renders every cam × light plate.
- [ ] Every plate is 1080x1920 with no character in it, and has a `.json` with ground_y, px_per_m, horizon_y and tint.
- [ ] Style: stylised CC0 models (not photo scans), thin dark ink lines, saturated colour, readable silhouettes, depth haze or DOF, and at least 2 depth layers.
- [ ] Night and golden lights carry warm practicals against cool shadows. Emissives keep their colour, never washing out to white.
- [ ] Composition leaves clear ground space at roughly 0.35-0.65 of the frame width for characters.
- [ ] Reviewer scores: colour, lighting, ink, depth, composition and "would a character read clearly here".

## wardrobe (characters, bean-head cast)
- [ ] Matches the spec in `references/reports/characters.md` §2: proportions, head shape, plum variable-width ink, thin stroke limbs, dot hands, face layout, no blush or catchlights, and crescent shading.
- [ ] Anatomy rules from `stickman/DRAWING_RULES.md` hold: each arm from its own shoulder, continuous strokes, and foreshortening.
- [ ] Hats sit low (covering about 25% of the head) and never hide the eyes. Brows sit just under the hat base. Props are held at the dot hand, read clearly at video size, and never float.
- [ ] Clothing is clipped to the torso with at most 5 details.
- [ ] `cast_sheet.py` (or a new sheet script) shows every new item.
- [ ] Old calls to `character()` still work.
- [ ] The character is original, not a copy of a reference character.
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
