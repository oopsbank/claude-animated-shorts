"""Style test round 3 (2026-11-25): saturated blue night with warm practicals, a two-storey staircase house set,
round-bodied stickmen with clothes (stickman.BODY_STYLE='round', cardigan / pyjamas), staging with occluders
(sitting up in bed, peeking round a door frame, creeping up the stairs), prop macros and a continuous camera move.
usage: .venv/bin/python flat2d/style_test_rooms3.py OUTDIR [frame names...|clip]   (PREVIEW=1: 540x960 stills)"""
import os, sys, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import style_test_rooms as ST     # paths, chibi proportions (R=132 ...), the 'ref' face
import style_test_rooms2 as R2
from style_test_rooms import col, Part, box, Cam, Light, P3, cine, hangar, stickman, anim, kit
import toonlight as TL
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

stickman.BODY_STYLE = 'round'
PREVIEW = os.environ.get('PREVIEW', '0') == '1'
INKC = (30, 26, 34)
WHITE = R2.WHITE
OUT = sys.argv[1] if len(sys.argv) > 1 else 'out3'
os.makedirs(OUT, exist_ok=True)
shade = R2.shade

PYJ_A = dict(pyjamas='#e9a93c', hair=('swept', '#5a3e2a'))                    # the kid
PYJ_B = dict(pyjamas='#e58aa0', hair=('swept', '#2e2622'))
CARDI = dict(cardigan='#c25a3e', pants='#3a4058', hair=('swept', '#8a8a8a'), glasses=True)    # grandpa
TEE = dict(shirt='#2fa59b', pants='#3a4058', hair=('swept', '#6a4a30'))
UNIF = dict(uniform='#2e3f6e', hair=('swept', '#3a2e28'))

LOOK_NIGHT = dict(lift=(.0, .0, .02), gamma=(1.0, 1.0, 1.0), gain=(1.02, 1.02, 1.04), contrast=1.04, sat=1.08,
                  sh=(10, 14, 70), sh_k=.12, hi=(255, 246, 230), hi_k=.04)


# ------------------------------------------------------------------ small geometry helpers
def wrect(part, ax, v, a0, a1, z0, z1, c, n=1, ink=False, emit=0.0, e=.004):
    """A rect decal on a wall plane: ax='x' -> plane x=v (a = y), ax='y' -> plane y=v (a = x); n = sign of the
    wall's normal along that axis (into the room)."""
    if ax == 'x':
        x = v + n * e; pts = [(x, a0, z0), (x, a1, z0), (x, a1, z1), (x, a0, z1)]; nm = (n, 0, 0)
    else:
        y = v + n * e; pts = [(a0, y, z0), (a1, y, z0), (a1, y, z1), (a0, y, z1)]; nm = (0, n, 0)
    part.decal(pts, c, ink=ink, emit=emit, normal=nm)


def frect(part, x0, y0, x1, y1, z, c, ink=False, emit=0.0, n=1):
    pts = [(x0, y0, z), (x1, y0, z), (x1, y1, z), (x0, y1, z)]
    part.decal(pts, c, ink=ink, emit=emit, normal=(0, 0, n))


def wall(name, ax, v, a0, a1, z0, z1, c, n=1):
    """A wall polygon facing into the room (normal sign n along ax)."""
    p = Part(name, sil=False)
    if ax == 'x':
        pts = [(v, a0, z0), (v, a1, z0), (v, a1, z1), (v, a0, z1)]
        if n < 0: pts = pts[::-1]
    else:
        pts = [(a1, v, z0), (a0, v, z0), (a0, v, z1), (a1, v, z1)]
        if n < 0: pts = pts[::-1]
    p.poly(pts, c); return p


def picture(part, ax, v, a, z, fw, fh, inner, n=1, motif=None, frame=(70, 52, 40)):
    wrect(part, ax, v, a, a + fw, z, z + fh, frame, n, ink=True, e=.006)
    wrect(part, ax, v, a + .03, a + fw - .03, z + .03, z + fh - .03, inner, n, e=.007)
    if motif:
        wrect(part, ax, v, a + fw * .3, a + fw * .7, z + fh * .25, z + fh * .62, motif, n, e=.008)


def door_panel(part, ax, v, a0, a1, h=2.1, c=(252, 250, 246), n=1, glass=None, knob=True, z0=0.0):
    """A white panelled door decal (frame, two panels, optional glass with emit colour, brass knob)."""
    wrect(part, ax, v, a0 - .08, a1 + .08, z0, z0 + h + .08, WHITE, n, ink=True, e=.004)
    wrect(part, ax, v, a0, a1, z0, z0 + h, c, n, ink=True, e=.005)
    if glass:
        wrect(part, ax, v, a0 + .14, a1 - .14, z0 + 1.2, z0 + 1.95, glass, n, ink=True, emit=1.0, e=.006)
        am = (a0 + a1) / 2
        wrect(part, ax, v, am - .015, am + .015, z0 + 1.2, z0 + 1.95, c, n, e=.007)
    else:
        wrect(part, ax, v, a0 + .12, a1 - .12, z0 + 1.15, z0 + 1.95, shade(c, .95), n, ink=True, e=.006)
    wrect(part, ax, v, a0 + .12, a1 - .12, z0 + .15, z0 + 1.0, shade(c, .95), n, ink=True, e=.006)
    if knob:
        ka = a1 - .1 if n > 0 else a0 + .1
        p = (v + n * .06, ka, z0 + 1.0) if ax == 'x' else (ka, v + n * .06, z0 + 1.0)
        part.dot(p, .04, (226, 186, 80), ink=True)


def ao(img, cam, segs, k=.22, blur=26, w=40):
    R2.soft_ao(img, cam, segs, k, blur) if w == 40 else None


def flashlight(img, hand, s, ang, beam=600, spread=16, spot=None, k=.6):
    """A torch held at `hand` (x, y px), pointing along screen angle ang (deg), s = px per card px (~figure scale);
    draws the body, a hot lens and the beam (toonlight.cone)."""
    x, y = hand; L = 150 * s; Wd = 44 * s
    a = math.radians(ang); ux, uy = math.cos(a), math.sin(a); nx, ny = -uy, ux
    tip = (x + ux * L * .7, y + uy * L * .7); back = (x - ux * L * .3, y - uy * L * .3)
    TL.cone(img, tip[0], tip[1], ang, beam, spread, k=k, spot=spot)
    d = ImageDraw.Draw(img)
    pts = [(back[0] + nx * Wd * .4, back[1] + ny * Wd * .4), (tip[0] + nx * Wd * .55, tip[1] + ny * Wd * .55),
           (tip[0] - nx * Wd * .55, tip[1] - ny * Wd * .55), (back[0] - nx * Wd * .4, back[1] - ny * Wd * .4)]
    d.polygon(pts, fill=(60, 64, 78), outline=INKC, width=max(2, int(9 * s)))
    r = Wd * .5
    d.ellipse((tip[0] - r, tip[1] - r, tip[0] + r, tip[1] + r), fill=(255, 250, 220), outline=INKC, width=max(2, int(7 * s)))
    TL.glow_at(img, tip[0], tip[1], Wd * 2.2, (255, 240, 190), k=.9)


def char_layer(img, cam, P, night=True, tint=(214, 226, 255), **kw):
    """Draw a stickman (hangar.stand) on its own layer, moon-tint it for night, composite. Returns (layer, geom)."""
    lay = Image.new('RGBA', img.size, (0, 0, 0, 0))
    g = hangar.stand(lay, cam, P, kw.pop('t', 0.0), blink_ok=False, **kw)
    if night: TL.moon_tint(lay, col=tint)
    img.alpha_composite(lay)
    return g


def render_set(img, cam, parts, light, order=None, ink=INKC, s=1.0):
    P3.render(img, cam, parts, light=light, order=order, ink=ink, ink_w=3.2 * s, sil_w=6.0 * s)


def finish3(img, night=True, vig=.22, grain=.01, bloom_k=.35, thr=200):
    img = cine.grade(img, LOOK_NIGHT if night else R2.STORY)
    if bloom_k: img = cine.bloom(img, thr, 26 * img.width / 1080, bloom_k)
    cine.vignette(img, vig, (6, 8, 40) if night else (30, 20, 50))
    if grain: anim.grain(img, grain, t=0.0)
    return img


NIGHT_LIGHT = Light(d=(-.3, -.5, .8), amb=.78, bands=(.15, .5, .8), soft=.5, shadow=(40, 50, 120), shadow_k=.2)
DAY_LIGHT = Light(d=(.2, -.7, .7), amb=.76, bands=(.15, .5, .8), soft=.5, shadow=(100, 90, 140), shadow_k=.14)


# ------------------------------------------------------------------ the two-storey house (hall + stairs + landing)
X1 = 2.6                 # right wall
YB, YF = -2.4, 6.4       # landing back wall, hall front-door wall
ZT, ZC = 2.8, 5.4        # upstairs floor, ceiling
RUN, NST = .28, 12
RISE = ZT / NST
SX = 1.05                # stair width (x 0..SX)
MOON_L = np.array([-.12, -.45, -.89]); MOON_L = MOON_L / np.linalg.norm(MOON_L)
WIN_S = (1.05, 2.05, 3.3, 4.7)          # stairwell window on the front wall (x0, x1, z0, z1)


def step_z(i): return ZT - (i + 1) * RISE           # top of step i (i = 0 just below the landing)


def house(rng=None):
    """Parts of the stair hall. Stairs run down along +y from the landing (y<0, z=2.8) to the hall floor."""
    rng = rng or np.random.default_rng(3)
    parts = []
    wallc = (138, 176, 214)                              # day palette; night_map turns it into the blue ramp
    # floors: hall planks
    fl = Part('floor', sil=False)
    x = 0
    while x < X1 - 1e-6:
        y = SX * 0 + 0.0
        y = -.0
        yy = 0.0
        while yy < YF - 1e-6:
            L = rng.uniform(.9, 1.8); y1 = min(YF, yy + L)
            fl.poly([(x, yy, 0), (min(X1, x + .18), yy, 0), (min(X1, x + .18), y1, 0), (x, y1, 0)], shade((200, 146, 90), rng.uniform(.9, 1.08)), ink=1.0)
            yy = y1
        x += .18
    parts.append(fl)
    # runner rug in the hall
    rug = Part('rug', sil=False)
    rug.poly([(1.15, 3.7, .004), (2.15, 3.7, .004), (2.15, 6.1, .004), (1.15, 6.1, .004)], (178, 52, 60), ink=1.0)
    for k in range(9):
        yy = 3.85 + k * .27
        rug.decal([(1.3, yy, .005), (2.0, yy, .005), (2.0, yy + .08, .005), (1.3, yy + .08, .005)], (240, 200, 120), normal=(0, 0, 1))
    parts.append(rug)
    # walls (two storeys)
    wl = wall('wall_l', 'x', 0, YB, YF, 0, ZC, wallc, 1)
    wr = wall('wall_r', 'x', X1, YB, YF, 0, ZC, shade(wallc, .96), -1)
    wf = wall('wall_f', 'y', YF, 0, X1, 0, ZC, shade(wallc, 1.02), -1)
    wbk = wall('wall_bk', 'y', YB, 0, X1, ZT, ZC, shade(wallc, .98), 1)
    for p in (wl, wr):                                   # wallpaper motifs
        ax_n = 1 if p is wl else -1
        v = 0 if p is wl else X1
        for zz in np.arange(.4, ZC - .2, .3):
            for yy in np.arange(YB + .15 + (zz * 7 % .3), YF, .3):
                wrect(p, 'x', v, yy, yy + .03, zz, zz + .07, shade(wallc, .88), ax_n, e=.0015)
    parts += [wl, wr, wf, wbk]
    ce = Part('ceiling', sil=False); ce.poly([(0, YB, ZC), (0, YF, ZC), (X1, YF, ZC), (X1, YB, ZC)], WHITE); parts.append(ce)
    # landing slab (upstairs floor) + its planks
    sl = Part('slab', sil=True)
    box((0, YB, ZT - .22), (X1, 0, ZT), WHITE, part=sl, cols={'top': (196, 142, 88)})
    for k in range(1, int(X1 / .18)):
        xx = k * .18
        sl.decal([(xx - .004, YB, ZT + .001), (xx + .004, YB, ZT + .001), (xx + .004, 0, ZT + .001), (xx - .004, 0, ZT + .001)],
                 (150, 104, 64), normal=(0, 0, 1))
    parts.append(sl)
    # stairs: wood treads, white risers, a red runner
    for i in range(NST - 1):
        st = Part(f'step{i}')
        z = step_z(i); y0, y1 = i * RUN, (i + 1) * RUN
        box((0, y0, 0), (SX, y1, z), WHITE, part=st, cols={'top': (196, 142, 88), 'px': (240, 238, 232)})
        frect(st, .2, y0 + .01, SX - .2, y1, z + .002, (190, 56, 62))
        frect(st, .2, y0 + .01, .25, y1, z + .003, (240, 200, 120)); frect(st, SX - .25, y0 + .01, SX - .2, y1, z + .003, (240, 200, 120))
        st.decal([(.2, y1 + .003, z - RISE), (SX - .2, y1 + .003, z - RISE), (SX - .2, y1 + .003, z), (.2, y1 + .003, z)],
                 (170, 46, 54), normal=(0, 1, 0))
        st.order = None
        parts.append(st)
    # banister: newels, rail, spindles along the stairs and along the landing edge
    # (one Part per piece, so the pieces near the camera can be split off and blurred as foreground)
    wood = (120, 74, 44)
    def bp(): p = Part('ban'); parts.append(p); return p
    box((SX - .05, 3.3, 0), (SX + .07, 3.42, 1.05), wood, part=bp())
    box((SX - .05, -.12, ZT), (SX + .07, 0, ZT + 1.0), wood, part=bp())
    for a in range(4):                                   # the sloped rail in four pieces
        y0, y1 = -.06 + a * 3.42 / 4, -.06 + (a + 1) * 3.42 / 4
        bp().line((SX + .01, y0, ZT + .95 - (y0 + .06) * ZT / 3.42), (SX + .01, y1, ZT + .95 - (y1 + .06) * ZT / 3.42), .06, wood)
    for k in range(1, 24):
        yy = k * .14
        if yy > 3.3: break
        i = int(yy / RUN); zb = step_z(min(i, NST - 2)) if i < NST - 1 else 0
        zt = ZT + .92 - yy * (ZT / 3.36)
        bp().line((SX + .01, yy, zb), (SX + .01, yy, zt), .03, WHITE)
    bp().line((SX + .01, -.06, ZT + .95), (X1, -.06, ZT + .95), .06, wood)
    for xx in np.arange(SX + .14, X1, .14):
        bp().line((xx, -.06, ZT), (xx, -.06, ZT + .92), .03, WHITE)
    und = wall('wall_und', 'y', YB, 0, X1, 0, ZT, shade(wallc, .9), 1); parts.append(und)
    # trims: skirting along the hall + the landing, inked corners
    tr = Part('trims', sil=False)
    for (ax, v, a0, a1, n, z0) in [('x', 0, 3.36, YF, 1, 0), ('x', X1, YB, YF, -1, 0), ('y', YF, 0, X1, -1, 0),
                                   ('x', 0, YB, 0, 1, ZT), ('y', YB, 0, X1, 1, ZT)]:
        wrect(tr, ax, v, a0, a1, z0, z0 + .12, WHITE, n, ink=True, e=.005)
    for (ax, v, a0, a1, n) in [('x', 0, YB, YF, 1), ('x', X1, YB, YF, -1), ('y', YF, 0, X1, -1), ('y', YB, 0, X1, 1)]:
        wrect(tr, ax, v, a0, a1, ZC - .1, ZC, WHITE, n, ink=True, e=.005)
    # the stair stringer on the left wall (a white band following the steps)
    for i in range(NST - 1):
        z = step_z(i)
        tr.decal([(.005, i * RUN, z), (.005, (i + 1) * RUN, z - RISE), (.005, (i + 1) * RUN, z - RISE + .14), (.005, i * RUN, z + .14)],
                 WHITE, ink=True, normal=(1, 0, 0))
    parts.append(tr)
    cor = Part('corners', sil=False)
    for p0, p1 in [((0, YF, 0), (0, YF, ZC)), ((X1, YF, 0), (X1, YF, ZC)), ((0, YB, ZT), (0, YB, ZC)), ((X1, YB, ZT), (X1, YB, ZC))]:
        cor.line(p0, p1, .012, INKC)
    parts.append(cor)
    # front wall: front door with glass, stairwell window (night sky), pictures
    deco = Part('deco_f', sil=False)
    door_panel(deco, 'y', YF, .35, 1.25, c=(46, 120, 96), n=-1, glass=(150, 200, 255))
    x0, x1, z0, z1 = WIN_S
    wrect(deco, 'y', YF, x0 - .09, x1 + .09, z0 - .12, z1 + .09, WHITE, -1, ink=True, e=.004)
    wrect(deco, 'y', YF, x0, x1, z0, z1, (40, 70, 170), -1, emit=1.0, e=.005)
    rs = np.random.default_rng(5)
    for k in range(18):
        sx_, sz = rs.uniform(x0, x1), rs.uniform(z0 + .25, z1)
        wrect(deco, 'y', YF, sx_, sx_ + .016, sz, sz + .016, (240, 240, 255), -1, emit=1.0, e=.006)
    deco.decal([(x1 - .38, YF - .0055, z1 - .42), (x1 - .16, YF - .0055, z1 - .42), (x1 - .16, YF - .0055, z1 - .2), (x1 - .38, YF - .0055, z1 - .2)],
               (250, 250, 230), emit=1.0, normal=(0, -1, 0))                                          # the moon
    for (a, b) in [((x0 + x1) / 2 - .025, (x0 + x1) / 2 + .025)]:
        wrect(deco, 'y', YF, a, b, z0, z1, WHITE, -1, ink=True, e=.009)
    wrect(deco, 'y', YF, x0, x1, (z0 + z1) / 2 - .025, (z0 + z1) / 2 + .025, WHITE, -1, ink=True, e=.009)
    picture(deco, 'y', YF, 1.6, 1.3, .5, .62, (250, 236, 210), -1, motif=(200, 90, 60))
    parts.append(deco)
    # left wall: a rising row of pictures along the stairs, coat hooks in the hall
    dl = Part('deco_l', sil=False)
    for k, (yy, c, m) in enumerate([(.3, (120, 190, 240), (250, 250, 250)), (1.0, (250, 236, 210), (90, 150, 200)),
                                    (1.7, (240, 150, 90), (250, 240, 200)), (2.4, (130, 200, 140), (250, 220, 90))]):
        zb = ZT + .9 - (yy + .2) * ZT / 3.36 + .45
        picture(dl, 'x', 0, yy, zb, .42 if k % 2 else .34, .5 if k % 2 else .42, c, 1, motif=m)
    wrect(dl, 'x', 0, 4.2, 5.6, 1.62, 1.68, (120, 74, 44), 1, ink=True)
    parts.append(dl)
    coats = Part('coats')
    for k, (yy, c) in enumerate([(4.4, (200, 120, 50)), (4.85, (70, 110, 160)), (5.3, (150, 60, 70))]):
        box((.02, yy - .17, .85), (.16, yy + .17, 1.62), c, part=coats)
    parts.append(coats)
    # right wall: side door (kitchen, warm light under it), console table, pictures; landing: a night lamp table
    dr = Part('deco_r', sil=False)
    door_panel(dr, 'x', X1, 4.55, 5.4, n=-1)
    picture(dr, 'x', X1, 3.6, 1.35, .5, .4, (250, 250, 248), -1, motif=(60, 60, 60))
    picture(dr, 'x', X1, -1.6, ZT + 1.2, .5, .6, (120, 190, 240), -1, motif=(240, 200, 80))
    door_panel(dr, 'y', YB, 1.25, 2.1, c=(252, 250, 246), n=1, z0=ZT)                              # bedroom door
    wrect(dr, 'y', YB, .42, .68, ZT + 1.55, ZT + 1.85, (255, 210, 140), 1, ink=True, emit=1.0, e=.03)  # wall sconce
    parts.append(dr)
    con = Part('console')
    box((X1 - .38, 3.55, 0), (X1, 4.25, .8), (176, 120, 78), part=con, cols={'top': (196, 140, 92)})
    box((X1 - .32, 3.7, .8), (X1 - .18, 3.84, 1.0), (240, 236, 226), part=con)          # vase
    for k in range(5): con.dot((X1 - .25 + rng.uniform(-.06, .06), 3.77 + rng.uniform(-.06, .06), 1.04 + rng.uniform(0, .08)), .05, (230, 90, 90), ink=True)
    box((X1 - .33, 3.98, .8), (X1 - .08, 4.18, .86), (60, 100, 170), part=con)          # books
    parts.append(con)
    nt = Part('nlamp')
    box((X1 - .45, -2.2, ZT), (X1 - .05, -1.7, ZT + .7), (176, 120, 78), part=nt)
    nt.line((X1 - .25, -1.95, ZT + .7), (X1 - .25, -1.95, ZT + .95), .02, (60, 60, 60))
    t_, b_ = .09, .16
    pb = [(X1 - .25 - b_, -1.95 - b_, ZT + .92), (X1 - .25 + b_, -1.95 - b_, ZT + .92), (X1 - .25 + b_, -1.95 + b_, ZT + .92), (X1 - .25 - b_, -1.95 + b_, ZT + .92)]
    pt = [(X1 - .25 - t_, -1.95 - t_, ZT + 1.12), (X1 - .25 + t_, -1.95 - t_, ZT + 1.12), (X1 - .25 + t_, -1.95 + t_, ZT + 1.12), (X1 - .25 - t_, -1.95 + t_, ZT + 1.12)]
    for i in range(4):
        j = (i + 1) % 4; nt.poly([pb[i], pb[j], pt[j], pt[i]], (255, 214, 150), ink=True, two=True, emit=1.0)
    parts.append(nt)
    umb = Part('umb'); box((.15, 6.0, 0), (.4, 6.25, .5), (60, 110, 150), part=umb)
    umb.line((.25, 6.1, .5), (.3, 6.12, .95), .025, (200, 60, 60)); umb.line((.3, 6.15, .5), (.22, 6.2, .9), .025, (40, 40, 40))
    parts.append(umb)
    return parts


HOUSE_ORDER = ['floor', 'rug', 'wall_l', 'wall_r', 'wall_f', 'wall_bk', 'wall_und', 'ceiling', 'deco_f', 'deco_l', 'deco_r', 'trims', 'corners']


def house_lights(img, cam, s=1.0, door=True, nlamp=True, moon=True):
    """The practicals of the stair hall at night (after night_map); lights behind the camera are skipped."""
    def vis(P): return cam.depth(P) > .3
    x0, x1, z0, z1 = WIN_S
    if moon and vis(((x0 + x1) / 2, YF, (z0 + z1) / 2)):
        x0, x1, z0, z1 = WIN_S
        TL.floor_patch(img, cam, [(x0, YF, z0), (x1, YF, z0), (x1, YF, z1), (x0, YF, z1)], MOON_L, col=(170, 210, 255),
                       k=.7, blur=3 * s, shaft=.2, cine=cine)
        TL.glow_at(img, *cam.p(((x0 + x1) / 2, YF, (z0 + z1) / 2)), 260 * s, (120, 160, 255), k=.35, core=0)
    if door and vis((X1, 5.0, 0)):
        TL.under_door(img, cam, (X1, 4.55, .002), (X1, 5.4, .002), depth=1.1, col=(255, 170, 80), k=1.0)
    sc = (.55, YB + .05, ZT + 1.7)
    if nlamp and vis(sc):
        TL.glow_at(img, *cam.p(sc), 200 * s, (255, 170, 80), k=.9, mix=.55)
        TL.wall_pool(img, cam, (.55, YB + .004, ZT + 1.5), 'y', .8, .9, (255, 160, 70), k=.7)
        TL.pool(img, cam, (.55, -1.0, ZT), .9, 1.1, (255, 160, 70), k=.5, z=ZT + .002)
    P = (X1 - .25, -1.95, ZT + 1.02)
    if nlamp and vis(P):
        TL.glow_at(img, *cam.p(P), 230 * s, (255, 180, 100), k=.9)
        TL.wall_pool(img, cam, (X1 - .004, -1.95, ZT + 1.2), 'x', .9, .9, (255, 170, 90), k=.55)
        TL.pool(img, cam, (X1 - .6, -1.6, ZT), .9, .8, (255, 170, 90), k=.5, z=ZT + .002)


def split_near(parts, cam, d):
    """(far, near) parts by the depth of their centre (near ones get the foreground blur)."""
    far, near = [], []
    for p in parts: (near if cam.depth(p.centre()) < d else far).append(p)
    return far, near


def stairs_frame(cam, chars, size, t=0.0, fg_d=1.3, fg_blur=14, beam=None, s_ink=1.0):
    """Render the night stair hall from cam: far set -> night_map -> practicals -> characters -> near set blurred."""
    img = Image.new('RGBA', size, (10, 14, 50, 255))
    k = size[0] / 1080
    parts = house()
    ban_front = cam.pos[0] > SX + .1                   # on the landing side: the banister is between us and the stairs
    far, near = split_near(parts, cam, fg_d)
    bans = [p for p in far if p.name == 'ban'] if ban_front else []
    far = [p for p in far if p not in bans]
    render_set(img, cam, far, NIGHT_LIGHT, order=HOUSE_ORDER, s=s_ink * k)
    ao(img, cam, [((0, YF, 0), (X1, YF, 0)), ((X1, YF, 0), (X1, 3.4, 0)), ((0, YF, 0), (0, 3.4, 0))])
    img = TL.night_map(img)
    house_lights(img, cam, k)
    g = None
    for c in chars:
        c = dict(c); fl = c.pop('flash', None)
        g = char_layer(img, cam, c.pop('P'), t=t, **c)
        if fl and g:
            hx, hy, _ = g['hands']['R']
            flashlight(img, (hx, hy), float(np.mean(g['scale'])), fl['ang'], beam=fl.get('len', 700) * k,
                       spread=fl.get('spread', 15), spot=fl.get('spot'), k=fl.get('k', .5))
    for grp, blur in ((bans, 0), (near, fg_blur)):
        if not grp: continue
        lay = Image.new('RGBA', size, (0, 0, 0, 0))
        render_set(lay, cam, grp, NIGHT_LIGHT, s=s_ink * k)
        lay = TL.night_map(lay)
        if blur: lay = cine.defocus(lay, blur * k)
        img.alpha_composite(lay)
    return img, g


# ------------------------------------------------------------------ frames
def S(): return (540, 960) if PREVIEW else (1080, 1920)


def frame_stairs_pov():
    """Peephole POV from the top step: banister close and blurred, the kid creeping up with a torch."""
    size = S(); k = size[0] / 1080
    cam = Cam((.62, -.45, ZT + 1.25), (.6, 3.4, .5), fov=62, size=size)
    i = 5; P = (.55, (i + .55) * RUN, step_z(i))
    img, g = stairs_frame(cam, [dict(P=P, expr='scared', pose='hold', h=1.3, look=.15, rim=(255, 200, 140), rim_dir=(1, -.3),
                                     flash=dict(ang=-122, len=760, spread=13, k=1.0, spot='end'), **PYJ_A)], size, fg_d=1.7, fg_blur=16)
    return finish3(img)


def frame_stairs_low():
    """Low angle from the hall floor up the stairs: the kid on the top steps, phone glow, warm landing lamp behind."""
    size = S(); k = size[0] / 1080
    cam = Cam((.6, 4.5, .4), (.5, .3, 2.7), fov=62, size=size)
    i = 2; P = (.5, (i + .5) * RUN, step_z(i))
    img, g = stairs_frame(cam, [dict(P=P, expr='worried', pose='hold', h=1.3, look=.3, prop='phone', rim=(255, 190, 120),
                                     rim_dir=(1, -1), **PYJ_B)], size, fg_d=0)
    if g:
        hx, hy, _ = g['hands']['R']
        TL.glow_at(img, hx, hy - 20 * k, 160 * k, (150, 230, 255), k=.8)
        hd = g['head']; TL.glow_at(img, hd[0], hd[1] + 60 * k, 140 * k, (150, 210, 255), k=.25, core=0)
    return finish3(img)


# --- night bedroom
def bedroom(rng=None):
    w, d = 4.0, 3.6
    parts = R2.room2(w, d, wall='#8fb0e0', wall_pattern=True, floor_col='#c08a5a', rng=rng or np.random.default_rng(6))
    wb = [p for p in parts if p.name == 'wall_b'][0]; wr = [p for p in parts if p.name == 'wall_r'][0]
    wl = [p for p in parts if p.name == 'wall_l'][0]
    R2.window_b(wb, d, 2.2, 3.2, 1.1, 2.1, 'night', curtain='#4a6ab0')
    wb.decal([(2.95, d - .0055, 1.75), (3.12, d - .0055, 1.75), (3.12, d - .0055, 1.92), (2.95, d - .0055, 1.92)], (250, 250, 230), emit=1.0, normal=(0, -1, 0))
    R2.door_r(wr, w, .5, 1.35, glass=False)
    picture(wl, 'x', 0, 1.6, 1.4, .5, .4, (250, 236, 210), 1, motif=(90, 150, 200))
    picture(wb, 'y', d, .3, 1.5, .4, .5, (120, 190, 240), -1, motif=(250, 220, 90))
    # posters + a shelf with toys over the bed
    wrect(wb, 'y', d, 1.0, 1.9, 1.45, 1.5, (176, 120, 78), -1, ink=True, e=.006)
    sh = Part('shelf_toys')
    for k, (x, c) in enumerate([(1.08, (230, 90, 90)), (1.3, (90, 170, 230)), (1.55, (250, 200, 80)), (1.75, (120, 200, 120))]):
        box((x, d - .16, 1.5), (x + .14, d - .02, 1.5 + .12 + .06 * (k % 2)), c, part=sh)
    parts.append(sh)
    rugp = R2.rug(parts, 1.4, .6, 3.4, 2.4, base=(244, 220, 200), border=(90, 120, 200))
    ns = Part('nstand'); box((1.95, 3.0, 0), (2.4, 3.5, .55), (176, 120, 78), part=ns, cols={'top': (196, 140, 92)})
    box((2.02, 3.05, .55), (2.22, 3.2, .7), (220, 70, 70), part=ns)                 # alarm clock body
    ns.decal([(2.04, 3.049, .57), (2.2, 3.049, .57), (2.2, 3.049, .68), (2.04, 3.049, .68)], (255, 120, 90), emit=1.0, normal=(0, -1, 0))
    parts.append(ns)
    ml = Part('mushroom')                                                            # a warm night-light on the stand
    ml.line((2.28, 3.32, .55), (2.28, 3.32, .66), .04, (250, 240, 220))
    ml.dot((2.28, 3.32, .7), .08, (255, 200, 120), ink=True, emit=1.0)
    parts.append(ml)
    toyb = Part('toybox'); box((3.2, 2.6, 0), (3.85, 3.2, .45), (90, 160, 210), part=toyb, cols={'top': (110, 180, 230)})
    toyb.dot((3.4, 2.9, .55), .1, (240, 140, 40), ink=True); toyb.dot((3.62, 2.85, .52), .07, (230, 90, 90), ink=True)
    parts.append(toyb)
    return parts, w, d


def bed_parts(x0=.12, x1=1.42, y0=1.25, y1=3.6, zt=.5):
    back, front = Part('bed_back'), Part('bed_front')
    box((x0, y1 - .1, 0), (x1, y1, 1.05), (120, 84, 60), part=back)                  # headboard
    box((x0 + .15, y1 - .5, zt), (x1 - .15, y1 - .12, zt + .16), (250, 250, 255), part=back)   # pillow
    box((x0, y0, 0), (x1, y1 - .1, zt - .08), (230, 232, 240), part=front, cols={'top': (240, 240, 246)})
    q = Part('quilt')
    box((x0 - .02, y0 - .02, zt - .08), (x1 + .02, y1 - .62, zt + .1), (80, 120, 210), part=q)
    box((x0 - .02, y1 - .82, zt + .1), (x1 + .02, y1 - .62, zt + .16), (250, 250, 255), part=q)   # folded sheet
    for i in range(4):
        for j in range(5):
            if (i + j) % 2:
                xa, ya = x0 + i * (x1 - x0) / 4, y0 + j * .27
                q.decal([(xa, ya, zt + .101), (xa + (x1 - x0) / 4, ya, zt + .101), (xa + (x1 - x0) / 4, ya + .27, zt + .101), (xa, ya + .27, zt + .101)],
                        (110, 160, 230), normal=(0, 0, 1))
    rq = np.random.default_rng(9)
    for k in range(22):
        q.dot((rq.uniform(x0 + .05, x1 - .05), rq.uniform(y0 + .05, y1 - .85), zt + .105), .022, (250, 236, 150))
    box((.4, y0 + .55, zt + .1), (1.15, y0 + 1.0, zt + .2), (80, 120, 210), part=q)              # knees under the quilt
    return back, front, q


def frame_night_bed():
    """Night bedroom: the kid sits up in bed, phone glow on the face, moonlight shaft + window patch on the floor,
    warm light under the door, the alarm clock glow."""
    size = S(); k = size[0] / 1080
    img = Image.new('RGBA', size, (10, 14, 50, 255))
    parts, w, d = bedroom()
    back, front, quilt = bed_parts()
    cam = Cam((3.3, -.1, 1.4), (1.45, 2.95, .85), fov=56, size=size)
    render_set(img, cam, parts + [back], NIGHT_LIGHT, order=['floor', 'wall_b', 'wall_l', 'wall_r', 'ceiling', 'trims', 'corners', 'rug'], s=k)
    ao(img, cam, [((0, d, 0), (w, d, 0)), ((w, d, 0), (w, 0, 0)), ((0, d, 0), (0, 0, 0))])
    img = TL.night_map(img)
    TL.floor_patch(img, cam, [(2.2, d, 1.1), (3.2, d, 1.1), (3.2, d, 2.1), (2.2, d, 2.1)], (-.3, -.6, -.74), col=(170, 210, 255),
                   k=.75, blur=3 * k, shaft=.22, cine=cine)
    TL.glow_at(img, *cam.p((2.7, d, 1.6)), 260 * k, (120, 160, 255), k=.35, core=0)
    TL.under_door(img, cam, (w, 1.35, .002), (w, .5, .002), depth=1.0, col=(255, 170, 80), k=1.0)
    TL.glow_at(img, *cam.p((2.12, 3.045, .63)), 50 * k, (255, 110, 80), k=.7)
    TL.glow_at(img, *cam.p((2.28, 3.32, .7)), 130 * k, (255, 160, 70), k=1.0, mix=.6)
    TL.wall_pool(img, cam, (2.3, 3.596, .8), 'y', .5, .35, (255, 160, 80), k=.7)
    TL.pool(img, cam, (2.2, 3.1, .552), .35, .3, (255, 180, 100), k=.6, z=.552)
    TL.pool(img, cam, (2.2, 2.9, .002), .8, .6, (255, 170, 90), k=.35)
    g = char_layer(img, cam, (.77, 2.95, .02), expr='worried', pose='hold', h=1.4, look=.35, prop='phone',
                   rim=(170, 210, 255), rim_dir=(1, -.2), **PYJ_A)
    lay = Image.new('RGBA', size, (0, 0, 0, 0))
    render_set(lay, cam, [front, quilt], NIGHT_LIGHT, s=k)
    img.alpha_composite(TL.night_map(lay))
    if g:
        hx, hy, _ = g['hands']['R']
        TL.glow_at(img, hx + 10 * k, hy - 10 * k, 170 * k, (150, 230, 255), k=.85)
        hd = g['head']; TL.glow_at(img, hd[0] + 30 * k, hd[1] + 50 * k, 170 * k, (150, 220, 255), k=.25, core=0)
    return finish3(img)


# --- day living room with two characters
def frame_day_two():
    """Day: grandpa sits on the sofa with a cup, the kid peeks round the door frame (a real hole in the back wall:
    the kid is drawn first, the wall covers all but what shows through the doorway); the coffee table is drawn
    after grandpa so it sits in front of his legs."""
    size = S(); k = size[0] / 1080
    w, d, h = 4.6, 4.0, 2.7
    rng = np.random.default_rng(4)
    c = col('#f3e6c4')
    parts = [p for p in R2.room2(w, d, wall='#f3e6c4', floor_col='#c98d54', rng=rng) if p.name != 'wall_b']
    dx0, dx1 = 2.15, 2.95                                   # doorway in the back wall (x range), 2.1 high
    wb = Part('wall_b', sil=False)
    for (a, b, z0, z1) in [(0, dx0, 0, h), (dx1, w, 0, h), (dx0, dx1, 2.1, h)]:
        wb.poly([(a, d, z0), (b, d, z0), (b, d, z1), (a, d, z1)], c)
    wl = [p for p in parts if p.name == 'wall_l'][0]
    for zz in np.arange(.3, h - .2, .26):                    # wallpaper motifs (none in the doorway)
        for xx in np.arange(.15 + (zz * 7 % .26), w, .26):
            if not (dx0 - .08 < xx < dx1 + .05 and zz < 2.2):
                wrect(wb, 'y', d, xx, xx + .025, zz, zz + .06, shade(c, .88), -1, e=.0015)
        for yy in np.arange(.15 + (zz * 7 % .26), d, .26):
            wrect(wl, 'x', 0, yy, yy + .025, zz, zz + .06, shade(c, .85), 1, e=.0015)
    for (a, b, z0, z1) in [(dx0 - .08, dx0, 0, 2.18), (dx1, dx1 + .08, 0, 2.18), (dx0 - .08, dx1 + .08, 2.1, 2.18)]:
        wrect(wb, 'y', d, a, b, z0, z1, WHITE, -1, ink=True, e=.005)
    R2.window_b(wb, d, 3.4, 4.3, 1.0, 2.2, 'day', curtain='#f0b030')
    picture(wb, 'y', d, .35, 1.45, .55, .42, (120, 190, 240), -1, motif=(250, 250, 250))
    picture(wb, 'y', d, 1.05, 1.62, .32, .4, (250, 236, 210), -1, motif=(200, 90, 60))
    picture(wb, 'y', d, 1.5, 1.3, .4, .32, (240, 150, 90), -1, motif=(250, 240, 200))
    wrect(wb, 'y', d, 1.0, 1.06, 0, 2.5, shade(c, .93), -1, e=.002)
    parts.insert(1, wb)
    jamb = Part('jamb')
    box((dx0 - .08, d, 0), (dx0, d + .14, 2.18), WHITE, part=jamb); box((dx1, d, 0), (dx1 + .08, d + .14, 2.18), WHITE, part=jamb)
    parts.append(jamb)
    R2.rug(parts, .5, 1.2, 3.3, 3.2, rng=rng)
    parts.append(ST.sofa(.35, 3.05, wdt=1.75, c='#e24c48'))
    R2.side_table(parts, 3.25, 3.65)
    parts.append(ST.plant(4.25, 3.55, .9))
    sh = ST.bookshelf(3.6, 2.2, wdt=.9, h=1.8) if False else None
    R2.pumpkin(parts, 3.0, 3.75, 0, r=.12)
    tv = Part('tv'); box((w - .5, 1.0, 0), (w, 2.2, .55), (176, 120, 78), part=tv, cols={'top': (196, 140, 92)})
    box((w - .3, 1.15, .55), (w - .22, 2.05, 1.15), (40, 40, 50), part=tv); parts.append(tv)
    ctab = Part('ctable'); box((.65, 1.75, 0), (1.85, 2.3, .4), (176, 120, 78), part=ctab, cols={'top': (196, 140, 92)})
    box((.85, 1.9, .4), (1.2, 2.15, .46), (60, 110, 170), part=ctab); box((1.5, 1.95, .4), (1.6, 2.05, .52), (250, 250, 250), part=ctab)
    ctab.dot((1.72, 2.15, .45), .05, (240, 140, 40), ink=True)
    cam = Cam((2.05, -.35, 1.2), (1.75, 3.0, .85), fov=66, size=size)
    img = Image.new('RGBA', size, (240, 230, 200, 255))
    # beyond the doorway: the next room (a sunny yellow wall + floor) and the kid peeking round the left jamb
    nr = Part('next', sil=False)
    nr.poly([(dx0 - 1.5, d + 1.4, 0), (dx1 + 1.5, d + 1.4, 0), (dx1 + 1.5, d + 1.4, h), (dx0 - 1.5, d + 1.4, h)], (246, 206, 96))
    nr.poly([(dx0 - 1.5, d, 0), (dx1 + 1.5, d, 0), (dx1 + 1.5, d + 1.4, 0), (dx0 - 1.5, d + 1.4, 0)], (190, 140, 96))
    for xx in np.arange(dx0 - 1.4, dx1 + 1.5, .3):
        wrect(nr, 'y', d + 1.4, xx, xx + .12, 0, h, (240, 190, 80), -1, e=.002)
    render_set(img, cam, [nr], DAY_LIGHT, s=k)
    hangar.stand(img, cam, (dx0 - .05, d + .35, 0), 0.0, expr='surprised', pose='stand', h=1.3, look=.55, lean=13,
                 rim=(255, 250, 230), blink_ok=False, **PYJ_A)
    render_set(img, cam, parts, DAY_LIGHT, order=['floor', 'wall_b', 'wall_l', 'wall_r', 'ceiling', 'trims', 'corners', 'rug'], s=k)
    R2.soft_ao(img, cam, [((0, d, 0), (w, d, 0)), ((w, d, 0), (w, 0, 0)), ((0, d, 0), (0, 0, 0))])
    lay = Image.new('RGBA', size, (0, 0, 0, 0)); dd = ImageDraw.Draw(lay)
    dd.polygon([cam.p((3.2, 3.3, .001)), cam.p((4.4, 3.3, .001)), cam.p((4.1, 1.7, .001)), cam.p((2.9, 1.7, .001))], fill=(255, 250, 220, 80))
    img.alpha_composite(lay.filter(ImageFilter.GaussianBlur(18 * k)))
    sit = dict(armL=(24, 10), armR=(-30, -95, .95, .9), legL=(42, 4, 1.0, .5), legR=(-42, -4, 1.0, .5), _name='sit')
    hangar.stand(img, cam, (1.2, 3.0, .12), 0.0, expr='happy', pose=sit, h=1.5, look=.45, prop='cup', rim=(255, 250, 230),
                 rim_dir=(1, -.4), blink_ok=False, **CARDI)
    render_set(img, cam, [ctab], DAY_LIGHT, s=k)
    return finish2(img)


def finish2(img): return finish3(img, night=False, vig=.14, grain=.01, bloom_k=.12, thr=215)


# --- macros
def frame_phone_macro():
    """Macro: the phone glowing in the kid's hand in bed (the night bedroom defocused behind)."""
    size = S(); k = size[0] / 1080
    W_, H_ = size
    img = Image.new('RGBA', size, (10, 14, 50, 255))
    parts, w, d = bedroom()
    back, front, quilt = bed_parts()
    cam = Cam((1.2, 1.9, 1.0), (1.9, 3.6, .9), fov=55, size=size)
    render_set(img, cam, parts + [back, front, quilt], NIGHT_LIGHT, order=['floor', 'wall_b', 'wall_l', 'wall_r', 'ceiling', 'trims', 'corners', 'rug'], s=k)
    img = TL.night_map(img)
    TL.glow_at(img, *cam.p((2.7, d, 1.6)), 300 * k, (120, 160, 255), k=.45, core=.2)
    TL.glow_at(img, *cam.p((2.12, 3.045, .63)), 90 * k, (120, 255, 200), k=.9)
    img = cine.defocus(img, 18 * k)
    cine.bokeh(img, [(W_ * .7, H_ * .3, 1.2), (W_ * .2, H_ * .22, .8), (W_ * .82, H_ * .55, .7)], 40 * k, col=(160, 200, 255), alpha=.35)
    # the arm (stickman white, black outline, flat fill) rising from the bottom to a round hand at the phone's grip
    T = 190 * k; O = 13 * k; HAND = (222, 232, 255)
    A, Hc = (W_ * .9, H_ * 1.08), (W_ * .6, H_ * .66)
    ux, uy = Hc[0] - A[0], Hc[1] - A[1]; n_ = math.hypot(ux, uy); ux, uy = ux / n_, uy / n_
    def tube(dl, p0, p1, wdt, c, cap=True):
        dl.line([p0, p1], fill=c, width=int(wdt))
        if cap: dl.ellipse((p1[0] - wdt / 2, p1[1] - wdt / 2, p1[0] + wdt / 2, p1[1] + wdt / 2), fill=c)
    lay = Image.new('RGBA', size, (0, 0, 0, 0)); dl = ImageDraw.Draw(lay)
    tube(dl, A, Hc, T + 2 * O, INKC); tube(dl, A, Hc, T, HAND)
    img.alpha_composite(lay)
    # the phone (tilted), its glowing screen
    ph = Image.new('RGBA', (int(420 * k), int(800 * k)), (0, 0, 0, 0)); dp = ImageDraw.Draw(ph)
    pw, phh = ph.size
    dp.rounded_rectangle((0, 0, pw - 1, phh - 1), 56 * k, fill=INKC)
    dp.rounded_rectangle((10 * k, 10 * k, pw - 11 * k, phh - 11 * k), 48 * k, fill=(48, 52, 66))
    sx0, sy0, sx1, sy1 = 28 * k, 60 * k, pw - 28 * k, phh - 60 * k
    dp.rounded_rectangle((sx0, sy0, sx1, sy1), 22 * k, fill=(214, 240, 255))
    dp.rectangle((sx0, sy0, sx1, sy0 + 90 * k), fill=(90, 170, 240))                      # header bar
    dp.ellipse((sx0 + 20 * k, sy0 + 20 * k, sx0 + 70 * k, sy0 + 70 * k), fill=(250, 250, 255))
    dp.rounded_rectangle((sx0 + 90 * k, sy0 + 34 * k, sx0 + 230 * k, sy0 + 56 * k), 10 * k, fill=(240, 250, 255))
    yb = sy0 + 130 * k
    for j, (wf, right, c) in enumerate([(.62, 0, (255, 255, 255)), (.48, 1, (120, 220, 150)), (.7, 0, (255, 255, 255)),
                                        (.36, 1, (120, 220, 150)), (.55, 0, (255, 120, 110))]):
        bw_ = (sx1 - sx0 - 40 * k) * wf; bh = 70 * k if j != 2 else 110 * k
        xa = sx1 - 20 * k - bw_ if right else sx0 + 20 * k
        dp.rounded_rectangle((xa, yb, xa + bw_, yb + bh), 26 * k, fill=c, outline=(150, 190, 220), width=max(1, int(3 * k)))
        for li in range(int(bh / (34 * k))):
            dp.rounded_rectangle((xa + 18 * k, yb + 18 * k + li * 34 * k, xa + bw_ * (.8 - .2 * li), yb + 30 * k + li * 34 * k), 6 * k, fill=shade(c, .72))
        yb += bh + 26 * k
    dp.rounded_rectangle((pw / 2 - 60 * k, 24 * k, pw / 2 + 60 * k, 38 * k), 7 * k, fill=(20, 20, 26))
    ph = ph.rotate(-14, resample=Image.BICUBIC, expand=True)
    px, py = int(Hc[0] - ph.width * .62), int(Hc[1] - ph.height * .86)
    # screen glow behind/around + light on the hand
    gm = Image.new('L', size, 0); gm.paste(ph.split()[3], (px, py))
    kit.glow(img, gm, (140, 210, 255), .9, blur=int(90 * k), add=True)
    img.alpha_composite(ph, (px, py))
    # the hand end redrawn over the phone's lower edge (the grip): ink disc + fill, then the forearm fill again
    # (no outline) so the disc's ink never shows across the arm (DRAWING_RULES 9); then the striped pyjama sleeve
    lay = Image.new('RGBA', size, (0, 0, 0, 0)); dl = ImageDraw.Draw(lay)
    r = T * .5
    dl.ellipse((Hc[0] - r - O, Hc[1] - r - O, Hc[0] + r + O, Hc[1] + r + O), fill=INKC)
    dl.ellipse((Hc[0] - r, Hc[1] - r, Hc[0] + r, Hc[1] + r), fill=HAND)
    tube(dl, A, (Hc[0] - ux * r * .2, Hc[1] - uy * r * .2), T, HAND, cap=False)
    S0, S1 = A, (A[0] + ux * n_ * .55, A[1] + uy * n_ * .55)
    tube(dl, S0, S1, T, (200, 140, 50), cap=False)
    for j in (-.3, 0, .3):
        dl.line([(S0[0] - uy * T * j, S0[1] + ux * T * j), (S1[0] - uy * T * j, S1[1] + ux * T * j)], fill=(246, 206, 130), width=int(14 * k))
    img.alpha_composite(lay)
    TL.glow_at(img, Hc[0] - 40 * k, Hc[1] - 60 * k, 200 * k, (140, 210, 255), k=.35, core=0)
    TL.glow_at(img, W_ * .5, H_ * .45, 420 * k, (160, 220, 255), k=.35, core=0)
    return finish3(img, vig=.3, bloom_k=.45, thr=190)


def frame_lock_macro():
    """Macro: the bedroom door's brass knob and keyhole at night from the landing; warm light through the keyhole
    and under the door; past the door's edge the stair hall, defocused."""
    size = S(); k = size[0] / 1080
    W_, H_ = size
    cam_bg = Cam((2.0, -2.0, ZT + 1.2), (.8, 2.0, ZT - .2), fov=50, size=size)
    bg = Image.new('RGBA', size, (10, 14, 50, 255))
    render_set(bg, cam_bg, house(), NIGHT_LIGHT, order=HOUSE_ORDER, s=k)
    bg = TL.night_map(bg); house_lights(bg, cam_bg, k)
    bg = cine.defocus(bg, 24 * k)
    cine.bokeh(bg, [(W_ * .12, H_ * .3, 1.0), (W_ * .22, H_ * .62, .7), (W_ * .08, H_ * .8, .5)], 46 * k, col=(255, 190, 120), alpha=.35)
    img = bg
    # the door: plane y=0 (facing -y), free edge at x=0 with the knob near it, door body toward +x
    dc = Cam((-.42, -.95, 1.12), (.2, 0, .95), fov=40, size=size)
    door = Part('door', sil=False)
    dcol = (150, 160, 190)
    door.poly([(0, 0, -.3), (1.0, 0, -.3), (1.0, 0, 2.2), (0, 0, 2.2)][::-1], dcol)
    door.poly([(0, 0, -.3), (0, 0, 2.2), (0, .045, 2.2), (0, .045, -.3)][::-1], shade(dcol, .8), ink=True)
    door.decal([(.14, -.004, 1.25), (.86, -.004, 1.25), (.86, -.004, 2.1), (.14, -.004, 2.1)], shade(dcol, .9), ink=True, normal=(0, -1, 0))
    door.decal([(.2, -.006, 1.31), (.8, -.006, 1.31), (.8, -.006, 2.04), (.2, -.006, 2.04)], shade(dcol, 1.05), ink=True, normal=(0, -1, 0))
    door.decal([(.14, -.004, -.2), (.86, -.004, -.2), (.86, -.004, .82), (.14, -.004, .82)], shade(dcol, .9), ink=True, normal=(0, -1, 0))
    door.decal([(.2, -.006, -.14), (.8, -.006, -.14), (.8, -.006, .76), (.2, -.006, .76)], shade(dcol, 1.05), ink=True, normal=(0, -1, 0))
    hw = Part('hardware')
    brass = (214, 168, 70)
    box((.04, -.015, .78), (.13, 0, 1.2), brass, part=hw)                            # escutcheon plate
    hw.decal([(.075, -.016, .83), (.095, -.016, .83), (.092, -.016, .88), (.078, -.016, .88)], (255, 200, 110), emit=1.0, normal=(0, -1, 0))
    hw.dot((.085, -.0162, .895), .017, (255, 200, 110), emit=1.0)
    hw.line((.085, 0, 1.04), (.085, -.06, 1.04), .028, shade(brass, .8))
    hw.dot((.085, -.085, 1.04), .05, brass, ink=True)
    for zz in (.81, 1.17): hw.dot((.085, -.017, zz), .007, shade(brass, .7))
    dlay = Image.new('RGBA', size, (0, 0, 0, 0))
    P3.render(dlay, dc, [door], light=NIGHT_LIGHT, ink=INKC, ink_w=4 * k, sil_w=7 * k)
    img.alpha_composite(TL.night_map(dlay))
    hlay = Image.new('RGBA', size, (0, 0, 0, 0))
    P3.render(hlay, dc, [hw], light=Light(d=(-.6, -.5, .6), amb=.55, bands=(.2, .5, .8), soft=.3, shadow=(30, 30, 90), shadow_k=.4),
              ink=INKC, ink_w=4 * k, sil_w=7 * k)
    img.alpha_composite(TL.moon_tint(hlay, col=(150, 150, 205)))
    # warm light: through the keyhole (a beam with dust), on the knob, the gap under the door
    kx, ky = dc.p((.085, -.016, .875))
    TL.glow_at(img, kx, ky, 80 * k, (255, 190, 100), k=1.0)
    TL.cone(img, kx, ky, 200, 900 * k, spread=5, col=(255, 196, 120), k=.5)
    TL.glow_at(img, *dc.p((.07, -.12, 1.07)), 40 * k, (255, 230, 170), k=.7)
    nx, ny = dc.p((.085, -.085, 1.04))
    TL.add_light(img, TL.ellipse_soft(size, nx - 95 * k, ny + 40 * k, 60 * k, 40 * k, 30 * k), (255, 170, 80), .45)
    a, b = dc.p((0, -.01, -.29)), dc.p((1.0, -.01, -.29))
    m = Image.new('L', size, 0); ImageDraw.Draw(m).line([a, b], fill=255, width=int(14 * k))
    TL.add_light(img, m.filter(ImageFilter.GaussianBlur(8 * k)), (255, 170, 80), 1.0)
    cine.motes(img, 0.0, (int(kx - 700 * k), int(ky - 100 * k), int(kx - 40 * k), int(ky + 420 * k)), n=50, col=(255, 220, 160), alpha=170)
    return finish3(img, vig=.3, bloom_k=.45, thr=190)


# ------------------------------------------------------------------ the camera move
def clip_path(dur=3.5):
    return P3.Path([(0.0, (1.75, -2.05, ZT + 1.22), (1.1, 2.0, ZT + .5), 60, 0),
                    (dur * .45, (1.15, -1.2, ZT + 1.26), (.75, 2.8, 1.6), 61, 0),
                    (dur, (.62, -.45, ZT + 1.25), (.6, 3.4, .5), 62, 0)], drift=.006)


def clip(outdir, fps=24, dur=3.5, size=(540, 960)):
    """Landing by the bedroom door -> the top of the stairs, tilting down to the kid creeping up with a torch."""
    os.makedirs(outdir, exist_ok=True)
    path = clip_path(dur)
    n = int(fps * dur)
    for f in range(n):
        t = f / fps
        c = path.at(t); cam = Cam(c.pos, c.target, c.fov, c.roll, size=size)
        u = cine.smooth((t - 1.1) / 1.0)                  # the kid climbs one step: tread 6 -> tread 5, a small lift
        P = (.55, (6.55 - u) * RUN, step_z(6) + (step_z(5) - step_z(6)) * u + .07 * math.sin(math.pi * u))
        img, g = stairs_frame(cam, [dict(P=P, expr='scared', pose='hold', h=1.3, look=.15, rim=(255, 200, 140), rim_dir=(1, -.3),
                                         flash=dict(ang=-122 + 8 * math.sin(t * 1.7), len=760, spread=13, k=1.0, spot='end'), **PYJ_A)],
                              size, t=t, fg_d=1.7, fg_blur=16)
        img = finish3(img)
        img.convert('RGB').save(os.path.join(outdir, f'f{f:04d}.png'))
    return n


FRAMES = dict(night_bed=frame_night_bed, stairs_pov=frame_stairs_pov, stairs_low=frame_stairs_low, day_two=frame_day_two,
              phone_macro=frame_phone_macro, lock_macro=frame_lock_macro)

if __name__ == '__main__':
    names = sys.argv[2:] or list(FRAMES)
    if PREVIEW: P3.SS = 1
    else: P3.SS = 2
    for name in names:
        if name == 'clip':
            P3.SS = 1; clip(os.path.join(OUT, 'clip_frames')); print('ok clip'); continue
        try:
            im = FRAMES[name]()
            im.convert('RGB').save(os.path.join(OUT, name + '.png'))
            print('ok', name, TL.measure(im))
        except Exception as e:
            import traceback; traceback.print_exc(); print('FAIL', name, e)
