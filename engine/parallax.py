# Ride parallax: move the camera forward through a still plate using its metric depth map (sets --depth), so near
# ground and props stream past fast while the distant scene barely moves. Backward warp with a few fixed-point
# iterations on the depth (smooth ground converges in 2-3); no holes appear at the frame edges for forward moves.
import numpy as np
from PIL import Image


def load_depth(path, info):
    """Camera distance in metres, float32 (H, W)."""
    v = np.asarray(Image.open(path)).astype(np.float32) / 65535.0
    if info.get('encoding') == 'srgb':
        v = np.where(v <= 0.04045, v / 12.92, ((v + 0.055) / 1.055) ** 2.4)
    return info['near'] + v * (info['far'] - info['near'])


def _sample(img, x, y):
    """Bilinear sample of img (H, W, C) at float pixel coords, clamped to the edges."""
    h, w = img.shape[:2]
    x = np.clip(x, 0, w - 1.001); y = np.clip(y, 0, h - 1.001)
    x0 = x.astype(np.int32); y0 = y.astype(np.int32); fx = (x - x0)[..., None]; fy = (y - y0)[..., None]
    a = img[y0, x0]; b = img[y0, x0 + 1]; c = img[y0 + 1, x0]; d = img[y0 + 1, x0 + 1]
    return (a * (1 - fx) + b * fx) * (1 - fy) + (c * (1 - fx) + d * fx) * fy


class Rider:
    """Precomputes the rays of one plate; warp(dist) returns the plate seen from `dist` metres further along
    ride_dir (camera space, Blender axes: x right, y up, looking down -z)."""

    def __init__(self, plate_rgb, depth_m, f_px, ride_dir):
        self.img = plate_rgb.astype(np.float32); self.dist = depth_m[..., None]
        h, w = depth_m.shape; self.f = float(f_px); self.c = (w / 2.0, h / 2.0)
        u, v = np.meshgrid(np.arange(w, dtype=np.float32) + 0.5, np.arange(h, dtype=np.float32) + 0.5)
        self.r = np.stack([(u - self.c[0]) / self.f, -(v - self.c[1]) / self.f, -np.ones_like(u)], -1)   # z = -1 rays
        self.n = np.linalg.norm(self.r, axis=-1, keepdims=True)
        self.T = np.asarray(ride_dir, np.float32)

    def warp(self, dist, iters=3):
        if abs(dist) < 1e-4: return self.img.astype(np.uint8)
        T = self.T * dist
        s = (self.dist / self.n)[..., 0]                      # depth along -z at the output pixel (first guess)
        for _ in range(iters):
            P = self.r * s[..., None] + T                        # the point in the ORIGINAL camera
            z = np.maximum(-P[..., 2], 1e-3)
            qx = self.c[0] + self.f * P[..., 0] / z - 0.5; qy = self.c[1] - self.f * P[..., 1] / z - 0.5
            dq = _sample(self.dist, qx, qy)[..., 0]               # its camera distance there
            ray = np.stack([(qx + 0.5 - self.c[0]) / self.f, -(qy + 0.5 - self.c[1]) / self.f, -np.ones_like(qx)], -1)
            Pq = ray * (dq / np.linalg.norm(ray, axis=-1))[..., None]
            s = np.maximum(-(Pq - T)[..., 2], 1e-3)             # depth of that point from the moved camera
        return np.clip(_sample(self.img, qx, qy), 0, 255).astype(np.uint8)
