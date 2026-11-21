# Producer handoff (read this first)

The project state for a new Producer session. Then read `PIPELINE.md`, `QA.md`, `LESSONS.md` and `BACKLOG.md`. Updated 2026-11-21.

## The Director (the user)
- **Reply in Vietnamese**, briefly and plainly. Keep code, docs and commits in English. **Videos are in English.**
- **Style target:** 2D bean-head cartoon characters over bright 3D toon sets, daylight by default, readable joke signage, medium/close framing. The numbers are in `references/reports/recent_style_2026-11.md` and `characters.md`. A second channel in the genre is studied in `segment_zero_2026-11.md`. Share the style only: never copy scripts, characters, shots or titles, and never name another channel in a video.
- **Cast:** our own bean-heads (`characters/`). The stickman is on hold, but its anatomy and animation rules (`stickman/DRAWING_RULES.md`) apply to every character.
- **Length: always a little over 1 minute (62-66 s, never under 61 s).** YouTube Shorts is the platform that pays per view for us; TikTok's Creator Rewards needs an eligible country and >1 min.
- **Captions:** the "sentence" style (Poppins Bold, 1-2 words as written, white), picked on 2026-11-21 (`PIPELINE.md` › Captions).
- **Lean crew, nothing extra and nothing missing:** see "How to run the crew" below. **No scheduled tasks** unless asked. The nightly 1st AD task (`trig_01RG5qNmG98WYrpCXKiSLCjq`) is disabled.
- **Quality bar: 9/10 or higher on every criterion, for everything.**
- **Always ask before publishing.** Upload-Post was removed on 2026-11-21: the Director posts by hand, and we prepare the files and the text.

## Status
- **Video 1, "Why Your Bike Steers Backwards First": final, not yet posted.**
  - File to post: `videos/bike-countersteer/bike-countersteer_captions_cover_1080x1920.mp4` (draft v5, sentence captions, with the thumbnail as the first 3 frames, 64.14 s).
  - Also: `thumbnail.png`. The proposed title and captions are in `videos/bike-countersteer/NOTES.md`.
  - The draft history and open nice-to-haves are in the same NOTES file.
  - **The Director decided (2026-11-21) not to remake it.** It has the pacing and story weaknesses found in the retention study, so the lessons go into the next video. Posting it is the Director's call.
- **Video 2: "sailing-stones"** (topic M4 in `scripts/TOPICS.md`, picked 2026-11-21). A Screenwriter session writes the script on `claude/area-scripts`; the Director approves the script before voicing.
- **Next video:** start at `PIPELINE.md` › Stage gates, with a fresh Screenwriter session. It must apply, from the start:
  - the leaders' story engine (`QA.md` › scripts; `references/reports/retention_2026-11.md` §8);
  - a picture change every ≤ 1.5 s and a mid-action hook (preflight warns);
  - the shot grammar (`replication_playbook_2026-11.md` §3E);
  - "sentence" captions;
  - an ending on a gag or a loop.
  - Before its render, the P1 engine items should be in: the grade vignette and split tone, depth-tested characters, and fly-through clips.
- **Known channel problem:** posted shorts keep at most about 50% of their length (the Director's analytics). The causes and fixes are in `references/reports/retention_2026-11.md`.

## Accounts and limits
- **ElevenLabs** (proxy-injected, `api.elevenlabs.io`): free tier, 10,000 characters a month; 1,251 were used in November. One video is about 1,250 characters. Voice each script **once**.
- **Claude usage:** one 5-hour limit is shared by **all** sessions. Six parallel sessions hit it within hours and stalled for about 5 h each time.
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
- **The standard for everything is ≥ 9/10** (`QA.md`): iterate with fresh reviewers until every criterion passes, with no round cap, and report every 3 rounds. To save usage, review cheap previews (low-res stills, storyboards, crops) before expensive renders.
- Crew sessions push to `claude/area-<area>`. The Producer merges into the integration branch `claude/busy-maxwell-tkdir9`, keeping both sides of LESSONS/BACKLOG conflicts.
- Messages sent to a rate-limited session are lost. After a reset, resend the full instructions, not "continue".
- Kept session: Sound Designer `session_01CUE8441Kj9vhQtH74MvcqK` (it can voice the next script). All other first-video sessions are archived.

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
