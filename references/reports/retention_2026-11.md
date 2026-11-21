# Why our viewers leave around the middle (retention ≤ 50%), 2026-11-21

The Director reports the posted shorts keep at most about 50% of their length on average. The analytics need a channel login, so this compares the **videos themselves**.

**Compared:**
- three posted shorts: Lake Nyos, The Town Where You're Not Allowed to Die, and the plane windscreen (from branch `claude/sleepy-lovelace-n8psvk` and its git history);
- our bike-countersteer v5;
- four competitor shorts the Director downloaded (720p): Ricks Clips "Why Perfect Railroads Don't Work" (30 M views) and "Why Samurai Feared The Flying Thunder" (1.4 M); Segment Zero "The Deadliest Sniper Never Used a Scope" (1.4 M) and "Why Every Train Carries Sand" (1.1 M).

**Scripts:** `references/scripts/video_cuts.py` (cuts, shot lengths, motion) and `video_audio.py` (speech, pauses, music bed).

## 1. Pacing: the clearest gap
| Video | Shot length (median) | New cut/transition per 10 s | Picture motion (median frame diff) | Near-still frames |
|---|---|---|---|---|
| Ricks: Railroads | 0.4 s* | 7.8 | 7.4 | 2% |
| Ricks: Samurai | 1.1 s | 4.4 | 3.3 | 6% |
| Segment Zero: Sniper | 0.5 s* | 8.4 | 2.5 | 16% |
| Segment Zero: Train sand | 0.2 s* | 3.7 | 4.4 | 3% |
| **ours: Lake Nyos (posted)** | **3.4 s** | **2.9** | **1.0** | **38%** |
| ours: Town (posted) | 1.9 s | 4.0 | 1.8 | 9% |
| ours: Plane (posted) | 1.2 s | 6.3 | 2.3 | 5% |
| **ours: bike v5 (not posted)** | **3.2 s** | **3.3** | **0.9** | **29%** |

\* Their short "shots" are mostly **3D camera fly-throughs with heavy motion blur**: a bullet-cam through a snowy forest, a flight from desert to station, a whip along the rails. The camera physically travels through the 3D world, so the picture changes every 0.3-1 s even inside one scene. Our camera only zooms and pans a still picture.

## 2. The first 4 seconds
- **Theirs:**
  - the story starts mid-action ("He sawed gaps into a railroad every 39 feet", a falling bullet casing in slow motion);
  - a character acts in frame from frame 1;
  - there are 2-3 picture changes in 4 s, plus an extreme close-up or a moving camera.
- **Ours:**
  - Lake Nyos opens on 4 s of an empty, static landscape;
  - Town on one static frame of a standing character;
  - Plane on 3 s of a static close-up.

  The first visual change comes at 3-4 s.

## 3. Endings
- **Theirs:**
  - a big payoff gag (a giant explosion, the train sliding sideways);
  - or a **seamless loop**: the Sniper ends "And that's why…" over the opening shot, so the last line runs into the first, and replays push retention past 100%.
- **Ours:** Lake Nyos and Town loop, which is good. **Plane fades to black**, which tells the viewer the video is over.

## 4. Look and density
Theirs: rich 3D sets, warm/cool lighting, characters acting inside the set, an X-ray cutaway of a locomotive, map and newspaper inserts, UI badges ("1 TON", "GRIP ✗/✓", "HILL 1-2-3" progress), and POV gun sights. Lake Nyos and Plane are flat, simple vector scenes; Town is in between.

## 5. Sound
Loudness is equal (all -14 LUFS). Their LRA is 1.4-3.2 LU against our 1.2 (ours is slightly more squashed). The music sits under the voice in every gap. No clear audio gap; it is not the cause.

## 6. Diagnosis, ranked
1. **Too slow and too still in the middle:** 2-3 s static shots with zoom-only cameras. Viewers drift once the novelty of the hook is used up, around the middle. Their median is about 1 s per visual change, with constant camera travel.
2. **A weak visual hook:** nothing moves or changes in the first 3-4 s.
3. **Flat visuals** on some videos (Lake Nyos, Plane).
4. **Endings that close instead of loop** (Plane's fade to black).

## 7. Fixes (now in BACKLOG and PIPELINE)
- **A visual change every ≤ 1.5 s:** a cut, a punch-in, an insert or a camera move.
  - No shot longer than 3 s without a new beat.
  - `tools/preflight.py` should warn over 3 s (today it warns at 6.5 s).
- **Camera fly-through transitions:** render short Blender camera moves (0.5-1.5 s) at low res and low samples, then add heavy motion blur, which hides the quality. Use them between locations and for "follow the object" moments (bullet-cam, follow the coin).
- **Hook rule:**
  - frame 1 shows a character mid-action or an extreme close-up;
  - at least 2 picture changes before 3 s;
  - the first line starts in the story, not with a setup ("One night in 1986…").
- **End on a payoff gag, or a seamless loop where the last line runs into the first.** Never fade to black.
- **One insert type per 10 s:** a map, a newspaper, an X-ray cutaway, a UI badge or counter, a POV.

## 8. How their scripts are built (transcripts read from the burned-in captions with OCR)
All four follow the same story engine. We study the structure only; never reuse their stories or lines.

1. **Line 1 is a person doing something that looks wrong, told as fact, in the past tense:**
   - "He sawed gaps into a railroad every 39 feet."
   - "He rolled the bomb into the enemy camp but made sure it wouldn't go off."
   - "He poured a ton of sand into a brand-new locomotive…"
   - Or the paradox stated plainly: "The deadliest sniper in history … never used a scope."

   Line 1 is never a setting ("One night in 1986…") and never second person.
2. **Line 2 is "You see,"** plus the stakes (two companies racing, 10,000 samurai attacking at sunrise, paid by the ton, the Soviets invading). In the leaders, "You see," comes **early** to set the scene, not late before the mechanism.
3. **A mocking rival or boss, in quoted dialogue:**
   - "You're wrecking my railroad."
   - "Get out of my tent."
   - "Is that a locomotive or a litter box?"
   - "Son, real snipers use a scope."
4. **The rival's way wins first** (they finish first; the big engine storms up hill 1). The narration is in the present tense.
5. **Three escalating stages with clear markers:** May → July → the hottest day; hill 1 → 2 → 3; four soldiers → 25 → an army.
6. **The mechanism comes late and short,** with one physical analogy: "Ever run across a kitchen floor in socks?"; "a scope is just a tiny mirror".
7. **A reversal and a punchline:** the rival's way fails spectacularly (the rail kicks sideways under a train; the hammer hits the powder), the quirk is vindicated, then a last gag line ("Sorry. The sand is for the cat.") or a loop line ("And that's why…" into line 1).
8. **Length and rate:** 59-71 s at about 3.5-4 words/s (OCR estimate; ours is 3.66). There is no intro, no "did you know" and no call to action in the voice (Segment Zero adds a "Subscribe for more" pill on screen at the end).

**Our bike script, by this measure:**
- Its opening is second person ("Ride into a left turn…"), and "Meet Dale" comes second.
- The instructor is a voice, not a mocking rival.
- There is no spectacular failure of the rival's way, and "You see," comes late.

The posted Lake Nyos script is a documentary with no protagonist at all. Both are weaker story engines than the leaders'.
