# Cat righting: "Why Do Cats Always Land on Their Feet?" (flat2d, claude/area-cat-righting → claude/area-cat-righting-final, 2026-11-24)

Video 8. Same look, tone and pipeline as videos 3-7: white stickmen with a black outline, rich flat 2D, serious mystery, no comedy, "sentence" captions, continuous motion. Voice and mix: the Producer's `audio/cat-righting/` (Kokoro `am_adam`), unchanged: 1958 frames = 65.267 s. Built on the Blood Falls formula: one hero image (the cat UPSIDE DOWN in mid-air in Marey's 1894 Paris lab, against black velvet), the sepia 1894 film strip (sprocket holes) as the motif (s01, s06, s08, s09 photo, s18 loop), Marey reacting in most shots, big titles. **Status: fix pass done (new cat, s16 side view, lab variety, Marey's face, deeper s07/s09/s18, new thumbnail) and the 1080 final rendered: `videos/cat-righting/cat_righting_final_1080x1920.mp4` (see Final). Nothing is published.**

## Files
| file | what |
|---|---|
| `tests/preview_full_540.mp4` | 540x960 30 fps preview with `mix.wav` (1958 frames) |
| `tests/sheet_2s.jpg` | 2 s contact sheet of the preview |
| `tests/stills_r1/`, `tests/stills_r2/`, `tests/stills_r3/` | review stills per round (one per shot, 540x960, captions on) + `sheet.png`; r3 is the last reviewed round |
| `tests/review_brief.md` | what each reviewer got: every still's voice-over line and planned picture |
| `thumbnail.png` | `tools/thumbnail.py` on a dedicated caption-free frame (`flat2d/cat_righting_thumb.py`): the new cat big and UPSIDE DOWN mid-air (face visible), Marey below-left on the stool with his eyes clear, the lab with warm window light and the camera; THIS CAT (white) / BROKE PHYSICS? (blue) / IN 1894 (yellow) |
| `cat_righting_final_1080x1920.mp4` | **the posting copy**: 1080 render + `mix.wav` + the 0.1 s cover, 2-pass libx264 high 5200k, AAC 192k, +faststart |
| `flat2d/cat.py` | **the cat kit (redrawn in the fix pass)**: `render_cat` / `put_cat`, a brown tabby built as two halves joined at a bendy waist, each with its own ROLL, drawn from a tiny 3D model projected flat: the body is a chain of spheres (deep rounded chest, narrow waist, round haunches), the head a skull + cheek ruff + muzzle with two almond eyes on the face, nose, mouth, whiskers, two triangular ears with pink insides; the face always turns a little toward the camera, so it reads upside down and mid-twist. Tabby stripes are tapered rings that follow the body, a dark spine line, cream belly/chest bib/muzzle/paws (soft edged), tapered legs (shoulder-elbow-wrist, hip-knee-hock) with oval paws and leg bands, a curved ringed tail with a dark tip; a form shadow + a warm rim light inside the ink line. Same API: `tuckf`/`tuckb` (0 stretched, ~.4 standing, 1 tucked), `bend`, `tail=False` (Manx), `glow` (blue front / orange back halves with masks), `seam`. `righting(p)` = the tuck-and-turn program (unchanged) |
| `flat2d/cat_righting.py` | the shots `s01`-`s18`, `SHOT_LIST`, `END`, `STILL_AT`, `HIDE_UI`; sets: the 1894 lab (cached wall + window with Paris roofs and the Eiffel Tower, velvet backdrop, floor, mattress, stool, the chronophotographic camera with a spinning disc shutter), sepia film frames + strips, the explanation stage (tinted per shot, grid, lower-third diagram panel, turn dials, tuck icons), a present-day living room, a 1968 gym with a trampoline and a spacesuit gymnast, a top-view room with a swivel chair; Marey (beard, jacket) |
| `flat2d/cat_righting_thumb.py` | the thumbnail frame |

## Build
```
.venv/bin/python flat2d/render.py audio/cat-righting/words.json OUT.mp4 --film cat_righting --size 540x960     # 1958 frames, ~25 min on 4 cores
.venv/bin/python flat2d/stills.py audio/cat-righting/words.json OUTDIR --film cat_righting                     # review stills
.venv/bin/python flat2d/motion_qa.py OUT.mp4.frames <cuts> --impacts <beats>                                   # see Motion QA
ffmpeg -i OUT.mp4 -i audio/cat-righting/mix.wav -map 0:v -map 1:a -c:v copy -c:a aac -b:a 192k -shortest videos/cat-righting/tests/preview_full_540.mp4
.venv/bin/python flat2d/cat_righting_thumb.py frame.png
.venv/bin/python tools/thumbnail.py frame.png videos/cat-righting/thumbnail.png --zoom 1.25 --focus 0.55,0.5 --line "THIS CAT|white|130" --line "BROKE PHYSICS?|blue|130" --line "IN 1894|yellow|120"
```
Final (after the Producer's pass): `render.py ... --size 1080x1920`, mux `mix.wav`, `tools/add_cover.sh <video> videos/cat-righting/thumbnail.png <master>`. Shot ids are the Producer's s01-s18 (one per line, no splits), so `sfx.json` anchors need no rebuild.

## Shot list (timed to the real voice; a shot starts 0.1 s before its first word)
| shot | time s | picture |
|---|---|---|
| s01 | 0.00-4.48 | **frame 0 = the hook**, WIDE establishing shot: the cat upside down in mid-air in slow motion, lit against the black velvet; warm window light (sun shafts, a warm floor pool) vs the dark backdrop; Marey on a stool, hands just opened above it; 1894 + PARIS; the camera's lens glints, its disc spins up and the lens flashes on "filmed"; a sepia film strip slides out along the bottom |
| s02 | 4.48-8.88 | LOW ANGLE under the falling cat (keystoned lab: verticals converge upward, the floor sinks; the mattress big in the foreground): slow-motion fall with chronophotograph ghosts, the cat bigger: it tucks, the front turns, swap, the back catches up, it lands on "feet" (squash, dust lines); Marey reacts; NOTHING TO PUSH ON |
| s03 | 8.88-10.69 | CLOSE-UP on Marey's reaction (big, warm key light on his face, eyes wide), the landed cat on the mattress beside him; arms up on "break"; BREAKING A LAW / OF PHYSICS? with a crack, shake and flash on "physics" |
| s04 | 10.69-12.99 | cool-lit lab: a wooden block with an arrow falls straight, its ghosts all point the same way; a spin arrow is crossed out on "spin"; NO PUSH, / NO SPIN; Marey thinking |
| s05 | 12.99-16.13 | the wrong answer, imagined, in strong warm window light against the dark velvet: Marey on the stool holds the cat up; on "pushed" push arrows from his hands kick it into a spin (a pale ghost of where it was); PUSHED OFF / HIS HANDS? |
| s06 | 16.13-20.45 | Marey's sepia strip scrolls up: green checks on the first four upside-down frames (NO SPIN AT FIRST), a gold box on THE TURN STARTS HERE, a red X slams on PUSHED OFF? on "mid-air" |
| s07 | 20.45-23.11 | CLUE 1, the living room (now with a sun patch on the floor, floor haze, a shaded corner and an out-of-focus plant in the near foreground): a tailless (Manx) cat twists down and lands on the rug on "too"; NO TAIL tag + a short pointer to its rump; the owner surprised |
| s08 | 23.11-26.20 | CLUE 2: one big sepia frame under Marey's brass loupe (it magnifies what it covers); the waist glows with a V mark on "bent"; BENT IN / THE MIDDLE |
| s09 | 26.20-32.08 | CLUE 3, a 1968 gym with depth: high daylight windows and light shafts, wall bars, a clock, floor mat and shine, haze, a soft-focus 1968 film camera in the near foreground (echo of Marey's); a gymnast in a white spacesuit bounces on a trampoline and twists, arms in and out; a scientist watches; 1968, NASA-FUNDED, GYMNAST; the falling-cat photo on the wall lights up on "copy it" (COPY THE CAT) |
| s10 | 32.08-34.30 | the riddle: the cat upside down floating in the dark, a big glowing ?; Marey thinking; NOTHING TO PUSH ON |
| s11 | 34.30-38.37 | ONE SOLID OBJECT? box crossed out; on "two halves" the cat splits into a BACK (orange) and FRONT (blue) half; on "bendy spine" the vertebrae glow and it bends into a V; Marey watches |
| s12 | 38.37-41.60 | front legs tuck (FRONT LEGS IN), back legs stretch (BACK LEGS OUT); lower panel: STRETCHED: WIDE vs TUCKED: SMALL (end-on icons with dashed spin circles) |
| s13 | 41.60-45.31 | the front half turns ~195° with a big blue arrow (TUCKED: TURNS A LOT); the back turns ~15° the other way with a small orange one (STRETCHED: BARELY MOVES); FRONT / BACK turn dials count |
| s14 | 45.31-49.48 | SWAP!: back legs in, front legs out (faint ghost of the old pose); the back half catches up with a big orange arrow; dials |
| s15 | 49.48-53.49 | + and − twists slide together into = 0 (TWISTS CANCEL, NO LAW BROKEN); the glowing feet-down cat drops onto the mattress on "flipped" (FLIPPED!); Marey smiles |
| s16 | 53.49-57.23 | SIDE / three-quarter view (re-staged): a white stickman on an office swivel chair (5-star base, gas column, seat, backrest) in the living room, feet off the floor; arms out + legs tucked, then arms in + legs stretched, in turns; the seat steps round one way (3 × 120°), fading motion trails behind the hands and feet, a gold turn arrow round the column; A SPINNING CHAIR, ARMS & LEGS, IN TURNS |
| s17 | 57.23-59.64 | sunset window light, the cat big and calm on the mattress, Marey nodding; DIDN'T BREAK / PHYSICS. then IT USED IT. slams (shake + flash) on "used" |
| s18 | 59.64-65.27 | today, in the deeper living room: a cat leaps off the top bookshelf, twists, lands on the rug on "lands"; the owner watches; on "that cat did" the sepia strip slides in, the camera dives into the first frame, which dissolves into **s01's frame 0 exactly** (last 7 frames, the loop) |

## Fix pass + final (claude/area-cat-righting-final, 2026-11-24)
What changed (Director's notes, one pass, audio and shot timing untouched):
1. **The cat** (`flat2d/cat.py`) redrawn: a natural silhouette from a 3D sphere-chain body (rounded deep chest, narrow waist, haunches), tapered legs with oval cream paws and leg bands, a curved ringed tail with a dark tip; a proper head (round skull + cheek ruff + muzzle, two triangular ears with pink insides, two almond eyes on the face, small nose, mouth, whiskers, forehead M) that always turns toward the camera, so it reads upside down, mid-twist and landing; clean tabby rings that follow the body + a spine line, a soft cream belly/chest bib instead of white blocks; rim light inside the ink line. The Manx (`tail=False`), the s18 modern cat, the sepia film frames and the s11-s15 two-halves glow all use it unchanged.
2. **s16** re-staged as a SIDE / three-quarter view: a white stickman on an office swivel chair, feet off the floor, swinging arms and legs in turns, the seat stepping round one way with motion trails and a turn arrow round the column, in the living room; A SPINNING CHAIR kept.
3. **s01-s06 variety**: s01 wide with warm window light vs the dark velvet; s02 LOW ANGLE under the falling cat (keystone, big cat and mattress); s03 CLOSE-UP on Marey's reaction with a warm key; s05 strong warm window light; the camera's lens glints in every lab shot (and flares on "filmed").
4. **Marey**: the side-hair tufts sat at eye level and hid an eye when he looked sideways; now at the head rim, skipped on the look side. Eyes and brows clear in every shot and the thumbnail; the beard stays on the chin.
5. **Depth** in s07/s18 (living room: sun patch on the floor, floor haze, a shaded corner, an out-of-focus foreground plant; the NO TAIL pointer is now short and next to the cat) and s09 (1968 gym: high daylight windows + shafts, wall bars, clock, mat, floor shine, haze, a soft-focus 1968 film camera in the foreground).
6. **Thumbnail** redone on the new cat: big, upside down mid-air, face visible; Marey below-left with his eyes clear; THIS CAT / BROKE PHYSICS? / IN 1894 via `tools/thumbnail.py`.

Checks: `motion_qa.py` on the 1958 final frames → **PASS** (no pops, longest frozen span 11 frames = 0.37 s); loop: frame 1957 = frame 0 (mean abs diff 0.0); one sonnet sanity reviewer on the new `tests/sheet_2s.jpg` + thumbnail: no blocking problems (minor: the NOTHING TO PUSH ON chip is small at sheet size; s08 is a slow push-in).

**Final**: `videos/cat-righting/cat_righting_final_1080x1920.mp4`, 1080x1920 30 fps, 2-pass libx264 High 5200k, AAC 192k, +faststart, **43.8 MB, 65.39 s** (0.1 s cover from `thumbnail.png` + 1958 frames, audio delayed 0.1 s by `tools/add_cover.sh`). Built: `render.py audio/cat-righting/words.json OUT --film cat_righting --size 1080x1920` → mux `mix.wav` → `add_cover.sh` → 2-pass encode. Not published. `tests/preview_full_540.mp4` is the OLD (pre-fix) preview.

## Review (stills only; one fresh sonnet reviewer per round, each still with its voice-over line and planned picture (`tests/review_brief.md`), the in-order sheet and the Wind Cave sheet as the reference)
| Round | richness / readability / composition | overall | script contradiction | 3+ run | result |
|---|---|---|---|---|---|
| 1 | 7 / 7 / 6.5 | 6.8 | s15 (no flip shown), s02 (still before the landing), s14 borderline | s11-s15, s01-s05 | FAIL |
| 2 | 7 / 7 / 7 | 7.0 | s03 (Marey calm), s06 (tag unreadable), s15, s12 borderline | s01-s05, s10-s15 | FAIL |
| 3 | 7 / 7.5 / 7 | 7.2 | none (near-misses: s04 block arrows sideways, s15 still after the twist, s07 cat small) | s01-s05, s11-s15 | FAIL (< 8) |

Fixes per round:
- R1: s11-s15 rebuilt: a per-shot tint (navy, teal, violet, plum, warm lab), a bigger cat, a lower-third diagram panel with end-on tuck icons (TUCKED: SMALL / STRETCHED: WIDE) and turn dials, the halves split visibly with glowing vertebrae, a ghost of the pre-swap pose in s14; s15 ends on the landing on the mattress (FLIPPED!); s08 without Marey's body (title clear of the frame); a warm floor light pool in the lab; s02/s15 stills moved.
- R2: s03 Marey throws his arms up on "break"; s04 cool light; bigger tags (PUSHED OFF?, NO SPIN AT FIRST, GYMNAST, labels); a bigger explanation cat and big/small rotation arrows (TURNS A LOT vs BARELY MOVES); s17 re-staged (sunset light, a big calm cat, Marey on the right) so it no longer copies s03.
- After R3 (not re-reviewed, under the 3-round cap): Marey's beard moved down onto the chin (it sat on the eyes when he leans/looks); the s07 Manx cat 30% bigger.

**The gate (overall >= 8) was not reached in the 3 allowed rounds: 6.8 → 7.0 → 7.2.** Open notes from R3, for the Producer/Director:
- s01-s05 all sit in the same lab (by design: one hero set), reviewers want more camera/colour variety there;
- s11-s15 share the stage and the panel (deliberate continuity of the explanation; each shot has its own tint);
- s04's block arrow points sideways (it marks orientation; reviewers read it as motion);
- the cat's fur is flat colour + stripes (no fur texture);
- s07/s09/s16/s18 are lighter in detail than the lab.

## Motion QA (`flat2d/motion_qa.py`)
On the 1958 rendered preview frames: `motion_qa.py FRAMES 4.48 8.88 10.69 12.99 16.13 20.45 23.11 26.20 32.08 34.30 38.37 41.60 45.31 49.48 53.49 57.23 59.64 --impacts 3.5 8.5 9.6 10.22 14.46 15.2 18.33 19.94 22.76 25.19 25.44 35.37 35.69 36.57 37.6 45.74 47.9 53.0 54.2 57.62 58.16 58.94 61.19 64.97` → **PASS** (longest frozen span 11 frames = 0.37 s, in the quiet explanation holds where only the grain boils and the glow breathes; no pops).
- The impacts are designed beats on the word: the lens flash on "filmed", the landing on "feet", the arms-up and crack on "break"/"physics", the title slams (PUSHED OFF / HIS HANDS?, THE MIDDLE, TWO HALVES, SWAP!, A SPINNING CHAIR, PHYSICS., IT USED IT.), the X on "mid-air", the Manx landing, the bend glow, the solid-object X, the halves split, the icons-to-dials swap in s14, the FLIPPED! landing, the s18 landing and the loop dissolve.
- The first run flagged three real pops, fixed and re-rendered: the s08 loupe jumped onto the waist (now glides), and the s12-s14 lower panel appeared in one frame (now fades in over 0.3 s).
- Loop: s18's last 7 frames are `s01_frame(0, 0, loop=True)` (it pins `anim.NOW = 0` so Marey's idle motion matches); frame 1957 equals frame 0 exactly (mean abs diff 0.0).

## Sound
The Producer's mix is used unchanged. The picture lands on its cues: the 1894 title pop, the camera ticking on "filmed" (disc spin-up + lens flash), the flip whoosh, the soft landing on "feet", the impact on "physics", the X on "mid-air", CLUE pops, the Manx landing on "too", the bend glow on "bent", the trampoline bounce, the halves' glow on "halves", the front turn on "turns", the back catching up on "catches", the ding on "flipped" (the landing), the chair spin, IT USED IT on "used", the modern cat landing on "lands", the film strip on "Paris" (loop).

## Open notes
- Acting and feel are the Director's call on `tests/preview_full_540.mp4`; the Producer reviews `tests/sheet_2s.jpg` against the script before any 1080 final.
- Dramatised / simplified (as in SCRIPT.md): the fall is shown in slow motion (the real fall lasts ~0.3 s; Marey filmed at 12 frames per second); the righting is drawn as the simplified "tuck and turn" (front ~195° vs back ~15°, then swap), not the full Kane & Scher bend-and-twist; Marey on a stool and his loupe are staging; the 1968 gym, the suit design and the photo on the wall are illustrative.
- Render cost: frames are drawn at 1080 and downscaled; the 540 preview takes ~25-30 min on 4 cores, the 1080 final about 45-60 min.
