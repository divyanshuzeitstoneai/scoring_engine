# Configuration Reference (`f11.config.yaml`)

Every configuration key in Formula F11 is strictly required with **NO silent defaults**.
The engine refuses initialization if any key is missing or invalid.

---

### Core Configuration Keys

| Parameter Key | Permitted Values | Operational Meaning & Consequence |
| :--- | :--- | :--- |
| `api_version` | `"2024-10"` | Pinned Admin API version for GraphQL queries and introspection validation. |
| `as_of` | ISO-8601 UTC string | Evaluation anchor timestamp. Excludes refunds and edits timestamped after this date. |
| `shop_currency` | `"USD"`, `"GBP"`, `"CAD"`, `"INR"`, `"JPY"` | Primary store currency. Orders in other currencies trigger `CURRENCY_MISMATCH`. |
| `currency_exponent`| `0`, `2`, `3` | Number of decimal places. JPY = 0, USD = 2. Controls integer minor unit conversion. |
| `money_basis` | `"shopMoney"` | Enforces using store settlement currency, ignoring volatile presentment currencies. |
| `refund_window_days`| Dict by category | Duration during which open orders incur an estimated refund provision rate $r$. |
| `window_start_event`| `"processedAt"`, `"createdAt"` | Timestamp anchoring order age evaluation. |
| `refund_provision_rate`| Dict by category ($0.0 - 1.0$) | Estimated refund rate applied to net revenue $R$ while refund window remains open. |
| `discount_proration_policy`| `"pro_rata"`, `"full"` | Rule for allocating order-level coupons across items when lines are modified. |
| `rounding_mode` | `"half_up"`, `"half_even"` | Minor unit rounding algorithm for provisions and prorations. |
| `cogs_coverage_gate`| Number ($0.0 - 100.0$) | Minimum storewide revenue share with complete supplier costs required to report KPIs. |
| `suspect_zero_cost_policy`| `"measured_with_flag"`, `"treat_as_missing"` | Treatment of inventory items with $0.00 unit cost on non-free products. |
| `carrier_cost_source`| String | Order metafield key or file path sourcing true 3PL freight charges. |
| `shipping_rate_card`| Nested object | Weight and destination zone matrix used for estimating freight in `ESTIMATED` lane. |
| `zero_fee_gateways` | List of strings | Gateways carrying $0.00 processing fees by design (Cash on Delivery, Manual). |
| `gateway_fee_schedule`| Nested object | Processing fee estimation schedules (rate % + fixed fee) for third-party gateways. |
| `packaging_cost` | Integer (minor units) | Default operational handling and packaging material cost per physical order. |
| `band_thresholds` | `{high, acceptable, at_risk}` | Profit margin boundaries (e.g. 30%, 10%, 0%). Evaluated via integer cross-multiplication. |

---

### Bundled Configuration Profiles

1. **`strict.yaml`:** High evidentiary standards. No rate card or gateway fee estimation; missing costs route orders to `UNDETERMINED`; suspect zero costs quarantined; coverage gate = 95%.
2. **`balanced.yaml`:** Standard production baseline. Rate card active; gateway fee schedules active; suspect zero cost measured with flag; coverage gate = 90%.
3. **`lenient.yaml`:** Permissive analysis mode. Lower coverage gate (70%); relaxed band thresholds.
