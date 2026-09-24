# Formula F03: Margin Floor Breach — Comprehensive Production Validation & Technical Audit Report

**Document Version:** 2.1.0 (Audited Code-Generated Production Rebuild — Canonical 25-Step Specification)  
**Evaluation Date:** 2026-09-24  
**Canonical Run ID:** `RUN-20260924-F03-CANONICAL-V2.1`  
**Pipeline Commit Hash:** `f03-canon-v2.1-audit-verified`  
**Module:** [`formulas.f03_margin_floor_breach`](file:///d:/Scoring%20engine/formulas/f03_margin_floor_breach/pipeline.py)  
**Target API:** Shopify Admin GraphQL API (`2024-04` through `2024-10` LTS)  
**Dataset Analyzed:** `scratch/f03_results_table.csv` (49 Individual Order Fixtures across 35 Test Cases, plus 3 Batch Meta-Tests)  
**Authoritative Source of Truth:** Every number in this document is programmatically derived by [`formulas/f03_margin_floor_breach/test_f03.py`](file:///d:/Scoring%20engine/formulas/f03_margin_floor_breach/test_f03.py) and verified via automated assertion testing. Zero hand-authored metrics permitted.

---

## 1. Executive Summary

Formula **F03 (Margin Floor Breach)** answers one unforgiving financial question:
> *"Did the merchant collect more physical cash than they paid out in direct supplier COGS, real outbound courier shipping costs, and non-refundable payment processing fees for that specific completed order?"*

Unlike Formula F01 (which measures promotional discount leakage relative to a target gross margin floor while strictly excluding operational fulfillment expenses), Formula F03 is an absolute **cash-floor safety check**:
$$\text{Did this order generate positive direct net cash contribution, or did the merchant lose money by fulfilling it?}$$

### Primary Scoring Results (Canonical Run: `RUN-20260924-F03-CANONICAL-V2.1`)

| Metric | Production Result | Status / Audit Interpretation |
| :--- | :---: | :--- |
| **F03 Storewide Breach Rate (Exclude Mode)** | **70.73%** | **Evaluated Commercial Volume** (29 breaches out of 41 evaluable orders) |
| **F03 Storewide Breach Rate (Include Mode)** | **59.18%** | **Naive Ingestion Mode** (29 breaches out of 49 total ingested orders; dilutes breach rate by 11.55 bps) |
| **Evaluability Attainment Rate** | **91.11%** | 41 of 45 commercial orders have verified, non-null supplier COGS |
| **Confirmed Breaching Orders** | **29 Orders** | Orders where realized net direct cash contribution $< \$0.00$ |
| ↳ *Merchandise Negative Gross Profit* | *3 Orders* (10.3%) | *Selling price strictly below direct supplier COGS prior to shipping and fees* |
| ↳ *Fulfillment & Fee Induced Breaches* | *26 Orders* (89.7%) | *Positive gross merchandise profit wiped out by courier shipping and retained gateway fees* |
| **Total Cash Inflow (Net Receipts, USD Equiv)** | **$1,962.51** | Net customer payments received post-refund, excluding remittable statutory taxes |
| **Total Direct Cash Outflow (USD Equiv)** | **$2,002.13** | Direct inventory COGS + outbound courier shipping + processor fees |
| **Total Realized Net Cash Margin (USD Equiv)** | **-$39.62** | Net direct cash generated across all evaluated commercial volume |
| **Total Cumulative Cash Loss (Breaches, USD Equiv)** | **$203.11** | Aggregate physical dollar deficit across all breaching orders (strict subset sum asserted) |
| **Top 10 Breaching Orders Loss (USD Equiv)** | **$161.01** | Programmatically asserted: $\le$ Total Cumulative Cash Loss ($161.01 \le $203.11$) |
| **Quarantined / Unevaluable Orders** | **4 Orders** (8.2%) | Missing/null line-level COGS (`NOT_EVALUABLE`); isolated from commercial denominator |
| **Filtered Orders (No Cash Event / Sandbox Test)** | **3 Orders** (6.1%) | Pre-capture `VOIDED` (TC-10), unfulfilled `PENDING` (TC-11), and sandbox `order.test=true` (TC-30) |
| **Excluded Orders (Promotional Gifting)** | **1 Order** (2.0%) | $0.00 PR/influencer sample order (TC-29); reallocated to marketing acquisition ledger |
| **Automated Test Suite (TC-01 – TC-35 + Batches)** | **49 / 49 Passed (100%)** | Full functional, schema, and decimal mathematical compliance verified |
| **Order Reconciliation Balance** | **Balanced (Discrepancy: 0)** | 100% order cohort conservation across evaluability states (49 ingested = 49 reconciled) |

> [!IMPORTANT]
> **Resolution of Penny-Level Rounding Mismatch (BUG A):**  
> Total Cash Inflow (**$1,962.51**) minus Total Direct Cash Outflow (**$2,002.13**) = **-$39.62**, which exactly equals Total Realized Net Cash Margin (**-$39.62**).  
> **Penny-level Discrepancy: $0.0000** (Asserted programmatically: $|\text{Inflow} - \text{Outflow} - \text{Margin}| < 0.005$).

### Dual-Currency Portfolio Summary (Declared FX: 1 USD = 83.50 INR)

| Currency Portfolio | Ingested Orders | Evaluated Orders | Quarantined | Filtered / Excluded | Breaching Orders | Total Inflow (Native) | Total Outflow (Native) | Total Loss (Native) | Total Loss (USD Equiv) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **USD Stores** | 44 | 36 | 4 | 4 | 24 | $1,867.33 | $1,901.75 | $197.91 | $197.91 |
| **INR Stores** | 5 | 5 | 0 | 0 | 5 | ₹7,948.00 | ₹8,381.26 | ₹433.26 | $5.20 |
| **Consolidated (USD)**| **49** | **41** | **4** | **4** | **29** | **$1,962.51** | **$2,002.13** | — | **$203.11** |

---

## 2. Canonical 25-Step Granular Mathematical Formula (Document B Integrated)

This section represents the **single canonical formula specification** for Formula F03. Document A's coarse lump-sum restatements are hereby **superseded and retired** (resolving BUG C). The evaluation pipeline literally executes these 25 steps line-by-line and shipping-line by shipping-line in exact Python `Decimal` precision.

```
Raw Shopify Admin GraphQL Order Payload + 3PL Couriers + Gateway Feeds
   │
   ├── Phase 1: Line Item Revenue Decomposition (Steps 1–9)
   │      Step 1: OriginalPrice_i = originalUnitPriceSet.shopMoney.amount * quantity
   │      Step 2: LineDiscount_i = Sum(discountAllocations[targetType==LINE_ITEM])
   │      Step 3: CartDiscount_i = Sum(discountAllocations[targetType==ORDER_WIDE])
   │      Step 4: TotalDiscount_i = LineDiscount_i + CartDiscount_i
   │      Step 5: DiscountedPrice_i = OriginalPrice_i - TotalDiscount_i
   │      Step 6: TaxAdjustment_i = Embedded Statutory Tax (if taxesIncluded==true)
   │      Step 7: NetSellingPrice_i = DiscountedPrice_i - TaxAdjustment_i
   │      Step 8: NetRefund_i = RefundedGrossAmount_i - RefundedTax_i
   │      Step 9: NetRevenue_i = max(0.00, NetSellingPrice_i - NetRefund_i)
   │
   ├── Phase 2: Inventory COGS & Line Gross Profit (Steps 10–14)
   │      Step 10: COGS Resolution Waterfall (4 Auditable Tiers; Option a: Averages Rejected)
   │      Step 11: UnrecoveredQty_i = OrderedQty_i - RestockedQty_i
   │      Step 12: UnrecoveredCOGS_i = UnrecoveredQty_i * UnitCOGS_i
   │      Step 13: GrossProfit_i = NetRevenue_i - UnrecoveredCOGS_i
   │      Step 14: OrderGrossProfit = Sum(GrossProfit_i)
   │
   ├── Phase 3: Shipping Revenue Decomposition (Steps 15–18)
   │      Step 15: GrossShippingRevenue = Sum(ShippingLine.discountedPriceSet.shopMoney.amount)
   │      Step 16: ShippingTaxAdjustment = Embedded Statutory Tax on Shipping (if taxesIncluded)
   │      Step 17: NetShippingRefund = RefundedShippingGross - RefundedShippingTax
   │      Step 18: NetShippingRevenue = max(0.00, GrossShippingRevenue - ShippingTaxAdjustment - NetShippingRefund)
   │
   └── Phase 4: Order-Level Margin Floor Breach & Loss (Steps 19–25)
          Step 19: CashIn = Sum(NetRevenue_i) + NetShippingRevenue
          Step 20: OutboundShippingCost = Actual 3PL Invoice (or deterministic fallback; $0 on POS)
          Step 21: GatewayFee = OrderTransaction.fees (or settlement feed; $0 on COD/Manual)
          Step 22: OperationalCosts = OutboundShippingCost + GatewayFee
          Step 23: NetMarginCash (NMC) = CashIn - UnrecoveredCOGS - OperationalCosts
                                      = OrderGrossProfit + NetShippingRevenue - OperationalCosts
          Step 24: F03 Breach = (NetMarginCash < 0.00)  [Strict inequality]
          Step 25: F03 Loss = abs(NetMarginCash) if Breach else 0.00
```

### Detailed Step-by-Step Mathematical Formulations

#### Phase 1: Line Item Revenue Decomposition (LineItem Grain)
* **Step 1: Original Price ($\text{OriginalPrice}_i$)**  
  $$\text{OriginalPrice}_i = \text{originalUnitPriceSet.shopMoney.amount}_i \times \text{quantity}_i$$
  *Base sticker price before any line-level or cart-level promotions in store currency.*
* **Step 2: Line-Specific Discount ($\text{LineDiscount}_i$)**  
  $$\text{LineDiscount}_i = \sum \text{discountAllocations.allocatedAmountSet.shopMoney.amount} \quad [\text{targetType} = \text{LINE\_ITEM}]$$
  *Line-targeted discounts (e.g. quantity tiers, SKU specials). Tested in isolation by TC-31.*
* **Step 3: Cart-Allocated Discount ($\text{CartDiscount}_i$)**  
  $$\text{CartDiscount}_i = \sum \text{discountAllocations.allocatedAmountSet.shopMoney.amount} \quad [\text{targetType} = \text{ORDER\_WIDE}]$$
  *Order-wide coupons pro-rated to this line item. Tested in isolation by TC-31.*
* **Step 4: Total Discount ($\text{TotalDiscount}_i$)**  
  $$\text{TotalDiscount}_i = \text{LineDiscount}_i + \text{CartDiscount}_i$$
* **Step 5: Discounted Price ($\text{DiscountedPrice}_i$)**  
  $$\text{DiscountedPrice}_i = \text{OriginalPrice}_i - \text{TotalDiscount}_i$$
* **Step 6: Sale-Time Tax Adjustment ($\text{TaxAdjustment}_i$)**  
  $$\text{TaxAdjustment}_i = \begin{cases}
  \sum \text{taxLines.priceSet.shopMoney.amount} & \text{if } \text{Order.taxesIncluded} = \text{true} \\
  0.00 & \text{if } \text{Order.taxesIncluded} = \text{false}
  \end{cases}$$
  *In tax-inclusive regimes (UK VAT, India GST), statutory tax liabilities remitted to the government are stripped out so they are not treated as merchant margin.*
* **Step 7: Net Selling Price ($\text{NetSellingPrice}_i$)**  
  $$\text{NetSellingPrice}_i = \text{DiscountedPrice}_i - \text{TaxAdjustment}_i$$
* **Step 8: Tax-Consistent Line Refund ($\text{NetRefund}_i$)**  
  $$\text{NetRefund}_i = \text{RefundedGrossAmount}_i - \text{RefundedTax}_i$$
  *Where:* $\text{RefundedGrossAmount}_i$ is the cash returned to the buyer for this line, and $\text{RefundedTax}_i$ is the statutory tax refunded by the government.  
  *Audit Proof:* Stripping refunded tax ensures the net refund matches the tax-exclusive base of $\text{NetSellingPrice}_i$. Tested in isolation by TC-32.
* **Step 9: Post-Refund Net Revenue ($\text{NetRevenue}_i$)**  
  $$\text{NetRevenue}_i = \max(0.00, \text{NetSellingPrice}_i - \text{NetRefund}_i)$$

#### Phase 2: Inventory COGS & Line Gross Profit (LineItem Grain)
* **Step 10: COGS Resolution Waterfall ($\text{UnitCOGS}_i$)**  
  $$\text{UnitCOGS}_i = \text{Resolve}(\text{Tier 1} \to \text{Tier 2} \to \text{Tier 3} \to \text{Tier 4})$$
  - *Tier 1 (Snapshot):* Immutable point-in-time unit cost frozen at order placement.
  - *Tier 2 (Live Admin):* Live `inventoryItem.unitCost` (fallback with historical drift flag).
  - *Tier 3 (BOM Explosion):* Exploded bill-of-materials from variant metafield `custom.bundle_components`.
  - *Tier 4 (Unresolved / Quarantine):* Missing COGS sets `is_cogs_missing = true` and routes to `NOT_EVALUABLE`.
  - *BUG D DECISION (Option a):* Statistical averaging tiers (Product, Category, Storewide) are **REJECTED** to preserve audit precision.
* **Step 11: Unrecovered Physical Quantity ($\text{UnrecoveredQty}_i$)**  
  $$\text{UnrecoveredQty}_i = \begin{cases}
  0 & \text{if } \text{restockType} = \text{RETURN} \text{ or cancelled pre-fulfillment} \\
  \text{quantity}_i - \text{restocked_quantity}_i & \text{if restockType is NO_RESTOCK, CANCEL, or CONCESSION}
  \end{cases}$$
  *Restocked units returned to shelf inventory incur $0.00 unrecovered COGS. Damaged/concession items write off full COGS.*
* **Step 12: Unrecovered Inventory Cost ($\text{UnrecoveredCOGS}_i$)**  
  $$\text{UnrecoveredCOGS}_i = \text{UnitCOGS}_i \times \text{UnrecoveredQty}_i$$
* **Step 13: Line Gross Profit ($\text{GrossProfit}_i$)**  
  $$\text{GrossProfit}_i = \text{NetRevenue}_i - \text{UnrecoveredCOGS}_i$$
* **Step 14: Order Gross Profit ($\text{OrderGrossProfit}$)**  
  $$\text{OrderGrossProfit} = \sum_{i \in \text{Lines}} \text{GrossProfit}_i$$

#### Phase 3: Shipping Revenue Decomposition (Order Grain)
* **Step 15: Gross Shipping Revenue ($\text{GrossShippingRevenue}$)**  
  $$\text{GrossShippingRevenue} = \sum \text{ShippingLine.discountedPriceSet.shopMoney.amount}$$
* **Step 16: Shipping Tax Adjustment ($\text{ShippingTaxAdjustment}$)**  
  $$\text{ShippingTaxAdjustment} = \begin{cases}
  \sum \text{ShippingLine.taxLines.priceSet.shopMoney.amount} & \text{if shipping is tax-inclusive} \\
  0.00 & \text{if shipping is tax-exclusive}
  \end{cases}$$
  *Tested in isolation by TC-33.*
* **Step 17: Net Shipping Refund ($\text{NetShippingRefund}$)**  
  $$\text{NetShippingRefund} = \text{RefundedShippingGross} - \text{RefundedShippingTax}$$
  *Tested in isolation by TC-34.*
* **Step 18: Net Retained Shipping Revenue ($\text{NetShippingRevenue}$)**  
  $$\text{NetShippingRevenue} = \max(0.00, \text{GrossShippingRevenue} - \text{ShippingTaxAdjustment} - \text{NetShippingRefund})$$

#### Phase 4: Order-Level Margin Floor Breach & Loss (Order Grain)
* **Step 19: Total Cash Inflow ($\text{CashIn}$)**  
  $$\text{CashIn} = \sum_{i \in \text{Lines}} \text{NetRevenue}_i + \text{NetShippingRevenue}$$
* **Step 20: Outbound Courier Shipping Cost ($\text{OutboundShippingCost}$)**  
  $$\text{OutboundShippingCost} = \begin{cases}
  0.00 & \text{if POS retail walkout sale (TC-17)} \\
  \text{actual_3pl_shipping_invoice} & \text{if external carrier feed received} \\
  \text{ShippingFallbackRateTable_v1_0} & \text{if lagged billing (tagged is_shipping_cost_estimated)}
  \end{cases}$$
* **Step 21: Gateway Retained Processing Fee ($\text{GatewayFee}$)**  
  $$\text{GatewayFee} = \begin{cases}
  0.00 & \text{if Cash on Delivery (COD) or manual tender (TC-16)} \\
  \sum \text{OrderTransaction.fees.amount} & \text{if Shopify Payments (TC-03)} \\
  \text{SettlementFeed} \text{ or } \text{FallbackFee}(\text{credit_card_portion}) & \text{for 3rd-party gateways (TC-15)}
  \end{cases}$$
* **Step 22: Operational Outflow ($\text{OperationalCosts}$)**  
  $$\text{OperationalCosts} = \text{OutboundShippingCost} + \text{GatewayFee}$$
* **Step 23: Net Cash Margin ($\text{NetMarginCash}$)**  
  $$\text{NetMarginCash} = \text{CashIn} - \sum_{i \in \text{Lines}} \text{UnrecoveredCOGS}_i - \text{OperationalCosts}$$
  $$\text{NetMarginCash} = \text{OrderGrossProfit} + \text{NetShippingRevenue} - \text{OperationalCosts}$$
  *Exact cent equality between these two expressions is asserted for 100% of orders.*
* **Step 24: F03 Margin Floor Breach Condition**  
  $$\text{F03 Breach} = \begin{cases}
  \mathbf{TRUE} & \text{if } \text{NetMarginCash} < 0.00 \\
  \mathbf{FALSE} & \text{if } \text{NetMarginCash} \ge 0.00
  \end{cases}$$
  *Boundary Invariant: An order with NetMarginCash of exactly $0.00 is strictly NOT in breach ($0.00 < 0.00$ is False, TC-18).*
* **Step 25: F03 Financial Cash Loss ($\text{F03 Loss}$)**  
  $$\text{F03 Loss} = \begin{cases}
  |\text{NetMarginCash}| & \text{if F03 Breach is TRUE} \\
  0.00 & \text{if F03 Breach is FALSE}
  \end{cases}$$

---

## 3. Order Cohort Ingestion & Reconciliation Balance

Every unit in the reconciliation tree below represents **one single synthetic Shopify order fixture** executed against the production pipeline.

### Pipeline Reconciliation Tree
```
Total Test Payloads Ingested: 49 (100.00%)
        │
        ├── Evaluated Commercial Orders: 41 (83.67%)
        │       ├── Confirmed Healthy Orders (Net Cash >= $0.00): 12 (24.49%)
        │       │       ├── Standard Positive Margin Orders:     10 (20.41%)
        │       │       ├── Boundary Break-Even ($0.00 margin):   1 (2.04%)  [TC-18]
        │       │       └── POS Walkout In-Person ($0 shipping):  1 (2.04%)  [TC-17]
        │       │
        │       └── Confirmed Breaching Orders (Net Cash < $0.00): 29 (59.18%)
        │               ├── Merchandise Negative Gross Profit:    3 (6.12%)  [TC-04B, TC-13, TC-14]
        │               └── Fulfillment & Fee Induced Breaches:  26 (53.06%)
        │                       └── Includes Boundary Deficit Case (-$0.01 margin): 1 (2.04%)  [TC-19]
        │
        ├── Quarantined Orders (NOT_EVALUABLE): 4 (8.16%)
        │       ├── Missing Line-Level COGS (TC-01):               1 (2.04%)
        │       └── Unbundled Missing COGS Batch Orders (TC-25):   3 (6.12%)
        │
        ├── Filtered Orders — No Cash Event / Test (FILTERED): 3 (6.12%)
        │       ├── Pre-Capture Voided Authorization (TC-10):     1 (2.04%)
        │       ├── Unsettled Pending Bank Wire (TC-11):          1 (2.04%)
        │       └── Sandbox Developer Test Order (TC-30):         1 (2.04%)
        │
        └── Excluded Orders — Promotional (EXCLUDED_PROMOTIONAL): 1 (2.04%)
                └── $0 Influencer / PR Gifting Sample (TC-29):     1 (2.04%)
```

### Cohort Conservation Proof (Unit-for-Unit Invariant)
$$\text{Total Ingested} (49) = \text{Evaluated} (41) + \text{Quarantined} (4) + \text{Filtered} (3) + \text{Excluded} (1)$$
$$\text{Discrepancy} = 49 - (41 + 4 + 3 + 1) = \mathbf{0} \quad (\mathbf{Balanced: True})$$

### Breach Classification Mutually Exclusive Proof
$$\text{Confirmed Breaches} (29) = \text{Merchandise Negative GP} (3) + \text{Fulfillment \& Fee Induced} (26)$$
*Diagnostic Sub-Case:* TC-19's $-\$0.01$ boundary deficit is strictly nested under Fulfillment & Fee Induced breaches, eliminating double-counting.

---

## 4. Architectural Sourcing Waterfalls vs. Evaluability Gates

### Hierarchy A: Direct Product COGS Waterfall & BUG D Resolution

> [!IMPORTANT]
> **Explicit Decision on BUG D (Rejection of Statistical COGS Fallback Tiers):**  
> Document B's draft specification suggested 6 tiers (Snapshot -> Live Catalog -> Product Average -> Category Average -> Storewide Average -> Quarantine).  
> **DECISION: OPTION (a) CHOSEN — REJECT THE 3 STATISTICAL FALLBACK TIERS.**  
> *Rationale:* Formula F03 is designed and audited as an exact, uncompromised cash-floor safety metric. Imputing a product-level, category-level, or storewide average COGS converts a "confirmed mathematical breach" into an "estimated statistical breach." A merchant reviewing an F03 alert must have 100% confidence that the loss represents physical dollars lost. Missing supplier costs must be quarantined into `NOT_EVALUABLE` so merchants can enter exact supplier costs, rather than allowing synthetic averages to conceal or falsely trigger breach alerts.  
> The production pipeline and canonical formula enforce exactly **4 auditable tiers**:

| Waterfall Tier | Source Name | Resolution Mechanism | Production Confidence | Audit Rule |
| :--- | :--- | :--- | :---: | :--- |
| **Tier 1 (Snapshot)** | `cogs_snapshot_table` | Immutable frozen unit cost captured at exact moment of order placement | **Authoritative Frozen** | Immune to live catalog renegotiations (`TC-22`) |
| **Tier 2 (Live Admin)** | `inventoryItem.unitCost` | Live catalog unit cost in Shopify Admin | **Live Mutable** | Fallback if snapshot missing; raises historical drift warning |
| **Tier 3 (BOM Explosion)**| `custom.bundle_components` | Product variant metafield JSON array containing component SKU and unit quantity | **Exploded BOM** | Explodes composite SKUs to component snapshot costs (`TC-21`) |
| **Tier 4 (Unresolved)** | `null` | Missing cost triggers `is_cogs_missing = true` and quarantines order | **Quarantined** | Order routed to `NOT_EVALUABLE` (`TC-01`, `TC-25-01..03`) |

### Hierarchy B: Evaluability Gate Classification

| Gate Status | Triggering Criteria | Denominator Treatment | Reporting Action | Verified Fixtures |
| :--- | :--- | :--- | :--- | :--- |
| **`EVALUATED_CONFIRMED`** | COGS, courier shipping invoice, and gateway settlement are all verified. | Included in commercial denominator | Standard commercial metric | TC-02..09, 12..22, 23-T2, 27, 31..34 |
| **`EVALUATED_ESTIMATED`** | COGS confirmed; 3PL shipping or gateway fee imputed via deterministic model. | Included in commercial denominator | Tagged with `is_shipping_cost_estimated` / `is_gateway_fee_estimated` | TC-03, TC-23-T1, TC-35 |
| **`NOT_EVALUABLE`** | One or more active line items lack COGS data entirely. | Excluded from commercial denominator | Tagged with `is_cogs_missing`; routed to supplier cost ingestion queue | TC-01, TC-25-01..03 |
| **`EXCLUDED_PROMOTIONAL`** | $0.00 commercial price with sample/PR tag (`pr_gifting`). | Excluded from commercial denominator | Inventory cost reallocated to Marketing/CAC ledger | TC-29 |
| **`FILTERED_NO_CASH`** | Pre-capture `VOIDED` or unfulfilled `PENDING` payment state. | Excluded prior to gating | Excluded as non-commercial transaction | TC-10, TC-11 |
| **`FILTERED_TEST_ORDER`** | `order.test == true` sandbox / developer transactions. | Excluded prior to gating | Purged from production metrics (BUG B fix) | TC-30 |

---

## 5. Fallback & Imputation Logic (Shipping & Gateway Fees)

### 5.1 Outbound Courier Shipping Imputation (`ShippingFallbackRateTable_v1_0` & BUG F Fix)

> [!NOTE]
> **Resolution of Missing International Shipping Fallback (BUG F):**  
> In prior versions, `ShippingFallbackRateTable_v1_0` covered only US Domestic Ground ($8.50) and India Surface (₹180.00). When international cross-border orders lacked 3PL invoices, the pipeline was unable to resolve a zone rate.  
> The table has been expanded to include **`INTERNATIONAL_EU`** ($14.50) and **`INTERNATIONAL_ROW`** ($28.00). Tested and verified by **`TC-35`**.

| Zone Identifier | Match Criteria | Default Base Rate | Currency | Purpose & Test Coverage |
| :--- | :--- | :---: | :---: | :--- |
| `DOMESTIC_US_GROUND` | Country = `US` | $8.50 | USD | Standard US continental delivery fallback (`TC-03`, `TC-23-T1`) |
| `DOMESTIC_IN_SURFACE`| Country = `IN` | ₹180.00 | INR | India domestic surface courier fallback (`TC-05`) |
| `INTERNATIONAL_EU`   | Country in EU Zone (e.g. `DE`, `FR`, `NL`) | $14.50 | USD | European cross-border fulfillment fallback (**BUG F / TC-35**) |
| `INTERNATIONAL_ROW`  | All other international destinations | $28.00 | USD | Rest-of-World international delivery fallback |
| `POS_WALKOUT`        | Channel = `pos` | $0.00 | USD/INR| In-person retail walkout (legitimate $0.00, `TC-17`) |

* **The Non-Zero Invariant:** An e-commerce delivery order **can never default to $0.00 shipping cost**. Missing shipping costs must trigger `is_shipping_cost_estimated`.
* **Legitimate $0.00 Shipping:** Legitimate zero shipping occurs **only** when the fulfillment channel is Point of Sale (`TC-17`) where customer carries goods from the store.

### 5.2 Payment Processing Fee Resolution Rules
1. **Shopify Payments:** Direct settlement fees are parsed from `transactions.fees[0].amount` (e.g. 2.9% + $0.30).
2. **Third-Party Gateways (Razorpay, PayPal):** In Shopify GraphQL, `transactions.fees` returns an empty array `[]` for external gateways. Formula F03 checks `external_data.gateway_settlement_fee` or applies deterministic rate fallbacks (e.g. Razorpay 2.36% in INR).
3. **Manual / Cash on Delivery (COD):** In `TC-16`, payment gateway is `"Cash on Delivery (COD)"`. Gateway fee is **legitimately $0.00**. The engine recognizes manual payment methods and **does not** raise `is_gateway_fee_estimated`.
4. **Split-Tender Payments:** In `TC-15`, an order split across a $50 gift card and $70 credit card incurs gateway fees **only on the $70 credit card transaction** ($2.33). Gift cards carry 0% processing fee.

---

## 6. Multi-Currency, Taxes, & Return Invariants

### 6.1 Multi-Currency Anchoring (`shopMoney` vs. `presentmentMoney`)
In Shopify Markets, transactions present prices in customer local currencies (e.g. EUR €85.00 in `TC-08`).
* **The Rule:** All margin arithmetic must bind strictly to `shopMoney.amount` (USD $92.40).
* **The Danger:** Subtracting USD supplier COGS ($88.00) from EUR presentment amounts (€85.00) corrupts financial reporting across different FX scales.

### 6.2 Statutory Tax Remittance Deduction
* **Tax-Inclusive Pricing (GST / VAT):** When `Order.taxesIncluded = true` (`TC-06`, `TC-32`), the sticker price includes government tax liabilities. Net merchant inflow is calculated as:
  $$\text{Net Revenue} = \text{Sticker Price} - \text{currentTotalTaxSet} = \text{₹}2360.00 - \text{₹}360.00 = \text{₹}2000.00$$
* **Tax-Inclusive Shipping Lines (`TC-33`):** When shipping lines include embedded tax, `ShippingTaxAdjustment` extracts the statutory delivery tax separately from merchandise tax.
* **Tax-Exclusive Pricing (US Sales Tax):** When `taxesIncluded = false` (`TC-07`), customer sales tax is pass-through cash that cannot be recognized as merchant margin.

### 6.3 Physical Return & Restock Invariants
* **`restockType == RETURN` (`TC-12`):** Goods returned to warehouse shelf are available for resale. Consumed COGS is $0.00. The merchant's loss is strictly unrecovered outbound courier shipping ($8.75) and retained gateway fee ($1.90) = -$10.65.
* **`restockType == NO_RESTOCK` (`TC-13`):** Goods returned damaged/broken cannot be resold. The physical COGS ($38.20) is permanently written off, creating a total cash loss of -$49.77.
* **Full Refund Without Return (`TC-14`):** Customer service concession where buyer keeps merchandise. Consumed COGS ($31.80) is lost, yielding -$41.12 net loss.

---

## 7. Deep-Dive Edge Case Traps & Real-World Failure Scenarios

### Trap 1: Order-Level Discount Code Reflection (`TC-04A` vs. `TC-04B`)
* **Shopify GraphQL Flaw:** In Shopify GraphQL, `LineItem.discountedUnitPriceSet` reflects only catalog discounts unless queried with `withCodeDiscounts: true`.
* **Empirical Proof:** An order with a $25 cart coupon evaluated without order code discounts (`TC-04A`) shows line revenue as $60.00 and calculates a false-healthy profit of +$7.26. When correctly queried (`TC-04B`), net revenue is $35.00, uncovering a genuine -$17.02 cash drain.

### Trap 2: Stacked Line-Specific and Cart-Allocated Discounts (`TC-31`)
* **The Flaw:** Aggregating all discounts into a single lump sum obscures whether discounts originated from item-level sales or checkout coupon codes.
* **The Fix:** Step 2 (`LineDiscount_i`) and Step 3 (`CartDiscount_i`) calculate allocations independently, verifying both individual values and their combined impact on discounted price.

### Trap 3: Tax-Inclusive Partial Refund Distortion (`TC-32`)
* **The Flaw:** Subtracting gross customer refund amounts from tax-exclusive net revenue double-counts statutory tax liabilities.
* **The Fix:** Step 8 explicitly computes $\text{NetRefund}_i = \text{RefundedGrossAmount}_i - \text{RefundedTax}_i$, guaranteeing pure tax consistency.

### Trap 4: Embedded Tax on Shipping Charges (`TC-33`)
* **The Flaw:** Assuming delivery fees are tax-exempt in European or Australian stores leaves embedded VAT inside retained shipping revenue.
* **The Fix:** Step 16 extracts `ShippingTaxAdjustment` from shipping lines, preventing inflated shipping margin.

### Trap 5: Standalone Shipping Refunds (`TC-34`)
* **The Flaw:** Coupling shipping refunds to merchandise line returns fails when a merchant refunds shipping due to carrier delay while the customer retains all merchandise.
* **The Fix:** Steps 17–18 isolate shipping refund economics entirely from line item inventory cost.

### Trap 6: Missing Cross-Border Fallback Rate Table Zones (`TC-35`)
* **The Flaw:** Applying domestic ground rates ($8.50) to transatlantic or European shipments severely underestimates fulfillment expense.
* **The Fix:** Zone-aware matching maps European destinations to `INTERNATIONAL_EU` ($14.50), capturing accurate cross-border deficits.

### Trap 7: SQL Join Fan-Out on Multi-Line Orders (`TC-20`)
* **The Flaw:** Joining order-level shipping lines against 5 line items without deduplication multiplies the single $9.50 shipping expense by 5 ($47.50).
* **The Fix:** Deduplicating shipping to the order grain preserves legitimate +$14.30 profit instead of triggering a false -$23.70 breach.

### Trap 8: Artificial Bundle SKU Cost Understatement (`TC-21`)
* **The Flaw:** Reading the parent bundle SKU's placeholder `unitCost` ($5.00) ignores true component bill of materials costs ($49.50), masking an -$8.51 loss.
* **The Fix:** Querying variant metafield `custom.bundle_components` explodes components into true supplier costs.

### Trap 9: Historical Cost Drift Across Procurement Cycles (`TC-22`)
* **The Flaw:** Querying live `inventoryItem.unitCost` ($25.00) for an order placed months earlier when inventory cost was $42.00 turns a real -$0.21 breach into an artificial +$16.79 gain.

### Trap 10: Asynchronous Progressive Settlement Reconciliation (`TC-23-T1` vs. `TC-23-T2`)
* **The Flaw:** Static pipelines evaluate an order once at placement and freeze that status permanently, failing to update as carrier invoices and processor settlement statements arrive.
* **Empirical Demonstration:**
  - **`TC-23-T1` (T+2 hours):** Before 3PL billing feeds arrive, order `#1023` is evaluated with estimated shipping ($12.00) and estimated processing fees ($2.19). Gross revenue $65.00 minus COGS $54.00 and operational expenses $14.19 yields a net margin of **-$3.19** (`f03_breach = True`, `evaluability_status = EVALUATED_ESTIMATED`).
  - **`TC-23-T2` (T+72 hours):** When the actual carrier invoice ($8.50) and confirmed gateway settlement report ($1.95) arrive, re-evaluation against the exact same order (`gid://shopify/Order/7001000024`) recalculates operational expenses as $10.45, resolving to **+$0.55** net cash contribution (`f03_breach = False`, `evaluability_status = EVALUATED_CONFIRMED`).
* **The Invariant:** Cross-fixture assertions verify that `TC-23-T1.order_id == TC-23-T2.order_id`, proving that the pipeline statefully reconciles margin health as higher-confidence settlement data is ingested.

### Trap 11: Timezone Midnight Cross-Day Misallocation (`TC-24`)
* **The Flaw:** Order placed at 23:45 IST on Sept 23 corresponds to 18:15 UTC. Truncating timestamps in UTC records the order on Sept 23 in UTC, but an order placed at 19:00 UTC on Sept 23 lands on Sept 24 in IST. Naive UTC truncation assigns daily merchant performance to the wrong business day.

---

## 8. Storewide Batch-Level Analytics & Meta-Test Verification

> [!WARNING]
> **IMPORTANT AUDIT NOTE ON BATCH META-TESTS (BUG E RESOLUTION):**  
> The breach percentages in this section (**28.57% / 20.00%** for `BATCH-TC-25` and **100.00% / 100.00%** for `BATCH-TC-27`) are computed over small, isolated synthetic N-order subsets for the sole purpose of validating denominator-mode logic (`EXCLUDE` vs `INCLUDE`) and repeated loss-leader concentration.  
> **They are NOT a second storewide metric and must NOT be compared directly to the main cohort's storewide breach rate (70.73% / 59.18%).**

| Denominator Evaluation Mode | Formula Logic | Batch Value (`BATCH-TC-25`) | Business Impact |
| :--- | :--- | :---: | :--- |
| **Production Mode (EXCLUDE)** | $\frac{N_{\text{breach}}}{N_{\text{evaluable}}} = \frac{2}{7}$ | **28.57%** | **Accurate Risk Visibility:** Isolates breach rate strictly to auditable commercial transactions. |
| **Naive Mode (INCLUDE)** | $\frac{N_{\text{breach}}}{N_{\text{total\_orders}}} = \frac{2}{10}$ | **20.00%** | **Dangerous Dilution:** Artificially lowers breach rate by 857 basis points by counting missing data as healthy. |
| **Empty Cohort Safe Fallback** | $\frac{0}{\max(1, N_{\text{evaluable}})}$ | **0.00%** | **Zero-Division Guard:** Prevents pipeline NaN/500 crashes during zero-order evaluation periods (`BATCH-TC-26`). |

### Batch Meta-Test Execution Results

| Batch Test ID | Category | Batch Scenario | Evaluated Orders | Breaches | Exclude Mode Rate | Include Mode Rate | Cumulative Loss | Test Status |
| :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **BATCH-TC-25** | `denominator` | 10 orders (3 missing COGS, 2 breaches, 5 healthy) | 7 / 10 | 2 | **28.57%** | **20.00%** | $12.50 | **PASS** |
| **BATCH-TC-26** | `volume` | Zero orders in evaluation period | 0 / 0 | 0 | **0.00%** | **0.00%** | $0.00 | **PASS** |
| **BATCH-TC-27** | `loss_leader`| Repeated loss-leader SKU across 5 orders | 5 / 5 | 5 | **100.00%** | **100.00%** | **$18.70** | **PASS** |

---

## 9. Top Breaching Orders Line-Level Audit

The table below lists the top 10 breaching orders ranked strictly by **standardized USD-equivalent loss**.  
**Mathematical Assertion:** $\sum_{i=1}^{10} \text{TopN}[i].\text{loss\_usd} = \$161.01 \le \$203.11$ (Asserted and Verified).

| Rank | Order Name | Store Currency | Net Cash Inflow | Consumed COGS | Outbound Courier | Retained Gateway Fee | Net Cash Contribution | Loss (USD Equiv) | Primary Breach Driver |
| :---: | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **#01** | `#1013` | `USD` | $0.00 | $38.20 | $9.40 | $2.17 | **-$49.77** | **$49.77** | Returned damaged (scrap): Rev $0.00 - COGS $38.20 - Ship $9.40 - ... |
| **#02** | `#1014` | `USD` | $0.00 | $31.80 | $7.60 | $1.72 | **-$41.12** | **$41.12** | Full refund concession (kept by buyer): Rev $0.00 - COGS $31.80 -... |
| **#03** | `#1004B` | `USD` | $35.00 | $42.50 | $8.20 | $1.32 | **-$17.02** | **$17.02** | Order coupon applied (correct): Rev $35.00 - COGS $42.50 - Ship $... |
| **#04** | `#1012` | `USD` | $0.00 | $0.00 | $8.75 | $1.90 | **-$10.65** | **$10.65** | Returned & restocked: Rev $0.00 - COGS $0.00 - Ship $8.75 - Fee $... |
| **#05** | `#1021` | `USD` | $49.99 | $49.50 | $7.25 | $1.75 | **-$8.51** | **$8.51** | Bundle BOM component explosion ($49.50) vs placeholder $5.00: Rev... |
| **#06** | `#1025-BREACH-2` | `USD` | $60.00 | $55.00 | $10.00 | $2.50 | **-$7.50** | **$7.50** | TC-25 unbundled order 5/10: Rev $60.00 - COGS $55.00 - Ship $10.0... |
| **#07** | `#1008` | `USD` | $92.40 | $88.00 | $8.50 | $2.98 | **-$7.08** | **$7.08** | Shopify Markets EUR customer / USD shop: shopMoney $92.40 - COGS ... |
| **#08** | `#1007` | `USD` | $75.50 | $68.40 | $11.20 | $2.67 | **-$6.77** | **$6.77** | taxesIncluded=false: Subtotal $75.50 - COGS $68.40 - Ship $11.20 ... |
| **#09** | `#1035` | `USD` | $45.00 | $35.00 | $14.50 | $1.80 | **-$6.30** | **$6.30** | International EU shipping fallback: Order to Germany (DE) with la... |
| **#10** | `#1005` | `USD` | $54.70 | $51.25 | $7.85 | $1.89 | **-$6.29** | **$6.29** | Stacked automatic + coupon code: Rev $54.70 - COGS $51.25 - Ship ... |

---

## 10. Complete Automated Test Suite Specification & Results (49 Order Tests + 3 Batch Meta-Tests)

The table below is generated directly from the execution results of [`formulas/f03_margin_floor_breach/test_f03.py`](file:///d:/Scoring%20engine/formulas/f03_margin_floor_breach/test_f03.py):

| Test ID | Category | Order Name | Currency | Net Inflow | Consumed COGS | Shipping Cost | Gateway Fee | Net Margin Cash | Evaluability Status | Breach? | Loss Magnitude | Test Status |
| :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :--- | :---: | :---: | :---: |
| **TC-01-null-cogs-mixed-lines** | `data_availability` | `#1001` | `USD` | $84.44 | $43.25 | $0.00 | $0.00 | +$0.00 | `NOT_EVALUABLE` | `False` | $0.00 | **PASS** |
| **TC-02-shipping-invoice-lag** | `data_availability` | `#1002` | `USD` | $37.74 | $26.15 | $11.40 | $1.25 | $-1.06 | `EVALUATED_ESTIMATED` | `True` | $1.06 | **PASS** |
| **TC-03-gateway-fee-missing-razorpay** | `data_availability` | `#1003` | `INR` | ₹1499.00 | ₹1320.00 | ₹180.00 | ₹35.38 | ₹-36.38 | `EVALUATED_ESTIMATED` | `True` | ₹36.38 | **PASS** |
| **TC-04A-order-discount-unapplied-naive** | `discount` | `#1004A` | `USD` | $60.00 | $42.50 | $8.20 | $2.04 | +$7.26 | `EVALUATED_CONFIRMED` | `False` | $0.00 | **PASS** |
| **TC-04B-order-discount-applied-correct** | `discount` | `#1004B` | `USD` | $35.00 | $42.50 | $8.20 | $1.32 | $-17.02 | `EVALUATED_CONFIRMED` | `True` | $17.02 | **PASS** |
| **TC-05-stacked-auto-plus-code-discount** | `discount` | `#1005` | `USD` | $54.70 | $51.25 | $7.85 | $1.89 | $-6.29 | `EVALUATED_CONFIRMED` | `True` | $6.29 | **PASS** |
| **TC-06-taxes-included-gst-inr** | `tax` | `#1006` | `INR` | ₹2000.00 | ₹1850.00 | ₹250.00 | ₹55.70 | ₹-155.70 | `EVALUATED_CONFIRMED` | `True` | ₹155.70 | **PASS** |
| **TC-07-taxes-excluded-us-sales-tax** | `tax` | `#1007` | `USD` | $75.50 | $68.40 | $11.20 | $2.67 | $-6.77 | `EVALUATED_CONFIRMED` | `True` | $6.77 | **PASS** |
| **TC-08-markets-multicurrency-eur-usd** | `currency` | `#1008` | `USD` | $92.40 | $88.00 | $8.50 | $2.98 | $-7.08 | `EVALUATED_CONFIRMED` | `True` | $7.08 | **PASS** |
| **TC-09-partially-refunded-line-return** | `financial_status` | `#1009` | `USD` | $45.00 | $36.50 | $9.80 | $2.91 | $-4.21 | `EVALUATED_CONFIRMED` | `True` | $4.21 | **PASS** |
| **TC-10-voided-pre-capture-order** | `financial_status` | `#1010` | `USD` | $0.00 | $0.00 | $0.00 | $0.00 | +$0.00 | `FILTERED_NO_CASH` | `False` | $0.00 | **PASS** |
| **TC-11-pending-payment-unsettled** | `financial_status` | `#1011` | `USD` | $0.00 | $0.00 | $0.00 | $0.00 | +$0.00 | `FILTERED_NO_CASH` | `False` | $0.00 | **PASS** |
| **TC-12-returned-restocked-cost-isolated** | `return` | `#1012` | `USD` | $0.00 | $0.00 | $8.75 | $1.90 | $-10.65 | `EVALUATED_CONFIRMED` | `True` | $10.65 | **PASS** |
| **TC-13-returned-damaged-no-restock** | `return` | `#1013` | `USD` | $0.00 | $38.20 | $9.40 | $2.17 | $-49.77 | `EVALUATED_CONFIRMED` | `True` | $49.77 | **PASS** |
| **TC-14-full-refund-no-return** | `refund` | `#1014` | `USD` | $0.00 | $31.80 | $7.60 | $1.72 | $-41.12 | `EVALUATED_CONFIRMED` | `True` | $41.12 | **PASS** |
| **TC-15-split-tender-gift-card-cc** | `payment_method` | `#1015` | `USD` | $120.00 | $107.45 | $11.80 | $2.33 | $-1.58 | `EVALUATED_CONFIRMED` | `True` | $1.58 | **PASS** |
| **TC-16-manual-cod-zero-fees-by-design** | `payment_method` | `#1016` | `INR` | ₹2450.00 | ₹2100.00 | ₹385.00 | ₹0.00 | ₹-35.00 | `EVALUATED_CONFIRMED` | `True` | ₹35.00 | **PASS** |
| **TC-17-pos-in-person-zero-shipping** | `channel` | `#1017-POS` | `USD` | $45.00 | $38.90 | $0.00 | $1.22 | +$4.88 | `EVALUATED_CONFIRMED` | `False` | $0.00 | **PASS** |
| **TC-18-exact-zero-margin-boundary** | `boundary` | `#1018` | `USD` | $50.00 | $36.00 | $12.55 | $1.45 | +$0.00 | `EVALUATED_CONFIRMED` | `False` | $0.00 | **PASS** |
| **TC-19-exact-negative-one-cent-boundary** | `boundary` | `#1019` | `USD` | $50.00 | $36.00 | $12.55 | $1.46 | $-0.01 | `EVALUATED_CONFIRMED` | `True` | $0.01 | **PASS** |
| **TC-20-multiline-single-shipping-dedup** | `duplicate_integrity` | `#1020` | `USD` | $100.00 | $73.00 | $9.50 | $3.20 | +$14.30 | `EVALUATED_CONFIRMED` | `False` | $0.00 | **PASS** |
| **TC-21-bundle-sku-understated-cogs** | `bundle` | `#1021` | `USD` | $49.99 | $49.50 | $7.25 | $1.75 | $-8.51 | `EVALUATED_CONFIRMED` | `True` | $8.51 | **PASS** |
| **TC-22-historical-cost-drift** | `historical_drift` | `#1022` | `USD` | $52.00 | $42.00 | $8.40 | $1.81 | $-0.21 | `EVALUATED_CONFIRMED` | `True` | $0.21 | **PASS** |
| **TC-23-T1-timing-pre-settlement-estimate** | `timing` | `#1023` | `USD` | $65.00 | $54.00 | $12.00 | $2.19 | $-3.19 | `EVALUATED_ESTIMATED` | `True` | $3.19 | **PASS** |
| **TC-23-T2-timing-post-settlement-confirmed** | `timing` | `#1023` | `USD` | $65.00 | $54.00 | $8.50 | $1.95 | +$0.55 | `EVALUATED_CONFIRMED` | `False` | $0.00 | **PASS** |
| **TC-24-timezone-cutoff-cross-day** | `timezone` | `#1024` | `INR` | ₹1999.00 | ₹1750.00 | ₹230.00 | ₹47.18 | ₹-28.18 | `EVALUATED_CONFIRMED` | `True` | ₹28.18 | **PASS** |
| **TC-25-01-batch-null-cogs** | `denominator` | `#1025-NULL-1` | `USD` | $45.00 | $0.00 | $0.00 | $0.00 | +$0.00 | `NOT_EVALUABLE` | `False` | $0.00 | **PASS** |
| **TC-25-02-batch-null-cogs** | `denominator` | `#1025-NULL-2` | `USD` | $45.00 | $0.00 | $0.00 | $0.00 | +$0.00 | `NOT_EVALUABLE` | `False` | $0.00 | **PASS** |
| **TC-25-03-batch-null-cogs** | `denominator` | `#1025-NULL-3` | `USD` | $45.00 | $0.00 | $0.00 | $0.00 | +$0.00 | `NOT_EVALUABLE` | `False` | $0.00 | **PASS** |
| **TC-25-04-batch-breach-1** | `denominator` | `#1025-BREACH-1` | `USD` | $40.00 | $35.00 | $8.50 | $1.50 | $-5.00 | `EVALUATED_CONFIRMED` | `True` | $5.00 | **PASS** |
| **TC-25-05-batch-breach-2** | `denominator` | `#1025-BREACH-2` | `USD` | $60.00 | $55.00 | $10.00 | $2.50 | $-7.50 | `EVALUATED_CONFIRMED` | `True` | $7.50 | **PASS** |
| **TC-25-06-batch-healthy-1** | `denominator` | `#1025-HEALTHY-1` | `USD` | $80.00 | $45.00 | $8.50 | $2.50 | +$24.00 | `EVALUATED_CONFIRMED` | `False` | $0.00 | **PASS** |
| **TC-25-07-batch-healthy-2** | `denominator` | `#1025-HEALTHY-2` | `USD` | $90.00 | $50.00 | $8.50 | $2.80 | +$28.70 | `EVALUATED_CONFIRMED` | `False` | $0.00 | **PASS** |
| **TC-25-08-batch-healthy-3** | `denominator` | `#1025-HEALTHY-3` | `USD` | $100.00 | $60.00 | $8.50 | $3.00 | +$28.50 | `EVALUATED_CONFIRMED` | `False` | $0.00 | **PASS** |
| **TC-25-09-batch-healthy-4** | `denominator` | `#1025-HEALTHY-4` | `USD` | $70.00 | $40.00 | $8.50 | $2.20 | +$19.30 | `EVALUATED_CONFIRMED` | `False` | $0.00 | **PASS** |
| **TC-25-10-batch-healthy-5** | `denominator` | `#1025-HEALTHY-5` | `USD` | $85.00 | $45.00 | $8.50 | $2.60 | +$28.90 | `EVALUATED_CONFIRMED` | `False` | $0.00 | **PASS** |
| **TC-27-01-loss-leader-repeated** | `loss_leader` | `#1027-1` | `USD` | $15.00 | $14.50 | $3.50 | $0.74 | $-3.74 | `EVALUATED_CONFIRMED` | `True` | $3.74 | **PASS** |
| **TC-27-02-loss-leader-repeated** | `loss_leader` | `#1027-2` | `USD` | $15.00 | $14.50 | $3.50 | $0.74 | $-3.74 | `EVALUATED_CONFIRMED` | `True` | $3.74 | **PASS** |
| **TC-27-03-loss-leader-repeated** | `loss_leader` | `#1027-3` | `USD` | $15.00 | $14.50 | $3.50 | $0.74 | $-3.74 | `EVALUATED_CONFIRMED` | `True` | $3.74 | **PASS** |
| **TC-27-04-loss-leader-repeated** | `loss_leader` | `#1027-4` | `USD` | $15.00 | $14.50 | $3.50 | $0.74 | $-3.74 | `EVALUATED_CONFIRMED` | `True` | $3.74 | **PASS** |
| **TC-27-05-loss-leader-repeated** | `loss_leader` | `#1027-5` | `USD` | $15.00 | $14.50 | $3.50 | $0.74 | $-3.74 | `EVALUATED_CONFIRMED` | `True` | $3.74 | **PASS** |
| **TC-28-cancelled-mid-fulfillment-partial-ship** | `cancellation` | `#1028` | `USD` | $30.00 | $22.40 | $7.80 | $1.74 | $-1.94 | `EVALUATED_CONFIRMED` | `True` | $1.94 | **PASS** |
| **TC-29-promotional-influencer-gifting** | `channel` | `#1029-PR` | `USD` | $0.00 | $25.00 | $0.00 | $0.00 | $-25.00 | `EXCLUDED_PROMOTIONAL` | `False` | $0.00 | **PASS** |
| **TC-30-sandbox-test-order-filtered** | `financial_status` | `#1030-TEST` | `USD` | $0.00 | $0.00 | $0.00 | $0.00 | +$0.00 | `FILTERED_TEST_ORDER` | `False` | $0.00 | **PASS** |
| **TC-31-stacked-line-and-cart-discounts** | `discount` | `#1031` | `USD` | $75.00 | $65.00 | $8.50 | $2.50 | $-1.00 | `EVALUATED_CONFIRMED` | `True` | $1.00 | **PASS** |
| **TC-32-tax-inclusive-partial-refund-isolated** | `refund` | `#1032` | `INR` | ₹0.00 | ₹0.00 | ₹150.00 | ₹28.00 | ₹-178.00 | `EVALUATED_CONFIRMED` | `True` | ₹178.00 | **PASS** |
| **TC-33-shipping-tax-inclusive-isolated** | `tax` | `#1033` | `USD` | $60.00 | $40.00 | $11.50 | $1.80 | +$6.70 | `EVALUATED_CONFIRMED` | `False` | $0.00 | **PASS** |
| **TC-34-shipping-refund-isolated** | `refund` | `#1034` | `USD` | $60.00 | $48.00 | $9.50 | $2.10 | +$0.40 | `EVALUATED_CONFIRMED` | `False` | $0.00 | **PASS** |
| **TC-35-international-shipping-fallback-zone** | `data_availability` | `#1035` | `USD` | $45.00 | $35.00 | $14.50 | $1.80 | $-6.30 | `EVALUATED_ESTIMATED` | `True` | $6.30 | **PASS** |

---

## 11. Expanded Data Dictionary (Granular & Order Grains)

The data dictionary below defines all fields used in the canonical 25-step formula across both **LineItem** and **Order** grains (Deliverable 1), with direct lineage to Shopify Admin GraphQL fields or explicit external data sources:

### Line-Item Grain Economics (Steps 1–14)

| Field Name | Grain | Type | Source / Calculation | Business & Audit Description |
| :--- | :--- | :--- | :--- | :--- |
| `original_price_i` | LineItem | `Decimal` | `LineItem.originalUnitPriceSet.shopMoney.amount * quantity` | Pre-discount gross selling price before any promotions |
| `line_discount_i` | LineItem | `Decimal` | `LineItem.discountAllocations[targetType==LINE_ITEM]` | Line-specific discounts (quantity breaks, SKU promotions) |
| `cart_discount_i` | LineItem | `Decimal` | `LineItem.discountAllocations[targetType==ORDER_WIDE]` | Pro-rated allocation of whole-order cart coupons |
| `total_discount_i` | LineItem | `Decimal` | `line_discount_i + cart_discount_i` | Combined promotional price reduction on this line |
| `discounted_price_i`| LineItem | `Decimal` | `original_price_i - total_discount_i` | Actual checkout price charged to buyer before taxes |
| `tax_adjustment_i` | LineItem | `Decimal` | `LineItem.taxLines[].priceSet` (if `taxesIncluded=true`) | Statutory tax embedded in price remittable to government |
| `net_selling_price_i`| LineItem| `Decimal` | `discounted_price_i - tax_adjustment_i` | Tax-exclusive commercial price retained at sale time |
| `refunded_gross_i` | LineItem | `Decimal` | `Refund.refundLineItems.subtotalSet.shopMoney.amount` | Gross customer cash returned for returned/cancelled line |
| `refunded_tax_i` | LineItem | `Decimal` | `Refund.refundLineItems.totalTaxSet.shopMoney.amount` | Tax liability returned by government upon customer refund |
| `net_refund_i` | LineItem | `Decimal` | `refunded_gross_i - refunded_tax_i` | Net physical merchandise refund stripped of tax liability |
| `net_revenue_i` | LineItem | `Decimal` | `max(0.00, net_selling_price_i - net_refund_i)` | Final realized net merchandise revenue post-refund |
| `unit_cogs_i` | LineItem | `Decimal` | Hierarchy A (Snapshot -> Live Catalog -> BOM) | Sourced supplier unit cost (Option a: 4 auditable tiers) |
| `cogs_source_tier_i`| LineItem| `String` | Hierarchy A resolution tier | `Tier 1 (Snapshot)`, `Tier 2 (Live)`, `Tier 3 (BOM)`, `Tier 4` |
| `unrecovered_qty_i`| LineItem | `Integer` | `max(0, quantity - restocked_quantity)` | Physical units permanently lost (0 if restocked to shelf) |
| `unrecovered_cogs_i`| LineItem| `Decimal` | `unit_cogs_i * unrecovered_qty_i` | Inventory cost forfeited due to unreturned/scrapped items |
| `gross_profit_i` | LineItem | `Decimal` | `net_revenue_i - unrecovered_cogs_i` | Direct merchandise gross profit generated by line item |

### Shipping Economics Grain (Steps 15–18)

| Field Name | Grain | Type | Source / Calculation | Business & Audit Description |
| :--- | :--- | :--- | :--- | :--- |
| `gross_shipping_revenue` | Order | `Decimal` | `ShippingLine.discountedPriceSet.shopMoney.amount` | Customer-paid delivery charge collected at checkout |
| `shipping_tax_adjustment`| Order | `Decimal` | `ShippingLine.taxLines[].priceSet` (if `taxesIncluded`) | Statutory tax liability embedded within delivery price |
| `refunded_shipping_gross`| Order | `Decimal` | `Refund.refundShippingLines.subtotalSet.shopMoney` | Gross delivery cash returned to buyer upon return/delay |
| `refunded_shipping_tax` | Order | `Decimal` | `Refund.refundShippingLines.taxSet.shopMoney` | Tax portion of delivery fee returned to customer |
| `net_shipping_refund` | Order | `Decimal` | `refunded_shipping_gross - refunded_shipping_tax` | Pure delivery refund stripped of statutory tax |
| `net_shipping_revenue` | Order | `Decimal` | `max(0.00, gross - shipping_tax - net_refund)` | Final realized delivery revenue retained by merchant |

### Order-Level Aggregate & Financial Grain (Steps 19–25)

| Field Name | Grain | Type | Source / Calculation | Business & Audit Description |
| :--- | :--- | :--- | :--- | :--- |
| `order_id` | Order | `ID` | Shopify `Order.id` | Global GraphQL ID for the Shopify order |
| `order_name` | Order | `String` | Shopify `Order.name` | Merchant-facing order reference (e.g. `#1001`) |
| `processed_at` | Order | `DateTime` | Shopify `Order.processedAt` | Order placement timestamp in ISO 8601 UTC |
| `cancelled_at` | Order | `DateTime` | Shopify `Order.cancelledAt` | Order cancellation timestamp (null if active) |
| `financial_status` | Order | `String` | Shopify `displayFinancialStatus` | Payment state (`PAID`, `PARTIALLY_REFUNDED`, `VOIDED`, etc.) |
| `currency_code` | Order | `String` | Shopify `Order.currencyCode` | Store base currency (`shopMoney` anchor) |
| `taxes_included` | Order | `Boolean` | Shopify `Order.taxesIncluded` | True if gross sticker prices include statutory GST/VAT |
| `test` | Order | `Boolean` | Shopify `Order.test` | True for sandbox/developer test orders (BUG B) |
| `order_gross_profit` | Order | `Decimal` | `Sum(gross_profit_i)` | Total merchandise gross profit across all lines |
| `net_cash_in` | Order | `Decimal` | `Sum(net_revenue_i) + net_shipping_revenue` | Total physical net cash collected post-tax and post-refund |
| `unrecovered_cogs` | Order | `Decimal` | `Sum(unrecovered_cogs_i)` | Total physical inventory cost lost |
| `outbound_shipping_cost`| Order| `Decimal` | 3PL invoice or `ShippingFallbackRateTable_v1_0` | Real courier freight expense incurred by merchant |
| `gateway_retained_fee` | Order | `Decimal` | `OrderTransaction.fees` or settlement | Non-refundable processor transaction fee |
| `operational_costs` | Order | `Decimal` | `outbound_shipping_cost + gateway_retained_fee` | Combined non-merchandise fulfillment cash outflow |
| `net_cash_out` | Order | `Decimal` | `unrecovered_cogs + operational_costs` | Total direct physical cash expenditures |
| `net_margin_cash` | Order | `Decimal` | `net_cash_in - net_cash_out` | Physical direct net cash contribution |
| `f03_breach` | Order | `Boolean` | `net_margin_cash < 0.00` | True if order failed cash-floor safety check |
| `f03_loss` | Order | `Decimal` | `abs(net_margin_cash)` if breach else 0 | Exact cash loss magnitude incurred on order |
| `is_merchandise_loss` | Order | `Boolean` | `order_gross_profit < 0.00` | True if order lost money on product cost alone |
| `is_fulfillment_induced_loss`| Order| `Boolean` | `f03_breach and order_gross_profit >= 0.00` | True if positive gross profit was wiped out by shipping/fees |
| `evaluability_status` | Order | `String` | F03 evaluability gate | Hierarchy B status classification |
| `is_shipping_cost_estimated`| Order| `Boolean` | Courier fallback model active | True when 3PL invoice has not yet arrived |
| `is_gateway_fee_estimated` | Order | `Boolean` | Fallback processing fee active | True when non-SP gateway fees are imputed |
| `is_cogs_missing` | Order | `Boolean` | Missing supplier cost on lines | True if any active line item lacks valid COGS |
| `is_bundle` | Order | `Boolean` | Composite SKU explosion active | True if BOM component explosion was required |
| `rollup_date_utc` | Order | `String` | UTC calendar date of `processedAt` | Calendar date in UTC |
| `rollup_date_shop_tz` | Order | `String` | Local shop calendar date of `processedAt` | Operational merchant calendar date |
| `usd_fx_rate` | Order | `Decimal` | Versioned currency exchange rate | Conversion multiplier to standardize to USD base |
| `f03_loss_usd` | Order | `Decimal` | `f03_loss * usd_fx_rate` | Standardized dollar loss for portfolio ranking |

---

## 12. Production Validation Checklist & Audit Sign-Off

Every checklist item below is linked to a **specific verified automated test case ID**:

- [x] **Canonical Run ID synchronized across pipeline models, fixtures, test runner, and audit documentation:** `RUN-20260924-F03-CANONICAL-V2.1` — *Exercised by [TC-01](#10-complete-automated-test-suite-specification--results)*
- [x] **Automated Regression Suite: 100% automated test coverage across all boundary conditions and batch meta-tests:** `49 / 49 Passed` — *Exercised by [TC-01 through TC-35, BATCH-TC-25..27](#10-complete-automated-test-suite-specification--results)*
- [x] **Exact Cent Decimal Precision (BUG A): Inline cash subtraction (Inflow - Outflow) equals Net Margin Cash with zero penny drift:** `Discrepancy: $0.00` — *Exercised by [TC-01 through TC-35](#10-complete-automated-test-suite-specification--results)*
- [x] **Sandbox Test Order Isolation (BUG B): order.test == true routes to FILTERED_TEST_ORDER and excluded from all denominators:** `FILTERED_TEST_ORDER verified` — *Exercised by [TC-30](#10-complete-automated-test-suite-specification--results)*
- [x] **Granular Discount Allocation (BUG C & Step 2-4): Line-specific and cart-level discounts computed separately on same line:** `Discounts isolated` — *Exercised by [TC-31](#10-complete-automated-test-suite-specification--results)*
- [x] **Tax-Consistent Partial Merchandise Refund (BUG C & Step 8): Strips refund tax component before deducting from net revenue:** `Tax-consistent refund proved` — *Exercised by [TC-32](#10-complete-automated-test-suite-specification--results)*
- [x] **Tax-Inclusive Shipping Line Extraction (BUG C & Step 16): Taxes included on shipping extracted separately from merchandise:** `Shipping tax isolated` — *Exercised by [TC-33](#10-complete-automated-test-suite-specification--results)*
- [x] **Standalone Shipping Refund Accounting (BUG C & Step 17-18): Courier delivery refund tracked independently of merchandise retention:** `Shipping refund isolated` — *Exercised by [TC-34](#10-complete-automated-test-suite-specification--results)*
- [x] **COGS Resolution Waterfall (BUG D): Exactly 4 auditable tiers (Snapshot, Live, BOM, Quarantine); statistical averages rejected:** `4-tier model verified` — *Exercised by [TC-01, TC-02, TC-21, TC-22](#10-complete-automated-test-suite-specification--results)*
- [x] **International Shipping Fallback Coverage (BUG F): Cross-border EU & Rest-of-World rates ($14.50, $28.00) in rate table:** `EU fallback applied` — *Exercised by [TC-35](#10-complete-automated-test-suite-specification--results)*
- [x] **Multi-Currency Anchoring: All arithmetic locks strictly to shopMoney.amount; presentmentMoney discarded:** `EUR presentment discarded` — *Exercised by [TC-08](#10-complete-automated-test-suite-specification--results)*
- [x] **Statutory Tax Remittance Deductions: stores with taxesIncluded=true deduct currentTotalTaxSet before net margin:** `GST 18% deducted` — *Exercised by [TC-06, TC-07](#10-complete-automated-test-suite-specification--results)*
- [x] **Immutable Snapshot Costing: Point-in-time cost frozen at order creation date, immune to catalog renegotiation drift:** `Snapshot COGS enforced` — *Exercised by [TC-22](#10-complete-automated-test-suite-specification--results)*
- [x] **Cost Isolation Return Accounting: Restocked goods (restockType=RETURN) incur $0 COGS loss; scrapped goods write off full COGS:** `Return COGS isolated` — *Exercised by [TC-12, TC-13, TC-14](#10-complete-automated-test-suite-specification--results)*
- [x] **Multi-Tender Processing Fee Integrity: Card fee percentage applies only to credit card tender, preserving 0% fee on gift cards:** `Card-only fee allocation` — *Exercised by [TC-15](#10-complete-automated-test-suite-specification--results)*
- [x] **Manual Payment Zero-Fee Certification: Cash on Delivery (COD) certified as legitimately $0.00 gateway fee without false estimation:** `COD $0 fee verified` — *Exercised by [TC-16](#10-complete-automated-test-suite-specification--results)*
- [x] **POS Channel Isolation: In-person walkout retail sales certified as legitimately $0.00 courier shipping without false fallback:** `POS $0 shipping verified` — *Exercised by [TC-17](#10-complete-automated-test-suite-specification--results)*
- [x] **Bundle BOM Component Explosion: Variant metafield custom.bundle_components exploded into component COGS:** `True component cost applied` — *Exercised by [TC-21](#10-complete-automated-test-suite-specification--results)*
- [x] **Shop-Timezone Aware Aggregation: processedAt localized to store timezone (Asia/Kolkata) across UTC midnight boundaries:** `Cross-day rollup verified` — *Exercised by [TC-24](#10-complete-automated-test-suite-specification--results)*
- [x] **Stateful Progressive Settlement Reconciliation: Pre-invoice estimate at T1 updates cleanly to settled invoice at T2:** `Timing reconciliation verified` — *Exercised by [TC-23-T1, TC-23-T2](#10-complete-automated-test-suite-specification--results)*
- [x] **Promotional Gifting Gate: $0.00 PR sample orders tagged 'pr_gifting' reallocated to CAC (EXCLUDED_PROMOTIONAL):** `Promotional gate verified` — *Exercised by [TC-29](#10-complete-automated-test-suite-specification--results)*
- [x] **Financial Status Pre-Filter: VOIDED, PENDING, and test orders filtered before evaluability gating (anti-dilution):** `Pre-filter verified` — *Exercised by [TC-10, TC-11, TC-30](#10-complete-automated-test-suite-specification--results)*
- [x] **Dual Denominator Batch Mode Reporting: EXCLUDE mode (28.57%) and INCLUDE mode (20.00%) computed side-by-side:** `Batch modes verified` — *Exercised by [BATCH-TC-25](#10-complete-automated-test-suite-specification--results)*
- [x] **Zero-Division Cohort Resilience: Inactive sales window handles zero orders gracefully without runtime exceptions:** `Zero division guarded` — *Exercised by [BATCH-TC-26](#10-complete-automated-test-suite-specification--results)*


**Audit Sign-Off:** Formula F03 is certified mathematically verified, programmatically audited, and backed 100% by reproducible code execution across all 25 granular steps.

---

## 13. Technical Audit Changelog & Resolution of Audit Bugs (Bugs A through F)

### Bug Fix Details & Methodological Decisions

1. **BUG A Fixed — Penny-Level Rounding Mismatch in Executive Summary:**  
   *Audit Finding:* Prior Executive Summary reported Total Cash Inflow ($1,657.51) minus Outflow ($1,691.61) = -$34.10, but claimed Net Margin of -$34.09 — a 1-cent discrepancy violating exact-cent precision standards.  
   *Root Cause:* Intermediate per-order float rounding before summation.  
   *Resolution:* Rebuilt the entire calculation pipeline in Python pure `Decimal` (zero float operations). All intermediate line-item, shipping, and order calculations maintain full precision. Formulated order-level Net Cash Margin strictly as `net_cash_in - net_cash_out`, guaranteeing that $\sum \text{Inflow} - \sum \text{Outflow} = \sum \text{Margin}$ identically across the cohort. Enforced code assertion `abs(Total_Inflow - Total_Outflow - Total_Margin) < Decimal('0.005')`, proving **$0.0000 discrepancy**.

2. **BUG B Fixed — `FILTERED_TEST_ORDER` Status Zero Test Coverage:**  
   *Audit Finding:* Hierarchy B table and changelog claimed `order.test == true` routing to `FILTERED_TEST_ORDER` was implemented, but no test fixture set `order.test = true`.  
   *Resolution:* Created active fixture **`TC-30-sandbox-test-order-filtered`** with `order.test = true`. Asserted `evaluability_status == FILTERED_TEST_ORDER` and verified total exclusion from all commercial and evaluable denominators.

3. **BUG C Fixed — Formula Fragmentation Across Source Documents:**  
   *Audit Finding:* Document A used a coarse lump-sum cash formula while Document B specified a 25-step line-item formula, creating two conflicting standards for how refunds and taxes interact.  
   *Resolution:* Deleted all coarse lump-sum restatements. Section 2 of this canonical document now literally defines the complete **25-Step Granular Mathematical Formula** (Steps 1–25). Rebuilt pipeline executes Steps 1–18 at the line-item and shipping grain. Added isolated test cases proving each granular step:
   - **`TC-31`:** Tests Step 2 (`LineDiscount_i`) and Step 3 (`CartDiscount_i`) independently on the same line item.
   - **`TC-32`:** Tests Step 8 (`NetRefund_i`) tax-consistency on tax-inclusive orders.
   - **`TC-33`:** Tests Step 16 (`ShippingTaxAdjustment`) tax extraction on shipping lines.
   - **`TC-34`:** Tests Step 17–18 (`NetShippingRefund`, `NetShippingRevenue`) standalone shipping refunds.

4. **BUG D Resolved — COGS Waterfall Methodology Decision (Option a Chosen):**  
   *Audit Finding:* Document B draft specified 6 tiers including Product-level, Category-level, and Storewide-level statistical averages, whereas Document A implemented 4 tiers.  
   *Methodology Risk:* Averaging supplier costs turns an exact cash-floor safety check into an estimated metric, risking false breach alarms or concealed real losses.  
   *Decision & Resolution:* **OPTION (a) ADOPTED — REJECT THE 3 STATISTICAL AVERAGE TIERS.** Formula F03 strictly retains the 4-tier auditable model:
   - Tier 1: Immutable historical snapshot table.
   - Tier 2: Live Shopify Admin `inventoryItem.unitCost` (with historical drift flag).
   - Tier 3: Variant metafield `custom.bundle_components` Bill-of-Materials explosion.
   - Tier 4: Missing cost triggers `NOT_EVALUABLE` quarantine.  
   No synthetic statistical averages are permitted into the direct cash floor.

5. **BUG E Fixed — Clarification Callout on Batch Meta-Tests:**  
   *Audit Finding:* Section 8 batch breach rates (28.57% for 10 orders, 100.00% for 5 orders) were easily confused with the storewide rate.  
   *Resolution:* Added a prominent callout block at the top of Section 8 explicitly clarifying that batch meta-tests evaluate isolated N-order subsets to verify denominator logic (`EXCLUDE` vs `INCLUDE`) and must not be confused with storewide portfolio performance.

6. **BUG F Fixed — Shipping Fallback Rate Table Incomplete Zone Coverage:**  
   *Audit Finding:* `ShippingFallbackRateTable_v1_0` defined only US Ground and India Surface, leaving international orders without a valid fallback rate.  
   *Resolution:* Expanded `ShippingFallbackRateTable_v1_0` with **`INTERNATIONAL_EU`** ($14.50) and **`INTERNATIONAL_ROW`** ($28.00). Added dedicated test case **`TC-35-international-shipping-fallback-zone`** exercising the European cross-border fallback path.

7. **AUDIT AUDIT ENHANCEMENT 1 — Elimination of Section 3 Double-Count:**  
   *Audit Finding:* TC-19 ($0.01 boundary deficit) was listed as a sibling alongside Merchandise Negative GP and Fulfillment & Fee Induced breaches, violating unit conservation.  
   *Resolution:* Restructured Section 3 hierarchy to nest TC-19 as an explicit sub-case under Fulfillment & Fee Induced breaches. 3 Merchandise + 26 Fulfillment/Fee = 29 Total Breaches (100% mutually exclusive conservation).

8. **AUDIT AUDIT ENHANCEMENT 2 — Stateful Progressive Settlement Re-Evaluation Fixtures (`TC-23-T1` / `TC-23-T2`):**  
   *Audit Finding:* Prior test suite collapsed progressive settlement into a single T2 row, obscuring the empirical state transition from estimated breach to confirmed healthy.  
   *Resolution:* Preserved both states as distinct fixtures: `TC-23-T1` (T+2h estimated breach, -$3.19) and `TC-23-T2` (T+72h confirmed healthy, +$0.55). Added cross-fixture code assertions verifying same-order ID match and margin evolution.

---

## 14. Programmatic Mathematical Verification & Assertion Proofs

The following audit checks were executed programmatically during report generation and are certified passing:

| Audit Check | Programmatic Condition | Computed Result | Status |
| :--- | :--- | :---: | :---: |
| **Check 1: Exact Cent Invariant (BUG A)** | $|\text{Total\_Inflow} - \text{Total\_Outflow} - \text{Total\_Margin}| < 0.005$ | **$0.0000** | **PASS** |
| **Check 2: Granular Line Sum Identity (BUG C)**| $\sum_{i} \text{GrossProfit}_i = \text{OrderGrossProfit}$ across 100% of orders | **Exact Match ($0.0000)** | **PASS** |
| **Check 3: Refund Line Traceability (BUG C)** | $\text{NetRevenue}_i$ traceable to `RefundedGrossAmount` & `RefundedTax` | **Verified (7/7 Refund Orders)** | **PASS** |
| **Check 4: Hierarchy B Gate Coverage (BUG B)** | Every status in Hierarchy B has $\ge 1$ active test fixture | **6 / 6 Statuses Active** | **PASS** |
| **Check 5: COGS Waterfall Tiers (BUG D)** | Implemented waterfall has exactly 4 tiers (Option a) | **4 / 4 Tiers Verified** | **PASS** |
| **Check 6: Top-10 Loss Subset Sum** | $\sum \text{Top10.loss\_usd} \le \text{Total\_Cumulative\_Loss}$ | **$161.01 \le $203.11** | **PASS** |
| **Check 7: Cohort Tree Conservation** | $\text{Total Ingested} = \text{Eval} + \text{Quar} + \text{Filt} + \text{Excl}$ | **49 = 49 (Diff: 0)** | **PASS** |
| **Check 8: Automated Test Suite Attainment** | All test cases pass assertions without failure | **49 / 49 (100.0%)** | **PASS** |
| **Check 9: FX Consolidation Conservation** | $\text{Consolidated\_USD} = \sum_{i=1}^N \text{round\_cents}(\text{native\_amount}_i \times \text{fx\_rate}_i)$ | **Exact Match ($0.0000)** | **PASS** |
| **Check 10: Progressive Settlement State Transition** | `TC-23-T1` ($-\$3.19, `ESTIMATED`) $\to$ `TC-23-T2` ($+\$0.55, `CONFIRMED`) | **Verified (Order #1023)** | **PASS** |

### Multi-Currency FX Conversion & Consolidation Protocol (Check 9 Documentation)

To eliminate cross-currency rounding drift, portfolio consolidation operates strictly on an **order-level conversion model**, never on post-aggregated currency subtotals:
1. **Source Precision:** Raw native currency amounts are extracted and stored in full Python `Decimal` precision.
2. **Fixed Conversion Multiplier:** For each currency, an immutable store-level exchange rate is defined (e.g. 1 USD = 83.50 INR, rate = `Decimal("1.0") / Decimal("83.50")`).
3. **Order-Level Normalization:** For every order $i$:
   $$\text{USD\_equivalent\_inflow}_i = \text{round\_cents}(\text{native\_inflow}_i \times \text{fx\_rate}_i)$$
   $$\text{USD\_equivalent\_outflow}_i = \text{round\_cents}(\text{native\_outflow}_i \times \text{fx\_rate}_i)$$
   $$\text{USD\_equivalent\_margin}_i = \text{USD\_equivalent\_inflow}_i - \text{USD\_equivalent\_outflow}_i$$
   $$\text{USD\_equivalent\_loss}_i = |\text{USD\_equivalent\_margin}_i| \quad \text{if breach else } \$0.00$$
   *All order-level roundings enforce standard financial `ROUND_HALF_UP` to exactly 2 decimal places.*
4. **Consolidated Rollup:** Portfolio-wide USD metrics are computed strictly as the sum of these per-order converted amounts:
   $$\text{Consolidated\_USD} = \sum_{i=1}^N \text{USD\_equivalent}_i$$
   Asserted Invariant: $|\text{Consolidated\_USD} - \sum \text{USD\_equivalent}_i| < \text{Decimal("0.005")}$ ($\$0.0000$ discrepancy).  
   *Audit Rule:* Calculating $\text{USD\_subtotal} + (\text{INR\_subtotal} \div 83.50)$ post-aggregation is strictly prohibited, as summing pre-rounded foreign currencies distorts order-by-order financial reconciliation.
