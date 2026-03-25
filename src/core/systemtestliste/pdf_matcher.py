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
import gc
import os
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Callable

from .utils import extract_sw_name, extract_variant_from_swfl, extract_library_version

# Number of parallel PDF workers.  Capped at 8 to avoid overwhelming the OS
# file-handle limit; pdfplumber I/O releases the GIL so threads help here.
_MAX_WORKERS: int = min(8, (os.cpu_count() or 4))


# Result keywords in priority order – first match wins
KEYWORDS = ["passed", "failed", "error", "undefined", "not executed", "no result"]

# Minimum fuzzy-match score required to consider a PDF a match
MIN_SCORE: float = 0.95

# Empty page-3 extras (used as a default sentinel)
_NO_PAGE3 = {"page3_sw": "", "page3_variant": "", "library_version": ""}


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


def _read_pdf_pages(pdf_path: str, page_indices: list[int]) -> dict[int, str]:
    """Open *pdf_path* once and return text for every requested page index.

    De-duplicates indices so each page is extracted only once.  Falls back
    gracefully when a page does not exist.

    Returns
    -------
    dict[int, str]
        Mapping of requested index → extracted text (empty string on failure).
    """
    import pdfplumber
    unique = sorted(set(page_indices))
    texts: dict[int, str] = {idx: "" for idx in page_indices}
    try:
        with pdfplumber.open(pdf_path) as pdf:
            n = len(pdf.pages)
            for idx in unique:
                if idx < n:
                    texts[idx] = pdf.pages[idx].extract_text() or ""
                elif n >= 2:
                    texts[idx] = pdf.pages[1].extract_text() or ""
                elif n >= 1:
                    texts[idx] = pdf.pages[0].extract_text() or ""
    except Exception:
        pass
    return texts


def _read_pdf_page(pdf_path: str, pref_idx: int) -> str:
    """Convenience wrapper – read a single page (opens the PDF once)."""
    return _read_pdf_pages(pdf_path, [pref_idx])[pref_idx]


def _extract_page3_full(
    pdf_path: str,
    variant_map: dict[str, str],
    sw_page_idx: int = 2,
    result_page_idx: int = 2,
    variant_page_idx: int = 2,
    library_page_idx: int = 2,
    sw_patterns: list[str] | None = None,
    keywords: list[str] | None = None,
    library_search_text: str = "",
    library_version_pattern: str = r"[vV]\d+\.\d+",
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
        # Open the PDF once and read all required pages in a single pass
        needed = list({result_page_idx, sw_page_idx, variant_page_idx, library_page_idx})
        pages  = _read_pdf_pages(pdf_path, needed)

        txt_result = pages[result_page_idx]
        t = txt_result.lower()
        found = next((kw for kw in _kws if kw in t), None)
        result = found.title() if found else (
            "Page" + str(result_page_idx + 1) + ": "
            + next((ln.strip() for ln in txt_result.splitlines() if ln.strip()), "No data")[:120]
        )

        page3_sw      = extract_sw_name(pages[sw_page_idx], sw_patterns)
        page3_variant = extract_variant_from_swfl(pages[variant_page_idx], variant_map)

        library_version = ""
        if library_search_text:
            library_version = extract_library_version(
                pages[library_page_idx], library_search_text, library_version_pattern
            ) or ""

        return {
            "result": result,
            "page3_sw": page3_sw,
            "page3_variant": page3_variant,
            "library_version": library_version,
        }
    except Exception:
        return {"result": "No Result", "page3_sw": "", "page3_variant": "", "library_version": ""}


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
    library_page_idx: int = 2,
    library_search_text: str = "",
    library_version_pattern: str = r"[vV]\d+\.\d+",
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
    library_page_idx : int
        0-based page index for library version extraction (default 2).
    library_search_text : str
        Anchor phrase to locate the library version block.
    library_version_pattern : str
        Regex for the version value.

    Returns
    -------
    dict
        ``{"result": str, "page3_sw": str, "page3_variant": str, "library_version": str}``
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
            library_page_idx=library_page_idx,
            sw_patterns=sw_patterns,
            keywords=_kws,
            library_search_text=library_search_text,
            library_version_pattern=library_version_pattern,
        )

    if sw_name:
        try:
            needed = list({result_page_idx, sw_page_idx, variant_page_idx,
                           *([library_page_idx] if library_search_text else [])})
            pages  = _read_pdf_pages(matched, needed)
            found  = next((kw for kw in _kws if kw in pages[result_page_idx].lower()), None)
            result = found.title() if found else "No Result"
            page3_sw      = extract_sw_name(pages[sw_page_idx], sw_patterns)
            page3_variant = extract_variant_from_swfl(pages[variant_page_idx], vm)
            library_version = ""
            if library_search_text:
                library_version = extract_library_version(
                    pages[library_page_idx], library_search_text, library_version_pattern
                ) or ""
        except Exception:
            result, page3_sw, page3_variant, library_version = "No Result", "", "", ""
        return {
            "result": result,
            "page3_sw": page3_sw,
            "page3_variant": page3_variant,
            "library_version": library_version,
        }

    # No SW/variant context – result only
    try:
        needed = list({result_page_idx, *([library_page_idx] if library_search_text else [])})
        pages  = _read_pdf_pages(matched, needed)
        found  = next((kw for kw in _kws if kw in pages[result_page_idx].lower()), None)
        library_version = ""
        if library_search_text:
            library_version = extract_library_version(
                pages[library_page_idx], library_search_text, library_version_pattern
            ) or ""
        return {
            "result": found.title() if found else "No Result",
            **{k: v for k, v in _NO_PAGE3.items() if k != "library_version"},
            "library_version": library_version,
        }
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
    library_page_idx: int = 2,
    library_search_text: str = "",
    library_version_pattern: str = r"[vV]\d+\.\d+",
    min_score: float = MIN_SCORE,
    on_progress: Callable[[int, int, str], None] | None = None,
) -> list[dict[str, str]]:
    """Match every row in *data_rows* against *pdf_index* using parallel workers.

    PDFs are processed concurrently (up to :data:`_MAX_WORKERS` threads).
    Result order always matches the input row order regardless of completion
    order.  The *on_progress* callback is invoked in a thread-safe manner as
    each PDF finishes.
    """
    total = len(data_rows)
    # Pre-allocate to preserve input order
    results: list[dict[str, str]] = [{}] * total

    _lock = threading.Lock()
    _completed = [0]  # mutable counter shared across worker threads

    def _process(row_idx: int, row: list[str]) -> tuple[int, dict[str, str]]:
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
            library_page_idx=library_page_idx,
            library_search_text=library_search_text,
            library_version_pattern=library_version_pattern,
            min_score=min_score,
        )
        # Free pdfplumber page objects and extracted text immediately
        gc.collect()
        return row_idx, match

    with ThreadPoolExecutor(max_workers=_MAX_WORKERS) as executor:
        futures = {
            executor.submit(_process, idx, row): idx
            for idx, row in enumerate(data_rows)
        }
        for future in as_completed(futures):
            row_idx, match = future.result()
            results[row_idx] = match
            if on_progress:
                with _lock:
                    _completed[0] += 1
                    count = _completed[0]
                on_progress(count, total, match["result"])

    # Final collect after all workers are done
    gc.collect()
    return results
