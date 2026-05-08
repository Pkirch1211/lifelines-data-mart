"""
SKU normalization transforms.
Loads alias and correction tables from reference_data/*.xlsx
then applies them to a DataFrame's SKU column.
"""

import re
import os
import pandas as pd

# ---------------------------------------------------------------------------
# Load reference tables once at import time
# ---------------------------------------------------------------------------
_REF_DIR = os.path.join(os.path.dirname(__file__), "..", "reference_data")


def _load_ref(filename: str, key_col: str, val_col: str) -> dict[str, str]:
    path = os.path.join(_REF_DIR, filename)
    df = pd.read_excel(path, dtype=str).dropna(subset=[key_col, val_col])
    return dict(zip(df[key_col].str.strip(), df[val_col].str.strip()))


# Lazy-loaded so tests can patch before import side effects
_ALIASES: dict | None = None
_CORRECTIONS: dict | None = None


def _get_aliases() -> dict:
    global _ALIASES
    if _ALIASES is None:
        _ALIASES = _load_ref("sku_aliases.xlsx", "external_sku", "ll_sku")
    return _ALIASES


def _get_corrections() -> dict:
    global _CORRECTIONS
    if _CORRECTIONS is None:
        _CORRECTIONS = _load_ref("sku_corrections.xlsx", "bad_value", "ll_sku")
    return _CORRECTIONS


# ---------------------------------------------------------------------------
# Suffix stripper  (mirrors M code logic)
# ---------------------------------------------------------------------------
_PRESERVE_SUFFIX = {"LL-11-2507-A", "LL-11-2503-A", "LL-11-2501-A"}

def _strip_suffix(sku: str) -> str:
    if sku in _PRESERVE_SUFFIX:
        return sku
    if sku.upper().endswith("-A"):
        return sku[:-2]
    return sku


# ---------------------------------------------------------------------------
# Public transform
# ---------------------------------------------------------------------------
def apply_sku_map(df: pd.DataFrame, sku_col: str = "SKU") -> pd.DataFrame:
    """
    Adds an 'LL SKU' column to df by:
      1. Applying known corrections (Excel date mangling, etc.)
      2. Looking up alias map (retailer SKU → LL SKU)
      3. Stripping trailing -A suffixes (with exceptions)
      4. Falling back to original SKU if no mapping found
    """
    corrections = _get_corrections()
    aliases = _get_aliases()

    def _map(raw):
        if pd.isna(raw) or raw == "":
            return None
        s = str(raw).strip()
        # Step 1: corrections (Excel date artifacts etc.)
        s = corrections.get(s, s)
        # Step 2: alias lookup
        s = aliases.get(s, s)
        # Step 3: suffix strip
        s = _strip_suffix(s)
        return s

    df = df.copy()
    df["LL SKU"] = df[sku_col].apply(_map)
    return df
