import sys, random, math
sys.path.insert(0, 'stickman/scripts')
from stickman import draw
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageChops
W, H = 1080, 1920; INK = (18, 16, 26)
F = 'engine/fonts/Poppins-ExtraBold.ttf'; FB = 'engine/fonts/Poppins-Bold.ttf'
random.seed(7)
def lerp(a, b, t): return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))
def layer(): return Image.new('RGBA', (W, H), (0, 0, 0, 0))
def comp(base, l, blur=0):
    if blur: l = l.filter(ImageFilter.GaussianBlur(blur))
    base.alpha_composite(l)
im = Image.new('RGBA', (W, H)); d = ImageDraw.Draw(im)
for y in range(H):  # polar sky: deep blue -> pale peach horizon
    t = min(1, y / 1000); d.line([(0, y), (W, y)], fill=lerp((58, 104, 170), (250, 214, 190), t ** 1.4) + (255,))
g = layer(); ImageDraw.Draw(g).ellipse([600, 640, 1200, 1240], fill=(255, 236, 200, 170)); comp(im, g, 90)  # low sun glow
ImageDraw.Draw(im).ellipse([840, 880, 960, 1000], fill=(255, 246, 225, 255))
def ridge(y0, amp, col, seed, ink=False, step=60):
    random.seed(seed); pts = [(0, H)]; x = 0
    while x <= W + step: pts.append((x, y0 - random.random() * amp)); x += step
    pts.append((W, H)); l = layer(); ld = ImageDraw.Draw(l); ld.polygon(pts, fill=col)
    if ink: ld.line(pts[1:-1], fill=INK + (255,), width=5)
    return l, pts
for y0, amp, col, s, bl in ((980, 220, (170, 170, 205, 255), 1, 3), (1040, 160, (140, 160, 205, 255), 2, 1)):
    l, _ = ridge(y0, amp, col, s); comp(im, l, bl)
haze = layer(); hd = ImageDraw.Draw(haze)
for y in range(950, 1150): hd.line([(0, y), (W, y)], fill=(255, 230, 215, int(110 * (1 - abs(y - 1050) / 100))))
comp(im, haze, 10)
# glacier wall: faceted ice with light & shadow planes
gl = layer(); gd = ImageDraw.Draw(gl)
top = [(300, 1010), (380, 960), (470, 985), (560, 930), (660, 960), (760, 915), (880, 950), (1000, 905), (1080, 925)]
face = top + [(1080, 1560), (300, 1580)]
gd.polygon(face, fill=(214, 234, 248, 255))
for i in range(len(top) - 1):
    (x0, y0), (x1, y1) = top[i], top[i + 1]
    col = (238, 248, 255, 255) if i % 2 else (176, 208, 236, 255)
    gd.polygon([(x0, y0), (x1, y1), (x1 + 20, 1560), (x0 + 10, 1580)], fill=col)
    gd.line([(x0, y0), (x0 + 10, 1580)], fill=(150, 190, 225, 255), width=4)
for i in range(40):  # strata lines
    y = random.randint(1050, 1540); x = random.randint(300, 1000); gd.line([(x, y), (x + random.randint(40, 140), y + 4)], fill=(160, 196, 228, 255), width=3)
for x in range(310, 1080, 38):  # icicles at the lip
    yb = 1000 if x < 700 else 950; L = random.randint(20, 70); gd.polygon([(x, yb), (x + 16, yb), (x + 8, yb + L)], fill=(236, 248, 255, 255))
gd.line(top, fill=INK + (255,), width=6); gd.line([(300, 1010), (300, 1580)], fill=INK + (255,), width=6)
comp(im, gl)
# the blood falls: gradient stream with highlights and drips
fl = layer(); fd = ImageDraw.Draw(fl)
path = [(650, 950), (690, 945), (705, 1100), (730, 1300), (790, 1500), (830, 1580), (690, 1590), (640, 1420), (620, 1200), (630, 1050)]
fd.polygon(path, fill=(168, 22, 30, 255))
fd.polygon([(662, 955), (680, 955), (690, 1150), (720, 1400), (700, 1420), (668, 1180)], fill=(220, 60, 52, 255))
for i in range(6): fd.line([(640 + i * 12, 1000 + i * 70), (650 + i * 14, 1080 + i * 70)], fill=(250, 130, 110, 220), width=4)
fd.line(path + path[:1], fill=INK + (255,), width=6)
comp(im, fl)
gw = layer(); ImageDraw.Draw(gw).polygon(path, fill=(255, 60, 50, 90)); comp(im, gw, 40)  # red glow
# snow ground with red pool, shadows, footprints
sn = layer(); sd = ImageDraw.Draw(sn)
sd.polygon([(0, 1560), (300, 1580), (1080, 1545), (1080, H), (0, H)], fill=(246, 249, 253, 255))
sd.line([(0, 1560), (300, 1580), (1080, 1545)], fill=INK + (255,), width=6)
sd.polygon([(640, 1590), (840, 1585), (1080, 1680), (1080, 1800), (900, 1760), (700, 1660)], fill=(178, 30, 36, 255))
sd.polygon([(700, 1620), (860, 1620), (1080, 1720), (1040, 1730)], fill=(214, 70, 60, 255))
for k in range(6):
    x = 120 + k * 45; y = 1880 - k * 50; sd.ellipse([x, y, x + 30, y + 14], fill=(205, 218, 235, 255))
comp(im, sn)
sh = layer(); ImageDraw.Draw(sh).ellipse([150, 1585, 420, 1625], fill=(90, 110, 150, 120)); comp(im, sh, 8)
# character bigger, with rim light glow and label
c = draw(expr='surprised', pose='point', color='#f6f6f2', look=0.6); s = 0.82; c = c.resize((int(600 * s), int(1000 * s)), Image.LANCZOS)
cx, gy = 290, 1610; px, py = int(cx - c.width / 2), int(gy - 975 * s)
halo = layer(); halo.paste((120, 170, 255, 150), (px, py), c.split()[3]); comp(im, halo, 25)
im.alpha_composite(c, (px, py))
d = ImageDraw.Draw(im); f = ImageFont.truetype(FB, 40); txt = 'GEOLOGIST · 1911'; w = d.textlength(txt, font=f)
lg = layer(); ImageDraw.Draw(lg).rounded_rectangle([cx - w/2 - 26, py + 40, cx + w/2 + 26, py + 112], 34, fill=(60, 120, 230, 160)); comp(im, lg, 14)
d.rounded_rectangle([cx - w/2 - 22, py + 44, cx + w/2 + 22, py + 108], 32, fill=(52, 110, 215), outline=INK, width=5)
d.text((cx - w/2, py + 50), txt, font=f, fill='white')
# falling snow (3 depths) + vignette
for depth, n, r, bl in ((0, 60, 4, 0), (1, 30, 9, 2), (2, 10, 18, 5)):
    l = layer(); ld = ImageDraw.Draw(l)
    for i in range(n):
        x, y = random.randint(0, W), random.randint(0, H); ld.ellipse([x, y, x + r, y + r], fill=(255, 255, 255, 200))
    comp(im, l, bl)
v = Image.new('L', (W, H), 0); ImageDraw.Draw(v).ellipse([-300, -200, W + 300, H + 200], fill=255); v = v.filter(ImageFilter.GaussianBlur(160))
dark = Image.new('RGBA', (W, H), (20, 20, 50, 255)); im = Image.composite(im, dark, ImageChops.lighter(v, Image.new('L', (W, H), 150)))
d = ImageDraw.Draw(im); ft = ImageFont.truetype(F, 92); yy = 240
for line in ('THE GLACIER', 'IS BLEEDING'):
    w = d.textlength(line, font=ft); col = 'white' if yy < 300 else (255, 80, 70)
    d.text(((W - w) / 2 + 5, yy + 8), line, font=ft, fill=(0, 0, 0), stroke_width=9, stroke_fill=(0, 0, 0))
    d.text(((W - w) / 2, yy), line, font=ft, fill=col, stroke_width=9, stroke_fill=INK); yy += 108
size = int(0.037 * H); fc = ImageFont.truetype(FB, size); txt = 'found it'; w = d.textlength(txt, font=fc)
d.text(((W - w) / 2, 0.70 * H - size), txt, font=fc, fill='white', stroke_width=int(size * .1), stroke_fill='black')
out = sys.argv[1]; im.convert('RGB').resize((540, 960), Image.LANCZOS).save(out + '/rich_A.png')
old = Image.open(out + '/frame_A.png').convert('RGB'); s2 = Image.new('RGB', (1110, 980), 'white')
s2.paste(old, (10, 10)); s2.paste(Image.open(out + '/rich_A.png'), (560, 10)); s2.save(out + '/compare_A.jpg', quality=88)
