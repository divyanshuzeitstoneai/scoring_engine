# Formula F10 Product Contribution v2: Formal Mathematical Specification

**Target API:** Shopify Admin GraphQL API `2024-10`  
**Precision Standard:** Fixed-point Python `Decimal` (quantized to `currency_minor_units` via `rounding_mode`)  
**Aggregation Principle:** Ratio of Sums (Never average per-order percentages)

---

## 1. Core Grain & Boundary Principles

1. **Atomic Unit:** One order line item (`LineItem`). Every financial and operational quantity is decomposed to this atomic level.
2. **Order-to-Line Allocation:** Order-level variables (shipping charged, courier invoices, gateway fees, goodwill adjustments) are distributed to line items via the **largest-remainder method (Hare-Niemeyer)** at the currency's minor unit. Sum conservation is absolute ($0.0000$ drift).
3. **Maturity & Rolling Windows:** Calculated over trailing 30, 90, and 365 days ending at explicit `config.as_of`. A line is matured if:
   $$\text{order\_date} + \text{return\_window\_days} + \text{processing\_days} \le \text{as\_of}$$
   Unmatured lines are classified as `PROVISIONAL` and excluded from ranking scores.

---

## 2. Revenue Decomposition

$$\begin{aligned}
\text{GrossLine} &= \text{originalTotalSet.shopMoney.amount} \\
\text{DiscLine} &= \sum \text{discountAllocations.allocatedAmountSet.shopMoney.amount} \\
\text{NetBilled} &= \text{GrossLine} - \text{DiscLine} \\
\text{RefundItem} &= \sum \text{refundLineItems.subtotalSet.shopMoney.amount} \\
\text{Goodwill} &= \text{attribution per } \texttt{config.goodwill\_rule} \\
\text{RetainedRev} &= \text{NetBilled} - \text{RefundItem} - \text{Goodwill}
\end{aligned}$$

> [!NOTE]
> **Rejection of `discountedTotalSet`:** `discountedTotalSet` in Shopify GraphQL excludes cart discounts, excludes code discounts unless specific query arguments are passed, and aggregates refunded/removed units. `discountAllocations` provides the only auditable ground truth for line discounts.

---

## 3. Unit Taxonomy

| Symbol | Definition | Derivation Rule |
| :--- | :--- | :--- |
| $q_{\text{ordered}}$ | Units originally purchased | `LineItem.quantity` |
| $q_{\text{removed}}$ | Units removed via order edit | $\max(0, q_{\text{ordered}} - \text{currentQuantity} - q_{\text{cancelled}} - q_{\text{refunded}})$ |
| $q_{\text{cancelled}}$ | Units cancelled before fulfillment | Refunded units with `restockType == CANCEL` or pre-capture order cancellation |
| $q_{\text{shipped}}$ | Units physically fulfilled | Successful `FulfillmentLineItem.quantity` or $q_{\text{ordered}} - q_{\text{cancelled}} - q_{\text{removed}}$ |
| $q_{\text{refunded}}$ | Units refunded post-sale | Sum of `RefundLineItem.quantity` |
| $q_{\text{restocked}}$ | Units returned & restocked | Units in `RefundLineItem` with `restockType` $\in \{\text{RESTOCK}, \text{RETURN}\}$ |
| $q_{\text{not\_restocked}}$ | Refunded units not restocked | $\max(0, q_{\text{refunded}} - q_{\text{restocked}})$ |
| $q_{\text{lost\_returns}}$ | Unrestocked units written off | Evaluated per `config.no_restock_policy` (`lost` $\to q_{\text{not\_restocked}}$, `kept_by_customer` $\to 0$) |
| $q_{\text{kept}}$ | Net units retained by customer | $\max(0, q_{\text{shipped}} - q_{\text{refunded}})$ |

> [!IMPORTANT]
> **Cancellation Invariant:** Cancelled or removed units never shipped: they carry **zero COGS** and **zero outbound shipping**.

---

## 4. Cost of Goods Lost (COGS)

$$\text{COGS}_{\text{lost}} = (q_{\text{kept}} + q_{\text{lost\_returns}}) \times \text{cost\_snapshot}$$

- **Restocked Units:** Recover 100% of their inventory cost ($0.00$ charged to $\text{COGS}_{\text{lost}}$).
- **Written-Off Units:** Charged at full unit inventory replacement cost.
- **Unresolved Policy:** If `no_restock_policy == "unknown"`, units are routed to `cogs_unresolved` ledger and flagged.

---

## 5. Direct Operational Costs & Evidence Tiers

Costs carry auditable evidence tiers:
- **T1:** Actual Shopify Admin API data (e.g. `OrderTransaction.fees`).
- **T2:** Merchant-confirmed configuration parameters.
- **T3:** Derived from Shopify fields.
- **T4:** Category prior (unconfirmed estimate).

$$\begin{aligned}
\text{Outbound} &= \text{carrier\_cost\_allocated} - \text{shipping\_charged\_allocated} \quad [\text{T2/T3}] \\
\text{PayFees} &= \text{OrderTransaction.fees} \text{ (T1) else } (\text{NetBilled} \times \text{rate} + \text{fixed}) \quad [\text{T2}] \\
\text{ReturnShip} &= q_{\text{physical\_returns}} \times \texttt{config.return\_ship\_cost} \quad [\text{T2}] \\
\text{Handling} &= q_{\text{physical\_returns}} \times \texttt{config.handling\_cost} \quad [\text{T2}] \\
\text{Packaging} &= q_{\text{shipped}} \times \texttt{config.pick\_pack\_cost} \quad [\text{T2}]
\end{aligned}$$

---

## 6. Variant Financial Metrics & Health Status

$$\begin{aligned}
\text{Contribution} &= \text{RetainedRev} - \text{COGS}_{\text{lost}} - \text{Outbound} - \text{PayFees} - \text{ReturnShip} - \text{Handling} - \text{Packaging} \\
\text{MarginPct} &= \begin{cases} 
\frac{\text{Contribution}}{\text{RetainedRev}} \times 100 & \text{if } \text{RetainedRev} > 0 \\
\text{null} & \text{if } \text{RetainedRev} \le 0 
\end{cases} \\
\text{Score} &= \begin{cases}
0.00 & \text{if } \text{RetainedRev} \le 0 \text{ and } \text{TotalCosts} > 0 \\
\text{null} & \text{if unscoreable or no data} \\
\text{clamp}(\text{MarginPct}, 0, 100) & \text{otherwise}
\end{cases} \\
\text{NaiveProfit} &= \text{NetBilled} - (q_{\text{shipped}} \times \text{cost\_snapshot}) \\
\text{HiddenLeakage} &= \text{NaiveProfit} - \text{Contribution}
\end{aligned}$$

### Variant Status Evaluation Matrix:
- `NO_DATA`: 0 orders in window.
- `PROVISIONAL`: Young orders within return/processing maturity window.
- `UNSCOREABLE`: Quarantined cost share $> \texttt{config.max\_unknown\_cost\_share}$.
- `VALUE_DESTROYING`: $\text{RetainedRev} \le 0$ with costs $> 0$, OR $\text{Contribution} < 0$.
- `BREAKEVEN`: $\text{Contribution} == 0.00$.
- `HEALTHY`: $\text{MarginPct} \ge \text{healthy\_margin\_by\_category}[\text{category}]$.
- `UNDERPERFORMING`: $0 < \text{MarginPct} < \text{healthy\_margin\_by\_category}[\text{category}]$.
- `LOW_CONFIDENCE`: Total ordered units $< \texttt{config.min\_units\_for\_confidence}$.
