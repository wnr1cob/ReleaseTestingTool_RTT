# Utility functions and helpers


def fmt_elapsed(seconds: float) -> str:
    """Format elapsed seconds as a human-readable duration string.

    < 60 s        ->  "12.3s"
    60 s - 1 h    ->  "2m 05s"
    >= 1 h        ->  "1h 02m 09s"
    """
    s = int(seconds)
    if s < 60:
        return f"{seconds:.1f}s"
    m, s = divmod(s, 60)
    if m < 60:
        return f"{m}m {s:02d}s"
    h, m = divmod(m, 60)
    return f"{h}h {m:02d}m {s:02d}s"
