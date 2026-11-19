# usage: python3 scripts/sheet.py out.jpg cols img1 img2 ...  (labels each tile with its frame number)
import sys
from PIL import Image, ImageDraw
out, cols, files = sys.argv[1], int(sys.argv[2]), sys.argv[3:]
ims = [Image.open(f).convert("RGB") for f in files]
w, h = 270, 480
ims = [i.resize((w, h)) for i in ims]
rows = (len(ims) + cols - 1) // cols
S = Image.new("RGB", (cols * w, rows * h), "white")
for k, (im, f) in enumerate(zip(ims, files)):
    S.paste(im, ((k % cols) * w, (k // cols) * h))
    d = ImageDraw.Draw(S); d.rectangle([(k % cols) * w, (k // cols) * h, (k % cols) * w + 60, (k // cols) * h + 18], fill="black")
    d.text(((k % cols) * w + 3, (k // cols) * h + 3), f.split("_")[-1].split(".")[0], fill="white")
S.save(out, quality=88)
