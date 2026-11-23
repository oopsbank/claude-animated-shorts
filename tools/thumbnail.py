# Thumbnail in the channel's house style: a caption-free engine frame (zoomed onto the action) with a big
# 3-4 line headline in the top third, white with one or two keyword lines in yellow/red, thick plum outline + shadow.
# usage: .venv/bin/python tools/thumbnail.py frame.png out.png --zoom 1.3 --focus 0.5,0.55 \
#            --line "WHY YOUR BIKE|white|100" --line "BACKWARDS|yellow|170" ...
# Render the frame without captions first: copy shots.json with "captions": {"enabled": false} and
# engine/render_video.py ... --frames N, --png --no-mp4.
import sys, os, argparse
from PIL import Image, ImageDraw, ImageFont, ImageFilter

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
sys.path.insert(0, os.path.join(ROOT, 'engine'))
import captions as CAP  # noqa: E402  (same bold face as the captions)

W, H = 1080, 1920
COLORS = {'white': (255, 255, 255), 'yellow': (255, 210, 63), 'red': (239, 75, 58), 'blue': (130, 206, 255)}
INK = (36, 23, 38)


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('frame'); ap.add_argument('out')
    ap.add_argument('--zoom', type=float, default=1.0); ap.add_argument('--focus', default='0.5,0.5')
    ap.add_argument('--line', action='append', required=True, help='TEXT|color|px')
    ap.add_argument('--top', type=float, default=0.07, help='first baseline region, fraction of the height')
    a = ap.parse_args()
    im = Image.open(a.frame).convert('RGB').resize((W, H))
    if a.zoom > 1:
        fx, fy = (float(v) for v in a.focus.split(','))
        cw, ch = W / a.zoom, H / a.zoom
        x0 = min(max(fx * W - cw / 2, 0), W - cw); y0 = min(max(fy * H - ch / 2, 0), H - ch)
        im = im.crop((int(x0), int(y0), int(x0 + cw), int(y0 + ch))).resize((W, H), Image.LANCZOS)
    # darken the top a touch so white text reads on bright skies
    grad = Image.linear_gradient('L').resize((W, H)).point(lambda v: int(max(0, 110 - v * 0.9)))
    im = Image.composite(Image.new('RGB', (W, H), INK), im, grad)
    lay = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    y = a.top * H
    for spec in a.line:
        text, col, px = spec.split('|'); px = int(px)
        f = ImageFont.truetype(CAP.font_path(), px)
        while d.textlength(text, font=f) > W * 0.92 and px > 40: px -= 4; f = ImageFont.truetype(CAP.font_path(), px)
        tw = d.textlength(text, font=f); x = (W - tw) / 2
        sh = Image.new('RGBA', (W, H), (0, 0, 0, 0)); ds = ImageDraw.Draw(sh)
        ds.text((x + px * 0.05, y + px * 0.07), text, font=f, fill=INK + (200,), stroke_width=int(px * 0.12), stroke_fill=INK + (200,))
        lay.alpha_composite(sh.filter(ImageFilter.GaussianBlur(px * 0.04)))
        d.text((x, y), text, font=f, fill=COLORS.get(col, (255, 255, 255)), stroke_width=int(px * 0.1), stroke_fill=INK)
        y += px * 1.02
    out = im.convert('RGBA'); out.alpha_composite(lay); out.convert('RGB').save(a.out)
    print(a.out)


if __name__ == '__main__':
    main()
