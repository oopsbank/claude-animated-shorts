# Preflight: catch defects in shots.json BEFORE any voice-over or render is spent on them (seconds, no rendering).
# Every check here is a defect that the first video only found after a full render or a full-cut review.
# usage: .venv/bin/python tools/preflight.py scripts/<slug>/shots.json [words.json] [--plates DIR ...] [--out report.md]
# Without words.json it uses stand-in timings (3.7 words/s, like engine/fake_words.py).
# Exit code 1 if any ERROR. WARNs need a decision: fix it, or write why it's fine in the shot's "note".
import os, sys, json, re, argparse, io, contextlib

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
sys.path.insert(0, os.path.join(ROOT, 'engine'))
os.environ.setdefault('ENGINE_QUIET', '1'); os.environ.setdefault('ENGINE_STANDIN', '0')
import anim  # noqa: E402
import render_video as RV  # noqa: E402

W, H, FPS = anim.W, anim.H, anim.FPS
SYMBOLS = {'question_mark', 'exclaim', 'anger_vein', 'sweat_drop', 'music_note'}
DIRECTIONAL = {'steer_arrow', 'lean_arc'}
BODY_KEYS = {'arm_pose', 'pose', 'lean', 'body_lean', 'facing', 'prop', 'look', 'tilt', 'knee_out', 'steer', 'contact_shift'}
MIN_H = {'close': 0.33, 'medium': 0.28, 'wide': 0.14}        # character height (at the shot's tightest zoom) / frame height
# Bare plates, before characters and the engine grade: flag only misses the grade can't fix (v1: golden plates at
# lum 0.28-0.33 gave 6/65 passing frames). Edge density is left to qa.py, because characters add most of it.
TARGET = {'lum': (0.36, 0.66), 'sat': (0.26, 0.60)}


def fake_words(shots, wps=3.7):
    out, t = [], 0.3
    for s in shots:
        for w in s['text'].split():
            out.append({'word': w.strip('.,!?:;"'), 'start': round(t, 3), 'end': round(t + 0.8 / wps, 3)})
            t += 1 / wps + (0.35 if w.rstrip('"')[-1] in '.!?' else 0.12 if w.rstrip('"')[-1] in ',:;' else 0)
    return out


def plate_stats(png):
    # same measure as references/scripts/frame_stats.py (which can't be imported: it runs its CLI at import)
    import numpy as np
    from PIL import Image
    im = Image.open(png).convert('RGB').resize((270, 480)); a = np.asarray(im).astype(np.float32) / 255
    L = a @ np.array([.2126, .7152, .0722]); S = np.asarray(im.convert('HSV')).astype(np.float32)[..., 1] / 255
    g = np.asarray(im.convert('L')).astype(np.float32)
    e = ((np.abs(np.diff(g, axis=1))[:-1, :] + np.abs(np.diff(g, axis=0))[:, :-1]) > 60).mean()
    return {'lum': float(L.mean()), 'sat': float(S.mean()), 'edge': float(e)}


def max_zoom(cam):
    cam = cam or {}; z = [float(cam.get('zoom', 1.0))]
    for g in [cam] + list(cam.get('glides', [])):
        if 'to' in g: z.append(float(g['to'].get('zoom', 1.0)))
    if cam.get('move') == 'push_in': z.append(1 + float(cam.get('amount', 0.05)))
    return max(z)


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('shots'); ap.add_argument('words', nargs='?')
    ap.add_argument('--plates', action='append', default=[]); ap.add_argument('--out')
    a = ap.parse_args()
    doc = json.load(open(a.shots)); shots = doc['shots']
    words = json.load(open(a.words)) if a.words else fake_words(shots)
    if isinstance(words, dict): words = words.get('words', [])
    spans = anim.shot_spans(shots, words)
    plate_dirs = a.plates or [os.path.join(ROOT, 'blender', 'sets', s, 'plates') for s in sorted({s['set'] for s in shots})]
    rows, seen_plates = [], {}

    def add(level, sid, msg): rows.append((level, sid, msg))

    # ---- script level
    text = ' '.join(s['text'] for s in shots); n = len(text.split())
    if not 170 <= n <= 240: add('ERROR', '-', f'voice-over is {n} words (need 170-240; aim <= 232)')
    hook = re.split(r'(?<=[.!?])\s', shots[0]['text'] if shots else '')[0]
    if not 10 <= len(hook.split()) <= 16: add('ERROR', 's01', f'hook is {len(hook.split())} words (need 10-16): "{hook}"')
    script_md = os.path.join(os.path.dirname(a.shots), 'SCRIPT.md')
    if os.path.exists(script_md) and not re.search(r'https?://', open(script_md).read()):
        add('ERROR', '-', 'SCRIPT.md has no source URLs')

    for k, (s, sp) in enumerate(zip(shots, spans)):
        sid = s.get('id', f'#{k}'); nw = len(s['text'].split()); size = s.get('size', 'medium')
        dur = (sp['f1'] - sp['f0']) / FPS
        if dur < 1.2: add('WARN', sid, f'shot lasts {dur:.1f} s: too short to read; merge it with a neighbour')
        if dur > 6.5: add('WARN', sid, f'shot lasts {dur:.1f} s with one framing: add a camera move, a cut or an insert')

        # every at_word inside the shot's own text
        def chk(at, what):
            if at is not None and not 0 <= int(at) < nw: add('ERROR', sid, f'{what} at_word {at} outside the shot (0..{nw - 1})')
        for e in s.get('fx', []): chk(e.get('at_word', 0), f"fx {e['name']}")
        chk((s.get('camera') or {}).get('at_word'), 'camera')
        for c in s.get('characters', []):
            for b in c.get('beats', []): chk(b.get('at_word', 0), f"{c.get('id')} beat")
            if c.get('insert'): chk(c['insert'].get('at_word', 0), f"{c.get('id')} insert")

        # plate exists (the engine falls back to a stand-in silently when ENGINE_STANDIN=1)
        with contextlib.redirect_stdout(io.StringIO()):
            try: p = RV.find_plate(s, plate_dirs)
            except Exception: p = None
        if not p or not os.path.exists(p):
            add('ERROR', sid, f"no plate for {s['set']}/{s['cam']}/{s['light']}: add it to the sets backlog before voicing")
            continue
        meta = json.load(open(os.path.splitext(p)[0] + '.json'))
        if p not in seen_plates:
            st = plate_stats(p); seen_plates[p] = st
            bad = [f'{kk}={st[kk]:.2f} (target {lo}-{hi})' for kk, (lo, hi) in TARGET.items() if not lo <= st[kk] <= hi]
            if bad and s['light'] != 'night': add('WARN', sid, f'plate {os.path.basename(p)} off the reference look: ' + ', '.join(bad))

        top = 'top' in s['cam']
        # staging, measured with the engine's own layout
        cs = json.loads(json.dumps(s.get('characters', [])))
        s2 = dict(s, characters=cs)
        before = {c.get('id'): c.get('x', 0.5) for c in cs}
        RV.resolve_points_at(s2, meta)
        for c in cs:
            for b in c.get('beats', []):
                t = b.get('points_at')
                if t and t not in meta.get('targets', {}) and not any(o.get('id') == t for o in cs):
                    add('WARN', sid, f"{c.get('id')} points_at '{t}' is not a plate target: they will point off-screen")
        RV.layout_shot(s2, meta)
        for c in cs:
            if abs(float(c.get('x', 0.5)) - float(before.get(c.get('id'), 0.5))) > 1e-3:
                add('ERROR', sid, f"{c.get('id')} x {before[c.get('id')]} overlaps another body: the engine moves it to {c['x']}; set x yourself")
            if c.get('_depth'):
                add('WARN', sid, f"{c.get('id')} stepped back to {c['_depth']}x (two-shot too wide for {s['cam']}): use a closer cam or fewer people")
        heights = {}
        for c in cs:
            h = meta['px_per_m'] * 1.75 * float(c.get('scale', 1.0)) * float(c.get('_depth', 1.0)) / H
            heights[c.get('id')] = h; h *= max_zoom(s.get('camera'))
            if h < MIN_H.get(size, 0.3) and not top:
                add('WARN', sid, f"{c.get('id')} is {h:.0%} of the frame height on {s['cam']} ({size} needs >= {MIN_H.get(size, .3):.0%}): they will read as a speck")
        near = [c for c in cs if c.get('_near')]
        for c in cs:
            if near and not c.get('_near') and heights[c.get('id')] < 0.67 * heights[near[0].get('id')]:
                talks = any(b.get('expr') for b in c.get('beats', []))
                if talks: add('WARN', sid, f"{c.get('id')} acts (face beats) but is under 2/3 of the near character's size: swap the OTS or bring them forward")

        # what the camera can see
        for c in cs:
            view = c.get('view', 'front')
            for b in c.get('beats', []):
                if b.get('expr') and (view == 'rear' or view == 'top' or top) and not c.get('insert'):
                    add('ERROR', sid, f"{c.get('id')} face beat '{b['expr']}' at word {b.get('at_word', 0)} but we see their back/top")
                if set(b) - {'at_word', 'expr', 'mouth', 'blink', 'talk'} == set() and b.get('expr') and b.get('at_word', 0) != 0:
                    add('WARN', sid, f"{c.get('id')} beat at word {b.get('at_word')} only changes the face: add a body change")
        views = {c.get('view', 'front') for c in cs}
        for e in s.get('fx', []):
            if e['name'] in DIRECTIONAL and e.get('direction') in ('left', 'right') and cs and views <= {'front'}:
                add('ERROR', sid, f"{e['name']} {e['direction']} in a front-view shot: left/right reads mirrored; use a rear or top cam")
            eff = float(e.get('size', 0.35)) * float(e.get('scale', 1.0))
            if e['name'] in SYMBOLS and eff < 0.4:
                add('WARN', sid, f"{e['name']} at word {e.get('at_word', 0)} is {eff:.2f}W: symbols need >= 0.40W to read on a phone")

    # ---- report
    err = sum(r[0] == 'ERROR' for r in rows); warn = len(rows) - err
    out = [f"# Preflight: {doc.get('title', a.shots)}", '',
           f"{len(shots)} shots, {n} words, {spans[-1]['f1'] / FPS:.1f} s ({'real' if a.words else 'stand-in'} timings). "
           f"**{err} errors, {warn} warnings.**", '', '| level | shot | finding |', '|---|---|---|']
    out += [f'| {l} | {s} | {m} |' for l, s, m in sorted(rows, key=lambda r: (r[0] != 'ERROR', r[1]))]
    md = '\n'.join(out) + '\n'
    if a.out: open(a.out, 'w').write(md)
    print(md); sys.exit(1 if err else 0)


if __name__ == '__main__':
    main()
