# Narrator voice

## Choice
| | |
|---|---|
| Voice | **Liam** (ElevenLabs premade), voice_id `TX3LPaxmHKxFdv7VOQHJ` |
| Labels | male, young, American, "energetic, social media creator", confident |
| Model | `eleven_multilingual_v2` (1 credit per character; stable prosody; supports `/with-timestamps`) |
| Settings | stability **0.50**, similarity_boost **0.75**, style **0.20**, use_speaker_boost **true**, speed **1.10** |
| Output | `mp3_44100_128` (free tier), decoded and resampled to 48 kHz mono 24-bit by `tts.py` |
| Seed | 1234 (same text + settings gives near-identical takes) |

Why Liam: of the premade male English voices on the account, he is the one built for fast, clear, upbeat social delivery. The others are slower or more relaxed (Roger, Chris, Will, Eric, Brian), British-formal (George, Daniel), character voices (Callum, Harry) or Australian (Charlie). The "professional" library voices (Alex Wright and others) are not used: the free tier cannot rely on library voices via the API. Premade voices are always available.

## Test: `voice_test.mp3`
"To turn left on a bike, you first steer right, and you never notice." (68 characters)
- Raw API take: 14 words, 3.81 s (3.7 words/s). Comma pauses were 0.31 s ("bike,") and 0.26 s ("right,").
- After `tts.py` processing (`voice_test_words.json`): words over 3.27 s = 4.3 words/s, longest gap 0.12 s.
  A single sentence has no sentence-end gaps, so a full script lands lower, around 3.8-4.0 words/s.
- Loudness of the raw take: -23.3 LUFS, peak -6.6 dBFS. `build_mix.py` sets the level.

## Knobs if the full take is off-target
- Too fast (>4.1 words/s after processing): set `speed` to 1.05, or raise the `MAX_GAP` values in `tts.py` (cheap, no API call).
- Too slow (<3.5): set `speed` to 1.15 (the maximum is 1.2).
- Flat or monotone: raise `style` to 0.3-0.35. Lower stability (0.4) adds expressiveness but also take-to-take variation.
- Changing the settings means a new paid take. Re-processing a cached take (`--from-response`) is free.

## Quota (free tier, 10,000 characters per month)
- Before the test: 0/10,000. After the test: see BACKLOG/commit notes; the counter can lag.
- A 170-240 word script is about 1,000-1,400 characters, so there is room for about 6 full takes a month. Generate **once**, when the script is final.
