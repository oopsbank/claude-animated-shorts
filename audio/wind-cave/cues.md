# This Cave Has Been Breathing Since 1881: soundtrack cue sheet

All music and SFX are original, synthesized in numpy/scipy (`audio/lib/score.py`, `audio/lib/sfx_x.py`, template `dsp.py` / `instruments.py` / `sfx_gen.py`). Voice: ElevenLabs (see `audio/VOICE.md`), high-passed at 70 Hz and gently compressed (2:1, max 6.7 dB), no EQ colour or pitch change.

## Files
| file | content |
|---|---|
| `mix.wav` | final mix, 48 kHz stereo 24-bit, 3112000 samples = 1945 frames @ 30 fps = 64.833 s |
| `stem_voice.wav` / `stem_music.wav` / `stem_sfx.wav` | stems at mix gain, pre-limiter (their sum + the master limiter = the mix) |
| `length.json` | the picture length the engine must render |

## Master loudness (own BS.1770-4 meter)
- Integrated **-14.0 LUFS** (target -14.0), true peak **-1.2 dBTP** (ceiling -1.2), LRA 1.0 LU
- Stems at mix gain: voice -14.2, music -24.9, sfx -36.4 LUFS; master gain +4.94 dB
- Limiter: max gain reduction 3.08 dB, active (>0.1 dB) on 17.79 % of samples

ffmpeg ebur128 cross-check:
```
Summary:

  Integrated loudness:
    I:         -14.0 LUFS
    Threshold: -24.1 LUFS

  Loudness range:
    LRA:         1.0 LU
    Threshold: -34.0 LUFS
    LRA low:   -14.5 LUFS
    LRA high:  -13.5 LUFS

  True peak:
    Peak:       -1.2 dBFS
```

## Voice pacing (words.json)
- 219 words over 63.95 s = **3.42 words/s** (reference 3.5-4.1, median 3.7)
- gaps > 0.25 s: 1, total 0.25 s (reference < 1 s); longest gap 0.25 s
- first word at 0.060 s (frame 1.8); last word ends 64.011 s

## Voice on top, per section (LUFS at mix gain)
bed = music + sfx. margin = voice - bed (integrated). speech median / p10 = 400 ms momentary voice - bed over spoken words. Reference: bed 5-10 dB under the voice.

| section | time s | voice | music | sfx | bed | margin LU | speech median LU | speech p10 LU |
|---|---|---|---|---|---|---|---|---|
| mystery 0.0 | 0.00-18.80 | -14.1 | -24.6 | -36.3 | -24.3 | 10.2 | 11.1 | 6.4 |
| explain 18.8 | 18.80-34.20 | -14.1 | -24.6 | -38.0 | -24.4 | 10.3 | 11.0 | 7.4 |
| mystery 34.2 | 34.20-36.14 | -13.5 | -26.3 | -41.7 | -26.1 | 12.7 | 12.1 | 10.6 |
| explain 36.1 | 36.14-51.92 | -14.3 | -24.8 | -35.6 | -24.5 | 10.1 | 10.1 | 6.7 |
| payoff 51.9 | 51.92-57.92 | -14.3 | -26.1 | -35.9 | -25.7 | 11.4 | 12.7 | 7.9 |
| mystery 57.9 | 57.92-64.83 | -14.2 | -24.8 | -36.8 | -24.5 | 10.3 | 11.1 | 7.2 |

## Music map (original, G major, 112 bpm)
Music under the voice: -3 dB duck keyed from words.json, section targets (LU vs voice): mystery -10.5, explain -10.5, payoff -11.0. Applied section gains (dB): mystery@0.0s -2.4, explain@18.8s -6.9, mystery@34.2s -1.4, explain@36.1s -7.5, payoff@51.9s -0.0, mystery@57.9s -2.9.

| time s | frame | music |
|---|---|---|
| 0.00 | 0 | mystery/curious: drums out, sus pad vi-IV-ii-Vsus + ticking glock |
| 18.80 | 564 | explain/reveal: light vibes arpeggio IV-I/3-ii-V, bass; soft kick + brushes from bar 2 |
| 34.20 | 1026 | mystery/curious: drums out, sus pad vi-IV-ii-Vsus + ticking glock |
| 36.14 | 1084 | explain/reveal: light vibes arpeggio IV-I/3-ii-V, bass; soft kick + brushes from bar 2 |
| 51.92 | 1558 | payoff: thins to pad + bass so the punchline lands dry |
| 57.92 | 1738 | mystery/curious: drums out, sus pad vi-IV-ii-Vsus + ticking glock |
| 64.13 | 1924 | loop end: no sting; riser into the last frame so the restart lands on the hook |

## SFX events
level = target LU vs the voice stem (max momentary of the event). Beds are integrated.

| # | time s | frame | cue | sound | why | level LU | pan |
|---|---|---|---|---|---|---|---|
| 1 | 0.281 | 8.4 | card_pop | title card pop: paper flick + thump | 1881 title (word 1 '1881,') | -16 | +0.00 |
| 2 | 3.116 | 93.5 | cave_whistle | thin whistle from a hole in the rock | the whistle from the ground (word 9 'whistle') | -14 | +0.00 |
| 3 | 7.576 | 227.3 | cave_breath | the hole breathing: hollow gust + faint whistle | THE HOLE IS BREATHING (exhale) (word 26 'breathing.') | -10 | +0.00 |
| 4 | 7.876 | 236.3 | impact | cartoon impact thump + crack | title slam (word 26 'breathing.') | -15 | +0.00 |
| 5 | 8.372 | 251.2 | cave_breath | the hole breathing: hollow gust + faint whistle | the gust that takes Tom's hat (word 27 'Wind') | -9 | +0.00 |
| 6 | 10.587 | 317.6 | whoosh | transition whoosh | the hat flies off (word 36 'hat') | -15 | +0.00 |
| 7 | 11.047 | 331.4 | whoosh | transition whoosh | transition s03->s04 (earth/None) | -17 | +0.00 |
| 8 | 12.413 | 372.4 | question | rising two-note pizzicato 'hmm?' | imagined tunnel ? (word 42 'tunnel,') | -17 | +0.00 |
| 9 | 14.179 | 425.4 | whoosh | transition whoosh | transition s04->s05 (prairie/None) | -17 | +0.00 |
| 10 | 18.328 | 549.8 | card_pop | title card pop: paper flick + thump | SMALLER THAN A SHEET OF PAPER (word 62 'paper.') | -16 | +0.00 |
| 11 | 18.799 | 564.0 | card_pop | title card pop: paper flick + thump | CLUE 1 (word 63 'Clue') | -16 | +0.00 |
| 12 | 20.154 | 604.6 | cave_breath | the hole breathing: hollow gust + faint whistle | the hole inhales (word 68 'breathed') | -11 | +0.00 |
| 13 | 21.157 | 634.7 | whoosh | transition whoosh | Jesse's hat sucked in (word 71 'sucked') | -14 | +0.00 |
| 14 | 22.828 | 684.8 | card_pop | title card pop: paper flick + thump | CLUE 2 (word 75 'Clue') | -16 | +0.00 |
| 15 | 25.186 | 755.6 | thunder | distant thunder roll | storm side (word 83 'storm,') | -14 | +0.00 |
| 16 | 27.980 | 839.4 | card_pop | title card pop: paper flick + thump | CLUE 3 (word 93 'Clue') | -16 | +0.00 |
| 17 | 31.327 | 939.8 | card_pop | title card pop: paper flick + thump | 260+ KM counter (word 105 'sixty') | -16 | +0.00 |
| 18 | 33.939 | 1018.2 | whoosh | transition whoosh | transition s08->s09 (prairie/None) | -17 | +0.00 |
| 19 | 35.330 | 1059.9 | cave_breath | the hole breathing: hollow gust + faint whistle | the ? rising on the breath (word 121 'breathe?') | -13 | +0.00 |
| 20 | 35.880 | 1076.4 | whoosh | transition whoosh | transition s09->s10 (sky/None) | -17 | +0.00 |
| 21 | 37.022 | 1110.7 | impact | cartoon impact thump + crack | AIR PRESSURE weight (word 127 'heavy.') | -15 | +0.00 |
| 22 | 39.240 | 1177.2 | thunder | distant thunder roll | storm arrives (word 134 'storm') | -13 | +0.00 |
| 23 | 42.429 | 1272.9 | cave_breath | the hole breathing: hollow gust + faint whistle | the cave exhales (word 146 'rushes') | -10 | +0.00 |
| 24 | 43.082 | 1292.5 | whoosh | transition whoosh | transition s11->s12 (sky/None) | -17 | +0.00 |
| 25 | 46.489 | 1394.7 | cave_breath | the hole breathing: hollow gust + faint whistle | the sky pushes air back in (word 160 'back') | -12 | +0.00 |
| 26 | 47.047 | 1411.4 | whoosh | transition whoosh | transition s12->s13 (cave/None) | -17 | +0.00 |
| 27 | 49.451 | 1483.5 | cave_breath | the hole breathing: hollow gust + faint whistle | the whole maze breathes through one hole (word 171 'huge') | -12 | +0.00 |
| 28 | 51.658 | 1549.7 | whoosh | transition whoosh | transition s13->s14 (cabin/None) | -17 | +0.00 |
| 29 | 53.630 | 1608.9 | bag_puff | snack bag puffing tight | chips bag puffs (word 187 'puffing') | -14 | +0.00 |
| 30 | 56.001 | 1680.0 | impact | cartoon impact thump + crack | NOT BREATHING. (word 196 'isn't') | -12 | +0.00 |
| 31 | 57.184 | 1715.5 | impact | cartoon impact thump + crack | THE SKY IS. (word 199 'sky') | -11 | +0.00 |
| 32 | 57.658 | 1729.7 | whoosh | transition whoosh | transition s15->s16 (prairie/None) | -17 | +0.00 |
| 33 | 58.828 | 1764.8 | thunder | distant thunder roll | storm over the hills (word 204 'storm') | -15 | +0.00 |
| 34 | 61.813 | 1854.4 | cave_breath | the hole breathing: hollow gust + faint whistle | the hole breathes out into the loop (word 213 'breathes') | -11 | +0.00 |
| bed | 0.000-11.247 | 0.0 | amb_prairie | ambience for set 'prairie' | shots on that set | -30.0 (int.) | 0 |
| bed | 11.247-14.379 | 337.4 | amb_under | ambience for set 'earth' | shots on that set | -30.0 (int.) | 0 |
| bed | 14.379-22.768 | 431.4 | amb_prairie | ambience for set 'prairie' | shots on that set | -30.0 (int.) | 0 |
| bed | 22.768-27.920 | 683.0 | amb_storm | ambience for set 'storm' | shots on that set | -30.0 (int.) | 0 |
| bed | 27.920-34.139 | 837.6 | amb_cave | ambience for set 'cave' | shots on that set | -30.0 (int.) | 0 |
| bed | 34.139-38.932 | 1024.2 | amb_prairie | ambience for set 'prairie' | shots on that set | -30.0 (int.) | 0 |
| bed | 38.932-43.282 | 1168.0 | amb_storm | ambience for set 'storm' | shots on that set | -30.0 (int.) | 0 |
| bed | 43.282-47.247 | 1298.5 | amb_prairie | ambience for set 'sky' | shots on that set | -30.0 (int.) | 0 |
| bed | 47.247-51.858 | 1417.4 | amb_cave | ambience for set 'cave' | shots on that set | -30.0 (int.) | 0 |
| bed | 51.858-55.533 | 1555.7 | amb_cabin | ambience for set 'cabin' | shots on that set | -30.0 (int.) | 0 |
| bed | 55.533-57.858 | 1666.0 | amb_storm | ambience for set 'storm' | shots on that set | -30.0 (int.) | 0 |
| bed | 57.858-64.833 | 1735.7 | amb_prairie | ambience for set 'prairie' | shots on that set | -30.0 (int.) | 0 |
