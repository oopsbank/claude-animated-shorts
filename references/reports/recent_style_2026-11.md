# Recent style study (Nov 2026): the 31 newest explainer shorts

Private study. The source is 3 full-res frames per video (`i.ytimg.com/vi/<id>/oar1..3.jpg`, at about 25/50/75% of the runtime), 93 frames in total. YouTube blocks video, caption and storyboard downloads, so motion and audio could not be measured here (see `motion.md` for the older set). Numbers mask the caption band (60-75% of the height). No reference character, script or shot is to be copied; these are general targets.

## 1. Value and colour: our plates are far off

| metric (median, caption masked) | reference, all 93 (IQR) | reference, the 17 dark/night frames | **ours** (village night plate + characters) |
|---|---|---|---|
| mean luminance | **0.46** (0.35-0.57) | 0.28 | **0.21** |
| luminance std (contrast) | 0.20 (0.18-0.23) | — | 0.14 |
| p2 (darkest) | 0.11 (0.07-0.16) | — | 0.03 |
| p98 (brightest) | **0.93** (0.86-0.96) | **0.88** | **0.52** |
| mean saturation | **0.43** (0.35-0.54) | 0.54 | **0.67** |
| p90 saturation | 0.74 (0.65-0.83) | — | 0.93 |
| cool-blue share (hue 180-270°, sat>0.35) | **0.17** (0.02-0.37) | 0.37 | **0.51** |
| warm share (red-orange, sat>0.35) | 0.20 (0.06-0.41) | — | 0.18 |
| edge density (strong gradients) | **0.05** (0.04-0.08) | — | 0.02 |

What this means:
- **Our picture is about half as bright, has no highlights, and is over-saturated and blue.** Even their night frames are brighter than ours (0.28 vs 0.21) and keep near-white highlights (p98 0.88). Faces stay close to white in every lighting, lamps and windows make strong pools of light, and interiors are warm.
- **Night is only about 18% of frames.** The default is bright daylight or a warm-lit interior. Night is a story beat, not the house look.
- **They have more than twice our edge density.** Busy, specific props and signage fill the frame, and ink lines are everywhere.
- Targets for plates **with characters in them**: mean lum 0.40-0.55, p98 ≥ 0.85, mean sat 0.35-0.50, cool share ≤ 0.35, edge density ≥ 0.04. Check these with `references/scripts/frame_stats.py` (see §5).

## 2. Shot sizes and staging (coded by eye from 93 frames, approximate)
- **Medium shots and medium close-ups dominate (about 60%).** The character's head and torso fill much of the frame, and the head is often 20-40% of the frame width.
- **Close-ups of a face or a hand with a prop: about 20%.**
- **Wide or establishing shots with small characters: about 15%.** Effect-only shots with no character (explosion, waves, a flying cart): about 5-10%.
- Almost every frame has a character in it. **One or two characters**, often a two-shot facing each other. Crowds appear as a background layer.
- The camera is at eye level or slightly low, with occasional dutch tilts. Characters are near the centre, and the background is soft (DOF) in close-ups.
- **Ours so far:** wide shots with small characters (about 20% of the frame height). This is the opposite of their dominant framing.

## 3. Story-specific set dressing is a joke device
- Nearly every video has **readable custom signs and props that carry the joke or the premise**. Examples: a banner "FIRST LINE IN GETS IT ALL!", a sign "YEARS AT WAR 100", a shop "Pardons", "PRIZE COUNTER", "LUCKY 7s", a "WINNERS 400,000" board, a sign "DON'T HIT" on the tree that was hit, and labelled boxes and posters.
- Each video has 3-5 distinct places (tent, battlefield, explosion; mine tunnel, office, gold seam; prison cell grey, then pink). Sets are built per story, not reused generically.
- **Implication:** our sets need a cheap way to add custom signage (text on a plank, banner, poster or screen) and hero props per script. A generic village is not enough.

## 4. Style evolution on the channel
- The oldest frames in this window (the teleportation, upload-your-brain and banana-tree videos) use flatter, vector-like 2D backgrounds. The recent ones are 3D toon environments with real lighting, DOF and lots of props, and views rose with them (railroads 30M, storm oil 16M, roller coasters 12M, pink cell 11M, crash instinct 10M).
- The cast style (bean heads, thin limbs, plum ink, lidded eyes) stayed the same, while costumes and props got richer.

## 5. Rules to apply (owners in brackets)
1. **[sets] Expose for daylight first.** Every set needs a bright `day` light whose plates measure mean lum ≥ 0.45 and p98 ≥ 0.9. Night is optional per story, and must keep p98 ≥ 0.85 using lamps, windows and a bright moon.
2. **[sets] Reduce saturation and the blue cast.** Measured sat 0.35-0.50; cool share ≤ 0.35 except in night beats.
3. **[sets] Add per-shot medium and close cameras** (`*_med`, `*_close`) where a 1.75 m character fills 45-65% of the frame height, not only wides.
4. **[sets] Add a signage helper.** `sign(text, style)` renders readable text onto a plank, banner, poster or screen mesh, so scripts can request custom signs.
5. **[scripts] `shots.json` shot mix:** about 60% medium, 20% close, 15% wide, ≤ 10% effect-only. Every video should list 2-4 custom signs or props that carry jokes.
6. **[engine] Character scale** comes from the plate JSON (`px_per_m`), and close shots crop the character at the waist or chest.
7. **[characters] Faces stay near white** under any light: tint the body, not the face highlights (face luma ≥ 0.85).
8. **[all] Measure, don't eyeball.** Run the frame-stats check on every plate and draft frame, and compare with the targets above.
