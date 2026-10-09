"""Pull one frame out of an animated GIF, to check what is really in the file.

Reading a .gif directly shows only the first frame, so a specific frame has to
be extracted before it can be looked at or sampled.

Note: this must seek and copy.  ImageSequence.Iterator yields one Image object
that is re-decoded in place, so collecting it into a list leaves you with N
references to whichever frame was decoded last -- every frame then looks like
the final one.

    python3 gif_frame.py <in.gif> <index> <out.png>
"""
import sys
from PIL import Image


def read_frames(path):
    im = Image.open(path)
    frames = []
    for i in range(getattr(im, "n_frames", 1)):
        im.seek(i)
        frames.append(im.convert("RGB").copy())
    return frames


if __name__ == "__main__":
    if len(sys.argv) < 4:
        sys.exit("usage: gif_frame.py <in.gif> <index> <out.png>")
    frames = read_frames(sys.argv[1])
    idx = int(sys.argv[2])
    if not 0 <= idx < len(frames):
        sys.exit("%s has %d frames (0-%d), asked for %d"
                 % (sys.argv[1], len(frames), len(frames) - 1, idx))
    frames[idx].save(sys.argv[3])
    print("%s: %d frames, took %d -> %s"
          % (sys.argv[1], len(frames), idx, sys.argv[3]))
