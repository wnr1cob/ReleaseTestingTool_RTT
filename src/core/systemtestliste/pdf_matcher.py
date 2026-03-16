"""
PDF fuzzy-matching utilities for the SystemTestListe analyser.

Public API
----------
build_pdf_index(pdf_dir)
    Walk a directory tree and return ``[(name_no_ext, full_path), ...]``.

match_pdf_result(description, pdf_index, sw_name, variant)
    Fuzzy-match one description to a PDF and return the result string.

match_all_rows(data_rows, pdf_index, sw_name, variant, on_progress)
    Match every row and return a list of result strings.
"""
import os
from typing import Callable


# Result keywords in priority order – first match wins
KEYWORDS = ["passed", "failed", "error", "undefined", "not executed", "no result"]

# Minimum fuzzy-match score required to consider a PDF a match
MIN_SCORE: float = 0.95


# ═══════════════════════════════════════════════════════════════
# HELPERS
# ═══════════════════════════════════════════════════════════════

def build_pdf_index(pdf_dir: str) -> list[tuple[str, str]]:
    """Walk *pdf_dir* recursively and collect all PDF paths.

    Returns
    -------
    list[tuple[str, str]]
        ``[(filename_without_extension, absolute_path), ...]``
    """
    index: list[tuple[str, str]] = []
    for root, _dirs, files in os.walk(pdf_dir):
        for f in files:
            if f.lower().endswith(".pdf"):
                name = os.path.splitext(f)[0]
                index.append((name, os.path.join(root, f)))
    return index


def _read_pdf_page(pdf_path: str, pref_idx: int) -> str:
    """Return text from *pref_idx* page of *pdf_path* (with fallback).

    Falls back to page 2 (index 1) then page 1 (index 0) when the
    preferred page does not exist.
    """
    import pdfplumber
    with pdfplumber.open(pdf_path) as pdf:
        if len(pdf.pages) > pref_idx:
            return pdf.pages[pref_idx].extract_text() or ""
        if len(pdf.pages) >= 2:
            return pdf.pages[1].extract_text() or ""
        if len(pdf.pages) >= 1:
            return pdf.pages[0].extract_text() or ""
    return ""


# ═══════════════════════════════════════════════════════════════
# PUBLIC FUNCTIONS
# ═══════════════════════════════════════════════════════════════

def match_pdf_result(
    description: str,
    pdf_index: list[tuple[str, str]],
    sw_name: str = "",
    variant: str = "",
    min_score: float = MIN_SCORE,
) -> str:
    """Fuzzy-match *description* against *pdf_index* and extract the test result.

    Parameters
    ----------
    description : str
        Description cell value from the STL row.
    pdf_index : list[tuple[str, str]]
        Output of :func:`build_pdf_index`.
    sw_name : str, optional
        SW name parsed from the selected tab (used to determine page).
    variant : str, optional
        Variant parsed from the selected tab (used to determine page).
    min_score : float
        Minimum fuzzy-match ratio to accept a match.

    Returns
    -------
    str
        One of: ``'Passed'``, ``'Failed'``, ``'Error'``, ``'Undefined'``,
        ``'Not Executed'``, ``'No Result'``, ``'No report'``,
        or a ``'Page3: …'`` excerpt.
    """
    from difflib import SequenceMatcher

    descr_norm = description.strip().lower()
    best: tuple[str | None, float] = (None, 0.0)

    for pname, ppath in pdf_index:
        score = SequenceMatcher(None, descr_norm, pname.lower()).ratio()
        if score > best[1]:
            best = (ppath, score)

    matched, score = best
    if not matched or score < min_score:
        return "No report"

    # Page index: SW+variant → page 3 (idx 2), SW only → page 2 (idx 1)
    pref_idx = 2 if (sw_name and variant) else 1

    try:
        txt = _read_pdf_page(matched, pref_idx)
        t = txt.lower()
        found = next((kw for kw in KEYWORDS if kw in t), None)

        if sw_name and variant:
            if found:
                return found.title()
            first_line = next(
                (ln.strip() for ln in txt.splitlines() if ln.strip()), ""
            )
            return (
                f"Page3: {first_line[:120]}" if first_line else "Page3: No data"
            )
        else:
            return found.title() if found else "No Result"
    except Exception:
        return "No Result"


def match_all_rows(
    data_rows: list[list[str]],
    pdf_index: list[tuple[str, str]],
    sw_name: str = "",
    variant: str = "",
    min_score: float = MIN_SCORE,
    on_progress: Callable[[int, int, str], None] | None = None,
) -> list[str]:
    """Match every row in *data_rows* against *pdf_index*.

    Parameters
    ----------
    data_rows : list[list[str]]
        Rows in ``[ID, Description, Result, …]`` order.
    pdf_index : list[tuple[str, str]]
        Output of :func:`build_pdf_index`.
    sw_name : str, optional
        SW name (affects which page is examined).
    variant : str, optional
        Variant string (affects which page is examined).
    min_score : float
        Minimum fuzzy-match ratio.
    on_progress : callable, optional
        ``on_progress(current, total, pdf_result)`` called after each row.

    Returns
    -------
    list[str]
        One result string per input row, in the same order.
    """
    results: list[str] = []
    total = len(data_rows)

    for idx, row in enumerate(data_rows):
        description = row[1] if len(row) > 1 else ""
        pdf_result = match_pdf_result(
            description, pdf_index, sw_name, variant, min_score
        )
        results.append(pdf_result)
        if on_progress:
            on_progress(idx + 1, total, pdf_result)

    return results
