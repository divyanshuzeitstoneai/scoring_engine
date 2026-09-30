# Formula F10: Comprehensive Data Dictionary

**Target Schema:** Shopify Admin GraphQL API `2024-10` LTS  
**Precision Standard:** Monetary amounts stored as exact `Decimal` strings (quantized to currency minor units)  
**Null Handling:** Nulls explicitly guarded; zero-imputation prohibited unless merchant-confirmed

---

## 1. Input Fields: Shopify Admin GraphQL API (2024-10)

| Field Name | GraphQL Path | Type | Nullable? | Provenance | Treatment if Null / Empty / Invalid |
| :--- | :--- | :---: | :---: | :---: | :--- |
| `order.id` | `Order.id` | `ID!` | No | `VERIFIED-DOCS` | Fatal: blocks batch ingestion (Gate DQ-S1) |
| `order.createdAt` | `Order.createdAt` | `DateTime!` | No | `VERIFIED-DOCS` | Fatal: missing timestamp blocks order attribution |
| `order.processedAt` | `Order.processedAt` | `DateTime!` | No | `VERIFIED-DOCS` | Fallback to `createdAt` if absent |
| `order.cancelledAt` | `Order.cancelledAt` | `DateTime` | Yes | `VERIFIED-DOCS` | Populates cancellation flag; lines audited for shipped units |
| `order.test` | `Order.test` | `Boolean!` | No | `VERIFIED-PROBE` | If `true`, quarantined from production reporting (Gate DQ-S4) |
| `order.displayFinancialStatus` | `Order.displayFinancialStatus` | `OrderDisplayFinancialStatus` | Yes | `VERIFIED-DOCS` | Informational; does not override line-level refund math |
| `order.taxesIncluded` | `Order.taxesIncluded` | `Boolean!` | No | `VERIFIED-PROBE` | Verified in PR-29; determines tax extraction basis |
| `order.totalPriceSet` | `Order.totalPriceSet.shopMoney.amount` | `Decimal!` | No | `VERIFIED-DOCS` | Order financial control total for Gate DQ-R1 |
| `lineItem.id` | `LineItem.id` | `ID!` | No | `VERIFIED-DOCS` | Fatal: primary key for atomic line fact (Gate DQ-U1) |
| `lineItem.quantity` | `LineItem.quantity` | `Int!` | No | `VERIFIED-DOCS` | Initial units ordered |
| `lineItem.currentQuantity` | `LineItem.currentQuantity` | `Int!` | No | `VERIFIED-DOCS` | Used with `quantity` to detect order-edit unit removals (PR-17) |
| `lineItem.sku` | `LineItem.sku` | `String` | Yes | `VERIFIED-DOCS` | Nullable in Shopify; `variant.id` serves as immutable primary key |
| `lineItem.title` | `LineItem.title` | `String!` | No | `VERIFIED-DOCS` | Product display name |
| `lineItem.originalTotalSet` | `LineItem.originalTotalSet.shopMoney.amount` | `Decimal!` | No | `VERIFIED-DOCS` | Gross billing base prior to line-level discounts |
| `lineItem.discountAllocations` | `LineItem.discountAllocations[].allocatedAmountSet` | `[DiscountAllocation!]!` | No | `VERIFIED-PROBE` | Verified in PR-01 to PR-08; exact line-item discount share |
| `inventoryItem.unitCost` | `InventoryItem.unitCost.amount` | `Decimal` | Yes | `VERIFIED-PROBE` | If null, flagged `COGS_MISSING` and quarantined (Gate DQ-K1) |
| `inventoryItem.measurement` | `InventoryItem.measurement.weight.value` | `Float` | Yes | `VERIFIED-DOCS` | Physical weight for shipping allocation; triggers fallback if null |
| `transaction.fees` | `OrderTransaction.fees[].amount.amount` | `[TransactionFee!]!` | Yes | `VERIFIED-PROBE` | Exact payment processor fees (Tier T1); falls back to config model if empty |
| `refundLineItem.quantity` | `RefundLineItem.quantity` | `Int!` | No | `VERIFIED-DOCS` | Total refunded units on this line item |
| `refundLineItem.subtotalSet` | `RefundLineItem.subtotalSet.shopMoney.amount` | `Decimal!` | No | `VERIFIED-PROBE` | Verified in PR-09; exact refunded dollars |
| `refundLineItem.restockType` | `RefundLineItem.restockType` | `RestockType!` | No | `VERIFIED-PROBE` | `RESTOCK`/`RETURN` restores inventory cost; `NO_RESTOCK` lost |
| `orderAdjustment.amountSet` | `OrderAdjustment.amountSet.shopMoney.amount` | `Decimal!` | Yes | `VERIFIED-PROBE` | Goodwill refunds (PR-12); attributed proportionally across line items |
| `return.status` | `Return.status` | `ReturnStatus!` | Yes | `VERIFIED-DOCS` | Tracks return progression: `OPEN`, `REQUESTED`, `CLOSED`, `CANCELLED` |

---

## 2. Normalized Line Facts Schema (`f10_line_facts`)

| Field Name | Type | Description |
| :--- | :---: | :--- |
| `line_item_id` | `String` | Immutable line item ID from Shopify GraphQL |
| `order_id` | `String` | Order ID |
| `variant_id` | `String` | Product variant ID (primary grouping key) |
| `product_id` | `String` | Parent product ID |
| `sku` | `String` | SKU string (or empty string if unassigned) |
| `title` | `String` | Product title |
| `category` | `String` | Product category mapped via `category_map` config |
| `cohort_date` | `String` | Order date (`YYYY-MM-DD`) in shop timezone |
| `is_matured` | `Boolean` | True if order cohort age >= `return_window_days + processing_days` |
| `q_ordered` | `Int` | Units initially ordered (`lineItem.quantity`) |
| `q_removed` | `Int` | Units removed before shipping via order edits (`quantity - currentQuantity`) |
| `q_cancelled` | `Int` | Units cancelled before shipping |
| `q_shipped` | `Int` | Units physically fulfilled (`q_ordered - q_removed - q_cancelled`) |
| `q_refunded` | `Int` | Total units refunded |
| `q_restocked` | `Int` | Refunded units restocked/returned into available inventory |
| `q_not_restocked` | `Int` | Refunded units damaged, destroyed, or kept by customer |
| `q_kept` | `Int` | Units kept by customer without refund (`max(0, q_shipped - q_refunded)`) |
| `q_lost_returns` | `Int` | Units lost to merchant (`q_not_restocked` under lost/kept policies) |
| `q_physical_returns` | `Int` | Units requiring reverse shipping (`q_restocked + (q_not_restocked if policy=lost)`) |
| `gross_line` | `Decimal` | Gross amount billed before discounts |
| `disc_line` | `Decimal` | Line-allocated discounts |
| `net_billed` | `Decimal` | Billed revenue (`gross_line - disc_line`) |
| `refund_item` | `Decimal` | Refunded item amount |
| `goodwill` | `Decimal` | Proportional goodwill refund allocated from order adjustments |
| `retained_rev` | `Decimal` | Retained revenue (`net_billed - refund_item - goodwill`) |
| `cost_snapshot` | `Decimal` | Point-in-time unit COGS snapshot |
| `cogs_lost` | `Decimal` | Incurred inventory cost (`(q_kept + q_lost_returns) * unit_cost`) |
| `cogs_unresolved` | `Decimal` | Quarantined COGS dollars under `unknown` restock policy |
| `cogs_state` | `CogsState` | `COGS_OBSERVED`, `COGS_MISSING`, `COGS_ZERO_SUSPECT` |
| `cogs_tier` | `EvidenceTier` | Evidence level: T1 (Point-in-time), T2 (Confirmed 0), T3 (Backfill), T4 (Missing) |
| `carrier_cost_allocated` | `Decimal` | Largest-remainder allocated courier outbound shipping cost |
| `shipping_charged_allocated` | `Decimal` | Largest-remainder allocated shipping charged to customer |
| `outbound` | `Decimal` | Net outbound logistics cost (`carrier_cost - shipping_charged`) |
| `pay_fees` | `Decimal` | Payment gateway transaction fees |
| `pay_fees_tier` | `EvidenceTier` | T1 (Observed in transaction), T3 (Calculated from fallback model) |
| `return_ship` | `Decimal` | Reverse logistics shipping cost (`q_physical_returns * return_ship_cost`) |
| `handling` | `Decimal` | Return handling/inspection fee (`q_physical_returns * handling_cost`) |
| `packaging` | `Decimal` | Pick-and-pack fee (`q_shipped * pick_pack_cost`) |
| `contribution` | `Decimal` | Net product contribution dollars (null if costs unresolved) |
| `contribution_before_unknown`| `Decimal` | Contribution dollars before unresolved/unknown cost components |
| `data_quality_flags` | `List[String]`| Audit flags (`cogs_missing`, `cogs_zero_suspect`, `alloc_fallback`, etc.) |

---

## 3. Variant Rollup Metrics Schema (`f10_variant_metrics`)

| Field Name | Type | Description |
| :--- | :---: | :--- |
| `variant_id` | `String` | Primary identifier for the variant |
| `product_id` | `String` | Parent product ID |
| `sku` | `String` | Merchant SKU |
| `title` | `String` | Variant / product title |
| `category` | `String` | Assigned product category |
| `window_days` | `Int` | Cohort window duration (30, 90, 180, or 365 calendar days) |
| `rev_billed` | `Decimal` | Total net billed revenue across all scored lines |
| `rev_refunded` | `Decimal` | Total refunded dollars |
| `rev_retained` | `Decimal` | Total retained revenue |
| `cogs_total` | `Decimal` | Total incurred COGS on retained & lost units |
| `outbound_total` | `Decimal` | Total outbound courier cost net of shipping collected |
| `pay_fees_total` | `Decimal` | Total payment gateway processing fees |
| `return_ship_total` | `Decimal` | Total reverse shipping cost |
| `handling_total` | `Decimal` | Total return handling and inspection fees |
| `packaging_total` | `Decimal` | Total pick-and-pack fulfillment cost |
| `contribution` | `Decimal` | Net Contribution Dollars: RetainedRev - AllCosts |
| `margin_pct` | `Decimal` | Contribution Margin: `Contribution / RetainedRev * 100` (null if RetainedRev <= 0) |
| `score` | `Decimal` | Clamped Contribution Score `[0.00, 100.00]` (0 if RetainedRev <= 0 and costs > 0) |
| `status` | `VariantStatus` | Product status classification (see Section 4) |
| `confidence` | `String` | `OK` (units >= min_units) or `LOW_CONFIDENCE` (excluded from rankings) |
| `naive_profit` | `Decimal` | Naive gross profit: `NetBilled - (q_shipped * cost)` |
| `hidden_leakage` | `Decimal` | Hidden return & operational drag: `NaiveProfit - Contribution` |
| `leakage_cogs_lost` | `Decimal` | Waterfall: inventory cost of written-off / unreturned goods |
| `leakage_outbound` | `Decimal` | Waterfall: outbound courier loss on returned items |
| `leakage_fees` | `Decimal` | Waterfall: unrefunded payment processing fees |
| `leakage_return_ship` | `Decimal` | Waterfall: reverse transit carrier fees |
| `leakage_handling` | `Decimal` | Waterfall: return warehouse handling and restocking fees |
| `leakage_packaging` | `Decimal` | Waterfall: wasted pick-and-pack supplies and labor |
| `units_shipped` | `Int` | Total units shipped across scored lines |
| `units_refunded` | `Int` | Total units refunded |
| `units_restocked` | `Int` | Total units restocked |
| `units_lost` | `Int` | Total units lost/destroyed |
| `return_rate` | `Decimal` | Refund rate percentage: `units_refunded / units_shipped * 100` |
| `revenue_scored` | `Decimal` | Billed revenue included in scoring |
| `revenue_quarantined` | `Decimal` | Billed revenue quarantined due to missing/suspect costs |
| `unknown_cost_share` | `Decimal` | Ratio: `revenue_quarantined / (revenue_scored + revenue_quarantined)` |
| `config_hash` | `String` | SHA-256 fingerprint of the configuration used |
| `as_of` | `String` | Cut-off timestamp (`YYYY-MM-DD`) in shop timezone |

---

## 4. Enumerations & Value Domains

### VariantStatus
- `HEALTHY`: Scored variant with `margin_pct >= healthy_margin` (default 25.00%).
- `UNDERPERFORMING`: Scored variant with `0.00% < margin_pct < healthy_margin`.
- `BREAKEVEN`: Scored variant with `contribution == 0.00` and `margin_pct == 0.00%`.
- `VALUE_DESTROYING`: Scored variant with `contribution < 0.00` or `retained_rev <= 0.00` with positive costs.
- `UNSCOREABLE`: Variant where `unknown_cost_share > max_unknown_cost_share` (Gate DQ-K2).
- `INCOMPLETE_COSTS`: Variant with unconfigured cost components (e.g., return shipping unknown).
- `RANGE_ONLY`: Variant with bounded unknown cost components (bounds configured, no exact point).
- `UNRESOLVED`: Variant with unresolvable inventory disposition under `no_restock_policy: unknown`.
- `NO_DATA`: Variant with zero units shipped during the cohort window.

### EvidenceTier
- `T1` (Verified Point-in-Time): Captured snapshot from Shopify API at transaction time.
- `T2` (Confirmed Contractual): Merchant-confirmed flat rate or confirmed zero cost.
- `T3` (Modelled / Backfilled): Fallback fee formula or current catalog cost snapshot.
- `T4` (Missing / Unknown): Value unknown; quarantined or marked incomplete.
