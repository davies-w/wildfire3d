"""Pull one frame out of an animated GIF, to check what is really in the file.

Reading a .gif directly shows only the first frame, so a specific frame has to
be extracted before it can be looked at or sampled.

    python3 gif_frame.py <in.gif> <index> <out.png>
"""
import sys
from PIL import Image, ImageSequence

gif, idx, out = sys.argv[1], int(sys.argv[2]), sys.argv[3]
frames = list(ImageSequence.Iterator(Image.open(gif)))
frames[idx].convert("RGB").save(out)
print("%s: %d frames, took %d -> %s" % (gif, len(frames), idx, out))
