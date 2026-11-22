# Explainer-short SFX library (own numpy synthesis, built on the template's dsp.py / sfx_gen.py / instruments.py).
# Every generator takes an rng and returns mono (n,) or stereo (2, n) float audio at 48 kHz; levels are set by the mixer.
# GEN maps cue names (used by shots.json fx names and audio/<slug>/sfx.json) to generators.
import numpy as np
from dsp import SR, TAU, ns, tt, rng, lp, hp, bp, colored, smooth_noise, fades, phase, modal, pan, st, place
import sfx_gen as G
import instruments as I


def _chirp(f0, f1, dur, tau_f=None):
    t = tt(dur)
    f = f1 + (f0 - f1) * np.exp(-t / tau_f) if tau_f else np.linspace(f0, f1, len(t))
    return np.sin(phase(f))


# ---------------------------------------------------------------- generic cartoon / editorial
def whoosh(r, dur=0.55, peak=0.2, bright=1.0):
    return G.whoosh(dur, r, peak=peak, f_lo=300 * bright, f_hi=2400 * bright, width=0.8, tail=0.16, air=0.12)


def whoosh_fast(r):
    return G.whoosh(0.32, r, peak=0.07, f_lo=600, f_hi=4200, width=0.7, tail=0.08, air=0.25)


def impact(r, size=1.0):
    t = tt(0.6)
    thump = np.sin(phase(70 * size ** -0.3 * (1 + 1.2 * np.exp(-t / 0.012)))) * np.exp(-t / (0.09 * size))
    crack = bp(r.standard_normal(len(t)), 900, 7000, 1) * np.exp(-t / 0.012)
    return fades(1.4 * thump + 0.6 * crack, 0.0, 0.05)


def boom(r):
    t = tt(2.2)
    n = len(t)
    low = np.sin(phase(48 * (1 + 0.8 * np.exp(-t / 0.05)))) * np.exp(-t / 0.45)
    burst = lp(r.standard_normal(n), 2500, 2) * np.exp(-t / 0.08)
    rumble = lp(colored(n, r, 1.5), 180, 2) * (1 - np.exp(-t / 0.02)) * np.exp(-t / 0.7)
    return fades(1.5 * low + 0.8 * burst + 1.2 * rumble, 0.0, 0.3)


def puff(r):
    t = tt(0.35)
    return fades(bp(r.standard_normal(len(t)), 150, 1800, 1) * (1 - np.exp(-t / 0.01)) * np.exp(-t / 0.07), 0, 0.05)


def pop(r):
    t = tt(0.1)
    return fades(_chirp(900, 300, 0.1, 0.015) * np.exp(-t / 0.025), 0.0005, 0.02)


def ding(r, f=1760.0):
    return I.glock(f, 0.7, r, 1.2)


def sparkle(r):
    y = np.zeros(ns(1.4))
    for k, m in enumerate([88, 91, 95, 100]):
        G._place_mono(y, I.glock(I.m2f(m), 0.5 - 0.06 * k, r, 1.0), 0.055 * k)
    return y


def boing(r):
    t = tt(0.7)
    f = 180 * (1 + 0.9 * (1 - np.exp(-t / 0.18))) * (1 + 0.06 * np.sin(TAU * 13 * t) * np.exp(-t / 0.25))
    y = (np.sin(phase(f)) + 0.3 * np.sin(2 * phase(f))) * np.exp(-t / 0.22) * (1 - np.exp(-t / 0.003))
    return fades(y, 0.0, 0.05)


def question(r):
    """two-note rising 'hmm?' (pizzicato), the mystery beat"""
    y = np.zeros(ns(1.0))
    G._place_mono(y, I.pluck(I.m2f(64), 0.7, r, 0.6, 0.6), 0.0)
    G._place_mono(y, I.pluck(I.m2f(71), 0.75, r, 0.8, 0.6), 0.16)
    return y


def drip(r):
    t = tt(0.12)
    return fades(_chirp(700, 2200, 0.12) * np.exp(-t / 0.03), 0.0005, 0.02)


def riser(r, dur=1.2):
    """filtered-noise swell that ends exactly at dur (place with offset -dur)"""
    n = ns(dur)
    t = np.arange(n) / SR
    u = t / dur
    y = G.shape(colored(n, r, 0.5), lambda T, F: np.exp(-0.5 * (np.log2(np.maximum(F[:, None], 20) / (300 + 3500 * (T[None, :] / dur) ** 2)) / 0.7) ** 2), 1024, 256)
    return fades(y * u ** 2.5, 0.02, 0.01)


def splash(r):
    return G.splash_big(r)[: ns(1.6)] * np.linspace(1, 0, ns(1.6)) ** 0.5


# ---------------------------------------------------------------- bicycle / road
def bike_bell(r, rings=2):
    """thumb-lever bell: each ring = a few fast striker hits on a small brass dome (modal), rings ~0.18 s apart"""
    y = np.zeros(ns(1.6))
    f0 = r.uniform(1950, 2100)
    modes = [(f0, 1.0, 0.55), (f0 * 1.51, 0.35, 0.3), (f0 * 2.37, 0.5, 0.25), (f0 * 3.92, 0.2, 0.12), (f0 * 5.1, 0.1, 0.06)]
    for k in range(rings):
        for j in range(3):
            hit = modal(1.0, modes, r) * (0.9 if j == 0 else 0.45)
            hit += hp(r.standard_normal(len(hit)), 4000) * np.exp(-tt(1.0) / 0.0015) * 0.3
            G._place_mono(y, hit, 0.19 * k + 0.028 * j + r.uniform(0, 0.004))
    return fades(y, 0.0, 0.2)


def freewheel(r, dur=1.4, rate=18.0):
    """coasting freewheel ratchet: pawl clicks slowing down"""
    y = np.zeros(ns(dur))
    t = 0.0
    while t < dur - 0.05:
        c = modal(0.04, [(r.uniform(3800, 4300), 1.0, 0.004), (r.uniform(6500, 7200), 0.5, 0.002)], r)
        G._place_mono(y, c * r.uniform(0.7, 1.0) * (1 - 0.5 * t / dur), t)
        t += 1.0 / (rate * (1 - 0.45 * t / dur)) * r.uniform(0.92, 1.08)
    return y


def tyre_skid(r, dur=0.7):
    t = tt(dur)
    n = len(t)
    f = 1150 * (1 + 0.05 * smooth_noise(n, r, 9)) * (1 - 0.15 * t / dur)
    sq = sum(a * np.sin(k * phase(f)) for k, a in [(1, 1.0), (2, 0.5), (3, 0.25)])
    sq *= 0.5 + 0.5 * smooth_noise(n, r, 14) ** 2
    grit = bp(r.standard_normal(n), 800, 6000, 1) * 0.5
    env = (1 - np.exp(-t / 0.02)) * np.clip((dur - t) / 0.15, 0, 1)
    return (0.5 * sq + grit) * env


def crash(r):
    """bike going down: body thump + frame clatter + bell knock + spinning wheel ticks"""
    y = np.zeros(ns(1.8))
    G._place_mono(y, impact(r, 1.3), 0.0)
    G._place_mono(y, G.rattle(0.6, r, 45, np.exp(-np.linspace(0, 4, ns(0.6))), heavy=True) * 0.8, 0.03)
    for k in range(3):
        G._place_mono(y, G.clink(r, r.uniform(1800, 3200)) * 0.5, 0.05 + 0.09 * k)
    G._place_mono(y, freewheel(r, 1.2, 10) * 0.5, 0.5)
    return fades(y, 0.0, 0.2)


def lean(r):
    """the swoop of a bike tipping into a corner"""
    return G.whoosh(0.7, r, peak=0.32, f_lo=200, f_hi=1300, width=0.9, tail=0.2, air=0.08)


def pedal(r, strokes=4, cadence=1.4):
    """chain + crank: soft rhythmic chain rattle per pedal stroke"""
    y = np.zeros(ns(strokes / cadence + 0.4))
    for k in range(strokes):
        G._place_mono(y, G.rattle(0.25, r, 22, np.exp(-np.linspace(0, 3, ns(0.25))), heavy=False) * 0.6, k / cadence)
    return y


# ---------------------------------------------------------------- ambience beds (stereo)
def amb_road(dur, r):
    """quiet street: tyre-on-asphalt hush + light air, rare distant car passes"""
    n = ns(dur)
    out = G.breeze(dur, r, 0.5, gust=0.12, bright=700)
    hush = lp(colored(n, r, 1.2), 900, 2) * (0.75 + 0.25 * smooth_noise(n, r, 0.3))
    out += st(hush * 0.8)
    t = r.uniform(1.5, 4.0)
    while t < dur - 2:
        L = r.uniform(2.5, 4.0)
        tl = tt(L)
        e = np.exp(-((tl - L / 2) / (L / 5)) ** 2)
        cn = colored(len(tl), r, 1.0)
        car = (lp(cn, 600, 1) * (1 - e) + lp(cn, 1500, 1) * e) * e
        p = np.clip((tl - L / 2) / (L / 2), -1, 1) * r.choice([-1, 1]) * 0.7
        car_st = np.stack([car * np.sqrt((1 - p) / 2), car * np.sqrt((1 + p) / 2)]) * np.sqrt(2)
        a = ns(t)
        b = min(n, a + len(tl))
        out[:, a:b] += 0.9 * car_st[:, : b - a]
        t += L + r.uniform(4, 9)
    return out


def amb_outdoor(dur, r):
    out = G.breeze(dur, r, 0.7)
    out += pan(G.bird_chirps(dur, r, 0.4) * 0.08, -0.4)
    return out


def amb_room(dur, r):
    n = ns(dur)
    return st(lp(colored(n, r, 1.0), 400, 2) * 0.5 + hp(colored(n, r, 0.0), 6000) * 0.02)


# ---------------------------------------------------------------- desert / ice / money / livestream (sailing-stones)
def gps_ping(r):
    """tracker ping: soft sonar blip + a quieter echo"""
    y = np.zeros(ns(0.8))
    for k, (d, a) in enumerate([(0.0, 1.0), (0.22, 0.35)]):
        t = tt(0.35)
        b = np.sin(TAU * 1760 * t) * np.exp(-t / 0.09) * (1 - np.exp(-t / 0.003))
        b += 0.3 * np.sin(TAU * 3520 * t) * np.exp(-t / 0.04)
        G._place_mono(y, b * a, d)
    return y


def card_pop(r):
    """a title/year card slapping onto the screen: paper flick + small thump"""
    y = np.zeros(ns(0.4))
    G._place_mono(y, G.whoosh(0.18, r, peak=0.1, f_lo=900, f_hi=5000, width=0.6, tail=0.04, air=0.3) * 0.7, 0.0)
    t = tt(0.25)
    G._place_mono(y, np.sin(phase(160 * (1 + 0.6 * np.exp(-t / 0.01)))) * np.exp(-t / 0.04) * 0.9, 0.1)
    G._place_mono(y, bp(r.standard_normal(len(t)), 1500, 6000, 1) * np.exp(-t / 0.006) * 0.5, 0.1)
    return y


def dust_storm(r, dur=3.2):
    """a wall of dust rolling over: wind roar swelling in, sand hiss and grit, a few gust whooshes (stereo)"""
    n = ns(dur)
    t = np.arange(n) / SR
    env = np.clip(t / 0.8, 0, 1) ** 1.5 * np.clip((dur - t) / 1.2, 0, 1)
    out = G.breeze(dur, r, 1.6, gust=0.6, bright=1400) * env[None, :]
    hiss = hp(colored(n, r, 0.3), 2500) * (0.5 + 0.5 * smooth_noise(n, r, 3.0) ** 2)
    grit = np.zeros(n)
    k = 0
    while k < 260:
        G._place_mono(grit, hp(r.standard_normal(ns(0.004)), 3000) * r.uniform(0.2, 1.0), r.uniform(0, dur - 0.01))
        k += 1
    out += st((0.35 * hiss + 0.5 * grit) * env)
    for g in (0.3, 1.2, 2.0):
        w = G.whoosh(0.9, r, peak=0.35, f_lo=200, f_hi=1200, width=1.0, tail=0.3, air=0.1) * 0.8
        place(out, pan(w, r.uniform(-0.6, 0.6)), g)
    return out


def flash_flood(r, dur=3.0):
    """brown wall of water: low roar + churning rush + debris knocks + a splash on arrival (stereo)"""
    n = ns(dur)
    t = np.arange(n) / SR
    env = np.clip(t / 0.35, 0, 1) * np.clip((dur - t) / 1.0, 0, 1)
    roar = lp(colored(n, r, 1.4), 500, 2) * (0.8 + 0.2 * smooth_noise(n, r, 2.0))
    rush = G.shape(colored(n, r, 0.6), lambda T, F: np.exp(-0.5 * (np.log2(np.maximum(F[:, None], 20) / 1100) / 1.1) ** 2), 1024, 256)
    rush *= 0.6 + 0.4 * smooth_noise(n, r, 6.0) ** 2
    bub = G.bubbles(dur, r, 140.0, 250, 1800, (0.005, 0.02), np.ones(n))
    y = (1.3 * roar + 0.8 * rush + 0.35 * bub) * env
    out = np.stack([y, np.roll(y, ns(0.011))])
    for k in range(4):
        place(out, pan(impact(r, 0.6) * 0.25, r.uniform(-0.7, 0.7)), r.uniform(0.4, dur - 0.6))
    place(out, st(splash(r)[: ns(1.2)] * 0.7), 0.05)
    return out


def rain(r, dur=2.8):
    """rain on a shallow pond: dense drop plinks + hiss"""
    n = ns(dur)
    t = np.arange(n) / SR
    env = np.clip(t / 0.4, 0, 1) * np.clip((dur - t) / 0.8, 0, 1)
    drops = G.bubbles(dur, r, 260.0 * np.ones(n), 1500, 5500, (0.002, 0.008), env, rise=(8, 25))
    hiss = hp(colored(n, r, 0.2), 3000) * env
    return np.stack([drops * 0.8 + 0.25 * hiss, np.roll(drops, ns(0.007)) * 0.8 + 0.25 * np.roll(hiss, 97)])


def _ice_tick(r, f0=None):
    """one crack in thin ice: a sharp click + the dispersive 'pew' (high to low chirp) that ice sheets sing"""
    d = r.uniform(0.05, 0.12)
    t = tt(d)
    f0 = f0 or r.uniform(4500, 8000)
    f = 600 + (f0 - 600) * np.exp(-t / (d / 3))
    y = np.sin(phase(f)) * np.exp(-t / (d / 2.5))
    y += hp(r.standard_normal(len(t)), 2500) * np.exp(-t / 0.0015) * 0.8
    return y


def ice_crack(r, dur=1.3):
    """thin ice crackling: a burst of cracks thinning out, two bigger ones with a low knock"""
    y = np.zeros(ns(dur + 0.2))
    tm = 0.0
    while tm < dur:
        G._place_mono(y, _ice_tick(r) * r.uniform(0.3, 0.9), tm)
        tm += r.exponential(0.035 + 0.12 * tm / dur)
    for tb in (0.0, 0.45):
        G._place_mono(y, _ice_tick(r, 9000) * 1.2, tb)
        t = tt(0.2)
        G._place_mono(y, np.sin(phase(180 * (1 + 0.4 * np.exp(-t / 0.01)))) * np.exp(-t / 0.05) * 0.6, tb)
    return fades(y, 0.0, 0.1)


def ice_pane(r, dur=1.6):
    """a pane of ice grinding and shoving: high stick-slip scrape + crunch ticks"""
    c = G.creak(dur, r, 60, 140, [(1300, 10, 1.0), (2300, 12, 0.7), (3900, 14, 0.45), (6100, 16, 0.25)],
                [(0, 0), (0.2, 1), (0.8, 0.9), (1, 0)], rough=0.3, noise=0.2)
    t = tt(dur)
    scrape = bp(r.standard_normal(len(t)), 1200, 7000, 1) * np.sin(np.pi * np.clip(t / dur, 0, 1)) ** 1.5
    scrape *= 0.5 + 0.5 * smooth_noise(len(t), r, 12) ** 2
    y = c / (np.abs(c).max() + 1e-9) + 0.25 * scrape
    for k in range(5):
        G._place_mono(y, _ice_tick(r) * 0.4, r.uniform(0.05, dur - 0.15))
    return fades(y, 0.02, 0.15)


def sliding_rock(r, dur=1.4):
    """a heavy rock dragging over wet mud/ice: low gritty scrape + rumble, no squeal"""
    n = ns(dur)
    t = np.arange(n) / SR
    env = np.sin(np.pi * np.clip(t / dur, 0, 1)) ** 1.2
    grind = bp(colored(n, r, 0.8), 120, 1600, 2) * (0.6 + 0.4 * smooth_noise(n, r, 15) ** 2)
    rumble = lp(colored(n, r, 1.6), 140, 2)
    grit = np.zeros(n)
    for k in range(60):
        G._place_mono(grit, bp(r.standard_normal(ns(0.006)), 1500, 5000, 1) * r.uniform(0.1, 0.6), r.uniform(0, dur - 0.01))
    return fades((grind + 0.9 * rumble + 0.6 * grit) * env, 0.02, 0.1)


def ka_ching(r):
    """cash register: drawer slide-clunk, the bell 'ka-CHING', a few coins"""
    y = np.zeros(ns(1.6))
    t = tt(0.12)
    G._place_mono(y, (np.sin(phase(140 * (1 + 0.5 * np.exp(-t / 0.01)))) * np.exp(-t / 0.03)
                      + bp(r.standard_normal(len(t)), 800, 5000, 1) * np.exp(-t / 0.008) * 0.8) * 0.8, 0.0)   # 'ka'
    bell = modal(1.4, [(2637, 1.0, 0.45), (3951, 0.6, 0.35), (5274, 0.35, 0.22), (7040, 0.2, 0.12)], r)
    bell += modal(1.4, [(2650, 0.5, 0.4), (3968, 0.3, 0.3)], r)                       # a slightly detuned 2nd bell
    G._place_mono(y, bell * 1.1, 0.07)                                                  # 'CHING'
    G._place_mono(y, G.whoosh(0.25, r, peak=0.05, f_lo=1200, f_hi=4000, width=0.6, tail=0.08, air=0.2) * 0.4, 0.05)
    for k in range(4):
        G._place_mono(y, G.clink(r, r.uniform(3500, 6000)) * 0.35, 0.18 + 0.05 * k + r.uniform(0, 0.02))
    return fades(y, 0.0, 0.2)


def sign_crash(r):
    """a wooden sign splitting and slapping flat: crack, splinters, a flat wood slap, rattling bits"""
    y = np.zeros(ns(1.8))
    G._place_mono(y, G.wood_crack(r) * 0.9, 0.0)
    G._place_mono(y, impact(r, 0.8) * 0.6, 0.0)
    t = tt(0.4)
    slap = bp(r.standard_normal(len(t)), 300, 4000, 1) * np.exp(-t / 0.02) + np.sin(phase(110 + 0 * t)) * np.exp(-t / 0.06)
    G._place_mono(y, slap * 0.9, 0.42)
    for k in range(5):
        G._place_mono(y, modal(0.15, [(r.uniform(400, 900), 0.8, 0.02), (r.uniform(1200, 2400), 0.5, 0.012)], r) * 0.35,
                      0.5 + 0.07 * k + r.uniform(0, 0.03))
    return fades(y, 0.0, 0.2)


def live_ping(r, n_pings=1):
    """livestream notification: soft two-note chime (E6 -> B6), optionally a flurry of them"""
    y = np.zeros(ns(0.5 + 0.11 * n_pings))
    for k in range(n_pings):
        a = 1.0 if k == 0 else r.uniform(0.35, 0.7)
        m0 = 88 + int(r.integers(-2, 3)) * (k > 0)
        for j, m in enumerate((m0, m0 + 7)):
            t = tt(0.3)
            G._place_mono(y, np.sin(TAU * I.m2f(m) * t) * np.exp(-t / 0.08) * (1 - np.exp(-t / 0.002)) * a, 0.11 * k + 0.07 * j)
    return y


def live_flurry(r):
    return live_ping(r, 7)


def amb_desert(dur, r):
    """open playa: low wide wind, very sparse, almost silent (stereo)"""
    out = G.breeze(dur, r, 0.6, gust=0.08, bright=600)
    return out


def amb_alien(dur, r):
    """fantasy cutaway room tone: a soft detuned sci-fi hum with a slow warble (stereo)"""
    n = ns(dur)
    t = np.arange(n) / SR
    w = 1 + 0.004 * np.sin(TAU * 0.7 * t)
    y = sum(a * np.sin(TAU * f * w * t + k) for k, (f, a) in enumerate([(110, 1.0), (110.7, 0.8), (220.4, 0.35), (330, 0.15)]))
    y *= 0.8 + 0.2 * np.sin(TAU * 0.23 * t)
    return np.stack([y, np.roll(y, ns(0.013))]) * 0.5 + 0.05 * st(hp(colored(n, r, 0.5), 5000))



# cue name -> (generator, default level LU vs the voice, short description)
GEN = {
    "whoosh": (whoosh, -17, "transition whoosh"),
    "whoosh_fast": (whoosh_fast, -16, "fast swish / speed lines"),
    "speed_lines": (whoosh_fast, -16, "fast swish / speed lines"),
    "impact": (impact, -10, "cartoon impact thump + crack"),
    "impact_star": (impact, -10, "cartoon impact thump + crack"),
    "explosion": (boom, -8, "boom + rumble"),
    "boom": (boom, -8, "boom + rumble"),
    "dust_puff": (puff, -15, "dust puff"),
    "puff": (puff, -15, "dust puff"),
    "pop": (pop, -15, "pop"),
    "exclaim": (ding, -14, "ding"),
    "ding": (ding, -14, "ding"),
    "sparkle": (sparkle, -15, "glock sparkle run"),
    "glow_eyes": (sparkle, -16, "glock sparkle run"),
    "question_mark": (question, -16, "rising two-note pizzicato 'hmm?'"),
    "question": (question, -16, "rising two-note pizzicato 'hmm?'"),
    "boing": (boing, -13, "spring boing"),
    "sweat_drop": (drip, -16, "drip blip"),
    "splash": (splash, -14, "splash"),
    "riser": (riser, -16, "noise riser ending on the cue time"),
    "bike_bell": (bike_bell, -11, "bicycle thumb bell, ring-ring"),
    "freewheel": (freewheel, -16, "coasting freewheel ratchet"),
    "tyre_skid": (tyre_skid, -13, "tyre skid squeal"),
    "crash": (crash, -9, "bike crash: thump, frame clatter, spinning wheel"),
    "lean": (lean, -15, "swoop of the bike leaning into a turn"),
    "pedal": (pedal, -18, "chain rattle on pedal strokes"),
    "gps_ping": (gps_ping, -16, "tracker ping: sonar blip + echo"),
    "year_badge": (card_pop, -16, "title card pop: paper flick + thump"),
    "card_pop": (card_pop, -16, "title card pop: paper flick + thump"),
    "dust_storm": (dust_storm, -15, "dust storm rolling in: wind roar, sand hiss, gusts"),
    "flash_flood": (flash_flood, -15, "flash flood: water roar, rush, debris, splash"),
    "rain": (rain, -16, "rain on a shallow pond"),
    "ice_crack": (ice_crack, -14, "thin ice crackling, dispersive 'pew' cracks"),
    "ice_pane": (ice_pane, -15, "ice pane grinding / shoving"),
    "pane_push_top": (ice_pane, -15, "engine s17 mechanism: the wind shoves a pane into a rock (same grind as ice_pane)"),
    "sliding_rock": (sliding_rock, -15, "rock scraping over wet mud and ice"),
    "ka_ching": (ka_ching, -10, "cash register ka-ching"),
    "sign_crash": (sign_crash, -9, "wooden sign splitting and slapping flat"),
    "live_ping": (live_ping, -15, "livestream notification chime"),
    "live_flurry": (live_flurry, -14, "a flurry of livestream notification chimes"),
}
# fx names with no sound of their own (the music or the picture carries them)
SILENT = {"zzz", "music_note", "anger_vein", "light_shaft", "lens_flash", "steer_arrow", "path_line", "air_hockey_overlay"}
BEDS = {"road": amb_road, "track": amb_road, "playa": amb_desert, "inserts": amb_alien, "village": amb_outdoor, "park": amb_outdoor, "harbour": amb_outdoor, "interior": amb_room,
        "room": amb_room}
