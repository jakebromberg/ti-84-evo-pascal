# Runs one calculator program under MicroPython with the stand-in TI modules in this folder,
# then writes what it drew to out.txt: an error line, one line per pixel, one per text box, and the call counts.
# Used by tools/validate.py; run from this folder as: micropython runprog.py <program.py>
import sys
sys.path.insert(0, '.')
import ti_draw
prog = sys.argv[1]
err = None
try:
    exec(open(prog).read(), {"__name__": "__main__"})
except Exception as e:
    err = e
    sys.print_exception(e)
with open('out.txt', 'w') as f:
    f.write('ERR %s\n' % (repr(err) if err else ''))
    for (x, y), c in ti_draw.pixels.items():
        f.write('P %d %d %d %d %d\n' % (x, y, c[0], c[1], c[2]))
    for t in ti_draw.text_boxes:
        f.write('T %d %d %d %d %s\n' % t)
    f.write('C %r\n' % (ti_draw.calls,))
