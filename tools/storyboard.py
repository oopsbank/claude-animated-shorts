# Storyboard: one real engine frame per shot (plus one per insert), on a labelled sheet, BEFORE the voice-over.
# It uses stand-in timings, so it costs no ElevenLabs characters and ~2-4 min of CPU instead of a full render.
# The Director and one reviewer look at this sheet; staging, size, left/right and readability are fixed here.
# usage: .venv/bin/python tools/storyboard.py scripts/<slug>/shots.json OUT_DIR [words.json]
import os, sys, json, subprocess, textwrap
from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
sys.path.insert(0, os.path.join(ROOT, 'engine'))
import anim  # noqa: E402

shots_p, out = sys.argv[1], sys.argv[2]
os.makedirs(out, exist_ok=True)
words_p = sys.argv[3] if len(sys.argv) > 3 else os.path.join(out, 'stand_in_words.json')
if len(sys.argv) <= 3:
    subprocess.run([sys.executable, os.path.join(ROOT, 'engine', 'fake_words.py'), shots_p, words_p], check=True, stdout=subprocess.DEVNULL)
shots = json.load(open(shots_p))['shots']; words = json.load(open(words_p))
spans = anim.shot_spans(shots, words)

picks = []                                   # (frame, label, text)
for s, sp in zip(shots, spans):
    w = (sp['w0'], sp['w1'])
    # the moment that sells the shot: just after its last body beat, else 60% through
    ats = [b.get('at_word', 0) for c in s.get('characters', []) for b in c.get('beats', []) if set(b) - {'at_word', 'expr'}]
    ats += [e.get('at_word', 0) for e in s.get('fx', [])]
    f = anim.beat_frame(w, words, max(ats))[1] + 8 if ats else int(sp['f0'] + 0.6 * (sp['f1'] - sp['f0']))
    f = min(max(f, sp['f0'] + 4), sp['f1'] - 4)
    ins = next((c['insert'] for c in s.get('characters', []) if c.get('insert')), None)
    fi = anim.beat_frame(w, words, ins.get('at_word', 0))[1] + 10 if ins else None
    if ins:                                  # the main pick shows the main plate, not the cut-in
        a0 = anim.beat_frame(w, words, ins.get('at_word', 0))[1] - anim.LEAD
        a1 = anim.beat_frame(w, words, ins['until_word'])[1] - anim.LEAD if 'until_word' in ins else sp['f1']
        if a0 <= f < a1: f = max(sp['f0'] + 4, a0 - 6) if a0 - 6 > sp['f0'] + 4 else min(sp['f1'] - 4, a1 + 6)
    # shots whose framing or picture changes a lot get an opening frame too (an XCU that pulls out, a flood that rolls in)
    cam = s.get('camera') or {}
    if (cam.get('glides') or cam.get('zoom')) and f - sp['f0'] > 24:
        picks.append((sp['f0'] + 8, s.get('id', '') + ' open', ''))
    picks.append((f, s.get('id', ''), s['text']))
    if ins and sp['f0'] <= fi < sp['f1'] and all(abs(fi - p[0]) > 6 for p in picks): picks.append((fi, s.get('id', '') + ' insert', ''))
picks.sort()

env = dict(os.environ, ENGINE_STANDIN='0', ENGINE_QUIET='1')
subprocess.run([sys.executable, os.path.join(ROOT, 'engine', 'render_video.py'), shots_p, words_p, out,
                '--frames', ','.join(str(p[0]) for p in picks) + ',', '--no-mp4'], check=True, env=env)

# labelled sheet: 6 per row, 270x480 thumbs + 3 lines of text
cw, ch, th = 270, 480, 64; cols = 6; rows = (len(picks) + cols - 1) // cols
sheet = Image.new('RGB', (cols * cw, rows * (ch + th)), (24, 20, 28)); d = ImageDraw.Draw(sheet)
try: font = ImageFont.truetype('DejaVuSans.ttf', 13); bold = ImageFont.truetype('DejaVuSans-Bold.ttf', 15)
except OSError: font = bold = ImageFont.load_default()
for i, (f, label, text) in enumerate(picks):
    x, y = (i % cols) * cw, (i // cols) * (ch + th)
    p = os.path.join(out, 'frames', f'f_{f:05d}.jpg')
    if os.path.exists(p): sheet.paste(Image.open(p).convert('RGB').resize((cw, ch)), (x, y))
    d.text((x + 6, y + ch + 3), f'{label}  ({f / anim.FPS:.1f}s)', fill=(255, 210, 63), font=bold)
    for j, line in enumerate(textwrap.wrap(text, 38)[:2]): d.text((x + 6, y + ch + 22 + 16 * j), line, fill=(230, 230, 230), font=font)
sheet.save(os.path.join(out, 'storyboard.jpg'), quality=85)
print(os.path.join(out, 'storyboard.jpg'), f'{len(picks)} frames')
