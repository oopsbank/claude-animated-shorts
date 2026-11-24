# Why Do Moths Fly Into Lights?: soundtrack cue sheet

All music and SFX are original, synthesized in numpy/scipy (`audio/lib/score.py`, `audio/lib/sfx_x.py`, template `dsp.py` / `instruments.py` / `sfx_gen.py`). Voice: ElevenLabs (see `audio/VOICE.md`), high-passed at 70 Hz and gently compressed (2:1, max 5.8 dB), no EQ colour or pitch change.

## Files
| file | content |
|---|---|
| `mix.wav` | final mix, 48 kHz stereo 24-bit, 3064000 samples = 1915 frames @ 30 fps = 63.833 s |
| `stem_voice.wav` / `stem_music.wav` / `stem_sfx.wav` | stems at mix gain, pre-limiter (their sum + the master limiter = the mix) |
| `length.json` | the picture length the engine must render |

## Master loudness (own BS.1770-4 meter)
- Integrated **-14.0 LUFS** (target -14.0), true peak **-1.2 dBTP** (ceiling -1.2), LRA 0.9 LU
- Stems at mix gain: voice -14.2, music -24.9, sfx -40.3 LUFS; master gain +4.68 dB
- Limiter: max gain reduction 2.25 dB, active (>0.1 dB) on 11.70 % of samples

ffmpeg ebur128 cross-check:
```
Summary:

  Integrated loudness:
    I:         -14.0 LUFS
    Threshold: -24.0 LUFS

  Loudness range:
    LRA:         0.9 LU
    Threshold: -34.0 LUFS
    LRA low:   -14.4 LUFS
    LRA high:  -13.5 LUFS

  True peak:
    Peak:       -1.2 dBFS
```

## Voice pacing (words.json)
- 227 words over 62.97 s = **3.60 words/s** (reference 3.5-4.1, median 3.7)
- gaps > 0.25 s: 0, total 0.00 s (reference < 1 s); longest gap 0.24 s
- first word at 0.060 s (frame 1.8); last word ends 63.031 s

## Voice on top, per section (LUFS at mix gain)
bed = music + sfx. margin = voice - bed (integrated). speech median / p10 = 400 ms momentary voice - bed over spoken words. Reference: bed 5-10 dB under the voice.

| section | time s | voice | music | sfx | bed | margin LU | speech median LU | speech p10 LU |
|---|---|---|---|---|---|---|---|---|
| mystery 0.0 | 0.00-19.49 | -14.3 | -24.8 | -40.2 | -24.7 | 10.4 | 11.6 | 6.3 |
| explain 19.5 | 19.49-31.84 | -14.2 | -24.7 | -40.0 | -24.6 | 10.4 | 10.7 | 6.7 |
| mystery 31.8 | 31.84-34.05 | -13.9 | -26.3 | -39.7 | -26.0 | 12.1 | 12.3 | 10.8 |
| explain 34.0 | 34.05-51.02 | -14.0 | -24.5 | -41.1 | -24.4 | 10.4 | 10.8 | 6.9 |
| payoff 51.0 | 51.02-58.76 | -14.2 | -25.7 | -39.9 | -25.5 | 11.3 | 12.9 | 8.0 |
| mystery 58.8 | 58.76-63.83 | -14.4 | -24.9 | -40.5 | -24.8 | 10.4 | 11.9 | 7.3 |

## Music map (original, G major, 112 bpm)
Music under the voice: -3 dB duck keyed from words.json, section targets (LU vs voice): mystery -10.5, explain -10.5, payoff -11.0. Applied section gains (dB): mystery@0.0s -2.4, explain@19.5s -6.7, mystery@31.8s -1.8, explain@34.0s -6.8, payoff@51.0s +0.4, mystery@58.8s -2.4.

| time s | frame | music |
|---|---|---|
| 0.00 | 0 | mystery/curious: drums out, sus pad vi-IV-ii-Vsus + ticking glock |
| 19.49 | 585 | explain/reveal: light vibes arpeggio IV-I/3-ii-V, bass; soft kick + brushes from bar 2 |
| 31.84 | 955 | mystery/curious: drums out, sus pad vi-IV-ii-Vsus + ticking glock |
| 34.05 | 1021 | explain/reveal: light vibes arpeggio IV-I/3-ii-V, bass; soft kick + brushes from bar 2 |
| 51.02 | 1531 | payoff: thins to pad + bass so the punchline lands dry |
| 58.76 | 1763 | mystery/curious: drums out, sus pad vi-IV-ii-Vsus + ticking glock |
| 63.13 | 1894 | loop end: no sting; riser into the last frame so the restart lands on the hook |

## SFX events
level = target LU vs the voice stem (max momentary of the event). Beds are integrated.

| # | time s | frame | cue | sound | why | level LU | pan |
|---|---|---|---|---|---|---|---|
| 1 | -0.240 | -7.2 | lamp_hum | an electric lamp switching on and humming | the UV lamp humming in the night forest (word 0 'In') | -22 | +0.00 |
| 2 | 0.269 | 8.1 | card_pop | title card pop: paper flick + thump | 2024 · COSTA RICA title (word 1 '2024,') | -16 | +0.00 |
| 3 | 2.898 | 86.9 | moth_flutter | a moth fluttering past | moths circle the lamp (word 7 'moths') | -19 | +0.00 |
| 4 | 6.923 | 207.7 | whoosh | transition whoosh | transition s01->s02 (room/None) | -17 | +0.00 |
| 5 | 9.437 | 283.1 | bulb_tick | a moth bumping a glass lamp | a moth taps a lamp (word 27 'lights') | -19 | +0.00 |
| 6 | 12.687 | 380.6 | question | rising two-note pizzicato 'hmm?' | DRAWN TO THE LIGHT? (word 38 'answer:') | -17 | +0.00 |
| 7 | 15.148 | 454.4 | sparkle | glock sparkle run | the Moon (word 49 'Moon.') | -19 | +0.00 |
| 8 | 16.476 | 494.3 | impact | cartoon impact thump + crack | X: they didn't fly at the lamp (word 54 'didn't') | -16 | +0.00 |
| 9 | 17.750 | 532.5 | whoosh | transition whoosh | orbit trail (word 60 'flew') | -18 | +0.00 |
| 10 | 19.494 | 584.8 | card_pop | title card pop: paper flick + thump | CLUE 1 (word 66 'Clue') | -16 | +0.00 |
| 11 | 21.033 | 631.0 | moth_flutter | a moth fluttering past | a moth circling, back to the light (word 72 'kept') | -20 | +0.00 |
| 12 | 23.058 | 691.7 | card_pop | title card pop: paper flick + thump | CLUE 2 (word 79 'Clue') | -16 | +0.00 |
| 13 | 25.250 | 757.5 | whoosh | transition whoosh | the moth flips over (word 87 'flipped') | -17 | +0.00 |
| 14 | 26.414 | 792.4 | dust_puff | dust puff | it drops to the ground (word 91 'fell') | -19 | +0.00 |
| 15 | 27.498 | 824.9 | card_pop | title card pop: paper flick + thump | CLUE 3 (word 95 'Clue') | -16 | +0.00 |
| 16 | 29.128 | 873.8 | sparkle | glock sparkle run | the white sheet glows like a sky (word 101 'glowed') | -19 | +0.00 |
| 17 | 31.977 | 959.3 | question | rising two-note pizzicato 'hmm?' | the riddle (word 112 'why') | -17 | +0.00 |
| 18 | 33.788 | 1013.6 | whoosh | transition whoosh | transition s08->s09 (night/None) | -17 | +0.00 |
| 19 | 36.687 | 1100.6 | sparkle | glock sparkle run | the night sky (word 133 'the') | -20 | +0.00 |
| 20 | 41.949 | 1258.5 | ding | ding | UP arrow (word 154 'up.') | -18 | +0.00 |
| 21 | 44.514 | 1335.4 | whoosh | transition whoosh | the insect tilts toward the lamp (word 163 'tilts') | -18 | +0.00 |
| 22 | 46.231 | 1386.9 | moth_flutter | a moth fluttering past | circling the lamp (word 170 'circling') | -20 | +0.00 |
| 23 | 49.641 | 1489.2 | whoosh | transition whoosh | it rolls over (word 183 'rolls') | -17 | +0.00 |
| 24 | 50.543 | 1516.3 | dust_puff | dust puff | and falls (word 186 'falls.') | -19 | +0.00 |
| 25 | 51.505 | 1545.1 | compass_spin | a compass needle swinging and settling | a compass needle swings to a magnet (word 190 'compass') | -17 | +0.00 |
| 26 | 55.934 | 1678.0 | card_pop | title card pop: paper flick + thump | NOT ATTRACTED. (word 205 'Moths') | -17 | +0.00 |
| 27 | 57.936 | 1738.1 | impact | cartoon impact thump + crack | TRAPPED. (word 212 'trapped') | -15 | +0.00 |
| 28 | 59.237 | 1777.1 | card_pop | title card pop: paper flick + thump | back to 2024 (word 217 '2024,') | -17 | +0.00 |
| 29 | 60.575 | 1817.2 | moth_flutter | a moth fluttering past | moths circling the lamp again (word 221 'the') | -20 | +0.00 |
| bed | 0.000-7.123 | 0.0 | amb_nightforest | ambience for set 'cloudforest' | shots on that set | -30.0 (int.) | 0 |
| bed | 7.123-12.217 | 213.7 | amb_room | ambience for set 'room' | shots on that set | -30.0 (int.) | 0 |
| bed | 12.217-15.503 | 366.5 | amb_night | ambience for set 'night' | shots on that set | -30.0 (int.) | 0 |
| bed | 15.503-33.988 | 465.1 | amb_nightforest | ambience for set 'cloudforest' | shots on that set | -30.0 (int.) | 0 |
| bed | 33.988-50.960 | 1019.6 | amb_night | ambience for set 'night' | shots on that set | -30.0 (int.) | 0 |
| bed | 50.960-55.874 | 1528.8 | amb_room | ambience for set 'room' | shots on that set | -30.0 (int.) | 0 |
| bed | 55.874-63.833 | 1676.2 | amb_nightforest | ambience for set 'cloudforest' | shots on that set | -30.0 (int.) | 0 |
