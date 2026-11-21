# Playa materials: cracked pale clay (polygon mud cracks), dark rock, groove trails, thin ice.
import bpy, math
import common as C

def clay_mat(name="clay", scale=3.2, c0=(0.31, 0.215, 0.135), c1=(0.47, 0.35, 0.23), crack=(0.24, 0.16, 0.10), width=0.035):
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

def trail(start, heading, length, width=0.28, wobble=0.6, seed=0, depth=0.08):
    """A shallow groove the rock dragged: a dark smooth furrow with raised lips, curving gently.
    `start` is at the rock; the trail runs back along `heading` (degrees, 0 = +X)."""
    import bmesh, random
    from mathutils import Vector
    rnd = random.Random(seed); n = max(8, int(length * 6)); pts = []
    h = math.radians(heading); bend = rnd.uniform(-1, 1) * wobble
    for i in range(n + 1):
        u = i / n; a = h + bend * math.sin(u * math.pi * 0.9) * 0.6
        if i == 0: p = Vector((start[0], start[1], 0))
        else: p = pts[-1] + Vector((math.cos(a), math.sin(a), 0)) * (length / n)
        pts.append(p)
    me = bpy.data.meshes.new('trail'); bm = bmesh.new()
    rows = []
    prof = [(-1.6, 0.0), (-1.15, 0.45), (-0.75, 0.2), (0, 0.05), (0.75, 0.2), (1.15, 0.45), (1.6, 0.0)]   # metres = value * depth: a berm with a sunken floor
    for i, p in enumerate(pts):
        t = (pts[min(i + 1, n)] - pts[max(i - 1, 0)]).normalized(); nr = Vector((-t.y, t.x, 0))
        fade = min(1.0, (n - i) / (n * 0.25))
        rows.append([bm.verts.new(p + nr * (x * width / 2) + Vector((0, 0, z * depth * fade + 0.003))) for x, z in prof])
    for i in range(n):
        for j in range(len(prof) - 1):
            f = bm.faces.new((rows[i][j], rows[i + 1][j], rows[i + 1][j + 1], rows[i][j + 1])); f.material_index = 1 if j in (2, 3) else 0
    bm.to_mesh(me); bm.free(); o = bpy.data.objects.new('trail', me); C.sc().collection.objects.link(o)
    for pl in o.data.polygons: pl.use_smooth = True
    m = bpy.data.materials.get('trail') or C.pbr('trail', (0.05, 0.028, 0.02), rough=0.9, coat=0.0, bevel=0.0)
    lip = bpy.data.materials.get('clay') or C.pbr('trail_lip', (0.42, 0.31, 0.20), rough=0.95, coat=0.0, bevel=0.0)   # berms in the ground's own clay
    o.data.materials.append(lip); o.data.materials.append(m); C.no_ink(o); return o

def mountains(radius=260, n=26, seed=7, col=(0.22, 0.10, 0.16), h=(25, 60), cx=0, cy=0, arc=(0, 360)):
    """Ring of low, eroded desert mountains: squashed noisy cones in dark brown/purple, faceted, no ink."""
    import random
    from mathutils import noise as mn, Vector
    rnd = random.Random(seed); m = bpy.data.materials.get('mtn') or C.pbr('mtn', col, rough=0.8, coat=0.0, bevel=0.0, noise=0.35, noise_scale=0.02)
    objs = []
    for k in range(n):
        a = math.radians(arc[0] + (arc[1] - arc[0]) * (k + rnd.uniform(-0.3, 0.3)) / n)
        r = radius * rnd.uniform(0.85, 1.15); hh = rnd.uniform(*h)
        bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=3, radius=1, location=(cx + r * math.cos(a), cy + r * math.sin(a), 0))
        o = bpy.context.object; off = Vector((rnd.uniform(0, 50), rnd.uniform(0, 50), 0))
        for v in o.data.vertices:
            c = v.co.copy(); z = max(c.z, 0)
            v.co = Vector((c.x * (1 + 0.25 * mn.noise(c * 2 + off)), c.y * (1 + 0.25 * mn.noise(c * 2 + off)), z * (1 + 0.5 * mn.noise(c * 3 + off))))
        o.scale = (hh * rnd.uniform(1.8, 3.0), hh * 1.6, hh); o.rotation_euler.z = a
        C.assign(o, m); C.no_ink(o); objs.append(o)
    return objs

def pebbles(center, n=14, spread=0.8, seed=1, size=0.05):
    import random
    rnd = random.Random(seed); out = []
    for k in range(n):
        out.append(C.rock((center[0] + rnd.gauss(0, spread), center[1] + rnd.gauss(0, spread), 0), (size * rnd.uniform(0.6, 1.4),) * 2 + (size * 0.6,), seed=seed * 100 + k, detail=1, facet=True))
    return out
