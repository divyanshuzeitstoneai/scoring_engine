# Formula F11 Specification v2.1

## 1. Sold-Unit Basis and Line Mathematics (Amendment A1)
All financial amounts are strictly calculated in integer minor units (e.g. cents) in shop currency (`shopMoney`).

For line item $\ell$:
- $q_0 = \text{quantity}$ (originally ordered)
- $q_c = \text{currentQuantity}$ (active, unrefunded)
- $q_e = \max(0, q_0 - q_c - \text{refunded\_units})$ (removed by edit)
- $q_s = \max(0, q_0 - q_e)$ (sold units)

Financial derivations:
$$\text{gross}_\ell = u \times q_s$$
$$\text{disc}_\ell = \text{allocated\_discounts} \times \frac{q_s}{q_0}$$
$$\text{net}_\ell = \text{gross}_\ell - \text{disc}_\ell - \text{embedded\_tax}_\ell$$
$$\text{cost}_\ell = \text{unitCost} \times q_s$$

---

## 2. Order Aggregations
- **Net Merchandise Revenue ($R$):** $R = \sum \text{net}_\ell$
- **Shipping Collected ($S_c$):** Active shipping charged, stripped of statutory tax on tax-inclusive stores.
- **Commercial Inflow ($C$):** $C = R + S_c$
- **Cost of Goods Sold ($\text{COGS}$):** $\text{COGS} = \sum \text{cost}_\ell$ (or $\text{NULL}$ if any line cost missing)
- **Carrier Shipping Cost ($S$):** Measured if actual carrier invoice exists; structural zero if digital/pickup; estimated by rate card; else $\text{NULL}$.
- **Gateway Processing Fees ($G$):** Measured from transaction fees; structural zero if COD/manual; estimated via schedule; else $\text{NULL}$.
- **Refund & Return Costs ($E$):**
  - If realized refund exists: $\text{Refunded} - \text{COGS recovered} + \text{Return shipping} + \text{Restock fee}$.
  - If window open and no refund: $r \times R$ (estimated provision).
  - If window closed and no refund: $0$ (measured).
- **Overhead ($O$):** Configured packaging and operational handling fees.

---

## 3. Contribution Profit & Upper Bound ($P_{\text{upper}}$)
$$\text{Profit } P = C - \text{COGS} - S - G - E - O$$
$$P_{\text{upper}} = C - \sum(\text{measured and structural costs only})$$

### Evidentiary Lanes:
1. `MEASURED`: No estimated or missing components. $P$ is exact.
2. `ESTIMATED`: COGS complete; $\ge 1$ estimated component.
3. `CONFIRMED_LOSS`: Any missing or estimated component AND $P_{\text{upper}} < 0$.
4. `UNDETERMINED`: Missing COGS (or unmeasured component) AND $P_{\text{upper}} \ge 0$. Headroom stored as $P_{\text{upper}}$.
5. `EXCLUDED`: Test orders, pre-capture voided, cancelled before fulfillment.

---

## 4. Exact Driver Decomposition
$$P = (L - \text{COGS}) - D + (S_c - S) - G - E - O$$
1. **Product Margin at List:** $L - \text{COGS}$
2. **Discount Leak:** $-D$
3. **Shipping Net:** $S_c - S$ (negative indicates shipping subsidy)
4. **Gateway Fee Leak:** $-G$
5. **Refund Leak:** $-E$
6. **Operational Leak:** $-O$
Identity holds exactly: $\sum \text{Drivers} \equiv P$.
