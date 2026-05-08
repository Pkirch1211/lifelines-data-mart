"""
COGs calculation — mirrors the M code monthly std_cost logic.
Joins Item Master data onto the sales DataFrame and computes:
  - COGs $
  - Product Margin $
  - Accounts Receivable $
"""

import pandas as pd


# ---------------------------------------------------------------------------
# AR calculation (mirrors M code step 8)
# ---------------------------------------------------------------------------
def add_accounts_receivable(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    def _ar(row):
        if row.get("Data Source") == "Shopify":
            return row.get("Net Order $")
        net = row.get("Net Order $")
        gross = row.get("Gross Order $")
        return net if pd.notna(net) else gross

    df["Accounts Receivable $"] = df.apply(_ar, axis=1).astype(float)
    return df


# ---------------------------------------------------------------------------
# COGs join + calculation (mirrors M code step 11)
# ---------------------------------------------------------------------------
def add_cogs(df: pd.DataFrame, item_master: pd.DataFrame) -> pd.DataFrame:
    """
    Joins item_master on LL SKU and computes COGs $ and Product Margin $.
    item_master must have columns: SBOM SKU, std_cost_YYYY_MM, SKU DESC,
    SKU SUBCATEGORY, SKU CATEGORY, SKU PARENT CATEGORY
    """
    im = item_master.copy()
    im = im.rename(columns={"SBOM SKU": "LL SKU"})

    # Columns to bring over from Item Master
    meta_cols = ["LL SKU", "SKU DESC", "SKU SUBCATEGORY", "SKU CATEGORY", "SKU PARENT CATEGORY"]
    cost_cols = [c for c in im.columns if c.startswith("std_cost_") or c in ("STD Cost -2025", "STD Cost - 2024")]
    im = im[meta_cols + cost_cols].drop_duplicates(subset=["LL SKU"])

    df = df.merge(im, on="LL SKU", how="left")

    def _cogs(row):
        date_val = row.get("Date (Accounts Rec.)")
        units = row.get("Gross Order U")
        if pd.isna(date_val) or pd.isna(units):
            return 0.0

        year = date_val.year
        month = date_val.month
        month_str = f"{month:02d}"

        if year == 2025:
            cost = row.get("STD Cost -2025")
        elif year == 2024:
            cost = row.get("STD Cost - 2024")
        elif year >= 2026:
            cost = row.get(f"std_cost_{year}_{month_str}")
        else:
            cost = None

        if pd.isna(cost):
            return 0.0
        return float(cost) * float(units)

    df["COGs $"] = df.apply(_cogs, axis=1)
    df["Product Margin $"] = df["Accounts Receivable $"] - df["COGs $"]

    # Drop raw cost columns — they've served their purpose
    drop_cols = [c for c in df.columns if c.startswith("std_cost_") or c in ("STD Cost -2025", "STD Cost - 2024")]
    df = df.drop(columns=drop_cols)

    return df
