# Why Your Bike Steers Backwards First: soundtrack cue sheet

All music and SFX are original, synthesized in numpy/scipy (`audio/lib/score.py`, `audio/lib/sfx_x.py`, template `dsp.py` / `instruments.py` / `sfx_gen.py`). Voice: ElevenLabs (see `audio/VOICE.md`), high-passed at 70 Hz and gently compressed (2:1, max 6.7 dB), no EQ colour or pitch change.

## Files
| file | content |
|---|---|
| `mix.wav` | final mix, 48 kHz stereo 24-bit, 3052800 samples = 1908 frames @ 30 fps = 63.600 s |
| `stem_voice.wav` / `stem_music.wav` / `stem_sfx.wav` | stems at mix gain, pre-limiter (their sum + the master limiter = the mix) |
| `length.json` | the picture length the engine must render |

## Master loudness (own BS.1770-4 meter)
- Integrated **-14.0 LUFS** (target -14.0), true peak **-1.2 dBTP** (ceiling -1.2), LRA 1.2 LU
- Stems at mix gain: voice -14.4, music -23.5, sfx -33.2 LUFS; master gain +9.19 dB
- Limiter: max gain reduction 3.69 dB, active (>0.1 dB) on 8.92 % of samples

ffmpeg ebur128 cross-check:
```
Summary:

  Integrated loudness:
    I:         -14.0 LUFS
    Threshold: -24.1 LUFS

  Loudness range:
    LRA:         1.2 LU
    Threshold: -34.0 LUFS
    LRA low:   -14.5 LUFS
    LRA high:  -13.4 LUFS

  True peak:
    Peak:       -1.2 dBFS
```

## Voice pacing (words.json)
- 231 words over 62.74 s = **3.68 words/s** (reference 3.5-4.1, median 3.7)
- gaps > 0.25 s: 0, total 0.00 s (reference < 1 s); longest gap 0.22 s
- first word at 0.040 s (frame 1.2); last word ends 62.778 s

## Voice on top, per section (LUFS at mix gain)
bed = music + sfx. margin = voice - bed (integrated). speech median / p10 = 400 ms momentary voice - bed over spoken words. Reference: bed 5-10 dB under the voice.

| section | time s | voice | music | sfx | bed | margin LU | speech median LU | speech p10 LU |
|---|---|---|---|---|---|---|---|---|
| hook | 0.00-4.12 | -14.6 | -23.1 | -40.2 | -23.0 | 8.4 | 8.5 | 5.8 |
| body | 4.12-32.83 | -14.3 | -23.3 | -32.5 | -23.0 | 8.7 | 8.6 | 5.0 |
| mystery | 32.83-35.83 | -14.6 | -24.6 | -37.2 | -24.5 | 9.9 | 10.1 | 4.0 |
| explain | 35.83-59.00 | -14.3 | -23.8 | -31.8 | -23.4 | 9.1 | 9.0 | 4.3 |
| payoff | 59.00-62.44 | -14.3 | -23.8 | -40.0 | -23.7 | 9.4 | 10.2 | 6.3 |
| sting+tail | 62.74-63.60 | -99.0 | -21.6 | -43.9 | -21.6 | -77.4 | nan | nan |

## Music map (original, G major, 112 bpm)
Music under the voice: -3 dB duck keyed from words.json, section targets (LU vs voice): hook -8.5, body -9.0, mystery -10.0, explain -9.5, payoff -9.5, sting -7.0. Applied section gains (dB): hook -10.5, body -11.1, mystery -6.1, explain -9.3, payoff -3.8, sting -6.2.

| time s | frame | music |
|---|---|---|
| 0.00 | 0 | hook: pluck arpeggio I-V-vi-IV, glock motif, kick + clap (no hats), from the first word |
| 4.12 | 124 | body: full groove, hats + pad join, 112 bpm |
| 32.83 | 985 | mystery: drums drop out, sus pad vi-IV-ii-Vsus + ticking glock |
| 34.93 | 1048 | riser into the pivot |
| 35.83 | 1075 | 'You see,': light vibes arpeggio IV-I/3-ii-V, bass; soft kick + brushes from bar 2 |
| 59.00 | 1770 | payoff: thins to pad + bass so the punchline lands dry |
| 62.74 | 1882 | sting: G major chord, glock, kick, soft cymbal right after the last word, rings out |

## SFX events
level = target LU vs the voice stem (max momentary of the event). Beds are integrated.

| # | time s | frame | cue | sound | why | level LU | pan |
|---|---|---|---|---|---|---|---|
| 1 | 0.040 | 1.2 | speed_lines | fast swish / speed lines | fx speed_lines (s01 word 0) | -16 | -0.36 |
| 2 | 3.862 | 115.9 | whoosh | transition whoosh | transition s01->s02 (track/pit_med) | -17 | +0.00 |
| 3 | 4.919 | 147.6 | sparkle | glock sparkle run | fx sparkle (s02 word 2) | -15 | -0.12 |
| 4 | 8.322 | 249.7 | whoosh | transition whoosh | transition s02->s03 (track/track_wide) | -17 | +0.00 |
| 5 | 9.936 | 298.1 | question_mark | rising two-note pizzicato 'hmm?' | fx question_mark (s03 word 7) | -16 | +0.19 |
| 6 | 10.664 | 319.9 | whoosh | transition whoosh | transition s03->s04 (track/bike_close) | -17 | +0.00 |
| 7 | 12.294 | 368.8 | sparkle | glock sparkle run | fx sparkle (s04 word 5) | -15 | -0.06 |
| 8 | 13.528 | 405.8 | exclaim | ding | fx exclaim (s04 word 9) | -14 | +0.06 |
| 9 | 15.085 | 452.6 | whoosh | transition whoosh | transition s04->s05 (track/pit_med) | -17 | +0.00 |
| 10 | 18.459 | 553.8 | whoosh | transition whoosh | transition s05->s06 (track/track_med) | -17 | +0.00 |
| 11 | 19.574 | 587.2 | dust_puff | dust puff | fx dust_puff (s06 word 2) | -15 | +0.14 |
| 12 | 20.186 | 605.6 | speed_lines | fast swish / speed lines | fx speed_lines (s06 word 5) | -16 | -0.30 |
| 13 | 20.674 | 620.2 | lean | swoop of the bike leaning into a turn | Dale leans hard left (word 70 'and') | -15 | +0.00 |
| 14 | 21.759 | 652.8 | whoosh | transition whoosh | transition s06->s07 (track/bike_chase) | -17 | +0.00 |
| 15 | 23.142 | 694.3 | whoosh | transition whoosh | transition s07->s08 (track/track_med) | -17 | +0.00 |
| 16 | 23.402 | 702.1 | impact | cartoon impact thump + crack | camera shake s08 | -14 | +0.00 |
| 17 | 23.818 | 714.5 | sweat_drop | drip blip | fx sweat_drop (s08 word 2) | -16 | +0.10 |
| 18 | 25.569 | 767.1 | boing | spring boing | wiggles his hips (word 85 'wiggles') | -15 | +0.00 |
| 19 | 27.255 | 817.7 | whoosh | transition whoosh | transition s08->s09 (track/track_top) | -17 | +0.00 |
| 20 | 28.665 | 859.9 | tyre_skid | tyre skid squeal | bike runs wide across the track (word 98 'runs') | -15 | +0.00 |
| 21 | 29.187 | 875.6 | dust_puff | dust puff | fx dust_puff (s09 word 7) | -15 | +0.38 |
| 22 | 30.114 | 903.4 | whoosh | transition whoosh | transition s09->s10 (track/pit_med) | -17 | +0.00 |
| 23 | 32.222 | 966.7 | sweat_drop | drip blip | fx sweat_drop (s10 word 9) | -16 | -0.10 |
| 24 | 32.565 | 976.9 | whoosh | transition whoosh | transition s10->s11 (track/rider_close) | -17 | +0.00 |
| 25 | 35.276 | 1058.3 | question_mark | rising two-note pizzicato 'hmm?' | fx question_mark (s11 word 10) | -16 | +0.18 |
| 26 | 35.567 | 1067.0 | whoosh | transition whoosh | transition s11->s12 (track/bike_chase) | -17 | +0.00 |
| 27 | 41.685 | 1250.6 | dust_puff | dust puff | fx dust_puff (s13 word 4) | -15 | +0.07 |
| 28 | 43.412 | 1302.4 | lean | swoop of the bike leaning into a turn | the bike tips left (word 158 'tips') | -15 | +0.00 |
| 29 | 44.947 | 1348.4 | whoosh | transition whoosh | transition s13->s14 (track/pit_ots) | -17 | +0.00 |
| 30 | 47.945 | 1438.3 | speed_lines | fast swish / speed lines | fx speed_lines (s14 word 12) | -16 | +0.10 |
| 31 | 48.761 | 1462.8 | sparkle | glock sparkle run | fx sparkle (s14 word 16) | -15 | -0.12 |
| 32 | 49.117 | 1473.5 | whoosh | transition whoosh | transition s14->s15 (track/track_med) | -17 | +0.00 |
| 33 | 52.502 | 1575.1 | sparkle | glock sparkle run | fx sparkle (s15 word 11) | -15 | +0.12 |
| 34 | 53.206 | 1596.2 | whoosh | transition whoosh | transition s15->s16 (track/pit_med) | -17 | +0.00 |
| 35 | 55.754 | 1672.6 | exclaim | ding | fx exclaim (s16 word 8) | -14 | -0.24 |
| 36 | 57.227 | 1716.8 | whoosh | transition whoosh | transition s16->s17 (village/street_med) | -17 | +0.00 |
| 37 | 57.487 | 1724.6 | speed_lines | fast swish / speed lines | fx speed_lines (s17 word 0) | -16 | -0.36 |
| 38 | 57.487 | 1724.6 | freewheel | coasting freewheel ratchet | bicycle coasting in (word 209 'And') | -17 | +0.00 |
| 39 | 57.959 | 1738.8 | bike_bell | bicycle thumb bell, ring-ring | bell on 'bicycles' (word 211 'bicycles') | -11 | +0.30 |
| 40 | 58.493 | 1754.8 | exclaim | ding | fx exclaim (s17 word 3) | -14 | +0.14 |
| 41 | 58.742 | 1762.3 | whoosh | transition whoosh | transition s17->s18 (track/pit_med) | -17 | +0.00 |
| bed | 0.000-4.062 | 0.0 | amb_outdoor | ambience for set 'village' | shots on that set | -30.0 (int.) | 0 |
| bed | 4.062-57.427 | 121.9 | amb_road | ambience for set 'track' | shots on that set | -30.0 (int.) | 0 |
| bed | 57.427-58.942 | 1722.8 | amb_outdoor | ambience for set 'village' | shots on that set | -30.0 (int.) | 0 |
| bed | 58.942-63.600 | 1768.3 | amb_road | ambience for set 'track' | shots on that set | -30.0 (int.) | 0 |
