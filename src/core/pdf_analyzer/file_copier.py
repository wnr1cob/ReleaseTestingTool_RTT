"""
PDF file copy utility for the PDF Analyser.

Public API
----------
copy_pdfs(pdf_files, dest_dir, mode, on_progress)
    Copy a list of PDF files into *dest_dir* and return a summary dict.

load_canonical_map(config_path)
    Load {test_id: canonical_name} from a canonical_names.txt file.

smart_deduplicate(dest_dir, canonical_map, on_progress)
    Group PDFs in dest_dir by test ID, keep the best result, rename to
    the canonical name when available.
"""
import os
import re
import shutil
from typing import Callable

import pdfplumber


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

def _detect_result_priority(pdf_path: str) -> int:
    """Return the numeric priority (0-4) of the result found on page 2."""
    try:
        with pdfplumber.open(pdf_path) as pdf:
            if len(pdf.pages) < 2:
                return 0
            text = (pdf.pages[1].extract_text() or "").lower()
    except Exception:
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
    """Read *config_path* (canonical_names.txt) and return ``{test_id: canonical_name}``.

    Lines starting with ``#`` and blank lines are ignored.
    """
    canonical_map: dict[str, str] = {}
    if not os.path.isfile(config_path):
        return canonical_map
    with open(config_path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            test_id = _extract_test_id(line)
            if test_id:
                canonical_map[test_id] = line
    return canonical_map


def smart_deduplicate(
    dest_dir: str,
    canonical_map: dict[str, str],
    on_progress: Callable[[int, int, str], None] | None = None,
) -> dict:
    """Group PDFs in *dest_dir* by test ID, keep the best result, rename to canonical.

    For each group of files sharing the same test ID:
    - The file whose page-2 result has the highest priority
      (Passed=4 > Failed=3 > Error=2 > Undefined=1 > None=0) is kept.
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

    Returns
    -------
    dict
        ``{"removed": int, "renamed": int, "unmatched": int}``
    """
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
                priority = _detect_result_priority(os.path.join(dest_dir, fname))
                if priority > best_priority:
                    best_priority = priority
                    best_file = fname
            # Remove all losers
            for fname in files:
                if fname != best_file:
                    try:
                        os.remove(os.path.join(dest_dir, fname))
                        removed += 1
                    except Exception:
                        pass
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
                except Exception:
                    pass
        else:
            unmatched += 1

    return {"removed": removed, "renamed": renamed, "unmatched": unmatched}
