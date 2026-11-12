"""Check a calculator screenshot against the exact triangle, pixel by pixel.

Usage: python3 tools/check_screenshot.py <screenshot.png>

Exits 0 only if every one of the 22,155 triangle pixels has the right color. Screenshot colors are slightly quantized, so each pixel is matched to its nearest palette color.
"""
import sys

import screenshot
import triangle


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
    wrong = wrong_pixels(screenshot.load(sys.argv[1]))
    print("wrong pixels:", wrong)
    sys.exit(0 if wrong == 0 else 1)
