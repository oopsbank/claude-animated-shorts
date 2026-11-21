# Replication playbook: how to get the Ricks Clips / Segment Zero look in our stack (2026-11-21)

**Goal:** match their *look and craft*, with our own stories, characters and shots. Never trace or copy their characters, sets, shots, titles or overlays.

**Builds on:**
- `channels_2026-11.md`: output, topics, titles, what they show;
- the older per-topic studies (`characters`, `lighting`, `outlines`, `textures`, `depth`, `grade`, `motion`). Those were written for a three.js stack; their *numbers* still hold, and this file maps them to our Blender + PIL engine.

**Measured with** `references/scripts/style_metrics.py` and `frame_stats.py` on 99 Ricks frames, 102 Segment Zero frames and 13 of our draft v4 frames.

## 1. Measured gaps (beyond `channels_2026-11.md` §3)
| Metric | Ricks | Segment Zero | Ours (v4) | Verdict |
|---|---|---|---|---|
| **Vignette** (corner/centre luminance) | **0.78** | 0.84 | **0.99** | We have none. Cheapest visible fix. |
| **Warm/cool split** (R-B of the brightest 25% vs the darkest 25%) | highlights **+0.08**, shadows +0.02 | +0.20 / +0.03 | highlights **+0.04**, shadows **+0.12** | Ours is inverted: our shadows are warmer than our lights. Theirs: warm lights over neutral or cool shadows. |
| Background blur (mid/top sharpness ratio) | 2.0; 68% of frames have a clearly blurred background | 1.6; 56% | 4.1; 92% | Fine, maybe a touch strong. Keep DOF, and let some wides stay sharp. |
| Ink colour (darkest pixels) | (40, 26, 34), plum | (30, 25, 26) | (32, 24, 33) | Matches. |
| Captions | baseline 0.716 H, about 0.22 W wide, rounded bold sans, thin outline | 0.698 H, 0.25 W | now: Poppins Bold 0.037 H, baseline 0.70 H, outline 10% | Matched on 2026-11-21 (style "sentence"). |

## 2. What the zoomed frames show (technique)
- **Character line:** a brush-like ink with slight width wobble and rounded ends. Faces are simple strokes: closed-eye arcs for joy, toothy grins, lidded deadpan. Ours is cleaner, more vector-like and more even.
- **Character shading:** white heads with a faint grey edge falloff (the crescent), no hard cel band. Costumes carry 2-3 flat tones and small gold or colour details.
- **Integration:** characters stand *in* doorways (the door leaf in front), behind counters and in chairs, and overlap each other in depth. A foreground head or shoulder is often cut by the frame. Lamps light the faces (warm rim in night scenes).
- **Sets:** dense, clean, story-specific props with ink outlines. Readable product labels and signs ("CHOCO", "COOKIES", "PRIZE COUNTER"). Rich patterned surfaces (tufted cushions, studs, tiles, posters). Our plates are emptier, with plainer walls.
- **Colour:** bright saturated primaries on props against softer walls; warm practicals; night scenes are deep blue, never black.

## 3. Every way to close the gap, in our stack
Ordered by impact per unit of cost. "Area" is who does it.

### A. Grade (engine, cost: an hour; affects every frame)
1. **Vignette** to a corner/centre ratio of about 0.80: a radial multiply in `engine/grade.py`, applied after the per-shot grade and before captions.
2. **Split toning:** warm the highlights (R-B ≈ +0.08) and pull the shadows neutral or slightly cool (R-B ≈ 0 to +0.02). Day: warm highlights, cool shadows. Night: blue shadows, warm practicals.
3. **Warm-only bloom on practicals** (lamps, screens, neon), never on faces. `LESSONS` › Sets already has the rule.

### B. Characters inside the set (engine, cost: 1-2 days; the biggest gap)
4. **Depth-tested compositing** from the depth maps we already render: the character's depth comes from its ground point, and nearer plate pixels draw over it (door leaves, counters, posts, cab frames).
5. **Light on the characters:** multiply by the plate `tint`, add a rim from `light_dir` (warm at night and golden), and a soft contact shadow.
6. **DOF on far characters** from the plate depth, so crowds read in layers.
7. **Foreground cut characters:** a near character at 1.6-2.2x scale cut by the frame edge (we have `_near` for OTS). Allow it in any shot.

### C. Character drawing (wardrobe, cost: 1-2 days)
8. **Brush ink:** variable stroke width with low-frequency noise (±12%), rounded caps, a slight wobble; inner lines (mouth, brows) at 0.6x.
9. **Face library additions:** closed-eye joy arcs, a toothy grin, crying, a gritted "GRR", and big shocked pupils. Expressions must read at 8% of the frame height.
10. **Costume library per period or job** (samurai armour, knight, police, captain, chef, pilot, worker), 2-3 flat tones plus small detail, and **crowds** by seed variation.

### D. Sets (sets, cost: per set; plates are stills, so quality is affordable)
11. **Story-specific dense sets** (no reuse across topics). Each needs:
    - 3-5 hero props with labels (`common.sign()`);
    - at least one patterned surface (tiles, tufts, posters, shelves).
12. **Procedural material library** in `common.py`: tufted cushion, tiled floor, brick, planks, wallpaper and shelf stock. Bake to textures so every set uses them.
13. **Lighting design per cam:**
    - a visible practical (bulb, lamp, screen) per interior;
    - volumetric beams (Cycles volume scatter is fine for stills);
    - night = deep blue ambient with warm windows;
    - golden = a backlit sun with long shadows.
14. **Depth maps and occluder props** for every cam (`--depth`); put a near prop in front of the actor in about 1/3 of shots.

### E. Camera and staging (scripts + engine, cost: low)
15. Per video, at least: one extreme close-up (a face filling 50%+ of the frame), one POV or prop insert, one Dutch angle (`camera.roll` 6-10°), one low angle, one crowd, and **one visual metaphor set piece** for the mechanism. See BACKLOG scripts P1 and the preflight count.
16. **POV inserts drawn in PIL:** a phone screen, an inbox, a document, a scoreboard, in our palette.
17. Motion grammar from `motion.md`: push in on every hold, ease every glide, carry blur on whips, and add smear frames on fast moves.

### F. Production options (bigger choices)
| Option | What it gives | Cost and limits here | Verdict |
|---|---|---|---|
| **Hybrid 2.5D (today)** + A-E | 80-90% of their look | CPU only; already built | **Do this.** |
| Characters as textured planes inside Blender (true occlusion, light, DOF) | 100% integration | Cycles CPU takes 1-3 min a frame, so about 60 h a video. Too slow without a GPU. | Only with a GPU. |
| Blender EEVEE (real-time) on the Director's own GPU computer (Remote Control) | Full 3D render at about 1-3 s a frame | Needs the Director's machine to be on and attached; the pipeline would move there | A good future option if they have a GPU. |
| Grease Pencil 2D characters in Blender | Hand-drawn look in 3D space | Same render cost; the cast would be redrawn | No (cost). |
| AI image generation for backgrounds | Fast detailed backgrounds | Not available here; style drift and gibberish text (Segment Zero shows signs of this); no control of geometry and depth | No. |
| Paid stylised asset packs | Denser sets faster | Needs the Director's budget and licence check | Ask if wanted. |

## 3b. Props and sets up close (720p crops from the four uploaded videos, 2026-11-21)
What their 3D objects look like, and how that differs from our flat low-poly with Freestyle ink:
- **Stylised PBR, not flat toon.** Smooth rounded shapes with **bevelled edges that catch a highlight**. Glossy painted metal (the locomotive's teal boiler), **gold metallic trim**, varnished wood, glass lanterns with warm emission and glow. There are soft gradients across every surface, not flat fills.
- **Little or no ink on 3D props.** The locomotive, the bowler hat, the coil and the cabin read by light and shape. The ink belongs to the 2D characters. (The older `outlines.md` found thin lines on some sets; keep any line subtle.)
- **Geometric detail where the story looks:** a rope wound around a tube, rivets, planks, gold bands, hay. Fur and grass are particles (a hay bale, a meadow).
- **Soft contact shadows and ambient occlusion** in every crevice; warm key with cool fill; **DOF** behind.

**Recipe for our Blender stack:** Cycles stills, so the cost is fine.
1. Principled BSDF, roughness 0.3-0.5 for paint and wood; metallic 1 for gold trim (#d9a441); clearcoat 0.3-0.5 for a toy-like gloss.
2. A **Bevel node** in the normal (radius 1-3 cm), or modifier bevels, so every edge gets a highlight.
3. A soft key light (a large area light or the sun with angle 5-10°), a sky fill, AO from Cycles; emission ×3 on lamps plus our warm bloom.
4. Turn Freestyle **off** for props, or keep it very thin (≤ 1 px, 50% alpha). Keep it only for silhouettes far away.
5. Hair-particle grass and hay where needed; procedural rope, rivets and planks for hero props.
6. Check: a look test of one hero prop next to a reference crop, scored by the panel (≥ 9) before a whole set is built.

## 4. Plan (BACKLOG)
- **P1:**
  - vignette and split toning in the grade (A1-A2);
  - depth-tested compositing plus scene light on characters (B4-B5);
  - shot grammar in scripts and preflight (E15).
- **P2:**
  - brush ink and the face library (C8-C9);
  - the procedural material library and lighting design per cam (D12-D13);
  - DOF on far characters (B6);
  - POV inserts (E16).
- **P3:**
  - costumes and crowds (C10);
  - the GPU option (F), if the Director has one.
