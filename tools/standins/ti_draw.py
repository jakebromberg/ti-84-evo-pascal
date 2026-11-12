"""Stand-in for the TI-84 Evo ti_draw, following its documented quirks (calcplex.com)."""
W, H = 320, 210
pixels = {}
text_boxes = []
calls = {"set_color": 0, "fill_rect": 0, "plot_xy": 0, "draw_text": 0}
_c = [(0, 0, 0)]

class tidrawException(Exception): pass

def _put(x, y):
    if 0 <= x < W and 0 <= y < H:      # off-screen is silently ignored
        pixels[(x, y)] = _c[0]

def clear(): pixels.clear()
def set_color(r, g, b):
    calls["set_color"] += 1
    for v in (r, g, b):
        if int(v) != v or not 0 <= v <= 255: raise tidrawException("bad color %r" % ((r, g, b),))
    _c[0] = (r, g, b)
def fill_rect(x, y, w, h):
    # Fills strictly inside the box (x, y)-(x+w, y+h); extents below 2 raise.
    calls["fill_rect"] += 1
    if w < 2: raise tidrawException("Width cannot be negative.")
    if h < 2: raise tidrawException("Height cannot be negative.")
    for px in range(x + 1, x + w):
        for py in range(y + 1, y + h): _put(px, py)
def plot_xy(x, y, mark):
    calls["plot_xy"] += 1
    if mark != 7: raise NotImplementedError("only mark 7 (single pixel) is modeled")
    _put(x, y)
def draw_text(x, y, s):
    # Glyphs are 10 px wide and occupy rows y-17 .. y-3.
    calls["draw_text"] += 1
    if not isinstance(s, str): raise tidrawException("text must be a string")
    text_boxes.append((x, y - 17, x + 10 * len(s) - 1, y - 3, s))
def show_draw(): pass

# --- Undocumented-detail guesses below: only good enough for dry runs ---
calls.update({"draw_line": 0, "draw_poly": 0, "fill_poly": 0})
def _line(x1, y1, x2, y2, on=None):
    # on(i) says whether the line's i-th pixel is painted; None paints them all
    i = 0
    dx, dy = abs(x2 - x1), abs(y2 - y1)
    sx = 1 if x1 < x2 else -1
    sy = 1 if y1 < y2 else -1
    err = dx - dy
    while True:
        if on is None or on(i): _put(x1, y1)
        i += 1
        if x1 == x2 and y1 == y2: break
        e2 = 2 * err
        if e2 > -dy: err -= dy; x1 += sx
        if e2 < dx: err += dx; y1 += sy
def draw_line(x1, y1, x2, y2):
    calls["draw_line"] += 1
    _line(x1, y1, x2, y2)
def draw_poly(xs, ys):
    calls["draw_poly"] += 1
    if len(xs) != len(ys): raise tidrawException("lists differ in length")
    for i in range(len(xs) - 1): _line(xs[i], ys[i], xs[i + 1], ys[i + 1])
def fill_poly(xs, ys):
    calls["fill_poly"] += 1
    if len(xs) != len(ys): raise tidrawException("lists differ in length")
    for i in range(len(xs)): _line(xs[i], ys[i], xs[(i + 1) % len(xs)], ys[(i + 1) % len(xs)])
def set_window(*a):
    if len(a) not in (0, 4): raise TypeError("set_window takes 0 or 4 arguments")
