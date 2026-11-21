# Production pipeline: multi-session contract

> New Producer? Start with [`HANDOFF.md`](HANDOFF.md).

This repo is worked on by **several Claude sessions in parallel**, each owning one area. This file is the contract between them. Read it fully before you start, then read [`QA.md`](QA.md) (how to check your work), [`LESSONS.md`](LESSONS.md) (mistakes not to repeat) and [`BACKLOG.md`](BACKLOG.md) (what to do).

## The video we make
- A vertical 1080x1920, 30 fps, 45-65 s explainer short: "Why / How + a surprising real phenomenon".
- Our own **2D bean-head cartoon characters** (`characters/`, the main cast) act over **3D background plates** rendered in Blender (`blender/`). The stickman (`stickman/`) is **on hold**, reserved for later.
- There is a voice-over, SFX and music, and **dynamic word-by-word captions** (the user asked for them on 2026-11-20; see Captions below).
- The script formula and visual targets are in [`references/STYLE_BIBLE.md`](references/STYLE_BIBLE.md). The reference channel is study material only: never copy its scripts, characters, shots or titles, and never name it in our videos.
- Every character and story is ours. Facts must be real and sourced.

## Areas, owners and folders
Each session edits **only its own folders**. If you need a change elsewhere, add it to `BACKLOG.md` for that area's owner.

| Crew role (session name) | Area | Folder | Produces |
|---|---|---|---|
| 🎬 Biên kịch (Screenwriter) | scripts | `scripts/<slug>/` | `SCRIPT.md` (facts and sources at the top, then the voice-over) and `shots.json` |
| 🏛️ Thiết kế bối cảnh (Production Designer) | sets | `blender/sets/<set>/` | `build.py` plus rendered plates `plates/<set>__<cam>__<light>.png` with a `.json` beside each |
| 👔 Phục trang (Costume Designer) | wardrobe | `characters/` | the `character()` API: builds, expressions, arm poses, outfits, hats, hair, held props, mouth shapes, views, walk |
| 💥 Kỹ xảo (VFX Artist) | fx | `fx/` | `fx.py` with `render(name, t, size, **kw) -> RGBA PIL image` |
| 🕺 Hoạt họa (Animator) | engine | `engine/` | `render_video.py shots.json words.json -> frames -> mp4` (picture only) |
| 🎧 Âm thanh (Sound Designer) | audio | `audio/` | `voice.wav`, `words.json`, SFX, music, `mix.wav` |
| ✂️ Dựng phim (Editor) | videos | `videos/<slug>/` | final `video.mp4` (not committed if >50 MB), `qa/` reports, `NOTES.md` |

Coordination roles:
- 🎥 **Nhà sản xuất (Producer)**: the orchestrating session. It creates the crew sessions, monitors them and relays the user's decisions.
- 🌙 **Trợ lý đạo diễn (1st AD)**: the nightly scheduled task. It integrates branches, does one backlog item, and writes `reports/nightly/`.
- The user is the **Đạo diễn (Director)**: they approve topics and scripts, review drafts, and give the final OK to publish.

## Data contracts

### `scripts/<slug>/shots.json`
```json
{
  "slug": "storm-oil",
  "title": "Why Sailors Carried Storm Oil",
  "shots": [
    {
      "id": "s01",
      "text": "the voice-over words of this shot",
      "set": "harbour", "cam": "deck_wide", "light": "storm",
      "camera": {"move": "push_in", "amount": 0.05},
      "characters": [
        {"id": "captain", "color": "#4a86e0", "outfit": "sailor", "hat": "captain",
         "x": 0.5, "beats": [{"at_word": 3, "pose": "point", "expr": "angry"}]}
      ],
      "fx": [{"name": "splash", "at_word": 7, "x": 0.6, "y": 0.7}],
      "props": ["oil_bag"]
    }
  ]
}
```
- `set`, `cam`, `light` must exist in `blender/sets/`. Character `x` is the fraction of the frame width, standing on the plate's ground line.
- Timings come from `audio/.../words.json` (`[{"word": "...", "start": s, "end": s}]`). Beats are tied to word indexes within the shot, never to absolute seconds.

### Plates: `blender/sets/<set>/plates/<set>__<cam>__<light>.png` + `.json`
- PNG 1080x1920 with no characters, already post-processed (glow).
- JSON: `{"ground_y": px, "px_per_m": px at the ground line, "horizon_y": px, "light_dir": "left|right|top", "tint": "#rrggbb"}`. The engine uses it to place and scale characters and to tint them toward the scene light.
- Lights: at least `day`, `golden` and `night` for every set.

### Characters (main cast): `characters/scripts/bean.py`
- Signature: `character(build, skin, shirt, pants, expr, facing, hat, hat_col, hair, hair_col, outfit, glasses, arm_pose, prop, seed, white_head, moustache, lean) -> 600x1000 RGBA`, with the soles at y=975 (see `characters/README.md`).
- The style spec is `references/reports/characters.md` §2 (measured from the reference). It covers:
  - proportions: adult 3.5 head-heights;
  - shapes: superellipse bean heads and bean torsos;
  - ink: plum #241726, thicker on the bottom/shadow side;
  - limbs: thin ink-stroke limbs, dot hands, short feet strokes;
  - faces: lidded deadpan eyes, no blush and no catchlights;
  - shading: a soft crescent.
- The anatomy rules in [`stickman/DRAWING_RULES.md`](stickman/DRAWING_RULES.md) also apply to this cast: each arm from its own shoulder, continuous strokes, foreshortening, and animation rules 20-29.
- New options are keyword arguments with defaults, so old calls keep working.
- **Characters are our own designs.** Share the style, never copy a reference character's look.

### Stickman (on hold): `stickman/scripts/stickman.py`
- `draw(expr, pose, color, hat=None, look=0.0, fixed=False)`. Do not develop it further unless the user asks.

### FX: `fx/fx.py`
- `render(name, t, size, **kw)`: `t` runs 0..1 over the effect's life and the result is an RGBA image.
- Use flat 2D cartoon sprites in the same style as the cast: plum ink #241726 with a thick/thin line weight and soft crescent shading.
- `fx/CATALOG.md` lists every name with a preview PNG.

## Captions (engine renders them from words.json)
- **One word at a time** (2-3 only for very short words like "a", "of the"), with a hard swap on each word's start time.
- **Style:** white bold sans, about 7% of the frame height, a thick black outline (about 10% of the font size) and a soft drop shadow.
- **Placement:** horizontally centred, baseline at about 66% of the frame height. Nudge it up if a face or key prop would sit behind it.
- **Dynamic:** each word pops in, scaling 1.25 to 1.0 over 4 frames with an ease-out and a slight overshoot. **Keywords** (numbers, "left", "right", the punchline, key nouns) are yellow #ffd23f and pop bigger.
- Captions sit above FX and below nothing. They must never cover the face of the character speaking.
- Must pass: readable at phone size, in sync with the voice (each word appears 0-2 frames before it is spoken), and no caption on screen during silences longer than 0.4 s.

## Stage gates (catch defects where they are born)
Most defects in the first video were born in the shot list and caught only after a full render (see `references/reports/defect_origins_v1.md`). So nothing moves to an expensive stage until the cheap gate before it passes:

| Gate | When | Run | Pass |
|---|---|---|---|
| **G1 Script** | `shots.json` written, **before** the voice-over and before new sets/props are commissioned | `.venv/bin/python tools/preflight.py scripts/<slug>/shots.json` (stand-in timings, ~4 s) | 0 ERROR; every WARN fixed or justified in the shot's `note` |
| **G2 Storyboard** | right after G1 | `.venv/bin/python tools/storyboard.py scripts/<slug>/shots.json videos/<slug>/storyboard` (~2 min) | one reviewer reads `storyboard.jpg` against the script: each shot shows its point (who acts, which way, cause before effect, readable at phone size). The Director gets the sheet with the script. |
| **G3 Assets** | each new plate, prop or rig | re-run G2 with the new asset | the asset reads in its real shots, not only on its own sheet |
| **G4 Voice** | after G1-G2 pass | audio makes `words.json` once; re-run preflight with it | 0 ERROR with real timings |
| **G5 Draft** | full render | `engine/qa.py` + one full-cut review | as before; any defect found here gets a new preflight check or a LESSONS rule, so it is caught at G1 next time |

A missing plate is a G1 ERROR: it becomes a sets backlog item before anything is voiced.

## Publishing (channel conventions)
The channel is **Some Crazy Things**. Its publishing log is `projects/channel/PUBLISHING.md` on branch `claude/sleepy-lovelace-n8psvk` (the earlier shorts). Always ask the Director before publishing.
- **Thumbnail:** run `tools/thumbnail.py` on a caption-free engine frame. Zoom inside the engine (a camera `zoom` in a copy of shots.json), never by upscaling the frame. The house style is a 3-4 line headline in the top third: white, with the keyword line in yellow or red, a thick plum outline and a shadow. The character and the action sit below it. Save it as `videos/<slug>/thumbnail.png`.
- **Cover as the first 3 frames:** `tools/add_cover.sh video.mp4 thumbnail.png videos/<slug>/<slug>_captions_cover_1080x1920.mp4` puts the thumbnail in the first 0.1 s and delays the audio by 0.1 s. Only this captioned cut with the cover is posted.
- **Upload-Post** (`api.upload-post.com`, the proxy injects the key), profile `somecrazythings`:
  - YouTube, Instagram and the Facebook Page; send `thumbnail=@thumbnail.png` with every upload.
  - Free plan: 10 uploads a month, and each platform counts as 1. 6 of 10 were used by 2026-11-20.
  - Keep the Facebook caption under 255 bytes, or it is cut.
  - YouTube can hit a rate limit. A failed upload does not use a credit; retry later.
  - TikTok is posted by hand.
- **Length:** TikTok and Snapchat pay only for videos over 1 minute, so aim for 61-70 s.

## Branches
- Each session works on **its own branch** (given in its first message) and pushes there. Never push to another session's branch.
- The integration branch is `claude/busy-maxwell-tkdir9`. The nightly integrator task (see below) merges area branches whose `QA.md` checks pass.
- Commit small and often. Never commit `packs/`, `.venv/`, `__pycache__/`, renders over 20 MB, or anything secret.

## The self-check loop (mandatory, every task)
1. **Read** `PIPELINE.md`, `QA.md`, `LESSONS.md`, your area's rules (for example `references/reports/characters.md` §2 and `stickman/DRAWING_RULES.md`) and your `BACKLOG.md` items.
2. **Build** the smallest thing that does the task.
3. **Check it yourself** against the QA checklist for your area. Run the automatic checks, render previews, and look at zoomed crops.
4. **Get an independent review.** Spawn a fresh reviewer agent with the previews, the relevant rules and the reference frames. Ask for a score per criterion out of 10 and a numbered fix list. It must not have seen your work in progress.
5. **Fix and repeat** until every criterion is 7 or higher and the automatic checks pass. Stop after 4 rounds and record what is still missing in `BACKLOG.md`.
6. **Learn.** Every mistake you found and fixed becomes a one-line rule in `LESSONS.md` (general) or your area's rules file (specific). Phrase it as an instruction for next time.
7. **Update `BACKLOG.md`**: tick what you finished, and add what you discovered. Then commit and push.

## Human checkpoints (always ask the user)
- Approve the topic and script before any video is produced.
- Watch the draft video before it is published.
- Approve anything that publishes, spends money or deletes data.

## Environment
- The setup script installs `.venv` (Blender `bpy`, Pillow, numpy) and clones the CC0 packs into `packs/`. Run Python with `.venv/bin/python`.
- The container has no GPU. Plates are stills, so Cycles on the CPU is fine (1-3 min each). Characters are 2D and cheap.
- YouTube blocks automated downloads. Kenney.nl blocks automated user agents; never spoof one. Use Poly Haven's API and the KayKit and Quaternius git repos.
