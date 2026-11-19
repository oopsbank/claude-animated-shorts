# Shared set-building code: import helpers, stylised materials, sky + light presets, Freestyle ink,
# render settings, a depth-haze pass, warm-only glow post, and the plate JSON writer.
# A set's build.py builds its geometry once, then calls main(set_name, CAMS, LIGHTS) to render every cam x light.
#   python blender/sets/<set>/build.py [--cams a,b] [--lights day,night] [--pct 25] [--samples 24] [--out DIR]
import bpy, sys, os, math, json, time, colorsys, argparse
import numpy as np
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view
from PIL import Image, ImageFilter

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))
PACKS = os.environ.get('PACKS', os.path.join(ROOT, 'packs'))
QUAT = os.path.join(PACKS, 'quaternius-showcase/public/glb')
KAY_MED = os.path.join(PACKS, 'KayKit-Medieval-Hexagon-Pack-1.0/addons/kaykit_medieval_hexagon_pack/Assets/gltf')
KAY_CITY = os.path.join(PACKS, 'KayKit-City-Builder-Bits-1.0/addons/kaykit_city_builder_bits/Assets/gltf')
W, H = 1080, 1920
HERO_M = 1.75           # character height in metres
SPRITE_PX = 975 - 59    # stickman sprite: head top y=59, soles y=975 on the 600x1000 card

def sc(): return bpy.context.scene

def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    for name in ('noink', 'lights'):
        c = bpy.data.collections.new(name); sc().collection.children.link(c)

# ---------------------------------------------------------------- import
def imp(path, loc=(0, 0, 0), rz=0, s=1.0, rx=0, ink=True):
    before = set(bpy.data.objects)
    if path.endswith(('.glb', '.gltf')): bpy.ops.import_scene.gltf(filepath=path)
    new = [o for o in bpy.data.objects if o not in before]
    root = bpy.data.objects.new(os.path.basename(path), None); sc().collection.objects.link(root)
    for o in new:
        if o.parent is None: o.parent = root
    root.location = loc; root.rotation_euler = (math.radians(rx), 0, math.radians(rz))
    root.scale = (s,) * 3 if not isinstance(s, (tuple, list)) else s
    if not ink:
        for o in new: no_ink(o)
    return root

def imp_h(path, height, loc=(0, 0, 0), rz=0, **kw):
    """Import and scale uniformly so the model is `height` metres tall, standing on loc."""
    r = imp(path, (0, 0, 0), rz, 1.0, **kw); mn, mx = dims(r); k = height / max(1e-6, mx.z - mn.z)
    r.scale = (k,) * 3; r.location = (loc[0], loc[1], loc[2] - mn.z * k); return r

def dims(root):
    """World-space bounding box (min, max) of an imported hierarchy (for scaling packs to metres)."""
    bpy.context.view_layer.update()
    pts = [o.matrix_world @ Vector(c) for o in [root] + list(root.children_recursive) if o.type == 'MESH' for c in o.bound_box]
    mn = Vector([min(p[i] for p in pts) for i in range(3)]); mx = Vector([max(p[i] for p in pts) for i in range(3)])
    return mn, mx

def no_ink(o):
    """Move an object (ground, water, sky dome, glow cards) out of the Freestyle lineset."""
    for c in list(o.users_collection): c.objects.unlink(o)
    bpy.data.collections['noink'].objects.link(o)

# ---------------------------------------------------------------- materials
def mat(name, col, emit=0.0, rough=0.7, metal=0.0):
    m = bpy.data.materials.new(name); m.use_nodes = True; p = m.node_tree.nodes['Principled BSDF']
    p.inputs['Base Color'].default_value = (*col, 1); p.inputs['Roughness'].default_value = rough
    p.inputs['Metallic'].default_value = metal
    if emit: p.inputs['Emission Color'].default_value = (*col, 1); p.inputs['Emission Strength'].default_value = emit
    return m

def assign(o, m):
    o.data.materials.clear(); o.data.materials.append(m); return o

EMISSIVE = {}   # material name -> (colour, strength at night); scaled by the light preset's `emit`

def emissive(m, col, strength):
    EMISSIVE[m.name] = (col, strength); return m

def stylise(sat=1.18, val=1.12, rough=0.85, emissive_prefixes=('Windows',), emit_col=(1.0, 0.62, 0.25), emit_strength=5.0):
    """Flat toon-ish look for the packs: high roughness, saturation boost; window materials become practicals."""
    for m in bpy.data.materials:
        if not m.use_nodes or m.name in EMISSIVE: continue
        P = next((x for x in m.node_tree.nodes if x.type == 'BSDF_PRINCIPLED'), None)
        if not P: continue
        P.inputs['Roughness'].default_value = max(P.inputs['Roughness'].default_value, rough) if P.inputs['Metallic'].default_value < 0.5 else 0.5
        P.inputs['Specular IOR Level'].default_value = 0.25
        if m.name.startswith(emissive_prefixes):
            emissive(m, emit_col, emit_strength); continue
        if not P.inputs['Base Color'].is_linked:
            c = P.inputs['Base Color'].default_value
            h, s_, v = colorsys.rgb_to_hsv(c[0], c[1], c[2])
            r, g, b = colorsys.hsv_to_rgb(h, min(1, s_ * sat), min(1, v * val))
            P.inputs['Base Color'].default_value = (r, g, b, 1)

def set_emissives(k):
    for name, (col, s) in EMISSIVE.items():
        m = bpy.data.materials.get(name)
        P = next((x for x in m.node_tree.nodes if x.type == 'BSDF_PRINCIPLED'), None)
        P.inputs['Emission Color'].default_value = (*col, 1); P.inputs['Emission Strength'].default_value = s * k

def cobble_mat(scale=3.6, c0=(0.30, 0.22, 0.16), c1=(0.42, 0.32, 0.22)):
    m = bpy.data.materials.new('cobble'); m.use_nodes = True
    n = m.node_tree.nodes; l = m.node_tree.links; P = n['Principled BSDF']; P.inputs['Roughness'].default_value = 0.7
    tc = n.new('ShaderNodeTexCoord')
    vor = n.new('ShaderNodeTexVoronoi'); vor.feature = 'DISTANCE_TO_EDGE'; vor.inputs['Scale'].default_value = scale
    vor2 = n.new('ShaderNodeTexVoronoi'); vor2.inputs['Scale'].default_value = scale
    l.new(tc.outputs['Object'], vor.inputs['Vector']); l.new(tc.outputs['Object'], vor2.inputs['Vector'])
    rmp = n.new('ShaderNodeValToRGB'); rmp.color_ramp.elements[0].position = 0.02; rmp.color_ramp.elements[1].position = 0.06
    rmp.color_ramp.elements[0].color = (0.30, 0.24, 0.24, 1); rmp.color_ramp.elements[1].color = (1, 1, 1, 1)
    l.new(vor.outputs['Distance'], rmp.inputs['Fac'])
    tint = n.new('ShaderNodeValToRGB')
    tint.color_ramp.elements[0].color = (*c0, 1); tint.color_ramp.elements[1].color = (*c1, 1)
    l.new(vor2.outputs['Color'], tint.inputs['Fac'])
    mul = n.new('ShaderNodeMixRGB'); mul.blend_type = 'MULTIPLY'; mul.inputs['Fac'].default_value = 1
    l.new(tint.outputs['Color'], mul.inputs['Color1']); l.new(rmp.outputs['Color'], mul.inputs['Color2'])
    l.new(mul.outputs['Color'], P.inputs['Base Color'])
    bmp = n.new('ShaderNodeBump'); bmp.inputs['Strength'].default_value = 0.4
    l.new(rmp.outputs['Color'], bmp.inputs['Height']); l.new(bmp.outputs['Normal'], P.inputs['Normal'])
    return m

def plank_mat(c0=(0.36, 0.20, 0.09), c1=(0.52, 0.31, 0.14), width=0.25, axis='X'):
    """Stylised deck / pier boards: flat colour stripes with dark seams."""
    m = bpy.data.materials.new('planks'); m.use_nodes = True
    n = m.node_tree.nodes; l = m.node_tree.links; P = n['Principled BSDF']; P.inputs['Roughness'].default_value = 0.8
    tc = n.new('ShaderNodeTexCoord'); sep = n.new('ShaderNodeSeparateXYZ'); l.new(tc.outputs['Object'], sep.inputs['Vector'])
    k = 'Y' if axis == 'X' else 'X'   # boards run along `axis`, stripes across the other one
    mt = n.new('ShaderNodeMath'); mt.operation = 'DIVIDE'; mt.inputs[1].default_value = width; l.new(sep.outputs[k], mt.inputs[0])
    fr = n.new('ShaderNodeMath'); fr.operation = 'FRACT'; l.new(mt.outputs[0], fr.inputs[0])
    fl = n.new('ShaderNodeMath'); fl.operation = 'FLOOR'; l.new(mt.outputs[0], fl.inputs[0])
    wn = n.new('ShaderNodeTexWhiteNoise'); wn.noise_dimensions = '1D'; l.new(fl.outputs[0], wn.inputs['W'])
    tint = n.new('ShaderNodeValToRGB'); tint.color_ramp.elements[0].color = (*c0, 1); tint.color_ramp.elements[1].color = (*c1, 1)
    l.new(wn.outputs['Value'], tint.inputs['Fac'])
    seam = n.new('ShaderNodeValToRGB'); e = seam.color_ramp.elements
    e[0].position = 0.0; e[0].color = (0.12, 0.08, 0.06, 1); e[1].position = 0.06; e[1].color = (1, 1, 1, 1)
    l.new(fr.outputs[0], seam.inputs['Fac'])
    mul = n.new('ShaderNodeMixRGB'); mul.blend_type = 'MULTIPLY'; mul.inputs['Fac'].default_value = 1
    l.new(tint.outputs['Color'], mul.inputs['Color1']); l.new(seam.outputs['Color'], mul.inputs['Color2'])
    l.new(mul.outputs['Color'], P.inputs['Base Color'])
    return m

def water_mat(deep=(0.02, 0.16, 0.38), shallow=(0.05, 0.42, 0.62), scale=1.0):
    """Stylised water: two-tone by facing, glossy, wave bump; reads as cartoon sea at a distance."""
    m = bpy.data.materials.new('water'); m.use_nodes = True
    n = m.node_tree.nodes; l = m.node_tree.links; P = n['Principled BSDF']
    P.inputs['Roughness'].default_value = 0.12; P.inputs['Specular IOR Level'].default_value = 0.6
    lw = n.new('ShaderNodeLayerWeight'); lw.inputs['Blend'].default_value = 0.35
    ramp = n.new('ShaderNodeValToRGB'); ramp.color_ramp.elements[0].color = (*shallow, 1); ramp.color_ramp.elements[1].color = (*deep, 1)
    l.new(lw.outputs['Facing'], ramp.inputs['Fac'])
    tc = n.new('ShaderNodeTexCoord')
    wv = n.new('ShaderNodeTexNoise'); wv.inputs['Scale'].default_value = 1.4 * scale; wv.inputs['Detail'].default_value = 3
    l.new(tc.outputs['Object'], wv.inputs['Vector'])
    foam = n.new('ShaderNodeValToRGB'); e = foam.color_ramp.elements
    e[0].position = 0.66; e[0].color = (0, 0, 0, 1); e[1].position = 0.70; e[1].color = (1, 1, 1, 1)
    l.new(wv.outputs['Fac'], foam.inputs['Fac'])
    mix = n.new('ShaderNodeMixRGB'); mix.inputs['Color2'].default_value = (0.55, 0.78, 0.9, 1)
    l.new(ramp.outputs['Color'], mix.inputs['Color1']); l.new(foam.outputs['Color'], mix.inputs['Fac'])
    l.new(mix.outputs['Color'], P.inputs['Base Color'])
    bmp = n.new('ShaderNodeBump'); bmp.inputs['Strength'].default_value = 0.35; bmp.inputs['Distance'].default_value = 0.3
    l.new(wv.outputs['Fac'], bmp.inputs['Height']); l.new(bmp.outputs['Normal'], P.inputs['Normal'])
    return m

def plane(size, loc=(0, 0, 0), m=None, ink=False, sx=1, sy=1):
    bpy.ops.mesh.primitive_plane_add(size=size, location=loc); o = bpy.context.object
    o.scale = (sx, sy, 1)
    if m: assign(o, m)
    if not ink: no_ink(o)
    return o

def box(size, loc, m, rz=0, ink=True):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc, rotation=(0, 0, math.radians(rz))); o = bpy.context.object
    o.scale = size; assign(o, m)
    if not ink: no_ink(o)
    return o

def cyl(r, depth, loc, m, rot=(0, 0, 0), verts=12):
    bpy.ops.mesh.primitive_cylinder_add(vertices=verts, radius=r, depth=depth, location=loc,
                                        rotation=tuple(math.radians(a) for a in rot))
    o = bpy.context.object; assign(o, m); return o

# ---------------------------------------------------------------- signage
FONTS = ['/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', '/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf',
         '/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf']
SIGN_STYLES = {   # background, text colour, border colour, font index, emissive
    'plank':  ((128, 78, 40), (250, 236, 200), (60, 34, 18), 1, 0.0),
    'banner': ((196, 46, 46), (255, 246, 226), (120, 20, 24), 0, 0.0),
    'poster': ((246, 232, 196), (52, 30, 34), (120, 70, 40), 1, 0.0),
    'screen': ((16, 28, 40), (120, 255, 190), (40, 44, 52), 0, 2.5),
    'chalk':  ((34, 58, 44), (240, 240, 228), (120, 78, 40), 0, 0.0),
    'board':  ((24, 24, 30), (255, 214, 64), (200, 200, 205), 0, 0.0),
}

def _font(i, size):
    from PIL import ImageFont
    for f in [FONTS[i]] + FONTS:
        if os.path.exists(f): return ImageFont.truetype(f, size)
    return ImageFont.load_default()

def sign(text, style='plank', loc=(0, 0, 2), rz=0, w=2.0, h=0.7, depth=0.06, tex_dir=None, draw=None, text_frac=1.0):
    """Readable custom signage for story jokes: text painted on a plank, banner, poster or screen. Returns the object.
    Text may contain newlines; it is fitted to the board. The board is inked; the face is a textured plane.
    draw(ImageDraw, (x0, y0, x1, y1), fg) adds a drawing under the text, which then takes the top `text_frac` of the board."""
    from PIL import ImageDraw
    bg, fg, bd, fi, em = SIGN_STYLES[style]
    px = 128; Wt, Ht = int(w * px * 2), int(h * px * 2)
    im = Image.new('RGB', (Wt, Ht), bg); d = ImageDraw.Draw(im)
    if style == 'plank':
        for y in range(0, Ht, max(8, Ht // 4)): d.line([(0, y), (Wt, y)], fill=bd, width=max(2, Ht // 60))
    b = max(4, Ht // 14); d.rectangle([b // 2, b // 2, Wt - b // 2, Ht - b // 2], outline=bd, width=b)
    lines = text.split('\n'); size = Ht
    while size > 8:
        f = _font(fi, size); bbs = [d.textbbox((0, 0), ln, font=f) for ln in lines]
        tw = max(bb[2] - bb[0] for bb in bbs); th = sum(bb[3] - bb[1] for bb in bbs) * 1.25
        if tw < Wt * 0.86 and th < Ht * 0.78 * text_frac: break
        size = int(size * 0.92)
    y = (Ht * text_frac - th) / 2 + (b if text_frac < 1 else 0)
    for ln, bb in zip(lines, bbs):
        d.text(((Wt - (bb[2] - bb[0])) / 2 - bb[0], y - bb[1]), ln, font=f, fill=fg); y += (bb[3] - bb[1]) * 1.25
    if draw: draw(d, (b * 2, int(Ht * text_frac), Wt - b * 2, Ht - b * 2), fg)
    tex_dir = tex_dir or os.path.join(bpy.app.tempdir or '/tmp', 'signs'); os.makedirs(tex_dir, exist_ok=True)
    import hashlib
    path = os.path.join(tex_dir, 'sign_' + hashlib.md5((text + style).encode()).hexdigest()[:10] + '.png'); im.save(path)
    m = bpy.data.materials.new('sign_' + style); m.use_nodes = True; n = m.node_tree.nodes; P = n['Principled BSDF']
    t = n.new('ShaderNodeTexImage'); t.image = bpy.data.images.load(path); t.image.pack()
    m.node_tree.links.new(t.outputs['Color'], P.inputs['Base Color']); P.inputs['Roughness'].default_value = 0.8
    if em:
        m.node_tree.links.new(t.outputs['Color'], P.inputs['Emission Color']); P.inputs['Emission Strength'].default_value = em
    board = box((w, depth, h), loc, mat('signboard', tuple(c / 255 * 0.5 for c in bd)), rz=rz)
    bpy.ops.mesh.primitive_plane_add(size=1); face = bpy.context.object; assign(face, m)   # face sits on the -Y side
    face.location = Vector(loc) + Vector((math.sin(math.radians(rz)) * (depth / 2 + 0.005), -math.cos(math.radians(rz)) * (depth / 2 + 0.005), 0))
    face.rotation_euler = (math.radians(90), 0, math.radians(rz)); face.scale = (w * 0.999, h * 0.999, 1)
    no_ink(face)
    return board

# ---------------------------------------------------------------- lights
PRACTICALS = []   # (light object, power at night)

def point(loc, color=(1.0, 0.62, 0.30), power=500, radius=0.3):
    ld = bpy.data.lights.new('pt', 'POINT'); ld.color = color; ld.energy = power; ld.shadow_soft_size = max(radius, 0.15)
    o = bpy.data.objects.new('pt', ld); bpy.data.collections['lights'].objects.link(o); o.location = loc
    PRACTICALS.append((o, power)); return o

def lamp_post(x, y, h=3.4, glow_col=(1.0, 0.50, 0.15), power=650):
    """Simple stylised iron street lamp with a warm practical."""
    iron = bpy.data.materials.get('iron') or mat('iron', (0.04, 0.04, 0.06), rough=0.6)
    glow = bpy.data.materials.get('lampglow') or emissive(mat('lampglow', glow_col, 2.2), glow_col, 2.2)
    cyl(0.07, h, (x, y, h / 2), iron); cyl(0.16, 0.25, (x, y, 0.12), iron)
    bpy.ops.mesh.primitive_cube_add(size=0.34, location=(x, y, h + 0.15)); assign(bpy.context.object, glow)
    bpy.ops.mesh.primitive_cone_add(vertices=4, radius1=0.33, depth=0.28, location=(x, y, h + 0.46),
                                    rotation=(0, 0, math.radians(45))); assign(bpy.context.object, iron)
    return point((x, y, h + 0.05), (1.0, 0.62, 0.30), power, 0.15)

# Light presets. Colours are linear. `sky` = gradient stops (z of view dir, colour); `amb` = what the sky lights the
# scene with (separate from what the camera sees, so a bright painted sky doesn't flatten the set).
PRESETS = {
    'day': dict(sun=(1.0, 0.95, 0.86), sun_e=4.2, elev=50, amb=(0.60, 0.70, 1.0), amb_e=0.6,
                fill=(0.80, 0.86, 1.0), fill_e=260, prac=0.0, emit=0.15, exposure=0.35,
                sky=[(0.0, (0.80, 0.88, 1.0)), (0.18, (0.45, 0.66, 0.98)), (0.55, (0.22, 0.48, 0.93))],
                stars=0, clouds=(1.0, 1.0, 1.0), cloud_amt=0.55,
                haze=(0.72, 0.84, 1.0), haze_k=0.55, tint='#fff4e4'),
    'golden': dict(sun=(1.0, 0.58, 0.26), sun_e=6.5, elev=13, amb=(0.60, 0.55, 0.85), amb_e=0.5,
                   fill=(0.70, 0.66, 1.0), fill_e=260, prac=0.5, emit=0.6, exposure=0.6,
                   sky=[(0.0, (1.0, 0.72, 0.38)), (0.08, (1.0, 0.55, 0.36)), (0.22, (0.62, 0.42, 0.62)), (0.55, (0.26, 0.30, 0.62))],
                   stars=0, clouds=(1.0, 0.55, 0.40), cloud_amt=0.45,
                   haze=(1.0, 0.62, 0.42), haze_k=0.4, tint='#ffbf86'),
    'night': dict(sun=(0.62, 0.70, 1.0), sun_e=1.6, elev=55, amb=(0.32, 0.36, 0.62), amb_e=0.45,
                  fill=(0.75, 0.72, 1.0), fill_e=150, prac=3.5, emit=5.0, exposure=0.6,
                  sky=[(0.0, (0.36, 0.34, 0.58)), (0.12, (0.13, 0.15, 0.36)), (0.45, (0.04, 0.06, 0.18))],
                  stars=3.0, clouds=None, cloud_amt=0,
                  haze=(0.16, 0.18, 0.36), haze_k=0.45, tint='#a9b0e6'),
    'storm': dict(sun=(0.62, 0.72, 0.90), sun_e=1.6, elev=40, amb=(0.40, 0.48, 0.62), amb_e=0.55,
                  fill=(0.60, 0.66, 0.85), fill_e=500, prac=1.2, emit=1.0, exposure=0.6,
                  sky=[(0.0, (0.30, 0.36, 0.44)), (0.12, (0.13, 0.17, 0.26)), (0.5, (0.04, 0.05, 0.10))],
                  stars=0, clouds=(0.30, 0.34, 0.44), cloud_amt=0.9,
                  haze=(0.24, 0.30, 0.40), haze_k=0.75, tint='#9aa8c0'),
}

def _sky(p):
    w = bpy.data.worlds.get('w') or bpy.data.worlds.new('w'); sc().world = w; w.use_nodes = True
    nt = w.node_tree; nt.nodes.clear(); n = nt.nodes; l = nt.links
    out = n.new('ShaderNodeOutputWorld')
    tc = n.new('ShaderNodeTexCoord'); sep = n.new('ShaderNodeSeparateXYZ'); l.new(tc.outputs['Generated'], sep.inputs['Vector'])
    ramp = n.new('ShaderNodeValToRGB'); cr = ramp.color_ramp
    stops = p['sky']
    cr.elements[0].position, cr.elements[0].color = stops[0][0], (*stops[0][1], 1)
    cr.elements[1].position, cr.elements[1].color = stops[-1][0], (*stops[-1][1], 1)
    for pos, col in stops[1:-1]: cr.elements.new(pos).color = (*col, 1)
    l.new(sep.outputs['Z'], ramp.inputs['Fac'])
    col = ramp.outputs['Color']
    if p['clouds']:   # soft painted cloud bands, stretched horizontally, only above the horizon
        mp = n.new('ShaderNodeMapping'); mp.inputs['Scale'].default_value = (1.0, 1.0, 4.5)
        l.new(tc.outputs['Generated'], mp.inputs['Vector'])
        nz = n.new('ShaderNodeTexNoise'); nz.inputs['Scale'].default_value = 2.2; nz.inputs['Detail'].default_value = 2
        nz.inputs['Roughness'].default_value = 0.45; l.new(mp.outputs['Vector'], nz.inputs['Vector'])
        th = n.new('ShaderNodeMapRange'); th.inputs['From Min'].default_value = 0.58 - 0.12 * p['cloud_amt']
        th.inputs['From Max'].default_value = 0.66 - 0.12 * p['cloud_amt']; l.new(nz.outputs['Fac'], th.inputs['Value'])
        hz = n.new('ShaderNodeMapRange'); hz.inputs['From Min'].default_value = 0.02; hz.inputs['From Max'].default_value = 0.12
        l.new(sep.outputs['Z'], hz.inputs['Value'])
        mm = n.new('ShaderNodeMath'); mm.operation = 'MULTIPLY'; l.new(th.outputs['Result'], mm.inputs[0]); l.new(hz.outputs['Result'], mm.inputs[1])
        mm2 = n.new('ShaderNodeMath'); mm2.operation = 'MULTIPLY'; mm2.inputs[1].default_value = 0.85
        l.new(mm.outputs[0], mm2.inputs[0])
        mix = n.new('ShaderNodeMixRGB'); mix.inputs['Color2'].default_value = (*p['clouds'], 1)
        l.new(mm2.outputs[0], mix.inputs['Fac']); l.new(col, mix.inputs['Color1']); col = mix.outputs['Color']
    if p['stars']:
        vw = n.new('ShaderNodeTexVoronoi'); vw.inputs['Scale'].default_value = 140; l.new(tc.outputs['Generated'], vw.inputs['Vector'])
        st = n.new('ShaderNodeMapRange'); st.inputs['From Min'].default_value = 0.035; st.inputs['From Max'].default_value = 0.0
        st.inputs['To Max'].default_value = p['stars']; l.new(vw.outputs['Distance'], st.inputs['Value'])
        hz = n.new('ShaderNodeMapRange'); hz.inputs['From Min'].default_value = 0.08; hz.inputs['From Max'].default_value = 0.25
        l.new(sep.outputs['Z'], hz.inputs['Value'])
        mm = n.new('ShaderNodeMath'); mm.operation = 'MULTIPLY'; l.new(st.outputs['Result'], mm.inputs[0]); l.new(hz.outputs['Result'], mm.inputs[1])
        add = n.new('ShaderNodeMixRGB'); add.blend_type = 'ADD'; add.inputs['Color2'].default_value = (0.9, 0.95, 1.0, 1)
        l.new(mm.outputs[0], add.inputs['Fac']); l.new(col, add.inputs['Color1']); col = add.outputs['Color']
    bg_cam = n.new('ShaderNodeBackground'); l.new(col, bg_cam.inputs['Color'])
    bg_cam.inputs['Strength'].default_value = p.get('sky_e', 1.0)
    bg_amb = n.new('ShaderNodeBackground'); bg_amb.inputs['Color'].default_value = (*p['amb'], 1)
    bg_amb.inputs['Strength'].default_value = p['amb_e']
    lp = n.new('ShaderNodeLightPath'); mx = n.new('ShaderNodeMixShader')
    l.new(lp.outputs['Is Camera Ray'], mx.inputs['Fac']); l.new(bg_amb.outputs[0], mx.inputs[1]); l.new(bg_cam.outputs[0], mx.inputs[2])
    l.new(mx.outputs[0], out.inputs['Surface'])

def apply_light(name, cam_obj, overrides=None):
    p = dict(PRESETS[name]); p.update(overrides or {})
    for o in list(bpy.data.collections['lights'].objects):
        if o.get('preset'): bpy.data.objects.remove(o)
    sun = bpy.data.lights.new('sun', 'SUN'); sun.color = p['sun']; sun.energy = p['sun_e']; sun.angle = math.radians(p.get('sun_soft', 6))
    so = bpy.data.objects.new('sun', sun); bpy.data.collections['lights'].objects.link(so); so['preset'] = 1
    so.rotation_euler = (math.radians(90 - p['elev']), 0, math.radians(p.get('az', 210)))
    if p['fill_e']:   # soft camera-side fill so facades never go black at night
        f = bpy.data.lights.new('fill', 'AREA'); f.color = p['fill']; f.energy = p['fill_e']; f.size = 14
        fo = bpy.data.objects.new('fill', f); bpy.data.collections['lights'].objects.link(fo); fo['preset'] = 1
        fwd = cam_obj.matrix_world.to_3x3() @ Vector((0, 0, -1)); fwd.z = 0; fwd.normalize()
        fo.location = cam_obj.location - fwd * 8 + Vector((2.5, 0, 6))
        fo.rotation_euler = (cam_obj.location + fwd * 12 - fo.location).to_track_quat('-Z', 'Y').to_euler()
        fo.data.energy = p['fill_e'] * p.get('fill_k', 1.0)
    for o, pw in PRACTICALS: o.data.energy = pw * p['prac']; o.hide_render = p['prac'] <= 0
    set_emissives(p['emit'])
    _sky(p)
    sc().view_settings.exposure = p['exposure']
    return p, so

# ---------------------------------------------------------------- camera + ink + render
def camera(loc, target, lens=27, roll=0.0):
    cam = bpy.data.cameras.get('cam') or bpy.data.cameras.new('cam')
    co = bpy.data.objects.get('cam') or bpy.data.objects.new('cam', cam)
    if co.name not in sc().collection.objects: sc().collection.objects.link(co)
    sc().camera = co; cam.lens = lens; cam.sensor_fit = 'AUTO'; cam.sensor_width = 36
    co.location = loc
    if target is None: co.rotation_euler = (0, 0, math.radians(roll))   # straight down, image-up = +Y rotated by roll
    else:
        co.rotation_euler = (Vector(target) - Vector(loc)).to_track_quat('-Z', 'Y').to_euler()
        co.rotation_euler.y += math.radians(roll)
    cam.clip_start = 0.05; cam.clip_end = 600
    return co

def ink(pct=100, fade=(14, 40, 0.5), thick=3.4, color=(0.018, 0.009, 0.020)):   # linear plum #241726
    s = sc(); s.render.use_freestyle = True; s.render.line_thickness_mode = 'ABSOLUTE'
    vl = s.view_layers[0]; vl.use_freestyle = True
    fs = vl.freestyle_settings; fs.crease_angle = math.radians(140)
    ls = fs.linesets[0] if len(fs.linesets) else fs.linesets.new('ink')
    ls.select_by_visibility = True; ls.select_by_edge_types = True
    ls.select_silhouette = True; ls.select_border = False; ls.select_crease = True; ls.select_external_contour = True
    ls.select_by_collection = True; ls.collection = bpy.data.collections['noink']; ls.collection_negation = 'EXCLUSIVE'
    lst = ls.linestyle or bpy.data.linestyles.new('ink'); ls.linestyle = lst
    for m in list(lst.thickness_modifiers): lst.thickness_modifiers.remove(m)
    for m in list(lst.alpha_modifiers): lst.alpha_modifiers.remove(m)
    lst.color = color; lst.alpha = 1.0; lst.thickness = thick * (W * pct / 100) / 1080
    md = lst.thickness_modifiers.new('dist', 'DISTANCE_FROM_CAMERA')
    md.range_min = 3; md.range_max = 30; md.value_min = 1.0; md.value_max = 0.45; md.blend = 'MULTIPLY'
    am = lst.alpha_modifiers.new('fade', 'DISTANCE_FROM_CAMERA')
    am.range_min, am.range_max, am.influence = fade; am.mapping = 'LINEAR'; am.invert = True; am.blend = 'MULTIPLY'

def render_settings(samples=24, pct=100):
    s = sc(); r = s.render; r.engine = 'CYCLES'
    s.cycles.device = 'CPU'; s.cycles.samples = samples; s.cycles.use_denoising = True; s.cycles.max_bounces = 4
    s.cycles.use_adaptive_sampling = True; s.cycles.adaptive_threshold = 0.03
    r.resolution_x, r.resolution_y, r.resolution_percentage = W, H, pct
    s.view_settings.view_transform = 'Khronos PBR Neutral'; s.view_settings.look = 'None'
    r.image_settings.file_format = 'PNG'; r.image_settings.color_mode = 'RGB'; r.film_transparent = False

def _depth_pass(path, near, far):
    """Cheap second render: every surface emits its normalised camera distance (sky = 1). Used for haze in post."""
    s = sc(); vl = s.view_layers[0]
    m = bpy.data.materials.get('_depth')
    if not m:
        m = bpy.data.materials.new('_depth'); m.use_nodes = True; n = m.node_tree.nodes; l = m.node_tree.links; n.clear()
        o = n.new('ShaderNodeOutputMaterial'); e = n.new('ShaderNodeEmission'); cd = n.new('ShaderNodeCameraData')
        mr = n.new('ShaderNodeMapRange'); mr.name = 'mr'
        l.new(cd.outputs['View Distance'], mr.inputs['Value']); l.new(mr.outputs['Result'], e.inputs['Strength'])
        l.new(e.outputs[0], o.inputs['Surface'])
    mr = m.node_tree.nodes['mr']; mr.inputs['From Min'].default_value = near; mr.inputs['From Max'].default_value = far
    world, saved = s.world, {}
    dw = bpy.data.worlds.get('_dw') or bpy.data.worlds.new('_dw'); dw.use_nodes = True
    dw.node_tree.nodes['Background'].inputs['Color'].default_value = (1, 1, 1, 1); dw.node_tree.nodes['Background'].inputs['Strength'].default_value = 1
    saved = dict(samples=s.cycles.samples, fs=s.render.use_freestyle, dof=s.camera.data.dof.use_dof, vt=s.view_settings.view_transform,
                 den=s.cycles.use_denoising, exp=s.view_settings.exposure, path=s.render.filepath)
    s.world = dw; vl.material_override = m; s.cycles.samples = 4; s.render.use_freestyle = False; s.cycles.use_denoising = False
    s.camera.data.dof.use_dof = False; s.view_settings.view_transform = 'Standard'; s.view_settings.exposure = 0
    hidden = [o for o in bpy.data.objects if o.type == 'LIGHT' and not o.hide_render]
    s.render.filepath = path; bpy.ops.render.render(write_still=True)
    s.world = world; vl.material_override = None; s.cycles.samples = saved['samples']; s.render.use_freestyle = saved['fs']
    s.camera.data.dof.use_dof = saved['dof']; s.view_settings.view_transform = saved['vt']; s.cycles.use_denoising = saved['den']
    s.view_settings.exposure = saved['exp']; s.render.filepath = saved['path']

def srgb_to_lin(c): return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)

def post(src, out, depth=None, haze=(0.7, 0.8, 1.0), haze_k=0.5, haze_gamma=1.6):
    """Depth haze toward the preset's haze colour, then warm-only bloom (white faces never glow)."""
    im = Image.open(src).convert('RGB'); a = np.asarray(im).astype(np.float32) / 255
    if depth is not None and haze_k > 0:
        d = np.asarray(Image.open(depth).convert('L')).astype(np.float32) / 255
        hc = np.array([c ** (1 / 2.2) for c in haze], np.float32)   # display-space haze colour
        f = np.clip(d, 0, 1) ** haze_gamma * haze_k
        f = (f * np.clip((0.995 - d) / 0.02, 0, 1))[..., None]   # the painted sky keeps its own colours
        a = a * (1 - f) + hc * f
    lum = a @ np.array([0.2126, 0.7152, 0.0722], np.float32)
    warm = np.clip((a[..., 0] - a[..., 2] - 0.12) / 0.2, 0, 1)
    mask = (np.clip((lum - 0.6) / 0.25, 0, 1) * warm)[..., None]
    hi = Image.fromarray((np.clip(a * mask, 0, 1) * 255).astype(np.uint8))
    glow = np.zeros_like(a)
    for r, w in ((6, 0.5), (18, 0.45), (45, 0.35)):
        glow += np.asarray(hi.filter(ImageFilter.GaussianBlur(r * im.height / 1280))).astype(np.float32) / 255 * w
    o = 1 - (1 - a) * (1 - np.clip(glow, 0, 1))
    Image.fromarray((np.clip(o, 0, 1) * 255).astype(np.uint8)).save(out, optimize=True)

def measure(cam_obj, stand, sun_obj, preset, top=False):
    """Project a 1.75 m marker standing at `stand` through the camera -> ground_y, px_per_m, horizon_y, light_dir."""
    s = sc(); bpy.context.view_layer.update()
    foot = Vector(stand); head = foot + Vector((0, 0, HERO_M))
    pf = world_to_camera_view(s, cam_obj, foot); ph = world_to_camera_view(s, cam_obj, head)
    gy = (1 - pf.y) * H; hy = (1 - ph.y) * H
    fwd = cam_obj.matrix_world.to_3x3() @ Vector((0, 0, -1)); fwd.z = 0; fwd.normalize()
    far = cam_obj.location + fwd * 1e5
    hz = (1 - world_to_camera_view(s, cam_obj, far).y) * H
    if top:   # looking straight down: the marker collapses to a point, so scale from 1 m along the ground
        p1 = world_to_camera_view(s, cam_obj, foot + Vector((1, 0, 0))); hy = gy - abs(p1.x - pf.x) * W * HERO_M
        hz = -1.0
    to_sun = (sun_obj.matrix_world.to_3x3() @ Vector((0, 0, 1))).normalized()
    right = (cam_obj.matrix_world.to_3x3() @ Vector((1, 0, 0))).normalized()
    dx = to_sun.dot(right)
    ld = 'top' if abs(dx) < 0.35 else ('right' if dx > 0 else 'left')
    return {'ground_y': round(gy, 1), 'px_per_m': round((gy - hy) / HERO_M, 2), 'horizon_y': round(hz, 1),
            'light_dir': ld, 'tint': preset['tint'], 'stand_x': round(pf.x, 3)}

def main(set_name, CAMS, LIGHTS, haze_range=(4, 90)):
    """CAMS: name -> dict(loc, target, lens, stand, fstop, roll, ink_fade, light_overrides, setup=callable)
       LIGHTS: name -> dict of preset overrides (az, elev, ...)."""
    ap = argparse.ArgumentParser()
    ap.add_argument('--cams'); ap.add_argument('--lights'); ap.add_argument('--pct', type=int, default=100)
    ap.add_argument('--samples', type=int, default=32); ap.add_argument('--out')
    argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else sys.argv[1:]
    a = ap.parse_args(argv)
    out = a.out or os.path.join(ROOT, 'blender/sets', set_name, 'plates'); os.makedirs(out, exist_ok=True)
    tmp = os.path.join(out, '_tmp'); os.makedirs(tmp, exist_ok=True)
    cams = a.cams.split(',') if a.cams else list(CAMS); lights = a.lights.split(',') if a.lights else list(LIGHTS)
    render_settings(a.samples, a.pct)
    for cn in cams:
        c = CAMS[cn]
        co = camera(c['loc'], c['target'], c.get('lens', 27), c.get('roll', 0))
        if c.get('setup'): c['setup']()
        cam = co.data; cam.dof.use_dof = bool(c.get('fstop'))
        cam.dof.focus_distance = (co.location - (Vector(c['stand']) + Vector((0, 0, 1.2)))).length
        cam.dof.aperture_fstop = c.get('fstop') or 2.0
        ink(a.pct, c.get('ink_fade', (14, 40, 0.5)), c.get('ink_thick', 3.4))
        dpath = os.path.join(tmp, f'{cn}_depth.png')
        _depth_pass(dpath, *c.get('haze_range', haze_range))
        for ln in lights:
            ov = dict(LIGHTS[ln] or {}); ov.update(c.get('light_overrides', {}).get(ln, {}))
            p, sun = apply_light(ln, co, ov)
            if c.get('per_light'): c['per_light'](ln)
            base = f'{set_name}__{cn}__{ln}'
            raw = os.path.join(tmp, base + '_raw.png'); sc().render.filepath = raw
            t = time.time(); bpy.ops.render.render(write_still=True)
            post(raw, os.path.join(out, base + '.png'), dpath, p['haze'], p['haze_k'] * c.get('haze_k', 1.0))
            js = measure(co, c['stand'], sun, p, c.get('top', False)); js.update(set=set_name, cam=cn, light=ln)
            if c.get('top'): js['view'] = 'top'
            if c.get('note'): js['note'] = c['note']
            with open(os.path.join(out, base + '.json'), 'w') as f: json.dump(js, f, indent=1)
            print(f'PLATE {base} {time.time() - t:.0f}s {js}', flush=True)
