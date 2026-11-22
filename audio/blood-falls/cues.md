# The Glacier That Bleeds: soundtrack cue sheet

All music and SFX are original, synthesized in numpy/scipy (`audio/lib/score.py`, `audio/lib/sfx_x.py`, template `dsp.py` / `instruments.py` / `sfx_gen.py`). Voice: ElevenLabs (see `audio/VOICE.md`), high-passed at 70 Hz and gently compressed (2:1, max 6.9 dB), no EQ colour or pitch change.

## Files
| file | content |
|---|---|
| `mix.wav` | final mix, 48 kHz stereo 24-bit, 3144000 samples = 1965 frames @ 30 fps = 65.500 s |
| `stem_voice.wav` / `stem_music.wav` / `stem_sfx.wav` | stems at mix gain, pre-limiter (their sum + the master limiter = the mix) |
| `length.json` | the picture length the engine must render |

## Master loudness (own BS.1770-4 meter)
- Integrated **-14.0 LUFS** (target -14.0), true peak **-1.2 dBTP** (ceiling -1.2), LRA 1.5 LU
- Stems at mix gain: voice -14.3, music -24.9, sfx -38.9 LUFS; master gain +11.34 dB
- Limiter: max gain reduction 3.16 dB, active (>0.1 dB) on 4.69 % of samples

ffmpeg ebur128 cross-check:
```
Summary:

  Integrated loudness:
    I:         -14.1 LUFS
    Threshold: -24.1 LUFS

  Loudness range:
    LRA:         1.5 LU
    Threshold: -34.1 LUFS
    LRA low:   -14.8 LUFS
    LRA high:  -13.3 LUFS

  True peak:
    Peak:       -1.2 dBFS
```

## Voice pacing (words.json)
- 217 words over 64.78 s = **3.35 words/s** (reference 3.5-4.1, median 3.7)
- gaps > 0.25 s: 2, total 0.59 s (reference < 1 s); longest gap 0.30 s
- first word at 0.024 s (frame 0.7); last word ends 64.809 s

## Voice on top, per section (LUFS at mix gain)
bed = music + sfx. margin = voice - bed (integrated). speech median / p10 = 400 ms momentary voice - bed over spoken words. Reference: bed 5-10 dB under the voice.

| section | time s | voice | music | sfx | bed | margin LU | speech median LU | speech p10 LU |
|---|---|---|---|---|---|---|---|---|
| mystery 0.0 | 0.00-21.08 | -14.1 | -24.6 | -39.4 | -24.4 | 10.4 | 11.3 | 6.4 |
| explain 21.1 | 21.08-36.69 | -14.7 | -25.2 | -40.0 | -25.1 | 10.4 | 10.6 | 7.2 |
| mystery 36.7 | 36.69-51.38 | -14.3 | -25.1 | -38.6 | -24.9 | 10.5 | 12.2 | 5.9 |
| explain 51.4 | 51.38-56.95 | -14.0 | -24.5 | -38.1 | -24.3 | 10.3 | 11.2 | 7.6 |
| payoff 56.9 | 56.95-59.08 | -14.8 | -29.0 | -35.0 | -28.1 | 13.3 | 13.3 | 11.4 |
| mystery 59.1 | 59.08-65.50 | -14.1 | -24.6 | -39.3 | -24.5 | 10.4 | 11.1 | 6.6 |

## Music map (original, G major, 112 bpm)
Music under the voice: -3 dB duck keyed from words.json, section targets (LU vs voice): mystery -10.5, explain -10.5, payoff -11.0. Applied section gains (dB): mystery@0.0s -8.2, explain@21.1s -13.6, mystery@36.7s -8.7, explain@51.4s -13.0, payoff@56.9s -7.8, mystery@59.1s -8.2.

| time s | frame | music |
|---|---|---|
| 0.00 | 0 | mystery/curious: drums out, sus pad vi-IV-ii-Vsus + ticking glock |
| 21.08 | 632 | explain/reveal: light vibes arpeggio IV-I/3-ii-V, bass; soft kick + brushes from bar 2 |
| 36.69 | 1101 | mystery/curious: drums out, sus pad vi-IV-ii-Vsus + ticking glock |
| 51.38 | 1541 | explain/reveal: light vibes arpeggio IV-I/3-ii-V, bass; soft kick + brushes from bar 2 |
| 56.95 | 1708 | payoff: thins to pad + bass so the punchline lands dry |
| 59.08 | 1772 | mystery/curious: drums out, sus pad vi-IV-ii-Vsus + ticking glock |
| 64.81 | 1944 | loop end: no sting; riser into the last frame so the restart lands on the hook |

## SFX events
level = target LU vs the voice stem (max momentary of the event). Beds are integrated.

| # | time s | frame | cue | sound | why | level LU | pan |
|---|---|---|---|---|---|---|---|
| 1 | 0.144 | 4.3 | impact | cartoon impact thump + crack | title THE GLACIER IS BLEEDING slams in (word 0 'In') | -17 | +0.00 |
| 2 | 9.223 | 276.7 | impact | cartoon impact thump + crack | BLOOD FALLS sign drops and plants (word 34 'Blood') | -15 | +0.00 |
| 3 | 12.441 | 373.2 | ice_crack | thin ice crackling, dispersive 'pew' cracks | frost creeps, icicles grow on "Nothing" (word 42 'Nothing') | -17 | +0.00 |
| 4 | 13.541 | 406.2 | impact | cartoon impact thump + crack | hook: "Yet the red kept coming" punch-in + shake (word 45 'Yet') | -14 | +0.00 |
| 5 | 17.179 | 515.4 | impact | cartoon impact thump + crack | MYSTERY SOLVED stamp slams (word 57 'Mystery') | -13 | +0.00 |
| 6 | 18.039 | 541.2 | whoosh | transition whoosh | transition s04->s05 (lab/None) | -17 | +0.00 |
| 7 | 18.749 | 562.5 | ice_crack | thin ice crackling, dispersive 'pew' cracks | the stamp cracks apart (word 59 'But') | -15 | +0.00 |
| 8 | 20.740 | 622.2 | impact | cartoon impact thump + crack | red X on the algae: no algae (word 67 'no') | -14 | +0.00 |
| 9 | 21.082 | 632.5 | card_pop | title card pop: paper flick + thump | CLUE 1 badge (word 69 'Clue') | -15 | +0.00 |
| 10 | 24.865 | 746.0 | riser | noise riser ending on the cue time | the room darkens into "what is?" (word 88 'what') | -17 | +0.00 |
| 11 | 26.065 | 782.0 | impact | cartoon impact thump + crack | the big ? slams in (word 88 'what') | -15 | +0.00 |
| 12 | 26.674 | 800.2 | card_pop | title card pop: paper flick + thump | CLUE 2 badge (word 90 'Clue') | -15 | +0.00 |
| 13 | 27.982 | 839.5 | sparkle | glock sparkle run | microbes pop into the drop (word 95 'alive') | -19 | +0.00 |
| 14 | 32.803 | 984.1 | card_pop | title card pop: paper flick + thump | CLUE 3 badge (word 108 'Clue') | -15 | +0.00 |
| 15 | 36.157 | 1084.7 | sparkle | glock sparkle run | "clear" sparkle (word 122 'clear.') | -18 | +0.00 |
| 16 | 36.886 | 1106.6 | whoosh | transition whoosh | the survey plane passes (word 123 'Then') | -16 | +0.00 |
| 17 | 37.405 | 1122.2 | gps_ping | tracker ping: sonar blip + echo | radar scan pulses (word 125 'scanned') | -15 | +0.00 |
| 18 | 39.030 | 1170.9 | whoosh | transition whoosh | transition s10->s11a (under/None) | -17 | +0.00 |
| 19 | 41.393 | 1241.8 | gps_ping | tracker ping: sonar blip + echo | the hidden pool lights up (word 140 'hidden') | -14 | +0.00 |
| 20 | 43.158 | 1294.7 | ice_crack | thin ice crackling, dispersive 'pew' cracks | cracks spread under his boots (word 145 'sealed') | -15 | +0.00 |
| 21 | 44.840 | 1345.2 | whoosh | transition whoosh | transition s11b->s12 (under/None) | -17 | +0.00 |
| 22 | 50.522 | 1515.7 | impact | cartoon impact thump + crack | the crack opens: "Until it escapes" (word 167 'Until') | -15 | +0.00 |
| 23 | 49.549 | 1486.5 | riser | noise riser ending on the cue time | the iron rushes up the crack (word 169 'escapes.') | -17 | +0.00 |
| 24 | 51.122 | 1533.7 | whoosh | transition whoosh | transition s13->s14a (polar/None) | -17 | +0.00 |
| 25 | 51.982 | 1559.5 | ice_crack | thin ice crackling, dispersive 'pew' cracks | the brine squeezes out (word 174 'squeezes') | -16 | +0.00 |
| 26 | 54.668 | 1640.0 | impact | cartoon impact thump + crack | "rusts": orange flash down the stream (word 184 'rusts.') | -14 | +0.00 |
| 27 | 55.061 | 1651.8 | whoosh | transition whoosh | transition s14a->s14b (interior/None) | -17 | +0.00 |
| 28 | 56.687 | 1700.6 | whoosh | transition whoosh | transition s14b->s15 (polar/None) | -17 | +0.00 |
| 29 | 57.433 | 1723.0 | impact | cartoon impact thump + crack | NOT BLEEDING. slams in (word 193 'isn't') | -15 | +0.00 |
| 30 | 58.507 | 1755.2 | impact | cartoon impact thump + crack | RUSTING. slams in (word 196 'rusting.') | -13 | +0.00 |
| 31 | 60.178 | 1805.3 | pop | pop | the RED ALGAE bubble pops on "Never" (word 201 'Never') | -15 | +0.00 |
| 32 | 60.782 | 1823.5 | whoosh | transition whoosh | iris dive under the ice (word 203 'Just') | -15 | +0.00 |
| 33 | 62.353 | 1870.6 | whoosh | transition whoosh | transition s16a->s16b (polar/None) | -17 | +0.00 |
| bed | 0.000-18.239 | 0.0 | amb_polar | ambience for set 'polar' | shots on that set | -30.0 (int.) | 0 |
| bed | 18.239-26.614 | 547.2 | amb_room | ambience for set 'lab' | shots on that set | -30.0 (int.) | 0 |
| bed | 26.614-32.743 | 798.4 | amb_under | ambience for set 'under' | shots on that set | -30.0 (int.) | 0 |
| bed | 32.743-39.230 | 982.3 | amb_polar | ambience for set 'polar' | shots on that set | -30.0 (int.) | 0 |
| bed | 39.230-43.098 | 1176.9 | amb_under | ambience for set 'under' | shots on that set | -30.0 (int.) | 0 |
| bed | 43.098-45.040 | 1292.9 | amb_polar | ambience for set 'polar' | shots on that set | -30.0 (int.) | 0 |
| bed | 45.040-51.322 | 1351.2 | amb_under | ambience for set 'under' | shots on that set | -30.0 (int.) | 0 |
| bed | 51.322-55.261 | 1539.7 | amb_polar | ambience for set 'polar' | shots on that set | -30.0 (int.) | 0 |
| bed | 55.261-56.887 | 1657.8 | amb_room | ambience for set 'interior' | shots on that set | -30.0 (int.) | 0 |
| bed | 56.887-59.017 | 1706.6 | amb_polar | ambience for set 'polar' | shots on that set | -30.0 (int.) | 0 |
| bed | 59.017-62.553 | 1770.5 | amb_under | ambience for set 'under' | shots on that set | -30.0 (int.) | 0 |
| bed | 62.553-65.500 | 1876.6 | amb_polar | ambience for set 'polar' | shots on that set | -30.0 (int.) | 0 |
