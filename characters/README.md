# Bean-head cast (main character style)

Original characters in the channel's target style: bean heads, a bean torso, thin ink-stroke limbs, dot hands, plum ink that is thicker on the shadow side, and lidded deadpan eyes. The style is shared with the reference channel. **No reference character is copied**: every cast member here is our own design.

- Spec: `references/reports/characters.md` §2 (measured from 96 reference frames). `scripts/bean.py` implements it.
- `character(build, skin, shirt, pants, expr, facing, hat, hat_col, hair, hair_col, outfit, glasses, arm_pose, prop, seed, white_head, moustache, lean)` returns a 600x1000 RGBA card with the soles at y=975.
  - builds: adult, stout, kid
  - expressions: neutral, stern, grin, shock, nervous, smile, smug, pained
  - hats: cap, beanie, hardhat, tophat
  - hair: short, side, bun
  - outfits: buttons, tie, belt, apron, overalls, coat_open, stripes, collar
  - arm poses (left, right): hang, wave, point, hold, hip, chin
  - props: mug, clipboard, wrench
- `scripts/cast_sheet.py out.png` renders the prototype cast. `out/in_scene_v1.jpg` shows two of them composited on the village night plate.
- The stickman (`stickman/`) is on hold. Its drawing rules about anatomy (each arm from its own shoulder, foreshortening, continuous strokes) still apply here.
