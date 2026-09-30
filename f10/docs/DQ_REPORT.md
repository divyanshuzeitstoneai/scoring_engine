# Formula F10: Data Quality (DQ) Audit Report

**API Version:** `2024-10`  
**Config Hash:** `9e26a5fae94e`  
**Evaluation Date (as_of):** `2024-10-31`  
**Dataset Ingested:** `50,000` Orders | `84,096` Line Items  
**BLOCK Gates Passed:** `100% GREEN`

---

## 1. Summary of All 19 Data Quality Gates

| Gate ID | Check Name | Severity | Status | Evaluated Count | Failed Count | Quarantined Rev ($) |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: |
| **DQ-S1** | Schema Validation | `BLOCK` | **PASSED** | 0 | 0 | $0.00 |
| **DQ-S2** | Enum Validity | `QUARANTINE` | **PASSED** | 0 | 0 | $0.00 |
| **DQ-U1** | Uniqueness | `BLOCK` | **PASSED** | 92,371 | 0 | $0.00 |
| **DQ-U2** | Idempotency | `BLOCK` | **PASSED** | 0 | 0 | $0.00 |
| **DQ-RI1** | Referential Integrity | `QUARANTINE` | **PASSED** | 0 | 0 | $0.00 |
| **DQ-RI2** | Refund Quantity Bound | `QUARANTINE` | **PASSED** | 0 | 0 | $0.00 |
| **DQ-R1** | Order Reconciliation | `QUARANTINE` | **PASSED** | 0 | 0 | $0.00 |
| **DQ-R2** | Discount Allocation Sum | `QUARANTINE` | **PASSED** | 0 | 0 | $0.00 |
| **DQ-R3** | Refund Subtotal Reconciliation | `QUARANTINE` | **PASSED** | 0 | 0 | $0.00 |
| **DQ-C1** | Currency Consistency | `BLOCK` | **PASSED** | 0 | 0 | $0.00 |
| **DQ-K1** | COGS State Completeness | `BLOCK` | **PASSED** | 84,096 | 0 | $0.00 |
| **DQ-K2** | Unknown Cost Share Reporting | `WARN` | **PASSED** | 0 | 0 | $0.00 |
| **DQ-A1** | Allocation Conservation | `BLOCK` | **PASSED** | 0 | 0 | $0.00 |
| **DQ-A2** | Positive Allocations | `QUARANTINE` | **PASSED** | 0 | 0 | $0.00 |
| **DQ-T1** | Deterministic Time | `BLOCK` | **PASSED** | 1 | 0 | $0.00 |
| **DQ-F1** | Score Bounds & Margin Rule | `BLOCK` | **PASSED** | 59 | 0 | $0.00 |
| **DQ-F2** | Waterfall Conservation | `BLOCK` | **PASSED** | 59 | 0 | $0.00 |
| **DQ-F3** | Revenue Conservation | `BLOCK` | **PASSED** | 59 | 0 | $0.00 |
| **DQ-D1** | Sync Freshness | `WARN` | **PASSED** | 0 | 0 | $0.00 |
| **DQ-D2** | Schema Drift Introspection | `WARN` | **PASSED** | 0 | 0 | $0.00 |

---

## 2. Revenue and Quarantine Ledger Summary

- **Total Ingested Line Revenue:** `$12,331,408.75`
- **Quarantined Lines Count:** `2,600` lines
- **Quarantined Revenue:** `$73,240.25`
- **Quarantined Revenue Share:** `0.59%`

### Conservation Invariant (Gate DQ-F3):
$$\text{Revenue}_{\text{scored}} + \text{Revenue}_{\text{quarantined}} \equiv \text{Revenue}_{\text{total}}$$
Verified to **$0.0000** drift across all `59` product variants.
