# Zebra stripes: "Why Do Zebras Have Stripes?" (flat2d, claude/area-zebra-stripes, 2026-11-24)

Video 9. Same look, tone and pipeline as videos 3-8: white stickmen with a black outline (the 2016 scientists, a
farmer), rich flat 2D, serious mystery, no comedy, "sentence" captions, continuous motion. Voice and mix: the
Producer's `audio/zebra-stripes/` (Kokoro `am_adam` 1.16), unchanged: 1951 frames = 65.033 s. Built on the Blood
Falls formula: ONE hero image (a brown horse in a fitted zebra-striped coat, head bare, in a green English field in
2016, horse flies circling it with dotted trails), the black-and-white stripe motif against fresh green / warm gold,
the scientists reacting in most shots, big titles, the flip (NOT HIDING THE ZEBRA. / HIDING THE LANDING SPOT.), and a
loop back to the 2016 field. **Status: fix pass done and the 1080 final rendered:
`videos/zebra-stripes/zebra_stripes_final_1080x1920.mp4` (see "Fix pass + final"). Nothing is published.**

## Files
| file | what |
|---|---|
| `tests/preview_full_540.mp4` | 540x960 30 fps preview with `mix.wav` (1951 frames) |
| `tests/sheet_2s.jpg` | 2 s contact sheet of the preview |
| `tests/stills_r1/`, `tests/stills_r2/`, `tests/stills_r3/` | review stills per round (one per shot, 540x960, captions on) + `sheet.png`. r3 is the last reviewed round, re-rendered with the final code after the small post-review fixes below |
| `tests/review_brief.md` | what each reviewer got: every still's voice-over line and planned picture |
| `thumbnail.png` | `tools/thumbnail.py` on a caption-free frame (`flat2d/zebra_stripes_thumb.py`): the striped-coat horse big, head bare and in frame, flies circling with dotted trails, one fly bonking off the coat; IT'S NOT (white) / CAMOUFLAGE (yellow) |
| `flat2d/animals.py` | **the animal kit (new)**. One side-view quadruped renderer for `zebra`, `horse` (bay), `coat` (bay horse in a fitted zebra-striped rug: torso, neck and hood covered, head and lower legs bare, black binding at the hem), `lion` (stalking crouch, shaggy mane) and `cow` (Japanese Black; `painted=True` gives white brushed stripes). Shapes are built in unit space (1 unit = withers height) and painted through a LABEL image (torso, neck, head, near and far legs, ears, mane, tail, hooves), so each part gets its own colour and pattern. Zebra stripes follow the body: vertical on the barrel, sweeping round the haunch to horizontal, rings on the legs, across the neck into an upright striped mane, fine stripes across the face, a black muzzle, ears with black tips. The render adds one ink outline round the silhouette, inner lines where a near leg crosses the body, a far-leg group drawn darker, a form shadow under the barrel and a rim light inside the ink. Poses cover neck, head, ear flick, tail swing, breath, walk legs and blink; layers are cached by pose. `fly_layer`/`put_fly` draw the HORSE FLY side on: a huge green compound eye with violet zigzag bands and facets, a humped striped thorax with bristles, a banded abdomen, a blade mouth and veined wings (`blur` beating / `fold` / `up`); legs go from tucked (fast flight) to stretched (landing) |
| `flat2d/savanna.py` | **the world kit (new)**: `english_field` (summer sky + cumulus, patchwork far fields stitched with hedgerows, a hedgerow with oaks, the pasture, a post-and-rail fence, buttercups and daisies; `kind='evening'` for warm low light), `field_front`, `savanna` (sunset / noon / haze skies, a big low sun with rays, far hills and a kopje, acacias at three depths, golden plains, haze), `oak`, `acacia`, `hedgerow`, `patchwork`, `fence`, `flowers`, plus props `tripod_camera`, `clipboard` (tally marks), `thermometer`, `africa_pts`/`madagascar_pts`/`lonlat` (the map), `dots_trail` (the flight trail) |
| `flat2d/zebra_stripes.py` | the shots `s01`-`s17` (+ splits), `SHOT_LIST`, `END`, `STILL_AT`, `HIDE_UI`; scientists, flies (`fly_at` with a dotted trail, `orbit`, `swarm`, `bonk_star`), the hide-wrapped barrels, the stage diagram, the fly's-eye hex view, the Japan farm, the striped stairs |
| `flat2d/zebra_stripes_thumb.py` | the thumbnail frame |

## Build
```
.venv/bin/python flat2d/render.py audio/zebra-stripes/words.json OUT.mp4 --film zebra_stripes --size 540x960     # 1951 frames, ~30 min on 4 cores
.venv/bin/python flat2d/stills.py audio/zebra-stripes/words.json OUTDIR --film zebra_stripes                     # review stills
.venv/bin/python flat2d/motion_qa.py OUT.mp4.frames <cut times>                                                  # see Motion QA
ffmpeg -i OUT.mp4 -i audio/zebra-stripes/mix.wav -map 0:v -map 1:a -c:v copy -c:a aac -b:a 192k -shortest videos/zebra-stripes/tests/preview_full_540.mp4
.venv/bin/python flat2d/zebra_stripes_thumb.py frame.png
.venv/bin/python tools/thumbnail.py frame.png videos/zebra-stripes/thumbnail.png --line "IT'S NOT|white|150" --line "CAMOUFLAGE|yellow|170" --top 0.08
```
Final (after the Producer's pass, not done here): `render.py ... --size 1080x1920`, mux `mix.wav`, then `tools/add_cover.sh <video> videos/zebra-stripes/thumbnail.png <master>`. Shot splits (s01b, s04b, s05b, s07b, s14b) are inside lines only, so the Producer's s01-s17 `sfx.json` anchors still hold.

## Shot list (timed to the real voice; a shot starts 0.1 s before its first word)
| shot | time s | picture |
|---|---|---|
| s01 | 0.00-4.71 | **frame 0 = the hook**: the brown horse in the zebra-striped coat (head bare) in the green English field, 8 horse flies circling it with dotted trails, two scientists (clipboard tally, tripod video camera) in the foreground; 2016 + ENGLAND (re-pops on "2016"); ZEBRA-STRIPED COAT on "coats" |
| s01b | 4.71-5.98 | close on the coat: four big flies circling with trails; the scientist with the clipboard watching; WATCH THE FLIES |
| s02 | 5.98-8.86 | savanna sunset, a walking herd, two researchers shrug in turn with ? marks; WHY THE / STRIPES? |
| s03 | 8.86-11.74 | a zebra in tall golden grass; CAMOUFLAGE? on "camouflage", HIDE FROM LIONS; a lion's head rises out of the grass on "lions" |
| s04 | 11.74-14.82 | noon, open short grass: a crouching lion stares at a grazing zebra in plain view; a dotted sight line + ring, SPOTTED!; OPEN GRASSLAND; X beside CAMOUFLAGE on "easily" |
| s04b | 14.82-17.44 | hazy wide: lion bottom-left, the zebra far off, a 50+ METRES measure; LION'S VIEW inset hanging off the lion's eye where the zebra blurs to a grey shape on "stripes" (NO STRIPES) |
| s05 | 17.44-18.98 | harsh noon sun, heat shimmer, a zebra and a rising thermometer; COOLING? |
| s05b | 18.98-21.64 | a dusty test yard: a barrel wrapped in zebra hide and one in grey hide (hide folded over the rim, roped), thermometers rising together; JUST AS HOT, X beside COOLING? on "hot"; a scientist points |
| s06 | 21.64-25.51 | CLUE 1: map of Africa on a board; zebras pop in (bold-striped in East Africa, paler stripes further south); the red biting-fly zone spreads on "biting flies" with tiny flies; BOLDEST STRIPES with a pointer; the scientist points |
| s07 | 25.51-28.20 | CLUE 2: the HORSE FLY big, landing on a patch of hide (green banded eyes, folded veined wings), sun shafts and motes; SPREADS DEADLY DISEASES |
| s07b | 28.20-30.68 | macro: zebra skin cross-section with short black/white hair; the fly stands on the hair tips; SHORT HAIR bracket; its blade mouth reaches the skin on "bite" (BITE, red glow) |
| s08 | 30.68-35.52 | CLUE 3: the coated horse; flies veer around the coat without landing; on "except" flies land one by one on the bare head; white-red ring on "bare" (BARE HEAD: BITTEN); COAT: FEWER LANDINGS; the clipboard tally counts |
| s09 | 35.52-37.26 | the riddle: a fly hovering over the striped coat in a glow, a big yellow ?, the scientist thinking |
| s10 | 37.26-41.33 | the mechanism diagram (navy stage, brown hide strip): the fly's trail, one dot per 0.1 s: wide dots (FAST) close up (SLOWS DOWN), legs come out, LANDS; a speed bar drains |
| s11 | 41.33-43.67 | evening light, plain bay horse: the fly comes in, its dots tighten (BRAKES), it touches down legs-first on the withers; green check |
| s12 | 43.67-47.45 | same framing, the striped coat: the dots stay wide (NO BRAKING), the fly BONKs off the coat on "bumps" and tumbles away (shake); a second fly zooms past on "zooms"; X |
| s13 | 47.45-49.94 | fly's-eye view: hexagonal facets each showing the stripes, jittering out of register as the scramble grows on "scramble"; WHERE IS / THE SURFACE? |
| s14 | 49.94-52.43 | Japan: mountains, a barn with a dark curved roof, a fenced paddock; a black cow; the FARMER paints white stripes on it from the rump forward (long brush, drips, bucket); JAPAN, PAINTED STRIPES |
| s14b | 52.43-53.63 | plain black cow swarmed by flies (PLAIN: MANY BITES) over the striped cow with two (STRIPED: FAR FEWER) |
| s15 | 53.63-56.90 | a wide staircase from the top landing: the left half plain (every step edge clear), the right half painted with bold diagonal stripes on "painted ... stripes" so its edges vanish; a person on the striped side hovers a foot, worried; WHERE'S THE STEP?, ? |
| s16 | 56.90-60.28 | the flip, biggest title over a big zebra at sunset while flies bonk off it: NOT HIDING / THE ZEBRA. then HIDING THE / LANDING SPOT. (yellow), each line on its word |
| s17 | 60.28-65.03 | back in the 2016 field, zoomed in: flies dive at the coat, fail to brake, bounce off or overshoot (THE FLIES KEPT MISSING); the camera pulls back, the circling flies fade in and the title returns; **the last frame is s01's frame 0** (loop) |

## Review (stills only; one fresh sonnet reviewer per round, each still with its voice-over line and planned picture (`tests/review_brief.md`), the in-order sheet and the Wind Cave sheet as the reference)
| Round | richness / readability / composition | overall | script contradiction | 3+ run | result |
|---|---|---|---|---|---|
| 1 | 6.5 / 6.5 / 6 | 6.3 | none (near: s05b barrel read as an empty striped can) | s02-s05b sunset run (6), green-field shots bunched | FAIL |
| 2 | 6.5 / 7 / 6.5 | 6.7 | none (risk: s17 flies looked like landing) | savanna s02-s05b, field s08-s12 (mild) | FAIL |
| 3 | 7 / 7.5 / 6.5 | 7.0 | none (mild: s04b inset still showed faint stripes) | s02-s05 savanna palette | FAIL (< 8) |

Fixes per round:
- R1: palette variety (s04 noon, s04b haze, s05 harsh noon, s05b a dusty test yard, s11/s12 evening); barrels redrawn as hide-wrapped (folded rim, ropes), scientist calm and off the barrels; X marks beside the chips, not over the words; s08 chips staggered, head in frame; s06 bigger map zebras, the southern ones with pale brownish stripes; s09 bigger fly with a glow; s14 shows painting in progress (long brush, drips, bucket); s14b bigger flies; s15 rebuilt as plain vs painted halves; light shafts + motes in s07/s07b, a pulse in s13.
- R2: chips moved out of the caption band in s10-s12; s15 painted half keeps the steps under shallow diagonal stripes (faint edge ghosts); s14 the whole cow incl. head; s17 flies visibly miss (dive, bounce, overshoot) and the circling swarm only fades in for the loop; s09 pulled back to show the horse; s04b bigger lion and zebra; s08 bigger flies on the head, white-red ring; s06 BOLDEST STRIPES off the map with a pointer; s10 motes.
- After R3 (not re-reviewed, under the 3-round cap): the s04b inset blurs fully grey and is smaller, the 50+ METRES chip moved off the lion; s08 head flies spread out; a sky gap under the hedgerow (it read as a lake) and holes in the far patchwork fields filled in every field shot.

**The gate (overall >= 8) was not reached in the 3 allowed rounds: 6.3 → 6.7 → 7.0.** Open notes from R3, for the Producer/Director:
- the savanna block s02-s05b is still a long gold run, even with the noon/haze/yard changes (one setting by design: the wrong answers);
- the s14 cow is stiff and blocky next to the horses and zebras (the shared quadruped rig: a cow-specific head/body pass would help);
- s10 (diagram stage) and s15 (stairwell) are the plainest sets; s14/s14b have empty sky;
- the lion in s04/s04b reads a little tube-like;
- s01's caption sits on the horse's belly (the band picker's least-busy choice).

## Motion QA
`motion_qa.py` on the 1951 preview frames, with the 21 cut times and `--impacts 45.71` (the s12 BONK: shake + star, designed) → **PASS**: no pops, longest frozen span 1 frame (0.03 s), median frame diff 2.15.
Fixed on the way: an s08 ring radius went negative for a few frames (render crash); s17's zoom jumped 1.04 → 1.0 near its end (a full-frame pop at 64.5 s); s17's bonked flies vanished at the end of their window (now fade out).

## Loop
Frame 1950 (the last) = frame 0: mean abs difference **0.0** (s17's last frame calls `s01_frame(0, 0)` with the idle clock `anim.NOW` reset to 0, so the stickmen's secondary motion matches too). Note: in the parallel render the two frames differed by 0.13 (cached cards/layers built from neighbouring pose values in each worker), so frames 0 and 1950 were re-rendered in one process; for the 1080 final do the same (or render those two frames last in one process).

## Fix pass + final (claude/fix-zebra-stripes, 2026-11-24)
One pass on the Producer's review of `tests/sheet_2s.jpg` + `stills_r3`. Audio, timing and shot ids untouched; the
savanna palette (s02-s05b) untouched. New review stills: `tests/stills_r4/` (540, captions on, checked by eye, no
reviewer subagents).
- **Cow (s14, s14b)** — `animals._cow` redrawn as a Japanese Black: deep rounded barrel with a sagging belly that
  tucks up at the flank, a withers hump, the hip bone (hook) and pin bone on a straight back, a short thick neck with
  a dewlap to the brisket, a broad short head carried low, small cream horns with dark tips curving up and forward,
  ears sticking out sideways (pink-grey inside, hair fringe), a pink-grey muzzle with a nostril, a high tail set with a
  tassel, knees / hocks (a real hock angle) tapering to cloven hooves (cleft + coronet). A black coat shows form by
  sheen: soft light lobes on the shoulder, back, hook, thigh and neck, lighter strokes for the shoulder blade, elbow,
  flank fold, hook bone, dewlap fold and faint ribs, plus the rim light and form shadow. The painted stripes have
  dry-brush streaks; the leg tops inside the body are painted as body (no boxy leg roots).
- **s14** — the farmer stands BESIDE the cow (right of the rump, nothing in front of the cow), both hands on a long
  brush whose head rides the wet stroke on the flank (well away from his face). Painting goes stripe by stripe from the
  rump forward (`_cow_reveal`: finished columns behind, the current column painted top-down, glistening, with drips),
  rump + hind leg already striped at the first frame, mid-barrel by the end. New Japan set `japan_farm`: morning sky,
  two soft cloud bands across layered blue-green cedar-covered ridges, rice terraces on the right, a tree line, a
  white-walled farmhouse with a dark curved roof, the fenced paddock with flowers. s14b uses it too (higher horizon).
- **Lion (s03, s04, s04b)** — `animals._lion` redrawn as a stalking side view: shoulder blades up as the high point,
  the back dipping to the hips, the big head low and forward, a shaggy mane of rounded locks (`_shag`) drawn over the
  back of the head so it frames the face and hangs long under the chest (golden near the face, dark brown outside,
  strands flowing back from the face), muscled forelegs with the far one lifted mid-stalk, elbow/thigh/belly lines, an
  amber almond eye with a hard brow, a tear line, nose pad, chin, whisker spots, a long low tail with a dark tuft.
  Sight line + ring + SPOTTED unchanged; the lion moved right (s04) so more of it shows; the 50+ METRES measure now
  starts at the lion's nose.
- **s15** — rebuilt as a one-point view looking down a wide staircase: a back wall with a window (light patch + rays on
  the landing), plaster walls, wooden handrails with brackets on both sides, a brass wall lamp with a glow, a wooden
  landing, steps widening toward us (riser shade, lit tread, nosing highlight, crisp edge line, shadow under each
  nosing, stone speckle). The person stands fully visible on the landing at the edge of the painted half, one foot
  lifted and hovering (its shadow on the first step), arms out, worried. The right half is wiped white with bold
  diagonal stripes that hide every edge.
- **s01 / s01b / s17** — flies 1.5x bigger (s01 swarm, s17 divers) with bigger trail dots; the horse moved up
  (HGY 1450 → 1390), the scientists down (+60 px); captions fixed on the grass under the horse, above the scientists
  (`BAND_FIX` in the film, read by `render.Film.band`). s01b pulled back so the horse's legs and the grass show (the
  caption sits under it). s17 zooms about the hoof line so the horse never drops into the caption. The last frame of
  s17 is still `s01_frame(0, 0)`.
- **s10** — depth: a soft spotlight cone onto the landing spot and a light pool, the hide is a cached hair-textured
  strip (gradient + 2,600 hair strokes + a lit bevel), the fly is bigger (220 → 300 px) and casts a shadow that
  sharpens as it comes down; grid kept, chips re-spaced.
- `thumbnail.png`: rebuilt with the same lines, came out pixel-identical (its frame doesn't use the s01 layout), kept.

**Preview**: `tests/preview_full_540.mp4` (fix-pass build, 65.03 s, `mix.wav`) + `tests/sheet_2s.jpg`. Motion QA with the
21 cut times and `--impacts 45.71` → **PASS** (no pops, longest frozen span 1 frame). Loop: frames 0 and 1950
re-rendered in one process after the parallel render → mean abs difference **0.0** (540 and 1080).

**Final**: `videos/zebra-stripes/zebra_stripes_final_1080x1920.mp4`, 1080x1920 30 fps, 2-pass libx264 High 5200k,
AAC 192k, +faststart, **44.2 MB, 65.15 s** (0.1 s cover from `thumbnail.png` + 1951 frames, audio delayed 0.1 s by
`tools/add_cover.sh`). Built: `render.py audio/zebra-stripes/words.json OUT --film zebra_stripes --size 1080x1920` →
re-render frames 0 + 1950 in one process (single-process loop fix) → re-encode the frames (CRF 16) → mux `mix.wav` →
`add_cover.sh` → 2-pass encode. Frame 0 (after the cover) and s14 checked by eye. Not published.

## Posted 2026-11-24 (Buffer, media file `zebra_stripes_1080x1920.mp4`)
- TikTok 6b057c65e2bac802e9a1c1f0 https://tiktok.com/@somecrazythingzz/video/7711706838231813397
- Facebook 6b057c78e2bac802e9a1d965 https://facebook.com/1395801306957363_122108703447549918
- YouTube: shareNow 6b057c76bc0aa082945408d8 failed (daily limit); scheduled in Buffer as 6b057c8ee2bac802e9a1e84f for 2026-11-25 04:30 UTC (11:30 Vietnam).
