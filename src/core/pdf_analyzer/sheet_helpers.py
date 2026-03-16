"""
Worksheet helper utilities for the PDF Analyser report generator.

Functions
---------
_fill_range(ws, r1, r2, c1, c2, fill)
    Apply a fill to a rectangular cell range.

_auto_col_width(ws, col_letter, min_width)
    Auto-size a column to fit the longest value.

_extract_module(filename)
    Return the module name (text before the first ``-``), or
    ``'Unknown'``.
"""
import os


def _fill_range(ws, r1: int, r2: int, c1: int, c2: int, fill) -> None:
    """Apply *fill* to every cell in the rectangle [r1:r2, c1:c2]."""
    for r in range(r1, r2 + 1):
        for c in range(c1, c2 + 1):
            ws.cell(row=r, column=c).fill = fill


def _auto_col_width(ws, col_letter: str, min_width: float = 12) -> None:
    """Set the column width to fit the longest cell value (+ padding)."""
    max_len = min_width
    for cell in ws[col_letter]:
        if cell.value:
            max_len = max(max_len, len(str(cell.value)) + 4)
    ws.column_dimensions[col_letter].width = max_len


def _extract_module(filename: str) -> str:
    """Return the module name (text before the first ``-``), or ``'Unknown'``.

    Returns ``'Unknown'`` when *filename* has no ``-``, or when the prefix
    before the first ``-`` is empty (e.g. ``'-StartDash.pdf'``).
    """
    base = os.path.splitext(filename)[0]
    if "-" in base:
        prefix = base.split("-", 1)[0].strip()
        if prefix:
            return prefix
    return "Unknown"
