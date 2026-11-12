#!/bin/sh
# Runs every calculator program on this computer under MicroPython with the stand-in TI modules.
# The triangle programs must draw the exact picture; benchmarks and probes only have to finish.
set -e
cd "$(dirname "$0")/.."
for p in programs/*.py; do python3 tools/validate.py "$p"; done
for p in benchmarks/*.py probes/*.py; do python3 tools/validate.py --run-only "$p"; done
python3 -m unittest discover -s tools -p 'test_*.py'
