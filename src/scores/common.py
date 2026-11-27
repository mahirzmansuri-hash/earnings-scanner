"""Small helpers shared by all scores. Work on single numbers AND whole pandas columns."""
import numpy as np


def safe_div(a, b):
    """a / b, but give NaN (= 'unknown') instead of crashing or returning infinity when b is 0 or missing."""
    with np.errstate(divide="ignore", invalid="ignore"):
        out = np.divide(np.asarray(a, dtype=float), np.asarray(b, dtype=float))
    out = np.where(np.isfinite(out), out, np.nan)
    return out.item() if out.ndim == 0 else out


def zone(value, low: float, high: float):
    """'distress' below low, 'gray' from low to high (inclusive), 'safe' above high, None if unknown."""
    v = np.asarray(value, dtype=float)
    out = np.select([np.isnan(v), v > high, v >= low], [None, "safe", "gray"], default="distress").astype(object)
    out[np.isnan(v)] = None
    return out.item() if out.ndim == 0 else out


def test_or_nan(condition, *inputs):
    """1.0 if condition is true, 0.0 if false, NaN if any input needed for the test is missing."""
    known = np.all([~np.isnan(np.asarray(x, dtype=float)) for x in inputs], axis=0)
    return np.where(known, np.asarray(condition, dtype=float), np.nan)
