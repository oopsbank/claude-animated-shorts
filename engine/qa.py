# Automatic checks from QA.md > engine and video, on a render_video.py output folder (frames/ + track.json).
# usage: python engine/qa.py out_dir [--video out_dir/video.mp4] [--no-sheet]
#   - no black, white or frozen spans of >= 12 frames (from the frame images);
#   - no character clipped at the frame edge (left/right/top always; bottom unless the shot sets "crop");
#   - grounded characters' feet on the plate's ground line (+-4 px);
#   - planted feet move <= 2 px between frames while grounded and not turning;
#   - beats land 0-3 frames before their word;
#   - frame stats vs the reference targets (references/scripts/frame_stats.py), reported as a warning per shot;
#   - contact sheets every 0.5 s for the reviewer (qa/contact_*.jpg) and qa/report.md.
# Exit code 0 = all hard checks pass.
import os, sys, json, glob, argparse, subprocess
import numpy as np
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.abspath(os.path.join(HERE, '..'))
SPAN = 12


def runs(flags, min_len=SPAN):
    out, s = [], None
    for i, v in enumerate(list(flags) + [False]):
        if v and s is None: s = i
        if not v and s is not None:
            if i - s >= min_len: out.append((s, i - 1))
            s = None
    return out


def load_small(paths, w=180, h=320):
    return np.stack([np.asarray(Image.open(p).convert('RGB').resize((w, h), Image.BILINEAR)) for p in paths])


def contact_sheets(paths, fps, out, every=0.5, cols=8, per=48):
    step = max(1, int(round(every * fps))); sel = paths[::step]; tw, th = 180, 320; made = []
    for k in range(0, len(sel), per):
        chunk = sel[k:k + per]; rows = (len(chunk) + cols - 1) // cols
        sh = Image.new('RGB', (cols * tw, rows * (th + 18)), (255, 255, 255)); d = ImageDraw.Draw(sh)
        for i, p in enumerate(chunk):
            f = int(os.path.basename(p).split('_')[1].split('.')[0])
            x, y = (i % cols) * tw, (i // cols) * (th + 18)
            sh.paste(Image.open(p).convert('RGB').resize((tw, th), Image.LANCZOS), (x, y + 18))
            d.text((x + 4, y + 3), f'{f / fps:5.1f}s  f{f}', fill=(0, 0, 0))
        name = os.path.join(out, f'contact_{k // per:02d}.jpg'); sh.save(name, quality=88); made.append(name)
    return made


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('out'); ap.add_argument('--video'); ap.add_argument('--no-sheet', action='store_true')
    a = ap.parse_args()
    tr = json.load(open(os.path.join(a.out, 'track.json'))); fps = tr['fps']; W, H = tr['size']
    paths = sorted(glob.glob(os.path.join(a.out, 'frames', 'f_*.*')))
    qd = os.path.join(a.out, 'qa'); os.makedirs(qd, exist_ok=True)
    R, fails = [], []

    def check(name, bad, detail=''):
        R.append(f"- [{'x' if not bad else ' '}] **{name}**: {'PASS' if not bad else 'FAIL'} {detail}")
        if bad: fails.append(name)

    # ---- picture: black / white / frozen
    F = load_small(paths).astype(np.float32)
    lum = (F / 255 @ np.array([0.2126, 0.7152, 0.0722])).reshape(len(F), -1).mean(1)
    diff = np.r_[99.0, np.abs(np.diff(F, axis=0)).mean(axis=(1, 2, 3))]
    blk, wht, frz = runs(lum < 0.04), runs(lum > 0.93), runs(diff < 0.25)
    check('no black spans >= 12 f', blk, str(blk[:5]))
    check('no white spans >= 12 f', wht, str(wht[:5]))
    check('no frozen spans >= 12 f', frz, str(frz[:5]) + f' (median frame diff {np.median(diff[1:]):.2f} grey levels)')
    if len(paths) != tr['n']: check('frame count matches the timeline', True, f'{len(paths)} files vs {tr["n"]}')

    # ---- characters
    crop = {sp['id']: sp.get('crop') for sp in tr['spans']}
    clip, ground, planted, prev = [], [], [], {}
    for m in tr['frames']:
        f = m['f']
        for c in m['chars']:
            sb = c.get('screen_bbox')
            if sb:
                edges = [e for e, v in (('left', sb[0] < 1), ('right', sb[2] > W - 1), ('top', sb[1] < 1),
                                         ('bottom', sb[3] > H - 1 and not crop.get(m['shot']))) if v]
                if edges and not m.get('transition') and not c.get('near') and not m.get('crop_any'): clip.append((f, c['id'], edges))
            if c['grounded'] and c['foot_y'] is not None and c['ground_y'] < H and abs(c['foot_y'] - c['ground_y']) > 4:   # off-frame ground: n/a
                ground.append((f, c['id'], round(c['foot_y'] - c['ground_y'], 1)))
            key = (m['shot'], c['id']); p = prev.get(key)
            if p and p['f'] == f - 1 and p.get('planted', p['grounded']) and c.get('planted', c['grounded']) and p.get('facing') == c.get('facing'):
                for side in ('foot_l', 'foot_r'):
                    if p[side] is not None and c[side] is not None and abs(p[side] - c[side]) > 2:
                        planted.append((f, c['id'], side, round(c[side] - p[side], 1)))
            prev[key] = dict(c, f=f)
    check('no character clipped at the frame edge', clip, f'{len(clip)} frames; first: {clip[:4]}')
    check('feet on the ground line (+-4 px)', ground, f'{len(ground)} frames; worst: {sorted(ground, key=lambda g: -abs(g[2]))[:4]}')
    check('planted feet move <= 2 px', planted, f'{len(planted)} frames; first: {planted[:4]}')

    # ---- beats
    late = [(b['shot'], b['char'], b['word'], b['word_frame'] - b['land']) for b in tr['beats']
            if not 0 <= b['word_frame'] - b['land'] <= 3 or not b['shot_f0'] <= b['land'] < b['shot_f1']]
    check('beats land 0-3 f before their word', late, f"{len(tr['beats'])} beats; off: {late[:5]}")

    # ---- frame stats (warning): one frame per second
    fs = os.path.join(ROOT, 'references', 'scripts', 'frame_stats.py'); stat_lines = []
    if os.path.exists(fs):
        sample = paths[::fps]
        r = subprocess.run([sys.executable, '-I', fs] + sample, capture_output=True, text=True)
        lines = r.stdout.strip().splitlines(); ok = sum(l.endswith('PASS') for l in lines)
        R.append(f'- [i] frame stats (reference targets, warning only): {ok}/{len(lines)} sampled frames pass')
        stat_lines = lines
    if a.video and os.path.exists(a.video):
        pr = json.loads(subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'stream=width,height,r_frame_rate,nb_frames', '-of', 'json', a.video],
                                       capture_output=True, text=True).stdout)['streams'][0]
        okv = (pr['width'], pr['height'], pr['r_frame_rate']) == (W, H, f'{fps}/1') and int(pr.get('nb_frames', 0)) == tr['n']
        check('mp4 is 1080x1920, 30 fps, frame count matches', not okv, str(pr))
    sheets = [] if a.no_sheet else contact_sheets(paths, fps, qd)
    rep = ['# Engine QA', '', f"{tr['n']} frames ({tr['n'] / fps:.2f} s), {len(tr['spans'])} shots", ''] + R + \
          ['', '## Frame stats (1 per second)', '```'] + [os.path.basename(l.split()[0]) + ' ' + ' '.join(l.split()[1:]) for l in stat_lines] + ['```', ''] + \
          ['Contact sheets (every 0.5 s): ' + ', '.join(os.path.basename(s) for s in sheets)]
    open(os.path.join(qd, 'report.md'), 'w').write('\n'.join(rep) + '\n')
    print('\n'.join(R)); print('FAIL: ' + ', '.join(fails) if fails else 'ALL HARD CHECKS PASS')
    sys.exit(1 if fails else 0)


if __name__ == '__main__':
    main()
