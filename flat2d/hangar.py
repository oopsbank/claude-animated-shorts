"""The 1954 test hangar world (video 12, plane-windows): a Farnborough-style test hangar built in 3D for persp.render,
with the hero image: a Comet fuselage sunk in a giant water tank, its wings out through the tank walls on jacks.

World (metres, z up): the Comet's nose at x = 0, its axis along +x at y = 0, z = ZC. The tank (inner box
x TX0..TX1, y -TY..TY, floor 0, rim TZ) holds water to WZ, so the fuselage is under water and the fin breaks the
surface; the wings pass through the long walls (rubber seals) and rest on hydraulic jacks. Gantries with railings run
along both long walls at rim height; a control desk (gauges, a cycle counter) and a pump stand at the nose end. The
hangar: a concrete floor, riveted grey-green steel, big sliding doors with window strips, clerestory windows, a
pitched roof on lattice trusses with skylight strips, hanging enamel lamps.

`scene(cam, t, ...)` draws the whole set in DOF layers (background / mid / foreground) with the water (planar
reflections of the skylights, ripples round the fin, caustics, refraction wobble), light shafts and motes, and returns
(img, info) before grading. Characters are placed in 3D with `stand`.
"""
import math, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageChops
import kit, anim, cine
import persp as P3
import airliner as A
from persp import Part, rgb_mix, rgb_mul

# ---------------------------------------------------------------- dimensions
TX0, TX1, TY, TZ, WALL = -1.8, 30.4, 4.3, 5.4, .3
WZ = 5.1
ZC = 3.0
HX0, HX1, HY, HZ, RIDGE = -52.0, 92.0, 56.0, 25.0, 32.5
LIGHT_DIR = (.06, -.52, -.85)            # sunlight through the skylights (from the light into the room)

STEEL = (80, 102, 96)        # grey-green painted steel
STEEL_D = (52, 66, 66)
TANKC = (88, 112, 106)
TANK_IN = (96, 120, 118)
CREAM = (214, 206, 182)
FLOOR = (112, 110, 104)
FLOOR2 = (108, 106, 100)
ROOF = (54, 62, 66)
GLASSW = (236, 244, 236)
YEL = (228, 186, 60)
RUBBER = (34, 34, 40)
WATER = (34, 128, 138)
WATER_DEEP = (14, 58, 74)

LIGHT = P3.Light(d=(-.28, -.3, .9), amb=.5, bands=(.2, .55, .82), soft=.4, shadow=(44, 64, 84), shadow_k=.34)


def fog_hangar(c, P, depth):
    """Aerial haze in the big hangar: far things fade toward a grey-green haze."""
    k = max(0.0, min(.4, (depth - 45) / 140))
    return rgb_mix(c, (96, 116, 114), k)


def fog_water(c, P, depth):
    """Under water: mix toward deep teal by the depth below the surface."""
    d = max(0.0, WZ - P[2]); k = 1 - math.exp(-d / 3.8)
    c = rgb_mix(c, WATER, .1 + .5 * k)
    return rgb_mix(c, WATER_DEEP, max(0.0, k - .5) * .7)


# ---------------------------------------------------------------- static parts (built once per process)
_S = {}


def _hangar_shell():
    bg = []
    floor = Part('floor', sil=False, order=-1e9)
    step = 6.0
    rng = np.random.default_rng(7)
    for i, x in enumerate(np.arange(HX0, HX1, step)):
        for j, y in enumerate(np.arange(-HY, HY, step)):
            col = rgb_mul(FLOOR, rng.uniform(.95, 1.04))
            floor.poly([(x, y, 0), (x + step, y, 0), (x + step, y + step, 0), (x, y + step, 0)], col)
    for x in np.arange(HX0, HX1, step):
        floor.line((x, -HY, .005), (x, HY, .005), .05, (84, 82, 78), ink=False)
    for y in np.arange(-HY, HY, step):
        floor.line((HX0, y, .005), (HX1, y, .005), .05, (84, 82, 78), ink=False)
    # painted safety lines round the tank
    for y in (-TY - 3.4, TY + 3.4):
        floor.decal([(TX0 - 4, y - .12, .01), (TX1 + 4, y - .12, .01), (TX1 + 4, y + .12, .01), (TX0 - 4, y + .12, .01)], YEL, normal=(0, 0, 1))
    bg.append(floor)
    # far end wall (x = HX1): big sliding doors with window strips
    wall = Part('wall_end', sil=False)
    for k in range(8):
        y0 = -HY + k * (2 * HY / 8); y1 = y0 + 2 * HY / 8
        col = (92, 108, 104) if k % 2 else (86, 101, 98)
        wall.poly([(HX1, y0, 0), (HX1, y0, 18), (HX1, y1, 18), (HX1, y1, 0)][::-1], col, ink=2)
        wall.decal([(HX1 - .05, y0 + 1.0, 13.6), (HX1 - .05, y1 - 1.0, 13.6), (HX1 - .05, y1 - 1.0, 16.6), (HX1 - .05, y0 + 1.0, 16.6)][::-1],
                   GLASSW, emit=1.0, ink=2, normal=(-1, 0, 0))
        for z in (4.0, 8.0):
            wall.decal([(HX1 - .05, y0 + .6, z), (HX1 - .05, y1 - .6, z), (HX1 - .05, y1 - .6, z + .25), (HX1 - .05, y0 + .6, z + .25)][::-1],
                       rgb_mul(col, .8), normal=(-1, 0, 0))
    wall.poly([(HX1, -HY, 18), (HX1, -HY, HZ), (HX1, 0, RIDGE), (HX1, HY, HZ), (HX1, HY, 18)][::-1], (96, 110, 106))
    bg.append(wall)
    # far side wall (y = HY): a cream dado, window bands, clerestory, stanchions
    side = Part('wall_side', sil=False)
    for k, x in enumerate(np.arange(HX0, HX1, 9.0)):
        x1 = x + 9.0
        side.poly([(x, HY, 0), (x1, HY, 0), (x1, HY, 2.6), (x, HY, 2.6)], (176, 168, 146))
        side.poly([(x, HY, 2.6), (x1, HY, 2.6), (x1, HY, HZ), (x, HY, HZ)], (82, 98, 96) if k % 2 else (78, 94, 92))
        side.decal([(x + 1.0, HY - .05, 4.2), (x1 - 1.0, HY - .05, 4.2), (x1 - 1.0, HY - .05, 7.4), (x + 1.0, HY - .05, 7.4)],
                   (206, 222, 214), emit=1.0, ink=2, normal=(0, -1, 0))
        side.decal([(x + .8, HY - .05, 15.0), (x1 - .8, HY - .05, 15.0), (x1 - .8, HY - .05, 21.4), (x + .8, HY - .05, 21.4)],
                   GLASSW, emit=1.0, ink=2, normal=(0, -1, 0))
        side.line((x, HY - .3, 0), (x, HY - .3, HZ), .55, STEEL_D)
    bg.append(side)
    # near side wall and the nose end wall (seen in reverse angles)
    near = Part('wall_near', sil=False)
    for k, x in enumerate(np.arange(HX0, HX1, 9.0)):
        x1 = x + 9.0
        near.poly([(x1, -HY, 0), (x, -HY, 0), (x, -HY, 2.6), (x1, -HY, 2.6)], CREAM)
        near.poly([(x1, -HY, 2.6), (x, -HY, 2.6), (x, -HY, HZ), (x1, -HY, HZ)], (100, 116, 112))
        near.decal([(x1 - .8, -HY + .05, 15.0), (x + .8, -HY + .05, 15.0), (x + .8, -HY + .05, 21.4), (x1 - .8, -HY + .05, 21.4)],
                   GLASSW, emit=1.0, ink=2, normal=(0, 1, 0))
    bg.append(near)
    endw = Part('wall_nose', sil=False)
    endw.poly([(HX0, -HY, 0), (HX0, HY, 0), (HX0, HY, HZ), (HX0, 0, RIDGE), (HX0, -HY, HZ)][::-1][::-1], (100, 116, 112))
    bg.append(endw)
    # roof: panels + skylight strips between trusses, lattice trusses, purlins, lamps
    roof = Part('roof', sil=False)
    for k, x in enumerate(np.arange(HX0, HX1, 9.0)):
        x1 = x + 9.0
        for s in (1, -1):
            def rp(yy): return RIDGE - (RIDGE - HZ) * abs(yy) / HY
            ys = [0, 10, 26, HY]
            for a, b in zip(ys[:-1], ys[1:]):
                ya, yb = s * a, s * b
                glass = (a, b) == (10, 26)
                pts = [(x, ya, rp(ya)), (x1, ya, rp(ya)), (x1, yb, rp(yb)), (x, yb, rp(yb))]
                if s > 0: pts = pts[::-1]
                lit = glass and s > 0 and k % 2 == 0
                roof.poly(pts, (255, 248, 226) if lit else GLASSW if glass else ROOF, emit=1.0 if glass else 0.0, two=True)
    bg.append(roof)
    trusses = Part('trusses', sil=False)
    for x in np.arange(HX0, HX1 + .1, 9.0):
        trusses.line((x, -HY, HZ), (x, HY, HZ), .38, STEEL_D, ink=1.5)
        for s in (1, -1):
            trusses.line((x, 0, RIDGE), (x, s * HY, HZ), .42, STEEL_D, ink=1.5)
            for k in range(1, 9):
                y = s * HY * k / 9; zt = RIDGE - (RIDGE - HZ) * k / 9
                trusses.line((x, y, HZ), (x, y, zt), .16, STEEL_D, ink=False)
                y2 = s * HY * (k - 1) / 9; zt2 = RIDGE - (RIDGE - HZ) * (k - 1) / 9
                trusses.line((x, y, HZ), (x, y2, zt2), .16, STEEL_D, ink=False)
    for s in (1, -1):
        for yy in (8, 30, 46):
            z = RIDGE - (RIDGE - HZ) * yy / HY
            trusses.line((HX0, s * yy, z - .2), (HX1, s * yy, z - .2), .22, STEEL_D, ink=False)
    # overhead crane girder across the hangar
    trusses.line((44, -HY, 21.4), (44, HY, 21.4), .9, (176, 140, 58), ink=2)
    trusses.line((44.9, -HY, 21.4), (44.9, HY, 21.4), .9, (160, 126, 50), ink=2)
    bg.append(trusses)
    lamps = Part('lamps', sil=False)
    for x in np.arange(HX0 + 4.5, HX1, 18.0):
        for y in LAMP_Y:
            lamps.line((x, y, HZ), (x, y, 15.2), .05, (40, 40, 44), ink=False)
            lamps.dot((x, y, 14.9), .45, (60, 72, 70))
            lamps.dot((x, y, 14.7), .22, (255, 236, 190), emit=1.0)
    bg.append(lamps)
    return bg


def _tank():
    """Tank walls (inner faces for the under-water view, outer faces + rims), stiffeners, portholes, seals."""
    inner = Part('tank_inner', sil=False, order=-1e8)
    x0, x1, y0, y1 = TX0, TX1, -TY, TY
    inner.poly([(x0, y0, 0), (x1, y0, 0), (x1, y1, 0), (x0, y1, 0)], (70, 96, 96))                       # floor (up)
    for (a, b, nrm) in (((x0, y1), (x1, y1), (0, -1, 0)), ((x1, y0), (x0, y0), (0, 1, 0)), ((x1, y1), (x1, y0), (-1, 0, 0)),
                        ((x0, y0), (x0, y1), (1, 0, 0))):
        pts = [(a[0], a[1], 0), (b[0], b[1], 0), (b[0], b[1], TZ), (a[0], a[1], TZ)]
        if np.dot(P3._newell(np.array(pts, float)), nrm) < 0: pts = pts[::-1]
        inner.poly(pts, TANK_IN)
    outer = []
    o0, o1, p0, p1 = x0 - WALL, x1 + WALL, y0 - WALL, y1 + WALL
    walls = Part('tank_walls', sil=True, sil_w=4)
    # long walls (outer faces), with plate seams
    for yy, sgn in ((p0, -1), (p1, 1)):
        for k, xa in enumerate(np.arange(o0, o1, 2.0)):
            xb = min(o1, xa + 2.0)
            pts = [(xa, yy, 0), (xb, yy, 0), (xb, yy, TZ), (xa, yy, TZ)]
            if sgn > 0: pts = pts[::-1]
            walls.poly(pts, TANKC if k % 2 else rgb_mul(TANKC, .96), ink=1.2)
    for xx, sgn in ((o0, -1), (o1, 1)):
        pts = [(xx, p0, 0), (xx, p1, 0), (xx, p1, TZ), (xx, p0, TZ)]
        if sgn < 0: pts = pts[::-1]
        walls.poly(pts, rgb_mul(TANKC, .94), ink=1.5)
    # rim (top of the walls)
    for (ax, ay, bx, by) in ((o0, p0, o1, y0), (o0, y1, o1, p1), (o0, y0, x0, y1), (x1, y0, o1, y1)):
        walls.poly([(ax, ay, TZ), (bx, ay, TZ), (bx, by, TZ), (ax, by, TZ)], (120, 140, 134), ink=1.5)
    # stiffeners (vertical ribs) and two horizontal girders on the long walls
    ribs = Part('tank_ribs', sil=False)
    for yy, sgn in ((p0, -1), (p1, 1)):
        for xa in np.arange(o0 + 1.0, o1, 2.0):
            P3.box((xa - .12, yy + (-.32 if sgn < 0 else 0), 0), (xa + .12, yy + (0 if sgn < 0 else .32), TZ), STEEL_D,
                   ink=1.2, part=ribs, skip=('bottom',))
        for z in (1.7, 3.6):
            a, b = (yy - .36, yy) if sgn < 0 else (yy, yy + .36)
            P3.box((o0, a, z - .16), (o1, b, z + .16), (104, 128, 122), ink=1.2, part=ribs, skip=('bottom',))
        # rivet rows along the plate seams (dots)
        for xa in np.arange(o0, o1, 2.0):
            for z in np.arange(.35, TZ, .55):
                ribs.dot((xa + .5, yy + (-.34 if sgn < 0 else .34), z), .035, (104, 128, 122))
    # portholes on the long walls (round inspection windows)
    ports = []
    for yy, sgn in ((p0, -1), (p1, 1)):
        for x in PORT_X:
            ports.append((x, yy + (-.37 if sgn < 0 else .37), PORT_Z, sgn))
    return inner, walls, ribs, ports


def porthole(part, x, y, z, sgn, r=.62, glass=(70, 160, 160), emit=.0):
    """A bolted round inspection window on a tank wall (part gets the flange ring, the glass disc and bolts)."""
    n = 20
    def ring(rr, off):
        return [(x + rr * math.cos(2 * math.pi * k / n), y + sgn * off, z + rr * math.sin(2 * math.pi * k / n)) for k in range(n)]
    for rr, off, col in ((r * 1.42, .02, (98, 124, 118)), (r * 1.18, .05, (124, 148, 140)), (r, .07, glass)):
        pts = ring(rr, off)
        if sgn > 0: pts = pts[::-1]
        part.decal(pts, col, ink=1.6, normal=(0, sgn, 0), emit=emit if col == glass else 0.0)
    for k in range(10):
        a = 2 * math.pi * k / 10
        part.dot((x + r * 1.3 * math.cos(a), y + sgn * .1, z + r * 1.3 * math.sin(a)), .045, (60, 74, 72))


def gantry(side=-1):
    """A walkway at rim height along a long wall: grating deck, posts, two rails, columns to the floor."""
    yi = side * (TY + WALL + .36); yo = side * (TY + WALL + 1.7)
    deck = Part('deck%d' % side, sil=True, sil_w=3)
    a, b = (yo, yi) if side < 0 else (yi, yo)
    P3.box((TX0 - 3.2, a, TZ - .22), (TX1 + 1.0, b, TZ), (82, 92, 90), ink=1.2, part=deck,
           cols={'top': (96, 106, 104)})
    for x in np.arange(TX0 - 3.0, TX1 + 1, .45):
        deck.line((x, a + .05, TZ + .01), (x, b - .05, TZ + .01), .03, (60, 68, 68), ink=False)
    cols = Part('cols%d' % side, sil=False)
    for x in np.arange(TX0 - 2.6, TX1 + 1, 4.0):
        cols.line((x, yo + side * -.1, 0), (x, yo + side * -.1, TZ - .2), .2, STEEL_D, ink=1.2)
    rail = Part('rail%d' % side, sil=False)
    for x in np.arange(TX0 - 3.1, TX1 + 1.1, 1.6):
        rail.line((x, yo, TZ), (x, yo, TZ + 1.08), .07, YEL, ink=1.2)
    for z in (TZ + .55, TZ + 1.08):
        rail.line((TX0 - 3.1, yo, z), (TX1 + 1.0, yo, z), .07, YEL, ink=1.2)
    return deck, cols, rail


def jacks(flex=0.0):
    """Hydraulic jacks under both wings (2 per side); flex (-1..1) moves the rams (the wing load cycles)."""
    out = []
    for side in (1, -1):
        for y in (8.8, 13.4):
            p = Part('jack%d_%d' % (side, int(y)), sil=True, sil_w=3)
            yy = side * y
            # wing underside height at y (approx.)
            zw = ZC - .86 + (y - 1.18) * math.tan(math.radians(2.2)) - .3 + .05 * flex * (y / 13.4)
            le = 9.75 + (y - 3.9) * math.tan(math.radians(24)); xm = le + 2.2
            P3.box((xm - .9, yy - .9, 0), (xm + .9, yy + .9, .45), (90, 96, 100), ink=1.2, part=p)
            P3.box((xm - .28, yy - .28, .45), (xm + .28, yy + .28, zw - .9), (180, 66, 50), ink=1.2, part=p)
            P3.box((xm - .1, yy - .1, zw - .9), (xm + .1, yy + .1, zw - .18), (214, 218, 222), ink=1.2, part=p)
            P3.box((xm - .5, yy - .35, zw - .2), (xm + .5, yy + .35, zw), (72, 78, 84), ink=1.2, part=p)
            out.append(p)
    return out


def seals():
    """Rubber seals where the wings pass through the long walls."""
    p = Part('seals', sil=False)
    for side in (1, -1):
        y = side * (TY + WALL + .03)
        le = 8.55 + (9.75 - 8.55) * min(1, (TY - 2.3) / 1.6); c = 9.05 + (7.35 - 9.05) * min(1, (TY - 2.3) / 1.6)
        zw = ZC - .86 + (TY - 1.18) * math.tan(math.radians(2.2))
        pts = [(le - .35, y, zw - .55), (le + c + .35, y, zw - .55), (le + c + .35, y, zw + .75), (le - .35, y, zw + .75)]
        if side > 0: pts = pts[::-1]
        p.decal(pts, RUBBER, ink=2, normal=(0, side, 0))
    return p


def pipes():
    p = Part('pipes', sil=True, sil_w=3)
    y = -(TY + WALL + .55)
    p.line((TX0 - 9.0, y, .55), (TX1 - 2.0, y, .55), .5, (150, 64, 52), ink=1.6)
    for x in np.arange(TX0 - 8, TX1 - 2, 4.0):
        p.line((x, y, .55), (x + .12, y, .55), .7, (120, 50, 42), ink=1.4)
    p.line((TX0 - .5, y, .55), (TX0 - .5, y, TZ + .8), .3, (150, 64, 52), ink=1.4)
    p.line((TX0 - .5, y, TZ + .8), (TX0 + 1.6, -1.0, TZ + .8), .3, (150, 64, 52), ink=1.4)
    p.line((TX0 + 1.6, -1.0, TZ + .8), (TX0 + 1.6, -1.0, WZ - .2), .3, (150, 64, 52), ink=1.4)
    return p


DESK = (-8.4, -8.9)
PORT_X = (1.6, 6.8, 21.2, 26.0)
PORT_Z = 3.1
LAMP_Y = (20.0, 38.0, -40.0)


def desk():
    """The control desk at the nose end: a cabinet with a sloped panel (gauges are drawn in 2D on top)."""
    x, y = DESK
    p = Part('desk', sil=True, sil_w=3)
    P3.box((x - 1.4, y - .45, 0), (x + 1.4, y + .45, 1.0), (96, 112, 104), ink=1.4, part=p)
    p.poly([(x - 1.4, y - .45, 1.0), (x + 1.4, y - .45, 1.0), (x + 1.4, y + .45, 1.45), (x - 1.4, y + .45, 1.45)],
           (78, 92, 86), ink=1.4)
    pump = Part('pump', sil=True, sil_w=3)
    P3.box((-12.6, -3.4, 0), (-9.6, -.8, 1.3), (150, 64, 52), ink=1.4, part=pump)
    P3.box((-12.2, -3.0, 1.3), (-10.0, -1.2, 2.2), (120, 120, 128), ink=1.4, part=pump)
    return p, pump


DESK_PANEL = [(-1.4, -.45, 1.0), (1.4, -.45, 1.0), (1.4, .45, 1.45), (-1.4, .45, 1.45)]


def build():
    if _S: return _S
    _S['shell'] = _hangar_shell()
    inner, walls, ribs, ports = _tank()
    _S['tank_inner'], _S['tank_walls'], _S['tank_ribs'], _S['ports'] = inner, walls, ribs, ports
    for side in (-1, 1):
        _S['gantry%d' % side] = gantry(side)
    _S['seals'] = seals(); _S['pipes'] = pipes()
    _S['desk'], _S['pump'] = desk()
    _S['props'] = props()
    pp = Part('portholes', sil=False)
    for x, y, z, sgn in ports: porthole(pp, x, y, z, sgn)
    _S['portholes'] = pp
    # the Comet in the tank: under water (inside the tank, below WZ) and above (the fin; the wings outside the walls)
    c = A.place(A.comet(hatch_x=A.COMET_WINDOWS_X[8]), t=(0, 0, ZC))
    under, above = [], []
    for k, prt in c.items():
        a, b = A.clip_part(prt, (0, 0, 1), WZ)                     # a: above the water, b: below
        for piece, is_above in ((a, True), (b, False)):
            if not piece.polys and not piece.decals: continue
            if k.startswith('wing'):
                side = 1 if k.endswith('R') else -1
                o, i = A.clip_part(piece, (0, side, 0), TY + WALL)        # o: outside the wall
                if i.polys or i.decals: under.append(i) if not is_above else above.append(i)
                if o.polys or o.decals: above.append(o)
            else:
                (above if is_above else under).append(piece)
    for p in under: p.name = 'u_' + p.name
    _S['comet_under'], _S['comet_above'] = under, above
    return _S


# ---------------------------------------------------------------- the frame-0 camera (the hook and the loop frame)
CAM0 = dict(pos=(-15.5, -27.0, 21.5), target=(14.0, 1.5, 1.6), fov=50.0, roll=0.0)


def cam0():
    return P3.Cam(CAM0['pos'], CAM0['target'], CAM0['fov'], CAM0['roll'])


# ---------------------------------------------------------------- characters in 3D
def stand(img, cam, P, t, expr='neutral', pose='stand', h=1.78, look=0.0, bphase=0.0, rim=(214, 236, 230),
          rim_dir=(1, -.5), lean=0.0, **kw):
    """Draw a stickman with its soles at world point P (height h m). Returns the actor geometry (or None)."""
    C = cam.to_cam([P])[0]
    if C[2] < .5: return None
    x, y = cam.proj_cam(C[None])[0]
    ppm = cam.fpx / C[2]
    s = h * ppm / 930.0
    if s < .02: return None
    return anim.actor(img, expr, pose, x, y, s, t, look=look, lean=lean, rim=rim, rim_dir=rim_dir, rim_w=10, bphase=bphase, **kw)


ENG_A = dict(coat='#ecebe4', pants='#3a3f4e')                       # engineer in a white coat
ENG_B = dict(uniform='#4c5c72')                                     # engineer in a boiler suit
ENG_C = dict(coat='#e6e2d6', pants='#4a4038', hair=('tuft', '#3a2e28'))


# ---------------------------------------------------------------- water
def water_poly(cam):
    pts = [(TX0, -TY, WZ), (TX1, -TY, WZ), (TX1, TY, WZ), (TX0, TY, WZ)]
    S, z = cam.project(pts)
    if (z < cam.near).any(): return None
    return [tuple(p) for p in S]


def water(img, under_lay, cam, t, swell=0.0, surge=0.0, ripples=True, refl=True):
    """Composite the under-water layer through the water: refraction wobble, caustics, the surface tint, planar
    reflections of the skylights and clerestories, ripples round the fin, a swell bulge."""
    wp = water_poly(cam)
    if wp is None: return
    m = Image.new('L', img.size, 0); ImageDraw.Draw(m).polygon(wp, fill=255)
    bb = m.getbbox()
    if not bb: return
    # refraction wobble of what is under the surface
    ul = under_lay.copy()
    cine.wobble(ul, bb, t, amp=2.2 + 3 * surge, wl=46, speed=2.4)
    # caustics on the submerged shapes
    ua = ImageChops.multiply(ul.split()[3], m)
    cine.caustics(ul, t * .8, mask=ua, box=bb, col=(200, 255, 236), alpha=.34, scale=1 / 60, res=3, sharp=7.0)
    img.paste(ul, (0, 0), m)
    # surface tint (thin teal veil, stronger toward the far side: Fresnel)
    x0, y0, x1, y1 = bb
    veil = Image.new('L', img.size, 0)
    g = np.zeros((y1 - y0, x1 - x0), np.float32) + np.linspace(.34, .08, y1 - y0, dtype=np.float32)[:, None]
    veil.paste(Image.fromarray((g * 255).astype(np.uint8)), (x0, y0))
    veil = ImageChops.multiply(veil, m)
    img.paste(Image.new('RGBA', img.size, (30, 96, 112, 255)), (0, 0), veil)
    # planar reflections: skylight strips mirrored in the water plane
    if refl:
        lay = kit.layer(img.width, img.height); d = ImageDraw.Draw(lay)
        for x in np.arange(HX0, HX1, 9.0):
            for s in (1, -1):
                def rp(yy): return RIDGE - (RIDGE - HZ) * abs(yy) / HY
                pts = [(x + .3, s * 10, rp(10)), (x + 8.7, s * 10, rp(10)), (x + 8.7, s * 26, rp(26)), (x + .3, s * 26, rp(26))]
                pts = [(a, b, 2 * WZ - c) for a, b, c in pts]
                S, z = cam.project(pts)
                if (z < cam.near).any(): continue
                d.polygon([tuple(p) for p in S], fill=(236, 252, 244, 170))
        for x in np.arange(HX0, HX1, 9.0):                       # clerestory band of the far side wall
            pts = [(x + .8, HY, 2 * WZ - 15.0), (x + 8.2, HY, 2 * WZ - 15.0), (x + 8.2, HY, 2 * WZ - 21.4), (x + .8, HY, 2 * WZ - 21.4)]
            S, z = cam.project(pts)
            if (z < cam.near).any(): continue
            d.polygon([tuple(p) for p in S], fill=(224, 246, 236, 120))
        lay = kit.soft_layer(lay, 5)
        cine.wobble(lay, bb, t * 1.3, amp=6, wl=30, speed=3.0)
        lay.putalpha(ImageChops.multiply(lay.split()[3], m))
        img.alpha_composite(lay)
    # ripples round the fin (circles on the water plane, expanding)
    if ripples:
        lay = kit.layer(img.width, img.height); d = ImageDraw.Draw(lay)
        cx, cy = 25.6, 0.0
        for k in range(4):
            u = (t * .45 + k / 4) % 1.0; r = .6 + 4.2 * u + 3 * surge
            pts = [(cx + r * math.cos(a) * 1.25, cy + r * math.sin(a), WZ + .01) for a in np.linspace(0, 2 * math.pi, 40)]
            S, z = cam.project(pts)
            if (z < cam.near).any(): continue
            d.line([tuple(p) for p in S] + [tuple(S[0])], fill=(240, 255, 250, int(150 * (1 - u))), width=3)
        if swell > .01 or surge > .01:
            for k in range(3):
                r = 3 + 8 * k + 10 * surge
                pts = [(13 + r * 1.6 * math.cos(a), r * .5 * math.sin(a), WZ + .01) for a in np.linspace(0, 2 * math.pi, 48)]
                S, z = cam.project(pts)
                if (z < cam.near).any(): continue
                d.line([tuple(p) for p in S] + [tuple(S[0])], fill=(240, 255, 250, int(110 * max(swell, surge))), width=4)
        lay = kit.soft_layer(lay, 1.2); lay.putalpha(ImageChops.multiply(lay.split()[3], m))
        img.alpha_composite(lay)


def sky_quads():
    """The sunlit skylight openings (sun-side slope, every other bay) as world quads."""
    out = []
    for k, x in enumerate(np.arange(HX0, HX1, 9.0)):
        if k % 2: continue
        def rp(yy): return RIDGE - (RIDGE - HZ) * abs(yy) / HY
        for yc in (13.0, 17.5, 22.0):
            out.append([(x + 1.0, yc - .45, rp(yc - .45)), (x + 8.0, yc - .45, rp(yc - .45)), (x + 8.0, yc + .45, rp(yc + .45)),
                        (x + 1.0, yc + .45, rp(yc + .45))])
    return out


def floor_pools(img, cam, k=1.0):
    """Warm light pools where the shafts land on the floor (drawn before the tank so it occludes them)."""
    L = np.asarray(LIGHT_DIR, float); lay = kit.mask(*cam.size); d = ImageDraw.Draw(lay)
    for q in sky_quads():
        q = np.asarray(q, float); ln = q[:, 2] / -L[2]; f = q + L[None] * ln[:, None]
        S, z = cam.project(f)
        if (z < cam.near).any(): continue
        d.polygon([tuple(p) for p in S], fill=255)
    kit.glow(img, lay, (255, 222, 160), .5 * k, blur=10, add=True)


def props(seed=4):
    """Floor clutter: crates, gas bottles, a tool trolley, coiled hoses, oil stains."""
    rng = np.random.default_rng(seed); p = Part('props', sil=True, sil_w=3)
    for (x, y, sx, sy, sz, col) in ((-6.0, 7.5, 1.6, 1.2, 1.1, (150, 116, 70)), (-4.4, 7.9, 1.1, 1.0, .8, (160, 126, 76)),
                                     (34.0, -8.5, 1.4, 1.4, 1.2, (150, 116, 70)), (35.5, -8.0, 1.0, 1.0, .9, (140, 108, 66)),
                                     (33.5, 7.8, 2.0, 1.2, 1.0, (96, 110, 104))):
        P3.box((x, y, 0), (x + sx, y + sy, sz), col, ink=1.4, part=p)
    for k in range(5):                                               # gas bottles
        x, y = -13.0 + k * .55, 6.6
        p.line((x, y, 0), (x, y, 1.5), .42, (80, 110, 90) if k % 2 else (180, 70, 56), ink=1.2)
    P3.box((31.5, -6.6, .4), (33.1, -5.8, 1.0), (170, 64, 52), ink=1.4, part=p)          # tool trolley
    for (x, y) in ((31.6, -6.5), (33.0, -6.5), (31.6, -5.9), (33.0, -5.9)): p.line((x, y, 0), (x, y, .4), .06, (50, 50, 56), ink=False)
    for k in range(7):                                               # oil stains
        x, y = rng.uniform(-14, 40), rng.choice([-1, 1]) * rng.uniform(6, 12); r = rng.uniform(.5, 1.2)
        p.decal([(x + r * math.cos(a), y + r * .7 * math.sin(a), .012) for a in np.linspace(0, 6.28, 14)][::-1],
                (118, 116, 110), normal=(0, 0, 1))
    return p


def port_ellipses(cam, shrink=.98, sel=None):
    """Screen polygons of the porthole glass discs that face the camera."""
    out = []
    for x, y, z, sgn in build()['ports']:
        cen = np.array([x, y + sgn * .07, z])
        if not (sel is None or (x, sgn) in sel): continue
        if (cam.pos - cen) @ np.array([0, sgn, 0]) <= 0: continue
        pts = [(x + .62 * shrink * math.cos(a), y + sgn * .07, z + .62 * shrink * math.sin(a)) for a in np.linspace(0, 2 * math.pi, 36)]
        S, zz = cam.project(pts)
        if (zz < cam.near).any(): continue
        out.append([tuple(p) for p in S])
    return out


def port_views(img, ul, cam, t, glow=0.0):
    """Show the under-water layer through each porthole: deeper teal, caustics, a glass sheen."""
    polys = port_ellipses(cam)
    if not polys: return
    m = Image.new('L', img.size, 0); d = ImageDraw.Draw(m)
    for p in polys: d.polygon(p, fill=255)
    bb = m.getbbox()
    if not bb: return
    v = Image.new('RGBA', img.size, (26, 104, 116, 255))
    v.alpha_composite(ul)
    tint = Image.new('RGBA', img.size, (20, 96, 110, 90)); v.alpha_composite(tint)
    cine.caustics(v, t * .8, box=bb, col=(190, 255, 236), alpha=.3, scale=1 / 40, res=2, sharp=6.0)
    cine.wobble(v, bb, t, amp=2.0, wl=40, speed=2.0)
    if glow: kit.glow(v, m, (120, 230, 220), .3 * glow, blur=30, add=True)
    img.paste(v, (0, 0), m)
    sh = kit.layer(*img.size); d2 = ImageDraw.Draw(sh)
    for p in polys:
        xs = [q[0] for q in p]; ys = [q[1] for q in p]; cx, cy = (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2
        rx, ry = (max(xs) - min(xs)) / 2, (max(ys) - min(ys)) / 2
        d2.arc([cx - rx * .8, cy - ry * .8, cx + rx * .8, cy + ry * .8], 200, 250, fill=(255, 255, 255, 150), width=max(2, int(rx * .07)))
    img.alpha_composite(kit.soft_layer(sh, 2))


# ---------------------------------------------------------------- the whole scene
def scene(cam, t, focus=None, aperture=0.0, chars=None, flex=0.0, swell=0.0, surge=0.0, fg=None, shafts_k=1.0,
          bg_blur=2.0, motes_k=1.0, porthole_glow=0.0, extra_mid=None, extra_after=None):
    """Draw the hangar + tank + Comet for camera `cam` at time t. chars(img, cam, layer_name) draws characters
    ('deck-1' on the near gantry, 'deck1' on the far gantry, 'floor' on the floor). fg(img) draws the blurred
    foreground. Returns (img RGBA, info)."""
    S = build()
    img = Image.new('RGBA', cam.size, (150, 166, 160, 255))
    # ---- background: shell (walls, roof, trusses, lamps), slightly defocused
    bg = Image.new('RGBA', cam.size, (120, 136, 130, 255))
    P3.render(bg, cam, S['shell'], light=LIGHT, fog=fog_hangar, ink_w=2)
    floor_pools(bg, cam, shafts_k)
    P3.render(bg, cam, [S['props']], light=LIGHT, fog=fog_hangar, ink_w=2)
    if bg_blur: bg = cine.defocus(bg, bg_blur)
    img.alpha_composite(bg)
    # lamp glows (bokeh-ish)
    pts = []
    for x in np.arange(HX0 + 4.5, HX1, 18.0):
        for y in LAMP_Y:
            C = cam.to_cam([(x, y, 14.7)])[0]
            if C[2] > 1: pts.append(tuple(cam.proj_cam(C[None])[0]) + (min(2.0, 30 / C[2]),))
    if pts: cine.bokeh(img, pts, 22, (255, 230, 180), .5)
    # ---- under water: tank inner faces + the submerged Comet (fogged), composited through the water
    ul = kit.layer(*cam.size)
    P3.render(ul, cam, [S['tank_inner']] + S['comet_under'], light=LIGHT, fog=fog_water, ink_w=2, sil_w=4)
    # ---- far gantry (behind the tank from any angle), then the far engineers, then the tank (occludes them when low)
    deckN, colsN, railN = S['gantry-1']; deckF, colsF, railF = S['gantry1']
    far = kit.layer(*cam.size)
    P3.render(far, cam, [colsF, deckF, railF], light=LIGHT, fog=fog_hangar, ink_w=2, sil_w=4)
    img.alpha_composite(far)
    if chars: chars(img, cam, 'far')
    mid = kit.layer(*cam.size)
    jk = jacks(flex)
    P3.render(mid, cam, [S['tank_walls'], S['tank_ribs'], S['portholes'], S['seals'], S['pipes'],
                         S['pump'], S['desk']] + jk, light=LIGHT, fog=fog_hangar, ink_w=2, sil_w=4)
    img.alpha_composite(mid)
    if cam.pos[2] > TZ + .3: water(img, ul, cam, t, swell, surge)
    port_views(img, ul, cam, t, porthole_glow)
    mid2 = kit.layer(*cam.size)
    wings_out = [p for p in S['comet_above'] if p.name.startswith('wing')]
    rest = [p for p in S['comet_above'] if not p.name.startswith('wing')]
    P3.render(mid2, cam, wings_out + rest + [colsN, deckN], light=LIGHT, fog=fog_hangar, ink_w=2, sil_w=4)
    img.alpha_composite(mid2)
    if extra_mid: extra_mid(img, cam)
    if chars: chars(img, cam, 'near')
    rl = kit.layer(*cam.size)
    P3.render(rl, cam, [railN], light=LIGHT, fog=fog_hangar, ink_w=2)
    img.alpha_composite(rl)
    if chars: chars(img, cam, 'front')
    # ---- light: shafts from the skylights, motes in them
    if shafts_k > 0:
        sm = cine.shafts3d(img, cam, sky_quads(), LIGHT_DIR, 40, col=(255, 232, 186), alpha=.3 * shafts_k, blur=10, floor_z=0)
        if sm is not None and motes_k > 0:
            cine.motes(img, t, (0, 0, cam.size[0], cam.size[1]), n=int(110 * motes_k), mask=sm, alpha=200, size=(1.6, 4.2))
    if extra_after: extra_after(img, cam)
    if fg: fg(img)
    return img, {}
