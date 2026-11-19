import json, base64, sys, urllib.request, time
VOICE = sys.argv[1] if len(sys.argv) > 1 else "JBFqnCBsd6RMkjVDRZzb"
text = open("script.txt").read().strip()
body = json.dumps({"text": text, "model_id": "eleven_multilingual_v2",
  "voice_settings": {"stability": 0.62, "similarity_boost": 0.8, "style": 0.0, "use_speaker_boost": True, "speed": 1.0}}).encode()
url = f"https://api.elevenlabs.io/v1/text-to-speech/{VOICE}/with-timestamps?output_format=mp3_44100_192"
for attempt in range(6):
    try:
        req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json", "xi-api-key": "dummy"})
        d = json.load(urllib.request.urlopen(req, timeout=240))
        break
    except Exception as e:
        print("attempt", attempt, e, flush=True); time.sleep(10)
else: sys.exit(1)
open("voice.mp3", "wb").write(base64.b64decode(d["audio_base64"]))
json.dump(d["alignment"], open("alignment.json", "w"))
print("ok", len(d["alignment"]["characters"]))
