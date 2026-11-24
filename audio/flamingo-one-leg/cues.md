# Why Do Flamingos Stand on One Leg?: soundtrack cue sheet

All music and SFX are original, synthesized in numpy/scipy (`audio/lib/score.py`, `audio/lib/sfx_x.py`, template `dsp.py` / `instruments.py` / `sfx_gen.py`). Voice: ElevenLabs (see `audio/VOICE.md`), high-passed at 70 Hz and gently compressed (2:1, max 5.9 dB), no EQ colour or pitch change.

## Files
| file | content |
|---|---|
| `mix.wav` | final mix, 48 kHz stereo 24-bit, 3020800 samples = 1888 frames @ 30 fps = 62.933 s |
| `stem_voice.wav` / `stem_music.wav` / `stem_sfx.wav` | stems at mix gain, pre-limiter (their sum + the master limiter = the mix) |
| `length.json` | the picture length the engine must render |

## Master loudness (own BS.1770-4 meter)
- Integrated **-14.0 LUFS** (target -14.0), true peak **-1.2 dBTP** (ceiling -1.2), LRA 0.8 LU
- Stems at mix gain: voice -14.2, music -24.8, sfx -40.6 LUFS; master gain +4.61 dB
- Limiter: max gain reduction 2.98 dB, active (>0.1 dB) on 13.51 % of samples

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
- 224 words over 62.06 s = **3.61 words/s** (reference 3.5-4.1, median 3.7)
- gaps > 0.25 s: 0, total 0.00 s (reference < 1 s); longest gap 0.25 s
- first word at 0.060 s (frame 1.8); last word ends 62.124 s

## Voice on top, per section (LUFS at mix gain)
bed = music + sfx. margin = voice - bed (integrated). speech median / p10 = 400 ms momentary voice - bed over spoken words. Reference: bed 5-10 dB under the voice.

| section | time s | voice | music | sfx | bed | margin LU | speech median LU | speech p10 LU |
|---|---|---|---|---|---|---|---|---|
| mystery 0.0 | 0.00-19.30 | -14.2 | -24.7 | -40.6 | -24.6 | 10.4 | 11.6 | 6.5 |
| explain 19.3 | 19.30-33.56 | -14.3 | -24.8 | -40.6 | -24.6 | 10.4 | 11.0 | 7.1 |
| mystery 33.6 | 33.56-36.26 | -14.0 | -25.5 | -40.4 | -25.4 | 11.5 | 12.3 | 8.0 |
| explain 36.3 | 36.26-49.87 | -14.1 | -24.6 | -40.9 | -24.5 | 10.4 | 11.5 | 7.0 |
| payoff 49.9 | 49.87-58.33 | -14.2 | -25.7 | -41.5 | -25.6 | 11.4 | 13.2 | 7.7 |
| mystery 58.3 | 58.33-62.93 | -14.0 | -24.5 | -42.3 | -24.4 | 10.4 | 10.8 | 7.5 |

## Music map (original, G major, 112 bpm)
Music under the voice: -3 dB duck keyed from words.json, section targets (LU vs voice): mystery -10.5, explain -10.5, payoff -11.0. Applied section gains (dB): mystery@0.0s -2.0, explain@19.3s -6.7, mystery@33.6s -2.6, explain@36.3s -6.6, payoff@49.9s +0.5, mystery@58.3s -2.2.

| time s | frame | music |
|---|---|---|
| 0.00 | 0 | mystery/curious: drums out, sus pad vi-IV-ii-Vsus + ticking glock |
| 19.30 | 579 | explain/reveal: light vibes arpeggio IV-I/3-ii-V, bass; soft kick + brushes from bar 2 |
| 33.56 | 1007 | mystery/curious: drums out, sus pad vi-IV-ii-Vsus + ticking glock |
| 36.26 | 1088 | explain/reveal: light vibes arpeggio IV-I/3-ii-V, bass; soft kick + brushes from bar 2 |
| 49.87 | 1496 | payoff: thins to pad + bass so the punchline lands dry |
| 58.33 | 1750 | mystery/curious: drums out, sus pad vi-IV-ii-Vsus + ticking glock |
| 62.23 | 1867 | loop end: no sting; riser into the last frame so the restart lands on the hook |

## SFX events
level = target LU vs the voice stem (max momentary of the event). Beds are integrated.

| # | time s | frame | cue | sound | why | level LU | pan |
|---|---|---|---|---|---|---|---|
| 1 | 0.294 | 8.8 | card_pop | title card pop: paper flick + thump | 2017 · ATLANTA title (word 1 '2017,') | -16 | +0.00 |
| 2 | 5.158 | 154.7 | joint_settle | a joint settling to the end of its range | the specimen settles into the one-leg pose (word 13 'held') | -17 | +0.00 |
| 3 | 6.977 | 209.3 | flamingo_honk | a flamingo call | the sleeping flock (word 20 'Live') | -19 | +0.00 |
| 4 | 8.175 | 245.3 | water_step | a thin leg in shallow water | a leg tucks up out of the water (word 23 'like') | -18 | +0.00 |
| 5 | 10.831 | 324.9 | question | rising two-note pizzicato 'hmm?' | WARMTH? (word 31 'answer:') | -17 | +0.00 |
| 6 | 12.820 | 384.6 | whoosh | transition whoosh | transition s03->s04 (room/None) | -17 | +0.00 |
| 7 | 15.210 | 456.3 | whoosh | transition whoosh | NOT HOW: cut to the person (word 46 'how.') | -17 | +0.00 |
| 8 | 18.224 | 546.7 | sweat_drop | drip blip | the person wobbles (word 57 'wobble') | -18 | +0.00 |
| 9 | 19.303 | 579.1 | card_pop | title card pop: paper flick + thump | CLUE 1 (word 60 'Clue') | -16 | +0.00 |
| 10 | 23.145 | 694.4 | ding | ding | ANKLE label (word 76 'ankle.') | -17 | +0.00 |
| 11 | 25.358 | 760.7 | card_pop | title card pop: paper flick + thump | CLUE 2 (word 85 'Clue') | -16 | +0.00 |
| 12 | 27.422 | 822.7 | water_step | a thin leg in shallow water | the foot shifts under the body (word 92 'moves') | -17 | +0.00 |
| 13 | 29.910 | 897.3 | card_pop | title card pop: paper flick + thump | CLUE 3 (word 102 'Clue') | -16 | +0.00 |
| 14 | 33.715 | 1011.5 | question | rising two-note pizzicato 'hmm?' | the riddle (word 114 'how') | -17 | +0.00 |
| 15 | 35.995 | 1079.8 | whoosh | transition whoosh | transition s08->s09 (lab/None) | -17 | +0.00 |
| 16 | 37.841 | 1135.2 | whoosh | transition whoosh | weight arrow down the leg (word 133 'weight') | -18 | +0.00 |
| 17 | 41.291 | 1238.7 | joint_settle | a joint settling to the end of its range | hip and knee hit the end of their bend (word 147 'end') | -15 | +0.00 |
| 18 | 43.390 | 1301.7 | sparkle | glock sparkle run | gravity holds it (word 156 'Gravity') | -19 | +0.00 |
| 19 | 48.833 | 1465.0 | impact | cartoon impact thump + crack | two legs: it slumps (word 176 'couldn't') | -17 | +0.00 |
| 20 | 49.612 | 1488.4 | whoosh | transition whoosh | transition s12->s13 (room/None) | -17 | +0.00 |
| 21 | 53.874 | 1616.2 | whoosh | transition whoosh | transition s13->s14 (lagoon/None) | -17 | +0.00 |
| 22 | 56.338 | 1690.1 | whoosh | transition whoosh | the flip (word 206 'For') | -17 | +0.00 |
| 23 | 58.073 | 1742.2 | whoosh | transition whoosh | transition s14->s15 (lab/None) | -17 | +0.00 |
| 24 | 59.360 | 1780.8 | flamingo_honk | a flamingo call | back to 2017 (word 217 'flamingo') | -19 | +0.00 |
| bed | 0.000-7.117 | 0.0 | amb_room | ambience for set 'lab' | shots on that set | -30.0 (int.) | 0 |
| bed | 7.117-13.020 | 213.5 | amb_lagoon | ambience for set 'lagoon' | shots on that set | -30.0 (int.) | 0 |
| bed | 13.020-25.298 | 390.6 | amb_room | ambience for set 'room' | shots on that set | -30.0 (int.) | 0 |
| bed | 25.298-29.850 | 758.9 | amb_lagoon | ambience for set 'lagoon' | shots on that set | -30.0 (int.) | 0 |
| bed | 29.850-33.499 | 895.5 | amb_outdoor | ambience for set 'park' | shots on that set | -30.0 (int.) | 0 |
| bed | 33.499-36.195 | 1005.0 | amb_lagoon | ambience for set 'lagoon' | shots on that set | -30.0 (int.) | 0 |
| bed | 36.195-54.074 | 1085.8 | amb_room | ambience for set 'lab' | shots on that set | -30.0 (int.) | 0 |
| bed | 54.074-58.273 | 1622.2 | amb_lagoon | ambience for set 'lagoon' | shots on that set | -30.0 (int.) | 0 |
| bed | 58.273-62.933 | 1748.2 | amb_room | ambience for set 'lab' | shots on that set | -30.0 (int.) | 0 |
