from ti_draw import *

# Lists what this calculator's Python really offers, beyond the documented
# functions: hidden names in the TI modules, other importable modules, and
# a few facts about the interpreter.
#
# The report is too long to read off the screen, so it is drawn as a block
# of black pixels: 7 bits per character, 45 characters per pixel row,
# starting at x = 2, y = 0. A screenshot taken over USB is decoded on the
# computer. "Done" appears at the bottom when the block is complete.

DOCUMENTED = {
    "ti_draw": "clear clear_rect draw_circle draw_line draw_poly draw_rect "
               "draw_text fill_circle fill_poly fill_rect get_screen_dim "
               "plot_xy set_color set_pen set_window show_draw",
    "ti_system": "disp_at disp_clr disp_wait escape get_key recall_RegEQ "
                 "recall_list sleep store_list wait wait_key",
    "ti_plotlib": "a b xmax xmin ymax ymin auto_window axes cls color grid "
                  "labels lin_reg line pen plot scatter show_plot text_at "
                  "title window",
    "ti_image": "clear_image get_pixel load_image set_pixel show_image "
                "show_screen",
    "ti_graphics": "drawArc drawImage fillArc hsv_to_rgb setFont string_size",
}

CANDIDATES = (
    "sys gc os uos micropython array struct ustruct framebuf math cmath "
    "random time utime collections ucollections uctypes machine builtins "
    "io uio json ujson re ure binascii ubinascii errno select hashlib heapq "
    "zlib uzlib displayio "
    "bitmaptools board storage supervisor ti_st ti_common ti_gfx ti_tools "
    "ti_picture ti_pict ti_note ti_matrix ti_list ti_stat ti_data ti_file "
    "ti_usb ti_sound ti_keys ti_lcd ti_display ti_screen ti_buffer ti_fb "
    "ti_canvas ti_turtle turtle ti_io ti_os ti_var ti_basic ti_python "
    "ti_evo evo ti_ext ti_ce ce_turtl ce_chart ce_box ce_quivr ce_tools "
    "_thread asyncio uasyncio ulab numpy usb_cdc busio digitalio "
    "microcontroller terminalio fontio vectorio framebufferio atexit "
    "traceback msgpack _ti_draw _ti_image _ti_graphics _ti_system tidraw "
    "tiimage tigraphics")

# Importable modules whose contents are standard and not worth listing
BORING = ("math cmath random collections ucollections re ure json ujson "
          "binascii ubinascii hashlib heapq errno struct ustruct array "
          "builtins select zlib uzlib").split()

BUILTINS = "open memoryview exec eval compile input help globals".split()


def attempt(fn):
    # Returns str(fn()), or the error text, so one failure can't stop the report
    try:
        return str(fn())
    except Exception as e:
        return "ERR " + str(e)


def names(m):
    return [n for n in dir(m) if not n.startswith("__")]


def report():
    out = []
    for name in ("ti_draw", "ti_system", "ti_plotlib", "ti_image",
                 "ti_graphics"):
        try:
            m = __import__(name)
            known = DOCUMENTED[name].split()
            extra = [n for n in names(m) if n not in known]
            gone = [n for n in known if n not in dir(m)]
            out.append("[" + name + "] " + str(m) + " file="
                       + attempt(lambda: m.__file__)
                       + " extra: " + " ".join(extra)
                       + " missing: " + " ".join(gone))
        except Exception as e:
            out.append("[" + name + "] ERR " + str(e))
    out.append("types: fill_rect=" + attempt(lambda: fill_rect)
               + " set_color=" + attempt(lambda: set_color)
               + " exc=" + attempt(lambda: tidrawException))
    ok = []
    for name in CANDIDATES.split():
        try:
            m = __import__(name)
        except Exception:
            continue
        ok.append(name)
        if name not in BORING:
            # Listing a module can itself fail (some load names lazily)
            out.append("[" + name + "] " + attempt(
                lambda: str(m) + " " + " ".join(names(m))))
    out.append("importable: " + " ".join(ok))
    out.append("builtins: " + attempt(lambda: " ".join(
        [n for n in BUILTINS if n in dir(__import__("builtins"))])))
    out.append("version=" + attempt(lambda: __import__("sys").version))
    out.append("impl=" + attempt(lambda: __import__("sys").implementation))
    out.append("platform=" + attempt(lambda: __import__("sys").platform))
    out.append("path=" + attempt(lambda: __import__("sys").path))
    out.append("mem_free=" + attempt(lambda: __import__("gc").mem_free()))
    out.append("mem_alloc=" + attempt(lambda: __import__("gc").mem_alloc()))
    out.append("cwd=" + attempt(lambda: __import__("os").getcwd()))
    out.append("ls=" + attempt(lambda: __import__("os").listdir())[:400])
    out.append("ls/=" + attempt(lambda: __import__("os").listdir("/"))[:400])
    return "\n".join(out)


def draw_bits(text):
    # 4-digit length, the text, then one all-ones character as an end mark
    text = text[:8000]
    text = "%04d" % len(text) + text + "\x7f"
    fr = fill_rect
    per_row = 45
    y = 0
    for start in range(0, len(text), per_row):
        x = 2
        run = -1                # x where the current run of 1 bits began
        for ch in text[start:start + per_row]:
            v = ord(ch) & 127
            for bit in (64, 32, 16, 8, 4, 2, 1):
                if v & bit:
                    if run < 0:
                        run = x
                elif run >= 0:
                    # Evo fill_rect fills only inside the box; pad by one
                    fr(run - 1, y - 1, x - run + 1, 2)
                    run = -1
                x += 1
        if run >= 0:
            fr(run - 1, y - 1, x - run + 1, 2)
        y += 1


def main():
    text = report()
    clear()
    set_color(0, 0, 0)
    draw_bits(text)
    draw_text(4, 206, "Done")
    show_draw()


main()
