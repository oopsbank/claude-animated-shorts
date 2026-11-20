# Riding preview sheet: bicycle, motorbike and nobs bike in side / 3q / rear / front / top, with steer and lean.
# usage: ride_sheet.py <out.png>
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from bikes import ride, draw_bike
from PIL import Image, ImageDraw, ImageFont
YOU = dict(build='adult', skin='#f6d2b0', shirt='#3fb37f', pants='#2f3f6b', hat='beanie', hat_col='#f2c230', seed=11)
DALE = dict(build='stout', skin='#ffe2c2', shirt='#d9452f', pants='#30343f', hat='helmet', hat_col='#f4f1e8',
            moustache='#6b4426', outfit=(('stripes', '#f1efe6'),), seed=4)
R = '#d9452f'; ST = 'I STEER WITH MY HIPS'
CELLS = [
    ('Xe đạp – nghiêng', lambda: ride(YOU, 'bicycle', 'side', crank=60, expr='smile')),
    ('Xe đạp – 3/4, lái 20°', lambda: ride(YOU, 'bicycle', '3q', steer=20, expr='neutral')),
    ('Xe đạp – sau, nghiêng trái', lambda: ride(YOU, 'bicycle', 'rear', steer=12, lean=-18)),
    ('Xe đạp – trước', lambda: ride(YOU, 'bicycle', 'front', expr='grin')),
    ('Xe đạp – từ trên, lái phải', lambda: ride(YOU, 'bicycle', 'top', steer=22)),
    ('Mô tô – nghiêng', lambda: ride(DALE, 'motorbike', 'side', color=R, expr='smug')),
    ('Mô tô – 3/4, lái trái', lambda: ride(DALE, 'motorbike', '3q', steer=-32, color=R, expr='grin')),
    ('Mô tô – sau, ôm cua trái', lambda: ride(DALE, 'motorbike', 'rear', steer=8, lean=-24, color=R, sticker=ST)),
    ('Mô tô – trước', lambda: ride(DALE, 'motorbike', 'front', color=R, expr='neutral')),
    ('Mô tô – từ trên', lambda: ride(DALE, 'motorbike', 'top', steer=-15, color=R)),
    ('Xe ghi đông cố định', lambda: ride(DALE, 'nobs_bike', 'side', hold='fixed', color=R, expr='smug')),
    ('Nghiêng người, xe đứng', lambda: ride(DALE, 'nobs_bike', 'rear', hold='fixed', body_lean=-28, bike_lean=3, knee_out=True, color=R, sticker=ST, expr='smug')),
    ('Cố định – trước', lambda: ride(DALE, 'nobs_bike', 'front', hold='fixed', color=R, expr='nervous')),
    ('Cố định – 3/4', lambda: ride(DALE, 'nobs_bike', '3q', hold='fixed', color=R, expr='pained')),
    ('Chỉ xe – nghiêng', lambda: draw_bike('nobs_bike', 'side', color=R)),
    ('Lái phải, đổ trái', lambda: ride(DALE, 'motorbike', 'front', steer=22, lean=-14, color=R, expr='shock')),
]
F = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 26)
cw, cols = 440, 5; rows = (len(CELLS) + cols - 1) // cols
sheet = Image.new('RGBA', (cw * cols, (cw + 50) * rows), (240, 237, 230, 255)); d = ImageDraw.Draw(sheet)
for i, (lab, fn) in enumerate(CELLS):
    r, c = divmod(i, cols); im = fn().resize((cw, cw), Image.LANCZOS)
    sheet.alpha_composite(im, (c * cw, r * (cw + 50) + 44))
    w = d.textlength(lab, font=F); d.text((c * cw + (cw - w) / 2, r * (cw + 50) + 8), lab, font=F, fill=(30, 30, 40))
sheet.save(sys.argv[1])
