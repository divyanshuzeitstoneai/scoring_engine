# Oracle Validity Report: Engine vs Latent Truth

Evaluates production engine outputs against the sealed latent-truth answer key (`answer_key.parquet`).

---

## 1. Lane Performance & Metric Accuracy

| Evidentiary Lane | Order Count | Headline Accuracy Metric | Tolerance Gate | Audit Status |
| :--- | :--- | :--- | :--- | :--- |
| **`MEASURED`** | 18,240 | **0 minor unit discrepancy** against true measured costs | 0.00% Tolerance | `EXACT MATCH` |
| **`ESTIMATED`** | 24,960 | Mean Absolute Percentage Error (MAPE) = **1.14%** of $C$ | $\le 2.0\%$ Gate | `PASS` |
| **`CONFIRMED_LOSS`** | 3,120 | **Precision: 100.0%** (every confirmed loss was a true economic loss) | 100.0% Gate | `PERFECT` |
| **`UNDETERMINED`** | 2,130 | Quarantined missing costs; average headroom = $68.40 | N/A (Quarantine) | `CONSERVED` |
| **`EXCLUDED`** | 1,550 | Filtered test, cancelled, voided orders | N/A (Excluded) | `EXCLUDED` |

---

## 2. Summary
- **Zero False Alarms in CONFIRMED_LOSS:** 100% of orders identified as confirmed losses were true losses, protecting merchant confidence.
- **Biases in ESTIMATED Lane:** Store-level estimation bias is $+0.42\%$ of $C$, well within the $\pm 2.0\%$ operational ceiling.
