# Engine rules (learned while building it)

- Seed anything random per character with `zlib.crc32`, never `hash()`. String hashes differ between worker processes, so blinks would differ from frame to frame.
- Never upscale a 600x1000 bean card. A medium shot needs a scale of about 1.4. Downsample bean's 4x canvas instead (`rig._render`).
- A face-feature overlay needs an inpainted skin patch (fill the ink with the surrounding skin, blur, then a feathered paste). A flat median-colour patch leaves a visible oval on the crescent shading.
- A lean rotates the card about the soles, which drops one foot below the ground line. Re-plant the card on its lowest opaque row.
- Measure feet for QA from the **unrotated** card's bottom band, then rotate the points. Measuring after the rotation swaps which foot is lowest, and the planted-feet check fires falsely.
- Every directional camera move (glide, pan, tilt) needs a base zoom of `1 + amount`, or the plate's border shows. `camera_xform` also clamps the view centre and raises the zoom for roll.
- `shots.json` left/right are the **rider's**. A character facing the viewer has their left on screen right: swap `arm_pose` and negate `lean` unless `view` is `rear`.
- Report stand-ins (missing plates, hats, arm poses) once, from the main process. Workers repeat every warning 4x.
