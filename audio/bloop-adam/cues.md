# The Sound From the Deep: soundtrack cue sheet

All music and SFX are original, synthesized in numpy/scipy (`audio/lib/score.py`, `audio/lib/sfx_x.py`, template `dsp.py` / `instruments.py` / `sfx_gen.py`). Voice: ElevenLabs (see `audio/VOICE.md`), high-passed at 70 Hz and gently compressed (2:1, max 6.2 dB), no EQ colour or pitch change.

## Files
| file | content |
|---|---|
| `mix.wav` | final mix, 48 kHz stereo 24-bit, 3148800 samples = 1968 frames @ 30 fps = 65.600 s |
| `stem_voice.wav` / `stem_music.wav` / `stem_sfx.wav` | stems at mix gain, pre-limiter (their sum + the master limiter = the mix) |
| `length.json` | the picture length the engine must render |

## Master loudness (own BS.1770-4 meter)
- Integrated **-14.0 LUFS** (target -14.0), true peak **-1.2 dBTP** (ceiling -1.2), LRA 0.9 LU
- Stems at mix gain: voice -14.2, music -24.8, sfx -34.3 LUFS; master gain +4.88 dB
- Limiter: max gain reduction 3.19 dB, active (>0.1 dB) on 17.48 % of samples

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
    LRA high:  -13.5 LUFS

  True peak:
    Peak:       -1.2 dBFS
```

## Voice pacing (words.json)
- 216 words over 64.97 s = **3.32 words/s** (reference 3.5-4.1, median 3.7)
- gaps > 0.25 s: 0, total 0.00 s (reference < 1 s); longest gap 0.25 s
- first word at 0.060 s (frame 1.8); last word ends 65.025 s

## Voice on top, per section (LUFS at mix gain)
bed = music + sfx. margin = voice - bed (integrated). speech median / p10 = 400 ms momentary voice - bed over spoken words. Reference: bed 5-10 dB under the voice.

| section | time s | voice | music | sfx | bed | margin LU | speech median LU | speech p10 LU |
|---|---|---|---|---|---|---|---|---|
| mystery 0.0 | 0.00-20.45 | -14.2 | -24.7 | -34.0 | -24.3 | 10.1 | 11.3 | 6.7 |
| explain 20.4 | 20.45-35.40 | -14.2 | -24.7 | -38.8 | -24.5 | 10.3 | 11.1 | 6.2 |
| mystery 35.4 | 35.40-40.90 | -13.8 | -24.9 | -32.3 | -24.2 | 10.4 | 11.3 | 6.9 |
| explain 40.9 | 40.90-50.53 | -14.3 | -24.8 | -32.6 | -24.1 | 9.9 | 10.6 | 6.3 |
| payoff 50.5 | 50.53-58.40 | -14.0 | -25.5 | -34.2 | -24.9 | 10.9 | 12.1 | 7.7 |
| mystery 58.4 | 58.40-65.60 | -14.2 | -24.7 | -34.2 | -24.2 | 10.0 | 10.1 | 5.6 |

## Music map (original, G major, 112 bpm)
Music under the voice: -3 dB duck keyed from words.json, section targets (LU vs voice): mystery -10.5, explain -10.5, payoff -11.0. Applied section gains (dB): mystery@0.0s -2.6, explain@20.4s -6.9, mystery@35.4s -1.8, explain@40.9s -7.9, payoff@50.5s +0.2, mystery@58.4s -2.2.

| time s | frame | music |
|---|---|---|
| 0.00 | 0 | mystery/curious: drums out, sus pad vi-IV-ii-Vsus + ticking glock |
| 20.45 | 613 | explain/reveal: light vibes arpeggio IV-I/3-ii-V, bass; soft kick + brushes from bar 2 |
| 35.40 | 1062 | mystery/curious: drums out, sus pad vi-IV-ii-Vsus + ticking glock |
| 40.90 | 1227 | explain/reveal: light vibes arpeggio IV-I/3-ii-V, bass; soft kick + brushes from bar 2 |
| 50.53 | 1516 | payoff: thins to pad + bass so the punchline lands dry |
| 58.40 | 1752 | mystery/curious: drums out, sus pad vi-IV-ii-Vsus + ticking glock |
| 65.03 | 1951 | loop end: no sting; riser into the last frame so the restart lands on the hook |

## SFX events
level = target LU vs the voice stem (max momentary of the event). Beds are integrated.

| # | time s | frame | cue | sound | why | level LU | pan |
|---|---|---|---|---|---|---|---|
| 1 | 0.010 | 0.3 | bloop_rumble | the Bloop evoked: deep rising rumble | the Bloop rumble under the opening (already sounding at frame 0) (word 0 'In') | -7 | +0.00 |
| 2 | 2.257 | 67.7 | impact | cartoon impact thump + crack | A SOUND FROM THE DEEP slams (word 7 'sound') | -16 | +0.00 |
| 3 | 2.731 | 81.9 | gps_ping | tracker ping: sonar blip + echo | station 1 lights up ("heard") (word 8 'heard') | -17 | +0.00 |
| 4 | 3.319 | 99.6 | gps_ping | tracker ping: sonar blip + echo | station 2 lights up ("microphones") (word 10 'microphones') | -17 | +0.00 |
| 5 | 4.441 | 133.2 | card_pop | title card pop: paper flick + thump | 4,800 KM APART (word 12 'five') | -17 | +0.00 |
| 6 | 6.261 | 187.8 | whoosh | transition whoosh | transition s01->s02 (room/None) | -17 | +0.00 |
| 7 | 6.479 | 194.4 | riser | noise riser ending on the cue time | the pitch rises on the display (word 18 'it') | -18 | +0.00 |
| 8 | 10.240 | 307.2 | impact | cartoon impact thump + crack | TOO LOUD slams (word 31 'that') | -15 | +0.00 |
| 9 | 10.805 | 324.1 | whoosh | transition whoosh | transition s02->s03 (ocean/None) | -17 | +0.00 |
| 10 | 12.223 | 366.7 | impact | cartoon impact thump + crack | THE BLOOP slams (word 37 'Bloop.') | -13 | +0.00 |
| 11 | 12.978 | 389.3 | whoosh | transition whoosh | the phone slides up (word 40 'internet') | -17 | +0.00 |
| 12 | 14.488 | 434.6 | pop | pop | the ? on the post (word 44 '"Something') | -17 | +0.00 |
| 13 | 16.245 | 487.4 | impact | cartoon impact thump + crack | NO CREATURE FITS (word 51 'creature') | -16 | +0.00 |
| 14 | 19.454 | 583.6 | impact | cartoon impact thump + crack | red X over the whale level (word 61 'isn't') | -15 | +0.00 |
| 15 | 20.449 | 613.5 | card_pop | title card pop: paper flick + thump | CLUE 1 badge (word 64 'Clue') | -15 | +0.00 |
| 16 | 22.536 | 676.1 | gps_ping | tracker ping: sonar blip + echo | the source near Antarctica pulses (word 71 'near') | -16 | +0.00 |
| 17 | 24.119 | 723.6 | card_pop | title card pop: paper flick + thump | CLUE 2 badge (word 76 'Clue') | -15 | +0.00 |
| 18 | 26.321 | 789.6 | bloop_rumble | the Bloop evoked: deep rising rumble | the rumble on the trace (cut at "stopped") (word 84 'It') | -13 | +0.00 |
| 19 | 28.484 | 854.5 | card_pop | title card pop: paper flick + thump | CLUE 3 badge (word 92 'Clue') | -15 | +0.00 |
| 20 | 31.084 | 932.5 | splash | splash | the microphone goes into the water (word 98 'microphones') | -18 | +0.00 |
| 21 | 32.897 | 986.9 | gps_ping | tracker ping: sonar blip + echo | it hears it again (word 102 'heard') | -16 | +0.00 |
| 22 | 34.037 | 1021.1 | pop | pop | 1,000s / YEAR (word 105 'Thousands') | -16 | +0.00 |
| 23 | 34.504 | 1035.1 | riser | noise riser ending on the cue time | into the big ? (word 110 'So') | -16 | +0.00 |
| 24 | 36.127 | 1083.8 | bloop_rumble | the Bloop evoked: deep rising rumble | roars under the shadow (word 114 'roars') | -12 | +0.00 |
| 25 | 39.206 | 1176.2 | impact | cartoon impact thump + crack | NOT A MONSTER. (word 125 'Not') | -14 | +0.00 |
| 26 | 40.223 | 1206.7 | glass_shatter | a window pane bursting | the shadow shatters into ice (word 128 'Ice.') | -12 | +0.00 |
| 27 | 40.223 | 1206.7 | deep_boom | huge distant airburst: sub thump + long rumble | ICE. hit (word 128 'Ice.') | -12 | +0.00 |
| 28 | 40.641 | 1219.2 | whoosh | transition whoosh | transition s09->s10 (polar/None) | -17 | +0.00 |
| 29 | 42.780 | 1283.4 | ice_crack | thin ice crackling, dispersive 'pew' cracks | the shelf cracks (word 135 'crack') | -11 | +0.00 |
| 30 | 43.337 | 1300.1 | ice_groan | an ice shelf giving way: groan, cracks, thud | the slab breaks away (word 137 'break') | -9 | +0.00 |
| 31 | 43.937 | 1318.1 | splash | splash | it hits the sea (word 139 'into') | -12 | +0.00 |
| 32 | 44.613 | 1338.4 | whoosh | transition whoosh | transition s10->s11 (ocean/None) | -17 | +0.00 |
| 33 | 45.630 | 1368.9 | card_pop | title card pop: paper flick + thump | SIZE OF A CITY (word 146 'size') | -16 | +0.00 |
| 34 | 46.249 | 1387.5 | ice_crack | thin ice crackling, dispersive 'pew' cracks | the slab splits (word 150 'splits,') | -11 | +0.00 |
| 35 | 46.855 | 1405.6 | deep_boom | huge distant airburst: sub thump + long rumble | the shudder through the water (word 152 'crack') | -10 | +0.00 |
| 36 | 49.302 | 1479.1 | gps_ping | tracker ping: sonar blip + echo | the far station hears it (word 161 'thousands') | -16 | +0.00 |
| 37 | 50.273 | 1508.2 | whoosh | transition whoosh | transition s11->s12 (room/None) | -17 | +0.00 |
| 38 | 51.180 | 1535.4 | ice_crack | thin ice crackling, dispersive 'pew' cracks | the ice cube cracks in the drink (word 168 'cracking') | -13 | +0.00 |
| 39 | 52.249 | 1567.5 | riser | noise riser ending on the cue time | the cube grows (word 172 'Now') | -17 | +0.00 |
| 40 | 53.628 | 1608.8 | bloop_rumble | the Bloop evoked: deep rising rumble | mountain-sized crack (word 178 'size') | -12 | +0.00 |
| 41 | 57.686 | 1730.6 | impact | cartoon impact thump + crack | ICEQUAKE stamp (word 192 'icequake.') | -12 | +0.00 |
| 42 | 58.606 | 1758.2 | ice_crack | thin ice crackling, dispersive 'pew' cracks | cracks along the coast (word 194 'monster') | -14 | +0.00 |
| 43 | 59.679 | 1790.4 | bloop_rumble | the Bloop evoked: deep rising rumble | the sound of Antarctica breaking (word 199 'the') | -11 | +0.00 |
| 44 | 61.389 | 1841.7 | whoosh | transition whoosh | transition s14a->s14b (room/None) | -17 | +0.00 |
| 45 | 64.014 | 1920.4 | riser | noise riser ending on the cue time | push into the display (loop) (word 226 'listening.') | -17 | +0.00 |
| bed | 0.000-6.461 | 0.0 | amb_ocean | ambience for set 'ocean' | shots on that set | -30.0 (int.) | 0 |
| bed | 6.461-11.005 | 193.8 | amb_room | ambience for set 'room' | shots on that set | -30.0 (int.) | 0 |
| bed | 11.005-20.389 | 330.1 | amb_ocean | ambience for set 'ocean' | shots on that set | -30.0 (int.) | 0 |
| bed | 20.389-24.059 | 611.7 | amb_outdoor | ambience for set 'chart' | shots on that set | -30.0 (int.) | 0 |
| bed | 24.059-28.424 | 721.8 | amb_room | ambience for set 'room' | shots on that set | -30.0 (int.) | 0 |
| bed | 28.424-35.344 | 852.7 | amb_polar | ambience for set 'polar' | shots on that set | -30.0 (int.) | 0 |
| bed | 35.344-40.841 | 1060.3 | amb_ocean | ambience for set 'ocean' | shots on that set | -30.0 (int.) | 0 |
| bed | 40.841-44.813 | 1225.2 | amb_polar | ambience for set 'polar' | shots on that set | -30.0 (int.) | 0 |
| bed | 44.813-50.473 | 1344.4 | amb_ocean | ambience for set 'ocean' | shots on that set | -30.0 (int.) | 0 |
| bed | 50.473-58.341 | 1514.2 | amb_room | ambience for set 'room' | shots on that set | -30.0 (int.) | 0 |
| bed | 58.341-61.589 | 1750.2 | amb_polar | ambience for set 'polar' | shots on that set | -30.0 (int.) | 0 |
| bed | 61.589-65.600 | 1847.7 | amb_room | ambience for set 'room' | shots on that set | -30.0 (int.) | 0 |
