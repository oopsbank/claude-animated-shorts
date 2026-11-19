# Thumbnail title over the rendered background (scripts/thumb.mjs), in the subtitle style: Inter ExtraBold, cream /
# gold fill, thick dark-brown outline, hard drop shadow. usage: python3 thumb_text.py bg.png out.png
import sys
from PIL import Image, ImageDraw, ImageFont, ImageFilter
FONT = "public/Inter-ExtraBold.otf"
INK, CREAM, GOLD = (42, 20, 7, 255), (255, 250, 240, 255), (255, 197, 49, 255)
bg = Image.open(sys.argv[1]).convert("RGBA")
W, H = bg.size


def line(text, size, fill, cx, cy, rot=0.0, stroke=None):
    f = ImageFont.truetype(FONT, size)
    st = stroke or max(8, size // 9)
    l, t, r, b = ImageDraw.Draw(bg).textbbox((0, 0), text, font=f, stroke_width=st)
    pad = st * 3
    lay = Image.new("RGBA", (r - l + 2 * pad, b - t + 2 * pad + size // 8), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    o = (pad - l, pad - t)
    sh = Image.new("RGBA", lay.size, (0, 0, 0, 0))  # soft shadow
    ImageDraw.Draw(sh).text((o[0], o[1] + size // 7), text, font=f, fill=(0, 0, 0, 120), stroke_width=st, stroke_fill=(0, 0, 0, 120))
    lay = Image.alpha_composite(lay, sh.filter(ImageFilter.GaussianBlur(size // 10)))
    d = ImageDraw.Draw(lay)
    d.text((o[0], o[1] + size // 14), text, font=f, fill=INK, stroke_width=st, stroke_fill=INK)  # hard drop
    d.text(o, text, font=f, fill=fill, stroke_width=st, stroke_fill=INK)
    lay = lay.rotate(rot, resample=Image.BICUBIC, expand=True)
    bg.alpha_composite(lay, (int(cx - lay.width / 2), int(cy - lay.height / 2)))


s = W / 1080
# everything inside the middle 3:4 band (y 240 .. 1680 at 1080x1920)
line("PAUSE TIME...", int(104 * s), CREAM, W * 0.5, H * 0.17, 2.0)
line("BUT ONLY", int(122 * s), CREAM, W * 0.5, H * 0.245, -2.0)
line("YOU AGE?!", int(172 * s), GOLD, W * 0.5, H * 0.335, -3.0, stroke=int(21 * s))
bg.convert("RGB").save(sys.argv[2], quality=95)
print("ok", sys.argv[2], bg.size)
