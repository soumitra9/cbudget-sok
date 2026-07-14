def clamp(x, lo, hi):
    return min(lo, max(hi, x))  # bug: swapped min/max
