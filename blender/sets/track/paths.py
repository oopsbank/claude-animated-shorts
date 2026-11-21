# Racing lines for the top-down cam, projected exactly onto the plate (pure Python, no Blender needed).
# The engine's fx path_line uses them by name ("planned": "tight_left" etc.), so a drawn path follows the real road.
# usage: python blender/sets/track/paths.py   (adds "paths" to the existing track_top plate JSONs)
import math, json, glob, os

TW, R, L, CY = 9.0, 20.0, 50.0, 4.5                  # must match build.py
CENTRE = (L / 2, CY + R)                              # right corner centre; riders go counter-clockwise (a left turn)
W, H = 1080, 1920


def top_cam(lens=35.0, height=24.0):
    """track_top camera (build.py CAMS): straight down, image up = +Y, sensor 36 mm on the long side."""
    loc = (L / 2 + R * 0.707 + 0.5, CY + R - R * 0.707 + 4.0)
    return loc, lens / 36.0 * H / height              # px per metre on the ground


def lines():
    """(radius, angle) racing lines through the corner, radius measured from the corner centre."""
    rin, rout = R - 2.5, R + TW / 2 + 2.5              # inner lane, off the outer kerb onto the grass
    def path(rfun, a0=-70.0, a1=40.0, n=48): return [(rfun(i / n), a0 + (a1 - a0) * i / n) for i in range(n + 1)]
    ease = lambda u: u * u * (3 - 2 * u)
    return {
        'tight_left': path(lambda u: rin),
        # running wide = barely turning: it leaves the bend over the outer kerb while still in frame (lower right)
        'wide_arc': path(lambda u: rin + (rout + 1.5 - rin) * ease(u), a1=-12.0),
        # countersteer: a short jog to the rider's right (outward), then a tighter line than planned
        'kink_right_then_left': path(lambda u: rin + 3.5 * math.sin(math.pi * min(1.0, u / 0.22)) - 0.8 * ease(min(1.0, max(0.0, (u - 0.22) / 0.2)))),
    }


def project():
    (cx, cy), k = top_cam(); out = {}
    for name, pts in lines().items():
        xy = []
        for r, a in pts:
            x, y = CENTRE[0] + r * math.cos(math.radians(a)), CENTRE[1] + r * math.sin(math.radians(a))
            xy.append([round((W / 2 + (x - cx) * k) / W, 4), round((H / 2 - (y - cy) * k) / H, 4)])
        out[name] = xy
    return out


if __name__ == '__main__':
    here = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'plates')
    for p in glob.glob(os.path.join(here, 'track__track_top__*.json')):
        js = json.load(open(p)); js['paths'] = project(); json.dump(js, open(p, 'w'), indent=1); print('paths ->', p)
