from ti_draw import *
from time import monotonic
import ti_graphics as gr
import ti_image

# Second probe of the native ti_graphics module. GRPROBE showed that
# gr.fillRect(x, y, w, h) fills exactly w by h pixels in full-screen
# coordinates (the drawing area starts at y = 30) and costs about as much
# as ti_draw.fill_rect. This one checks the calls that could paint many
# runs at once: drawPolyLine, fillPolygon, drawString, pushImage/popImage.
#
# The report is drawn as a block of black pixels (7 bits per character,
# 45 characters per pixel row, from x = 2, y = 0) and decoded from a
# screenshot on the computer.

OY = 30     # screen row of the drawing area's first row


def attempt(fn):
    try:
        return str(fn())
    except Exception as e:
        return "ERR " + str(e)[:80]


def arg_count(fn):
    # Too many arguments: MicroPython reports the right count without
    # running the function. Returns (count or -1, message).
    try:
        fn(1, 2, 3, 4, 5, 6, 7, 8, 9)
        return -1, "ran with 9 args"
    except Exception as e:
        msg = str(e)
        i = msg.find("takes ")
        if i >= 0:
            try:
                return int(msg[i + 6:].split()[0]), msg[:70]
            except Exception:
                pass
        return -1, msg[:70]


def first_ok(tries):
    notes = []
    for label, fn in tries:
        try:
            fn()
            return label, notes
        except Exception as e:
            notes.append(label + ": " + str(e)[:60])
    return None, notes


def timed(count, fn):
    try:
        t0 = monotonic()
        for k in range(count):
            fn()
        return "%.3f ms" % ((monotonic() - t0) * 1000 / count)
    except Exception as e:
        return "ERR " + str(e)[:70]


def comb(x, y, runs):
    # 2-pixel runs on row y, 1 pixel apart, joined through row y + 1
    pts = []
    for r in range(runs):
        a = x + 3 * r
        pts += [(a, y), (a + 1, y), (a + 1, y + 1), (a + 3, y + 1)]
    return pts


def shape_of(pts, form):
    if form == "tuples":
        return pts
    if form == "lists":
        return [list(p) for p in pts]
    flat = []
    for p in pts:
        flat += [p[0], p[1]]
    return flat


def read_box(x, y, w, h):
    # Rows of 0/1: which pixels are not white. getPixel is fast (0.05 ms)
    rows = []
    for py in range(y, y + h):
        s = ""
        for px in range(x, x + w):
            s += "0" if min(gr.getPixel(px, py)) > 200 else "1"
        rows.append(s)
    return "/".join(rows)


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
    clear()

    # Argument counts, learned without running anything
    for name in ("popImage", "cls"):
        out.append(name + ": " + arg_count(getattr(gr, name))[1])
    for name in ("load_image", "show_image", "clear_image", "set_pixel",
                 "get_pixel", "new_image", "copy_image"):
        out.append("ti_image." + name + ": "
                   + arg_count(getattr(ti_image, name))[1])

    # drawPolyLine: argument form, then cost against the number of points
    gr.setColor((255, 0, 0))
    form, notes = first_ok((
        ("tuples", lambda: gr.drawPolyLine([(60, 60), (64, 60), (64, 62)])),
        ("lists", lambda: gr.drawPolyLine([[60, 60], [64, 60], [64, 62]])),
        ("flat", lambda: gr.drawPolyLine([60, 60, 64, 60, 64, 62]))))
    out.append("polyline form: " + str(form) + " " + "; ".join(notes))
    if form:
        for n in (2, 20, 100, 200, 400):
            pts = shape_of(comb(10, 70 + n // 10, n // 4 + 1)[:n], form)
            out.append("polyline %d pts %s" % (
                n, timed(20, lambda: gr.drawPolyLine(pts))))
        # Long straight segments: is the cost per point or per pixel?
        zig = shape_of([(10 + 300 * (i & 1), 150 + i) for i in range(20)],
                       form)
        out.append("polyline 20 pts long " + timed(
            20, lambda: gr.drawPolyLine(zig)))
        # Exactly which pixels a comb path paints
        clear()
        gr.setColor((255, 0, 0))
        out.append("comb draw: " + attempt(lambda: gr.drawPolyLine(
            shape_of(comb(100, 100, 3) + [(112, 100)], form))))
        out.append("comb pixels x98-114 y99-102: " + attempt(
            lambda: read_box(98, 99, 17, 4)))
        # A path that dips below the bottom edge of the screen
        out.append("offscreen: " + attempt(lambda: gr.drawPolyLine(
            shape_of([(100, 239), (102, 239), (102, 240), (106, 240),
                      (106, 239), (108, 239)], form))))
        out.append("offscreen pixels x98-110 y238-239: " + attempt(
            lambda: read_box(98, 238, 13, 2)))

    # fillPolygon with the same argument form
    if form:
        quad = shape_of([(200, 100), (204, 100), (204, 103), (200, 103)],
                        form)
        out.append("fillPolygon 4 pts " + timed(
            50, lambda: gr.fillPolygon(quad)))
        out.append("fillPolygon pixels x198-206 y98-105: " + attempt(
            lambda: read_box(198, 98, 9, 8)))

    # drawString: does a longer string cost more?
    out.append("drawString 1 char " + timed(
        50, lambda: gr.drawString("X", 10, 190)))
    out.append("drawString 20 chars " + timed(
        50, lambda: gr.drawString("XXXXXXXXXXXXXXXXXXXX", 10, 210)))

    # pushImage / popImage: can a screen region be copied?
    clear()
    gr.setColor((0, 0, 255))
    gr.fillRect(100, 100, 6, 4)
    gr.setColor((255, 0, 0))
    gr.fillRect(102, 101, 2, 2)
    n, msg = arg_count(gr.popImage)
    if n == 0:
        # Every push is paired with a pop, so nothing is left on the stack
        out.append("push: " + attempt(lambda: gr.pushImage(100, 100, 6, 4)))
        gr.setColor((255, 255, 255))
        gr.fillRect(100, 100, 6, 4)
        out.append("pop(): " + attempt(lambda: gr.popImage()))
        out.append("after pop x98-107 y99-104: " + attempt(
            lambda: read_box(98, 99, 10, 6)))
        out.append("push+pop pair " + timed(
            10, lambda: (gr.pushImage(100, 100, 6, 4), gr.popImage())))
        out.append("push+pop pair 100x60 " + timed(
            10, lambda: (gr.pushImage(100, 100, 100, 60), gr.popImage())))
    else:
        out.append("pop not tried: " + msg)

    # Native calls measured inside a plain loop, as PASFAST would use them
    fr = gr.fillRect
    t0 = monotonic()
    for k in range(400):
        fr(100, 200, 3, 1)
    out.append("fillRect in loop %.3f ms" % (
        (monotonic() - t0) * 1000 / 400))

    clear()
    draw_bits("\n".join(out), 6500)
    set_color(0, 0, 0)
    draw_text(4, 206, "Done")
    show_draw()


main()
