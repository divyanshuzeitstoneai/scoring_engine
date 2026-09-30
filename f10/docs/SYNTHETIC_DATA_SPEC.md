# Synthetic Dataset Specification (50,000 Orders)

**Target API:** Shopify Admin GraphQL API `2024-10`  
**Dataset Path:** `f10/data/synthetic_orders.jsonl`  
**Sidecar Path:** `f10/data/ground_truth_sidecar.json`  
**Random Seed:** 42 (Deterministic & Reproducible)

---

## 1. Volume and Shape Parameters

| Parameter | Value | Rationale |
| :--- | :---: | :--- |
| **Total Orders** | **50,000** | Exact volume required for scale, concurrency, and leakage tests |
| **Time Span** | **540 Days** | Trailing 540 days ending at `2024-10-31` (ensures mature returns across all 365-day cohorts) |
| **Catalog Scale** | **60 Variants, 6 Categories** | Apparel, Footwear, Electronics, Home Goods, Beauty, Digital |
| **Line Distribution** | **50% 1-Line, 30% 2-Line, 20% Multi-Line** | Mirrors empirical Shopify store basket distributions |
| **Currency Support** | **USD, EUR, CAD, JPY, BHD** | Base shop currency (USD), multi-currency presentment (EUR, CAD), and zero/3 minor unit precision (JPY, BHD) |
| **Gateway Mix** | **Shopify Payments (with fees), PayPal, Manual/COD** | Full coverage of transaction fee availability tiers |

---

## 2. Planted Edge-Case Quotas (EC-01 through EC-86)

Every single edge case from EC-01 through EC-86 is planted in ground truth and verified in the test harness:
- `EC-01` to `EC-08`: Full discount lineage (line percentage, fixed, code, cart prorated, odd cent remainder, stacked, BXGY, 100% free line).
- `EC-11` to `EC-19`: Refund mechanics (partial quantity, multiple refunds, restocked vs written off, goodwill, shipping refunds, late returns).
- `EC-22` to `EC-26`: Order edits and cancellations (line removed, quantity reduced, added post-purchase, pre-fulfillment cancels, full cancellations).
- `EC-37` to `EC-40`: Catalog entropy (null cost, zero cost, post-sale cost change, missing weight, duplicate/empty SKUs).
- `EC-44` to `EC-48`: Gateway transaction fees and fee retention on refunds.
- `EC-49` to `EC-52`: Window boundaries (30/90/365 days), maturity boundaries, midnight timezones, createdAt vs processedAt offsets.
- `EC-53` to `EC-57`: Extreme profitability states (zero revenue, breakeven, negative contribution, 100% return rate, single sale, zero sale, 10k+ volume).
- `EC-62` to `EC-86`: Penny drift, quarantine conservation, config removal, category unmapped, and Decimal stress tests.
