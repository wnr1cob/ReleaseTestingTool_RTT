"""
Presets load / save helpers for the SystemTestListe analyser.

Presets are stored in ``config/presets.json`` and contain:

  sw_extraction
    page     – 1-based page number to extract the SW name from.
    patterns – list of {label, regex} dicts (tried in order).

  result_extraction
    page     – 1-based page number to find result keywords on.
    keywords – ordered list of keyword strings to search for.

  variant_extraction
    page     – 1-based page number to scan for SWFL codes.
    entries  – list of {variant, swfl} dicts mapping SWFL codes to variant
               labels (e.g. V35 ↔ SWFL-0000DE16).

Public API
----------
load_presets(path) → dict
save_presets(presets, path)
variant_map_from_presets(presets) → dict[str, str]   # {SWFL_UPPER: variant}
sw_patterns_from_presets(presets)  → list[str]       # regex strings
result_keywords_from_presets(presets) → list[str]    # keyword strings (lowercase)
"""
import copy
import json
import os
import re

# ── default location ────────────────────────────────────────────
_CONFIG_DIR = os.path.normpath(
    os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "..", "..", "..", "config",
    )
)
PRESETS_PATH = os.path.join(_CONFIG_DIR, "presets.json")

# ── canonical defaults (used when file is missing / corrupt) ───
DEFAULT_PRESETS: dict = {
    "sw_extraction": {
        "page": 3,
        "patterns": [
            {
                "label": "Default SW Pattern",
                "regex": r"\d{3}_\d{3}_[^_\s]+_\d{2}_\d{2}_[A-Za-z]\d{2}",
            }
        ],
    },
    "result_extraction": {
        "page": 3,
        "keywords": ["passed", "failed", "error", "undefined", "not executed", "no result"],
    },
    "variant_extraction": {
        "page": 3,
        "entries": [],
    },
}


# ═══════════════════════════════════════════════════════════════
# I/O
# ═══════════════════════════════════════════════════════════════

def load_presets(path: str | None = None) -> dict:
    """Load presets from *path* (default: ``config/presets.json``).

    Falls back to :data:`DEFAULT_PRESETS` on any I/O or JSON error.
    The returned dict is always a deep copy so callers may mutate it
    freely without affecting the cached defaults.
    """
    fpath = path or PRESETS_PATH
    try:
        with open(fpath, encoding="utf-8") as fh:
            data = json.load(fh)
        # Merge with defaults to handle partial / old files gracefully
        result = copy.deepcopy(DEFAULT_PRESETS)
        if "sw_extraction" in data:
            result["sw_extraction"].update(data["sw_extraction"])
        if "result_extraction" in data:
            result["result_extraction"].update(data["result_extraction"])
        if "variant_extraction" in data:
            result["variant_extraction"].update(data["variant_extraction"])
        return result
    except (FileNotFoundError, json.JSONDecodeError, KeyError):
        return copy.deepcopy(DEFAULT_PRESETS)


def save_presets(presets: dict, path: str | None = None) -> None:
    """Persist *presets* to *path* (default: ``config/presets.json``)."""
    fpath = path or PRESETS_PATH
    os.makedirs(os.path.dirname(fpath), exist_ok=True)
    with open(fpath, "w", encoding="utf-8") as fh:
        json.dump(presets, fh, indent=2, ensure_ascii=False)


# ═══════════════════════════════════════════════════════════════
# HELPERS – derive runtime objects from a presets dict
# ═══════════════════════════════════════════════════════════════

def variant_map_from_presets(presets: dict) -> dict[str, str]:
    """Return ``{SWFL_UPPER: variant_label}`` from presets.

    When multiple entries share the same SWFL code the first one wins.
    """
    vm: dict[str, str] = {}
    for entry in presets.get("variant_extraction", {}).get("entries", []):
        swfl = entry.get("swfl", "").strip().upper()
        variant = entry.get("variant", "").strip()
        if swfl and variant:
            vm.setdefault(swfl, variant)
    return vm


def sw_patterns_from_presets(presets: dict) -> list[str]:
    """Return a list of regex strings from the SW patterns in *presets*."""
    return [
        p["regex"]
        for p in presets.get("sw_extraction", {}).get("patterns", [])
        if p.get("regex")
    ]


def result_keywords_from_presets(presets: dict) -> list[str]:
    """Return the ordered list of result keywords (lowercase) from *presets*.

    Falls back to the built-in keyword list when the presets entry is empty.
    """
    kws = [
        k.strip().lower()
        for k in presets.get("result_extraction", {}).get("keywords", [])
        if k.strip()
    ]
    if kws:
        return kws
    return ["passed", "failed", "error", "undefined", "not executed", "no result"]


def import_variant_txt(txt_path: str) -> list[dict[str, str]]:
    """Parse a *Variant_Info.txt* file and return a list of
    ``{variant, swfl}`` dicts suitable for ``presets["variant_extraction"]["entries"]``.

    Lines not matching ``<Variant> - <SWFL>`` are silently ignored.
    """
    entries: list[dict[str, str]] = []
    try:
        with open(txt_path, encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                parts = line.split(" - ", 1)
                if len(parts) == 2:
                    entries.append(
                        {
                            "variant": parts[0].strip(),
                            "swfl": parts[1].strip().upper(),
                        }
                    )
    except FileNotFoundError:
        pass
    return entries


# ═══════════════════════════════════════════════════════════════
# SW PATTERN MANAGEMENT
# ═══════════════════════════════════════════════════════════════

def try_add_sw_pattern(
    presets: dict,
    label: str,
    regex: str,
    update_idx: int | None = None,
) -> tuple[bool, str]:
    """Validate and add (or update) a SW name pattern in *presets*.

    Parameters
    ----------
    presets : dict
        Live presets dict (mutated in place on success).
    label : str
        Human-readable name for the pattern.
    regex : str
        Regular expression string to store.
    update_idx : int | None
        When set the pattern at this index is replaced (edit mode).
        Duplicate checks skip the entry being replaced.

    Returns
    -------
    tuple[bool, str]
        ``(True, "")`` on success.
        ``(False, reason)`` when the pattern could not be stored, where
        *reason* is a human-readable explanation suitable for a dialog.
    """
    regex = regex.strip()
    label = label.strip()

    # ── basic validation ────────────────────────────────────────
    if not regex:
        return False, "Regex field is empty. Enter a valid regex pattern."

    try:
        re.compile(regex)
    except re.error as exc:
        return False, f"Invalid regex syntax — the pattern cannot be compiled:\n{exc}"

    patterns: list[dict] = presets["sw_extraction"].setdefault("patterns", [])

    # ── duplicate regex check ───────────────────────────────────
    for i, p in enumerate(patterns):
        if update_idx is not None and i == update_idx:
            continue
        if p.get("regex", "").strip() == regex:
            existing_label = p.get("label") or p.get("regex", "")
            return False, (
                f"Duplicate regex — the same pattern is already stored as\n"
                f"\u201c{existing_label}\u201d.\n\n"
                f"Edit the existing entry instead of creating a duplicate."
            )

    # ── duplicate label check (non-empty labels only) ───────────
    if label:
        for i, p in enumerate(patterns):
            if update_idx is not None and i == update_idx:
                continue
            if p.get("label", "").strip().lower() == label.lower():
                return False, (
                    f"A pattern named \u201c{label}\u201d already exists.\n"
                    f"Choose a different label, or leave it blank to use the "
                    f"regex as the label."
                )

    # ── persist ────────────────────────────────────────────────
    entry = {"label": label or regex, "regex": regex}
    if update_idx is not None and 0 <= update_idx < len(patterns):
        patterns[update_idx] = entry
    else:
        patterns.append(entry)

    return True, ""


def detect_unmatched_sw(text: str, presets: dict) -> dict[str, list]:
    """Scan *text* for SW name strings not covered by any existing pattern.

    Uses the broad built-in ``SW_NAME_RE`` to discover all candidate SW
    names in *text*, then checks each against every stored pattern.  Any
    candidate not matched by at least one stored pattern is returned as an
    \u201cunmatched\u201d suggestion together with an auto-generated regex.

    Returns
    -------
    dict with two keys:

    ``matched``
        ``list[tuple[str, str]]`` — (sw_value, pattern_label) pairs for
        names that are already covered.
    ``unmatched``
        ``list[dict]`` — each dict has keys ``value``, ``suggested_regex``,
        and ``suggested_label`` for names not covered by any pattern.
    """
    from src.core.systemtestliste.utils import SW_NAME_RE  # local import avoids circular dep

    existing: list[dict] = presets.get("sw_extraction", {}).get("patterns", [])
    candidates: set[str] = {m.group(0) for m in SW_NAME_RE.finditer(text)}

    matched: list[tuple[str, str]] = []
    unmatched: list[dict] = []

    for value in sorted(candidates):
        found_by: str | None = None
        for pat_entry in existing:
            pat_str = pat_entry.get("regex", "")
            if not pat_str:
                continue
            try:
                if re.search(pat_str, value):
                    found_by = pat_entry.get("label") or pat_str
                    break
            except re.error:
                pass
        if found_by:
            matched.append((value, found_by))
        else:
            sug_regex, sug_label = _generalize_sw_name(value)
            unmatched.append(
                {
                    "value": value,
                    "suggested_regex": sug_regex,
                    "suggested_label": sug_label,
                }
            )

    return {"matched": matched, "unmatched": unmatched}


def _generalize_sw_name(sw_value: str) -> tuple[str, str]:
    """Build a generalised regex from a concrete SW name string.

    Digit-only segments are replaced by ``\\d{N}`` wildcards; mixed
    alpha-digit suffixes such as ``A03`` become ``[A-Za-z]\\d{2}``; all
    other segments are escaped verbatim.

    Example::

        "123_456_MySW_01_02_A03"
        \u2192 (r"\\d{3}_\\d{3}_MySW_\\d{2}_\\d{2}_[A-Za-z]\\d{2}",
               "Pattern for MySW")
    """
    parts = sw_value.split("_")
    rx_parts: list[str] = []
    for part in parts:
        if part.isdigit():
            rx_parts.append(r"\d{" + str(len(part)) + r"}")
        elif len(part) >= 2 and part[0].isalpha() and part[1:].isdigit():
            # e.g. A03  →  [A-Za-z]\d{2}
            rx_parts.append(r"[A-Za-z]\d{" + str(len(part) - 1) + r"}")
        else:
            rx_parts.append(re.escape(part))
    # Use the 3rd segment (product / model name) as the label hint
    label_part = parts[2] if len(parts) > 2 else sw_value[:20]
    return "_".join(rx_parts), f"Pattern for {label_part}"
