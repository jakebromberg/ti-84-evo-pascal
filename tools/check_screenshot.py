"""Check a calculator screenshot against the exact triangle, pixel by pixel.

Usage: python3 tools/check_screenshot.py <screenshot.png>

Exits 0 only if every one of the 22,155 triangle pixels has the right color and nothing is painted outside the triangle. Screenshot colors are slightly quantized, so each pixel is matched to its nearest palette color. The top TEXT_ROWS rows outside the triangle are not checked, because the programs write their time there.
"""
import sys

import screenshot
import triangle


TEXT_ROWS = 20


def stray_pixels(rows):
    """Count non-white pixels outside the triangle, below the rows used for text."""
    inside = triangle.expected()
    return sum(1 for y in range(TEXT_ROWS, triangle.HEIGHT) for x in range(triangle.WIDTH)
               if (x, y) not in inside and min(screenshot.pixel(rows, x, y + screenshot.DRAW_TOP)) < 200)


def wrong_pixels(rows):
    wrong = 0
    for (x, y), index in triangle.expected().items():
        got = screenshot.pixel(rows, x, y + screenshot.DRAW_TOP)
        nearest = min(range(triangle.N),
                      key=lambda i: sum((a - b) ** 2 for a, b in zip(got, triangle.COLORS[i])))
        if nearest != index:
            wrong += 1
    return wrong


if __name__ == "__main__":
    shot = screenshot.load(sys.argv[1])
    wrong, stray = wrong_pixels(shot), stray_pixels(shot)
    print("wrong pixels:", wrong, "- stray pixels outside:", stray)
    sys.exit(0 if wrong == 0 and stray == 0 else 1)
