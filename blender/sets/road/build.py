# Road set: a modern town street (KayKit City Builder Bits + Quaternius street pack, CC0).
# cams: roadside (on the pavement, road and cars receding to the right), in_car (inside a car, looking back at the driver seat).
# usage: .venv/bin/python blender/sets/road/build.py [--cams roadside,in_car] [--lights day,golden] [--pct 25]
import sys, os, math, bpy
from mathutils import Vector
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import common as C

C.reset()
KS = 4.8                                   # KayKit city tile 2 units -> 9.6 m; car 0.94 -> 4.5 m
T = 2 * KS
k = lambda n, *a, **kw: C.imp(f'{C.KAY_CITY}/{n}.gltf', *a, **kw)
qs = lambda n, *a, **kw: C.imp(f'{C.QUAT}/street_pack/{n}.glb', *a, **kw)

# ---------- layout: road along +Y at x = T, pavement/buildings at x = 0 and x = 2T ----------
ROAD_X = T
for j in range(-2, 9):
    y = j * T
    k('road_straight_crossing' if j == 3 else 'road_straight', (ROAD_X, y, 0), 90, KS)
BUILD_L = ['building_C', 'building_E', 'building_A', 'building_G', 'building_B', 'building_H', 'building_D', 'building_F', 'building_C', 'building_E']
for j, b in enumerate(BUILD_L):   # near side: pavement tiles (base) where the character stands, buildings further left
    y = (j - 2) * T
    k('base', (0, y, 0), 0, KS)
    k(b, (-T, y, 0), 90, KS)
for j, b in enumerate(reversed(BUILD_L)):   # far side of the road
    y = (j - 2) * T
    k(b, (2 * T, y, 0), -90, KS)
    k(BUILD_L[(j + 3) % len(BUILD_L)], (3 * T, y, 0), -90, KS * 1.15)
for j in range(10):   # a taller back row so the top of the frame has content
    k(BUILD_L[(j * 3) % len(BUILD_L)], (-2 * T, (j - 2) * T, 0), 90, KS * 1.35)
ground = C.plane(600, (0, 0, -0.02), C.mat('grass', (0.16, 0.30, 0.10), rough=0.95))

# street furniture on the near pavement (x ~ +3.2 = kerb side)
for y in (-6.0, 14.0, 34.0):
    k('streetlight', (3.6, y, 0.48), 180, KS)
qs('Sign_Stop', (3.9, 22.5, 0.48), 0, 4.8)
k('firehydrant', (3.4, 4.5, 0.48), 0, KS)
k('bench', (-2.8, 7.0, 0.48), 90, KS)
k('bush', (-3.6, 2.0, 0.48), 0, KS); k('bush', (-3.6, 11.5, 0.48), 30, KS)
k('trafficlight_B', (3.6, 26.0, 0.48), 180, KS)
k('dumpster', (-3.2, 18.0, 0.48), 90, KS)
# traffic
CARS = [('car_taxi', ROAD_X - 2.2, 8.0, 0), ('car_sedan', ROAD_X + 2.2, 18.0, 180), ('car_hatchback', ROAD_X - 2.2, 30.0, 0),
        ('car_police', ROAD_X + 2.2, 42.0, 180), ('car_stationwagon', ROAD_X - 2.2, 55.0, 0)]
for n, x, y, rz in CARS: k(n, (x, y, 0.1), rz, KS)

C.stylise(emissive_prefixes=('Windows', 'window', 'Light', 'light'), emit_strength=3.0)

# ---------- in_car: a simple stylised car interior parked on the near lane ----------
CX, CY, CZ = ROAD_X - 2.2, -10.0, 0.0      # car origin on the road
seat = C.mat('seat', (0.55, 0.12, 0.10), rough=0.9)
trim = C.mat('trim', (0.12, 0.12, 0.16), rough=0.8)
body = C.mat('carbody', (0.95, 0.70, 0.10), rough=0.5)
INT = []
def ib(size, loc, m, rx=0):
    o = C.box(size, (CX + loc[0], CY + loc[1], CZ + loc[2]), m); o.rotation_euler.x = math.radians(rx); INT.append(o); return o
SEAT_Z = 0.55
ib((0.55, 0.55, 0.18), (-0.4, 0.15, SEAT_Z - 0.09), seat)                 # driver cushion
ib((0.55, 0.14, 0.75), (-0.4, 0.48, SEAT_Z + 0.36), seat, rx=-12)        # driver seat back
ib((0.30, 0.12, 0.20), (-0.4, 0.58, SEAT_Z + 0.90), seat, rx=-12)        # headrest
ib((0.55, 0.55, 0.18), (0.45, 0.15, SEAT_Z - 0.09), seat)
ib((0.55, 0.14, 0.75), (0.45, 0.48, SEAT_Z + 0.36), seat, rx=-12)
ib((0.30, 0.12, 0.20), (0.45, 0.58, SEAT_Z + 0.90), seat, rx=-12)
ib((1.5, 0.6, 0.6), (0.0, 1.35, SEAT_Z + 0.15), seat)                     # back bench
ib((1.8, 3.2, 0.08), (0.0, 0.6, 1.42), trim)                               # roof liner
ib((1.8, 3.2, 0.3), (0.0, 0.6, 0.15), trim)                                # floor
for sx in (-0.92, 0.92):
    ib((0.08, 3.2, 0.55), (sx, 0.6, 0.62), body)                           # doors (below the windows)
    ib((0.08, 0.12, 0.55), (sx, 0.95, 1.15), trim)                         # B-pillar
    ib((0.08, 0.2, 0.6), (sx, 2.1, 1.12), trim, rx=25)                     # C-pillar
ib((1.8, 0.08, 0.35), (0.0, 2.2, 0.55), body)                              # rear below the window
ib((1.8, 0.1, 0.08), (0.0, 2.25, 1.38), trim)                              # rear window top rail
ib((0.25, 0.25, 0.04), (0.0, 2.05, 0.92), trim)                            # parcel shelf box
bpy.ops.mesh.primitive_torus_add(major_radius=0.19, minor_radius=0.025, location=(CX - 0.4, CY - 0.55, CZ + SEAT_Z + 0.32),
                                 rotation=(math.radians(70), 0, 0))
C.assign(bpy.context.object, trim); INT.append(bpy.context.object)
ib((1.8, 0.25, 0.25), (0.0, -0.85, SEAT_Z + 0.1), trim)                   # dashboard edge
def hide_interior(h):
    for o in INT: o.hide_render = h

# ---------- practicals (golden): car tail lights + shop windows ----------
for n, x, y, rz in CARS:
    C.point((x, y + (-2.4 if rz == 0 else 2.4), 0.9), (1.0, 0.25, 0.1), 60, 0.2)
C.point((-4.0, 10.0, 3.0), power=400, radius=1.5)
C.point((-4.0, 30.0, 3.0), power=400, radius=1.5)
for y in (-6.0, 14.0, 34.0): C.point((4.4, y, 4.2), power=500, radius=0.2)

def stand_z(x, y):
    bpy.context.view_layer.update(); dg = bpy.context.evaluated_depsgraph_get()
    hit, loc, *_ = bpy.context.scene.ray_cast(dg, Vector((x, y, 30)), Vector((0, 0, -1)))
    return loc.z if hit else 0
PZ = stand_z(1.5, 0.0)
print('PAVEMENT_Z', PZ)

CAMS = {
    'roadside': dict(loc=(-0.3, -7.2, PZ + 1.25), target=(3.5, 20.0, PZ + 3.6), lens=24, roll=2, stand=(1.4, -0.6, PZ),
                     fstop=2.4, haze_range=(4, 160), setup=lambda: hide_interior(True)),
    # driver seat seen from the dashboard; `stand` is a virtual floor 0.9 m under the cushion so a standing
    # character's hips sit on the seat (legs go below the frame).
    'in_car': dict(loc=(CX - 0.35, CY - 1.0, CZ + SEAT_Z + 0.75), target=(CX - 0.4, CY + 3.0, CZ + SEAT_Z + 0.55), lens=17,
                   stand=(CX - 0.4, CY + 0.2, CZ + SEAT_Z - 0.9), fstop=2.8, ink_fade=(3, 12, 0.7), haze_range=(3, 140),
                   setup=lambda: hide_interior(False)),
}
LIGHTS = {'day': dict(az=10, elev=50), 'golden': dict(az=-25, elev=12)}
C.main('road', CAMS, LIGHTS)
