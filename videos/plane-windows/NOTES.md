# Plane Windows: "Why Are Airplane Windows Round?" (flat2d, claude/area-plane-windows, 2026-11-25)

Video 12, and the first video in the Director's **cinematic 2D style**. The house look stays: white stickmen with a black outline, rich flat 2D, "sentence" captions, a serious mystery tone with no comedy. On top of it, the sets are drawn from a moving 3D camera with real perspective, and the shots get depth of field, varied angles, few hard cuts, per-scene grades with a vignette, light shafts and water caustics.

It follows the Blood Falls formula:
- **Hero image** (frame 0, the loop frame and the thumbnail): a Comet fuselage sunk in a giant water tank in a 1954 test hangar, its wings sticking out through the tank walls on jacks.
- **Colour motif:** the teal of the tank water against the grey-green steel of the hangar.

The voice is Kokoro `am_adam` 1.16. The voice and mix are the Producer's `audio/plane-windows/` and are unchanged: 1956 frames = 65.20 s, about 65.3 s with the 0.1 s cover.

**Status:** the build, three review rounds (the brief's maximum; the ≥ 8 gate was not reached: 7.6 / 7.75 / 7.4), the 540 preview (motion QA PASS, exact loop), the thumbnail and these notes are done. **No 1080 final, nothing published.**

## Files
| file | what |
|---|---|
| `tests/preview_full_540.mp4` | the 540x960 preview, 30 fps, muxed with `audio/plane-windows/mix.wav` (AAC 192k) |
| `tests/sheet_2s.jpg` | a contact sheet of the preview, one frame every 2 s |
| `tests/stills_r1/`, `stills_r2/`, `stills_r3/` | the stills each review round saw: one per shot, 540x960, captions on, plus `sheet.png` |
| `tests/stills_r4/` | the round-3 fixes, checked by the Animator only (no 4th review; the brief allows 3 rounds) |
| `tests/stills_dev/` | the first pass |
| `tests/review_brief.md` | what each reviewer got: every still's voice-over line and its planned picture, plus the cinematic-upgrade brief |
| `thumbnail.png` | the hero image (see Thumbnail) + `tools/thumbnail.py`: WHY SINK (white) / A PLANE? (yellow) |
| `flat2d/plane_windows.py` | the shots `s01`-`s15` and `SHOT_LIST`, `END`, `STILL_AT`, `BAND_FIX`, `NO_PUNCH`, `HIDE_UI`. s01b, s04a, s04b, s05b, s07b, s09b and s11b are splits inside a line |
| `flat2d/plane_windows_thumb.py` | the thumbnail frame |
| `flat2d/persp.py` | **new, reusable:** the 3D camera and toon renderer (see Cinematic tools) |
| `flat2d/cine.py` | **new, reusable:** DOF, grades, light, transitions (see Cinematic tools) |
| `flat2d/airliner.py` | **new kit:** the Comet 1, a modern twinjet, the modern cabin set (3D), and 2D window close-up art |
| `flat2d/hangar.py` | **new world:** the 1954 test hangar and water tank in 3D |
| `flat2d/skyworld.py` | **new world:** the altitude sky |

## Cinematic tools (new in flat2d; reusable by later videos)
**`flat2d/persp.py`: a 3D camera and toon renderer.** World units are metres, z up.
- `Cam(pos, target, fov, roll, shift)` is a look-at pinhole camera. `shift` is a lens shift: it frames up or down while keeping verticals straight.
- `Path(keys)` is a camera move through keyframes `[(t, pos, target, fov, roll)]`. It runs Catmull-Rom through the keys, so the camera never stops at a key, and eases only at the first and last key. An optional handheld drift adds a slow wander.
- `Part` is the drawing unit:
  - parts are sorted far to near (painter's algorithm);
  - inside a part, back faces are culled, then the polygons, decals, 3D beams (`line`, width in metres) and 3D dots are drawn.
- Builders: `box`, `lathe` (fuselages, tanks), `loft` (wings, fins), `prism`, `quad`, `round_rect2d`.
- `render(layer, cam, parts, light, fog)` draws in the house flat2d look:
  - toon shading in soft bands with a cool shadow tint and optional specular (`Light`);
  - a per-face `fog(col, P, depth)` hook for haze or an under-water tint;
  - near-plane clipping, so the camera can fly inside a set;
  - supersampling (`persp.SS`: 1 for the preview, 2 when rendering 1080);
  - a silhouette ink rim per part (blur+threshold dilation);
  - the canvas clipped to the projected bounding box, for speed.
- Plane-split clipping (`airliner.clip_part`) cuts the Comet at the water line and at the tank walls, so the water and the walls composite correctly.

**`flat2d/cine.py`: depth of field, grades, light and transitions.**
- **Depth of field:**
  - `defocus` is a premultiplied blur, cached, and done at half size for big radii;
  - `coc` gives the circle of confusion for a depth;
  - `fg_frame` draws a defocused foreground framing layer (seat backs, a shoulder, a lamp shade, a pencil, a rail, a window rim, a riveted frame member);
  - `bokeh` draws out-of-focus point lights;
  - `multiplane` is a 2.5D camera: painted planes at depths with parallax, dolly and DOF.
- **Camera:** `cam2d` adds zoom, pan and roll for 2D shots, such as the rotating top-down map.
- **Grades:** `grade(img, look)`, with these presets:
  - `hangar`: cool grey-green, teal shadows, warm highlights;
  - `cabin`: warm;
  - `altitude`: bright thin blue;
  - `navy`: the diagram stage and high altitude;
  - `archive`: sepia paper and the office;
  - `water`: teal;
  - `desk`: warm tungsten;
  - `steel`: cool studio light on metal.
  The grades are per-channel LUT curves (lift, gamma, gain, contrast) plus split toning and saturation, so they are fast. `mix_grade` cross-grades between two presets.
- **Post:** `bloom`, `vignette` (soft and cached), and `finish` (grade, bloom, vignette and the boiling grain).
- **Light:**
  - `shafts` draws 2D light shafts;
  - `shafts3d` sweeps 3D openings (skylight strips) along the light direction to the floor, clips each edge at the near plane, and returns the mask;
  - `motes` draws dust that only shows inside the shafts;
  - `caustics` is an animated network made from the zero lines of warped sine fields;
  - `wobble` is a refraction row-shift;
  - `flare` is a sun flare with ghosts.
- **Transitions:** `xfade`, `through` (show the next shot through a mask), `iris`, `whip`.

**How the film uses them:**
- **s01 → s01b:** one continuous 7.2 s crane, from the high hero angle over the tank down to a porthole in the tank wall.
- **s01b → s02:** a match cut from the round porthole to a modern cabin window at the same place and size.
- **s03 → s04:** a push through the passenger's window into the sky.
- **s04b:** the plane fades into cloud, then a match cut to the same plane printed as a halftone photo in a 1954 newspaper.
- **s11 → s11b → s12:** one pan along one metal panel, from the round window to the sharp corner and into it.
- **s14 → s15:** a match cut from the cabin window to the porthole, then the crane back up to frame 0.

## Kits and worlds
**`flat2d/airliner.py`**
- `comet()` is the Comet 1, with no airline name or logo:
  - a 3.05 m slim fuselage with a drooping elliptical nose and a stepped cockpit (a brow over the windscreen), and an upswept tail cone;
  - a low swept wing whose thick roots bury the four engines: oval intakes sit flush in a blunt leading-edge bay, and round exhausts at the trailing edge;
  - a swept fin and tailplane;
  - twelve SQUARISH windows per side (small corner radii) inside a dark blue cheatline;
  - a white top and a polished-metal belly;
  - the two roof ADF windows;
  - an optional hatch window.
- `twinjet()` is a modern airliner: oval windows, podded engines and winglets.
- `cabin_shell` and `seat_row` build the modern cabin in 3D: sidewalls with a window per row, bins, ceiling light strips and seats.
- 2D close-up art: `window_art` (the inside of a modern window: bezel, deep reveal with parallax, shade, glare, breather hole), `squarish_window`, `skin_panel`.
- Helpers: `attitude`, `place`, `clip_part`.

**`flat2d/hangar.py`**
- The set:
  - a concrete floor with joints and safety lines;
  - big sliding doors with window strips, a cream dado, clerestories, stanchions;
  - a pitched roof on lattice trusses with skylight strips, purlins, an overhead crane and enamel lamps;
  - the tank: walls, ribs, girders, rivets, bolted portholes and wing seals;
  - gantries with yellow railings, hydraulic jacks under the wings that flex with each pressure cycle, pipes, a pump, a control desk, and floor clutter.
- The water:
  - a refraction wobble and caustics on the submerged Comet;
  - a Fresnel-graded veil;
  - planar reflections of the skylights and clerestories;
  - ripples round the fin, and a swell or surge;
  - portholes that show the under-water layer.
- `stand()` places stickmen at 3D foot points, and `CAM0`/`cam0()` is the frame-0 camera.
- `scene()` composites the layers in order: background (defocused), the far gantry and its engineers, the tank, the water, the parts above the water, the near engineers, the near rail, then the shafts and motes. It has hooks `extra_under`, `extra_mid` and `extra_after`, and `roof=False` for the thumbnail.

**`flat2d/skyworld.py`:** the altitude sky with a thin-blue gradient and the sun, cirrus, a cloud sea in parallax depth rows, and speed wisps.

## Build
```
.venv/bin/python flat2d/render.py audio/plane-windows/words.json OUT.mp4 --film plane_windows --size 540x960     # 1956 frames
.venv/bin/python flat2d/stills.py audio/plane-windows/words.json OUTDIR --film plane_windows [shot ...]           # review stills
.venv/bin/python flat2d/motion_qa.py OUT.mp4.frames <cuts> --impacts <beats>                                     # see Motion QA
ffmpeg -i OUT.mp4 -i audio/plane-windows/mix.wav -map 0:v -map 1:a -c:v copy -c:a aac -b:a 192k -shortest videos/plane-windows/tests/preview_full_540.mp4
.venv/bin/python flat2d/plane_windows_thumb.py frame.png
.venv/bin/python tools/thumbnail.py frame.png videos/plane-windows/thumbnail.png --line "WHY SINK|white|190" --line "A PLANE?|yellow|230"
```
Shot ids follow the Producer's `scripts/plane-windows/shots.json` (one per line). The splits stay inside a line, so the mix and the `sfx.json` anchors need no rebuild.

For the final, after the Producer's pass: run `render.py ... --size 1080x1920` (this sets `persp.SS = 2`, which supersamples the 3D sets), mux `mix.wav`, then `tools/add_cover.sh <video> videos/plane-windows/thumbnail.png <master>`.

## Shot list (timed to the real voice; a shot starts 0.1 s before its first word)
| shot | time s | line | picture (camera) |
|---|---|---|---|
| s01 | 0.00-5.31 | 1 (0-13) | **frame 0 = the hook and the loop frame:** the 1954 hangar, the giant tank, the Comet fuselage under the water, its wings out through the walls on jacks, the fin breaking the surface, engineers on the gantries, skylight shafts, a defocused rail in the foreground; 1954 / ENGLAND. The crane starts, with A WHOLE AIRLINER, GIANT WATER TANK (high angle) |
| s01b | 5.31-7.22 | 1 (14-) | the crane comes down to a porthole in the tank wall (squarish windows under water); a pressure gauge and a CYCLES counter rise into the foreground with rack focus, pulsing on "pumped / again / again" while the jacks flex the wings |
| s02 | 7.22-10.03 | 2 | match cut porthole → cabin window, pulling back over a passenger's shoulder (defocused); a bold arc traces the round corner; NO SHARP CORNERS, ? (over the shoulder) |
| s03 | 10.03-11.74 | 3 | the reverse angle down the cabin aisle (3D set, rows receding); the passenger by his window shrugs; JUST STYLE?; a push through his window into the sky (eye level) |
| s04 | 11.74-13.79 | 4 (0-6) | the Comet climbs past above the cloud sea (3/4 front chase: nose, stepped cockpit, wing-root intakes); FIRST JET AIRLINER, THE COMET |
| s04a | 13.79-14.98 | 4 (7-9) | the chase closes on its windows: red corner brackets; SQUARISH WINDOWS |
| s04b | 14.98-18.58 | 4 (10-) | the plane pulls away and fades into the cloud, then a match cut to its photo in a 1954 newspaper: COMET AIRLINER LOST OFF ELBA; the April paper slides in: SECOND COMET LOST / ALL COMETS GROUNDED; JUST STYLE? gets a red X (top-down) |
| s05 | 18.58-21.36 | 5 (0-8) | CLUE 1, a 1950s map from above, slowly rotating, a pencil defocused in the foreground: dotted climb-outs from ROME to markers off Elba (10 JAN 1954) and off Naples (8 APR 1954); BOTH WHILE CLIMBING |
| s05b | 21.36-22.88 | 5 (9-) | side view: the Comet climbs, air dots dense low and sparse high; THIN AIR / THICK AIR, AIR OUTSIDE: THINNER (crane up) |
| s06 | 22.88-27.34 | 6 | CLUE 2, the records office: an investigator behind a desk, two logbooks under a green lamp (defocused in the foreground), FLIGHTS counters roll to 1290 and 0900; NEITHER WAS OLD, ~1,000 FLIGHTS EACH |
| s07 | 27.34-30.57 | 7 (0-10) | CLUE 3, over the tank from the gantry (medium-high): TANK CYCLES 1830, the gauge falls, a split opens on the sunk fuselage and water boils up, the engineers start; THE TEST PLANE, SPLIT OPEN! |
| s07b | 30.57-32.98 | 7 (11-) | under water, macro push-in: the hatch window's sharp corner with the crack running from it (caustics, light rays, motes); THE SHARP CORNER, OF A HATCH WINDOW |
| s08 | 32.98-34.67 | 8 | the riddle: the cracked panel on a workbench in perspective, an engineer with a magnifier behind (rack focus), a lamp in soft focus; a big ?; WHY THE CORNER? |
| s09 | 34.67-37.49 | 9 (0-12) | a modern airliner comes at us nose-on and dissolves into the cross-section: deep high-altitude sky, the warm cabin with seated passengers fills with air (pump arrows); UP HIGH: THIN AIR, CABIN: PUMPED FULL OF AIR, SO YOU CAN BREATHE |
| s09b | 37.49-39.76 | 9 (13-) | the ring swells (arrows out, a dashed ghost), a balloon inflates; SWELLS, LIKE A BALLOON, (EXAGGERATED) (slight tilt) |
| s10 | 39.76-42.78 | 10 | landing at dusk: the runway rises, the ring shrinks back (inward arrows, a ghost of the swollen ring); then a flight arc, a SQUEEZES counter and the ring pulsing per flight; LANDING, SHRINKS BACK, 1 FLIGHT = 1 SQUEEZE |
| s11 | 42.78-45.68 | 11 (0-8) | the mechanism panel: stretch lines (a stream function solved round the holes) flow smoothly round a ROUND WINDOW in cool colours; STRETCH, FLOWS SMOOTHLY PAST + check (defocused frame member in the foreground) |
| s11b | 45.68-48.43 | 11 (9-) | the same panel, panned to the SHARP CORNER window: the lines bunch, all four corners glow, lines funnel into the hot top-right point; PILES UP, ONE TINY POINT + arrow |
| s12 | 48.43-53.70 | 12 | macro on that corner: SQUEEZES counter, a crack grows a little each squeeze, then rips (flash, shake); METAL FATIGUE |
| s13 | 53.70-57.89 | 13 | macro with shallow focus: a person (soft, behind) bends a paperclip with both hands; BENDS 1 → 100, ONCE IS FINE + check, x100, the bend glows, SNAP! |
| s14 | 57.89-61.11 | 14 | the flip, the biggest title, over a round cabin window on the clouds: NOT ABOUT LOOKS. / ABOUT NOT TEARING OPEN. (yellow, slam + shake on "tearing") |
| s15 | 61.11-65.20 | 15 | match cut window → porthole, then the crane back up to the frame-0 pose; A TANK OF WATER, 1954 / ENGLAND. **The last frame is `s01_frame(0)`, s01's frame 0 (the loop)** |

## Review (stills only)
Each round used one fresh sonnet reviewer. It got:
- each still with its voice-over line and planned picture, plus the cinematic-upgrade brief (`tests/review_brief.md`);
- the in-order sheet;
- `videos/wind-cave/tests/sheet_2s.jpg` as the bar.

| round | stills | richness / readability / composition / cinematic | overall | script contradiction | 3+ run | result |
|---|---|---|---|---|---|---|
| 1 | `stills_r1` | 7.5 / 8 / 7.5 / 7.5 | 7.6 | s05b (an arrow pointed down while the plane climbs; the wing seen edge-on read as a pod) | s09-s12 one blue/navy block | FAIL |
| 2 | `stills_r2` | 7.5 / 8 / 7.5 / 8 | 7.75 | none | s09-s10 ring, s11-s12 panel (judged fine for a mechanism) | FAIL |
| 3 | `stills_r3` | 7 / 8 / 7 / 7.5 | 7.4 | none | s09/s09b/s10 ring framing, s11/s11b/s12 panel | FAIL |

**The ≥ 8 gate was not reached** in the three rounds the brief allows (7.6 → 7.75 → 7.4; fresh reviewers vary by about ±0.5 on the same work).

Fixes by round:
- **R1:**
  - s05b: the arrow removed and the camera raised so the swept wings read;
  - the blue mechanism block broken: s09/s09b went deep high-altitude navy with a warm cabin glow, s10 a warm dusk landing, and the panel shots got a framing member and a light sweep, with s12 warmer;
  - s04 split into s04 (the whole Comet, 3/4 front view) and s04a (the windows);
  - the s04b chip moved, and the s12 title moved;
  - the cross-section enlarged;
  - a defocused rail added in frame 0;
  - the match cuts aligned (porthole ↔ window position and size; the plane ↔ the newspaper photo).
- **R2:**
  - s10 now shows the shrink, with a ghost of the swollen ring;
  - the Comet's root bays given a blunt leading edge so the intakes sit flush, not like pods, and its windows enlarged;
  - only the corners go red in s11b;
  - chip and caption collisions fixed in s04b, s06, s08 and s11;
  - s03 tilted down;
  - s09 and s09b framed differently;
  - s07 got a split line on the sunk fuselage.
- **R3** (checked on `stills_r4` by the Animator only):
  - all four corners glow in s11b, with lines funnelling into the hot point;
  - the Comet lit on its visible side, so the top is white, not lavender;
  - s04 kept wide through THE COMET;
  - the s07 split line moved under the water;
  - s12 kept on the panel with the crack clear of the title;
  - label and caption separations in s07b, s09b and s10;
  - Elba moved into frame in s05;
  - a lamp added in s08, the investigator enlarged in s06, and foreground window rims added in s09/s10.

Open notes (the reviewers' remaining points, for the Producer and Director):
- The diagram shots (s05b, s09-s12) are still flatter than the hangar and cabin sets. The cross-section ring repeats across s09-s10, and the panel repeats across s11-s12 (they are one continuous move each).
- Some captions repeat a title word (s12 "fatigue.", s14 "open."). Captions show every spoken word by house rule.
- The JUST STYLE? chip in s03 is small when it pops.

## Motion QA (`flat2d/motion_qa.py`)
On the 1956 preview frames:

`motion_qa.py FRAMES 5.31 7.22 10.03 11.74 13.79 14.98 18.58 21.36 22.88 27.34 30.57 32.98 34.67 37.49 39.76 42.78 45.68 48.43 53.70 57.89 61.11 --impacts 11.40 30.05`

The result is **PASS**: median diff 2.63, the longest frozen span is 2 frames (0.07 s), and there are no pops. The cuts are the shot starts. The impacts are two designed beats: the push through the cabin window into the sky (11.40) and the flash on "split" (30.05).

- The first QA run found pops, now fixed:
  - **s14 at 60.87 (and the same pattern in s07, s12 and s13):** a fixed 1.02 cover zoom was used during a camera shake and snapped back to 1.0 on the shake's last frame. `shake_cam` now scales the zoom with the shake amplitude, down to 1.0.
  - **s10 at 41.5 and 42.3:** the quick flight cycles overlapped, so the sky jumped between dusk and altitude. The cycles no longer overlap and the ground holds still.
  - **s15 at 61.33:** the match-cut dissolve ran past the cut window. It now lasts 0.2 s.
- Those frame ranges were re-rendered and spliced in by frame index (frames are a pure function of film time): 895-917, 1238-1283, 1555-1584, 1720-1736, 1810-1846.
- The full render had crashed at 21.2 s: s05b's air density took a negative base to a fractional power. That is fixed, every shot passed `flat2d/smoke.py` (start, middle and last frame), and the render resumed from frame 635.
- **Frame 0** (checked): the hero tank shot with 1954 / ENGLAND, the engineers and the defocused rail.
- **Loop:** s15's last frame (f 1955) is `s01_frame(0)`. Its mean abs difference from frame 0 is **0.0/255**.
- **Preview:** `tests/preview_full_540.mp4` is 1956 frames, 65.20 s, h264 + AAC 192k, 19.8 MB.
- **Render cost:** frames are drawn at 1080 and downscaled. A hangar frame is ~6 s and a 2D diagram frame ~2-3 s, so the full 540 render takes ~50 min on 4 cores (the 1080 final will be similar, plus supersampling on the 3D sets).
- **Speedups added:**
  - `persp.render` clips its canvas to each part's bounding box;
  - small stickmen reuse cached cards (`anim.actor(quant=2)`), and extras in the cabin don't sway, which took s03 from 25 s to 4 s a frame;
  - the stress-line glow is cached.

## Thumbnail
`flat2d/plane_windows_thumb.py` follows the Producer's change (approved by the Director): the thumbnail is the hero image itself, readable at a glance without text.
- It shows the Comet fuselage sunk in the giant tank, with both wings out through the walls, engineers on both gantries, and skylight light pools.
- The camera is high over the nose end, looking along the fuselage, so the airliner's cross shape fills the frame. The roof is left out of that render so the camera can rise above the trusses.
- The top third is darkened for the headline. `tools/thumbnail.py` adds WHY SINK (white, 190) / A PLANE? (yellow, 230).

## Sound
The Producer's mix (`audio/plane-windows/mix.wav`, `sfx.json`, `music.json`) is used unchanged. The shot ids keep their cue anchors, since the splits are inside lines. The picture lands on the cue sheet's beats:
- the 1954 title pop at 0.28;
- the pump hiss and metal groan on the s01b pulses;
- the whoosh on the porthole → window match cut;
- the jet pass as the Comet flies in;
- the card pops on the CLUE badges;
- the crack ping on the split (30.05) and on the crack (50.05);
- the paperclip snap (57.54);
- the impact on "tearing" (60.45);
- 1954 at 64.10.

## Open notes
- Acting and feel are the Director's call on `tests/preview_full_540.mp4`. The Producer reviews `tests/sheet_2s.jpg` against the script before any 1080 final.
- Simplified, as in SCRIPT.md:
  - the tank counter shows 1830 (the tank's own cycles);
  - the newspaper pages are generic, period-styled props: no real masthead, the dates are the day after each loss;
  - the map markers stand for the two loss areas, not precise positions.

## Final (the Producer, 2026-11-25, rendered locally; no fix session)
The Producer's preview pass found no defects worth a fix session. `plane_windows_final_1080x1920.mp4` (**the posting copy**): `render.py audio/plane-windows/words.json OUT.mp4 --film plane_windows --size 1080x1920` (30 min on 4 cores), mux `audio/plane-windows/mix.wav`, `tools/add_cover.sh <muxed> videos/plane-windows/thumbnail.png <master>`, 2-pass libx264 high 5200k `-preset slow`, AAC 192k, +faststart. 1080x1920, 1959 frames (3 cover + 1956), **65.32 s**, **43.9 MB** (43,909,931 bytes). Loop: last frame = frame 0 (diff 0.0); frame 0 checked by eye. Posting title (the Director's OK): "In 1954, They Sank a Whole Airliner in a Tank ✈️". Not published.

## Posted 2026-11-25 (Buffer, media file `plane_windows_1080x1920.mp4`)
- TikTok 6b06ea74cdd06687d1a38c13 https://tiktok.com/@somecrazythingzz/video/7712109405784870164
- Facebook 6b06ea7fd1898df0f7fb5695 https://facebook.com/1395801306957363_122109438021549918
- YouTube: shareNow refused (LimitReachedError, 2 YouTube posts that day); scheduled in Buffer as 6b06ea92d1898df0f7fb6404 for 2026-11-26 04:30 UTC (11:30 Vietnam).
