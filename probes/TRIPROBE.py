from ti_draw import *
from time import monotonic
import ti_graphics as gr

# Which corner points make ti_graphics.fillPolygon paint exactly the
# pixels of a triangle whose rows grow by one pixel on alternating sides?
# PASFAST3's first pass is 210 full-width boxes forming such a triangle;
# one polygon could replace them if its edges land on the right pixels.
#
# For each choice of corners this draws the polygon, then reads the left
# and right end of every row back with getPixel and counts how far each
# is from where it should be. Two shapes are tried: the whole triangle,
# and a 15-row upside-down triangle like the picture's zero regions.
#
# The report is drawn as a block of black pixels (7 bits per character,
# 45 characters per pixel row, from x = 2, y = 0) and decoded from a
# screenshot on the computer.

OY = 30     # screen row of the drawing area's first row


def ends(y, left, right):
    # How far the painted ends of screen row y are from left and right.
    # "x" means nothing was painted within 4 pixels of that end.
    gp = gr.getPixel
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


def tally(counts, key):
    counts[key] = counts.get(key, 0) + 1


def show(counts):
    return ",".join([str(k) + ":" + str(counts[k]) for k in counts])


def trial(points, rows, extra_rows):
    # Draws the polygon and compares every expected row.
    #   rows: list of (screen y, left x, right x) that should be painted
    #   extra_rows: (screen y, x from, x to) that should stay white
    clear()
    try:
        t0 = monotonic()
        gr.fillPolygon(points)
        ms = (monotonic() - t0) * 1000
    except Exception as e:
        return "ERR " + str(e)[:40]
    lefts = {}
    rights = {}
    good = 0
    for y, left, right in rows:
        dl, dr = ends(y, left, right)
        tally(lefts, dl)
        tally(rights, dr)
        if dl == 0 and dr == 0:
            good += 1
    spill = 0
    for y, x1, x2 in extra_rows:
        if y < 240:
            for x in range(x1, x2 + 1):
                if min(gr.getPixel(x, y)) < 200:
                    spill += 1
    return "%d ms ok=%d/%d L[%s] R[%s] spill=%d" % (
        ms, good, len(rows), show(lefts), show(rights), spill)


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

    # The whole triangle: row y runs from (319 - y) // 2 for y + 1 pixels
    rows = []
    for y in range(210):
        x0 = (319 - y) // 2
        rows.append((y + OY, x0, x0 + y))
    gr.setColor((255, 95, 0))
    for ax in (159, 160):
        for by in (239, 240):
            for lx in (54, 55):
                for rx in (264, 265):
                    out.append("U a%d b%d l%d r%d: " % (ax, by, lx, rx) + trial(
                        [(ax, OY), (lx, by), (rx, by)], rows, ()))

    # An upside-down triangle: the zero region that starts at row 128,
    # entries 1 to 15, and loses its leftmost entry on each later row
    rows = []
    for t in range(15):
        x0 = (319 - (128 + t)) // 2
        rows.append((128 + t + OY, x0 + 1 + t, x0 + 15))
    top = 128 + OY          # 158: 15 pixels, x 96 to 110
    tip = 142 + OY          # 172: 1 pixel, x 103
    gr.setColor((255, 0, 0))
    for ty in (top - 1, top):
        for py in (tip, tip + 1):
            for lx in (95, 96):
                for rx in (110, 111):
                    out.append("D t%d p%d l%d r%d: " % (ty, py, lx, rx) + trial(
                        [(lx, ty), (rx, ty), (103, py)], rows,
                        ((top - 1, 90, 116), (tip + 1, 90, 116))))

    clear()
    draw_bits("\n".join(out), 6500)
    set_color(0, 0, 0)
    draw_text(4, 206, "Done")
    show_draw()


main()
