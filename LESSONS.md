# Lessons (general)

Each line is a mistake already made once, phrased as an instruction. Add a line every time you find and fix something new. Area-specific rules go in that area's rules file, such as `stickman/DRAWING_RULES.md`.

## Tools and environment
- Never name a Python script after a stdlib module (`inspect.py` broke `import bpy`). Keep your scripts in a `scripts/` folder.
- Run scripts that read downloaded files with `python -I`, and keep downloads in their own folder.
- YouTube blocks yt-dlp and page fetches ("confirm you're not a bot"). `i.ytimg.com/vi/<id>/oar1..3.jpg` gives three full-res frames, and storyboards need a signature (403). Don't burn time on more attempts.
- Kenney.nl returns 403 to automated clients. **Never spoof a browser user agent.** Use the Poly Haven API (`api.polyhaven.com`, download with curl) and the KayKit and Quaternius git repos.
- Python `urllib` gets 403 from `dl.polyhaven.org`. Use curl.
- The Blender 5 compositor needs a GPU and crashes here. Do glow and post-processing in Python (see `blender/scripts/post.py`), and do DOF in-render.
- Never commit `__pycache__`, `.venv`, `packs/` or large renders. `.gitignore` covers them, so don't override it.

- Find standing heights (ship decks, kerbs) with `scene.ray_cast` straight down, starting the ray under sails and overhangs, never from high above.
- A sign is a board plus a separate face plane: rotate or tilt them together, and keep the face at least 5 cm proud of anything else on the wall (a garage door box hid a sign).
- A camera looking along -Y puts +X on the left of the frame. Check which side a sign faces before placing it.

## Look
- Photo-scanned models (Poly Haven) clash with 2D characters. Use stylised flat-colour packs (Quaternius, KayKit).
- The AgX view transform washes bright emissives to white. Use "Khronos PBR Neutral" and add glow in post.
- Freestyle on dense scan meshes gives messy, heavy lines. On low-poly models, use silhouette + crease at about 140°, fade the lines with distance, and tint them toward the night colour.
- Freestyle lines are drawn after DOF, so they stay sharp on a blurred background. Fade line alpha with distance, faster in close-ups.
- Glow and bloom must be **warm-only**, or it blows out white faces.
- Night scenes need a soft lavender fill from the camera side, or facades go black.
- A wide 9:16 shot has too much sky. Build layered back rows (houses climbing a hill) so the top third has content.
- The scale of each pack differs (a Quaternius barrel is 0.2 units). Scale every model to real metres.

- Split the world shader with Light Path › Is Camera Ray: the camera sees the painted sky, the set is lit by a separate ambient colour. Otherwise a bright sky flattens every facade.
- Depth haze without the compositor: render a second cheap pass (4 samples, no ink) with `view_layer.material_override` emitting the camera distance, then mix toward the haze colour in Python. Keep the sky (depth = 1) out of the haze, or it washes the painted sky.
- Big pale surfaces (concrete, white walls, bright grass) push mean luminance past 0.6 and saturation under 0.3 in daylight. Keep large-area albedo at about 0.35-0.6 and let the sky and practicals carry the highlights.
- **Expose for daylight by default.** The reference's median frame luminance is 0.46 with near-white highlights; our night village was 0.21. Night is a story beat (~18% of frames), not the house look. Check every plate with `references/scripts/frame_stats.py`.
- Freestyle line colours are **linear**, not sRGB: plum #241726 is (0.018, 0.009, 0.020). Typing sRGB values gives washed-out pink lines.
- A Blender sun shines along its local -Z. Rotation (50°, 0, 335°) lights facades that face a camera looking +Y; 215° lit them from behind and left them in shadow.
- `color_ramp.elements` are re-sorted by position after `elements.new()`. Index the elements by position, not by creation order.
- Frame for medium shots: a 1.75 m character should fill about 55-65% of the frame height, as most reference frames do. Wide shots with tiny characters are the exception.

- Ink that is 2-3 px at 1080 wide vanishes at phone and contact-sheet size. On open sets with big distances, use about 4.8 px, keep far lines at 0.6 thickness, and widen the distance fade.
- Flat planes (road, kerbs) only get outlines from Freestyle *border* edges, and anything lying on top (painted line strips) hides those borders. Ink the top strips too.
- Golden hour needs a strong orange sun (energy ~12) with a weak blue ambient, plus a warm grade. A pink-lavender sky and haze alone reads as "pastel dusk", not warm-against-cool.
- Lamp glass must stay amber: keep its emission low (≤ 0.3 × the night multiplier), or it clips to white under Khronos PBR Neutral.

## Audio
- ElevenLabs free tier: always dry-run `tts.py` first and read the extracted text. The voice-over parser once grabbed "Facts and sources (… the voice-over)" instead of "## Voice-over". Prefer a heading that *starts* with "Voice-over", and take only the list items.
- Cache the raw TTS response (`_tts_response.json`) and re-process from it. Trimming, pause tightening and word refinement must never cost characters.
- The TTS take paused up to 1.08 s (14 s in total) at sentence ends and around dialogue. Always tighten pauses (cut the quietest part of the gap, with a crossfade) and re-measure words/s on the **full** script, not a one-sentence test. A single sentence over-reads the rate because it has no sentence gaps.
- The API's end time for a word before a comma includes the pause. Snap word edges to the waveform before using them for lip sync or gap stats.
- A music sting on the last word masks the punchline. Start it at the word's **end**.
- Sentence-final words trail off quietly. Dip the music an extra 3 dB under them, and start section level changes *at* the section's first word (a centred smooth lifts the bed under the end of the previous line).
- Don't flatten every pause to one value: sentence gaps of exactly 0.20 s sound mechanical. Vary them (0.17-0.23 s) and keep a ~0.3 s breath after a closing quote and before the "Wait," / "You see," pivots, while keeping gaps >0.25 s under 1 s in total.
- When a section's music gain *rises*, ramp it over ~1.2 s. A fast raise boosts the previous section's ringing tails under the new line's first word (it masked "Wait,").
- A camera shake is not always an impact: never add an automatic impact sound to it. Cue the sound from the story.
- Limit to -1.2 dBTP, not -1.0: fades and 24-bit writing after the limiter, and codecs, can overshoot.

## Process
- Catch defects where they are born: 9 of 13 first-video defects were decidable from `shots.json` alone but found after a full render. Run `tools/preflight.py` and `tools/storyboard.py` before the voice-over (PIPELINE › Stage gates).
- Every defect found at the draft stage becomes a new preflight check or a rule here, so the next video catches it at G1.
- Judge new assets in their real shots (storyboard), not only on their own sheet: the motorbike passed its sheet and failed from behind in context.
- An effect must follow its cause on screen by at least 8-10 frames (the broom tipped before the hand flicked).
- The shot that carries the mechanism must frame the action at medium or closer (rider >= 28% of the frame height), with the cue arrow at the part that moves and at >= 0.5 W. A wide chase with a small arrow near the ground failed clarity twice.
- Choreograph the mechanism as one continuous chain: upright, the cause (steer cue), then a single move as the effect. A lean that rocks back and forth before the cue (0, -20, 0, -20) made the order unreadable.
- A rider in front of a still plate looks like riding on the spot. Every riding cam needs a depth map (`build.py --depth`), and the engine dollies into it (ride parallax). Keep the travel at <= 3 m, or <= 1.2 m on cams close to tall objects, or edges ghost.
- A top-down diagram must use the plate's own racing lines (projected from the set geometry, `paths.py`), never a generic shape: a path that ignores the drawn road reads as wrong.
- Blender writes a 16-bit "Raw" emission PNG with the sRGB curve applied. Decode it before using it as data.
- A front-view close-up mirrors left/right cues: a "rider's right" arrow reads as screen right in the wrong sense. Show a steering mechanism from behind or above only.
- Symbol FX (?, !, sweat, notes) need at least 0.40 W to read on a phone; the default 0.35 W is too small.
- Keep a character the audience must read at >= 28% of the frame height in medium shots (>= 14% in wide ones), and a far acting character at >= 2/3 of the near one in an over-the-shoulder shot.
- Review animation on a dense sheet (t = 1/12 .. 11/12), never only on a 5-frame strip. Pops at the entry or exit and frozen holds hide between the samples.
- PIL `GaussianBlur` on straight RGBA drags black in from empty pixels, which gives grey or brown halos. Blur only the alpha channel and keep the RGB solid.
- Feed each reviewer round the same inputs, and turn every fix into a rule (for example `fx/RULES.md`). Otherwise the next round undoes the last one: alpha fades get swapped for shrinks, then the shrink pops.
- Seed per-character randomness with a stable hash (`zlib.crc32`), never Python `hash()`: it differs between processes, so multiprocessing renders flicker.
- Never upscale a 2D card to fit a medium shot; render it at the target scale (or downsample the supersampled canvas).
- An independent reviewer scores acting low if a beat only swaps the face: every beat needs a body change (lean, arms, shoulders).
- Render a cheap low-res still after every change, and look at it before rendering full size.
- Compare side-by-side with a reference frame. Numbers and adjectives lie; pictures don't.
- When the user corrects something, fix it **and** add a rule so it never happens again.
- Show every pose and every joint at 2x zoom before calling it done.
- Measure ink density (`frame_stats.py` edge) on full-size plates: 25% test renders read about half the real edge density.
- Two Blender renders at once on 4 CPUs each run at half speed. Queue full-size plates; overlap only cheap low-res tests.

## Scripts and topics
- Classic science facts score low on originality (toast, the ring-road traffic jam, tickling yourself, tomato juice on planes, Leidenfrost, "objects in mirror"). Prefer a lesser-known *angle* or a fresh phenomenon, and judge originality by "is this already a viral short?", not by "is it true?".
- A hook must state a fact, never give an instruction ("Flip the tab…", "Shut your freezer…"), and must not contain the mechanism ("half your brain stays on guard"). Count the words with a script, not by eye.
- Check each source against the specific claim in your hook. The ketchup source's physicist called the "57" tip marketing; the noise study found only sweet suppressed and umami boosted, not salt; a convex passenger mirror is *allowed*, not required.
- A pop-science number repeated by the press ("taste drops 30%", "1% water", "delays up to 2 s") must be checked against the paper or press release. If it doesn't match, hedge it or drop it.
- Keep a payoff physically true: a door whose pressure has evened out becomes easy to open, but it never opens by itself.
- Never show or say brand names (Heinz, Cheerios, an airline). Plan the payoff so it works without the brand, or drop the topic.
- Reviewers' originality scores drift without the reference channel's full title list. Put that list in the repo before the next topic round.
- In a shot list, left and right must be defined from one point of view (we use the rider's own). A front view mirrors them on screen, so any shot with a left/right arrow or lean uses a rear (chase) or top view, and any demo by a character facing the camera is shot over the shoulder.
- Never put a face beat (an expression change) on a character seen from behind or from directly above: nobody will see it.
- Don't let the mystery line and the "You see," line contradict each other in wording ("leaning doesn't turn it" vs "it only turns when it leans"). Name the exact thing ("leaning your body" vs "leaning the whole bike").
- Generate `shots.json` from a script that names anchor words instead of hand-typed word indexes, and that checks every voice-over line has a shot with identical text, plus word counts and the shot mix.
- Keep the script at or under about 232 words (≤ 63 s), so the voice has headroom under the 240-word / 65 s cap.
- Never `git stash drop` after a `git stash pop` that hit a conflict: the pop did not apply. Check `git stash list` and `git diff` first. (A dropped stash can be recovered with `git fsck --no-reflog | grep 'dangling commit'`.)
- Keep raw renders (`plates/_tmp/*_raw.png`) and the depth pass, so grade and haze fixes are a `--repost` (Python only) instead of a full re-render.
- Never `git stash` while background renders are queued: a later process in the queue starts from the stashed (old) files.
