# F10 v2 Formula Test Cases (hand-checked, executed)

Companion to `F10_test_and_build_prompt.md`. **Status:** all 29 formula cases, 6 allocation cases, 6 date cases and 6 metamorphic checks below were executed against a Decimal reference implementation and matched the hand-calculated values. The 20,000 random allocation checks also summed exactly.

**What this does and does not prove:** these tests start from *normalised line facts* (net billed, units, refund amounts, cost). They prove the formula arithmetic, quarantine and status rules. They do **not** prove how Shopify reports those facts (discount allocation, refund subtotal basis, order edits, restock types). That is what the dev-store probes (PR-xx) and the extraction-layer tests are for.

## Fixture configuration (declared test inputs, not claims about any real store)

| Parameter | Value |
|---|---|
| return shipping per physical return | 6.50 |
| handling per physical return | 5.00 |
| pick-pack per unit | 0.00 |
| no_restock_policy | lost (unless the case says otherwise) |
| min_units_for_confidence | 30 (proposal) |
| max_unknown_cost_share | 0.15 (proposal), rule: strictly greater than |
| healthy margin | 25% inclusive (proposal) |
| currency minor units | 2 |
| as_of | 2026-09-30, shop timezone America/New_York |

## Rules the cases enforce

```
RetainedRev = NetBilled - RefundItem - Goodwill
COGS_lost   = (q_shipped - q_refunded + q_not_restocked) x cost_snapshot     [policy lost or kept_by_customer]
physical returns = q_restocked + (q_not_restocked if policy = lost else 0)
Contribution = RetainedRev - COGS_lost - Outbound - Fees - ReturnShip x phys - Handling x phys - PickPack x q_shipped
Margin = Contribution / RetainedRev x 100   (null if RetainedRev <= 0)
Score  = clamp(Margin, 0, 100); 0 if RetainedRev <= 0 and costs > 0
Leakage = NaiveProfit - Contribution, where NaiveProfit = NetBilled - q_shipped x cost
```

## A. Formula cases

### FT-01: Dress, 40% returns, 30 restocked / 10 written off
*Proves:* Restocked units recover cost; only unsold and lost units carry COGS (fixes Flaw 1)

| Line | net billed | shipped | refunded | restocked | refund $ | goodwill | cost | outbound | fees |
|---|---|---|---|---|---|---|---|---|---|
| L | 10000.00 | 100 | 40 | 30 | 4000.00 | 0.00 | 40.00 | 500.00 | 300.00 |

*Hand check:* 10,000 - 4,000 = 6,000; COGS (100-40+10) x 40 = 2,800; return ship 40 x 6.50 = 260; handling 40 x 5 = 200; 6,000 - 2,800 - 500 - 300 - 260 - 200 = 1,940.

*Expected:* `status` = **HEALTHY**; `confidence` = **OK**; `retained` = **6000.00**; `cogs` = **2800.00**; `phys` = **40**; `contribution` = **1940.00**; `margin` = **32.33%**; `score` = **32.33**; `leakage` = **4060.00**; `rev_scored` = **10000.00**; `rev_quarantined` = **0**; `unknown_share` = **0.0%**

### FT-02: Same dress, all 40 returns written off
*Proves:* Worst-case disposition; equals the old spec figure

| Line | net billed | shipped | refunded | restocked | refund $ | goodwill | cost | outbound | fees |
|---|---|---|---|---|---|---|---|---|---|
| L | 10000.00 | 100 | 40 | 0 | 4000.00 | 0.00 | 40.00 | 500.00 | 300.00 |

*Expected:* `status` = **UNDERPERFORMING**; `confidence` = **OK**; `retained` = **6000.00**; `cogs` = **4000.00**; `phys` = **40**; `contribution` = **740.00**; `margin` = **12.33%**; `score` = **12.33**; `leakage` = **5260.00**; `rev_scored` = **10000.00**; `rev_quarantined` = **0**; `unknown_share` = **0.0%**

### FT-03: Same dress, all 40 returns restocked
*Proves:* Best-case disposition

| Line | net billed | shipped | refunded | restocked | refund $ | goodwill | cost | outbound | fees |
|---|---|---|---|---|---|---|---|---|---|
| L | 10000.00 | 100 | 40 | 40 | 4000.00 | 0.00 | 40.00 | 500.00 | 300.00 |

*Expected:* `status` = **HEALTHY**; `confidence` = **OK**; `retained` = **6000.00**; `cogs` = **2400.00**; `phys` = **40**; `contribution` = **2340.00**; `margin` = **39.00%**; `score` = **39.00**; `leakage` = **3660.00**; `rev_scored` = **10000.00**; `rev_quarantined` = **0**; `unknown_share` = **0.0%**

### FT-04: Healthy accessory, 2% returns, both restocked
*Proves:* Low-return product; return costs only on physical returns

| Line | net billed | shipped | refunded | restocked | refund $ | goodwill | cost | outbound | fees |
|---|---|---|---|---|---|---|---|---|---|
| L | 5000.00 | 100 | 2 | 2 | 100.00 | 0.00 | 15.00 | 250.00 | 100.00 |

*Expected:* `status` = **HEALTHY**; `confidence` = **OK**; `retained` = **4900.00**; `cogs` = **1470.00**; `phys` = **2**; `contribution` = **3057.00**; `margin` = **62.39%**; `score` = **62.39**; `leakage` = **443.00**; `rev_scored` = **5000.00**; `rev_quarantined` = **0**; `unknown_share` = **0.0%**

### FT-05: Goodwill refund only, no return
*Proves:* No units returned so return shipping and handling are 0

| Line | net billed | shipped | refunded | restocked | refund $ | goodwill | cost | outbound | fees |
|---|---|---|---|---|---|---|---|---|---|
| L | 1000.00 | 10 | 0 | 0 | 0.00 | 10.00 | 30.00 | 50.00 | 30.00 |

*Expected:* `status` = **HEALTHY**; `confidence` = **LOW_CONFIDENCE**; `retained` = **990.00**; `cogs` = **300.00**; `phys` = **0**; `contribution` = **610.00**; `margin` = **61.62%**; `score` = **61.62**; `leakage` = **90.00**; `rev_scored` = **1000.00**; `rev_quarantined` = **0**; `unknown_share` = **0.0%**

### FT-06: Refunded, not restocked, customer kept item (policy kept_by_customer)
*Proves:* COGS lost, but no physical return so no return costs

| Line | net billed | shipped | refunded | restocked | refund $ | goodwill | cost | outbound | fees |
|---|---|---|---|---|---|---|---|---|---|
| L | 100.00 | 1 | 1 | 0 | 100.00 | 0.00 | 40.00 | 8.00 | 3.00 |

*Expected:* `status` = **VALUE_DESTROYING**; `confidence` = **LOW_CONFIDENCE**; `retained` = **0.00**; `cogs` = **40.00**; `phys` = **0**; `contribution` = **-51.00**; `margin` = **null**; `score` = **0.00**; `leakage` = **111.00**; `rev_scored` = **100.00**; `rev_quarantined` = **0**; `unknown_share` = **0.0%**

### FT-07: Same as FT-06 under policy unknown
*Proves:* Must not guess; result is UNRESOLVED with no dollar metrics

| Line | net billed | shipped | refunded | restocked | refund $ | goodwill | cost | outbound | fees |
|---|---|---|---|---|---|---|---|---|---|
| L | 100.00 | 1 | 1 | 0 | 100.00 | 0.00 | 40.00 | 8.00 | 3.00 |

*Expected:* `status` = **UNRESOLVED**; `confidence` = **LOW_CONFIDENCE**; `contribution` = **null**; `margin` = **null**; `score` = **null**; `rev_scored` = **100.00**; `rev_quarantined` = **0**; `unknown_share` = **0.0%**

### FT-08: 2 of 10 units cancelled before shipping
*Proves:* Cancelled units carry no COGS and no outbound cost

| Line | net billed | shipped | refunded | restocked | refund $ | goodwill | cost | outbound | fees |
|---|---|---|---|---|---|---|---|---|---|
| L | 1000.00 | 8 | 0 | 0 | 200.00 | 0.00 | 30.00 | 40.00 | 30.00 |

*Expected:* `status` = **HEALTHY**; `confidence` = **LOW_CONFIDENCE**; `retained` = **800.00**; `cogs` = **240.00**; `phys` = **0**; `contribution` = **490.00**; `margin` = **61.25%**; `score` = **61.25**; `leakage` = **270.00**; `rev_scored` = **1000.00**; `rev_quarantined` = **0**; `unknown_share` = **0.0%**

*Note:* Refund of the 2 cancelled units is in refund_item; they are not in q_refunded because they never shipped.

### FT-09: Free item (100% discount)
*Proves:* Revenue 0, costs positive: dollars shown, margin null, score 0

| Line | net billed | shipped | refunded | restocked | refund $ | goodwill | cost | outbound | fees |
|---|---|---|---|---|---|---|---|---|---|
| L | 0.00 | 5 | 0 | 0 | 0.00 | 0.00 | 20.00 | 25.00 | 0.00 |

*Expected:* `status` = **VALUE_DESTROYING**; `confidence` = **LOW_CONFIDENCE**; `retained` = **0.00**; `cogs` = **100.00**; `phys` = **0**; `contribution` = **-125.00**; `margin` = **null**; `score` = **0.00**; `leakage` = **25.00**; `rev_scored` = **0.00**; `rev_quarantined` = **0**; `unknown_share` = **0.0%**

### FT-10: Refunds plus goodwill exceed billed (negative retained revenue)
*Proves:* Margin must be null, not a huge negative percentage

| Line | net billed | shipped | refunded | restocked | refund $ | goodwill | cost | outbound | fees |
|---|---|---|---|---|---|---|---|---|---|
| L | 100.00 | 1 | 1 | 1 | 100.00 | 30.00 | 40.00 | 10.00 | 3.00 |

*Expected:* `status` = **VALUE_DESTROYING**; `confidence` = **LOW_CONFIDENCE**; `retained` = **-30.00**; `cogs` = **0.00**; `phys` = **1**; `contribution` = **-54.50**; `margin` = **null**; `score` = **0.00**; `leakage` = **114.50**; `rev_scored` = **100.00**; `rev_quarantined` = **0**; `unknown_share` = **0.0%**

### FT-11: Contribution exactly 0
*Proves:* Breakeven is neither positive nor negative

| Line | net billed | shipped | refunded | restocked | refund $ | goodwill | cost | outbound | fees |
|---|---|---|---|---|---|---|---|---|---|
| L | 100.00 | 1 | 0 | 0 | 0.00 | 0.00 | 60.00 | 30.00 | 10.00 |

*Expected:* `status` = **BREAKEVEN**; `confidence` = **LOW_CONFIDENCE**; `retained` = **100.00**; `cogs` = **60.00**; `phys` = **0**; `contribution` = **0.00**; `margin` = **0.00%**; `score` = **0.00**; `leakage` = **40.00**; `rev_scored` = **100.00**; `rev_quarantined` = **0**; `unknown_share` = **0.0%**

### FT-12: Margin exactly 25.00% (healthy threshold)
*Proves:* Threshold is inclusive: >= 25 is HEALTHY

| Line | net billed | shipped | refunded | restocked | refund $ | goodwill | cost | outbound | fees |
|---|---|---|---|---|---|---|---|---|---|
| L | 100.00 | 1 | 0 | 0 | 0.00 | 0.00 | 50.00 | 15.00 | 10.00 |

*Expected:* `status` = **HEALTHY**; `confidence` = **LOW_CONFIDENCE**; `retained` = **100.00**; `cogs` = **50.00**; `phys` = **0**; `contribution` = **25.00**; `margin` = **25.00%**; `score` = **25.00**; `leakage` = **25.00**; `rev_scored` = **100.00**; `rev_quarantined` = **0**; `unknown_share` = **0.0%**

### FT-13: Margin 24.99%
*Proves:* Just below threshold

| Line | net billed | shipped | refunded | restocked | refund $ | goodwill | cost | outbound | fees |
|---|---|---|---|---|---|---|---|---|---|
| L | 10000.00 | 100 | 0 | 0 | 0.00 | 0.00 | 50.00 | 1500.00 | 1001.00 |

*Expected:* `status` = **UNDERPERFORMING**; `confidence` = **OK**; `retained` = **10000.00**; `cogs` = **5000.00**; `phys` = **0**; `contribution` = **2499.00**; `margin` = **24.99%**; `score` = **24.99**; `leakage` = **2501.00**; `rev_scored` = **10000.00**; `rev_quarantined` = **0**; `unknown_share` = **0.0%**

### FT-14: 29 units shipped
*Proves:* Below min_units (30): LOW_CONFIDENCE, excluded from ranking

| Line | net billed | shipped | refunded | restocked | refund $ | goodwill | cost | outbound | fees |
|---|---|---|---|---|---|---|---|---|---|
| L | 290.00 | 29 | 0 | 0 | 0.00 | 0.00 | 4.00 | 0.00 | 0.00 |

*Expected:* `status` = **HEALTHY**; `confidence` = **LOW_CONFIDENCE**; `retained` = **290.00**; `cogs` = **116.00**; `phys` = **0**; `contribution` = **174.00**; `margin` = **60.00%**; `score` = **60.00**; `leakage` = **0.00**; `rev_scored` = **290.00**; `rev_quarantined` = **0**; `unknown_share` = **0.0%**

### FT-15: 30 units shipped
*Proves:* At min_units: confidence OK

| Line | net billed | shipped | refunded | restocked | refund $ | goodwill | cost | outbound | fees |
|---|---|---|---|---|---|---|---|---|---|
| L | 300.00 | 30 | 0 | 0 | 0.00 | 0.00 | 4.00 | 0.00 | 0.00 |

*Expected:* `status` = **HEALTHY**; `confidence` = **OK**; `retained` = **300.00**; `cogs` = **120.00**; `phys` = **0**; `contribution` = **180.00**; `margin` = **60.00%**; `score` = **60.00**; `leakage` = **0.00**; `rev_scored` = **300.00**; `rev_quarantined` = **0**; `unknown_share` = **0.0%**

### FT-16: Quarantine: cost missing on one line (unknown share 33.3%)
*Proves:* Above max_unknown 15%: UNSCOREABLE, score null; conservation holds

| Line | net billed | shipped | refunded | restocked | refund $ | goodwill | cost | outbound | fees |
|---|---|---|---|---|---|---|---|---|---|
| A | 600.00 | 6 | 0 | 0 | 0.00 | 0.00 | 50.00 | 0.00 | 0.00 |
| B | 400.00 | 4 | 0 | 0 | 0.00 | 0.00 | 50.00 | 0.00 | 0.00 |
| C | 500.00 | 5 | 0 | 0 | 0.00 | 0.00 | null | 0.00 | 0.00 |

*Expected:* `status` = **UNSCOREABLE**; `confidence` = **LOW_CONFIDENCE**; `contribution` = **null**; `margin` = **null**; `score` = **null**; `rev_scored` = **1000.00**; `rev_quarantined` = **500.00**; `unknown_share` = **33.3%**

### FT-17: Unknown share exactly 15.0%
*Proves:* Rule is "exceeds": equal is still scoreable

| Line | net billed | shipped | refunded | restocked | refund $ | goodwill | cost | outbound | fees |
|---|---|---|---|---|---|---|---|---|---|
| A | 850.00 | 17 | 0 | 0 | 0.00 | 0.00 | 20.00 | 0.00 | 0.00 |
| B | 150.00 | 3 | 0 | 0 | 0.00 | 0.00 | null | 0.00 | 0.00 |

*Expected:* `status` = **HEALTHY**; `confidence` = **LOW_CONFIDENCE**; `retained` = **850.00**; `cogs` = **340.00**; `phys` = **0**; `contribution` = **510.00**; `margin` = **60.00%**; `score` = **60.00**; `leakage` = **0.00**; `rev_scored` = **850.00**; `rev_quarantined` = **150.00**; `unknown_share` = **15.0%**

*Note:* Status is computed on scored lines only.

### FT-18: Unknown share 15.1%
*Proves:* Just above the limit: UNSCOREABLE

| Line | net billed | shipped | refunded | restocked | refund $ | goodwill | cost | outbound | fees |
|---|---|---|---|---|---|---|---|---|---|
| A | 849.00 | 17 | 0 | 0 | 0.00 | 0.00 | 20.00 | 0.00 | 0.00 |
| B | 151.00 | 3 | 0 | 0 | 0.00 | 0.00 | null | 0.00 | 0.00 |

*Expected:* `status` = **UNSCOREABLE**; `confidence` = **LOW_CONFIDENCE**; `contribution` = **null**; `margin` = **null**; `score` = **null**; `rev_scored` = **849.00**; `rev_quarantined` = **151.00**; `unknown_share` = **15.1%**

### FT-19: Cost = 0, not confirmed
*Proves:* Zero cost may be unset: quarantined as COGS_ZERO_SUSPECT

| Line | net billed | shipped | refunded | restocked | refund $ | goodwill | cost | outbound | fees |
|---|---|---|---|---|---|---|---|---|---|
| L | 100.00 | 1 | 0 | 0 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |

*Expected:* `status` = **UNSCOREABLE**; `confidence` = **LOW_CONFIDENCE**; `contribution` = **null**; `margin` = **null**; `score` = **null**; `rev_scored` = **0**; `rev_quarantined` = **100.00**; `unknown_share` = **100.0%**

### FT-20: Cost = 0, merchant-confirmed (digital product)
*Proves:* Confirmed zero is a real cost and is scored

| Line | net billed | shipped | refunded | restocked | refund $ | goodwill | cost | outbound | fees |
|---|---|---|---|---|---|---|---|---|---|
| L | 100.00 | 1 | 0 | 0 | 0.00 | 0.00 | 0.00 | 0.00 | 3.00 |

*Expected:* `status` = **HEALTHY**; `confidence` = **LOW_CONFIDENCE**; `retained` = **100.00**; `cogs` = **0.00**; `phys` = **0**; `contribution` = **97.00**; `margin` = **97.00%**; `score` = **97.00**; `leakage` = **3.00**; `rev_scored` = **100.00**; `rev_quarantined` = **0**; `unknown_share` = **0.0%**

### FT-21: Return shipping cost unknown, no bounds configured
*Proves:* Unknown is not 0: no score, only contribution before the unknown cost

| Line | net billed | shipped | refunded | restocked | refund $ | goodwill | cost | outbound | fees |
|---|---|---|---|---|---|---|---|---|---|
| L | 10000.00 | 100 | 40 | 30 | 4000.00 | 0.00 | 40.00 | 500.00 | 300.00 |

*Expected:* `status` = **INCOMPLETE_COSTS**; `confidence` = **OK**; `retained` = **6000.00**; `cogs` = **2800.00**; `phys` = **40**; `contribution` = **null**; `contribution_before_unknown` = **2200.00**; `margin` = **null**; `score` = **null**; `rev_scored` = **10000.00**; `rev_quarantined` = **0**; `unknown_share` = **0.0%**

### FT-22: Return shipping unknown, bounds 4.00 to 10.00
*Proves:* Show a range instead of a point

| Line | net billed | shipped | refunded | restocked | refund $ | goodwill | cost | outbound | fees |
|---|---|---|---|---|---|---|---|---|---|
| L | 10000.00 | 100 | 40 | 30 | 4000.00 | 0.00 | 40.00 | 500.00 | 300.00 |

*Expected:* `status` = **RANGE_ONLY**; `confidence` = **OK**; `retained` = **6000.00**; `cogs` = **2800.00**; `phys` = **40**; `contribution` = **null**; `contribution_before_unknown` = **2200.00**; `contribution_range` = **1800.00 to 2040.00**; `margin` = **null**; `score` = **null**; `rev_scored` = **10000.00**; `rev_quarantined` = **0**; `unknown_share` = **0.0%**

### FT-23: Same variant on two lines of one order
*Proves:* Must equal one merged line

| Line | net billed | shipped | refunded | restocked | refund $ | goodwill | cost | outbound | fees |
|---|---|---|---|---|---|---|---|---|---|
| A | 300.00 | 3 | 0 | 0 | 0.00 | 0.00 | 40.00 | 12.00 | 9.00 |
| B | 200.00 | 2 | 0 | 0 | 0.00 | 0.00 | 40.00 | 8.00 | 6.00 |

*Expected:* `status` = **HEALTHY**; `confidence` = **LOW_CONFIDENCE**; `retained` = **500.00**; `cogs` = **200.00**; `phys` = **0**; `contribution` = **265.00**; `margin` = **53.00%**; `score` = **53.00**; `leakage` = **35.00**; `rev_scored` = **500.00**; `rev_quarantined` = **0**; `unknown_share` = **0.0%**

### FT-24: Cost snapshot 40.00 vs current cost 55.00
*Proves:* Uses the snapshot taken at order time, never the current cost

| Line | net billed | shipped | refunded | restocked | refund $ | goodwill | cost | outbound | fees |
|---|---|---|---|---|---|---|---|---|---|
| L | 1000.00 | 10 | 0 | 0 | 0.00 | 0.00 | 40.00 | 20.00 | 30.00 |

*Expected:* `status` = **HEALTHY**; `confidence` = **LOW_CONFIDENCE**; `retained` = **1000.00**; `cogs` = **400.00**; `phys` = **0**; `contribution` = **550.00**; `margin` = **55.00%**; `score` = **55.00**; `leakage` = **50.00**; `rev_scored` = **1000.00**; `rev_quarantined` = **0**; `unknown_share` = **0.0%**

*Note:* If the pipeline used 55.00, COGS would be 550 and contribution 400: the test must fail then.

### FT-25: 100% return rate variant, all restocked
*Proves:* Retained revenue 0, only costs remain; leakage larger than naive profit

| Line | net billed | shipped | refunded | restocked | refund $ | goodwill | cost | outbound | fees |
|---|---|---|---|---|---|---|---|---|---|
| L | 2000.00 | 20 | 20 | 20 | 2000.00 | 0.00 | 30.00 | 100.00 | 60.00 |

*Expected:* `status` = **VALUE_DESTROYING**; `confidence` = **LOW_CONFIDENCE**; `retained` = **0.00**; `cogs` = **0.00**; `phys` = **20**; `contribution` = **-390.00**; `margin` = **null**; `score` = **0.00**; `leakage` = **1790.00**; `rev_scored` = **2000.00**; `rev_quarantined` = **0**; `unknown_share` = **0.0%**

### FT-26: Unit cost above price, no returns
*Proves:* Loses money before any return

| Line | net billed | shipped | refunded | restocked | refund $ | goodwill | cost | outbound | fees |
|---|---|---|---|---|---|---|---|---|---|
| L | 500.00 | 10 | 0 | 0 | 0.00 | 0.00 | 60.00 | 50.00 | 15.00 |

*Expected:* `status` = **VALUE_DESTROYING**; `confidence` = **LOW_CONFIDENCE**; `retained` = **500.00**; `cogs` = **600.00**; `phys` = **0**; `contribution` = **-165.00**; `margin` = **-33.00%**; `score` = **0.00**; `leakage` = **65.00**; `rev_scored` = **500.00**; `rev_quarantined` = **0**; `unknown_share` = **0.0%**

### FT-27: No sales
*Proves:* NO_DATA is null, not 0

| Line | net billed | shipped | refunded | restocked | refund $ | goodwill | cost | outbound | fees |
|---|---|---|---|---|---|---|---|---|---|
| (no lines) | | | | | | | | | |

*Expected:* `status` = **NO_DATA**; `contribution` = **null**; `margin` = **null**; `score` = **null**

### FT-28: Refund basis A: refund subtotal is post-discount (pending PR-09)
*Proves:* 2 units at 50.00, line discount 10.00; refund 1 unit = 45.00

| Line | net billed | shipped | refunded | restocked | refund $ | goodwill | cost | outbound | fees |
|---|---|---|---|---|---|---|---|---|---|
| L | 90.00 | 2 | 1 | 1 | 45.00 | 0.00 | 20.00 | 6.00 | 3.00 |

*Expected:* `status` = **UNDERPERFORMING**; `confidence` = **LOW_CONFIDENCE**; `retained` = **45.00**; `cogs` = **20.00**; `phys` = **1**; `contribution` = **4.50**; `margin` = **10.00%**; `score` = **10.00**; `leakage` = **45.50**; `rev_scored` = **90.00**; `rev_quarantined` = **0**; `unknown_share` = **0.0%**

*Note:* Use whichever basis PR-09 proves. If Shopify returns basis B, the pipeline must convert before this formula.

### FT-29: Refund basis B: refund subtotal is pre-discount (pending PR-09)
*Proves:* Same order; refund 50.00 would over-refund the 45.00 actually paid

| Line | net billed | shipped | refunded | restocked | refund $ | goodwill | cost | outbound | fees |
|---|---|---|---|---|---|---|---|---|---|
| L | 90.00 | 2 | 1 | 1 | 50.00 | 0.00 | 20.00 | 6.00 | 3.00 |

*Expected:* `status` = **VALUE_DESTROYING**; `confidence` = **LOW_CONFIDENCE**; `retained` = **40.00**; `cogs` = **20.00**; `phys` = **1**; `contribution` = **-0.50**; `margin` = **-1.25%**; `score` = **0.00**; `leakage` = **50.50**; `rev_scored` = **90.00**; `rev_quarantined` = **0**; `unknown_share` = **0.0%**

*Note:* This mismatch is exactly what gate DQ-R3 must catch if basis B is real.

## B. Allocation cases (order-level cost to lines, exact to the minor unit)

| ID | Case | Result | Why |
|---|---|---|---|
| AL-01 | 10.00 across revenues 33.33 / 33.33 / 33.34 | 3.33 / 3.33 / 3.34 | Remainder cent goes to the largest fractional part |
| AL-02 | 10.00 across three equal lines | 3.34 / 3.33 / 3.33 | Exact tie: remainder goes to the lowest line index (rule must be deterministic and documented) |
| AL-03 | JPY 1000 across three equal lines (0 minor units) | 334 / 333 / 333 | Currency with no minor unit |
| AL-04 | KWD 10.000 across 3 equal lines (3 minor units) | 3.334 / 3.333 / 3.333 | Currency with 3 minor units |
| AL-05 | Shipping 12.00 by weight 1.0 / 2.5 / 0.5 kg | 3.00 / 7.50 / 1.50 | Weight allocation, all lines have weight |
| AL-06 | Shipping 12.00 by revenue when weight missing: 60 / 30 / 10 | 7.20 / 3.60 / 1.20 | Fallback path; line must be flagged alloc_fallback |

Property check: 20,000 random allocations (random totals, 1-12 lines, random weights) all summed exactly to the order amount.

## C. Date, window and maturity cases

| ID | Case | Rule proven |
|---|---|---|
| DT-01 | Order on 2026-08-26 (window 30 + processing 5, as_of 2026-09-30) | Matured: 08-26 + 35 days = 09-30 (inclusive) |
| DT-02 | Order on 2026-08-27 | Provisional: matures 2026-10-01; excluded from ranking |
| DT-03 | 30-day window boundary: 2026-09-01 in, 2026-08-31 out | Window is 30 calendar days inclusive in shop timezone (decision D14 to ratify) |
| DT-04 | Order at 2026-09-30 23:30 New York (= 2026-10-01 03:30 UTC) | Counts as 09-30 in shop time; using UTC date would wrongly push it past as_of |
| DT-05 | Leap day: 365-day window ending 2028-03-01 | Window start is 2027-03-03 because 2028-02-29 exists (365 days inclusive) |
| DT-06 | Refund created 2026-09-25 on an order from 2026-09-02 | As-of 2026-09-20 the refund is invisible; as-of 2026-09-30 it is included and attributed to the original order cohort (restatement test EC-80) |

## D. Metamorphic checks (all passed)

| ID | Transformation | Expected |
|---|---|---|
| MM-01 | Scale all money by 3 | Contribution x3, margin unchanged |
| MM-02 | Shuffle line order (10 shuffles per multi-line case) | Identical results |
| MM-03 | Add a quarantined line (small, under the 15% limit) | Other lines unchanged; quarantined revenue increases by exactly its amount |
| MM-04 | Add a line with 0 shipped units (fully cancelled) | No change to contribution |
| MM-05 | Split one line into two vs merged | Same total contribution |
| MM-06 | Run twice on identical input | Byte-identical results |

## E. Defects and ambiguities found in the earlier prompt while writing these cases

| # | Problem | Resolution used here | Action needed |
|---|---|---|---|
| 1 | Score for `RetainedRev <= 0` was inconsistent (null in one place, 0 in another) | Margin null; score 0 when costs > 0 | Patch applied to the prompt |
| 2 | Two different "unknown share" metrics had similar names (revenue-based gate vs cost-based estimate flag) | Gate uses quarantined NetBilled / total NetBilled; the cost-based share is a separate display flag | Ratify (D15) |
| 3 | `q_physical_returns` was loosely defined | restocked + not-restocked only under policy `lost` | Ratify with PR-11 and PR-15 (D1) |
| 4 | Unknown cost components (for example return shipping) had no defined score rule | Score null unless bounds are configured, then range only | Ratify (D16) |
| 5 | Largest-remainder tie-break was unspecified | Lowest line index wins | Ratify (D17) |
| 6 | Window definition (inclusive or not, shop timezone or UTC) was unspecified | 30 calendar days inclusive in shop timezone | Ratify (D14) |
| 7 | Refunds dated after `as_of` had no rule | Invisible until a later as_of, then attributed to the original order | Ratify (D18) |
| 8 | Unknown share denominator (billed vs retained) unspecified | NetBilled, because retained can be zero or negative | Ratify (D15) |

## F. Cases still to be written by the agent (need probe results first)

Extraction-layer cases whose expected values come from Shopify fixtures, not from arithmetic: discount allocation (PR-01 to PR-08), refund subtotal basis (PR-09), order edits (PR-17), cancel vs refund vs removed (PR-18), restock types (PR-11), exchanges (PR-16), fees on refunds (PR-31), bundles (PR-34), currencies and tax-inclusive stores (PR-28, PR-29). Each must become a golden case in the same format as Section A once the probe result is known.
