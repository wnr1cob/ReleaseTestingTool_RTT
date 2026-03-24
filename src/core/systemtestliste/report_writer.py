"""
Output Excel creation for the SystemTestListe analyser.

Public API
----------
write_stl_helper(output_dir, data_rows, pdf_results, output_cols, timestamp, ...)
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
    *,
    match_flags: list[bool] | None = None,
    page3_sw_list: list[str] | None = None,
    sw_match_flags: list[bool] | None = None,
    page3_variant_list: list[str] | None = None,
    variant_match_flags: list[bool] | None = None,
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
    match_flags : list[bool], optional
        Result-match flag per row (adds ``ResultMatch`` column when provided).
    page3_sw_list : list[str], optional
        SW name extracted from page 3 per row (adds ``Page3_SW`` column).
    sw_match_flags : list[bool], optional
        Whether the selected SW matches page 3 (adds ``SWMatch`` column).
    page3_variant_list : list[str], optional
        Variant extracted from SWFL on page 3 per row (adds ``Page3_Variant``).
    variant_match_flags : list[bool], optional
        Whether the selected variant matches page 3 (adds ``VariantMatch``).

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

    # ── Build header ────────────────────────────────────────────
    headers = list(output_cols) + ["PDFResult"]
    if match_flags is not None:
        headers.append("ResultMatch")
    if page3_sw_list is not None:
        headers.append("Page3_SW")
    if sw_match_flags is not None:
        headers.append("SWMatch")
    if page3_variant_list is not None:
        headers.append("Page3_Variant")
    if variant_match_flags is not None:
        headers.append("VariantMatch")
    ws.append(headers)

    # ── Data rows ───────────────────────────────────────────────
    if len(data_rows) != len(pdf_results):
        raise ValueError(
            f"data_rows ({len(data_rows)}) and pdf_results ({len(pdf_results)}) "
            "must have the same length."
        )

    for i, (row, pdf_result) in enumerate(zip(data_rows, pdf_results)):
        data = list(row) + [pdf_result]
        if match_flags is not None:
            data.append("✓" if match_flags[i] else "✗")
        if page3_sw_list is not None:
            data.append(page3_sw_list[i])
        if sw_match_flags is not None:
            data.append("✓" if sw_match_flags[i] else "✗")
        if page3_variant_list is not None:
            data.append(page3_variant_list[i])
        if variant_match_flags is not None:
            data.append("✓" if variant_match_flags[i] else "✗")
        ws.append(data)

    wb.save(output_path)
    return output_path
