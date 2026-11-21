# Why Your Bike Steers Backwards First: draft v1 (engine render, 2026-11-20)

`draft_v1.mp4` is 1080x1920, 30 fps, exactly 1921 frames (64.033 s), with `audio/bike-countersteer/mix.wav` muxed in. It is **a draft for the Director's review. Not for publishing.**

- **Inputs:**
  - `scripts/bike-countersteer/shots.json` (18 shots);
  - `audio/bike-countersteer/words.json`;
  - plates from `blender/sets/track` (final) and `blender/sets/village` (final);
  - riders from `characters/scripts/bikes.py`;
  - props from bean.py;
  - effects from `fx/fx.py`.
- **Engine:** `claude/area-engine` at commit a0b7b82. Command:
  `ENGINE_STANDIN=0 .venv/bin/python engine/render_video.py scripts/bike-countersteer/shots.json audio/bike-countersteer/words.json OUT --audio audio/bike-countersteer/mix.wav` (about 8 minutes on 4 CPUs).
- **Automatic QA** (`qa/engine_qa_draft_v1.md`): all hard checks pass.
  - no black, white or frozen spans of 12 frames or more;
  - no character clipped at the frame edge;
  - feet on the ground line;
  - planted feet;
  - all 32 beats land 0-3 frames before their word;
  - length and format.
- **Contact sheet:** `qa/contact_every_2s_draft_v1.jpg`.

## Known issues
1. **Frame stats are a warning:** only 6 of 65 sampled frames meet the reference value targets. Most fail on mean luminance below 0.40, and some on saturation or edge density. This comes from the plates, so it belongs to sets.
2. **Two-shots on `pit_med`** (s05, s10, s16, s18): at the script's `x` values the characters overlapped, so the engine spread them apart. In s05, s10 and s16 it also stepped them back to 0.86x in depth. Scripts may want to set those positions.
3. **Countersteer:** `shots.json` has no `steer` values, so the engine adds an automatic countersteer flick before every lean of more than 5°. Please check that it reads clearly (s01, s12, s13, s15, s17).
4. **s14 (`pit_ots`):** the near instructor is seen from behind at 1.7x. Check that the broom on the palm reads clearly.
5. **Not reviewed:** no independent reviewer has watched this full draft yet. The engine's earlier test clip scored motion 7, acting 6, readability 7, pacing 7 and look 6.
6. **Blinks:** half-closed blink frames still use an engine overlay; bean.py has no half-lid option.

---

# Draft v2 (2026-11-20)

`draft_v2.mp4` is 1080x1920, 30 fps, exactly 1921 frames, with `mix.wav` muxed in. **It is a draft. Not for publishing.**

- **Inputs:** shots v2 (f3acd3e), wardrobe's rear-view motorbike and `broom_insert` card, and the final plates.
- **New since v1:**
  - word-by-word captions;
  - a per-shot grade;
  - shots v2 (pit shot/reverse-shot, rider close-up punch-ins, the s14 broom insert);
  - countersteer cue arrows at handlebar height.
- **Engine:** `claude/area-engine` at commit f8d6868. After the review, the changed shots (s01, s02, s06, s07, s12-s15, s17, s18) were re-rendered with the same per-shot grade (`grade.json`) and spliced into the full render.
- **Automatic QA** (`qa/engine_qa_draft_v2.md`): all hard checks pass. That includes caption sync (0-2 f), no captions in silences and no caption over a face. Frame stats (a warning): 43 of 65 sampled frames pass (v1: 6 of 65). The rest are plate content (edge density, sky-blue share).
- **Contact sheet:** `qa/contact_every_2s_draft_v2.jpg`.

## Independent review (one pass, before the fixes)
- **Scores:** motion 7, acting 7, readability 6, pacing 8, look 8, clarity 5.
- **Blockers, both fixed (not re-reviewed):**
  1. **s13:** the countersteer flick was hidden behind Dale's body. Fixes:
     - an arrow now appears at handlebar height with every automatic flick;
     - the flick is stronger;
     - the `contact_shift` "nudge" flicks the bars.
  2. **s14:** the broom tipped before the hand flicked. The tip now plays 10 f after the flick, as its result.
- **Nice-to-haves, not done:**
  - Dale is small behind the near instructor in s18 (60-64 s); scripts could swap the shot/reverse-shot or move Dale forward;
  - the "?" at 36 s is small;
  - the s10 close-up has a static mouth (Dale doesn't talk; it's voice-over);
  - the riders are specks in s15 (50-51 s, on `track_wide`);
  - the broom card's ghost hand is faint (wardrobe).

---

# Draft v3 (2026-11-21)

`draft_v3.mp4` is 1080x1920, 30 fps, exactly 1921 frames, with `mix.wav` muxed in. **It is a draft. Not for publishing until the Director says so.** The voice-over is unchanged.

- **Process:** the first video run through the new stage gates (`PIPELINE.md` › Stage gates). `tools/preflight.py` reports 0 errors and 3 noted warnings (s16). A storyboard was reviewed before the render.
- **Fixed since v2:**
  - s03/s16: the two-shot `x` values are set by the script, so the engine no longer moves anyone.
  - s06: no face beats on the rear view.
  - s03, s10, s16, s18: body changes on every beat.
  - Symbol FX are 0.45-0.5 W and anchored to Dale (s16's "!" sits above the head).
  - s15: on `track_med`, so the rider is readable.
  - s05/s18: the far actor is scaled up in the OTS.
  - The ghost hand on the broom card is stronger.
- **Mechanism section, after two independent review rounds:**
  - s12 is a closer chase that stays upright until the steer.
  - s13 keeps the same framing across the cut, with a big yellow "nudge" arrow at the bars, then one continuous tip left and the turn.
  - s12 was re-rendered with s13 and spliced in, because a static end of s12 failed the frozen-span check.
- **Automatic QA** (`qa/engine_qa_draft_v3.md`): all hard checks pass. Frame stats pass 43 of 65 (a warning).
- **Review:** round 1 FAIL (clarity 6, s12-s13 blocker). Round 2 FAIL (clarity 6: the lean rocked before the steer, and the arrow was small and red on red). Both blockers are fixed. There was no third review (QA caps it at 2 rounds).
- **Open, NICE only:**
  - the bars/front tyre never visibly turn: a new rig view is needed (BACKLOG wardrobe P2);
  - the path_line kink is thin;
  - the "I STEER WITH MY HIPS" sticker is unreadable at phone size;
  - the ending two-shot is static for about 4 s;
  - nothing on screen shows "steers right first" in the 0-4 s hook.

---

# Draft v4 (2026-11-21)

`draft_v4.mp4`: v3 plus the Director's two notes on v3. The voice-over is unchanged. **It is a draft, not for publishing until the Director says so.**

- **The background moves when riding.** Sets write metric depth maps (`build.py --depth`) for `bike_chase`, `track_med` and `street_med`. The engine dollies the chase camera into the plate (`engine/parallax.py`), so near ground, cones and the start line stream past while the distance barely moves.
  - Travel: up to 2.5 m in the village, 1.2 m on `track_med`, and 1.6 + 2.0 m carried across the s12/s13 cut.
  - A light unsharp mask after the warp keeps the ink edges.
- **Top-down paths follow the real road.** Racing lines are projected from the track geometry into the `track_top` JSON (`blender/sets/track/paths.py`), and the planned line is yellow. In s09 the rider runs wide over the outer kerb. The s12 cut-in rider rides the kink, and the diagram ends with its cut-in.
- **Automatic QA:** all hard checks pass. Frame stats pass 45 of 65 (v3: 43).
- **Review:** no independent review of v4 yet. The changes are the background and the paths, checked by eye on sampled frames.

---

# Final cut and posting (2026-11-21)

- **Post this:** `bike-countersteer_captions_cover_1080x1920.mp4`, which is draft v4 with `thumbnail.png` as the first 3 frames and the audio delayed by 0.1 s (1924 frames, 64.14 s). Not posted yet; the Director posts by hand.
- **Title:** Why Your Bike Steers Backwards First 🏍️
- **YouTube description:** To turn left on a bike, you steer right for a split second. It's called countersteering: that nudge pulls the wheels out from under you, so the bike leans left, then turns left. Riders do it without noticing, and motorcycle schools teach it on purpose. #countersteering #motorcycle #physics #science #shorts
- **Instagram/Facebook caption** (under 255 bytes): To turn left on a bike, you steer RIGHT first 🤯 It's called countersteering, and you've done it your whole life without noticing. #countersteering #motorcycle #bicycle #physics #science
- **Open nice-to-haves** (not planned):
  - the bars and front tyre never visibly turn (BACKLOG characters P2);
  - the "I STEER WITH MY HIPS" sticker is unreadable at phone size;
  - the ending two-shot is static for about 4 s;
  - the 0-4 s hook doesn't show "steers right first".
