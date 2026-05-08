"""
Shopify connector — wraps the Admin REST API.
Handles both B2B and DTC stores via separate tokens.
"""

import os
import requests
import pandas as pd
from datetime import datetime, timedelta

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
SHOPIFY_B2B_TOKEN  = os.environ["SHOPIFY_B2B_TOKEN"]
SHOPIFY_B2B_STORE  = os.environ["SHOPIFY_B2B_STORE"]   # e.g. lifelines-b2b.myshopify.com
SHOPIFY_DTC_TOKEN  = os.environ["SHOPIFY_DTC_TOKEN"]
SHOPIFY_DTC_STORE  = os.environ["SHOPIFY_DTC_STORE"]   # e.g. lifelines-dtc.myshopify.com

API_VERSION = "2024-01"


# ---------------------------------------------------------------------------
# Core paginated fetcher
# ---------------------------------------------------------------------------
def _get_orders(store: str, token: str, days_back: int = 90) -> list[dict]:
    """
    Fetch all orders updated in the last `days_back` days.
    Handles Shopify cursor-based pagination automatically.
    """
    since = (datetime.utcnow() - timedelta(days=days_back)).strftime("%Y-%m-%dT%H:%M:%SZ")
    url = f"https://{store}/admin/api/{API_VERSION}/orders.json"
    headers = {"X-Shopify-Access-Token": token}
    params = {
        "status": "any",
        "updated_at_min": since,
        "limit": 250,
        "fields": (
            "id,name,created_at,processed_at,financial_status,"
            "line_items,shipping_address,total_price,subtotal_price,"
            "total_discounts,total_shipping_price_set,total_tax,"
            "customer,tags"
        ),
    }

    orders = []
    while url:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        data = response.json()
        orders.extend(data.get("orders", []))

        # Follow pagination link if present
        link_header = response.headers.get("Link", "")
        url = _parse_next_link(link_header)
        params = {}  # params are encoded in the next URL

    return orders


def _parse_next_link(link_header: str) -> str | None:
    """Extract the 'next' page URL from Shopify's Link header."""
    for part in link_header.split(","):
        if 'rel="next"' in part:
            return part.split(";")[0].strip().strip("<>")
    return None


# ---------------------------------------------------------------------------
# Order flattener — one row per line item
# ---------------------------------------------------------------------------
def _flatten_orders(orders: list[dict], data_source: str) -> pd.DataFrame:
    rows = []
    for order in orders:
        ship = order.get("shipping_address") or {}
        customer = order.get("customer") or {}
        customer_name = (
            f"{customer.get('first_name', '')} {customer.get('last_name', '')}".strip()
            or customer.get("email", "")
        )

        for line in order.get("line_items", []):
            rows.append({
                "Data Source":      data_source,
                "Order Id":         order["name"],          # e.g. #1001
                "Date":             order.get("processed_at") or order.get("created_at"),
                "SKU":              line.get("sku", ""),
                "Gross Order U":    line.get("quantity", 0),
                "Gross Order $":    float(line.get("price", 0)) * line.get("quantity", 0),
                "Net Order $":      None,                   # calculated after discounts — filled in transform
                "Shipping":         float(order.get("total_shipping_price_set", {}).get("shop_money", {}).get("amount", 0)),
                "Taxes":            float(order.get("total_tax", 0)),
                "Ship To State":    ship.get("province_code", ""),
                "Postal Code":      ship.get("zip", ""),
                "Customer":         data_source,            # overridden per store below
                "Shopify Customer": customer_name,
            })

    df = pd.DataFrame(rows)
    if df.empty:
        return df

    df["Date"] = pd.to_datetime(df["Date"], utc=True).dt.tz_localize(None)
    return df


# ---------------------------------------------------------------------------
# Public: B2B and DTC extractors
# ---------------------------------------------------------------------------
def get_shopify_b2b(days_back: int = 90) -> pd.DataFrame:
    orders = _get_orders(SHOPIFY_B2B_STORE, SHOPIFY_B2B_TOKEN, days_back)
    df = _flatten_orders(orders, data_source="Shopify")
    df["Customer"] = "Shopify B2B"
    return df


def get_shopify_dtc(days_back: int = 90) -> pd.DataFrame:
    orders = _get_orders(SHOPIFY_DTC_STORE, SHOPIFY_DTC_TOKEN, days_back)
    df = _flatten_orders(orders, data_source="Shopify")
    df["Customer"] = "Shopify DTC"
    return df
