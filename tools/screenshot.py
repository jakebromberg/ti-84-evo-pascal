"""Read TI-84 Evo screenshots (320x240, 8-bit RGB PNG) without third-party packages.

The Python app's drawing area is 320x210 and starts DRAW_TOP rows down the screen, below the status bar.
"""
import struct
import zlib

DRAW_TOP = 30
WHITE = (248, 252, 248)     # how the calculator's white reads back in a screenshot


def load(path):
    """Return the screenshot as a list of rows, each a bytes object of R, G, B triples."""
    with open(path, "rb") as f:
        data = f.read()
    pos = 8
    idat = b""
    while pos < len(data):
        length, kind = struct.unpack(">I4s", data[pos:pos + 8])
        if kind == b"IHDR":
            width, height, depth, color_type = struct.unpack(">IIBB", data[pos + 8:pos + 18])
        elif kind == b"IDAT":
            idat += data[pos + 8:pos + 8 + length]
        pos += 12 + length
    if depth != 8 or color_type != 2:
        raise ValueError("expected an 8-bit RGB PNG")
    raw = zlib.decompress(idat)
    stride = width * 3
    rows = []
    prev = bytearray(stride)
    for y in range(height):
        start = y * (stride + 1)
        filter_type = raw[start]
        cur = bytearray(raw[start + 1:start + 1 + stride])
        for i in range(stride):
            a = cur[i - 3] if i >= 3 else 0
            b = prev[i]
            c = prev[i - 3] if i >= 3 else 0
            if filter_type == 1:
                cur[i] = (cur[i] + a) & 255
            elif filter_type == 2:
                cur[i] = (cur[i] + b) & 255
            elif filter_type == 3:
                cur[i] = (cur[i] + (a + b) // 2) & 255
            elif filter_type == 4:
                pa, pb, pc = abs(b - c), abs(a - c), abs(a + b - 2 * c)
                cur[i] = (cur[i] + (a if pa <= pb and pa <= pc else b if pb <= pc else c)) & 255
        rows.append(bytes(cur))
        prev = cur
    return rows


def pixel(rows, x, y):
    """Return the (r, g, b) color at full-screen coordinates (x, y)."""
    return tuple(rows[y][x * 3:x * 3 + 3])
