"""
Result Separator – organise PDFs from All_Available_Reports into
sub-folders based on the test result found on the second page.

The second page of each PDF is read and searched for one of:
    Passed, Failed, Error, Undefined

The PDF is then moved into the matching sub-folder under
``<all_reports_dir>/Result_Separated/<result>/``.

Example
-------
    Report_A.pdf  (page 2 contains "Passed")  →  Result_Separated/Passed/Report_A.pdf
    Report_B.pdf  (page 2 contains "Failed")  →  Result_Separated/Failed/Report_B.pdf
"""

import os
import shutil
from typing import Callable

import pdfplumber


# Priority order – first match wins when a page contains multiple keywords
_RESULT_KEYWORDS = ["Passed", "Failed", "Error", "Undefined"]


def _detect_result(pdf_path: str) -> str | None:
    """
    Open *pdf_path*, read the **second page**, and return the first
    matching result keyword found, or ``None`` if nothing matches.
    """
    try:
        with pdfplumber.open(pdf_path) as pdf:
            if len(pdf.pages) < 2:
                return None
            page_text = pdf.pages[1].extract_text() or ""
    except Exception:
        return None

    # Case-insensitive search, but return the canonical keyword
    text_lower = page_text.lower()
    for keyword in _RESULT_KEYWORDS:
        if keyword.lower() in text_lower:
            return keyword

    return None


def separate_by_result(
    all_reports_dir: str,
    on_progress: Callable[[int, int, str], None] | None = None,
) -> dict:
    """
    Scan *all_reports_dir* for PDF files, read page 2 of each,
    detect the test result, and move the file into
    ``<all_reports_dir>/Result_Separated/<result>/``.

    Parameters
    ----------
    all_reports_dir : str
        Path to the ``All_Available_Reports`` folder.
    on_progress : callable, optional
        ``on_progress(current, total, filename)`` called after each file
        is processed so the caller can update a progress bar.

    Returns
    -------
    dict
        {
            "moved": int,
            "skipped": int,
            "results": dict[str, int],
            "file_results": list[dict],
            "dest_root": str,
        }
    """
    dest_root = os.path.join(all_reports_dir, "Result_Separated")
    os.makedirs(dest_root, exist_ok=True)

    moved = 0
    skipped = 0
    results_count: dict[str, int] = {}
    file_results: list[dict[str, str]] = []

    # Collect PDF list first so we know the total
    pdf_files = [
        f for f in os.listdir(all_reports_dir)
        if os.path.isfile(os.path.join(all_reports_dir, f))
        and f.lower().endswith(".pdf")
    ]
    total = len(pdf_files)

    for idx, filename in enumerate(pdf_files, start=1):
        filepath = os.path.join(all_reports_dir, filename)

        if on_progress:
            on_progress(idx, total, filename)

        result = _detect_result(filepath)
        if result is None:
            skipped += 1
            file_results.append({"name": filename, "result": "Unknown"})
            continue

        # Create the result sub-folder
        result_dir = os.path.join(dest_root, result)
        os.makedirs(result_dir, exist_ok=True)

        # Move the file
        dest_path = os.path.join(result_dir, filename)

        # Handle duplicates inside the result folder
        if os.path.exists(dest_path):
            name, ext = os.path.splitext(filename)
            counter = 1
            while os.path.exists(dest_path):
                dest_path = os.path.join(result_dir, f"{name}_{counter}{ext}")
                counter += 1

        shutil.move(filepath, dest_path)
        moved += 1
        results_count[result] = results_count.get(result, 0) + 1
        file_results.append({"name": filename, "result": result})

    return {
        "moved": moved,
        "skipped": skipped,
        "results": results_count,
        "file_results": file_results,
        "dest_root": dest_root,
    }
