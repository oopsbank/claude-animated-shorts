# Look test (playbook 3b): the tour van and a rock with a GPS box on cracked clay, soft sun, no ink on props.
# usage: .venv/bin/python blender/sets/playa/looktest.py <out.png> [pct] [samples]
import sys, os, math, bpy
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__)))); sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common as C, props as PR, ground as G
AZ = float(os.environ.get('AZ', 150)); SUN = tuple(float(x) for x in os.environ.get('SUN', '0.9,0.35,0.45').split(','))
out = sys.argv[1]; pct = int(sys.argv[2]) if len(sys.argv) > 2 else 50; spp = int(sys.argv[3]) if len(sys.argv) > 3 else 48
C.reset()
C.plane(200, (0, 0, 0), G.clay_mat())
PR.tour_van((0.8, 1.6, 0), rz=-140)
r = C.rock((-1.0, -2.6, 0), (0.46, 0.36, 0.26), seed=3, facet=True, detail=1, m=C.pbr('rockL', (0.075, 0.065, 0.07), rough=0.22, coat=0.8, bevel=0.04, noise=0.5, noise_scale=4.0))
PR.gps_box((-0.98, -2.62, 0.29), rz=20, s=4.0)
G.trail((-0.85, -2.25), 62, 14.0, width=0.85, wobble=0.25)
C.contact_blob((-1.0, -2.6, 0), 1.5, 1.2)
import math as M
for wy in (-0.85, 0.85):   # tyre tracks from the rear wheels, running back the way the van came
    a = M.radians(-140); lx, ly = -1.45, wy
    G.trail((0.8 + lx * M.cos(a) - ly * M.sin(a), 1.6 + lx * M.sin(a) + ly * M.cos(a)), -140 + 180, 30.0, width=0.3, wobble=0.1, depth=0.015, seed=9)
G.pebbles((-0.2, -0.6), n=10, spread=0.6, seed=2)
G.mountains(radius=480, n=22, cx=0, cy=0, arc=(30, 150), h=(30, 70))
C.rock((3.4, -3.0, 0), (0.25, 0.2, 0.17), seed=5)
co = C.camera((-2.6, -5.6, 1.7), (0.0, -0.2, 0.8), lens=30)
C.render_settings(spp, pct)
C.ink(pct, thick=0.0)  # props are noink; nothing else inked here
C.sc().render.use_freestyle = False
p, sun = C.apply_light('day', co, dict(sun_from=SUN, az=AZ, elev=20, sun=(1.0, 0.58, 0.30), sun_e=9.0, sun_soft=18, amb=(0.26, 0.44, 1.0), amb_e=0.85, fill=(0.36, 0.52, 1.0), fill_e=200, grade_sat=1.22, sky_refl=1.0, exposure=-0.45))
C.softbox((-4.5, 4.5, 5.0), (0.8, 1.6, 1.0), size=6, power=450)
C.softbox((5.5, 6.0, 4.0), (0.8, 1.6, 1.2), size=3, power=700, col=(1.0, 0.78, 0.55))   # warm rim from behind right
C.sc().render.filepath = out; bpy.ops.render.render(write_still=True)
dp = out[:-4] + '_d.png'; C._depth_pass(dp, 4, 520)
C.post(out, out, dp, (0.86, 0.74, 0.86), 0.45, sat=p.get('grade_sat', 1.0))
import json; js = C.measure(co, (0.6, -2.4, 0), sun, p); json.dump(js, open(out[:-4] + '.json', 'w'))
