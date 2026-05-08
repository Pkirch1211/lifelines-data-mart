# LifeLines Sales Data Pipeline

Automated pipeline that pulls sales data from all channels, normalizes it to a unified schema, and outputs a daily parquet file.

## Architecture

```
extractors/       # one file per data source
connectors/       # API clients (Shopify, SharePoint)
transforms/       # shared logic (SKU map, COGs, state, customer group)
reference_data/   # maintainable Excel lookup tables
.github/          # GitHub Actions scheduled workflow
main.py           # orchestrator
```

## Sources

| Source | Status | Method |
|--------|--------|--------|
| Shopify B2B | ✅ Built | Admin API |
| Shopify DTC | ✅ Built | Admin API |
| Amazon | 🔲 Pending | SP-API |
| SPS Commerce | 🔲 Pending | sFTP |
| Rithum Commerce Hub | 🔲 Pending | Manual CSV |
| Rithum DSCO (Kohls/AAFES/TCS) | 🔲 Pending | Manual CSV |
| TikTok Shop | 🔲 Pending | Manual CSV |
| Walmart Marketplace | 🔲 Pending | Manual CSV |
| Wayfair | 🔲 Pending | Manual CSV |
| MarketTime | 🔲 Pending | Manual CSV |

## Reference Data

Maintain these files in `/reference_data/` — no code changes needed when adding mappings:

- `sku_aliases.xlsx` — retailer SKU → LL SKU mappings (columns: `external_sku`, `ll_sku`)
- `sku_corrections.xlsx` — known bad values (Excel date artifacts, etc.) (columns: `bad_value`, `ll_sku`)
- `customer_map.xlsx` — customer name → customer group (columns: `customer_key`, `customer_group`)

Item Master is pulled live from SharePoint on each run.

## Setup

### Local development
```bash
cp .env.example .env
# fill in your credentials in .env
pip install -r requirements.txt
python main.py
```

### GitHub Actions secrets
Add these in repo Settings → Secrets → Actions:
- `MS_TENANT_ID`
- `MS_CLIENT_ID`
- `MS_CLIENT_SECRET`
- `SHOPIFY_B2B_TOKEN`
- `SHOPIFY_B2B_STORE`
- `SHOPIFY_DTC_TOKEN`
- `SHOPIFY_DTC_STORE`

## Output

Daily parquet file saved to `output/sales_data_YYYYMMDD.parquet`.
Compatible with pandas, Power BI, and any other tool that reads parquet.
