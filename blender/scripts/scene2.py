# Stylised night village square: Quaternius + KayKit (CC0) models, built entirely by script.
# usage: python scripts/scene2.py <out.png> [samples] [scale%] [comp_dof 0/1] [shot A|B]
import bpy, sys, math, os, time
from mathutils import Vector

OUT = sys.argv[1]
SAMPLES = int(sys.argv[2]) if len(sys.argv) > 2 else 32
SCALE = int(sys.argv[3]) if len(sys.argv) > 3 else 100
COMP_DOF = int(sys.argv[4]) if len(sys.argv) > 4 else 0
SHOT = sys.argv[5] if len(sys.argv) > 5 else 'A'
ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))   # repo root
PACKS = os.environ.get('PACKS', os.path.join(ROOT, 'packs'))   # CC0 model packs (gitignored, cloned by the setup script)
Q = os.path.join(PACKS, 'quaternius-showcase/public/glb/medieval_village_pack')
K = os.path.join(PACKS, 'KayKit-Medieval-Hexagon-Pack-1.0/addons/kaykit_medieval_hexagon_pack/Assets/gltf/decoration/props')
A = os.path.join(ROOT, 'stickman')

bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene

def imp(path, loc=(0, 0, 0), rz=0, s=1.0):
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=path)
    new = [o for o in bpy.data.objects if o not in before]
    root = bpy.data.objects.new(os.path.basename(path), None); sc.collection.objects.link(root)
    for o in new:
        if o.parent is None: o.parent = root
    root.location = loc; root.rotation_euler.z = math.radians(rz); root.scale = (s,) * 3
    return root

q = lambda n, *a, **k: imp(f'{Q}/{n}.glb', *a, **k)
kk = lambda n, *a, **k: imp(f'{K}/{n}.gltf', *a, **k)

# ---------- layout (metres; hero card is 1.75 m) ----------
HZ = 2.2   # house scale -> ~8 m tall houses
for name, x, y, rz in (('House_1', -6.4, 13.0, 10), ('Inn', -0.6, 15.5, 0), ('House_2', 5.6, 13.5, -10),
                       ('House_1', 10.5, 10.5, -30), ('House_2', -11.5, 10.0, 30), ('House_3', 2.6, 21.0, 0)):
    q(name, (x, y, 0), rz, HZ)
q('Bell_Tower', (-4.0, 22.0, 0), 0, 3.0)
for i, (name, x, y, rz) in enumerate((('House_2', -9.0, 21.0, 5), ('House_1', 7.5, 22.0, -5), ('Inn', 12.5, 19.0, -20),
        ('House_1', -14.5, 17.0, 20), ('House_2', 0.5, 29.0, 0), ('House_1', -6.0, 31.0, 0), ('Inn', 7.0, 32.0, 0),
        ('House_2', -12.0, 30.0, 10), ('House_1', 13.0, 29.0, -10))):
    q(name, (x, y, (2.0 if y < 25 else 5.5) + 0.25 * i), rz, HZ * 1.05)   # rows climb a hill behind the square
q('Well', (-2.3, 5.0, 0.45), 15, 1.9)
q('MarketStand_1', (2.9, 6.0, 0), -20, 2.3)
q('Cart', (0.9, 9.0, 0), 60, 1.9)
for x, y, rz in ((1.35, 0.9, 0), (1.95, 1.35, 30), (1.65, 1.95, 60)):
    q('Barrel', (x, y, 0), rz, 4.6)
kk('crate_A_big', (-1.05, -2.6, 0), 10, 3.4)
kk('crate_A_big', (-1.00, -2.55, 0.71), 35, 3.0)
kk('crate_A_small', (-0.35, -3.0, 0), 20, 3.4)
kk('barrel', (1.5, -2.2, 0), 0, 4.0)

# ---------- materials: brighten palette, glowing windows ----------
for m in bpy.data.materials:
    if not m.use_nodes: continue
    P = next((x for x in m.node_tree.nodes if x.type == 'BSDF_PRINCIPLED'), None)
    if not P: continue
    P.inputs['Roughness'].default_value = 0.85
    if m.name.startswith('Windows'):
        P.inputs['Emission Color'].default_value = (1.0, 0.62, 0.25, 1)
        P.inputs['Emission Strength'].default_value = 5.0
    elif not P.inputs['Base Color'].is_linked:
        c = P.inputs['Base Color'].default_value
        import colorsys
        h, s_, v = colorsys.rgb_to_hsv(c[0], c[1], c[2])
        r, g, b = colorsys.hsv_to_rgb(h, min(1, s_ * 1.25), min(1, v * 1.1))
        P.inputs['Base Color'].default_value = (r, g, b, 1)

# ---------- ground: stylised cobbles (voronoi edges = mortar) ----------
bpy.ops.mesh.primitive_plane_add(size=120)
gnd = bpy.context.object
gm = bpy.data.materials.new('cobble'); gm.use_nodes = True; gnd.data.materials.append(gm)
n = gm.node_tree.nodes; l = gm.node_tree.links; P = n['Principled BSDF']; P.inputs['Roughness'].default_value = 0.7
tc = n.new('ShaderNodeTexCoord')
vor = n.new('ShaderNodeTexVoronoi'); vor.feature = 'DISTANCE_TO_EDGE'; vor.inputs['Scale'].default_value = 5.5
vor2 = n.new('ShaderNodeTexVoronoi'); vor2.inputs['Scale'].default_value = 5.5
l.new(tc.outputs['Object'], vor.inputs['Vector']); l.new(tc.outputs['Object'], vor2.inputs['Vector'])
rmp = n.new('ShaderNodeValToRGB'); rmp.color_ramp.elements[0].position = 0.02; rmp.color_ramp.elements[1].position = 0.06
rmp.color_ramp.elements[0].color = (0.10, 0.09, 0.12, 1); rmp.color_ramp.elements[1].color = (1, 1, 1, 1)
l.new(vor.outputs['Distance'], rmp.inputs['Fac'])
tint = n.new('ShaderNodeValToRGB')                    # per-stone colour variation
tint.color_ramp.elements[0].color = (0.17, 0.16, 0.20, 1); tint.color_ramp.elements[1].color = (0.30, 0.26, 0.26, 1)
l.new(vor2.outputs['Color'], tint.inputs['Fac'])
mul = n.new('ShaderNodeMixRGB'); mul.blend_type = 'MULTIPLY'; mul.inputs['Fac'].default_value = 1
l.new(tint.outputs['Color'], mul.inputs['Color1']); l.new(rmp.outputs['Color'], mul.inputs['Color2'])
l.new(mul.outputs['Color'], P.inputs['Base Color'])
bmp = n.new('ShaderNodeBump'); bmp.inputs['Strength'].default_value = 0.4
l.new(rmp.outputs['Color'], bmp.inputs['Height']); l.new(bmp.outputs['Normal'], P.inputs['Normal'])

bpy.ops.mesh.primitive_uv_sphere_add(radius=40, location=(0, 62, -32)); hill = bpy.context.object
hill.scale = (1.6, 1.0, 1.0)
hm = bpy.data.materials.new('hill'); hm.use_nodes = True; hill.data.materials.append(hm)
hm.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = (0.05, 0.07, 0.14, 1)
# ---------- street lamp (simple stylised post) ----------
def mat(name, col, emit=0.0):
    m = bpy.data.materials.new(name); m.use_nodes = True; p = m.node_tree.nodes['Principled BSDF']
    p.inputs['Base Color'].default_value = (*col, 1); p.inputs['Roughness'].default_value = 0.6
    if emit: p.inputs['Emission Color'].default_value = (*col, 1); p.inputs['Emission Strength'].default_value = emit
    return m
iron = mat('iron', (0.04, 0.04, 0.06)); glow = mat('glow', (1.0, 0.50, 0.15), 2.2)
LX, LY = -1.55, 1.6
bpy.ops.mesh.primitive_cylinder_add(vertices=12, radius=0.07, depth=3.4, location=(LX, LY, 1.7)); bpy.context.object.data.materials.append(iron)
bpy.ops.mesh.primitive_cylinder_add(vertices=12, radius=0.16, depth=0.25, location=(LX, LY, 0.12)); bpy.context.object.data.materials.append(iron)
bpy.ops.mesh.primitive_cube_add(size=0.34, location=(LX, LY, 3.55)); bpy.context.object.data.materials.append(glow)
bpy.ops.mesh.primitive_cone_add(vertices=4, radius1=0.33, depth=0.28, location=(LX, LY, 3.86), rotation=(0, 0, math.radians(45))); bpy.context.object.data.materials.append(iron)

def point(loc, color, power, radius=0.1):
    ld = bpy.data.lights.new('pt', 'POINT'); ld.color = color; ld.energy = power; ld.shadow_soft_size = max(radius, 0.35)
    o = bpy.data.objects.new('pt', ld); sc.collection.objects.link(o); o.location = loc
point((LX, LY, 3.45), (1.0, 0.62, 0.30), 650, 0.15)        # lamp
point((-0.6, 12.0, 2.2), (1.0, 0.6, 0.3), 500, 1.0)         # inn doorway spill
point((5.6, 10.5, 2.0), (1.0, 0.6, 0.3), 250, 1.0)

moon = bpy.data.lights.new('moon', 'SUN'); moon.color = (0.50, 0.62, 1.0); moon.energy = 2.2; moon.angle = math.radians(12)
mo = bpy.data.objects.new('moon', moon); sc.collection.objects.link(mo); mo.rotation_euler = (math.radians(55), 0, math.radians(210))
fill = bpy.data.lights.new('fill', 'AREA'); fill.color = (0.62, 0.58, 1.0); fill.energy = 650; fill.size = 14
fo = bpy.data.objects.new('fill', fill); sc.collection.objects.link(fo); fo.location = (3, -12, 7)
fo.rotation_euler = (Vector((0, 6, 0)) - fo.location).to_track_quat('-Z', 'Y').to_euler()   # lavender camera-side fill

# ---------- sky: painted gradient + stars ----------
w = bpy.data.worlds.new('w'); sc.world = w; w.use_nodes = True
wn = w.node_tree.nodes; wl = w.node_tree.links
tcw = wn.new('ShaderNodeTexCoord'); sep = wn.new('ShaderNodeSeparateXYZ'); wl.new(tcw.outputs['Generated'], sep.inputs['Vector'])
ramp = wn.new('ShaderNodeValToRGB'); cr = ramp.color_ramp
cr.elements[0].position = 0.0; cr.elements[0].color = (0.30, 0.26, 0.60, 1)
cr.elements[1].position = 0.45; cr.elements[1].color = (0.012, 0.022, 0.11, 1)
cr.elements.new(0.12).color = (0.07, 0.09, 0.32, 1)
wl.new(sep.outputs['Z'], ramp.inputs['Fac'])
vw = wn.new('ShaderNodeTexVoronoi'); vw.inputs['Scale'].default_value = 140; wl.new(tcw.outputs['Generated'], vw.inputs['Vector'])
st = wn.new('ShaderNodeMapRange'); st.inputs['From Min'].default_value = 0.035; st.inputs['From Max'].default_value = 0.0
st.inputs['To Max'].default_value = 3.0; wl.new(vw.outputs['Distance'], st.inputs['Value'])
add = wn.new('ShaderNodeMixRGB'); add.blend_type = 'ADD'; wl.new(st.outputs['Result'], add.inputs['Fac'])
add.inputs['Color2'].default_value = (0.9, 0.95, 1.0, 1)
wl.new(ramp.outputs['Color'], add.inputs['Color1']); wl.new(add.outputs['Color'], wn['Background'].inputs['Color'])
wn['Background'].inputs['Strength'].default_value = 3.2

# ---------- LIGHT=day: bright daylight (the reference's default look; see references/reports/recent_style_2026-11.md) ----------
LIGHT = os.environ.get('LIGHT', 'night')
if LIGHT == 'day':
    moon.color = (1.0, 0.93, 0.82); moon.energy = 4.2; moon.angle = math.radians(4)
    mo.rotation_euler = (math.radians(50), 0, math.radians(335))          # warm sun from the camera side, slightly left: lights the facades
    fill.color = (0.80, 0.86, 1.0); fill.energy = 260                      # cool sky fill from the camera side
    for o in [o for o in sc.objects if o.type == 'LIGHT' and o.data.type == 'POINT']: o.data.energy = 0
    for m in bpy.data.materials:
        if not m.use_nodes: continue
        Pm = next((x for x in m.node_tree.nodes if x.type == 'BSDF_PRINCIPLED'), None)
        if Pm and Pm.inputs['Emission Strength'].default_value > 0 and m.name.startswith(('Windows', 'glow')):
            Pm.inputs['Emission Strength'].default_value = 0.3
    # ramp elements are sorted by position: [0]=horizon 0.0, [1]=0.12, [2]=zenith 0.45
    cr.elements[0].color = (0.80, 0.88, 1.0, 1); cr.elements[1].color = (0.55, 0.74, 0.98, 1)
    cr.elements[2].color = (0.22, 0.48, 0.93, 1)
    st.inputs['To Max'].default_value = 0.0                                  # no stars
    wn['Background'].inputs['Strength'].default_value = 1.6


img = bpy.data.images.load(os.environ.get('CARD', f'{A}/stick_neutral.png'))
H = 1.75; Wc = H * 0.6
bpy.ops.mesh.primitive_plane_add(size=1); card = bpy.context.object; card.name = 'card'
card.scale = (Wc, H, 1); card.rotation_euler = (math.radians(90), 0, 0)
bpy.ops.object.transform_apply(rotation=True, scale=True)
for v in card.data.vertices: v.co.z += H / 2 - 0.024 * H
card.location = (0.15, -0.2, 0)
cm = bpy.data.materials.new('card'); cm.use_nodes = True; card.data.materials.append(cm)
cn = cm.node_tree.nodes; cl = cm.node_tree.links; cp = cn['Principled BSDF']
tex = cn.new('ShaderNodeTexImage'); tex.image = img
cl.new(tex.outputs['Color'], cp.inputs['Base Color']); cl.new(tex.outputs['Alpha'], cp.inputs['Alpha'])
cl.new(tex.outputs['Color'], cp.inputs['Emission Color']); cp.inputs['Emission Strength'].default_value = 0.8
cp.inputs['Roughness'].default_value = 0.9

if os.environ.get('NOCHAR'): card.hide_render = True   # clean background plate for 2D compositing
# ---------- optional 3D stickman (replaces the 2D card) ----------
body = None
if os.environ.get('STICK3D'):
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import stick3d
    pose, expr = (('think', 'thinking') if SHOT == 'B' else ('wave', 'happy'))
    pose = os.environ.get('POSE', pose); expr = os.environ.get('EXPR', expr)
    body = stick3d.build('stick', pose, expr, os.environ.get('COLOR', '#4a86e0'), 1.75, os.path.dirname(os.path.abspath(OUT)))
    card.hide_render = True

# ---------- camera ----------
cam = bpy.data.cameras.new('cam'); cam.lens = 27
co = bpy.data.objects.new('cam', cam); sc.collection.objects.link(co); sc.camera = co
co.location = (0.7, -5.4, 1.35)
tgt = Vector((0.0, 6.0, 2.0))
co.rotation_euler = (tgt - co.location).to_track_quat('-Z', 'Y').to_euler()
co.rotation_euler.y += math.radians(3)
if SHOT == 'M':      # medium shot: a 1.75 m character fills ~55-65% of the frame height
    cam.lens = 35
    co.location = (0.45, -3.2, 1.2)
    tgt = Vector((0.0, 3.0, 1.45))
    co.rotation_euler = (tgt - co.location).to_track_quat('-Z', 'Y').to_euler()
    co.rotation_euler.y += math.radians(2)
if SHOT == 'B':
    card.location = (-1.15, 4.1, 0)
    cam.lens = 38
    co.location = (-0.15, 1.15, 1.45)
    tgt = Vector((-1.75, 4.9, 1.25))
    co.rotation_euler = (tgt - co.location).to_track_quat('-Z', 'Y').to_euler()
    co.rotation_euler.y += math.radians(-4)
card.rotation_euler.z = math.atan2(co.location.x - card.location.x, -(co.location.y - card.location.y))
if body:
    body.location = card.location
    body.rotation_euler.z = card.rotation_euler.z
    sc.view_layers[0].update()
    cam.dof.focus_distance = (co.location - (Vector(card.location) + Vector((0, 0, 1.45)))).length
cam.dof.focus_object = None if body else card; cam.dof.aperture_fstop = 1.2 if SHOT == 'B' else 2.0
cam.dof.use_dof = not COMP_DOF

# ---------- ink: Freestyle, world only ----------
sc.render.use_freestyle = True; sc.render.line_thickness_mode = 'ABSOLUTE'
vl = sc.view_layers[0]; vl.use_freestyle = True; vl.use_pass_z = True
fs = vl.freestyle_settings; fs.crease_angle = math.radians(140)
ls = fs.linesets[0]
ls.select_by_visibility = True; ls.select_by_edge_types = True
ls.select_silhouette = True; ls.select_border = False; ls.select_crease = True; ls.select_external_contour = True
nolines = bpy.data.collections.new('noink'); sc.collection.children.link(nolines)
for o in (card, gnd):
    for c in o.users_collection: c.objects.unlink(o)
    nolines.objects.link(o)
ls.select_by_collection = True; ls.collection = nolines; ls.collection_negation = 'EXCLUSIVE'
if body:   # stickman: its own lineset, outer silhouette only (no crease ticks at the joints), thin dark ink
    nolines.objects.link(body)
    ls2 = fs.linesets.new('stick'); ls2.select_by_visibility = True; ls2.select_by_edge_types = True
    ls2.select_silhouette = True; ls2.select_border = False; ls2.select_crease = False; ls2.select_external_contour = True
    ls2.select_by_collection = True; ls2.collection = bpy.data.collections['stick']; ls2.collection_negation = 'INCLUSIVE'
    st2 = bpy.data.linestyles.new('stick_ink'); ls2.linestyle = st2
    st2.color = (0.07, 0.06, 0.10); st2.thickness = 2.4 * SCALE / 100; st2.alpha = 1.0
lst = ls.linestyle or bpy.data.linestyles.new('ink'); ls.linestyle = lst
lst.color = (0.0, 0.0, 0.0); lst.alpha = 1.0; lst.thickness = 3.4 * SCALE / 100
md = lst.thickness_modifiers.new('dist', 'DISTANCE_FROM_CAMERA')
md.range_min = 3; md.range_max = 30; md.value_min = 1.0; md.value_max = 0.45; md.blend = 'MULTIPLY'
am = lst.alpha_modifiers.new('fade', 'DISTANCE_FROM_CAMERA')
am.range_min = 14; am.range_max = 40; am.mapping = 'LINEAR'; am.invert = True; am.influence = 0.6; am.blend = 'MULTIPLY'
if SHOT == 'B': am.range_min, am.range_max, am.influence = 4.5, 9.0, 0.85
lst.color = (0.03, 0.02, 0.07)   # ink tinted toward the night, like the reference

# ---------- compositor lens blur (so the ink blurs with the scene) ----------
if COMP_DOF:
    try:
        cam.dof.use_dof = True   # defocus node reads the camera's f-stop / focus
        tree = bpy.data.node_groups.new('comp', 'CompositorNodeTree'); sc.compositing_node_group = tree
        rl = tree.nodes.new('CompositorNodeRLayers')
        df = tree.nodes.new('CompositorNodeDefocus')
        out = tree.nodes.new('NodeGroupOutput'); tree.interface.new_socket('Image', in_out='OUTPUT', socket_type='NodeSocketColor')
        tree.links.new(rl.outputs['Image'], df.inputs['Image']); tree.links.new(rl.outputs['Depth'], df.inputs['Z'])
        tree.links.new(df.outputs['Image'], out.inputs[0])
        cam.dof.use_dof = False   # don't also blur in-render
        print('COMP_DOF ok', [i.identifier for i in df.inputs])
    except Exception as e:
        print('COMP_DOF failed', e); cam.dof.use_dof = True

# ---------- render ----------
r = sc.render; r.engine = 'CYCLES'
sc.cycles.device = 'CPU'; sc.cycles.samples = SAMPLES; sc.cycles.use_denoising = True; sc.cycles.max_bounces = 6
r.resolution_x, r.resolution_y, r.resolution_percentage = 720, 1280, SCALE
sc.view_settings.view_transform = 'Khronos PBR Neutral'; sc.view_settings.exposure = 0.0
if LIGHT == 'day':
    lst.color = (0.018, 0.009, 0.020)       # plum ink #241726 in LINEAR space (sRGB values look washed out here)
    tint.color_ramp.elements[0].color = (0.36, 0.30, 0.25, 1); tint.color_ramp.elements[1].color = (0.55, 0.46, 0.37, 1)   # warm cobbles
    sc.view_settings.exposure = 0.35
r.filepath = os.path.abspath(OUT)  # shot ; r.image_settings.file_format = 'PNG'
# plate metadata (PIPELINE.md contract): where a 1.75 m character standing at the card spot lands on screen
from bpy_extras.object_utils import world_to_camera_view
import json
sc.view_layers[0].update()
def scr(v):
    p = world_to_camera_view(sc, co, Vector(v)); return p.x * r.resolution_x * r.resolution_percentage / 100, (1 - p.y) * r.resolution_y * r.resolution_percentage / 100
gx, gy = scr(card.location); hx_, hy_ = scr(Vector(card.location) + Vector((0, 0, 1.75)))
meta = {'ground_x': round(gx, 1), 'ground_y': round(gy, 1), 'px_per_m': round((gy - hy_) / 1.75, 1), 'light': os.environ.get('LIGHT', 'night'), 'shot': SHOT}
json.dump(meta, open(os.path.splitext(os.path.abspath(OUT))[0] + '.json', 'w')); print('PLATE_META', meta)
t = time.time(); bpy.ops.render.render(write_still=True)
print(f'RENDER_SECONDS {time.time() - t:.1f}')
bpy.ops.wm.save_as_mainfile(filepath=os.path.splitext(os.path.abspath(OUT))[0] + '.blend')
