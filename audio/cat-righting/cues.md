# Why Do Cats Always Land on Their Feet?: soundtrack cue sheet

All music and SFX are original, synthesized in numpy/scipy (`audio/lib/score.py`, `audio/lib/sfx_x.py`, template `dsp.py` / `instruments.py` / `sfx_gen.py`). Voice: ElevenLabs (see `audio/VOICE.md`), high-passed at 70 Hz and gently compressed (2:1, max 6.3 dB), no EQ colour or pitch change.

## Files
| file | content |
|---|---|
| `mix.wav` | final mix, 48 kHz stereo 24-bit, 3132800 samples = 1958 frames @ 30 fps = 65.267 s |
| `stem_voice.wav` / `stem_music.wav` / `stem_sfx.wav` | stems at mix gain, pre-limiter (their sum + the master limiter = the mix) |
| `length.json` | the picture length the engine must render |

## Master loudness (own BS.1770-4 meter)
- Integrated **-14.0 LUFS** (target -14.0), true peak **-1.2 dBTP** (ceiling -1.2), LRA 0.9 LU
- Stems at mix gain: voice -14.2, music -24.8, sfx -39.1 LUFS; master gain +4.83 dB
- Limiter: max gain reduction 2.06 dB, active (>0.1 dB) on 18.32 % of samples

ffmpeg ebur128 cross-check:
```
Summary:

  Integrated loudness:
    I:         -14.0 LUFS
    Threshold: -24.1 LUFS

  Loudness range:
    LRA:         0.9 LU
    Threshold: -34.0 LUFS
    LRA low:   -14.5 LUFS
    LRA high:  -13.6 LUFS

  True peak:
    Peak:       -1.2 dBFS
```

## Voice pacing (words.json)
- 224 words over 64.38 s = **3.48 words/s** (reference 3.5-4.1, median 3.7)
- gaps > 0.25 s: 0, total 0.00 s (reference < 1 s); longest gap 0.24 s
- first word at 0.060 s (frame 1.8); last word ends 64.435 s

## Voice on top, per section (LUFS at mix gain)
bed = music + sfx. margin = voice - bed (integrated). speech median / p10 = 400 ms momentary voice - bed over spoken words. Reference: bed 5-10 dB under the voice.

| section | time s | voice | music | sfx | bed | margin LU | speech median LU | speech p10 LU |
|---|---|---|---|---|---|---|---|---|
| mystery 0.0 | 0.00-20.55 | -14.2 | -24.7 | -38.6 | -24.5 | 10.3 | 11.2 | 6.9 |
| explain 20.6 | 20.55-32.18 | -14.2 | -24.7 | -39.1 | -24.6 | 10.3 | 11.4 | 7.0 |
| mystery 32.2 | 32.18-34.40 | -13.8 | -26.2 | -38.8 | -26.0 | 12.2 | 12.2 | 9.3 |
| explain 34.4 | 34.40-53.59 | -14.1 | -24.6 | -41.2 | -24.5 | 10.4 | 10.7 | 7.3 |
| payoff 53.6 | 53.59-59.74 | -14.2 | -25.8 | -38.6 | -25.6 | 11.4 | 13.2 | 8.3 |
| mystery 59.7 | 59.74-65.27 | -14.3 | -24.8 | -38.0 | -24.6 | 10.3 | 11.6 | 5.0 |

## Music map (original, G major, 112 bpm)
Music under the voice: -3 dB duck keyed from words.json, section targets (LU vs voice): mystery -10.5, explain -10.5, payoff -11.0. Applied section gains (dB): mystery@0.0s -2.2, explain@20.6s -7.0, mystery@32.2s -1.3, explain@34.4s -6.8, payoff@53.6s +0.2, mystery@59.7s -2.4.

| time s | frame | music |
|---|---|---|
| 0.00 | 0 | mystery/curious: drums out, sus pad vi-IV-ii-Vsus + ticking glock |
| 20.55 | 617 | explain/reveal: light vibes arpeggio IV-I/3-ii-V, bass; soft kick + brushes from bar 2 |
| 32.18 | 965 | mystery/curious: drums out, sus pad vi-IV-ii-Vsus + ticking glock |
| 34.40 | 1032 | explain/reveal: light vibes arpeggio IV-I/3-ii-V, bass; soft kick + brushes from bar 2 |
| 53.59 | 1608 | payoff: thins to pad + bass so the punchline lands dry |
| 59.74 | 1792 | mystery/curious: drums out, sus pad vi-IV-ii-Vsus + ticking glock |
| 64.57 | 1937 | loop end: no sting; riser into the last frame so the restart lands on the hook |

## SFX events
level = target LU vs the voice stem (max momentary of the event). Beds are integrated.

| # | time s | frame | cue | sound | why | level LU | pan |
|---|---|---|---|---|---|---|---|
| 1 | 0.300 | 9.0 | card_pop | title card pop: paper flick + thump | 1894 title (word 1 '1894,') | -16 | +0.00 |
| 2 | 3.354 | 100.6 | film_clatter | 1894 chronophotograph camera ticking | the 1894 camera ticks (word 10 'filmed') | -16 | +0.00 |
| 3 | 6.988 | 209.6 | whoosh | transition whoosh | the cat twists over (word 21 'flipped') | -14 | +0.00 |
| 4 | 8.487 | 254.6 | paw_land | cat paws land softly | lands on its feet (word 27 'feet.') | -11 | +0.00 |
| 5 | 10.296 | 308.9 | impact | cartoon impact thump + crack | BROKE PHYSICS? slam (word 36 'physics.') | -14 | +0.00 |
| 6 | 14.512 | 435.4 | question | rising two-note pizzicato 'hmm?' | pushed off the hands? (word 51 'pushed') | -17 | +0.00 |
| 7 | 16.403 | 492.1 | film_clatter | 1894 chronophotograph camera ticking | the film strip (word 58 'photos') | -17 | +0.00 |
| 8 | 19.987 | 599.6 | impact | cartoon impact thump + crack | X on the hand theory / turn began in mid-air (word 70 'mid-air.') | -15 | +0.00 |
| 9 | 20.553 | 616.6 | card_pop | title card pop: paper flick + thump | CLUE 1 (word 71 'Clue') | -16 | +0.00 |
| 10 | 22.762 | 682.9 | paw_land | cat paws land softly | tailless cat lands (word 80 'too.') | -13 | +0.00 |
| 11 | 23.215 | 696.5 | card_pop | title card pop: paper flick + thump | CLUE 2 (word 81 'Clue') | -16 | +0.00 |
| 12 | 25.286 | 758.6 | sparkle | glock sparkle run | the bend glows (word 89 'bent') | -17 | +0.00 |
| 13 | 26.301 | 789.0 | card_pop | title card pop: paper flick + thump | CLUE 3 (word 93 'Clue') | -16 | +0.00 |
| 14 | 29.674 | 890.2 | boing | spring boing | trampoline bounce (soft) (word 101 'gymnast') | -20 | +0.00 |
| 15 | 31.921 | 957.6 | whoosh | transition whoosh | transition s09->s10 (lab/None) | -17 | +0.00 |
| 16 | 32.794 | 983.8 | question | rising two-note pizzicato 'hmm?' | the riddle (word 112 'turn') | -16 | +0.00 |
| 17 | 36.668 | 1100.0 | glow_eyes | glock sparkle run | the cat splits into two glowing halves (word 127 'halves,') | -17 | +0.00 |
| 18 | 42.661 | 1279.8 | whoosh | transition whoosh | the front half turns (word 150 'turns') | -15 | +0.00 |
| 19 | 48.717 | 1461.5 | whoosh | transition whoosh | the back half catches up (word 171 'catches') | -15 | +0.00 |
| 20 | 53.030 | 1590.9 | ding | ding | twists cancel; flipped (word 187 'flipped.') | -16 | +0.00 |
| 21 | 54.204 | 1626.1 | whoosh | transition whoosh | office chair spins (word 191 'spinning') | -17 | +0.00 |
| 22 | 57.074 | 1712.2 | whoosh | transition whoosh | transition s16->s17 (lab/None) | -17 | +0.00 |
| 23 | 59.022 | 1770.7 | impact | cartoon impact thump + crack | IT USED IT slam (word 208 'used') | -13 | +0.00 |
| 24 | 59.479 | 1784.4 | whoosh | transition whoosh | transition s17->s18 (room/None) | -17 | +0.00 |
| 25 | 61.088 | 1832.6 | paw_land | cat paws land softly | a cat lands today (word 214 'lands') | -12 | +0.00 |
| 26 | 63.096 | 1892.9 | film_clatter | 1894 chronophotograph camera ticking | back to the 1894 film: loop (word 221 'Paris,') | -17 | +0.00 |
| bed | 0.000-65.267 | 0.0 | amb_room | ambience for set 'lab' | shots on that set | -30.0 (int.) | 0 |
