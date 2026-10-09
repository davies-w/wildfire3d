"""Crop a region of an image and upscale it, for reading detail in a render.

    python3 crop_zoom.py <in.png> <out.png> x0 y0 x1 y1 [scale]
"""
import sys
from PIL import Image

src, dst = sys.argv[1], sys.argv[2]
x0, y0, x1, y1 = (int(v) for v in sys.argv[3:7])
scale = int(sys.argv[7]) if len(sys.argv) > 7 else 3
im = Image.open(src).crop((x0, y0, x1, y1))
im = im.resize((im.width * scale, im.height * scale), Image.NEAREST)
im.save(dst)
print("%s -> %s  %dx%d" % (src, dst, im.width, im.height))
