# audio/ (🎧 Sound Designer)

| file | what |
|---|---|
| `VOICE.md` | the narrator voice and its settings, the quota notes, and the test |
| `voice_test.mp3`, `voice_test_words.json` | the one-sentence voice test |
| `tts.py` | `SCRIPT.md` → ElevenLabs `/with-timestamps` → `voice.wav` (48 kHz) + `words.json`. Dry run by default; `--go` spends characters; the raw response is cached so re-processing is free |
| `build_mix.py` | voice + original music + SFX → `mix.wav`, stems, `cues.md` and `length.json` (−14 LUFS, ≤ −1.2 dBTP, exact frame length) |
| `review_sheet.py` | visual listen-check: `qa_mix.png`, `qa_voice_zoom.png` |
| `lib/` | `dsp.py`, `instruments.py` and `sfx_gen.py` (from `templates/audio/`), `score.py` (music), `sfx_x.py` (SFX cue library) |
| `<slug>/` | per-video output; `sfx.json` holds the hand-placed topic cues |

## Make a short
```
.venv/bin/python audio/tts.py scripts/<slug>/SCRIPT.md audio/<slug>        # dry run: check the text and cost
.venv/bin/python audio/tts.py scripts/<slug>/SCRIPT.md audio/<slug> --go   # once, when the script is final
.venv/bin/python audio/build_mix.py audio/<slug> --shots scripts/<slug>/shots.json [--frames N]
.venv/bin/python audio/review_sheet.py audio/<slug>
```
Per-video plans in `audio/<slug>/`:
- `music.json`: an explicit section list by shot (`hook`, `body`, `mystery`, `explain`, `payoff`; styles may repeat), `overlays` (an `alien` theremin over fantasy shots), `"end": "loop"` (no sting; a riser after the last word), `"reveal_riser": false`, and `"levels"` (section targets in LU vs the voice). Without it, sections come from the script (sentence 1, the question before "You see,", the last sentence).
- `sfx.json`: hand cues (`"at": "end"` puts a cue at a word's end; `"len"` cuts its tail), plus `{"mute": "s17:speed_lines"}` and `{"mute": "s20:transition"}`.

`tts.py` options for a take that is too slow: `--breath-before "year one"` (repeatable), `--breath`, `--gap-scale`, and `--target <s>` (a formant-preserving stretch, at most 1.25x). Re-process from the cached take with `--from-response`.

Without `--frames`, the length is the end of the last word + 0.8 s, rounded up to a whole frame. `length.json` gives the frame count the engine must render. If the engine needs a different length, re-run with `--frames N`: the voice stays the same, and only the tail changes.

`words.json` keeps the script's own tokens, punctuation included (`"corner."`, `Dale's`), one entry per whitespace-separated word of the voice-over. That matches the `shots.json` word counting.
