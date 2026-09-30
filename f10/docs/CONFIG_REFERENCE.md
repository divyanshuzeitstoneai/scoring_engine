# Formula F10: Configuration Reference Guide

**Schema Definition:** [`f10/config/config.schema.json`](file:///d:/Scoring%20engine/f10/config/config.schema.json)  
**Production Example:** [`f10/config/config.example.yaml`](file:///d:/Scoring%20engine/f10/config/config.example.yaml)

---

## 1. Parameters Reference Table

| Parameter | Type | Required? | Allowed Values | Description & Best Practice |
| :--- | :---: | :---: | :--- | :--- |
| `api_version` | String | Yes | `2024-10` | Pinned Shopify Admin GraphQL API version. |
| `as_of` | String | Yes | `YYYY-MM-DD` | Historical cutoff date. Never reads system clock. |
| `shop_currency` | String | Yes | ISO 4217 (e.g. `USD`) | Base shop currency for financial aggregation. |
| `currency_minor_units`| Int | Yes | `0, 2, 3` | Precision scale for rounding (2 for USD, 0 for JPY). |
| `rounding_mode` | String | Yes | `ROUND_HALF_UP`, etc. | Quantization rounding behavior for currency remainders. |
| `cohort_date_field` | Enum | Yes | `processedAt`, `createdAt`| Defines order cohort timestamp (PR-39). |
| `return_window_days`| Int | Yes | $\ge 0$ | Merchant return policy window in days (e.g. 30). |
| `processing_days` | Int | Yes | $\ge 0$ | Inspection / transit turnaround days (e.g. 5). |
| `carrier_cost_model`| Enum | Yes | `flat`, `weight_table`, `none` | Courier shipping cost calculation model. |
| `carrier_flat_rate` | Decimal | Optional | $\ge 0.00$ | Flat courier invoice cost per shipment. |
| `return_ship_cost` | Decimal | Yes | $\ge 0.00$ | Reverse courier cost per return label (Tier T2). |
| `handling_cost` | Decimal | Yes | $\ge 0.00$ | Warehouse inspection labor cost per return (Tier T2). |
| `pick_pack_cost` | Decimal | Optional| $\ge 0.00$ | Outbound pick & pack fulfillment labor cost per unit. |
| `fee_fallback` | Object | Yes | `{rate: Float, fixed: Float}`| Gateway fee fallback model when transaction fee is missing. |
| `shipping_alloc_fallback`| Enum | Yes | `net_billed_share`, `equal_split` | Allocation behavior when line item weights are missing. |
| `no_restock_policy` | Enum | Yes | `lost`, `kept_by_customer`, `unknown` | Interpretation of unrestocked returns (Decision D1). |
| `goodwill_rule` | Enum | Yes | `proportional`, `unallocated` | Attribution of non-line goodwill refunds (Decision D3). |
| `max_unknown_cost_share`| Float | Yes | `0.0 - 1.0` | Max uncosted revenue share before marking `UNSCOREABLE` (0.15). |
| `min_units_for_confidence`| Int | Yes | $\ge 1$ | Minimum ordered units to avoid `LOW_CONFIDENCE` flag (30). |
| `healthy_margin_by_category`| Map | Yes | Category $\to$ Float | Category-specific margin thresholds (e.g. Apparel: 0.52). |
| `category_map` | Map | Yes | `productType` $\to$ Category | Normalizes merchant free-text product types. |
| `return_rate_baseline_by_category`| Map | Yes | Category $\to$ Float | Expected return rate baseline for defect detection. |
| `bundle_policy` | Enum | Yes | `explode`, `single` | Handling of bundle line items (Decision D5). |
| `cost_snapshot_policy`| Enum | Yes | `current_with_flag`, `quarantine` | Historical backfill COGS policy (Decision D12). |
| `exchange_policy` | Enum | Yes | `netting`, `separate_lines`| Treatment of exchanges (Decision D4). |
| `reconcile_tolerance`| Float | Yes | $\ge 0.00$ | Numerical tolerance for reconciliation gates (0.01). |
