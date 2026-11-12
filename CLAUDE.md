# Project instructions

Python programs for the TI-84 Evo, plus computer-side tools that check them. Read `README.md` first: it records the calculator's measured behavior, which is not documented anywhere else.

## Calculator programs

- They run on TI's MicroPython build (Python 3.4 syntax, about 163 KB of memory, few modules). No f-strings, no `os`, no files.
- Program names on the calculator are at most 8 letters and digits. Name the file to match.
- Keep hot loops inside a function and bind calls to local names; locals are much faster than globals.
- Planning must stay small: the calculator has about 150 KB free and the planner once filled it. Drop data as soon as it is no longer needed, and keep the 200k heap test in `tools/test_tools.py` passing.
- Every drawing call costs 4 to 6 ms. Count calls before changing a drawing strategy; `tools/validate.py` prints the counts.
- `programs/PASFAST2.py` uses only documented calls. Keep it that way; undocumented calls belong in `PASFAST3.py` and later, and in the probes.
- A new undocumented call must be probed on the calculator before a program relies on it. Add what the probe finds to `README.md` and to the stand-ins in `tools/standins/`.

## Before uploading

- Run `sh tools/check.sh`. Triangle programs must pass pixel for pixel; benchmarks and probes must run without errors.
- A pass on the computer is not proof: the stand-ins do not model memory or timing.

## Talking to the calculator

- While a program is on screen, send nothing but screenshots. A file listing sent during a program's final screen was followed by a RAM clear. Check with `tools/screen_kind.py` first.
- Never send an OS update.
- Take no screenshots while a program is being timed; each one slows it by about 0.2 s. Wait until it must have finished, then take one.
- Programs live in RAM and a RAM clear removes them. Anything on the calculator that is not in this repo should be saved before running a probe.
- Stored programs appear to share memory with the running one. A `MemoryError` before anything is drawn usually means too much is stored: replace finished probes with a one-line file of the same name, and keep a new program's source under about 10 KB.

## Conventions

- Tools use only the Python standard library.
- Markdown paragraphs are single long lines; do not hard-wrap.
