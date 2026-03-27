"""
Cross-LIMS terpene / analyte normalization (canonical names, common aliases, unit hints).

This is the start of the defensible layer: Metrc-style minimums won't give you harmonized
analyte identity across Confident Cannabis, LabWare, CannaLIMS, etc.
"""
from __future__ import annotations

import re
from typing import Any, Dict, List, Optional, Tuple


def _normalize_token(s: str) -> str:
    s = s.strip().lower()
    s = s.replace("α", "alpha").replace("β", "beta")
    s = re.sub(r"\s+", " ", s)
    return s


# Canonical key -> aliases (matched after _normalize_token)
TERPENE_CANONICAL_ALIASES: Dict[str, frozenset[str]] = {
    "myrcene": frozenset({"myrcene", "beta-myrcene", "b-myrcene", "beta myrcene"}),
    "limonene": frozenset({"limonene", "d-limonene", "d limonene"}),
    "pinene": frozenset(
        {"pinene", "alpha-pinene", "a-pinene", "beta-pinene", "b-pinene"}
    ),
    "linalool": frozenset({"linalool", "linalol"}),
    "caryophyllene": frozenset(
        {"caryophyllene", "beta-caryophyllene", "b-caryophyllene", "bcp"}
    ),
    "humulene": frozenset({"humulene", "alpha-humulene", "a-humulene"}),
    "terpinolene": frozenset({"terpinolene"}),
    "ocimene": frozenset({"ocimene", "beta-ocimene", "b-ocimene", "alpha-ocimene"}),
    "bisabolol": frozenset({"bisabolol", "alpha-bisabolol", "beta-bisabolol"}),
    "camphene": frozenset({"camphene"}),
    "carene": frozenset({"carene", "delta-3-carene", "3-carene"}),
    "terpineol": frozenset({"terpineol", "alpha-terpineol", "beta-terpineol"}),
    "geraniol": frozenset({"geraniol"}),
    "nerolidol": frozenset({"nerolidol", "trans-nerolidol"}),
    "guaiol": frozenset({"guaiol"}),
    "eucalyptol": frozenset({"eucalyptol", "1,8-cineole", "cineole"}),
    "phellandrene": frozenset({"phellandrene", "alpha-phellandrene", "beta-phellandrene"}),
    "cymene": frozenset({"cymene", "para-cymene", "p-cymene"}),
    "farnesene": frozenset({"farnesene", "beta-farnesene", "alpha-farnesene"}),
    "valencene": frozenset({"valencene"}),
    "fenchol": frozenset({"fenchol", "alpha-fenchol"}),
    "borneol": frozenset({"borneol", "isoborneol"}),
    "cedrol": frozenset({"cedrol"}),
    "sabinene": frozenset({"sabinene"}),
    "pulegone": frozenset({"pulegone"}),
    "menthol": frozenset({"menthol", "isomenthol"}),
}

_ALIAS_TO_CANONICAL: Dict[str, str] = {}
for _canon, _aliases in TERPENE_CANONICAL_ALIASES.items():
    for _a in _aliases:
        _ALIAS_TO_CANONICAL[_normalize_token(_a)] = _canon


def normalize_terpene_name(raw: str) -> str:
    """Map LIMS analyte strings to a canonical terpene slug (lowercase, no Greek)."""
    key = _normalize_token(raw)
    if key in _ALIAS_TO_CANONICAL:
        return _ALIAS_TO_CANONICAL[key]
    for alias, canon in _ALIAS_TO_CANONICAL.items():
        if key == alias:
            return canon
    return key.replace(" ", "-")


def split_value_by_unit(
    value: Optional[float],
    unit: Optional[str],
) -> Tuple[Optional[float], Optional[float]]:
    """Return (percent_wt, mg_per_g) from numeric value + unit string."""
    if value is None:
        return None, None
    u = (unit or "").strip().lower()
    if u in ("%", "percent", "wt%", "w/w%", "w/w"):
        return float(value), None
    if u in ("mg/g", "mg_g", "mg per g", "milligrams per gram"):
        return None, float(value)
    if u == "ppm":
        return None, float(value) / 1000.0
    return None, None


def lims_row_to_terpene_dict(row: Dict[str, Any], *, normalize: bool) -> Tuple[Dict[str, Any], List[str]]:
    """
    row keys: name, value, unit, loq, lod, method, below_loq (optional).
    Returns (firestore-friendly dict, log lines).
    """
    notes: List[str] = []
    raw_name = str(row.get("name") or "").strip()
    if not raw_name:
        return {}, ["skip: empty analyte name"]

    canon = normalize_terpene_name(raw_name) if normalize else _normalize_token(raw_name)
    if normalize and _normalize_token(raw_name) != canon and raw_name.lower().replace(" ", "-") != canon:
        notes.append(f"terpene alias: '{raw_name}' -> '{canon}'")

    value = row.get("value")
    if value is not None and not isinstance(value, (int, float)):
        try:
            value = float(value)
        except (TypeError, ValueError):
            value = None

    unit = row.get("unit")
    unit_s = str(unit) if unit is not None else None
    pct, mg = split_value_by_unit(value, unit_s)

    out: Dict[str, Any] = {
        "name": canon,
        "raw_name": raw_name,
        "value": value,
        "unit": unit,
        "percent_wt": pct,
        "mg_per_g": mg,
        "loq": row.get("loq"),
        "lod": row.get("lod"),
        "method": row.get("method"),
        "below_loq": row.get("below_loq"),
    }
    return {k: v for k, v in out.items() if v is not None}, notes


def lims_row_to_cannabinoid_dict(row: Dict[str, Any], *, normalize: bool) -> Tuple[Dict[str, Any], List[str]]:
    """Same shape as terpene rows; canonical name is slugified LIMS label (no terpene alias table)."""
    notes: List[str] = []
    raw_name = str(row.get("name") or "").strip()
    if not raw_name:
        return {}, ["skip: empty cannabinoid name"]
    key = _normalize_token(raw_name)
    canon = key.replace(" ", "-") if normalize else raw_name
    value = row.get("value")
    if value is not None and not isinstance(value, (int, float)):
        try:
            value = float(value)
        except (TypeError, ValueError):
            value = None
    unit = row.get("unit")
    unit_s = str(unit) if unit is not None else None
    pct, mg = split_value_by_unit(value, unit_s)
    out: Dict[str, Any] = {
        "name": canon,
        "raw_name": raw_name,
        "value": value,
        "unit": unit,
        "percent_wt": pct,
        "mg_per_g": mg,
        "loq": row.get("loq"),
        "lod": row.get("lod"),
        "method": row.get("method"),
        "below_loq": row.get("below_loq"),
    }
    return {k: v for k, v in out.items() if v is not None}, notes
