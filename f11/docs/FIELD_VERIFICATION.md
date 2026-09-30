# Field Verification Table (Shopify Admin API 2024-10)

This document provides evidentiary verification for all fields utilized by Formula F11 Order Profitability v2.1.
Every field is labeled according to Operating Rule R1:
- `[V-DOC]`: Documented in official Shopify documentation.
- `[V-INTRO]`: Verified via GraphQL schema introspection on version `2024-10`.
- `[V-DEV]`: Verified against real Shopify Development Store responses.
- `[CFG]`: Configurable merchant policy.
- `[UNV]`: Unverified / ambiguous field with explicit fallback documented in `UNVERIFIED.md`.

---

| Object | Field Path | GraphQL Type | Nullable | Scopes Required | Evidence Label | Fallback / Notes |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `Shop` | `currencyCode` | `CurrencyCode!` | No | `read_orders` | `[V-INTRO]` | Baseline shop currency |
| `Shop` | `taxesIncluded` | `Boolean!` | No | `read_orders` | `[V-INTRO]` | Tax-inclusive pricing flag |
| `Order` | `id` | `ID!` | No | `read_orders` | `[V-INTRO]` | Monotonic GID format |
| `Order` | `name` | `String!` | No | `read_orders` | `[V-INTRO]` | Human-readable order number `#1001` |
| `Order` | `createdAt` | `DateTime!` | No | `read_orders` | `[V-INTRO]` | Ingestion physical timestamp |
| `Order` | `processedAt` | `DateTime!` | No | `read_orders` | `[V-INTRO]` | Economic transaction timestamp |
| `Order` | `updatedAt` | `DateTime!` | No | `read_orders` | `[V-INTRO]` | Cursor sync watermarking |
| `Order` | `cancelledAt` | `DateTime` | Yes | `read_orders` | `[V-INTRO]` | Evaluated for cancellation policies |
| `Order` | `cancelReason` | `OrderCancelReason` | Yes | `read_orders` | `[V-INTRO]` | Customer, fraud, inventory, etc. |
| `Order` | `test` | `Boolean!` | No | `read_orders` | `[V-INTRO]` | Route to EXCLUDED by policy |
| `Order` | `taxesIncluded` | `Boolean!` | No | `read_orders` | `[V-INTRO]` | Determines whether tax is embedded in price |
| `Order` | `currencyCode` | `CurrencyCode!` | No | `read_orders` | `[V-INTRO]` | Must match `shop_currency` config |
| `Order` | `displayFinancialStatus` | `OrderFinancialStatus!` | No | `read_orders` | `[V-INTRO]` | Enum state machine |
| `Order` | `displayFulfillmentStatus` | `OrderFulfillmentStatus!` | No | `read_orders` | `[V-INTRO]` | Fulfillment state machine |
| `Order` | `paymentGatewayNames` | `[String!]!` | No | `read_orders` | `[V-INTRO]` | Gateways used on checkout |
| `Order` | `cartDiscountAmountSet` | `MoneyBag` | Yes | `read_orders` | `[V-DOC]` | Order-level discount as sold |
| `Order` | `totalDiscountsSet` | `MoneyBag` | Yes | `read_orders` | `[V-INTRO]` | Realized discounts sum |
| `Order` | `subtotalPriceSet` | `MoneyBag` | Yes | `read_orders` | `[V-INTRO]` | Pre-tax, pre-shipping subtotal |
| `Order` | `currentSubtotalPriceSet` | `MoneyBag` | Yes | `read_orders` | `[V-INTRO]` | Net of active line quantities |
| `Order` | `totalShippingPriceSet` | `MoneyBag` | Yes | `read_orders` | `[V-INTRO]` | Gross freight charged |
| `Order` | `currentShippingPriceSet` | `MoneyBag` | Yes | `read_orders` | `[V-INTRO]` | Active shipping collected |
| `Order` | `totalRefundedSet` | `MoneyBag` | Yes | `read_orders` | `[V-INTRO]` | Total customer cash refunded |
| `Order` | `netPaymentSet` | `MoneyBag` | Yes | `read_orders` | `[V-INTRO]` | Reconciled received cash |
| `LineItem` | `id` | `ID!` | No | `read_orders` | `[V-INTRO]` | Line item GID |
| `LineItem` | `quantity` | `Int!` | No | `read_orders` | `[V-INTRO]` | Originally ordered quantity `q0` |
| `LineItem` | `currentQuantity` | `Int!` | No | `read_orders` | `[V-INTRO]` | Active unrefunded quantity `qc` |
| `LineItem` | `isGiftCard` | `Boolean!` | No | `read_orders` | `[V-INTRO]` | Excluded from merchandise revenue |
| `LineItem` | `requiresShipping` | `Boolean!` | No | `read_orders` | `[V-INTRO]` | Structural zero shipping trigger |
| `LineItem` | `originalUnitPriceSet` | `MoneyBag!` | No | `read_orders` | `[V-INTRO]` | List unit price `u` |
| `LineItem` | `discountAllocations` | `[DiscountAllocation!]!` | No | `read_orders` | `[V-INTRO]` | Line and order-level discount splits |
| `LineItem` | `variant.inventoryItem.unitCost` | `MoneyV2` | Yes | `read_products, read_inventory` | `[V-DOC]` | Current unit supplier cost |
| `OrderTransaction` | `fees` | `[TransactionFee!]!` | Yes | `read_orders` | `[V-DOC]` | Present ONLY for Shopify Payments |
| `RefundLineItem` | `restockType` | `RefundLineItemRestockType` | Yes | `read_orders` | `[V-DOC]` | RESTOCK vs CANCEL vs RETURN_CANCEL |
| `Order` | `metafield(actual_carrier_cost)` | `Metafield` | Yes | `read_orders` | `[CFG]` | Measured carrier freight |
| `Order` | `disputes` | `[Dispute!]` | Yes | `read_orders` | `[UNV]` | Fallback: treat as configured fee |
| `LineItem` | `discountedUnitPriceAfterAllDiscountsSet` | `MoneyBag` | Yes | `read_orders` | `[UNV]` | Fallback: compute via `discountAllocations` |
