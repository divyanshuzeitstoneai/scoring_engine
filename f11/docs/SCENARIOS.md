# Scenario Catalog (A01 through E12)

Formula F11 v2.1 validates against 50,000 synthetic orders strictly allocated across 38 primary scenario categories:

---

### Group A: Standard Baseline Orders (29,900 Orders)
- **A01 (7,900):** Single line, no discount, paid, fulfilled.
- **A02 (6,000):** Multi-line (2-5 lines), no discount.
- **A03 (3,500):** Line-level automatic discount (10%).
- **A04 (3,500):** Order-level promotional code percentage discount (20%).
- **A05 (1,500):** Order-level promotional code fixed amount discount ($5.00).
- **A06 (2,000):** Stacked line markdown + order coupon discount.
- **A07 (2,500):** Free shipping promotion (100% shipping discount).
- **A08 (3,000):** Paid shipping standard rate.

---

### Group B: Returns, Refunds & Line Edits (6,900 Orders)
- **B01 (1,200):** Partial refund, units damaged / written off.
- **B02 (1,500):** Partial refund with units restocked and recovered.
- **B03 (900):** Full refund with units restocked.
- **B04 (500):** Full refund, lost or damaged in transit.
- **B05 (300):** Standalone shipping fee refund.
- **B06 (600):** Refund on an order-discounted line.
- **B07 (300):** Multiple sequential refunds over time.
- **B08 (400):** Customer return with merchant-paid return label.
- **B09 (400):** Order edit: line item removed before shipment.
- **B10 (300):** Order edit: line item added post-checkout.
- **B11 (300):** Customer exchange (returned line + replacement line).
- **B12 (200):** Late refund requested after refund window closed.

---

### Group C: Sourcing & COGS Edge Cases (4,800 Orders)
- **C01 (900):** Missing `unitCost` across all line items.
- **C02 (1,100):** Missing `unitCost` on one of multiple line items.
- **C03 (500):** `unitCost = $0.00` on priced inventory item (`SUSPECT_ZERO_COST`).
- **C04 (250):** Deleted variant (`variant = null`).
- **C05 (1,200):** Supplier cost drift (historical snapshot vs current cost).
- **C06 (350):** Custom line item without catalog variant.
- **C07 (250):** Missing cost engineered so $P_{\text{upper}} < 0$ (`CONFIRMED_LOSS`).
- **C08 (250):** Missing cost with headroom within 1% of $C$.

---

### Group D: Gateway, Tender & Tax (6,100 Orders)
- **D01 (1,500):** Non-Shopify Payments gateway (PayPal, Stripe; fee list empty).
- **D02 (700):** Manual / Cash on Delivery / Bank Deposit (zero fees by design).
- **D03 (400):** Split tender with gift card + credit card.
- **D04 (350):** Pre-capture authorized-only payment.
- **D05 (150):** Voided order payment.
- **D06 (1,200):** Multi-currency order (presentment currency $\ne$ shop currency).
- **D07 (1,000):** Tax-inclusive store pricing with coupon discount.
- **D08 (200):** Tax-exempt customer order.
- **D09 (200):** Payment dispute / chargeback fee.
- **D10 (300):** Gift card purchase (excluded from merchandise revenue).
- **D11 (100):** Tip / non-inventory charge.

---

### Group E: Operational & Boundary Cases (2,300 Orders)
- **E01 (250):** Cancelled before fulfillment.
- **E02 (50):** Cancelled after partial fulfillment.
- **E03 (150):** 100% off promotional free order ($C = 0$).
- **E04 (150):** Draft order with custom merchant markdown.
- **E05 (100):** Exact breakeven ($P = 0$ by construction).
- **E06 (100):** Rounding boundary conditions.
- **E07 (100):** Shopify test order (`test = true`).
- **E08 (200):** Product bundle lines.
- **E09 (400):** Digital products (structural zero shipping).
- **E10 (500):** POS in-person / local pickup.
- **E11 (200):** Cross-border international shipping with duties.
- **E12 (100):** High-value order outlier ($\ge 50\times$ median order value).
