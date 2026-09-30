# Data Quality Verification Report: Synthetic Dataset (50,000 Orders)

**Generated At:** 2026-09-30T06:07:19.119710+00:00  
**Target Dataset:** `f11/data/synthetic_orders.jsonl`  
**Total Records Evaluated:** `50,250` (50,000 unique orders + 250 test duplicates)  
**Schema Pinned API Version:** `2024-10`

---

## 1. Data Quality Gate Compliance

| Gate ID | Check Description | Criteria | Result | Status |
| :--- | :--- | :--- | :--- | :--- |
| **DQ-01** | Schema Conformance | Types, enums match `introspection.json` | 100.0% Valid | `PASS` |
| **DQ-02** | Referential Integrity | All lines and transactions link to valid orders | 0 Orphans | `PASS` |
| **DQ-03** | Monotonic Timestamps | $t_{\text{created}} \le t_{\text{processed}} \le t_{\text{refund}} \le t_{\text{as\_of}}$ | 100.0% Ordered | `PASS` |
| **DQ-04** | Money Minor Units | Decimal strings match currency exponent | 100.0% Exact | `PASS` |
| **DQ-05** | Quota Exactness | Exact quotas for A01 through E12 | 50,000 / 50,000 | `PASS` |
| **DQ-06** | Pairwise Overlay Coverage | Every overlay pair occurs $\ge 20$ times | 100.0% Covered | `PASS` |
| **DQ-07** | Latent Truth Isolation | Zero latent fields exposed in visible layer | 0 Leaks | `PASS` |
| **DQ-08** | Determinism & Idempotence | Byte-identical re-run on seed 42 | Exact Hash Match | `PASS` |

---

## 2. Shop Stratification Summary

| Shop ID | Currency | Exponent | Tax Mode | Order Count | Primary Gateways |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **S1** | USD | 2 | Exclusive | 20,000 | Shopify Payments (85%), PayPal (15%) |
| **S2** | GBP | 2 | Inclusive | 12,000 | Shopify Payments (90%), Gift Card (10%) |
| **S3** | CAD | 2 | Exclusive | 8,000 | Shopify Payments, PayPal, Manual |
| **S4** | INR | 2 | Inclusive | 6,000 | Razorpay (60%), Cash on Delivery (40%) |
| **S5** | JPY | 0 | Exclusive | 4,000 | Stripe (70%), Bank Deposit (30%) |
