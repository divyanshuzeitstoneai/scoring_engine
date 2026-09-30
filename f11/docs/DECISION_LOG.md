# Decision Log (`[CFG]` Choices & Architectural Invariants)

| Decision ID | Area | Selected Choice | Rationale & Evidence | Date | Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **DEC-01** | Sold-Unit Basis | Amendment A1 implemented | Prevents severe double-counting of customer refunds on both line revenue and refund cost. | 2026-09-30 | `ACCEPTED` |
| **DEC-02** | Zero-Fee Gateways | Manual/COD = structural zero | Prevents false `UNDETERMINED` quarantine on legitimate non-fee payment methods. | 2026-09-30 | `ACCEPTED` |
| **DEC-03** | Empty Dataset | Margin NULL, counts 0 | Prevents false 0% breakeven collision when no data exists. | 2026-09-30 | `ACCEPTED` |
| **DEC-04** | Margin Denominator | $C_{\text{sold}}$ | Preserves consistent revenue baseline even on partially refunded orders. | 2026-09-30 | `ACCEPTED` |
| **DEC-05** | Window Boundary | Age < N days strictly open | Day 30 at 00:00 UTC is closed; releases provision deterministically. | 2026-09-30 | `ACCEPTED` |
| **DEC-06** | Integer Math | Integer minor units | Eliminates float representation discrepancies at boundary pennies. | 2026-09-30 | `ACCEPTED` |
