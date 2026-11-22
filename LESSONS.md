# Lessons

Each line is a mistake already made once, phrased as an instruction. Add a line every time you find and fix something new. Area-only rules go in the area's rules file (`engine/RULES.md`, `fx/RULES.md`, `characters/RULES.md`, `stickman/DRAWING_RULES.md`).

## Tools and environment
- Never name a Python script after a stdlib module (`inspect.py` broke `import bpy`). Keep scripts in a `scripts/` folder.
- Run scripts that read downloaded files with `python -I`, and keep downloads in their own folder.
- YouTube blocks yt-dlp and page fetches. Use oEmbed (`www.youtube.com/oembed?url=…`) for the title and channel, and `i.ytimg.com/vi/<id>/oar1..3.jpg` for three full-res frames. Storyboards need a signature (403); don't keep trying.
- Kenney.nl returns 403 to automated clients. **Never spoof a user agent.** Use the Poly Haven API with curl (`urllib` gets 403 from `dl.polyhaven.org`) and the KayKit/Quaternius git repos.
- The Blender 5 compositor needs a GPU and crashes here. Do glow and post in Python (`blender/scripts/post.py`), and DOF in-render.
- Blender writes a 16-bit "Raw" emission PNG with the sRGB curve applied. Decode it before using it as data.
- Two Blender renders at once on 4 CPUs each run at half speed. Queue full-size plates; overlap only cheap low-res tests.
- Never commit `__pycache__`, `.venv`, `packs/` or renders over 50 MB.
- Never `git stash` while renders run: workers re-read `shots.json` and later queued jobs start from the stashed files. Never `git stash drop` after a conflicting `pop` (it did not apply). Recover with `git fsck --no-reflog | grep 'dangling commit'`.

- HuggingFace is blocked, so Whisper and other model downloads fail. To get a competitor's script, read the burned-in captions with `rapidocr-onnxruntime` (pip, models bundled) in a separate venv, at 10 fps on the caption band, then de-duplicate. Measure pacing with `references/scripts/video_cuts.py` and sound with `video_audio.py`.
- The Director can upload competitor MP4s into the session (YouTube blocks downloads here). Keep them out of the repo; keep only measurements and structure notes.

- A low-res test plate (25%) must be upscaled to 1080x1920 before the engine reads it: its JSON is in full-size px, and `load_plate` rescales the JSON by the image size (ground_y x4 off the frame).

## Engine wiring (video 2)
- New engine features must not change old shots: gate them (string props are sprites only on `props.SPRITE_SETS`) and diff video 1 frames 290 and 1040 before and after.
- Scale props by perspective from their ground row, and keep them near the plate's ground line: on a low camera (rock_low, 0.38 m up) a prop at y 0.8 came out 7x too big. Place scale props from plate `targets` (the fridge beside the hero rock).
- A `props` entry can be a dict now: every reader of `props` must skip non-strings (`p.startswith` crashed on dicts).
- Environment fx (storm, flood, rain, ice) need a `dur` that fits the beat: a storm that lasts to the end of the shot still covers the "Gary" punch-in.
- UI cards over a zoomed or rolled camera go in screen space (`"screen": true`), or the zoom crops them.
- A storyboard with one frame per shot hides every shot that changes: show an opening frame for shots with glides, keep the key pick off a cut-in, and never pick the same cut-in twice (s14 showed one moment three times and reviewers scored it as three duplicates).
- A cut-in must hide the main shot's fx (the s14 ice fx covered the sleeping-cousins cut-in).
- A mechanism drawn by an fx with its own built-in rock can't push the story's rock: move the fx canvas along the rock's path (`move`), switch its rock off, and draw the hero rock over it (props layer `top`).
- Never splice-render a few shots into a full render: `--frames` rewrites `track.json` for those frames only and `qa.py` then misses the rest. Finish the shot-list changes first, or stop the render and restart it whole (CPU is cheap, usage is not).
- A `follow` camera with no rider in the shot doesn't move: give character-free or static shots a slow glide, or qa.py flags frozen spans (s10, s14's ending, s16's opening).
- Check that a camera field is actually read before tuning it: the base `camera.x`/`y` were ignored (only the auto `focus` was used), so six shots' framing notes did nothing for 2 review rounds.
- A cut-in with no `until_word` must run to the shot's last frame: its end got the same 2-frame lead as its start, so the cousins were drawn over the top-view plate for 2 frames (planted-feet QA caught it).
- A rolled camera has a zoom floor (roll -6° needs ~1.18 to hide the border): a push below it is clamped to nothing. Glide above the floor.
- Seated cards (`seated=`) sit ~6 px above the ground line: re-plant them on their lowest opaque row, like a lean.
- A deliberate punch-in that cuts edge characters needs `crop: true` on the shot, or qa.py counts every frame of it as clipped.
- A new engine fx name needs an entry in `audio/lib/sfx_x.py` GEN or SILENT, or the mix drops its sound (`pane_push_top` reuses the ice_pane grind).
- `audio/build_mix.py` needs scipy, which the venv lacked: `uv pip install --python .venv/bin/python scipy`.
- Storyboard reviews plateau around 7.4 ±0.3 when the remaining notes are frozen assets (fx at 5.8, frost plates, dense inserts): report them to the Producer after round 3 instead of polishing around them.

## Sets (Blender look)
- Photo-scanned models clash with 2D characters. Use stylised flat-colour packs (Quaternius, KayKit), scaled to real metres (a Quaternius barrel is 0.2 units).
- Use "Khronos PBR Neutral" (AgX washes emissives to white) and add glow in post. Glow and bloom are **warm-only**, or they blow out white faces. Keep lamp glass emission ≤ 0.3 × the night multiplier, or it clips to white.
- **Expose for daylight by default** (the reference's median luminance is 0.46). Night is a story beat (~18% of frames), with a soft lavender fill from the camera side, or facades go black. The frame-stat targets are a house average, not a per-shot rule: a strong channel in our genre ranges from 0.36 (lamp-lit cabin) to 0.71 (snow).
- Keep large-area albedo at about 0.35-0.6. Big pale surfaces push luminance past 0.6 and saturation under 0.3.
- Split the world shader with Light Path › Is Camera Ray: the camera sees the painted sky, and the set is lit by a separate ambient colour.
- Golden hour needs a strong orange sun (energy ~12), a weak blue ambient and a warm grade. A pink-lavender sky alone reads as pastel dusk.
- A Blender sun shines along its local -Z. A camera looking along -Y puts +X on the left of the frame. Check which way lights and signs face.
- Freestyle on low-poly models: silhouette + crease at about 140°. Fade lines with distance (they are drawn after DOF), and use ~4.8 px on open sets, because 2-3 px vanish at phone size. Line colours are **linear** (plum #241726 = 0.018, 0.009, 0.020).
- Flat planes only get outlines from Freestyle *border* edges, and strips lying on top hide them: ink the strips too.
- Depth haze: a cheap second pass emitting camera distance, mixed in Python, with the sky kept out.
- Measure ink density on full-size plates (25% renders read about half the edge density).
- A wide 9:16 shot has too much sky: build layered back rows so the top third has content.
- `color_ramp.elements` re-sort by position after `new()`: index them by position.
- Find standing heights with `scene.ray_cast` straight down, starting under overhangs.
- A sign is a board plus a face plane: move them together, with the face ≥ 5 cm proud of the wall.
- Keep raw renders and the depth pass, so grade and haze fixes are a `--repost` instead of a re-render.
- Every riding cam needs a depth map (`build.py --depth`): a rider over a still plate looks like riding on the spot. The engine dollies into it; keep the travel ≤ 3 m, or ≤ 1.2 m on cams close to tall objects, or edges ghost.
- A top-down route must use the set's own racing lines (projected from the geometry, `paths.py`), never a generic shape.
- Stylised-PBR props (`common.pbr`/`soften`): clearcoat paint only looks glossy if glossy rays see a sky. Use the preset key `sky_refl` (the default ambient is a flat colour), plus a `softbox` placed to streak the flanks.
- Aim the key with `sun_from` (a world vector toward the sun), not `az`. Light from the side or back of a prop gives a warm/cool split and visible long shadows. Front light reads "flat midday" to every reviewer.
- A mesh groove at playa scale reads as a pipe or a plank at low cameras. Paint the trail on a flat strip instead (`ground.trail`: a dark floor, pale rims and faded ends).
- Haze depth must be rendered after per-light scene changes. One depth pass per cam left a ghost of a hidden banner (`common.main` now re-renders it when a cam has `per_light`).
- Hide per-light props by moving them under the ground (`playa/build.py show()`), so Freestyle, the depth pass and the haze all agree.
- A practical light right above a mirror (pond, ice) shows up as a white disc in the reflection. Set `visible_glossy = False` on it.
- A prop look test alone plateaued at about 7/10 with reviewers (19 rounds). Shot context (mountains, haze, a stand-in character, DOF) added more than another material tweak. Judge props in their plates.

## Shot lists and staging (caught by `tools/preflight.py`)
- Define left and right from one point of view: the rider's own. A front view mirrors them, so show any left/right cue, lean or steering mechanism from behind or above; a demo by a character facing the camera is shot over the shoulder.
- Never put a face beat on a character seen from behind or from above.
- Every beat needs a body change (lean, arms, shoulders), not only a new face.
- A character the audience must read is ≥ 28% of the frame height in medium shots (≥ 14% in wide shots, 55-65% is typical). A far acting character is ≥ 2/3 of the near one in an over-the-shoulder shot.
- The shot that carries the mechanism frames the action at medium or closer, with the cue arrow at the part that moves and ≥ 0.5 W.
- Choreograph a mechanism as one chain: at rest, the cause (the cue), then a single move as the effect, at least 8-10 frames after the cause. A lean that rocks before the cue makes the order unreadable.
- Symbol FX (?, !, sweat, notes) are ≥ 0.40 W, anchored to the character.
- Generate `shots.json` from a script with anchor words, not hand-typed indexes, and check every voice-over line has a shot with identical text.

## Scripts and topics
- Write a story, not a documentary: a protagonist doing something that looks wrong, a mocking rival who wins first, 3 escalating stages, then the rival's spectacular failure and a gag or loop line. All four leader shorts studied use this engine; our Lake Nyos (no protagonist) and bike (second-person opening, no rival) don't.
- Retention dies in the middle when the picture sits still: change it every ≤ 1.5 s (a cut, a punch-in, an insert, a camera move), and never hold one framing over 3 s. Our posted shorts ran 2-3.4 s static shots against the leaders' ~1 s (`references/reports/retention_2026-11.md`).
- Open mid-action on a character or an extreme close-up, with 2+ picture changes before 3 s, and start the voice inside the story, not with a setup. End on a payoff gag or a seamless loop; never fade to black.
- Judge originality by "is this already a viral short?", not "is it true?". Classic facts score low (toast, ring-road jams, tickling yourself, Leidenfrost…).
- A hook states a fact, never an instruction, and never contains the mechanism. Count words with a script.
- Check each source against the exact claim, and check press numbers against the paper. Hedge or drop what doesn't match.
- Keep the payoff physically true, and never show or say brand names.
- The mystery line and the "You see," line must not contradict each other in wording: name the exact thing.
- Estimate length from the word count (video 1: 231 words = 63.2 s of real voice), not from preflight's stand-in total, which reads ~15% long (72.8 s for the same script). Spoken years add words ("1948" = three).
- Make every video a little over 1 minute: 225-240 words gives 62-66 s. Never under 61 s (TikTok/Snapchat pay only over 1 minute), never over about 66 s (retention).

## Audio
- Free tier: dry-run `tts.py` and read the extracted text first (the parser once grabbed the wrong heading). Cache the raw response, and re-process from it at no cost.
- Tighten TTS pauses (it paused up to 1.08 s), varying sentence gaps 0.17-0.23 s, with ~0.3 s breaths after a closing quote and before "Wait," / "You see,". Measure words/s on the full script.
- Snap word edges to the waveform: the API's end time before a comma includes the pause.
- Start a music sting at the punchline word's **end**. Dip the music 3 dB under quiet sentence ends. Ramp rising section gains over ~1.2 s. Cue sounds from the story: a camera shake is not an automatic impact.
- Limit to -1.2 dBTP: later steps and codecs overshoot -1.0.
- A pause cut with a crossfade removes the gap **plus** the crossfade: shift later words by the samples really removed. The 8 ms-per-cut drift put video 1's words up to 0.26 s late and the last word of video 2 on silence. `tts.py` now refuses to write when any word sits on silence; check the END of the file, not just the first seconds.
- A slow TTS take (video 2: 96 s raw for 235 words) is fixed in post, not re-voiced: tighten pauses, then use a formant-preserving rubberband stretch (`tts.py --target`, at most 1.25x; pad before stretching, because rubberband drops the last ~30 ms). Timestamps scale exactly by 1/tempo.
- SFX clutter is what holds the audio score down. Whoosh only on a change of *place*, never two whooshes within 0.6 s, never a transition whoosh within 0.5 s of a story cue, and duck every SFX under speech (-4 dB; -6 dB for long beds like storms and floods).
- A section's music gain *cut* must finish before its first downbeat (the old gain made the first kick hit over the voice); a *raise* starts at it.
- Text-only reviewers plateau around 7.6-7.8 on "comedy timing" and "SFX" and start contradicting each other. Declutter structurally rather than cue by cue, and keep picture sync (an SFX lands when the picture shows the event) over a reviewer's wish to move it.

## Process and QA
- Don't push a look metric all the way to the reference number by grading alone: forcing our warm/cool split to the leaders' value made frames dull and blue (our dark pixels are warm because of plum ink and red costumes, not the grade). Use a gentle finish (vignette 0.14, split ±0.02) and fix the rest in lighting and sets.
- Fresh LLM reviewers disagree by about ±1 on the same script, so "all five ≥ 9" is noise-bound: 8 rounds plateaued at 7-9. Gate scripts on the panel median ≥ 8, no swipe before 50 s and facts ≥ 9, then let real retention data judge.
- `tools/preflight.py` must report every missing plate, not exit on the first one: `find_plate` raises SystemExit, so catch it (fixed 2026-11-21).
- The 5-reviewer script panel with no round cap burned one session's whole 5-hour limit in 9 rounds (53 sub-agents) and stalled it for 4 h. Run panel reviewers and gag writers on `model: "sonnet"` with short prompts, all in parallel, and keep the main model for the rewrite itself.
- Measure, don't eyeball, when matching a reference: our first "sentence" captions were 3x wider than theirs. Our frames also had no vignette (0.99 vs 0.78) and an inverted warm/cool split, and both only showed up in `style_metrics.py`.
- Catch defects where they are born: run `tools/preflight.py` and `tools/storyboard.py` before the voice-over. Every defect found later becomes a preflight check or a line here.
- Judge new assets in their real shots (storyboard), not only on their own sheet.
- Render a cheap low-res still after every change. Compare side by side with a reference frame. Show joints at 2x zoom. Review animation on a dense sheet (t = 1/12 … 11/12).
- Feed each reviewer round the same inputs, and turn every fix into a rule, or the next round undoes the last.
- When the Director corrects something, fix it **and** add a rule.
- Check the other branches and earlier sessions for channel conventions before calling a video final (the cover-as-first-3-frames rule was missing from the handoff).
- PIL `GaussianBlur` on straight RGBA drags in black halos. Blur only the alpha.
- Sheet reviews of many small assets plateau around 7: each fresh reviewer finds new nitpicks. Once a stage has not improved for 3 rounds, freeze it with notes and judge it in its real shots (G3). Give reviewers the fixed-upstream context (cast colours, style rules) up front, or they spend their points on it.
- Judge a mechanism (a push, a shove, a drift) on a large 3-4 frame strip of the beat, or in the storyboard. On 180 px dense sheets the reviewers read 0.3-canvas moves as "static".
- Check the review sheet itself before blaming the asset. A crop that cut off the seated legs, and an enlarged thumbnail that overlapped its neighbour, cost two rounds of "clipped" notes.
