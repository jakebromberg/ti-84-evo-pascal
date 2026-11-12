from ti_draw import *
from time import monotonic
import gc
import ti_graphics as gr

# Where does PASFAST5's time go? This is PASFAST5 with a timer around
# each phase: planning, the line self-test, the base triangle, the boxes
# (with the color changes counted separately) and the lines. It also
# reports the free memory before and after planning.
#
# The report is drawn as a block of black pixels (7 bits per character,
# 45 characters per pixel row, from x = 2, y = 0) and decoded from a
# screenshot on the computer.

OY = 30     # screen row of the drawing area's first row


# --- PASFAST5's functions, copied without their comments ---

def hue_to_rgb(h):
    h6 = h * 6
    k = int(h6)
    f = h6 - k
    up = int(255 * f)
    down = 255 - up
    return [(255, up, 0), (down, 255, 0), (0, 255, up),
            (0, down, 255), (up, 0, 255), (255, 0, down)][k % 6]


def plan(v, lo, hi, key, base, cb, out):
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
        v = R.to_bytes(n, 'little')
        x0 = (W - n) // 2
        k = v.find(z, 1)
        while k >= 0:
            a = k
            k += 1
            while not v[k]:
                k += 1
            if p[a] and k - a > 2:
                ln = k - a + 1
                if ln > H - y:
                    ln = H - y
                if ln > 1:
                    sh = (W - n - ln + 1) // 2 - x0
                    key = (ln << 2) | (y & 1)
                    pk = ((y + OY) << 22) | (ln - 1)
                    if a > 1 and (key | 2) not in bad:
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


# --- the probe ---

def phases(out):
    N = 16
    W = 320
    H = 210
    m0 = gc.mem_free()
    t0 = monotonic()
    o, sides, shapes = plan_all(N, W, H, OY, set())
    t1 = monotonic()
    out.append("M free at start %d, after planning %d" % (m0, gc.mem_free()))
    ok = sum([line_ok(shapes[k], W, OY) for k in shapes])
    t2 = monotonic()
    clear()
    fr = gr.fillRect
    sc = gr.setColor
    del o[1]
    draw_base(W, H, OY, hue_to_rgb(1 / N))
    t3 = monotonic()
    nb = 0
    nc = 0
    tc = 0.0
    for g in sorted(o):
        ta = monotonic()
        sc(hue_to_rgb((g % N) / N))
        tc += monotonic() - ta
        nc += 1
        for p in o[g]:
            fr((p >> 9) & 511, p >> 18, p & 511, 1)
        nb += len(o[g])
    t4 = monotonic()
    dl = gr.drawLine
    nl = 0
    for c in sides:
        sc(hue_to_rgb(c / N))
        for p in sides[c]:
            y = p >> 22
            dl((p >> 13) & 511, y, (p >> 4) & 511, y + (p & 15))
        nl += len(sides[c])
    t5 = monotonic()
    out.append("P plan %.2f selftest %.2f (%d/%d ok) base %.2f boxes %.2f (%d; "
               "%d color changes %.2f) lines %.2f (%d in %d colors) total %.2f" % (
                   t1 - t0, t2 - t1, ok, len(shapes), t3 - t2, t4 - t3, nb, nc, tc,
                   t5 - t4, nl, len(sides), t5 - t0))


def draw_bits(text, limit):
    # 4-digit length, the text, then one all-ones character as an end mark
    text = text[:limit]
    text = "%04d" % len(text) + text + "\x7f"
    fr = gr.fillRect
    gr.setColor((0, 0, 0))
    per_row = 45
    y = OY
    for start in range(0, len(text), per_row):
        x = 2
        run = -1                # x where the current run of 1 bits began
        for ch in text[start:start + per_row]:
            v = ord(ch) & 127
            for bit in (64, 32, 16, 8, 4, 2, 1):
                if v & bit:
                    if run < 0:
                        run = x
                elif run >= 0:
                    fr(run, y, x - run, 1)
                    run = -1
                x += 1
        if run >= 0:
            fr(run, y, x - run, 1)
        y += 1


def main():
    out = []
    phases(out)
    clear()
    draw_bits("\n".join(out), 7500)
    set_color(0, 0, 0)
    draw_text(4, 206, "Done")
    show_draw()


main()
