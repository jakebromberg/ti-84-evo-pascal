"""Run a calculator program on this computer under MicroPython, using the stand-in TI modules.

Usage: python3 tools/validate.py [--run-only] <program.py>

By default the program's drawing is compared with the exact triangle: every pixel must match, nothing may be drawn outside it, and text must not overlap it. With --run-only the program only has to finish without an error, which is the right check for benchmarks and probes.

Needs the `micropython` command (on macOS: brew install micropython).
"""
import os
import subprocess
import sys

import triangle

STANDINS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "standins")


def run(program):
    """Run the program and return (error text, pixels, text boxes, call counts)."""
    result = subprocess.run(["micropython", "-X", "heapsize=64M", "runprog.py", os.path.abspath(program)],
                            cwd=STANDINS, capture_output=True, text=True, timeout=600)
    with open(os.path.join(STANDINS, "out.txt")) as f:
        lines = f.read().splitlines()
    error = lines[0][4:]
    if error:
        error += "\n" + result.stdout.strip()[-600:]
    pixels, texts, calls = {}, [], ""
    for line in lines[1:]:
        if line.startswith("P "):
            _, x, y, r, g, b = line.split()
            pixels[(int(x), int(y))] = (int(r), int(g), int(b))
        elif line.startswith("T "):
            parts = line.split(" ", 5)
            texts.append((int(parts[1]), int(parts[2]), int(parts[3]), int(parts[4]), parts[5]))
        elif line.startswith("C "):
            calls = line[2:]
    return error, pixels, texts, calls


def main():
    args = sys.argv[1:]
    run_only = "--run-only" in args
    program = [a for a in args if not a.startswith("--")][0]
    name = os.path.basename(program)
    error, pixels, texts, calls = run(program)
    if error:
        print(f"{name}: FAIL - {error}")
        return 1
    if run_only:
        print(f"{name}: ran without errors")
        return 0
    expected = {p: triangle.COLORS[i] for p, i in triangle.expected().items()}
    missing = sum(p not in pixels for p in expected)
    wrong = sum(p in pixels and pixels[p] != expected[p] for p in expected)
    extra = sum(p not in expected for p in pixels)
    overlap = [t[4] for t in texts if any(t[0] <= x <= t[2] and t[1] <= y <= t[3] for (x, y) in expected)]
    ok = not (missing or wrong or extra or overlap)
    print(f"{name}: {'PASS' if ok else 'FAIL'} - missing {missing}, wrong {wrong}, extra {extra}, text overlap {overlap or 'none'}")
    print("  calls:", calls)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
