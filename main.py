"""
Main pipeline — orchestrates extraction, normalization, and transforms.
Run directly or via GitHub Actions on a schedule.
"""

import os
import pandas as pd
from datetime import datetime, date

# Connectors
from connectors.sharepoint import get_item_master
from connectors.shopify import get_shopify_b2b, get_shopify_dtc

# Transforms
from transforms.sku_map import apply_sku_map
from transforms.state_map import add_state_map
from transforms.cogs import add_accounts_receivable, add_cogs
from transforms.customer_group import add_customer_group

# ---------------------------------------------------------------------------
# Schema — all sources normalize to these columns before combining
# ---------------------------------------------------------------------------
TARGET_COLUMNS = [
    "Data Source", "Invoice Date", "Date", "SKU", "Customer",
    "Gross Order $", "Net Order $", "Gross Order U", "Order Id",
    "Invoice Id", "Shipping", "Taxes", "Ship To State",
    "Postal Code", "Shopify Customer", "Returns $",
]


def normalize(df: pd.DataFrame) -> pd.DataFrame:
    """Force every source DataFrame into the shared schema."""
    for col in TARGET_COLUMNS:
        if col not in df.columns:
            df[col] = None
    return df[TARGET_COLUMNS]


# ---------------------------------------------------------------------------
# Date helpers
# ---------------------------------------------------------------------------
def _master_date(row) -> date | None:
    inv = row.get("Invoice Date")
    ord_ = row.get("Date")
    for val in (inv, ord_):
        try:
            return pd.to_datetime(val).date()
        except Exception:
            pass
    return None


def _week_begin(d: date) -> date | None:
    if d is None:
        return None
    return d - pd.Timedelta(days=d.weekday() + 1 if d.weekday() != 6 else 0)


def _last_week_flag(d: date) -> str:
    if d is None:
        return "N"
    today = date.today()
    target = today - pd.Timedelta(days=7 + today.weekday() + 1)
    wb = _week_begin(d)
    return "Y" if wb == _week_begin(target) else "N"


def _clean_postal(raw) -> str | None:
    if raw is None or (isinstance(raw, float) and pd.isna(raw)):
        return None
    s = str(raw).strip()
    s = s.split("-")[0][:5]
    return s.zfill(5)


# ---------------------------------------------------------------------------
# Pipeline
# ---------------------------------------------------------------------------
def run(days_back: int = 90) -> pd.DataFrame:
    print("Fetching Item Master from SharePoint...")
    item_master = get_item_master()

    print("Extracting Shopify B2B...")
    b2b = normalize(get_shopify_b2b(days_back))

    print("Extracting Shopify DTC...")
    dtc = normalize(get_shopify_dtc(days_back))

    # --- combine all sources (more will be added here as extractors are built) ---
    print("Combining sources...")
    combined = pd.concat([b2b, dtc], ignore_index=True)

    # --- ghost row killer ---
    combined = combined[combined["SKU"].notna() & (combined["SKU"] != "")]

    # --- type cleanup ---
    for col in ["Gross Order $", "Net Order $", "Shipping", "Taxes", "Returns $"]:
        combined[col] = pd.to_numeric(combined[col], errors="coerce")
    combined["Gross Order U"] = pd.to_numeric(combined["Gross Order U"], errors="coerce").astype("Int64")

    # --- SKU mapping ---
    print("Applying SKU map...")
    combined = apply_sku_map(combined)

    # --- master date ---
    combined["Date (Accounts Rec.)"] = combined.apply(_master_date, axis=1)
    combined = combined[combined["Date (Accounts Rec.)"].notna()]

    # --- AR ---
    combined = add_accounts_receivable(combined)

    # --- state map ---
    combined = add_state_map(combined)

    # --- week logic ---
    combined["Week Begin Dt"] = combined["Date (Accounts Rec.)"].apply(_week_begin)
    combined["Last Week (Y/N)"] = combined["Date (Accounts Rec.)"].apply(_last_week_flag)

    # --- COGs + margin ---
    print("Calculating COGs and margin...")
    combined = add_cogs(combined, item_master)

    # --- customer group ---
    combined = add_customer_group(combined)

    # --- postal cleanup ---
    combined["Postal Code"] = combined["Postal Code"].apply(_clean_postal)

    print(f"Pipeline complete — {len(combined):,} rows")
    return combined


# ---------------------------------------------------------------------------
# Output
# ---------------------------------------------------------------------------
def save(df: pd.DataFrame, output_dir: str = "output") -> str:
    os.makedirs(output_dir, exist_ok=True)
    filename = f"sales_data_{datetime.today().strftime('%Y%m%d')}.parquet"
    path = os.path.join(output_dir, filename)
    df.to_parquet(path, index=False)
    print(f"Saved to {path}")
    return path


if __name__ == "__main__":
    df = run()
    save(df)
