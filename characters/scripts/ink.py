# Shared cast-style ink for props and sprites: shapes in DESIGN units are drawn as one merged silhouette with plum ink
# (thin top-left, ~3x thicker bottom-right), flat fills with the soft crescent shade, then un-outlined details.
# Shape tuples are the ones fx/fx.py uses: ('c', x, y, r, col) | ('e', x, y, rx, ry, col) |
# ('s', [(x, y, w), ...], col) | ('p', [(x, y), ...], col).  Works on a local bbox layer, so it is cheap.
import math, os, sys
from PIL import Image, ImageDraw
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'fx'))
import fx  # noqa: E402

S = fx.S
INK = fx.INK


def _bbox(shapes):
    xs, ys = [], []
    for sh in shapes:
        k = sh[0]
        if k == 'c': _, x, y, r, _c = sh; xs += [x - r, x + r]; ys += [y - r, y + r]
        elif k == 'e': _, x, y, rx, ry, _c = sh; xs += [x - rx, x + rx]; ys += [y - ry, y + ry]
        elif k == 's':
            for x, y, w in sh[1]: xs += [x - w, x + w]; ys += [y - w, y + w]
        else:
            for x, y in sh[1]: xs.append(x); ys.append(y)
    return min(xs), min(ys), max(xs), max(ys)


def _move(sh, dx, dy, k=1.0):
    t = sh[0]
    if t == 'c': return ('c', (sh[1] + dx) * k, (sh[2] + dy) * k, sh[3] * k, sh[4])
    if t == 'e': return ('e', (sh[1] + dx) * k, (sh[2] + dy) * k, sh[3] * k, sh[4] * k, sh[5])
    if t == 's': return ('s', [((x + dx) * k, (y + dy) * k, w * k) for x, y, w in sh[1]], sh[2])
    return ('p', [((x + dx) * k, (y + dy) * k) for x, y in sh[1]], sh[2])


def layer(shapes, e, details=(), shade=True, scale=1.0, pad=None):
    """Render shapes (design units) to a local RGBA layer at `scale` output px per unit x S supersampling.
    Returns (img at S x scale, (x0, y0) design-unit origin)."""
    allsh = list(shapes) + list(details)
    x0, y0, x1, y1 = _bbox(allsh)
    pad = pad if pad is not None else 2 * e + 4
    x0 -= pad; y0 -= pad; x1 += pad; y1 += pad
    w, h = int(math.ceil((x1 - x0) * scale)) + 1, int(math.ceil((y1 - y0) * scale)) + 1
    sh_ = [_move(s, -x0, -y0, scale) for s in shapes]
    de_ = [_move(s, -x0, -y0, scale) for s in details]
    ee = e * scale
    fills = Image.new('RGBA', (w * S, h * S), (0, 0, 0, 0)); d = ImageDraw.Draw(fills)
    for s in sh_: fx.shape(d, s, 0)
    if shade and sh_:
        sizes = sorted(fx.size_of(s) for s in sh_)
        fills = fx.crescent(fills, sizes[len(sizes) // 2])
    lay = Image.new('RGBA', (w * S, h * S), (0, 0, 0, 0))
    if ee > 0:
        dd = ImageDraw.Draw(lay)
        for s in sh_: fx.shape(dd, s, ee, INK, fx.THICK)
    lay.alpha_composite(fills)
    if de_:
        dd = ImageDraw.Draw(lay)
        for s in de_: fx.shape(dd, s, 0)
    return lay, (x0, y0)


def stamp(C, shapes, e, details=(), shade=True):
    """Draw onto a bean.Canvas (design units, S supersampling)."""
    lay, (x0, y0) = layer(shapes, e, details, shade)
    C.im.alpha_composite(lay, (int(round(x0 * S)), int(round(y0 * S))))
    C.d = ImageDraw.Draw(C.im)


def text(C, x, y, txt, h, col=(255, 255, 255), font='bold', anchor='mm', rot=0.0, maxw=None):
    """Text of cap-height ~h design units centred at (x, y) on a bean.Canvas. Poppins Bold when available."""
    from PIL import ImageFont
    here = os.path.dirname(os.path.abspath(__file__))
    fp = os.path.join(here, '..', '..', 'engine', 'fonts', 'Poppins-Bold.ttf')
    if not os.path.exists(fp): fp = '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
    px = max(4, int(h * S * 1.38))
    f = ImageFont.truetype(fp, px)
    if maxw:
        while px > 6 and f.getlength(txt) > maxw * S: px = int(px * 0.92); f = ImageFont.truetype(fp, px)
    bb = f.getbbox(txt)
    tw, th = bb[2] - bb[0] + 8, bb[3] - bb[1] + 8
    im = Image.new('RGBA', (tw, th), (0, 0, 0, 0))
    ImageDraw.Draw(im).text((tw / 2, th / 2), txt, font=f, fill=col, anchor='mm')
    if rot: im = im.rotate(rot, resample=Image.BICUBIC, expand=True)
    C.im.alpha_composite(im, (int(x * S - im.width / 2), int(y * S - im.height / 2)))
    C.d = ImageDraw.Draw(C.im)


def rpoly(cx, cy, w, h, r, ang=0.0, n=6):
    """Rounded rectangle polygon (design units), rotated by ang degrees about its centre."""
    pts = []
    r = min(r, w / 2, h / 2)
    for qx, qy, a0 in ((1, -1, -90), (1, 1, 0), (-1, 1, 90), (-1, -1, 180)):
        ox, oy = cx + qx * (w / 2 - r), cy + qy * (h / 2 - r)
        for i in range(n + 1):
            a = math.radians(a0 + 90 * i / n); pts.append((ox + r * math.cos(a), oy + r * math.sin(a)))
    return [fx.rot(x, y, cx, cy, ang) for x, y in pts] if ang else pts


def rock_pts(cx, cy, rx, ry, seed=0, n=28, lumpy=0.10, flat=0.35):
    """A rounded-boulder outline with a flatter base (sits on the ground)."""
    import random
    rnd = random.Random(seed); ph = [rnd.uniform(0, 6.28) for _ in range(3)]
    pts = []
    for i in range(n):
        a = 2 * math.pi * i / n
        r = 1 + lumpy * (0.5 * math.sin(2 * a + ph[0]) + 0.35 * math.sin(3 * a + ph[1]) + 0.2 * math.sin(5 * a + ph[2]))
        x, y = math.cos(a) * rx * r, math.sin(a) * ry * r
        if y > 0: y *= (1 - flat)
        pts.append((cx + x, cy + y))
    return pts


def googly(cx, cy, r, look=(0.3, 0.35), rot=0.0):
    """One googly eye: white disc + plum pupil sitting low (gravity) toward `look`. Returns (shape, detail)."""
    px, py = cx + look[0] * r * 0.45, cy + look[1] * r * 0.45
    return ('c', cx, cy, r, (255, 255, 255)), ('c', px, py, r * 0.5, INK)
