# Original explainer music bed (own synthesis with the template instruments), arranged to the script's structure.
# Sections come from words.json (see build_mix.sections): hook, body, mystery, explain ("You see," on), payoff, sting.
# Each section restarts the bar grid on its own first word, so every section change lands on a downbeat with the voice.
# Key G major, 112 bpm. Progressions: drive I-V-vi-IV, mystery vi-IV-ii-V(sus), explanation IV-I/3-ii-V.
import numpy as np
from dsp import SR, ns, rng, lp, hp, bp, fades, phase, pan, st, place, integrated, dbg, make_ir, convolve_st
import instruments as I

BPM = 112
Q = 60.0 / BPM
F = I.m2f

CH = {  # name: (bass midi, chord voicing midi)
    "G": (43, [55, 59, 62]), "D": (38, [54, 57, 62]), "Em": (40, [55, 59, 64]), "C": (36, [55, 60, 64]),
    "Am": (45, [57, 60, 64]), "Bsus": (47, [52, 54, 59]), "B": (47, [51, 54, 59]), "G/B": (47, [55, 59, 62]),
    "Cmaj7": (36, [55, 59, 64]),
}
PROG = {"hook": ["G", "D", "Em", "C"], "body": ["G", "D", "Em", "C"], "mystery": ["Em", "Cmaj7", "Am", "Bsus"],
        "explain": ["C", "G/B", "Am", "D"], "payoff": ["C", "D"]}
HOOK_MOTIF = [(0.0, 74, 0.5), (0.5, 79, 0.5), (1.0, 83, 0.75), (2.0, 81, 0.5), (2.5, 79, 0.5), (3.0, 78, 1.0)]

# balance inside the band (LU, each track's own integrated level)
BAL = {"kick": -2.0, "clap": -7.0, "hat": -14.0, "bass": -3.0, "arp": -5.0, "pad": -8.0, "glock": -9.0,
       "vibes": -6.0, "tick": -15.0, "sting": 0.0, "riser": -17.0}
SEND = {"kick": 0.02, "clap": 0.12, "hat": 0.05, "bass": 0.0, "arp": 0.18, "pad": 0.25, "glock": 0.3, "vibes": 0.25,
        "tick": 0.2, "sting": 0.3, "riser": 0.1}


def kick(vel, r):
    t = np.arange(ns(0.45)) / SR
    y = np.sin(phase(48 * (1 + 1.6 * np.exp(-t / 0.025)))) * np.exp(-t / 0.13)
    y += lp(r.standard_normal(len(t)), 3000) * np.exp(-t / 0.002) * 0.3
    return fades(y * vel, 0.0002, 0.03)


def clap(vel, r):
    t = np.arange(ns(0.3)) / SR
    nz = bp(r.standard_normal(len(t)), 900, 5000, 2)
    e = sum(np.exp(-np.maximum(t - d, 0) / 0.006) * (t >= d) for d in (0.0, 0.011, 0.022))
    e += np.exp(-np.maximum(t - 0.03, 0) / 0.07) * (t >= 0.03)
    return fades(nz * e * vel, 0.0002, 0.03)


class Score:
    def __init__(self, n, seed=2026):
        self.n = n
        self.tr = {}
        self.R = rng(seed)
        self.map = []

    def r(self):
        return rng(int(self.R.integers(1 << 30)))

    def add(self, name, x, t, p=0.0, g=1.0):
        if t >= self.n / SR or t < -1:
            return
        buf = self.tr.setdefault(name, np.zeros((2, self.n)))
        place(buf, pan(x, p) if np.ndim(x) == 1 else x, max(t, 0.0), g)

    # -------------------------------------------------------------- section writers
    def grid(self, a, b):
        """bars (t_bar, bar index) starting at a, until b"""
        k, out = 0, []
        while a + k * 4 * Q < b - 0.05:
            out.append((a + k * 4 * Q, k))
            k += 1
        return out

    def drive(self, a, b, prog, motif=False, full=True):
        for t, k in self.grid(a, b):
            name = prog[k % len(prog)]
            root, ch = CH[name]
            notes = ch + [ch[0] + 12]
            for i, s in enumerate([0, 1, 2, 3, 2, 1, 2, 3]):                     # 8th-note pluck arpeggio
                tn = t + i * Q / 2
                if tn < b:
                    self.add("arp", I.pluck(F(notes[s] + 12), 0.55 + 0.1 * (i % 2 == 0), self.r(), 0.5, 0.55), tn,
                             0.25 * (-1) ** i)
            for bt in ([0, 1.5, 2] if full else [0, 2]):                          # kick
                if t + bt * Q < b:
                    self.add("kick", kick(0.9, self.r()), t + bt * Q)
            for bt in (1, 3):                                                     # clap on 2 and 4
                if t + bt * Q < b:
                    self.add("clap", clap(0.8, self.r()), t + bt * Q, 0.05)
            if full:
                for i in range(8):                                                # brush hats
                    if t + i * Q / 2 < b:
                        self.add("hat", I.brush(0.5 if i % 2 else 0.8, self.r(), 0.12), t + i * Q / 2, 0.35)
            for bt, dur in ((0, 1.4 * Q), (2.5, 0.4 * Q), (3, 0.9 * Q)):          # bass (pizz)
                if t + bt * Q < b:
                    m = root + (12 if bt == 2.5 else 0)
                    self.add("bass", I.pluck(F(m), 0.85, self.r(), dur + 0.3, 0.3, 0.12), t + bt * Q, -0.05)
            if full:
                self.add("pad", I.pad([F(m) for m in ch], min(4 * Q, b - t), 0.5, self.r(), att=0.15, rel=0.4), t)
            if motif and k % 2 == 0:
                for bt, m, d in HOOK_MOTIF:
                    if t + bt * Q < b:
                        self.add("glock", I.glock(F(m), 0.6, self.r(), 1.0), t + bt * Q, 0.2)

    def mystery(self, a, b):
        for t, k in self.grid(a, b):
            root, ch = CH[PROG["mystery"][k % 4]]
            self.add("pad", I.pad([F(m) for m in ch], min(4 * Q, b - t) + 0.2, 0.55, self.r(), att=0.4, rel=0.6), t)
            self.add("bass", I.pluck(F(root), 0.7, self.r(), 2.0, 0.2, 0.12), t, -0.05)
            for bt in range(4):                                                   # ticking glock, 'thinking'
                if t + bt * Q < b:
                    self.add("tick", I.glock(F(86 if bt % 2 == 0 else 83), 0.4, self.r(), 0.4), t + bt * Q, 0.3)

    def explain(self, a, b):
        for t, k in self.grid(a, b):
            root, ch = CH[PROG["explain"][k % 4]]
            self.add("pad", I.pad([F(m) for m in ch], min(4 * Q, b - t), 0.45, self.r(), att=0.2, rel=0.5), t)
            for bt in range(4):
                if t + bt * Q < b:
                    m = (ch + [ch[0] + 12])[bt] + 12
                    self.add("vibes", I.vibes(F(m), 0.55, self.r(), 1.1), t + bt * Q, 0.2 * (-1) ** bt)
            for bt, dur in ((0, 1.6 * Q), (2, 1.6 * Q)):
                if t + bt * Q < b:
                    self.add("bass", I.pluck(F(root), 0.8, self.r(), dur + 0.3, 0.3, 0.12), t + bt * Q, -0.05)
            if k >= 1:                                                            # light pulse comes back
                for bt in (0, 2):
                    if t + bt * Q < b:
                        self.add("kick", kick(0.6, self.r()), t + bt * Q)
                for i in range(8):
                    if t + i * Q / 2 < b:
                        self.add("hat", I.brush(0.35 if i % 2 else 0.55, self.r(), 0.1), t + i * Q / 2, 0.35)

    def payoff(self, a, b):
        """thin out under the punchline: pad + one pluck per bar, so the last line lands dry"""
        for t, k in self.grid(a, b):
            root, ch = CH[PROG["payoff"][k % 2]]
            self.add("pad", I.pad([F(m) for m in ch], min(4 * Q, b - t) + 0.1, 0.35, self.r(), att=0.3, rel=0.25), t)
            self.add("bass", I.pluck(F(root), 0.6, self.r(), 1.2, 0.2, 0.12), t, -0.05)

    def sting(self, t):
        """final chord on the last word: pluck chord + glock + kick + soft cymbal + pad, rings out"""
        root, ch = CH["G"]
        for i, m in enumerate(ch + [67]):
            self.add("sting", I.pluck(F(m), 0.8, self.r(), 2.5, 0.6), t + 0.012 * i, 0.3 * (i - 1.5) / 1.5)
        self.add("sting", I.glock(F(79), 0.7, self.r(), 2.0), t, 0.2)
        self.add("sting", I.glock(F(86), 0.5, self.r(), 2.0), t + 0.06, -0.2)
        self.add("sting", I.pluck(F(root), 1.0, self.r(), 2.5, 0.3, 0.12) * 1.2, t)
        self.add("sting", kick(1.0, self.r()) * 0.9, t)
        self.add("sting", I.cymbal(0.25, self.r(), 2.5, 0.7), t)
        self.add("sting", I.pad([F(m) for m in ch + [67]], 1.2, 0.5, self.r(), att=0.05, rel=1.2), t)

    def riser(self, t_end, dur=1.0):
        from sfx_x import riser
        self.add("riser", riser(self.r(), dur), t_end - dur)

    # -------------------------------------------------------------- render
    def render(self, ref=-20.0):
        hall = make_ir(1.3, 11, pre=0.015, hf=1.5)
        dry = np.zeros((2, self.n))
        wet = np.zeros(self.n)
        for k, x in self.tr.items():
            L = integrated(x)
            if not np.isfinite(L):
                continue
            x = x * dbg(ref + BAL.get(k, -8) - L)
            self.tr[k] = x
            dry += x
            wet += SEND.get(k, 0.1) * x.mean(0)
        return hp(dry + 0.8 * convolve_st(wet, hall), 35, 2)


def build(sec, n, seed=2026):
    """sec: dict name -> (a, b) times; 'sting' -> t. Returns (stereo music, map rows)."""
    s = Score(n, seed)
    rows = []
    if "hook" in sec:
        a, b = sec["hook"]
        s.drive(a, b, PROG["hook"], motif=True, full=False)
        rows.append((a, "hook: pluck arpeggio I-V-vi-IV, glock motif, kick + clap (no hats), from the first word"))
    if "body" in sec:
        a, b = sec["body"]
        s.drive(a, b, PROG["body"], motif=False, full=True)
        rows.append((a, "body: full groove, hats + pad join, 112 bpm"))
    if "mystery" in sec:
        a, b = sec["mystery"]
        s.mystery(a, b)
        rows.append((a, "mystery: drums drop out, sus pad vi-IV-ii-Vsus + ticking glock"))
    if "explain" in sec:
        a, b = sec["explain"]
        s.riser(a, 0.9)
        s.explain(a, b)
        rows.append((a - 0.9, "riser into the pivot"))
        rows.append((a, "'You see,': light vibes arpeggio IV-I/3-ii-V, bass; soft kick + brushes from bar 2"))
    if "payoff" in sec:
        a, b = sec["payoff"]
        s.payoff(a, b)
        rows.append((a, "payoff: thins to pad + bass so the punchline lands dry"))
    if "sting" in sec:
        s.sting(sec["sting"])
        rows.append((sec["sting"], "sting: G major chord, glock, kick, soft cymbal right after the last word, rings out"))
    return s.render(), rows
