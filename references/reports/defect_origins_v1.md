# Where the first video's defects were born, and where they were caught

Study by the Producer, 2026-11-21, over the 104 commits, the QA reports, `NOTES.md`, `LESSONS.md` and the area rules of "Why Your Bike Steers Backwards First".

**Finding: most defects were born in the script/shot list but caught only after a full render or a full-cut review.** Each one then cost a re-render, a review round and, for audio, ElevenLabs characters. The cheapest place to catch them is the shot list itself, before the voice-over and before any set, prop or render.

| # | Defect | Born in | Caught at | Now caught at |
|---|---|---|---|---|
| 1 | Two-shot bodies overlap; the engine spread them or stepped them back (s03, s05, s10, s16) | script (`x`) | full render v1 (engine warnings) | **preflight ERROR** |
| 2 | Face beats on a character seen from behind (s06 "grin", "smug") | script | never (wasted beats in v2) | **preflight ERROR** |
| 3 | Riders are specks on `track_wide` (s15) | script (cam choice) | full-cut review v2 | **preflight WARN** (character height) |
| 4 | Dale small behind the near instructor (s18) | script (OTS order) | full-cut review v2 | **preflight WARN** (near/far ratio) + storyboard |
| 5 | The "?" too small (s11) | script (default fx size 0.35 W) | full-cut review v2 | **preflight WARN** (symbols >= 0.40 W) |
| 6 | Left/right read mirrored in front views | script | review rounds | LESSONS rule + **preflight ERROR** |
| 7 | Countersteer flick hidden behind the body (s13) | script (rear view hides the bars) | full-cut review v2 | **storyboard** |
| 8 | Broom tipped before the hand flicked (s14): effect before cause | script/engine timing | full-cut review v2 | **storyboard** (+ rule below) |
| 9 | Motorbike didn't read as a motorbike from behind | wardrobe | draft v1 review | **storyboard** (assets judged in context) |
| 10 | Plates too dark/flat: 6 of 65 frames on target in v1 | sets (night/golden exposure) | full render v1 | sets `frame_stats`, **preflight WARN** per plate |
| 11 | Face-only beats score low on acting | script | engine test review | **preflight WARN** |
| 12 | TTS parser read the wrong section | audio | after generation | LESSONS (dry-run first) |
| 13 | Render workers OOM-killed, pool hung | engine | full render | engine RULES (not a script issue) |

Lessons drawn:
- 9 of 13 were decidable from `shots.json` + plate JSON alone. A static check costs about 4 seconds.
- 3 more (7, 8, 9) needed a picture, but only one frame per shot, not a 64 s render: the storyboard costs about 1.5 min of CPU.
- Assets were reviewed in isolation (sheets, plates) for up to 4 rounds each, then failed in context. Judge new assets in the storyboard.
- The late reviews found real problems, but too late: by then the voice was locked and every fix was a re-render.

Tools that came out of this study: `tools/preflight.py`, `tools/storyboard.py` (see `PIPELINE.md` › Stage gates).
