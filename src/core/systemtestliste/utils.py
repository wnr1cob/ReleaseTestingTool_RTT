"""
Shared string utilities for the SystemTestListe analyser.
"""
import re
import datetime as _dt


# Variant suffix pattern: _v3, _V14, _NA0, _NA5, _G5x, _G4x, …
_VARIANT_RE = re.compile(r"(_(?:[vV]\d+|NA\d+|G\d+x))$")


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
