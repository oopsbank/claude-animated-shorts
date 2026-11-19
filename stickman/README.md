# Stickman character

An original solid-colour stickman, about 5 heads tall. It has a tube body, smoothly bent limbs, a thin dark outline, a lit head and an expressive face.

- `scripts/stickman.py`: `draw(expr, pose, color, hat, look, fixed, **wardrobe)` returns a 600x1000 RGBA card with the soles at y=975.
  - Outfits: `shirt=`, `coat=`, `uniform=`, `apron=`, `pants=` (a `'#rrggbb'` colour, or `True` for the default), or `outfit=` a preset in `OUTFITS` (sailor, captain, soldier, chef, detective, worker, farmer). Explicit keywords override the preset.
  - Expressions: neutral, happy, angry, surprised, worried, scared, sad, smug, thinking, determined.
  - Poses: stand, wave, walk, run, point, shrug, think, cheer.
  - Hats: helmet, sailor.
- `scripts/sheets.py <outdir>`: rebuilds the reference sheets and the per-expression PNGs in this folder.

**Before drawing or changing anything, read [`DRAWING_RULES.md`](DRAWING_RULES.md).** It lists the user's corrections: one flat colour, merged silhouette, continuous strokes, symmetric front view, each arm from its own shoulder, and foreshortening.
