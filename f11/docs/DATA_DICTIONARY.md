# Formula F11 Data Dictionary

## 1. Input Fields

| Field Name | Type | Source Object | Description |
| :--- | :--- | :--- | :--- |
| `id` | `String` | `Order` | Order GraphQL GID |
| `name` | `String` | `Order` | Human-readable order number `#1001` |
| `createdAt` | `DateTime` | `Order` | Physical creation timestamp |
| `processedAt` | `DateTime` | `Order` | Economic order timestamp |
| `currencyCode` | `String` | `Order` | ISO currency code (USD, GBP, etc.) |
| `taxesIncluded` | `Boolean` | `Order` | True if prices embed statutory tax |
| `currentShippingPriceSet` | `MoneyBag` | `Order` | Active shipping amount collected |
| `actual_carrier_cost` | `Decimal` | `Metafield` | Measured carrier freight cost |
| `lineItems` | `List` | `Order` | Ingested line item array |
| `line.quantity` | `Int` | `LineItem` | Ordered quantity ($q_0$) |
| `line.currentQuantity`| `Int` | `LineItem` | Active unrefunded quantity ($q_c$) |
| `line.originalUnitPriceSet` | `MoneyBag` | `LineItem` | List unit price ($u$) |
| `line.discountAllocations` | `List` | `LineItem` | Allocated discounts list |
| `line.variant.inventoryItem.unitCost` | `MoneyV2` | `InventoryItem` | Sourced supplier unit cost |
| `transactions` | `List` | `Order` | Payment transactions and gateway fees |
| `refunds` | `List` | `Order` | Customer refunds and return line items |

---

## 2. Output Fields

| Metric / Field | Type | Unit | Description |
| :--- | :--- | :--- | :--- |
| `L` | `Int` | Minor Unit | List merchandise revenue |
| `D` | `Int` | Minor Unit | Allocated promotional discounts |
| `R` | `Int` | Minor Unit | Net merchandise collected |
| `Sc` | `Int` | Minor Unit | Shipping collected net of tax |
| `C` | `Int` | Minor Unit | Total commercial cash inflow ($R + S_c$) |
| `COGS` | `Int` / `NULL` | Minor Unit | Incurred Cost of Goods Sold |
| `S` | `Int` / `NULL` | Minor Unit | Outbound carrier freight cost |
| `G` | `Int` / `NULL` | Minor Unit | Gateway payment processing fees |
| `E` | `Int` | Minor Unit | Customer refunds & return write-offs |
| `O` | `Int` | Minor Unit | Operational handling & packaging |
| `P` | `Int` / `NULL` | Minor Unit | Contribution profit |
| `P_upper` | `Int` | Minor Unit | Upper bound profit without estimates |
| `margin` | `Decimal` | Percent | Net contribution margin ($P / C \times 100$) |
| `lane` | `String` | Enum | Evidentiary lane (`MEASURED`, `ESTIMATED`, `CONFIRMED_LOSS`, `UNDETERMINED`, `EXCLUDED`) |
| `band` | `String` | Enum | Profitability band (`high`, `acceptable`, `at_risk`, `cash_drain`, `zero_revenue`) |
| `classification` | `String` | Enum | `profitable`, `breakeven`, `unprofitable`, `excluded` |
| `top_loss_driver`| `String` / `NULL` | Enum | Primary loss contributor on cash drain orders |
