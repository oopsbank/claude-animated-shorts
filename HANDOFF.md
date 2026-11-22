# Producer handoff (read this first)

The project state for a new Producer session. Then read `PIPELINE.md`, `QA.md`, `LESSONS.md` and `BACKLOG.md`. Updated 2026-11-22.

## The Director (the user)
- **Reply in Vietnamese**, briefly and plainly. Keep code, docs and commits in English. **Videos are in English.**
- **Style target:** 2D bean-head cartoon characters over bright 3D toon sets, daylight by default, readable joke signage, medium/close framing. The numbers are in `references/reports/recent_style_2026-11.md` and `characters.md`. A second channel in the genre is studied in `segment_zero_2026-11.md`. Share the style only: never copy scripts, characters, shots or titles, and never name another channel in a video.
- **Cast:** our own bean-heads (`characters/`). The stickman is on hold, but its anatomy and animation rules (`stickman/DRAWING_RULES.md`) apply to every character.
- **Length: always a little over 1 minute (62-66 s, never under 61 s).** YouTube Shorts is the platform that pays per view for us; TikTok's Creator Rewards needs an eligible country and >1 min.
- **Captions:** the "sentence" style (Poppins Bold, 1-2 words as written, white), picked on 2026-11-21 (`PIPELINE.md` › Captions).
- **Lean crew, nothing extra and nothing missing:** see "How to run the crew" below. **No scheduled tasks** unless asked. The nightly 1st AD task (`trig_01RG5qNmG98WYrpCXKiSLCjq`) is disabled.
- **Quality bar: each stage's overall score ≥ 8/10** (updated 2026-11-21 evening). Iterate until it passes and until there is a finished video.
- **Comedy taste: ABSURD** (picked 2026-11-21 over slapstick and deadpan). Lean into absurd escalation and imagined cutaways (e.g. aliens playing air hockey with boulders), always framed as a character's fantasy or a joke, never as fact. One deadpan line can land the payoff.
- **Always ask before publishing.** Posting goes through the **Buffer API** (`PIPELINE.md` › Publishing; connected 2026-11-21: YouTube, TikTok, Facebook). Videos need a public URL. Upload-Post was removed.

## Status (2026-11-22)
- **Video 1, "Why Your Bike Steers Backwards First": final (v6 + cover), NOT posted.** File: `videos/bike-countersteer/bike-countersteer_captions_cover_1080x1920.mp4`; title and captions in its `NOTES.md`. The 2026-11-21 Buffer draft (`6b019df9d5eabfb8cc337d28`) points to the old file: re-upload v6 to the media repo and post fresh. Posting is the Director's call (asked 2026-11-22, no answer yet).
- **Video 2, "The Rocks That Move By Themselves" (`sailing-stones`): POSTED 2026-11-22 ~16:34** on YouTube, TikTok and Facebook (reel) via Buffer, with the Director's OK. Links and post ids are in `videos/sailing-stones/NOTES.md`.
  - The posted cut is draft v1 with the cover: G2 storyboard frozen at 7.5, G5 draft frozen at 7.1 (plateau rule). Script v17 panel PASS; sound 8.0.
  - What held the scores under 8 (fix these for the next video, BACKLOG has the details):
    - acting 6: one-frame arm swaps, small faces, the same stance for 2-4 s;
    - fx frozen at 5.8;
    - plates: playa 6.9, inserts 7.4 (dense text);
    - a few static spans.
  - Not done: the Director's listen to the 1.24x voice stretch.
- **Video 3 (decided 2026-11-22): a personified-trait stickman race ("who makes it?"), 2D, neon on dark, with a voice-over**, modelled on the structure of reference short xBqCZDzFmog. Brief: `scripts/trait-race/BRIEF.md`. The stickman is off hold for this format.
- **All crew sessions are archived.** No scheduled tasks are active (the one-time 13:00 restart fired and disabled itself; the nightly 1st AD task stays disabled).
- **Next video:** start at `PIPELINE.md` › Stage gates, with fresh sessions. It must apply, from the start:
  - the leaders' story engine (`QA.md` › scripts; `references/reports/retention_2026-11.md` §8);
  - a picture change every ≤ 1.5 s and a mid-action hook (preflight warns);
  - the shot grammar (`replication_playbook_2026-11.md` §3E);
  - "sentence" captions;
  - an ending on a gag or a loop.
  - Biggest quality gap: **acting** (`character()` arm in-betweens, bigger poses and faces). It is worth a wardrobe pass before the next render.
- **Known channel problem:** posted shorts keep at most about 50% of their length (the Director's analytics). The causes and fixes are in `references/reports/retention_2026-11.md`. Check video 2's retention when the Director shares analytics.

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
- **The standard for every stage is an overall score ≥ 8/10** (`QA.md`): iterate with fresh reviewers until every criterion passes, with no round cap, and report every 3 rounds. To save usage, review cheap previews (low-res stills, storyboards, crops) before expensive renders.
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
