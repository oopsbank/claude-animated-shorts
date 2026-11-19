# Blender night-village test (script-built)

Proof of concept for "option 2": the 3D world is built and rendered in Blender by script, with no manual work.

- `scripts/scene2.py`: builds a night village square (Quaternius medieval village + KayKit props, both CC0), a painted gradient sky with stars, a lamp, glowing windows, Freestyle ink, and a 2D character card. Renders with Cycles.
  `python scripts/scene2.py out.png [samples] [scale%] 0 [A|B]`. Shot A is the wide shot, shot B the close-up at the well. Set `CARD=/path/to/card.png` to change the character.
- `scripts/post.py`: warm-only bloom glow, standing in for the compositor (which needs a GPU in Blender 5).
- `scripts/dl.py`: downloads Poly Haven models via its API.

Setup (run from this folder):
- `uv venv -p 3.13 .venv && uv pip install -p .venv bpy pillow`
- Clone the packs to `../packs/` relative to this folder:
  - `KayKit-Game-Assets/KayKit-Medieval-Hexagon-Pack-1.0`
  - `trebeljahr/quaternius-showcase`
- Put the character card at `assets/sailor.png`, or set `CARD`.

Measured on a 4-CPU cloud container with no GPU, 720x1280 at 32 samples: about 58 s per frame for A, about 70 s for B. A full video needs a GPU render.
