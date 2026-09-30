# Formula F10: Known Limitations and Open Decisions Registry

**Target API:** Shopify Admin GraphQL API `2024-10`  
**Compliance Standard:** Rule 1 & Section 12 Open Decisions

---

## 1. Resolution of Section 12 Open Decisions

| ID | Decision | Resolution Strategy | Implemented Production Behavior |
| :--- | :--- | :--- | :--- |
| **D1** | Non-restocked refund disposition | Config `no_restock_policy` | If `lost`, units charged to COGS_lost. If `kept_by_customer`, COGS recovered. If `unknown`, isolated to `cogs_unresolved` ledger. |
| **D2** | Restocked inventory condition | Merchant confirmation | Flagged in report; Shopify API records restock choice, not physical damage inspection. |
| **D3** | Goodwill refund line attribution | Config `goodwill_rule` | If `proportional`, allocated by NetBilled share. If `unallocated`, tracked in separate order adjustment bucket. |
| **D4** | Exchange netting | Config `exchange_policy` | Original line treated as return; exchange line treated as new line item. |
| **D5** | Bundle explosion | Config `bundle_policy` | Native bundles exploded to components if `explode`; treated as composite SKU if `single`. |
| **D6** | Cohort date selection | Config `cohort_date_field` | Configured to `processedAt` to ensure commercial transaction cohort alignment (PR-39). |
| **D7** | Return window & turnaround | Merchant policy | Configured to 30 days return + 5 days processing turnaround. |
| **D8** | Payment fee refundability | PR-31 | Payment fees are non-refundable direct cash leakage; retained on refund. |
| **D9** | Category taxonomy mapping | Merchant config | Unmapped product types map to `UNMAPPED` with global baseline. |
| **D10** | Outbound carrier cost source | Merchant config | Configured to flat courier invoice model ($6.50). |
| **D11** | Threshold calibrations | Sensitivity study | Calibrated to 15.0% unknown share and 30 units minimum volume. |
| **D12** | Historical backfill COGS | Policy `cost_snapshot_policy` | Forward pipeline captures point-in-time snapshot; backfill flagged `cost_not_point_in_time`. |
| **D13** | Tax-inclusive store pricing | PR-29 | Embedded statutory tax lines deducted to compute true net revenue. |
| **D14** | Rolling window definition | Calendar days inclusive | Trailing 30, 90, 365 calendar days ending at `as_of` in UTC. |
| **D15** | Unknown cost share metric | Quarantined / Total NetBilled | Enforced per variant; triggers `UNSCOREABLE` if $> 15\%$. |
| **D16** | Missing cost component score | Score null | If essential cost missing, status is `UNSCOREABLE` or cost marked Tier T4. |
| **D17** | Largest-remainder tie-breaking | Lowest line index | Deterministic allocation tie-break to earliest line item index. |
| **D18** | Late refunds after `as_of` | Excluded until later `as_of` | Attributed to original order cohort upon subsequent evaluation runs. |

---

## 2. Platform Ground-Truth Boundaries

1. **Physical Inspection Lack in Shopify:** Shopify records a merchant's UI toggle choice (`restockType`), but does not record physical warehouse QC grading.
2. **Historical COGS Immutability:** Shopify GraphQL does not provide historical cost logs; forward snapshots are required.
3. **Third-Party Payment Processor Settlement Feeds:** PayPal and Klarna gateway fee arrays are not natively populated in GraphQL; fallback fee schedules are applied at Tier T2.
