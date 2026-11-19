# Synthesized sound effects for "What If Your Plane's Windscreen Blew Out?", event table locked to the picture
# (project/src/videos/plane/story.ts times). Own numpy synthesis from sfx_gen.py / dsp.py. Writes sfx.wav (stereo, 48 kHz).
import numpy as np
from dsp import SR, ns, tt, rng, lp, hp, bp, colored, smooth_noise, fades, modal, pan, place, write_wav, phase
import sfx_gen as G
import instruments as I

DUR = 1990 / 30
N = ns(DUR)
out = np.zeros((2, N))
R = rng(1990)
r = lambda: rng(int(R.integers(1 << 30)))

T_HOOK, T_BLOW, T_SUCK, T_ROOF, T_STEW, T_GRAB, T_TAKE = 2.33, 11.66, 14.2, 15.5, 19.0, 20.25, 24.15
T_TD, T_ALIVE, T_THUMB, T_RED, T_SHORT, T_MATCH, T_WRONG = 30.6, 34.55, 37.6, 43.15, 46.1, 48.75, 50.45
T_PUSH, T_HARD, T_FAIL, T_OFF = 55.65, 61.6, 62.55, 64.2
SHOT_T = [0, 3.2, 4.667, 7.6, 9.733, 12.6, 16.933, 18.933, 22.533, 25.0, 29.133, 30.4, 33.267, 37.6, 39.0, 42.4, 44.6, 47.5, 51.8, 57.833, 63.0, DUR]


def add(x, t, g=1.0, p=0.0):
    x = np.asarray(x, float)
    place(out, pan(x, p) if x.ndim == 1 else x, t, g)


def env_seg(n, pts):
    t = np.arange(n) / SR
    return np.interp(t, [a for a, _ in pts], [b for _, b in pts])


def wind(dur, rr, pts, bright=1800, howl=0.0):
    """rushing air: low roar + mid rush + a whistling howl, level follows pts [(t, gain)]"""
    n = ns(dur)
    e = env_seg(n, pts)
    lo = lp(colored(n, rr, 1.4), 220, 2) * 1.3
    mid = bp(colored(n, rr, 0.5), 300, bright, 1) * (0.7 + 0.3 * smooth_noise(n, rr, 1.5))
    y = lo + mid
    if howl:
        f = 620 + 180 * smooth_noise(n, rr, 0.6)
        y = y + howl * 0.05 * np.sin(phase(f)) * (0.6 + 0.4 * smooth_noise(n, rr, 2.0))
    y = y * e
    return np.stack([y, np.roll(y, 293) * 0.9 + 0.1 * y])


def jet(dur, rr, pts, whine=1.0):
    """jet engines: broadband roar + a turbine whine"""
    n = ns(dur)
    e = env_seg(n, pts)
    roar = lp(colored(n, rr, 1.0), 1400, 2) + 0.4 * bp(colored(n, rr, 0.3), 800, 3500, 1)
    t = np.arange(n) / SR
    wh = whine * 0.03 * (np.sin(phase(3150 + 60 * smooth_noise(n, rr, 0.5))) + 0.5 * np.sin(phase(4720 + 40 * smooth_noise(n, rr, 0.5))))
    y = (roar + wh) * e
    return np.stack([y, np.roll(y, 211)])


def hum(dur, rr, level=1.0):
    """cabin hum: low steady drone"""
    n = ns(dur)
    y = lp(colored(n, rr, 1.2), 400, 2) * 0.6 + 0.02 * np.sin(phase(np.full(n, 116.0))) + 0.01 * np.sin(phase(np.full(n, 232.0)))
    return np.stack([y, np.roll(y, 160)]) * level


def bang(rr):
    """explosive decompression: a deep thump, a glass crack, the air going"""
    n = ns(1.8)
    t = np.arange(n) / SR
    thump = np.exp(-t / 0.18) * np.sin(phase(52 * (1 + 0.6 * np.exp(-t / 0.03)))) * 2.4
    crack = bp(rr.standard_normal(n), 1200, 12000, 2) * np.exp(-t / 0.012) * 1.8
    rush = bp(colored(n, rr, 0.4), 200, 4000, 1) * np.exp(-t / 0.6) * 0.9
    return thump + crack + rush


def glass_pop(rr):
    t = tt(0.6)
    crack = bp(rr.standard_normal(len(t)), 2000, 14000, 2) * np.exp(-t / 0.01) * 1.4
    ring = modal(0.6, [(2900, 1, 0.12), (4300, 0.6, 0.08), (6100, 0.4, 0.05)], rr) * 0.4
    return crack + ring


def beep(f, dur, vel=0.4):
    t = tt(dur)
    return vel * np.sin(TAU_ * f * t) * np.minimum(1, t / 0.005) * np.minimum(1, (dur - t) / 0.01)


def flutter(dur, rr, rate=24):
    """papers flapping"""
    n = ns(dur)
    y = bp(rr.standard_normal(n), 1500, 6000, 1) * (0.5 + 0.5 * np.sign(np.sin(phase(rate + 6 * smooth_noise(n, rr, 3.0)))))
    return fades(y * 0.15, 0.05, 0.1)


TAU_ = 2 * np.pi

# ================================================================ events
# 1 hook: wind over the nose, the pane pops and whips away
add(wind(3.3, r(), [(0, 0.35), (2.2, 0.5), (2.4, 1.0), (3.3, 0.8)], howl=0.5), 0.0, 0.5)
add(glass_pop(r()), T_HOOK, 0.8)
add(G.whoosh(0.9, r(), peak=0.12, f_lo=400, f_hi=3000, tail=0.3), T_HOOK + 0.02, 0.6)
add(G.whoosh(0.7, r(), peak=0.12, f_lo=600, f_hi=3000, tail=0.15), 3.2 - 0.08, 0.35)  # into the white flash
# 2 Birmingham: engines spooling, wheels rumbling on the runway
add(jet(1.6, r(), [(0, 0.5), (1.6, 0.8)]), 3.2, 0.45)
add(lp(colored(ns(1.6), r(), 1.5), 120) * 0.6, 3.2, 0.5)
# 3 take-off roar past the lens
add(jet(3.1, r(), [(0, 0.9), (1.2, 1.0), (2.6, 0.7), (3.1, 0.3)], whine=1.4), 4.6, 0.55)
add(G.whoosh(2.6, r(), peak=1.0, f_lo=200, f_hi=1600, tail=0.8), 4.8, 0.4)
# 4 cabin: hum, soft chatter, a chime
add(hum(2.2, r()), 7.55, 0.5)
add(G.babble(2.0, r(), 160, 1.0) * 0.25, 7.6, 0.3, -0.2)
add(I.glock(I.m2f(84), 0.4, r()) + 0, 7.75, 0.25)
add(I.glock(I.m2f(79), 0.4, r()), 8.05, 0.25)
# 5 cockpit hum, then the windscreen goes
add(hum(2.0, r(), 0.8), 9.7, 0.5)
add(bang(r()), T_BLOW, 1.0)
add(glass_pop(r()), T_BLOW, 0.7)
# the gale: in the cockpit loud, outside howling, over everything until the landing
add(wind(18.9, r(), [(0, 0), (0.15, 1.0), (1.5, 0.85), (5.2, 0.85), (5.3, 1.0), (7.2, 1.0), (7.3, 0.8), (13.3, 0.8), (13.4, 1.0), (17.4, 0.85), (18.9, 0.0)], howl=1.0), T_BLOW + 0.02, 0.75)
for t0, d in [(T_BLOW + 0.2, 0.9), (SHOT_T[6], 2.0), (SHOT_T[7], 3.5), (SHOT_T[8], 2.4), (SHOT_T[10], 1.2)]:
    add(flutter(d, r()), t0, 0.5, -0.3)
# a cockpit warning: a steady repeating two-tone alert from the blow-out to the landing (quieter outside)
for k, tb in enumerate(np.arange(T_BLOW + 0.5, T_TD - 0.2, 0.6)):
    outside = SHOT_T[5] <= tb < SHOT_T[6] or SHOT_T[9] <= tb < SHOT_T[10]
    add(beep(1180 if k % 2 == 0 else 880, 0.22, 0.12), tb, 0.12 if outside else 0.35, 0.2)
# 6 the captain sucked out: a whoosh, a thud on the roof
add(G.whoosh(1.2, r(), peak=0.5, f_lo=200, f_hi=2600, tail=0.4), T_SUCK - 0.1, 0.8)
add(lp(r().standard_normal(ns(0.3)), 250) * np.exp(-tt(0.3) / 0.05) * 1.5, T_ROOF - 0.15, 0.6)
# 8 the steward: running steps, the grab
for tm in np.arange(T_STEW + 0.1, T_GRAB - 0.4, 0.22):
    add(G.stroll_step(r(), 0.7), tm, 0.25)
add(G.oof(r(), "oof"), T_GRAB + 0.05, 0.25)
add(lp(r().standard_normal(ns(0.2)), 400) * np.exp(-tt(0.2) / 0.03), T_GRAB, 0.5)
add(G.oof(r(), "oof"), 22.95, 0.2)  # arms give out
for tm in [T_TAKE - 0.6, T_TAKE - 0.35, T_TAKE - 0.1]:
    add(G.stroll_step(r(), 0.8), tm, 0.25)
# 10 the danger path: soft pops for the dots, a sting at the engine
for k in range(22):
    add(beep(900 + 25 * k, 0.05, 0.3), 25.95 + 1.2 + (28.45 - 27.15) * k / 22, 0.3)
# 12 the landing: tyres chirp, a thud, reverse thrust roar
add(jet(2.8, r(), [(0, 0.6), (0.5, 0.7), (1.0, 1.0), (2.8, 0.2)]), 30.4, 0.5)
for k, d in enumerate([0.0, 0.07]):
    t = tt(0.35)
    chirp = bp(r().standard_normal(len(t)), 900, 3000, 2) * np.exp(-t / 0.08) * (0.6 + 0.4 * np.sin(phase(np.full(len(t), 1400.0)))) * 1.2
    add(chirp, T_TD + d, 0.6, -0.3 + 0.6 * k)
add(lp(r().standard_normal(ns(0.4)), 160) * np.exp(-tt(0.4) / 0.1) * 2.0, T_TD, 0.7)
# 13 the ward: room tone, a heart monitor beeping (it quickens on "Alive.")
add(hum(5.8, r(), 0.12), 33.2, 0.5)
tb = 33.4
while tb < 39.0:
    add(beep(1046, 0.09, 0.25), tb, 0.35)
    tb += 1.0 if tb < T_ALIVE - 0.2 else 0.62
for k in range(3):
    add(G.clink(r(), 5200 + 600 * k, 0.4, 1.4), 36.75 + 0.1 * k, 0.12)  # frost sparkle
# 14 back to flying: a cockpit chime, engines
add(hum(1.4, r(), 0.7), 37.6, 0.5)
add(I.glock(I.m2f(88), 0.5, r()), T_THUMB + 0.25, 0.3)
# 15 the hangar at night: a big room, the work lamps buzzing, a ratchet screwdriver
add(lp(colored(ns(DUR - 39.0), r(), 1.0), 300) * 0.25 + 0.006 * np.sin(phase(np.full(ns(DUR - 39.0), 100.0))), 39.0, 0.5)
for tm in np.arange(39.4, 42.2, 0.13):
    add(G.clink(r(), 2600, 0.04, 1.0), tm, 0.12, -0.2)
# 16 ninety bolts: a ripple of ticks as 84 turn red, then six
for k in range(84):
    add(G.clink(r(), 3200 + 8 * k, 0.05, 0.8), T_RED + 0.012 * k * (90 / 84), 0.12)
for k in range(6):
    add(G.clink(r(), 1800, 0.08, 0.8), T_SHORT + 0.04 * k, 0.2)
# 17 the macro: a soft metallic ring as each bolt is shown
add(modal(1.2, [(1900, 1, 0.5), (3100, 0.5, 0.3)], r()) * 0.2, 44.6, 0.35)
add(lp(r().standard_normal(ns(0.3)), 300) * np.exp(-tt(0.3) / 0.05), T_SHORT, 0.3)
# 18 matching the bolts: clink-clink, a happy ding... a wrong buzzer
add(G.clink(r(), 2400, 0.15), T_MATCH, 0.4, -0.2)
add(G.clink(r(), 2500, 0.15), T_MATCH + 0.12, 0.4, 0.2)
t = tt(0.7)
add(np.sign(np.sin(TAU_ * 110 * t)) * 0.15 * np.exp(-t / 0.4) + np.sign(np.sin(TAU_ * 116 * t)) * 0.12 * np.exp(-t / 0.4), T_WRONG, 0.5)
# 19-20 the cutaway: the cabin air hissing up, the bolts straining, then they go
n = ns(T_FAIL - T_PUSH + 0.1)
hiss = bp(colored(n, r(), 0.0), 2000, 8000, 1) * np.linspace(0, 1, n) ** 1.5 * 0.35
add(hiss, T_PUSH - 0.1, 0.5)
for k, tm in enumerate(np.arange(57.9, T_FAIL - 0.1, 0.45)):
    add(G.bolt_strain(r(), 0.5 + 0.1 * k), tm, 0.35 + 0.04 * k, 0.3)
add(G.bolt_snap(r()), T_FAIL, 0.6, 0.3)
add(G.bolt_snap(r()), T_FAIL + 0.06, 0.5, 0.1)
add(bang(r()), T_FAIL + 0.02, 0.8)
add(G.whoosh(1.4, r(), peak=0.15, f_lo=300, f_hi=3200, tail=0.5), T_FAIL, 0.6)
# 21 nobody checked: footsteps on concrete, the light switch, silence
for tm in np.arange(63.25, 64.2, 0.42):
    add(G.stroll_step(r(), 0.4), tm, 0.3, -0.2)
t = tt(0.12)
add(bp(r().standard_normal(len(t)), 1500, 6000, 2) * np.exp(-t / 0.006) + np.exp(-t / 0.02) * np.sin(TAU_ * 180 * t) * 0.5, T_OFF, 0.6)

out = hp(out, 30, 2)
write_wav("sfx.wav", out, 24)
print("sfx.wav", out.shape[1] / SR, "s, peak", np.abs(out).max())
