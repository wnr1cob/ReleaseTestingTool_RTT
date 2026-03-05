"""
Module Separator – organise PDFs from All_Available_Reports into
sub-folders based on the text before the first '-' in the filename.

Example
-------
    ABC-FC_Report.pdf  →  Module_Separated/ABC/ABC-FC_Report.pdf
    XYZ-01_Results.pdf →  Module_Separated/XYZ/XYZ-01_Results.pdf
"""

import os
import shutil
from typing import Callable


def separate_by_module(
    all_reports_dir: str,
    on_progress: Callable[[int, int, str], None] | None = None,
) -> dict:
    """
    Scan *all_reports_dir* for PDF files, parse the module prefix
    (text before the first ``-``), and move each file into
    ``<all_reports_dir>/Module_Separated/<prefix>/``.

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
            "modules": list[str],
            "dest_root": str,
        }
    """
    dest_root = os.path.join(all_reports_dir, "Module_Separated")
    os.makedirs(dest_root, exist_ok=True)

    moved = 0
    skipped = 0
    modules_seen: set[str] = set()

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

        # Find the first '-' in the filename (without extension)
        dash_index = filename.find("-")
        if dash_index <= 0:
            skipped += 1
            continue

        module_name = filename[:dash_index].strip()
        if not module_name:
            skipped += 1
            continue

        # Create the module sub-folder
        module_dir = os.path.join(dest_root, module_name)
        os.makedirs(module_dir, exist_ok=True)
        modules_seen.add(module_name)

        # Move the file into its module folder
        dest_path = os.path.join(module_dir, filename)

        # Handle duplicates inside the module folder
        if os.path.exists(dest_path):
            name, ext = os.path.splitext(filename)
            counter = 1
            while os.path.exists(dest_path):
                dest_path = os.path.join(module_dir, f"{name}_{counter}{ext}")
                counter += 1

        shutil.move(filepath, dest_path)
        moved += 1

    return {
        "moved": moved,
        "skipped": skipped,
        "modules": sorted(modules_seen),
        "dest_root": dest_root,
    }
