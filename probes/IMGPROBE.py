from ti_draw import *
from time import monotonic
import ti_graphics as gr
import ti_image

# Probe of ti_image's undocumented new_image. Every call that changes
# the screen costs 4-6 ms, but reading a pixel costs 0.05 ms. If
# new_image makes an off-screen image that set_pixel can write to
# quickly, the whole triangle could be built off-screen and shown with
# one show_image call.
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


def timed(count, fn):
    try:
        t0 = monotonic()
        for k in range(count):
            fn()
        return "%.3f ms" % ((monotonic() - t0) * 1000 / count)
    except Exception as e:
        return "ERR " + str(e)[:70]


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

    def name():
        return attempt(lambda: repr(ti_image._image_name))

    out.append("name before: " + name())
    # Try the likely argument orders; stop at the first that runs
    made = None
    for label, fn in (
            ("new_image(8,6,(255,0,0))",
             lambda: ti_image.new_image(8, 6, (255, 0, 0))),
            ("new_image('PROBE',8,6)",
             lambda: ti_image.new_image("PROBE", 8, 6))):
        try:
            r = fn()
            made = label
            out.append(label + " -> " + str(r)[:60])
            break
        except Exception as e:
            out.append(label + " ERR " + str(e)[:70])
    out.append("name after: " + name())

    if made:
        # Does set_pixel now write to the image instead of the screen?
        out.append("screen x0-9 y30-37 before set_pixel: "
                   + attempt(lambda: read_box(0, OY, 10, 8)))
        out.append("set_pixel " + timed(
            200, lambda: ti_image.set_pixel(3, 2, (0, 0, 255))))
        out.append("set_pixel(1,1): " + attempt(
            lambda: ti_image.set_pixel(1, 1, (0, 0, 255))))
        out.append("get_pixel(3,2)=" + attempt(
            lambda: ti_image.get_pixel(3, 2))
            + " get_pixel(0,0)=" + attempt(lambda: ti_image.get_pixel(0, 0)))
        out.append("screen x0-9 y30-37 after set_pixel: "
                   + attempt(lambda: read_box(0, OY, 10, 8)))
        # Does show_image stamp it, and what does a stamp cost?
        out.append("show_image(100,100): " + attempt(
            lambda: ti_image.show_image(100, 100)))
        out.append("screen x98-111 y98-109: " + attempt(
            lambda: read_box(98, 98, 14, 12)))
        out.append("screen x98-111 y128-139: " + attempt(
            lambda: read_box(98, 128, 14, 12)))
        out.append("colors at (103,102)=" + attempt(
            lambda: gr.getPixel(103, 102)) + " (103,132)=" + attempt(
            lambda: gr.getPixel(103, 132)) + " (100,130)=" + attempt(
            lambda: gr.getPixel(100, 130)))
        out.append("show_image " + timed(
            20, lambda: ti_image.show_image(100, 100)))
        # A full-size image: can it be made, and what does showing it cost?
        out.append("new 320x210: " + attempt(
            lambda: ti_image.new_image(320, 210, (255, 255, 255))
            if made.startswith("new_image(8") else
            ti_image.new_image("PROBE", 320, 210)))
        out.append("set_pixel big " + timed(
            200, lambda: ti_image.set_pixel(160, 100, (255, 0, 0))))
        out.append("show big " + timed(
            5, lambda: ti_image.show_image(0, 0)))
        out.append("name end: " + name())

    clear()
    draw_bits("\n".join(out), 6500)
    set_color(0, 0, 0)
    draw_text(4, 206, "Done")
    show_draw()


main()
