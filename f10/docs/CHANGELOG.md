# Formula F10: Changelog & Architectural Flaw Resolutions

**Document:** F10 Product Contribution v1 $\to$ v2 Migration Log  
**Formula Version:** `v2.0`  
**API Target:** Shopify Admin GraphQL API `2024-10`

---

## 1. Summary of Flaws Fixed in Formula F10 v2

| # | Flaw Identified in Prior Versions | Root Cause & Damage | Formula F10 v2 Production Resolution |
|---|---|---|---|
| **F-01** | **COGS charged on restocked units** | Prior formula charged inventory cost on all returned units, even when restocked into inventory, artificially penalizing high-volume sellable apparel. | **Resolved:** Restocked units recover 100% of cost. $\text{COGS}_{\text{lost}} = (q_{\text{kept}} + q_{\text{lost\_returns}}) \times \text{cost}$. Restocked units contribute $\$0.00$ to COGS loss. |
| **F-02** | **Double-counted damaged items** | Flawed logic counted written-off returns both as lost inventory and as direct cash damage penalties. | **Resolved:** Unit taxonomy cleanly isolates $q_{\text{lost\_returns}}$ into inventory write-off once without secondary cash penalties. |
| **F-03** | **Margin denominator including refunded revenue** | Calculating profit margin over gross or net billed revenue rather than retained revenue distorted true commercial margin when refund rates were high. | **Resolved:** Margin denominator strictly uses $\text{RetainedRev} = \text{NetBilled} - \text{RefundItem} - \text{Goodwill}$. Returns are completely removed from denominator. |
| **F-04** | **$0.00 for unknown COGS** | Setting missing variant costs to $\$0.00$ falsely inflated variant margin to 100%, misleading merchandising teams. | **Resolved:** Uncosted lines assigned `COGS_MISSING` and quarantined. Variants exceeding 15% unknown revenue are classified `UNSCOREABLE`. |
| **F-05** | **Current rather than historical COGS** | Querying current inventory cost distorted historical cohort performance when costs changed post-sale. | **Resolved:** Mandated point-in-time cost capture table. Backfilled lines without snapshot flagged `cost_not_point_in_time`. |
| **F-06** | **Ignoring customer return lag** | Scoring young orders before return windows closed created premature false positive profitability rankings. | **Resolved:** Enforced return maturity window ($\text{order\_date} + 30 + 5 \le \text{as\_of}$). Immature orders flagged `PROVISIONAL` and excluded from scoring. |
| **F-07** | **Revenue-share shipping allocation** | Allocating courier shipping fees by dollar revenue charged heavy coats less shipping than lightweight jewelry. | **Resolved:** Physical weight-based allocation with deterministic fallback to NetBilled share and largest-remainder penny conservation. |
| **F-08** | **Arbitrary 5% restocking fee assumption** | Hardcoded 5% handling cost assumption masked actual 3PL warehouse labor costs. | **Resolved:** Formalized Tier T2 configured costs (`handling_cost`, `return_ship_cost`). Missing config marks cost `UNKNOWN`, never guessing a default. |
