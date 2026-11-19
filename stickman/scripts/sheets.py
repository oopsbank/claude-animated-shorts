# Builds the expression / pose reference sheets + individual PNGs. usage: sheets.py <outdir>
import sys, os; sys.path.insert(0, os.path.dirname(__file__))
from stickman import draw
from PIL import Image, ImageDraw, ImageFont
OUT = sys.argv[1]; os.makedirs(OUT, exist_ok=True)
FB = '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'; FR = '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
F = ImageFont.truetype(FB, 40); f2 = ImageFont.truetype(FR, 26); F3 = ImageFont.truetype(FB, 34)
BG = (240, 237, 230, 255); TXT = (30, 30, 40); SUB = (120, 120, 130)
COL = '#4a86e0'
ex = [('neutral', 'Bình thường'), ('happy', 'Vui'), ('angry', 'Giận'), ('surprised', 'Ngạc nhiên'), ('worried', 'Lo lắng'),
      ('scared', 'Sợ hãi'), ('sad', 'Buồn'), ('smug', 'Tự mãn'), ('thinking', 'Đang nghĩ'), ('determined', 'Quyết tâm')]

def face_crop(im):
    top = im.getbbox()[1]
    return im.crop((300 - 125, top - 15, 300 + 125, top + 235))

for e, _ in ex: draw(e, 'stand', COL).save(f'{OUT}/stick_{e}.png')

cw, fh, T = 300, 300, 110
sheet = Image.new('RGBA', (cw * len(ex), T + fh + 70 + 560 + 30), BG); d = ImageDraw.Draw(sheet)
d.text((30, 26), 'Stickman – danh sách biểu cảm', font=F, fill=TXT)
for i, (e, label) in enumerate(ex):
    im = draw(e, 'stand', COL)
    d.rounded_rectangle((i * cw + 14, T, i * cw + cw - 14, T + fh), radius=24, fill=(255, 255, 255, 255))
    face = face_crop(im).resize((fh - 30, fh - 30), Image.LANCZOS)
    sheet.alpha_composite(face, (i * cw + (cw - face.width) // 2, T + 15))
    w = d.textlength(label, font=F3); d.text((i * cw + (cw - w) / 2, T + fh + 12), label, font=F3, fill=TXT)
    w = d.textlength(e, font=f2); d.text((i * cw + (cw - w) / 2, T + fh + 52), e, font=f2, fill=SUB)
    body = im.resize((336, 560), Image.LANCZOS)
    sheet.alpha_composite(body, (i * cw + (cw - body.width) // 2, T + fh + 95))
sheet.save(f'{OUT}/stick_expressions.png')

ps = [('stand', 'Đứng', 'neutral'), ('wave', 'Vẫy tay', 'happy'), ('walk', 'Bước đi', 'neutral'), ('run', 'Chạy', 'scared'),
      ('point', 'Chỉ tay', 'angry'), ('shrug', 'Nhún vai', 'smug'), ('think', 'Suy nghĩ', 'thinking'), ('cheer', 'Ăn mừng', 'happy')]
cols = ['#4a86e0', '#e0583f', '#3fae6a', '#f2b234', '#8a5cd6', '#4a86e0', '#e0583f', '#3fae6a']
ch = 700
sh = Image.new('RGBA', (cw * len(ps), T + 40 + ch + 20), BG); d = ImageDraw.Draw(sh)
d.text((30, 26), 'Stickman – tư thế & màu', font=F, fill=TXT)
for i, ((p, label, e), c) in enumerate(zip(ps, cols)):
    im = draw(e, p, c, 'helmet' if p == 'point' else None).resize((420, ch), Image.LANCZOS)
    w = d.textlength(label, font=F3); d.text((i * cw + (cw - w) / 2, T - 10), label, font=F3, fill=TXT)
    sh.alpha_composite(im, (i * cw + (cw - im.width) // 2, T + 40))
sh.save(f'{OUT}/stick_poses.png')
print('ok')

# ---------------- wardrobe sheets ----------------
def grid(title, cells, out, cols, cw=300, ch=560, lab=70):
    """cells: [(image 600x1000, label, sublabel)] laid out in rows of `cols`."""
    rows = (len(cells) + cols - 1) // cols
    g = Image.new('RGBA', (cw * cols, T + rows * (ch + lab + 20)), BG); dd = ImageDraw.Draw(g)
    dd.text((30, 26), title, font=F, fill=TXT)
    for k, (im, label, sub) in enumerate(cells):
        r, c = divmod(k, cols); x0, y0 = c * cw, T + r * (ch + lab + 20)
        body = im.resize((int(ch * 0.6), ch), Image.LANCZOS)
        g.alpha_composite(body, (x0 + (cw - body.width) // 2, y0))
        w = dd.textlength(label, font=F3); dd.text((x0 + (cw - w) / 2, y0 + ch + 2), label, font=F3, fill=TXT)
        w = dd.textlength(sub, font=f2); dd.text((x0 + (cw - w) / 2, y0 + ch + 40), sub, font=f2, fill=SUB)
    g.save(out)

oc = [('Áo sơ mi', 'shirt=True', dict(shirt=True), '#4a86e0', 'neutral', 'stand'),
      ('Áo khoác dài', 'coat=True', dict(coat=True), '#e0583f', 'happy', 'stand'),
      ('Đồng phục', 'uniform=True', dict(uniform=True), '#3fae6a', 'determined', 'stand'),
      ('Tạp dề', 'apron=True', dict(apron=True, shirt='#6fb3d9'), '#f2b234', 'happy', 'stand'),
      ('Thủy thủ', "outfit='sailor'", dict(outfit='sailor'), '#4a86e0', 'happy', 'stand'),
      ('Thuyền trưởng', "outfit='captain'", dict(outfit='captain'), '#e0583f', 'smug', 'stand'),
      ('Đầu bếp', "outfit='chef'", dict(outfit='chef'), '#f2b234', 'happy', 'stand'),
      ('Thám tử', "outfit='detective'", dict(outfit='detective'), '#8a5cd6', 'thinking', 'think'),
      ('Công nhân', "outfit='worker'", dict(outfit='worker'), '#3fae6a', 'determined', 'point'),
      ('Lính', "outfit='soldier'", dict(outfit='soldier'), '#e0583f', 'angry', 'shrug'),
      ('Nông dân', "outfit='farmer'", dict(outfit='farmer'), '#8a5cd6', 'happy', 'wave'),
      ('Khoác – đi', 'coat, walk', dict(coat=True), '#4a86e0', 'neutral', 'walk'),
      ('Bếp – chạy', 'chef, run', dict(outfit='chef'), '#f2b234', 'scared', 'run'),
      ('Đồng phục – đi', 'uniform, walk', dict(uniform=True), '#3fae6a', 'neutral', 'walk')]
grid('Stickman – trang phục', [(draw(e, p, c, **kw), lab, sub) for lab, sub, kw, c, e, p in oc], f'{OUT}/stick_outfits.png', 7)
print('wardrobe ok')
