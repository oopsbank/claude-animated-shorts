# Bean-head cast (main character style)

Original characters in the channel's target style: bean heads, a bean torso, thin ink-stroke limbs, dot hands, plum ink that is thicker on the shadow side, and lidded deadpan eyes. The style is shared with the reference channel. **No reference character is copied**: every cast member here is our own design.

- Spec: `references/reports/characters.md` §2 (measured from 96 reference frames). `scripts/bean.py` implements it.
- `character(build, skin, shirt, pants, expr, facing, hat, hat_col, hair, hair_col, outfit, glasses, arm_pose, prop, seed, white_head, moustache, lean)` returns a 600x1000 RGBA card with the soles at y=975.
  - builds: adult, stout, kid
  - expressions: neutral, stern, grin, shock, nervous, smile, smug, pained
  - hats: cap, beanie, hardhat, tophat
  - hair: short, side, bun
  - outfits: buttons, tie, belt, apron, overalls, coat_open, stripes, collar
  - arm poses (left, right): hang, wave, point, hold, hip, chin, palm
  - props: mug, clipboard, wrench, plus `clipboard:<text>`, `helmet:<sticker>`, `broom_upright` / `broom_tip_left` / `broom_tip_right` / `broom:<deg>` (with arm pose `palm`)
- **Views:** `view='side'` or `'3q'` (facing < 0 faces left) goes through `turned()`, a rig with joint angles (`pose=dict(legN=(thigh, shin), legF, armN=(upper, fore), armF, lean, tilt)`, + = forward), IK targets (`handN`/`handF`/`footN`/`footF`, plus `hip` for a fixed hip), `mouth=`, `blink=` and `rig={}` to read back the solved joints. Rules: `RULES.md`.
- `turned()` also does `view='rear'` (no face, hair and hat from behind) and a jointed `view='front'`, `pad=` for a wider card, and `layers={}` to get the far / legs / upper / near layers separately.
- Hats: `helmet` (open-face; `sticker='I STEER WITH MY HIPS'` puts a label on the shell, large on the back).
- `scripts/bikes.py`: `draw_bike(kind, view, steer, lean, crank)` and `ride(char, bike, view, steer, lean | bike_lean + body_lean, hold='steer'|'fixed', knee_out, crank, expr, mouth, sticker)` return a 1000x1000 card (ground y=975). Bikes: `bicycle`, `motorbike`, `nobs_bike` (a second handlebar bolted to the frame; `hold='fixed'` grips it). Views: side, 3q, rear, front, top. `steer` + = front wheel to the bike's right; `lean` + = to the bike's right.
- `walk.py`: `walk_pose(t)`, `walk_track(seconds)` (foot-locked hip x per frame), `blink_at(t)`; `previews/walk_v1.png`.
- Lip sync: `mouth=` closed, small, open, wide, O, smile_talk in every view; `previews/mouths_v1.png` (`mouths_sheet.py`). Props: `previews/props_v1.png` (`props_sheet.py`).
- `scripts/inserts.py`: `broom_insert(pose, w=1080, h=1920, sleeve, skin, bg=None)` close-up cards; poses broom_upright, broom_tip_left, broom_flick_right, broom_tip_right, broom_flick_left.
- `scripts/ride_sheet.py out.png` renders `previews/ride_v1.png`.
- `scripts/views_sheet.py out.png` renders `previews/views_v1.png` (front, side and 3/4 for the whole cast).
- `scripts/cast_sheet.py out.png` renders the prototype cast (`previews/cast_v2.png`). `previews/in_scene_v1.jpg` shows two of them composited on the village night plate.
- The stickman (`stickman/`) is on hold. Its drawing rules about anatomy (each arm from its own shoulder, foreshortening, continuous strokes) still apply here.

## Video 2 (`sailing-stones`) additions
- **Hat `antennae`:** a dark plum headband with two springy green antenna balls (the guide and his tourists; the balls take `hat_col`).
  - `antennae='up'` (default), `'droop'`, or a float from 0 to 1 for the droop amount. The engine can ease it from 0 to 1 on "Fine. It's ice.".
  - `antennae_sway=deg`: spring wobble; + leans toward screen right.
  - Works in every view.
- **`seated='cooler'`** (front view): sits on a drawn picnic cooler, with the thighs angled out under the belly and the shins hanging down the cooler front. `seated='bare'` is the same pose with no seat, for the engine to place on its own `cooler` sprite. `seat_top(build)` gives the card y of the seat top. The soles stay at y=975.
- **Held props** (`held.py`), with arm pose `'hold'`: gps_box, screwdriver, googly_eyes, mug, laptop, frying_pan, ticket, cash_fan, camera, flashlight, phone (`'phone:<badge>'`), selfie_stick, megaphone, flag (`'flag:<text>'`), air_hockey_mallet, gary_rock (`'gary_rock:askew'`).
  - One hand on `'hold'`: small props (`held.SHOW`) are raised beside the head. The laptop and Gary stay at chest height. Poles (flag, selfie stick) are held close to the body. The forearm reaches the prop's edge from outside, and the dot hand (with a sleeve-coloured cuff) sits on top.
  - Both hands on `'hold'`: two-hand props (`held.TWO_HANDED`: gps_box, laptop, camera, phone, gary_rock) are held at the chest with a hand on each side edge. Any other prop goes in the right hand, and the left hand rests on the belly. For example, on the cooler the frying pan is raised like an oar.
  - The old props (clipboard, wrench, broom, helmet) are unchanged. `mug` now uses the new raised grip, which is the only old call whose output changed.
- **Engine sprites** (`sprites.py`): `sprite(name, t=0, k=1, **kw) -> RGBA`.
  - Units match the character card, so pass the same `k` as the card scale.
  - `im.info['anchor']` is the ground contact point (bottom centre), or the centre for UI cards.
  - Names: gary_rock (`eyes='askew'`, `look`), gary_buried, rock, gps_box, cooler, cooler_trophy, tent, tent_floating, timelapse_cam, tour_sign (`'tour_sign:LINE · LINE'`, ALIEN crossed out on the ICE TOURS variant), tour_sign_free (t: shudder, crack, both halves topple), flying_bills (t; gone by 0.9), banner, livestream_counter, price_card, fridge_silhouette and phone_silhouette (scale cues, `ghost=True`).
  - The shots.json prop strings (with notes in parentheses) are accepted as-is.
- **Sheets:**
  - `scripts/v2_sheet.py out.png crops.png` renders `previews/v2_wardrobe.png` and `v2_wardrobe_crops.png` (with a night row).
  - `scripts/sprites_sheet.py out.png` renders `previews/v2_sprites.png`.
  - The shared ink helper is `scripts/ink.py`.

