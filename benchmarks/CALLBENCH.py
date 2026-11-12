from ti_draw import *
from time import monotonic

# Times single-pixel drawing methods on the TI-84 Evo.
# Each test makes COUNT calls into a 100x20 area at the bottom right.
# Results are milliseconds per call, including loop overhead
# (the "loop" line is the overhead alone).

COUNT = 2000
AX = 210    # pixel test area: x 210..309, y 180..199
AY = 180


def ms(t):
    return "%.2f ms" % (t * 1000 / COUNT)


def main():
    n = COUNT
    fr = fill_rect
    px = plot_xy
    sc = set_color
    results = []

    clear()

    # Loop overhead only
    t0 = monotonic()
    for k in range(n):
        x = AX + k % 100
        y = AY + k // 100
    results.append("loop " + ms(monotonic() - t0))

    # set_color, alternating so every call is a real change
    t0 = monotonic()
    for k in range(n):
        if k & 1:
            sc(255, 0, 0)
        else:
            sc(0, 0, 255)
    results.append("set_color " + ms(monotonic() - t0))

    # One pixel with fill_rect (padded: Evo fills only inside the box)
    sc(0, 160, 0)
    t0 = monotonic()
    for k in range(n):
        x = AX + k % 100
        y = AY + k // 100
        fr(x - 1, y - 1, 2, 2)
    results.append("fill_rect " + ms(monotonic() - t0))

    # One pixel with plot_xy mark 7
    sc(160, 0, 160)
    t0 = monotonic()
    for k in range(n):
        x = AX + k % 100
        y = AY + k // 100
        px(x, y, 7)
    results.append("plot_xy " + ms(monotonic() - t0))

    # One pixel with ti_image.set_pixel (color passed in, no set_color)
    try:
        from ti_image import set_pixel
        sp = set_pixel
        t0 = monotonic()
        for k in range(n):
            x = AX + k % 100
            y = AY + k // 100
            sp(x, y, (230, 120, 0))
        results.append("set_pixel " + ms(monotonic() - t0))
    except Exception as e:
        results.append("set_pixel n/a")

    # Off-screen drawing, if this ti_draw has it
    try:
        ub = use_buffer
        pb = paint_buffer
    except NameError:
        ub = None
    if ub is not None:
        try:
            ub()
        except Exception:
            # The Evo defines use_buffer but raises "Unsupported operation."
            ub = None
    if ub is None:
        results.append("buffer n/a")
    else:
        sc(0, 120, 200)
        t0 = monotonic()
        for k in range(n):
            x = AX + k % 100
            y = AY + k // 100
            fr(x - 1, y - 1, 2, 2)
        pb()
        results.append("buffered " + ms(monotonic() - t0))

    sc(0, 0, 0)
    y = 20
    for line in results:
        draw_text(4, y, line)
        y += 20
    show_draw()


main()
