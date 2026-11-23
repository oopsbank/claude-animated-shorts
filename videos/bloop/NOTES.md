# The Bloop: "The Sound From the Deep" (flat2d, claude/area-bloop → claude/area-bloop-v2, 2026-11-23)

Video 5. Same look, tone and pipeline as videos 3-4: white stickmen with a black outline, rich flat 2D, serious mystery, no comedy, "sentence" captions, continuous motion. Status: **v2 (the Producer's pass: s08→s09 made one continuous transformation; s02 lower left filled; s12 inset enlarged) rendered; 1080x1920 posting copy committed.** Not published.

## Files
| file | what |
|---|---|
| `bloop_final_1080x1920.mp4` | **the posting copy** (committed, under 45 MB): 1080x1920, captions, the mix, 0.1 s cover in front. See "Final cut" |
| `tests/preview_full_540.mp4` | 540x960 full-length preview with the mix (no cover), 1962 frames = 65.40 s (v2) |
| `tests/sheet_2s.jpg` | 2 s contact sheet of the preview |
| `tests/stills_r1/`, `tests/stills_r2/`, `tests/stills_r3/` (v2: changed shots + `sequence.png`) | the review stills (one per shot, 540x960, with captions) and `sheet.png` |
| `thumbnail.png` | house-style thumbnail: caption-free s02 frame (the SCIENTIST startled in his headphones, the VOLUME bar where BLOOP tops ANIMALS), headline THE OCEAN MADE / A SOUND NO / ANIMAL / COULD MAKE |
| `flat2d/bloop.py` | the shots `s01`-`s14b`, `SHOT_LIST`, `END`, `BAND_AT`, `STILL_AT`, `HIDE_UI` (thumbnail frames) |
| `flat2d/ocean.py` | new kit layers: ocean cross-section with depth bands, depth ruler, moored hydrophone station (glows when it hears), glowing sound rings / pulse trains, waveform trace, blue whale, ice shelf + splash, research ship with A-frame, glass + ice cube, headphones, the vague sea shadow (speculation only) |
| `audio/bloop/music.json`, `sfx.json`, `mix.wav`, `cues.md`, `length.json` | soundtrack plan, the mix, the cue sheet |
| `scripts/bloop/shots.json` | minimal shot list for `build_mix.py`, exported from `SHOT_LIST` |

## Build
```
.venv/bin/python audio/build_mix.py audio/bloop --shots scripts/bloop/shots.json --frames 1962
.venv/bin/python flat2d/render.py audio/bloop/words.json OUT.mp4 --film bloop --size 540x960     # 1962 frames
.venv/bin/python flat2d/stills.py audio/bloop/words.json OUTDIR --film bloop                     # review stills
.venv/bin/python flat2d/motion_qa.py OUT.mp4.frames <cut times> --impacts <designed beats>
ffmpeg -i OUT.mp4 -i audio/bloop/mix.wav -map 0:v -map 1:a -c:v copy -c:a aac -b:a 192k -shortest videos/bloop/tests/preview_full_540.mp4
```
`build_mix.py` needs scipy (installed into `.venv` with `uv pip install --python .venv/bin/python scipy`).
Final (after the Producer's pass): `render.py ... --film bloop --size 1080x1920`, mux `mix.wav`, `tools/add_cover.sh <video> videos/bloop/thumbnail.png <master>`, then the 2-pass posting encode as in `videos/tunguska/NOTES.md`. 1962 frames = 65.40 s; with the 0.1 s cover **65.5 s** (62-66 s rule). The voice's last word ends at 64.64 s.

## Shot list (timed to the real voice; a shot starts 0.1 s before its first word)
| shot | time s | line | picture |
|---|---|---|---|
| s01 | 0.00-6.03 | 1 | dark ocean cross-section at night, depth ruler; a red pulse train is already spreading from the deep at frame 0; two moored stations flash as the fronts reach them (on "heard", "microphones"); 1997 · PACIFIC OCEAN; A SOUND / FROM THE DEEP slams on "sound"; a 4,800 KM APART span on "five thousand" |
| s02 | 6.03-10.32 | 2 | the listening room: rack LEDs, a tall display; a reel-to-reel recorder (turning reels, blinking REC) lower left; the SCIENTIST (navy sweater, red over-ear headphones, cable to the console) jolts back on "rose"; the PITCH trace climbs; LIKE AN ANIMAL CALL; the VOLUME bars: ANIMALS stop at a mark, BLOOP runs past it; TOO LOUD |
| s03 | 10.32-15.29 | 3 | purple ocean section, red pulses; SCIENTISTS NICKNAMED IT; "THE BLOOP" slams with a flash; on "internet" a phone slides up: a post (`deepseafan_99`, "online theory") with a murky photo of a vague giant silhouette, an UNVERIFIED tag, a big ?, the quote "Something huge is down there.", likes climbing; THE INTERNET'S GUESS. Speculation, never shown as fact |
| s04 | 15.29-20.04 | 4 | bright mid-water, a fish school; NO CREATURE FITS; a blue whale glides through, soft rings from its head; a VOLUME scale: BLOOP mark at the top, the whale's level rises and stops far below; BLUE WHALE · LOUDEST ANIMAL; red X on "isn't" |
| s05 | 20.04-23.58 | 5 | CLUE 1: a nautical chart (equator, Australia, the Americas, Antarctica); four LISTENING STATIONS on the equator; dashed bearings run south and meet at a red pulsing source at the edge of Antarctica; FAR SOUTH |
| s06 | 23.58-28.02 | 6 | CLUE 2: green oscilloscope screen: WHALE SONG repeats (REPEATS brackets); THE BLOOP is one long rumble that draws on during "rumbled for about a minute", ~1 MINUTE span, then a flat line, THEN SILENCE |
| s07 | 28.02-34.60 | 7 | CLUE 3: polar day, ice shelf front, a red research ship lowers a microphone on its A-frame cable into the water (split above/below); 2005 · NEAR ANTARCTICA; on "heard it again" icequake rings start from the shelf root and the microphone flashes; a counter 1 → 100 → 1,000s / YEAR |
| s08 | 34.60-38.46 | 8 | **one continuous shot with s09 (`riddle()`, s09 in `NO_PUNCH`: no cut punch/flash).** Night sea, moon, far icebergs, moonlight shafts, far seafloor ridges; the camera descends from the surface toward the deep; a heavily blurred, featureless dark mass (soft shifting lobes, no limbs) sending red pulses and glowing red as it "roars"; a sonar pinger sends scan rings, and where a ring crosses the mass only a faint cyan arc of its outline shows (half-seen); drifting question marks; the big red ?; ROARS 1,000s OF TIMES A YEAR; NEVER NEEDS TO BREATHE? |
| s09 | 38.46-39.99 | 9 | same shot, same clock: on "Not" the ?, chips and question marks give way, NOT A slams and bright angular ice fractures spread through the mass with frosted facets and light leaking out (a light shake); on "monster." MONSTER. slams and the mass shatters (flash, shake, camera pulls back) into faceted shards that stay in the sea; on "Ice." the scene floods with cold light, NOT A MONSTER. lifts away, ICE. slams and the shards settle as glinting ice (star glints, floes bobbing at the waterline). The shape never resolves into a creature |
| s10 | 39.99-44.20 | 10 | golden-hour Antarctic shelf panorama; ANTARCTICA; ICE SHELVES / CRACK on "crack" as two glowing cracks run down the wall; a slab tilts and sinks behind the waterline on "break away into the sea", splash, a red front into the water |
| s11 | 44.20-49.96 | 11 | daylight cross-section: a big slab with a lit city skyline on it (THE SIZE OF A CITY); SPLIT! on "splits" with a flash and shake; on "shudder" bold red fronts run through the water; the camera pans with them to a far station that flashes; a dashed arrow, 1,000s OF KM |
| s12 | 49.96-54.29 | 12 | warm kitchen, a glass with an ice cube that cracks (glowing fracture lines, ripples) on "cracking"; IN YOUR DRINK; on "Now make that ice cube..." the cube grows while the kitchen dissolves into a polar sea; a mountain (solid, snow caps) and a tiny ship for scale; a larger inset (lower right) of the glass it started in; the cube a little under the mountain's height; THE SIZE OF / A MOUNTAIN; a red front on "mountain" |
| s13 | 54.29-58.08 | 13 | an office: the pinned BLOOP · 1997 chart, a bookshelf; YEARS LATER; the SCIENTIST nods on "made it official" (OFFICIAL); the case file THE BLOOP · PACIFIC · 1997 with the "MONSTER?" photo; ICEQUAKE stamp slams on "icequake", red X over the photo |
| s14a | 58.08-61.20 | 14 | the Antarctic coast at night under an aurora; cracks flash along the ice cliff, each sending red fronts down into the dark sea; THE "MONSTER" = / ANTARCTICA, BREAKING |
| s14b | 61.20-65.40 | 14 | the dark listening room, the SCIENTIST listening (thinking pose, headphones), the tall display live with the s01 ocean (red pulses, stations); EVERY DAY; after "listening." (64.64) a 0.6 s push into the display until it fills the frame; the last frame is s01 one frame before frame 0 (the loop). No caption during the push (`seam`) |

Hooks (SCRIPT.md map): 0 s sound crossing the ocean + A SOUND FROM THE DEEP; 6.9 s the jolt / pitch rising; 9.8 s TOO LOUD; 11.7 s THE BLOOP; 12.7 s the monster post; 15.6 s NO CREATURE FITS; 19.1 s X over the whale; 20 s CLUE 1; 23.7 s CLUE 2; 28 s CLUE 3; 33.2 s 1,000s / YEAR; 34.7 s the big ?; 38.6 s NOT A MONSTER; 39.5 s ICE.; 42.5 s the shelf cracks; 45.8 s SPLIT!; 47.2 s the shudder; 52 s cube → mountain; 57.3 s ICEQUAKE; 60 s ANTARCTICA, BREAKING; 64.8 s push into the loop.

## Review (stills only; one fresh sonnet reviewer per round, each still with its voice-over line and shot-table row, plus an in-order sequence sheet)
| Round | richness / readability / composition | per shot r/r/c (s01 … s14b) | Overall | script contradiction | 3+ run | result |
|---|---|---|---|---|---|---|
| 1 | 7.1 / 8.2 / 7.0 | 8/9/8 8/9/8 8/9/8 7/8/6 8/8/8 8/9/8 8/8/7 6/8/6 6/9/6 7/8/7 7/8/7 5/6/5 6/7/5 8/9/8 8/8/7 | 7.4 | none | none | FAIL |
| 2 | 7.7 / 8.5 / 7.9 | 8/9/8 8/9/8 9/9/9 8/9/8 8/8/8 8/9/8 8/8/8 7/8/8 6/8/7 9/9/8 7/7/7 8/8/7 7/8/7 8/9/8 8/8/8 | **8.0** | none | none | **PASS** |

Fixes after R1: s12 shows the mountain stage with a solid mountain, a bigger ship and an inset of the glass; s13 larger scientist, cleaner file, the stamp off the photo; s08 far icebergs and clouds, a defined shadow not cropped; s09 denser shards from the shadow, still taken nearer the burst; s10 bigger tilt, the crack scars stay lit, a recessed wall behind the slab; s11 bigger slab with the city on it, shorter pan, the far station in frame; s04 whale redrawn (blunt head, belly inside the body), fully in frame, the X on the whale level; s14b scientist centred, floor glow and lines, a mug.
After R2 (gate passed; small fixes from its list, not re-reviewed): FAR SOUTH next to the source (s05), THEN SILENCE off the trace (s06), a bookshelf instead of empty wall boxes (s13), bolder shudder fronts and a filled, lit city skyline (s11), varied shard colours (s09). Not done: R2's "fill s02's lower left", "s07 second ship", "enlarge the s12 inset".

### v2 review (changed shots only: s02, s08, s09 at crack/shatter/ice, s12; each still with its line and shot row, plus an s07-s13 sequence sheet)
| Round | richness / readability / composition | per shot r/r/c (s02, s08, s09, s12) | script contradiction | 3+ run | result |
|---|---|---|---|---|---|
| 3 | 7.0 / 7.5 / 6.75 | 8/8/7 7/8/7 6/7/6 7/7/7 | near: s08 tentacle streaks read as a creature | none | FAIL |
| 4 | 7.25 / 8.0 / 7.5 | 8/8/7 6/8/8 7/8/7 8/8/8 | NOT A MONSTER. still on screen with ICE. | none | FAIL |
| 5 | 7.0 / 7.75 / 7.0 | 8/8/7 6/7/7 7/8/7 7/8/7 | none (its "s09a sync" flag is the still's time: 38.9 s is after "monster." starts at 38.80 s) | none | FAIL |

Fixes after R3: the mass is a featureless blob (no tentacles; sonar returns only on the body outline); angular ice cracks with frosted facets instead of lightning forks; varied shard sizes (a few big chunks), shards kept in the sea, more glints; NOT A / MONSTER. slam word by word; s12 cube scaled to a little under the mountain, MOUNTAIN tag removed, inset moved right; recorder larger and lighter.
After R4: NOT A MONSTER. lifts away as ICE. lands; s08 gets moonlight shafts, two far seafloor ridges, more marine snow, bolder pulses and a red glow as it roars; faceted (two-tone) shards, fewer.
**Plateau rule (3 rounds) reached at ~7.0-7.25 richness / ~7.0-7.5 composition, below the 8 gate; shipped on the Producer's brief.** The three reviewers contradict each other on details (s12 cube "taller than the mountain" in R3 vs "make it clearly larger" in R5). No script contradiction remains. Left open from R5: a faint lit edge on the s08 mass (kept off on purpose: the Producer asked that it never look confirmed), s02 legs overlapping the recorder, a different palette for s12 vs s11, more refraction on the s09 shards.

## Motion QA (`flat2d/motion_qa.py`)
Run on the 1962 rendered preview frames: `motion_qa.py FRAMES 6.03 10.32 15.29 20.04 23.58 28.02 34.60 38.46 39.99 44.20 49.96 54.29 58.08 61.20 --impacts 6.83 11.66 15.68 39.47 45.70 57.22` → **PASS** (longest frozen span 1 frame; frame diffs median 1.61).
- First run (impacts 11.66, 39.47, 45.70 only) flagged three pops, all designed beats on the word, now listed as impacts: the SCIENTIST's jolt + shake on "rose" (6.83 s), the NO CREATURE FITS slam (15.68 s), the ICEQUAKE stamp + shake (57.22 s). The others: THE BLOOP flash (11.66), ICE. flash (39.47), SPLIT! flash (45.70).
- The s14b push-in into the display (64.8-65.4 s) is smooth and passes without an impact. Last frame vs frame 0: mean diff 6.7/255, the opening caption "In 1997," (first word at 0.02 s) and the marine snow; the picture is the same framing (the loop).
- Characters in holds go through `anim.actor` (breath, blinks, `anim.secondary`). Acting and feel are the Director's call on the preview.

## Sound
Serious mystery, no comedy stings. `mystery` for the sound and the monster guess (s01-s04), `explain` for the clues (s05-s07), `mystery` for the riddle (s08-s09), `explain` for the answer (s10-s11), `payoff` (thin) for the ice-cube analogy and the ruling (s12-s13), `mystery` into a loop end (riser into the push-in, no sting). Beds: `ocean` (new `amb_ocean`: low pressure hum and swell), `room`, `polar`, chart.
New cues in `audio/lib/sfx_x.py`: `bloop_rumble` (a deep sub rumble rising in pitch, the Bloop evoked) under the s01 opening (already sounding at frame 0), the s06 trace (cut at "stopped"), the s08 shadow, the s12 mountain and the s14a reveal; `ice_groan` (groan, cracks, thud) on the s10 slab. Other cues: `ice_crack` on the shelf crack, the s11 split, the s12 ice cube and the s14a coast; `deep_boom` on ICE. and the s11 shudder; `glass_shatter` as the shadow bursts into ice; pings when stations hear; impacts on the title slams and the ICEQUAKE stamp; card pops on the CLUE badges; splashes on the microphone and the slab; a whoosh on the phone; risers into the pitch rise, the ?, the cube growing and the loop.
Mix: −14.01 LUFS integrated, −1.20 dBTP, voice 9.9-11.0 LU over the bed per section; 1962 frames = 65.40 s (`length.json`).

## Publishing text (draft; never posted without the Director's OK)
**Title:** The Ocean Made a Sound No Animal Could Make 🌊 #shorts

**YouTube description:**
In 1997, underwater microphones in the Pacific picked up a sound so loud it was heard by sensors nearly 5,000 km apart. It rose in pitch like an animal call, but no known animal, not even the blue whale, the loudest animal alive, is that loud. Scientists nicknamed it "the Bloop", and the internet decided something huge was down there. The clues pointed elsewhere: the sound came from far south, near Antarctica; it rumbled for about a minute and didn't repeat; and when scientists put microphones near Antarctica in 2005, they heard sounds like it thousands of times a year. The answer: icequakes, giant ice shelves cracking and breaking away, sending a shudder through the water that travels thousands of kilometres.

Sources: Bloop (Wikipedia) https://en.wikipedia.org/wiki/Bloop · NOAA PMEL Acoustics, "Bloop" https://www.pmel.noaa.gov/acoustics/node/115 · Popular Science on NOAA's icequake explanation https://www.popsci.com/environment/sea-monster-bloop-sound/ · ScienceAlert, "Listen to the Pacific Bloop sound" https://www.sciencealert.com/listen-to-the-pacific-bloop-sound-that-flummoxed-scientists-for-8-years · Blue whale (Wikipedia) https://en.wikipedia.org/wiki/Blue_whale
"The internet had an answer" stands for the popular sea-monster speculation; the social post in the video is invented and marked UNVERIFIED.

#bloop #ocean #antarctica #science #mystery #shorts

**FB/TikTok caption (176 bytes, ≤ 255):**
1997: the Pacific made a sound heard 4,800 km apart, louder than any animal. The internet said sea monster. The real answer was colder. 🌊🧊 #bloop #ocean #science #mystery

## Open notes
- The acting and the feel are the Director's call on `tests/preview_full_540.mp4`.
- s14b → s01 loop: the display shows the s01 world live (s01 drawn at negative time), then a push-in until it fills the frame, so the restart has no jump.
- Render cost: about 3-4 frames/s on 4 cores at 540 output (frames drawn at 1080 and downscaled), ~10-15 min for the preview.
