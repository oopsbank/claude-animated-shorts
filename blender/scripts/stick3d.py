# 3D stickman for Blender, built from the same skeleton and rules as stickman/scripts/stickman.py
# (see stickman/DRAWING_RULES.md): one flat colour, one merged body (voxel-remeshed, so no seams),
# smooth bent tube limbs with round ends, each arm from its own shoulder, real depth for foreshortened limbs,
# and the 2D face projected onto the front of the head.
import bpy, math, os, sys
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '..', 'stickman', 'scripts'))
import stickman as S2   # noqa: E402

# 2D design units (canvas 600x1000) -> metres
R, T, TB = 98, 50, 56
HIP, SHOULDER = (300, 520), (300, 262)
SEG_ARM, SEG_LEG = 124, 205

def _limb(root, ang, seg):
    a1, a2 = math.radians(ang[0]), math.radians(ang[1])
    f2 = ang[2] if len(ang) > 2 else 1.0
    f1 = ang[3] if len(ang) > 3 else 1.0
    s1, s2 = seg * f1, seg * f2
    depth = -seg * math.sqrt(max(0.0, 1 - f1 * f1))           # foreshortened upper segment points at the camera
    j = (root[0] - math.sin(a1) * s1, root[1] + math.cos(a1) * s1, depth)
    e = (j[0] - math.sin(a2) * s2, j[1] + math.cos(a2) * s2, depth)
    return (root[0], root[1], 0.0), j, e

def _path(r, j, e, n=24):
    c = [2 * j[i] - (r[i] + e[i]) / 2 for i in range(3)]
    return [tuple((1 - t) ** 2 * r[i] + 2 * (1 - t) * t * c[i] + t * t * e[i] for i in range(3))
            for t in (k / n for k in range(n + 1))]

def _face_texture(expr, color, out_png):
    """Face features only (eyes, brows, mouth, sweat...) from the 2D drawing, transparent elsewhere."""
    from PIL import Image
    im = S2.draw(expr, 'stand', color).convert('RGBA')
    top = im.getbbox()[1]; hy = top + R + 3
    crop = im.crop((300 - R, hy - R, 300 + R, hy + R)).resize((512, 512), Image.LANCZOS)
    C = S2.hexrgb(color); px = crop.load(); w, h = crop.size
    for y in range(h):
        for x in range(w):
            r, g, b, a = px[x, y]
            dx, dy = (x - w / 2) / (w / 2), (y - h / 2) / (h / 2)
            inside = dx * dx + dy * dy < 0.86 ** 2
            far = abs(r - C[0]) + abs(g - C[1]) + abs(b - C[2]) > 90
            px[x, y] = (r, g, b, 255) if (inside and far and a > 0) else (0, 0, 0, 0)
    crop.save(out_png)
    return out_png

def build(name='stick', pose='stand', expr='neutral', color='#4a86e0', height=1.75, tmpdir='/tmp'):
    sc = bpy.context.scene
    P = S2.POSES[pose]
    think = pose == 'think'
    shL, shR = ((278, 262), (322, 262)) if think else (SHOULDER, SHOULDER)
    legs = [_limb(HIP, P['legL'], SEG_LEG), _limb(HIP, P['legR'], SEG_LEG)]
    arms = [_limb(shL, P['armL'], SEG_ARM), _limb(shR, P['armR'], SEG_ARM)]
    # soles at the ground, centred like the 2D card
    low = max(max(p[1] for p in _path(*l)) for l in legs) + T / 2
    top = 140 - R
    k = height / (low - top)
    def W(p):  # design (x right, y down, d toward camera<0) -> local metres (x, y forward, z up)
        return Vector(((p[0] - 300) * k, p[2] * k, (low - p[1]) * k))

    col = bpy.data.collections.new(name); sc.collection.children.link(col)
    parts = []
    def tube(pts, radius, nm):
        cu = bpy.data.curves.new(nm, 'CURVE'); cu.dimensions = '3D'
        sp = cu.splines.new('POLY'); sp.points.add(len(pts) - 1)
        for i, p in enumerate(pts): v = W(p); sp.points[i].co = (v.x, v.y, v.z, 1)
        cu.bevel_depth = radius * k; cu.bevel_resolution = 6; cu.use_fill_caps = True
        o = bpy.data.objects.new(nm, cu); col.objects.link(o); parts.append(o)
        for p in (pts[0], pts[-1]):                      # round ends
            bpy.ops.mesh.primitive_uv_sphere_add(radius=radius * k, location=W(p), segments=24, ring_count=12)
            s = bpy.context.object
            for c in s.users_collection: c.objects.unlink(s)
            col.objects.link(s); parts.append(s)

    tube([(300, 232 + i * (520 - 232) / 12, 0) for i in range(13)], TB / 2, nm=name + '_torso')
    for i, l in enumerate(legs): tube(_path(*l), T / 2, f'{name}_leg{i}')
    for i, a in enumerate(arms): tube(_path(*a), T / 2, f'{name}_arm{i}')
    hc = W((300, 140, 0))
    bpy.ops.mesh.primitive_uv_sphere_add(radius=R * k, location=hc, segments=48, ring_count=24)
    head = bpy.context.object
    for c in head.users_collection: c.objects.unlink(head)
    col.objects.link(head); parts.append(head)

    # merge everything into ONE watertight body (rule 8/9: no seams, no knots at the joints)
    bpy.ops.object.select_all(action='DESELECT')
    for o in parts:
        o.select_set(True)
    bpy.context.view_layer.objects.active = head
    bpy.ops.object.convert(target='MESH')
    bpy.ops.object.join()
    body = bpy.context.object; body.name = name
    rm = body.modifiers.new('merge', 'REMESH'); rm.mode = 'VOXEL'; rm.voxel_size = height / 320
    bpy.ops.object.modifier_apply(modifier='merge')
    bpy.ops.object.shade_smooth()
    # origin at the feet (world 0), so placing the body puts its soles on the ground and object coords match W()
    from mathutils import Matrix
    body.data.transform(Matrix.Translation(body.location)); body.location = (0, 0, 0)

    # material: one flat colour, slight self-light so it reads at night; face projected on the front of the head
    c = S2.hexrgb(color); lin = [(v / 255) ** 2.2 for v in c]
    m = bpy.data.materials.new(name + '_mat'); m.use_nodes = True; body.data.materials.append(m)
    nt = m.node_tree; n = nt.nodes; L = nt.links; Pb = n['Principled BSDF']
    Pb.inputs['Roughness'].default_value = 0.55
    face = bpy.data.images.load(_face_texture(expr, color, os.path.join(tmpdir, f'{name}_face.png')))
    tc = n.new('ShaderNodeTexCoord')
    mp = n.new('ShaderNodeMapping'); mp.vector_type = 'POINT'
    # object coords -> (u,v) over the head's front: u = (x-hx)/(2R)+.5, v = (z-hz)/(2R)+.5
    mp.inputs['Location'].default_value = (0.5 - hc.x / (2 * R * k), 0.5 - hc.z / (2 * R * k), 0)
    mp.inputs['Scale'].default_value = (1 / (2 * R * k), 1 / (2 * R * k), 1)
    sw = n.new('ShaderNodeSeparateXYZ'); cmb = n.new('ShaderNodeCombineXYZ')
    L.new(tc.outputs['Object'], sw.inputs['Vector'])
    # build (x, z) as the 2D vector to map
    L.new(sw.outputs['X'], cmb.inputs['X']); L.new(sw.outputs['Z'], cmb.inputs['Y'])
    L.new(cmb.outputs['Vector'], mp.inputs['Vector'])
    tex = n.new('ShaderNodeTexImage'); tex.image = face; tex.extension = 'CLIP'
    L.new(mp.outputs['Vector'], tex.inputs['Vector'])
    front = n.new('ShaderNodeMath'); front.operation = 'LESS_THAN'; front.inputs[1].default_value = 0.0
    L.new(sw.outputs['Y'], front.inputs[0])                               # only the camera-facing half
    near = n.new('ShaderNodeMath'); near.operation = 'GREATER_THAN'; near.inputs[1].default_value = hc.z - 1.05 * R * k
    L.new(sw.outputs['Z'], near.inputs[0])                                # only on the head, not the body
    m1 = n.new('ShaderNodeMath'); m1.operation = 'MULTIPLY'; L.new(front.outputs[0], m1.inputs[0]); L.new(near.outputs[0], m1.inputs[1])
    m2 = n.new('ShaderNodeMath'); m2.operation = 'MULTIPLY'; L.new(m1.outputs[0], m2.inputs[0]); L.new(tex.outputs['Alpha'], m2.inputs[1])
    mix = n.new('ShaderNodeMixRGB'); mix.inputs['Color1'].default_value = (*lin, 1)
    L.new(m2.outputs[0], mix.inputs['Fac']); L.new(tex.outputs['Color'], mix.inputs['Color2'])
    L.new(mix.outputs['Color'], Pb.inputs['Base Color'])
    L.new(mix.outputs['Color'], Pb.inputs['Emission Color']); Pb.inputs['Emission Strength'].default_value = 0.18
    return body
