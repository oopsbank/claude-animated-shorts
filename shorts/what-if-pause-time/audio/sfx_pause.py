# Synthesized sound effects for "What If You Could Pause Time, But Only You Got Older?", event table locked to the
# picture (project/src/videos/pause/story.ts times). Own numpy synthesis from sfx_gen.py / dsp.py. Writes sfx.wav.
# The rule of the sound: when time is paused the world goes silent except for a thin glassy shimmer and his own sounds.
import numpy as np
from dsp import SR, ns, tt, rng, lp, hp, bp, colored, smooth_noise, fades, modal, pan, place, write_wav, phase
import sfx_gen as G
import instruments as I

DUR = 1935 / 30
N = ns(DUR)
out = np.zeros((2, N))
R = rng(1935)
r = lambda: rng(int(R.integers(1 << 30)))
TAU = 2 * np.pi

T_OLD, T_MON, T_ALARM, T_CLICK1, T_SLEEP, T_NOBODY = 2.69, 3.56, 4.42, 5.02, 7.4, 8.78
T_HOME, T_RACE, T_CAKE, T_MOUST, T_TEST, T_PAUSE2, T_STUDY, T_TOP = 10.14, 12.3, 13.29, 15.63, 17.14, 18.14, 18.79, 19.54
T_LATE, T_PAUSE3, T_STROLL, T_EARLY, T_MORNING, T_GREY = 20.4, 21.33, 21.87, 22.73, 25.41, 27.05
T_FROZEN, T_WERENT, T_NINE, T_WEEK, T_SIXTEEN, T_BODY, T_FRIENDS, T_MUM = 29.35, 30.61, 31.6, 32.35, 33.42, 34.87, 35.65, 37.83
T_STOP, T_BUS, T_SISTER, T_CLICK4, T_RUN, T_CARRY, T_MOVING, T_DRAWN, T_SAW, T_UNPAUSE = 40.03, 42.14, 43.47, 44.93, 46.84, 47.37, 50.49, 53.83, 60.39, 62.4
SHOT_F = [0, 105, 263, 302, 365, 397, 455, 513, 610, 698, 760, 840, 1000, 1066, 1132, 1198, 1262, 1302, 1345, 1372, 1470, 1548, 1612, 1675, 1703, 1760, 1935]
SH = [f / 30 for f in SHOT_F]


def add(x, t, g=1.0, p=0.0):
    x = np.asarray(x, float)
    place(out, pan(x, p) if x.ndim == 1 else x, t, g)


def env_seg(n, pts):
    t = np.arange(n) / SR
    return np.interp(t, [a for a, _ in pts], [b for _, b in pts])


def frozen(t):
    return (t < T_MON - 0.05) or (T_CLICK1 + 0.08 <= t < T_MORNING - 0.05 and not (T_TEST - 0.05 <= t < T_PAUSE2 + 0.08) and not (T_LATE - 0.05 <= t < T_PAUSE3 + 0.08)) \
        or (T_CLICK4 + 0.08 <= t < T_UNPAUSE + 0.05)


def click(rr, big=1.0):
    """the pause button: a hard plastic click"""
    t = tt(0.15)
    return (bp(rr.standard_normal(len(t)), 1800, 9000, 2) * np.exp(-t / 0.004) * 1.4 + np.exp(-t / 0.012) * np.sin(TAU * 900 * t) * 0.5) * big


def freeze(rr, up=False):
    """the world stopping: a falling 'zwoom' + a soft low thump + a glassy ring (reversed for play)"""
    t = tt(1.1)
    f = 900 * np.exp(-t / 0.18) + 70
    sw = np.sin(phase(f)) * np.exp(-t / 0.35) * 0.6
    th = np.sin(phase(55 * (1 + 0.5 * np.exp(-t / 0.03)))) * np.exp(-t / 0.2) * 1.0
    ring = modal(1.1, [(2637, 1, 0.6), (3951, 0.6, 0.45), (5274, 0.4, 0.3)], rr) * 0.25
    y = sw + th + ring
    if up:
        y = y[::-1] * np.minimum(1, np.linspace(0, 6, len(y)))
    return fades(y, 0.002, 0.05)


def shimmer(dur, rr):
    """the frozen world's tone: a thin high sustained glassy shimmer"""
    n = ns(dur)
    t = np.arange(n) / SR
    y = sum(a * np.sin(phase(np.full(n, f) * (1 + 0.002 * smooth_noise(n, rr, 0.5)))) for f, a in [(3136, 0.02), (4186, 0.012), (5274, 0.008)])
    y = y + bp(colored(n, rr, 0.0), 5000, 9000, 1) * 0.02
    return y * (0.8 + 0.2 * smooth_noise(n, rr, 0.3))


def city(dur, rr, birds=True):
    """street ambience: distant traffic rumble + a few birds"""
    n = ns(dur)
    y = lp(colored(n, rr, 1.2), 500, 2) * 0.5 + bp(colored(n, rr, 0.5), 300, 2500, 1) * 0.15
    y = np.stack([y, np.roll(y, 311)])
    if birds:
        b = G.bird_chirps(dur, rr, 0.35)
        y = y + (np.stack([b, np.roll(b, 200)]) if b.ndim == 1 else b) * 0.5
    return y


def room(dur, rr):
    n = ns(dur)
    y = lp(colored(n, rr, 1.0), 300, 2) * 0.12
    return np.stack([y, np.roll(y, 211)])


def bell(dur, rr):
    """an alarm clock's bell: a hammer hitting two bells at ~18 Hz"""
    n = ns(dur)
    y = np.zeros(n)
    for k, tm in enumerate(np.arange(0, dur - 0.05, 1 / 18)):
        m = modal(0.12, [(2350 if k % 2 else 2620, 1, 0.05), (5900, 0.5, 0.03)], rr)
        i = ns(tm); y[i:i + len(m)] += m[:n - i] * 0.8
    return fades(y, 0.005, 0.03)


def snore(rr):
    t = tt(1.1)
    e = np.sin(np.pi * np.clip(t / 0.9, 0, 1)) ** 2
    y = lp(rr.standard_normal(len(t)), 600) * (0.6 + 0.4 * np.sign(np.sin(phase(np.full(len(t), 32.0))))) * e
    return y * 0.8


def scribble(dur, rr, rate=9):
    n = ns(dur)
    g = 0.5 + 0.5 * np.sin(phase(np.full(n, rate) + 4 * smooth_noise(n, rr, 3)))
    return bp(rr.standard_normal(n), 2500, 8000, 2) * g ** 2 * 0.25


def flutter(dur, rr, rate=24):
    n = ns(dur)
    y = bp(rr.standard_normal(n), 1500, 6000, 1) * (0.5 + 0.5 * np.sign(np.sin(phase(rate + 6 * smooth_noise(n, rr, 3.0)))))
    return fades(y * 0.15, 0.05, 0.1)


def chomp(rr):
    t = tt(0.22)
    return lp(rr.standard_normal(len(t)), 900) * np.exp(-t / 0.05) * 0.9 + bp(rr.standard_normal(len(t)), 2000, 6000, 1) * np.exp(-t / 0.02) * 0.3


def squeak(rr, dur=0.35, f0=2200):
    t = tt(dur)
    f = f0 + 500 * np.sin(TAU * 7 * t) + 300 * smooth_noise(len(t), rr, 20)
    return fades(np.sin(phase(f)) * 0.12 + bp(rr.standard_normal(len(t)), 2500, 6000, 1) * 0.08, 0.01, 0.03)


def boing(rr):
    t = tt(0.7)
    f = 330 * (1 + 0.35 * np.sin(TAU * 11 * t) * np.exp(-t / 0.25))
    return np.sin(phase(f)) * np.exp(-t / 0.3) * 0.6


def tick(rr, hi=True):
    t = tt(0.05)
    return bp(rr.standard_normal(len(t)), 2500 if hi else 1500, 9000, 2) * np.exp(-t / 0.004) * 0.7


def pop(rr, f=900):
    t = tt(0.12)
    return np.sin(phase(f * (1 + 0.8 * np.exp(-t / 0.01)))) * np.exp(-t / 0.03) * 0.6


def laugh(rr, base, dur=1.8, scale=1.0):
    """a burst of 'ha-ha-ha' from the additive voice"""
    n = ns(dur)
    t = np.arange(n) / SR
    rate = 5.5 + rr.uniform(-0.5, 0.5)
    gate = np.clip(np.sin(TAU * rate * t), 0, 1) ** 0.6 * np.exp(-t / (dur * 0.8))
    f0 = base * (1.25 - 0.3 * t / dur) * (1 + 0.04 * np.sin(TAU * rate * t))
    forms = np.tile(np.array(G.VOW["a"], float), (n, 1))
    y = G.vox(f0, forms, gate, rr, scale, breath=0.35, fmax=4000)
    return y * 0.25


def diesel(dur, rr, pts):
    n = ns(dur)
    e = env_seg(n, pts)
    t = np.arange(n) / SR
    f = 38 + 20 * np.clip(t / dur, 0, 1)
    y = lp(np.sign(np.sin(phase(f))) * 0.4 + colored(n, rr, 1.0) * 0.6, 700, 2) * e
    return np.stack([y, np.roll(y, 177)])


def horn(dur=0.7):
    t = tt(dur)
    y = sum(np.sign(np.sin(TAU * f * t)) * 0.12 for f in (330, 415))
    return fades(lp(y, 2500, 2), 0.01, 0.05)


# ================================================================ ambience
# street / room tone only while the world plays; the shimmer while it is frozen (and never in the studio)
sh = shimmer(DUR, r())
fz = np.array([1.0 if frozen(k / 100) and not (SH[11] <= k / 100 < SH[13]) else 0.0 for k in range(int(DUR * 100) + 1)])
fz = np.convolve(fz, np.ones(5) / 5, mode="same")
mask = np.interp(np.arange(N) / SR, np.arange(len(fz)) / 100, fz)
add(np.stack([sh * mask, np.roll(sh * mask, 97)]), 0, 0.9)
add(room(T_CLICK1 - SH[1] + 0.05, r()), SH[1], 0.8)
add(G.bird_chirps(T_CLICK1 - SH[1], r(), 0.4) * 0.3, SH[1], 0.5, -0.3)
add(room(SH[12] - T_MORNING, r()), T_MORNING, 0.8)          # mirror .. maths
add(room(SH[15] - SH[13] + 0.6, r()), SH[13], 0.6)           # friends, mum
add(room(SH[16] - SH[15], r()), SH[15], 0.8)
add(G.babble(T_PAUSE2 - SH[7], r(), 170, 1.1) * 0.3, SH[7], 0.35, 0.3)   # class chatter until the pause
add(G.babble(T_PAUSE2 - SH[7], r(), 230, 1.2) * 0.3, SH[7] + 0.2, 0.3, -0.3)
add(city(T_PAUSE3 - SH[8], r(), False), SH[8], 0.5)
add(city(T_CLICK4 - SH[16] + 0.05, r()), SH[16], 0.6)
add(city(DUR - T_UNPAUSE, r()), T_UNPAUSE, 0.7)
add(G.babble(2.0, r(), 200, 1.1) * 0.3, SH[13], 0.25, -0.3)

# ================================================================ events
# 1 hook: frozen; a clock ticking fast and a warping sweep as he ages
for k, tm in enumerate(np.arange(0.2, T_OLD, 0.5)):
    add(tick(r(), k % 2 == 0), tm, 0.25)
for k, tm in enumerate(np.arange(T_OLD, 3.4, 0.06)):
    add(tick(r(), k % 2 == 0), tm, 0.2)
t = tt(0.9)
add(np.sin(phase(600 * np.exp(-t / 0.4) + 120)) * np.exp(-t / 0.5) * 0.35, T_OLD, 0.6)
add(G.whoosh(0.7, r(), peak=0.12, f_lo=600, f_hi=3000, tail=0.15), SH[1] - 0.08, 0.35)
# 2 alarm, click, the world stops, snoring
add(bell(T_CLICK1 - T_ALARM, r()), T_ALARM, 0.45, -0.3)
for tc, g in [(T_CLICK1, 1.0), (T_PAUSE2, 0.9), (T_PAUSE3, 0.9), (T_CLICK4, 1.1)]:
    add(click(r()), tc - 0.02, 0.6 * g)
    add(freeze(r()), tc, 0.7 * g)
for k, tm in enumerate(np.arange(T_SLEEP + 0.5, SH[2] - 0.4, 1.4)):
    add(snore(r()), tm, 0.35, -0.2)
add(G.whoosh(0.5, r(), peak=0.1, f_lo=300, f_hi=1500), T_SLEEP - 0.05, 0.25)  # flops back
# 4 homework: frantic pencil + pages
add(scribble(SH[4] - SH[3], r(), 11), SH[3], 0.5, 0.2)
add(flutter(SH[4] - SH[3] - 0.3, r(), 30), SH[3] + 0.2, 0.6, -0.2)
# 5 the race: his easy footsteps among frozen runners, the tape
for tm in np.arange(T_RACE - 0.2, SH[5], 0.3):
    add(G.stroll_step(r(), 0.5), tm, 0.3)
add(pop(r(), 500), 12.95, 0.3)
# 6 cakes: chomps
for k, tm in enumerate(np.arange(T_CAKE + 0.1, SH[6] - 0.1, 0.42)):
    add(chomp(r()), tm, 0.45)
# 7 the marker squeaks
for k, tm in enumerate([15.6, 15.95, 16.3, 16.6]):
    add(squeak(r(), 0.3, 2000 + 250 * k), tm, 0.35, 0.2)
# 8 study: pages + pencil, then top marks
add(flutter(T_TOP - T_STUDY - 0.1, r(), 34), T_STUDY, 0.6)
add(scribble(T_TOP - T_STUDY - 0.1, r(), 13), T_STUDY, 0.5)
add(I.glock(I.m2f(96), 0.7, r()), T_TOP - 0.02, 0.35)
for k in range(3): add(G.clink(r(), 5200 + 700 * k, 0.4, 1.4), T_TOP + 0.08 * k, 0.12)
# 9 late: running steps + a school bell far off, then the stroll
for tm in np.arange(SH[8] + 0.1, T_PAUSE3, 0.17):
    add(G.stroll_step(r(), 0.8), tm, 0.3)
add(bell(T_PAUSE3 - SH[8], r()) * 0.4, SH[8], 0.25, 0.4)
for tm in np.arange(T_STROLL - 0.1, SH[9], 0.45):
    add(G.stroll_step(r(), 0.4), tm, 0.28)
add(I.glock(I.m2f(91), 0.6, r()), T_EARLY, 0.3)
for k in range(3): add(G.clink(r(), 5000 + 600 * k, 0.4, 1.4), T_EARLY + 0.07 * k, 0.1)
# 10 perfect: a contented creak of the bed
add(G.creak(0.5, r(), 120, 160) * 0.3, SH[9] + 0.2, 0.3)
# 11 the mirror: brushing, then the grey hair boings
for k, tm in enumerate(np.arange(SH[10] + 0.1, T_GREY - 0.1, 0.16)):
    n = ns(0.12); add(bp(r().standard_normal(n), 2000, 7000, 1) * np.sin(np.pi * np.arange(n) / n) * 0.25, tm, 0.4, 0.1 if k % 2 else -0.1)
add(boing(r()), T_GREY, 0.5)
# 12 the maths: clocks ticking; frozen clocks pop in; his clock whirring; hourglass pops
for k, tm in enumerate(np.arange(SH[11] + 0.1, T_WERENT, 0.5)):
    add(tick(r(), k % 2 == 0), tm, 0.25)
for k in range(6): add(pop(r(), 700 + 60 * k), T_FROZEN - 0.1 + 0.06 * k, 0.25)
for k, tm in enumerate(np.arange(T_WERENT, SH[12] - 0.2, 0.07)):
    add(tick(r(), k % 2 == 0), tm, 0.16)
for k, tk in enumerate([T_NINE, T_NINE + 0.25, T_WEEK, T_WEEK + 0.15, T_WEEK + 0.3, T_WEEK + 0.45]):
    add(pop(r(), 500 + 80 * k), tk, 0.35)
# 13 sixteen: a party blower; twenty-six: a low thud
t = tt(0.5); add(lp(np.sign(np.sin(phase(np.full(len(t), 420.0) + 60 * np.sin(TAU * 6 * t)))), 2000) * 0.12 * np.minimum(1, t / 0.03) * np.exp(-t / 0.4), T_SIXTEEN + 0.1, 0.4)
add(np.sin(phase(np.full(ns(0.5), 60.0))) * np.exp(-tt(0.5) / 0.15) * 1.0, T_BODY - 0.03, 0.5)
# 14 friends laughing
add(laugh(r(), 190, 2.0), T_FRIENDS + 0.4, 0.6, -0.4)
add(laugh(r(), 240, 1.8, 1.1), T_FRIENDS + 0.6, 0.55, 0.4)
# 16 the remote dropped into the box
add(lp(r().standard_normal(ns(0.25)), 600) * np.exp(-tt(0.25) / 0.04) * 1.2, T_STOP + 0.8, 0.45)
add(G.clink(r(), 1400, 0.1), T_STOP + 0.8, 0.2)
# 17-18 the bus: diesel roaring closer, a horn
add(diesel(T_CLICK4 - T_BUS + 1.0, r(), [(0, 0.2), (T_CLICK4 - T_BUS - 1.0, 0.9), (T_CLICK4 - T_BUS, 1.2), (T_CLICK4 - T_BUS + 0.05, 0.0), (9, 0)]), T_BUS, 0.9)
add(horn(0.9), T_SISTER + 0.2, 0.4)
add(horn(0.5), T_SISTER + 1.2, 0.45)
# 20 he runs out, carries her
for tm in np.arange(T_RUN - 0.05, T_CARRY, 0.16):
    add(G.stroll_step(r(), 0.9), tm, 0.35)
for tm in np.arange(T_CARRY + 0.1, 48.6, 0.32):
    add(G.stroll_step(r(), 0.6), tm, 0.3)
# 21-25 someone else moving: slow old footsteps in the silence
for tm in list(np.arange(T_MOVING - 0.3, T_DRAWN - 0.3, 0.62)) + list(np.arange(57.0, 58.6, 0.62)):
    add(G.stroll_step(r(), 0.3), tm, 0.22, 0.3)
# 26 "I saw that." ... play: the world rushes back, the bus whooshes past, pigeons take off, a horn
add(click(r()), T_UNPAUSE - 0.02, 0.6)
add(freeze(r(), True), T_UNPAUSE - 1.05, 0.7)
add(diesel(2.5, r(), [(0, 1.2), (1.0, 0.8), (2.5, 0.0)]), T_UNPAUSE, 0.8)
add(G.whoosh(1.6, r(), peak=0.35, f_lo=200, f_hi=2600, tail=0.6), T_UNPAUSE + 0.05, 0.9, 0.4)
add(horn(0.6), T_UNPAUSE + 0.3, 0.3)
for k in range(10):
    n = ns(0.08); add(bp(r().standard_normal(n), 400, 2500, 1) * np.exp(-np.arange(n) / SR / 0.02), T_UNPAUSE + 0.1 + 0.07 * k, 0.25, 0.3)

out = hp(out, 30, 2)
write_wav("sfx.wav", out, 24)
print("sfx.wav", out.shape[1] / SR, "s, peak", np.abs(out).max())
