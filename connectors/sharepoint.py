"""
SharePoint connector via Microsoft Graph API.
Uses client credentials (app-only auth) — no user login required.
"""

import os
import msal
import requests
import pandas as pd
from io import BytesIO

# ---------------------------------------------------------------------------
# Config — loaded from environment variables / GitHub Actions secrets
# ---------------------------------------------------------------------------
TENANT_ID     = os.environ["MS_TENANT_ID"]
CLIENT_ID     = os.environ["MS_CLIENT_ID"]
CLIENT_SECRET = os.environ["MS_CLIENT_SECRET"]

DRIVE_ID         = "b!HTnOnJwPMEWf4Qc1OT0tJzUXtA3JA_dFmeLcrifvRQA3dGqF56dSRIF8RuQ19ZxM"
ITEM_MASTER_PATH = "Planning/3) Planning BOM/Master BOM.xlsx"
ITEM_MASTER_SHEET = "SBOM"


# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------
def _get_token() -> str:
    app = msal.ConfidentialClientApplication(
        CLIENT_ID,
        authority=f"https://login.microsoftonline.com/{TENANT_ID}",
        client_credential=CLIENT_SECRET,
    )
    result = app.acquire_token_for_client(
        scopes=["https://graph.microsoft.com/.default"]
    )
    if "access_token" not in result:
        raise RuntimeError(f"Failed to acquire token: {result.get('error_description')}")
    return result["access_token"]


# ---------------------------------------------------------------------------
# File fetcher
# ---------------------------------------------------------------------------
def _fetch_file(file_path: str) -> bytes:
    token = _get_token()
    url = (
        f"https://graph.microsoft.com/v1.0/drives/{DRIVE_ID}"
        f"/root:/{file_path}:/content"
    )
    response = requests.get(url, headers={"Authorization": f"Bearer {token}"})
    response.raise_for_status()
    return response.content


# ---------------------------------------------------------------------------
# Public: Item Master
# ---------------------------------------------------------------------------
def get_item_master() -> pd.DataFrame:
    """
    Pull the Master BOM from SharePoint and return the SBOM sheet as a DataFrame.
    Columns returned mirror what the Power Query pipeline expects:
      SBOM SKU, SKU DESC, SKU SUBCATEGORY, SKU CATEGORY, SKU PARENT CATEGORY,
      STD Cost -2025, STD Cost - 2024,
      std_cost_2026_01 ... std_cost_2027_12
    """
    raw = _fetch_file(ITEM_MASTER_PATH)
    df = pd.read_excel(BytesIO(raw), sheet_name=ITEM_MASTER_SHEET, dtype={"SBOM SKU": str})

    # Drop completely empty rows that sometimes appear at the bottom of the sheet
    df = df.dropna(how="all").reset_index(drop=True)

    return df
