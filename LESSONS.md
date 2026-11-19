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

## Look
- Photo-scanned models (Poly Haven) clash with 2D characters. Use stylised flat-colour packs (Quaternius, KayKit).
- The AgX view transform washes bright emissives to white. Use "Khronos PBR Neutral" and add glow in post.
- Freestyle on dense scan meshes gives messy, heavy lines. On low-poly models, use silhouette + crease at about 140°, fade the lines with distance, and tint them toward the night colour.
- Freestyle lines are drawn after DOF, so they stay sharp on a blurred background. Fade line alpha with distance, faster in close-ups.
- Glow and bloom must be **warm-only**, or it blows out white faces.
- Night scenes need a soft lavender fill from the camera side, or facades go black.
- A wide 9:16 shot has too much sky. Build layered back rows (houses climbing a hill) so the top third has content.
- The scale of each pack differs (a Quaternius barrel is 0.2 units). Scale every model to real metres.

- **Expose for daylight by default.** The reference's median frame luminance is 0.46 with near-white highlights; our night village was 0.21. Night is a story beat (~18% of frames), not the house look. Check every plate with `references/scripts/frame_stats.py`.
- Freestyle line colours are **linear**, not sRGB: plum #241726 is (0.018, 0.009, 0.020). Typing sRGB values gives washed-out pink lines.
- A Blender sun shines along its local -Z. Rotation (50°, 0, 335°) lights facades that face a camera looking +Y; 215° lit them from behind and left them in shadow.
- `color_ramp.elements` are re-sorted by position after `elements.new()`. Index the elements by position, not by creation order.
- Frame for medium shots: a 1.75 m character should fill about 55-65% of the frame height, as most reference frames do. Wide shots with tiny characters are the exception.

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
- Render a cheap low-res still after every change, and look at it before rendering full size.
- Compare side-by-side with a reference frame. Numbers and adjectives lie; pictures don't.
- When the user corrects something, fix it **and** add a rule so it never happens again.
- Show every pose and every joint at 2x zoom before calling it done.

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
