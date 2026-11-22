"""flat2d props: hand-drawn flat props in the kit's ink style (outline 5-6 px, lit/shadow planes)."""
import math
from PIL import Image, ImageDraw
from kit import INK, rgb, lerp, layer, mask, fill_mask, glow, font, text_w, rotated_paste


def fur_hat(img, head, R, color=(120, 82, 56), fur=(214, 196, 170)):
    """1911 fur trapper hat sitting on the crown (never over the eyes: stays above hy - 0.5R)."""
    hx, hy = head; d = ImageDraw.Draw(img)
    top = hy - R * 1.32; band = hy - R * 0.55
    d.chord([hx - R * .95, top, hx + R * .95, band + R * .5], 180, 360, fill=INK)
    d.chord([hx - R * .9, top + 6, hx + R * .9, band + R * .5 - 6], 180, 360, fill=rgb(color))
    d.chord([hx - R * .55, top + 14, hx + R * .2, band], 200, 300, fill=lerp(rgb(color), (255, 255, 255), .2))
    d.rounded_rectangle([hx - R * 1.08, band - R * .24, hx + R * 1.08, band + R * .02], R * .13, fill=rgb(fur), outline=INK, width=5)
    for k in range(9):
        x = hx - R * .95 + k * R * .24
        d.line([(x, band - R * .2), (x + 6, band - R * .02)], fill=lerp(rgb(fur), (90, 70, 50), .35), width=3)


def ice_axe(img, hand, s=1.0):
    """Ice axe hanging from a hand (hand = (x, y))."""
    x, y = hand; d = ImageDraw.Draw(img)
    L = 260 * s
    d.line([(x, y - 30 * s), (x + 8 * s, y + L)], fill=INK, width=int(22 * s))
    d.line([(x, y - 30 * s), (x + 8 * s, y + L)], fill=(150, 98, 58), width=int(13 * s))
    hy = y + L
    d.polygon([(x - 70 * s, hy - 6 * s), (x + 90 * s, hy - 14 * s), (x + 96 * s, hy + 6 * s), (x - 60 * s, hy + 14 * s)],
              fill=(178, 188, 200), outline=INK, width=int(5 * s))
    d.line([(x - 50 * s, hy - 2 * s), (x + 80 * s, hy - 8 * s)], fill=(236, 242, 248), width=int(4 * s))


def footprints(img, pts, color=(176, 194, 222), s=1.0):
    d = ImageDraw.Draw(img)
    for i, (x, y) in enumerate(pts):
        o = 16 * s if i % 2 else -16 * s; k = s * (0.6 + 0.4 * i / max(1, len(pts) - 1))
        d.ellipse([x + o - 18 * k, y - 8 * k, x + o + 18 * k, y + 8 * k], fill=rgb(color))


def microscope(img, x, base_y, s=1.0, body=(70, 96, 110), lit=(112, 148, 162), metal=(200, 210, 218)):
    """Side-view lab microscope, eyepiece up-left. Returns eyepiece top (x, y)."""
    d = ImageDraw.Draw(img); S = lambda v: v * s
    d.rounded_rectangle([x - S(120), base_y - S(46), x + S(120), base_y], S(16), fill=rgb(body), outline=INK, width=6)
    d.rounded_rectangle([x - S(108), base_y - S(42), x + S(108), base_y - S(30)], S(6), fill=rgb(lit))
    d.polygon([(x + S(40), base_y - S(46)), (x + S(84), base_y - S(46)), (x + S(70), base_y - S(330)),
               (x + S(20), base_y - S(360)), (x - S(4), base_y - S(320))], fill=rgb(body), outline=INK, width=6)
    d.line([(x + S(52), base_y - S(60)), (x + S(44), base_y - S(300))], fill=rgb(lit), width=int(S(10)))
    d.rounded_rectangle([x - S(110), base_y - S(170), x + S(50), base_y - S(146)], S(6), fill=rgb(metal), outline=INK, width=5)
    glow_m = mask(img.width, img.height); ImageDraw.Draw(glow_m).ellipse([x - S(60), base_y - S(180), x - S(10), base_y - S(140)], fill=255)
    glow(img, glow_m, (255, 120, 100), .9, blur=10, add=True)
    d.ellipse([x - S(50), base_y - S(168), x - S(20), base_y - S(150)], fill=(220, 50, 50), outline=INK, width=3)  # red sample slide
    # tube (angled)
    tube = [(x - S(30), base_y - S(200)), (x + S(10), base_y - S(214)), (x - S(80), base_y - S(430)), (x - S(120), base_y - S(416))]
    d.polygon(tube, fill=rgb(metal), outline=INK, width=6)
    d.line([(x - S(16), base_y - S(212)), (x - S(98), base_y - S(410))], fill=(250, 252, 255), width=int(S(8)))
    d.polygon([(x - S(22), base_y - S(196)), (x + S(4), base_y - S(204)), (x - S(4), base_y - S(176)), (x - S(18), base_y - S(172))],
              fill=rgb(body), outline=INK, width=4)
    d.ellipse([x + S(40), base_y - S(250), x + S(96), base_y - S(194)], fill=rgb(body), outline=INK, width=5)  # focus knob
    d.ellipse([x + S(56), base_y - S(234), x + S(80), base_y - S(210)], fill=rgb(lit))
    ex, ey = x - S(100), base_y - S(424)
    d.rounded_rectangle([ex - S(30), ey - S(40), ex + S(30), ey + S(8)], S(8), fill=rgb(body), outline=INK, width=5)
    return ex, ey - S(40)


def flask(img, x, base_y, h, liquid, kind='round', glow_on=True):
    """Glass flask / bottle / tube with a liquid that can glow. Moves: bubbles rise, liquid level wobbles."""
    d = ImageDraw.Draw(img); glass = (214, 232, 240)
    if kind == 'round':
        r = h * .36; cy = base_y - r
        neck = [x - h * .09, base_y - h, x + h * .09, cy - r * .7]
        if glow_on:
            m = mask(img.width, img.height); ImageDraw.Draw(m).ellipse([x - r, cy - r, x + r, cy + r], fill=255)
            glow(img, m, liquid, .55, blur=int(h * .25))
        d.rectangle(neck, fill=glass, outline=INK, width=5)
        d.ellipse([x - r, cy - r, x + r, cy + r], fill=glass, outline=INK, width=5)
        d.chord([x - r + 5, cy - r + 5, x + r - 5, cy + r - 5], 20, 160, fill=rgb(liquid))
        d.chord([x - r + 5, cy - r * .15, x + r - 5, cy + r - 5], 330, 210, fill=rgb(liquid))
        d.arc([x - r * .7, cy - r * .7, x + r * .3, cy + r * .3], 190, 250, fill='white', width=6)
    elif kind == 'tube':
        w = h * .16
        d.rounded_rectangle([x - w, base_y - h, x + w, base_y], w, fill=glass, outline=INK, width=5)
        d.rounded_rectangle([x - w + 5, base_y - h * .55, x + w - 5, base_y - 5], w - 5, fill=rgb(liquid))
        d.line([(x - w * .4, base_y - h * .9), (x - w * .4, base_y - h * .2)], fill='white', width=4)
    else:  # bottle
        w = h * .3
        d.rounded_rectangle([x - w, base_y - h * .78, x + w, base_y], 14, fill=rgb(liquid), outline=INK, width=5)
        d.rectangle([x - w * .4, base_y - h, x + w * .4, base_y - h * .76], fill=(60, 60, 70), outline=INK, width=4)
        d.rectangle([x - w * .75, base_y - h * .55, x + w * .75, base_y - h * .25], fill=(245, 240, 226), outline=INK, width=3)
        d.line([(x - w * .55, base_y - h * .5), (x - w * .55, base_y - h * .1)], fill=lerp(rgb(liquid), (255, 255, 255), .5), width=5)


def stamp(text, color=(46, 168, 92), size=74, cracked=False, check=True):
    """Rubber-stamp card (returns RGBA layer to rotate/paste). cracked=True splits it with a jagged
    crack and offsets the halves (the s05 'MYSTERY SOLVED' breaks). Moves: slam (scale 1.4 -> 1), crack."""
    f = font(size); w = text_w(text + (' ✓' if False else ''), f) + (size * 1.1 if check else 0); h = size * 1.7
    Wd, Hd = int(w + 120), int(h + 80)
    lay = layer(Wd, Hd); d = ImageDraw.Draw(lay)
    c = rgb(color)
    d.rounded_rectangle([20, 20, Wd - 20, Hd - 20], 22, fill=(250, 248, 240, 235), outline=c, width=12)
    d.rounded_rectangle([36, 36, Wd - 36, Hd - 36], 14, outline=c, width=4)
    d.text((60, Hd / 2), text, font=f, fill=c, anchor='lm')
    if check:
        cx = Wd - 60 - size * .5; cy = Hd / 2
        d.line([(cx - size * .38, cy), (cx - size * .08, cy + size * .3), (cx + size * .42, cy - size * .38)], fill=c, width=int(size * .2), joint='curve')
    if not cracked: return lay
    gap = (60 + text_w(text.split(' ')[0], f) + text_w(' ', f) / 2) if ' ' in text else Wd * .5  # split between words
    crack = [(gap + 6, 0), (gap - 8, Hd * .3), (gap + 8, Hd * .5), (gap - 6, Hd * .72), (gap + 4, Hd)]
    mL = mask(Wd, Hd); ImageDraw.Draw(mL).polygon([(0, 0)] + crack + [(0, Hd)], fill=255)
    left = layer(Wd + 80, Hd + 40); right = layer(Wd + 80, Hd + 40)
    left.paste(lay, (0, 30), mL)
    from PIL import ImageChops
    right.paste(lay, (60, 0), ImageChops.invert(mL))
    out = layer(Wd + 80, Hd + 40); out.alpha_composite(left); out.alpha_composite(right)
    d2 = ImageDraw.Draw(out)
    d2.line([(x, y + 30) for x, y in crack], fill=INK + (255,), width=9)
    d2.line([(x + 60, y) for x, y in crack], fill=INK + (255,), width=9)
    return out


def big_x(img, cx, cy, r, color=(230, 40, 44), w=None):
    d = ImageDraw.Draw(img); w = w or int(r * .32)
    for a, b in (((cx - r, cy - r), (cx + r, cy + r)), ((cx + r, cy - r), (cx - r, cy + r))):
        d.line([a, b], fill=INK, width=w + 12)
    for a, b in (((cx - r, cy - r), (cx + r, cy + r)), ((cx + r, cy - r), (cx - r, cy + r))):
        d.line([a, b], fill=rgb(color), width=w)
        for p in (a, b): d.ellipse([p[0] - w / 2, p[1] - w / 2, p[0] + w / 2, p[1] + w / 2], fill=rgb(color))


def algae_chain(img, cx, cy, s=1.0, color=(70, 170, 90), dashed=False, n=5):
    """A chain of round algae cells (green), drawn wavy. dashed = ghost outline (absent)."""
    d = ImageDraw.Draw(img); r = 30 * s
    for i in range(n):
        x = cx + (i - (n - 1) / 2) * r * 1.8; y = cy + math.sin(i * 1.3) * r * .7
        if dashed:
            for a in range(0, 360, 40): d.arc([x - r, y - r, x + r, y + r], a, a + 22, fill=rgb(color), width=6)
        else:
            d.ellipse([x - r, y - r, x + r, y + r], fill=rgb(color), outline=INK, width=4)
            d.ellipse([x - r * .4, y - r * .5, x, y - r * .1], fill=lerp(rgb(color), (255, 255, 255), .5))


def plane(img, x, y, s=1.0, body=(236, 92, 64)):
    """Small survey plane, facing right."""
    d = ImageDraw.Draw(img); S = lambda v: v * s
    d.polygon([(x - S(110), y - S(10)), (x + S(90), y - S(14)), (x + S(120), y), (x + S(90), y + S(14)), (x - S(110), y + S(10))], fill=rgb(body), outline=INK, width=5)
    d.polygon([(x - S(20), y), (x + S(30), y), (x - S(10), y + S(70)), (x - S(40), y + S(70))], fill=lerp(rgb(body), (0, 0, 0), .2), outline=INK, width=5)
    d.polygon([(x - S(10), y), (x + S(20), y), (x - S(20), y - S(50)), (x - S(40), y - S(50))], fill=lerp(rgb(body), (255, 255, 255), .2), outline=INK, width=5)
    d.polygon([(x - S(110), y - S(6)), (x - S(80), y - S(6)), (x - S(110), y - S(46)), (x - S(124), y - S(46))], fill=rgb(body), outline=INK, width=5)
    d.ellipse([x + S(50), y - S(10), x + S(84), y + S(4)], fill=(170, 220, 250), outline=INK, width=3)
