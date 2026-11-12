"""Dry-run stand-in for the Evo's native ti_graphics.

Coordinates are full-screen: the drawing area starts 30 rows down. fillRect, setPixel, drawLine and drawPolyLine follow what the GRPROBE programs measured on the calculator; fillPolygon, drawString and drawRect are rough or empty.
"""
import ti_draw
class Color: RED = 1
class Font: SMALL = 0; MEDIUM = 1; LARGE = 2; ICON = 3; SMALLD = 4
class Style: SMOOTH = 0; DOTTED = 1; DASHED = 2
def hsv_to_rgb(h, s, v): return (0, 0, 0)
ti_draw.calls.update({"fillRect": 0, "setColor": 0, "fillPolygon": 0, "getPixel": 0, "drawLine": 0})
def setColor(c):
    ti_draw.calls["setColor"] += 1
    if not isinstance(c, tuple): raise TypeError("can't convert int to tuple")
    ti_draw._c[0] = c
def fillRect(x, y, w, h):
    ti_draw.calls["fillRect"] += 1
    for px in range(x, x + w):
        for py in range(y, y + h): ti_draw._put(px, py - 30)
def setPixel(x, y, c): ti_draw._c[0] = c; ti_draw._put(x, y - 30)
def getPixel(x, y):
    ti_draw.calls["getPixel"] += 1
    return ti_draw.pixels.get((x, y - 30), (255, 255, 255))
def drawLine(x1, y1, x2, y2):
    ti_draw.calls["drawLine"] += 1
    ti_draw._line(x1, y1 - 30, x2, y2 - 30, _PATTERNS[_pen[0]])
def drawRect(x, y, w, h): pass
def cls(): ti_draw.clear()
def pushImage(a, b): pass
def popImage(): pass
_stack = []
def drawPolyLine(pts):
    if not isinstance(pts[0], tuple): raise TypeError("expected a list of tuples")
    for i in range(len(pts) - 1): ti_draw._line(pts[i][0], pts[i][1] - 30, pts[i + 1][0], pts[i + 1][1] - 30)
def fillPolygon(pts):
    ti_draw.calls["fillPolygon"] += 1
    # Even-odd scanline fill sampled at pixel centers. The calculator's exact edge rule is not known.
    ys = [p[1] for p in pts]
    for py in range(int(min(ys)), int(max(ys)) + 1):
        xs = []
        for i in range(len(pts)):
            (x1, y1), (x2, y2) = pts[i], pts[(i + 1) % len(pts)]
            if (y1 <= py < y2) or (y2 <= py < y1):
                xs.append(x1 + (py - y1) * (x2 - x1) / (y2 - y1))
        xs.sort()
        for j in range(0, len(xs) - 1, 2):
            for px in range(int(xs[j] + 0.5), int(xs[j + 1] + 0.5) + 1): ti_draw._put(px, py - 30)
def drawString(s, x, y):
    # Rough, after the small font: "." is the measured 2 by 2 dot and moves on 4 pixels, a space moves on 6, anything else is a 4 by 6 block. The font chosen is ignored.
    cx = x
    for ch in s:
        if ch == ".":
            for px in (cx + 1, cx + 2):
                for py in (y - 30 + 10, y - 30 + 11): ti_draw._put(px, py)
            cx += 4
        else:
            if ch != " ":
                for px in range(cx + 1, cx + 5):
                    for py in range(y - 30 + 2, y - 30 + 8): ti_draw._put(px, py)
            cx += 6
def setFont(f): pass
_pen = [0]
# Which pixels of a 1-pixel line each pen style paints, counted from the line's first point (measured by PENPROBE)
_PATTERNS = [None, lambda i: i % 4 in (0, 3), lambda i: i % 6 in (0, 1, 2, 5), lambda i: i % 4 == 3]
def setPen(style, thickness):
    # Styles are modeled for drawLine only; thickness is accepted and ignored (lines stay 1 pixel thick)
    if isinstance(style, str) or isinstance(thickness, str): raise TypeError("can't convert str to float")
    _pen[0] = int(style) if 0 <= int(style) <= 3 else 0
def string_size(s): return (10, 15)
def pushImage(x, y, w, h): _stack.append((x, y, w, h, [getPixel(px, py) for py in range(y, y + h) for px in range(x, x + w)]))
def popImage():
    x, y, w, h, data = _stack.pop(); i = 0
    for py in range(y, y + h):
        for px in range(x, x + w): setPixel(px, py, data[i]); i += 1
