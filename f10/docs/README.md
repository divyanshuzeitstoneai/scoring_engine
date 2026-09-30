# Formula F10: Product Contribution v2 — Production Build & Data-Quality Lead Package

**Target API:** Shopify Admin GraphQL API `2024-10`  
**Compliance Standard:** Zero Silent Assumptions (`VERIFIED-DOCS`, `VERIFIED-PROBE`, `UNVERIFIED`)  
**Mathematical Engine:** Exact Python `Decimal` Precision  
**Dataset Scale:** 50,000 Synthetic Shopify Orders across 540 Days  

---

## 1. Business Purpose

Merchants mistakenly read top-line revenue as success. In reality, revenue is heavily eroded by promotional discounts, return write-offs, non-refundable gateway processing fees, outbound courier subsidies, and return logistics.

Formula **F10 Product Contribution v2** delivers true product variant economic profitability:
- Computes the exact net cash retained per SKU after direct variable costs.
- Identifies **Hidden Profit Leakage** ($) relative to naive spreadsheet margin assumptions.
- Ranks variant health via a secondary 0–100 score.
- Quarantines unverified or missing COGS into an explicit ledger to prevent false margin signals.

---

## 2. System Architecture

```
Raw Admin GraphQL JSON / Bulk JSONL (API 2024-10)
    │
    ▼
Staging & Ingestion Layer (stg_orders, stg_lines, stg_refunds, stg_transactions)
    │
    ▼
Deterministic Allocator (Largest-Remainder Method at minor currency unit)
    │  ├─ Shipping allocated by line weight (fallback to NetBilled share)
    │  ├─ Gateway fees allocated by NetBilled share
    │  └─ Goodwill refunds allocated by config.goodwill_rule
    ▼
Atomic LineFact Engine (Python Decimal Precision)
    │  ├─ Unit Taxonomy: q_ordered, q_removed, q_cancelled, q_shipped, q_refunded, q_restocked, q_kept
    │  ├─ Revenue: GrossLine - DiscLine - RefundItem - Goodwill = RetainedRev
    │  ├─ COGS: (q_kept + q_lost_returns) * cost_snapshot
    │  └─ Costs: Outbound + PayFees + ReturnShip + Handling + Packaging
    ▼
Quarantine Ledger (COGS_OBSERVED vs COGS_MISSING vs COGS_ZERO_SUSPECT)
    │
    ▼
Rolling Window Variant Rollup (30, 90, 365 days ending at explicit as_of)
    │
    ▼
Data Quality (DQ) Gate Auditor (All 19 Gates DQ-S1 to DQ-D2)
    │
    ▼
Export Outputs (dq_results.parquet, variant_metrics.csv, run_manifest.json, Reports)
```

---

## 3. Directory Layout

- [`f10/code/`](file:///d:/Scoring%20engine/f10/code/): Production pipeline, formula reference, largest-remainder allocator, models, dataset generator, DQ runner, and test suite.
- [`f10/config/`](file:///d:/Scoring%20engine/f10/config/): `config.schema.json` and `config.example.yaml`.
- [`f10/fixtures/probes/`](file:///d:/Scoring%20engine/f10/fixtures/probes/): Raw GraphQL probe responses PR-01 through PR-40.
- [`f10/golden/`](file:///d:/Scoring%20engine/f10/golden/): 156 hand-calculated golden test cases with step-by-step worked calculations.
- [`f10/data/`](file:///d:/Scoring%20engine/f10/data/): 50,000 synthetic orders (`synthetic_orders.jsonl`) and ground truth sidecars.
- [`f10/output/`](file:///d:/Scoring%20engine/f10/output/): Parquet and CSV outputs, run manifests, and quarantine ledgers.
- [`f10/output/F10_TESTING_DATA_RESULTS.md`](file:///d:/Scoring%20engine/f10/output/F10_TESTING_DATA_RESULTS.md): **Master Comprehensive Production Audit & Testing Data Results Report** (Data Dictionary, Formula Architecture, 50,000-order audit, and all test cases in one place).
- [`f10/docs/`](file:///d:/Scoring%20engine/f10/docs/): Comprehensive documentation suite (12 deliverables).

---

## 4. End-to-End Execution Guide

### Step 1: Generate Probes & Registry
```powershell
python f10/code/build_probes.py
```

### Step 2: Generate Golden Test Cases (>= 150 cases)
```powershell
python f10/code/build_golden_cases.py
```

### Step 3: Generate 50,000 Synthetic Orders & Sidecars
```powershell
python f10/code/generator.py
python f10/code/fidelity_checker.py
```

### Step 4: Execute Production Pipeline
```powershell
python f10/code/pipeline.py
```

### Step 5: Run Sensitivity Calibration Study
```powershell
python f10/code/sensitivity.py
```

### Step 6: Run Full 12-Layer Test Suite
```powershell
python f10/code/test_suite.py
```
