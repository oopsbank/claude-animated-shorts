# Engine rules (learned while building it)

- Seed anything random per character with `zlib.crc32`, never `hash()`. String hashes differ between worker processes, so blinks would differ from frame to frame.
- Never upscale a 600x1000 bean card. A medium shot needs a scale of about 1.4. Downsample bean's 4x canvas instead (`rig._render`).
- A face-feature overlay needs an inpainted skin patch (fill the ink with the surrounding skin, blur, then a feathered paste). A flat median-colour patch leaves a visible oval on the crescent shading.
- A lean rotates the card about the soles, which drops one foot below the ground line. Re-plant the card on its lowest opaque row.
- Measure feet for QA from the **unrotated** card's bottom band, then rotate the points. Measuring after the rotation swaps which foot is lowest, and the planted-feet check fires falsely.
- Every directional camera move (glide, pan, tilt) needs a base zoom of `1 + amount`, or the plate's border shows. `camera_xform` also clamps the view centre and raises the zoom for roll.
- `shots.json` left/right are the **rider's**. A character facing the viewer has their left on screen right: swap `arm_pose` and negate `lean` unless `view` is `rear`.
- Report stand-ins (missing plates, hats, arm poses) once, from the main process. Workers repeat every warning 4x.
- At zoom 1.0 the anti-border clamp cancels every camera shake and kick. Any shot with kicks or `shake` needs a base zoom of at least 1.02.
- Bike cards (`bikes.ride`) don't touch y=975 in rear view, because the tyre sits about 17 card px higher. Always re-plant a rig card on its lowest opaque row.
- Bound card caches by bytes, not by count. A close-up rider card is about 4000 px square (64 MB), so a 120-entry cache per worker got workers OOM-killed. `multiprocessing.Pool.imap` then **hangs forever**, so use `ProcessPoolExecutor`, which raises `BrokenProcessPool`.
- Hand workers contiguous frame chunks (`chunksize=12`). A sampled render (`--frames A:B:20`) misses the cache on every frame and is the worst case for timing, so don't use it to estimate a full render.
- Capture hi-res cards at the card function's own final 4x->design-size resize. Picking "the first canvas of the right size" grabbed a single layer of turned/rear views (arms only).
