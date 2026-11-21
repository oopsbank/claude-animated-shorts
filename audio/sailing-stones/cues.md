# The Rocks That Walk Across the Desert: soundtrack cue sheet

All music and SFX are original, synthesized in numpy/scipy (`audio/lib/score.py`, `audio/lib/sfx_x.py`, template `dsp.py` / `instruments.py` / `sfx_gen.py`). Voice: ElevenLabs (see `audio/VOICE.md`), high-passed at 70 Hz and gently compressed (2:1, max 7.1 dB), no EQ colour or pitch change.

## Files
| file | content |
|---|---|
| `mix.wav` | final mix, 48 kHz stereo 24-bit, 3153600 samples = 1971 frames @ 30 fps = 65.700 s |
| `stem_voice.wav` / `stem_music.wav` / `stem_sfx.wav` | stems at mix gain, pre-limiter (their sum + the master limiter = the mix) |
| `length.json` | the picture length the engine must render |

## Master loudness (own BS.1770-4 meter)
- Integrated **-14.0 LUFS** (target -14.0), true peak **-1.2 dBTP** (ceiling -1.2), LRA 1.5 LU
- Stems at mix gain: voice -14.4, music -24.5, sfx -38.8 LUFS; master gain +12.03 dB
- Limiter: max gain reduction 3.40 dB, active (>0.1 dB) on 3.53 % of samples

ffmpeg ebur128 cross-check:
```
Summary:

  Integrated loudness:
    I:         -14.0 LUFS
    Threshold: -24.1 LUFS

  Loudness range:
    LRA:         1.5 LU
    Threshold: -34.1 LUFS
    LRA low:   -14.9 LUFS
    LRA high:  -13.4 LUFS

  True peak:
    Peak:       -1.2 dBFS
```

## Voice pacing (words.json)
- 235 words over 65.31 s = **3.60 words/s** (reference 3.5-4.1, median 3.7)
- gaps > 0.25 s: 7, total 2.73 s (reference < 1 s); longest gap 0.47 s
- first word at 0.040 s (frame 1.2); last word ends 65.346 s

## Voice on top, per section (LUFS at mix gain)
bed = music + sfx. margin = voice - bed (integrated). speech median / p10 = 400 ms momentary voice - bed over spoken words. Reference: bed 5-10 dB under the voice.

| section | time s | voice | music | sfx | bed | margin LU | speech median LU | speech p10 LU |
|---|---|---|---|---|---|---|---|---|
| hook 0.0 | 0.00-5.35 | -13.9 | -23.4 | -40.6 | -23.3 | 9.4 | 9.7 | 7.1 |
| mystery 5.3 | 5.35-10.97 | -14.2 | -24.5 | -41.3 | -24.4 | 10.2 | 11.0 | 6.7 |
| body 11.0 | 10.97-35.97 | -14.7 | -24.7 | -38.6 | -24.5 | 9.8 | 10.1 | 6.5 |
| mystery 36.0 | 35.97-41.13 | -14.0 | -24.6 | -36.4 | -24.4 | 10.4 | 10.5 | 6.4 |
| body 41.1 | 41.13-49.93 | -14.1 | -24.1 | -37.7 | -23.9 | 9.8 | 9.7 | 6.1 |
| explain 49.9 | 49.93-54.99 | -14.5 | -24.2 | -40.1 | -24.1 | 9.6 | 10.0 | 7.4 |
| body 55.0 | 54.99-59.61 | -14.1 | -24.1 | -38.5 | -23.9 | 9.8 | 9.9 | 7.7 |
| payoff 59.6 | 59.61-65.70 | -14.5 | -26.2 | -43.1 | -26.1 | 11.6 | 13.6 | 9.1 |

## Music map (original, G major, 112 bpm)
Music under the voice: -3 dB duck keyed from words.json, section targets (LU vs voice): hook -9.5, body -10.0, mystery -10.0, explain -9.5, payoff -11.0. Applied section gains (dB): hook@0.0s -13.0, mystery@5.3s -7.9, body@11.0s -14.6, mystery@36.0s -8.2, body@41.1s -13.8, explain@49.9s -11.6, body@55.0s -14.2, payoff@59.6s -5.1.

| time s | frame | music |
|---|---|---|
| 0.00 | 0 | hook: pluck arpeggio I-V-vi-IV, glock motif, kick + clap (no hats) |
| 5.35 | 160 | mystery/curious: drums out, sus pad vi-IV-ii-Vsus + ticking glock |
| 10.97 | 329 | body: full groove, hats + pad, 112 bpm |
| 22.48 | 674 | alien overlay: theremin-like sine glides 'ooo-eee-ooo' over the fantasy cutaway |
| 30.20 | 906 | alien overlay: theremin-like sine glides 'ooo-eee-ooo' over the fantasy cutaway |
| 35.97 | 1079 | mystery/curious: drums out, sus pad vi-IV-ii-Vsus + ticking glock |
| 41.13 | 1234 | body: full groove, hats + pad, 112 bpm |
| 45.84 | 1375 | alien overlay: theremin-like sine glides 'ooo-eee-ooo' over the fantasy cutaway |
| 49.93 | 1498 | explain/reveal: light vibes arpeggio IV-I/3-ii-V, bass; soft kick + brushes from bar 2 |
| 54.99 | 1650 | body: full groove, hats + pad, 112 bpm |
| 59.61 | 1788 | payoff: thins to pad + bass so the punchline lands dry |
| 65.35 | 1960 | loop end: no sting; riser into the last frame so the restart lands on the hook |

## SFX events
level = target LU vs the voice stem (max momentary of the event). Beds are integrated.

| # | time s | frame | cue | sound | why | level LU | pan |
|---|---|---|---|---|---|---|---|
| 1 | 1.043 | 31.3 | gps_ping | tracker ping: sonar blip + echo | fx gps_ping (s01 word 4) | -16 | -0.10 |
| 2 | 4.848 | 145.4 | sparkle | glock sparkle run | fx sparkle (s02 word 4) | -15 | -0.12 |
| 3 | 10.516 | 315.5 | question_mark | rising two-note pizzicato 'hmm?' | fx question_mark (s04 word 7) | -16 | +0.14 |
| 4 | 12.787 | 383.6 | year_badge | title card pop: paper flick + thump | fx year_badge (s06 word 0) | -16 | +0.00 |
| 5 | 15.327 | 459.8 | sliding_rock | rock scraping over wet mud and ice | fx sliding_rock (s06 word 8) | -15 | +0.30 |
| 6 | 17.646 | 529.4 | ka_ching | cash register ka-ching | price beat: Twenty bucks (word 67 'bucks."') | -14 | +0.00 |
| 7 | 20.467 | 614.0 | dust_storm | dust storm rolling in: wind roar, sand hiss, gusts | fx dust_storm (s08 word 3) | -15 | +0.00 |
| 8 | 22.532 | 676.0 | whoosh | transition whoosh | fx whoosh (s09 word 0) | -17 | +0.00 |
| 9 | 24.689 | 740.7 | ka_ching | cash register ka-ching | price beat: Thirty bucks (word 89 'bucks."') | -13 | +0.00 |
| 10 | 25.831 | 774.9 | flash_flood | flash flood: water roar, rush, debris, splash | fx flash_flood (s10 word 3) | -15 | +0.00 |
| 11 | 30.582 | 917.5 | speed_lines | fast swish / speed lines | fx speed_lines (s12 word 1) | -16 | +0.00 |
| 12 | 32.613 | 978.4 | ka_ching | cash register ka-ching | price beat: Forty bucks (word 115 'bucks."') | -12 | +0.00 |
| 13 | 34.323 | 1029.7 | live_ping | livestream notification chime | he livestreams (word 121 'livestreams') | -15 | +0.00 |
| 14 | 35.966 | 1079.0 | rain | rain on a shallow pond | fx rain (s14 word 0) | -16 | +0.00 |
| 15 | 37.646 | 1129.4 | ice_crack | thin ice crackling, dispersive 'pew' cracks | frost creeping on 'freeze' (word 134 'freeze') | -16 | +0.00 |
| 16 | 39.036 | 1171.1 | live_ping | livestream notification chime | a lone ping in the gap before 'Even': LIVE 3 watching (word 139 'Even') | -16 | +0.40 |
| 17 | 42.341 | 1270.2 | ice_crack | thin ice crackling, dispersive 'pew' cracks | fx ice_crack (s15 word 5) | -14 | +0.00 |
| 18 | 43.120 | 1293.6 | sliding_rock | rock scraping over wet mud and ice | fx sliding_rock (s15 word 8) | -15 | +0.00 |
| 19 | 46.227 | 1386.8 | whoosh | transition whoosh | fx whoosh (s16 word 1) | -17 | +0.00 |
| 20 | 49.614 | 1488.4 | ka_ching | cash register ka-ching | price beat: Fifty bucks (the biggest) (word 173 'bucks!"') | -11 | +0.00 |
| 21 | 51.735 | 1552.0 | ice_pane | ice pane grinding / shoving | huge panes (one pane, not two over the rock) (word 182 'panes;') | -16 | +0.00 |
| 22 | 55.146 | 1654.4 | live_flurry | a flurry of livestream notification chimes | the counter shoots up to 1.2M (word 195 'livestream') | -16 | +0.00 |
| 23 | 58.373 | 1751.2 | sign_crash | wooden sign splitting and slapping flat | Gary goes straight through the NIGHT ONLY sign (word 207 'through') | -15 | +0.00 |
| 24 | 64.688 | 1940.6 | ka_ching | cash register ka-ching | five bucks: a small, deflated ka-ching (word 231 'bucks.') | -17 | +0.00 |
| bed | 0.000-22.472 | 0.0 | amb_desert | ambience for set 'playa' | shots on that set | -30.0 (int.) | 0 |
| bed | 22.472-25.076 | 674.2 | amb_alien | ambience for set 'inserts' | shots on that set | -30.0 (int.) | 0 |
| bed | 25.076-30.185 | 752.3 | amb_desert | ambience for set 'playa' | shots on that set | -30.0 (int.) | 0 |
| bed | 30.185-33.001 | 905.6 | amb_alien | ambience for set 'inserts' | shots on that set | -30.0 (int.) | 0 |
| bed | 33.001-45.831 | 990.0 | amb_desert | ambience for set 'playa' | shots on that set | -30.0 (int.) | 0 |
| bed | 45.831-49.866 | 1374.9 | amb_alien | ambience for set 'inserts' | shots on that set | -30.0 (int.) | 0 |
| bed | 49.866-54.927 | 1496.0 | amb_desert | ambience for set 'playa' | shots on that set | -30.0 (int.) | 0 |
| bed | 54.927-57.191 | 1647.8 | amb_alien | ambience for set 'inserts' | shots on that set | -30.0 (int.) | 0 |
| bed | 57.191-65.700 | 1715.7 | amb_desert | ambience for set 'playa' | shots on that set | -30.0 (int.) | 0 |
