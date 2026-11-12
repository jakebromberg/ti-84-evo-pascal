from ti_draw import *
from time import monotonic

# Draws Pascal's triangle mod 16 twice and times each drawing strategy:
#   A: row by row, changing color whenever the next run differs
#   B: one color at a time (16 color changes)
# The row math and clear() are excluded from the drawing times.


def hue_to_rgb(h):
    # h in [0, 1); full saturation and brightness; returns 0-255 ints
    h6 = h * 6
    k = int(h6)
    f = h6 - k
    up = int(255 * f)
    down = 255 - up
    return [(255, up, 0), (down, 255, 0), (0, 255, up),
            (0, down, 255), (up, 0, 255), (255, 0, down)][k % 6]


def compute_rows(N, H):
    # One big integer holds a row, one byte per entry
    rows = []
    R = 1
    mask = N - 1
    for y in range(H):
        rows.append(R.to_bytes(y + 1, 'little'))
        mask = (mask << 8) | (N - 1)
        R = (R + (R << 8)) & mask
    return rows


def draw_by_row(rows, colors, W):
    sc = set_color
    fr = fill_rect
    last = -1
    y = 0
    for vals in rows:
        n = y + 1
        x0 = (W - n) // 2
        i = 0
        while i < n:
            v = vals[i]
            j = i + 1
            while j < n and vals[j] == v:
                j += 1
            if v != last:
                sc(*colors[v])
                last = v
            # Evo fill_rect fills only inside the box; pad by one pixel
            fr(x0 + i - 1, y - 1, j - i + 1, 2)
            i = j
        y += 1


def draw_by_color(rows, colors, W):
    fr = fill_rect
    for c in range(len(colors)):
        set_color(*colors[c])
        cb = bytes([c])
        y = 0
        for vals in rows:
            n = y + 1
            x0 = (W - n) // 2
            i = vals.find(cb)
            while i >= 0:
                j = i + 1
                while j < n and vals[j] == c:
                    j += 1
                fr(x0 + i - 1, y - 1, j - i + 1, 2)
                i = vals.find(cb, j)
            y += 1


def main():
    N = 16
    W = 320
    H = 210
    colors = [hue_to_rgb(i / N) for i in range(N)]

    t0 = monotonic()
    rows = compute_rows(N, H)
    t_math = monotonic() - t0

    clear()
    t0 = monotonic()
    draw_by_row(rows, colors, W)
    t_row = monotonic() - t0

    clear()
    t0 = monotonic()
    draw_by_color(rows, colors, W)
    t_color = monotonic() - t0

    set_color(0, 0, 0)
    # Seconds; kept short so the text stays left of the triangle
    draw_text(4, 20, "Math " + str(round(t_math, 2)))
    draw_text(4, 40, "Row " + str(round(t_row, 2)))
    draw_text(4, 60, "Color " + str(round(t_color, 2)))
    show_draw()


main()
