"""Decode the pixel-block report drawn by the probe programs (MODDUMP, GRPROBE, GRPROBE2, IMGPROBE).

Usage: python3 tools/decode_bits.py <screenshot.png | tools/standins/out.txt>

The block holds 7 bits per character and 45 characters per pixel row, starting at x = 2 on the first row of the drawing area. The text starts with its length as 4 digits and ends with one all-ones character. Exits with an error if the end mark is missing, which means the block is incomplete.
"""
import sys

import screenshot

PER_ROW = 45
LEFT = 2


def dark_from_png(path):
    rows = screenshot.load(path)
    return lambda x, y: max(screenshot.pixel(rows, x, y + screenshot.DRAW_TOP)) < 128


def dark_from_dry_run(path):
    on = set()
    with open(path) as f:
        for line in f:
            if line.startswith("P "):
                _, x, y, r, g, b = line.split()
                if max(int(r), int(g), int(b)) < 128:
                    on.add((int(x), int(y)))
    return lambda x, y: (x, y) in on


def decode(dark):
    """Return the report text, given dark(x, y) for drawing-area coordinates."""
    def char(i):
        y, column = divmod(i, PER_ROW)
        value = 0
        for bit in range(7):
            value = (value << 1) | dark(LEFT + column * 7 + bit, y)
        return value

    digits = "".join(chr(char(i)) for i in range(4))
    if not digits.isdigit():
        raise ValueError("no report block found")
    length = int(digits)
    text = "".join(chr(char(4 + i)) for i in range(length))
    if char(4 + length) != 127:
        raise ValueError("end mark missing: the block is incomplete or misaligned")
    return text


if __name__ == "__main__":
    path = sys.argv[1]
    try:
        print(decode(dark_from_png(path) if path.endswith(".png") else dark_from_dry_run(path)))
    except ValueError as e:
        sys.exit(str(e))
