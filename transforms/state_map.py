"""
State normalization — mirrors M code step 9.
Accepts full state names or abbreviations, returns 2-letter code.
"""

import pandas as pd

_STATE_MAP = {
    "AL": "AL", "ALABAMA": "AL",
    "AK": "AK", "ALASKA": "AK",
    "AZ": "AZ", "ARIZONA": "AZ",
    "AR": "AR", "ARKANSAS": "AR",
    "CA": "CA", "CALIFORNIA": "CA",
    "CO": "CO", "COLORADO": "CO",
    "CT": "CT", "CONNECTICUT": "CT",
    "DE": "DE", "DELAWARE": "DE",
    "FL": "FL", "FLORIDA": "FL",
    "GA": "GA", "GEORGIA": "GA",
    "HI": "HI", "HAWAII": "HI",
    "ID": "ID", "IDAHO": "ID",
    "IL": "IL", "ILLINOIS": "IL",
    "IN": "IN", "INDIANA": "IN",
    "IA": "IA", "IOWA": "IA",
    "KS": "KS", "KANSAS": "KS",
    "KY": "KY", "KENTUCKY": "KY",
    "LA": "LA", "LOUISIANA": "LA",
    "ME": "ME", "MAINE": "ME",
    "MD": "MD", "MARYLAND": "MD",
    "MA": "MA", "MASSACHUSETTS": "MA",
    "MI": "MI", "MICHIGAN": "MI",
    "MN": "MN", "MINNESOTA": "MN",
    "MS": "MS", "MISSISSIPPI": "MS",
    "MO": "MO", "MISSOURI": "MO",
    "MT": "MT", "MONTANA": "MT",
    "NE": "NE", "NEBRASKA": "NE",
    "NV": "NV", "NEVADA": "NV",
    "NH": "NH", "NEWHAMPSHIRE": "NH",
    "NJ": "NJ", "NEWJERSEY": "NJ",
    "NM": "NM", "NEWMEXICO": "NM",
    "NY": "NY", "NEWYORK": "NY",
    "NC": "NC", "NORTHCAROLINA": "NC",
    "ND": "ND", "NORTHDAKOTA": "ND",
    "OH": "OH", "OHIO": "OH",
    "OK": "OK", "OKLAHOMA": "OK",
    "OR": "OR", "OREGON": "OR",
    "PA": "PA", "PENNSYLVANIA": "PA",
    "RI": "RI", "RHODEISLAND": "RI",
    "SC": "SC", "SOUTHCAROLINA": "SC",
    "SD": "SD", "SOUTHDAKOTA": "SD",
    "TN": "TN", "TENNESSEE": "TN",
    "TX": "TX", "TEXAS": "TX",
    "UT": "UT", "UTAH": "UT",
    "VT": "VT", "VERMONT": "VT",
    "VA": "VA", "VIRGINIA": "VA",
    "WA": "WA", "WASHINGTON": "WA",
    "WV": "WV", "WESTVIRGINIA": "WV",
    "WI": "WI", "WISCONSIN": "WI",
    "WY": "WY", "WYOMING": "WY",
    "DC": "DC", "DISTRICTOFCOLUMBIA": "DC",
}


def _normalize_state(raw) -> str:
    if raw is None or (isinstance(raw, float)):
        return "N/A"
    cleaned = str(raw).upper().strip().replace(".", "").replace(",", "").replace(" ", "")
    return _STATE_MAP.get(cleaned, "N/A")


def add_state_map(df: pd.DataFrame, state_col: str = "Ship To State") -> pd.DataFrame:
    df = df.copy()
    df["Ship To State (Map)"] = df[state_col].apply(_normalize_state)
    return df
