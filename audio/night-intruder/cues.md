# Night Intruder: soundtrack cue sheet

Original short film, no narrator, no music bed (a very low drone under shots 2-5 and 12-15). Every sound is procedural numpy/scipy synthesis written for this film (`audio/lib/sfx_night.py`, on the template `dsp.py` / `sfx_gen.py`); no third-party samples or packs were used. THIEF 2's line: Kokoro-82M (Apache-2.0, kokoro-onnx v1.0 model files), voice **am_onyx** at speed 0.9, pitched down 1.5 semitones (rubberband, formants preserved), low shelf +2.5 dB, high shelf -3 dB, hallway + room reverb. Rebuild: `voice_kokoro.py` (once) then `build.py`; the cue list is `sfx.json`.

## Files
| file | content |
|---|---|
| `mix.wav` | final mix, 48 kHz stereo 24-bit, 3840000 samples = 2400 frames @ 30 fps = 80.000 s |
| `stem_amb.flac` / `stem_foley.flac` / `stem_body.flac` / `stem_voice.flac` | stems at mix gain, pre-limiter (24-bit FLAC; their sum + the master limiter = the mix) |
| `voice.wav` | THIEF 2's line with its room, at mix gain (48 kHz stereo); sample 0 = 56.40 s on the picture |
| `words.json` | the line's 7 words with absolute times (for the caption) |
| `length.json` | the picture length: 2400 frames |
| `sfx.json` | the hand-placed cue list (time, generator, level, pan, distance, reverb) |
| `voice_kokoro.py`, `voice_raw24k.wav`, `words_raw.json` | the Kokoro take and its word split |
| `qa_mix.png` | waveform + momentary loudness overview with the shot grid |

## Master loudness (own BS.1770-4 meter)
- Integrated **-14.1 LUFS** (target -14.0), true peak **-1.4 dBTP** (ceiling -1.2), LRA 10.7 LU
- Master gain +8.62 dB; limiter max gain reduction 9.95 dB (only on the transients: clang, thwack, slam, final impact)
- **35.000-37.000 s is digital zero: True** (every sample of both channels); 79.8-80.000 s is digital zero: True

ffmpeg ebur128 cross-check:
```
Summary:

  Integrated loudness:
    I:         -14.2 LUFS
    Threshold: -24.8 LUFS

  Loudness range:
    LRA:        10.9 LU
    Threshold: -34.8 LUFS
    LRA low:   -22.2 LUFS
    LRA high:  -11.3 LUFS

  True peak:
    Peak:       -1.4 dBFS
```

## Per shot (max momentary LUFS, sample peak)
| shot | time | M max | peak dBFS |
|---|---|---|---|
| 1 | 0:00.00-0:04.00 | -14.5 | -1.5 |
| 2 | 0:04.00-0:08.00 | -15.6 | -1.7 |
| 3 | 0:08.00-0:13.00 | -15.5 | -2.8 |
| 4 | 0:13.00-0:22.00 | -16.4 | -3.3 |
| 5 | 0:22.00-0:27.00 | -13.9 | -1.5 |
| 6 | 0:27.00-0:32.00 | -11.7 | -1.5 |
| 7 | 0:32.00-0:35.00 | -12.1 | -1.5 |
| 8 | 0:35.00-0:38.00 | -12.6 | -1.5 |
| 9 | 0:38.00-0:42.00 | -7.2 | -1.5 |
| 10 | 0:42.00-0:47.00 | -8.4 | -1.5 |
| 11 | 0:47.00-0:55.00 | -9.2 | -1.5 |
| 12 | 0:55.00-1:02.00 | -8.3 | -1.5 |
| 13 | 1:02.00-1:08.00 | -8.5 | -1.5 |
| 14 | 1:08.00-1:14.00 | -10.8 | -1.5 |
| 15 | 1:14.00-1:20.00 | -8.8 | -1.5 |

## Dialogue
| word | start | end |
|---|---|---|
| You | 56.660 | 56.860 |
| done | 56.890 | 57.270 |
| yet? | 57.300 | 57.499 |
| What's | 57.850 | 58.120 |
| all | 58.130 | 58.340 |
| the | 58.360 | 58.460 |
| noise? | 58.470 | 59.090 |

## Cues
time = start on the picture; level = max momentary LUFS of the event before the master gain (+8.6 dB) (bed = integrated). Hard cuts at 35.000 (into digital silence) and 76.000 (cut to black).

| time | shot | sound | level | stem |
|---|---|---|---|---|
| 0:00.00 | 1 | quiet house air under shots 1-7 (`room_tone`) | -54 bed | amb |
| 0:00.00 | 1 | steady clock ticking, bedroom wall (`clock_ticks`) | -27 | amb |
| 0:02.55 | 1 | dry metal CLACK downstairs, on tiles (`metal_drop`) | -23 | foley |
| 0:04.00 | 2 | very low dark drone, shots 2-5 (`drone`) | -51 bed | amb |
| 0:04.05 | 2 | faint wind whistling through a door gap (`door_gap_wind`) | -33 | amb |
| 0:07.05 | 2 | SCREEECH 1 (after 1.95 s of silence 5.10-7.05) (`chair_screech`) | -25 | foley |
| 0:07.58 | 2 | SCREEECH 2 (`chair_screech`) | -24 | foley |
| 0:08.00 | 3 | dull low heartbeat 8.0-35.0, rising in rate and level (`heartbeat`) | -21 | body |
| 0:08.70 | 3 | hand fumbling on the nightstand (`rustle`) | -38 | foley |
| 0:09.40 | 3 | fumbling (`rustle`) | -39 | foley |
| 0:10.10 | 3 | grips the metal lamp (`lamp_lift`) | -33 | foley |
| 0:11.60 | 3 | yanks the plug out of the socket (`plug_yank`) | -29 | foley |
| 0:13.20 | 4 | ME's held-back breathing, close (shots 4-7) (`breathing`) | -30 | body |
| 0:13.25 | 4 | bedroom door opened a crack (`door_creak_soft`) | -33 | foley |
| 0:14.90 | 4 | bare step 1 on the stairs (`barefoot`) | -36 | foley |
| 0:15.60 | 4 | ZZIP... (backpack zipper, from below) (`zip_pull`) | -31 | foley |
| 0:16.10 | 4 | step 2 (`barefoot`) | -36 | foley |
| 0:16.45 | 4 | ZZIP... (`zip_pull`) | -31 | foley |
| 0:17.00 | 4 | rummaging below, distant (`rummage`) | -31 | foley |
| 0:17.30 | 4 | step 3, the stair creaks a little (`barefoot`) | -35 | foley |
| 0:18.50 | 4 | step 4 (`barefoot`) | -36 | foley |
| 0:19.70 | 4 | step 5 (`barefoot`) | -36 | foley |
| 0:20.90 | 4 | step 6 (`barefoot`) | -36 | foley |
| 0:22.00 | 5 | rummaging louder, things clinking in the backpack (`rummage`) | -27 | foley |
| 0:27.00 | 6 | rummaging, clear (POV, 3 m) (`rummage`) | -24 | foley |
| 0:28.20 | 6 | laptop stuffed into the backpack (`laptop_slide`) | -23 | foley |
| 0:29.20 | 6 | settling the bag (`rummage`) | -26 | foley |
| 0:30.00 | 6 | one sharp, decisive ZIP (`zip_pull`) | -17 | foley |
| 0:30.80 | 6 | bag lifted (`rustle`) | -29 | foley |
| 0:32.75 | 7 | bare foot past the last stair (floor-level ECU) (`barefoot`) | -33 | foley |
| 0:33.20 | 7 | sharp plastic CRACK! (`plastic_crack`) | -15 | foley |
| 0:34.90 | 7 | the flashlight snaps off (ends 34.96, then digital zero) (`flashlight_click`) | -27 | foley |
| 0:37.00 | 8 | ME breathing hard in the dark (alone on top from 37.0, under the fight after) (`breathing`) | -22 | body |
| 0:37.00 | 12 | house air after the silence (`room_tone`) | -54 bed | amb |
| 0:37.08 | 8 | THIEF 1 breathing hard (`breathing`) | -24 | body |
| 0:37.95 | 9 | feet shift, the dodge (`cloth_scrape`) | -27 | foley |
| 0:38.05 | 9 | WHOOSH! the crowbar swing (peak ~38.41) (`swing_whoosh`) | -14 | foley |
| 0:38.50 | 9 | iron on the wall edge: ringing CLANG! (`clang_wall`) | -11.5 | foley |
| 0:38.52 | 9 | a few small spark crackles (`sparks`) | -30 | foley |
| 0:42.60 | 10 | ME lunges (cloth swish) (`swing_whoosh`) | -26 | foley |
| 0:42.72 | 10 | the lamp swung (`swing_whoosh`) | -18 | foley |
| 0:43.05 | 10 | THWACK! lamp on the weapon arm (`thwack`) | -13 | foley |
| 0:43.18 | 10 | THIEF 1's groan of pain (`groan`) | -18 | body |
| 0:43.55 | 10 | the bar clatters, bounces, rolls on the tiles (to ~46.4) (`crowbar_drop_roll`) | -14 | foley |
| 0:47.00 | 11 | ME's effort as he shoves (`groan`) | -24 | body |
| 0:47.30 | 11 | THIEF 1 slammed down on the tiles (`body_fall`) | -13 | foley |
| 0:47.45 | 11 | the backpack flies (`swing_whoosh`) | -27 | foley |
| 0:47.50 | 11 | ME fast panting (`breathing`) | -20 | body |
| 0:47.55 | 11 | THIEF 1 fast panting (`breathing`) | -22 | body |
| 0:47.60 | 11 | struggle, clothes scraping the tiles (`cloth_scrape`) | -19 | foley |
| 0:47.80 | 11 | contents spill everywhere (`bag_spill`) | -17 | foley |
| 0:49.60 | 11 | strain (THIEF 1) (`groan`) | -25 | body |
| 0:51.80 | 11 | strain (ME) (`groan`) | -25 | body |
| 0:53.40 | 11 | strain (THIEF 1) (`groan`) | -25 | body |
| 0:55.00 | 12 | low dark drone, shots 12-15 (cut at 76.0) (`drone`) | -48 bed | amb |
| 0:55.00 | 12 | house air (cut at 76.0) (`room_tone`) | -54 bed | amb |
| 0:55.20 | 12 | front-door hinge/latch CLICK (`latch_click`) | -19 | foley |
| 0:55.30 | 12 | ME, frozen, breathing hard but held (`breathing`) | -28 | body |
| 0:55.35 | 12 | street ambience leaks in, cut by the slam (`street_spill`) | -36 bed | amb |
| 0:55.35 | 12 | THIEF 1 under ME (`breathing`) | -31 | body |
| 0:55.40 | 12 | the door swings open softly (`door_creak_soft`) | -30 | foley |
| 0:56.65 | 12 | THIEF 2 (Kokoro am_onyx): "You done yet? What's all the noise?" (ends ~59.09) (`voice`) | -15.0 | voice |
| 0:59.50 | 12 | THIEF 2 steps in (`shoe_step`) | -22 | foley |
| 1:00.00 | 12 | heavy door SLAM (`door_slam`) | -10.5 | foley |
| 1:02.90 | 13 | elbow into ME's ribs (`elbow_hit`) | -15 | foley |
| 1:02.93 | 13 | the HUFF! (`huff`) | -15 | body |
| 1:03.35 | 13 | ME's low groan (`groan`) | -19 | body |
| 1:03.60 | 13 | a long slide across the tiles (to ~65.6) (`body_slide`) | -15 | foley |
| 1:05.70 | 13 | ME, scared breathing, faster to the end of shot 15 (`breathing`) | -24 | body |
| 1:08.50 | 14 | CLOMP 1 (far) (`shoe_step`) | -27 | foley |
| 1:09.90 | 14 | CLOMP 2 (`shoe_step`) | -23 | foley |
| 1:11.25 | 14 | CLOMP 3 (`shoe_step`) | -19 | foley |
| 1:12.50 | 14 | CLOMP 4 (`shoe_step`) | -15.5 | foley |
| 1:13.65 | 14 | CLOMP 5 (fills the frame) (`shoe_step`) | -13.5 | foley |
| 1:14.70 | 15 | CLOMP 6, right in front of him (`shoe_step`) | -12 | foley |
| 1:15.25 | 15 | ME's panic gasp (`breath`) | -21 | body |
| 1:15.45 | 15 | tearing WHOOSH! (swells into the cut) (`swing_whoosh`) | -11 | foley |
| 1:16.00 | 15 | dry impact on the cut to black (`dry_impact`) | -11 | foley |
| 1:16.35 | 15 | black: heavy panting, fading (`breathing`) | -19 | body |
| 1:16.60 | 15 | hurried footsteps running away, fading to nothing by ~79.6 (`running_away`) | -16 | foley |
| 0:35.00-0:37.00 | 8 | **ABSOLUTE DIGITAL SILENCE** | -inf | all |
