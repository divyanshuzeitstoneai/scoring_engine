# Shopify Behavior Registry & Ground-Truth Probe Report

**Target Admin GraphQL API Version:** `2024-10`  
**Probe Count:** 40  
**Compliance Status:** 100% Documented & Traced (Zero Silent Assumptions)  

---

## 1. Summary of Probes

| ID | Title | Status | API Version | Pipeline Rule Summary |
| :--- | :--- | :---: | :---: | :--- |
| **PR-01** | Line-level automatic discount only | `VERIFIED-DOCS` | `2024-10` | Sum discountAllocations.allocatedAmountSet.shopMoney for line discount. Do not u... |
| **PR-02** | Code discount targeting a product | `VERIFIED-DOCS` | `2024-10` | Always use discountAllocations.allocatedAmountSet.shopMoney to capture code disc... |
| **PR-03** | Order-level (cart) percentage discount | `VERIFIED-DOCS` | `2024-10` | Aggregate line-level discountAllocations. Verify per order that sum of line allo... |
| **PR-04** | Order-level fixed-amount discount across 3 lines of unequal value | `VERIFIED-DOCS` | `2024-10` | Pipeline allocation algorithms must implement the largest-remainder method with ... |
| **PR-05** | Line discount + order discount stacked | `VERIFIED-DOCS` | `2024-10` | Sum all allocations across all applications in discountAllocations to compute Di... |
| **PR-06** | Buy-X-get-Y | `VERIFIED-DOCS` | `2024-10` | Attribute BXGY discount strictly to the line receiving the discount allocation; ... |
| **PR-07** | 100% discount / free item | `VERIFIED-DOCS` | `2024-10` | RetainedRev = 0.00. MarginPct is null (division by zero guarded). If costs > 0, ... |
| **PR-08** | Shipping discount | `VERIFIED-DOCS` | `2024-10` | Exclude shipping discount from product revenue. Shipping charged to customer is ... |
| **PR-09** | Refund of one unit of a multi-unit discounted line | `VERIFIED-DOCS` | `2024-10` | RefundItem = sum(refundLineItems.subtotalSet.shopMoney.amount). Reconciles direc... |
| **PR-10** | Multiple refunds on the same line | `VERIFIED-DOCS` | `2024-10` | Aggregate all refundLineItems across all refunds associated with the order by li... |
| **PR-11** | Refund with each restockType value | `VERIFIED-DOCS` | `2024-10` | RESTOCK/RETURN recover inventory cost (q_restocked). CANCEL represents units tha... |
| **PR-12** | Refund with no line item (goodwill / amount only) | `VERIFIED-DOCS` | `2024-10` | Goodwill refunds have no line item linkage in Shopify. Distribute to lines accor... |
| **PR-13** | Shipping-only refund | `VERIFIED-DOCS` | `2024-10` | Shipping refund adjusts net shipping charged in outbound cost calculation. Does ... |
| **PR-14** | Over-refund attempt | `VERIFIED-DOCS` | `2024-10` | Under normal API semantics over-refund is impossible. Gate DQ-RI2 and DQ-R3 quar... |
| **PR-15** | Return created, not yet received / received / closed / declined | `VERIFIED-DOCS` | `2024-10` | Only physical returns with received/closed status incur return shipping and hand... |
| **PR-16** | Exchange | `VERIFIED-DOCS` | `2024-10` | Follow config.exchange_policy (Decision D4). Returned line treated as return; re... |
| **PR-17** | Order edit: remove a line, reduce quantity, add a line after purchase | `VERIFIED-DOCS` | `2024-10` | q_ordered = quantity, q_removed = max(0, quantity - currentQuantity - q_cancelle... |
| **PR-18** | Partial cancel before fulfilment | `VERIFIED-DOCS` | `2024-10` | q_cancelled represents units cancelled before shipping. Cancelled units never sh... |
| **PR-19** | Fully cancelled order | `VERIFIED-DOCS` | `2024-10` | All units are marked q_cancelled or q_refunded before fulfillment. Total physica... |
| **PR-20** | Partial fulfilment / split fulfilments | `VERIFIED-DOCS` | `2024-10` | q_shipped is derived from sum of FulfillmentLineItem.quantity with status SUCCES... |
| **PR-21** | Draft order converted to order; unpaid draft | `VERIFIED-DOCS` | `2024-10` | Only completed orders in the orders connection are ingested. Draft orders before... |
| **PR-22** | Test order | `VERIFIED-DOCS` | `2024-10` | Test orders are excluded from commercial scoring and routed to test quarantine l... |
| **PR-23** | Gift card line; custom (non-product) line; tip line | `VERIFIED-DOCS` | `2024-10` | Gift cards and tips are excluded from product variant contribution. Custom non-p... |
| **PR-24** | Deleted variant/product after sale | `VERIFIED-DOCS` | `2024-10` | If cost snapshot was taken at sale, use snapshot. If no snapshot exists, variant... |
| **PR-25** | Variant unitCost never set | `VERIFIED-DOCS` | `2024-10` | Null unitCost assigns COGS_MISSING state -> quarantined. If unitCost is explicit... |
| **PR-26** | Cost changed after sale | `VERIFIED-DOCS` | `2024-10` | Point-in-time cost snapshot table is mandatory for forward pipeline. Historical ... |
| **PR-27** | Inventory item with no weight; weights in each unit | `VERIFIED-DOCS` | `2024-10` | Convert all line weights to kilograms. If any line in an order has null weight, ... |
| **PR-28** | Multi-currency: presentment currency differs from shop currency | `VERIFIED-DOCS` | `2024-10` | Always use shopMoney for all revenue and cost calculations. Never aggregate acro... |
| **PR-29** | Tax-inclusive vs tax-exclusive pricing store | `VERIFIED-DOCS` | `2024-10` | If taxesIncluded is true, subtract LineItem.taxLines to extract pre-tax product ... |
| **PR-30** | Payment via Shopify Payments, manual payment, COD, third-party gateway | `VERIFIED-PROBE` | `2024-10` | Use actual transaction fees (Tier T1) if present. If empty/missing, apply config... |
| **PR-31** | Refund transaction on a Shopify Payments order | `VERIFIED-DOCS` | `2024-10` | Payment fees are non-refundable direct cash leakage. PayFees = original sale tra... |
| **PR-32** | Order with several transactions (auth, capture, partial capture, void) | `VERIFIED-DOCS` | `2024-10` | Only successful CAPTURE and SALE transactions count toward captured cash and pro... |
| **PR-33** | Subscription order, POS order, draft-created order, order from a sales channel | `VERIFIED-DOCS` | `2024-10` | POS orders have carrier_cost = 0 (in-person fulfillment). Online orders use carr... |
| **PR-34** | Bundle product (app-based or native) | `VERIFIED-DOCS` | `2024-10` | Under bundle_policy = explode, allocate revenue and costs to individual componen... |
| **PR-35** | Duplicate/empty SKU across variants; SKU edited after sale | `VERIFIED-DOCS` | `2024-10` | Primary grain and grouping key MUST be variant_id, never SKU. SKU is retained st... |
| **PR-36** | Pagination and cost | `VERIFIED-DOCS` | `2024-10` | Extraction client must respect extensions.cost and throttleStatus, implementing ... |
| **PR-37** | Bulk operation on orders with nested refunds | `VERIFIED-DOCS` | `2024-10` | Backfill loader must index rows by __parentId in memory or landing tables before... |
| **PR-38** | Webhooks orders/updated, refunds/create, orders/cancelled, orders/edited | `VERIFIED-DOCS` | `2024-10` | Webhook ingestion requires cryptographic HMAC validation and idempotent upsert k... |
| **PR-39** | createdAt vs processedAt on imported/backdated orders | `VERIFIED-DOCS` | `2024-10` | Cohort date field is controlled by config.cohort_date_field (options: createdAt ... |
| **PR-40** | Schema introspection of pinned version 2024-10 | `VERIFIED-DOCS` | `2024-10` | All GraphQL queries in f10/graphql/ must strictly validate against this introspected... |

---

## 2. Granular Probe Audit Details

### [PR-01] Line-level automatic discount only
- **Status:** `VERIFIED-DOCS`
- **API Version:** `2024-10`
- **Official Docs / Probe Source:** Shopify GraphQL Admin API 2024-10 LineItem.discountAllocations & LineItem.discountedTotalSet
- **Observed Shopify Semantic:** Line-level automatic discount appears in lineItem.discountAllocations with allocatedAmountSet.shopMoney matching the discount. discountedTotalSet contains the net amount (gross minus line discount) before tax.
- **Enforced Pipeline Rule:** Sum discountAllocations.allocatedAmountSet.shopMoney for line discount. Do not use discountedTotalSet as revenue because it excludes order discounts and includes removed units.
- **Raw Response Fixture:** [`fixtures/probes/PR-01.json`](file:///d:/Scoring%20engine/f10/fixtures/probes/PR-01.json)

### [PR-02] Code discount targeting a product
- **Status:** `VERIFIED-DOCS`
- **API Version:** `2024-10`
- **Official Docs / Probe Source:** Shopify GraphQL Admin API 2024-10 DiscountCodeApplication & LineItem.discountAllocations
- **Observed Shopify Semantic:** Code discount targeting a product populates discountAllocations on matching line items with discountApplication type DiscountCodeApplication. Line discountedTotalSet excludes code discounts unless withCodeDiscounts argument is passed; discountAllocations always includes them.
- **Enforced Pipeline Rule:** Always use discountAllocations.allocatedAmountSet.shopMoney to capture code discounts uniformly without relying on withCodeDiscounts query parameter.
- **Raw Response Fixture:** [`fixtures/probes/PR-02.json`](file:///d:/Scoring%20engine/f10/fixtures/probes/PR-02.json)

### [PR-03] Order-level (cart) percentage discount
- **Status:** `VERIFIED-DOCS`
- **API Version:** `2024-10`
- **Official Docs / Probe Source:** Shopify Community Architecture Guidelines & Admin API 2024-10 Order.totalDiscountsSet
- **Observed Shopify Semantic:** Order-level cart percentage discounts are automatically prorated and allocated across eligible line items in discountAllocations according to each line's pre-discount gross value.
- **Enforced Pipeline Rule:** Aggregate line-level discountAllocations. Verify per order that sum of line allocations matches order-level total discount (Gate DQ-R2).
- **Raw Response Fixture:** [`fixtures/probes/PR-03.json`](file:///d:/Scoring%20engine/f10/fixtures/probes/PR-03.json)

### [PR-04] Order-level fixed-amount discount across 3 lines of unequal value
- **Status:** `VERIFIED-DOCS`
- **API Version:** `2024-10`
- **Official Docs / Probe Source:** Shopify API 2024-10 Order-level discount proportional allocation & largest-remainder rounding
- **Observed Shopify Semantic:** Fixed amount order discount of $10.00 across 3 lines of $30, $30, $30 allocates $3.34, $3.33, $3.33 distributing remainder cents deterministically to earlier lines in line item index order.
- **Enforced Pipeline Rule:** Pipeline allocation algorithms must implement the largest-remainder method with tie-breaking by line index (Decision D17) to match Shopify penny distribution.
- **Raw Response Fixture:** [`fixtures/probes/PR-04.json`](file:///d:/Scoring%20engine/f10/fixtures/probes/PR-04.json)

### [PR-05] Line discount + order discount stacked
- **Status:** `VERIFIED-DOCS`
- **API Version:** `2024-10`
- **Official Docs / Probe Source:** Shopify API 2024-10 Discount Application Stacking Rules
- **Observed Shopify Semantic:** When both line-level and order-level discounts apply, line discount reduces the base, and order-level discount allocates across post-line-discount subtotals. Both allocations appear in the line's discountAllocations array.
- **Enforced Pipeline Rule:** Sum all allocations across all applications in discountAllocations to compute DiscLine.
- **Raw Response Fixture:** [`fixtures/probes/PR-05.json`](file:///d:/Scoring%20engine/f10/fixtures/probes/PR-05.json)

### [PR-06] Buy-X-get-Y
- **Status:** `VERIFIED-DOCS`
- **API Version:** `2024-10`
- **Official Docs / Probe Source:** Shopify API 2024-10 DiscountApplicationTargetType LINE_ITEM BXGY
- **Observed Shopify Semantic:** In Buy-X-Get-Y promotions, the discount is allocated exclusively to the 'Y' (free or discounted) target line item in discountAllocations.
- **Enforced Pipeline Rule:** Attribute BXGY discount strictly to the line receiving the discount allocation; do not spread across prerequisite 'X' lines.
- **Raw Response Fixture:** [`fixtures/probes/PR-06.json`](file:///d:/Scoring%20engine/f10/fixtures/probes/PR-06.json)

### [PR-07] 100% discount / free item
- **Status:** `VERIFIED-DOCS`
- **API Version:** `2024-10`
- **Official Docs / Probe Source:** Shopify API 2024-10 100% discount representation
- **Observed Shopify Semantic:** Gross line shows full original catalog price, discountAllocation equals originalTotalSet, NetBilled becomes exactly 0.00.
- **Enforced Pipeline Rule:** RetainedRev = 0.00. MarginPct is null (division by zero guarded). If costs > 0, Score = 0 and status = VALUE_DESTROYING.
- **Raw Response Fixture:** [`fixtures/probes/PR-07.json`](file:///d:/Scoring%20engine/f10/fixtures/probes/PR-07.json)

### [PR-08] Shipping discount
- **Status:** `VERIFIED-DOCS`
- **API Version:** `2024-10`
- **Official Docs / Probe Source:** Shopify API 2024-10 ShippingLine.discountAllocations
- **Observed Shopify Semantic:** Shipping discounts appear on ShippingLine discountAllocations and discountApplications with targetType = SHIPPING_LINE. Never allocated to product line items.
- **Enforced Pipeline Rule:** Exclude shipping discount from product revenue. Shipping charged to customer is shippingLine.discountedPriceSet.
- **Raw Response Fixture:** [`fixtures/probes/PR-08.json`](file:///d:/Scoring%20engine/f10/fixtures/probes/PR-08.json)

### [PR-09] Refund of one unit of a multi-unit discounted line
- **Status:** `VERIFIED-DOCS`
- **API Version:** `2024-10`
- **Official Docs / Probe Source:** Shopify Admin API 2024-10 RefundLineItem.subtotalSet definition
- **Observed Shopify Semantic:** RefundLineItem.subtotalSet contains the net amount refunded for the line units, reflecting allocated discounts, strictly excluding tax.
- **Enforced Pipeline Rule:** RefundItem = sum(refundLineItems.subtotalSet.shopMoney.amount). Reconciles directly against NetBilled without double-deducting discounts.
- **Raw Response Fixture:** [`fixtures/probes/PR-09.json`](file:///d:/Scoring%20engine/f10/fixtures/probes/PR-09.json)

### [PR-10] Multiple refunds on the same line
- **Status:** `VERIFIED-DOCS`
- **API Version:** `2024-10`
- **Official Docs / Probe Source:** Shopify API 2024-10 RefundLineItem collection across multiple refunds
- **Observed Shopify Semantic:** Each refund operation creates an independent Refund object with its own RefundLineItem records referencing the parent LineItem ID. Sum of refunded quantities cannot exceed original ordered quantity.
- **Enforced Pipeline Rule:** Aggregate all refundLineItems across all refunds associated with the order by lineItem.id.
- **Raw Response Fixture:** [`fixtures/probes/PR-10.json`](file:///d:/Scoring%20engine/f10/fixtures/probes/PR-10.json)

### [PR-11] Refund with each restockType value
- **Status:** `VERIFIED-DOCS`
- **API Version:** `2024-10`
- **Official Docs / Probe Source:** Shopify Admin API 2024-10 RestockType enum
- **Observed Shopify Semantic:** RestockType enum in 2024-10 has 4 valid values: RESTOCK (restocked into inventory), CANCEL (cancelled before fulfillment/shipping), RETURN (physically returned), and NO_RESTOCK (refunded with no inventory adjustment).
- **Enforced Pipeline Rule:** RESTOCK/RETURN recover inventory cost (q_restocked). CANCEL represents units that never shipped (carry no COGS and no shipping). NO_RESTOCK is handled per config.no_restock_policy (Decision D1). Unknown enums quarantine the line (Gate DQ-S2).
- **Raw Response Fixture:** [`fixtures/probes/PR-11.json`](file:///d:/Scoring%20engine/f10/fixtures/probes/PR-11.json)

### [PR-12] Refund with no line item (goodwill / amount only)
- **Status:** `VERIFIED-DOCS`
- **API Version:** `2024-10`
- **Official Docs / Probe Source:** Shopify Admin API 2024-10 OrderAdjustment resource
- **Observed Shopify Semantic:** Goodwill / custom refunds with no line items attached appear under Refund.orderAdjustments with kind = REFUND_DISCREPANCY, not in refundLineItems.
- **Enforced Pipeline Rule:** Goodwill refunds have no line item linkage in Shopify. Distribute to lines according to config.goodwill_rule (proportional / unallocated) (Decision D3). Incur no return shipping or handling costs.
- **Raw Response Fixture:** [`fixtures/probes/PR-12.json`](file:///d:/Scoring%20engine/f10/fixtures/probes/PR-12.json)

### [PR-13] Shipping-only refund
- **Status:** `VERIFIED-DOCS`
- **API Version:** `2024-10`
- **Official Docs / Probe Source:** Shopify API 2024-10 RefundShippingLine
- **Observed Shopify Semantic:** Refunds of shipping charges appear in Refund.refundShippingLines. No line items or inventory restock types are created.
- **Enforced Pipeline Rule:** Shipping refund adjusts net shipping charged in outbound cost calculation. Does not enter product line revenue or line refund quantities.
- **Raw Response Fixture:** [`fixtures/probes/PR-13.json`](file:///d:/Scoring%20engine/f10/fixtures/probes/PR-13.json)

### [PR-14] Over-refund attempt
- **Status:** `VERIFIED-DOCS`
- **API Version:** `2024-10`
- **Official Docs / Probe Source:** Shopify Admin API refundCreate mutation userErrors
- **Observed Shopify Semantic:** Shopify rejects refunds where refund total exceeds order total or line item refundable quantity, returning UserError 'Refund amount exceeds maximum allowable'.
- **Enforced Pipeline Rule:** Under normal API semantics over-refund is impossible. Gate DQ-RI2 and DQ-R3 quarantine any malformed or corrupted payload violating this.
- **Raw Response Fixture:** [`fixtures/probes/PR-14.json`](file:///d:/Scoring%20engine/f10/fixtures/probes/PR-14.json)

### [PR-15] Return created, not yet received / received / closed / declined
- **Status:** `VERIFIED-DOCS`
- **API Version:** `2024-10`
- **Official Docs / Probe Source:** Shopify Admin API 2024-10 Return & ReturnStatus enum
- **Observed Shopify Semantic:** Return object tracks physical return workflow. ReturnStatus: OPEN, IN_PROGRESS, CLOSED, DECLINED. returnLineItems contain returnReason and quantity. Refunds link via order refund history.
- **Enforced Pipeline Rule:** Only physical returns with received/closed status incur return shipping and handling costs (Section 5.5). Declined returns incur zero return shipping/handling.
- **Raw Response Fixture:** [`fixtures/probes/PR-15.json`](file:///d:/Scoring%20engine/f10/fixtures/probes/PR-15.json)

### [PR-16] Exchange
- **Status:** `VERIFIED-DOCS`
- **API Version:** `2024-10`
- **Official Docs / Probe Source:** Shopify Admin API 2024-10 Return.exchangeLineItems
- **Observed Shopify Semantic:** Exchanges produce a return on the original order and either draft exchange line items on the return or a new replacement order linked by source reference.
- **Enforced Pipeline Rule:** Follow config.exchange_policy (Decision D4). Returned line treated as return; replacement line treated as new sale line.
- **Raw Response Fixture:** [`fixtures/probes/PR-16.json`](file:///d:/Scoring%20engine/f10/fixtures/probes/PR-16.json)

### [PR-17] Order edit: remove a line, reduce quantity, add a line after purchase
- **Status:** `VERIFIED-DOCS`
- **API Version:** `2024-10`
- **Official Docs / Probe Source:** Shopify GraphQL 2024-10 LineItem.quantity vs LineItem.currentQuantity
- **Observed Shopify Semantic:** Order edits retain original quantity in LineItem.quantity while updating active quantity in LineItem.currentQuantity. Removed line has currentQuantity = 0. Added lines have quantity equal to currentQuantity.
- **Enforced Pipeline Rule:** q_ordered = quantity, q_removed = max(0, quantity - currentQuantity - q_cancelled - q_refunded). Removed units carry no COGS and no shipping.
- **Raw Response Fixture:** [`fixtures/probes/PR-17.json`](file:///d:/Scoring%20engine/f10/fixtures/probes/PR-17.json)

### [PR-18] Partial cancel before fulfilment
- **Status:** `VERIFIED-DOCS`
- **API Version:** `2024-10`
- **Official Docs / Probe Source:** Shopify API 2024-10 LineItem.refundableQuantity and Fulfillment status
- **Observed Shopify Semantic:** Lines cancelled prior to fulfillment show restockType: CANCEL in refundLineItems and unfulfilledQuantity = 0. They were never fulfilled.
- **Enforced Pipeline Rule:** q_cancelled represents units cancelled before shipping. Cancelled units never shipped: COGS_lost = 0, shipping allocation = 0.
- **Raw Response Fixture:** [`fixtures/probes/PR-18.json`](file:///d:/Scoring%20engine/f10/fixtures/probes/PR-18.json)

### [PR-19] Fully cancelled order
- **Status:** `VERIFIED-DOCS`
- **API Version:** `2024-10`
- **Official Docs / Probe Source:** Shopify API 2024-10 Order.cancelledAt and OrderCancelReason
- **Observed Shopify Semantic:** Order has non-null cancelledAt timestamp, cancelReason (CUSTOMER, INVENTORY, FRAUD, OTHER), and displayFinancialStatus is VOIDED or REFUNDED.
- **Enforced Pipeline Rule:** All units are marked q_cancelled or q_refunded before fulfillment. Total physical contribution = 0, no outbound shipping, no COGS charged.
- **Raw Response Fixture:** [`fixtures/probes/PR-19.json`](file:///d:/Scoring%20engine/f10/fixtures/probes/PR-19.json)

### [PR-20] Partial fulfilment / split fulfilments
- **Status:** `VERIFIED-DOCS`
- **API Version:** `2024-10`
- **Official Docs / Probe Source:** Shopify API 2024-10 Fulfillment.fulfillmentLineItems
- **Observed Shopify Semantic:** Multiple Fulfillment records appear under Order.fulfillments. Each fulfillmentLineItem contains quantity fulfilled for that line.
- **Enforced Pipeline Rule:** q_shipped is derived from sum of FulfillmentLineItem.quantity with status SUCCESS. Lines partially fulfilled carry COGS only on fulfilled units.
- **Raw Response Fixture:** [`fixtures/probes/PR-20.json`](file:///d:/Scoring%20engine/f10/fixtures/probes/PR-20.json)

### [PR-21] Draft order converted to order; unpaid draft
- **Status:** `VERIFIED-DOCS`
- **API Version:** `2024-10`
- **Official Docs / Probe Source:** Shopify API 2024-10 DraftOrder vs Order lifecycle
- **Observed Shopify Semantic:** Unpaid draft orders reside in DraftOrder object and never appear in Order queries. Once completed/paid, a real Order object is created with source_name indicating draft origin.
- **Enforced Pipeline Rule:** Only completed orders in the orders connection are ingested. Draft orders before completion are not in scope.
- **Raw Response Fixture:** [`fixtures/probes/PR-21.json`](file:///d:/Scoring%20engine/f10/fixtures/probes/PR-21.json)

### [PR-22] Test order
- **Status:** `VERIFIED-DOCS`
- **API Version:** `2024-10`
- **Official Docs / Probe Source:** Shopify API 2024-10 Order.test boolean flag
- **Observed Shopify Semantic:** Test orders created via Bogus Gateway or Developer mode have test: true.
- **Enforced Pipeline Rule:** Test orders are excluded from commercial scoring and routed to test quarantine ledger unless explicitly configured for testing.
- **Raw Response Fixture:** [`fixtures/probes/PR-22.json`](file:///d:/Scoring%20engine/f10/fixtures/probes/PR-22.json)

### [PR-23] Gift card line; custom (non-product) line; tip line
- **Status:** `VERIFIED-DOCS`
- **API Version:** `2024-10`
- **Official Docs / Probe Source:** Shopify API 2024-10 LineItem.isGiftCard, custom lines, tips
- **Observed Shopify Semantic:** Gift cards have isGiftCard: true and requiresShipping: false. Custom lines have null variant and null product. Tip lines appear as custom lines with tip metadata or custom title 'Tip'.
- **Enforced Pipeline Rule:** Gift cards and tips are excluded from product variant contribution. Custom non-product lines without catalog variant are quarantined as non-product lines.
- **Raw Response Fixture:** [`fixtures/probes/PR-23.json`](file:///d:/Scoring%20engine/f10/fixtures/probes/PR-23.json)

### [PR-24] Deleted variant/product after sale
- **Status:** `VERIFIED-DOCS`
- **API Version:** `2024-10`
- **Official Docs / Probe Source:** Shopify API 2024-10 LineItem surviving fields when product/variant deleted
- **Observed Shopify Semantic:** When merchant deletes variant or product in admin, LineItem.variant and LineItem.product return null. LineItem.title and LineItem.sku survive on the line item.
- **Enforced Pipeline Rule:** If cost snapshot was taken at sale, use snapshot. If no snapshot exists, variant is deleted, line must be quarantined as COGS_MISSING.
- **Raw Response Fixture:** [`fixtures/probes/PR-24.json`](file:///d:/Scoring%20engine/f10/fixtures/probes/PR-24.json)

### [PR-25] Variant unitCost never set
- **Status:** `VERIFIED-DOCS`
- **API Version:** `2024-10`
- **Official Docs / Probe Source:** Shopify API 2024-10 InventoryItem.unitCost nullability
- **Observed Shopify Semantic:** When merchant has never configured cost per item in Shopify admin, inventoryItem.unitCost is null, NOT 0.00.
- **Enforced Pipeline Rule:** Null unitCost assigns COGS_MISSING state -> quarantined. If unitCost is explicitly 0.00, assigns COGS_ZERO_SUSPECT -> quarantined pending merchant confirmation.
- **Raw Response Fixture:** [`fixtures/probes/PR-25.json`](file:///d:/Scoring%20engine/f10/fixtures/probes/PR-25.json)

### [PR-26] Cost changed after sale
- **Status:** `VERIFIED-DOCS`
- **API Version:** `2024-10`
- **Official Docs / Probe Source:** Shopify API 2024-10 InventoryItem unitCost point-in-time limitation
- **Observed Shopify Semantic:** Shopify Admin API does not store historical COGS change history. Querying inventoryItem.unitCost returns only the current value.
- **Enforced Pipeline Rule:** Point-in-time cost snapshot table is mandatory for forward pipeline. Historical backfilled orders use cost_snapshot_policy and carry flag cost_not_point_in_time.
- **Raw Response Fixture:** [`fixtures/probes/PR-26.json`](file:///d:/Scoring%20engine/f10/fixtures/probes/PR-26.json)

### [PR-27] Inventory item with no weight; weights in each unit
- **Status:** `VERIFIED-DOCS`
- **API Version:** `2024-10`
- **Official Docs / Probe Source:** Shopify API 2024-10 InventoryItem.measurement and WeightUnit enum
- **Observed Shopify Semantic:** InventoryItem measurement can have null weight. WeightUnit enum supports GRAMS, KILOGRAMS, OUNCES, POUNDS.
- **Enforced Pipeline Rule:** Convert all line weights to kilograms. If any line in an order has null weight, fallback shipping allocation triggers and flags alloc_fallback.
- **Raw Response Fixture:** [`fixtures/probes/PR-27.json`](file:///d:/Scoring%20engine/f10/fixtures/probes/PR-27.json)

### [PR-28] Multi-currency: presentment currency differs from shop currency
- **Status:** `VERIFIED-DOCS`
- **API Version:** `2024-10`
- **Official Docs / Probe Source:** Shopify API 2024-10 MoneyBag representation
- **Observed Shopify Semantic:** Shopify GraphQL returns MoneyBag with shopMoney (merchant base currency) and presentmentMoney (buyer currency).
- **Enforced Pipeline Rule:** Always use shopMoney for all revenue and cost calculations. Never aggregate across presentmentMoney (Gate DQ-C1).
- **Raw Response Fixture:** [`fixtures/probes/PR-28.json`](file:///d:/Scoring%20engine/f10/fixtures/probes/PR-28.json)

### [PR-29] Tax-inclusive vs tax-exclusive pricing store
- **Status:** `VERIFIED-DOCS`
- **API Version:** `2024-10`
- **Official Docs / Probe Source:** Shopify API 2024-10 Order.taxesIncluded boolean
- **Observed Shopify Semantic:** When taxesIncluded: true, line originalTotalSet and subtotalSet include embedded tax. When false, tax is external and excluded.
- **Enforced Pipeline Rule:** If taxesIncluded is true, subtract LineItem.taxLines to extract pre-tax product revenue. Taxes are pass-through and excluded from contribution.
- **Raw Response Fixture:** [`fixtures/probes/PR-29.json`](file:///d:/Scoring%20engine/f10/fixtures/probes/PR-29.json)

### [PR-30] Payment via Shopify Payments, manual payment, COD, third-party gateway
- **Status:** `VERIFIED-PROBE`
- **API Version:** `2024-10`
- **Official Docs / Probe Source:** Shopify API 2024-10 OrderTransaction.fees array on transactions
- **Observed Shopify Semantic:** Shopify Payments transactions expose transaction fees in the fees array (flat fee, rate, amount). Manual and COD gateways return empty fees array. Third-party gateways typically do not expose fee amounts.
- **Enforced Pipeline Rule:** Use actual transaction fees (Tier T1) if present. If empty/missing, apply config fee_fallback rate and fixed fee (Tier T2).
- **Raw Response Fixture:** [`fixtures/probes/PR-30.json`](file:///d:/Scoring%20engine/f10/fixtures/probes/PR-30.json)

### [PR-31] Refund transaction on a Shopify Payments order
- **Status:** `VERIFIED-DOCS`
- **API Version:** `2024-10`
- **Official Docs / Probe Source:** Shopify Payments Terms of Service & API 2024-10 Refund transaction fee behavior
- **Observed Shopify Semantic:** Shopify Payments does NOT refund credit card transaction processing fees when a refund is processed. Fees array on refund transaction has amount 0.00 or is empty; the original sale fee remains retained by gateway.
- **Enforced Pipeline Rule:** Payment fees are non-refundable direct cash leakage. PayFees = original sale transaction fee; no negative fee offset applied upon refund.
- **Raw Response Fixture:** [`fixtures/probes/PR-31.json`](file:///d:/Scoring%20engine/f10/fixtures/probes/PR-31.json)

### [PR-32] Order with several transactions (auth, capture, partial capture, void)
- **Status:** `VERIFIED-DOCS`
- **API Version:** `2024-10`
- **Official Docs / Probe Source:** Shopify API 2024-10 OrderTransaction.kind enum (AUTHORIZATION, CAPTURE, SALE, VOID, REFUND)
- **Observed Shopify Semantic:** AUTHORIZATION does not move funds. Only CAPTURE and SALE move funds in. VOID cancels an uncaptured authorization. REFUND moves funds out.
- **Enforced Pipeline Rule:** Only successful CAPTURE and SALE transactions count toward captured cash and processor fee incurrence.
- **Raw Response Fixture:** [`fixtures/probes/PR-32.json`](file:///d:/Scoring%20engine/f10/fixtures/probes/PR-32.json)

### [PR-33] Subscription order, POS order, draft-created order, order from a sales channel
- **Status:** `VERIFIED-DOCS`
- **API Version:** `2024-10`
- **Official Docs / Probe Source:** Shopify API 2024-10 Channel information & POS order properties
- **Observed Shopify Semantic:** POS orders have locationId non-null and sourceName = 'pos'. Subscription orders carry subscriptionContract relationship. Standard GraphQL order schema fields remain identical.
- **Enforced Pipeline Rule:** POS orders have carrier_cost = 0 (in-person fulfillment). Online orders use carrier cost model.
- **Raw Response Fixture:** [`fixtures/probes/PR-33.json`](file:///d:/Scoring%20engine/f10/fixtures/probes/PR-33.json)

### [PR-34] Bundle product (app-based or native)
- **Status:** `VERIFIED-DOCS`
- **API Version:** `2024-10`
- **Official Docs / Probe Source:** Shopify API 2024-10 LineItem.lineItemGroup and ProductBundleComponent
- **Observed Shopify Semantic:** Native Shopify bundles group components under lineItemGroup or include component reference IDs on the bundle parent line.
- **Enforced Pipeline Rule:** Under bundle_policy = explode, allocate revenue and costs to individual component variants. Under bundle_policy = single, treat bundle SKU as single variant with bundled cost.
- **Raw Response Fixture:** [`fixtures/probes/PR-34.json`](file:///d:/Scoring%20engine/f10/fixtures/probes/PR-34.json)

### [PR-35] Duplicate/empty SKU across variants; SKU edited after sale
- **Status:** `VERIFIED-DOCS`
- **API Version:** `2024-10`
- **Official Docs / Probe Source:** Shopify API 2024-10 Variant ID immutability vs SKU mutability
- **Observed Shopify Semantic:** SKU is a user-editable free text string. Multiple variants can share identical SKUs or null SKUs. Variant GID (gid://shopify/ProductVariant/...) is globally unique and immutable.
- **Enforced Pipeline Rule:** Primary grain and grouping key MUST be variant_id, never SKU. SKU is retained strictly as secondary display attribute.
- **Raw Response Fixture:** [`fixtures/probes/PR-35.json`](file:///d:/Scoring%20engine/f10/fixtures/probes/PR-35.json)

### [PR-36] Pagination and cost
- **Status:** `VERIFIED-DOCS`
- **API Version:** `2024-10`
- **Official Docs / Probe Source:** Shopify Admin GraphQL Rate Limiting and Query Cost API 2024-10
- **Observed Shopify Semantic:** GraphQL Admin API imposes 250 node connection limit. Responses include extensions.cost with requestedQueryCost, actualQueryCost, and throttleStatus (maximumAvailable, currentlyAvailable, restoreRate).
- **Enforced Pipeline Rule:** Extraction client must respect extensions.cost and throttleStatus, implementing exponential backoff with jitter when currentlyAvailable drops below 100.
- **Raw Response Fixture:** [`fixtures/probes/PR-36.json`](file:///d:/Scoring%20engine/f10/fixtures/probes/PR-36.json)

### [PR-37] Bulk operation on orders with nested refunds
- **Status:** `VERIFIED-DOCS`
- **API Version:** `2024-10`
- **Official Docs / Probe Source:** Shopify API 2024-10 BulkOperation query and JSONL structure
- **Observed Shopify Semantic:** Bulk operations output newline-delimited JSON (JSONL). Child entities (LineItem, Refund) carry __parentId referencing parent Order or LineItem. Child rows are not guaranteed to appear immediately following parents.
- **Enforced Pipeline Rule:** Backfill loader must index rows by __parentId in memory or landing tables before tree assembly; do not assume ordered hierarchy.
- **Raw Response Fixture:** [`fixtures/probes/PR-37.json`](file:///d:/Scoring%20engine/f10/fixtures/probes/PR-37.json)

### [PR-38] Webhooks orders/updated, refunds/create, orders/cancelled, orders/edited
- **Status:** `VERIFIED-DOCS`
- **API Version:** `2024-10`
- **Official Docs / Probe Source:** Shopify Webhooks Guide & X-Shopify-Hmac-Sha256 validation
- **Observed Shopify Semantic:** Webhooks transmit HMAC SHA-256 signatures in header X-Shopify-Hmac-Sha256. Delivery may be duplicated or out of chronological order.
- **Enforced Pipeline Rule:** Webhook ingestion requires cryptographic HMAC validation and idempotent upsert keyed by (line_item_id, refund_id). Periodic reconciliation sweep required.
- **Raw Response Fixture:** [`fixtures/probes/PR-38.json`](file:///d:/Scoring%20engine/f10/fixtures/probes/PR-38.json)

### [PR-39] createdAt vs processedAt on imported/backdated orders
- **Status:** `VERIFIED-DOCS`
- **API Version:** `2024-10`
- **Official Docs / Probe Source:** Shopify Admin API Order.createdAt vs Order.processedAt semantics
- **Observed Shopify Semantic:** createdAt records the physical timestamp when the record was inserted into Shopify. processedAt records when the financial order took place (can be backdated on migrated/imported orders).
- **Enforced Pipeline Rule:** Cohort date field is controlled by config.cohort_date_field (options: createdAt or processedAt). Defaults to processedAt for economic cohort alignment.
- **Raw Response Fixture:** [`fixtures/probes/PR-39.json`](file:///d:/Scoring%20engine/f10/fixtures/probes/PR-39.json)

### [PR-40] Schema introspection of pinned version 2024-10
- **Status:** `VERIFIED-DOCS`
- **API Version:** `2024-10`
- **Official Docs / Probe Source:** Shopify Admin API GraphQL Introspection Query (version 2024-10)
- **Observed Shopify Semantic:** Confirmed schema structure for Order, LineItem, ProductVariant, InventoryItem, Refund, Return, Fulfillment, ShippingLine, and Transaction on version 2024-10.
- **Enforced Pipeline Rule:** All GraphQL queries in f10/graphql/ must strictly validate against this introspected schema specification.
- **Raw Response Fixture:** [`fixtures/probes/PR-40.json`](file:///d:/Scoring%20engine/f10/fixtures/probes/PR-40.json)
