# Study: Segment Zero (@segmentzero), 2 shorts (2026-11-21)

A second channel in our genre: "Why / How" explainers with bean-head 2D characters in 3D toon sets. **Study material only.** Never copy its scripts, characters, shots, titles or its progress-bar design, and never name it in our videos.

Sources: the oEmbed title and the three full-res frames YouTube serves (`i.ytimg.com/vi/<id>/oar1..3.jpg`). Frames are in `references/frames/segment_zero/`. The voice-over and the motion were not available, so the notes on tools are inferences.

| Short | ID | Topic angle |
|---|---|---|
| Why Every Train Carries Sand | t62JpTmUGNs | Locomotives drop sand on the rails for grip: steel on steel is slippery. Everyday analogy: socks on a shiny tiled floor. |
| The Deadliest Sniper Never Used a Scope | B07PK1vPyOg | A history paradox title (Winter War), told through soldiers in a log cabin and a snowy forest. |

## What they do that we don't (yet)
1. **Characters live inside the 3D space, not in front of it.**
   - A driver sits inside a locomotive cab, behind the window frame.
   - A soldier stands behind a snowy log, and feet sink into snow.
   - Background characters are smaller and softer (DOF on characters too).
   - It is probably 2D characters placed in the 3D scene (for example Blender Grease Pencil), so occlusion, DOF and perspective come for free.
2. **Lighting with mood:** a warm oil-lamp practical in a dark cabin, low golden sun with long shadows on snow, rim light on metal, steam/volumetrics. The sets carry ink outlines like ours.
3. **Motion:** motion blur on train wheels, and a smear frame on a fast rifle swing.
4. **Retention overlays:** a small top-centre progress map (a track profile with stages 1-2-3 and a marker for where the story is), plus a faint channel watermark.
5. **Captions:** sentence case, 1-2 words, white bold rounded sans (Poppins-like), dark outline, at about 70% of the frame height. Ours are upper case with yellow keywords, which is a valid alternative; keep ours.

## Measured frame stats (`references/scripts/frame_stats.py`)
| Frame | lum | p98 | sat | cool | edge |
|---|---|---|---|---|---|
| train-sand_1 | 0.36 | 0.84 | 0.33 | 0.26 | 0.05 |
| train-sand_2 | 0.37 | 0.76 | 0.35 | 0.04 | 0.05 |
| train-sand_3 | 0.71 | 0.98 | 0.29 | 0.15 | 0.06 |
| sniper_1 | 0.39 | 0.94 | 0.50 | 0.00 | 0.04 |
| sniper_2 | 0.58 | 0.89 | 0.30 | 0.46 | 0.06 |
| sniper_3 | 0.64 | 0.87 | 0.22 | 0.01 | 0.07 |

Their luminance ranges from 0.36 to 0.71 per scene, driven by the story mood (dark cabin, bright snow). Our 0.40-0.55 target is a house average, not a rule for every shot. Keep it as a warning.

## What we take from this (style, not content)
- Use the depth maps we already have to put characters **behind** near objects (depth-tested compositing), and blur far characters by depth. See BACKLOG engine P2.
- Add foreground occluder layers and ground contact (sinking feet in snow or sand), with smear frames for fast actions.
- Sets: one motivated practical light per interior, a low sun for exteriors, and some steam/dust volumetrics.
- Design **our own** retention overlay (not a copy of their progress map), for example a small chapter dot row in our palette.
