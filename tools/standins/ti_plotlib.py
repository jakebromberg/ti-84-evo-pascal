"""Dry-run stand-in for ti_plotlib: assumes window units map straight to pixels, y up."""
import ti_draw
_w = [-10, 10, -6.56, 6.56]
def cls(): ti_draw.clear()
def window(a, b, c, d): _w[:] = [a, b, c, d]
def color(r, g, b): ti_draw._c[0] = (r, g, b)
def scatter(xs, ys, mark="o"):
    if len(xs) != len(ys): raise ValueError("lists differ in length")
    if mark not in ("o", "x", "+", "*", "."): raise ValueError("bad mark")
    for x, y in zip(xs, ys):
        ti_draw._put(int((x - _w[0]) * 319 / (_w[1] - _w[0])), 209 - int((y - _w[2]) * 209 / (_w[3] - _w[2])))
