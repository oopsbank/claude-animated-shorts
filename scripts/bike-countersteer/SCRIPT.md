# Why Your Bike Steers Backwards First (script v1, 2026-11-19)

- **Slug:** `bike-countersteer`
- **Topic:** #5 in `scripts/TOPICS.md`, chosen by the Director (the user) on 2026-11-19.
- **Approval:** the Director waived script approval for this video ("làm luôn khỏi duyệt kịch bản"). The draft-video review still applies.
- **Format:** story mode. The hook is in the second person ("you"), then the story follows an original everyman, Dale, at a riding school. About 3.7 words/s.

## Facts and sources (everything said in the voice-over)

| # | Claim in the voice-over | Sources | Status |
|---|---|---|---|
| F1 | At riding speed, a two-wheeler turns by leaning. To start a lean to the left, the rider first steers briefly to the right ("countersteering"). The bike then turns toward its lean. | [Wikipedia: Countersteering](https://en.wikipedia.org/wiki/Countersteering) · [Rider Magazine](https://ridermagazine.com/stayin-safe-countersteering/) · [Motorcyclist](https://motorcyclistonline.com/clearing-up-confusion-over-how-a-motorcycle-turns) | solid |
| F2 | The brief steer moves the tyres' contact patches out from under the bike, so the bike tips the other way. | [Wikipedia: Countersteering](https://en.wikipedia.org/wiki/Countersteering) · [Motorcyclist](https://motorcyclistonline.com/clearing-up-confusion-over-how-a-motorcycle-turns) | solid. ⚠ The full physics (trail, gyroscopic effects) is argued over; the voice-over stays at "pulls the wheels out from under you". |
| F3 | Riders do it without noticing ("even when unconscious"). | [Motorcyclist: Keith Code, countersteering vs body steering](https://motorcyclistonline.com/how-to-ride-motorcycle-body-steering-vs-counter-steering-riding-tips-how-to-steer-bike-keith-code) · [Rider Magazine](https://ridermagazine.com/stayin-safe-countersteering/) | solid |
| F4 | A riding school (the California Superbike School) built a test motorcycle with a second handlebar bolted to the frame, which cannot steer the front wheel, to show that leaning your body alone barely turns the bike. | [RideApart: "Counter Steering Your Bike Is No BS"](https://www.rideapart.com/news/350561/counter-steering-bike-no-bs/) · [The Kneeslider: the No BS bike](https://thekneeslider.com/motorcycle-countersteering-and-the-no-bs-bike/) · [Motorcyclist: Keith Code](https://motorcyclistonline.com/how-to-ride-motorcycle-body-steering-vs-counter-steering-riding-tips-how-to-steer-bike-keith-code) | solid. ⚠ Body steering alone makes a slow, wide turn, not zero turn. The voice-over says "barely turns" and "runs wide", never "can't turn at all". ⚠ The school isn't named in the video. |
| F5 | Motorcycle schools teach it on purpose: "push the left grip forward to go left". | [Wikipedia: Countersteering](https://en.wikipedia.org/wiki/Countersteering) (the MSF teaches it at all its schools) · [Ottawa Safety Council: push on the side where you want to go](https://www.ottawasafetycouncil.ca/?p=1981) | solid |
| F6 | Bicycles countersteer too. | [Wikipedia: Countersteering](https://en.wikipedia.org/wiki/Countersteering) · [Wikipedia: Bicycle and motorcycle dynamics](https://en.wikipedia.org/wiki/Bicycle_and_motorcycle_dynamics) | solid. ⚠ It's masked at walking speed, so every bike shot is at riding speed. |

Fiction, made up for the story: Dale, his twenty years of riding, the instructor, the lines of dialogue, and the signs. The demo is restaged with our own characters, and no real person is shown.

## Voice-over (one line = one shot in `shots.json`)

1. Ride into a left turn, and your bike steers right first, without you knowing it.
2. Meet Dale. Twenty years on motorcycles, and he swears he steers by leaning.
3. So a riding school hands him a strange bike.
4. It has two handlebars: a normal one, and one bolted to the frame that can't steer.
5. "Hold the fixed bars," says the instructor, "and take that corner."
6. Dale laughs, rolls onto the track, and leans hard left.
7. Almost nothing happens.
8. He leans harder, sticks his knee out, and wiggles his hips like he's at a wedding.
9. The bike barely turns and runs wide across the whole track.
10. Twenty years of riding, and he can't make the corner.
11. Wait, if leaning your body doesn't turn the bike, what does?
12. You see, bikes turn by leaning the whole bike, and to lean it left, you steer right for a split second.
13. That nudge pulls the wheels out from under you, so the bike tips left, then turns left.
14. It's like balancing a broom on your palm: to tip it left, flick your hand right first.
15. Riders do it without noticing, but the fixed bars stopped Dale's hands from doing it.
16. Motorcycle schools teach it on purpose: push the left grip forward to go left.
17. And yes, bicycles too.
18. So Dale's been steering the wrong way for twenty years, and it's the only way he ever turned.

**Word count: 231. Estimated length: 62.4 s at 3.7 words/s.** `build.py` checks this and writes `shots.json`.

## Formula check
| Formula step | Line(s) |
|---|---|
| Hook: a paradox stated as fact, 15 words | 1 |
| Setting (present tense, a named everyman, a number) | 2-3 |
| Escalation: dialogue, the stakes climb, exaggeration jokes (the wedding hips, "Twenty years… one corner") | 4-10 |
| Mystery beat ("Wait, …?") | 11 |
| "You see," + mechanism | 12-13 |
| Everyday analogy (the broom) | 14 |
| Ironic payoff (the "wrong way" is the only way he ever turned) | 15-18, ending on the last word |

## Signs and props that carry jokes (for the sets and characters areas)
1. A sticker on Dale's helmet: **"I STEER WITH MY HIPS"** (shots 2, 8).
2. A school banner over the track: **"BODY-STEERING CHALLENGE"** (shot 3).
3. The instructor's clipboard tally / lap board: **"CORNERS MADE: 0"** (shot 10).
4. A chalkboard in the pit: **"PUSH LEFT → GO LEFT"** (shot 16).

## Review
- Round 1 (an independent reviewer): hook 8, clarity 6, humour 7, accuracy 6, visual 6, FAIL. Fixed: "at speed" in the hook (now "Riding into a left turn"); "Almost nothing happens"; line 11 now says "leaning your body"; line 15 now ties the fixed bars to the hands; the pre-lean beats that went the wrong way were removed; body-only lean on the fixed-bars bike; front views wherever a steer arrow appears; the double helmet/broom props were removed. The reviewer's `music_note` note was wrong: it is in `fx/CATALOG.md`.
- Round 2: hook 8, clarity 6, humour 7, accuracy 8, visual 6, FAIL. Fixed: line 12 is now "a bike turns when the bike leans, not you" (it no longer sounds like it contradicts line 11); steer and lean shots use the rear chase cam plus a rider-side sign convention; the top-down shot s09 lost its unreadable face beat; the s12 path now shows a right kink then left; s15 now shows the normal bike, then a cut-in of the fixed bars blocking the steer; the s16 chalkboard draws the push-left/wheel-right link; "the corner" (not "one corner").
- Round 3: hook 8, clarity 7, humour 7, accuracy 8, visual 6, FAIL. Fixed: the broom demo is shot over the instructor's shoulder, so left/right match the screen; s12 shows the bike leaning on the chase cam, then cuts to top-down at "steer"; s13 slides the tyre contact patch at "pulls" and pans at "turns"; s08 starts on the grips and wiggles 5 times; s15 cuts in on the grips (front) for the blocked steer; distinct second beats in s05 and s16; no face beats on rear-view rigs; the s18 smile lands at "only".
- Round 4: hook 8, clarity 6, humour 7, accuracy 7, visual 7, FAIL on clarity. Fixed: the hook no longer over-claims ("your bike steers right first"); line 12 is simpler ("bikes turn by leaning the whole bike"); line 13 is "out from under you"; the top view in s12 is now an insert, so the lean reads on the chase cam; s07-s08 use the rear view; on the fixed-bars bike, the bike rolls slightly the wrong way (+3/+4) while Dale hangs left; the s16 exclaim moved to Dale's shock; speed lines in s17; cut to 231 words.
- **The loop stopped at 4 rounds** (per `PIPELINE.md`). The round-4 fixes target the only failing criterion (clarity) but were not re-reviewed. Re-review is logged in `BACKLOG.md`. The Director waived script approval, so this version goes to production.

## Shot mix
18 shots: 11 medium (61%), 4 close (22%, one of them, s04, is an effect-only close-up of the bike with no character), and 3 wide/top-down (17%). This matches `references/reports/recent_style_2026-11.md` §5.5 (about 60/20/15, ≤10).

## What the other areas need (also added to `BACKLOG.md`)
- **sets:** `village` gets a NEW `street_med` cam (day, golden). A NEW `track` set (a riding-school track with a pit lane and a grass run-off) with the cams `track_wide`, `track_med`, `track_top` (top-down), `pit_med`, `pit_ots` (over the instructor's shoulder), `bike_close`, `bike_chase` (behind the rider), `grips_close` (the handlebars from the front) and `rider_close` (front, face), in `day` and `golden` lights. It also needs the 4 signs above, via a signage helper.
- **characters:**
  - a `ride` arm pose (both hands forward on the grips), a seated/riding lower body, and a `helmet` hat (open-face, so the eyes stay visible);
  - bike sprites: `bicycle` and `motorbike` in side and front views, and a `nobs_bike` (a motorbike with a second, higher handlebar fixed to the frame);
  - props: `broom` (balanced upright on the palm) and `helmet` (under the arm);
  - lean support while riding: `lean` rotates the rider and bike together around the tyre contact point (up to about ±30°). For the fixed-bars gag (s06-s09), `body_lean` tilts only the rider while `bike_lean` keeps the bike near upright.
- **fx:** new `steer_arrow` (a curved arrow on the front wheel or the grips, `direction=left|right|blocked`; `blocked` adds a red stop bar), plus `path_line` (a dashed planned line vs the actual line on the top-down track). Existing: `speed_lines`, `dust_puff`, `sweat_drop`, `question_mark`, `exclaim`, `sparkle`.
- **engine:** bike rigs have `view: side|front|rear|top`. Shots with a left/right steer arrow use `rear` (a chase cam) or `top`, so the arrow reads. **Left, right and lean signs are always the rider's own** (negative lean = the rider's left). `insert` = a cut-in of another rig at that word (s15). `lean`, `body_lean` and `bike_lean` are animated from beats.
