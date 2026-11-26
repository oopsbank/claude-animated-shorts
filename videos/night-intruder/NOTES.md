# Night Intruder (video 13): Animator notes

Build script: `flat2d/night_intruder.py` (one file: the house set, characters + props, 15 shot functions, captions,
parallel renderer, encoder, contact sheet). The shot list in `scripts/night-intruder/SCRIPT.md` is the contract; the
picture is cut to the sound team's sync points in `audio/night-intruder/cues.md` (see Timing below).

## Commands
```
# key-frame stills of every shot (540x960) or chosen times (shot:time)
.venv/bin/python flat2d/night_intruder.py stills OUT [s01 s07:33.3 ...]
# all 2400 frames, 4 processes (skips frames that already exist; t0/t1 optional)
.venv/bin/python flat2d/night_intruder.py frames FRAMES_DIR [--t0 38 --t1 42]
# encode with the mix (CRF env, default 24)
.venv/bin/python flat2d/night_intruder.py encode FRAMES_DIR videos/night-intruder/preview_540.mp4 --audio audio/night-intruder/mix.wav
# 2 s contact sheet (frame at k*2 + 0.5 s)
.venv/bin/python flat2d/night_intruder.py sheet FRAMES_DIR videos/night-intruder/sheet_2s.jpg
# thumbnail frame (1080x1920, no caption) -> tools/thumbnail.py
SIZE=1080x1920 .venv/bin/python flat2d/night_intruder.py thumbframe thumb_frame.png 17.0
# motion QA (cuts + impacts)
.venv/bin/python flat2d/motion_qa.py FRAMES_DIR 4 8 13 22 27 32 34.3 38 42 47 55 62 68 74 75.3 --impacts 0.55 2.55 4.3 7.05 \
  10.0 11.6 30.0 33.2 34.9 37.0 38.5 43.05 47.3 47.8 60.0 62.9 63.35 63.55 68.5 69.9 71.25 72.5 73.65 74.7 75.45 76.0
```
Final 1080: `SIZE=1080x1920` (sets `persp.SS = 2`) with the same `frames` / `encode` commands (not rendered here).
Render time at 540: about 1.7 s per frame per core (2400 frames in about 17 min on 4 cores).

## Look
- Stickmen: `FACE_STYLE='ref'`, `BODY_STYLE='round'`, R=132 / SEG_LEG=170 / SEG_ARM=112 / OUT=4.4.
  ME: messy (`wild`) dark hair, beige striped pyjamas (`#d9bf94`, the Director's lock), barefoot.
  THIEF 1: a plain dark hooded zip jacket (`uniform` + the new opt-in `plain=True` of `stickman.draw`: zip line +
  front pocket, no buttons/belt), hood up (from behind: a peaked hood shell draping onto the shoulders, seam + folds) + black balaclava drawn over the card (`masked_head`: only an eye
  slot shows the card's eyes), backpack, crowbar (hip or in hand). THIEF 2: the card stretched 1.28x wide, 2.05 m,
  flattened to one near-black colour (no face, the Director's lock), lit only by sodium rim light, a long steel
  wrench with a cold glint. From shot 12 on he is a dedicated 2D silhouette (`thief2_sil`: broad square shoulders,
  long coat, collar up, stride, the wrench arm hanging / raised / swinging) with a backlit rim (`sil_finish`).
- The desk lamp (`lamp2d`, redesigned in the fix pass): round weighted base (a short cylinder), lower arm + spring,
  knuckle, upper arm, cone shade with the bulb, cord + plug dangling; held by the lower arm above the base, drawn at
  0.74 x the old prop scale so it reads as a lamp, not a hammer.
- Set: one 3D house (`house_parts`): tiled living room, enclosed stairs with a header over the stair mouth,
  display cabinet, window with lit blinds, sideboard, front door (a hinged `door_part`), sofa (rounded prisms),
  TV, plant, coats, pictures. Night = render the day palette then `toonlight.night_map` onto a darker `LOW_RAMP`.
- Light sources only: phone screen (shots 1-3), the street lamp (warm stripes of the blinds on the floor, the lit
  slats, the gap under the door, the open door in shot 12; also the rim on every character from shot 9 on), the
  flashlight (`beam`: soft cone + brighter core + motes + hot spot; lens glow under THIEF 1's chin).
- Close-ups draw the stickman card at a higher supersample (`big_card`) instead of upscaling it. Hands in macros are
  cartoon hands (`hand2d`: palm, four fingers, thumb; open / grip); held props get a `fist` with knuckle creases.

## Shots (times in s)
| # | time | what the frame does |
|---|---|---|
| 1 | 0-4 | ECU on the nightstand: the dark phone lights up at 0.55 s (00:00 lock screen), glow on the wood, the metal lamp and its plug behind; slow push in; a small jolt on the clack at 2.55 |
| 2 | 4-8 | Top-down CU of ME on the pillow: eyes closed, snap open at 4.3, he tilts his head toward the door during the silence, flinches on the screeches (7.05, 7.58) |
| 3 | 8-13 | Handheld CU: a striped arm + cartoon hand gropes the nightstand (nudges the phone), grips the lamp stem at 10.1, lifts against the cord, the plug pops out of the socket at 11.6 (sparks, jolt), lamp lifts out of frame |
| 4 | 13-22 | The bedroom door leaf slides open from a crack, then OTS from high behind ME: a purpose-drawn back view (`me_stairs_3d`, `body2d`) creeping down, each foot contact on its audio footstep (14.9 + 1.2 k), feet planted on the 3D treads by IK, support knee lowering him, lamp arm lagging, left hand sliding on the partition; the camera floats behind, smoothed. The bottom of the frame is a second plate (`s04_plate_b`: the foot of the stairwell and the living-room cabinet) blended in under a dark seam, the torch beam sweeping across the cabinet |
| 5 | 22-27 | MCU with a slow push-in: ME pressed to the wall, sweat beads sliding down, the lamp low in his other hand (clear of his head); he leans out and peeks (head moves out, worried -> scared, torch rim on his face); the rummaging torchlight flickers over the walls |
| 6 | 27-32 | POV past the blurred wall edge: THIEF 1 from behind against the lit blinds (peaked hood, strong sodium back-rim on hood + shoulders, torch rim), the crowbar on his hip, the laptop (glinting) slides into the open backpack 28.0-28.8, the torch from under his chin lights the bag (beam + pool), the zipper pull races across at 30.0, the bag lifts |
| 7 | 32-34.3 | Floor-level ECU: the bare foot comes down past the last step onto a child's toy car, CRACK at 33.2 (shards, a wheel flies, flash, jolt) |
| 8 | 34.3-38 | Frontal MS: THIEF 1 frozen, face lit from below by the torch; torch off at 34.9; pure black 35.0-37.0 (digital silence in the mix); the street-lamp spill slowly brings both shapes back 37-38 |
| 9 | 38-42 | Whip pan in (motion blur), profile: THIEF 1 spins and swings the crowbar, ME leans back, CLANG + sparks on the wall corner at 38.5, standoff |
| 10 | 42-47 | Dutch angle (-15 deg): ME lunges, lamp hits the weapon arm at 43.05 (flash, sparks, jolt), the crowbar falls, clatters and rolls (43.55-46.4) |
| 11 | 47-55 | Shaky handheld, 3/4 top-down (`pile_cam`), purpose-drawn bodies (`pile_poses`): the shove in 3 beats (47.0-47.12 ME's shoulder into THIEF 1's back, 47.12-47.3 both topple, impact 47.3 with jolt + dust puff), ME lands astride and settles by 47.55, kneeling with both fists on the collar; THIEF 1 face-down, head turned to us, kicking + flailing; the backpack flies and its contents spill around |
| 12 | 55-62 | Low, from behind the pile: the front door opens (latch 55.2), a strong sodium wedge on the tiles with THIEF 2's long shadow, THIEF 2 a big backlit silhouette filling the doorway (~60-70% of the frame height, wrench in his right hand); caption 1.3x; steps in 59.5; the slam at 60.0 swallows the light (the door's frosted glass glows after) |
| 13 | 62-68 | Low CU on the tiles: THIEF 1's hooded masked head lying on its cheek (card head + hood, tilted 34 deg, floor shadow), ME's fists on his collar; the lids drop into the eye slot (smug squint), the eyes slide up to ME; elbow at 62.9 (flash, ME's hands fly off), whip pan to the slide 63.6-65.6: ME on his back across the foreground, the door glass glowing and THIEF 1 getting up behind (prone -> all fours -> crouch -> stand), ME rolls onto his elbow and lifts his head |
| 14 | 68-74 | Camera on the floor: ME in the foreground lying on his side propped on one elbow, head turned back up toward THIEF 2 (face in profile/3-4, scared -> surprised, trembling); THIEF 2's silhouette walks from the door toward the lens, one stride per CLOMP (68.5, 69.9, 71.25, 72.5, 73.65), the wrench glinting |
| 15 | 74-80 | CU ME looking up in panic: the startle (head pulls back 74.70), the hands lead both forearms up with an overshoot, elbows follow, they cross in front of his face 74.74-75.04, tremble; hard cut 75.3 to the low angle (keystoned): THIEF 2 towers, wrench raised high (glint), swings down 75.45-75.95 with a push-in + blur; CUT TO BLACK at 76.000; black to 80.0 |

## Timing vs the soundtrack
Shot boundaries are the script's, except shots 7/8: the sound team placed the torch click-off at 34.9 with digital
silence from 35.0, so the frozen frontal moment of shot 8 runs 34.3-34.9 and black starts at 35.0 (shot 7 is
32.0-34.3). All other sync points from `audio/night-intruder/cues.md` are matched in the picture (listed above).
Captions: THIEF 2's line "You done" / "yet?" / "What's all" / "the noise?" (`audio/night-intruder/words.json`) in pale
sodium yellow, 1.3x, baseline 70% H; ME's whispered narration (`audio/night-intruder/vo_words.json`, 4 lines) in white,
house size, chunks of 1-3 words (`VO`, built at import), only inside each line's window (0.85-6.23, 14.37-20.21,
23.62-28.15, 60.55-65.49; line 4 splits around the elbow: "They..." ends 62.44, "weren't alone." 64.4); baseline per
shot in a clean band (`vo_base`: 62.5% H in shot 4 = the dark seam, 20% H during the slide, else 80% H). House style:
Poppins Bold 3.7% H, black outline, soft shadow, 1.08 -> 1.0 pop. The preview is muxed with the rebuilt mix (c84b24a).

## Fix pass 1 (Producer review of the 540 preview, 2026-11-25)
Rebuilt shots 4, 5, 6, 11, 12, 13 (the CU half), 14 and 15 and the desk lamp; shots 1-3, 7-10, the toy car ECU, the
black holds and every sync point / shot boundary are unchanged. Iterated on 540 key stills (3 rounds + fixes).
- Motion QA (impacts list above): **0 pops**; the only frozen spans > 0.4 s are the planned black holds
  34.93-37.2 s (68 frames) and 76.03-80.0 s (119 frames), so the tool still prints FAIL only for those two.
- Bugs met on the way (kept here for the next pass): `TL.glow_at` / `add_light` apply their `mix` pull even when k
  is ~0, so a glow faded in with k alone makes a one-frame colour jump; scale `mix` with the fade too.

## Fix pass 2 (Director: "fix it", every shot >= 8/10; plus natural motion; 2026-11-26)
- New `flat2d/body2d.py`: figures drawn from joints (`figure`), pose builders + 2D/3D IK, `stair_descent` gait (see
  LESSONS > Natural motion). In night_intruder.py: `head_sprite`/`put_head` (card head + hair / hood + balaclava as a
  rotatable sprite), `me_style`/`thief_style`, poses `prone_J`, `kneel_J`, `elbow_J`, `slide_J`, `stand_J`,
  `thief_getup_J`, `jlerp`, `eback` (overshoot ease), `dust`.
- Rebuilt: shot 4 (gait + reframe + bottom plate), 6 (rims, beam on the bag), 11 (shove + pin), 13 (CU head, slide,
  get-up), 14 (ME on his elbow), thumbnail (new lamp, plain jacket, the toy car on the bottom step). Motion timing
  tweaks: 5 (stepped peek), 9 (dodge reflex), 15 (startle + overlap). Narration captions added.
- Reference clips: YouTube media is blocked by the session proxy, so the motion data are from biomechanics knowledge.
- Motion QA (impacts list above): 0 pops; frozen spans > 0.4 s only the planned black holds (34.93-37.2, 76.03-80.0).

## Known issues
- No sonnet reviewer run (no subagent tool here); stills judged by the Animator only.
- Shot 4: looking down a flight from behind, the far end always projects ABOVE the walker, so the cabinet at the
  bottom of the frame is a cheat: a second plate blended under a dark seam at ~56-67% H. ME's head is big from this
  high angle (the big-head proportions) and the first 1.5 s (on the landing) shows mostly walls.
- Shot 5: in the MCU the lamp is held low (base at the hip, arm up beside him), so its shade is partly out of frame.
- Shot 11: during the shove (47.0-47.2) the two bodies overlap (ME's head over THIEF 1's back) for ~6 frames.
- Shot 13: the CU head is still a round hood + slot (stylised), just tilted onto the cheek with a floor shadow.
- Shot 12: the pile in the foreground is reduced to ME's back + THIEF 1's legs; THIEF 2 is drawn clipped to the
  door gap while the door swings open, the frosted door glass only glows after the slam (a cheat, not visible).
- Shot 15: the low angle is a keystoned 2D silhouette, the wrench's swing is a 0.5 s blur into the black.
- 1080 final not rendered (expect about 4x the 540 time: persp.SS = 2 and 4x pixels, roughly 70-90 min on 4 cores).
