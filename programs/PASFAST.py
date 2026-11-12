from ti_draw import *
from time import monotonic

# Set True to time only the math (no drawing calls)
COMPUTE_ONLY = False


def hue_to_rgb(h):
    # h in [0, 1); full saturation and brightness; returns 0-255 ints
    h6 = h * 6
    k = int(h6)
    f = h6 - k
    up = int(255 * f)
    down = 255 - up
    return [(255, up, 0), (down, 255, 0), (0, 255, up),
            (0, down, 255), (up, 0, 255), (255, 0, down)][k % 6]


def main():
    # Locals are much faster than globals in MicroPython
    N = 16      # must be a power of 2, up to 128
    W = 320
    H = 210
    t0 = monotonic()

    # Compute every row first. The whole row lives in one big integer,
    # one byte per entry, so native integer math makes each next row
    # in three operations.
    rows = []
    R = 1
    mask = N - 1
    for y in range(H):
        rows.append(R.to_bytes(y + 1, 'little'))
        mask = (mask << 8) | (N - 1)
        R = (R + (R << 8)) & mask

    # Each drawing call costs about 6 ms, so make as few as possible.
    # Paint each row in its background color (the color with the most
    # separate runs there) in one call, then draw only the other colors.
    # A list, not a bytearray: MicroPython can't do "c in bytearray"
    bg = [0] * H
    for y in range(H):
        count = [0] * N
        prev = -1
        for v in rows[y]:
            if v != prev:
                count[v] += 1
                prev = v
        bg[y] = count.index(max(count))

    if not COMPUTE_ONLY:
        clear()
        fr = fill_rect
        # Color changes cost about 4 ms, so draw one color at a time.
        # Evo fill_rect fills only the inside of the box, and sizes
        # below 2 raise, so every box is padded by one pixel per side.
        for c in range(N):
            if c in bg:
                set_color(*hue_to_rgb(c / N))
                for y in range(H):
                    if bg[y] == c:
                        n = y + 1
                        fr((W - n) // 2 - 1, y - 1, n + 1, 2)
        for c in range(N):
            set_color(*hue_to_rgb(c / N))
            cb = bytes([c])
            for y in range(H):
                if bg[y] == c:
                    continue
                vals = rows[y]
                n = y + 1
                x0 = (W - n) // 2
                i = vals.find(cb)          # native search for this color
                while i >= 0:
                    j = i + 1
                    while j < n and vals[j] == c:
                        j += 1
                    fr(x0 + i - 1, y - 1, j - i + 1, 2)
                    i = vals.find(cb, j)

    elapsed = monotonic() - t0
    set_color(0, 0, 0)
    # Text sits in rows y-17..y-3; the top-left corner is empty
    draw_text(4, 20, "Time: %.2f s" % elapsed)
    show_draw()


main()
