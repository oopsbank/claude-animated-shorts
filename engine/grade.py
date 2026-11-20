# Per-shot grade (PIPELINE.md / references/reports/recent_style_2026-11.md targets): a tone curve per shot that moves the
# frame's mean luminance into the reference range, with a soft highlight shoulder so white faces never clip, plus a
# saturation trim. The curve is solved once per shot from a representative composited frame (main process) and applied
# to every frame of the shot as a 256-entry LUT (cheap).
import numpy as np
from PIL import Image, ImageEnhance

LUM = np.array([0.2126, 0.7152, 0.0722], np.float32)


def stats(img):
    a = np.asarray(img.convert('RGB').resize((270, 480))).astype(np.float32) / 255
    m = np.ones(a.shape[:2], bool); m[288:360, :] = False          # same caption-band mask as frame_stats.py
    L = (a @ LUM)[m]
    hsv = np.asarray(img.convert('RGB').resize((270, 480)).convert('HSV')).astype(np.float32) / 255
    return {'lum': float(L.mean()), 'p98': float(np.percentile(L, 98)), 'sat': float(hsv[..., 1][m].mean())}


def curve(g, shoulder=0.96, lift=0.0):
    """x^g, an optional highlight lift (keeps p98 up when a shot is darkened), then a soft shoulder above 0.85 so the
    brightest values land at `shoulder` (faces keep detail)."""
    x = np.arange(256, dtype=np.float32) / 255
    y = x ** g
    if lift: y = y + lift * y * (1 - y) * np.clip((y - 0.45) / 0.35, 0, 1) * 2
    k = 0.85
    hi = y > k
    y[hi] = k + (shoulder - k) * np.tanh((y[hi] - k) / (shoulder - k))
    return y


def solve(img, golden=False):
    """Grade params for one shot from a representative frame."""
    s = stats(img)
    lo, hi = (0.42, 0.49) if golden else (0.43, 0.51)          # golden: a little darker/warmer, never under 0.40
    target = min(max(s['lum'], lo), hi)
    a = np.asarray(img.convert('RGB').resize((270, 480))).astype(np.float32) / 255
    def mean_after(g, lift):
        lut = curve(g, lift=lift); return float((lut[(a * 255).astype(np.uint8)] @ LUM).mean())
    def p98_after(g, lift):
        lut = curve(g, lift=lift); return float(np.percentile(lut[(a * 255).astype(np.uint8)] @ LUM, 98))
    def solve_g(lift):
        g_lo, g_hi = 0.35, 2.5                                       # mean_after decreases as g grows
        for _ in range(30):
            g = (g_lo + g_hi) / 2
            if mean_after(g, lift) > target: g_lo = g
            else: g_hi = g
        return g
    lift = 0.0; g = solve_g(lift)
    for _ in range(3):                    # keep highlights up (p98 >= 0.88) and the mean on target together
        if p98_after(g, lift) >= 0.87: break
        for lift in np.arange(lift + 0.05, 0.8, 0.05):
            if p98_after(g, lift) >= 0.88: break
        g = solve_g(lift)
    # cool share (hue 180-270, sat > .35) over the reference's 0.35: warm the white balance a little
    hsv = np.asarray(img.convert('RGB').resize((270, 480)).convert('HSV')).astype(np.float32) / 255
    cool = float(((hsv[..., 0] > .5) & (hsv[..., 0] < .75) & (hsv[..., 1] > .35)).mean())
    warm = 0.0 if cool <= 0.28 else min(0.15, (cool - 0.28) * 1.0)
    sat = 1.0
    if s['sat'] > 0.50: sat = 0.47 / s['sat']
    elif s['sat'] < 0.33: sat = min(1.25, 0.36 / max(s['sat'], 1e-3))
    return {'gamma': round(g, 4), 'lift': round(float(lift), 3), 'warm': round(warm, 3), 'sat': round(sat, 3),
            'before': dict({k: round(v, 3) for k, v in s.items()}, cool=round(cool, 3))}


_luts = {}


def apply(img, p):
    if not p: return img
    key = (p['gamma'], p.get('lift', 0.0), p.get('warm', 0.0))
    if key not in _luts:
        base = curve(p['gamma'], lift=p.get('lift', 0.0)); w = p.get('warm', 0.0)
        chan = [np.clip(base * (1 + 0.4 * w), 0, 1), base, np.clip(base * (1 - w), 0, 1)]      # R up a touch, B down
        _luts[key] = [int(round(v * 255)) for c in chan for v in c]
    img = img.convert('RGB').point(_luts[key])
    if abs(p.get('sat', 1.0) - 1.0) > 0.01: img = ImageEnhance.Color(img).enhance(p['sat'])
    return img
