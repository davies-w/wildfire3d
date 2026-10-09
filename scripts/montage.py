"""Tile several images into one grid, so a sweep can be compared at a glance.

    python3 montage.py <out.png> <cols> <in1.png> <in2.png> ...
"""
import sys
from PIL import Image, ImageDraw

out, cols = sys.argv[1], int(sys.argv[2])
paths = sys.argv[3:]
ims = [Image.open(p).convert("RGB") for p in paths]
w = max(i.width for i in ims)
h = max(i.height for i in ims)
rows = (len(ims) + cols - 1) // cols
sheet = Image.new("RGB", (cols * w, rows * (h + 14)), (255, 255, 255))
d = ImageDraw.Draw(sheet)
for k, (p, im) in enumerate(zip(paths, ims)):
    x, y = (k % cols) * w, (k // cols) * (h + 14)
    sheet.paste(im, (x, y))
    d.text((x + 4, y + h + 1), p.split("/")[-1][:-4], fill=(0, 0, 0))
sheet.save(out)
print("%s  %dx%d  %d tiles" % (out, sheet.width, sheet.height, len(ims)))
