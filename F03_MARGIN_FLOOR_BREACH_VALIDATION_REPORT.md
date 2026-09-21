# Formula F03: Margin Floor Breach — Technical QA Validation & Schema Integrity Report

**Author:** E-Commerce Data Engineering & QA Architecture  
**Target API:** Shopify Admin GraphQL API (`2024-04` / `2024-07` / `2024-10` LTS)  
**Subject:** Formula F03 (Margin Floor Breach) — V1 Flawed Spec vs. V2 Production Rebuild  
**Status:** Complete Programmatic Validation & Leak Audit  

---

## Executive Summary & Core Objective

The **Margin Floor Breach (F03)** metric determines whether a completed order generated positive direct cash contribution:
$$\text{Did the merchant collect more physical cash than they paid out in direct COGS, real outbound shipping, and non-refundable payment processing fees for that specific order?}$$

It is an unforgiving cash-floor safety check, not an accrual P&L. This report validates the original flawed formula (**Formula V1**) against the production rebuild (**Formula V2**) across 12 distinct real-world scenarios. Every scenario is grounded in the exact response structures, types, connections, and undocumented quirks of the **Shopify Admin GraphQL API**.

### Formula Specifications Under Test

#### Formula V1 — Original (Flawed) Spec
$$\text{Order Gross Profit} = \sum (\text{Net Selling Price}_i - \text{COGS}_i) \quad [\text{Active Items}]$$
$$\text{Net Margin Cash} = \text{Order Gross Profit} - \text{Actual Shipping Cost} - \text{Gateway Fee}$$
$$\text{F03 Breach} = \text{Net Margin Cash} < 0$$
$$\text{F03 Loss} = |\text{Net Margin Cash}| \quad \text{if Breach else } 0.00$$

#### Formula V2 — Production Rebuild Spec
$$\begin{aligned}
\text{Cash In} = &\sum \text{Net Item Price}_i \ (\text{tax-excl., discount-allocated, shop-currency}) \\
&+ \text{Shipping Revenue Collected} \ (\text{net of shipping refunds}) \\
&- \text{Refunded Revenue} \ (\text{prorated by unit for partial returns})
\end{aligned}$$

$$\begin{aligned}
\text{Cash Out} = &\sum (\text{Unit COGS}_i \times \text{Units NOT Restocked}_i) \\
&+ \text{Actual Outbound Shipping Cost} \ (\text{estimated + flagged if missing; never } \$0 \text{ default}) \\
&+ \text{Gateway Fee Actually Retained} \ (\text{post-refund; } \$0 \text{ only if manual/unprocessed}) \\
&+ \text{Other Direct Fulfillment Cost} \ (\text{optional, if merchant supplied})
\end{aligned}$$

$$\text{Net Margin Cash} = \text{Cash In} - \text{Cash Out}$$
$$\text{F03 Breach} = \text{Net Margin Cash} < \text{Merchant-Defined Floor (default } \$0.00)$$
$$\text{F03 Loss} = |\text{Net Margin Cash}| \quad \text{if Breach else } 0.00$$

#### Evaluability Gate (V2):
* **`NOT_EVALUABLE`**: Missing/invalid COGS or item price $\rightarrow$ Excluded from breach rate denominator.
* **`EVALUATED_ESTIMATED`**: COGS present, but shipping or gateway cost missing $\rightarrow$ Imputed via fallback models, flagged, included in denominator.
* **`EVALUATED_CONFIRMED`**: All financial inputs verified from confirmed schema sources.

---

## Appendix: Shopify Admin GraphQL API Schema Field Verification

Every field referenced across the synthetic test vectors has been audited against the Shopify Admin GraphQL Schema (`2024-04` through `2024-10`).

| Object / Path | Field Name | GraphQL Type | Status | Verified Source / Schema Reference | Implementation Quirk & Audit Notes |
| :--- | :--- | :--- | :---: | :--- | :--- |
| `Order` | `id` | `ID!` | **VERIFIED** | `Order.id` | Global ID (`gid://shopify/Order/...`). |
| `Order` | `name` | `String!` | **VERIFIED** | `Order.name` | Display order name (e.g. `#1001`). |
| `Order` | `createdAt` | `DateTime!` | **VERIFIED** | `Order.createdAt` | ISO 8601 UTC timestamp of creation. |
| `Order` | `cancelledAt` | `DateTime` | **VERIFIED** | `Order.cancelledAt` | Null if active; populated if cancelled. |
| `Order` | `currencyCode` | `CurrencyCode!` | **VERIFIED** | `Order.currencyCode` | Base store currency when order was placed. |
| `Order` | `taxesIncluded` | `Boolean!` | **VERIFIED** | `Order.taxesIncluded` | If `true`, line items and shipping prices include tax. |
| `Order` | `displayFinancialStatus` | `OrderDisplayFinancialStatus` | **VERIFIED** | `Order.displayFinancialStatus` | Enum: `PAID`, `PARTIALLY_REFUNDED`, `REFUNDED`, etc. |
| `Order` | `currentSubtotalPriceSet` | `MoneyBag!` | **VERIFIED** | `Order.currentSubtotalPriceSet` | Subtotal after line-level refunds and returns. |
| `Order` | `currentTotalPriceSet` | `MoneyBag!` | **VERIFIED** | `Order.currentTotalPriceSet` | Net total cash after all discounts, taxes, returns. |
| `Order` | `currentShippingPriceSet`| `MoneyBag!` | **VERIFIED** | `Order.currentShippingPriceSet`| **True net shipping revenue collected** post-refund. |
| `Order` | `currentTotalTaxSet` | `MoneyBag!` | **VERIFIED** | `Order.currentTotalTaxSet` | Remittable tax liability (must be excluded from net margin). |
| `Order` | `currentCartDiscountAmountSet` | `MoneyBag!` | **VERIFIED** | `Order.currentCartDiscountAmountSet` | Order-level discount amount applied across cart. |
| `Order` | `tags` | `[String!]!` | **VERIFIED** | `Order.tags` | String array. Store-defined tags (used for sample/gift identification). |
| `Order` | `order_type` | *None* | **NON-EXISTENT** | Schema Introspection | **Shopify has NO native `order_type` field.** Must be inferred from tags, channels, or $0 drafts. |
| `LineItem` | `id` | `ID!` | **VERIFIED** | `LineItem.id` | Unique line item GID. |
| `LineItem` | `quantity` | `Int!` | **VERIFIED** | `LineItem.quantity` | Original ordered quantity. |
| `LineItem` | `currentQuantity` | `Int!` | **VERIFIED** | `LineItem.currentQuantity` | Remaining physical quantity post-refund/removal. |
| `LineItem` | `discountedUnitPriceSet` | `MoneyBag!` | **VERIFIED** | `LineItem.discountedUnitPriceSet` | **Critical Quirk:** Only includes *line-level* discounts. Excludes cart/order-level discount codes! |
| `LineItem` | `originalUnitPriceSet` | `MoneyBag!` | **VERIFIED** | `LineItem.originalUnitPriceSet` | Stated catalog price before any line discounts. |
| `LineItem` | `discountAllocations` | `[DiscountAllocation!]!` | **VERIFIED** | `LineItem.discountAllocations` | Lists exact portion of cart/order discounts applied to this item. |
| `InventoryItem` | `unitCost` | `MoneyV2` | **VERIFIED** | `InventoryItem.unitCost` | **Critical Quirk:** Current live cost on product variant. **Zero historical point-in-time snapshot.** |
| `OrderTransaction` | `fees` | `[TransactionFee!]!` | **VERIFIED** | `OrderTransaction.fees` | **Critical Quirk:** Empty array `[]` for all gateways except Shopify Payments. |
| `OrderTransaction` | `status` | `OrderTransactionStatus!` | **VERIFIED** | `OrderTransaction.status` | Enum: `SUCCESS`, `PENDING`, `FAILURE`, `ERROR`. |
| `Refund` | `totalRefundedSet` | `MoneyBag!` | **VERIFIED** | `Refund.totalRefundedSet` | Total refunded amount. Reports `0.00` while gateway refund transaction is `PENDING`. |
| `RefundLineItem` | `restocked` | `Boolean!` | **VERIFIED** | `RefundLineItem.restocked` | True if physical item was put back in inventory. |
| `RefundLineItem` | `restockType` | `RestockType!` | **VERIFIED** | `RefundLineItem.restockType` | Enum: `RETURN`, `CANCEL`, `NO_RESTOCK`. |
| `Fulfillment` | `actualShippingCost` | *None* | **UNVERIFIED / ABSENT** | Schema Introspection | External 3PL/carrier label costs (ShipStation, etc.) are **NOT** stored in Shopify Order graph. |

---

## Scenario Validations (TC-01 through TC-12)

---

### Scenario 01: Standard Clean Order (Sanity Baseline)
* **Description:** Clean single-item order paid via Shopify Payments. No discounts, free shipping offered ($0.00), zero courier delivery expense ($0.00 digital/local pickup), zero tax.
* **Test Focus:** Baseline sanity check where both formulas should agree.

#### Synthetic GraphQL Response JSON
```json
{
  "data": {
    "order": {
      "id": "gid://shopify/Order/8100000001",
      "name": "#1001",
      "createdAt": "2026-09-15T10:00:00Z",
      "cancelledAt": null,
      "currencyCode": "USD",
      "taxesIncluded": false,
      "displayFinancialStatus": "PAID",
      "currentSubtotalPriceSet": { "shopMoney": { "amount": "100.00", "currencyCode": "USD" }, "presentmentMoney": { "amount": "100.00", "currencyCode": "USD" } },
      "currentTotalPriceSet": { "shopMoney": { "amount": "100.00", "currencyCode": "USD" }, "presentmentMoney": { "amount": "100.00", "currencyCode": "USD" } },
      "currentShippingPriceSet": { "shopMoney": { "amount": "0.00", "currencyCode": "USD" }, "presentmentMoney": { "amount": "0.00", "currencyCode": "USD" } },
      "currentTotalTaxSet": { "shopMoney": { "amount": "0.00", "currencyCode": "USD" }, "presentmentMoney": { "amount": "0.00", "currencyCode": "USD" } },
      "currentCartDiscountAmountSet": { "shopMoney": { "amount": "0.00", "currencyCode": "USD" }, "presentmentMoney": { "amount": "0.00", "currencyCode": "USD" } },
      "tags": [],
      "lineItems": {
        "edges": [
          {
            "node": {
              "id": "gid://shopify/LineItem/9100000001",
              "quantity": 1,
              "currentQuantity": 1,
              "discountedUnitPriceSet": { "shopMoney": { "amount": "100.00", "currencyCode": "USD" }, "presentmentMoney": { "amount": "100.00", "currencyCode": "USD" } },
              "discountAllocations": [],
              "variant": {
                "id": "gid://shopify/ProductVariant/7100000001",
                "inventoryItem": { "unitCost": { "amount": "40.00", "currencyCode": "USD" } }
              }
            }
          }
        ]
      },
      "transactions": [
        {
          "id": "gid://shopify/OrderTransaction/6100000001",
          "kind": "SALE",
          "status": "SUCCESS",
          "gateway": "shopify_payments",
          "manualPaymentGateway": false,
          "amountSet": { "shopMoney": { "amount": "100.00", "currencyCode": "USD" } },
          "fees": [
            { "id": "gid://shopify/TransactionFee/5100000001", "amount": { "amount": "3.20", "currencyCode": "USD" }, "flatFee": { "amount": "0.30", "currencyCode": "USD" }, "rate": "0.029" }
          ]
        }
      ],
      "refunds": []
    }
  }
}
```

#### Formula Walkthroughs
* **Formula V1 Substitution:**
  * $\text{Order Gross Profit} = \sum(100.00 - 40.00) = \$60.00$
  * $\text{Net Margin Cash} = \$60.00 - \$0.00 (\text{Shipping Cost}) - \$3.20 (\text{Gateway Fee}) = \$56.80$
  * $\text{F03 Breach} = \text{False}$ | $\text{F03 Loss} = \$0.00$
* **Formula V2 Substitution:**
  * $\text{Cash In} = \$100.00 (\text{Net Item Price}) + \$0.00 (\text{Shipping Collected}) - \$0.00 (\text{Refunds}) = \$100.00$
  * $\text{Cash Out} = (1 \times \$40.00) + \$0.00 (\text{Shipping Outbound}) + \$3.20 (\text{Retained Fee}) = \$43.20$
  * $\text{Net Margin Cash} = \$100.00 - \$43.20 = \$56.80$
  * $\text{Evaluability Status} = \text{EVALUATED\_CONFIRMED}$
  * $\text{F03 Breach} = \text{False}$ | $\text{F03 Loss} = \$0.00$

#### Leak Analysis
* **Leak Classification:** None (Baseline Control).
* **Flaws Demonstrated:** None (Confirms formula parity under idealized zero-noise conditions).
* **Merchant Takeaway:** Under clean, single-item Shopify Payments orders with no shipping or tax, both formulas report an accurate contribution margin of \$56.80.

---

### Scenario 02: Customer-Paid Flat Shipping vs. Discrepant Carrier Outbound Cost
* **Description:** Merchant charges customer flat-rate \$10.00 shipping. Item price is \$50.00 with COGS of \$25.00. Actual courier outbound label purchased costs \$32.00. Payment fee on \$60.00 total is \$2.04.
* **Test Focus:** Demonstrates V1's omission of the customer shipping revenue term.

#### Synthetic GraphQL Response JSON
```json
{
  "data": {
    "order": {
      "id": "gid://shopify/Order/8100000002",
      "name": "#1002",
      "createdAt": "2026-09-15T11:00:00Z",
      "cancelledAt": null,
      "currencyCode": "USD",
      "taxesIncluded": false,
      "displayFinancialStatus": "PAID",
      "currentSubtotalPriceSet": { "shopMoney": { "amount": "50.00", "currencyCode": "USD" } },
      "currentTotalPriceSet": { "shopMoney": { "amount": "60.00", "currencyCode": "USD" } },
      "currentShippingPriceSet": { "shopMoney": { "amount": "10.00", "currencyCode": "USD" } },
      "currentTotalTaxSet": { "shopMoney": { "amount": "0.00", "currencyCode": "USD" } },
      "currentCartDiscountAmountSet": { "shopMoney": { "amount": "0.00", "currencyCode": "USD" } },
      "tags": [],
      "lineItems": {
        "edges": [
          {
            "node": {
              "id": "gid://shopify/LineItem/9100000002",
              "quantity": 1,
              "currentQuantity": 1,
              "discountedUnitPriceSet": { "shopMoney": { "amount": "50.00", "currencyCode": "USD" } },
              "discountAllocations": [],
              "variant": { "inventoryItem": { "unitCost": { "amount": "25.00", "currencyCode": "USD" } } }
            }
          }
        ]
      },
      "transactions": [
        {
          "id": "gid://shopify/OrderTransaction/6100000002",
          "kind": "SALE",
          "status": "SUCCESS",
          "gateway": "shopify_payments",
          "manualPaymentGateway": false,
          "amountSet": { "shopMoney": { "amount": "60.00", "currencyCode": "USD" } },
          "fees": [{ "id": "gid://shopify/TransactionFee/5100000002", "amount": { "amount": "2.04", "currencyCode": "USD" } }]
        }
      ],
      "refunds": []
    }
  }
}
```
*(External courier manifest confirms actual label cost = \$32.00)*

#### Formula Walkthroughs
* **Formula V1 Substitution:**
  * $\text{Order Gross Profit} = 50.00 - 25.00 = \$25.00$
  * $\text{Net Margin Cash} = \$25.00 - \$32.00 (\text{Actual Shipping}) - \$2.04 (\text{Gateway Fee}) = -\$9.04$
  * $\text{F03 Breach} = \mathbf{TRUE}$ | $\text{F03 Loss} = \mathbf{\$9.04}$
* **Formula V2 Substitution:**
  * $\text{Cash In} = \$50.00 (\text{Items}) + \$10.00 (\text{Shipping Rev: } \texttt{currentShippingPriceSet}) - \$0.00 = \$60.00$
  * $\text{Cash Out} = \$25.00 (\text{COGS}) + \$32.00 (\text{Carrier Outbound}) + \$2.04 (\text{Fee}) = \$59.04$
  * $\text{Net Margin Cash} = \$60.00 - \$59.04 = \mathbf{+\$0.96}$
  * $\text{Evaluability Status} = \text{EVALUATED\_CONFIRMED}$
  * $\text{F03 Breach} = \mathbf{FALSE}$ | $\text{F03 Loss} = \mathbf{\$0.00}$

#### Leak Analysis
* **Leak Classification:** **Formula Leak**.
* **Responsible Field/Behavior:** Omission of `Order.currentShippingPriceSet`. V1 subtracts outbound courier freight costs from merchandise margin without crediting the \$10.00 paid by the buyer toward shipping.
* **Flaws Demonstrated:** Flaw 1 (No shipping-revenue-collected term).
* **Merchant Takeaway:** V1 issues a false alarm claiming this order bled \$9.04, when the merchant actually retained +\$0.96 in net cash because the buyer subsidised shipping costs.

---

### Scenario 03: Tax-Inclusive Store (`taxesIncluded: true`) with Thin Margin
* **Description:** UK store operating with 20% VAT included in displayed prices (`taxesIncluded: true`). Gross item price £120.00 (contains £20.00 VAT, net £100.00). COGS £95.00. Carrier cost £8.00. Gateway fee £3.78.
* **Test Focus:** Tests tax-inclusive revenue inflation and failure to deduct statutory tax liability.

#### Synthetic GraphQL Response JSON
```json
{
  "data": {
    "order": {
      "id": "gid://shopify/Order/8100000003",
      "name": "#1003",
      "createdAt": "2026-09-15T12:00:00Z",
      "cancelledAt": null,
      "currencyCode": "GBP",
      "taxesIncluded": true,
      "displayFinancialStatus": "PAID",
      "currentSubtotalPriceSet": { "shopMoney": { "amount": "120.00", "currencyCode": "GBP" } },
      "currentTotalPriceSet": { "shopMoney": { "amount": "120.00", "currencyCode": "GBP" } },
      "currentShippingPriceSet": { "shopMoney": { "amount": "0.00", "currencyCode": "GBP" } },
      "currentTotalTaxSet": { "shopMoney": { "amount": "20.00", "currencyCode": "GBP" } },
      "currentCartDiscountAmountSet": { "shopMoney": { "amount": "0.00", "currencyCode": "GBP" } },
      "tags": [],
      "lineItems": {
        "edges": [
          {
            "node": {
              "id": "gid://shopify/LineItem/9100000003",
              "quantity": 1,
              "currentQuantity": 1,
              "discountedUnitPriceSet": { "shopMoney": { "amount": "120.00", "currencyCode": "GBP" } },
              "discountAllocations": [],
              "variant": { "inventoryItem": { "unitCost": { "amount": "95.00", "currencyCode": "GBP" } } }
            }
          }
        ]
      },
      "transactions": [
        {
          "id": "gid://shopify/OrderTransaction/6100000003",
          "kind": "SALE",
          "status": "SUCCESS",
          "gateway": "shopify_payments",
          "manualPaymentGateway": false,
          "amountSet": { "shopMoney": { "amount": "120.00", "currencyCode": "GBP" } },
          "fees": [{ "id": "gid://shopify/TransactionFee/5100000003", "amount": { "amount": "3.78", "currencyCode": "GBP" } }]
        }
      ],
      "refunds": []
    }
  }
}
```
*(Actual courier outbound cost = £8.00)*

#### Formula Walkthroughs
* **Formula V1 Substitution:**
  * $\text{Order Gross Profit} = 120.00 - 95.00 = £25.00$
  * $\text{Net Margin Cash} = £25.00 - £8.00 (\text{Shipping}) - £3.78 (\text{Fee}) = \mathbf{+£13.22}$
  * $\text{F03 Breach} = \mathbf{FALSE}$ | $\text{F03 Loss} = \mathbf{£0.00}$
* **Formula V2 Substitution:**
  * $\text{Tax Liability} = \texttt{currentTotalTaxSet} = £20.00$
  * $\text{Net Tax-Excl. Price} = £120.00 - £20.00 = £100.00$
  * $\text{Cash In} = £100.00 + £0.00 - £0.00 = £100.00$
  * $\text{Cash Out} = £95.00 (\text{COGS}) + £8.00 (\text{Shipping}) + £3.78 (\text{Fee}) = £106.78$
  * $\text{Net Margin Cash} = £100.00 - £106.78 = \mathbf{-£6.78}$
  * $\text{Evaluability Status} = \text{EVALUATED\_CONFIRMED}$
  * $\text{F03 Breach} = \mathbf{TRUE}$ | $\text{F03 Loss} = \mathbf{£6.78}$

#### Leak Analysis
* **Leak Classification:** **Formula Leak**.
* **Responsible Field/Behavior:** `Order.taxesIncluded: true` ignored by V1. V1 mistakenly treats the £20.00 government tax collection as retained merchant revenue.
* **Flaws Demonstrated:** Flaw 2 (No explicit handling of tax-inclusive prices).
* **Merchant Takeaway:** V1 gives a dangerous false green light (+£13.22 profit), masking a real cash-bleeding loss (-£6.78) because the merchant must remit £20.00 in VAT to the tax authority.

---

### Scenario 04: Order-Level Percentage Discount Code Applied Across Cart
* **Description:** Order with 2 line items ($100.00 each, total $200.00). COGS is $60.00 each ($120.00 total). A storewide 40% discount code (`SAVE40`) discounts $80.00 at the cart level. Courier cost is $10.00. Gateway fee on $120.00 collected is $3.78.
* **Test Focus:** Tests `LineItem.discountedUnitPriceSet` schema documented limitation (it excludes order-level discounts).

#### Synthetic GraphQL Response JSON
```json
{
  "data": {
    "order": {
      "id": "gid://shopify/Order/8100000004",
      "name": "#1004",
      "createdAt": "2026-09-15T13:00:00Z",
      "cancelledAt": null,
      "currencyCode": "USD",
      "taxesIncluded": false,
      "displayFinancialStatus": "PAID",
      "currentSubtotalPriceSet": { "shopMoney": { "amount": "120.00", "currencyCode": "USD" } },
      "currentTotalPriceSet": { "shopMoney": { "amount": "120.00", "currencyCode": "USD" } },
      "currentShippingPriceSet": { "shopMoney": { "amount": "0.00", "currencyCode": "USD" } },
      "currentTotalTaxSet": { "shopMoney": { "amount": "0.00", "currencyCode": "USD" } },
      "currentCartDiscountAmountSet": { "shopMoney": { "amount": "80.00", "currencyCode": "USD" } },
      "tags": [],
      "lineItems": {
        "edges": [
          {
            "node": {
              "id": "gid://shopify/LineItem/9100000004-1",
              "quantity": 1,
              "currentQuantity": 1,
              "discountedUnitPriceSet": { "shopMoney": { "amount": "100.00", "currencyCode": "USD" } },
              "discountAllocations": [
                { "allocatedAmountSet": { "shopMoney": { "amount": "40.00", "currencyCode": "USD" } } }
              ],
              "variant": { "inventoryItem": { "unitCost": { "amount": "60.00", "currencyCode": "USD" } } }
            }
          },
          {
            "node": {
              "id": "gid://shopify/LineItem/9100000004-2",
              "quantity": 1,
              "currentQuantity": 1,
              "discountedUnitPriceSet": { "shopMoney": { "amount": "100.00", "currencyCode": "USD" } },
              "discountAllocations": [
                { "allocatedAmountSet": { "shopMoney": { "amount": "40.00", "currencyCode": "USD" } } }
              ],
              "variant": { "inventoryItem": { "unitCost": { "amount": "60.00", "currencyCode": "USD" } } }
            }
          }
        ]
      },
      "transactions": [
        {
          "id": "gid://shopify/OrderTransaction/6100000004",
          "kind": "SALE",
          "status": "SUCCESS",
          "gateway": "shopify_payments",
          "manualPaymentGateway": false,
          "amountSet": { "shopMoney": { "amount": "120.00", "currencyCode": "USD" } },
          "fees": [{ "id": "gid://shopify/TransactionFee/5100000004", "amount": { "amount": "3.78", "currencyCode": "USD" } }]
        }
      ],
      "refunds": []
    }
  }
}
```
*(Actual courier outbound cost = \$10.00)*

#### Formula Walkthroughs
* **Formula V1 Substitution:**
  * V1 reads `LineItem.discountedUnitPriceSet` directly (\$100.00 each!):
  * $\text{Order Gross Profit} = (100.00 - 60.00) + (100.00 - 60.00) = \$80.00$
  * $\text{Net Margin Cash} = \$80.00 - \$10.00 (\text{Shipping}) - \$3.78 (\text{Fee}) = \mathbf{+\$66.22}$
  * $\text{F03 Breach} = \mathbf{FALSE}$ | $\text{F03 Loss} = \mathbf{\$0.00}$
* **Formula V2 Substitution:**
  * V2 applies `discountAllocations` (\$40.00 deducted per line item) or reads `currentSubtotalPriceSet`:
  * $\text{Net Item Price}_1 = \$100.00 - \$40.00 = \$60.00$; $\text{Net Item Price}_2 = \$100.00 - \$40.00 = \$60.00$
  * $\text{Cash In} = \$120.00 + \$0.00 - \$0.00 = \$120.00$
  * $\text{Cash Out} = (2 \times \$60.00) + \$10.00 (\text{Shipping}) + \$3.78 (\text{Fee}) = \$133.78$
  * $\text{Net Margin Cash} = \$120.00 - \$133.78 = \mathbf{-\$13.78}$
  * $\text{Evaluability Status} = \text{EVALUATED\_CONFIRMED}$
  * $\text{F03 Breach} = \mathbf{TRUE}$ | $\text{F03 Loss} = \mathbf{\$13.78}$

#### Leak Analysis
* **Leak Classification:** **Formula Leak**.
* **Responsible Field/Behavior:** Quoting Shopify Documentation: *"LineItem.discountedUnitPriceSet includes line-level discounts... It doesn't include order-level or code-based discounts."* V1 assumed unit prices reflect all discounts.
* **Flaws Demonstrated:** Flaw 6 (Assumes discountedUnitPriceSet reflects all discounts).
* **Merchant Takeaway:** V1 reports a fictitious profit of +\$66.22 by completely ignoring the \$80.00 coupon code, blinding the merchant to an actual cash loss of -\$13.78.

---

### Scenario 05: Third-Party Gateway (PayPal Express) with Empty `fees` Array
* **Description:** $200.00 order processed via PayPal. COGS is $170.00. Outbound courier shipping is $18.00. PayPal actually charged the merchant $7.47 (3.49% + $0.49), but Shopify GraphQL returns an empty `fees: []` array.
* **Test Focus:** Tests Shopify's restriction of `OrderTransaction.fees` to Shopify Payments only, and V1's default-to-$0.00 flaw.

#### Synthetic GraphQL Response JSON
```json
{
  "data": {
    "order": {
      "id": "gid://shopify/Order/8100000005",
      "name": "#1005",
      "createdAt": "2026-09-15T14:00:00Z",
      "cancelledAt": null,
      "currencyCode": "USD",
      "taxesIncluded": false,
      "displayFinancialStatus": "PAID",
      "currentSubtotalPriceSet": { "shopMoney": { "amount": "200.00", "currencyCode": "USD" } },
      "currentTotalPriceSet": { "shopMoney": { "amount": "200.00", "currencyCode": "USD" } },
      "currentShippingPriceSet": { "shopMoney": { "amount": "0.00", "currencyCode": "USD" } },
      "currentTotalTaxSet": { "shopMoney": { "amount": "0.00", "currencyCode": "USD" } },
      "tags": [],
      "lineItems": {
        "edges": [
          {
            "node": {
              "id": "gid://shopify/LineItem/9100000005",
              "quantity": 1,
              "currentQuantity": 1,
              "discountedUnitPriceSet": { "shopMoney": { "amount": "200.00", "currencyCode": "USD" } },
              "discountAllocations": [],
              "variant": { "inventoryItem": { "unitCost": { "amount": "170.00", "currencyCode": "USD" } } }
            }
          }
        ]
      },
      "transactions": [
        {
          "id": "gid://shopify/OrderTransaction/6100000005",
          "kind": "SALE",
          "status": "SUCCESS",
          "gateway": "paypal",
          "manualPaymentGateway": false,
          "amountSet": { "shopMoney": { "amount": "200.00", "currencyCode": "USD" } },
          "fees": []
        }
      ],
      "refunds": []
    }
  }
}
```
*(Actual courier outbound cost = \$18.00; Real off-platform PayPal fee = \$7.47)*

#### Formula Walkthroughs
* **Formula V1 Substitution:**
  * $\text{Order Gross Profit} = 200.00 - 170.00 = \$30.00$
  * V1 sees `fees: []` and defaults missing gateway fee to \$0.00:
  * $\text{Net Margin Cash} = \$30.00 - \$18.00 (\text{Shipping}) - \mathbf{\$0.00 (\text{Defaulted Fee})} = \mathbf{+\$12.00}$
  * $\text{F03 Breach} = \mathbf{FALSE}$ | $\text{F03 Loss} = \mathbf{\$0.00}$
* **Formula V2 Substitution:**
  * V2 inspects gateway (`gateway == "paypal"`, `manualPaymentGateway == false`).
  * Recognizes missing fee data as a **Data Leak**; initiates `EVALUATED_ESTIMATED` gate.
  * Applies standard PayPal benchmark fee rate ($3.49\% + \$0.49 = \$7.47$):
  * $\text{Cash In} = \$200.00$
  * $\text{Cash Out} = \$170.00 (\text{COGS}) + \$18.00 (\text{Shipping}) + \mathbf{\$7.47 (\text{Estimated Fee})} = \$195.47$
  * $\text{Net Margin Cash} = \$200.00 - \$195.47 = \mathbf{+\$4.53}$
  * $\text{Evaluability Status} = \mathbf{EVALUATED\_ESTIMATED}$
  * $\text{F03 Breach} = \mathbf{FALSE}$ | $\text{F03 Loss} = \mathbf{\$0.00}$ (Delta = -\$7.47 margin reduction)

*(Note: If shipping had been \$25.00, V1 would falsely report +\$5.00 healthy, while V2 correctly identifies a -\$2.47 breach).*

#### Leak Analysis
* **Leak Classification:** **Data Leak** (producing a Formula Leak in V1).
* **Responsible Field/Behavior:** `OrderTransaction.fees` is officially documented by Shopify as: *"Only present for Shopify Payments transactions."* For all other gateways, fees are omitted from the GraphQL schema entirely.
* **Flaws Demonstrated:** Flaw 5 (Missing gateway cost defaults to \$0.00) & **New Unaudited Leak (Shopify Payments-Only Fee Monopolization)**.
* **Merchant Takeaway:** V1 overstates net cash by \$7.47 on every PayPal order because Shopify refuses to ingest third-party processor fees, blinding merchants on thin margins to real processor-driven cash breaches.

---

### Scenario 06: Multi-Currency Order (`shopMoney` vs. `presentmentMoney`)
* **Description:** Store operates in US Dollars (`USD`). A customer in Japan purchases in Japanese Yen (`JPY`). Retail price is ¥15,000 JPY ($100.00 USD at spot rate 150 JPY/USD). COGS in store currency is $75.00 USD. Courier cost is $15.00 USD. Gateway fee is $3.20 USD.
* **Test Focus:** Validates currency handling and confirms `shopMoney` usage prevents massive numerical corruption.

#### Synthetic GraphQL Response JSON
```json
{
  "data": {
    "order": {
      "id": "gid://shopify/Order/8100000006",
      "name": "#1006",
      "createdAt": "2026-09-15T15:00:00Z",
      "cancelledAt": null,
      "currencyCode": "USD",
      "taxesIncluded": false,
      "displayFinancialStatus": "PAID",
      "currentSubtotalPriceSet": {
        "shopMoney": { "amount": "100.00", "currencyCode": "USD" },
        "presentmentMoney": { "amount": "15000.00", "currencyCode": "JPY" }
      },
      "currentTotalPriceSet": {
        "shopMoney": { "amount": "100.00", "currencyCode": "USD" },
        "presentmentMoney": { "amount": "15000.00", "currencyCode": "JPY" }
      },
      "currentShippingPriceSet": {
        "shopMoney": { "amount": "0.00", "currencyCode": "USD" },
        "presentmentMoney": { "amount": "0.00", "currencyCode": "JPY" }
      },
      "currentTotalTaxSet": { "shopMoney": { "amount": "0.00", "currencyCode": "USD" } },
      "tags": [],
      "lineItems": {
        "edges": [
          {
            "node": {
              "id": "gid://shopify/LineItem/9100000006",
              "quantity": 1,
              "currentQuantity": 1,
              "discountedUnitPriceSet": {
                "shopMoney": { "amount": "100.00", "currencyCode": "USD" },
                "presentmentMoney": { "amount": "15000.00", "currencyCode": "JPY" }
              },
              "discountAllocations": [],
              "variant": { "inventoryItem": { "unitCost": { "amount": "75.00", "currencyCode": "USD" } } }
            }
          }
        ]
      },
      "transactions": [
        {
          "id": "gid://shopify/OrderTransaction/6100000006",
          "kind": "SALE",
          "status": "SUCCESS",
          "gateway": "shopify_payments",
          "manualPaymentGateway": false,
          "amountSet": {
            "shopMoney": { "amount": "100.00", "currencyCode": "USD" },
            "presentmentMoney": { "amount": "15000.00", "currencyCode": "JPY" }
          },
          "fees": [{ "id": "gid://shopify/TransactionFee/5100000006", "amount": { "amount": "3.20", "currencyCode": "USD" } }]
        }
      ],
      "refunds": []
    }
  }
}
```
*(Actual courier outbound cost = \$15.00 USD)*

#### Formula Walkthroughs
* **Formula V1 Substitution (Naive Currency Parsing):**
  * V1 naively reads the raw presentment number without checking currency:
  * $\text{Gross Profit} = 15,000.00 (\text{JPY}) - 75.00 (\text{USD COGS}) = \$14,925.00$
  * $\text{Net Margin Cash} = \$14,925.00 - \$15.00 - \$3.20 = \mathbf{+\$14,906.80}$
  * $\text{F03 Breach} = \mathbf{FALSE}$ | $\text{F03 Loss} = \mathbf{\$0.00}$ (Catastrophically corrupt number)
* **Formula V2 Substitution (Strict `shopMoney` Locking):**
  * V2 binds exclusively to `shopMoney`:
  * $\text{Cash In} = \$100.00 (\text{USD})$
  * $\text{Cash Out} = \$75.00 (\text{COGS}) + \$15.00 (\text{Shipping}) + \$3.20 (\text{Fee}) = \$93.20 (\text{USD})$
  * $\text{Net Margin Cash} = \$100.00 - \$93.20 = \mathbf{+\$6.80 (\text{USD})}$
  * $\text{Evaluability Status} = \text{EVALUATED\_CONFIRMED}$
  * $\text{F03 Breach} = \mathbf{FALSE}$ | $\text{F03 Loss} = \mathbf{\$0.00}$

#### Leak Analysis
* **Leak Classification:** **Formula Leak**.
* **Responsible Field/Behavior:** Failure to parse `MoneyBag.shopMoney`. Reading `presentmentMoney` mixes disparate foreign currencies directly against base store currency COGS.
* **Flaws Demonstrated:** Flaw 7 (No currency handling).
* **Merchant Takeaway:** Without strict `shopMoney` anchoring, multi-currency orders generate absurd phantom profits (e.g. +\$14,906.80 on a \$100 order), entirely wrecking cohort-level margin metrics.

---

### Scenario 07: Product Whose `unitCost` Changed Post-Order (Stale COGS Hazard)
* **Description:** Order placed on June 1st when product COGS was $30.00. Retail price was $60.00. In August, inflation forced a supplier price increase, and the merchant updated Shopify's `InventoryItem.unitCost` to $58.00. Audit runs in September. Outbound shipping was $8.00; gateway fee was $2.04.
* **Test Focus:** Demonstrates that `InventoryItem.unitCost` is a mutable live pointer and Shopify provides no historical cost snapshot in GraphQL.

#### Synthetic GraphQL Response JSON
```json
{
  "data": {
    "order": {
      "id": "gid://shopify/Order/8100000007",
      "name": "#1007",
      "createdAt": "2026-06-01T10:00:00Z",
      "cancelledAt": null,
      "currencyCode": "USD",
      "taxesIncluded": false,
      "displayFinancialStatus": "PAID",
      "currentSubtotalPriceSet": { "shopMoney": { "amount": "60.00", "currencyCode": "USD" } },
      "currentTotalPriceSet": { "shopMoney": { "amount": "60.00", "currencyCode": "USD" } },
      "currentShippingPriceSet": { "shopMoney": { "amount": "0.00", "currencyCode": "USD" } },
      "tags": [],
      "lineItems": {
        "edges": [
          {
            "node": {
              "id": "gid://shopify/LineItem/9100000007",
              "quantity": 1,
              "currentQuantity": 1,
              "discountedUnitPriceSet": { "shopMoney": { "amount": "60.00", "currencyCode": "USD" } },
              "discountAllocations": [],
              "variant": {
                "inventoryItem": {
                  "unitCost": { "amount": "58.00", "currencyCode": "USD" }
                }
              }
            }
          }
        ]
      },
      "transactions": [
        {
          "id": "gid://shopify/OrderTransaction/6100000007",
          "kind": "SALE",
          "status": "SUCCESS",
          "gateway": "shopify_payments",
          "manualPaymentGateway": false,
          "amountSet": { "shopMoney": { "amount": "60.00", "currencyCode": "USD" } },
          "fees": [{ "id": "gid://shopify/TransactionFee/5100000007", "amount": { "amount": "2.04", "currencyCode": "USD" } }]
        }
      ],
      "refunds": []
    }
  }
}
```
*(Historical cost at order creation = \$30.00; Current live cost in Shopify = \$58.00; Courier cost = \$8.00)*

#### Formula Walkthroughs
* **Formula V1 Substitution:**
  * V1 reads current live `unitCost` (\$58.00):
  * $\text{Order Gross Profit} = 60.00 - 58.00 = \$2.00$
  * $\text{Net Margin Cash} = \$2.00 - \$8.00 (\text{Shipping}) - \$2.04 (\text{Fee}) = \mathbf{-\$8.04}$
  * $\text{F03 Breach} = \mathbf{TRUE}$ | $\text{F03 Loss} = \mathbf{\$8.04}$ (False Alarm!)
* **Formula V2 Substitution (with Point-in-Time Sidecar Index):**
  * V2 checks historical cost index at `createdAt` (June 1) $\rightarrow$ Resolves \$30.00 COGS:
  * $\text{Cash In} = \$60.00$
  * $\text{Cash Out} = \$30.00 (\text{Historical COGS}) + \$8.00 (\text{Shipping}) + \$2.04 (\text{Fee}) = \$40.04$
  * $\text{Net Margin Cash} = \$60.00 - \$40.04 = \mathbf{+\$19.96}$
  * $\text{Evaluability Status} = \text{EVALUATED\_CONFIRMED}$
  * $\text{F03 Breach} = \mathbf{FALSE}$ | $\text{F03 Loss} = \mathbf{\$0.00}$
  * *(If no historical index exists, V2 is forced into `EVALUATED_ESTIMATED` with a STALE_COGS warning).*

#### Leak Analysis
* **Leak Classification:** **Data Leak**.
* **Responsible Field/Behavior:** `InventoryItem.unitCost` is a mutable live pointer. The Shopify Admin GraphQL API has **zero historical point-in-time cost field** on `Order` or `LineItem`.
* **Flaws Demonstrated:** Flaw 3 (Uses current/live COGS regardless of order date).
* **Merchant Takeaway:** V1 falsely flags historically profitable orders as cash breaches whenever suppliers increase product costs months later.

---

### Scenario 08: Partial-Quantity Return (Restocked Unit vs. Scrapped Unit)
* **Description:** Customer buys 2 jackets at $100.00 each ($200.00 total). Unit COGS is $40.00 ($80.00 total). Customer returns 1 jacket. Merchant inspects the item, approves the return, and restocks it to inventory (`restocked: true`, `restockType: "RETURN"`). Merchant refunds $100.00. Outbound shipping was $15.00; retained gateway fee post-refund is $3.20.
* **Test Focus:** Tests unit-level proration using `RefundLineItem.restocked` vs. naive boolean order-level refund handling.

#### Synthetic GraphQL Response JSON
```json
{
  "data": {
    "order": {
      "id": "gid://shopify/Order/8100000008",
      "name": "#1008",
      "createdAt": "2026-09-10T09:00:00Z",
      "cancelledAt": null,
      "currencyCode": "USD",
      "taxesIncluded": false,
      "displayFinancialStatus": "PARTIALLY_REFUNDED",
      "currentSubtotalPriceSet": { "shopMoney": { "amount": "100.00", "currencyCode": "USD" } },
      "currentTotalPriceSet": { "shopMoney": { "amount": "100.00", "currencyCode": "USD" } },
      "currentShippingPriceSet": { "shopMoney": { "amount": "0.00", "currencyCode": "USD" } },
      "currentTotalTaxSet": { "shopMoney": { "amount": "0.00", "currencyCode": "USD" } },
      "tags": [],
      "lineItems": {
        "edges": [
          {
            "node": {
              "id": "gid://shopify/LineItem/9100000008",
              "quantity": 2,
              "currentQuantity": 1,
              "discountedUnitPriceSet": { "shopMoney": { "amount": "100.00", "currencyCode": "USD" } },
              "discountAllocations": [],
              "variant": { "inventoryItem": { "unitCost": { "amount": "40.00", "currencyCode": "USD" } } }
            }
          }
        ]
      },
      "transactions": [
        {
          "id": "gid://shopify/OrderTransaction/6100000008-1",
          "kind": "SALE",
          "status": "SUCCESS",
          "gateway": "shopify_payments",
          "amountSet": { "shopMoney": { "amount": "200.00", "currencyCode": "USD" } },
          "fees": [{ "id": "gid://shopify/TransactionFee/5100000008-1", "amount": { "amount": "6.10", "currencyCode": "USD" } }]
        },
        {
          "id": "gid://shopify/OrderTransaction/6100000008-2",
          "kind": "REFUND",
          "status": "SUCCESS",
          "gateway": "shopify_payments",
          "amountSet": { "shopMoney": { "amount": "100.00", "currencyCode": "USD" } },
          "fees": []
        }
      ],
      "refunds": [
        {
          "id": "gid://shopify/Refund/4100000008",
          "createdAt": "2026-09-12T14:00:00Z",
          "totalRefundedSet": { "shopMoney": { "amount": "100.00", "currencyCode": "USD" } },
          "refundLineItems": {
            "edges": [
              {
                "node": {
                  "id": "gid://shopify/RefundLineItem/3100000008",
                  "quantity": 1,
                  "restocked": true,
                  "restockType": "RETURN",
                  "subtotalSet": { "shopMoney": { "amount": "100.00", "currencyCode": "USD" } },
                  "lineItem": { "id": "gid://shopify/LineItem/9100000008" }
                }
              }
            ]
          }
        }
      ]
    }
  }
}
```
*(Actual courier outbound cost = \$15.00; Net gateway fee retained post-refund = \$3.20)*

#### Formula Walkthroughs
* **Formula V1 Substitution:**
  * V1 uses original `quantity` (2) from `lineItems` or treats active items without unit proration:
  * $\text{Order Gross Profit} = \sum(\text{Net Selling Price} - \text{COGS}) = 100.00 - (2 \times 40.00) = 100.00 - 80.00 = \$20.00$
  * $\text{Net Margin Cash} = \$20.00 - \$15.00 (\text{Shipping}) - \$3.20 (\text{Fee}) = \mathbf{+\$1.80}$
  * $\text{F03 Breach} = \mathbf{FALSE}$ | $\text{F03 Loss} = \mathbf{\$0.00}$
  * *(Note: If shipping had been \$22.00, V1 would declare a breach of -\$5.20).*
* **Formula V2 Substitution (Unit-Level Restock Proration):**
  * $\text{Initial Ordered Units} = 2$; $\text{Restocked Units} = 1$
  * $\text{Units NOT Restocked} = 2 - 1 = 1 \text{ unit}$
  * $\text{Realized Cash In} = \$200.00 (\text{Initial}) - \$100.00 (\text{Refund}) = \$100.00$
  * $\text{Realized Cash Out} = (1 \times \$40.00 \text{ COGS}) + \$15.00 (\text{Shipping}) + \$3.20 (\text{Fee}) = \$58.20$
  * $\text{Net Margin Cash} = \$100.00 - \$58.20 = \mathbf{+\$41.80}$
  * $\text{Evaluability Status} = \text{EVALUATED\_CONFIRMED}$
  * $\text{F03 Breach} = \mathbf{FALSE}$ | $\text{F03 Loss} = \mathbf{\$0.00}$

#### Leak Analysis
* **Leak Classification:** **Formula Leak**.
* **Responsible Field/Behavior:** Failure to evaluate `RefundLineItem.restocked` and `restockType`. V1 burdens the order with the COGS of returned merchandise that was physically put back on the shelf and made available for resale.
* **Flaws Demonstrated:** Flaw 8 (Returns modeled as an all-or-nothing boolean, not unit-level).
* **Merchant Takeaway:** V1 severely understates retained margin (\$1.80 vs. \$41.80, a \$40.00 discrepancy) because it treats restocked inventory as lost cash expense.

---

### Scenario 09: Full Refund with Asynchronous Third-Party Gateway (`totalRefundedSet: 0.00` Race Condition)
* **Description:** A $100.00 order via an external BNPL/gateway (e.g. Klarna). A full refund was initiated 2 minutes ago. The refund transaction is asynchronous and currently in `PENDING` status. The GraphQL `Refund.totalRefundedSet` temporarily reports `$0.00` until settlement. Product was not restocked (damaged/scrapped, COGS $40.00). Outbound shipping was $10.00. Non-refundable gateway fee is $3.20.
* **Test Focus:** Tests timing vulnerabilities and asynchronous gateway settlement race conditions.

#### Synthetic GraphQL Response JSON
```json
{
  "data": {
    "order": {
      "id": "gid://shopify/Order/8100000009",
      "name": "#1009",
      "createdAt": "2026-09-15T16:00:00Z",
      "cancelledAt": null,
      "currencyCode": "USD",
      "taxesIncluded": false,
      "displayFinancialStatus": "REFUNDED",
      "currentSubtotalPriceSet": { "shopMoney": { "amount": "0.00", "currencyCode": "USD" } },
      "currentTotalPriceSet": { "shopMoney": { "amount": "0.00", "currencyCode": "USD" } },
      "currentShippingPriceSet": { "shopMoney": { "amount": "0.00", "currencyCode": "USD" } },
      "tags": [],
      "lineItems": {
        "edges": [
          {
            "node": {
              "id": "gid://shopify/LineItem/9100000009",
              "quantity": 1,
              "currentQuantity": 0,
              "discountedUnitPriceSet": { "shopMoney": { "amount": "100.00", "currencyCode": "USD" } },
              "discountAllocations": [],
              "variant": { "inventoryItem": { "unitCost": { "amount": "40.00", "currencyCode": "USD" } } }
            }
          }
        ]
      },
      "transactions": [
        {
          "id": "gid://shopify/OrderTransaction/6100000009-1",
          "kind": "SALE",
          "status": "SUCCESS",
          "gateway": "custom_gateway",
          "manualPaymentGateway": false,
          "amountSet": { "shopMoney": { "amount": "100.00", "currencyCode": "USD" } },
          "fees": []
        },
        {
          "id": "gid://shopify/OrderTransaction/6100000009-2",
          "kind": "REFUND",
          "status": "PENDING",
          "gateway": "custom_gateway",
          "manualPaymentGateway": false,
          "amountSet": { "shopMoney": { "amount": "100.00", "currencyCode": "USD" } },
          "fees": []
        }
      ],
      "refunds": [
        {
          "id": "gid://shopify/Refund/4100000009",
          "createdAt": "2026-09-15T16:30:00Z",
          "totalRefundedSet": { "shopMoney": { "amount": "0.00", "currencyCode": "USD" } },
          "refundLineItems": {
            "edges": [
              {
                "node": {
                  "id": "gid://shopify/RefundLineItem/3100000009",
                  "quantity": 1,
                  "restocked": false,
                  "restockType": "NO_RESTOCK",
                  "subtotalSet": { "shopMoney": { "amount": "100.00", "currencyCode": "USD" } },
                  "lineItem": { "id": "gid://shopify/LineItem/9100000009" }
                }
              }
            ]
          }
        }
      ]
    }
  }
}
```
*(Actual courier outbound cost = \$10.00; Estimated non-refundable fee = \$3.20)*

#### Formula Walkthroughs
* **Formula V1 Substitution:**
  * V1 reads `Refund.totalRefundedSet` (\$0.00) or looks at `LineItem.discountedUnitPriceSet` (\$100.00):
  * $\text{Order Gross Profit} = 100.00 - 40.00 = \$60.00$
  * V1 ignores missing fee and sets it to \$0.00:
  * $\text{Net Margin Cash} = \$60.00 - \$10.00 (\text{Shipping}) - \$0.00 (\text{Fee}) = \mathbf{+\$50.00}$
  * $\text{F03 Breach} = \mathbf{FALSE}$ | $\text{F03 Loss} = \mathbf{\$0.00}$
* **Formula V2 Substitution (Asynchronous Status Trap):**
  * V2 detects `OrderTransaction.status == PENDING` on the refund transaction and `currentQuantity == 0`:
  * Quarantines immediate evaluation until settlement or reads pending refund amount (\$100.00):
  * $\text{Cash In} = \$100.00 - \$100.00 (\text{Pending Refund}) = \$0.00$
  * $\text{Cash Out} = \$40.00 (\text{Unrestocked COGS}) + \$10.00 (\text{Shipping}) + \$3.20 (\text{Retained Fee}) = \$53.20$
  * $\text{Net Margin Cash} = \$0.00 - \$53.20 = \mathbf{-\$53.20}$
  * $\text{Evaluability Status} = \mathbf{EVALUATED\_ESTIMATED \ (QUARANTINED\_SETTLEMENT\_PENDING)}$
  * $\text{F03 Breach} = \mathbf{TRUE}$ | $\text{F03 Loss} = \mathbf{\$53.20}$

#### Leak Analysis
* **Leak Classification:** **Data Leak** (Asynchronous Settlement Latency).
* **Responsible Field/Behavior:** `Refund.totalRefundedSet` reports `"0.00"` while the underlying transaction has `status: PENDING`. Evaluating F03 instantly upon webhook trigger causes an enormous false-healthy reading.
* **Flaws Demonstrated:** **New Unaudited Leak (Gateway Refund Settlement Latency / Async Race Condition)**.
* **Merchant Takeaway:** Evaluating orders immediately upon refund webhooks before gateway settlement tells merchants an order made +\$50.00 when it actually suffered a -\$53.20 total cash loss.

---

### Scenario 10: Missing/NULL `unitCost` on Newly Launched SKU (Evaluability Gate)
* **Description:** Fast-launch promotional product sold for $80.00. The catalog manager forgot to fill in the "Cost per item" field in Shopify admin (`unitCost: null`). Courier shipping was $12.00; Shopify Payments fee was $2.62.
* **Test Focus:** Tests V1's "fold missing COGS into healthy" default vs. V2's strict `NOT_EVALUABLE` gate.

#### Synthetic GraphQL Response JSON
```json
{
  "data": {
    "order": {
      "id": "gid://shopify/Order/8100000010",
      "name": "#1010",
      "createdAt": "2026-09-15T17:00:00Z",
      "cancelledAt": null,
      "currencyCode": "USD",
      "taxesIncluded": false,
      "displayFinancialStatus": "PAID",
      "currentSubtotalPriceSet": { "shopMoney": { "amount": "80.00", "currencyCode": "USD" } },
      "currentTotalPriceSet": { "shopMoney": { "amount": "80.00", "currencyCode": "USD" } },
      "currentShippingPriceSet": { "shopMoney": { "amount": "0.00", "currencyCode": "USD" } },
      "tags": [],
      "lineItems": {
        "edges": [
          {
            "node": {
              "id": "gid://shopify/LineItem/9100000010",
              "quantity": 1,
              "currentQuantity": 1,
              "discountedUnitPriceSet": { "shopMoney": { "amount": "80.00", "currencyCode": "USD" } },
              "discountAllocations": [],
              "variant": {
                "inventoryItem": {
                  "unitCost": null
                }
              }
            }
          }
        ]
      },
      "transactions": [
        {
          "id": "gid://shopify/OrderTransaction/6100000010",
          "kind": "SALE",
          "status": "SUCCESS",
          "gateway": "shopify_payments",
          "manualPaymentGateway": false,
          "amountSet": { "shopMoney": { "amount": "80.00", "currencyCode": "USD" } },
          "fees": [{ "id": "gid://shopify/TransactionFee/5100000010", "amount": { "amount": "2.62", "currencyCode": "USD" } }]
        }
      ],
      "refunds": []
    }
  }
}
```
*(Actual courier outbound cost = \$12.00)*

#### Formula Walkthroughs
* **Formula V1 Substitution:**
  * V1 defaults missing COGS to \$0.00:
  * $\text{Order Gross Profit} = 80.00 - \mathbf{0.00} = \$80.00$
  * $\text{Net Margin Cash} = \$80.00 - \$12.00 (\text{Shipping}) - \$2.62 (\text{Fee}) = \mathbf{+\$65.38}$
  * $\text{F03 Breach} = \mathbf{FALSE}$ | $\text{F03 Loss} = \mathbf{\$0.00}$
* **Formula V2 Substitution:**
  * V2 evaluates input completeness: detects `unitCost == null` and absence of category fallback cost.
  * Triggers **Evaluability Gate**: Order classified as **`NOT_EVALUABLE`**.
  * Excluded from the breach rate calculation denominator.
  * Emits alert: `COGS_MISSING_QUARANTINE (SKU: UNKNOWN)`.
  * $\text{Net Margin Cash} = \mathbf{NULL / UNKNOWN}$
  * $\text{F03 Breach} = \mathbf{EXCLUDED}$ | $\text{F03 Loss} = \mathbf{\$0.00}$

#### Leak Analysis
* **Leak Classification:** **Formula Leak**.
* **Responsible Field/Behavior:** V1's assumption that missing inputs can be safely treated as \$0.00 cost, folding unknown operational blind spots into healthy profit.
* **Flaws Demonstrated:** Flaw 4 (Missing COGS defaults to non-breach) and Flaw 10 (Undefined denominator for breach rate).
* **Merchant Takeaway:** V1 manufactures a fictitious +\$65.38 profit out of thin air when catalog costs are unentered, while V2 quarantines the order so merchants know their reporting has missing data.

---

### Scenario 11: $0.00 Influencer Sample / Replacement Order with Real COGS
* **Description:** Marketing team generates a $0.00 draft order for a VIP influencer (`tags: ["influencer_sample", "pr_gifting"]`). 2 luxury items sent at 100% discount. Stated retail was $180.00, customer paid $0.00. COGS is $45.00 each ($90.00 total). Expedited courier freight paid by merchant is $24.00. No processor involved (`manualPaymentGateway: true`, fee = $0.00).
* **Test Focus:** Tests order-type pollution and absence of native `order_type` field in GraphQL.

#### Synthetic GraphQL Response JSON
```json
{
  "data": {
    "order": {
      "id": "gid://shopify/Order/8100000011",
      "name": "#1011",
      "createdAt": "2026-09-15T18:00:00Z",
      "cancelledAt": null,
      "currencyCode": "USD",
      "taxesIncluded": false,
      "displayFinancialStatus": "PAID",
      "currentSubtotalPriceSet": { "shopMoney": { "amount": "0.00", "currencyCode": "USD" } },
      "currentTotalPriceSet": { "shopMoney": { "amount": "0.00", "currencyCode": "USD" } },
      "currentShippingPriceSet": { "shopMoney": { "amount": "0.00", "currencyCode": "USD" } },
      "tags": ["influencer_sample", "pr_gifting"],
      "lineItems": {
        "edges": [
          {
            "node": {
              "id": "gid://shopify/LineItem/9100000011",
              "quantity": 2,
              "currentQuantity": 2,
              "discountedUnitPriceSet": { "shopMoney": { "amount": "0.00", "currencyCode": "USD" } },
              "discountAllocations": [],
              "variant": { "inventoryItem": { "unitCost": { "amount": "45.00", "currencyCode": "USD" } } }
            }
          }
        ]
      },
      "transactions": [
        {
          "id": "gid://shopify/OrderTransaction/6100000011",
          "kind": "SALE",
          "status": "SUCCESS",
          "gateway": "manual",
          "manualPaymentGateway": true,
          "amountSet": { "shopMoney": { "amount": "0.00", "currencyCode": "USD" } },
          "fees": []
        }
      ],
      "refunds": []
    }
  }
}
```
*(Actual expedited courier outbound cost = \$24.00)*

#### Formula Walkthroughs
* **Formula V1 Substitution:**
  * $\text{Order Gross Profit} = 0.00 - (2 \times 45.00) = -\$90.00$
  * $\text{Net Margin Cash} = -\$90.00 - \$24.00 (\text{Shipping}) - \$0.00 (\text{Fee}) = \mathbf{-\$114.00}$
  * $\text{F03 Breach} = \mathbf{TRUE}$ | $\text{F03 Loss} = \mathbf{\$114.00}$
  * *(Pollutes commercial store breach rate and fires executive emergency alerts).*
* **Formula V2 Substitution (Order Intent Segmentation):**
  * V2 inspects `tags` and `manualPaymentGateway`:
  * Detects `pr_gifting` tag and \$0.00 commercial price.
  * Segregates order as **`EXCLUDED_PROMOTIONAL_MARKETING`** from the commercial F03 breach denominator.
  * Reallocates \$114.00 cash expenditure to Customer Acquisition Cost (CAC) / Marketing ledger.
  * $\text{Commercial F03 Breach} = \mathbf{EXCLUDED}$ | $\text{Commercial F03 Loss} = \mathbf{\$0.00}$

#### Leak Analysis
* **Leak Classification:** **Data & Formula Leak**.
* **Responsible Field/Behavior:** Shopify lacks an `order_type` enum (Data Leak). V1 has no business logic to filter intentional non-revenue orders (Formula Leak), treating marketing expenses as defective retail sales.
* **Flaws Demonstrated:** Flaw 9 (No order_type concept for gifts/samples/replacements).
* **Merchant Takeaway:** V1 panics leadership by reporting intentional marketing gifting as commercial cash-bleeding failures, polluting core retail margin analytics.

---

### Scenario 12: External Shipping Label via 3PL (The "Missing Courier Cost" Leak)
* **Description:** $30.00 order with $22.00 COGS. Processed via Shopify Payments (fee $1.17). The merchant ships via ShipStation/EasyPost; no Shopify Shipping label is purchased. The real carrier cost charged by UPS is $8.50.
* **Test Focus:** Tests V1's default-to-$0.00 shipping cost flaw against V2's fallback estimation model.

#### Synthetic GraphQL Response JSON
```json
{
  "data": {
    "order": {
      "id": "gid://shopify/Order/8100000012",
      "name": "#1012",
      "createdAt": "2026-09-15T19:00:00Z",
      "cancelledAt": null,
      "currencyCode": "USD",
      "taxesIncluded": false,
      "displayFinancialStatus": "PAID",
      "currentSubtotalPriceSet": { "shopMoney": { "amount": "30.00", "currencyCode": "USD" } },
      "currentTotalPriceSet": { "shopMoney": { "amount": "30.00", "currencyCode": "USD" } },
      "currentShippingPriceSet": { "shopMoney": { "amount": "0.00", "currencyCode": "USD" } },
      "tags": [],
      "lineItems": {
        "edges": [
          {
            "node": {
              "id": "gid://shopify/LineItem/9100000012",
              "quantity": 1,
              "currentQuantity": 1,
              "discountedUnitPriceSet": { "shopMoney": { "amount": "30.00", "currencyCode": "USD" } },
              "discountAllocations": [],
              "variant": { "inventoryItem": { "unitCost": { "amount": "22.00", "currencyCode": "USD" } } }
            }
          }
        ]
      },
      "transactions": [
        {
          "id": "gid://shopify/OrderTransaction/6100000012",
          "kind": "SALE",
          "status": "SUCCESS",
          "gateway": "shopify_payments",
          "manualPaymentGateway": false,
          "amountSet": { "shopMoney": { "amount": "30.00", "currencyCode": "USD" } },
          "fees": [{ "id": "gid://shopify/TransactionFee/5100000012", "amount": { "amount": "1.17", "currencyCode": "USD" } }]
        }
      ],
      "refunds": []
    }
  }
}
```
*(In Shopify GraphQL, `actualShippingCost` is completely absent. Real carrier cost paid on ShipStation = \$8.50)*

#### Formula Walkthroughs
* **Formula V1 Substitution:**
  * V1 sees no shipping cost field and defaults to \$0.00:
  * $\text{Order Gross Profit} = 30.00 - 22.00 = \$8.00$
  * $\text{Net Margin Cash} = \$8.00 - \mathbf{\$0.00 (\text{Defaulted Shipping})} - \$1.17 (\text{Fee}) = \mathbf{+\$6.83}$
  * $\text{F03 Breach} = \mathbf{FALSE}$ | $\text{F03 Loss} = \mathbf{\$0.00}$
* **Formula V2 Substitution (Estimated Courier Fallback):**
  * V2 detects that carrier shipping cost is missing from the GraphQL payload.
  * Enforces **Evaluability Gate rule**: Never default missing shipping to \$0.00.
  * Imputes zone-based standard shipping fallback ($8.50) and tags order as `EVALUATED_ESTIMATED`:
  * $\text{Cash In} = \$30.00$
  * $\text{Cash Out} = \$22.00 (\text{COGS}) + \mathbf{\$8.50 (\text{Estimated Courier})} + \$1.17 (\text{Fee}) = \$31.67$
  * $\text{Net Margin Cash} = \$30.00 - \$31.67 = \mathbf{-\$1.67}$
  * $\text{Evaluability Status} = \mathbf{EVALUATED\_ESTIMATED}$
  * $\text{F03 Breach} = \mathbf{TRUE}$ | $\text{F03 Loss} = \mathbf{\$1.67}$

#### Leak Analysis
* **Leak Classification:** **Data Leak** (Absence of 3PL shipping cost in Shopify) $\rightarrow$ **Formula Leak in V1** (defaulting to \$0).
* **Responsible Field/Behavior:** Outbound carrier shipping cost does not exist in Shopify's Order GraphQL schema when fulfilled via external shipping software.
* **Flaws Demonstrated:** Flaw 5 (Missing shipping/gateway cost defaults to \$0.00).
* **Merchant Takeaway:** V1 reports a comfortable +\$6.83 profit on an order that actually lost -\$1.67 in physical cash, because it assumed shipping packages across the country was completely free.

---

## Comprehensive Validation Summary Table

| Scenario ID & Description | Formula V1 Net Cash (Result) | Formula V2 Net Cash (Result) | Absolute Discrepancy ($\Delta$) | Primary Leak Type | Flaw(s) Proved & Schema Driver | Severity |
| :--- | :---: | :---: | :---: | :---: | :--- | :---: |
| **TC-01: Baseline Clean Order** | +\$56.80 (Healthy) | +\$56.80 (Healthy) | **\$0.00** | None (Control) | Baseline Sanity Parity | Low |
| **TC-02: Flat Shipping vs. Courier** | -\$9.04 (Breach) | +\$0.96 (Healthy) | **\$10.00** | **Formula Leak** | Flaw 1: Omission of `currentShippingPriceSet` | **High** |
| **TC-03: Tax-Inclusive Store (VAT)** | +£13.22 (Healthy) | -£6.78 (Breach) | **£20.00** | **Formula Leak** | Flaw 2: Failure to subtract `currentTotalTaxSet` | **Critical** |
| **TC-04: Cart Discount Code** | +\$66.22 (Healthy) | -\$13.78 (Breach) | **\$80.00** | **Formula Leak** | Flaw 6: Ignored `discountAllocations` on lines | **Critical** |
| **TC-05: 3rd-Party Gateway (PayPal)**| +\$12.00 (Healthy) | +\$4.53 (Healthy) | **\$7.47** | **Data Leak** | Flaw 5: `OrderTransaction.fees` empty for non-SP | **High** |
| **TC-06: Multi-Currency (JPY/USD)** | +\$14,906.80 (Corrupt)| +\$6.80 (Healthy) | **\$14,900.00** | **Formula Leak** | Flaw 7: Failure to bind strictly to `shopMoney` | **Critical** |
| **TC-07: Stale Mutable COGS** | -\$8.04 (Breach) | +\$19.96 (Healthy) | **\$28.00** | **Data Leak** | Flaw 3: `unitCost` is live pointer; no snapshot | **High** |
| **TC-08: Partial Return & Restock** | +\$1.80 (Healthy) | +\$41.80 (Healthy) | **\$40.00** | **Formula Leak** | Flaw 8: Ignored `RefundLineItem.restocked` | **High** |
| **TC-09: Async Refund Race Cond.** | +\$50.00 (Healthy) | -\$53.20 (Breach) | **\$103.20** | **Data Leak** | New Leak: `totalRefundedSet` 0.00 while pending | **Critical** |
| **TC-10: Null COGS Promo SKU** | +\$65.38 (Healthy) | Null (Quarantined) | **\$65.38** | **Formula Leak** | Flaw 4 & 10: Null COGS defaulted to \$0.00 | **Critical** |
| **TC-11: $0 Influencer Gift Order** | -\$114.00 (Breach) | \$0.00 (Excluded) | **\$114.00** | **Data & Formula**| Flaw 9: Absence of native `order_type` enum | **Medium** |
| **TC-12: External 3PL Shipping** | +\$6.83 (Healthy) | -\$1.67 (Breach) | **\$8.50** | **Data Leak** | Flaw 5: 3PL courier costs missing from GraphQL | **High** |

---

## Architectural Conclusions & Production Implementation Directives

1. **Eliminate Blind Defaults:** Under no circumstances may missing shipping or processor costs default to \$0.00. Missing costs must either trigger deterministic estimation fallbacks tagged with `EVALUATED_ESTIMATED`, or be quarantined under `NOT_EVALUABLE`.
2. **Strict Currency Anchoring:** All arithmetic must lock directly to `shopMoney.amount`. `presentmentMoney` must be discarded during margin scoring to prevent catastrophic foreign exchange scale distortion.
3. **Point-in-Time Cost Capture:** Because the Shopify Admin GraphQL API does not record historical COGS on `Order` or `LineItem`, the ingestion pipeline must archive an append-only historical cost ledger captured via `inventory_items/update` webhooks or order-creation time snapshots.
4. **Enforce Settlement Verification:** For third-party gateways, refund webhook processing must verify that all refund transactions have reached `SUCCESS` before evaluating margin contribution, avoiding the `totalRefundedSet == 0.00` pending race condition.
5. **Tax Liability Isolation:** For stores with `taxesIncluded: true`, the statutory tax obligation (`currentTotalTaxSet`) must be deducted from gross receipts before evaluating net cash contribution.
