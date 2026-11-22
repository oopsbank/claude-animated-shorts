# The Explosion With No Crater: soundtrack cue sheet

All music and SFX are original, synthesized in numpy/scipy (`audio/lib/score.py`, `audio/lib/sfx_x.py`, template `dsp.py` / `instruments.py` / `sfx_gen.py`). Voice: ElevenLabs (see `audio/VOICE.md`), high-passed at 70 Hz and gently compressed (2:1, max 6.8 dB), no EQ colour or pitch change.

## Files
| file | content |
|---|---|
| `mix.wav` | final mix, 48 kHz stereo 24-bit, 3139200 samples = 1962 frames @ 30 fps = 65.400 s |
| `stem_voice.wav` / `stem_music.wav` / `stem_sfx.wav` | stems at mix gain, pre-limiter (their sum + the master limiter = the mix) |
| `length.json` | the picture length the engine must render |

## Master loudness (own BS.1770-4 meter)
- Integrated **-14.0 LUFS** (target -14.0), true peak **-1.2 dBTP** (ceiling -1.2), LRA 1.4 LU
- Stems at mix gain: voice -14.3, music -24.9, sfx -37.3 LUFS; master gain +11.52 dB
- Limiter: max gain reduction 3.45 dB, active (>0.1 dB) on 5.21 % of samples

ffmpeg ebur128 cross-check:
```
Summary:

  Integrated loudness:
    I:         -14.1 LUFS
    Threshold: -24.1 LUFS

  Loudness range:
    LRA:         1.4 LU
    Threshold: -34.1 LUFS
    LRA low:   -14.8 LUFS
    LRA high:  -13.4 LUFS

  True peak:
    Peak:       -1.2 dBFS
```

## Voice pacing (words.json)
- 216 words over 64.79 s = **3.33 words/s** (reference 3.5-4.1, median 3.7)
- gaps > 0.25 s: 1, total 0.30 s (reference < 1 s); longest gap 0.30 s
- first word at 0.024 s (frame 0.7); last word ends 64.810 s

## Voice on top, per section (LUFS at mix gain)
bed = music + sfx. margin = voice - bed (integrated). speech median / p10 = 400 ms momentary voice - bed over spoken words. Reference: bed 5-10 dB under the voice.

| section | time s | voice | music | sfx | bed | margin LU | speech median LU | speech p10 LU |
|---|---|---|---|---|---|---|---|---|
| mystery 0.0 | 0.02-19.97 | -14.2 | -24.7 | -36.3 | -24.4 | 10.2 | 11.1 | 7.0 |
| explain 20.0 | 19.97-31.97 | -15.0 | -25.5 | -39.0 | -25.3 | 10.3 | 11.0 | 6.7 |
| mystery 32.0 | 31.97-38.89 | -14.5 | -25.5 | -37.9 | -25.2 | 10.7 | 12.0 | 7.0 |
| explain 38.9 | 38.89-52.30 | -14.1 | -24.6 | -36.5 | -24.4 | 10.2 | 11.0 | 6.1 |
| payoff 52.3 | 52.30-57.63 | -13.6 | -25.4 | -36.5 | -25.1 | 11.5 | 13.0 | 7.0 |
| mystery 57.6 | 57.63-65.40 | -14.3 | -24.8 | -40.7 | -24.7 | 10.4 | 10.1 | 5.9 |

## Music map (original, G major, 112 bpm)
Music under the voice: -3 dB duck keyed from words.json, section targets (LU vs voice): mystery -10.5, explain -10.5, payoff -11.0. Applied section gains (dB): mystery@0.0s -8.9, explain@20.0s -13.8, mystery@32.0s -9.2, explain@38.9s -13.5, payoff@52.3s -7.0, mystery@57.6s -8.7.

| time s | frame | music |
|---|---|---|
| 0.02 | 1 | mystery/curious: drums out, sus pad vi-IV-ii-Vsus + ticking glock |
| 19.97 | 599 | explain/reveal: light vibes arpeggio IV-I/3-ii-V, bass; soft kick + brushes from bar 2 |
| 31.97 | 959 | mystery/curious: drums out, sus pad vi-IV-ii-Vsus + ticking glock |
| 38.89 | 1167 | explain/reveal: light vibes arpeggio IV-I/3-ii-V, bass; soft kick + brushes from bar 2 |
| 52.30 | 1569 | payoff: thins to pad + bass so the punchline lands dry |
| 57.63 | 1729 | mystery/curious: drums out, sus pad vi-IV-ii-Vsus + ticking glock |
| 64.81 | 1944 | loop end: no sting; riser into the last frame so the restart lands on the hook |

## SFX events
level = target LU vs the voice stem (max momentary of the event). Beds are integrated.

| # | time s | frame | cue | sound | why | level LU | pan |
|---|---|---|---|---|---|---|---|
| 1 | -0.026 | -0.8 | whoosh_fast | fast swish / speed lines | the fireball streaks in (already in frame) (word 0 'In') | -16 | +0.00 |
| 2 | 1.001 | 30.0 | deep_boom | huge distant airburst: sub thump + long rumble | THE BLAST: white flash, fireball, shock ring (word 3 'blast') | -6 | +0.00 |
| 3 | 1.415 | 42.5 | impact | cartoon impact thump + crack | 1,000x HIROSHIMA slams (word 5 'thousand') | -15 | +0.00 |
| 4 | 4.673 | 140.2 | impact | cartoon impact thump + crack | NO CRATER slams (word 14 'no') | -14 | +0.00 |
| 5 | 8.938 | 268.1 | whoosh | transition whoosh | transition s02->s03 (village/None) | -17 | +0.00 |
| 6 | 11.090 | 332.7 | boom | boom + rumble | the shockwave hits the trading post (word 35 'thrown') | -11 | +0.00 |
| 7 | 11.140 | 334.2 | glass_shatter | a window pane bursting | the window bursts (word 35 'thrown') | -14 | +0.00 |
| 8 | 11.647 | 349.4 | puff | dust puff | he lands off the porch (word 38 'porch,') | -15 | +0.00 |
| 9 | 13.602 | 408.1 | card_pop | title card pop: paper flick + thump | 1927 card (word 43 'Nineteen') | -15 | +0.00 |
| 10 | 16.808 | 504.2 | gps_ping | tracker ping: sonar blip + echo | meteorite target (word 53 'meteorite.') | -17 | +0.00 |
| 11 | 19.972 | 599.2 | card_pop | title card pop: paper flick + thump | CLUE 1 badge (word 63 'Clue') | -15 | +0.00 |
| 12 | 20.981 | 629.4 | impact | cartoon impact thump + crack | red X over the crater outline (word 67 'no') | -15 | +0.00 |
| 13 | 23.048 | 691.4 | card_pop | title card pop: paper flick + thump | CLUE 2 badge (word 73 'Clue') | -15 | +0.00 |
| 14 | 25.206 | 756.2 | whoosh | transition whoosh | arrows shoot outward (word 80 'outward,') | -17 | +0.00 |
| 15 | 26.165 | 784.9 | gps_ping | tracker ping: sonar blip + echo | ONE SPOT pin (word 83 'one') | -16 | +0.00 |
| 16 | 26.966 | 809.0 | card_pop | title card pop: paper flick + thump | CLUE 3 badge (word 85 'Clue') | -15 | +0.00 |
| 17 | 30.383 | 911.5 | riser | noise riser ending on the cue time | into the riddle (word 102 'what') | -17 | +0.00 |
| 18 | 32.183 | 965.5 | impact | cartoon impact thump + crack | the big ? slams (word 102 'what') | -14 | +0.00 |
| 19 | 35.269 | 1058.1 | whoosh | transition whoosh | transition s08->s09 (taiga/None) | -17 | +0.00 |
| 20 | 36.191 | 1085.7 | pop | pop | COMET bubble (word 115 'comet,') | -16 | +0.00 |
| 21 | 36.649 | 1099.5 | pop | pop | ANTIMATTER bubble (word 116 'antimatter,') | -16 | +0.00 |
| 22 | 37.980 | 1139.4 | pop | pop | ALIEN SHIP bubble (word 120 'alien') | -16 | +0.00 |
| 23 | 38.631 | 1158.9 | whoosh | transition whoosh | transition s09->s10 (inserts/None) | -17 | +0.00 |
| 24 | 39.008 | 1170.2 | riser | noise riser ending on the cue time | the rock dives and heats (word 132 'burst') | -15 | +0.00 |
| 25 | 41.358 | 1240.7 | deep_boom | huge distant airburst: sub thump + long rumble | the burst 8 km up (word 132 'burst') | -8 | +0.00 |
| 26 | 43.438 | 1303.1 | impact | cartoon impact thump + crack | IT NEVER HIT THE GROUND slams (word 139 'never') | -15 | +0.00 |
| 27 | 44.795 | 1343.9 | boom | boom + rumble | the blast wave hits the trees (word 145 'blast') | -11 | +0.00 |
| 28 | 45.391 | 1361.7 | whoosh | transition whoosh | transition s11->s12a (room/None) | -17 | +0.00 |
| 29 | 47.139 | 1414.2 | whoosh | transition whoosh | arrows straight down (word 153 'straight') | -18 | +0.00 |
| 30 | 48.651 | 1459.5 | whoosh_fast | fast swish / speed lines | branches fly off (word 158 'lost') | -16 | +0.00 |
| 31 | 53.010 | 1590.3 | blower | a hairdryer running | the hairdryer runs (word 174 'pointed') | -19 | +0.00 |
| 32 | 54.941 | 1648.2 | whoosh | transition whoosh | sideways blast (word 180 'it') | -17 | +0.00 |
| 33 | 55.085 | 1652.5 | sparkle | glock sparkle run | STAYS UP (word 181 'stays') | -19 | +0.00 |
| 34 | 55.567 | 1667.0 | puff | dust puff | trees knocked flat (word 182 'up,') | -14 | +0.00 |
| 35 | 57.368 | 1721.0 | whoosh | transition whoosh | transition s13->s14a (taiga/None) | -17 | +0.00 |
| 36 | 62.344 | 1870.3 | riser | noise riser ending on the cue time | tilt up into the opening sky (loop) (word 226 'sky.') | -17 | +0.00 |
| 37 | 63.879 | 1916.4 | impact | cartoon impact thump + crack | NO CRATER slams (loop) (word 212 'pointing') | -14 | +0.00 |
| bed | 0.000-9.138 | 0.0 | amb_taiga | ambience for set 'taiga' | shots on that set | -30.0 (int.) | 0 |
| bed | 9.138-13.542 | 274.1 | amb_outdoor | ambience for set 'village' | shots on that set | -30.0 (int.) | 0 |
| bed | 13.542-22.988 | 406.3 | amb_taiga | ambience for set 'taiga' | shots on that set | -30.0 (int.) | 0 |
| bed | 22.988-26.906 | 689.6 | amb_room | ambience for set 'room' | shots on that set | -30.0 (int.) | 0 |
| bed | 26.906-31.913 | 807.2 | amb_taiga | ambience for set 'taiga' | shots on that set | -30.0 (int.) | 0 |
| bed | 31.913-35.469 | 957.4 | amb_alien | ambience for set 'inserts' | shots on that set | -30.0 (int.) | 0 |
| bed | 35.469-38.831 | 1064.1 | amb_taiga | ambience for set 'taiga' | shots on that set | -30.0 (int.) | 0 |
| bed | 38.831-43.240 | 1164.9 | amb_alien | ambience for set 'inserts' | shots on that set | -30.0 (int.) | 0 |
| bed | 43.240-45.591 | 1297.2 | amb_taiga | ambience for set 'taiga' | shots on that set | -30.0 (int.) | 0 |
| bed | 45.591-57.568 | 1367.7 | amb_room | ambience for set 'room' | shots on that set | -30.0 (int.) | 0 |
| bed | 57.568-65.400 | 1727.0 | amb_taiga | ambience for set 'taiga' | shots on that set | -30.0 (int.) | 0 |
