from ti_draw import *
from time import monotonic
import gc
import ti_graphics as gr

# Is there a cheaper way to paint the 3,557 single pixels that make up
# more than half of PASFAST5's boxes?
#
#   R  fillRect: is a 1-pixel box cheaper than a 300-pixel one?
#   F  each font: its timing, where its dots land, whether text takes
#      the pen color and leaves its surroundings alone, and every
#      character that paints 4 pixels or fewer or a single run of
#      pixels on one row. A character that paints one pixel would be
#      a cheaper single pixel than a box (4.5 ms against 5.5 ms).
#   N  the pen: which setPen arguments are accepted, and for each
#      distinct result what lines, boxes and polylines look like. A
#      dotted line could paint every other pixel of a row in one call.
#
# The font and the pen are put back as they were found.
#
# The report is drawn as a block of black pixels (7 bits per character,
# 45 characters per pixel row, from x = 2, y = 0) and decoded from a
# screenshot on the computer.

OY = 30     # screen row of the drawing area's first row
BLACK = (0, 0, 0)
gp = gr.getPixel


def fresh():
    clear()
    gr.setColor(BLACK)


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


def find_box(x1, y1, x2, y2):
    # The smallest box around every painted pixel, or None
    b = None
    for y in range(y1, y2 + 1):
        for x in range(x1, x2 + 1):
            if min(gp(x, y)) < 200:
                if b is None:
                    b = [x, y, x, y]
                else:
                    if x < b[0]:
                        b[0] = x
                    if x > b[2]:
                        b[2] = x
                    b[3] = y
    return b


def rect_cost(out):
    fresh()
    s = "R"
    for w in (1, 2, 10, 300):
        t0 = monotonic()
        for i in range(20):
            gr.fillRect(10, 40 + i, w, 1)
        s += " %dpx %.2f" % (w, (monotonic() - t0) * 50)
    out.append(s)


def font(out, name, f, hi, default_box):
    # Returns True if this font paints the calibration characters where
    # the font in use at the start did.
    AX = 100
    AY = 120
    try:
        gr.setFont(f)
    except Exception as e:
        out.append("F %s ERR %s" % (name, str(e)[:40]))
        return False
    fresh()
    for ch in "Wg|_'@":
        gr.drawString(ch, AX, AY)
    b = find_box(AX - 8, AY - 30, AX + 34, AY + 34)
    if b is None:
        out.append("F %s=%r paints nothing" % (name, f))
        return False
    x1 = b[0] - 1
    y1 = b[1] - 1
    cw = b[2] - b[0] + 3
    ch_ = b[3] - b[1] + 3
    s = "F %s=%r dx %d..%d dy %d..%d" % (name, f, b[0] - AX, b[2] - AX, b[1] - AY, b[3] - AY)
    t0 = monotonic()
    for i in range(10):
        gr.drawString(".", AX, AY)
    t1 = monotonic()
    for i in range(10):
        gr.drawString("..........", AX, AY)
    s += " t1=%.2f t10=%.2f" % ((t1 - t0) * 100, (monotonic() - t1) * 100)
    try:
        s += " size=%r" % (gr.string_size("."),)
    except Exception as e:
        s += " size ERR"
    # where the dots of a string land
    for text in ("....", ". ."):
        fresh()
        gr.drawString(text, AX, AY)
        cols = [x - AX for x in range(AX - 4, AX + 80)
                if sum([min(gp(x, y)) < 200 for y in range(y1, y1 + ch_)])]
        s += " %r cols %s" % (text, ",".join([str(c) for c in cols]))
    # does text take the pen color, and what happens to what is under it?
    gr.setColor((255, 0, 0))
    gr.fillRect(x1, y1, cw, ch_)
    gr.setColor((0, 0, 255))
    gr.drawString("X", AX, AY)
    n = [0, 0, 0, 0]
    other = ""
    for y in range(y1, y1 + ch_):
        for x in range(x1, x1 + cw):
            p = gp(x, y)
            if p[0] > 200 and p[1] < 100 and p[2] < 100:
                n[0] += 1
            elif p[2] > 200 and p[0] < 100 and p[1] < 100:
                n[1] += 1
            elif min(p) > 200:
                n[2] += 1
            else:
                n[3] += 1
                other = " %r" % (p,)
    s += " on red: red %d blue %d white %d other %d%s" % (n[0], n[1], n[2], n[3], other)
    # every character that paints very little
    fresh()
    gx = 2
    gy = OY + 2
    small = []
    blank = 0
    for c in range(32, hi):
        if gx + cw > 318:
            gx = 2
            gy += ch_
            if gy + ch_ > 238:
                fresh()
                gy = OY + 2
        try:
            gr.drawString(chr(c), gx + AX - x1, gy + AY - y1)
        except Exception as e:
            continue
        px = []
        for y in range(gy, gy + ch_):
            for x in range(gx, gx + cw):
                if min(gp(x, y)) < 200:
                    px.append((x - gx + x1 - AX, y - gy + y1 - AY))
        if not px:
            blank += 1
        elif len(px) <= 4:
            small.append("%d[%s]" % (c, " ".join(["%d,%d" % p for p in px])))
        elif px[0][1] == px[-1][1] and px[-1][0] - px[0][0] == len(px) - 1:
            small.append("%d[%d,%d w%d]" % (c, px[0][0], px[0][1], len(px)))
        gx += cw
    out.append(s + " blank %d small: %s" % (blank, " ".join(small)))
    return b == default_box


def pen(out):
    st = [getattr(gr.Style, n, None) for n in ("SMOOTH", "DOTTED", "DASHED")]
    import ti_draw as td
    out.append("N Style SMOOTH=%r DOTTED=%r DASHED=%r ti_draw.set_pen %s" % (
        st[0], st[1], st[2], hasattr(td, "set_pen")))
    fresh()
    gr.drawLine(20, 40, 59, 40)
    ref = runs(18, 36, 61, 44)
    good = {}       # what a line looks like -> the first arguments giving it
    errs = {}
    count = 0
    for t in (0, 1, 2, 3, "thin", "medium", "thick") + tuple(st):
        for s in tuple(st) + (0, 1, 2, "solid", "dotted", "dashed"):
            try:
                gr.setPen(t, s)
            except Exception as e:
                errs[str(e)[:40]] = (t, s)
                continue
            count += 1
            fresh()
            gr.drawLine(20, 40, 59, 40)
            look = runs(18, 36, 61, 44)
            if look not in good:
                good[look] = (t, s)
    out.append("N errors: " + "; ".join(["%r %s" % (errs[m], m) for m in errs])[:400])
    out.append("N accepted %d, distinct looks %d, default %s" % (count, len(good), ref))
    for look in good:
        t, s = good[look]
        line = "N %r/%r %s" % (t, s, look)
        if look.count("/") - look.count("//") * 2 < 3:      # at most 2 painted rows
            fresh()
            gr.setPen(t, s)
            gr.drawLine(21, 40, 60, 40)         # one pixel further right
            gr.drawLine(60, 44, 21, 44)         # drawn right to left
            gr.drawLine(100, 40, 107, 55)       # the picture's two diagonals
            gr.drawLine(120, 40, 113, 55)
            gr.drawLine(140, 40, 140, 60)
            gr.fillRect(150, 40, 10, 3)
            gr.drawPolyLine([(170, 40), (189, 40), (189, 50)])
            t0 = monotonic()
            for i in range(6):
                gr.drawLine(20, 70, 59, 70)
            line += " t=%.1f odd %s rev %s d1 %s d2 %s v %s rect %s poly %s" % (
                (monotonic() - t0) * 1000 / 6, runs(18, 40, 62, 40), runs(18, 44, 62, 44),
                runs(98, 40, 109, 55), runs(111, 40, 122, 55), runs(138, 40, 142, 60),
                runs(148, 39, 161, 43), runs(168, 39, 191, 51))
        out.append(line)
    if ref in good:
        gr.setPen(good[ref][0], good[ref][1])
        fresh()
        gr.drawLine(20, 40, 59, 40)
        out.append("N pen put back with %r: %s" % (good[ref], runs(18, 36, 61, 44) == ref))
    else:
        out.append("N pen NOT put back: nothing accepted looks like the default")


def draw_bits(text, limit):
    # 4-digit length, the text, then one all-ones character as an end mark
    text = text[:limit]
    text = "%04d" % len(text) + text + "\x7f"
    fr = gr.fillRect
    gr.setColor(BLACK)
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
    out = ["M free at start %d" % gc.mem_free()]
    rect_cost(out)

    # the font in use before anything is changed
    fresh()
    for ch in "Wg|_'@":
        gr.drawString(ch, 100, 120)
    default_box = find_box(92, 90, 134, 154)
    back = None
    for name, hi in (("SMALL", 256), ("SMALLD", 256), ("MEDIUM", 256), ("LARGE", 127), ("ICON", 127)):
        f = getattr(gr.Font, name, None)
        if f is not None and font(out, name, f, hi, default_box) and back is None:
            back = (name, f)
    if back:
        gr.setFont(back[1])
    elif getattr(gr.Font, "MEDIUM", None) is not None:
        gr.setFont(gr.Font.MEDIUM)
    out.append("F font at the start: %s" % (back[0] if back else "none of these"))

    pen(out)

    out.append("total %.1f s" % (monotonic() - t_start))
    clear()
    draw_bits("\n".join(out), 7500)
    set_color(0, 0, 0)
    draw_text(4, 206, "Done")
    show_draw()


main()
