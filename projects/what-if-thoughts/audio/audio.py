# Soundtrack for "What If You Could Hear Everyone's Thoughts?": original bouncy pluck groove in C major that gets
# crowded and tense through day 2 and 3, drops to birds in the woods, then a squeaky squirrel chorus; synthesized SFX
# (thought-bubble pops, dings, bus, city murmur, running steps, crickets). Mixed under the ElevenLabs voice (gain only).
# Mix rules as the other shorts: music ~17 dB under the voice (+3 dB), SFX -6 dB; master -14 LUFS, true peak <= -1 dBTP.
# usage: python audio.py   (writes mix.wav + stems next to this file)
import os
import sys
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "..", "templates", "audio"))
from dsp import SR, ns, tt, rng, dbg, lp, hp, bp, place, pan, fades, colored, read_wav, write_wav, integrated, true_peak, make_ir, convolve_st  # noqa: E402
import instruments as I  # noqa: E402
import sfx_gen as G  # noqa: E402

FPS, TOTAL = 30, 1935
DUR = TOTAL / FPS
N = ns(DUR)
BPM = 116
B = 60 / BPM
m2f = I.m2f

# ---------------- music ----------------
mus = np.zeros((2, N))
r = rng(31)

def note(fn, t, *a, p=0.0, g=1.0, **k):
    if t >= DUR - 0.02:
        return
    x = fn(*a, r=r, **k)
    place(mus, pan(fades(x), p) if x.ndim == 1 else x, t, g)

C = [48, 52, 55]; Am = [45, 48, 52]; F = [41, 45, 48]; G7 = [43, 47, 50, 53]; Dm = [50, 53, 57]; E7 = [40, 44, 47, 50]
PROG = [C, Am, F, G7]
MEL = [72, 76, 79, 76, 77, 74, 71, 74, 72, 76, 81, 79, 77, 76, 74, None]

def groove(t0, t1, vel=0.42, prog=PROG, sour=0.0):
    """bass on the beat, offbeat chord stabs"""
    t, k = t0, 0
    while t < t1 - 0.05:
        ch = prog[(k // 4) % len(prog)]
        note(I.pluck, t, m2f(ch[0] - 12), vel=vel, dur=0.5, p=-0.1)
        for j, n in enumerate(ch[1:3]):
            note(I.pluck, t + B / 2, m2f(n + 12) * (1 + sour * 0.012 * (j * 2 - 1)), vel=vel * 0.4, dur=0.22, p=0.3)
        t += B; k += 1

def tune(t0, t1, fn=I.glock, vel=0.32, tr=0, p=-0.2, step=0.5, **kw):
    t, i = t0, 0
    while t < t1 - 0.05:
        n = MEL[i % len(MEL)]
        if n is not None:
            note(fn, t, m2f(n + tr), vel=vel, p=p, **kw)
        t += B * step
        i += 1

# hook (0 - 3): music box arpeggio, curious
for k, n in enumerate([72, 76, 79, 84, 79, 76, 72, 76, 79, 83, 79, 74]):
    note(I.musicbox, 0.05 + k * 0.24, m2f(n), vel=0.45)
note(I.pad, 1.6, [m2f(60), m2f(64), m2f(67), m2f(71)], 1.6, vel=0.25, att=0.4, rel=0.4)
# day 1 (3.1 - 20): the groove + glock tune
note(I.glock, 3.1, m2f(84), vel=0.6); note(I.glock, 3.1, m2f(79), vel=0.4)
groove(3.3, 19.9)
tune(3.3, 10.0, I.glock, vel=0.28)
tune(10.0, 14.2, I.musicbox, vel=0.32, tr=-12)
tune(14.2, 18.9, I.glock, vel=0.26)
note(I.brass, 8.0, m2f(43), 0.5, vel=0.45, kind="tuba"); note(I.brass, 8.5, m2f(48), 0.5, vel=0.45, kind="tuba")
for k, n in enumerate([79, 79, 79]): note(I.vibes, [12.21, 12.77, 13.36][k], m2f(n + 2 * k), vel=0.45, dur=0.8)
note(I.timpani, 18.96, m2f(36), vel=0.9, dur=1.6); note(I.cymbal, 18.96, vel=0.5, dur=1.8)
# day 2 (20.15 - 31.6): same groove, a little sour; the annoying song on the bus
note(I.glock, 20.15, m2f(84), vel=0.6); note(I.glock, 20.15, m2f(79), vel=0.4)
groove(20.4, 27.3, vel=0.38, prog=[C, Am, Dm, G7], sour=0.6)
note(I.pluck, 23.3, m2f(55), vel=0.5, dur=0.5); note(I.pluck, 23.55, m2f(54), vel=0.5, dur=0.8)
note(I.vibes, 26.56, m2f(70), vel=0.4, dur=1.2)
# day 3 (31.7 - 43.2): tense pulse, rising pad, crowded
note(I.glock, 31.7, m2f(84), vel=0.6); note(I.glock, 31.7, m2f(78), vel=0.4)
note(I.timpani, 33.0, m2f(36), vel=0.7, dur=2.0)
for k in range(int((43.2 - 33.0) / (B / 2))):
    t = 33.0 + k * B / 2
    note(I.pluck, t, m2f([36, 36, 43, 36][k % 4] + (1 if t > 38 else 0)), vel=0.32 + 0.15 * min(1, (t - 33) / 3), dur=0.25)
note(I.pad, 33.4, [m2f(48), m2f(51), m2f(55)], 6.0, vel=0.28, att=1.5, rel=0.8)
note(I.pad, 39.3, [m2f(49), m2f(52), m2f(56)], 4.0, vel=0.3, att=0.3, rel=0.6)
note(I.timpani, 35.4, m2f(31), vel=0.8, dur=2.0); note(I.cymbal, 35.4, vel=0.35, dur=2.2, bright=0.6)
note(I.brass, 39.3, m2f(46), 0.4, vel=0.5, kind="tuba", fall=-4)
# run (43.3 - 47.6): fast pulse, fading out to nothing on "quiet"
for k in range(int((47.6 - 43.3) / (B / 3))):
    t = 43.3 + k * B / 3
    note(I.pluck, t, m2f([60, 63, 67, 63][k % 4]), vel=0.35 * (1 - (t - 43.3) / 4.6), dur=0.18, p=0.2)
# woods (48.3 - 53.7): soft pad, a tiny pluck on "tiny voice", sting on "us?"
note(I.pad, 48.3, [m2f(60), m2f(64), m2f(67), m2f(72)], 5.0, vel=0.2, att=1.2, rel=1.2)
note(I.musicbox, 51.3, m2f(96), vel=0.4); note(I.musicbox, 51.55, m2f(91), vel=0.35)
note(I.vibes, 53.2, m2f(66), vel=0.5, dur=1.0); note(I.vibes, 53.2, m2f(72), vel=0.4, dur=1.0)
note(I.pluck, 54.0, m2f(43), vel=0.6, dur=0.4); note(I.pluck, 54.25, m2f(48), vel=0.6, dur=0.6)
# squirrels (54.7 - 61.9): frantic groove, high and fast
groove(54.7, 61.8, vel=0.4, prog=[C, F, G7, C])
tune(56.6, 61.8, I.glock, vel=0.3, tr=12, step=0.25)
note(I.cymbal, 58.35, vel=0.4, dur=1.6); note(I.timpani, 58.35, m2f(36), vel=0.7, dur=1.4)
note(I.cymbal, 60.05, vel=0.4, dur=1.6)
# end (61.9 - 64.5): the hook arpeggio, calm, final ding
for k, n in enumerate([72, 76, 79, 84, 79, 76, 72, 76, 79]):
    note(I.musicbox, 61.95 + k * 0.26, m2f(n), vel=0.42)
note(I.pad, 62.0, [m2f(48), m2f(55), m2f(64)], 2.4, vel=0.22, att=0.5, rel=0.5)
note(I.glock, 63.3, m2f(84), vel=0.55); note(I.glock, 63.3, m2f(76), vel=0.4)

ir = make_ir(1.2, 3)
mus = 0.8 * mus + 0.2 * convolve_st(mus, ir)[:, :N]

# ---------------- sfx ----------------
fx = np.zeros((2, N))
rs = rng(9)
def sx(x, t, g=1.0, p=0.0):
    x = np.asarray(x, float)
    if t >= DUR:
        return
    place(fx, pan(fades(x), p) if x.ndim == 1 else fades(x), t, g)

def bloop(t, g=0.35, p=0.0, f0=420.0, f1=980.0):  # a thought bubble popping in
    k = tt(0.11); f = f0 + (f1 - f0) * (1 - np.exp(-k / 0.025))
    x = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-k / 0.04) * np.minimum(1, k / 0.004)
    sx(x, t, g, p)

def steps(t0, t1, rate, g=0.2, p=0.0):
    t = t0
    while t < t1: sx(G.stroll_step(rs, 0.3), t + rs.uniform(0, 0.015), g, p); t += 1 / rate

def murmur(t0, dur, voices, g, hi=False, lpf=3400):
    out = np.zeros((2, ns(dur)))
    for v in range(voices):
        if hi: base, scale = rs.uniform(420, 620), rs.uniform(1.5, 1.8)
        else:
            kind = rs.uniform()
            base, scale = ((rs.uniform(95, 140), rs.uniform(0.95, 1.05)) if kind < 0.45 else (rs.uniform(175, 235), rs.uniform(1.12, 1.2)))
        y = G.babble(dur, rs, base, scale, rs.uniform(3.8, 5.2), rs.uniform(0.6, 0.85), fmax=5000 if hi else 3400)
        out += pan(lp(y, rs.uniform(lpf * 0.7, lpf), 1) * rs.uniform(0.4, 1.0), rs.uniform(-0.85, 0.85))
    n = out.shape[1]; e = np.minimum(1, np.arange(n) / ns(0.4)) * np.minimum(1, (n - np.arange(n)) / ns(0.3))
    place(fx, out * e, t0, g)

# hook: three thought pops, room tone
for t, p in [(1.75, -0.3), (2.05, 0.3), (2.3, 0.0)]: bloop(t, 0.3, p)
# day 1: dings, pops, cafe cups, park birds, pencils
sx(G.whoosh(0.5, rs, peak=0.2), 2.95, 0.3)
for t in [3.6, 4.4]: sx(G.clink(rs, f0=2400, dur=0.1, bright=0.4), t, 0.2, 0.3)
murmur(3.2, 3.6, 3, 0.05)
for t in [4.95, 7.9, 9.05, 12.2, 12.75, 13.35, 16.85]: bloop(t, 0.32)
sx(G.bird_chirps(4.2, rs, density=0.8), 10.0, 0.25, 0.2)
sx(G.breeze(4.2, rs, level=0.5), 10.0, 0.25)
bloop(19.0, 0.4, 0, 300, 1400)
# day 2: pops, bus engine and the hummed tune from many heads
sx(G.whoosh(0.5, rs, peak=0.2), 20.0, 0.3)
for t in [23.25, 25.45]: bloop(t, 0.32)
n = ns(4.4); kk = np.arange(n) / SR
eng = lp(np.sign(np.sin(2 * np.pi * np.cumsum(32 + 3 * np.sin(kk * 1.3)) / SR)) * 0.3 + colored(n, rs, -1.0) * 0.4, 400)
sx(eng, 27.3, 0.35)
for k in range(10): bloop(28.15 + 0.1 * k, 0.16, rs.uniform(-0.7, 0.7), 500, 1100)
SONG = [(0.0, 0.3, 72, 0.7), (0.3, 0.3, 74, 0.7), (0.6, 0.3, 76, 0.7), (0.9, 0.6, 72, 0.7), (1.5, 0.3, 79, 0.7), (1.8, 0.3, 77, 0.7), (2.1, 0.6, 76, 0.7)]
for v in range(6):
    rv = rng(100 + v)
    st, y = I.whistle([(28.3 + a, d, m - 12 + (0 if v % 2 else 12), vel) for a, d, m, vel in SONG] + [(30.9, 0.6, 60 + (0 if v % 2 else 12), 0.6)], rv, detune=rv.uniform(-25, 25), lag=rv.uniform(0, 0.05))
    sx(lp(y, 2500) * 0.6, st, 0.25, rv.uniform(-0.8, 0.8))
# day 3: city air, the murmur of a whole city, a storm of pops
sx(G.whoosh(0.5, rs, peak=0.2), 31.55, 0.3)
sx(G.breeze(11.5, rs, level=0.6, bright=600), 31.7, 0.35)
murmur(32.6, 8.0, 14, 0.35)
for k in range(44): bloop(33.4 + 2.6 * k / 44, 0.12 + 0.1 * rs.random(), rs.uniform(-0.8, 0.8), rs.uniform(350, 600), rs.uniform(800, 1500))
bloop(39.2, 0.35, 0.2)
# night: muffled city through the window, crickets, a clock
murmur(40.2, 3.1, 8, 0.25, lpf=1200)
sx(G.crickets(3.1, rs), 40.2, 0.15)
for k in range(6): sx(G.clink(rs, f0=3000, dur=0.03, bright=0.2), 40.3 + k * 0.5, 0.12, -0.4)
for k in range(9): bloop(40.25 + 0.22 * k, 0.14, rs.uniform(-0.6, 0.6))
bloop(42.2, 0.2, 0, 900, 1300)
# run into the woods: fast steps, city fades behind
murmur(43.2, 2.0, 8, 0.2, lpf=1500)
steps(43.3, 46.8, 4.2, 0.3, 0.2)
sx(G.whoosh(1.2, rs, peak=0.4, f_lo=300, f_hi=1800), 46.6, 0.3, -0.3)
# woods: birds and a breeze; the tiny voice and the squirrel
sx(G.bird_chirps(17.0, rs, density=0.6), 47.4, 0.3, -0.2)
sx(G.breeze(17.0, rs, level=0.4, bright=800), 47.4, 0.3)
bloop(51.0, 0.2, 0.3, 700, 1400)
bloop(52.4, 0.22, 0.3, 900, 1500)
for k in range(27): bloop(54.7 + 0.09 * k, 0.12, rs.uniform(-0.8, 0.8), 800, 1600)
for k in range(27): bloop(56.6 + 0.04 * k, 0.1, rs.uniform(-0.8, 0.8), 900, 1500)
murmur(58.2, 3.6, 14, 0.4, hi=True, lpf=5000)
for k in range(27): bloop(58.3 + 0.03 * k, 0.1, rs.uniform(-0.8, 0.8), 600, 1200)
# end: back in the city, the murmur feels calm now
murmur(61.9, DUR - 61.9, 8, 0.15, lpf=2400)
sx(G.breeze(DUR - 61.9, rs, level=0.4), 61.9, 0.25)

# ---------------- mix ----------------
voice = read_wav(os.path.join(HERE, "..", "voice", "voice.wav"))[0]
voice = np.vstack([voice[0], voice[0]]) if voice.shape[0] == 1 else voice
vo = np.zeros((2, N)); place(vo, voice[:, : N], 0.0)
env = np.abs(vo[0]); win = ns(0.06)
env = np.convolve(env, np.ones(win) / win, mode="same")
duck = 1 - 0.45 * np.clip(env / (env.max() * 0.25), 0, 1)
duck = np.convolve(duck, np.ones(ns(0.3)) / ns(0.3), mode="same")
v_l = integrated(vo)
mus *= dbg((v_l - 20.0) - integrated(mus) + 3.0)
fx *= dbg((v_l - 18.0) - integrated(fx) - 6.0)
mus *= duck
mix = vo + mus + fx
mix *= dbg(-14.0 - integrated(mix))
if true_peak(mix) > -1.2:
    c = dbg(-1.2); mix = np.where(np.abs(mix) > c * 0.8, np.sign(mix) * (c * 0.8 + (np.abs(mix) - c * 0.8) * 0.3), mix)
    mix = np.clip(mix, -c, c)
write_wav(os.path.join(HERE, "mix.wav"), mix)
write_wav(os.path.join(HERE, "stem_music.wav"), mus)
write_wav(os.path.join(HERE, "stem_sfx.wav"), fx)
print(f"voice {v_l:.1f} LUFS | mix {integrated(mix):.1f} LUFS, true peak {true_peak(mix):.1f} dBTP | {mix.shape[1] / SR:.3f} s")
