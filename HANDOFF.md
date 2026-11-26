# Producer handoff (read this first)

The project state for a new Producer session. Then read `PIPELINE.md`, `QA.md`, `LESSONS.md` and `BACKLOG.md`. Updated 2026-11-25 (consolidated; start with "Status › Right now").

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
- **Posting:** Buffer for TikTok + Facebook (schema in PIPELINE › Publishing; files via the public media repo + Pages). **YouTube:** Buffer's `dailyPostingLimits` says YouTube 2 posts/day (TikTok 25, Facebook 35; checked 2026-11-24). Buffer's YouTube options: title, privacy, category, madeForKids, notifySubscribers, embeddable, license, isAiGenerated; no tags, playlist or custom thumbnail (the cover frame + thumbnailOffset 0 is the workaround). **In practice 1 YouTube post per 24 h** (video 8 was refused 5 h after video 7, 2026-11-24, although `dailyPostingLimits` said 2); the Director often uploads YouTube by hand. For hand uploads use a high-quality **1080x1920 (Full HD)** copy with no 45 MB limit (e.g. CRF ~16); **no 1440p upscale** (the Director, 2026-11-23). The 5 Mbps posting copy looked blocky on YouTube (video 5). After posting, check the YouTube thumbnail (`i.ytimg.com/vi/<id>/hqdefault.jpg`).
- **One copy only (the Director, 2026-11-23, video 6):** YouTube can use the same <45 MB posting copy as TikTok/Facebook; no separate high-quality YouTube copy is needed (this replaces the CRF ~16 hand-upload note above).
- **Cadence advice given:** max 1 video/day, ~24 h apart, ~6:30 VN (US evening peak); 2-3/week is sustainable.

- **Style target (the Director, 2026-11-25: "muốn dạng này"):** a stickman story short with real perspective sets (a third-party video the Director shared; frames are not kept in this public repo). Same white round-head stickmen as ours, but: cel-shaded rooms and streets with true perspective (the video 12 toolkit: persp 3D camera + toon renderer runs on CPU, no GPU needed), a camera that moves through the sets with almost no hard cuts, low/high/POV/peephole angles, blurred foreground, warm practical lights vs night blues, rich furnished interiors, characters acting inside the sets and big expressive close-ups. Keep our serious mystery tone and formula; adopt the look.
- **YouTube retention (Studio screenshot from the Director, 2026-11-25; avg view duration / avg % viewed):** Blood Falls 0:55 / 83.4%, Tunguska 0:53 / 80.8%, Bloop 0:56 / 85.7%, Boiling River 0:55 / 84.1%, Wind Cave 0:50 / 77.3% versus the "why" format: Cats 0:42 / 64.6%, Zebras 0:36 / 55.9%, Flamingo 0:41 / 64.7% (posted that day, little data). **The mystery format ("an impossible thing + a year" title) holds viewers ~15-25 points better than "Why do X…?" titles.** Shorts feed "viewed vs swiped away" (stayed to watch): Blood Falls 80.7%, Boiling River 74.0%, Tunguska 69.2%, Bloop 66.6%, Wind Cave 59.5%, Zebras 60.8%, Flamingo 55.4%, Cats 55.1%: the first frame decides most of it, and an ordinary animal (cat, zebra, flamingo) loses to a visually impossible frame 0 (a bleeding glacier). Frame future topics (even "why" topics) as a mystery: an impossible statement + a year in the title and thumbnail, not a question the viewer may already know.
- **Fix without asking (the Director, 2026-11-24: "mốt cứ thấy lỗi là sửa đừng có hỏi nữa"):** when the Producer's preview pass finds problems, open ONE fix + 1080 session straight away and tell the Director after. Topic choice and publishing still need the Director's explicit OK.

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

## Status (2026-11-25, consolidated for a fresh Producer session)
| # | Slug | Title | State |
|---|---|---|---|
| 1 | `bike-countersteer` | Why Your Bike Steers Backwards First | final, NOT posted (Director's call) |
| 2 | `sailing-stones` | The Rocks That Move By Themselves | posted 2026-11-22 (YT/TT/FB) |
| 3 | `blood-falls` | This Glacier Has Been "Bleeding" Since 1911 | posted 2026-11-22 (YT/TT/FB via Buffer); YouTube auto-picked a mid-video thumbnail |
| 4 | `tunguska` | A Blast 1,000x Hiroshima… and No Crater | posted 2026-11-23 (TT/FB via Buffer; YT by the Director) |
| 5 | `bloop` | The Ocean Made a Sound No Animal Could Make | posted 2026-11-23 (TT/FB via Buffer; YT by the Director). An Adam-voice version exists (`audio/bloop-adam/`, `flat2d/bloop_adam.py`, `videos/bloop/tests/preview_adam_540.mp4`) but the Liam cut was posted |
| 6 | `boiling-river` | This River Boils… and There's No Volcano | posted 2026-11-23 (YT/FB/TT all via Buffer, one <45 MB copy; Kokoro Adam voice). Buffer accepted a 2nd YouTube post the same day |
| 7 | `wind-cave` | This Cave Has Been Breathing Since 1881 🌬️ | posted 2026-11-24 (YT/FB/TT via Buffer, one <45 MB copy; Blood Falls formula; one fix pass after stills plateaued at 7.3) |
| 8 | `cat-righting` | Why Do Cats Always Land on Their Feet? 🐈 | posted 2026-11-24 (FB/TT via Buffer; YT by hand, Buffer hit the YouTube daily limit). First "why" format |
| 9 | `zebra-stripes` | Why Do Zebras Have Stripes? 🦓 | posted 2026-11-24 (FB/TT via Buffer); YT 2026-11-25 04:30 UTC (Buffer schedule) |
| 10 | `flamingo-one-leg` | Why Do Flamingos Stand on One Leg? 🦩 | posted 2026-11-25 (YT/FB/TT via Buffer) |
| 11 | `moth-light` | Why Do Moths Fly Into Lights? 🦋 | posted 2026-11-25 (FB/TT via Buffer); YouTube not posted (schedule cancelled by the Director) |
| 12 | `plane-windows` | In 1954, They Sank a Whole Airliner in a Tank ✈️ | posted 2026-11-25 (FB/TT via Buffer); YT sent 2026-11-26 04:30 UTC (https://www.youtube.com/shorts/OyP9p7qWaNI) |
- Links, post ids, build commands and review history: each `videos/<slug>/NOTES.md`. Scripts and sources: `scripts/<slug>/SCRIPT.md` (+ `REVIEW_VI.md` in Vietnamese).

### Right now
- **No crew sessions running.** All Animator sessions are archived. No scheduled tasks of ours (the 1 AM resume task fired and ended).
- **Buffer:** video 12's YouTube post is scheduled for **2026-11-26 04:30 UTC** (11:30 Vietnam), post `6b06ea92d1898df0f7fb6404`: check it went out. Video 11 `moth-light` is NOT on YouTube (the Director cancelled its schedule; `videos/moth-light/youtube_upload.txt` has the text if he wants it later).
- **Usage:** the 7-day usage limit was at **warning level** on 2026-11-25 (resets 2026-11-27 22:00 UTC = 05:00 Vietnam 28/11). Keep sessions lean until then.
- **Waiting for the Director:** (1) the next topic, in the NEW story format below: offered 2026-11-25: **1. the woman who lived in a stranger's closet for a year (Fukuoka, 2008; the homeowner's camera caught her after food kept vanishing)**, **2. Reg Spiers mailed himself from London to Perth in a wooden crate (1964; the airline then billed him the freight)**, **3. Mehran Karimi Nasseri lived in Paris CDG airport 1988-2006 (inspired The Terminal; died there in 2022; sensitive, the reason he got stuck is disputed)**. The Producer recommended 1. (2) the **tone** for the story format: keep our serious mystery tone, or allow the light humour of the reference. Ask before writing.

### Direction set on 2026-11-25 (read before the next video)
- **The Director writes the scripts himself from now on** (2026-11-25, after rejecting the Producer's draft `scripts/night-clock/`, an original 3 a.m. story: "no more sloppy scripts"). Wait for his script; the Producer only formats it (SCRIPT.md + REVIEW_VI.md, word count for 62-66 s), voices it and runs production. Do not write or pitch scripts unasked.
- **Format: "their" story format** (the Director, 2026-11-25: "theo dạng của họ"): a TRUE, documented human story told as a narrative with characters acting in homes and streets, ending on a twist; keep our mystery hook (an impossible thing + a year in line 1, title and thumbnail), keep sourcing every fact in SCRIPT.md. The retention data (above) is the reason for the hook rule.
- **Look: the stickman story style with real perspective sets.** Tools already in the repo, all CPU (no GPU needed):
  - `flat2d/persp.py` + `flat2d/cine.py` (video 12): 3D camera and toon renderer, DOF, grades, light, transitions (see `flat2d/README.md` › Cinematic 2D toolkit).
  - `flat2d/style_test_rooms.py` and `flat2d/style_test_rooms2.py`: the Producer's style tests (room shell, sofa, lamps, shelf, panelled door, windows with day/night views and curtains, tiled backsplash, calendar, wall phone, cabinets, rug, side table, plant, pumpkin, fake AO, high-key `STORY` grade and a `NIGHT` grade). Reached about 75% of the reference; LESSONS.md › "Style test" has the measured numbers and what is still missing (night scenes, staging, rounder bodies, prop close-ups).
  - **Faces:** `stickman.FACE_STYLE = 'ref'` (opt-in; 'house' default unchanged) + bigger-head proportions (`stickman.R = 132; SEG_LEG = 170; SEG_ARM = 112; OUT = 4.4`, set before any card is drawn), `glasses=True`, hair `('swept', colour)`. The Director asked for faces like the reference (eyes, brows, mouth): this is it.
- **Effort:** video 12's Animator ran at effort `max` (~$29.7, stills 7.6 / 7.75 / 7.4 vs ~7.2-7.3 at the default). The Producer suggested `xhigh` for the build (the new toolkit already exists), `high` for fix sessions and reviewers. Ask the Director which level for the next Animator.
- **Producer-side 1080 renders work:** for videos 11 and 12 the Producer rendered the 1080 final locally (30-50 min on 4 cores; the script pattern is in those NOTES), which saved a fix session when the preview had no real defects.
- **Cross-session messages are refused here** (`send_message` / scheduled tasks into a crew session fail with "only sessions in this same channel"); brief each session fully at creation, poll its branch with `git fetch` + `git cat-file -e`, and open a new session to continue a paused one.
- **Posting recipe that works (videos 9-12):** copy the final into the media repo (`oopsbank/some-crazy-things-media`, main) as `<slug_underscored>_1080x1920.mp4`, push, then Buffer `createPost` (`mode: shareNow`, `assets: [{video: {url, metadata: {thumbnailOffset: 0}}}]`; Facebook `metadata.facebook.type: "reel"`; YouTube `metadata.youtube {title, privacy: public, madeForKids: false, categoryId: "27"}`, text = description with sources; TikTok/Facebook text = caption <= 255 bytes). GitHub Pages needs 2-4 min, so retry the first post every ~100 s while it says "Video could not be read from its URL" (this container cannot fetch github.io itself). On YouTube `LimitReachedError` ("max 2 a day") or a refused shareNow, create the YouTube post with `mode: customScheduled, dueAt: <next day 04:30Z>`; `deletePost` works, `editPost` returns UnauthorizedError. Status: `{ post(input:{id}) { status externalLink error { message } } }`. Record ids and links in the video's NOTES.md. The scripts of the last posts are only in the old session's scratchpad: rebuild them from this description.
- **The repo is public:** never commit third-party frames, videos or other channels' material (reference frames were committed by mistake on 2026-11-25 and removed in the next commit; they remain in git history).

### Per-video notes (short; details in each NOTES.md)
- Video 7 `wind-cave`: Blood Falls formula; stills plateaued at 7.3 over 11 rounds (~$21), one fix pass.
- Video 8 `cat-righting`: first "why" video; the cat had to be redrawn in a fix pass; Marey's beard fixed by the Producer.
- Video 9 `zebra-stripes`: fix pass for a blocky cow, a tube lion, the stairs man, tiny flies.
- Video 10 `flamingo-one-leg`: fix pass for the flamingo's folded leg, sleeping neck and feathers.
- Video 11 `moth-light`: paused overnight by the Director, finished by a new session; small moths redrawn; 1080 by the Producer.
- Video 12 `plane-windows`: first cinematic 2D video, effort max, mystery title after the retention data; 1080 by the Producer.
- **Next topics offered earlier (mystery format; the Director picks):** Dyatlov Pass 1959, the Mona Lisa theft 1911, the Franklin expedition, the Wow! signal, Lake Nyos 1986, the Draupner wave 1995, Sandy Island, the 1876 Kentucky meat shower, Centralia, the 1518 dancing plague, Devil's Kettle, Lake Natron, Richat, Darvaza, Naica, Giant's Causeway, Marfa lights, Kola borehole, Lake Hillier. "Why" topics also offered: woodpecker concussions (2022), Prince Rupert's drops (1661), wombat cube poop (2018), sunflowers face east (2016), whip crack (1927), stress turns hair grey (2020), Leaning Tower of Pisa and earthquakes (2018).

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
