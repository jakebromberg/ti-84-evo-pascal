from ti_draw import *

N = 16

def hue_to_rgb(h):
    # h in [0, 1); full saturation and brightness; returns 0-255 ints
    h6 = h * 6
    k = int(h6)
    f = h6 - k
    up = int(255 * f)
    down = 255 - up
    return [(255, up, 0), (down, 255, 0), (0, 255, up),
            (0, down, 255), (up, 0, 255), (255, 0, down)][k % 6]

colors = [hue_to_rgb(i / N) for i in range(N)]

row = [0, 1, 0]
W = 320
H = 210

clear()

for y in range(H):
    x0 = (W - len(row)) // 2
    for i in range(1, len(row) - 1):
        set_color(*colors[row[i]])
        plot_xy(x0 + i, y, 7)
    row.append(0)
    for i in range(len(row) - 2, 0, -1):
        row[i] = (row[i] + row[i - 1]) % N

# Keep the drawing on screen until [clear] is pressed
show_draw()
