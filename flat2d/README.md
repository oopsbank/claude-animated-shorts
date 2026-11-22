# flat2d: rich flat-2D scene kit

Pillow + numpy helpers for 1080x1920 "rich flat 2D" scenes (the Director's look level, 2026-11-22: layered depth, haze, gradients, texture, faceted light/shadow planes, glow, rim light, contact shadows, particles, vignette). Every call draws one **layer**, back to front; its arguments (offset, seed, `t`, phase) are the animation parameters.

- `kit.py`: the layers.
  - **Sky and light:** `vgrad`, `radial` (sun/lamp/pool light), `light_rays`, `cloud_bands`, `haze`, `depth_fade`.
  - **Terrain:** `peak_range` (faceted lit/shadow planes and snow caps), `ice_cliff` (faceted glacier wall, crevasse seams, strata, icicles), `snow_ground`, `rocks`.
  - **Post:** `snow_particles` (3 depth planes, driven by `t`), `dust`, `grain` (paper and grain), `vignette`, `foreground_frame` (out-of-focus silhouettes).
  - **Characters:** `stick` (white stickman `#f6f6f2`, black outline), `place` (contact shadow, coloured aura, **rim light** on the light side; returns head geometry).
  - **Text and UI:** `label` (role pill), `title` (house headline), `caption` (PIPELINE "sentence" style), `pill`.
- `props.py`:
  - **Wardrobe and tools:** fur hat, ice axe, footprints.
  - **Lab:** microscope, flasks/tubes/bottles (glowing).
  - **Graphics:** a stamp (with `cracked=True`, split between words), a big X, an algae chain, a survey plane.
- `style_frames.py OUTDIR [--small DIR] [s01 s05 s11 s15]`: the blood-falls style frames. Every scene takes `t` (seconds), and the comment on each layer says how it moves.
- `sheet.py DIR`: joins the 540x960 review downscales into one sheet.

Rules kept: blur masks only, never straight RGBA (LESSONS); glow sits behind characters, never on faces (DRAWING_RULES 19); captions follow PIPELINE › Captions.
