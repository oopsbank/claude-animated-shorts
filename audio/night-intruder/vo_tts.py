#!/usr/bin/env python3
"""The Director's whispered narration (ME): 4 lines, each generated ONCE with ElevenLabs eleven_v3 /with-timestamps.
Raw JSON responses are cached in vo_raw/ (re-processing is free; a cached line is never re-requested).

    python3 audio/night-intruder/vo_tts.py          # dry run: texts + character count
    python3 audio/night-intruder/vo_tts.py --go     # request the lines that are not cached yet
"""
import json
import os
import sys
import urllib.request

OD = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(OD, "vo_raw")
API = "https://api.elevenlabs.io"
KEY = os.environ.get("ELEVENLABS_API_KEY", "proxy-injected")   # the proxy injects the real key
VOICE_ID = "bIHbv24MWmeRgasZH58o"         # Will (premade): young American male, relaxed / chill
MODEL_ID = "eleven_v3"
SETTINGS = {"stability": 0.5, "similarity_boost": 0.75}         # v3 "Natural"
FORMAT = "mp3_44100_128"
LINES = [
    "[whispers] Midnight, exactly... a noise downstairs. Not the wind.",
    "[whispers] [nervous] There was a child in the house. I grabbed the desk lamp... praying it wasn't what I thought.",
    "[whispers] He was alone. [exhales] If I could just get behind him...",
    "[whispers] I got it wrong. They... weren't alone.",
]


def main():
    os.makedirs(RAW, exist_ok=True)
    print("characters:", sum(len(t) for t in LINES))
    for i, t in enumerate(LINES, 1):
        p = os.path.join(RAW, f"line{i}.json")
        print(i, len(t), "cached" if os.path.exists(p) else "new", t)
        if "--go" not in sys.argv or os.path.exists(p):
            continue
        req = urllib.request.Request(f"{API}/v1/text-to-speech/{VOICE_ID}/with-timestamps?output_format={FORMAT}",
                                     data=json.dumps({"text": t, "model_id": MODEL_ID, "voice_settings": SETTINGS,
                                                      "seed": 2611}).encode(),
                                     headers={"xi-api-key": KEY, "Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=300) as r:
            d = json.loads(r.read())
        d["request"] = {"text": t, "voice_id": VOICE_ID, "model_id": MODEL_ID, "voice_settings": SETTINGS}
        json.dump(d, open(p, "w"))


if __name__ == "__main__":
    main()
