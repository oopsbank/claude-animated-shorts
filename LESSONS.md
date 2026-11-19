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

## Process
- Render a cheap low-res still after every change, and look at it before rendering full size.
- Compare side-by-side with a reference frame. Numbers and adjectives lie; pictures don't.
- When the user corrects something, fix it **and** add a rule so it never happens again.
- Show every pose and every joint at 2x zoom before calling it done.
- Measure ink density (`frame_stats.py` edge) on full-size plates: 25% test renders read about half the real edge density.
- Two Blender renders at once on 4 CPUs each run at half speed. Queue full-size plates; overlap only cheap low-res tests.
