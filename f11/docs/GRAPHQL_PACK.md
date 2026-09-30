# GraphQL Query Pack Reference

All queries are pinned to Shopify Admin API **2024-10** and validated against `introspection.json`.

---

| Query File | Primary Purpose | Required Scopes | Est. Cost |
| :--- | :--- | :--- | :--- |
| [`shop_info.graphql`](file:///d:/Scoring%20engine/f11/graphql/shop_info.graphql) | Store currency, tax inclusion, presentment currencies | `read_orders` | 1 pt |
| [`order_full.graphql`](file:///d:/Scoring%20engine/f11/graphql/order_full.graphql) | Complete single-order financial graph | `read_orders`, `read_products` | 15 pts |
| [`orders_paged.graphql`](file:///d:/Scoring%20engine/f11/graphql/orders_paged.graphql) | Incremental sync using cursor pagination by `updatedAt` | `read_orders` | 10 pts/pg |
| [`variant_costs.graphql`](file:///d:/Scoring%20engine/f11/graphql/variant_costs.graphql) | Extract current `InventoryItem.unitCost` | `read_products`, `read_inventory` | 5 pts/pg |
| [`bulk_orders.graphql`](file:///d:/Scoring%20engine/f11/graphql/bulk_orders.graphql) | Asynchronous Bulk Operation mutation for historical ingestion | `read_orders`, `read_all_orders` | 1 pt |
| [`refunds_and_returns.graphql`](file:///d:/Scoring%20engine/f11/graphql/refunds_and_returns.graphql) | Detailed refund lines and restock policies | `read_orders` | 5 pts |
| [`transactions_fees.graphql`](file:///d:/Scoring%20engine/f11/graphql/transactions_fees.graphql) | Transactions and Shopify Payments processing fees | `read_orders` | 5 pts |
| [`payout_reconciliation.graphql`](file:///d:/Scoring%20engine/f11/graphql/payout_reconciliation.graphql) | Bank deposit and payout fee reconciliation | `read_shopify_payments_payouts` | 5 pts |
| [`order_metafield_carrier_cost.graphql`](file:///d:/Scoring%20engine/f11/graphql/order_metafield_carrier_cost.graphql) | Extract 3PL actual freight invoice cost from metafield | `read_orders` | 2 pts |
