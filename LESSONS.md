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
- Review animation on a dense sheet (t = 1/12 .. 11/12), never only on a 5-frame strip. Pops at the entry or exit and frozen holds hide between the samples.
- PIL `GaussianBlur` on straight RGBA drags black in from empty pixels, which gives grey or brown halos. Blur only the alpha channel and keep the RGB solid.
- Feed each reviewer round the same inputs, and turn every fix into a rule (for example `fx/RULES.md`). Otherwise the next round undoes the last one: alpha fades get swapped for shrinks, then the shrink pops.
- Render a cheap low-res still after every change, and look at it before rendering full size.
- Compare side-by-side with a reference frame. Numbers and adjectives lie; pictures don't.
- When the user corrects something, fix it **and** add a rule so it never happens again.
- Show every pose and every joint at 2x zoom before calling it done.
