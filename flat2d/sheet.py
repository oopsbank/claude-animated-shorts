"""Contact sheet of the 540x960 review downscales: sheet.py DIR -> DIR/sheet.png"""
import sys
from PIL import Image
d = sys.argv[1]; names = ('s01', 's05', 's11', 's15')
ims = [Image.open(f'{d}/{n}_540.png') for n in names]
s = Image.new('RGB', (540 * len(ims), 960)); [s.paste(im, (540 * i, 0)) for i, im in enumerate(ims)]
s.save(f'{d}/sheet.png')
