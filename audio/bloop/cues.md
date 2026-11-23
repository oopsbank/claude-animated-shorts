# The Sound From the Deep: soundtrack cue sheet

All music and SFX are original, synthesized in numpy/scipy (`audio/lib/score.py`, `audio/lib/sfx_x.py`, template `dsp.py` / `instruments.py` / `sfx_gen.py`). Voice: ElevenLabs (see `audio/VOICE.md`), high-passed at 70 Hz and gently compressed (2:1, max 6.0 dB), no EQ colour or pitch change.

## Files
| file | content |
|---|---|
| `mix.wav` | final mix, 48 kHz stereo 24-bit, 3139200 samples = 1962 frames @ 30 fps = 65.400 s |
| `stem_voice.wav` / `stem_music.wav` / `stem_sfx.wav` | stems at mix gain, pre-limiter (their sum + the master limiter = the mix) |
| `length.json` | the picture length the engine must render |

## Master loudness (own BS.1770-4 meter)
- Integrated **-14.0 LUFS** (target -14.0), true peak **-1.2 dBTP** (ceiling -1.2), LRA 1.6 LU
- Stems at mix gain: voice -14.2, music -24.9, sfx -34.4 LUFS; master gain +9.34 dB
- Limiter: max gain reduction 2.46 dB, active (>0.1 dB) on 10.47 % of samples

ffmpeg ebur128 cross-check:
```
Summary:

  Integrated loudness:
    I:         -14.0 LUFS
    Threshold: -24.1 LUFS

  Loudness range:
    LRA:         1.6 LU
    Threshold: -34.0 LUFS
    LRA low:   -14.9 LUFS
    LRA high:  -13.3 LUFS

  True peak:
    Peak:       -1.2 dBFS
```

## Voice pacing (words.json)
- 216 words over 64.62 s = **3.34 words/s** (reference 3.5-4.1, median 3.7)
- gaps > 0.25 s: 2, total 0.62 s (reference < 1 s); longest gap 0.31 s
- first word at 0.023 s (frame 0.7); last word ends 64.641 s

## Voice on top, per section (LUFS at mix gain)
bed = music + sfx. margin = voice - bed (integrated). speech median / p10 = 400 ms momentary voice - bed over spoken words. Reference: bed 5-10 dB under the voice.

| section | time s | voice | music | sfx | bed | margin LU | speech median LU | speech p10 LU |
|---|---|---|---|---|---|---|---|---|
| mystery 0.0 | 0.00-20.14 | -14.2 | -24.7 | -33.8 | -24.3 | 10.1 | 10.7 | 7.0 |
| explain 20.1 | 20.14-34.70 | -14.5 | -25.0 | -38.8 | -24.8 | 10.3 | 11.0 | 6.5 |
| mystery 34.7 | 34.70-40.09 | -14.0 | -25.0 | -32.7 | -24.4 | 10.4 | 11.5 | 4.9 |
| explain 40.1 | 40.09-50.06 | -14.0 | -24.5 | -32.9 | -24.0 | 9.9 | 10.8 | 7.4 |
| payoff 50.1 | 50.06-58.18 | -14.1 | -25.7 | -34.4 | -25.1 | 11.0 | 12.2 | 8.0 |
| mystery 58.2 | 58.18-65.40 | -14.0 | -24.5 | -34.3 | -24.1 | 10.1 | 10.9 | 6.0 |

## Music map (original, G major, 112 bpm)
Music under the voice: -3 dB duck keyed from words.json, section targets (LU vs voice): mystery -10.5, explain -10.5, payoff -11.0. Applied section gains (dB): mystery@0.0s -7.0, explain@20.1s -11.5, mystery@34.7s -6.5, explain@40.1s -11.9, payoff@50.1s -4.5, mystery@58.2s -6.5.

| time s | frame | music |
|---|---|---|
| 0.00 | 0 | mystery/curious: drums out, sus pad vi-IV-ii-Vsus + ticking glock |
| 20.14 | 604 | explain/reveal: light vibes arpeggio IV-I/3-ii-V, bass; soft kick + brushes from bar 2 |
| 34.70 | 1041 | mystery/curious: drums out, sus pad vi-IV-ii-Vsus + ticking glock |
| 40.09 | 1203 | explain/reveal: light vibes arpeggio IV-I/3-ii-V, bass; soft kick + brushes from bar 2 |
| 50.06 | 1502 | payoff: thins to pad + bass so the punchline lands dry |
| 58.18 | 1745 | mystery/curious: drums out, sus pad vi-IV-ii-Vsus + ticking glock |
| 64.70 | 1941 | loop end: no sting; riser into the last frame so the restart lands on the hook |

## SFX events
level = target LU vs the voice stem (max momentary of the event). Beds are integrated.

| # | time s | frame | cue | sound | why | level LU | pan |
|---|---|---|---|---|---|---|---|
| 1 | -0.027 | -0.8 | bloop_rumble | the Bloop evoked: deep rising rumble | the Bloop rumble under the opening (already sounding at frame 0) (word 0 'In') | -7 | +0.00 |
| 2 | 2.415 | 72.5 | impact | cartoon impact thump + crack | A SOUND FROM THE DEEP slams (word 7 'sound') | -16 | +0.00 |
| 3 | 2.927 | 87.8 | gps_ping | tracker ping: sonar blip + echo | station 1 lights up ("heard") (word 8 'heard') | -17 | +0.00 |
| 4 | 3.262 | 97.9 | gps_ping | tracker ping: sonar blip + echo | station 2 lights up ("microphones") (word 10 'microphones') | -17 | +0.00 |
| 5 | 4.156 | 124.7 | card_pop | title card pop: paper flick + thump | 4,800 KM APART (word 12 'five') | -17 | +0.00 |
| 6 | 5.868 | 176.0 | whoosh | transition whoosh | transition s01->s02 (room/None) | -17 | +0.00 |
| 7 | 6.132 | 184.0 | riser | noise riser ending on the cue time | the pitch rises on the display (word 18 'it') | -18 | +0.00 |
| 8 | 9.559 | 286.8 | impact | cartoon impact thump + crack | TOO LOUD slams (word 31 'that') | -15 | +0.00 |
| 9 | 10.159 | 304.8 | whoosh | transition whoosh | transition s02->s03 (ocean/None) | -17 | +0.00 |
| 10 | 11.656 | 349.7 | impact | cartoon impact thump + crack | THE BLOOP slams (word 37 'Bloop.') | -13 | +0.00 |
| 11 | 12.355 | 370.7 | whoosh | transition whoosh | the phone slides up (word 40 'internet') | -17 | +0.00 |
| 12 | 13.771 | 413.1 | pop | pop | the ? on the post (word 44 '"Something') | -17 | +0.00 |
| 13 | 15.677 | 470.3 | impact | cartoon impact thump + crack | NO CREATURE FITS (word 51 'creature') | -16 | +0.00 |
| 14 | 19.064 | 571.9 | impact | cartoon impact thump + crack | red X over the whale level (word 61 'isn't') | -15 | +0.00 |
| 15 | 20.137 | 604.1 | card_pop | title card pop: paper flick + thump | CLUE 1 badge (word 64 'Clue') | -15 | +0.00 |
| 16 | 22.279 | 668.4 | gps_ping | tracker ping: sonar blip + echo | the source near Antarctica pulses (word 71 'near') | -16 | +0.00 |
| 17 | 23.677 | 710.3 | card_pop | title card pop: paper flick + thump | CLUE 2 badge (word 76 'Clue') | -15 | +0.00 |
| 18 | 25.891 | 776.7 | bloop_rumble | the Bloop evoked: deep rising rumble | the rumble on the trace (cut at "stopped") (word 84 'It') | -13 | +0.00 |
| 19 | 28.117 | 843.5 | card_pop | title card pop: paper flick + thump | CLUE 3 badge (word 92 'Clue') | -15 | +0.00 |
| 20 | 30.754 | 922.6 | splash | splash | the microphone goes into the water (word 98 'microphones') | -18 | +0.00 |
| 21 | 32.391 | 971.7 | gps_ping | tracker ping: sonar blip + echo | it hears it again (word 102 'heard') | -16 | +0.00 |
| 22 | 33.209 | 996.3 | pop | pop | 1,000s / YEAR (word 105 'Thousands') | -16 | +0.00 |
| 23 | 33.805 | 1014.1 | riser | noise riser ending on the cue time | into the big ? (word 110 'So') | -16 | +0.00 |
| 24 | 35.366 | 1061.0 | bloop_rumble | the Bloop evoked: deep rising rumble | roars under the shadow (word 114 'roars') | -12 | +0.00 |
| 25 | 38.506 | 1155.2 | impact | cartoon impact thump + crack | NOT A MONSTER. (word 125 'Not') | -14 | +0.00 |
| 26 | 39.468 | 1184.0 | glass_shatter | a window pane bursting | the shadow shatters into ice (word 128 'Ice.') | -12 | +0.00 |
| 27 | 39.468 | 1184.0 | deep_boom | huge distant airburst: sub thump + long rumble | ICE. hit (word 128 'Ice.') | -12 | +0.00 |
| 28 | 39.835 | 1195.0 | whoosh | transition whoosh | transition s09->s10 (polar/None) | -17 | +0.00 |
| 29 | 42.342 | 1270.3 | ice_crack | thin ice crackling, dispersive 'pew' cracks | the shelf cracks (word 135 'crack') | -11 | +0.00 |
| 30 | 42.844 | 1285.3 | ice_groan | an ice shelf giving way: groan, cracks, thud | the slab breaks away (word 137 'break') | -9 | +0.00 |
| 31 | 43.405 | 1302.2 | splash | splash | it hits the sea (word 139 'into') | -12 | +0.00 |
| 32 | 44.041 | 1321.2 | whoosh | transition whoosh | transition s10->s11 (ocean/None) | -17 | +0.00 |
| 33 | 45.100 | 1353.0 | card_pop | title card pop: paper flick + thump | SIZE OF A CITY (word 146 'size') | -16 | +0.00 |
| 34 | 45.697 | 1370.9 | ice_crack | thin ice crackling, dispersive 'pew' cracks | the slab splits (word 150 'splits,') | -11 | +0.00 |
| 35 | 46.545 | 1396.4 | deep_boom | huge distant airburst: sub thump + long rumble | the shudder through the water (word 152 'crack') | -10 | +0.00 |
| 36 | 48.711 | 1461.3 | gps_ping | tracker ping: sonar blip + echo | the far station hears it (word 161 'thousands') | -16 | +0.00 |
| 37 | 49.805 | 1494.1 | whoosh | transition whoosh | transition s11->s12 (room/None) | -17 | +0.00 |
| 38 | 50.762 | 1522.9 | ice_crack | thin ice crackling, dispersive 'pew' cracks | the ice cube cracks in the drink (word 168 'cracking') | -13 | +0.00 |
| 39 | 51.773 | 1553.2 | riser | noise riser ending on the cue time | the cube grows (word 172 'Now') | -17 | +0.00 |
| 40 | 53.262 | 1597.9 | bloop_rumble | the Bloop evoked: deep rising rumble | mountain-sized crack (word 178 'size') | -12 | +0.00 |
| 41 | 57.221 | 1716.6 | impact | cartoon impact thump + crack | ICEQUAKE stamp (word 192 'icequake.') | -12 | +0.00 |
| 42 | 58.316 | 1749.5 | ice_crack | thin ice crackling, dispersive 'pew' cracks | cracks along the coast (word 194 'monster') | -14 | +0.00 |
| 43 | 59.277 | 1778.3 | bloop_rumble | the Bloop evoked: deep rising rumble | the sound of Antarctica breaking (word 199 'the') | -11 | +0.00 |
| 44 | 61.035 | 1831.0 | whoosh | transition whoosh | transition s14a->s14b (room/None) | -17 | +0.00 |
| 45 | 63.596 | 1907.9 | riser | noise riser ending on the cue time | push into the display (loop) (word 226 'listening.') | -17 | +0.00 |
| bed | 0.000-6.068 | 0.0 | amb_ocean | ambience for set 'ocean' | shots on that set | -30.0 (int.) | 0 |
| bed | 6.068-10.359 | 182.0 | amb_room | ambience for set 'room' | shots on that set | -30.0 (int.) | 0 |
| bed | 10.359-20.077 | 310.8 | amb_ocean | ambience for set 'ocean' | shots on that set | -30.0 (int.) | 0 |
| bed | 20.077-23.617 | 602.3 | amb_outdoor | ambience for set 'chart' | shots on that set | -30.0 (int.) | 0 |
| bed | 23.617-28.057 | 708.5 | amb_room | ambience for set 'room' | shots on that set | -30.0 (int.) | 0 |
| bed | 28.057-34.645 | 841.7 | amb_polar | ambience for set 'polar' | shots on that set | -30.0 (int.) | 0 |
| bed | 34.645-40.035 | 1039.3 | amb_ocean | ambience for set 'ocean' | shots on that set | -30.0 (int.) | 0 |
| bed | 40.035-44.241 | 1201.0 | amb_polar | ambience for set 'polar' | shots on that set | -30.0 (int.) | 0 |
| bed | 44.241-50.005 | 1327.2 | amb_ocean | ambience for set 'ocean' | shots on that set | -30.0 (int.) | 0 |
| bed | 50.005-58.118 | 1500.1 | amb_room | ambience for set 'room' | shots on that set | -30.0 (int.) | 0 |
| bed | 58.118-61.235 | 1743.5 | amb_polar | ambience for set 'polar' | shots on that set | -30.0 (int.) | 0 |
| bed | 61.235-65.400 | 1837.0 | amb_room | ambience for set 'room' | shots on that set | -30.0 (int.) | 0 |
