# How the two leading channels in our genre make their shorts (2026-11-21)

Study of **Ricks Clips** (@RicksClips3000, 202K subscribers, our main style reference) and **Segment Zero** (@segmentzero, 16K subscribers). **Private study.** Never copy their scripts, characters, shots, titles or overlays, and never name them in our videos.

**Sources:**
- each channel's Shorts tab;
- each Short's public page (date, exact views, likes);
- 3 full-res frames per video (`i.ytimg.com/vi/<id>/oar1..3.jpg`, about 25/50/75% of the runtime): 33 Ricks explainers and 34 Segment Zero shorts, 201 frames in all.

YouTube blocks the video, the description and the captions, so motion, audio and runtimes were not measured here (`motion.md` has older motion numbers). Grids: `references/sheets/channels_2026-11/`. Full title lists: `references/titles.md`.

## 1. Output and results
| | Ricks Clips | Segment Zero |
|---|---|---|
| Explainer shorts studied | 33 (2026-07-12 → 11-19) | 34 (2026-10-23 → 11-20) |
| Cadence | **1.8 a week** | **8.2 a week** |
| Median views | **9.5 M** (IQR 3.9-11.6 M, max 35 M) | **0.21 M** (IQR 0.05-1.5 M, max 6.1 M) |
| Median like rate | 2.3% | 1.7% |

- **Quality beats quantity.** Segment Zero copies the look closely (frame stats below are almost identical) and posts 4.5x more often, but its median video gets 45x fewer views.
- Segment Zero's hits are the stories with a sharp paradox ("The Jar That Hid Two Nobel Prizes" 6.1 M, "80 Victories in a Plane Nobody Could See" 3.8 M, "Russia Guarded an Empty Lawn for 60 Years" 3.4 M). Its many weak ones are news, AI scares and plain history (5-50 K).
- **Ricks Clips' views rose with production quality.** Its July-August shorts were flat 2D, pixel or comic experiments (0.1-4 M). From September every short has full 3D sets and costumed bean-heads, at about 10 M each.

## 2. Topics and titles
- **Ricks:** the hidden mechanism of an everyday or historical system, often about money, rules or the brain:
  - gambling and lotteries (cashiers win the lottery, the Japanese pachinko "window" loophole, slot machines);
  - prisons (the pink cell);
  - railways (expansion gaps), sailors' storm oil, mine salting, the grave bell, random numbers, "your brain's idea zone".
- **Segment Zero:** war history, spies and escapes, AI scares, odd history (a pope who put a corpse on trial).
- **Title forms** (median views, Ricks):
  - "Why …" 7 of 33 (9.9 M);
  - "The … That/Who …" 5 (10.9 M);
  - "How …" 4 (6.4 M);
  - questions are rare.
  - Titles are 4-8 words, never clickbait caps, and often a paradox or a loophole ("Why Perfect Railroads Don't Work", "The Burglar Who Only Moved Furniture").
- **What this means for us:** our "Why Your Bike Steers Backwards First" fits the Ricks pattern exactly: an everyday mechanism, a paradox title and a "Why…" form. Keep choosing hidden mechanisms with a paradox. Avoid news, AI scares and war-heavy topics, which are Segment Zero's weak spots.

## 3. Picture: measured (`frame_stats.py`, captions masked)
| median (IQR) | Ricks | Segment Zero | our draft v4 |
|---|---|---|---|
| luminance | 0.46 (0.35-0.58) | 0.45 (0.37-0.57) | about 0.50 |
| p98 | 0.93 | 0.93 | 0.93-0.97 |
| saturation | 0.43 (0.35-0.54) | 0.46 (0.35-0.55) | 0.35-0.45 |
| cool share | 0.15 | 0.13 | 0.0-0.3 |
| edge density | 0.05 (0.04-0.08) | 0.05 (0.04-0.07) | 0.03-0.06 |

Our numbers are now in range. **The gap is no longer exposure: it is staging, set detail, lighting design and character integration** (below).

## 4. Picture: what they do (seen in the frames)
1. **Characters live in the set.** They:
   - sit on chairs, stand behind counters and tables, lean out of cabs and cockpits;
   - are cut by door frames;
   - stand in crowds of 3-6 that overlap in depth.

   A near character is often cut by the frame edge (a huge head or shoulder in the foreground), with the actor behind. Scene light reaches the characters: rim light from a lamp, warm or cool spill. This is probably 2D characters on cards inside the 3D scene (or Grease Pencil), not composited on top.
2. **Lighting is designed for every shot:**
   - one bare bulb or spotlight over a dark room;
   - volumetric beams;
   - night blue with warm practicals (shop windows, lamps);
   - sunsets with long shadows;
   - neon in gambling scenes.

   Daylight is common, but every interior has a motivated light.
3. **Sets are dense and specific to the story:** throne rooms, castle walls, a pachinko alley, prize counters, a ship's deck, a train station. Joke signage is large and readable ("FIRST LINE IN GETS IT ALL!", "PRIZE COUNTER", shop signs, a "400,000" counter).
4. **A visual metaphor set piece in most videos:**
   - a transparent body with a glowing brain;
   - a depth gauge underwater with "???";
   - a giant golden dragon head;
   - a tidal wave behind a ship;
   - in Segment Zero, a sea of identical faces and a giant Tetris wall.
5. **Varied cameras:**
   - extreme close-ups of faces that fill the frame;
   - Dutch (tilted) angles;
   - low angles on authority figures;
   - POV inserts (a phone screen, a document, an inbox);
   - prop close-ups (medals in a box);
   - wide establishing shots used sparingly.
6. **Costumes carry the period or the job** (samurai, knight, police, captain, chef, pilot), with expressive faces: big grins, gritted teeth, sweat drops, tears.
7. **Captions** (both channels):
   - 1-2 words, **sentence case** (not caps), white bold rounded sans with a thin black outline;
   - centred at about 68-72% of the height, with no keyword colour.

   Segment Zero adds a faint watermark, plus sometimes a top progress map or game-like UI overlays.

## 5. How they are probably made (inference, not confirmed)
- 3D sets in Blender or a similar tool, from stylised assets with toon shading, ink outlines, DOF and volumetrics.
- 2D bean-head characters with swappable faces, hats and costumes, placed in the 3D scene so they are occluded, lit and depth-blurred.
- Captions and the edit in a video editor or a captioning tool.
- Ricks: about 2 videos a week, with high craft per video (likely a small team or a strong template library).
- Segment Zero: 8 a week, a templated, high-volume pipeline.

## 6. What we change (in priority order)
1. **Characters inside the set** (engine): depth-tested compositing with our depth maps, characters sitting or leaning on props, foreground characters cut by the frame, and scene light on the characters (tint plus rim). This is the biggest visible gap. BACKLOG engine, now P1.
2. **Shot grammar** (scripts): every video needs at least:
   - one extreme close-up;
   - one POV or prop insert;
   - one Dutch or low angle;
   - one crowd or depth-layered shot;
   - one **visual metaphor set piece** for the mechanism.

   `tools/preflight.py` can count the shot types.
3. **Lighting per shot** (sets): one motivated practical per interior, night blue with warm practicals, beams; no flat interiors.
4. **Dense, story-specific sets** with big readable joke signs. That means new sets per topic, not one reused set.
5. **Captions:** both leaders use sentence case without keyword colour. Ours are caps with yellow keywords. This is a Director decision; test it on the next video.
6. **Topics and titles:** hidden mechanisms with a paradox, "Why…" or "The … That …", 4-8 words. Check `references/titles.md` for overlap.
7. **Cadence:** aim for quality over volume (about 1-2 a week), as Ricks does.
