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


def load(words_path):
    ws = json.load(open(words_path))
    lines = {}
    for i, w in enumerate(ws): lines.setdefault(w['line'], []).append(w)
    shots = []
    names = list(bf.SHOTS)
    for k, name in enumerate(names):
        li = bf.LINE_OF[name]
        t0 = 0.0 if k == 0 else lines[li][0]['start'] - LEAD
        nxt = lines.get(li + 1)
        t1 = nxt[0]['start'] - LEAD if nxt else lines[li][-1]['end'] + .6
        shots.append((name, t0, t1, li))
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


class Film:
    def __init__(self, words_path, band_cache=None):
        self.ws, self.lines, self.shots = load(words_path)
        self.caps = groups(self.ws)
        self.band_cache = band_cache; self.bands = {}
        if band_cache and os.path.exists(band_cache): self.bands = json.load(open(band_cache))

    def shot_at(self, T):
        for s in self.shots:
            if s[1] <= T < s[2]: return s
        return self.shots[-1]

    def raw(self, T):
        name, t0, t1, li = self.shot_at(T)
        lw = self.lines[li]
        cue = lambda i: lw[min(i, len(lw) - 1)]['start'] - t0
        return bf.SHOTS[name](T - t0, t1 - t0, cue), name

    def band(self, name):
        if name not in self.bands:
            s = [x for x in self.shots if x[0] == name][0]
            (img, info), _ = self.raw(s[2] - .35)
            if name == 's01': b = 0.70 * kit.H                               # NOTES: s01 keeps the fixed 70% line
            else: b = kit.clean_band(img, 0.42 * kit.W, int(0.037 * kit.H), avoid=info['faces'])
            self.bands[name] = b
        return self.bands[name]

    def frame(self, T):
        (img, info), name = self.raw(T)
        base = self.band(name)
        t0 = self.shot_at(T)[1]; u = T - t0
        if t0 > 0 and u < .2:                                    # cut: a 6-frame punch-in settle + a 3-frame light flash
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
    for name, *_ in film.shots: film.band(name)                             # caption bands, once per shot
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
