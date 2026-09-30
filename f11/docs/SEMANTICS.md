# Shopify Admin GraphQL Semantics Reference (Version 2024-10)

This document records the exact semantics of Shopify GraphQL fields used in Formula F11 Order Profitability v2.1.

---

### 1. Line Quantities and Refunded Units
- `quantity`: Original quantity ordered at checkout (`q0`).
- `currentQuantity`: Active, unrefunded quantity remaining on the order (`qc`).
- **Amendment A1 Rule:** To prevent double-counting, revenue and COGS are computed on the **sold-unit basis** `qs = quantity - qe`, where `qe` represents units removed via order edit without refund. **All refunds and returns are booked exclusively in refund cost `E`**.

### 2. Discount Allocations and Proration
- `LineItem.discountedUnitPriceSet` reflects item-level markdowns but **excludes** order-level coupons and automatic cart discounts.
- Order-wide discounts are exposed under `LineItem.discountAllocations`.
- When units are edited or partially refunded, order-wide discounts are prorated according to `discount_proration_policy` (`pro_rata = qc / q0`).

### 3. Payment Processing Fees
- `OrderTransaction.fees` is populated **only** for Shopify Payments transactions.
- For all third-party gateways (PayPal, Stripe, Razorpay, Klarna, COD, Bank Deposit), `fees` is an empty list (`[]`), representing an **unmeasured / unknown** value, **never $0.00**.
- In the `MEASURED` lane, orders with third-party gateways with unknown fees are routed to `UNDETERMINED` or `CONFIRMED_LOSS` unless estimated via `gateway_fee_schedule` in the `ESTIMATED` lane.
- Gateways configured in `zero_fee_gateways` (e.g. Cash on Delivery, Manual) are treated as **structural zero** measured costs.

### 4. COGS and Cost Sourcing
- `InventoryItem.unitCost` represents the **current** supplier unit cost at time of query execution.
- If supplier cost changed between checkout and audit, the order carries `cogs_basis = "restated_current_cost"`.
- If an ingested historical snapshot exists, `cogs_basis = "snapshot"`.
- If `unitCost` is null or variant is deleted, COGS is tagged `missing`.
- If `unitCost = 0` on a priced product, it is flagged `SUSPECT_ZERO_COST`.

### 5. Freight & 3PL Carrier Costs
- Shopify Admin API does NOT expose actual 3PL carrier invoice costs.
- `S` is measured if provided via configured metafield (e.g. `metafield:custom.actual_carrier_cost`).
- `S` is structural zero (measured) if all lines have `requiresShipping = false` or order was local pickup / POS in-person.
- Otherwise, `S` is estimated via the configured `shipping_rate_card` in the `ESTIMATED` lane, or tagged missing.
