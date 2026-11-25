"""Smoke test a flat2d film before a full render: draw every shot at its start, middle and last frame (in parallel)
and report any exception. A crash found here costs seconds; found mid-render it costs the render.

usage: .venv/bin/python flat2d/smoke.py WORDS.json --film plane_windows [--from s05b] [--procs 4]
"""
import os, sys, traceback
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from multiprocessing import Pool
import render

_F = None


def _init(words):
    global _F; _F = render.Film(words)


def _job(T):
    try:
        _F.frame(T); return T, None
    except Exception:
        return T, traceback.format_exc().splitlines()[-1]


if __name__ == '__main__':
    a = sys.argv[1:]; words = a[0]
    opt = lambda k, d: a[a.index(k) + 1] if k in a else d
    film = render.Film(words)
    names = [s[0] for s in film.shots]; k = names.index(opt('--from', names[0]))
    Ts = []
    for name, t0, t1, *_ in film.shots[k:]:
        film.band(name)
        Ts += [t0, (t0 + t1) / 2, t1 - 1 / render.FPS]
    bad = 0
    with Pool(int(opt('--procs', os.cpu_count())), _init, (words,)) as pool:
        for T, err in pool.imap(_job, Ts):
            if err: bad += 1; print(f'{T:7.3f} {film.shot_at(T)[0]:6s} {err}', flush=True)
    print(f'{len(Ts)} frames, {bad} failed:', 'FAIL' if bad else 'PASS')
