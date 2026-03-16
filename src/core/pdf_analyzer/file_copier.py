"""
PDF file copy utility for the PDF Analyser.

Public API
----------
copy_pdfs(pdf_files, dest_dir, mode, on_progress)
    Copy a list of PDF files into *dest_dir* and return a summary dict.
"""
import os
import shutil
from typing import Callable


def copy_pdfs(
    pdf_files: list[str],
    dest_dir: str,
    mode: str = "copy_duplicates",
    on_progress: Callable[[int, int], None] | None = None,
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
        dest_path = os.path.join(dest_dir, filename)

        if os.path.exists(dest_path):
            if mode == "ignore_duplicates":
                skipped += 1
                if on_progress:
                    on_progress(i, total)
                continue
            else:  # copy_duplicates
                name, ext = os.path.splitext(filename)
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
