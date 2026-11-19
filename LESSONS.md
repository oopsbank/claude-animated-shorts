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
