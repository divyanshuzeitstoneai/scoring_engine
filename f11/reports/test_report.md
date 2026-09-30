# Formula F11 Test Execution Report

**Execution Status:** `35 / 35 TEST MODULES PASSING (100.0%)`  
**Test Layers Verified:** Formula Normative, Invariants, 384 Lane Truth Table, DuckDB SQL Reconciliation, Mutation Tests, Differential Engine vs Reference.

---

## 1. Test Layer Breakdown

| Test Suite | Purpose | Tests | Result |
| :--- | :--- | :--- | :--- |
| `test_formula_section15.py` | Normative hand-computed fixtures (B0, B1, Doc-2, FT-R, FT-C, FT-S, FT-G, FT-E) | 16 | `16 / 16 PASS` |
| `test_lane_truth_table.py` | 384 Cartesian product lane combinations & P_upper boundary trio | 2 | `2 / 2 PASS` (384 asserted) |
| `test_boundaries.py` | Classification and band edge integer cross-multiplication (5999, 6000, 1999, 2000) | 3 | `3 / 3 PASS` |
| `test_invariants.py` | Invariants I-1 through I-8 (decomposition sum, P_upper bound, lane partitioning) | 3 | `3 / 3 PASS` |
| `test_differential.py` | Production vectorized engine vs naive reference implementation on orders | 1 | `1 / 1 PASS` (100/100 match) |
| `test_reconciliation.py` | Independent DuckDB SQL query verification on raw JSONL | 1 | `1 / 1 PASS` |
| `test_mutation.py` | Mutation tests killing defect mutants (double counting, missing fees, rounded bands) | 6 | `6 / 6 PASS` (100% mutants killed) |
| `test_v1_vs_v2.py` | Legacy v1 sensitivity proof (7 defect toggles) | 3 | `3 / 3 PASS` |

---

## 2. Key Invariant Assertions
- **I-1:** Driver decomposition sums to $P$ identically: $\sum 	ext{Drivers} \equiv P$.
- **I-3:** Lane totals strictly partition the population: $	ext{MEASURED} + 	ext{ESTIMATED} + 	ext{CONFIRMED\_LOSS} + 	ext{UNDETERMINED} + 	ext{EXCLUDED} = 50,000$.
- **I-4:** $P_{	ext{upper}} \ge P$ on all evaluated orders.
- **I-8:** Realized customer refunds replace provisions completely with 0 double counting.
