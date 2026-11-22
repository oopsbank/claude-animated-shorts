# Playa set (sailing-stones): a dry lake bed in the Racetrack style (not a copy of a photo): pale tan clay cracked into
# polygons, low dark brown/purple mountains all round, dark rocks with long shallow groove trails, the cousins' camp,
# and a gravel overlook at the road edge with the tour van and the sign. Props follow the stylised-PBR recipe (props.py).
# Layout (metres): camp around (0, 7); hero rock HERO at (6, -3), its trail running back along TRAIL_H degrees;
# overlook pad at (-30, -40) on the playa's south edge (the van never stands on the playa).
# usage: .venv/bin/python blender/sets/playa/build.py [--cams ...] [--lights day,golden,night,frost] [--pct 25] [--depth]
import sys, os, math, random, bpy
from mathutils import Vector
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE)); sys.path.insert(0, HERE)
import common as C, props as PR, ground as G

C.reset()
rnd = random.Random(11)
HERO = (6.0, -3.0); TRAIL_H = 108.0
OVER = (-30.0, -40.0)

# ---------- ground, mountains, scattered rocks with trails ----------
clay = G.clay_mat()
C.plane(1400, (0, 0, 0), clay)
G.mountains(radius=430, n=30, seed=7, h=(30, 75))
G.mountains(radius=520, n=22, seed=8, h=(50, 95), col=(0.14, 0.08, 0.13))
rock_m = C.pbr('rock_dark', (0.085, 0.07, 0.068), rough=0.25, coat=0.9, bevel=0.05, noise=0.5, noise_scale=4.0)
hero = C.rock((HERO[0], HERO[1], 0), (0.48, 0.38, 0.30), seed=3, facet=True, detail=1, m=rock_m, rz=20)
G.trail((HERO[0] + 0.35 * math.cos(math.radians(TRAIL_H)), HERO[1] + 0.35 * math.sin(math.radians(TRAIL_H))), TRAIL_H, 38.0, width=0.75, wobble=0.35, seed=1)
G.pebbles((HERO[0] - 0.6, HERO[1] - 0.4), n=8, spread=0.5, seed=4, size=0.045)
for k in range(26):   # far rocks and their trails (keep the camp and overlook clear)
    while True:
        x, y = rnd.uniform(-60, 70), rnd.uniform(-30, 90)
        if Vector((x, y - 7)).length > 12 and Vector((x - HERO[0], y - HERO[1])).length > 6: break
    s = rnd.uniform(0.18, 0.42); h = rnd.uniform(0, 360)
    C.rock((x, y, 0), (s, s * 0.8, s * 0.6), seed=100 + k, facet=True, detail=1, m=rock_m, rz=rnd.uniform(0, 360))
    G.trail((x + s * 0.8 * math.cos(math.radians(h)), y + s * 0.8 * math.sin(math.radians(h))), h, rnd.uniform(15, 45), width=s * 1.7, wobble=0.5, seed=200 + k)
    C.contact_blob((x, y, 0), s * 2.4, s * 2.0)

# ---------- the cousins' camp ----------
PR.dome_tent((-2.6, 8.4, 0), rz=-15)
PR.folding_chair((-0.7, 5.6, 0), rz=170, col='#2fb3c9'); PR.folding_chair((0.9, 5.7, 0), rz=195, col='#e85d8a')
PR.cooler((0.1, 6.3, 0), rz=8)
PR.tripod_cam((2.7, 5.2, 0), rz=200)
PR.weather_mast((4.2, 8.6, 0), rz=30)
PR.lantern((0.1, 6.3, 0.49))
C.point((-2.6, 8.4, 0.6), (1.0, 0.55, 0.22), power=45, radius=0.5)                 # glow inside the tent (night)
C.point((4.2, 8.6, 3.1), (1.0, 0.15, 0.1), power=4, radius=0.05)                    # red beacon on the mast
C.point((HERO[0] - 7.0, HERO[1] - 2.0, 0.4), (1.0, 0.6, 0.3), power=70, radius=0.6)  # warm spill from a lantern off-frame
for k in range(15):   # the row of 15 tagged rocks, each with a short trail behind
    x = -7.0 + k
    s = 0.2 + 0.05 * ((k * 7) % 4)
    C.rock((x, 10.5 + 0.25 * math.sin(k), 0), (s, s * 0.8, s * 0.6), seed=300 + k, facet=True, detail=1, m=rock_m, rz=k * 37)
    C.contact_blob((x, 10.5 + 0.25 * math.sin(k), 0), s * 3, s * 2.5)
    bpy.ops.mesh.primitive_cylinder_add(vertices=8, radius=0.012, depth=0.1, location=(x + 0.05, 10.5 + 0.25 * math.sin(k), s * 1.15))
    C.assign(bpy.context.object, C.pbr('gps_tip', PR.lin('#e8613c'), rough=0.3)); C.no_ink(bpy.context.object)   # GPS antenna stub
# flags marking the survey line
for x in (-8.0, 8.0):
    C.rcyl(0.015, 1.3, (x, 10.4, 0.65), C.pbr('flagpole', (0.8, 0.8, 0.8), rough=0.3), verts=6, r=0.0)
    C.rbox((0.32, 0.01, 0.2), (x + 0.17, 10.4, 1.18), C.pbr('flag', PR.lin('#ffc533'), rough=0.5, coat=0.2), r=0.01)

# ---------- overlook: gravel pull-out on the south edge ----------
pad = C.rbox((22, 12, 0.3), (OVER[0], OVER[1] - 4, 0.0), PR.gravel_mat(), r=0.12)
road = C.rbox((140, 7, 0.32), (OVER[0], OVER[1] - 13, 0.0), C.pbr('asphalt', (0.07, 0.065, 0.075), rough=0.8, coat=0.0, bevel=0.02), r=0.05)
for x in range(-60, 61, 6): C.rbox((3.0, 0.15, 0.01), (OVER[0] + x, OVER[1] - 13, 0.165), C.pbr('roadline', (0.85, 0.7, 0.2), rough=0.5, coat=0.0), r=0.0)
van = PR.tour_van((OVER[0] - 4.6, OVER[1] - 0.6, 0.15), rz=-24)
night_lamps = []
SIGN_TXT = {'day': 'ALIEN ROCK TOURS\nNIGHT ONLY · $20', 'night': 'ALIEN ROCK TOURS\nSOLD OUT'}   # golden and frost use the day board
SIGNS = {ln: PR.sign_posts(t, (OVER[0] + 3.4, OVER[1] - 1.6), rz=-8, w=2.6, h=1.15)[0] for ln, t in SIGN_TXT.items()}
SIGN_C = (OVER[0] + 3.4, OVER[1] - 1.6 - 0.1, 2.4 - 1.15 / 2 - 0.05)
PR.alien_cutout((OVER[0] + 0.6, OVER[1] + 1.2), rz=-5)
# ticket stand in the right foreground: folding table, cash box, ticket roll; cones along the pad edge
tbl = C.pbr('table_top', PR.lin('#f6d49a'), rough=0.4, coat=0.4)
C.rbox((1.4, 0.7, 0.05), (OVER[0] + 1.45, OVER[1] - 5.0, 0.92), tbl, r=0.02)
for sx in (-0.6, 0.6):
    for sy in (-0.28, 0.28): C.rcyl(0.02, 0.76, (OVER[0] + 1.45 + sx, OVER[1] - 5.0 + sy, 0.53), C.pbr('chair_al', (0.55, 0.55, 0.58), rough=0.3, metal=0.9, coat=0.0), verts=8, r=0.0)
C.rbox((0.36, 0.26, 0.14), (OVER[0] + 1.15, OVER[1] - 5.05, 1.02), C.pbr('cashbox', PR.lin('#2f6b4f'), rough=0.3, coat=0.7), r=0.02)
C.rbox((0.30, 0.02, 0.04), (OVER[0] + 1.15, OVER[1] - 5.19, 1.06), C.gold('cash_gold'), r=0.01)
C.rcyl(0.07, 0.12, (OVER[0] + 1.75, OVER[1] - 4.95, 1.0), C.pbr('tickets', PR.lin('#e8613c'), rough=0.5, coat=0.2), rot=(90, 0, 0), verts=18, r=0.01)
C.contact_blob((OVER[0] + 1.45, OVER[1] - 5.0, 0.15), 1.8, 1.1)
cone = C.pbr('cone', PR.lin('#ff7a1a'), rough=0.35, coat=0.6)
for cx, cy in ((-2.2, -4.8), (-1.6, -6.2), (3.6, -2.6)):
    bpy.ops.mesh.primitive_cone_add(vertices=20, radius1=0.17, radius2=0.03, depth=0.55, location=(OVER[0] + cx, OVER[1] + cy, 0.43))
    C.assign(bpy.context.object, cone); C.soften(bpy.context.object, 0.01, 2); C.no_ink(bpy.context.object)
    C.rbox((0.4, 0.4, 0.04), (OVER[0] + cx, OVER[1] + cy, 0.17), cone, r=0.01)
    C.rcyl(0.11, 0.07, (OVER[0] + cx, OVER[1] + cy, 0.5), C.pbr('cone_band', (0.9, 0.9, 0.88), rough=0.3, coat=0.5), verts=20, r=0.0)
BANNER, BANNER_POSTS, _ = PR.sign_posts('FINAL FAIL · LIVE', (OVER[0] - 0.8, OVER[1] + 3.6), rz=0, w=3.4, h=0.8, style='banner', post_h=3.0)
for wy in (-0.85, 0.85):   # the van's tyre tracks across the gravel, and two stray tumbleweeds
    a = math.radians(-24); G.trail((OVER[0] - 4.6 - 1.45 * math.cos(a) - wy * math.sin(a), OVER[1] - 0.6 - 1.45 * math.sin(a) + wy * math.cos(a)), -24 + 180 + 25, 14, width=0.32, wobble=0.6, seed=9)
for tx, ty, r in ((-2.6, -6.6, 0.32), (3.3, -7.4, 0.24)):
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2, radius=r, location=(OVER[0] + tx, OVER[1] + ty, 0.15 + r * 0.9))
    tw = bpy.context.object; w_ = tw.modifiers.new('wire', 'WIREFRAME'); w_.thickness = 0.03
    C.assign(tw, C.pbr('tumble', PR.lin('#b08a55'), rough=0.8, coat=0.0, bevel=0.0)); C.no_ink(tw)
# warm practicals: van headlamps and a lantern on the sign post
C.point((OVER[0] - 4.6 + 2.7 * math.cos(math.radians(-24)), OVER[1] - 0.6 + 2.7 * math.sin(math.radians(-24)), 1.0), (1.0, 0.70, 0.38), power=90, radius=0.3)
PR.lantern((OVER[0] + 2.0, OVER[1] - 1.7, 0.15))
C.point((OVER[0] - 4.6, OVER[1] - 0.6, 2.2), (1.0, 0.6, 0.3), power=70, radius=0.4)   # cabin glow

# ---------- the flooded / frozen playa (per light) ----------
ice = C.plane(1400, (0, 0, 0.012), G.ice_mat()); ice.name = 'ice_sheet'
pond = C.plane(1400, (0, 0, 0.03), G.pond_mat()); pond.name = 'pond_water'
HOME = {}
def show(o, vis):   # hide by moving under the ground: robust for Freestyle and the depth pass too
    HOME.setdefault(o.name, o.location.copy()); o.location = HOME[o.name] if vis else HOME[o.name] + Vector((0, 0, -60))

def sheet(ln, cam):
    show(ice, ln == 'frost')
    show(pond, ln == 'night' and cam == 'playa_top')
    for l2, objs in SIGNS.items():
        for o in objs: show(o, l2 == ('night' if ln == 'night' else 'day'))
    for o in BANNER + BANNER_POSTS: show(o, ln == 'frost')

# ---------- cameras ----------
hx, hy = HERO; th = math.radians(TRAIL_H); dx, dy = math.cos(th), math.sin(th)
def per(cam): return lambda ln: sheet(ln, cam)
CAMS = {
    'playa_wide': dict(loc=(hx - 3.0 * dx + 1.2 * dy, hy - 3.0 * dy - 1.2 * dx, 1.3), target=(-0.5, 8.0, 0.4), lens=26, stand=(2.4, 2.8, 0), fstop=None,
                       haze_range=(4, 480), per_light=per('playa_wide'), note='depth-layered: hero rock + trail near, camp mid, mountains far'),
    'playa_med': dict(loc=(0.3, -1.6, 1.4), target=(0.0, 9.0, 1.0), lens=22, stand=(0.2, 3.4, 0), fstop=5.6,
                      haze_range=(3, 480), per_light=per('playa_med'), note='camp two-shot; also the 1948/1960s flashbacks (engine sepia)'),
    'rock_low': dict(loc=(hx - 2.9 * dx + 0.9 * dy, hy - 2.9 * dy - 0.9 * dx, 0.38), target=(hx + 9 * dx, hy + 9 * dy, 0.55), lens=24, stand=(hx + 2.6 * dx + 0.9 * dy, hy + 2.6 * dy - 0.9 * dx, 0), fstop=3.2,
                     haze_range=(2, 480), per_light=per('rock_low'), note='ground-level beside the hero rock (left third), its trail running away; holds a 1.7x zoom on the rock edge'),
    'playa_top': dict(loc=(hx + 2.4 * dx, hy + 2.4 * dy, 7.5), target=None, lens=35, roll=TRAIL_H - 90, stand=(hx, hy, 0), fstop=None, top=True,
                      haze_range=(10, 40), haze_k=0.0, per_light=per('playa_top'), light_overrides={'night': dict(exposure=0.9, sun_e=3.0)}, note='top-down: rock near the bottom, trail running up; px_per_m along the ground'),
    'overlook_med': dict(loc=(OVER[0] - 0.2, OVER[1] - 8.6, 1.05), target=(OVER[0] - 0.2, OVER[1] + 6.0, 1.75), lens=18, stand=(OVER[0] - 0.4, OVER[1] - 3.6, 0.15), fstop=4.0,
                         haze_range=(3, 480), per_light=per('overlook_med'), note='gravel pull-out: van left, sign right, alien cut-out; room for 4 characters at 0.8x'),
}
C.INK_FADE, C.INK_RANGE, C.INK_BORDER, C.INK_FAR_K, C.INK_THICK = (20, 80, 0.5), (4, 60), False, 0.6, 2.4   # only the sign boards carry ink
DAYK = dict(sky_refl=1.0, grade_sat=1.18)
LIGHTS = {
    'day': dict(DAYK, az=150, elev=52, sun=(1.0, 0.90, 0.74), sun_e=7.0, sun_soft=10, amb=(0.30, 0.46, 1.0), amb_e=0.75,
                fill=(0.45, 0.6, 1.0), fill_e=120, exposure=-0.55, haze=(0.78, 0.80, 0.96), haze_k=0.45, prac=0.0, emit=0.15,
                sky=[(0.0, (0.82, 0.86, 0.98)), (0.12, (0.42, 0.62, 0.95)), (0.5, (0.16, 0.38, 0.88))], cloud_amt=0.35),
    'golden': dict(DAYK, az=120, elev=12, sun=(1.0, 0.52, 0.20), sun_e=17.0, sun_soft=6, amb=(0.30, 0.40, 0.95), amb_e=0.55,
                   fill=(0.5, 0.55, 1.0), fill_e=140, exposure=0.1, haze=(1.0, 0.62, 0.42), haze_k=0.4, prac=0.6, emit=0.6, grade_warm=(1.04, 1.0, 0.92),
                   sky=[(0.0, (1.0, 0.66, 0.32)), (0.08, (1.0, 0.52, 0.30)), (0.26, (0.55, 0.48, 0.78)), (0.6, (0.22, 0.32, 0.72))], clouds=(1.0, 0.6, 0.4)),
    'night': dict(az=200, elev=50, sun=(0.55, 0.65, 1.0), sun_e=1.6, amb=(0.24, 0.30, 0.62), amb_e=0.8, fill=(0.6, 0.62, 1.0), fill_e=150,
                  exposure=0.55, haze=(0.10, 0.12, 0.28), haze_k=0.45, prac=3.0, emit=5.0, sky_refl=1.0, grade_sat=1.1,
                  sky=[(0.0, (0.22, 0.20, 0.42)), (0.1, (0.07, 0.09, 0.26)), (0.45, (0.02, 0.03, 0.12))], stars=3.5, clouds=None, cloud_amt=0),
    'frost': dict(DAYK, az=95, elev=26, sun=(1.0, 0.84, 0.66), sun_e=8.0, sun_soft=6, amb=(0.42, 0.6, 1.0), amb_e=0.8,
                  fill=(0.55, 0.7, 1.0), fill_e=140, exposure=-0.6, haze=(0.80, 0.88, 1.0), haze_k=0.4, prac=0.0, emit=0.15,
                  sky=[(0.0, (0.86, 0.92, 1.0)), (0.12, (0.52, 0.72, 0.98)), (0.5, (0.22, 0.46, 0.92))], cloud_amt=0.25, tint='#eaf4ff'),
}
TARGETS = {'rock': (HERO[0], HERO[1], 0.3), 'tour_sign': SIGN_C, 'camp_rocks': (0.0, 10.5, 0.2), 'tent': (-2.6, 8.4, 0.8)}
C.PRESETS['frost'] = dict(C.PRESETS['day'])
C.main('playa', CAMS, LIGHTS, targets=TARGETS)
