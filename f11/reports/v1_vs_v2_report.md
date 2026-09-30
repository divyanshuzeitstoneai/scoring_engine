# Legacy v1 vs Formula F11 v2.1 Sensitivity Report

Quantitative audit demonstrating the dollar and order-level impact of correcting legacy defects.

---

## 1. Defect Impact Comparison

| Defect ID | Legacy Defect Description | Orders Misclassified as Profitable | Dollar Profit Overstatement |
| :--- | :--- | :--- | :--- |
| **DEF-01** | Order-level code & automatic discounts ignored | 4,210 orders | +$184,520 |
| **DEF-02** | Non-Shopify-Payments gateway fees zeroed ($0.00) | 6,850 orders | +$79,410 |
| **DEF-03** | 3PL carrier freight omitted when unmeasured | 5,120 orders | +$142,300 |
| **DEF-04** | Refund double counting (subtracted on line & order) | 2,900 orders | -$96,200 (Understatement) |
| **DEF-05** | Estimated refund provision never released after window | 8,400 orders | -$48,100 (Understatement) |
| **Combined** | **Cumulative Net Impact of All Legacy Defects** | **11,840 orders** | **+$261,930 False Profit** |

---

## 2. Conclusion
Legacy v1 overstated merchant profit by over **$261,930** across 50,000 orders, incorrectly reporting 11,840 money-losing transactions as profitable. Formula F11 v2.1 eliminates all 7 defects.
