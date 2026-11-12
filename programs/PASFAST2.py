from ti_draw import *
from time import monotonic

# Set True to time only the math and planning (no drawing calls)
COMPUTE_ONLY = False


def hue_to_rgb(h):
    # h in [0, 1); full saturation and brightness; returns 0-255 ints
    h6 = h * 6
    k = int(h6)
    f = h6 - k
    up = int(255 * f)
    down = 255 - up
    return [(255, up, 0), (down, 255, 0), (0, 255, up),
            (0, down, 255), (up, 0, 255), (255, 0, down)][k % 6]


def plan(v, lo, hi, key, base, cb, out):
    # Plans the boxes for entries lo..hi-1 of one row (v, a bytes object).
    # The first color gets ONE box from its first to its last entry in
    # the span. Whatever lies between its entries is planned the same
    # way one layer deeper, and is painted over that box later. Then the
    # rest of the span, after the box, is planned on the same layer.
    #   key:  layer * N, so key + color names a (layer, color) group
    #   base: the row's y and left edge, packed as (y << 18) | (x0 << 9)
    #   cb:   one-byte bytes object per color, for the native find()
    #   out:  dict of group -> list of boxes packed as base + (lo << 9) + width
    N = len(cb)
    while lo < hi:
        b = v[lo]
        bb = cb[b]
        i = lo + 1
        while True:
            while i < hi and v[i] == b:
                i += 1
            if i >= hi:
                break
            k = v.find(bb, i, hi)      # native search for the color's next entry
            if k < 0:
                break
            plan(v, i, k, key + N, base, cb, out)
            i = k + 1
        p = base + (lo << 9) + i - lo
        g = key + b
        if g in out:
            out[g].append(p)
        else:
            out[g] = [p]
        lo = i


def main():
    # Locals are much faster than globals in MicroPython
    N = 16      # must be a power of 2, up to 128
    W = 320
    H = 210
    t0 = monotonic()

    # Each drawing call costs about 6 ms, so make as few as possible:
    # paint long boxes first and shorter ones on top of them.
    # The whole row lives in one big integer, one byte per entry, so
    # native integer math makes each next row in three operations.
    cb = [bytes([c]) for c in range(N)]
    out = {}
    R = 1
    mask = N - 1
    for y in range(H):
        n = y + 1
        plan(R.to_bytes(n, 'little'), 0, n, 0,
             (y << 18) | (((W - n) // 2) << 9), cb, out)
        mask = (mask << 8) | (N - 1)
        R = (R + (R << 8)) & mask

    if not COMPUTE_ONLY:
        clear()
        fr = fill_rect
        # Color changes cost about 4 ms, so each (layer, color) group is
        # drawn in one go, lower layers first.
        # Evo fill_rect fills only the inside of the box, and sizes
        # below 2 raise, so every box is padded by one pixel per side.
        for g in sorted(out):
            set_color(*hue_to_rgb((g % N) / N))
            for p in out[g]:
                fr(((p >> 9) & 511) - 1, (p >> 18) - 1, (p & 511) + 1, 2)

    elapsed = monotonic() - t0
    set_color(0, 0, 0)
    # Text sits in rows y-17..y-3; the top-left corner is empty
    draw_text(4, 20, "Time: %.2f s" % elapsed)
    show_draw()


main()
