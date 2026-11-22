"""Render flat2d shots to video: timeline from words.json, house "sentence" captions, parallel frames.

usage: .venv/bin/python flat2d/render.py WORDS.json OUT.mp4 [--t0 0 --t1 24.2] [--size 540x960] [--fps 30]
                                          [--sheet DIR] [--strip NAME:T:N ...] [--frames-only]
- Shot sNN (flat2d/blood_falls.SHOTS) carries voice-over line NN; it starts 0.1 s before the line's first
  word (s01 at 0) and runs to the next shot.
- Captions (PIPELINE.md > Captions): 1-2 words as written (two short words said together join), Poppins
  Bold 3.7% H, white, 10% black outline, soft shadow, centred; baseline at 70% H nudged to the cleanest
  band of each shot (kit.clean_band on the shot's late frame, faces avoided); a 1.08 -> 1.0 pop over 4
  frames; each caption shows 1 frame before its word; nothing during silences over 0.4 s.
- --sheet DIR: 0.5 s-step contact sheets; --strip NAME:T:N: N consecutive frames from time T in a row.
"""
import json, math, os, re, subprocess, sys, shutil
from multiprocessing import Pool
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from PIL import Image, ImageDraw
import kit, anim
import blood_falls as bf

FPS = 30; LEAD = 0.10


def tag_lines(ws):
    """words.json from tts.py has no line index: tag each word with its SCRIPT.md voice-over line."""
    if all('line' in w for w in ws): return ws
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    txt = open(os.path.join(root, 'scripts', bf.SLUG, 'SCRIPT.md')).read().split('## Voice-over')[1].split('\n## ')[0]
    k = 0
    for li, m in enumerate(re.finditer(r'^\d+\. (.+)$', txt, re.M), 1):
        for _ in m.group(1).split():
            ws[k]['line'] = li; k += 1
    assert k == len(ws), f'SCRIPT.md has {k} words, words.json {len(ws)}'
    return ws


def load(words_path):
    """Shots from bf.SHOT_LIST [(name, line, first word of the line)]: a shot starts LEAD s before its first
    word (s01 at 0) and runs to the next shot; the last one runs to the film end (bf.END or last word + .6)."""
    ws = tag_lines(json.load(open(words_path)))
    lines = {}
    for i, w in enumerate(ws): lines.setdefault(w['line'], []).append(w)
    shots = []
    for k, (name, li, w0) in enumerate(bf.SHOT_LIST):
        t0 = 0.0 if k == 0 else lines[li][w0]['start'] - LEAD
        if k + 1 < len(bf.SHOT_LIST):
            _, l2, w2 = bf.SHOT_LIST[k + 1]; t1 = lines[l2][w2]['start'] - LEAD
        else:
            t1 = getattr(bf, 'END', None) or lines[li][-1]['end'] + .6
        shots.append((name, t0, t1, li, w0))
    return ws, lines, shots


def groups(ws):
    """Caption groups: 1-2 words as written; two short words said together join."""
    out = []; i = 0
    core = lambda w: re.sub(r'[^\w]', '', w['word'])
    while i < len(ws):
        a = ws[i]
        if (i + 1 < len(ws) and ws[i + 1]['line'] == a['line'] and len(core(a)) <= 4 and len(core(ws[i + 1])) <= 4
                and not re.search(r'[,.?!:;]["”]?$', a['word']) and ws[i + 1]['start'] - a['end'] < .15):
            out.append({'text': a['word'] + ' ' + ws[i + 1]['word'], 'start': a['start'], 'end': ws[i + 1]['end']}); i += 2
        else:
            out.append({'text': a['word'], 'start': a['start'], 'end': a['end']}); i += 1
    for g, n in zip(out, out[1:] + [None]):
        show_end = n['start'] - 1 / FPS if n else g['end'] + .3
        if n and n['start'] - g['end'] > .4: show_end = g['end'] + .1     # silence: clear the screen
        g['show'] = (g['start'] - 1 / FPS, show_end)
    return out


def draw_caption(img, text, base, scale=1.0):
    size = int(round(0.037 * img.height * scale)); f = kit.font(size, bold=True)
    w = kit.text_w(text, f); x = (img.width - w) / 2
    base = base + (scale - 1) * size * .3
    sh = kit.layer(img.width, img.height)
    ImageDraw.Draw(sh).text((x + 3, base + 5), text, font=f, fill=(0, 0, 0, 200), anchor='ls',
                            stroke_width=int(size * .16), stroke_fill=(0, 0, 0, 200))
    img.alpha_composite(kit.soft_layer(sh, 7))
    ImageDraw.Draw(img).text((x, base), text, font=f, fill='white', anchor='ls', stroke_width=max(2, int(size * .1)), stroke_fill='black')


def bodies(faces):
    """(torso, legs) boxes under each face box (face_box pads R by 1.15; a stickman is ~10 R tall)."""
    out = []
    for x0, y0, x1, y1 in faces:
        R = (x1 - x0) / 2 / 1.15; hx, hy = (x0 + x1) / 2, (y0 + y1) / 2
        out.append(((hx - R * .8, hy + R, hx + R * .8, hy + R * 6.2), (hx - R * 1.2, hy + R * 6.2, hx + R * 1.2, hy + R * 10)))
    return out


def place_band(img, info, w=0.42 * kit.W, search=0.15, step=6, k=0.012):
    size = int(0.037 * kit.H); base = 0.70 * kit.H
    x0, x1 = (kit.W - w) / 2 - 30, (kit.W + w) / 2 + 30
    hit = lambda a, b, box: a < box[3] and b > box[1] and x0 < box[2] and x1 > box[0]
    faces = list(info.get('faces', [])) + list(info.get('avoid', []))
    for x0_, y0_, x1_, y1_ in info.get('faces', []):                  # the role label floats above each head
        faces.append(((x0_ + x1_) / 2 - 190, y0_ - 150, (x0_ + x1_) / 2 + 190, y0_ - 10))
    bods = bodies(info.get('faces', []))
    best = None
    for hard in (faces + [t_ for t_, l_ in bods], faces):                # torsos are off limits too, unless no band is free
      for dy in range(-int(search * kit.H), int(search * kit.H) + 1, step):
        b = base + dy; a_, b_ = b - size, b + size * .32
        if any(hit(a_, b_, f) for f in hard): continue
        cost = kit.busy(img, (x0, a_, x1, b_)) + k * abs(dy)
        cost += sum(60 for t_, l_ in bods if hit(a_, b_, t_)) + sum(14 for t_, l_ in bods if hit(a_, b_, l_))
        if best is None or cost < best[0]: best = (cost, b)
      if best: break
    return best[1] if best else base


class Film:
    def __init__(self, words_path, band_cache=None):
        self.ws, self.lines, self.shots = load(words_path)
        self.caps = groups(self.ws)
        anim.BEATS = [w['start'] for w in self.ws if len(re.sub(r'[^\w]', '', w['word'])) >= 5]
        self.band_cache = band_cache; self.bands = {}
        if band_cache and os.path.exists(band_cache): self.bands = json.load(open(band_cache))

    def shot_at(self, T):
        for s in self.shots:
            if s[1] <= T < s[2]: return s
        return self.shots[-1]

    def raw(self, T):
        name, t0, t1, li, w0 = self.shot_at(T)
        lw = self.lines[li]
        cue = lambda i: lw[min(i, len(lw) - 1)]['start'] - t0          # i = word index in the voice-over LINE
        anim.NOW = T
        return bf.SHOTS[name](T - t0, t1 - t0, cue), name

    def band(self, name):
        """Caption baseline per shot: the cleanest band within +-10% of 70% on a late frame of the shot.
        Faces are never covered; torsos and legs (body boxes under each face) cost extra, so the caption
        moves off a body when a cleaner band is near (NOTES v3 open note)."""
        if name not in self.bands:
            s = [x for x in self.shots if x[0] == name][0]
            (img, info), _ = self.raw(s[2] - .35)
            f = kit.font(int(round(0.037 * kit.H)), bold=True)
            ws = [kit.text_w(g['text'], f) for g in self.caps if s[1] <= g['start'] < s[2]]
            self.bands[name] = place_band(img, info, w=max(ws + [0.2 * kit.W]))
        return self.bands[name]

    def frame(self, T):
        (img, info), name = self.raw(T)
        base = self.band(name)
        t0 = self.shot_at(T)[1]; u = T - t0
        if t0 > 0 and u < .2 and name not in getattr(bf, 'NO_PUNCH', ()):                                    # cut: a 6-frame punch-in settle + a 3-frame light flash
            img = anim.camera(img, 1 + .045 * (1 - anim.ease_out(u / .2)))
            if u < .1:
                img.alpha_composite(Image.new('RGBA', img.size, (255, 255, 255, int(70 * (1 - u / .1)))))
        for g in self.caps:
            a, b = g['show']
            if a <= T < b:
                k = (T - a) * FPS
                draw_caption(img, g['text'], base, 1.08 - .08 * anim.smooth(k / 4))
                break
        return img.convert('RGB')


_film = None
def _init(words, cache):
    global _film; _film = Film(words, cache)


def _job(args):
    f, T, out, size = args
    im = _film.frame(T)
    if size != im.size: im = im.resize(size, Image.LANCZOS)
    im.save(os.path.join(out, f'f_{f:05d}.png'), compress_level=1)
    return f


def sheet(frames_dir, n_frames, out_dir, step=0.5, cols=8, thumb=(135, 240)):
    os.makedirs(out_dir, exist_ok=True)
    idx = list(range(0, n_frames, int(step * FPS)))
    per = cols * 3; paths = []
    for p in range(0, len(idx), per):
        chunk = idx[p:p + per]; rows = math.ceil(len(chunk) / cols)
        S = Image.new('RGB', (cols * (thumb[0] + 6) + 6, rows * (thumb[1] + 30) + 6), (24, 24, 30))
        d = ImageDraw.Draw(S)
        for i, f in enumerate(chunk):
            im = Image.open(os.path.join(frames_dir, f'f_{f:05d}.png')).resize(thumb, Image.LANCZOS)
            x, y = 6 + (i % cols) * (thumb[0] + 6), 6 + (i // cols) * (thumb[1] + 30)
            S.paste(im, (x, y)); d.text((x + 4, y + thumb[1] + 4), f'{f / FPS:.1f}s', fill=(230, 230, 230), font=kit.font(18, True))
        path = os.path.join(out_dir, f'sheet_{p // per + 1}.png'); S.save(path); paths.append(path)
    return paths


def strip(frames_dir, out_path, f0, n, step=2, h=480):
    ims = [Image.open(os.path.join(frames_dir, f'f_{f:05d}.png')) for f in range(f0, f0 + n * step, step)]
    w = int(ims[0].width * h / ims[0].height)
    S = Image.new('RGB', (n * (w + 6) + 6, h + 40), (24, 24, 30)); d = ImageDraw.Draw(S)
    for i, im in enumerate(ims):
        S.paste(im.resize((w, h), Image.LANCZOS), (6 + i * (w + 6), 6))
        d.text((10 + i * (w + 6), h + 10), f'{(f0 + i * step) / FPS:.2f}s', fill=(230, 230, 230), font=kit.font(20, True))
    S.save(out_path)


if __name__ == '__main__':
    a = sys.argv[1:]
    words, out = a[0], a[1]
    opt = lambda k, d: a[a.index(k) + 1] if k in a else d
    t0, t1 = float(opt('--t0', 0)), opt('--t1', None)
    size = tuple(int(v) for v in opt('--size', '540x960').split('x'))
    film = Film(words)
    t1 = float(t1) if t1 else film.shots[-1][2]
    frames_dir = out + '.frames'; os.makedirs(frames_dir, exist_ok=True)
    cache = out + '.bands.json'
    for name, *_ in film.shots: film.band(name)
    print({k: round(v / kit.H, 3) for k, v in film.bands.items()})                             # caption bands, once per shot
    json.dump(film.bands, open(cache, 'w'))
    n = int(round((t1 - t0) * FPS))
    jobs = [(f, t0 + f / FPS, frames_dir, size) for f in range(n)]
    with Pool(int(opt('--procs', os.cpu_count())), _init, (words, cache)) as pool:
        for i, _ in enumerate(pool.imap_unordered(_job, jobs, chunksize=4)):
            if i % 60 == 0: print('frame', i, '/', n, flush=True)
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-framerate', str(FPS), '-i', f'{frames_dir}/f_%05d.png',
                    '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-crf', '20', '-preset', 'medium', '-movflags', '+faststart', out], check=True)
    print('wrote', out, os.path.getsize(out) // 1024, 'KB')
    if '--sheet' in a:
        print(sheet(frames_dir, n, opt('--sheet', None)))
    for k, v in enumerate(a):
        if v == '--strip':
            nm, T, N = a[k + 1].split(':')
            strip(frames_dir, os.path.join(opt('--sheet', os.path.dirname(out)), f'strip_{nm}.png'),
                  int(round((float(T) - t0) * FPS)), int(N))
    for s in film.shots: print(s)
