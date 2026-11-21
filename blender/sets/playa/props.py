# Hero props for the playa set (sailing-stones), built from primitives in the stylised-PBR recipe (common.pbr/soften):
# rounded bevels, glossy paint with clearcoat, gold trim, no ink. Every function returns the objects it made.
import os, sys, math, bpy
from mathutils import Vector
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import common as C

def lin(h):
    h = h.lstrip('#'); c = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    return tuple(x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in c)

PURPLE, CREAM, LIME, PLUM = lin('#7a22d6'), lin('#f6d49a'), lin('#6fd16a'), lin('#241726')

def _rot(p, rz):
    a = math.radians(rz); return (p[0] * math.cos(a) - p[1] * math.sin(a), p[0] * math.sin(a) + p[1] * math.cos(a), p[2])

def group(objs, loc, rz):
    """Parent objects built around the origin to an empty at loc, turned by rz."""
    e = bpy.data.objects.new('grp', None); C.sc().collection.objects.link(e)
    for o in objs: o.parent = e
    e.location = loc; e.rotation_euler.z = math.radians(rz); return e

def decal(text_draw, w, h, loc, rot, name):
    """A painted decal: PIL draws onto RGBA, the plane uses alpha (clip) so it sits on paint like a sticker."""
    from PIL import Image, ImageDraw
    px = 256; im = Image.new('RGBA', (int(w * px), int(h * px)), (0, 0, 0, 0)); text_draw(ImageDraw.Draw(im), im.size)
    d = os.path.join(bpy.app.tempdir or '/tmp', 'decals'); os.makedirs(d, exist_ok=True); p = os.path.join(d, name + '.png'); im.save(p)
    m = bpy.data.materials.new(name); m.use_nodes = True; n = m.node_tree.nodes; l = m.node_tree.links; P = n['Principled BSDF']
    t = n.new('ShaderNodeTexImage'); t.image = bpy.data.images.load(p); t.image.pack()
    l.new(t.outputs['Color'], P.inputs['Base Color']); l.new(t.outputs['Alpha'], P.inputs['Alpha'])
    P.inputs['Roughness'].default_value = 0.35; P.inputs['Coat Weight'].default_value = 0.4
    bpy.ops.mesh.primitive_plane_add(size=1, location=loc, rotation=tuple(math.radians(a) for a in rot)); o = bpy.context.object
    o.scale = (w, h, 1); C.assign(o, m); C.no_ink(o); return o

def tour_van(loc=(0, 0, 0), rz=0, lights_on=False):
    """A boxy tour van (no brand): purple lower body, cream top, a gold trim band, chrome bumpers, roof rack with
    two springy alien antenna balls, a painted green alien-head decal. Length along +X (front at +X), 4.8 m."""
    body = C.pbr('van_purple', PURPLE, rough=0.22, coat=1.0, bevel=0.06, dust=(0.75, (0.45, 0.32, 0.20)))
    body.node_tree.nodes['Principled BSDF'].inputs['Coat Roughness'].default_value = 0.04
    top = C.pbr('van_cream', CREAM, rough=0.22, coat=0.9, bevel=0.06)
    gl = C.glass('van_glass', (0.025, 0.06, 0.12)); gd = C.gold('van_gold')
    chrome = C.pbr('chrome', (0.75, 0.76, 0.78), rough=0.18, metal=1.0, coat=0.0, bevel=0.01)
    rub = C.pbr('tyre', (0.025, 0.022, 0.03), rough=0.75, coat=0.0, bevel=0.02)
    o = []
    L, Wd = 4.8, 1.95
    o.append(C.rbox((L, Wd, 0.95), (0, 0, 0.85), body, r=0.30, seg=5))
    o.append(C.rbox((L - 0.9, Wd - 0.06, 0.95), (-0.40, 0, 1.75), top, r=0.24, seg=5))
    o.append(C.rbox((L + 0.04, Wd + 0.04, 0.10), (0, 0, 1.32), gd, r=0.04))                      # gold belt line
    seam = C.pbr('van_seam', (0.03, 0.01, 0.05), rough=0.6, coat=0.0, bevel=0.0)
    for sy in (1, -1):   # door panel breaks on the flanks
        for x in (-0.75, 2.12): o.append(C.rbox((0.025, 0.02, 0.78), (x, sy * (Wd / 2 + 0.002), 0.86), seam, r=0.008))
        o.append(C.rbox((0.12, 0.03, 0.035), (0.75, sy * (Wd / 2 + 0.01), 1.05), C.pbr('chrome', (0.75, 0.76, 0.78), rough=0.18, metal=1.0, coat=0.0), r=0.01))
    # windows: side strips and the windscreen
    for sy in (1, -1):
        for k, x in enumerate((-1.75, -0.75, 0.25, 1.15)):
            o.append(C.rbox((0.82 if k < 3 else 0.62, 0.04, 0.44), (x, sy * (Wd / 2 - 0.02), 1.76), gl, r=0.08))
    ws = C.rbox((0.05, Wd - 0.50, 0.50), (L / 2 - 0.84, 0, 1.76), gl, r=0.08); o.append(ws)
    def streaks(d, sz):   # cartoon glass glints: two diagonal white bars
        w, h = sz
        for x0, bw in ((0.18, 0.16), (0.42, 0.07)):
            d.polygon([(w * x0, h), (w * (x0 + bw), h), (w * (x0 + bw + 0.25), 0), (w * (x0 + 0.25), 0)], fill=(235, 245, 255, 70))
    o.append(decal(streaks, Wd - 0.56, 0.46, (L / 2 - 0.80, 0, 1.76), (90, 0, 90), 'van_glint_f'))
    for sy in (1, -1): o.append(decal(streaks, 3.6, 0.4, (-0.3, sy * (Wd / 2 + 0.01), 1.76), (90, 0, 0 if sy < 0 else 180), f'van_glint{sy}'))
    o.append(C.rbox((0.9, Wd - 0.02, 0.18), (L / 2 - 0.45, 0, 1.36), top, r=0.08))                 # bonnet
    o.append(C.rbox((0.05, 0.5, 0.06), (L / 2 - 0.80, 0.35, 1.52), chrome, r=0.02))               # wiper
    # bumpers, grille, lamps
    for x in (L / 2 + 0.04, -L / 2 - 0.04): o.append(C.rbox((0.18, Wd + 0.06, 0.22), (x, 0, 0.48), chrome, r=0.07))
    o.append(C.rbox((0.06, 0.9, 0.36), (L / 2 + 0.01, 0, 0.88), C.pbr('grille', (0.03, 0.015, 0.04), rough=0.4, coat=0.3), r=0.03))
    for z in (0.78, 0.88, 0.98): o.append(C.rbox((0.04, 0.86, 0.035), (L / 2 + 0.045, 0, z), chrome, r=0.012))
    lamp = C.pbr('van_lamp', (1.0, 0.86, 0.55), rough=0.1, coat=0.0, bevel=0.0, emit=6.0 if lights_on else 0.4)
    C.emissive(lamp, (1.0, 0.86, 0.55), 0.6)
    for sy in (0.72, -0.72):
        o.append(C.rcyl(0.15, 0.08, (L / 2 + 0.01, sy, 0.95), lamp, rot=(0, 90, 0), verts=20, r=0.01))
        o.append(C.rcyl(0.19, 0.06, (L / 2 - 0.01, sy, 0.95), gd, rot=(0, 90, 0), verts=20, r=0.01))
        o.append(C.rbox((0.06, 0.22, 0.16), (-L / 2 - 0.0, sy * 0.95, 1.0), C.pbr('van_tail', (0.8, 0.05, 0.03), rough=0.2, emit=1.0), r=0.03))
    # wheels with gold hubs, in dark arches
    arch = C.pbr('arch', (0.02, 0.015, 0.025), rough=0.9, coat=0.0, bevel=0.0)
    for x in (1.45, -1.45):
        for sy in (1, -1):
            o.append(C.rcyl(0.47, 0.1, (x, sy * (Wd / 2 - 0.02), 0.52), arch, rot=(90, 0, 0), verts=28, r=0.0))
            o.append(C.rcyl(0.40, 0.32, (x, sy * (Wd / 2 - 0.12), 0.40), rub, rot=(90, 0, 0), verts=32, r=0.07))
            o.append(C.rcyl(0.20, 0.06, (x, sy * (Wd / 2 + 0.05), 0.40), gd, rot=(90, 0, 0), verts=24, r=0.02))
            o.append(C.rcyl(0.07, 0.08, (x, sy * (Wd / 2 + 0.08), 0.40), chrome, rot=(90, 0, 0), verts=16, r=0.01))
    # roof rack (gold rails) and the antenna balls on springs
    for sy in (0.7, -0.7): o.append(C.rcyl(0.055, L - 1.3, (-0.45, sy, 2.36), gd, rot=(0, 90, 0), verts=12, r=0.0))
    for x in (-1.9, -0.45, 1.0): o.append(C.rcyl(0.045, 1.4, (x, 0, 2.36), gd, rot=(90, 0, 0), verts=10, r=0.0))
    # luggage on the rack: a striped duffel, a cooler, a rolled tarp tied with rope
    o.append(C.rbox((0.8, 0.55, 0.38), (-1.5, 0.15, 2.58), C.pbr('bag', lin('#e8613c'), rough=0.6, coat=0.1, bevel=0.03), r=0.14))
    o.append(C.rbox((0.62, 0.5, 0.42), (-0.6, -0.25, 2.60), C.pbr('cooler_lug', lin('#3a8fd1'), rough=0.3, coat=0.6), r=0.07))
    o.append(C.rbox((0.66, 0.54, 0.06), (-0.6, -0.25, 2.83), C.pbr('cooler_lid', (0.85, 0.85, 0.82), rough=0.3, coat=0.6), r=0.03))
    o.append(C.rcyl(0.2, 1.1, (0.25, 0.3, 2.58), C.pbr('tarp', lin('#2f6b4f'), rough=0.7, coat=0.0, bevel=0.02), rot=(90, 0, 0), verts=20, r=0.04))
    for yy in (-0.05, 0.6): o.append(C.rcyl(0.215, 0.05, (0.25, yy, 2.58), C.pbr('rope', lin('#c9a46a'), rough=0.8, coat=0.0), rot=(90, 0, 0), verts=20, r=0.01))
    ball = C.pbr('alien_ball', LIME, rough=0.25, coat=0.8, bevel=0.0, emit=0.0)
    for sy in (0.45, -0.45):
        bpy.ops.curve.primitive_bezier_curve_add(); cu = bpy.context.object
        sp = cu.data.splines[0]; p0, p1 = sp.bezier_points
        p0.co = (1.0, sy, 2.25); p0.handle_left = (1.0, sy, 2.1); p0.handle_right = (1.0, sy * 1.2, 2.7)
        p1.co = (1.25, sy * 1.5, 3.05); p1.handle_left = (1.05, sy * 1.45, 2.85); p1.handle_right = (1.4, sy * 1.5, 3.2)
        cu.data.bevel_depth = 0.04; cu.data.bevel_resolution = 3; C.assign(cu, C.pbr('spring', PLUM, rough=0.4, coat=0.2, bevel=0.0))
        C.no_ink(cu); o.append(cu)
        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.2, location=(1.25, sy * 1.5, 3.15)); b = bpy.context.object
        for pl in b.data.polygons: pl.use_smooth = True
        C.assign(b, ball); C.no_ink(b); o.append(b)
    # side decal: a green alien head on both flanks
    def alien(d, sz):
        w, h = sz; d.ellipse([w * 0.18, h * 0.05, w * 0.82, h * 0.95], fill=(111, 209, 106, 255), outline=(36, 23, 38, 255), width=int(h * 0.05))
        for cx in (0.37, 0.63):
            d.ellipse([w * (cx - 0.11), h * 0.38, w * (cx + 0.11), h * 0.62], fill=(36, 23, 38, 255))
        d.arc([w * 0.40, h * 0.62, w * 0.60, h * 0.80], 20, 160, fill=(36, 23, 38, 255), width=int(h * 0.04))
    def lettering(d, sz):   # hand-painted tour name on the flank
        from PIL import ImageFont
        w, h = sz; f = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', int(h * 0.62))
        t = 'ALIEN ROCK TOURS'; bb = d.textbbox((0, 0), t, font=f)
        d.text(((w - bb[2]) / 2, (h - bb[3]) / 2 - bb[1] / 2), t, font=f, fill=(246, 212, 154, 255), stroke_width=int(h * 0.06), stroke_fill=(36, 23, 38, 255))
    for sy in (1, -1):
        o.append(decal(lettering, 2.6, 0.30, (0.75, sy * (Wd / 2 + 0.012), 0.80), (90, 0, 0 if sy < 0 else 180), f'van_name{sy}'))
    for sy in (1, -1):
        o.append(decal(alien, 0.5, 0.5, (-1.45, sy * (Wd / 2 + 0.012), 0.95), (90, 0, 0 if sy < 0 else 180), f'van_alien{sy}'))
    o.append(C.contact_blob((0, 0, 0), L + 1.4, Wd + 1.2))
    for x in (1.45, -1.45):
        for sy in (1, -1): o.append(C.contact_blob((x, sy * (Wd / 2 - 0.12), 0.001), 1.1, 0.7, strength=1.0))   # tyre AO
    for x in o:
        if x.name not in bpy.data.collections['noink'].objects: C.no_ink(x)
    return group(o, loc, rz)

def gps_box(loc=(0, 0, 0), rz=0, s=1.0):
    """Small grey tracker box with a stubby antenna and a green status LED (~16 x 10 x 6 cm)."""
    grey = C.pbr('gps_grey', lin('#aeb6c2'), rough=0.25, coat=0.8, bevel=0.008)
    o = [C.rbox((0.16 * s, 0.10 * s, 0.06 * s), (0, 0, 0.03 * s), grey, r=0.012 * s)]
    o.append(C.rcyl(0.008 * s, 0.14 * s, (0.05 * s, 0.03 * s, 0.13 * s), C.pbr('gps_ant', PLUM, rough=0.4), verts=8, r=0.0))
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.014 * s, location=(0.05 * s, 0.03 * s, 0.205 * s)); b = bpy.context.object
    C.assign(b, C.pbr('gps_tip', lin('#e8613c'), rough=0.3)); C.no_ink(b); o.append(b)
    led = C.pbr('gps_led', (0.2, 1.0, 0.3), rough=0.2, coat=0.0, bevel=0.0, emit=12.0)
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.012 * s, location=(-0.04 * s, 0.0, 0.062 * s)); lb = bpy.context.object
    C.assign(lb, led); C.no_ink(lb); o.append(lb)
    o.append(C.rbox((0.10 * s, 0.002 * s, 0.025 * s), (0.0, -0.051 * s, 0.03 * s), C.pbr('gps_label', lin('#ffc533'), rough=0.3), r=0.001 * s))
    o.append(C.rbox((0.17 * s, 0.11 * s, 0.012 * s), (0, 0, 0.004 * s), C.gold('gps_gold'), r=0.004 * s))
    return group(o, loc, rz)

def dome_tent(loc=(0, 0, 0), rz=0, col='#e8613c'):
    """Two-pole dome tent: a squashed hemisphere in glossy nylon, gold-ish pole arcs, a dark door zip panel, guy lines."""
    nylon = C.pbr('tent_nylon', lin(col), rough=0.45, coat=0.3, bevel=0.0, sheen=0.3)
    fly = C.pbr('tent_fly', lin('#f2b134'), rough=0.45, coat=0.3, bevel=0.0)
    o = []
    bpy.ops.mesh.primitive_uv_sphere_add(segments=24, ring_count=12, radius=1.0, location=(0, 0, 0)); d = bpy.context.object
    for v in d.data.vertices:
        if v.co.z < 0: v.co.z = 0
    d.scale = (1.15, 1.0, 1.05); [setattr(p, 'use_smooth', True) for p in d.data.polygons]; C.assign(d, nylon); C.no_ink(d); o.append(d)
    bpy.ops.mesh.primitive_uv_sphere_add(segments=24, ring_count=12, radius=1.0, location=(0, 0, 0)); f = bpy.context.object
    for v in f.data.vertices:
        if v.co.z < 0.55: v.co.z = 0.55
    f.scale = (0.75, 0.68, 1.11); [setattr(p, 'use_smooth', True) for p in f.data.polygons]; C.assign(f, fly); C.no_ink(f); o.append(f)
    for a in (35, -35):   # crossing pole arcs
        bpy.ops.mesh.primitive_torus_add(major_radius=1.06, minor_radius=0.022, location=(0, 0, 0), rotation=(math.radians(90), 0, math.radians(a)))
        t = bpy.context.object; C.assign(t, C.gold('tent_pole')); C.no_ink(t); o.append(t)
    door = C.pbr('tent_door', lin('#7a2a1a'), rough=0.6, coat=0.0, bevel=0.0)
    bpy.ops.mesh.primitive_circle_add(vertices=24, radius=0.5, fill_type='NGON', location=(0, -1.005, 0.38), rotation=(math.radians(90), 0, 0))
    dr = bpy.context.object; dr.scale = (0.85, 0.75, 1); C.assign(dr, door); C.no_ink(dr); o.append(dr)
    o.append(C.contact_blob((0, 0, 0), 2.9, 2.6))
    return group(o, loc, rz)

def tripod_cam(loc=(0, 0, 0), rz=0, h=1.35):
    """Time-lapse camera on a tripod: three legs, a chunky body with a big lens, a red record light, a small solar panel."""
    dark = C.pbr('tri_metal', (0.06, 0.06, 0.07), rough=0.35, metal=0.6, coat=0.2)
    o = []
    for k in range(3):
        a = math.radians(90 + k * 120); x, y = 0.38 * math.cos(a), 0.38 * math.sin(a)
        L = math.sqrt(0.38 ** 2 + h ** 2); tilt = math.degrees(math.atan2(0.38, h))
        leg = C.rcyl(0.02, L, (x / 2, y / 2, h / 2), dark, verts=8, r=0.0)
        leg.rotation_euler = (0, 0, 0); leg.rotation_euler = (Vector((-x, -y, h)).normalized()).to_track_quat('Z', 'Y').to_euler(); o.append(leg)
    body = C.pbr('cam_body', lin('#3a8fd1'), rough=0.3, coat=0.6)
    o.append(C.rbox((0.22, 0.16, 0.16), (0, 0, h + 0.1), body, r=0.03))
    o.append(C.rcyl(0.07, 0.12, (0, -0.12, h + 0.1), C.pbr('lens_ring', (0.03, 0.03, 0.035), rough=0.3, coat=0.5), rot=(90, 0, 0), verts=20, r=0.01))
    o.append(C.rcyl(0.05, 0.01, (0, -0.185, h + 0.1), C.glass('lens_glass', (0.05, 0.12, 0.25)), rot=(90, 0, 0), verts=20, r=0.0))
    o.append(C.rcyl(0.075, 0.015, (0, -0.172, h + 0.1), C.gold('cam_gold'), rot=(90, 0, 0), verts=20, r=0.003))
    rec = C.pbr('rec', (1.0, 0.08, 0.05), rough=0.2, coat=0.0, bevel=0.0, emit=8.0)
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.014, location=(0.08, -0.081, h + 0.16)); r = bpy.context.object; C.assign(r, rec); C.no_ink(r); o.append(r)
    sp = C.rbox((0.3, 0.2, 0.015), (0, 0.05, h + 0.3), C.pbr('solar', (0.02, 0.04, 0.12), rough=0.15, coat=0.8), r=0.005); sp.rotation_euler.x = math.radians(-30); o.append(sp)
    o.append(C.rcyl(0.012, 0.14, (0, 0.05, h + 0.22), dark, verts=8, r=0.0))
    return group(o, loc, rz)

def weather_mast(loc=(0, 0, 0), rz=0, h=3.0):
    """Weather station: a pole with guy wires, cup anemometer, a wind vane, a white radiation shield, a solar panel, a box."""
    pole = C.pbr('mast', (0.65, 0.66, 0.68), rough=0.3, metal=0.8, coat=0.0)
    white = C.pbr('shield', (0.85, 0.85, 0.82), rough=0.35, coat=0.4)
    o = [C.rcyl(0.035, h, (0, 0, h / 2), pole, verts=12, r=0.0)]
    o.append(C.rcyl(0.025, 0.7, (0, 0, h + 0.02), pole, rot=(0, 90, 0), verts=8, r=0.0))
    for k in range(3):   # anemometer cups
        a = math.radians(k * 120); bpy.ops.mesh.primitive_uv_sphere_add(radius=0.05, location=(0.33 + 0.12 * math.cos(a), 0.12 * math.sin(a), h + 0.1))
        c = bpy.context.object; c.scale.z = 0.6; C.assign(c, white); C.no_ink(c); o.append(c)
    o.append(C.rcyl(0.012, 0.12, (0.33, 0, h + 0.05), pole, verts=6, r=0.0))
    o.append(C.rbox((0.35, 0.02, 0.15), (-0.45, 0, h + 0.12), C.pbr('vane', lin('#e8613c'), rough=0.4, coat=0.4), r=0.01))
    for k in range(4): o.append(C.rcyl(0.09 - k * 0.004, 0.035, (0.0, -0.13, h * 0.55 + k * 0.05), white, verts=16, r=0.01))
    sp = C.rbox((0.5, 0.35, 0.02), (0, 0.22, h * 0.72), C.pbr('solar', (0.02, 0.04, 0.12), rough=0.15, coat=0.8), r=0.008); sp.rotation_euler.x = math.radians(-40); o.append(sp)
    o.append(C.rbox((0.24, 0.12, 0.3), (0, 0.1, 1.0), white, r=0.03))
    for k in range(3):   # guy wires
        a = math.radians(30 + k * 120); gx, gy = 1.4 * math.cos(a), 1.4 * math.sin(a)
        L = math.sqrt(1.4 ** 2 + (h * 0.8) ** 2); w = C.rcyl(0.004, L, (gx / 2, gy / 2, h * 0.4), pole, verts=4, r=0.0)
        w.rotation_euler = Vector((-gx, -gy, h * 0.8)).normalized().to_track_quat('Z', 'Y').to_euler(); o.append(w)
    o.append(C.contact_blob((0, 0, 0), 0.6, 0.6))
    return group(o, loc, rz)

def folding_chair(loc=(0, 0, 0), rz=0, col='#2fb3c9'):
    """Camp chair: a fabric sling seat and back on gold-tone aluminium X legs, a cup holder."""
    fab = C.pbr('chair_' + col, lin(col), rough=0.6, coat=0.1, bevel=0.01, sheen=0.4)
    al = C.pbr('chair_al', (0.55, 0.55, 0.58), rough=0.3, metal=0.9, coat=0.0)
    o = [C.rbox((0.5, 0.45, 0.06), (0, 0, 0.45), fab, r=0.025)]
    b = C.rbox((0.5, 0.05, 0.5), (0, 0.24, 0.75), fab, r=0.025); b.rotation_euler.x = math.radians(-12); o.append(b)
    for sx in (-0.25, 0.25):
        for a in (25, -25):
            l = C.rcyl(0.014, 0.6, (sx, 0, 0.24), al, rot=(a, 0, 0), verts=8, r=0.0); o.append(l)
        o.append(C.rcyl(0.014, 0.45, (sx, 0.0, 0.62), al, rot=(90, 0, 0), verts=8, r=0.0))   # arm rests
    o.append(C.rcyl(0.04, 0.06, (0.31, -0.15, 0.63), fab, verts=12, r=0.005))
    o.append(C.contact_blob((0, 0, 0), 0.9, 0.9))
    return group(o, loc, rz)

def cooler(loc=(0, 0, 0), rz=0, col='#3a8fd1'):
    o = [C.rbox((0.62, 0.42, 0.40), (0, 0, 0.2), C.pbr('cooler_' + col, lin(col), rough=0.3, coat=0.6), r=0.06)]
    o.append(C.rbox((0.66, 0.46, 0.07), (0, 0, 0.42), C.pbr('cooler_lid', (0.85, 0.85, 0.82), rough=0.3, coat=0.6), r=0.03))
    o.append(C.rbox((0.3, 0.05, 0.04), (0, -0.24, 0.32), C.gold('cooler_gold'), r=0.015))
    o.append(C.contact_blob((0, 0, 0), 0.9, 0.7))
    return group(o, loc, rz)

def lantern(loc=(0, 0, 0), on=True):
    """Camp lantern: a gold cage with a warm glass globe (warm practical at night)."""
    glow = C.emissive(C.pbr('lantern_glass', (1.0, 0.62, 0.25), rough=0.1, coat=0.0, bevel=0.0, emit=0.2), (1.0, 0.55, 0.2), 0.25)
    o = [C.rcyl(0.09, 0.03, (0, 0, 0.015), C.gold('lantern_gold'), verts=16, r=0.005)]
    o.append(C.rcyl(0.07, 0.18, (0, 0, 0.12), glow, verts=16, r=0.01))
    o.append(C.rcyl(0.08, 0.03, (0, 0, 0.225), C.gold('lantern_gold'), verts=16, r=0.005))
    bpy.ops.mesh.primitive_torus_add(major_radius=0.06, minor_radius=0.008, location=(0, 0, 0.28), rotation=(math.radians(90), 0, 0))
    t = bpy.context.object; C.assign(t, C.gold('lantern_gold')); C.no_ink(t); o.append(t)
    g = group(o, loc, 0)
    C.point((loc[0], loc[1], loc[2] + 0.2), (1.0, 0.58, 0.25), power=60, radius=0.08)
    return g

def sign_posts(text, loc, rz=0, w=2.4, h=1.1, style='plank', post_h=2.4):
    """A hand-painted sign board on two wooden posts (common.sign), board centre at post_h - h/2."""
    wood = C.pbr('post_wood', lin('#6b4a2e'), rough=0.6, coat=0.2, bevel=0.01, noise=0.3, noise_scale=12)
    a = math.radians(rz); ox, oy = math.cos(a), math.sin(a)
    posts = [C.rbox((0.12, 0.12, post_h), (loc[0] + ox * s * (w / 2 - 0.15), loc[1] + oy * s * (w / 2 - 0.15), post_h / 2), wood, r=0.02, rz=rz) for s in (-1, 1)]
    cz = post_h - h / 2 - 0.05
    b = C.sign(text, style, loc=(loc[0] - math.sin(a) * 0.09, loc[1] + math.cos(a) * -0.09, cz), rz=rz, w=w, h=h)
    face = bpy.context.object   # common.sign adds the textured face last
    return [b, face], posts, (loc[0] - math.sin(a) * 0.15, loc[1] - math.cos(a) * 0.15, cz)

def alien_cutout(loc, rz=0, h=1.9):
    """Plywood alien cut-out on a stake: a painted flat figure (big head, almond eyes, raised hand) with plywood edges."""
    from PIL import Image, ImageDraw
    W_, H_ = 512, 1024; im = Image.new('RGBA', (W_, H_), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    ink = (36, 23, 38, 255); g = (111, 209, 106, 255); ply = (214, 170, 110, 255); lw = 14
    d.ellipse([86, 470, 426, 1000], fill=ply)                              # plywood edge rim (slightly bigger)
    d.ellipse([96, 480, 416, 990], fill=g, outline=ink, width=lw)          # body
    d.line([(400, 600), (480, 380)], fill=ink, width=40); d.line([(400, 600), (480, 380)], fill=g, width=22)   # waving arm
    d.ellipse([440, 330, 510, 400], fill=g, outline=ink, width=10)
    d.ellipse([40, 40, 472, 560], fill=ply); d.ellipse([50, 50, 462, 550], fill=g, outline=ink, width=lw)    # head
    for cx in (170, 342):
        d.ellipse([cx - 70, 250, cx + 70, 360], fill=ink); d.ellipse([cx - 40, 268, cx - 12, 296], fill=(240, 240, 240, 255))
    d.arc([200, 380, 312, 470], 20, 160, fill=ink, width=12)
    d.rectangle([150, 830, 362, 930], fill=(246, 212, 154, 255), outline=ink, width=8)
    from PIL import ImageFont
    f = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 50); bb = d.textbbox((0, 0), 'HI!', font=f)
    d.text((256 - bb[2] / 2, 880 - bb[3] / 2 - 4), 'HI!', font=f, fill=ink)
    dd = os.path.join(bpy.app.tempdir or '/tmp', 'decals'); os.makedirs(dd, exist_ok=True); p = os.path.join(dd, 'alien_cut.png'); im.save(p)
    m = bpy.data.materials.new('alien_cut'); m.use_nodes = True; n = m.node_tree.nodes; l = m.node_tree.links; P = n['Principled BSDF']
    t = n.new('ShaderNodeTexImage'); t.image = bpy.data.images.load(p); t.image.pack()
    l.new(t.outputs['Color'], P.inputs['Base Color']); l.new(t.outputs['Alpha'], P.inputs['Alpha']); P.inputs['Roughness'].default_value = 0.5
    P.inputs['Coat Weight'].default_value = 0.3
    a = math.radians(rz)
    bpy.ops.mesh.primitive_plane_add(size=1, location=(loc[0], loc[1], h / 2 + 0.15), rotation=(math.radians(90), 0, a)); o = bpy.context.object
    o.scale = (h / 2, h, 1); C.assign(o, m); C.no_ink(o)
    sol = o.modifiers.new('thick', 'SOLIDIFY'); sol.thickness = 0.03
    stake = C.rbox((0.06, 0.06, 0.6), (loc[0] + math.sin(a) * 0.05, loc[1] - math.cos(a) * -0.05, 0.3), C.pbr('post_wood', lin('#6b4a2e')), r=0.01)
    return o

def gravel_mat():
    m = bpy.data.materials.new('gravel'); m.use_nodes = True; n = m.node_tree.nodes; l = m.node_tree.links; P = n['Principled BSDF']
    P.inputs['Roughness'].default_value = 0.8
    tc = n.new('ShaderNodeTexCoord'); v = n.new('ShaderNodeTexVoronoi'); v.inputs['Scale'].default_value = 22; l.new(tc.outputs['Object'], v.inputs['Vector'])
    r = n.new('ShaderNodeValToRGB'); e = r.color_ramp.elements; e[0].color = (0.16, 0.13, 0.12, 1); e[1].color = (0.40, 0.33, 0.27, 1)
    l.new(v.outputs['Color'], r.inputs['Fac']); l.new(r.outputs['Color'], P.inputs['Base Color'])
    v2 = n.new('ShaderNodeTexVoronoi'); v2.feature = 'DISTANCE_TO_EDGE'; v2.inputs['Scale'].default_value = 22; l.new(tc.outputs['Object'], v2.inputs['Vector'])
    b = n.new('ShaderNodeBump'); b.inputs['Strength'].default_value = 0.6; l.new(v2.outputs['Distance'], b.inputs['Height']); l.new(b.outputs['Normal'], P.inputs['Normal'])
    return m
