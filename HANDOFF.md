# Producer handoff (read this first)

The project state for a new Producer session. Then read `PIPELINE.md`, `QA.md`, `LESSONS.md` and `BACKLOG.md`. Updated 2026-11-23.

## The Director (the user)
- **Reply in Vietnamese**, briefly and plainly. Keep code, docs and commits in English. **Videos are in English.**
- **Style target:** 2D bean-head cartoon characters over bright 3D toon sets, daylight by default, readable joke signage, medium/close framing. The numbers are in `references/reports/recent_style_2026-11.md` and `characters.md`. A second channel in the genre is studied in `segment_zero_2026-11.md`. Share the style only: never copy scripts, characters, shots or titles, and never name another channel in a video.
- **Cast:** since video 3, white stickmen with black outline (see "Current format"). The bean-heads (`characters/`) were videos 1-2. `stickman/DRAWING_RULES.md` applies to every character.
- **Length: always a little over 1 minute (62-66 s, never under 61 s).** YouTube Shorts is the platform that pays per view for us; TikTok's Creator Rewards needs an eligible country and >1 min.
- **Captions:** the "sentence" style (Poppins Bold, 1-2 words as written, white), picked on 2026-11-21 (`PIPELINE.md` › Captions).
- **Lean crew, nothing extra and nothing missing:** see "How to run the crew" below. **No scheduled tasks** unless asked. The nightly 1st AD task (`trig_01RG5qNmG98WYrpCXKiSLCjq`) is disabled.
- **Quality bar: each visual stage's overall score ≥ 8/10** (updated 2026-11-21 evening). **Scripts are exempt since 2026-11-22: no score gate; the Director approves them directly.** Iterate until it passes and until there is a finished video.
- **Comedy: none since video 3** (the Director, 2026-11-22: serious mystery tone). Old note, videos 1-2 only — **ABSURD** (picked 2026-11-21 over slapstick and deadpan). Lean into absurd escalation and imagined cutaways (e.g. aliens playing air hockey with boulders), always framed as a character's fantasy or a joke, never as fact. One deadpan line can land the payoff.
- **Always ask before publishing.** Posting goes through the **Buffer API** (`PIPELINE.md` › Publishing; connected 2026-11-21: YouTube, TikTok, Facebook). Videos need a public URL. Upload-Post was removed.

## Current format (since video 3; the Director's decisions of 2026-11-22/23 — these override older notes below and in PIPELINE/QA)
- **Content:** a surprising TRUE story told as a mystery: hook → the wrong explanation → it is debunked RIGHT AFTER (Director) → CLUE 1-2-3 → the real answer with one everyday analogy → a loop ending. **No comedy** (serious mystery tone). A hook about every 10 s (keep a hook map in SCRIPT.md). Facts sourced at the top of SCRIPT.md; dramatised bits marked. **No score gate on scripts** (no panel, no facts score): the Director reads `scripts/<slug>/REVIEW_VI.md` (EN/VI side by side + shot table + hook map) and approves.
- **Length:** 215-220 words → voice ~64-65 s, final 62-66 s incl. the 0.1 s cover.
- **Look:** white stickmen with black outline (`stickman/`, goggles/hair/hats as identity items), coloured role labels, **rich flat 2D** (`flat2d/` kit: layered depth, haze, glow, particles, texture), backgrounds in any colours that fit. **Continuous animation** throughout (no frozen span > 0.4 s), not a cut timer. House "sentence" captions with the clean-band nudge (off faces and torsos).
- **Voice:** from video 6 on, **Kokoro `am_adam`** (free, local, unlimited; chosen by the Director 2026-11-23). `audio/kokoro_tts.py` makes voice + estimated word timings (per sentence, split by letters); models download from the kokoro-onnx GitHub release (HuggingFace is blocked). Speed ~1.16 fits 216 words into ~65 s. Videos 1-5 used ElevenLabs "Liam" (free tier: ~2,349 chars left until 2026-12-20).
- **Judging visuals** (`QA.md` › How visuals are judged): a sonnet reviewer scores stills only (richness/readability/composition ≥ 8), each still WITH its line (script contradiction = FAIL) plus a sequence sheet (no 3+ similar shots in a row); motion via `flat2d/motion_qa.py` (PASS/FAIL); acting/feel = the Director. The Producer reviews the 540 preview's 2 s sheet against the script before any 1080 final.
- **Flow that worked (videos 4-5, ~1.5-2 h each):** Producer writes the script + REVIEW_VI → Director OK → Producer voices → ONE Animator session "build + 540 preview + thumbnail + NOTES, then STOP" → Producer pass → ONE Animator session "fixes + 1080 final + <45 MB posting copy" → Director OK → post. Watch a session with a background `git ls-remote`/`git cat-file` poll on its branch (cross-session messages are refused here).
- **Thumbnail:** `tools/thumbnail.py` on a caption-free frame (render with `HIDE_UI`, monkeypatch titles/chips), character fully inside, no cut labels; the Director likes a clear visual comparison (video 5: whale + VOLUME panel + red rings rising from below).
- **Posting:** Buffer for TikTok + Facebook (schema in PIPELINE › Publishing; files via the public media repo + Pages). **YouTube:** Buffer allows ~1 post per channel per 24 h; the Director often uploads YouTube by hand. For hand uploads use a high-quality **1080x1920 (Full HD)** copy with no 45 MB limit (e.g. CRF ~16); **no 1440p upscale** (the Director, 2026-11-23). The 5 Mbps posting copy looked blocky on YouTube (video 5). After posting, check the YouTube thumbnail (`i.ytimg.com/vi/<id>/hqdefault.jpg`).
- **One copy only (the Director, 2026-11-23, video 6):** YouTube can use the same <45 MB posting copy as TikTok/Facebook; no separate high-quality YouTube copy is needed (this replaces the CRF ~16 hand-upload note above).
- **Cadence advice given:** max 1 video/day, ~24 h apart, ~6:30 VN (US evening peak); 2-3/week is sustainable.

## The Blood Falls formula (video 3 went viral; the Director, 2026-11-23: "learn its presentation again" — apply to every new video)
1. **Topic = one impossible image named with a body/life metaphor:** "a glacier that BLEEDS". Ice can't bleed → the contradiction is understood in 1 s, no number to decode.
2. **Title and thumbnail = that metaphor + a time anchor**, metaphor in the key colour: THIS GLACIER / IS BLEEDING / SINCE 1911. The hero image fills the thumbnail (red stream on white ice) with the witness reacting beside it.
3. **Line 1 = a human witness meets it:** "In 1911, geologist Griffith Taylor walked up to … and found it bleeding." Person + year + verb of discovery + the metaphor word.
4. **One hero image, one colour motif, revisited** (the red fall is on screen in ~10 of 33 two-second frames, red in almost every shot); one recurring character reacting in nearly every shot.
5. **Wrong answer stated with confidence, then killed in the next line:** "It's red algae. Mystery solved." → "But … there was no algae."
6. **3 clues, each a single concrete fact** with one picture; a riddle question before the answer ("So if plants aren't making it red, what is?").
7. **The reveal flips the metaphor in two short sentences:** "The glacier isn't bleeding. It's rusting." (big on-screen title). Then one everyday analogy (a wet nail turning orange).
8. **Loop:** the last line returns to the opening year and image ("…still painting the snow red, like in 1911").
Versus Tunguska (60% stayed): opened on a number comparison (1,000x Hiroshima), no single hero image, no metaphor flip.

## Status (2026-11-23)
| # | Slug | Title | State |
|---|---|---|---|
| 1 | `bike-countersteer` | Why Your Bike Steers Backwards First | final, NOT posted (Director's call) |
| 2 | `sailing-stones` | The Rocks That Move By Themselves | posted 2026-11-22 (YT/TT/FB) |
| 3 | `blood-falls` | This Glacier Has Been "Bleeding" Since 1911 | posted 2026-11-22 (YT/TT/FB via Buffer); YouTube auto-picked a mid-video thumbnail |
| 4 | `tunguska` | A Blast 1,000x Hiroshima… and No Crater | posted 2026-11-23 (TT/FB via Buffer; YT by the Director) |
| 5 | `bloop` | The Ocean Made a Sound No Animal Could Make | posted 2026-11-23 (TT/FB via Buffer; YT by the Director). An Adam-voice version exists (`audio/bloop-adam/`, `flat2d/bloop_adam.py`, `videos/bloop/tests/preview_adam_540.mp4`) but the Liam cut was posted |
| 6 | `boiling-river` | This River Boils… and There's No Volcano | posted 2026-11-23 (YT/FB/TT all via Buffer, one <45 MB copy; Kokoro Adam voice). Buffer accepted a 2nd YouTube post the same day |
| 7 | `wind-cave` | This Cave Has Been Breathing Since 1881 🌬️ | posted 2026-11-24 (YT/FB/TT via Buffer, one <45 MB copy; Blood Falls formula; one fix pass after stills plateaued at 7.3) |
- Links/post ids: each `videos/<slug>/NOTES.md`.
- **Next topics offered (Director picks):** Dyatlov Pass 1959 (avalanche), the Mona Lisa theft 1911 (Picasso questioned), the Franklin expedition (found 2014 where the Inuit said), the Wow! signal (2024 hydrogen-cloud idea), Lake Nyos 1986, the rogue wave (Draupner 1995), Sandy Island, the 1876 Kentucky meat shower, Centralia, the 1518 dancing plague. Always ask; never pick for the Director.
- **YouTube Studio (Director's screenshot, 2026-11-23):** video 3 Blood Falls 2,921 views, 74.8% stayed / 25.2% swiped, avg view 0:53 (80.8%); video 4 Tunguska 1,199 views, 60.0% stayed / 40.0% swiped, avg view 0:46 (70.8%). Read: the swipe rate decides reach. Blood Falls opened on one strange, concrete IMAGE (a glacier bleeding red); Tunguska opened on a number comparison (1,000x Hiroshima) that needs thinking. For video 6+: first 1-2 s = one striking visual the viewer sees at once, the title words match it, no number to decode. Video 5 numbers not in yet.
- **Retention:** ask the Director for YouTube Studio screenshots (views, viewed vs swiped away, retention curve) for videos 3-5; there is no Studio access from here, and Buffer metrics only refresh once right after posting.
- **Video 7 `wind-cave` (Wind Cave breathes, 1881):** script approved 2026-11-23 (Blood Falls formula; Director: meticulous, beautiful graphics); voiced (Adam 1.16) and mixed: `audio/wind-cave/`, 1945 frames = 64.833 s. Animator `session_01CUE842fgGKnVczuprVjjiJ` → `claude/area-wind-cave` (build + 540 preview + thumbnail + NOTES, then stop; stills gate ≥ 8 strictly, no plateau stop). **Done + merged, session archived:** 540 preview + thumbnail sent to the Director. Stills stuck at 7.2-7.3 over 11 rounds (fresh reviewers noisy; ~$21 of usage). Producer notes for the fix session: the breath ribbons read as a water fountain (make them airy: wisps, dust, bent grass); s14 cabin and s05b top view plain; s13 dot net busy; s16a dark and empty. Director chose one fix pass: Animator `session_01CUE844MUC2h7F6quXXf9SR` → `claude/area-wind-cave-final` (fixes + 1080 + <45 MB posting copy, then stop). **Done, merged, archived:** `videos/wind-cave/wind_cave_final_1080x1920.mp4` 43.9 MB, 64.96 s; **posted 2026-11-24** on YT/FB/TT via Buffer (links in NOTES).
- **Video 8 `cat-righting` (why cats land on their feet, Marey 1894):** first "why" format, still on the Blood Falls formula; script approved 2026-11-24; voiced (Adam 1.16) and mixed: `audio/cat-righting/`, 1958 frames = 65.27 s (new sfx `film_clatter`, `paw_land`). Animator `session_01CUE842iSCsfPQxSYxDoKMW` → `claude/area-cat-righting` (build + 540 preview + thumbnail + NOTES, then stop; max 3 review rounds). **Done, merged, archived (~$10):** stills 6.8 → 7.0 → 7.2; preview + thumbnail sent to the Director. Producer notes: the cat drawing is crude (blocky body, odd white patches, face), the s16 chair top view unreadable (make it a side view), s01-s06 lab dark and same-y, Marey's beard covers his eyes in the thumbnail. Waiting for the Director: one fix pass + 1080, or accept.
- **Video 6 done and posted.** No crew sessions running (both Animator sessions archived). Next: ask the Director for the next topic (lists above + the 2026-11-23 list in this session: Devil's Kettle, Lake Natron, Richat, Darvaza, Naica, Giant's Causeway, Marfa lights, Kola borehole, Lake Hillier).
- **No scheduled tasks.** (Video 5 note:) This Producer session ended at ~530k tokens of context: start a fresh Producer for video 6.

## Accounts and limits
- **ElevenLabs** (proxy-injected, `api.elevenlabs.io`): free tier, 10,000 characters a month; 2,641 were used in November (after video 2). One video is about 1,250 characters. Voice each script **once**.
- **Claude usage:** one 5-hour limit is shared by **all** sessions. Six parallel sessions hit it within hours and stalled for about 5 h each time. On 2026-11-22 a **weekly-limit warning** appeared and one Animator hit the 5-hour limit in about 1.5 h: keep reviewers on sonnet, previews low-res, and at most 3 sessions.
- **Environment `claude-animated-shorts`:**
  - The setup script installs `.venv` (bpy 5.3, Pillow, numpy, yt-dlp) and clones the CC0 packs into `packs/`.
  - Allowed hosts: YouTube (`www.youtube.com`, `i.ytimg.com`), Poly Haven, `kenney.nl`.
  - No GPU; CPU renders are fine.

## How to run the crew
- **The Producer does small fixes in any area itself** (shot-list edits, parameters, one-line engine/asset tweaks), and records them in the commit and the area notes.
- **Open a specialist session only for a full area job:** a new script, a new set, a new character/rig/asset, a voice-over, or a full render plus review. Archive it as soon as its work is merged.
- **At most 3 sessions at once**, counting the Producer. A new video gets fresh sessions, because long sessions re-read their history on every turn. Usual order:
  1. Screenwriter (G1-G2);
  2. Sound, plus a set or asset only if needed;
  3. Animator (G5).
- **Judging (2026-11-22, `QA.md` › How visuals are judged): LLM reviewers score stills only (≥ 8); motion is checked automatically (PASS/FAIL); acting and feel are the Director's call on a low-res motion test.**
- **The standard for every visual stage is an overall score ≥ 8/10 (scripts exempt)** (`QA.md`): iterate with fresh reviewers until every criterion passes, with no round cap, and report every 3 rounds. To save usage, review cheap previews (low-res stills, storyboards, crops) before expensive renders.
- Crew sessions push to `claude/area-<area>`. The Producer merges into the integration branch `claude/busy-maxwell-tkdir9`, keeping both sides of LESSONS/BACKLOG conflicts.
- Messages sent to a rate-limited session are lost. After a reset, resend the full instructions, not "continue".
- No crew sessions are kept between videos.

## Where the knowledge lives
| What | File |
|---|---|
| Contracts, stage gates, captions, publishing, branches | `PIPELINE.md` |
| Checklists and the reviewer protocol | `QA.md` |
| Lessons (one line per mistake already made) | `LESSONS.md` |
| Open work per area | `BACKLOG.md` |
| Pre-render checks | `tools/preflight.py`, `tools/storyboard.py` |
| Thumbnail and cover | `tools/thumbnail.py`, `tools/add_cover.sh` |
| Channel logo and brand | `channel/` |
| How Ricks Clips and Segment Zero make shorts (start here for style) | `references/reports/channels_2026-11.md` |
| How to get their look in our stack (measured gaps, every option, plan) | `references/reports/replication_playbook_2026-11.md` |
| Why retention stops at ~50%, and the fixes | `references/reports/retention_2026-11.md` |
| Competitor titles, for originality checks | `references/titles.md` |
| Style studies (deep reference: read only the section you need) | `references/STYLE_BIBLE.md`, `references/reports/*.md` |
| Characters: API and rules | `characters/README.md`, `characters/RULES.md`, `stickman/DRAWING_RULES.md` |
| Sets, plates, depth maps, racing lines | `blender/README.md`, `blender/sets/*/` |
| Engine: usage, rules, ride parallax | `engine/README.md`, `engine/RULES.md`, `engine/parallax.py` |
| FX | `fx/CATALOG.md`, `fx/RULES.md` |
| Audio | `audio/README.md`, `audio/VOICE.md` |
| Per-video notes | `videos/<slug>/NOTES.md` |
