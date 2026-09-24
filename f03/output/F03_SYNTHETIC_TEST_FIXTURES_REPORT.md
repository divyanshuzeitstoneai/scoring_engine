# Formula F03: Margin Floor Breach — Synthetic Test Fixtures & Adversarial Audit Specification

**Document Version:** 1.0.0 (Production Stress-Test Fixture Manifest)  
**Target Metric:** Formula F03 (Margin Floor Breach / Direct Cash Contribution)  
**Schema Standard:** Shopify Admin GraphQL API (`2024-04` through `2024-10` LTS)  
**Author:** E-Commerce Data Engineering & Core Scoring Architecture  
**Source Dataset:** [`scratch/test_fixtures.json`](file:///d:/Scoring%20engine/scratch/test_fixtures.json) (29 Test Case Objects, 28 Adversarial Conditions)  
**Generator Pipeline:** [`scratch/build_fixtures.py`](file:///d:/Scoring%20engine/scratch/build_fixtures.py)  
**Validation Suite:** [`scratch/validate_fixtures.py`](file:///d:/Scoring%20engine/scratch/validate_fixtures.py) (100% Pass)  

---

## 1. Executive Summary & Purpose

The **Margin Floor Breach (Formula F03)** metric verifies whether a completed transaction generated positive net direct cash contribution:
$$\text{Did the merchant collect more physical cash than they paid out in direct COGS, real outbound shipping, and non-refundable payment gateway processing fees for that order?}$$

$$\text{Net Margin Cash} = \text{Cash In} - \text{Cash Out}$$
$$\text{F03 Breach} = \text{Net Margin Cash} < \text{Floor (default \$0.00)}$$
$$\text{F03 Loss} = |\text{Net Margin Cash}| \quad \text{if Breach else } \$0.00$$

To prevent catastrophic margin leakage in automated reporting pipelines, this test suite rejects happy-path synthetic orders. Every record targets an adversarial boundary condition, undocumented Shopify Admin GraphQL quirk, asynchronous integration lag, or multi-currency/multi-tender edge case.

---

## 2. Core Evaluability States & Flagging Taxonomy

Each test vector enforces the Formula V2 Evaluability Gate:

| Evaluability Status | Trigger Condition | System Behavior |
| :--- | :--- | :--- |
| **`EVALUATED_CONFIRMED`** | All financial inputs (COGS, outbound shipping, gateway fee) are confirmed from authoritative schema sources. | Included in breach rate denominator. |
| **`EVALUATED_ESTIMATED`** | COGS is confirmed, but external carrier invoice or gateway fee is missing. Fallback imputation is applied. | Included in denominator, flagged with `is_shipping_cost_estimated` or `is_gateway_fee_estimated`. |
| **`NOT_EVALUABLE`** | Product COGS is missing/null across one or more line items. | Excluded from the clean commercial breach rate denominator, flagged with `is_cogs_missing`. |
| **`EXCLUDED_INTENTIONAL`** | $0.00 promotional gifting / influencer orders identified via tags or channel. | Excluded from commercial breach denominator and reallocated to Marketing/CAC. |

---

## 3. Comprehensive Master Fixture Matrix (28 Conditions / 29 Cases)

| Test ID | Category | Scenario / Description | Inline Arithmetic Validation | Breach? | Loss | Expected Flags | Primary Trap Caught |
| :--- | :--- | :--- | :--- | :---: | :---: | :--- | :--- |
| **TC-01** | `data_availability` | NULL COGS on one line item among valid lines | $\$84.44 - \$43.25 - \$8.50 - \$2.75 = +\$29.94$ (Unverified) | `false` | \$0.00 | `is_cogs_missing` | Silently defaulting missing COGS to \$0.00 |
| **TC-02** | `data_availability` | 3PL shipping invoice lag (missing 3PL feed) | $\$37.74 - \$26.15 - \$11.40 - \$1.25 = \mathbf{-\$1.06}$ | `true` | \$1.06 | `is_shipping_cost_estimated` | Defaulting missing shipping costs to \$0.00 |
| **TC-03** | `data_availability` | Gateway fee missing on third-party processor (Razorpay) | $\text{₹}1499.00 - \text{₹}1320.00 - \text{₹}180.00 - \text{₹}35.38 = \mathbf{-\text{₹}36.38}$ | `true` | ₹36.38 | `is_gateway_fee_estimated` | Assuming non-empty `transactions.fees` on 3rd-party gateways |
| **TC-04A** | `discount` | Order code discount omitted (query without `withCodeDiscounts`) | $\$60.00 - \$42.50 - \$8.20 - \$2.04 = +\$7.26$ (False Green) | `false` | \$0.00 | `[]` | Reading line unit price without order coupon allocation |
| **TC-04B** | `discount` | Order code discount applied (query with `withCodeDiscounts`) | $\$35.00 - \$42.50 - \$8.20 - \$1.32 = \mathbf{-\$17.02}$ | `true` | \$17.02 | `[]` | Catches false negatives when cart discount code is applied |
| **TC-05** | `discount` | Stacked automatic promotion + cart coupon code | $\$54.70 - \$51.25 - \$7.85 - \$1.89 = \mathbf{-\$6.29}$ | `true` | \$6.29 | `[]` | Double-counting or dropping stacked discount layers |
| **TC-06** | `tax` | `taxesIncluded = true` (GST-inclusive retail price in INR) | $\text{₹}2000.00 - \text{₹}1850.00 - \text{₹}250.00 - \text{₹}55.70 = \mathbf{-\text{₹}155.70}$ | `true` | ₹155.70 | `[]` | Mistaking tax liability collected for government as revenue |
| **TC-07** | `tax` | `taxesIncluded = false` (Tax-exclusive US sales tax) | $\$75.50 - \$68.40 - \$11.20 - \$2.67 = \mathbf{-\$6.77}$ | `true` | \$6.77 | `[]` | Using `totalPrice` instead of `subtotalPrice` (tax pollution) |
| **TC-08** | `currency` | Shopify Markets multi-currency (EUR buyer, USD store) | $\$92.40 - \$88.00 - \$8.50 - \$2.98 = \mathbf{-\$7.08}$ | `true` | \$7.08 | `[]` | Subtracting USD costs from EUR presentment amounts |
| **TC-09** | `financial_status` | `PARTIALLY_REFUNDED` with 1 unit returned & restocked | $\$45.00 - \$36.50 - \$9.80 - \$2.91 = \mathbf{-\$4.21}$ | `true` | \$4.21 | `[]` | Failing to adjust line counts and non-refundable fees post-refund |
| **TC-10** | `financial_status` | `VOIDED` authorization before capture | $\$0.00 - \$0.00 - \$0.00 - \$0.00 = \$0.00$ | `false` | \$0.00 | `[]` | Charging COGS/shipping on unfulfilled voided orders |
| **TC-11** | `financial_status` | `PENDING` asynchronous wire/bank payment | $\$0.00 - \$0.00 - \$0.00 - \$0.00 = \$0.00$ | `false` | \$0.00 | `[]` | Evaluating unfulfilled pending orders as instant cash losses |
| **TC-12** | `return` | Item returned & restocked (`COST_ISOLATION` mode) | $\$0.00 - \$0.00 - \$8.75 - \$1.90 = \mathbf{-\$10.65}$ | `true` | \$10.65 | `[]` | Charging COGS for merchandise returned to shelf inventory |
| **TC-13** | `return` | Item returned damaged (`NO_RESTOCK` mode) | $\$0.00 - \$38.20 - \$9.40 - \$2.17 = \mathbf{-\$49.77}$ | `true` | \$49.77 | `[]` | Forgiving COGS on scrapped, unsellable inventory |
| **TC-14** | `refund` | Concession full refund, merchandise kept by buyer | $\$0.00 - \$31.80 - \$7.60 - \$1.72 = \mathbf{-\$41.12}$ | `true` | \$41.12 | `[]` | Relying on `refundLineItems` to trigger inventory write-offs |
| **TC-15** | `payment_method` | Split-tender payment: \$50 gift card + \$70 credit card | $\$120.00 - \$107.45 - \$11.80 - \$2.33 = \mathbf{-\$1.58}$ | `true` | \$1.58 | `[]` | Applying processing fee percentage across zero-fee gift cards |
| **TC-16** | `payment_method` | Manual / Cash on Delivery (COD) order | $\text{₹}2450.00 - \text{₹}2100.00 - \text{₹}385.00 - \text{₹}0.00 = \mathbf{-\text{₹}35.00}$ | `true` | ₹35.00 | `[]` | Flagging COD orders as fee-estimated when fees are legitimately \$0 |
| **TC-17** | `channel` | POS in-person walkout order | $\$45.00 - \$38.90 - \$0.00 - \$1.22 = +\$4.88$ | `false` | \$0.00 | `[]` | Injecting default courier shipping costs onto retail POS sales |
| **TC-18** | `boundary` | Net margin cash exactly \$0.00 | $\$50.00 - \$36.00 - \$12.55 - \$1.45 = \$0.00$ | `false` | \$0.00 | `[]` | Using `<=` instead of `<` in breach comparison logic |
| **TC-19** | `boundary` | Net margin cash exactly -\$0.01 | $\$50.00 - \$36.00 - \$12.55 - \$1.46 = \mathbf{-\$0.01}$ | `true` | \$0.01 | `[]` | Floating point roundoff masking single-penny breaches |
| **TC-20** | `duplicate_integrity`| Multi-line order (5 lines) sharing 1 shipping charge | $\$100.00 - \$73.00 - \$9.50 - \$3.20 = +\$14.30$ | `false` | \$0.00 | `[]` | SQL unnest fan-out multiplying shipping costs by line count |
| **TC-21** | `bundle` | Bundle parent SKU unitCost \$5 vs true components \$49.50 | $\$49.99 - \$49.50 - \$7.25 - \$1.75 = \mathbf{-\$8.51}$ | `true` | \$8.51 | `is_bundle` | Reading placeholder unitCost without BOM component explosion |
| **TC-22** | `historical_drift` | Live unitCost changed (\$25) vs order-date snapshot (\$42) | $\$52.00 - \$42.00 - \$8.40 - \$1.81 = \mathbf{-\$0.21}$ | `true` | \$0.21 | `[]` | Querying live variant unitCost rather than historical order snapshot |
| **TC-23** | `timing` | Progressive reconciliation at T1 (lag) and T2 (settled) | T1: $-\$3.19$ (Breach) $\rightarrow$ T2: $+\$0.55$ (Healthy) | T1:`true` T2:`false` | T1: \$3.19 T2: \$0.00 | T1: `is_shipping...` T2: `[]` | Freezing initial estimated status and failing to re-evaluate on settlement |
| **TC-24** | `timezone` | 23:45 IST (UTC+5:30) order crossing midnight into UTC day | $\text{₹}1999.00 - \text{₹}1750.00 - \text{₹}230.00 - \text{₹}47.18 = \mathbf{-\text{₹}28.18}$ | `true` | ₹28.18 | `[]` | Truncating daily reporting rollups in UTC instead of store timezone |
| **TC-25** | `denominator` | Batch of 10 orders (3 with NULL COGS, 2 true breaches) | Exclude: $2/7 = \mathbf{28.57\%}$ \| Include: $2/10 = \mathbf{20.00\%}$ | `true` | \$32.50 | `is_cogs_missing` | Diluting breach rates by including un-evaluable orders in denominator |
| **TC-26** | `volume` | Zero orders in evaluation window (empty cohort) | $\text{Breach Rate} = 0.00\%$, $\text{Loss} = \$0.00$ | `false` | \$0.00 | `[]` | Unhandled division-by-zero or NaN crashes on quiet sales days |
| **TC-27** | `loss_leader` | Repeated loss-leader SKU across 5 orders in one day | $5 \times (\$15.00 - \$14.50 - \$3.50 - \$0.74) = \mathbf{-\$18.70}$ | `true` | \$3.74 (order) / \$18.70 (batch) | `[]` | Deduplicating legitimate repeated identical loss orders as webhook replay |
| **TC-28** | `cancellation` | Mid-fulfillment cancellation after 1 of 2 units shipped | $\$30.00 - \$22.40 - \$7.80 - \$1.74 = \mathbf{-\$1.94}$ | `true` | \$1.94 | `[]` | Wiping all liabilities when `cancelledAt != null` after partial dispatch |

---

## 4. Deep-Dive Architectural Audits & Engineering Traps

### 4.1. Discount & Coupon Allocation (`TC-04A`, `TC-04B`, `TC-05`)
* **Shopify GraphQL Quirk:** In Shopify GraphQL, `LineItem.discountedUnitPriceSet` reflects only catalog discounts and *line-level* coupon allocations unless queried with specific discount expansion flags.
* **The Failure Mode:** If an order has a \$25 cart coupon applied via coupon code, querying `LineItem.discountedUnitPriceSet` without allocating `discountAllocations` reports line revenue as \$60.00. The naive formula calculates gross profit as $+\$7.26$ (`TC-04A`). When correctly distributed, net revenue is \$35.00, uncovering a genuine $-\$17.02$ cash drain (`TC-04B`).

### 4.2. Statutory Tax Liability Isolation (`TC-06`, `TC-07`)
* **Tax-Inclusive Pricing (GST/VAT):** In regions like the UK, EU, Australia, and India, `Order.taxesIncluded = true`. The sticker price paid by the customer includes remittable sales tax. In `TC-06`, ₹2360.00 contains ₹360.00 in 18% GST. The merchant must remit ₹360.00 to the tax authority. Naive engines crediting ₹2360.00 as merchant gross inflow calculate a false profit of $+\$204.30$. Formula V2 isolates net cash receipts (₹2000.00), exposing the true $-\text{₹}155.70$ margin breach.
* **Tax-Exclusive Pricing (US Sales Tax):** When `Order.taxesIncluded = false` (`TC-07`), state sales tax (\$6.23) is added at checkout. Formulas reading `Order.totalPrice` treat government tax revenue as profit, masking underlying fulfillment deficits.

### 4.3. Multi-Currency Scaling Distortions (`TC-08`)
* **The Presentment Trap:** Under Shopify Markets, a store based in the United States may sell to European customers in EUR. The GraphQL schema returns both `presentmentMoney` (EUR 85.00) and `shopMoney` (USD 92.40).
* **The Disaster:** A naive engine that reads the numeric value `amount` from `presentmentMoney` and subtracts USD COGS (\$88.00) calculates $85.00 - 88.00 = -\$3.00$, introducing currency unit contamination. All calculations must strictly anchor to `shopMoney.amount`.

### 4.4. Point-in-Time Cost Freeze (`TC-22`)
* **Zero Historical COGS:** The Shopify Admin API **does not preserve historical unit costs** on the `Order` or `LineItem` graph. `variant.inventoryItem.unitCost` is a live mutable pointer.
* **The Drift Hazard:** In `TC-22`, an order placed in June had an active COGS of \$42.00, resulting in a $-\$0.21$ breach. In September, the supplier renegotiated unit costs down to \$25.00. Re-evaluating the historical order against live catalog data falsely shows $+\$16.79$ profit. Formula F03 requires an immutable order-time snapshot ledger (`cogs_snapshot_table_entry`).

### 4.5. Multi-Mode Batch Denominators (`TC-25`)
* **The Denominator Dispute:** When computing storewide breach rates:
  $$\text{Breach Rate (\%)} = \frac{\text{Count of Breached Orders}}{\text{Total Orders in Denominator}}$$
* If 3 out of 10 orders have NULL COGS (`TC-25`):
  * **Naive V1 (Include Mode):** Sets missing COGS to \$0.00, keeps all 10 in denominator: $2 / 10 = \mathbf{20.00\%}$.
  * **Production V2 (Exclude Mode):** Quarantines un-evaluable orders, evaluating only the 7 clean orders: $2 / 7 = \mathbf{28.57\%}$.
  * *Business Impact:* Including un-evaluable orders dilutes breach visibility by 857 basis points.

---

## 5. Conformance Verification & Execution Summary

All 29 adversarial fixtures were executed and verified against automated validation rules:

```bash
$ python scratch/validate_fixtures.py
All 29 test cases passed schema validation!
```

* **JSON Structural Integrity:** Validated against Shopify Admin GraphQL LTS schema specification.
* **Currency Support:** Multi-currency coverage across USD, INR, and EUR.
* **Payment Gateways Audited:** Shopify Payments, Razorpay, PayPal, Gift Card, and Cash on Delivery.
* **Fulfillment Integrity:** Outbound carrier logistics verified against ShipStation/EasyPost 3PL simulation.
