from ti_draw import *
from time import monotonic
import gc
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


def plan_all(N, W, H, OY, bad):
    # Plans the whole picture. Returns
    #   out:    (layer, color) group -> boxes, as plan() packs them
    #   sides:  color -> lines, packed (y1 << 22) | (x1 << 13) | (x2 << 4) | (rows - 1)
    #   shapes: line shape -> the first line of that shape, for line_ok()
    #
    # Every block of zeros in the picture is an upside-down triangle, and
    # the entries along its two slanted sides all have one value: each is
    # the entry above it plus a zero. Such a side is a straight line on
    # screen, so one drawLine call can paint all of it, last, on top of
    # the boxes. The boxes then need not get those entries right, which
    # lets the boxes on either side of them join up: here the row is
    # planned as if each such entry had the color of the entry before it.
    #   bad: line shapes that line_ok() found drawLine does not paint
    #        exactly; sides of those shapes are left to the boxes
    cb = [bytes([c]) for c in range(N)]
    z = cb[0]
    out = {}
    sides = {}
    shapes = {}
    wild = [[] for y in range(H)]
    R = 1
    mask = N - 1
    p = z
    for y in range(H):
        n = y + 1
        if not y & 15:
            # The plan nearly fills the calculator's memory. Clearing out
            # the dead rows regularly keeps the free space in one piece,
            # so a growing list can always find room.
            gc.collect()
        v = R.to_bytes(n, 'little')
        x0 = (W - n) // 2
        k = v.find(z, 1)
        while k >= 0:
            a = k
            k += 1
            while not v[k]:
                k += 1
            # Only a triangle's top row has a non-zero entry above its
            # first zero. Its sides run w + 1 rows, or to the last row.
            if p[a] and k - a > 2:
                ln = k - a + 1
                if ln > H - y:
                    ln = H - y
                if ln > 1:
                    # how far the row's left edge moves over those rows
                    sh = (W - n - ln + 1) // 2 - x0
                    key = (ln << 2) | (y & 1)
                    pk = ((y + OY) << 22) | (ln - 1)
                    if a > 1 and (key | 2) not in bad:
                        # left side: one entry further right on each row
                        x = x0 + a - 1
                        q = pk | (x << 13) | ((x + sh + ln - 1) << 4)
                        c = v[a - 1]
                        if c in sides:
                            sides[c].append(q)
                        else:
                            sides[c] = [q]
                        if (key | 2) not in shapes:
                            shapes[key | 2] = q
                        for t in range(ln):
                            wild[y + t].append(a - 1 + t)
                    if k < y and key not in bad:
                        # right side: the same entry on each row
                        x = x0 + k
                        q = pk | (x << 13) | ((x + sh) << 4)
                        c = v[k]
                        if c in sides:
                            sides[c].append(q)
                        else:
                            sides[c] = [q]
                        if key not in shapes:
                            shapes[key] = q
                        for t in range(ln):
                            wild[y + t].append(k)
            k = v.find(z, k)
        p = v
        wl = wild[y]
        wild[y] = None      # not needed again; frees it
        if wl:
            wl.sort()
            ba = bytearray(v)
            for k in wl:
                ba[k] = ba[k - 1]
            v = bytes(ba)
        plan(v, 0, n, 0, ((y + OY) << 18) | (x0 << 9), cb, out)
        mask = (mask << 8) | (N - 1)
        R = (R + (R << 8)) & mask
    return out, sides, shapes


def line_ok(q, W, OY):
    # Draws one planned line on an empty screen and checks that each of
    # its rows has exactly the right pixel painted and no neighbor.
    gp = gr.getPixel
    y1 = q >> 22
    x1 = (q >> 13) & 511
    x2 = (q >> 4) & 511
    ln = (q & 15) + 1
    clear()
    gr.setColor((0, 0, 0))
    gr.drawLine(x1, y1, x2, y1 + ln - 1)
    r = y1 - OY
    for t in range(ln):
        x = x1 + (W - 1 - r - t) // 2 - (W - 1 - r) // 2
        if x2 > x1:
            x += t
        if (min(gp(x, y1 + t)) > 200 or min(gp(x - 1, y1 + t)) < 200
                or min(gp(x + 1, y1 + t)) < 200):
            return False
    return True


def main():
    # Locals are much faster than globals in MicroPython
    N = 16      # must be a power of 2, up to 128
    W = 320
    H = 210
    OY = 30     # the drawing area starts 30 rows down the screen
    t0 = monotonic()

    # Each drawing call costs about 6 ms, so make as few as possible:
    # paint long boxes first and shorter ones on top of them, then the
    # sides of the zero triangles as lines.
    # The whole row lives in one big integer, one byte per entry, so
    # native integer math makes each next row in three operations.
    #
    # drawLine is undocumented, so before the lines are relied on, one
    # line of each shape is drawn and read back. If a shape comes out
    # wrong the picture is planned again without it.
    bad = set()
    while True:
        out, sides, shapes = plan_all(N, W, H, OY, bad)
        if COMPUTE_ONLY:
            break
        off = [k for k in shapes if not line_ok(shapes[k], W, OY)]
        if not off:
            break
        bad.update(off)
        # there is not room for two plans at once
        out = sides = shapes = None

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
        dl = gr.drawLine
        for c in sides:
            sc(hue_to_rgb(c / N))
            for p in sides[c]:
                y = p >> 22
                dl((p >> 13) & 511, y, (p >> 4) & 511, y + (p & 15))

    elapsed = monotonic() - t0
    set_color(0, 0, 0)
    # Text sits in rows y-17..y-3; the top-left corner is empty
    draw_text(4, 20, "Time: %.2f s" % elapsed)
    if bad:
        # line shapes that drawLine got wrong and the boxes covered for
        draw_text(4, 38, "%d off" % len(bad))
    show_draw()


main()
