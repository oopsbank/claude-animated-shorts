# Production pipeline: multi-session contract

This repo is worked on by **several Claude sessions in parallel**, each owning one area. This file is the contract between them. Read it fully before you start, then read [`QA.md`](QA.md) (how to check your work), [`LESSONS.md`](LESSONS.md) (mistakes not to repeat) and [`BACKLOG.md`](BACKLOG.md) (what to do).

## The video we make
- A vertical 1080x1920, 30 fps, 45-65 s explainer short: "Why / How + a surprising real phenomenon".
- Our own **2D stickman** characters (`stickman/`) act over **3D background plates** rendered in Blender (`blender/`).
- There is a voice-over, SFX and music, and no captions unless the user asks.
- The script formula and visual targets are in [`references/STYLE_BIBLE.md`](references/STYLE_BIBLE.md). The reference channel is study material only: never copy its scripts, characters, shots or titles, and never name it in our videos.
- Every character and story is ours. Facts must be real and sourced.

## Areas, owners and folders
Each session edits **only its own folders**. If you need a change elsewhere, add it to `BACKLOG.md` for that area's owner.

| Crew role (session name) | Area | Folder | Produces |
|---|---|---|---|
| 🎬 Biên kịch (Screenwriter) | scripts | `scripts/<slug>/` | `SCRIPT.md` (facts and sources at the top, then the voice-over) and `shots.json` |
| 🏛️ Thiết kế bối cảnh (Production Designer) | sets | `blender/sets/<set>/` | `build.py` plus rendered plates `plates/<set>__<cam>__<light>.png` with a `.json` beside each |
| 👔 Phục trang (Costume Designer) | wardrobe | `stickman/` | the `draw()` API: expressions, poses, outfits, hats, held props, mouth shapes |
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

### Stickman: `stickman/scripts/stickman.py`
- Signature: `draw(expr, pose, color, hat=None, look=0.0, fixed=False, **outfit_kwargs) -> 600x1000 RGBA`, with the soles at y=975.
- `pose` is a name from `POSES` or a dict of joint angles (see `anim_v2.py`).
- New outfits, hats and props are keyword arguments with defaults, so old calls keep working.
- **Every change must follow [`stickman/DRAWING_RULES.md`](stickman/DRAWING_RULES.md).**

### FX: `fx/fx.py`
- `render(name, t, size, **kw)`: `t` runs 0..1 over the effect's life and the result is an RGBA image.
- Use flat 2D cartoon sprites with a thin dark outline, in the same style as the stickman.
- `fx/CATALOG.md` lists every name with a preview PNG.

## Branches
- Each session works on **its own branch** (given in its first message) and pushes there. Never push to another session's branch.
- The integration branch is `claude/busy-maxwell-tkdir9`. The nightly integrator task (see below) merges area branches whose `QA.md` checks pass.
- Commit small and often. Never commit `packs/`, `.venv/`, `__pycache__/`, renders over 20 MB, or anything secret.

## The self-check loop (mandatory, every task)
1. **Read** `PIPELINE.md`, `QA.md`, `LESSONS.md`, your area's rules (for example `stickman/DRAWING_RULES.md`) and your `BACKLOG.md` items.
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
