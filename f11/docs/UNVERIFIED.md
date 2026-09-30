# Unverified Fields and Stop-and-Report Log (`[UNV]`)

Per Operating Rule **R2**, when a field, enum, scope, or behavior cannot be definitively verified on the pinned Admin API version (`2024-10`), it must NOT be guessed. It is logged below with its exact operational fallback.

---

### 1. `LineItem.discountedUnitPriceAfterAllDiscountsSet`
- **Status:** `[UNV]`
- **Uncertainty:** Whether this field consistently includes order-wide automatic discounts, draft order custom discounts, and cross-line allocations in all edge cases.
- **Operational Fallback:** Formula F11 **strictly computes** net unit price directly from `originalUnitPriceSet` and explicit allocations in `LineItem.discountAllocations`. We do not rely on `discountedUnitPriceAfterAllDiscountsSet`.

### 2. `Order.disputes` and Chargeback Fee Behavior
- **Status:** `[UNV]`
- **Uncertainty:** Whether disputes are queryable directly under `Order.disputes` on all merchant plans without specialized chargeback scopes.
- **Operational Fallback:** Evaluated via transaction records of kind `DISPUTE` and `DISPUTE_WON` / `DISPUTE_LOST` when present, plus configured dispute handling schedule in `f11.config.yaml`.

### 3. Payout Scope and Banking Settlement (`read_shopify_payments_payouts`)
- **Status:** `[UNV]`
- **Uncertainty:** Merchant access to payout-level adjustment tables varies by staff permission.
- **Operational Fallback:** Order-level fee evaluation uses `OrderTransaction.fees` directly. Cross-order bank payout adjustments are decoupled into optional reconciliation reports.

### 4. Shipping Line Embedded Tax on Tax-Inclusive Stores
- **Status:** `[UNV]`
- **Uncertainty:** On stores with `taxesIncluded = true`, whether `ShippingLine.priceSet` or `ShippingLine.discountedPriceSet` includes statutory tax.
- **Operational Fallback:** When `taxesIncluded = true` and `taxShipping = true`, embedded tax is calculated and stripped using the order's statutory tax rate before reporting net shipping collected `Sc`.

### 5. Historical Order Edit History Reconstruction
- **Status:** `[UNV]`
- **Uncertainty:** Point-in-time state of an order before multiple complex edits (line swaps + price modifications) cannot be reconstructed solely from line item snapshots.
- **Operational Fallback:** F11 computes primary profitability on the **current** order state, and compares it against the original **as-sold** baseline. Intermediate edit states are flagged as unconstructable.
