# Why Do Zebras Have Stripes?: soundtrack cue sheet

All music and SFX are original, synthesized in numpy/scipy (`audio/lib/score.py`, `audio/lib/sfx_x.py`, template `dsp.py` / `instruments.py` / `sfx_gen.py`). Voice: ElevenLabs (see `audio/VOICE.md`), high-passed at 70 Hz and gently compressed (2:1, max 6.3 dB), no EQ colour or pitch change.

## Files
| file | content |
|---|---|
| `mix.wav` | final mix, 48 kHz stereo 24-bit, 3121600 samples = 1951 frames @ 30 fps = 65.033 s |
| `stem_voice.wav` / `stem_music.wav` / `stem_sfx.wav` | stems at mix gain, pre-limiter (their sum + the master limiter = the mix) |
| `length.json` | the picture length the engine must render |

## Master loudness (own BS.1770-4 meter)
- Integrated **-14.0 LUFS** (target -14.0), true peak **-1.2 dBTP** (ceiling -1.2), LRA 0.8 LU
- Stems at mix gain: voice -14.2, music -24.9, sfx -39.9 LUFS; master gain +4.80 dB
- Limiter: max gain reduction 3.44 dB, active (>0.1 dB) on 15.39 % of samples

ffmpeg ebur128 cross-check:
```
Summary:

  Integrated loudness:
    I:         -14.0 LUFS
    Threshold: -24.0 LUFS

  Loudness range:
    LRA:         0.8 LU
    Threshold: -34.0 LUFS
    LRA low:   -14.4 LUFS
    LRA high:  -13.6 LUFS

  True peak:
    Peak:       -1.2 dBFS
```

## Voice pacing (words.json)
- 210 words over 64.16 s = **3.27 words/s** (reference 3.5-4.1, median 3.7)
- gaps > 0.25 s: 0, total 0.00 s (reference < 1 s); longest gap 0.24 s
- first word at 0.060 s (frame 1.8); last word ends 64.221 s

## Voice on top, per section (LUFS at mix gain)
bed = music + sfx. margin = voice - bed (integrated). speech median / p10 = 400 ms momentary voice - bed over spoken words. Reference: bed 5-10 dB under the voice.

| section | time s | voice | music | sfx | bed | margin LU | speech median LU | speech p10 LU |
|---|---|---|---|---|---|---|---|---|
| mystery 0.0 | 0.00-21.74 | -14.2 | -24.7 | -40.3 | -24.6 | 10.4 | 11.4 | 6.3 |
| explain 21.7 | 21.74-35.62 | -14.3 | -24.8 | -41.2 | -24.7 | 10.4 | 11.3 | 6.6 |
| mystery 35.6 | 35.62-37.36 | -13.8 | -26.7 | -38.8 | -26.5 | 12.7 | 13.0 | 11.1 |
| explain 37.4 | 37.36-50.04 | -14.1 | -24.6 | -39.5 | -24.5 | 10.3 | 10.8 | 7.4 |
| payoff 50.0 | 50.04-60.38 | -14.0 | -25.5 | -38.7 | -25.3 | 11.2 | 13.5 | 6.5 |
| mystery 60.4 | 60.38-65.03 | -14.4 | -24.9 | -41.3 | -24.8 | 10.4 | 12.2 | 3.6 |

## Music map (original, G major, 112 bpm)
Music under the voice: -3 dB duck keyed from words.json, section targets (LU vs voice): mystery -10.5, explain -10.5, payoff -11.0. Applied section gains (dB): mystery@0.0s -2.2, explain@21.7s -7.2, mystery@35.6s -1.8, explain@37.4s -7.1, payoff@50.0s +0.7, mystery@60.4s -2.9.

| time s | frame | music |
|---|---|---|
| 0.00 | 0 | mystery/curious: drums out, sus pad vi-IV-ii-Vsus + ticking glock |
| 21.74 | 652 | explain/reveal: light vibes arpeggio IV-I/3-ii-V, bass; soft kick + brushes from bar 2 |
| 35.62 | 1069 | mystery/curious: drums out, sus pad vi-IV-ii-Vsus + ticking glock |
| 37.36 | 1121 | explain/reveal: light vibes arpeggio IV-I/3-ii-V, bass; soft kick + brushes from bar 2 |
| 50.04 | 1501 | payoff: thins to pad + bass so the punchline lands dry |
| 60.38 | 1811 | mystery/curious: drums out, sus pad vi-IV-ii-Vsus + ticking glock |
| 64.33 | 1930 | loop end: no sting; riser into the last frame so the restart lands on the hook |

## SFX events
level = target LU vs the voice stem (max momentary of the event). Beds are integrated.

| # | time s | frame | cue | sound | why | level LU | pan |
|---|---|---|---|---|---|---|---|
| 1 | 0.287 | 8.6 | card_pop | title card pop: paper flick + thump | 2016 · ENGLAND title (word 1 '2016,') | -16 | +0.00 |
| 2 | 5.244 | 157.3 | fly_buzz | a horse fly passing | flies circle the striped horse (word 14 'flies.') | -17 | +0.00 |
| 3 | 5.819 | 174.6 | whoosh | transition whoosh | transition s01->s02 (savanna/None) | -17 | +0.00 |
| 4 | 8.042 | 241.3 | question | rising two-note pizzicato 'hmm?' | why stripes? (word 22 'stripes') | -17 | +0.00 |
| 5 | 10.019 | 300.6 | question | rising two-note pizzicato 'hmm?' | CAMOUFLAGE? (word 28 'camouflage,') | -17 | +0.00 |
| 6 | 14.312 | 429.4 | impact | cartoon impact thump + crack | X: lions spot zebras (word 40 'easily.') | -15 | +0.00 |
| 7 | 16.875 | 506.2 | whoosh | transition whoosh | stripes blur to grey at 50 m (word 49 'stripes.') | -17 | +0.00 |
| 8 | 21.327 | 639.8 | impact | cartoon impact thump + crack | X: barrels just as hot (word 64 'hot.') | -15 | +0.00 |
| 9 | 21.741 | 652.2 | card_pop | title card pop: paper flick + thump | CLUE 1 (word 65 'Clue') | -16 | +0.00 |
| 10 | 25.608 | 768.2 | card_pop | title card pop: paper flick + thump | CLUE 2 (word 77 'Clue') | -16 | +0.00 |
| 11 | 26.457 | 793.7 | fly_buzz | a horse fly passing | horse fly close-up (word 80 'flies') | -17 | +0.00 |
| 12 | 30.780 | 923.4 | card_pop | title card pop: paper flick + thump | CLUE 3 (word 94 'Clue') | -16 | +0.00 |
| 13 | 34.818 | 1044.5 | fly_buzz | a horse fly passing | flies on the bare head (word 108 'heads.') | -18 | +0.00 |
| 14 | 36.951 | 1108.5 | question | rising two-note pizzicato 'hmm?' | the riddle (word 116 'fly?') | -16 | +0.00 |
| 15 | 38.310 | 1149.3 | fly_buzz | a horse fly passing | fly comes in fast (word 122 'fast,') | -15 | +0.00 |
| 16 | 42.689 | 1280.7 | fly_buzz | a horse fly passing | brakes and lands (word 139 'touches') | -18 | +0.00 |
| 17 | 45.682 | 1370.5 | fly_bonk | a fly bumping into a striped coat | bonk into the coat (word 148 'bumps') | -13 | +0.00 |
| 18 | 46.727 | 1401.8 | whoosh | transition whoosh | zooms past (word 153 'zooms') | -17 | +0.00 |
| 19 | 48.044 | 1441.3 | sparkle | glock sparkle run | compound-eye scramble (word 157 'scramble') | -18 | +0.00 |
| 20 | 52.036 | 1561.1 | card_pop | title card pop: paper flick + thump | painted cow (word 171 'cows.') | -16 | +0.00 |
| 21 | 53.841 | 1615.2 | whoosh | transition whoosh | striped stairs (word 176 'stairs') | -18 | +0.00 |
| 22 | 56.737 | 1702.1 | whoosh | transition whoosh | transition s15->s16 (savanna/None) | -17 | +0.00 |
| 23 | 58.295 | 1748.9 | impact | cartoon impact thump + crack | NOT HIDING THE ZEBRA slam (word 193 'zebra.') | -14 | +0.00 |
| 24 | 59.588 | 1787.6 | impact | cartoon impact thump + crack | HIDING THE LANDING slam (word 197 'landing') | -13 | +0.00 |
| 25 | 60.120 | 1803.6 | whoosh | transition whoosh | transition s16->s17 (farm/None) | -17 | +0.00 |
| 26 | 62.790 | 1883.7 | fly_buzz | a horse fly passing | loop: flies keep missing (word 207 'flies') | -17 | +0.00 |
| bed | 0.000-6.019 | 0.0 | amb_outdoor | ambience for set 'farm' | shots on that set | -30.0 (int.) | 0 |
| bed | 6.019-21.681 | 180.6 | amb_savanna | ambience for set 'savanna' | shots on that set | -30.0 (int.) | 0 |
| bed | 21.681-25.548 | 650.4 | amb_room | ambience for set 'room' | shots on that set | -30.0 (int.) | 0 |
| bed | 25.548-30.720 | 766.4 | amb_savanna | ambience for set 'savanna' | shots on that set | -30.0 (int.) | 0 |
| bed | 30.720-53.667 | 921.6 | amb_outdoor | ambience for set 'farm' | shots on that set | -30.0 (int.) | 0 |
| bed | 53.667-56.937 | 1610.0 | amb_room | ambience for set 'room' | shots on that set | -30.0 (int.) | 0 |
| bed | 56.937-60.320 | 1708.1 | amb_savanna | ambience for set 'savanna' | shots on that set | -30.0 (int.) | 0 |
| bed | 60.320-65.033 | 1809.6 | amb_outdoor | ambience for set 'farm' | shots on that set | -30.0 (int.) | 0 |
