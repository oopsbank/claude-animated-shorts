# Harbour set: wooden pier, moored sailing ship (Quaternius ships pack), boats, water, a town on the far shore.
# usage: .venv/bin/python blender/sets/harbour/build.py [--cams pier_wide,deck] [--lights day,storm,night] [--pct 25]
import sys, os, math, bpy
from mathutils import Vector
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import common as C

C.reset()
S = f'{C.QUAT}/ships_pack'; V = f'{C.QUAT}/medieval_village_pack'; K = f'{C.KAY_MED}/decoration/props'
ship = lambda n, *a, **k: C.imp(f'{S}/{n}.glb', *a, **k)
q = lambda n, *a, **k: C.imp(f'{V}/{n}.glb', *a, **k)
kk = lambda n, *a, **k: C.imp(f'{K}/{n}.gltf', *a, **k)

# ---------- water + far shore ----------
WM = C.water_mat(); water = C.plane(400, (0, 120, 0), WM)
PIER_Z = 1.2                          # pier deck height above the water (m)
SHIP_Z = -1.0                         # ship sunk so the waterline sits on the hull
SHIP_X, SHIP_Y = 6.2, 14.0
hero = ship('Sail_ship', (SHIP_X, SHIP_Y, SHIP_Z), 180, 4.0)      # bow pointing away from the pier camera
ship('Viking_boat', (-9.0, 30.0, -0.35), 70, 3.2)
ship('Boat', (-3.0, 7.5, -0.05), 20, 6.0)
ship('Lifeboat', (2.2, 3.0, -0.1), -15, 4.0)
ship('BoatWSail', (-14.0, 48.0, -0.1), 40, 9.0)
ship('Sail_ship', (22.0, 70.0, -1.0), 120, 4.0)

# far shore: a land strip with a town climbing a hill, across the bay
land = C.mat('shore', (0.16, 0.32, 0.12), rough=0.95)
C.box((160, 30, 3), (0, 98, 0.4), land, ink=False)
bpy.ops.mesh.primitive_uv_sphere_add(radius=40, location=(-10, 135, -18)); hill = bpy.context.object
hill.scale = (2.0, 1.0, 1.0); C.assign(hill, land); C.no_ink(hill)
HZ = 2.4
for i, (name, x, y) in enumerate((('House_1', -30, 88), ('House_2', -20, 90), ('Inn', -9, 89), ('House_3', 2, 91),
                                  ('House_1', 13, 88), ('House_2', 24, 92), ('House_1', -25, 102), ('House_2', -6, 104),
                                  ('Inn', 10, 103), ('House_3', -16, 112), ('House_1', 4, 114))):
    q(name, (x, y, 1.9 + (y - 88) * 0.45), (i * 37) % 40 - 20, HZ)
q('Bell_Tower', (-38, 95, 1.9), 0, 4.5)                                     # lighthouse-ish tower on the point

# ---------- pier: plank deck on posts, running from the camera out into the bay ----------
wood = C.plank_mat(c0=(0.20, 0.11, 0.05), c1=(0.30, 0.17, 0.08), axis='Y', width=0.28)
post = C.mat('post', (0.22, 0.13, 0.07), rough=0.9)
deck = C.box((4.0, 30.0, 0.25), (0, 8.0, PIER_Z - 0.125), wood)
for y in range(-6, 24, 3):
    for x in (-1.9, 1.9):
        C.cyl(0.16, PIER_Z + 1.8, (x, y, (PIER_Z - 1.8) / 2 + 0.55), post, verts=8)   # posts stick up as bollards
rope = C.mat('rope', (0.55, 0.42, 0.25))
for y in (6.0, 12.0, 18.0):
    C.cyl(0.05, 2.2, (2.0 + 1.1, y, PIER_Z + 0.6), rope, rot=(0, 90, 15), verts=6)  # mooring lines toward the ship
# cargo on the pier
for x, y, rz, s in ((-1.3, 2.0, 10, 3.4), (-1.25, 2.05, 35, 3.0), (-1.2, 9.0, -15, 3.4)):
    kk('crate_A_big', (x, y, PIER_Z if s > 3.2 else PIER_Z + 0.71), rz, s)
for x, y in ((1.2, 4.2), (1.4, 4.9), (-1.4, 12.5)):
    q('Barrel', (x, y, PIER_Z), 20, 4.6)
kk('barrel', (-1.3, -2.5, PIER_Z), 0, 4.0)
kk('crate_A_small', (1.2, -3.2, PIER_Z), 25, 3.4)

C.stylise(emissive_prefixes=('Windows',))
# ship hull a touch warmer; sails cream
for m in bpy.data.materials:
    if 'Sail' in m.name or 'White' in m.name:
        P = m.node_tree.nodes.get('Principled BSDF')
        if P and not P.inputs['Base Color'].is_linked: P.inputs['Base Color'].default_value = (0.92, 0.86, 0.72, 1)

# ---------- practicals: pier lanterns + ship stern lantern + town windows ----------
DZ0 = 1.98
C.lamp_post(-1.75, 5.0, h=3.0)
C.lamp_post(-1.75, 17.0, h=3.0)
C.point((SHIP_X - 2.6, SHIP_Y + 6.5, DZ0 + 2.2), power=250, radius=0.2)   # lantern on the ship rail
C.point((0, 95, 6), power=4000, radius=3)        # town glow across the bay

def deck_z(x, y):
    bpy.context.view_layer.update(); dg = bpy.context.evaluated_depsgraph_get()
    hit, loc, *_ = bpy.context.scene.ray_cast(dg, Vector((x, y, 4.0)), Vector((0, 0, -1)))   # start under the sails
    return loc.z if hit else 0
DZ = deck_z(SHIP_X, SHIP_Y + 4.5)
print('DECK_Z', DZ)
C.sign('HARBOUR\nMASTER', 'plank', loc=(-1.95, 10.5, PIER_Z + 1.9), rz=-90, w=1.6, h=0.7)
WR = WM.node_tree.nodes['Color Ramp'] if 'Color Ramp' in WM.node_tree.nodes else [n for n in WM.node_tree.nodes if n.type == 'VALTORGB'][0]
def per_light(ln):   # storm: dark grey-green sea; otherwise cartoon blue
    sh, dp = {'storm': ((0.10, 0.22, 0.24), (0.02, 0.06, 0.09)), 'night': ((0.04, 0.16, 0.30), (0.01, 0.04, 0.12))}.get(
        ln, ((0.05, 0.42, 0.62), (0.02, 0.16, 0.38)))
    WR.color_ramp.elements[0].color = (*sh, 1); WR.color_ramp.elements[1].color = (*dp, 1)

CAMS = {
    'pier_wide': dict(loc=(0.3, -6.0, PIER_Z + 1.3), target=(1.2, 14.0, PIER_Z + 2.4), lens=24, roll=2,
                      stand=(0.2, 0.0, PIER_Z), fstop=2.4, haze_range=(4, 140), per_light=per_light),
    'pier_med': dict(loc=(0.6, -3.2, PIER_Z + 1.25), target=(0.5, 14.0, PIER_Z + 1.7), lens=30, roll=-2,
                     stand=(0.15, 0.0, PIER_Z), fstop=2.4, haze_range=(4, 140), ink_fade=(6, 30, 0.5), per_light=per_light),
    # on deck, looking across the port rail toward the pier and the town across the bay
    'deck': dict(loc=(SHIP_X + 2.4, SHIP_Y + 3.0, DZ + 1.45), target=(SHIP_X - 8.0, SHIP_Y + 16.0, DZ + 1.2), lens=24, roll=2,
                 stand=(SHIP_X - 0.6, SHIP_Y + 5.6, DZ), fstop=2.4, haze_range=(4, 140), per_light=per_light),
}
LIGHTS = {'day': dict(az=20, elev=45), 'storm': dict(az=40), 'night': dict(az=200)}
C.main('harbour', CAMS, LIGHTS)
