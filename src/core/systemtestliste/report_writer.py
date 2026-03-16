"""
Output Excel creation for the SystemTestListe analyser.

Public API
----------
write_stl_helper(output_dir, data_rows, pdf_results, output_cols, timestamp)
    Write the ``STL_Helper_<timestamp>.xlsx`` file and return its path.
"""
import os
from datetime import datetime


def write_stl_helper(
    output_dir: str,
    data_rows: list[list[str]],
    pdf_results: list[str],
    output_cols: list[str],
    timestamp: str | None = None,
) -> str:
    """Write the STL_Helper Excel file and return its absolute path.

    Parameters
    ----------
    output_dir : str
        Folder in which the file is saved.
    data_rows : list[list[str]]
        Baseline rows extracted from the STL sheet (ID, Description, Result, …).
    pdf_results : list[str]
        One PDF-result string per row in *data_rows* (same length).
    output_cols : list[str]
        Column headers for the first columns (without the ``PDFResult``
        column, which is appended automatically).
    timestamp : str, optional
        Timestamp suffix.  Defaults to ``YYYYMMDDHHMMSS`` of *now*.

    Returns
    -------
    str
        Absolute path to the saved ``.xlsx`` file.
    """
    import openpyxl

    if timestamp is None:
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")

    output_path = os.path.join(output_dir, f"STL_Helper_{timestamp}.xlsx")

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "MainSheet"

    # Header row
    ws.append(output_cols + ["PDFResult"])

    # Data rows – lengths must match; guard against silent truncation
    if len(data_rows) != len(pdf_results):
        raise ValueError(
            f"data_rows ({len(data_rows)}) and pdf_results ({len(pdf_results)}) "
            "must have the same length."
        )
    for row, pdf_result in zip(data_rows, pdf_results):
        ws.append(row + [pdf_result])

    wb.save(output_path)
    return output_path
