# Formula F11 Order Profitability v2.1

A mathematically rigorous, vectorized order-level contribution profitability engine for Shopify stores.
Engineered exclusively for Shopify Admin API version **2024-10**.

---

## 1. Quick Start & Execution Workflow

Execute each phase with a single command:

### Phase 1: Generate Synthetic Data (50,000 Orders + Latent Truth)
```bash
python f11/generator/generator.py
```
*Outputs:* `f11/data/synthetic_orders.jsonl` (visible layer) and `f11/data/answer_key.parquet` (sealed latent truth).

### Phase 2: Run Production Batch Pipeline
```bash
python -c "from f11.engine.pipeline import run_pipeline; run_pipeline()"
```
*Outputs:* `f11/output/order_profitability.parquet`, `order_profitability.csv`, and `run_manifest.json`.

### Phase 3: Run Full Automated QA Test Suite
```bash
pytest -o pythonpath=. f11/tests/
```
Runs all 35+ test modules including 384-combination lane truth table, hand-computed fixtures, Invariants I-1 through I-8, DuckDB SQL reconciliation, and mutation tests.

### Phase 4: Generate All Audit & Validation Reports
```bash
python f11/reports/generate_reports.py
```
Produces `dq_report.md`, `test_report.md`, `validity_report.md`, `v1_vs_v2_report.md`, and `production_readiness.md`.

---

## 2. Directory Structure

```
f11/
  config/            f11.config.yaml, schema.json, profiles/ (strict, balanced, lenient)
  data/              synthetic_orders.jsonl, synthetic_orders_sample.json, answer_key.parquet
  docs/              Specification, Audit Answers, Data Dictionary, Scenarios, Runbook
  engine/            formula.py (vectorized production engine), pipeline.py (batch executor)
  fixtures/          golden/ (B0, B1, Doc-2 YAMLs), formula/ (component fixtures)
  generator/         generator.py (50k order generator), params.yaml
  graphql/           Introspection dump, *.graphql query pack
  mockserver/        server.py (in-memory GraphQL mock server & bulk op emulator)
  output/            order_profitability.parquet, run_manifest.json
  reference/         reference_formula.py (naive independent reference implementation)
  reports/           dq_report.md, test_report.md, validity_report.md, v1_vs_v2_report.md
  tests/             test_formula_section15.py, test_boundaries.py, test_invariants.py, etc.
```
