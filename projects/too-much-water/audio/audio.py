# Soundtrack for "What if you drank too much water?": original quirky pizzicato score + synthesized SFX, mixed under
# the ElevenLabs voice (gain only). Reuses the bridge short's own DSP kit and instruments (templates/audio).
# Standard mix: music +3 dB, SFX -6 dB relative to the bridge reference levels; master -14 LUFS, true peak <= -1 dBTP.
# usage: python audio.py   (writes mix.wav + stems next to this file)
import os
import sys
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "..", "templates", "audio"))
from dsp import SR, ns, tt, rng, dbg, lp, hp, bp, place, pan, fades, colored, read_wav, write_wav, integrated, true_peak, make_ir, convolve_st  # noqa: E402
import instruments as I  # noqa: E402
import sfx_gen as G  # noqa: E402

FPS, TOTAL = 30, 1660
DUR = TOTAL / FPS
N = ns(DUR)
BPM = 112
B = 60 / BPM  # one beat
m2f = I.m2f

# ---------------- music ----------------
mus = np.zeros((2, N))
r = rng(11)

def note(fn, t, *a, p=0.0, g=1.0, **k):
    x = fn(*a, r=r, **k)
    place(mus, pan(fades(x), p) if x.ndim == 1 else x, t, g)

F_MAJ = [53, 57, 60]; BB = [58, 62, 65]; C7 = [48, 52, 55, 58]; DM = [50, 53, 57]
CHORDS = [F_MAJ, BB, C7, F_MAJ, DM, BB, C7, C7]

def oompah(t0, t1, vel=0.5, horn=True):
    k = 0
    t = t0
    while t < t1 - 0.05:
        ch = CHORDS[(k // 4) % 8]
        if k % 2 == 0:
            note(I.brass, t, m2f(ch[0] - 12), B * 0.8, vel=vel, kind="tuba", p=-0.1)
        elif horn:
            note(I.pluck, t, m2f(ch[1]), vel=vel * 0.6, dur=0.4, p=0.3)
            note(I.pluck, t, m2f(ch[2]), vel=vel * 0.5, dur=0.4, p=0.35)
        t += B; k += 1

MEL = [72, 74, 76, 72, 77, None, 76, 74, 72, 70, 69, 72, 74, None, 67, None]
def melody(t0, t1, fn=I.pluck, vel=0.55, tr=0, step=0.5, p=-0.25, **kw):
    t, i = t0, 0
    while t < t1 - 0.05:
        n = MEL[i % len(MEL)]
        if n is not None:
            note(fn, t, m2f(n + tr), vel=vel, p=p, **kw)
        t += B * step * 2
        i += 1

# hook (0 - 3.1): two pizz stabs on "dangerous" and "whiskey", glock sting on "water"
for t, n in [(0.7, 60), (1.72, 65)]:
    note(I.pluck, t, m2f(n), vel=0.8, dur=0.5); note(I.pluck, t, m2f(n - 12), vel=0.7, dur=0.6)
note(I.glock, 2.54, m2f(84), vel=0.7); note(I.glock, 2.54, m2f(79), vel=0.5)
note(I.cymbal, 3.07, vel=0.35, dur=1.6, p=0.2)
# story march (3.2 - 19.2): oompah + melody, denser as the queue grows
oompah(3.2, 19.2, vel=0.45)
melody(3.2, 10.8, I.pluck, vel=0.5, dur=0.7)
melody(10.8, 19.2, I.glock, vel=0.35, dur=1.0)
for k in range(int((19.2 - 14.2) / (B / 2))):  # snare from "Two liters"
    t = 14.2 + k * B / 2
    note(I.snare, t, vel=0.25 + 0.04 * (k % 4 == 0), dur=0.2, p=0.15)
# tension (19.3 - 24.75): pad + rising timpani roll, hit on "drink."
note(I.pad, 19.3, [m2f(53), m2f(56), m2f(60)], 5.45, vel=0.35, att=1.2, rel=0.3)
for k in range(int(5.4 / 0.09)):
    t = 19.35 + k * 0.09
    note(I.timpani, t, m2f(41), vel=0.12 + 0.5 * (t - 19.3) / 5.4, dur=0.4)
note(I.timpani, 24.73, m2f(41), vel=1.0, dur=2.0); note(I.cymbal, 24.73, vel=0.6, dur=2.4)
# light again (25.7 - 38.6): vibes + pizz, "bone" hit, sponge creeps
oompah(25.7, 38.6, vel=0.35, horn=False)
melody(25.7, 38.6, I.vibes, vel=0.4, tr=-12, dur=1.4)
note(I.timpani, 30.05, m2f(38), vel=0.8, dur=1.6)
# silence for the real case (38.7 - 45.2)
# soldiers (45.3 - 51.0): snare cadence + horn stabs, halt on 48.8
for k in range(int((48.8 - 45.3) / (B / 2))):
    note(I.snare, 45.3 + k * B / 2, vel=0.3 if k % 2 else 0.45, dur=0.2, p=0.1)
for t in [45.3, 46.4, 47.5]:
    note(I.brass, t, m2f(65), B * 0.6, vel=0.4, kind="stab"); note(I.brass, t, m2f(60), B * 0.6, vel=0.35, kind="stab")
note(I.snare, 48.8, vel=0.8, dur=0.4); note(I.brass, 48.8, m2f(53), 0.6, vel=0.6, kind="stab")
# warm resolve + loop pickup (51.0 - end)
note(I.pad, 51.0, [m2f(53), m2f(57), m2f(60), m2f(65)], 3.6, vel=0.35, att=0.5, rel=0.6)
melody(51.0, 54.0, I.pluck, vel=0.45, dur=0.7)
note(I.glock, 53.75, m2f(77), vel=0.6); note(I.glock, 53.75, m2f(84), vel=0.4)
note(I.pluck, DUR - 0.62, m2f(60), vel=0.6, dur=0.5)  # pickup into the hook on loop

ir = make_ir(0.9, 3)
mus = 0.8 * mus + 0.2 * convolve_st(mus, ir)[:, :N]

# ---------------- sfx ----------------
fx = np.zeros((2, N))
rs = rng(5)
def sx(x, t, g=1.0, p=0.0):
    x = np.asarray(x, float)
    place(fx, pan(fades(x), p) if x.ndim == 1 else fades(x), t, g)

def slide(t0, dur):  # glass sliding on wood: band-passed noise with a rough grain, ending in a soft knock
    n = ns(dur); e = np.sin(np.linspace(0, np.pi, n)) ** 0.6
    x = bp(colored(n, rs, -1.0), 400, 2600) * e * (1 + 0.5 * rs.standard_normal(n).clip(-1, 1) * 0.3)
    sx(x * 0.5, t0, 0.8, 0.2)
    sx(G.clink(rs, f0=2400, dur=0.15, bright=0.5) * 0.6, t0 + dur, 0.7)

def stamp(t):
    tt_ = tt(0.18)
    x = np.sin(2 * np.pi * 95 * tt_) * np.exp(-tt_ / 0.03) + bp(rs.standard_normal(len(tt_)), 300, 2500) * np.exp(-tt_ / 0.01) * 0.5
    sx(x, t, 0.55, rs.uniform(-0.2, 0.2))

def pitter(t0, t1, rate=6, g=0.15):
    t = t0
    while t < t1:
        tt_ = tt(0.06); x = bp(rs.standard_normal(len(tt_)), 1500, 6000) * np.exp(-tt_ / 0.008)
        sx(x, t, g, rs.uniform(-0.6, 0.6)); t += rs.uniform(0.5, 1.5) / rate

def room(t0, t1, g=0.03, lo=80, hi=600):
    n = ns(t1 - t0); x = bp(colored(n, rs, -1.0), lo, hi)
    sx(x * np.minimum(1, np.minimum(np.arange(n), n - np.arange(n)) / ns(0.2)), t0, g)

# bar
room(0, 3.2, 0.04); room(DUR - 2.4, DUR, 0.04)
slide(0.0, 0.85); slide(DUR - 0.25, 0.7)  # the loop slide continues into frame 0
# office: vault clank, salute clink, stamps on every strike, little feet
sx(G.clink(rs, f0=420, dur=0.6, bright=0.3), 3.25, 0.6)
sx(G.clink(rs, f0=3200, dur=0.15), 5.85, 0.5)
stamp(9.38)
for t0, t1, rate in [(10.8, 14.2, 3.2), (14.2, 16.5, 4.2)]:
    k = int(np.ceil(t0 * rate - 0.25));
    while (k + 0.25) / rate < t1:
        stamp((k + 0.25) / rate); stamp((k + 0.25) / rate + 0.13); k += 1
pitter(10.8, 16.5, 5); pitter(14.2, 16.5, 9)
# street: breeze, birds, a crowd of little feet
sx(G.breeze(2.8, rs, level=0.8), 16.5, 0.5); pitter(16.5, 19.2, 18, 0.12)
# cells: water rush, stretching membranes, the gulp + pop on "drink."
wb = G.water_bed(5.2, rs, close=0.8)
sx(wb if wb.ndim == 1 else wb.mean(axis=0), 19.5, 0.5)
sx(G.whoosh(1.2, rs, peak=0.4), 21.0, 0.6, -0.4)
sx(G.creak(2.6, rs, rate0=60, rate1=160, rough=0.2), 22.1, 0.35, 0.3)
tt_ = tt(0.35); gulp = np.sin(2 * np.pi * (220 * tt_ + 300 * tt_ ** 2)) * np.exp(-tt_ / 0.08)
sx(gulp, 24.7, 0.6)
# skull: bone creaks + hit on "bone."
sx(G.creak(1.6, rs, rate0=40, rate1=90, rough=0.25), 28.6, 0.45, -0.2)
sx(G.wood_crack(rs), 30.05, 0.35)
# kitchen: pour, sponge squelch, glass strain
sx(G.bubbles(2.2, rs, 30), 31.2, 0.35)
sx(lp(colored(ns(1.5), rs, -0.5), 900) * np.sin(np.linspace(0, np.pi, ns(1.5))), 32.7, 0.25)
sx(G.creak(3.5, rs, rate0=90, rate1=200, rough=0.08), 34.4, 0.25, 0.2)
# radio: room tone and the hum of the ON AIR lamp only
room(38.7, 45.2, 0.02, 60, 300)
hum = np.sin(2 * np.pi * 60 * tt(6.5)) * 0.004 + np.sin(2 * np.pi * 120 * tt(6.5)) * 0.002
sx(hum, 38.7, 1.0)
# soldiers: boots on cobbles, halt, canteen taps
k = 0
while 45.3 + k * 0.5 < 48.8:
    for j in range(4): sx(G.boot(rs, 0.6), 45.3 + k * 0.5 + rs.uniform(0, 0.02), 0.18, rs.uniform(-0.5, 0.5))
    k += 1
for j in range(6): sx(G.boot(rs, 1.0), 48.8 + rs.uniform(0, 0.015), 0.25, rs.uniform(-0.5, 0.5))
for t in [49.35, 49.75, 50.15]: sx(G.clink(rs, f0=1700, dur=0.12, bright=0.4), t, 0.5, 0.3)
sx(G.breeze(5.7, rs, level=0.6), 45.3, 0.35)
# thumbs up: two stamps of approval
stamp(51.25); stamp(51.6)

# ---------------- mix ----------------
voice = read_wav(os.path.join(HERE, "..", "voice", "voice.wav"))[0]
voice = np.vstack([voice[0], voice[0]]) if voice.shape[0] == 1 else voice
vo = np.zeros((2, N)); place(vo, voice[:, : N], 0.0)
# music ducks under speech (envelope of the voice, 60 ms attack / 300 ms release)
env = np.abs(vo[0]); win = ns(0.06)
env = np.convolve(env, np.ones(win) / win, mode="same")
duck = 1 - 0.45 * np.clip(env / (env.max() * 0.25), 0, 1)
duck = np.convolve(duck, np.ones(ns(0.3)) / ns(0.3), mode="same")
v_l = integrated(vo)
mus *= dbg((v_l - 20.0) - integrated(mus) + 3.0)  # music ~17 dB under the voice (+3 dB house rule)
fx *= dbg((v_l - 18.0) - integrated(fx) - 6.0)    # sfx under the voice (-6 dB house rule)
mus *= duck
mix = vo + mus + fx
mix *= dbg(-14.0 - integrated(mix))
peak = true_peak(mix)
if peak > -1.0:  # simple soft clip for the rare peaks above the ceiling
    c = dbg(-1.0); mix = np.where(np.abs(mix) > c * 0.8, np.sign(mix) * (c * 0.8 + (np.abs(mix) - c * 0.8) * 0.3), mix)
    mix = np.clip(mix, -c, c)
write_wav(os.path.join(HERE, "mix.wav"), mix)
write_wav(os.path.join(HERE, "stem_music.wav"), mus)
write_wav(os.path.join(HERE, "stem_sfx.wav"), fx)
print(f"voice {v_l:.1f} LUFS | mix {integrated(mix):.1f} LUFS, true peak {true_peak(mix):.1f} dBTP | {mix.shape[1] / SR:.3f} s")
