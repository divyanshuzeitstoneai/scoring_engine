# Known Limitations & Boundary Constraints

1. **Contribution Profit vs Net Profit:**
   - Formula F11 evaluates **Contribution Profit** ($P = C - \text{COGS} - S - G - E - O$). It does NOT deduct fixed general & administrative overhead, merchant salaries, warehouse leases, or paid ad acquisition spend (ROAS / CAC).
2. **Current vs Historical Supplier Costs:**
   - Shopify GraphQL exposes `InventoryItem.unitCost` representing current cost. In the absence of an ingested historical cost snapshot table, orders reflect `cogs_basis = "restated_current_cost"`.
3. **Third-Party Payment Gateway Fees:**
   - Gateways other than Shopify Payments (PayPal, Stripe, Razorpay) do not expose transaction fees through GraphQL. These are tagged `estimated` via schedule or `missing`.
4. **Actual 3PL Carrier Invoices:**
   - Freight invoices are not standard Shopify fields and must be populated into configured order metafields.
5. **Historical Edit Reconstruction:**
   - Shopify does not expose a chronological timeline of intermediate line modifications. F11 evaluates the current state versus the original as-sold baseline.
