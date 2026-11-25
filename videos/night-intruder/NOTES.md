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
.venv/bin/python flat2d/motion_qa.py FRAMES_DIR 4 8 13 22 27 32 34.3 38 42 47 55 62 68 74 75.3 --impacts ...
```
Final 1080: `SIZE=1080x1920` (sets `persp.SS = 2`) with the same `frames` / `encode` commands (not rendered here).
Render time at 540: about 1.7 s per frame per core (2400 frames in about 17 min on 4 cores).

## Look
- Stickmen: `FACE_STYLE='ref'`, `BODY_STYLE='round'`, R=132 / SEG_LEG=170 / SEG_ARM=112 / OUT=4.4.
  ME: messy (`wild`) dark hair, beige striped pyjamas (`#d9bf94`, the Director's lock), barefoot.
  THIEF 1: dark slate jacket (`uniform`), hood up + black balaclava drawn over the card (`masked_head`: only an eye
  slot shows the card's eyes), backpack, crowbar (hip or in hand). THIEF 2: the card stretched 1.28x wide, 2.05 m,
  flattened to one near-black colour (no face, the Director's lock), lit only by sodium rim light, a long steel
  wrench with a cold glint.
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
| 4 | 13-22 | Door crack opens from black, OTS from behind: ME (back view, hair over the head, lamp raised) walks to the stairs and creeps down, one step per audio footstep (14.9 + 1.2 k); the flashlight beam sweeps the cabinet through the stair mouth |
| 5 | 22-27 | MCU: ME with his back to the stairwell wall, beads of sweat, leans out and peeks round the corner (torch spill on his face) |
| 6 | 27-32 | POV past the blurred wall edge: THIEF 1 (hood, from behind) stuffs the laptop into the backpack, beam from under his chin onto the bag; the zip at 30.0 |
| 7 | 32-34.3 | Floor-level ECU: the bare foot comes down past the last step onto a child's toy car, CRACK at 33.2 (shards, a wheel flies, flash, jolt) |
| 8 | 34.3-38 | Frontal MS: THIEF 1 frozen, face lit from below by the torch; torch off at 34.9; pure black 35.0-37.0 (digital silence in the mix); the street-lamp spill slowly brings both shapes back 37-38 |
| 9 | 38-42 | Whip pan in (motion blur), profile: THIEF 1 spins and swings the crowbar, ME leans back, CLANG + sparks on the wall corner at 38.5, standoff |
| 10 | 42-47 | Dutch angle (-15 deg): ME lunges, lamp hits the weapon arm at 43.05 (flash, sparks, jolt), the crowbar falls, clatters and rolls (43.55-46.4) |
| 11 | 47-55 | Shaky high angle: the shove, THIEF 1 slammed down at 47.3, backpack flies and spills (laptop, watch, phone, cash, jewellery with glints), ME on top pinning the collar, struggle |
| 12 | 55-62 | Wide from behind the pile: the front door opens (latch 55.2), sodium wedge on the tiles, THIEF 2's silhouette in the doorway; caption of his line (words.json times); steps in 59.5; the door slams at 60.0 and the light is swallowed |
| 13 | 62-68 | Low CU: THIEF 1's head on the tiles, eyes narrow smug; his sleeve swings up, elbow at 62.9 (impact, ME's hands fly off), whip pan to ME sliding across the tiles 63.6-65.6, he lifts his head |
| 14 | 68-74 | Camera on the floor behind ME: THIEF 2 walks in from the lit window, one step per CLOMP (68.5, 69.9, 71.25, 72.5, 73.65), filling the frame, the wrench glinting |
| 15 | 74-80 | CU ME looking up in panic, arms up over his face (step jolt 74.7); hard cut 75.3 to the low angle: THIEF 2 towers, wrench raised (glint), swings down at 75.45 with a push-in; CUT TO BLACK at 76.000; black to 80.0 |

## Timing vs the soundtrack
Shot boundaries are the script's, except shots 7/8: the sound team placed the torch click-off at 34.9 with digital
silence from 35.0, so the frozen frontal moment of shot 8 runs 34.3-34.9 and black starts at 35.0 (shot 7 is
32.0-34.3). All other sync points from `audio/night-intruder/cues.md` are matched in the picture (listed above).
Caption: "You done" / "yet?" / "What's all" / "the noise?" from `audio/night-intruder/words.json`, house sentence
style (Poppins Bold 3.7% H, white, black outline, soft shadow, 1.08 -> 1.0 pop), baseline at 70% H (on the floor,
off every face).

## Known issues
- **No sonnet reviewer was run:** this Animator session had no subagent tool, so the stills were judged by the
  Animator only (two passes over all 15 key frames; my own estimate about 6.5-7/10 overall: clearly readable
  story beats, but not yet the target 8). A reviewer round on `stills` output is still owed.
- Motion QA (`flat2d/motion_qa.py`, cuts + audio impacts): 0 pops; the only frozen spans > 0.4 s are the deliberate
  black holds 34.93-37.2 s (torch off, digital silence) and 76.03-80.0 s (cut to black). The tool prints FAIL only
  because of those two holds.
- Shot 4: ME reads small and the stairs are dark; the stair mouth + beam on the cabinet read only weakly.
- Shot 5: the lamp head is mostly hidden behind ME's head; the lamp in general reads as a "hammer" at medium size.
- Shot 6: THIEF 1 from behind is a dark disc (hood) + jacket; the laptop going into the bag is small.
- Shots 11-12: the pinned pile is the two cards leaned by about 60-84 degrees (no real lying/kneeling poses);
  the pile is slid sideways in screen space (`SH11/SH12/SH13`) to keep it in frame.
- Shot 13: the masked head on the floor is a rotated card; the eye slot reads, the smug look is subtle at 540.
- Shot 14: THIEF 2 is a flat silhouette; until about 70 s he is small next to ME's head in the foreground.
- THIEF 1's jacket is the house `uniform` garment (buttons + belt buckle show).
- The thumbnail is a dedicated still (`thumb_frame`), not a frame of the film.
- 1080 final not rendered (expect about 4x the 540 time: persp.SS = 2 and 4x pixels, roughly 70-90 min on 4 cores).
