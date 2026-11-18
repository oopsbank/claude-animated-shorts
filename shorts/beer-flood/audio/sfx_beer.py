# Synthesized sound effects for "The Street That Drowned in Beer", event table locked to the picture
# (project/src/videos/beer/story.ts times). Own numpy synthesis from sfx_gen.py / dsp.py. Writes sfx.wav (stereo, 48 kHz).
import numpy as np
from dsp import SR, ns, tt, rng, lp, hp, bp, colored, smooth_noise, fades, modal, pan, place, write_wav, phase, shape
import sfx_gen as G

DUR = 1948 / 30
N = ns(DUR)
out = np.zeros((2, N))
R = rng(1814)
r = lambda: rng(int(R.integers(1 << 30)))


def add(x, t, g=1.0, p=0.0):
    x = np.asarray(x, float)
    place(out, pan(x, p) if x.ndim == 1 else x, t, g)


def env_seg(n, pts):
    t = np.arange(n) / SR
    return np.interp(t, [a for a, _ in pts], [b for _, b in pts])


# ---- story times (story.ts) ----
T_SLIP, T_WRITE, TB, T_WALL, TW = 17.6, 18.3, [21.7, 22.74, 24.8], 26.06, 26.3
T_POP, T_GAVEL, T_BLAME, T_HAND, T_SEVEN, T_FALL, T_RUN = 46.74, 48.68, 49.62, 51.98, 55.98, 61.38, 62.3
FLASH = 132 / 30


def roar(dur, rr, level_pts, bright=1600):
    """rushing beer: low surge + foamy hiss, level follows level_pts [(t, gain)]"""
    n = ns(dur)
    e = env_seg(n, level_pts)
    lo = lp(colored(n, rr, 1.6), 260, 2) * 1.2
    mid = bp(colored(n, rr, 0.6), 250, bright, 1) * (0.7 + 0.3 * smooth_noise(n, rr, 2.0))
    fizz = hp(colored(n, rr, 0.0), 3500) * 0.08 * (0.6 + 0.4 * smooth_noise(n, rr, 6.0))
    bub = G.bubbles(dur, rr, 140, 300, 2600, (0.005, 0.02)) * 0.5
    y = (lo + mid + fizz + bub) * e
    return np.stack([y, np.roll(y, 311) * 0.9 + 0.1 * y])


def brick_fall(rr, dur=1.6):
    """the breach: groan, a tumbling clatter of bricks, a heavy thud"""
    n = ns(dur)
    y = np.zeros(n)
    tm = 0.05
    while tm < dur - 0.2:
        k = modal(0.18, [(rr.uniform(300, 900), 1.0, 0.03), (rr.uniform(1100, 2600), 0.5, 0.012)], rr)
        k += bp(rr.standard_normal(ns(0.18)), 400, 3500, 1) * np.exp(-tt(0.18) / 0.01) * 0.8
        G._place_mono(y, k * rr.uniform(0.3, 1.0), tm)
        tm += rr.exponential(1 / (40 * np.exp(-tm / 0.7) + 6))
    t = np.arange(n) / SR
    thud = np.exp(-np.maximum(t - 0.55, 0) / 0.35) * (t > 0.55) * np.sin(phase(48 + 0 * t)) * 2.2
    groan = G.creak(0.6, rr, 22, 40, G.TIMBER, [(0, 0), (0.5, 1), (1, 0)], rough=0.3, noise=0.1) * 0.5
    G._place_mono(y, groan, 0.0)
    return y + thud


def coin_jingle(rr, dur=0.8, density=40):
    y = np.zeros(ns(dur))
    tm = 0.0
    while tm < dur - 0.12:
        G._place_mono(y, G.clink(rr, rr.uniform(2600, 5200), 0.12, 1.2) * rr.uniform(0.3, 1.0), tm)
        tm += rr.exponential(1 / (density * np.exp(-tm / (dur * 0.6))))
    return y


def iron_clang(rr):
    """a 700 lb hoop hitting stone: deep ring + rattle wobble"""
    y = modal(2.5, [(92, 1.0, 1.4), (241, 0.7, 0.9), (455, 0.5, 0.6), (733, 0.35, 0.4), (1100, 0.2, 0.25)], rr)
    t = tt(2.5)
    y += lp(rr.standard_normal(len(t)), 400) * np.exp(-t / 0.04) * 1.5
    wob = np.zeros(len(t))
    for k in range(10):  # the hoop settling: rattling taps speeding up
        tk = 0.35 + 0.9 * (1 - 0.82 ** k)
        G._place_mono(wob, modal(0.2, [(330, 1, 0.08), (800, 0.6, 0.05)], rr) * 0.35 * 0.85 ** k, tk)
    return y + wob


def quill(rr, dur):
    n = ns(dur)
    s = hp(colored(n, rr, 0.0), 2500) * (0.5 + 0.5 * np.sign(np.sin(TAU_ * np.arange(n) / SR * 5.5))) * 0.12
    return fades(s, 0.02, 0.05)


TAU_ = 2 * np.pi

# ================================================================ events
# hook: the wave coming down the street, crashing at "Of beer."
add(roar(4.9, r(), [(0, 0.15), (2.5, 0.6), (3.2, 1.0), (4.0, 0.7), (4.9, 0.0)]), 0.0, 0.55)
add(G.whoosh(1.4, r(), peak=1.15, f_lo=300, f_hi=2400, tail=0.12), 2.0, 0.6, 0.0)
add(G.splash_big(r()), 3.25, 0.8)
add(G.whoosh(0.7, r(), peak=0.12, f_lo=600, f_hi=3000, tail=0.15), FLASH - 0.08, 0.35)

# the yard: breeze, birds, a cart wheel far off, footsteps
add(G.breeze(16.6, r(), 0.6), 4.4, 0.35)
add(G.bird_chirps(16.4, r(), 0.4), 4.4, 0.25)
for k, tm in enumerate(np.arange(3.7, 11.5, 0.6)):  # the worker crossing the yard
    add(G.stroll_step(r(), 0.4), tm, 0.12, 0.3 - 0.06 * k)
for tm in np.arange(12.65, 14.6, 0.56):  # George walking in
    add(G.stroll_step(r(), 0.5), tm, 0.35, 0.1)
add(modal(1.2, [(118, 1.0, 0.5), (305, 0.6, 0.3), (590, 0.4, 0.2)], r()), T_SLIP, 0.55)  # the hoop clunks lower
add(G.clink(r(), 900, 0.3), T_SLIP + 0.01, 0.4)
add(quill(r(), 0.9), T_WRITE, 0.5, -0.1)

# an hour later: the vat groans, spurts hiss
add(G.creak(0.95, r(), 25, 60, G.TIMBER, [(0, 0.2), (0.5, 1), (1, 0.6)], rough=0.25, noise=0.08), 20.8, 0.6)
add(hp(colored(ns(0.6), r(), 0.0), 2500) * np.linspace(0, 1, ns(0.6)) * 0.25, 21.12, 0.6, 0.2)
# the bursts
for i, tb in enumerate(TB):
    g = [1.0, 0.75, 0.7][i]
    add(G.wood_crack(r()), tb, 0.9 * g, [0.0, -0.4, 0.4][i])
    add(G.splash_big(r()), tb + 0.05, 0.8 * g, [0.0, -0.3, 0.3][i])
    add(G.whoosh(0.9, r(), peak=0.08, f_lo=400, f_hi=2600, tail=0.3, air=0.3), tb - 0.02, 0.4 * g)
    for k in range(6):  # staves clattering down
        add(modal(0.25, [(R.uniform(250, 600), 1, 0.06), (R.uniform(900, 1800), 0.6, 0.03)], r()), tb + 0.45 + k * R.uniform(0.06, 0.16), 0.25 * g, R.uniform(-0.6, 0.6))
add(G.creak(0.6, r(), 30, 70, G.TIMBER, [(0, 0), (0.6, 1), (1, 0.3)], rough=0.3), TB[1] - 0.55, 0.5, -0.4)
add(G.creak(0.6, r(), 30, 70, G.TIMBER, [(0, 0), (0.6, 1), (1, 0.3)], rough=0.3), TB[2] - 0.55, 0.5, 0.4)
add(roar(11.5, r(), [(0, 0.0), (0.3, 0.8), (3.5, 0.75), (4.4, 0.9), (6.5, 1.0), (9.5, 0.7), (11.5, 0.0)]), 21.75, 0.5)
# the wall
add(brick_fall(r()), T_WALL - 0.05, 0.9)
add(G.splash_big(r()), TW + 0.1, 0.6)
# St Giles: the wave in the street, beer pouring into the cellar
add(G.water_bed(5.2, r(), 1.0, 1.2), 30.6, 0.35)
# the quiet after: only lapping
add(G.water_bed(4.4, r(), 0.4, 0.4), 32.9, 0.22)
# explanation: soft pops as the arrows grow
for tm in [39.27, 40.25, 41.03]:
    add(G.whoosh(0.5, r(), peak=0.15, f_lo=200, f_hi=900, tail=0.15, air=0.0), tm - 0.1, 0.25)
# dinner: cutlery, the belt straining, pop!
for tm in np.arange(42.2, 44.2, 1.5):
    add(G.clink(r(), 2400, 0.15), tm, 0.25, 0.1)
add(G.creak(1.6, r(), 40, 120, G.WOOD, [(0, 0), (0.3, 0.6), (1, 1)], rough=0.2, noise=0.05) * 0.6, 44.4, 0.45)
t_ = tt(0.25)
add(np.exp(-t_ / 0.03) * np.sin(phase(180 * (1 + 2 * np.exp(-t_ / 0.01)))) * 1.5, T_POP, 0.6)
add(G.whoosh(0.4, r(), peak=0.05, f_lo=800, f_hi=3500, tail=0.1), T_POP, 0.3)
add(G.clink(r(), 1800, 0.4), T_POP + 0.42, 0.5, 0.4)
add(G.clink(r(), 2100, 0.3), T_POP + 0.58, 0.3, 0.5)
# court: hush, the gavel twice
add(G.babble(2.0, r(), 140, 1.0) * 0.3, 47.3, 0.25, -0.3)
for tm in [T_GAVEL, T_BLAME]:
    add(G.hammer_hit(r(), 1.2), tm, 0.8)
# the refund: a heavy bag lands, coins
add(lp(r().standard_normal(ns(0.3)), 300) * np.exp(-tt(0.3) / 0.05) * 1.2, T_HAND + 0.15, 0.6)
add(coin_jingle(r(), 0.5, 30), T_HAND + 0.17, 0.35)
add(coin_jingle(r(), 1.0, 60), T_SEVEN - 0.05, 0.45, 0.2)
# the lesson: yard again, then the hoop falls
add(G.breeze(4.6, r(), 0.6), 57.6, 0.3)
add(G.bird_chirps(3.6, r(), 0.5), 57.6, 0.2)
add(G.whoosh(0.4, r(), peak=0.3, f_lo=200, f_hi=1200, tail=0.05), T_FALL - 0.02, 0.4)
add(iron_clang(r()), T_FALL + 0.31, 1.0)
# not fine: everybody runs
for k in range(4):
    add(G.whoa(r()), T_RUN + 0.05 + 0.12 * k, 0.3, R.uniform(-0.5, 0.5))
    for tm in np.arange(T_RUN + 0.1 + 0.05 * k, T_RUN + 2.3, 0.16):
        add(G.stroll_step(r(), 0.8), tm, 0.12, 0.6 * (k % 2 * 2 - 1) * 0.5)

out = hp(out, 35, 2)
write_wav("sfx.wav", out, 24)
print("sfx.wav", out.shape[1] / SR, "s, peak", np.abs(out).max())
