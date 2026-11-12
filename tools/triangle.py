"""The exact picture the Pascal programs should draw: Pascal's triangle mod 16, one pixel per entry."""
from math import comb

N = 16
WIDTH = 320
HEIGHT = 210


def hue_to_rgb(h):
    """Same hue function as the calculator programs: h in [0, 1), full saturation and brightness."""
    h6 = h * 6
    k = int(h6)
    f = h6 - k
    up = int(255 * f)
    down = 255 - up
    return [(255, up, 0), (down, 255, 0), (0, 255, up),
            (0, down, 255), (up, 0, 255), (255, 0, down)][k % 6]


COLORS = [hue_to_rgb(i / N) for i in range(N)]


def expected():
    """Return {(x, y): color index} in drawing-area coordinates."""
    pixels = {}
    for y in range(HEIGHT):
        x0 = (WIDTH - (y + 1)) // 2
        for k in range(y + 1):
            pixels[(x0 + k, y)] = comb(y, k) % N
    return pixels
