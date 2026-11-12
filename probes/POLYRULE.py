from ti_draw import *
from time import monotonic
from math import sin, cos
import ti_graphics as gr

# How does ti_graphics.fillPolygon really behave, and can one call do the
# work of many boxes? PASFAST4 still makes about 8,900 fillRect calls at
# 5.5 ms each, so these answers decide what a faster version can look like.
#
#   V  time against the number of corners, up to the limit
#   S  time against size, with a 4-corner box and fillRect for comparison
#   C  "combs": several separate runs of one row drawn as a single polygon,
#      joined by a spine along the top (CA), along the bottom (CB), and
#      with teeth 3 rows tall (CC)
#   B  two separate boxes joined by a path that goes out and comes back
#   O  a path that overlaps itself: is the overlap filled or left empty?
#   G  two ordinary triangles, every painted row listed, to work out the
#      rule for which edge pixels are painted
#   U  the whole-picture triangle: which rows have an end pixel wrong
#   T  every complete zero triangle in the picture (3, 7 and 15 wide),
#      drawn where it really sits with 8 choices of corners, each checked
#      pixel by pixel
#
# Nothing is drawn below the bottom of the screen.
#
# The report is drawn as a block of black pixels (7 bits per character,
# 45 characters per pixel row, from x = 2, y = 0) and decoded from a
# screenshot on the computer.

OY = 30     # screen row of the drawing area's first row
RED = (255, 0, 0)
gp = gr.getPixel
fp = gr.fillPolygon


def runs(x1, y1, x2, y2):
    # The painted pixels of screen rows y1..y2 between x1 and x2, as
    # "x1,y1:" then one entry per row. A row lists its runs as first-last
    # (counted from x1), separated by commas; rows are separated by "/".
    out = []
    for y in range(y1, y2 + 1):
        r = []
        s = -1
        for x in range(x1, x2 + 2):
            if x <= x2 and min(gp(x, y)) < 200:
                if s < 0:
                    s = x
            elif s >= 0:
                if x - 1 == s:
                    r.append(str(s - x1))
                else:
                    r.append("%d-%d" % (s - x1, x - 1 - x1))
                s = -1
        out.append(",".join(r))
    return "%d,%d:" % (x1, y1) + "/".join(out)


def ms(pts, reps):
    try:
        t0 = monotonic()
        for i in range(reps):
            fp(pts)
        return "%.1f" % ((monotonic() - t0) * 1000 / reps)
    except Exception as e:
        return "ERR " + str(e)[:48]


def fresh():
    clear()
    gr.setColor(RED)


def comb(spine, tip, teeth):
    # One polygon for several runs: along the spine row, with a tooth
    # reaching the tip row for each (first x, last x) run.
    pts = []
    for s, e in teeth:
        pts.append((s, spine))
        pts.append((s, tip))
        if e != s:
            pts.append((e, tip))
        pts.append((e, spine))
    return pts


def ends(y, left, right):
    # How far the painted ends of screen row y are from left and right
    dl = "x"
    for x in range(left - 4, left + 5):
        if min(gp(x, y)) < 200:
            dl = x - left
            break
    dr = "x"
    for x in range(right + 4, right - 5, -1):
        if min(gp(x, y)) < 200:
            dr = x - right
            break
    return dl, dr


def whole(pts):
    # Rows of the whole-picture triangle whose ends are not where they
    # should be, as row:left error,right error
    fresh()
    fp(pts)
    bad = []
    for y in range(210):
        x0 = (319 - y) // 2
        dl, dr = ends(y + OY, x0, x0 + y)
        if dl != 0 or dr != 0:
            bad.append("%d:%s,%s" % (y, dl, dr))
    return " ".join(bad)


def tops():
    # (row, first entry, width) of every complete zero triangle
    found = []
    prev = [1]
    for n in range(1, 210):
        row = [1] + [(prev[k - 1] + prev[k]) & 15 for k in range(1, n)] + [1]
        k = 1
        while k < n:
            if row[k] == 0 and prev[k] != 0:
                a = k
                while row[k] == 0:
                    k += 1
                if k - a > 1 and n + k - a <= 210:
                    found.append((n, a, k - a))
            else:
                k += 1
        prev = row
    return found


def corners(c, L, R, y, xm, yt):
    if c == 0:      # the exact corners; the tip row is expected to be missed
        return [(L, y), (R, y), (xm, yt)]
    if c == 1:      # the same with a tail one row down and back
        return [(L, y), (R, y), (xm, yt), (xm, yt + 1), (xm, yt)]
    if c == 2:
        return [(L, y), (R, y), (xm, yt), (xm, yt + 1)]
    if c == 3:
        return [(L, y), (R, y), (xm, yt), (xm + 1, yt + 1)]
    if c == 4:
        return [(L, y), (R, y), (xm, yt + 1)]
    if c == 5:
        return [(L, y), (R, y), (xm + 1, yt + 1)]
    if c == 6:
        return [(L, y), (R, y), (xm - 1, yt + 1)]
    return [(L, y), (R + 0.4, y), (xm + 0.2, yt + 0.4)]     # are fractions allowed?


def check(n, a, w, L, R, xm):
    # Pixels of the triangle left unpainted, and pixels painted around it
    miss = 0
    extra = 0
    for t in range(w):
        y = n + t + OY
        lx = (319 - n - t) // 2 + a + t
        rx = lx + w - t - 1
        for x in range(lx, rx + 1):
            if min(gp(x, y)) > 200:
                miss += 1
        if min(gp(lx - 1, y)) < 200:
            extra += 1
        if min(gp(rx + 1, y)) < 200:
            extra += 1
    y = n + OY - 1
    for x in range(L, R + 2):
        if min(gp(x, y)) < 200:
            extra += 1
    y = n + w + OY
    if y < 240:
        if min(gp(xm, y)) < 200:
            extra += 1
        if min(gp(xm + 1, y)) < 200:
            extra += 1
    return miss, extra


def zero_triangles(c, tris):
    fresh()
    res = {}
    for n, a, w in tris:
        y = n + OY
        L = (319 - n) // 2 + a
        R = L + w - 1
        xm = L + w // 2
        yt = y + w - 1
        t0 = monotonic()
        try:
            fp(corners(c, L, R, y, xm, yt))
        except Exception as e:
            return ["T%d ERR %s" % (c, str(e)[:40])]
        dt = monotonic() - t0
        m, e = check(n, a, w, L, R, xm)
        r = res.get(w)
        if r is None:
            r = res[w] = [0, 0, 0, 0, 0.0, ""]
        r[0] += 1
        r[2] += m
        r[3] += e
        r[4] += dt
        if m == 0 and e == 0:
            r[1] += 1
        elif not r[5]:
            r[5] = " " + runs(L - 2, y - 1, R + 2, min(yt + 1, 239))
    return ["T%d w%d ok%d/%d m%d e%d %.1fms%s" % (
        c, w, res[w][1], res[w][0], res[w][2], res[w][3],
        res[w][4] * 1000 / res[w][0], res[w][5]) for w in sorted(res)]


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
    t_start = monotonic()
    out = []

    # V: corners against time. After each, the painted width of the
    # middle row shows whether the shape was filled.
    s = "V"
    for n in (3, 4, 5, 6, 8, 12, 16, 24, 32, 48, 50, 51, 64):
        fresh()
        r = ms([(int(160.5 + 60 * cos(6.2831853 * i / n)),
                 int(135.5 + 60 * sin(6.2831853 * i / n))) for i in range(n)], 3)
        s += " %d:%s" % (n, r)
        if r[0] == "E":
            break
        s += "/%d" % sum([min(gp(x, 135)) < 200 for x in range(95, 226)])
    out.append(s)

    # S: size against time
    fresh()
    s = "S"
    for h in (3, 15, 60, 200):
        s += " %d:%s" % (h, ms([(160 - h // 2, 35), (160 + h // 2, 35), (160, 35 + h)], 6))
    s += " quad:" + ms([(100, 100), (110, 100), (110, 105), (100, 105)], 6)
    t0 = monotonic()
    for i in range(6):
        gr.fillRect(100, 100, 11, 5)
    out.append(s + " rect:%.1f" % ((monotonic() - t0) * 1000 / 6))

    # C: combs
    teeth = ((20, 29), (35, 35), (40, 47), (60, 61))
    fresh()
    out.append("CA " + ms(comb(40, 41, teeth), 1) + " " + runs(18, 39, 63, 42))
    out.append("CB " + ms(comb(51, 50, teeth), 1) + " " + runs(18, 49, 63, 52))
    out.append("CC " + ms(comb(63, 60, teeth), 1) + " " + runs(18, 59, 63, 64))

    # B: two boxes joined by a path out and back
    out.append("B " + ms([(20, 80), (29, 80), (29, 83), (40, 86), (49, 86), (49, 89),
                          (40, 89), (40, 86), (29, 83), (20, 83)], 1) + " " +
               runs(18, 79, 51, 90))

    # O: two squares in one path that overlap each other
    out.append("O " + ms([(20, 100), (30, 100), (30, 110), (20, 110), (20, 100),
                          (25, 105), (35, 105), (35, 115), (25, 115), (25, 105)], 1) + " " +
               runs(18, 99, 37, 116))

    # G: ordinary triangles
    out.append("G1 " + ms([(10, 130), (40, 133), (22, 150)], 1) + " " + runs(8, 129, 42, 151))
    out.append("G2 " + ms([(60, 150), (52, 131), (90, 140)], 1) + " " + runs(50, 130, 92, 151))

    # U: the whole-picture triangle
    out.append("U1 " + whole([(159, OY), (54, OY + 210), (264, OY + 210)]))
    out.append("U2 " + whole([(159, OY), (54, OY + 209), (264, OY + 209)]))

    # T: the zero triangles
    tris = tops()
    for c in range(8):
        out.extend(zero_triangles(c, tris))

    out.append("total %.1f s" % (monotonic() - t_start))
    clear()
    draw_bits("\n".join(out), 7500)
    set_color(0, 0, 0)
    draw_text(4, 206, "Done")
    show_draw()


main()
