# Stickman character

An original solid-colour stickman, about 5 heads tall. It has a tube body, smoothly bent limbs, a thin dark outline, a lit head and an expressive face.

- `scripts/stickman.py`: `draw(expr, pose, color, hat, look)` returns a 600x1000 RGBA card with the soles at y=975.
  - Expressions: neutral, happy, angry, surprised, worried, scared, sad, smug, determined.
  - Poses: stand, wave, walk, run, point, shrug, think, cheer.
  - Hats: helmet, sailor.
- `scripts/sheets.py <outdir>`: rebuilds the reference sheets and the per-expression PNGs in this folder.
