# Producer handoff (read this first)

This is the state of the project, written by the first Producer session before it was archived on 2026-11-21. A new Producer session starts by reading this file, then `PIPELINE.md`, `QA.md`, `LESSONS.md` and `BACKLOG.md`.

## The user (the Director)
- **Reply in Vietnamese**, briefly and plainly. Keep code, docs and commits in English.
- **Videos are in English**, for a global audience.
- **Target quality: the "Ricks Clips" YouTube channel style.** That means 2D bean-head cartoon characters over bright 3D toon sets, daylight by default, readable joke signage, and medium/close framing. The measured targets are in `references/reports/recent_style_2026-11.md` and `references/reports/characters.md`.
- Never copy their characters, scripts or shots. Share the style only, and never name the channel in our videos.
- **Main cast: our own bean-head characters** (`characters/`). The stickman (`stickman/`) is **on hold**, reserved for later. Its anatomy and animation rules (`stickman/DRAWING_RULES.md` 1-29) still apply to every character.
- **Captions: dynamic word-by-word captions are ON** (decided 2026-11-20; spec in `PIPELINE.md` › Captions).
- The user waived script approval for the first video. **Always ask before publishing.**
- The user cares about usage and cost, and asked to keep sessions lean (see "How to run the crew").

## First video: "Why Your Bike Steers Backwards First" (countersteering)
- Script: `scripts/bike-countersteer/` (SCRIPT.md, shots.json v2; the voice-over is locked).
- Audio: `audio/bike-countersteer/`. The voice is ElevenLabs "Liam"; 64.033 s = 1921 frames; `mix.wav` at -14 LUFS.
- **Latest: `videos/bike-countersteer/draft_v2.mp4`.** It has captions, the brightness grade, the fixed rear-view motorbike, the broom insert and countersteer cue arrows. qa.py passes every hard check, and frame stats pass 43/65. The independent full-cut review scored clarity 5; its two blockers were fixed but not re-reviewed.
- **Status: waiting for the Director's decision on draft v2:** publish, polish to v3, or other feedback.
- Nice-to-haves for v3 (see `videos/bike-countersteer/NOTES.md`):
  - s18: Dale is small behind the near instructor;
  - s15: the riders are specks on track_wide;
  - the "?" at 36 s is small;
  - the ghost hand on the broom card is faint.
- To publish, propose a title, description and hashtags, then **ask the user** which platforms and when. Upload-Post is connected (`api.upload-post.com`; the proxy injects the key). Nothing has been published yet.

## Accounts and limits
- **ElevenLabs:** connected through the proxy (`api.elevenlabs.io`). The user replaced the key on 2026-11-19; it is the FREE tier: 10,000 characters a month, 1,251 used. One video is about 1,250 characters. Generate the real voice-over **once** per script.
- **Claude usage: a shared 5-hour limit across ALL sessions.** Six parallel sessions hit it within hours and stalled for about 5 h each time.
- **Environment `claude-animated-shorts`:**
  - The setup script installs `.venv` (bpy 5.3, Pillow, numpy, yt-dlp) and clones the CC0 packs into `packs/` (KayKit x3, quaternius-showcase).
  - Allowed hosts: YouTube (`www.youtube.com`, `i.ytimg.com`), Poly Haven (`api.polyhaven.com`, `dl.polyhaven.org`), `kenney.nl` (it blocks automated clients anyway).
  - There is no GPU; plates are CPU stills, which is fine.

## How to run the crew (lessons from the first video)
- **A new video gets a fresh set of sessions.** Long sessions re-read their whole history on every turn, so they get expensive. Everything a fresh session needs is in the repo.
- **Run 2-3 sessions at a time, not 6.** A suggested order:
  1. Screenwriter (topic + script + shots.json; the user picks the topic).
  2. Sound (voice once) and Production Designer (new sets only if needed), in parallel.
  3. Costume/VFX only for new characters, props or effects.
  4. Animator renders the draft, with qa.py plus one independent full-cut review.
- At most 2 reviewer rounds per item unless something fails.
- Each crew session works on its own branch `claude/area-<area>`. The Producer merges into the integration branch `claude/busy-maxwell-tkdir9`, resolving LESSONS/BACKLOG conflicts as a union. Then the Producer tells the dependent sessions.
- **Messages sent to a session that is rate-limited are lost.** After a limit reset, resend the full instructions, not "continue".
- Do not run an hourly check trigger inside a long Producer session: every fire re-reads the whole history. The hourly crew-check trigger is **disabled**.
- The nightly "🌙 1st AD" scheduled task (`trig_01RG5qNmG98WYrpCXKiSLCjq`) was **disabled at the Director's request on 2026-11-21**. Do not re-enable it unless asked. The Producer integrates branches.

## Where the knowledge lives
| What | File |
|---|---|
| Areas, contracts, **stage gates (preflight, storyboard)**, branches, captions, self-check loop | `PIPELINE.md` |
| Where defects are born and caught (study) | `references/reports/defect_origins_v1.md` |
| Per-area checklists and the reviewer protocol | `QA.md` |
| General lessons (tools, look, process) | `LESSONS.md` |
| Work queue per area | `BACKLOG.md` |
| Reference style numbers | `references/reports/*.md`, `references/scripts/frame_stats.py` |
| Character style and API | `characters/README.md`, `characters/RULES.md`, `references/reports/characters.md` |
| Anatomy and animation rules (the user's corrections) | `stickman/DRAWING_RULES.md` |
| Sets: plates and JSON | `blender/sets/*/`, `blender/README.md` |
| FX catalogue | `fx/CATALOG.md` |
| Engine usage, captions, grade, QA | `engine/README.md` |
| Audio pipeline and voice choice | `audio/VOICE.md`, `audio/tts.py`, `audio/build_mix.py` |
| Per-video notes | `videos/<slug>/NOTES.md` |

## Archived sessions (first video)
The Producer, Screenwriter, Production Designer, Costume Designer, VFX Artist and Animator sessions were archived after this handoff. Their work is all on the branches above and in the integration branch. The Sound Designer session (`session_01CUE8441Kj9vhQtH74MvcqK`) was kept, because it is short and can voice the next script.
