# Track set (bike-countersteer): a riding-school track with a pit lane, grass run-off, a banner gantry and joke signage.
# Layout (metres): the near straight runs along +X at y = 0..9 (x -25..25), a stadium loop with R = 20 corners;
# the pit lane is at y = -12..-3 behind a low pit wall, the garages at y = -21.
# usage: .venv/bin/python blender/sets/track/build.py [--cams ...] [--lights day,golden] [--pct 25]
import sys, os, math, bpy, bmesh
from mathutils import Vector
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import common as C
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

C.reset()
NAT = f'{C.QUAT}/nature_pack'
TW, R, L = 9.0, 20.0, 50.0           # track width, corner radius (centreline), straight length
CY = 4.5                             # centreline y of the near straight
CORNER_C = (L / 2, CY + R)           # right corner centre

def centreline(n_corner=48):
    """Closed stadium centreline, counter-clockwise from the near straight's left end."""
    pts = []
    for i in range(11): pts.append((-L / 2 + L * i / 10, CY))
    for i in range(1, n_corner): a = -math.pi / 2 + math.pi * i / n_corner; pts.append((L / 2 + R * math.cos(a), CY + R + R * math.sin(a)))
    for i in range(11): pts.append((L / 2 - L * i / 10, CY + 2 * R))
    for i in range(1, n_corner): a = math.pi / 2 + math.pi * i / n_corner; pts.append((-L / 2 + R * math.cos(a), CY + R + R * math.sin(a)))
    return pts

def strip(name, pts, off0, off1, z, m, closed=True, uv_len=1.0):
    """Quad strip between two offsets (left of travel = +) of a polyline; u = arc length / uv_len."""
    me = bpy.data.meshes.new(name); bm = bmesh.new(); uv = bm.loops.layers.uv.new()
    n = len(pts); ring = []; acc = 0.0; us = []
    for i in range(n):
        p0 = Vector((*pts[i - 1], 0)) if (closed or i > 0) else Vector((*pts[i], 0))
        p1 = Vector((*pts[(i + 1) % n], 0)) if (closed or i < n - 1) else Vector((*pts[i], 0))
        t = (p1 - p0).normalized(); nrm = Vector((-t.y, t.x, 0)); p = Vector((*pts[i], z))
        ring.append((bm.verts.new(p + nrm * off0), bm.verts.new(p + nrm * off1)))
        if i: acc += (Vector(pts[i]) - Vector(pts[i - 1])).length
        us.append(acc / uv_len)
    rng = range(n) if closed else range(n - 1)
    for i in rng:
        j = (i + 1) % n; f = bm.faces.new((ring[i][0], ring[j][0], ring[j][1], ring[i][1]))
        uj = us[j] if j else us[i] + (Vector(pts[0]) - Vector(pts[i])).length / uv_len
        for loop, (u, v) in zip(f.loops, ((us[i], 0), (uj, 0), (uj, 1), (us[i], 1))): loop[uv].uv = (u, v)
    bm.to_mesh(me); bm.free(); o = bpy.data.objects.new(name, me); bpy.context.scene.collection.objects.link(o)
    o.data.materials.append(m); return o

def stripes_mat(name, c0, c1, period=1.0):
    m = bpy.data.materials.new(name); m.use_nodes = True; n = m.node_tree.nodes; l = m.node_tree.links
    P = n['Principled BSDF']; P.inputs['Roughness'].default_value = 0.7
    uvn = n.new('ShaderNodeUVMap'); sep = n.new('ShaderNodeSeparateXYZ'); l.new(uvn.outputs['UV'], sep.inputs['Vector'])
    mt = n.new('ShaderNodeMath'); mt.operation = 'PINGPONG'; mt.inputs[1].default_value = period; l.new(sep.outputs['X'], mt.inputs[0])
    gt = n.new('ShaderNodeMath'); gt.operation = 'GREATER_THAN'; gt.inputs[1].default_value = period / 2; l.new(mt.outputs[0], gt.inputs[0])
    mix = n.new('ShaderNodeMixRGB'); mix.inputs['Color1'].default_value = (*c0, 1); mix.inputs['Color2'].default_value = (*c1, 1)
    l.new(gt.outputs[0], mix.inputs['Fac']); l.new(mix.outputs['Color'], P.inputs['Base Color']); return m

def asphalt_mat():
    m = bpy.data.materials.new('asphalt'); m.use_nodes = True; n = m.node_tree.nodes; l = m.node_tree.links
    P = n['Principled BSDF']; P.inputs['Roughness'].default_value = 0.85
    tc = n.new('ShaderNodeTexCoord'); nz = n.new('ShaderNodeTexNoise'); nz.inputs['Scale'].default_value = 0.35
    l.new(tc.outputs['Object'], nz.inputs['Vector'])
    r = n.new('ShaderNodeValToRGB'); r.color_ramp.elements[0].color = (0.12, 0.12, 0.16, 1); r.color_ramp.elements[1].color = (0.19, 0.18, 0.25, 1)
    l.new(nz.outputs['Fac'], r.inputs['Fac']); l.new(r.outputs['Color'], P.inputs['Base Color']); return m

def grass_mat(name='grass', c0=(0.07, 0.20, 0.03), c1=(0.11, 0.27, 0.04), mow=True):
    m = bpy.data.materials.new(name); m.use_nodes = True; n = m.node_tree.nodes; l = m.node_tree.links
    P = n['Principled BSDF']; P.inputs['Roughness'].default_value = 0.95; P.inputs['Specular IOR Level'].default_value = 0.2
    tc = n.new('ShaderNodeTexCoord'); sep = n.new('ShaderNodeSeparateXYZ'); l.new(tc.outputs['Object'], sep.inputs['Vector'])
    mt = n.new('ShaderNodeMath'); mt.operation = 'PINGPONG'; mt.inputs[1].default_value = 3.0; l.new(sep.outputs['X'], mt.inputs[0])
    gt = n.new('ShaderNodeMath'); gt.operation = 'GREATER_THAN'; gt.inputs[1].default_value = 1.5; l.new(mt.outputs[0], gt.inputs[0])
    mix = n.new('ShaderNodeMixRGB'); mix.inputs['Color1'].default_value = (*c0, 1); mix.inputs['Color2'].default_value = (*c1, 1)
    mix.inputs['Fac'].default_value = 0.0
    if mow: l.new(gt.outputs[0], mix.inputs['Fac'])                          # mown stripes
    l.new(mix.outputs['Color'], P.inputs['Base Color']); return m

# ---------- ground, track, kerbs, lines ----------
C.plane(700, (0, 0, -0.01), grass_mat())
CL = centreline()
strip('track', CL, -TW / 2, TW / 2, 0.0, asphalt_mat())   # inked: its border edges are the track edges
white = C.mat('white_line', (0.92, 0.92, 0.88), rough=0.6)
for k, (a, b) in enumerate(((-TW / 2, -TW / 2 + 0.3), (TW / 2 - 0.3, TW / 2))):
    strip(f'edge{k}', CL, a, b, 0.012, white)          # inked: outlines both sides of the white line
kerb = stripes_mat('kerb', (0.85, 0.10, 0.08), (0.95, 0.95, 0.92), period=1.6)
for side in (1, -1):   # kerbs on the inside and outside of both corners (+ a little of the straights)
    cx = side * L / 2
    arc = [(cx + side * R * math.cos(-math.pi / 2 + math.pi * i / 40), CY + R + R * math.sin(-math.pi / 2 + math.pi * i / 40)) for i in range(41)]
    arc = [(cx - 6 * side, CY)] + arc + [(cx - 6 * side, CY + 2 * R)]
    o = strip(f'kerb_in{side}', arc, TW / 2 * side, (TW / 2 + 1.1) * side, 0.03, kerb, closed=False, uv_len=1.0)
    o = strip(f'kerb_out{side}', arc, -TW / 2 * side, -(TW / 2 + 1.1) * side, 0.03, kerb, closed=False, uv_len=1.0); C.no_ink(o)
# start / finish chequer across the near straight
chq = C.mat('chq', (0.95, 0.95, 0.92)); blk = C.mat('chq_b', (0.05, 0.05, 0.06))
for i in range(9):
    for j in range(2):
        b = C.box((0.5, 1.0, 0.02), (-12.0 + j * 0.5, 0.5 + i, 0.015), chq if (i + j) % 2 else blk, ink=False)

# ---------- pit lane: concrete apron, pit wall, garages ----------
concrete = C.mat('concrete', (0.36, 0.35, 0.34), rough=0.9)
C.box((70, 10, 0.06), (0, -7.5, 0.0), concrete, ink=False)
wall = stripes_mat('pitwall', (0.62, 0.62, 0.60), (0.70, 0.08, 0.06), period=4.0)
pw = C.box((62, 0.35, 0.95), (-4.0, -2.4, 0.47), wall)
pw.data.uv_layers.new(name='UVMap')
for l in pw.data.loops: pw.data.uv_layers['UVMap'].data[l.index].uv = (pw.data.vertices[l.vertex_index].co.x * 62, 0)
gw = C.mat('garage_wall', (0.70, 0.66, 0.58), rough=0.9); groof = C.mat('garage_roof', (0.20, 0.35, 0.70), rough=0.7)
dark = C.mat('garage_dark', (0.22, 0.24, 0.30), rough=0.9); stripe = C.mat('garage_stripe', (0.85, 0.15, 0.10))
C.box((44, 7, 4.2), (0, -16.5, 2.1), gw)
C.box((45, 8, 0.35), (0, -16.3, 4.35), groof)
C.box((44.05, 7.05, 0.4), (0, -16.5, 3.4), stripe)
for x in (-14, -5, 4, 13):                     # garage door openings (dark), one with its door half up
    C.box((6.0, 0.2, 3.0), (x, -12.95, 1.5), dark)
C.sign('RIDING SCHOOL', 'banner', loc=(0, -12.7, 4.95), w=10.0, h=1.0)
# chalkboard on an easel and the lap board on the garage wall
def push_left(d, box, fg):
    """Top view of a bike's front end (front = up): left grip pushed forward, front wheel turned right,
    and a curved arrow showing the bike then goes left."""
    x0, y0, x1, y1 = box; w, h = x1 - x0, y1 - y0; lw = max(3, int(h / 45)); yel = (255, 214, 80)
    cx, cy = x0 + w * 0.36, y0 + h * 0.62; a = math.radians(18)          # steering angle: wheel turned right
    def rot(px, py): return (cx + px * math.cos(a) - py * math.sin(a), cy + px * math.sin(a) + py * math.cos(a))
    wl, ww = h * 0.36, h * 0.07                                           # front wheel: long thin rounded shape, ahead of the bar
    d.polygon([rot(-ww, -wl * 0.15), rot(ww, -wl * 0.15), rot(ww, -wl), rot(0, -wl - ww), rot(-ww, -wl)], outline=fg, width=lw)
    d.line([rot(0, 0), rot(0, -wl * 0.15)], fill=fg, width=lw * 2)
    bl = w * 0.22; d.line([rot(-bl, 0), rot(bl, 0)], fill=fg, width=lw * 2)    # handlebar
    for sx in (-1, 1): d.line([rot(sx * bl, 0), rot(sx * bl * 0.78, 0)], fill=fg, width=lw * 5)   # grips
    gx, gy = rot(-bl * 0.9, 0)                                            # push arrow at the LEFT grip, pointing forward (up)
    d.line([(gx, gy), (gx, gy - h * 0.24)], fill=yel, width=lw * 2)
    d.polygon([(gx - h * 0.05, gy - h * 0.22), (gx + h * 0.05, gy - h * 0.22), (gx, gy - h * 0.31)], fill=yel)
    ax, ay = x0 + w * 0.80, y0 + h * 0.55                                 # result: the bike curls LEFT
    d.line([(ax, ay + h * 0.3), (ax, ay - h * 0.05)], fill=fg, width=lw * 2)
    d.arc([ax - w * 0.24, ay - h * 0.28, ax, ay + h * 0.14], 270, 360, fill=fg, width=lw * 2)
    d.polygon([(ax - w * 0.12, ay - h * 0.36), (ax - w * 0.12, ay - h * 0.20), (ax - w * 0.21, ay - h * 0.28)], fill=fg)
cb = C.sign('PUSH LEFT → GO LEFT', 'chalk', loc=(-0.8, -11.8, 1.75), rz=190, w=1.9, h=1.6, draw=push_left, text_frac=0.34)
legs = C.mat('easel', (0.45, 0.28, 0.14))
for dx in (-0.85, 0.85): C.cyl(0.04, 2.0, (-0.8 + dx * 0.9, -12.1, 0.95), legs, rot=(6, 0, 0), verts=6)
C.sign('CORNERS MADE: 0', 'board', loc=(1.05, -12.7, 3.0), rz=180, w=2.2, h=0.66)
# tyre stacks, cones, a toolbox trolley
tyre = C.mat('tyre', (0.05, 0.05, 0.06), rough=0.9)
def tyres(x, y, n):
    for k in range(n):
        bpy.ops.mesh.primitive_torus_add(major_radius=0.33, minor_radius=0.14, location=(x, y, 0.14 + 0.27 * k)); C.assign(bpy.context.object, tyre)
for x, y, n in ((-6.5, -11.8, 4), (-5.8, -11.4, 3), (7.0, -11.9, 4), (12.0, 10.8, 3), (13.0, 10.8, 3), (14.0, 10.8, 3),
                (-28, -6.5, 4), (31, 9.8, 3), (32, 9.6, 3)):
    tyres(x, y, n)
cone = C.mat('cone', (1.0, 0.35, 0.05)); band = C.mat('cone_band', (0.95, 0.95, 0.92))
def cone_at(x, y):
    bpy.ops.mesh.primitive_cone_add(vertices=10, radius1=0.18, radius2=0.03, depth=0.6, location=(x, y, 0.3)); C.assign(bpy.context.object, cone)
    C.box((0.42, 0.42, 0.04), (x, y, 0.02), cone)
for x, y in ((-18, 2.0), (-14, 2.4), (-10, 2.8), (17.0, 7.8), (19.5, 10.5), (-1.5, -7.0), (1.5, -7.5)):
    cone_at(x, y)
C.box((0.9, 0.5, 0.8), (6.0, -12.0, 0.45), C.mat('toolbox', (0.80, 0.10, 0.10), rough=0.5))

# ---------- banner gantry over the near straight ----------
GX = 10.0
steel = C.mat('steel', (0.42, 0.44, 0.50), rough=0.5, metal=0.3)
for y in (-1.2, TW + 1.2): C.cyl(0.14, 6.0, (GX, y, 3.0), steel, verts=10)
C.cyl(0.11, TW + 2.6, (GX, CY, 5.85), steel, rot=(90, 0, 0), verts=10)
C.sign('BODY-STEERING\nCHALLENGE', 'banner', loc=(GX - 0.1, CY, 4.85), rz=-90, w=TW - 0.6, h=1.8, depth=0.04)
C.sign('BODY-STEERING\nCHALLENGE', 'banner', loc=(GX + 0.1, CY, 4.85), rz=90, w=TW - 0.6, h=1.8, depth=0.04)

# ---------- scenery: trees, hills, a small grandstand ----------
import random
rnd = random.Random(4)
for k in range(46):
    a = rnd.uniform(0, 2 * math.pi); rr = rnd.uniform(46, 70)
    x, y = CORNER_C[0] * 0.2 + rr * 1.3 * math.cos(a), CY + R + rr * math.sin(a)
    if y < -26 or (-30 < x < 30 and y < 0): continue
    C.imp_h(f'{NAT}/CommonTree_{rnd.randint(1, 5)}.glb', rnd.uniform(7, 11), (x, y, 0), rnd.uniform(0, 360))
for x, y in ((-42, -30), (-36, -34), (36, -30), (44, -28), (-50, -18), (52, -14), (-8, -32), (8, -34), (20, -33), (-22, -33)):
    C.imp_h(f'{NAT}/CommonTree_{rnd.randint(1, 5)}.glb', rnd.uniform(8, 12), (x, y, 0), rnd.uniform(0, 360))
for x, y in ((-6, 20), (2, 26), (-12, 30), (8, 18)):                          # infield bushes
    C.imp_h(f'{NAT}/Bush_{rnd.randint(1, 2)}.glb', 1.4, (x, y, 0), rnd.uniform(0, 360))
hillm = C.mat('far_hill', (0.20, 0.38, 0.16), rough=0.95)
for x, y, sx, sz in ((-60, 150, 90, 28), (70, 160, 110, 34), (0, 190, 140, 45)):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=1, location=(x, y, -sz * 0.35)); h = bpy.context.object
    h.scale = (sx, 40, sz); C.assign(h, hillm)
seat = stripes_mat('stand_seats', (0.20, 0.45, 0.85), (0.95, 0.80, 0.15), period=6.0)
for k in range(5):   # grandstand steps along the far straight's outside
    o = C.box((40, 1.2, 0.6 + k * 0.6), (0, CY + 2 * R + TW / 2 + 5 + k * 1.2, 0.3 + k * 0.3), seat)
    o.data.uv_layers.new(name='UVMap')
    for l in o.data.loops: o.data.uv_layers['UVMap'].data[l.index].uv = (o.data.vertices[l.vertex_index].co.x * 40, 0)
C.box((42, 0.3, 6), (0, CY + 2 * R + TW / 2 + 11.2, 3), groof)

C.stylise(emissive_prefixes=('__none__',))
C.point((-6.0, -10.5, 3.0), power=120, radius=1.5)
lampm = C.emissive(C.mat('pitlamp', (1.0, 0.45, 0.12), 0.3), (1.0, 0.45, 0.12), 0.5)
for x in (-18, -9.5, -0.5, 8.5, 17.5):                    # warm lamps over the garage doors
    C.box((0.6, 0.25, 0.18), (x, -12.85, 3.25), lampm); C.point((x, -11.6, 2.6), power=70, radius=0.5)
for y in (-0.6, TW + 0.6): C.point((GX - 1.2, y, 5.6), power=220, radius=0.3)   # floodlights on the banner          # warm garage spill (golden only)

# ---------- cameras ----------
TOP_X = L / 2 + R / 2 + 2
CAMS = {
    'track_wide': dict(loc=(-6.0, -5.5, 4.2), target=(16.0, 14.0, 0.8), lens=22, roll=0, stand=(1.6, 2.0, 0), fstop=None,
                       haze_range=(5, 200)),
    'track_med': dict(loc=(-0.6, -0.6, 1.3), target=(9.0, 5.0, 2.5), lens=24, roll=0, stand=(1.7, 1.0, 0), fstop=2.4,
                      ink_fade=(6, 40, 0.5), haze_range=(4, 200)),
    'track_top': dict(loc=(L / 2 + R * 0.707 + 0.5, CY + R - R * 0.707 + 4.0, 24.0), target=None, lens=35, roll=0, stand=(L / 2 + R * 0.707, CY + R - R * 0.707, 0), fstop=None, top=True,
                      haze_range=(40, 120), haze_k=0.3, light_overrides={'day': dict(grade_sat=1.0, grade_gain=1.05), 'golden': dict(grade_sat=0.95, grade_gain=1.15)}, note='top-down view: px_per_m measured along the ground',
                      json_extra=lambda: {'paths': __import__('paths').project()}),   # racing lines on the real road (paths.py)
    'pit_med': dict(loc=(0.4, -7.2, 1.35), target=(-0.35, -16.0, 1.9), lens=26, roll=0, stand=(0.3, -9.75, 0), fstop=2.8,
                    ink_fade=(4, 30, 0.5), haze_range=(3, 120),
                    light_overrides={'day': dict(grade_sat=1.0, grade_gain=1.18), 'golden': dict(grade_sat=1.0, grade_gain=1.15)}),
    'pit_ots': dict(loc=(1.3, -12.4, 1.6), target=(-5.0, 6.0, 1.7), lens=32, roll=0, stand=(0.2, -8.9, 0), fstop=2.4,
                    ink_fade=(4, 40, 0.5), haze_range=(3, 200),
                    note='over the shoulder: stand = the facing character; the near character is composited large at the frame edge'),
    'bike_close': dict(loc=(-6.0, 0.9, 0.75), target=(-2.8, 4.2, 0.65), lens=32, roll=0, stand=(-3.2, 3.6, 0), fstop=2.0,
                       ink_fade=(3, 20, 0.6), haze_range=(3, 150)),
    'bike_chase': dict(loc=(-15.0, 4.0, 1.4), target=(20.0, 6.5, 1.2), lens=26, roll=0, stand=(-10.0, 4.4, 0), fstop=2.8,
                       haze_range=(4, 200)),
    'grips_close': dict(loc=(-7.7, 3.2, 1.2), target=(-6.0, 4.9, 1.05), lens=45, roll=-3, stand=(-6.1, 4.8, 0), fstop=1.8,
                        ink_fade=(3, 15, 0.7), haze_range=(2, 120)),
    'rider_close': dict(loc=(-1.0, 1.95, 1.5), target=(0.6, 4.6, 1.45), lens=40, roll=0, stand=(0.2, 3.6, 0), fstop=1.8,
                        ink_fade=(3, 15, 0.7), haze_range=(2, 150)),
}
C.INK_FADE, C.INK_RANGE, C.INK_BORDER, C.INK_FAR_K, C.INK_THICK = (35, 120, 0.4), (6, 80), True, 0.6, 4.8   # an open track: keep outlines on the far trees and gantry
LIGHTS = {'day': dict(az=-30, elev=50, exposure=-0.25, haze_k=0.2, grade_sat=1.3, grade_gain=1.0),
          'golden': dict(az=-35, elev=16, sun_e=12.0, sun=(1.0, 0.50, 0.18), amb=(0.40, 0.50, 1.0), amb_e=0.32, grade_warm=(1.04, 1.0, 0.9), haze=(1.0, 0.72, 0.42), clouds=(1.0, 0.72, 0.45),
                     sky=[(0.0, (1.0, 0.70, 0.32)), (0.10, (1.0, 0.58, 0.30)), (0.30, (0.50, 0.58, 0.88)), (0.60, (0.24, 0.40, 0.82))], exposure=0.0, haze_k=0.2, grade_sat=1.25, grade_gain=1.0)}
TARGETS = {'chalkboard': (-0.8, -11.8, 1.75), 'lapboard': (1.05, -12.7, 3.0), 'banner': (GX, CY, 4.85)}   # sign centres
C.main('track', CAMS, LIGHTS, targets=TARGETS)
