"""
Customer grouping — mirrors M code step 12.
Loads customer_map.xlsx from reference_data for maintainable mappings.
"""

import os
import pandas as pd

_REF_DIR = os.path.join(os.path.dirname(__file__), "..", "reference_data")
_CUSTOMER_MAP: dict | None = None


def _get_customer_map() -> dict:
    global _CUSTOMER_MAP
    if _CUSTOMER_MAP is None:
        path = os.path.join(_REF_DIR, "customer_map.xlsx")
        df = pd.read_excel(path, dtype=str).dropna(subset=["customer_key", "customer_group"])
        _CUSTOMER_MAP = dict(
            zip(
                df["customer_key"].str.upper().str.strip(),
                df["customer_group"].str.strip(),
            )
        )
    return _CUSTOMER_MAP


def add_customer_group(df: pd.DataFrame, customer_col: str = "Customer") -> pd.DataFrame:
    """
    Adds a 'Customer Group' column by looking up the customer name
    in customer_map.xlsx. Falls back to the original Customer value
    if no mapping is found.
    """
    mapping = _get_customer_map()

    def _group(raw):
        if pd.isna(raw) or raw == "":
            return raw
        key = str(raw).upper().strip()
        return mapping.get(key, raw)  # fall back to original if not in map

    df = df.copy()
    df["Customer Group"] = df[customer_col].apply(_group)
    return df
