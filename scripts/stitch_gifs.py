"""Glue several animated gifs side by side into one, frame by frame.

Pure stitching: no compositing, no labels, no scaling.  Frame n of each input
is pasted left to right to make frame n of the output, so the inputs must have
the same frame count and the same frame size.  That is what a pinned `crop_box`
in the render config buys -- auto-trimming gives each case its own box and the
halves then differ in size and scale.

    python3 stitch_gifs.py <out.gif> <in1.gif> <in2.gif> [...]
"""
import os, sys
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gif_frame import read_frames  # noqa: E402

if len(sys.argv) < 4:
    sys.exit("usage: stitch_gifs.py <out.gif> <in1.gif> <in2.gif> [...]")
out, srcs = sys.argv[1], sys.argv[2:]

seqs = [read_frames(p) for p in srcs]
counts = sorted({len(s) for s in seqs})
sizes = sorted({s[0].size for s in seqs})
if len(counts) != 1:
    sys.exit("frame counts differ: %s" % counts)
if len(sizes) != 1:
    sys.exit("frame sizes differ: %s -- pin the same crop_box in both configs"
             % sizes)
w, h = sizes[0]
print("%d inputs, %d frames, %dx%d each" % (len(srcs), counts[0], w, h))

duration = Image.open(srcs[0]).info.get("duration", 600)
strip = Image.new("RGB", (w * len(srcs), h), (255, 255, 255))
frames = []
for i in range(counts[0]):
    for k, s in enumerate(seqs):
        strip.paste(s[i], (k * w, 0))
    frames.append(strip.copy())

frames[0].save(out, save_all=True, append_images=frames[1:], duration=duration,
               loop=0)
print("%s  %d bytes" % (out, os.path.getsize(out)))
