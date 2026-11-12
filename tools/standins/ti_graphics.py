"""Dry-run stand-in for the Evo's native ti_graphics.

Coordinates are full-screen: the drawing area starts 30 rows down. fillRect, setPixel, drawLine and drawPolyLine follow what the GRPROBE programs measured on the calculator; fillPolygon, drawString and drawRect are rough or empty.
"""
import ti_draw
class Color: RED = 1
class Font: SMALL = 1
class Style: THIN = 1
def hsv_to_rgb(h, s, v): return (0, 0, 0)
ti_draw.calls.update({"fillRect": 0, "setColor": 0})
def setColor(c):
    ti_draw.calls["setColor"] += 1
    if not isinstance(c, tuple): raise TypeError("can't convert int to tuple")
    ti_draw._c[0] = c
def fillRect(x, y, w, h):
    ti_draw.calls["fillRect"] += 1
    for px in range(x, x + w):
        for py in range(y, y + h): ti_draw._put(px, py - 30)
def setPixel(x, y, c): ti_draw._c[0] = c; ti_draw._put(x, y - 30)
def getPixel(x, y): return ti_draw.pixels.get((x, y - 30), (255, 255, 255))
def drawLine(x1, y1, x2, y2): ti_draw._line(x1, y1 - 30, x2, y2 - 30)
def drawRect(x, y, w, h): pass
def cls(): ti_draw.clear()
def pushImage(a, b): pass
def popImage(): pass
_stack = []
def drawPolyLine(pts):
    if not isinstance(pts[0], tuple): raise TypeError("expected a list of tuples")
    for i in range(len(pts) - 1): ti_draw._line(pts[i][0], pts[i][1] - 30, pts[i + 1][0], pts[i + 1][1] - 30)
def fillPolygon(pts):
    xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
    fillRect(min(xs), min(ys), max(xs) - min(xs) + 1, max(ys) - min(ys) + 1)
def drawString(s, x, y): pass
def pushImage(x, y, w, h): _stack.append((x, y, w, h, [getPixel(px, py) for py in range(y, y + h) for px in range(x, x + w)]))
def popImage():
    x, y, w, h, data = _stack.pop(); i = 0
    for py in range(y, y + h):
        for px in range(x, x + w): setPixel(px, py, data[i]); i += 1
