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
- Never force-push an area branch that holds unrelated old history (`claude/area-engine`, `claude/area-sets`): push to a new name (`claude/area-engine-v2`), and cherry-pick only the new commits from the old one.
- When cherry-picking many area commits, resolve BACKLOG/LESSONS conflicts by keeping both sides, then dedupe duplicated lines and headings once at the end; keep the integration branch's `scripts/<slug>/` files and re-apply the area's small edits in `build.py`.
- Buffer: Facebook posts need `metadata.facebook.type: "reel"`; TikTok takes a few minutes in "sending", so poll `post(input:{id}) { status externalLink }` in the background.
- github.io is blocked from the container: check that Pages deployed through the repo's Actions runs before handing a URL to Buffer.

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
- Draft reviews on 0.5 s contact sheets score acting at 6 whatever the camera does: one-frame arm swaps and small face changes don't read at 180 px. Fix acting at the rig (in-betweens, bigger poses), not with more camera moves.
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
- Retention dies in the middle when the picture sits still. **Superseded by the Director (2026-11-22): no cut-every-1.5 s timer; instead keep the animation moving continuously throughout (characters act, fx and backgrounds drift, the camera glides), and never leave a frozen frame.** (Old rule: change the picture every ≤ 1.5 s, never hold one framing over 3 s.) Our posted shorts ran 2-3.4 s static shots against the leaders' ~1 s (`references/reports/retention_2026-11.md`).
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
- Fresh LLM reviewers disagree by about ±1 on the same script, so "all five ≥ 9" is noise-bound: 8 rounds plateaued at 7-9. Gate scripts on the panel median ≥ 8, no swipe before 50 s (the facts score was dropped by the Director on 2026-11-22), then let real retention data judge.
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
- Frozen upstream stages come back as the blockers downstream: video 2's fx (5.8) and dense insert text were named by every storyboard and draft reviewer. Fix the stage that froze lowest before the render, or stage around it in the engine early.
- For a mechanism shot, engine-moved sprites (a big translucent pane, a ≥ 0.5 W cue arrow, contact, a delayed move, a growing trail) read better than a self-contained fx clip, and are cheaper to iterate.
- Acting scores 6 when arms swap poses in one frame and faces are small at phone size. Fix `character()` in-betweens and bigger poses before the next video's render.
- Thumbnail: zoom onto the character so the action fills the middle; a wide frame leaves the bottom half empty and puts the headline over the sign.
- Times like "1h" are ambiguous (01:00 vs 13:00): confirm with the Director, and default to a one-shot task unless they say "every day".
- LLM reviewers score motion and acting from stills at ~6 whatever the animation does, and contradict each other round to round (blood-falls motion test: 4 rounds stuck at 6.5). Don't loop on it: check motion automatically and let the Director judge acting on a low-res mp4.
- Stills reviewers scoring richness/readability/composition never checked the picture against the narration, so a contradiction (CLUE 3 water orange while the line says "clear") and a 10 s same-palette run reached the final render. Give reviewers each still with its line, add a sequence sheet, and have the Producer check the preview before rendering the final.
- YouTube ignores the 0.1 s cover when it picks a Shorts thumbnail: video 3 got an auto-picked mid-video frame (CLUE 3, 'isn't red'). Buffer can't set one either, so after posting, check `i.ytimg.com/vi/<id>/hqdefault.jpg` and have the Director pick the cover frame (or upload the thumbnail) in the YouTube app or Studio.
- Buffer → YouTube refuses a second post within ~24 h ("daily posting limit for this channel"): video 4 failed the morning after video 3. Space YouTube posts >= 24 h apart, or schedule with `customScheduled` + `dueAt`.
- 2026-11-23: Blood Falls (74.8% stayed, viral) vs Tunguska (60%): open on ONE impossible image named by a body/life metaphor + a human witness and year, keep that hero image and colour on screen, flip the metaphor in the reveal ("isn't bleeding, it's rusting"); never open on a number comparison. Full formula: HANDOFF › The Blood Falls formula.
- 2026-11-24 (wind-cave): a wind/breath effect drawn as solid bright filled ribbons with ink edges and arrowheads fanning from one point reads as a WATER FOUNTAIN. Draw air as a low-alpha blurred haze body plus thin bright streak lines, curling eddies at the tips, a sideways drift (wind), carried bits (seed heads, grass, dust) and a heat-shimmer row displacement near the source (`prairie.breath`, `shimmer`).
- A big additive `aura`/radial over a whole interior washes it grey: check a set's saturation with the character layer on and off before blaming the set colours.
- 2026-11-24 (cat-righting final): a hero animal drawn as flat sausages with a side-profile head read as crude (eye on the cheek, triangle mouth, random white blocks). Build it as a tiny 3D model projected flat (a chain of spheres for the body with a deep chest/narrow waist/haunches, a skull + cheeks + muzzle head with features placed on the sphere, the face always yawed toward the camera), so it stays readable upside down and mid-twist; keep the old API so every shot picks it up at once.
- A top-down view of a person turning (s16 swivel chair) was unreadable: show rotation from the side/three-quarter view (a small 3D-projected figure, depth-sorted limbs, motion trails, an elliptical arrow round the axis).
- Keep hair tufts and props away from a stickman's eyes: Marey's side-hair tufts sat at eye level and covered one eye whenever he looked sideways; draw them at the head rim and skip the one on the look side.
- Rim/shade passes computed on the alpha paint over the ink outline: erode the alpha by the ink width first, so the light sits inside the line.
- 2026-11-24 (zebra-stripes): draw hero animals through a LABEL image (each pixel knows torso / neck / head / near leg / far leg / mane / tail), then colour, pattern and shade per label and put ONE ink outline round the silhouette (inner ink only where a near leg crosses the body). Patterns that follow the body (zebra stripes: vertical on the barrel, round the haunch, rings on the legs, across the neck into the mane) come from per-region phase fields. Use blur+threshold for dilation/erosion: PIL Min/MaxFilter at 15 px made each animal cost 2.5 s instead of 0.6 s.
- A loop frame rendered in a pool worker can differ from frame 0 (cached cards/layers built from neighbouring pose values, the global idle clock `anim.NOW`): reset `anim.NOW` in the loop frame, measure frame 0 vs the last frame, and re-render both in one process if they differ. Clamp any radius drawn from an eased value with overshoot (`out_back`, `sin` wobble): a negative ellipse radius crashes the whole render.
- 2026-11-24 (flamingo-one-leg): never switch a pose value with a time condition (`x if u < t else 0`): the s01b settle jumped the whole bird 25 px when the branch flipped. Write every pose value as one continuous curve that ends at its rest value, and run motion QA before calling a preview done.

## Cinematic 2D (video 12, plane-windows)
- Build hero sets that the camera must move through as small 3D models (`flat2d/persp.py`) and render them toon-flat: a painted set cannot crane, orbit or push through a window. Put the camera's keys in a `Path` (Catmull-Rom, eased only at the ends) so a move never stops at a key.
- With back-face culling, check winding on the first render: an inverted lathe shows the inside of the far wall (a dark top), and an inward decal normal hides the near-side windows and leaks the far ones at the silhouette. Normals = cross(along the surface, along x) pointing out.
- Light shafts from a roof: sweep NARROW strips running along the view (ridge-parallel), and clip each sweep edge at the near plane instead of dropping the shaft; wide skylights read as a grey wash, not beams. Darken the set so the beams have contrast.
- Never draw a water surface or far-side characters over walls the camera is behind: draw the water only when the camera is above the rim, and draw the far gantry, then its people, then the tank walls (they occlude them from low angles).
- A match cut needs the two shapes at the same screen place and size on the cut frame (porthole circle = cabin window bezel; the fading plane = the plane printed in the newspaper photo); compute the second shot's first framing from the first shot's last one. Keep each shot's own clock (anim.NOW) when one shot draws another for the dissolve.
- A long airliner in a 9:16 frame: use a 3/4 front chase (nose, cockpit and wing-root intakes toward the camera) instead of a side view, which never fits; light the side the camera sees, or the white top reads grey-lavender.
- Engines "buried in the wing root" read as pods unless the root bay has a blunt, flat leading edge for the intake decals to sit on.
- Reviewers call diagram stages "flat slides" next to 3D sets: give mechanism shots a defocused foreground (a window rim, a riveted frame member), a light sweep and varied framing, and alternate grades (deep navy / warm dusk / steel / warm red) across a mechanism run.
- Crowds of small stickmen are slow (a new card every frame from the idle motion): quantise their poses (`anim.actor(quant=2)`), freeze idle sway on distant extras, and draw each on a small canvas, not a full-frame layer (s03 went from 25 s to 4 s a frame).
- Smoke-test every shot at its start, middle and last frame (`flat2d/smoke.py`, ~1 min in parallel) before a full render: review stills sample one moment per shot, and a negative base `** 2.2` (complex) at the START of s05b crashed the 540 render 21 s in. Clamp bases before fractional powers.
- A camera shake that adds a fixed cover zoom only while it shakes pops on its last frame (the zoom snaps back to 1.0): scale the cover zoom with the shake amplitude so it lands on 1.0 (`plane_windows.shake_cam`).
- Repeating beats (flight cycles, pulses) must not overlap: a new cycle that restarts its phase before the last one ends makes every value it drives jump (the s10 sky flipped between dusk and altitude). Clip each cycle's length to the gap before the next one.

## Style test: stickmen in perspective toon rooms (Producer, 2026-11-25; `flat2d/style_test_rooms.py`)
The Director's style target is a stickman story short with real perspective rooms and a moving camera. Four quick iterations with `persp` + `cine`, on CPU, compared side by side with the reference:
- **Wall winding:** a room is seen from inside, so every wall polygon and wall decal must face into the room (`persp` culls back faces). Wrong winding showed black walls and no decals. Give wall decals an explicit `normal=`.
- **Bigger heads sell the look:** the reference's stickmen are about 3 heads tall. `stickman.R = 132; SEG_LEG = 170; SEG_ARM = 112` (set before any card is drawn) got close and read much better than the house 5-head figure in a 3D room. Turn blinks off (`blink_ok=False`) for stills.
- **Framing:** keep hanging lamps and the ceiling out of the top of the frame (the camera near the ceiling puts a lamp in your face); eye-level or low cameras, characters at 1/3, a blurred foreground object (`cine.fg_frame`, `cine.defocus` on the set behind a close-up) for depth.
- **Ink:** `render(..., ink_w=5, sil_w=8)` at 1080 matches the reference's bold outlines.
- **Still missing vs the reference:** much denser set dressing (pictures, shelves, small props, wallpaper and rug patterns), a brighter high-key grade (`desk`/`cabin` + grain read a little muddy), coloured night scenes (saturated blue with glows), hair/glasses/clothing details on the characters.

### Round 2 (2026-11-25): faces, high-key rooms, measured against the reference (`flat2d/style_test_rooms2.py`)
- **Measure, don't guess:** mean luminance / 5th-95th percentile / saturation / edge density per frame (360x640) put the gap in numbers. Reference day rooms: mean L 0.64-0.71, p95 0.94-0.98, edge density 0.11-0.17. Ours started at 0.41-0.54 / 0.62-0.82 / 0.05-0.09 (too dark, no clean whites, half the detail) and reached 0.68-0.72 / 0.91-0.95 / 0.10-0.12.
- **What closed the gap:** a high-key grade (`STORY` dict: lifted shadows, gain up, sat 1.12) with little grain (0.012) and a light vignette (0.14); a brighter toon light (amb 0.74-0.76, softer bands, shadow_k 0.14); white ceilings with plank lines, white skirting/crown moulding and window/door frames, inked corners; plank floors with per-plank tone; dense dressing (tiles, calendar, wall phone with a coiled cord, gingham curtain, panelled door with glass, rug border + speckles, side table + lamp, pumpkin, wallpaper motifs); fake AO strips along wall/floor seams; a sun patch on the floor.
- **Faces (`stickman.FACE_STYLE = 'ref'`, new; default 'house' is unchanged):** small white eyes with a black rim and a dark pupil, set close together and a little low; heavy half-lids for calm/smug; short, thick, rounded brows; a small dark pill mouth (no line); no nose; optional round `glasses=True`; new hair `('swept', colour)` = a hair cap over the crown with a side part. With the chibi proportions set `stickman.OUT = 4.4` for the bolder head outline.
- **Still behind:** night scenes (the reference's saturated blue with strong glows reads far better than ours), character staging (keep characters at about a third of the frame height and fully inside it), characters' bodies (the reference has rounder shirts), close-ups of props (the tape-measure macro).

### Round 3 (2026-11-25): blue night with warm practicals, a staircase house, round bodies, macros (`flat2d/style_test_rooms3.py`, renders in `videos/_style_tests/round3/`)
- **Night = gradient map, then lights:** render the set in its day palette, `toonlight.night_map` it onto a blue ramp (indigo -> saturated blue -> pale cyan), then add practicals. Round 2's night bed measured mean L 0.49, sat 0.58, edge 0.044 and read muddy; round 3 nights measure L 0.32-0.44, p5 0.11-0.20, p95 0.50-0.78, sat 0.60-0.71, edge 0.07-0.14 (rooms/stairs) and read clearly blue.
- **Warm on blue needs a mix, not a screen:** a screen-added orange on a blue wall turns pink-white. `add_light(..., mix=)` first pulls pixels toward the light colour, then screens a hot core; pools, wall splashes and the gap under a door now read orange.
- **Lights behind the camera blow up:** projecting a lamp or window that is behind the camera gives a giant glow that washed the whole frame lavender. Skip any practical whose point has camera depth < 0.3 m.
- **Moonlight:** `floor_patch` projects the window panes along the moon direction onto the floor with the bars left dark, plus `cine.shafts3d`; it is the strongest single cue for "night" in our frames.
- **Characters at night:** draw them on their own layer after `night_map`, multiplied by a pale moon tint, so they stay white with a black outline. Warm-coloured pyjamas (mustard, pink) separate the kid from the blue set; blue pyjamas vanished into it.
- **Round bodies (`stickman.BODY_STYLE = 'round'`, opt-in; the default 'tube' is byte-identical):** an egg torso joins the merged outline, shoulders and hips sit apart, and garment bands become straight-hemmed slices of the egg. New garments `cardigan=` (open front, shirt strip, buttons, pockets) and `pyjamas=` (striped jacket, piping, no shoes) work with both bodies.
- **Staging with occluders:** split the set into passes instead of trying to sort characters into the mesh. Bed: headboard and pillow, then the kid, then the quilt and bed body, so he sits up in bed. Doorway: a real hole in the wall, with the room beyond and the peeking kid drawn first so the wall covers the rest. Coffee table: drawn again after the seated character. Banister: one Part per spindle and rail piece, drawn after the characters when the camera is on the landing side.
- **Foreground blur from depth:** `split_near(parts, cam, d)` sends the parts nearer than d to a layer that gets `cine.defocus`. This gives the blurred-banister POV for free, and the near pieces blur on their own as the camera moves.
- **Day room with two characters:** mean L 0.70, p5 0.31, p95 0.91, sat 0.31, edge 0.12, inside the reference day range (L 0.64-0.71, p95 0.94-0.98, edge 0.11-0.17) except a slightly low p95.
- **Macros:** a defocused set render (r about 18-24 px at 1080) plus bokeh behind a sharp prop (the phone with a glowing UI screen held by a white stickman arm; the brass knob with light through the keyhole and under the door). Their edge density is low (0.03-0.04) by design.
- **Camera move:** `Path` keys from the bedroom door on the landing to the top step, tilting down onto the kid climbing a step with a torch. 3.5 s, 84 frames at 540x960 / 24 fps, about 2 s per frame on CPU.
- **Still behind the target:** the bed and furniture are blocky boxes (no rounded mattress or soft folds); the torch beam is faint; the stickman hand on the phone reads more like a finger than a hand; the night rooms have little contrast between objects (one ramp for everything); the bedroom character is small (about 1/6 of the frame).

## Natural motion (video 13 fix pass 2, 2026-11-26; helpers in `flat2d/body2d.py`)
Reference clips could not be studied: YouTube media hosts are blocked by the session proxy (and yt-dlp hits the bot
check), so the numbers below are from the published stair/gait biomechanics we know, checked by eye on our stills.
Never put third-party frames in the repo (public).
- **Draw poses from joints, not rotated cards.** `body2d.figure(lay, J, k, style)` draws the round-body stickman from
  screen joints (head, neck, pelvis, shoulders/elbows/hands, hips/knees/ankles/toes) with the card head pasted on
  top (`head_sprite` in night_intruder.py). Pose builders: `build` (absolute segment angles), `reach` / `plant`
  (2D IK onto a target, so hands stay on a collar and feet stay on a spot), `ik3` (3D IK: knees toward a pole).
  Lying / kneeling / propped poses made this way read in 1 s; a standing card rotated 90 deg reads as a tangle.
- **Stair descent (step-over-step):** normal ~0.55-0.65 s per step; a night creep 1.0-1.5 s (ours: 1.2 s = the
  footstep sounds). Per step: the lead foot lifts ~5 cm, moves forward over the nosing first, then reaches DOWN
  toe-first (ankle plantar-flexed ~20 deg, toe ~6 cm below the heel); contact on the sound; the heel settles over
  ~0.15 s. The support knee flexes (to ~80-90 deg) to lower the body from ~0.45 s before contact; the pelvis dips
  ~3 cm past its new height at +0.12 s and recovers by +0.4 s; then a held double-support pause (creep). Trunk 5-10
  deg forward, head pitched down 20-30 deg toward the next treads; the hand on the wall slides ~0.3 s behind the
  body; a raised arm lags the drop ~0.1 s (follow-through). `body2d.stair_descent(T, contacts, tread)` gives feet +
  pelvis in 3D; project with the shot camera, so feet are planted on the treads by construction.
- **Startle / shield (shot 15):** the head pulls back and down first (~0.1 s), the hands lead the arms up in ~0.2 s
  with a small overshoot (`eback`), the elbows follow ~0.05 s later, then a fine tremble.
- **Dodge reflex (shot 9):** starts with the swing (reaction ~0.2 s after the wind-up starts), fast ease-out with a
  small overshoot, slow recovery - not a symmetric smoothstep.
- **Peek (shot 5):** small moves with held pauses (inch out ~0.7 s, freeze ~0.7 s, inch again), not one slow slide.
- **Shove + fall:** 3 beats - contact (0.1 s: the victim's trunk whips forward, arms fling back), topple (~0.2 s,
  ease-IN like gravity, pivoting on the feet, arms swing forward to catch), impact (camera jolt + dust puff + a 1-2
  frame bounce), the attacker lands after with an overshoot-and-settle.
- **Getting up from the floor:** prone -> push up onto hands and knees -> one foot forward into a crouch -> stand,
  hands and knees planted while the weight shifts (key poses blended with eased joint lerps, `jlerp`).
