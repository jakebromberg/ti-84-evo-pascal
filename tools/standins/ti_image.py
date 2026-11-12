"""Dry-run stand-in for the Evo's ti_image. set_pixel draws to the stand-in screen; the rest do nothing."""
import ti_draw
def set_pixel(x, y, c):
    if not (isinstance(c, tuple) and len(c) == 3): raise TypeError("color must be an (r, g, b) tuple")
    ti_draw._c[0] = c; ti_draw._put(x, y)
gr = None
def new_image(w, h, c): pass
def copy_image(i): pass
def load_image(n): pass
def show_image(x, y): pass
def clear_image(): pass
def get_pixel(x, y): pass
def show_screen(): pass
_image_name = ""
