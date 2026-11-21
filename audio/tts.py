#!/usr/bin/env python3
"""Voice-over from a SCRIPT.md via ElevenLabs /with-timestamps -> voice.wav (48 kHz) + words.json.

    .venv/bin/python audio/tts.py scripts/<slug>/SCRIPT.md audio/<slug>          # dry run: shows text + cost
    .venv/bin/python audio/tts.py scripts/<slug>/SCRIPT.md audio/<slug> --go     # spends characters ONCE
    .venv/bin/python audio/tts.py --from-response audio/<slug>/_tts_response.json audio/<slug>   # re-process, free

The account is on the FREE tier (10,000 chars/month): without --go nothing is sent. The raw API response is cached in
out_dir/_tts_response.json and is reused automatically, so re-processing (trim, pause tightening, word refinement)
never spends characters again. The proxy injects the API key; the header below is a placeholder.

Processing after the API call:
  1. decode the MP3 to 48 kHz mono float (ffmpeg);
  2. words from the character alignment, then each word's start/end snapped to the waveform (the API's end time of a
     word before a comma includes the pause that follows it);
  3. pause tightening: every gap between words longer than MAX_GAP (by punctuation) is shortened by cutting its
     quietest part with an equal-power crossfade; later timestamps shift with it (reference: <1 s of gaps >0.25 s);
  4. trim leading/trailing silence (LEAD before the first word, TAIL after the last);
  5. write voice.wav (48 kHz, mono, 24-bit), words.json [{word, start, end}] and voice_report.json.
"""
import argparse
import base64
import json
import math
import os
import re
import subprocess
import sys
import urllib.request

import numpy as np

SR = 48000
API = "https://api.elevenlabs.io"
KEY = os.environ.get("ELEVENLABS_API_KEY", "proxy-injected")   # the proxy replaces it

# chosen voice: see audio/VOICE.md
VOICE_ID = "TX3LPaxmHKxFdv7VOQHJ"        # Liam (premade): young American male, energetic, clear
MODEL_ID = "eleven_multilingual_v2"
SETTINGS = {"stability": 0.5, "similarity_boost": 0.75, "style": 0.2, "use_speaker_boost": True, "speed": 1.1}
FORMAT = "mp3_44100_128"                  # available on the free tier; decoded and resampled to 48 kHz

LEAD, TAIL = 0.04, 0.20                   # s of silence kept before the first / after the last word
MAX_GAP = {".": 0.20, "!": 0.20, "?": 0.22, ",": 0.12, ";": 0.14, ":": 0.14, "-": 0.12, "": 0.10}
XFADE = 0.008
BREATH = 0.32                             # kept after a closing quote and before "You see," / "Wait,"
MARKS = None                              # --breath-before phrases: they get the long breath
MARK_BREATH = 1.4                         # breath before a --breath-before phrase, x BREATH
GAP_SCALE = 1.0                           # --gap-scale: multiplies every gap limit and the breath
TARGET = None                             # --target: final voice length in s (rubberband time-stretch, max 1.25x)
BREATH_BEFORE = re.compile(r"(you see|wait)\b")   # --breath-before adds phrases (e.g. "Month one", "Year one")
FLOOR_DB = 45.0                           # word edges: 10 ms RMS above (speech peak level - FLOOR_DB)


# ------------------------------------------------------------------ SCRIPT.md -> voice-over text
VO_HEAD = re.compile(r"^(#{1,6})\s*(.*?(voice[\s-]?over|\bvo\b|narration).*)$", re.I)


def extract_vo(md, section=None):
    lines = md.splitlines()
    start, level, best = None, None, 0
    for i, ln in enumerate(lines):
        m = re.match(r"^(#{1,6})\s*(.*)$", ln)
        if not m:
            continue
        h = m.group(2).strip().lower()
        if section:
            score = 2 if section.lower() in h else 0
        else:   # a heading that STARTS with voice-over beats one that merely mentions it ("Facts (said in the voice-over)")
            score = 2 if re.match(r"(voice[\s-]?over|vo\b|narration)", h) else (1 if VO_HEAD.match(ln) else 0)
        if score > best:
            start, level, best = i + 1, len(m.group(1)), score
    if start is None:
        raise SystemExit("no voice-over section found in SCRIPT.md (use --section '<heading text>')")
    body = []
    for ln in lines[start:]:
        m = re.match(r"^(#{1,6})\s", ln)
        if m and len(m.group(1)) <= level:
            break
        body.append(ln)
    # a section written as a list (one item per shot): take only the items, skip notes like "**Word count: ...**"
    if sum(bool(re.match(r"^\s*([-*+]|\d+[.)])\s+", ln)) for ln in body) >= 3:
        body = [ln for ln in body if re.match(r"^\s*([-*+]|\d+[.)])\s+", ln)]
    out, fence = [], False
    for ln in body:
        m = re.match(r"^(#{1,6})\s", ln)
        s = ln.strip()
        if s.startswith("```"):
            fence = not fence
            continue
        if fence or not s or m or s.startswith("|") or s.startswith("<!--") or re.fullmatch(r"[-*_=]{3,}", s):
            continue
        s = re.sub(r"<!--.*?-->", "", s)
        s = re.sub(r"^>\s*", "", s)
        s = re.sub(r"^([-*+]|\d+[.)])\s+", "", s)
        s = re.sub(r"^\(?\[?s\d{1,3}\]?\)?[:.]?\s+", "", s, flags=re.I)        # shot ids: s01:, [s01], (s01)
        s = re.sub(r"\[[^\]]*\]|\{[^}]*\}", "", s)                              # [stage directions], {notes}
        s = re.sub(r"\*\*|__|`", "", s)
        s = re.sub(r"(?<!\w)[*_](?=\S)|(?<=\S)[*_](?!\w)", "", s)              # *italic* / _italic_
        s = re.sub(r"\s+", " ", s).strip()
        if s:
            out.append(s)
    text = " ".join(out).strip()
    if not text:
        raise SystemExit("voice-over section is empty")
    return text


# ------------------------------------------------------------------ API
def api(path, body=None):
    req = urllib.request.Request(API + path, data=None if body is None else json.dumps(body).encode(),
                                 headers={"xi-api-key": KEY, "Content-Type": "application/json"},
                                 method="GET" if body is None else "POST")
    with urllib.request.urlopen(req, timeout=300) as r:
        return json.loads(r.read())


def quota():
    d = api("/v1/user/subscription")
    return d["character_count"], d["character_limit"], d.get("tier")


def synthesize(text):
    return api(f"/v1/text-to-speech/{VOICE_ID}/with-timestamps?output_format={FORMAT}",
               {"text": text, "model_id": MODEL_ID, "voice_settings": SETTINGS, "seed": 1234})


# ------------------------------------------------------------------ audio
def decode_mp3(b, tmpdir):
    p = os.path.join(tmpdir, "_tts_raw.mp3")
    with open(p, "wb") as f:
        f.write(b)
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", p, "-ac", "1", "-ar", str(SR), "-f", "f32le", "-"],
                         check=True, capture_output=True).stdout
    os.remove(p)
    return np.frombuffer(raw, np.float32).astype(np.float64)


def rms_db(x, win=0.010):
    w = int(win * SR)
    e = np.sqrt(np.convolve(x * x, np.ones(w) / w, "same"))
    return 20 * np.log10(e + 1e-9)


def words_from_alignment(al):
    ch, t0, t1 = al["characters"], al["character_start_times_seconds"], al["character_end_times_seconds"]
    words, cur = [], None
    for c, a, b in zip(ch, t0, t1):
        if c.isspace():
            if cur:
                words.append(cur)
            cur = None
        elif cur is None:
            cur = {"word": c, "start": a, "end": b}
        else:
            cur["word"] += c
            cur["end"] = b
    if cur:
        words.append(cur)
    # tokens of pure punctuation ("—", "-") merge into the previous word
    out = []
    for w in words:
        if out and not re.search(r"\w", w["word"]):
            out[-1]["word"] += " " + w["word"] if w["word"] in "—–-" else w["word"]
        else:
            out.append(w)
    return out


def refine(words, x):
    """snap each word's edges to the waveform: start = first loud 10 ms frame, end = last loud frame (+20 ms)"""
    db = rms_db(x)
    thr = np.percentile(db[db > -70], 95) - FLOOR_DB if np.any(db > -70) else -60
    loud = db > thr
    n = len(x)
    for i, w in enumerate(words):
        a, b = int(w["start"] * SR), min(n, int(w["end"] * SR))
        lo = max(0, a - int(0.06 * SR)) if i == 0 or words[i - 1]["end"] < w["start"] - 0.06 else a
        seg = np.where(loud[lo:b])[0]
        if len(seg):
            w["start"] = max((lo + seg[0]) / SR - 0.01, 0.0)
            w["end"] = min((lo + seg[-1]) / SR + 0.02, b / SR)
        w["end"] = max(w["end"], w["start"] + 0.04)
    for i in range(1, len(words)):                       # keep order
        words[i]["start"] = max(words[i]["start"], words[i - 1]["end"])
        words[i]["end"] = max(words[i]["end"], words[i]["start"] + 0.02)
    return thr


def gap_limit(word):
    p = re.sub(r"[\"'”’)\]]+$", "", word)[-1:]
    if p in "—–":
        p = "-"
    return MAX_GAP.get(p, MAX_GAP[""]) * GAP_SCALE


def cut(x, a, b):
    """remove samples [a, b) with an equal-power crossfade of XFADE"""
    f = int(XFADE * SR)
    if a - f < 0 or b + f > len(x):
        return np.concatenate([x[:a], x[b:]])
    u = np.linspace(0, np.pi / 2, f)
    mix = x[a - f:a] * np.cos(u) + x[b:b + f] * np.sin(u)
    return np.concatenate([x[:a - f], mix, x[b + f:]])


def tighten(words, x):
    """shorten long pauses, right to left, cutting the quietest stretch of each gap"""
    db = rms_db(x, 0.005)
    cuts = []
    for i in range(len(words) - 2, -1, -1):
        e, s = words[i]["end"], words[i + 1]["start"]
        lim = gap_limit(words[i]["word"])
        nxt = " ".join(w["word"] for w in words[i + 1:i + 3]).lower()
        if MARKS and MARKS.match(nxt):
            lim = BREATH * MARK_BREATH   # before a time marker / pivot ("Year one", "You see,"): the longest breath
        elif re.search(r"[.!?,][\"”’]$", words[i]["word"]) or BREATH_BEFORE.match(nxt):
            lim = BREATH                                    # end of a quote, or a breath before the pivot / mystery
        elif lim >= 0.2:
            lim += 0.03 * math.sin(i * 2.399)               # sentence gaps vary 0.17-0.23 s, not one fixed value
        excess = (s - e) - lim
        if excess < 0.02:
            continue
        a, b = int((e + 0.03) * SR), int((s - 0.03) * SR)      # never cut into the words' own edges
        k = int(excess * SR)
        if b - a < k + 2 * int(XFADE * SR):
            continue
        p = np.concatenate([[0], np.cumsum(10 ** (db[a:b] / 10))])
        j = int(np.argmin(p[k:] - p[:-k])) if b - a > k else 0
        c0 = a + j
        n0 = len(x)
        x = cut(x, c0, c0 + k)
        dt = (n0 - len(x)) / SR        # the crossfade removes XFADE more than k: shift by what was really removed
        for w in words[i + 1:]:
            w["start"] -= dt
            w["end"] -= dt
        cuts.append((round(c0 / SR, 3), round(dt, 3), words[i]["word"]))
    return x, cuts[::-1]


def trim(words, x):
    a = max(0, int((words[0]["start"] - LEAD) * SR))
    b = min(len(x), int((words[-1]["end"] + TAIL) * SR))
    x = x[a:b].copy()
    f = int(0.005 * SR)
    x[:f] *= np.linspace(0, 1, f)
    x[-f:] *= np.linspace(1, 0, f)
    for w in words:
        w["start"] -= a / SR
        w["end"] -= a / SR
    return x


def write_wav24(path, x):
    import wave
    q = np.clip(np.round(x * 8388607.0), -8388608, 8388607).astype("<i4")
    data = q.view(np.uint8).reshape(-1, 4)[:, :3].tobytes()
    with wave.open(path, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(3)
        w.setframerate(SR)
        w.writeframes(data)


def pacing(words):
    gaps = [words[i + 1]["start"] - words[i]["end"] for i in range(len(words) - 1)]
    span = words[-1]["end"] - words[0]["start"]
    return {"words": len(words), "speech_span_s": round(span, 3), "words_per_s": round(len(words) / span, 3),
            "gaps_over_0.25_s": sum(1 for g in gaps if g > 0.25),
            "gaps_over_0.25_total_s": round(sum(g for g in gaps if g > 0.25), 3),
            "max_gap_s": round(max(gaps) if gaps else 0, 3),
            "mean_gap_s": round(float(np.mean(gaps)) if gaps else 0, 3)}


def stretch(x, tempo, tmpdir):
    """pitch- and formant-preserving time-stretch (ffmpeg rubberband, short window for speech); time scales by 1/tempo"""
    pad = int(0.5 * SR)                                  # rubberband drops the last ~30 ms: pad, stretch, cut back
    raw = np.concatenate([x, np.zeros(pad)]).astype(np.float32).tobytes()
    out = subprocess.run(["ffmpeg", "-v", "error", "-f", "f32le", "-ar", str(SR), "-ac", "1", "-i", "-", "-af",
                          f"rubberband=tempo={tempo:.5f}:pitchq=quality:formant=preserved:transients=mixed:"
                          "detector=soft:window=short", "-f", "f32le", "-"], input=raw, check=True,
                         capture_output=True).stdout
    y = np.frombuffer(out, np.float32).astype(np.float64)[: int(round(len(x) / tempo))]
    print(f"time-stretch {tempo:.3f}x: {len(x) / SR:.2f} s -> {len(y) / SR:.2f} s")
    return y


def check_alignment(words, x):
    """every word must sit on sound, at the start AND the end of the file (a drift once silenced the last word)"""
    db = rms_db(x)
    thr = np.percentile(db[db > -70], 95) - FLOOR_DB
    bad = [(i, w["word"], round(w["start"], 2)) for i, w in enumerate(words)
           if db[int(w["start"] * SR): max(int(w["end"] * SR), int(w["start"] * SR) + 1)].max() < thr]
    if bad:
        raise SystemExit(f"ALIGNMENT ERROR: {len(bad)} words on silence: {bad[:6]}")
    if words[-1]["end"] > len(x) / SR + 0.005:
        raise SystemExit(f"ALIGNMENT ERROR: last word ends {words[-1]['end']:.3f} s, after the audio ({len(x) / SR:.3f} s)")


def process(resp, out_dir):
    x = decode_mp3(base64.b64decode(resp["audio_base64"]), out_dir)
    al = resp.get("alignment") or resp["normalized_alignment"]   # original spelling, as in the script
    words = words_from_alignment(al)
    raw = pacing([dict(w) for w in words])
    refine(words, x)
    before = pacing(words)
    x, cuts = tighten(words, x)
    tempo = 1.0
    if TARGET:
        cur = (words[-1]["end"] + TAIL) - max(0.0, words[0]["start"] - LEAD)
        tempo = cur / TARGET
        if tempo > 1.25:
            raise SystemExit(f"needs a {tempo:.2f}x stretch: over the 1.25x quality limit")
        if abs(tempo - 1) > 0.005:
            x = stretch(x, tempo, out_dir)
            for w in words:
                w["start"] /= tempo
                w["end"] /= tempo
    x = trim(words, x)
    peak = float(np.max(np.abs(x)))
    if peak > 0.98:
        x *= 0.98 / peak
    check_alignment(words, x)
    write_wav24(os.path.join(out_dir, "voice.wav"), x)
    wj = [{"word": w["word"], "start": round(w["start"], 3), "end": round(w["end"], 3)} for w in words]
    with open(os.path.join(out_dir, "words.json"), "w") as f:
        json.dump(wj, f, indent=1, ensure_ascii=False)
    rep = {"tempo": round(tempo, 4), "gap_scale": GAP_SCALE, "voice_id": VOICE_ID, "model_id": MODEL_ID, "settings": SETTINGS, "duration_s": round(len(x) / SR, 3),
           "pacing_api_raw": raw, "pacing_refined": before, "pacing_final": pacing(wj), "pause_cuts": cuts}
    with open(os.path.join(out_dir, "voice_report.json"), "w") as f:
        json.dump(rep, f, indent=1)
    print(json.dumps({k: rep[k] for k in ("duration_s", "pacing_refined", "pacing_final")}, indent=1))
    print(f"{len(cuts)} pauses tightened, {sum(c[1] for c in cuts):.2f} s removed")


def main():
    global MARKS, BREATH, GAP_SCALE, TARGET
    ap = argparse.ArgumentParser()
    ap.add_argument("script", nargs="?", help="SCRIPT.md (or a .txt with the plain voice-over)")
    ap.add_argument("out_dir")
    ap.add_argument("--section", help="heading text of the voice-over section (default: 'Voice-over'/'VO'/'Narration')")
    ap.add_argument("--go", action="store_true", help="really call the API (spends characters)")
    ap.add_argument("--force", action="store_true", help="ignore a cached _tts_response.json (spends characters)")
    ap.add_argument("--from-response", help="process an existing API response JSON, no API call")
    ap.add_argument("--breath-before", action="append", default=[],
                    help="phrase that gets a breath before it (repeatable), e.g. 'month one'")
    ap.add_argument("--breath", type=float, help=f"breath length in s (default {BREATH})")
    ap.add_argument("--gap-scale", type=float, help="multiply every pause limit (e.g. 0.85 for a slow take)")
    ap.add_argument("--target", type=float, help="final voice length in s: time-stretch the take to it (<= 1.25x)")
    a = ap.parse_args()
    if a.breath_before:
        MARKS = re.compile(r"(" + "|".join(re.escape(p.lower()) for p in a.breath_before) + r")\b")
    if a.breath:
        BREATH = a.breath
    if a.gap_scale:
        GAP_SCALE = a.gap_scale
    if a.target:
        TARGET = a.target
    os.makedirs(a.out_dir, exist_ok=True)
    cache = os.path.join(a.out_dir, "_tts_response.json")

    if a.from_response:
        with open(a.from_response) as f:
            return process(json.load(f), a.out_dir)

    with open(a.script) as f:
        src = f.read()
    text = src.strip() if a.script.endswith(".txt") else extract_vo(src, a.section)
    with open(os.path.join(a.out_dir, "vo_text.txt"), "w") as f:
        f.write(text + "\n")
    print(f"voice-over: {len(text.split())} words, {len(text)} characters\n---\n{text}\n---")

    if os.path.exists(cache) and not a.force:
        with open(cache) as f:
            resp = json.load(f)
        if resp.get("_text") == text:
            print("cached response matches the text: re-processing without an API call")
            return process(resp, a.out_dir)
        raise SystemExit("cached response is for a DIFFERENT text; pass --force --go to regenerate (spends characters)")

    used, limit, tier = quota()
    print(f"quota before: {used}/{limit} ({tier}); this call costs ~{len(text)}")
    if not a.go:
        print("dry run: add --go to generate")
        return
    if used + len(text) > limit:
        raise SystemExit("not enough characters left this month")
    resp = synthesize(text)
    resp["_text"] = text
    with open(cache, "w") as f:
        json.dump(resp, f)
    used2, _, _ = quota()
    print(f"quota after: {used2}/{limit} (this call: {used2 - used})")
    process(resp, a.out_dir)


if __name__ == "__main__":
    main()
