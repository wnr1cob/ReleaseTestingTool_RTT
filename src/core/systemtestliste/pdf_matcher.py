"""
PDF fuzzy-matching utilities for the SystemTestListe analyser.

Public API
----------
build_pdf_index(pdf_dir)
    Walk a directory tree and return ``[(name_no_ext, full_path), ...]``.

match_pdf_result(description, pdf_index, sw_name, variant, variant_map, min_score)
    Fuzzy-match one description to a PDF and return a result dict with
    keys ``result``, ``page3_sw``, ``page3_variant``.

match_all_rows(data_rows, pdf_index, sw_name, variant, variant_map, on_progress)
    Match every row and return a list of result dicts.
"""
import os
from typing import Callable

from .utils import extract_sw_name, extract_variant_from_swfl


# Result keywords in priority order – first match wins
KEYWORDS = ["passed", "failed", "error", "undefined", "not executed", "no result"]

# Minimum fuzzy-match score required to consider a PDF a match
MIN_SCORE: float = 0.95

# Empty page-3 extras (used as a default sentinel)
_NO_PAGE3 = {"page3_sw": "", "page3_variant": ""}


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


def _extract_page3_full(
    pdf_path: str,
    variant_map: dict[str, str],
    sw_page_idx: int = 2,
    result_page_idx: int = 2,
    variant_page_idx: int = 2,
    sw_patterns: list[str] | None = None,
    keywords: list[str] | None = None,
) -> dict[str, str]:
    """Extract result, SW name, and variant from the configured PDF pages.

    Parameters
    ----------
    result_page_idx : int
        0-based index of the page to search for result keywords (default 2).
    sw_page_idx : int
        0-based index of the page to read the SW name from (default 2).
    variant_page_idx : int
        0-based index of the page to scan for SWFL codes (default 2).
    keywords : list[str], optional
        Ordered lowercase keywords to match (from presets).  Falls back to
        the module-level :data:`KEYWORDS` when not provided.
    """
    _kws = keywords or KEYWORDS
    try:
        txt_result = _read_pdf_page(pdf_path, result_page_idx)
        t = txt_result.lower()
        found = next((kw for kw in _kws if kw in t), None)
        result = found.title() if found else (
            "Page" + str(result_page_idx + 1) + ": "
            + next((ln.strip() for ln in txt_result.splitlines() if ln.strip()), "No data")[:120]
        )

        txt_sw = _read_pdf_page(pdf_path, sw_page_idx)
        page3_sw = extract_sw_name(txt_sw, sw_patterns)

        txt_var = _read_pdf_page(pdf_path, variant_page_idx)
        page3_variant = extract_variant_from_swfl(txt_var, variant_map)

        return {"result": result, "page3_sw": page3_sw, "page3_variant": page3_variant}
    except Exception:
        return {"result": "No Result", "page3_sw": "", "page3_variant": ""}


# ═══════════════════════════════════════════════════════════════
# PUBLIC FUNCTIONS
# ═══════════════════════════════════════════════════════════════

def match_pdf_result(
    description: str,
    pdf_index: list[tuple[str, str]],
    sw_name: str = "",
    variant: str = "",
    variant_map: dict[str, str] | None = None,
    sw_patterns: list[str] | None = None,
    keywords: list[str] | None = None,
    result_page_idx: int = 2,
    sw_page_idx: int = 2,
    variant_page_idx: int = 2,
    min_score: float = MIN_SCORE,
) -> dict[str, str]:
    """Fuzzy-match *description* against *pdf_index* and extract test data.

    Parameters
    ----------
    keywords : list[str], optional
        Ordered lowercase result keywords from presets.
    result_page_idx : int
        0-based page index for result keyword search (default 2 = page 3).
    sw_page_idx : int
        0-based page index for SW-name extraction (default 2).
    variant_page_idx : int
        0-based page index for SWFL scanning (default 2).

    Returns
    -------
    dict
        ``{"result": str, "page3_sw": str, "page3_variant": str}``
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
        return {"result": "No report", **_NO_PAGE3}

    vm = variant_map or {}
    _kws = keywords or KEYWORDS

    if sw_name and variant:
        return _extract_page3_full(
            matched, vm,
            sw_page_idx=sw_page_idx,
            result_page_idx=result_page_idx,
            variant_page_idx=variant_page_idx,
            sw_patterns=sw_patterns,
            keywords=_kws,
        )

    if sw_name:
        try:
            txt_result = _read_pdf_page(matched, result_page_idx)
            found = next((kw for kw in _kws if kw in txt_result.lower()), None)
            result = found.title() if found else "No Result"
            txt_sw = _read_pdf_page(matched, sw_page_idx)
            page3_sw = extract_sw_name(txt_sw, sw_patterns)
        except Exception:
            result, page3_sw = "No Result", ""
        try:
            txt3 = _read_pdf_page(matched, variant_page_idx)
            page3_variant = extract_variant_from_swfl(txt3, vm)
        except Exception:
            page3_variant = ""
        return {"result": result, "page3_sw": page3_sw, "page3_variant": page3_variant}

    # No SW/variant context – result only
    try:
        txt = _read_pdf_page(matched, result_page_idx)
        found = next((kw for kw in _kws if kw in txt.lower()), None)
        return {"result": found.title() if found else "No Result", **_NO_PAGE3}
    except Exception:
        return {"result": "No Result", **_NO_PAGE3}


def match_all_rows(
    data_rows: list[list[str]],
    pdf_index: list[tuple[str, str]],
    sw_name: str = "",
    variant: str = "",
    variant_map: dict[str, str] | None = None,
    sw_patterns: list[str] | None = None,
    keywords: list[str] | None = None,
    result_page_idx: int = 2,
    sw_page_idx: int = 2,
    variant_page_idx: int = 2,
    min_score: float = MIN_SCORE,
    on_progress: Callable[[int, int, str], None] | None = None,
) -> list[dict[str, str]]:
    """Match every row in *data_rows* against *pdf_index*."""
    results: list[dict[str, str]] = []
    total = len(data_rows)

    for idx, row in enumerate(data_rows):
        description = row[1] if len(row) > 1 else ""
        match = match_pdf_result(
            description, pdf_index,
            sw_name=sw_name, variant=variant,
            variant_map=variant_map,
            sw_patterns=sw_patterns,
            keywords=keywords,
            result_page_idx=result_page_idx,
            sw_page_idx=sw_page_idx,
            variant_page_idx=variant_page_idx,
            min_score=min_score,
        )
        results.append(match)
        if on_progress:
            on_progress(idx + 1, total, match["result"])

    return results
