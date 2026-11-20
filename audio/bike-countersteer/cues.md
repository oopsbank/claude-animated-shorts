# Why Your Bike Steers Backwards First: soundtrack cue sheet

All music and SFX are original, synthesized in numpy/scipy (`audio/lib/score.py`, `audio/lib/sfx_x.py`, template `dsp.py` / `instruments.py` / `sfx_gen.py`). Voice: ElevenLabs (see `audio/VOICE.md`), high-passed at 70 Hz and gently compressed (2:1, max 6.8 dB), no EQ colour or pitch change.

## Files
| file | content |
|---|---|
| `mix.wav` | final mix, 48 kHz stereo 24-bit, 3073600 samples = 1921 frames @ 30 fps = 64.033 s |
| `stem_voice.wav` / `stem_music.wav` / `stem_sfx.wav` | stems at mix gain, pre-limiter (their sum + the master limiter = the mix) |
| `length.json` | the picture length the engine must render |

## Master loudness (own BS.1770-4 meter)
- Integrated **-14.0 LUFS** (target -14.0), true peak **-1.2 dBTP** (ceiling -1.2), LRA 1.2 LU
- Stems at mix gain: voice -14.3, music -23.5, sfx -34.3 LUFS; master gain +9.24 dB
- Limiter: max gain reduction 3.79 dB, active (>0.1 dB) on 8.95 % of samples

ffmpeg ebur128 cross-check:
```
Summary:

  Integrated loudness:
    I:         -14.0 LUFS
    Threshold: -24.0 LUFS

  Loudness range:
    LRA:         1.2 LU
    Threshold: -34.0 LUFS
    LRA low:   -14.6 LUFS
    LRA high:  -13.4 LUFS

  True peak:
    Peak:       -1.2 dBFS
```

## Voice pacing (words.json)
- 231 words over 63.17 s = **3.66 words/s** (reference 3.5-4.1, median 3.7)
- gaps > 0.25 s: 3, total 0.96 s (reference < 1 s); longest gap 0.32 s
- first word at 0.040 s (frame 1.2); last word ends 63.207 s

## Voice on top, per section (LUFS at mix gain)
bed = music + sfx. margin = voice - bed (integrated). speech median / p10 = 400 ms momentary voice - bed over spoken words. Reference: bed 5-10 dB under the voice.

| section | time s | voice | music | sfx | bed | margin LU | speech median LU | speech p10 LU |
|---|---|---|---|---|---|---|---|---|
| hook | 0.00-4.15 | -14.6 | -23.1 | -40.3 | -23.0 | 8.4 | 8.5 | 5.9 |
| body | 4.15-33.11 | -14.3 | -23.3 | -32.7 | -23.0 | 8.7 | 8.6 | 4.9 |
| mystery | 33.11-36.22 | -14.7 | -25.5 | -37.0 | -25.2 | 10.5 | 11.0 | 3.8 |
| explain | 36.22-59.43 | -14.3 | -23.8 | -33.3 | -23.4 | 9.2 | 9.0 | 4.3 |
| payoff | 59.43-62.87 | -14.3 | -24.1 | -44.5 | -24.1 | 9.9 | 11.3 | 5.8 |
| sting+tail | 63.17-64.03 | -99.0 | -20.9 | -40.9 | -20.8 | -78.2 | nan | nan |

## Music map (original, G major, 112 bpm)
Music under the voice: -3 dB duck keyed from words.json, section targets (LU vs voice): hook -8.5, body -9.0, mystery -10.0, explain -9.5, payoff -8.5, sting -7.0. Applied section gains (dB): hook -10.5, body -11.1, mystery -6.6, explain -9.3, payoff -2.4, sting -6.6.

| time s | frame | music |
|---|---|---|
| 0.00 | 0 | hook: pluck arpeggio I-V-vi-IV, glock motif, kick + clap (no hats), from the first word |
| 4.15 | 124 | body: full groove, hats + pad join, 112 bpm |
| 33.11 | 993 | mystery: drums drop out, sus pad vi-IV-ii-Vsus + ticking glock |
| 35.32 | 1059 | riser into the pivot |
| 36.22 | 1086 | 'You see,': light vibes arpeggio IV-I/3-ii-V, bass; soft kick + brushes from bar 2 |
| 59.43 | 1783 | payoff: thins to pad + bass so the punchline lands dry |
| 63.17 | 1895 | sting: G major chord, glock, kick, soft cymbal right after the last word, rings out |

## SFX events
level = target LU vs the voice stem (max momentary of the event). Beds are integrated.

| # | time s | frame | cue | sound | why | level LU | pan |
|---|---|---|---|---|---|---|---|
| 1 | 0.040 | 1.2 | speed_lines | fast swish / speed lines | fx speed_lines (s01 word 0) | -16 | -0.36 |
| 2 | 3.887 | 116.6 | whoosh | transition whoosh | transition s01->s02 (track/pit_med) | -17 | +0.00 |
| 3 | 4.963 | 148.9 | sparkle | glock sparkle run | fx sparkle (s02 word 2) | -15 | -0.12 |
| 4 | 8.393 | 251.8 | whoosh | transition whoosh | transition s02->s03 (track/track_wide) | -17 | +0.00 |
| 5 | 10.007 | 300.2 | question_mark | rising two-note pizzicato 'hmm?' | fx question_mark (s03 word 7) | -16 | +0.19 |
| 6 | 10.705 | 321.1 | whoosh | transition whoosh | transition s03->s04 (track/bike_close) | -17 | +0.00 |
| 7 | 12.336 | 370.1 | sparkle | glock sparkle run | fx sparkle (s04 word 5) | -15 | -0.06 |
| 8 | 13.570 | 407.1 | exclaim | ding | fx exclaim (s04 word 9) | -14 | +0.06 |
| 9 | 15.103 | 453.1 | whoosh | transition whoosh | transition s04->s05 (track/pit_med) | -17 | +0.00 |
| 10 | 18.597 | 557.9 | whoosh | transition whoosh | transition s05->s06 (track/track_med) | -17 | +0.00 |
| 11 | 19.712 | 591.4 | dust_puff | dust puff | fx dust_puff (s06 word 2) | -15 | +0.14 |
| 12 | 20.324 | 609.7 | speed_lines | fast swish / speed lines | fx speed_lines (s06 word 5) | -16 | -0.30 |
| 13 | 20.812 | 624.4 | lean | swoop of the bike leaning into a turn | Dale leans hard left (word 70 'and') | -15 | +0.00 |
| 14 | 21.875 | 656.3 | whoosh | transition whoosh | transition s06->s07 (track/bike_chase) | -17 | +0.00 |
| 15 | 23.261 | 697.8 | whoosh | transition whoosh | transition s07->s08 (track/track_med) | -17 | +0.00 |
| 16 | 23.938 | 718.1 | sweat_drop | drip blip | fx sweat_drop (s08 word 2) | -16 | +0.10 |
| 17 | 25.688 | 770.6 | boing | spring boing | wiggles his hips (word 85 'wiggles') | -15 | +0.00 |
| 18 | 27.396 | 821.9 | whoosh | transition whoosh | transition s08->s09 (track/track_top) | -17 | +0.00 |
| 19 | 28.806 | 864.2 | tyre_skid | tyre skid squeal | bike runs wide across the track (word 98 'runs') | -15 | +0.00 |
| 20 | 29.328 | 879.8 | dust_puff | dust puff | fx dust_puff (s09 word 7) | -15 | +0.38 |
| 21 | 30.282 | 908.5 | whoosh | transition whoosh | transition s09->s10 (track/pit_med) | -17 | +0.00 |
| 22 | 32.390 | 971.7 | sweat_drop | drip blip | fx sweat_drop (s10 word 9) | -16 | -0.10 |
| 23 | 32.853 | 985.6 | whoosh | transition whoosh | transition s10->s11 (track/rider_close) | -17 | +0.00 |
| 24 | 35.563 | 1066.9 | question_mark | rising two-note pizzicato 'hmm?' | fx question_mark (s11 word 10) | -16 | +0.18 |
| 25 | 35.955 | 1078.6 | whoosh | transition whoosh | transition s11->s12 (track/bike_chase) | -17 | +0.00 |
| 26 | 42.096 | 1262.9 | dust_puff | dust puff | fx dust_puff (s13 word 4) | -15 | +0.07 |
| 27 | 43.822 | 1314.7 | lean | swoop of the bike leaning into a turn | the bike tips left (word 158 'tips') | -15 | +0.00 |
| 28 | 45.334 | 1360.0 | whoosh | transition whoosh | transition s13->s14 (track/pit_ots) | -17 | +0.00 |
| 29 | 48.331 | 1449.9 | speed_lines | fast swish / speed lines | fx speed_lines (s14 word 12) | -16 | +0.10 |
| 30 | 49.148 | 1474.4 | sparkle | glock sparkle run | fx sparkle (s14 word 16) | -15 | -0.12 |
| 31 | 49.529 | 1485.9 | whoosh | transition whoosh | transition s14->s15 (track/track_med) | -17 | +0.00 |
| 32 | 52.914 | 1587.4 | sparkle | glock sparkle run | fx sparkle (s15 word 11) | -15 | +0.12 |
| 33 | 53.631 | 1608.9 | whoosh | transition whoosh | transition s15->s16 (track/pit_med) | -17 | +0.00 |
| 34 | 56.178 | 1685.3 | exclaim | ding | fx exclaim (s16 word 8) | -14 | -0.24 |
| 35 | 57.666 | 1730.0 | whoosh | transition whoosh | transition s16->s17 (village/street_med) | -17 | +0.00 |
| 36 | 57.926 | 1737.8 | freewheel | coasting freewheel ratchet | bicycle coasting in (word 209 'And') | -17 | +0.00 |
| 37 | 58.399 | 1752.0 | bike_bell | bicycle thumb bell, ring-ring | bell on 'bicycles' (word 211 'bicycles') | -14 | +0.30 |
| 38 | 59.172 | 1775.2 | whoosh | transition whoosh | transition s17->s18 (track/pit_med) | -17 | +0.00 |
| bed | 0.000-4.087 | 0.0 | amb_outdoor | ambience for set 'village' | shots on that set | -30.0 (int.) | 0 |
| bed | 4.087-57.866 | 122.6 | amb_road | ambience for set 'track' | shots on that set | -30.0 (int.) | 0 |
| bed | 57.866-59.372 | 1736.0 | amb_outdoor | ambience for set 'village' | shots on that set | -30.0 (int.) | 0 |
| bed | 59.372-64.033 | 1781.2 | amb_road | ambience for set 'track' | shots on that set | -30.0 (int.) | 0 |
