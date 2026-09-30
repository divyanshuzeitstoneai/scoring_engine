# Audit Findings and Architecture Answers (F11 v2.1)

---

### (a) Grain: Order vs SKU
- **Calculation Grain:** Order-level evaluated on a granular per-line basis.
- **Rollup Capability:** Supports multi-dimensional rollups by SKU, product category, gateway, channel, and storewide, but **strictly within evidentiary lanes**. Aggregated margins are calculated as $\sum P / \sum C$, never as an average of order margins.

### (b) Rolling & Cross-Order Dependencies
- Cross-order and rolling time dependencies are **strictly isolated from the MEASURED lane**.
- Every evaluated order is standalone and reproducible given its point-in-time inputs and stored `as_of` date.

### (c) Fields Shopify Does Not Provide
1. **Actual 3PL Carrier Invoices:** Shopify Admin API does not record third-party shipping invoices. Sourced via order metafields or estimated via rate cards.
2. **Third-Party Gateway Fees:** Fees are empty for PayPal, Stripe, COD, etc. Sourced via configured schedule in `ESTIMATED` lane or kept as unknown in `UNDETERMINED`.
3. **Historic Cost Snapshots on Order Lines:** Shopify's `InventoryItem.unitCost` reflects current cost. Ingestion snapshots preserve point-in-time costs.

### (d) Assumptions & Biases
- No silent assumptions (`[V-DOC]`, `[V-INTRO]`, `[V-DEV]`, `[CFG]`, `[UNV]`).
- Unknowns are never zeroed.
- Biases are reported with error bounds in the `ESTIMATED` lane.

### (e) Missing COGS Quarantine
- Orders with missing COGS and $P_{\text{upper}} \ge 0$ are quarantined into `UNDETERMINED`.
- If $P_{\text{upper}} < 0$, orders route to `CONFIRMED_LOSS` (proven loss without guessing).
- A 90% storewide COGS coverage gate halts headline KPI presentation if missing cost share is unacceptable.

### (f) Multi-Level Discounts
- Line markdowns, order coupons, and automatic cart discounts are captured via `discountAllocations` and allocated proportionally to active sold units.

### (g) Original vs Current Order State
- Primary profitability is evaluated on the **current state**.
- Original **as-sold** baseline is stored alongside delta profit and cause tags (`refund`, `edit`, `exchange`).
