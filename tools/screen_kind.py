"""Print what a calculator screenshot shows: "drawing", "python-menu" or "other".

Usage: python3 tools/screen_kind.py <screenshot.png>

"drawing" means a Python program's graphics screen is up, so the program is still running (possibly paused on its final screen). Send nothing but screenshots to the calculator in that state.
"""
import sys

import screenshot


def kind(rows):
    # The Python app shows its blue-and-yellow logo at the top left
    logo = sum(1 for y in range(2, 27) for x in range(4, 29)
               if rows[y][x * 3 + 2] > 140 and rows[y][x * 3] < 110)
    if logo < 20:
        return "other"
    # Menu screens have a soft-key bar across the bottom; a drawing leaves that row mostly white
    bar = sum(1 for x in range(320) if screenshot.pixel(rows, x, 236) != screenshot.WHITE)
    return "python-menu" if bar > 250 else "drawing"


if __name__ == "__main__":
    print(kind(screenshot.load(sys.argv[1])))
