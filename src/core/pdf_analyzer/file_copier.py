"""
PDF file copy utility for the PDF Analyser.

Public API
----------
copy_pdfs(pdf_files, dest_dir, mode, on_progress)
    Copy a list of PDF files into *dest_dir* and return a summary dict.

load_canonical_map(config_path)
    Load {test_id: canonical_name} from canonical_names.json (or .txt with
    auto-migration to JSON on first use).

smart_deduplicate(dest_dir, canonical_map, on_progress)
    Group PDFs in dest_dir by test ID, keep the best result, rename to
    the canonical name when available.
"""
import json
import logging
import os
import re
import shutil
from typing import Callable

import pdfplumber

logger = logging.getLogger(__name__)


# ── Result priority (higher = better) ──────────────────────────────────────
_RESULT_PRIORITY: dict[str, int] = {
    "Passed":    4,
    "Failed":    3,
    "Error":     2,
    "Undefined": 1,
}


def copy_pdfs(
    pdf_files: list[str],
    dest_dir: str,
    mode: str = "copy_duplicates",
    on_progress: Callable[[int, int], None] | None = None,
    canonical_map: dict[str, str] | None = None,
) -> dict:
    """Copy *pdf_files* into *dest_dir*, handling duplicates according to *mode*.

    Parameters
    ----------
    pdf_files : list[str]
        Absolute paths to the source PDF files.
    dest_dir : str
        Destination folder (created when missing).
    mode : {'copy_duplicates', 'ignore_duplicates'}
        ``'copy_duplicates'``  – rename the destination copy with a
        ``_Dup`` / ``_Dup<n>`` suffix when a file already exists.

        ``'ignore_duplicates'`` – skip the file entirely when it already
        exists in *dest_dir*.
    on_progress : callable, optional
        ``on_progress(processed, total)`` called after each file is
        handled (whether copied or skipped).
    canonical_map : dict, optional
        ``{test_id: canonical_name}`` as returned by
        :func:`load_canonical_map`.  When provided, the destination
        filename is resolved to the canonical name before any duplicate
        handling.  Duplicates are then suffixed as
        ``<canonical_name>_Dup.pdf``, ``<canonical_name>_Dup1.pdf``, …

    Returns
    -------
    dict
        ``{"copied": int, "skipped": int}``
    """
    os.makedirs(dest_dir, exist_ok=True)

    total = len(pdf_files)
    copied = 0
    skipped = 0

    for i, pdf_path in enumerate(pdf_files, start=1):
        filename = os.path.basename(pdf_path)

        # Resolve destination base name via canonical map if provided
        if canonical_map:
            stem = os.path.splitext(filename)[0]
            tid  = _extract_test_id(stem)
            canonical = canonical_map.get(tid) if tid else None
            dest_filename = (canonical + ".pdf") if canonical else filename
        else:
            dest_filename = filename

        dest_path = os.path.join(dest_dir, dest_filename)

        if os.path.exists(dest_path):
            if mode == "ignore_duplicates":
                skipped += 1
                if on_progress:
                    on_progress(i, total)
                continue
            else:  # copy_duplicates
                name, ext = os.path.splitext(dest_filename)
                dest_path = os.path.join(dest_dir, f"{name}_Dup{ext}")
                counter = 1
                while os.path.exists(dest_path):
                    dest_path = os.path.join(dest_dir, f"{name}_Dup{counter}{ext}")
                    counter += 1

        shutil.copy2(pdf_path, dest_path)
        copied += 1

        if on_progress:
            on_progress(i, total)

    return {"copied": copied, "skipped": skipped}


# ── Helpers for smart deduplication ────────────────────────────────────────

def _detect_result_priority(pdf_path: str, page_idx: int = 1) -> int:
    """Return the numeric priority (0-4) of the result found on *page_idx* (0-based)."""
    if page_idx < 0:
        return 0
    try:
        with pdfplumber.open(pdf_path) as pdf:
            if len(pdf.pages) <= page_idx:
                return 0
            text = (pdf.pages[page_idx].extract_text() or "").lower()
    except (OSError, IOError, ValueError) as exc:
        logger.warning("Cannot read %s for result priority: %s", pdf_path, exc)
        return 0
    except Exception as exc:
        logger.warning("Unexpected error reading %s: %s", pdf_path, exc)
        return 0

    for keyword, priority in sorted(_RESULT_PRIORITY.items(), key=lambda x: -x[1]):
        if keyword.lower() in text:
            return priority
    return 0


def _extract_test_id(filename: str) -> str | None:
    """Extract the test ID from a filename.

    The test ID is the first underscore-delimited token whose last
    hyphen-separated segment is purely numeric.

    Examples
    --------
    'DPSDC-FC-HILTS-1669_CloudDataCollector_TBT.pdf'  →  'DPSDC-FC-HILTS-1669'
    'Report_NoID.pdf'                                  →  None
    """
    name = os.path.splitext(filename)[0]
    first_token = name.split("_")[0]
    parts = first_token.split("-")
    if len(parts) >= 2 and parts[-1].isdigit():
        return first_token
    return None


def load_canonical_map(config_path: str) -> dict[str, str]:
    """Return ``{test_id: canonical_name}`` from *config_path*.

    Accepts two formats
    -------------------
    ``.json``  (preferred) – a ``{test_id: full_name}`` dict stored as JSON.
    ``.txt``   (legacy)    – one name per line, ``#`` lines ignored.

    Auto-migration
    --------------
    When *config_path* ends with ``.json`` but only the old ``.txt``
    sibling exists, the .txt is read, converted to JSON and written to
    the .json path automatically.  The original .txt is kept as
    ``canonical_names.txt.bak`` so nothing is lost.
    """
    canonical_map: dict[str, str] = {}

    json_path = config_path if config_path.endswith(".json") else None
    txt_path  = (
        os.path.splitext(config_path)[0] + ".txt"
        if config_path.endswith(".json")
        else config_path
    )

    # ── Try reading JSON first ──────────────────────────────────
    if json_path and os.path.isfile(json_path):
        try:
            with open(json_path, encoding="utf-8") as fh:
                data = json.load(fh)
            if isinstance(data, dict):
                return {str(k): str(v) for k, v in data.items()}
        except (json.JSONDecodeError, OSError):
            pass  # fall through to txt

    # ── Fall back to .txt (and auto-migrate if json_path is set) ─
    if not os.path.isfile(txt_path):
        return canonical_map

    with open(txt_path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            test_id = _extract_test_id(line)
            if test_id:
                canonical_map[test_id] = line

    # Auto-migrate: write JSON and rename .txt → .txt.bak
    if json_path and canonical_map:
        try:
            os.makedirs(os.path.dirname(json_path) or ".", exist_ok=True)
            with open(json_path, "w", encoding="utf-8") as fh:
                json.dump(canonical_map, fh, indent=4, ensure_ascii=False)
            bak_path = txt_path + ".bak"
            if not os.path.exists(bak_path):
                shutil.copy2(txt_path, bak_path)
        except OSError:
            pass  # migration is best-effort; original .txt still works

    return canonical_map


def smart_deduplicate(
    dest_dir: str,
    canonical_map: dict[str, str],
    on_progress: Callable[[int, int, str], None] | None = None,
    result_page_idx: int | None = None,
) -> dict:
    """Group PDFs in *dest_dir* by test ID, keep the best result, rename to canonical.

    For each group of files sharing the same test ID:
    - The file whose result page (from ``result_extraction.page`` in presets)
      has the highest priority (Passed=4 > Failed=3 > Error=2 > Undefined=1 > None=0) is kept.
    - All other files in the group are deleted.
    - The winner is renamed to ``<canonical_name>.pdf`` when the test ID
      is found in *canonical_map*; otherwise its original filename is kept.

    Parameters
    ----------
    dest_dir : str
        Folder to scan (typically ``All_Available_Reports``).
    canonical_map : dict[str, str]
        ``{test_id: canonical_name}`` as returned by :func:`load_canonical_map`.
    on_progress : callable, optional
        ``on_progress(current, total, test_id)`` called after each group.
    result_page_idx : int, optional
        0-based page index to read for the result keyword.  When ``None``
        (default), the value is taken from ``result_extraction.page`` in
        ``config/presets.json``.

    Returns
    -------
    dict
        ``{"removed": int, "renamed": int, "unmatched": int}``
    """
    if result_page_idx is None:
        from src.core.systemtestliste.presets import load_presets as _load_presets
        _presets = _load_presets()
        result_page_idx = _presets["result_extraction"]["page"] - 1  # convert 1-based → 0-based

    pdf_files = [
        f for f in os.listdir(dest_dir)
        if f.lower().endswith(".pdf") and os.path.isfile(os.path.join(dest_dir, f))
    ]

    # Group by test ID
    groups: dict[str, list[str]] = {}
    for fname in pdf_files:
        tid = _extract_test_id(fname)
        if tid:
            groups.setdefault(tid, []).append(fname)

    removed = 0
    renamed = 0
    unmatched = 0
    total = len(groups)

    for idx, (test_id, files) in enumerate(groups.items(), start=1):
        if on_progress:
            on_progress(idx, total, test_id)

        # Pick the winner
        if len(files) == 1:
            winner = files[0]
        else:
            best_file = files[0]
            best_priority = -1
            for fname in files:
                priority = _detect_result_priority(os.path.join(dest_dir, fname), page_idx=result_page_idx)
                if priority > best_priority:
                    best_priority = priority
                    best_file = fname
            # Remove all losers
            for fname in files:
                if fname != best_file:
                    try:
                        os.remove(os.path.join(dest_dir, fname))
                        removed += 1
                    except OSError as exc:
                        logger.warning("Failed to remove duplicate %s: %s", fname, exc)
            winner = best_file

        # Rename to canonical if available
        canonical = canonical_map.get(test_id)
        if canonical:
            new_name = canonical + ".pdf"
            old_path = os.path.join(dest_dir, winner)
            new_path = os.path.join(dest_dir, new_name)
            if os.path.normcase(old_path) != os.path.normcase(new_path):
                try:
                    os.rename(old_path, new_path)
                    renamed += 1
                except OSError as exc:
                    logger.warning("Failed to rename %s → %s: %s", winner, new_name, exc)
        else:
            unmatched += 1

    return {"removed": removed, "renamed": renamed, "unmatched": unmatched}
