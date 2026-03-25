"""
Shared string utilities for the SystemTestListe analyser.
"""
import os
import re
import datetime as _dt


# Variant suffix pattern: _v3, _V14, _NA0, _NA5, _G5x, _G4x, …
_VARIANT_RE = re.compile(r"(_(?:[vV]\d+|NA\d+|G\d+x))$")

# SW Name pattern: NNN_NNN_*_NN_NN_ANN
# NNN = 3 digits, * = one non-whitespace/non-underscore token, ANN = 1 alpha + 2 digits
SW_NAME_RE = re.compile(r"\b(\d{3}_\d{3}_[^_\s]+_\d{2}_\d{2}_[A-Za-z]\d{2})\b")

# SWFL code pattern (e.g. SWFL-0000DE16)
_SWFL_RE = re.compile(r"\bSWFL-([0-9A-Fa-f]+)\b")

# Library version pattern – compiled once at module level (was compiled on every call)
_VER_RE = re.compile(r"[vV] ?\d+(?:\.\d+)?")

# Cache for user-supplied SW-pattern strings → compiled re.Pattern objects.
# Avoids re.compile() overhead on every extract_sw_name call when patterns are in use.
_SW_PATTERN_CACHE: dict[str, re.Pattern] = {}

# Default path to Variant_Info.txt (config/ at project root)
_CONFIG_DIR = os.path.normpath(
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "config")
)
VARIANT_INFO_PATH = os.path.join(_CONFIG_DIR, "Variant_Info.txt")


def parse_sw_variant(tab_name: str) -> tuple[str, str]:
    """Split a tab name into (sw_name, variant).

    Returns ``(tab_name, '')`` when no recognised variant suffix is
    present.

    Examples
    --------
    >>> parse_sw_variant("MySW_v3")
    ('MySW', 'v3')
    >>> parse_sw_variant("MySW")
    ('MySW', '')
    """
    m = _VARIANT_RE.search(tab_name)
    if m:
        variant = m.group(1).lstrip("_")
        sw = tab_name[: m.start()]
        return sw, variant
    return tab_name, ""


def cell_to_str(v) -> str:
    """Convert any Excel cell value to a clean string.

    * ``None`` / empty string → ``''``
    * ``float`` that is a whole number (e.g. ``42.0``) → ``'42'``
    * ``datetime`` / ``date`` → ISO-formatted string
    * Everything else → ``str(v).strip()``
    """
    if v is None or v == "":
        return ""
    if isinstance(v, float):
        return str(int(v)) if v == int(v) else str(v)
    if isinstance(v, (_dt.datetime, _dt.date)):
        return v.isoformat()
    return str(v).strip()


# ═══════════════════════════════════════════════════════════════
# VARIANT MAP  (Variant_Info.txt)
# ═══════════════════════════════════════════════════════════════

def load_variant_map(path: str | None = None) -> dict[str, str]:
    """Parse *Variant_Info.txt* and return ``{swfl_code_upper: variant}``

    File format (lines)::

        V35 - SWFL-0000DE16
        # comment lines and blank lines are ignored

    Parameters
    ----------
    path : str, optional
        Override the default ``config/Variant_Info.txt`` location.

    Returns
    -------
    dict[str, str]
        Keys are upper-cased SWFL codes (e.g. ``'SWFL-0000DE16'``),
        values are the variant labels (e.g. ``'V35'``).
    """
    mapping: dict[str, str] = {}
    fpath = path or VARIANT_INFO_PATH
    try:
        with open(fpath, encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                parts = line.split(" - ", 1)
                if len(parts) == 2:
                    variant_label = parts[0].strip()
                    swfl_code = parts[1].strip().upper()
                    # Multiple variants may share a SWFL; store first occurrence
                    mapping.setdefault(swfl_code, variant_label)
    except FileNotFoundError:
        pass
    return mapping


# ═══════════════════════════════════════════════════════════════
# PAGE-3 EXTRACTION HELPERS
# ═══════════════════════════════════════════════════════════════

def extract_sw_name(text: str, patterns: list[str] | None = None) -> str:
    """Return the first SW name found in *text*, or ``''`` if none found.

    Parameters
    ----------
    text : str
        Raw text extracted from the PDF page.
    patterns : list[str], optional
        Ordered list of regex strings (from presets) to try in sequence.
        Falls back to the built-in :data:`SW_NAME_RE` when not provided.
    """
    if patterns:
        for pat in patterns:
            try:
                # Use the module-level cache so each pattern string is compiled only once.
                compiled = _SW_PATTERN_CACHE.get(pat)
                if compiled is None:
                    compiled = re.compile(pat)
                    _SW_PATTERN_CACHE[pat] = compiled
                m = compiled.search(text)
                if m:
                    # Return the whole match (group 0); some patterns may
                    # use a capturing group – prefer group 1 if present.
                    return m.group(1) if m.lastindex else m.group(0)
            except re.error:
                pass
        return ""
    m = SW_NAME_RE.search(text)
    return m.group(1) if m else ""


def extract_variant_from_swfl(text: str, variant_map: dict[str, str]) -> str:
    """Return the variant label for the first SWFL code found in *text*.

    Uses *variant_map* (from :func:`load_variant_map`) to translate
    ``SWFL-XXXXXXXX`` → variant label (e.g. ``'V35'``).
    Returns ``''`` when no matching SWFL code is found.
    """
    for m in _SWFL_RE.finditer(text):
        code = f"SWFL-{m.group(1).upper()}"
        if code in variant_map:
            return variant_map[code]
    return ""


def extract_library_version(
    text: str,
    search_text: str = "Used version of custom library",
    version_pattern: str = r"[vV]\d+\.\d+",
) -> str | None:
    """Extract a library version string from *text*.

    Finds the line containing *search_text* (case-insensitive) and inspects
    that line plus the next 3 lines (4 lines total).  The first token that
    matches the pattern ``[vV] ?\\d+(\\.\\d+)?`` is returned, normalised to
    uppercase with any internal spaces removed (e.g. ``"V 2"`` → ``"V2"``).

    Parameters
    ----------
    text : str
        Raw text extracted from the PDF page.
    search_text : str
        Anchor phrase whose line starts the search window.
    version_pattern : str
        Unused – kept for API compatibility.

    Returns
    -------
    str | None
        Normalised version string (e.g. ``'V114.0'``) or ``None`` when not
        found.
    """
    if not text:
        return None

    # _VER_RE is now a module-level constant (compiled once, not per call).
    lines = text.splitlines()
    anchor_lower = search_text.lower()

    for i, line in enumerate(lines):
        if anchor_lower in line.lower():
            window = "\n".join(lines[i: i + 4])
            m = _VER_RE.search(window)
            if m:
                return m.group(0).replace(" ", "").upper()
            return None  # anchor found but no version in the 4-line window

    return None
