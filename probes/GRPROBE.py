from ti_draw import *
from time import monotonic
import ti_draw
import ti_graphics as gr

# ti_draw turned out to be a Python wrapper around the native ti_graphics
# module, which has undocumented functions (fillRect, setPixel, setColor,
# drawLine, pushImage, ...). This program finds out how to call them, how
# fast they are, and exactly which pixels they paint.
#
# The report is drawn as a block of black pixels (7 bits per character,
# 45 characters per pixel row, from x = 2, y = 0) and decoded from a
# screenshot on the computer. Colored test shapes go below the block.


def attempt(fn):
    # Returns str(fn()), or the error text, so one failure can't stop the report
    try:
        return str(fn())
    except Exception as e:
        return "ERR " + str(e)


def describe(m, skip):
    # name=value for each non-dunder name in module m
    out = []
    for n in dir(m):
        if n.startswith("__") or n in skip:
            continue
        out.append(n + "=" + attempt(lambda: getattr(m, n))[:44])
    return "; ".join(out)


def no_args(m, names):
    # Calling with no arguments makes MicroPython say how many it wants
    out = []
    for n in names:
        try:
            r = getattr(m, n)()
            out.append(n + "() ran -> " + str(r)[:30])
        except Exception as e:
            out.append(n + "(): " + str(e)[:70])
    return "; ".join(out)


def first_ok(tries):
    # tries: (label, fn) pairs. Returns the first pair that runs, and notes.
    notes = []
    for label, fn in tries:
        try:
            fn()
            return label, fn, notes
        except Exception as e:
            notes.append(label + ": " + str(e)[:50])
    return None, None, notes


def timed(count, fn):
    try:
        t0 = monotonic()
        for k in range(count):
            fn()
        return "%.3f ms" % ((monotonic() - t0) * 1000 / count)
    except Exception as e:
        return "ERR " + str(e)[:50]


def plotlib_lines():
    # ti_plotlib is plain source on the calculator; its calls into
    # ti_graphics show the real argument conventions.
    try:
        f = open("ti_plotlib.py")
        src = f.read()
        f.close()
    except Exception as e:
        return "open ERR " + str(e)
    seen = []
    for line in src.split("\n"):
        line = line.strip()
        if ("gr." in line or line.startswith("import")
                or line.startswith("from")) and line not in seen:
            seen.append(line)
    return ("len=%d " % len(src)) + "\n".join(seen)


def draw_bits(text, limit):
    # 4-digit length, the text, then one all-ones character as an end mark
    text = text[:limit]
    text = "%04d" % len(text) + text + "\x7f"
    fr = fill_rect
    per_row = 45
    y = 0
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
                    # Evo fill_rect fills only inside the box; pad by one
                    fr(run - 1, y - 1, x - run + 1, 2)
                    run = -1
                x += 1
        if run >= 0:
            fr(run - 1, y - 1, x - run + 1, 2)
        y += 1


def main():
    out = []
    funcs = ("drawLine drawPolyLine drawRect drawString fillCircle "
             "fillPolygon fillRect getPixel setColor setPen setPixel "
             "drawArc fillArc drawImage setFont string_size "
             "checkImageExists").split()
    out.append("[gr] " + describe(gr, funcs))
    out.append("[gr args] " + no_args(gr, funcs))
    for n in ("Color", "Font", "Style"):
        out.append("[gr." + n + "] " + attempt(
            lambda: " ".join([a for a in dir(getattr(gr, n))
                              if not a.startswith("__")])))
    out.append("[ti_draw] " + describe(ti_draw, (
        "clear clear_rect draw_circle draw_line draw_poly draw_rect "
        "draw_text fill_circle fill_poly fill_rect get_screen_dim plot_xy "
        "set_color set_pen set_window show_draw gr").split()))
    import ti_image
    out.append("[ti_image] " + describe(ti_image, (
        "clear_image get_pixel load_image set_pixel show_image "
        "show_screen gr").split()))
    out.append("[ti_image args] " + no_args(
        ti_image, ("new_image", "copy_image")))
    # popImage is left alone: popping an empty stack might not be safe
    out.append("[gr stack args] " + no_args(gr, ("pushImage",)))

    # How each drawing call wants its arguments, then its speed
    clear()
    label, fn, notes = first_ok((
        ("setColor((r,g,b))", lambda: gr.setColor((0, 160, 0))),
        ("setColor(r,g,b)", lambda: gr.setColor(0, 160, 0))))
    out.append("setColor form: " + str(label) + " " + "; ".join(notes))
    if fn:
        out.append("setColor " + timed(400, fn))
    out.append("fillRect " + timed(
        400, lambda: gr.fillRect(100, 100, 3, 1)))
    label, fn, notes = first_ok((
        ("setPixel(x,y,(r,g,b))",
         lambda: gr.setPixel(120, 100, (0, 0, 255))),
        ("setPixel(x,y)", lambda: gr.setPixel(120, 100))))
    out.append("setPixel form: " + str(label) + " " + "; ".join(notes))
    if fn:
        out.append("setPixel " + timed(400, fn))
    out.append("drawLine " + timed(
        400, lambda: gr.drawLine(130, 100, 132, 100)))
    out.append("getPixel " + timed(400, lambda: gr.getPixel(100, 100)))
    out.append("getPixel value " + attempt(lambda: gr.getPixel(100, 100)))
    set_color(0, 160, 0)
    out.append("ti_draw.fill_rect " + timed(
        400, lambda: fill_rect(99, 119, 4, 2)))
    out.append("ti_draw.set_color " + timed(
        400, lambda: set_color(0, 160, 0)))
    out.append("[plotlib] " + plotlib_lines()[:2200])

    # Test shapes: where they land in the screenshot shows the coordinate
    # origin and exactly which pixels each call fills.
    clear()

    def color(r, g, b):
        try:
            gr.setColor((r, g, b))
        except Exception:
            gr.setColor(r, g, b)

    shapes = (
        ((255, 0, 0), lambda: gr.fillRect(100, 200, 5, 3)),
        ((0, 0, 255), lambda: gr.fillRect(120, 200, 1, 1)),
        ((0, 160, 0), lambda: gr.fillRect(130, 200, 2, 1)),
        ((255, 0, 255), lambda: gr.drawLine(140, 200, 150, 200)),
        ((255, 128, 0), lambda: gr.setPixel(160, 200, (255, 128, 0))),
        ((0, 200, 200), lambda: gr.drawRect(170, 200, 5, 3)),
    )
    bad = []
    for i in range(len(shapes)):
        try:
            color(*shapes[i][0])
            shapes[i][1]()
        except Exception as e:
            bad.append(str(i) + ": " + str(e)[:40])
    out.append("shape errors: " + "; ".join(bad))

    set_color(0, 0, 0)
    draw_bits("\n".join(out), 6500)
    draw_text(4, 206, "Done")
    show_draw()


main()
