# Night-house foley for "night-intruder" (own numpy synthesis on the template dsp.py / sfx_gen.py): clock ticks,
# a metal drop on tiles, door-gap wind, a dragged chair, heartbeat, breathing / panting, zips, backpack rummaging,
# a plastic crack, crowbar whoosh + clang on a wall, a lamp hitting an arm, a bar clattering and rolling on tiles,
# bodies and cloth on tiles, a door latch / creak / slam, street spill, hard shoe soles, a running-away exit.
# Every generator takes an rng and returns mono (n,) or stereo (2, n) float audio at 48 kHz; levels are set by the mixer.
import numpy as np
from dsp import (SR, TAU, ns, tt, lp, hp, bp, peq, colored, smooth_noise, fades, phase, modal, pan, place, resbank)
import sfx_gen as G


def _env(n, pts):
    u = np.arange(n) / SR
    return np.interp(u, [p[0] for p in pts], [p[1] for p in pts])


def _add(buf, x, t):
    i = ns(t)
    a, b = max(0, i), min(len(buf), i + len(x))
    if b > a:
        buf[a:b] += x[a - i: b - i]


def _norm(x):
    return x / (np.abs(x).max() + 1e-12)


# ---------------------------------------------------------------- bedroom
def clock_ticks(r, dur=4.0, period=1.0, first=0.12):
    """a wall clock: alternating tick / tock (small escapement clicks + a woody case knock)"""
    y = np.zeros(ns(dur))
    t, k = first, 0
    while t < dur:
        f = 3300 if k % 2 == 0 else 2750
        d = 0.09
        tc = tt(d)
        click = modal(d, [(f, 1.0, 0.006), (f * 1.73, 0.5, 0.004), (f * 0.41, 0.35, 0.012)], r)
        knock = modal(d, [(410, 0.5, 0.018), (980, 0.3, 0.01)], r)
        nz = bp(r.standard_normal(len(tc)), 2000, 9000, 1) * np.exp(-tc / 0.0015)
        _add(y, (click + knock + 0.8 * nz) * (1.0 if k % 2 == 0 else 0.85), t)
        t += period * (1 + r.normal(0, 0.002))
        k += 1
    return y


def metal_drop(r):
    """a small metal tool dropped on tiles downstairs: hard clack + two short bounces, quick ring"""
    d = 0.9
    y = np.zeros(ns(d))
    for i, (at, a) in enumerate([(0.0, 1.0), (0.11, 0.45), (0.19, 0.2)]):
        tc = tt(0.5)
        ring = modal(0.5, [(1320, 0.6, 0.05), (3480, 0.5, 0.03), (6100, 0.3, 0.012), (870, 0.3, 0.02)], r)
        hit = bp(r.standard_normal(len(tc)), 1200, 9000, 1) * np.exp(-tc / 0.002) * 2.0
        tile = modal(0.5, [(2300, 0.4, 0.008), (640, 0.4, 0.012)], r)
        _add(y, (ring + hit + tile) * a, at)
    return fades(y, 0, 0.1)


def door_gap_wind(r, dur=1.4):
    """wind whistling thinly through a door gap: a narrow wavering whistle over a soft hush"""
    n = ns(dur)
    t = np.arange(n) / SR
    w = smooth_noise(n, r, 1.5)
    f = 980 + 160 * w + 60 * smooth_noise(n, r, 6.0)
    whistle = np.sin(phase(f)) * (0.6 + 0.4 * smooth_noise(n, r, 3.0))
    whistle += 0.35 * np.sin(phase(f * 1.5)) * (0.5 + 0.5 * smooth_noise(n, r, 2.0))
    hush = bp(colored(n, r, 1.0), 250, 2200, 1) * 0.9
    nz = resbank(r.standard_normal(n), [(1000, 30, 1.0)])
    env = np.clip(np.sin(np.pi * t / dur), 0, 1) ** 1.3
    return fades((0.35 * whistle + hush + 0.2 * nz / (np.std(nz) + 1e-9)) * env, 0.05, 0.2)


def chair_screech(r, dur=0.5):
    """a wooden chair leg dragged across a floor: rough stick-slip screech with a pitch bend"""
    base = G.creak(dur, r, rate0=r.uniform(260, 320), rate1=r.uniform(420, 520), modes=G.WOOD, scale=1.6, rough=0.2,
                   noise=0.15, shape_pts=[(0, 0), (0.1, 1), (0.75, 0.9), (1.0, 0)])
    n = len(base)
    grit = bp(r.standard_normal(n), 900, 5000, 1) * _env(n, [(0, 0), (0.05, 0.6), (dur * 0.8, 0.5), (dur, 0)])
    thud = np.zeros(n)
    _add(thud, modal(0.2, [(140, 1.0, 0.03), (310, 0.5, 0.02)], r), 0.0)
    return fades(_norm(base) + 0.25 * grit + 0.5 * thud, 0.003, 0.05)


def heartbeat(r, dur, bpm0=60, bpm1=108, a0=0.35, a1=1.0):
    """dull low heartbeat (lub-dub) rising in rate and level; harmonics up to ~250 Hz so phones still hear it"""
    n = ns(dur)
    y = np.zeros(n)
    t = 0.15
    while t < dur - 0.4:
        u = t / dur
        bpm = bpm0 + (bpm1 - bpm0) * u ** 1.3
        a = a0 + (a1 - a0) * u ** 1.2
        for off, f, g, tau in ((0.0, 52, 1.0, 0.07), (0.23 - 0.07 * u, 64, 0.62, 0.055)):
            d = 0.4
            tc = tt(d)
            body = np.sin(phase(f * (1 + 0.5 * np.exp(-tc / 0.015)))) * (1 - np.exp(-tc / 0.006)) * np.exp(-tc / tau)
            body += 0.35 * np.sin(phase(2.1 * f * (1 + 0.4 * np.exp(-tc / 0.01)))) * np.exp(-tc / (tau * 0.6))
            thump = lp(r.standard_normal(len(tc)), 260, 2) * np.exp(-tc / 0.012) * 0.6
            _add(y, (body + thump) * g * a, t + off)
        t += 60.0 / bpm
    return y


def breath(r, kind="in", dur=0.5, f1=700, f2=1300, rasp=0.0, voice=0.0, f0=110):
    """one breath: shaped noise through two formants; 'in' ramps up, 'out' bursts and decays; rasp = throat flutter"""
    n = ns(dur)
    t = np.arange(n) / SR
    z = r.standard_normal(n)
    x = bp(z, 250, 6000, 1)
    x = peq(peq(x, f1, 9, 2.0), f2, 7, 2.0)
    x = peq(x, 3200, -5, 1.0)
    if kind == "in":
        env = _env(n, [(0, 0), (dur * 0.7, 1.0), (dur, 0)]) ** 1.2
        x = hp(x, 600) * 0.8
    else:
        env = _env(n, [(0, 0), (0.025, 1.0), (dur * 0.5, 0.6), (dur, 0)])
    if rasp:
        x *= 1 + rasp * np.sin(TAU * r.uniform(40, 70) * t + r.uniform(0, TAU))
    if voice:
        v = np.sin(phase(np.full(n, f0) * (1 - 0.1 * t / dur)))
        v = bp(v + 0.3 * np.sign(v), 80, 1600, 1)
        x = x / (np.std(x) + 1e-9) + voice * v / (np.std(v) + 1e-9)
    return fades(x * env, 0.005, 0.02)


def breathing(r, dur, rate0=0.6, rate1=0.6, hard=0.3, f_shift=1.0, held=False, f0=110):
    """a breathing line: in/out pairs; rate in breaths/s glides rate0 -> rate1; hard 0..1 adds voice and rasp.
    held=True: shallow, shaky, controlled (holding his breath on the stairs)"""
    n = ns(dur)
    y = np.zeros(n)
    t = r.uniform(0, 0.15)
    while t < dur:
        u = t / dur
        rate = rate0 + (rate1 - rate0) * u
        per = 1.0 / rate * r.uniform(0.9, 1.1)
        f1, f2 = 650 * f_shift * r.uniform(0.92, 1.08), 1250 * f_shift * r.uniform(0.92, 1.08)
        di = per * (0.42 if not held else 0.5)
        do = per * 0.45
        ai = (0.45 + 0.25 * hard) * (0.6 if held else 1.0)
        ao = 1.0 * (0.55 if held else 1.0)
        bi = breath(r, "in", di, f1 * 1.1, f2 * 1.1, rasp=0.4 if held else 0.15 * hard, voice=0.0)
        if held:  # shaky: the inhale stutters
            bi *= 1 + 0.6 * np.sin(TAU * r.uniform(7, 11) * np.arange(len(bi)) / SR)
        bo = breath(r, "out", do, f1, f2, rasp=0.25 * hard, voice=0.35 * hard, f0=f0 * r.uniform(0.95, 1.05))
        _add(y, bi * ai, t)
        _add(y, bo * ao, t + di * 0.95)
        t += per
    return fades(y, 0.05, 0.1)


def groan(r, dur=0.8, base=95, kind="pain"):
    """a low male groan through clenched teeth (pain), or a strained 'hnn' (effort)"""
    n = ns(dur)
    t = np.arange(n) / SR
    if kind == "pain":
        f0 = base * G._track(n, [(0, 1.25), (0.08, 1.35), (dur * 0.6, 1.0), (dur, 0.8)], t)
        forms = G.vowel_track(n, [(0, "A"), (dur * 0.5, "er"), (dur, "U")])
        amp = np.clip(t / 0.03, 0, 1) * _env(n, [(0, 1), (dur * 0.4, 0.85), (dur, 0)])
    else:
        f0 = base * G._track(n, [(0, 1.1), (dur, 1.25)], t)
        forms = G.vowel_track(n, [(0, "U"), (dur, "U")])
        amp = np.clip(t / 0.02, 0, 1) * _env(n, [(0, 1), (dur * 0.7, 0.9), (dur, 0)])
    y = G.vox(f0, forms, amp, r, 0.92, tilt=1.2, breath=0.6, fmax=4000, jitter=0.03)
    y *= 1 + 0.3 * np.sin(TAU * 31 * t)  # vocal fry roughness
    return fades(lp(y, 3500, 2), 0.01, 0.06)


# ---------------------------------------------------------------- the thief's bag
def zip_pull(r, dur=0.45, rate0=120, rate1=420, sharp=1.0):
    """zipper: a train of tooth clicks through a small resonant pull tab + fabric hiss"""
    n = ns(dur)
    t = np.arange(n) / SR
    rate = rate0 + (rate1 - rate0) * (t / dur) ** 0.6 if sharp >= 1 else rate0 + (rate1 - rate0) * np.sin(np.pi * t / dur)
    x = G.stick_slip(dur, rate, r, jitter=0.15, amp=_env(n, [(0, 0.3), (0.04, 1), (dur * 0.85, 1), (dur, 0.2)]))
    teeth = resbank(x, [(2600, 6, 1.0), (4300, 7, 0.7), (6800, 8, 0.45), (1500, 5, 0.4)])
    hiss = bp(r.standard_normal(n), 2500, 9000, 1) * _env(n, [(0, 0), (0.03, 0.5), (dur, 0.2)]) * 0.15
    y = teeth / (np.abs(teeth).max() + 1e-9) + hiss
    if sharp >= 1:  # the decisive zip ends on the slider hitting the stop
        stop = modal(0.12, [(3900, 1.0, 0.01), (6100, 0.6, 0.006)], r)
        y = np.concatenate([y, np.zeros(ns(0.12))])
        _add(y, stop * 0.9, dur - 0.01)
    return fades(y, 0.002, 0.03)


def rustle(r, dur=0.3, bright=1.0):
    """one grab of nylon / cloth: crinkly noise burst"""
    n = ns(dur)
    t = np.arange(n) / SR
    z = r.standard_normal(n) * (np.abs(r.standard_normal(n)) > 1.2)  # crackly
    c = bp(z, 1200 * bright, 8000, 1) * 0.8 + bp(r.standard_normal(n), 500, 3000, 1) * 0.5
    env = np.sin(np.pi * np.clip(t / dur, 0, 1)) ** 0.7 * (0.6 + 0.4 * smooth_noise(n, r, 20))
    return fades(c * env, 0.005, 0.03)


def rummage(r, dur, density=6.0, clinks=0.4, thumps=0.4):
    """hands digging through drawers and a backpack: rustles, small clinks, item thumps"""
    n = ns(dur)
    y = np.zeros(n)
    t = r.uniform(0, 0.2)
    while t < dur:
        _add(y, rustle(r, r.uniform(0.12, 0.45), r.uniform(0.7, 1.3)) * r.uniform(0.4, 1.0), t)
        if r.random() < clinks:
            for k in range(r.integers(1, 4)):
                _add(y, G.clink(r, dur=0.12) * r.uniform(0.3, 0.8), t + r.uniform(0, 0.3))
        if r.random() < thumps:
            tc = tt(0.15)
            th = modal(0.15, [(r.uniform(160, 300), 1.0, 0.02), (r.uniform(500, 900), 0.4, 0.01)], r)
            th += lp(r.standard_normal(len(tc)), 900, 2) * np.exp(-tc / 0.01)
            _add(y, th * r.uniform(0.3, 0.7), t + r.uniform(0, 0.3))
        t += r.exponential(1.0 / density) + 0.04
    return fades(y, 0.05, 0.1)


def laptop_slide(r, dur=0.9):
    """a laptop shoved into a padded backpack: nylon slide + a dull bump at the bottom"""
    n = ns(dur)
    s = bp(r.standard_normal(n), 400, 5000, 1) * _env(n, [(0, 0), (0.1, 0.8), (dur * 0.8, 1.0), (dur * 0.85, 0)])
    s *= 0.7 + 0.3 * smooth_noise(n, r, 15)
    bump = modal(0.25, [(120, 1.0, 0.04), (260, 0.5, 0.025)], r)
    _add(s, bump * 1.5, dur * 0.82)
    return fades(s, 0.01, 0.05)


def plastic_crack(r):
    """a bare foot snapping a thin piece of plastic: sharp double crack + bright fragments"""
    d = 0.5
    y = np.zeros(ns(d))
    for at, a in ((0.0, 1.0), (0.018, 0.7), (0.05, 0.35)):
        tc = tt(0.12)
        burst = hp(r.standard_normal(len(tc)), 1500) * np.exp(-tc / 0.0025)
        body = modal(0.12, [(r.uniform(1800, 2400), 0.8, 0.01), (r.uniform(3600, 4400), 0.6, 0.006),
                            (r.uniform(6500, 8000), 0.4, 0.004)], r)
        _add(y, (burst * 1.6 + body) * a, at)
    for _ in range(5):  # tiny bits skittering
        _add(y, G.clink(r, f0=r.uniform(4000, 7000), dur=0.03, bright=0.5) * r.uniform(0.1, 0.25), r.uniform(0.07, 0.3))
    foot = lp(r.standard_normal(ns(0.1)), 400, 2) * np.exp(-tt(0.1) / 0.015) * 0.4
    _add(y, foot, 0.0)
    return fades(y, 0.0005, 0.05)


def barefoot(r, creak=0.0):
    """a soft bare foot on a wooden stair (optional little plank creak)"""
    d = 0.5
    tc = tt(d)
    pad = lp(r.standard_normal(len(tc)), 500, 2) * np.exp(-tc / 0.03) * 0.8
    skin = bp(r.standard_normal(len(tc)), 800, 4000, 1) * np.exp(-tc / 0.02) * 0.15
    y = pad + skin + modal(d, [(r.uniform(170, 230), 0.3, 0.03)], r)
    if creak:
        cr = G.creak(0.35, r, 70, 110, modes=G.WOOD, scale=0.8)
        _add(y, _norm(cr) * 0.4 * creak, 0.05)
    return fades(y, 0.002, 0.05)


def door_creak_soft(r, dur=1.1, rate0=40, rate1=70):
    """a bedroom door opened a crack: slow low hinge creak"""
    y = G.creak(dur, r, rate0=rate0, rate1=rate1, modes=G.WOOD, scale=0.75, rough=0.25, noise=0.02,
                shape_pts=[(0, 0), (0.2, 0.8), (0.6, 1.0), (1, 0)])
    return _norm(y)


def flashlight_click(r):
    """the flashlight's tail switch: two tight plastic clicks"""
    y = np.zeros(ns(0.06))
    for at, a in ((0.0, 1.0), (0.012, 0.5)):
        _add(y, modal(0.04, [(2900, 1.0, 0.003), (5200, 0.6, 0.002)], r) * a, at)
    return y


# ---------------------------------------------------------------- the fight
def swing_whoosh(r, dur=0.45, heavy=1.0, f_lo=180, f_hi=1400, tear=False):
    """a heavy object swung hard past the ear: a fast band-swept roar with a peak late in the swing"""
    n = ns(dur)
    t = np.arange(n) / SR
    u = t / dur
    peak = 0.72 if not tear else 0.88
    env = np.exp(-((u - peak) / (0.22 if not tear else 0.3)) ** 2)
    env = np.where(u > peak, np.exp(-((u - peak) / 0.12) ** 2), env)
    z = colored(n, r, 0.6)
    fc = f_lo + (f_hi - f_lo) * np.exp(-((u - peak) / 0.25) ** 2)
    lo = bp(z, f_lo, f_hi * 0.6, 2)
    hi = bp(z, f_hi * 0.5, f_hi * 2.5, 2)
    w = np.clip((fc - f_lo) / (f_hi - f_lo), 0, 1)
    y = (lo * (1 - 0.5 * w) + hi * w) * env * heavy
    if tear:  # ragged, tearing edge on the final blow
        rough = 1 + 0.8 * (np.abs(smooth_noise(n, r, 90)) > 0.5)
        y = y * rough + 0.5 * hp(r.standard_normal(n), 2500) * env ** 3
    return fades(y, 0.01, 0.03)


def clang_wall(r):
    """an iron crowbar smashing into a wall edge: hard strike, long inharmonic bar ring, plaster crumble"""
    d = 2.6
    tc = tt(d)
    f = 520
    bar = modal(d, [(f, 1.0, 0.7), (f * 2.76, 0.8, 0.45), (f * 5.40, 0.55, 0.25), (f * 8.93, 0.35, 0.12),
                    (f * 1.013, 0.5, 0.6), (f * 2.79, 0.4, 0.4)], r)
    hit = bp(r.standard_normal(len(tc)), 800, 10000, 1) * np.exp(-tc / 0.004) * 3.0
    wall = lp(r.standard_normal(len(tc)), 700, 2) * np.exp(-tc / 0.03) * 1.6
    wall += np.sin(phase(75 * (1 + 0.6 * np.exp(-tc / 0.01)))) * np.exp(-tc / 0.06) * 1.2
    crumble = np.zeros(len(tc))
    for _ in range(40):
        g = bp(r.standard_normal(ns(0.02)), 1500, 7000, 1) * np.exp(-tt(0.02) / 0.004)
        _add(crumble, g * r.uniform(0.05, 0.25), 0.03 + r.exponential(0.18))
    return fades(bar * 0.9 + hit + wall + crumble, 0.0, 0.3)


def sparks(r):
    """a few tiny electric-ish spark crackles (very quiet, sold with the clang)"""
    y = np.zeros(ns(0.4))
    for _ in range(14):
        _add(y, hp(r.standard_normal(ns(0.004)), 4000) * r.uniform(0.3, 1.0), r.uniform(0, 0.3))
    return y


def thwack(r):
    """a metal desk lamp slammed into a forearm: meaty slap-thud + the lamp's hollow metal clank"""
    d = 0.8
    tc = tt(d)
    slap = bp(r.standard_normal(len(tc)), 300, 5000, 1) * np.exp(-tc / 0.007) * 2.0
    meat = np.sin(phase(110 * (1 + 0.8 * np.exp(-tc / 0.008)))) * np.exp(-tc / 0.05) * 1.4
    meat += lp(r.standard_normal(len(tc)), 500, 2) * np.exp(-tc / 0.025) * 1.2
    lamp = modal(d, [(780, 0.5, 0.09), (1460, 0.45, 0.07), (2390, 0.35, 0.05), (3610, 0.2, 0.03)], r)
    cloth = bp(r.standard_normal(len(tc)), 1000, 6000, 1) * np.exp(-tc / 0.03) * 0.3
    return fades(slap + meat + 0.7 * lamp + cloth, 0.0, 0.15)


def bar_hit(r, a=1.0, f=640):
    d = 1.0
    tc = tt(d)
    ring = modal(d, [(f, 1.0, 0.25), (f * 2.76, 0.7, 0.15), (f * 5.4, 0.45, 0.07), (f * 8.9, 0.25, 0.035)], r)
    clk = bp(r.standard_normal(len(tc)), 1500, 10000, 1) * np.exp(-tc / 0.002) * 2.0
    tile = modal(d, [(1900, 0.5, 0.01), (720, 0.5, 0.015)], r)
    return (ring + clk + tile) * a


def crowbar_drop_roll(r, roll=1.8):
    """the crowbar hits the tiles, bounces twice, then rolls: rattling clicks at each tile joint, ringing, a stop"""
    d = 0.45 + roll + 0.6
    y = np.zeros(ns(d))
    _add(y, bar_hit(r, 1.0, 640), 0.0)
    _add(y, bar_hit(r, 0.55, 652), 0.14)
    _add(y, bar_hit(r, 0.3, 635), 0.24)
    # rolling: an uneven bar (hex) rolls ~ 6 faces/s, slowing; tile grout joints every ~0.3 s
    t = 0.38
    rate = 9.0
    while t < 0.38 + roll:
        u = (t - 0.38) / roll
        tc = tt(0.12)
        tick = modal(0.12, [(640 * 2.76, 0.4, 0.04), (640 * 5.4, 0.3, 0.02), (2100, 0.3, 0.006)], r)
        tick += bp(r.standard_normal(len(tc)), 2000, 8000, 1) * np.exp(-tc / 0.0015) * 0.6
        _add(y, tick * (0.35 * (1 - 0.6 * u)) * r.uniform(0.7, 1.0), t)
        t += 1.0 / (rate * (1 - 0.65 * u))
    n_roll = ns(roll)
    rumble = bp(r.standard_normal(n_roll), 300, 2500, 1) * _env(n_roll, [(0, 0.25), (roll, 0.05)])
    _add(y, rumble, 0.38)
    for j in (0.55, 0.95, 1.4):  # grout joints
        if 0.38 + j * roll / 1.8 < 0.38 + roll:
            _add(y, bar_hit(r, 0.22, 645), 0.38 + j * roll / 1.8)
    _add(y, bar_hit(r, 0.18, 640), 0.38 + roll)  # comes to rest against something
    return fades(y, 0.0, 0.25)


def body_fall(r, big=1.0):
    """a body slammed down on a tiled floor: heavy low thud + cloth slap + breath knocked out"""
    d = 0.7
    tc = tt(d)
    th = np.sin(phase(68 * (1 + 0.9 * np.exp(-tc / 0.01)))) * np.exp(-tc / 0.08) * 1.6
    th += lp(r.standard_normal(len(tc)), 400, 2) * np.exp(-tc / 0.03) * 1.6
    slap = bp(r.standard_normal(len(tc)), 600, 6000, 1) * np.exp(-tc / 0.012) * 0.8
    tile = modal(d, [(1150, 0.2, 0.02), (2700, 0.12, 0.01)], r)
    return fades((th + slap + tile) * big, 0.0, 0.1)


def bag_spill(r, dur=1.4):
    """the backpack lands and spills: a padded thump, then phones, keys, coins, a torch skittering on tiles"""
    y = np.zeros(ns(dur))
    tc = tt(0.3)
    _add(y, (lp(r.standard_normal(len(tc)), 600, 2) * np.exp(-tc / 0.04) * 1.4 + rustle(r, 0.3) * 0.6), 0.0)
    for _ in range(9):  # coins / keys
        at = 0.05 + r.exponential(0.25)
        if at < dur - 0.2:
            _add(y, G.clink(r, dur=0.15) * r.uniform(0.3, 0.8), at)
    for k in range(3):  # bigger items: phone, torch, box
        at = 0.06 + 0.12 * k + r.uniform(0, 0.1)
        _add(y, modal(0.2, [(r.uniform(700, 1400), 0.8, 0.02), (r.uniform(2000, 3500), 0.5, 0.01)], r) * 0.8, at)
    # a coin spinning out
    t0 = 0.4
    for i in range(14):
        _add(y, G.clink(r, f0=5200, dur=0.05, bright=0.4) * 0.18 * (1 - i / 14), t0 + 0.5 * (1 - (1 - i / 14) ** 0.5))
    return fades(y, 0.0, 0.1)


def cloth_scrape(r, dur, density=2.5, squeak=0.25):
    """two bodies struggling on tiles: jacket / pyjama fabric scraping, palms slapping, a rubber-sole squeak"""
    n = ns(dur)
    y = np.zeros(n)
    t = r.uniform(0, 0.1)
    while t < dur:
        d = r.uniform(0.15, 0.55)
        m = ns(d)
        z = bp(r.standard_normal(m), 250, 4500, 1) * (0.6 + 0.4 * smooth_noise(m, r, 25))
        e = np.sin(np.pi * np.arange(m) / m) ** r.uniform(0.6, 1.5)
        _add(y, z * e * r.uniform(0.4, 1.0), t)
        if r.random() < 0.3:  # palm or knee slap on tile
            tc = tt(0.12)
            sl = bp(r.standard_normal(len(tc)), 500, 6000, 1) * np.exp(-tc / 0.008) + \
                lp(r.standard_normal(len(tc)), 350, 2) * np.exp(-tc / 0.02)
            _add(y, sl * r.uniform(0.6, 1.2), t + r.uniform(0, d))
        if r.random() < squeak:
            sq = G.creak(r.uniform(0.08, 0.16), r, 600, 900, modes=[(1400, 25, 1.0), (2900, 30, 0.6)], rough=0.05)
            _add(y, _norm(sq) * r.uniform(0.15, 0.35), t + r.uniform(0, d))
        t += r.exponential(1.0 / density) + 0.06
    return fades(y, 0.03, 0.1)


def elbow_hit(r):
    """an elbow driven into ribs: a short dull body punch"""
    d = 0.4
    tc = tt(d)
    th = np.sin(phase(90 * (1 + 0.7 * np.exp(-tc / 0.008)))) * np.exp(-tc / 0.04) * 1.4
    th += lp(r.standard_normal(len(tc)), 600, 2) * np.exp(-tc / 0.015) * 1.2
    cl = bp(r.standard_normal(len(tc)), 900, 5000, 1) * np.exp(-tc / 0.01) * 0.5
    return fades(th + cl, 0.0, 0.08)


def huff(r, base=118):
    """the air punched out of him: a hard voiced 'HUH' exhale"""
    d = 0.32
    n = ns(d)
    t = np.arange(n) / SR
    f0 = base * G._track(n, [(0, 1.4), (0.05, 1.3), (d, 0.9)], t)
    forms = G.vowel_track(n, [(0, "A"), (d, "er")])
    amp = np.clip(t / 0.006, 0, 1) * np.exp(-t / 0.09)
    y = G.vox(f0, forms, amp, r, 1.0, tilt=1.0, breath=1.2, fmax=5000, jitter=0.04)
    air = bp(r.standard_normal(n), 400, 5000, 1) * np.exp(-t / 0.07)
    return fades(y + 0.6 * air / (np.std(air) + 1e-9) * np.std(y), 0.001, 0.04)


def body_slide(r, dur=1.8):
    """a body thrown aside, sliding a long way across tiles: a long friction rush that slows, a bump at the end"""
    n = ns(dur)
    t = np.arange(n) / SR
    u = t / dur
    env = np.clip(t / 0.04, 0, 1) * (1 - u) ** 1.4
    z = colored(n, r, 0.5)
    lo = bp(z, 150, 900, 2) * 1.0
    hi = bp(z, 900, 5000, 2) * (0.7 - 0.5 * u)
    stutter = 1 + 0.5 * smooth_noise(n, r, 18) * u
    y = (lo + hi) * env * stutter
    _add(y, body_fall(r, 0.45), 0.0)
    _add(y, body_fall(r, 0.25), dur - 0.15)
    return fades(y, 0.0, 0.1)


def latch_click(r):
    """the front-door latch: a metal tongue drawn back (click-clack) + a small bolt thunk"""
    y = np.zeros(ns(0.4))
    _add(y, modal(0.15, [(2400, 1.0, 0.012), (4100, 0.7, 0.008), (6300, 0.4, 0.004)], r), 0.0)
    _add(y, modal(0.15, [(1900, 0.8, 0.015), (3300, 0.5, 0.01)], r), 0.065)
    _add(y, modal(0.2, [(330, 0.6, 0.03), (720, 0.4, 0.02)], r), 0.07)
    return fades(y, 0.0, 0.05)


def door_slam(r):
    """a heavy front door slammed: big low boom, wooden panel modes, latch smack, frame rattle"""
    d = 2.0
    tc = tt(d)
    boom = np.sin(phase(55 * (1 + 0.7 * np.exp(-tc / 0.015)))) * np.exp(-tc / 0.18) * 1.8
    panel = modal(d, [(118, 1.0, 0.12), (236, 0.7, 0.08), (391, 0.5, 0.06), (650, 0.3, 0.04), (1020, 0.2, 0.03)], r)
    smack = bp(r.standard_normal(len(tc)), 500, 7000, 1) * np.exp(-tc / 0.008) * 1.6
    latch = np.zeros(len(tc))
    _add(latch, latch_click(r) * 0.7, 0.005)
    rattle = G.rattle(0.35, r, 40, np.exp(-np.linspace(0, 1, ns(0.35)) * 4), heavy=True) * 0.15
    _add(latch, rattle, 0.03)
    return fades(boom + panel + smack + latch, 0.0, 0.4)


def street_spill(r, dur):
    """street through an open door at night: low distant traffic, air hush, one far car passing (stereo)"""
    n = ns(dur)
    t = np.arange(n) / SR
    rum = lp(colored(n, r, 2.0), 220, 2) * 1.2
    hush = bp(colored(n, r, 1.0), 300, 3000, 1) * (0.5 + 0.2 * smooth_noise(n, r, 0.5))
    car = bp(colored(n, r, 1.0), 200, 1800, 1) * np.exp(-((t - dur * 0.45) / (dur * 0.25)) ** 2) * 0.9
    L = rum + hush + car * 0.8
    R = lp(colored(n, r, 2.0), 220, 2) * 1.2 + bp(colored(n, r, 1.0), 300, 3000, 1) * 0.5 + car
    return fades(np.stack([L, R]), 0.3, 0.05)


def shoe_step(r, big=1.0, scuff=0.15):
    """a big man's hard leather sole on tiles: heel CLICK + sole CLOMP ~45 ms later, a short tile ring"""
    d = 0.7
    y = np.zeros(ns(d))
    tc = tt(d)
    heel = bp(r.standard_normal(len(tc)), 1500, 9000, 1) * np.exp(-tc / 0.0025) * 1.6
    heel += modal(d, [(r.uniform(1700, 1900), 0.5, 0.015), (r.uniform(3300, 3600), 0.3, 0.008)], r)
    clomp = np.sin(phase(r.uniform(95, 110) * (1 + 0.6 * np.exp(-tc / 0.01)))) * np.exp(-tc / 0.05) * 1.5 * big
    clomp += lp(r.standard_normal(len(tc)), 700, 2) * np.exp(-tc / 0.02) * 1.0 * big
    clomp += bp(r.standard_normal(len(tc)), 800, 5000, 1) * np.exp(-tc / 0.006) * 0.6
    _add(y, heel, 0.0)
    _add(y, clomp, 0.045)
    if scuff:
        m = ns(0.12)
        sc = bp(r.standard_normal(m), 600, 4000, 1) * np.sin(np.pi * np.arange(m) / m) * scuff
        _add(y, sc, 0.07)
    return fades(y, 0.0, 0.1)


def dry_impact(r):
    """the last blow in the black: a hard, dry, short hit (no ring, no tail)"""
    d = 0.35
    tc = tt(d)
    th = np.sin(phase(80 * (1 + 1.4 * np.exp(-tc / 0.006)))) * np.exp(-tc / 0.045) * 1.6
    crack = bp(r.standard_normal(len(tc)), 700, 9000, 1) * np.exp(-tc / 0.004) * 2.2
    body = lp(r.standard_normal(len(tc)), 500, 2) * np.exp(-tc / 0.02) * 1.3
    return fades(th + crack + body, 0.0, 0.08)


def running_away(r, dur=3.2, rate=3.6):
    """hurried shoe steps running away across tiles and out: each step quieter, duller and further"""
    y = np.zeros(ns(dur + 0.6))
    t = 0.0
    k = 0
    while t < dur:
        u = t / dur
        s = shoe_step(r, big=0.7, scuff=0.35)
        s = lp(s, 9000 * (1 - u) + 900 * u, 2)
        _add(y, s * (1 - u) ** 1.6 * (1.0 if k % 2 == 0 else 0.8), t)
        t += 1.0 / rate * r.uniform(0.92, 1.08)
        k += 1
    return y


def drone(r, dur, f=41.2):
    """a very low dark drone: two detuned low sines + a slow-breathing dark noise band (stereo)"""
    n = ns(dur)
    t = np.arange(n) / SR
    s = np.sin(phase(np.full(n, f) * (1 + 0.003 * smooth_noise(n, r, 0.2))))
    s2 = np.sin(phase(np.full(n, f * 1.498) * (1 + 0.004 * smooth_noise(n, r, 0.15))))
    s3 = np.sin(phase(np.full(n, f * 2.01)))
    nz = bp(colored(n, r, 1.5), 60, 300, 2) * (0.6 + 0.4 * smooth_noise(n, r, 0.12))
    L = s + 0.5 * s2 + 0.3 * s3 + 0.8 * nz
    R = s + 0.5 * s2 + 0.3 * np.sin(phase(np.full(n, f * 2.013))) + 0.8 * bp(colored(n, r, 1.5), 60, 300, 2)
    return np.stack([L, R]) * (0.85 + 0.15 * np.sin(TAU * 0.07 * t))


def room_tone(r, dur):
    """a quiet house at night: very low air + fridge-ish hum far away (stereo)"""
    n = ns(dur)
    a = lp(colored(n, r, 1.8), 900, 1) * 0.6
    b = lp(colored(n, r, 1.8), 900, 1) * 0.6
    hum = 0.08 * np.sin(TAU * 100 * np.arange(n) / SR)
    return np.stack([a + hum, b + hum])


def lamp_lift(r):
    """the hand finds the metal lamp: a soft hollow knock and a little base scrape on the nightstand"""
    y = np.zeros(ns(0.5))
    _add(y, modal(0.3, [(780, 0.6, 0.05), (1460, 0.45, 0.04), (2390, 0.3, 0.03)], r) * 0.8, 0.0)
    m = ns(0.25)
    _add(y, bp(r.standard_normal(m), 600, 4000, 1) * np.sin(np.pi * np.arange(m) / m) * 0.25, 0.05)
    return fades(y, 0.0, 0.05)


def plug_yank(r):
    """a plug yanked out of the wall socket: plastic scrape, a sharp snap and the cable whipping"""
    y = np.zeros(ns(0.6))
    m = ns(0.08)
    _add(y, bp(r.standard_normal(m), 1500, 7000, 1) * np.linspace(0.2, 1, m) * 0.4, 0.0)
    _add(y, modal(0.08, [(2100, 1.0, 0.006), (3900, 0.7, 0.004), (950, 0.5, 0.01)], r) * 1.2, 0.08)
    _add(y, hp(r.standard_normal(ns(0.004)), 2000) * 0.8, 0.08)
    _add(y, swing_whoosh(r, 0.22, 0.25, 600, 3000), 0.1)
    _add(y, modal(0.1, [(1200, 0.4, 0.01), (2600, 0.3, 0.006)], r), 0.32)
    return fades(y, 0.0, 0.05)
