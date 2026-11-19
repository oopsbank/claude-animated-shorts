# Post: bloom glow around bright lights (stand-in for the GPU compositor). usage: post.py in.png out.png
import sys, numpy as np
from PIL import Image, ImageFilter
im = Image.open(sys.argv[1]).convert('RGB'); a = np.asarray(im).astype(np.float32) / 255
lum = a @ np.array([0.2126, 0.7152, 0.0722], np.float32)
warm = np.clip((a[..., 0] - a[..., 2] - 0.12) / 0.2, 0, 1)   # only warm lights glow, not white faces
mask = (np.clip((lum - 0.6) / 0.25, 0, 1) * warm)[..., None]
hi = Image.fromarray((a * mask * 255).astype(np.uint8))
glow = np.zeros_like(a)
for r, w in ((6, 0.5), (18, 0.45), (45, 0.35)):
    glow += np.asarray(hi.filter(ImageFilter.GaussianBlur(r * im.height / 1280))).astype(np.float32) / 255 * w
out = 1 - (1 - a) * (1 - np.clip(glow, 0, 1))           # screen blend
Image.fromarray((np.clip(out, 0, 1) * 255).astype(np.uint8)).save(sys.argv[2])
