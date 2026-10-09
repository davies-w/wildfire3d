"""Where are the firebrands?  Parse the .prt5 particle file.

Format from the FDS source (dump.f90: header at line 1393, records in
SUBROUTINE DUMP_PART).  Fortran unformatted records, each with a 4-byte length
marker before and after:

  header  int 1 (endian) / int version / int n_classes /
          [n_quantities, 0] / per quantity: 30-char label, 30-char units
  step    float time / int count /
          3*count floats (X block, then Y, then Z) /
          count ints (tags) / count*n_quantities floats

This answers why only floor-level embers are visible: the Z block gives the
distribution of firebrand heights at each output time.
"""
import os, struct, sys

_d = os.path.dirname(os.path.abspath(__file__))
while not os.path.isfile(os.path.join(_d, "paths.py")):
    _d = os.path.dirname(_d)
sys.path.insert(0, _d)
from paths import FDS_ROOT  # noqa: E402

CASE = os.path.join(FDS_ROOT, "cases/wick3")
# Default to experiment 07's run; pass any .prt5 path to compare, e.g.
#   read_embers.py ../../FDS/cases/garden_loft/garden_loft_1.prt5
PRT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(CASE, "wick3c_1.prt5")


def records(buf, off):
    """Yield (payload, next_offset) for each Fortran record from `off`."""
    while off + 8 <= len(buf):
        (n,) = struct.unpack_from("<i", buf, off)
        payload = buf[off + 4: off + 4 + n]
        (m,) = struct.unpack_from("<i", buf, off + 4 + n)
        if n != m or n < 0:
            raise ValueError("record markers disagree at %d" % off)
        off += 8 + n
        yield payload, off


def header(buf):
    """(n_quantities, offset just past the header)."""
    it = records(buf, 0)
    for _ in range(3):                 # endian, version, n_classes
        _, off = next(it)
    payload, off = next(it)            # [n_quantities, 0]
    nq = struct.unpack("<i", payload[:4])[0]
    for _ in range(nq):                # label, units
        _, off = next(it)
        _, off = next(it)
    return nq, off


if __name__ == "__main__":
    buf = open(PRT, "rb").read()
    nq, start = header(buf)
    print("%s\n  %d bytes, %d quantities, data starts at byte %d"
          % (PRT, len(buf), nq, start))

    print("\n%-7s %-7s %-20s %-10s %s"
          % ("t", "n", "z range (m)", "z mean", "above 2 m"))
    it = records(buf, start)
    step = 0
    while True:
        try:
            payload, _ = next(it)
        except StopIteration:
            break
        if len(payload) != 4:
            print("unexpected record length %d after %d steps" % (len(payload), step))
            break
        (t,) = struct.unpack("<f", payload)
        payload, _ = next(it)
        (n,) = struct.unpack("<i", payload)
        xyz, _ = next(it)
        next(it)
        for _ in range(nq):
            next(it)
        if not n:
            continue
        vals = struct.unpack("<%df" % (3 * n), xyz)
        z = vals[2 * n: 3 * n]
        hi = sum(1 for v in z if v > 2.0)
        if step % 12 == 0 or step == 0:
            print("%-7.1f %-7d %-20s %-10.2f %d"
                  % (t, n, "%.2f .. %.2f" % (min(z), max(z)), sum(z) / n, hi))
        step += 1

    print("\n%d output steps" % step)
