from ti_draw import *
from time import monotonic

# Times the drawing calls PASFAST has not tried yet, then draws small
# test shapes so a screenshot shows exactly which pixels each call paints.
# Results are milliseconds per call. They are printed to the shell
# before the final screen is drawn, because print() wipes the drawing.


def comb(x, y, runs):
    # Path for `runs` 2-pixel runs on row y, 1 pixel apart, joined
    # through row y+1: the shape PASFAST would hand to draw_poly.
    xs = []
    ys = []
    for r in range(runs):
        a = x + 3 * r
        xs += [a, a + 1, a + 1, a + 3]
        ys += [y, y, y + 1, y + 1]
    return xs, ys


def timed(label, count, fn, results):
    # Runs fn(k) count times and records milliseconds per call
    try:
        t0 = monotonic()
        for k in range(count):
            fn(k)
        ms = (monotonic() - t0) * 1000 / count
        results.append(label + " %.2f" % ms)
    except Exception as e:
        results.append(label + " " + str(e)[:18])


def probe(name, fn, failed):
    # Failures are kept as short text; printing would wipe the screen
    try:
        fn()
    except Exception as e:
        failed.append(name + " " + str(e)[:12])


def main():
    results = []
    failed = []
    clear()

    # Four copies of each path on different rows, so calls don't repeat
    p2 = [([20 + 3 * i, 21 + 3 * i], [10 + i, 10 + i]) for i in range(4)]
    p20 = [comb(20, 20 + 3 * i, 5) for i in range(4)]
    p200 = [comb(20, 40 + 3 * i, 50) for i in range(4)]
    box = [([200 + 4 * i, 202 + 4 * i, 202 + 4 * i, 200 + 4 * i],
            [10, 10, 12, 12]) for i in range(4)]

    set_color(0, 160, 0)
    timed("rect", 400,
          lambda k: fill_rect(19 + k % 100, 59 + k // 100, 3, 2), results)
    set_color(0, 0, 255)
    timed("line", 400,
          lambda k: draw_line(20 + k % 100, 70 + k // 100,
                              21 + k % 100, 70 + k // 100), results)
    set_color(255, 0, 0)
    timed("poly2", 400, lambda k: draw_poly(*p2[k & 3]), results)
    timed("poly20", 100, lambda k: draw_poly(*p20[k & 3]), results)
    timed("poly200", 20, lambda k: draw_poly(*p200[k & 3]), results)
    set_color(160, 0, 160)
    timed("fpoly4", 200, lambda k: fill_poly(*box[k & 3]), results)
    timed("fpoly200", 10, lambda k: fill_poly(*p200[k & 3]), results)

    # ti_plotlib takes whole lists of points in one call
    plt = None
    try:
        import ti_plotlib as plt
        plt.cls()
        plt.window(0, 319, 0, 209)
        plt.color(230, 120, 0)
    except Exception as e:
        results.append("plotlib " + str(e)[:18])
        plt = None
    if plt is not None:
        s20 = [(list(range(20, 60, 2)), [100 + i] * 20) for i in range(4)]
        s200 = [(list(range(20, 220)), [110 + i] * 200) for i in range(4)]
        timed("scat20", 50,
              lambda k: plt.scatter(s20[k & 3][0], s20[k & 3][1], "."),
              results)
        timed("scat200", 10,
              lambda k: plt.scatter(s200[k & 3][0], s200[k & 3][1], "."),
              results)

    for line in results:
        print(line)

    # Wipe the timing marks, then draw the test shapes
    probe("W", lambda: set_window(), failed)
    clear()
    if plt is not None:
        # Three magenta dots; where they land shows how plot units map
        probe("S", lambda: (plt.color(255, 0, 255),
                            plt.scatter([250, 260, 250], [20, 20, 40], ".")),
              failed)
        probe("W", lambda: set_window(), failed)

    set_color(255, 0, 0)
    probe("A", lambda: draw_line(10, 168, 20, 168), failed)
    set_color(0, 0, 255)
    probe("B", lambda: draw_line(30, 168, 30, 173), failed)
    set_color(0, 160, 0)
    probe("C", lambda: draw_line(40, 168, 46, 174), failed)
    set_color(255, 0, 0)
    probe("D", lambda: draw_line(55, 168, 56, 169), failed)
    set_color(0, 0, 255)
    probe("E", lambda: draw_line(65, 168, 65, 169), failed)
    set_color(0, 160, 0)
    probe("F", lambda: draw_line(75, 168, 75, 168), failed)

    # Comb: runs at x 10-14, 20-22 and 30 on row 190, joined via row 191
    set_color(255, 0, 0)
    probe("G", lambda: draw_poly(
        [10, 14, 14, 20, 20, 22, 22, 30, 30, 30, 36],
        [190, 190, 191, 191, 190, 190, 191, 191, 190, 191, 191]), failed)
    set_color(0, 0, 255)
    probe("H", lambda: draw_poly([50, 55], [190, 190]), failed)
    # An open V: a line across the top would mean draw_poly closes shapes
    set_color(0, 160, 0)
    probe("I", lambda: draw_poly([70, 80, 90], [185, 195, 185]), failed)
    set_color(255, 0, 0)
    probe("J", lambda: fill_poly([100, 110, 110, 100],
                                 [185, 185, 195, 195]), failed)
    set_color(0, 0, 255)
    probe("K", lambda: fill_poly([120, 130, 130, 120],
                                 [190, 190, 191, 191]), failed)
    # Repeated point in the middle of a path
    set_color(0, 160, 0)
    probe("M", lambda: draw_poly([150, 155, 155, 160],
                                 [190, 190, 190, 190]), failed)
    # Path that dips below the bottom edge of the screen
    set_color(255, 0, 0)
    probe("N", lambda: draw_poly([170, 175, 175, 180, 180, 185],
                                 [209, 209, 210, 210, 209, 209]), failed)

    set_color(0, 0, 0)
    y = 18
    for line in results:
        draw_text(4, y, line)
        y += 16
    # Shapes that raised, in a second column
    y = 18
    for line in failed:
        draw_text(170, y, line)
        y += 16
    show_draw()


main()
