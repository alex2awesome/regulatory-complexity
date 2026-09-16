"""Optional native scheduling kernel; the NumPy path remains available.

No fast-math or parallel reductions: preserve the same max/add schedule exactly.
Numba is optional and does not change the statistical model or RNG stream.
"""
import numpy as np

try:
    from numba import njit
    import numba
except ImportError:
    njit = None
    numba = None


def schedule_loop(durations, mask, order, parent_ptr, parent_index):
    rows, n = mask.shape
    ends = np.zeros((rows, n), dtype=np.float64)
    for position in range(n):
        step = order[position]
        for row in range(rows):
            begin = 0.
            for k in range(parent_ptr[step], parent_ptr[step + 1]):
                begin = max(begin, ends[row, parent_index[k]])
            ends[row, step] = begin + durations[row, step] * mask[row, step]
    return ends


schedule_native = njit(cache=True)(schedule_loop) if njit is not None else None
ACCELERATOR = f'numba/{numba.__version__}' if numba is not None else 'numpy'
