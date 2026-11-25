# Why Are Airplane Windows Round?: soundtrack cue sheet

All music and SFX are original, synthesized in numpy/scipy (`audio/lib/score.py`, `audio/lib/sfx_x.py`, template `dsp.py` / `instruments.py` / `sfx_gen.py`). Voice: ElevenLabs (see `audio/VOICE.md`), high-passed at 70 Hz and gently compressed (2:1, max 6.3 dB), no EQ colour or pitch change.

## Files
| file | content |
|---|---|
| `mix.wav` | final mix, 48 kHz stereo 24-bit, 3129600 samples = 1956 frames @ 30 fps = 65.200 s |
| `stem_voice.wav` / `stem_music.wav` / `stem_sfx.wav` | stems at mix gain, pre-limiter (their sum + the master limiter = the mix) |
| `length.json` | the picture length the engine must render |

## Master loudness (own BS.1770-4 meter)
- Integrated **-14.0 LUFS** (target -14.0), true peak **-1.2 dBTP** (ceiling -1.2), LRA 0.8 LU
- Stems at mix gain: voice -14.2, music -24.9, sfx -40.3 LUFS; master gain +4.75 dB
- Limiter: max gain reduction 2.73 dB, active (>0.1 dB) on 17.05 % of samples

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
- 213 words over 64.33 s = **3.31 words/s** (reference 3.5-4.1, median 3.7)
- gaps > 0.25 s: 0, total 0.00 s (reference < 1 s); longest gap 0.24 s
- first word at 0.060 s (frame 1.8); last word ends 64.394 s

## Voice on top, per section (LUFS at mix gain)
bed = music + sfx. margin = voice - bed (integrated). speech median / p10 = 400 ms momentary voice - bed over spoken words. Reference: bed 5-10 dB under the voice.

| section | time s | voice | music | sfx | bed | margin LU | speech median LU | speech p10 LU |
|---|---|---|---|---|---|---|---|---|
| mystery 0.0 | 0.00-18.68 | -14.3 | -24.8 | -40.4 | -24.7 | 10.4 | 11.1 | 6.9 |
| explain 18.7 | 18.68-33.08 | -14.2 | -24.7 | -40.9 | -24.6 | 10.4 | 11.2 | 7.4 |
| mystery 33.1 | 33.08-34.77 | -13.8 | -26.9 | -38.8 | -26.5 | 12.7 | 12.5 | 11.8 |
| explain 34.8 | 34.77-53.80 | -14.2 | -24.7 | -40.7 | -24.6 | 10.4 | 10.8 | 6.8 |
| payoff 53.8 | 53.80-61.21 | -14.1 | -25.8 | -40.0 | -25.5 | 11.4 | 12.7 | 8.5 |
| mystery 61.2 | 61.21-65.20 | -14.1 | -24.6 | -40.1 | -24.5 | 10.4 | 10.9 | 5.6 |

## Music map (original, G major, 112 bpm)
Music under the voice: -3 dB duck keyed from words.json, section targets (LU vs voice): mystery -10.5, explain -10.5, payoff -11.0. Applied section gains (dB): mystery@0.0s -2.5, explain@18.7s -6.8, mystery@33.1s -1.7, explain@34.8s -6.8, payoff@53.8s +0.3, mystery@61.2s -2.2.

| time s | frame | music |
|---|---|---|
| 0.00 | 0 | mystery/curious: drums out, sus pad vi-IV-ii-Vsus + ticking glock |
| 18.68 | 560 | explain/reveal: light vibes arpeggio IV-I/3-ii-V, bass; soft kick + brushes from bar 2 |
| 33.08 | 992 | mystery/curious: drums out, sus pad vi-IV-ii-Vsus + ticking glock |
| 34.77 | 1043 | explain/reveal: light vibes arpeggio IV-I/3-ii-V, bass; soft kick + brushes from bar 2 |
| 53.80 | 1614 | payoff: thins to pad + bass so the punchline lands dry |
| 61.21 | 1836 | mystery/curious: drums out, sus pad vi-IV-ii-Vsus + ticking glock |
| 64.50 | 1935 | loop end: no sting; riser into the last frame so the restart lands on the hook |

## SFX events
level = target LU vs the voice stem (max momentary of the event). Beds are integrated.

| # | time s | frame | cue | sound | why | level LU | pan |
|---|---|---|---|---|---|---|---|
| 1 | 0.283 | 8.5 | card_pop | title card pop: paper flick + thump | 1954 · ENGLAND title (word 1 '1954,') | -16 | +0.00 |
| 2 | 5.718 | 171.5 | pump_hiss | air pumped into a sealed fuselage | the fuselage in the tank is pumped up (word 16 'pumped') | -19 | +0.00 |
| 3 | 6.466 | 194.0 | metal_groan | a fuselage flexing under pressure | the hull flexes, again and again (word 19 'again') | -18 | +0.00 |
| 4 | 7.064 | 211.9 | whoosh | transition whoosh | transition s01->s02 (aircabin/None) | -17 | +0.00 |
| 5 | 9.568 | 287.0 | question | rising two-note pizzicato 'hmm?' | no sharp corners? (word 30 'corners?') | -18 | +0.00 |
| 6 | 11.363 | 340.9 | card_pop | title card pop: paper flick + thump | JUST STYLE? (word 36 'style.') | -18 | +0.00 |
| 7 | 12.244 | 367.3 | jet_pass | a jet airliner passing overhead | the Comet, the first jet airliner (word 41 'airliner,') | -19 | +0.00 |
| 8 | 16.865 | 505.9 | impact | cartoon impact thump + crack | two Comets lost (respectful, low) (word 52 'broke') | -19 | +0.00 |
| 9 | 18.682 | 560.5 | card_pop | title card pop: paper flick + thump | CLUE 1 (word 57 'Clue') | -16 | +0.00 |
| 10 | 22.985 | 689.5 | card_pop | title card pop: paper flick + thump | CLUE 2 (word 71 'Clue') | -16 | +0.00 |
| 11 | 26.475 | 794.2 | ding | ding | about 1,000 flights (word 83 'thousand') | -19 | +0.00 |
| 12 | 27.436 | 823.1 | card_pop | title card pop: paper flick + thump | CLUE 3 (word 85 'Clue') | -16 | +0.00 |
| 13 | 30.049 | 901.5 | crack_ping | a fatigue crack giving way | the test fuselage splits at a window corner (word 94 'split') | -16 | +0.00 |
| 14 | 33.226 | 996.8 | question | rising two-note pizzicato 'hmm?' | the riddle (word 106 'why') | -17 | +0.00 |
| 15 | 34.509 | 1035.3 | whoosh | transition whoosh | transition s08->s09 (aircabin/None) | -17 | +0.00 |
| 16 | 35.679 | 1070.4 | pump_hiss | air pumped into a sealed fuselage | cabin pumped full of air (word 117 'pumped') | -20 | +0.00 |
| 17 | 38.044 | 1141.3 | metal_groan | a fuselage flexing under pressure | the body swells (word 127 'swells') | -19 | +0.00 |
| 18 | 40.591 | 1217.7 | whoosh | transition whoosh | it shrinks back (word 135 'shrinks') | -19 | +0.00 |
| 19 | 42.621 | 1278.6 | whoosh | transition whoosh | transition s10->s11 (room/None) | -17 | +0.00 |
| 20 | 44.917 | 1347.5 | sparkle | glock sparkle run | stress flows smoothly round the round window (word 148 'smoothly') | -20 | +0.00 |
| 21 | 47.767 | 1433.0 | pop | pop | stress piles into one point at the corner (word 158 'tiny') | -18 | +0.00 |
| 22 | 50.045 | 1501.4 | crack_ping | a fatigue crack giving way | a tiny crack grows (word 165 'crack') | -17 | +0.00 |
| 23 | 51.522 | 1545.7 | metal_groan | a fuselage flexing under pressure | the metal gives way (word 170 'metal') | -18 | +0.00 |
| 24 | 57.543 | 1726.3 | paperclip_snap | a paperclip snapping | the paperclip snaps (word 191 'snaps.') | -16 | +0.00 |
| 25 | 57.988 | 1739.6 | card_pop | title card pop: paper flick + thump | NOT ABOUT LOOKS. (word 192 'Round') | -17 | +0.00 |
| 26 | 60.455 | 1813.6 | impact | cartoon impact thump + crack | ABOUT NOT TEARING OPEN. (word 200 'tearing') | -16 | +0.00 |
| 27 | 60.953 | 1828.6 | whoosh | transition whoosh | transition s14->s15 (hangar/None) | -17 | +0.00 |
| 28 | 62.716 | 1881.5 | pump_hiss | air pumped into a sealed fuselage | back to the tank (word 208 'tank') | -20 | +0.00 |
| 29 | 64.099 | 1923.0 | card_pop | title card pop: paper flick + thump | 1954 (word 212 '1954.') | -17 | +0.00 |
| bed | 0.000-7.264 | 0.0 | amb_hangar | ambience for set 'hangar' | shots on that set | -30.0 (int.) | 0 |
| bed | 7.264-11.782 | 217.9 | amb_aircabin | ambience for set 'aircabin' | shots on that set | -30.0 (int.) | 0 |
| bed | 11.782-27.376 | 353.5 | amb_altitude | ambience for set 'altitude' | shots on that set | -30.0 (int.) | 0 |
| bed | 27.376-34.709 | 821.3 | amb_hangar | ambience for set 'hangar' | shots on that set | -30.0 (int.) | 0 |
| bed | 34.709-42.821 | 1041.3 | amb_aircabin | ambience for set 'aircabin' | shots on that set | -30.0 (int.) | 0 |
| bed | 42.821-57.928 | 1284.6 | amb_room | ambience for set 'room' | shots on that set | -30.0 (int.) | 0 |
| bed | 57.928-61.153 | 1737.8 | amb_aircabin | ambience for set 'aircabin' | shots on that set | -30.0 (int.) | 0 |
| bed | 61.153-65.200 | 1834.6 | amb_hangar | ambience for set 'hangar' | shots on that set | -30.0 (int.) | 0 |
