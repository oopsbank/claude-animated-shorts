# Playa materials: cracked pale clay (polygon mud cracks), dark rock, groove trails, thin ice.
import bpy, math
import common as C

def clay_mat(name="clay", scale=3.2, c0=(0.31, 0.215, 0.135), c1=(0.47, 0.35, 0.23), crack=(0.33, 0.235, 0.16), width=0.02):
    """Cracked lake-bed clay: Voronoi cells (polygons) with dark crack lines, raised curled edges via bump,
    a soft large-scale tint wobble. Object coordinates, so cells stay the same size across the plane."""
    m = bpy.data.materials.new(name); m.use_nodes = True; n = m.node_tree.nodes; l = m.node_tree.links
    P = n['Principled BSDF']; P.inputs['Roughness'].default_value = 0.88; P.inputs['Specular IOR Level'].default_value = 0.3
    tc = n.new('ShaderNodeTexCoord')
    dist = n.new('ShaderNodeTexNoise'); dist.inputs['Scale'].default_value = 1.5; dist.inputs['Detail'].default_value = 2
    l.new(tc.outputs['Object'], dist.inputs['Vector'])
    mixv = n.new('ShaderNodeMix'); mixv.data_type = 'VECTOR'; mixv.inputs['Factor'].default_value = 0.08
    l.new(tc.outputs['Object'], mixv.inputs[4]); l.new(dist.outputs['Color'], mixv.inputs[5])
    vor = n.new('ShaderNodeTexVoronoi'); vor.feature = 'DISTANCE_TO_EDGE'; vor.inputs['Scale'].default_value = scale
    vor.inputs['Randomness'].default_value = 0.9
    l.new(mixv.outputs[1], vor.inputs['Vector'])
    cell = n.new('ShaderNodeTexVoronoi'); cell.inputs['Scale'].default_value = scale; cell.inputs['Randomness'].default_value = 0.9
    l.new(mixv.outputs[1], cell.inputs['Vector'])
    edge = n.new('ShaderNodeMapRange'); edge.inputs['From Min'].default_value = 0.0; edge.inputs['From Max'].default_value = width
    l.new(vor.outputs['Distance'], edge.inputs['Value'])
    tint = n.new('ShaderNodeValToRGB'); tint.color_ramp.elements[0].color = (*c0, 1); tint.color_ramp.elements[1].color = (*c1, 1)
    big = n.new('ShaderNodeTexNoise'); big.inputs['Scale'].default_value = 0.12; l.new(tc.outputs['Object'], big.inputs['Vector'])
    mixf = n.new('ShaderNodeMath'); mixf.operation = 'MULTIPLY_ADD'; mixf.inputs[1].default_value = 0.30
    l.new(cell.outputs['Distance'], mixf.inputs[0]); l.new(big.outputs['Fac'], mixf.inputs[2])
    l.new(mixf.outputs[0], tint.inputs['Fac'])
    mc = n.new('ShaderNodeMix'); mc.data_type = 'RGBA'; mc.inputs[7].default_value = (*crack, 1)
    inv = n.new('ShaderNodeMath'); inv.operation = 'SUBTRACT'; inv.inputs[0].default_value = 1.0; l.new(edge.outputs['Result'], inv.inputs[1])
    l.new(inv.outputs[0], mc.inputs['Factor']); l.new(tint.outputs['Color'], mc.inputs[6])
    l.new(mc.outputs[2], P.inputs['Base Color'])
    bmp = n.new('ShaderNodeBump'); bmp.inputs['Strength'].default_value = 0.55; bmp.inputs['Distance'].default_value = 0.02
    sq = n.new('ShaderNodeMath'); sq.operation = 'POWER'; sq.inputs[1].default_value = 0.5; l.new(edge.outputs['Result'], sq.inputs[0])
    l.new(sq.outputs[0], bmp.inputs['Height']); l.new(bmp.outputs['Normal'], P.inputs['Normal'])
    return m

def trail_mat():
    """Painted furrow on a flat strip (v across 0..1): soft dark floor, thin pale rims, faded edges. A flat decal reads
    as a groove from any angle; real geometry at playa scale read as a pipe or a plank at low cameras."""
    m = bpy.data.materials.get('trail')
    if m: return m
    m = bpy.data.materials.new('trail'); m.use_nodes = True; n = m.node_tree.nodes; l = m.node_tree.links; n.clear()
    out = n.new('ShaderNodeOutputMaterial'); P = n.new('ShaderNodeBsdfPrincipled'); tr = n.new('ShaderNodeBsdfTransparent')
    P.inputs['Roughness'].default_value = 0.75
    uv = n.new('ShaderNodeUVMap'); sep = n.new('ShaderNodeSeparateXYZ'); l.new(uv.outputs['UV'], sep.inputs['Vector'])
    pp = n.new('ShaderNodeMath'); pp.operation = 'PINGPONG'; pp.inputs[1].default_value = 0.5; l.new(sep.outputs['Y'], pp.inputs[0])   # 0 at edges, 0.5 centre
    col = n.new('ShaderNodeValToRGB'); e = col.color_ramp.elements
    e[0].position = 0.0; e[0].color = (0.62, 0.48, 0.33, 1); e[1].position = 0.5; e[1].color = (0.09, 0.055, 0.035, 1)
    k = e.new(0.12); k.color = (0.66, 0.52, 0.36, 1); k = e.new(0.22); k.color = (0.20, 0.13, 0.08, 1)
    l.new(pp.outputs[0], col.inputs['Fac']); l.new(col.outputs['Color'], P.inputs['Base Color'])
    al = n.new('ShaderNodeMapRange'); al.inputs['From Min'].default_value = 0.0; al.inputs['From Max'].default_value = 0.08
    l.new(pp.outputs[0], al.inputs['Value'])
    fade = n.new('ShaderNodeAttribute'); fade.attribute_name = 'fade'
    mm = n.new('ShaderNodeMath'); mm.operation = 'MULTIPLY'; l.new(al.outputs['Result'], mm.inputs[0]); l.new(fade.outputs['Fac'], mm.inputs[1])
    mx = n.new('ShaderNodeMixShader'); l.new(mm.outputs[0], mx.inputs['Fac']); l.new(tr.outputs[0], mx.inputs[1]); l.new(P.outputs[0], mx.inputs[2])
    l.new(mx.outputs[0], out.inputs['Surface'])
    return m

def trail(start, heading, length, width=0.5, wobble=0.6, seed=0, depth=None):
    """The groove a sliding rock left: a flat painted strip from `start` (at the rock) running back along `heading`
    (degrees, 0 = +X), curving gently, fading out at the far end."""
    import bmesh, random
    from mathutils import Vector
    rnd = random.Random(seed); n = max(8, int(length * 6)); pts = []
    h = math.radians(heading); bend = rnd.uniform(-1, 1) * wobble
    for i in range(n + 1):
        u = i / n; a = h + bend * math.sin(u * math.pi * 0.9) * 0.6
        pts.append(Vector((start[0], start[1], 0)) if i == 0 else pts[-1] + Vector((math.cos(a), math.sin(a), 0)) * (length / n))
    me = bpy.data.meshes.new('trail'); bm = bmesh.new(); uvl = bm.loops.layers.uv.new()
    rows = []
    for i, p in enumerate(pts):
        t = (pts[min(i + 1, n)] - pts[max(i - 1, 0)]).normalized(); nr = Vector((-t.y, t.x, 0))
        rows.append((bm.verts.new(p + nr * width / 2 + Vector((0, 0, 0.004))), bm.verts.new(p - nr * width / 2 + Vector((0, 0, 0.004)))))
    for i in range(n):
        f = bm.faces.new((rows[i][0], rows[i + 1][0], rows[i + 1][1], rows[i][1]))
        for loop, uvv in zip(f.loops, ((i / n, 0), ((i + 1) / n, 0), ((i + 1) / n, 1), (i / n, 1))): loop[uvl].uv = uvv
    bm.to_mesh(me); bm.free()
    fa = me.attributes.new('fade', 'FLOAT', 'POINT')
    for k, v in enumerate(me.vertices): fa.data[k].value = min(1.0, (n - k // 2) / (n * 0.3)) * min(1.0, (k // 2) / 2 + 0.5)
    o = bpy.data.objects.new('trail', me); C.sc().collection.objects.link(o)
    C.assign(o, trail_mat()); C.no_ink(o); o.visible_shadow = False; return o

def mountains(radius=260, n=26, seed=7, col=(0.22, 0.10, 0.16), h=(25, 60), cx=0, cy=0, arc=(0, 360)):
    """Ring of low, eroded desert mountains: squashed noisy cones in dark brown/purple, faceted, no ink."""
    import random
    from mathutils import noise as mn, Vector
    rnd = random.Random(seed); m = bpy.data.materials.get('mtn') or C.pbr('mtn', col, rough=0.8, coat=0.0, bevel=0.0, noise=0.35, noise_scale=0.02)
    objs = []
    for k in range(n):
        a = math.radians(arc[0] + (arc[1] - arc[0]) * (k + rnd.uniform(-0.3, 0.3)) / n)
        r = radius * rnd.uniform(0.85, 1.15); hh = rnd.uniform(*h)
        bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=4, radius=1, location=(cx + r * math.cos(a), cy + r * math.sin(a), 0))
        o = bpy.context.object; off = Vector((rnd.uniform(0, 50), rnd.uniform(0, 50), 0))
        for v in o.data.vertices:
            c = v.co.copy(); z = max(c.z, 0)
            v.co = Vector((c.x * (1 + 0.25 * mn.noise(c * 2 + off)), c.y * (1 + 0.25 * mn.noise(c * 2 + off)), z * (1 + 0.5 * mn.noise(c * 3 + off))))
        o.scale = (hh * rnd.uniform(1.8, 3.0), hh * 1.6, hh); o.rotation_euler.z = a
        for pl in o.data.polygons: pl.use_smooth = True
        C.assign(o, m); C.no_ink(o); objs.append(o)
    return objs

def pebbles(center, n=14, spread=0.8, seed=1, size=0.05):
    import random
    rnd = random.Random(seed); out = []
    for k in range(n):
        out.append(C.rock((center[0] + rnd.gauss(0, spread), center[1] + rnd.gauss(0, spread), 0), (size * rnd.uniform(0.6, 1.4),) * 2 + (size * 0.6,), seed=seed * 100 + k, detail=1, facet=True))
    return out

def ice_mat():
    """Thin ice over shallow water: near-clear, mirror-glossy (reflects sky and mountains), pale cyan tint, faint pane seams."""
    m = bpy.data.materials.new('ice'); m.use_nodes = True; n = m.node_tree.nodes; l = m.node_tree.links; P = n['Principled BSDF']
    P.inputs['Base Color'].default_value = (0.70, 0.88, 0.95, 1); P.inputs['Roughness'].default_value = 0.02
    P.inputs['Transmission Weight'].default_value = 0.85; P.inputs['IOR'].default_value = 1.31
    P.inputs['Specular IOR Level'].default_value = 0.8
    tc = n.new('ShaderNodeTexCoord'); v = n.new('ShaderNodeTexVoronoi'); v.feature = 'DISTANCE_TO_EDGE'; v.inputs['Scale'].default_value = 0.3
    l.new(tc.outputs['Object'], v.inputs['Vector'])
    r = n.new('ShaderNodeMapRange'); r.inputs['From Min'].default_value = 0.0; r.inputs['From Max'].default_value = 0.005
    r.inputs['To Min'].default_value = 0.45; r.inputs['To Max'].default_value = 0.85; l.new(v.outputs['Distance'], r.inputs['Value'])
    l.new(r.outputs['Result'], P.inputs['Transmission Weight'])          # pane seams go white-opaque
    return m

def pond_mat():
    """Ankle-deep night water: dark, glossy, slightly see-through, small ripple bump."""
    m = bpy.data.materials.new('pond'); m.use_nodes = True; n = m.node_tree.nodes; l = m.node_tree.links; P = n['Principled BSDF']
    P.inputs['Base Color'].default_value = (0.22, 0.30, 0.42, 1); P.inputs['Roughness'].default_value = 0.05
    P.inputs['Transmission Weight'].default_value = 0.6; P.inputs['IOR'].default_value = 1.33
    tc = n.new('ShaderNodeTexCoord'); nz = n.new('ShaderNodeTexNoise'); nz.inputs['Scale'].default_value = 3.0; l.new(tc.outputs['Object'], nz.inputs['Vector'])
    b = n.new('ShaderNodeBump'); b.inputs['Strength'].default_value = 0.08; l.new(nz.outputs['Fac'], b.inputs['Height']); l.new(b.outputs['Normal'], P.inputs['Normal'])
    return m
