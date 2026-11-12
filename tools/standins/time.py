"""Dry-run stand-in for the Evo's time module. The clock never advances, so timings read as zero."""
def monotonic(): return 0.0
