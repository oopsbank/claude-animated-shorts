# Dynamic word-by-word captions (PIPELINE.md > Captions):
#   - one word at a time (very short words join the next one), hard swap on each word's start, shown 1 f early;
#   - white heavy sans ~7 % of the frame height, thick black outline (~10 % of the size) + soft drop shadow;
#   - centred, baseline ~66 % of the height, nudged off any visible face;
#   - pop-in 1.25 -> 1.0 over 4 f with ease-out + slight overshoot; keywords yellow #ffd23f and bigger;
#   - nothing on screen in silences longer than 0.4 s.
import os, re, math
from PIL import Image, ImageDraw, ImageFont, ImageFilter

FPS = 30
FONT_PATHS = [os.environ.get('ENGINE_CAPTION_FONT', ''), '/usr/share/fonts/opentype/inter/Inter-Black.otf',
              '/usr/share/fonts/opentype/inter/Inter-ExtraBold.otf', '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf']
WHITE, YELLOW, BLACK = (255, 255, 255), (255, 210, 63), (0, 0, 0)
LEAD = 1                   # frames before the word is spoken (spec 0-2)
SILENCE = 0.4              # s: longer gaps clear the caption
# Styles (shots.json "captions": {"style": ...}):
#   'pop' (default): one word, UPPER case, yellow + bigger keywords, strong pop.
#   'sentence': like both leading channels (references/reports/channels_2026-11.md): 1-2 words as written
#   (sentence case, punctuation kept), white only, thinner outline, a small pop, baseline ~70 %.
STYLE = {'name': 'pop'}
NUM_WORDS = set('zero one two three four five six seven eight nine ten eleven twelve twenty thirty forty fifty hundred '
                'thousand million first second third half double'.split())
STOP = set('the a an and or but of to in on at for with by from is are was were be been it its it\'s that this these those '
           'you your he she his her they them their we our i me my so if as do does did can can\'t not no yes why what '
           'how when then than just very into onto out up down over off too also has have had will would'.split())


def clean(w): return re.sub(r"[^\w'\-]", '', w)


def font_path():
    return next(p for p in FONT_PATHS if p and os.path.exists(p))


def keywords(doc, words):
    """Auto keywords: numbers, left/right, content words of the title, the payoff (last content word of the final
    shot), plus any `captions.keywords` (global or per shot)."""
    kw = set(k.lower() for k in doc.get('captions', {}).get('keywords', []))
    for s in doc.get('shots', []): kw |= set(k.lower() for k in s.get('captions', {}).get('keywords', []))
    title = [clean(w).lower() for w in doc.get('title', '').split()]
    kw |= {w for w in title if len(w) > 3 and w not in STOP}
    kw |= {'left', 'right'}
    if words:
        tail = [clean(w['word']).lower() for w in words[-12:]]
        content = [w for w in tail if w and w not in STOP and len(w) > 3]
        if content: kw.add(content[-1])
    return kw


def is_key(w, kw):
    lw = clean(w).lower()
    stem = lw[:-1] if lw.endswith('s') and lw[:-1] in kw else lw
    return bool(lw) and (lw in kw or stem in kw or lw.isdigit() or lw in NUM_WORDS or lw.rstrip('s') in kw)


def schedule(words, doc, n_frames, case='upper'):
    STYLE['name'] = doc.get('captions', {}).get('style', 'pop'); _cache.clear()
    if STYLE['name'] == 'sentence': return _schedule_sentence(words, n_frames)
    """List of caption events: (f_on, f_off, text, key). Short function words (<= 2 letters, said quickly) ride along
    with the next word."""
    kw = keywords(doc, words); ev = []; i = 0
    while i < len(words):
        w = words[i]; text = clean(w['word']); j = i
        while (len(clean(words[j]['word'])) <= 2 and j + 1 < len(words) and words[j + 1]['start'] - words[j]['end'] < 0.12
               and len(text) + len(clean(words[j + 1]['word'])) <= 9):
            j += 1; text = text + ' ' + clean(words[j]['word'])
        key = any(is_key(words[t]['word'], kw) for t in range(i, j + 1))
        f_on = max(0, int(round(w['start'] * FPS)) - LEAD)
        if j + 1 < len(words):
            gap = words[j + 1]['start'] - words[j]['end']
            f_next = int(round(words[j + 1]['start'] * FPS)) - LEAD
            f_off = int(round(words[j]['end'] * FPS)) + 2 if gap > SILENCE else f_next
        else: f_off = int(round(words[j]['end'] * FPS)) + 6
        f_off = min(max(f_off, f_on + 2), n_frames)
        if text: ev.append((f_on, f_off, text.upper() if case == 'upper' else text, key))
        i = j + 1
    return ev


def _schedule_sentence(words, n_frames):
    """1-2 words per caption as written: a word joins the next when both are short, said together (gap < 0.12 s)
    and the first doesn't end a phrase."""
    ev = []; i = 0
    while i < len(words):
        w = words[i]; text = w['word'].strip(); j = i
        if (j + 1 < len(words) and text[-1:] not in '.,!?;:' and words[j + 1]['start'] - words[j]['end'] < 0.12
                and len(text) + len(words[j + 1]['word']) <= 12):
            j += 1; text = text + ' ' + words[j]['word'].strip()
        f_on = max(0, int(round(w['start'] * FPS)) - LEAD)
        if j + 1 < len(words):
            gap = words[j + 1]['start'] - words[j]['end']
            f_next = int(round(words[j + 1]['start'] * FPS)) - LEAD
            f_off = int(round(words[j]['end'] * FPS)) + 2 if gap > SILENCE else f_next
        else: f_off = int(round(words[j]['end'] * FPS)) + 6
        f_off = min(max(f_off, f_on + 2), n_frames)
        if text: ev.append((f_on, f_off, text, False))
        i = j + 1
    return ev


def at(events, f):
    for e in events:
        if e[0] <= f < e[1]: return e
    return None


_cache = {}


def _card(text, key, H):
    """Rendered caption at its resting size (RGBA, tight box) with outline and shadow; cached."""
    k = (text, key, H)
    if k in _cache: return _cache[k]
    sent = STYLE['name'] == 'sentence'
    size = int(H * (0.058 if sent else 0.078 if key else 0.068))
    font = ImageFont.truetype(font_path(), size)
    stroke = max(3, int(size * (0.085 if sent else 0.11)))
    d0 = ImageDraw.Draw(Image.new('L', (1, 1)))
    l, t, r, b = d0.textbbox((0, 0), text, font=font, stroke_width=stroke)
    pad = int(size * 0.3); w, h = r - l + 2 * pad, b - t + 2 * pad
    sh = Image.new('L', (w, h), 0)
    ImageDraw.Draw(sh).text((pad - l, pad - t + int(size * 0.07)), text, font=font, fill=255, stroke_width=stroke, stroke_fill=255)
    sh = sh.filter(ImageFilter.GaussianBlur(size * 0.06)).point(lambda v: int(v * 0.55))
    im = Image.new('RGBA', (w, h), (0, 0, 0, 0)); im.putalpha(sh)
    lay = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    ImageDraw.Draw(lay).text((pad - l, pad - t), text, font=font, fill=YELLOW if key else WHITE, stroke_width=stroke, stroke_fill=BLACK)
    im.alpha_composite(lay)
    base = pad - t + font.getmetrics()[0]                                   # baseline y inside the card
    _cache[k] = (im, base)
    return _cache[k]


def pop(n, key):
    """Scale over the first frames: 1.25 (keywords 1.4) -> 1.0 in 4 f, ease-out with a small overshoot below 1."""
    s0 = 1.08 if STYLE['name'] == 'sentence' else 1.4 if key else 1.25
    if n >= 6: return 1.0
    u = min(1.0, n / 4.0)
    o = 1 + 2.2 * (u - 1) ** 3 + 1.2 * (u - 1) ** 2                         # out_back: overshoots past 1, settles
    return s0 + (1.0 - s0) * o


def draw(img, events, f, faces=(), W=1080, H=1920):
    """Draw the caption for frame f on img (RGB, final frame). faces: screen boxes (x0, y0, x1, y1) to keep clear.
    Returns the caption box or None."""
    e = at(events, f)
    if not e: return None
    f_on, f_off, text, key = e
    im, base = _card(text, key, H)
    s = pop(f - f_on, key)
    if abs(s - 1) > 1e-3: im = im.resize((max(1, int(im.width * s)), max(1, int(im.height * s))), Image.BICUBIC)
    bw, bh = im.size; base_s = base * s
    max_w = W * 0.92
    if bw > max_w:                                                          # long words fit the width
        k = max_w / bw; im = im.resize((int(bw * k), int(bh * k)), Image.BICUBIC); bw, bh = im.size; base_s *= k
    y_base = (0.70 if STYLE['name'] == 'sentence' else 0.66) * H
    # clearance is tested at the largest pop size, so the word never grazes a face mid-pop and never jumps
    r0, _ = _card(text, key, H); smax = 1.08 if STYLE['name'] == 'sentence' else 1.4 if key else 1.25
    pw, ph, pb = r0.width * smax, r0.height * smax, base * smax
    def box(yb): return (W / 2 - pw / 2, yb - pb, W / 2 + pw / 2, yb - pb + ph)
    def hits(b, m=6): return any(not (b[2] < fx0 - m or b[0] > fx1 + m or b[3] < fy0 - m or b[1] > fy1 + m) for fx0, fy0, fx1, fy1 in faces)
    if hits(box(y_base)):                                                   # nudge up past the face; else below it
        for dy in range(20, int(0.4 * H), 20):
            if not hits(box(y_base - dy)) and box(y_base - dy)[1] > 0.12 * H: y_base -= dy; break
            if not hits(box(y_base + dy)) and box(y_base + dy)[3] < 0.9 * H: y_base += dy; break
    x0, y0 = int(W / 2 - bw / 2), int(y_base - base_s)
    out = img.convert('RGBA'); out.alpha_composite(im, (x0, max(0, y0)))
    img.paste(out.convert('RGB'))
    return (x0, y0, x0 + bw, y0 + bh, text)
