# Builds fx/previews/<name>.png strips (t = 0, .25, .5, .75, 1 over a day and a night tile), a contact sheet of
# denser samples for timing review, fx/previews/fx_demo.gif, and runs the automatic fx checks.
# usage: .venv/bin/python fx/scripts/catalog.py [name ...]    (no names = all)
import os, sys, math
import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
FX = os.path.dirname(HERE)
sys.path.insert(0, FX)
import fx  # noqa: E402

OUT = os.path.join(FX, 'previews')
TILE = 240
TS = (0, 0.25, 0.5, 0.75, 1.0)


def font(sz):
    for f in ('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',
              '/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf'):
        if os.path.exists(f): return ImageFont.truetype(f, sz)
    return ImageFont.load_default()


def tile(kind, w=TILE, h=TILE):
    """Procedural stand-in for a plate: day sky over grass, or night sky over a dark street with a warm window."""
    im = Image.new('RGB', (w, h)); d = ImageDraw.Draw(im)
    top, bot, ground = (((110, 190, 245), (205, 235, 252), (120, 170, 90)) if kind == 'day'
                        else ((22, 26, 70), (64, 50, 112), (44, 38, 72)))
    gy = int(h * 0.78)
    for y in range(gy):
        d.line([(0, y), (w, y)], fill=fx.mixc(top, bot, y / gy))
    d.rectangle([0, gy, w, h], fill=ground)
    if kind == 'day':
        d.ellipse([w * 0.62, h * 0.12, w * 0.92, h * 0.26], fill=(250, 252, 255))
        d.rectangle([w * 0.05, h * 0.5, w * 0.3, gy], fill=(214, 120, 90), outline=fx.INK, width=2)
    else:
        d.rectangle([w * 0.05, h * 0.45, w * 0.32, gy], fill=(58, 48, 96), outline=fx.INK, width=2)
        d.rectangle([w * 0.12, h * 0.53, w * 0.24, h * 0.64], fill=(255, 196, 102), outline=fx.INK, width=2)
        for sx, sy in ((0.6, 0.1), (0.8, 0.2), (0.45, 0.25), (0.9, 0.08)):
            d.ellipse([w * sx - 1.5, h * sy - 1.5, w * sx + 1.5, h * sy + 1.5], fill=(240, 240, 255))
    return im.convert('RGBA')


def strip(name, ts=TS, size=TILE):
    pad, head = 6, 30
    W = len(ts) * (size + pad) + pad + 60
    H = head + 2 * (size + pad) + pad + 18
    im = Image.new('RGB', (W, H), (236, 234, 240)); d = ImageDraw.Draw(im)
    d.text((pad, 6), name, fill=fx.INK, font=font(18))
    for r, kind in enumerate(('day', 'night')):
        y = head + r * (size + pad)
        d.text((pad, y + size // 2 - 8), kind, fill=fx.INK, font=font(13))
        for c, t in enumerate(ts):
            x = 60 + pad + c * (size + pad)
            bg = tile(kind, size, size); bg.alpha_composite(fx.render(name, t, size))
            im.paste(bg.convert('RGB'), (x, y))
            if r == 1: d.text((x + size // 2 - 18, y + size + 2), f't={t:g}', fill=fx.INK, font=font(13))
    return im


def checks(name, frames=60, size=200):
    """Automatic fx checks: empty at t=0 and t=1, and no frame-to-frame pop in coverage (QA.md > fx)."""
    cov = []
    for i in range(frames + 1):
        a = np.asarray(fx.render(name, i / frames, size))[..., 3].astype(np.float32) / 255
        cov.append(a.sum())
    cov = np.array(cov); peak = cov.max() or 1
    jumps = np.abs(np.diff(cov)) / peak
    res = {'start': cov[0] / peak, 'end': cov[-1] / peak, 'max_jump': float(jumps.max()),
           'peak_at': int(cov.argmax()) / frames}
    res['ok'] = res['start'] < 0.01 and res['end'] < 0.01 and res['max_jump'] < 0.35
    return res


def gif(names, path, frames=30, size=200):
    seq = []
    for i in range(frames + 6):
        t = min(1.0, i / frames)
        row = Image.new('RGBA', (size * len(names), size * 2))
        for j, nm in enumerate(names):
            for r, kind in enumerate(('day', 'night')):
                bg = tile(kind, size, size); bg.alpha_composite(fx.render(nm, t, size))
                row.paste(bg, (j * size, r * size))
        seq.append(row.convert('RGB').quantize(colors=255, method=Image.MEDIANCUT, dither=Image.NONE))
    seq[0].save(path, save_all=True, append_images=seq[1:], duration=33, loop=0)


if __name__ == '__main__':
    os.makedirs(OUT, exist_ok=True)
    names = sys.argv[1:] or list(fx.NAMES)
    bad = 0
    for nm in names:
        strip(nm).save(os.path.join(OUT, f'{nm}.png'))
        r = checks(nm); bad += not r['ok']
        print(f"{nm:14s} start={r['start']:.3f} end={r['end']:.3f} max_jump={r['max_jump']:.2f} "
              f"peak_at={r['peak_at']:.2f} {'OK' if r['ok'] else 'FAIL'}")
    if not sys.argv[1:]:
        gif(['explosion', 'impact_star', 'splash', 'glow_eyes', 'music_note'], os.path.join(OUT, 'fx_demo.gif'))
    sys.exit(1 if bad else 0)
