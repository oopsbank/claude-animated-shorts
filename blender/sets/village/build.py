# Village square set (Quaternius medieval village + KayKit props, CC0), rebuilt from blender/scripts/scene2.py.
# usage: .venv/bin/python blender/sets/village/build.py [--cams wide,well_close,street_low] [--lights day,golden,night] [--pct 25]
import sys, os, math
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import common as C

C.reset()
Q = f'{C.QUAT}/medieval_village_pack'
K = f'{C.KAY_MED}/decoration/props'
q = lambda n, *a, **k: C.imp(f'{Q}/{n}.glb', *a, **k)
kk = lambda n, *a, **k: C.imp(f'{K}/{n}.gltf', *a, **k)

# ---------- layout (metres) ----------
HZ = 2.2   # house scale -> ~8 m tall houses
for name, x, y, rz in (('House_1', -6.4, 13.0, 10), ('Inn', -0.6, 15.5, 0), ('House_2', 5.6, 13.5, -10),
                       ('House_1', 10.5, 10.5, -30), ('House_2', -11.5, 10.0, 30), ('House_3', 2.6, 21.0, 0)):
    q(name, (x, y, 0), rz, HZ)
q('Bell_Tower', (-4.0, 22.0, 0), 0, 3.0)
for i, (name, x, y, rz) in enumerate((('House_2', -9.0, 21.0, 5), ('House_1', 7.5, 22.0, -5), ('Inn', 12.5, 19.0, -20),
        ('House_1', -14.5, 17.0, 20), ('House_2', 0.5, 29.0, 0), ('House_1', -6.0, 31.0, 0), ('Inn', 7.0, 32.0, 0),
        ('House_2', -12.0, 30.0, 10), ('House_1', 13.0, 29.0, -10))):
    q(name, (x, y, (2.0 if y < 25 else 5.5) + 0.25 * i), rz, HZ * 1.05)   # rows climb a hill behind the square
# side street (seen by street_low): houses lining the right of the square
for name, x, y, rz in (('House_2', 9.5, 2.5, -90), ('House_1', 10.0, -5.0, -90), ('House_3', -9.5, 2.0, 90)):
    q(name, (x, y, 0), rz, HZ)
# the lane south of the square (street_med: a street a bicycle can ride down)
for i, y in enumerate((-12.0, -20.0, -28.0, -36.0)):
    q(('House_1', 'House_2', 'House_3', 'House_2')[i], (-5.9, y, 0), 90 + (i % 2) * 6, HZ)
    q(('House_2', 'House_3', 'House_1', 'House_1')[i], (5.9, y, 0), -90 - (i % 2) * 6, HZ)
q('Barrel', (-3.6, -27.0, 0), 10, 4.6); q('Barrel', (-3.9, -26.2, 0), 40, 4.6)
q('Well', (-2.3, 5.0, 0.45), 15, 1.9)
q('MarketStand_1', (2.9, 6.0, 0), -20, 2.3)
q('Cart', (0.9, 9.0, 0), 60, 1.9)
for x, y, rz in ((1.35, 0.9, 0), (1.95, 1.35, 30), (1.65, 1.95, 60)):
    q('Barrel', (x, y, 0), rz, 4.6)
kk('crate_A_big', (-1.05, -2.6, 0), 10, 3.4)
kk('crate_A_big', (-1.00, -2.55, 0.71), 35, 3.0)
kk('crate_A_small', (-0.35, -3.0, 0), 20, 3.4)
kk('barrel', (1.5, -2.2, 0), 0, 4.0)
kk('crate_A_big', (4.6, -4.3, 0), -15, 3.4)          # street_low foreground layer
kk('crate_A_small', (4.4, -3.5, 0), 30, 3.4)

C.stylise(emissive_prefixes=('Windows',))
# a sample story sign on the market stand (scripts request their own via C.sign)
C.sign('FRESH\nBREAD', 'plank', loc=(2.75, 5.35, 2.55), rz=-20, w=1.5, h=0.62)
C.sign('TOWN\nNOTICES', 'poster', loc=(-5.0, 9.6, 1.9), rz=10, w=1.1, h=1.3)

# ---------- ground + hill ----------
C.plane(140, m=C.cobble_mat(c0=(0.20, 0.15, 0.13), c1=(0.34, 0.24, 0.18)))
import bpy
bpy.ops.mesh.primitive_uv_sphere_add(radius=40, location=(0, 62, -32)); hill = bpy.context.object
hill.scale = (1.6, 1.0, 1.0); C.assign(hill, C.mat('hill', (0.10, 0.20, 0.12), rough=0.95)); C.no_ink(hill)
HILL = bpy.data.materials['hill'].node_tree.nodes['Principled BSDF']

# ---------- practicals ----------
C.lamp_post(-1.55, 1.6)
C.point((-0.6, 12.0, 2.2), power=500, radius=1.0)    # inn doorway spill
C.point((5.6, 10.5, 2.0), power=250, radius=1.0)

def per_light(ln):   # hill reads green by day, deep blue at night
    HILL.inputs['Base Color'].default_value = {'day': (0.16, 0.36, 0.14, 1), 'golden': (0.20, 0.22, 0.10, 1),
                                               'night': (0.05, 0.07, 0.14, 1)}[ln]

CAMS = {
    'wide': dict(loc=(0.7, -5.4, 1.35), target=(0.0, 6.0, 2.0), lens=27, roll=3, stand=(0.35, -0.2, 0), fstop=2.0,
                 per_light=per_light),
    'well_close': dict(loc=(-0.15, 1.15, 1.45), target=(-1.75, 4.9, 1.25), lens=38, roll=-4, stand=(-1.15, 4.1, 0),
                       fstop=2.4, ink_fade=(4.5, 9.0, 0.85), haze_range=(3, 60), per_light=per_light),
    'square_med': dict(loc=(0.75, -3.4, 1.3), target=(0.1, 6.0, 1.75), lens=30, roll=2, stand=(0.35, -0.2, 0), fstop=2.4,
                       ink_fade=(6, 25, 0.5), per_light=per_light),
    'street_med': dict(loc=(0.45, -32.5, 1.3), target=(-0.1, 0.0, 2.4), lens=30, roll=0, stand=(0.1, -29.6, 0), fstop=2.4,
                       ink_fade=(6, 30, 0.5), per_light=per_light),
    'street_low': dict(loc=(3.2, -5.8, 0.45), target=(0.8, 8.0, 2.8), lens=21, roll=-3, stand=(2.5, -2.9, 0), fstop=2.8,
                       per_light=per_light),
}
LIGHTS = {'day': dict(az=25, elev=48), 'golden': dict(az=-20, elev=14), 'night': dict(az=210)}
C.main('village', CAMS, LIGHTS)
