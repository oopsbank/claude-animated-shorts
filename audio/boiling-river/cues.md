# The River That Boils With No Volcano: soundtrack cue sheet

All music and SFX are original, synthesized in numpy/scipy (`audio/lib/score.py`, `audio/lib/sfx_x.py`, template `dsp.py` / `instruments.py` / `sfx_gen.py`). Voice: ElevenLabs (see `audio/VOICE.md`), high-passed at 70 Hz and gently compressed (2:1, max 6.3 dB), no EQ colour or pitch change.

## Files
| file | content |
|---|---|
| `mix.wav` | final mix, 48 kHz stereo 24-bit, 3113600 samples = 1946 frames @ 30 fps = 64.867 s |
| `stem_voice.wav` / `stem_music.wav` / `stem_sfx.wav` | stems at mix gain, pre-limiter (their sum + the master limiter = the mix) |
| `length.json` | the picture length the engine must render |

## Master loudness (own BS.1770-4 meter)
- Integrated **-14.0 LUFS** (target -14.0), true peak **-1.2 dBTP** (ceiling -1.2), LRA 0.8 LU
- Stems at mix gain: voice -14.2, music -24.9, sfx -37.8 LUFS; master gain +4.86 dB
- Limiter: max gain reduction 2.45 dB, active (>0.1 dB) on 13.38 % of samples

ffmpeg ebur128 cross-check:
```
Summary:

  Integrated loudness:
    I:         -14.0 LUFS
    Threshold: -24.1 LUFS

  Loudness range:
    LRA:         0.8 LU
    Threshold: -34.0 LUFS
    LRA low:   -14.4 LUFS
    LRA high:  -13.6 LUFS

  True peak:
    Peak:       -1.2 dBFS
```

## Voice pacing (words.json)
- 217 words over 63.98 s = **3.39 words/s** (reference 3.5-4.1, median 3.7)
- gaps > 0.25 s: 2, total 0.52 s (reference < 1 s); longest gap 0.26 s
- first word at 0.060 s (frame 1.8); last word ends 64.044 s

## Voice on top, per section (LUFS at mix gain)
bed = music + sfx. margin = voice - bed (integrated). speech median / p10 = 400 ms momentary voice - bed over spoken words. Reference: bed 5-10 dB under the voice.

| section | time s | voice | music | sfx | bed | margin LU | speech median LU | speech p10 LU |
|---|---|---|---|---|---|---|---|---|
| mystery 0.0 | 0.00-19.84 | -14.2 | -24.7 | -36.2 | -24.4 | 10.2 | 11.2 | 5.8 |
| explain 19.8 | 19.84-33.24 | -14.2 | -24.7 | -40.6 | -24.6 | 10.4 | 11.1 | 7.0 |
| mystery 33.2 | 33.24-36.22 | -14.1 | -25.5 | -40.3 | -25.3 | 11.3 | 11.4 | 8.5 |
| explain 36.2 | 36.22-49.11 | -14.3 | -24.8 | -38.9 | -24.6 | 10.3 | 9.9 | 7.6 |
| payoff 49.1 | 49.11-59.18 | -14.2 | -25.6 | -38.3 | -25.3 | 11.1 | 12.7 | 6.9 |
| mystery 59.2 | 59.18-64.87 | -14.1 | -24.6 | -37.5 | -24.4 | 10.3 | 11.1 | 4.5 |

## Music map (original, G major, 112 bpm)
Music under the voice: -3 dB duck keyed from words.json, section targets (LU vs voice): mystery -10.5, explain -10.5, payoff -11.0. Applied section gains (dB): mystery@0.0s -2.4, explain@19.8s -7.1, mystery@33.2s -3.2, explain@36.2s -7.4, payoff@49.1s +0.3, mystery@59.2s -2.7.

| time s | frame | music |
|---|---|---|
| 0.00 | 0 | mystery/curious: drums out, sus pad vi-IV-ii-Vsus + ticking glock |
| 19.84 | 595 | explain/reveal: light vibes arpeggio IV-I/3-ii-V, bass; soft kick + brushes from bar 2 |
| 33.24 | 997 | mystery/curious: drums out, sus pad vi-IV-ii-Vsus + ticking glock |
| 36.22 | 1086 | explain/reveal: light vibes arpeggio IV-I/3-ii-V, bass; soft kick + brushes from bar 2 |
| 49.11 | 1473 | payoff: thins to pad + bass so the punchline lands dry |
| 59.18 | 1775 | mystery/curious: drums out, sus pad vi-IV-ii-Vsus + ticking glock |
| 64.17 | 1925 | loop end: no sting; riser into the last frame so the restart lands on the hook |

## SFX events
level = target LU vs the voice stem (max momentary of the event). Beds are integrated.

| # | time s | frame | cue | sound | why | level LU | pan |
|---|---|---|---|---|---|---|---|
| 1 | 0.010 | 0.3 | boil | a river at the boil: bubbles, churn, steam hiss | the river boiling under the opening (sounding at frame 0) (word 0 'Deep') | -9 | +0.00 |
| 2 | 1.480 | 44.4 | impact | cartoon impact thump + crack | THIS RIVER BOILS slams ('river') (word 6 'river') | -15 | +0.00 |
| 3 | 3.099 | 93.0 | splash | splash | the frog drops toward the water ('fall') - cut before contact (word 12 'fall') | -17 | +0.00 |
| 4 | 4.282 | 128.5 | whoosh | transition whoosh | transition s01->s02 (room/None) | -17 | +0.00 |
| 5 | 6.112 | 183.4 | card_pop | title card pop: paper flick + thump | LEGEND stamp (word 23 'legend.') | -16 | +0.00 |
| 6 | 9.891 | 296.7 | riser | noise riser ending on the cue time | thermometer climbing ('thermometer') (word 38 'thermometer.') | -17 | +0.00 |
| 7 | 12.503 | 375.1 | impact | cartoon impact thump + crack | ~100°C ('hundred') (word 41 'hundred') | -14 | +0.00 |
| 8 | 14.760 | 442.8 | deep_boom | huge distant airburst: sub thump + long rumble | the imagined volcano under the river ('volcano') (word 47 'volcano') | -14 | +0.00 |
| 9 | 15.795 | 473.9 | whoosh | transition whoosh | transition s04->s05 (lab/None) | -17 | +0.00 |
| 10 | 18.131 | 543.9 | card_pop | title card pop: paper flick + thump | 700 KM ruler ('seven') (word 56 'seven') | -15 | +0.00 |
| 11 | 19.368 | 581.0 | impact | cartoon impact thump + crack | the volcano breaks, ✗ ('away.') (word 59 'away.') | -15 | +0.00 |
| 12 | 19.843 | 595.3 | card_pop | title card pop: paper flick + thump | CLUE 1 (word 60 'Clue') | -16 | +0.00 |
| 13 | 25.007 | 750.2 | card_pop | title card pop: paper flick + thump | CLUE 2 (word 77 'Clue') | -16 | +0.00 |
| 14 | 26.962 | 808.9 | steam_hiss | steam venting from a crack | heat pours through the cracks ('cracks,') (word 84 'cracks,') | -15 | +0.00 |
| 15 | 29.635 | 889.1 | card_pop | title card pop: paper flick + thump | CLUE 3 (word 94 'Clue') | -16 | +0.00 |
| 16 | 32.977 | 989.3 | whoosh | transition whoosh | transition s08->s09 (river/None) | -17 | +0.00 |
| 17 | 34.561 | 1036.8 | question | rising two-note pizzicato 'hmm?' | the big ? ('hot,') (word 112 'hot,') | -17 | +0.00 |
| 18 | 35.956 | 1078.7 | whoosh | transition whoosh | transition s09->s10 (earth/None) | -17 | +0.00 |
| 19 | 37.391 | 1121.7 | impact | cartoon impact thump + crack | THE EARTH IS THE STOVE ('stove.') (word 122 'stove.') | -14 | +0.00 |
| 20 | 41.235 | 1237.0 | rain | rain on a shallow pond | rain on the far mountains (word 135 'Rain') | -17 | +0.00 |
| 21 | 46.862 | 1405.9 | steam_hiss | steam venting from a crack | hot water bursts up through the cracks ('up') (word 156 'up') | -14 | +0.00 |
| 22 | 47.933 | 1438.0 | boil | a river at the boil: bubbles, churn, steam hiss | the river bubbles ('straight into the river') (word 160 'straight') | -13 | +0.00 |
| 23 | 48.849 | 1465.5 | whoosh | transition whoosh | transition s12->s13 (interior/None) | -17 | +0.00 |
| 24 | 53.341 | 1600.2 | steam_hiss | steam venting from a crack | coffee machine steam ('steaming.') (word 179 'steaming.') | -16 | +0.00 |
| 25 | 53.751 | 1612.5 | whoosh | transition whoosh | hot plate zooms out to the planet core (word 180 'Here,') | -16 | +0.00 |
| 26 | 55.526 | 1665.8 | whoosh | transition whoosh | transition s14->s15 (river/None) | -17 | +0.00 |
| 27 | 56.663 | 1699.9 | card_pop | title card pop: paper flick + thump | BIGGEST label ('known') (word 190 'known') | -16 | +0.00 |
| 28 | 62.351 | 1870.5 | boil | a river at the boil: bubbles, churn, steam hiss | steam thickens into the loop ('jungle,') (word 211 'jungle,') | -12 | +0.00 |
| bed | 0.000-4.482 | 0.0 | amb_river | ambience for set 'river' | shots on that set | -30.0 (int.) | 0 |
| bed | 4.482-6.561 | 134.5 | amb_room | ambience for set 'room' | shots on that set | -30.0 (int.) | 0 |
| bed | 6.561-15.995 | 196.8 | amb_river | ambience for set 'river' | shots on that set | -30.0 (int.) | 0 |
| bed | 15.995-19.783 | 479.8 | amb_room | ambience for set 'lab' | shots on that set | -30.0 (int.) | 0 |
| bed | 19.783-24.947 | 593.5 | amb_river | ambience for set 'river' | shots on that set | -30.0 (int.) | 0 |
| bed | 24.947-29.575 | 748.4 | amb_under | ambience for set 'earth' | shots on that set | -30.0 (int.) | 0 |
| bed | 29.575-33.177 | 887.3 | amb_room | ambience for set 'lab' | shots on that set | -30.0 (int.) | 0 |
| bed | 33.177-36.156 | 995.3 | amb_river | ambience for set 'river' | shots on that set | -30.0 (int.) | 0 |
| bed | 36.156-49.049 | 1084.7 | amb_under | ambience for set 'earth' | shots on that set | -30.0 (int.) | 0 |
| bed | 49.049-53.891 | 1471.5 | amb_room | ambience for set 'interior' | shots on that set | -30.0 (int.) | 0 |
| bed | 53.891-55.726 | 1616.7 | amb_under | ambience for set 'earth' | shots on that set | -30.0 (int.) | 0 |
| bed | 55.726-64.867 | 1671.8 | amb_river | ambience for set 'river' | shots on that set | -30.0 (int.) | 0 |
