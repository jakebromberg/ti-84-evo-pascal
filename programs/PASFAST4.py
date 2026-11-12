from ti_draw import *
from time import monotonic
import ti_graphics as gr

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
    #   base: the row's screen y and left edge, packed as (y << 18) | (x0 << 9)
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


def draw_base(W, H, OY, color):
    # Paints the whole triangle in one color with two polygons instead of
    # one box per row. Row y must cover x0 .. x0 + y, x0 = (W - y - 1) // 2.
    #
    # fillPolygon's edges do not land exactly on that staircase. Measured
    # on the calculator (TRIPROBE) for W = 320, H = 210: the first polygon
    # below gets every right end exactly but leaves the leftmost pixel
    # unpainted on 41 rows; the second has an exact left edge on every row
    # but the last. Together they should be exact, but that rests on one
    # set of measurements, so every row's ends are then read back with
    # getPixel (0.05 ms each) and anything wrong is repaired.
    gp = gr.getPixel
    fr = gr.fillRect
    top = (W - 1) // 2
    left = (W - H) // 2
    gr.setColor(color)
    gr.fillPolygon([(top, OY), (left - 1, OY + H), (left + H - 1, OY + H)])
    gr.fillPolygon([(top, OY), (left - 1, OY + H - 1), (top, OY + H - 1)])
    spill = []
    for y in range(H):
        sy = y + OY
        a = (W - y - 1) // 2
        b = a + y
        # Unpainted pixels at either end of the row
        x = a
        while x <= b and min(gp(x, sy)) > 200:
            x += 1
        if x > a:
            fr(a, sy, x - a, 1)
        if x <= b:
            x = b
            while min(gp(x, sy)) > 200:
                x -= 1
            if x < b:
                fr(x + 1, sy, b - x, 1)
        # Painted pixels outside the row
        x = a - 1
        while x >= 0 and min(gp(x, sy)) <= 200:
            x -= 1
        if x < a - 1:
            spill.append((x + 1, sy, a - 1 - x))
        x = b + 1
        while x < W and min(gp(x, sy)) <= 200:
            x += 1
        if x > b + 1:
            spill.append((b + 1, sy, x - b - 1))
    if spill:
        gr.setColor((255, 255, 255))
        for x, sy, w in spill:
            fr(x, sy, w, 1)


def main():
    # Locals are much faster than globals in MicroPython
    N = 16      # must be a power of 2, up to 128
    W = 320
    H = 210
    OY = 30     # the drawing area starts 30 rows down the screen
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
             ((y + OY) << 18) | (((W - n) // 2) << 9), cb, out)
        mask = (mask << 8) | (N - 1)
        R = (R + (R << 8)) & mask

    if not COMPUTE_ONLY:
        clear()
        # ti_draw is a Python wrapper around the native ti_graphics
        # module. Calling the native fillRect directly saves about 0.8 ms
        # per box. It takes full-screen coordinates and fills exactly
        # w by h pixels. (It is undocumented; PASFAST2 is the same
        # program using only documented calls.)
        fr = gr.fillRect
        sc = gr.setColor
        # Layer 0 is one full-width box per row, all in color 1 because
        # every row starts and ends with 1: together, one big triangle.
        # Two polygons paint it instead of H boxes.
        del out[1]
        draw_base(W, H, OY, hue_to_rgb(1 / N))
        # Color changes cost about 4 ms, so each (layer, color) group is
        # drawn in one go, lower layers first.
        for g in sorted(out):
            sc(hue_to_rgb((g % N) / N))
            for p in out[g]:
                fr((p >> 9) & 511, p >> 18, p & 511, 1)

    elapsed = monotonic() - t0
    set_color(0, 0, 0)
    # Text sits in rows y-17..y-3; the top-left corner is empty
    draw_text(4, 20, "Time: %.2f s" % elapsed)
    show_draw()


main()
