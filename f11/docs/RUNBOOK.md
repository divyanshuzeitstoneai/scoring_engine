# Operational Runbook & API Version Upgrade Guide

## 1. Daily Ingestion & Continuous Audit
1. **Incremental Sync:** Poll `orders_paged.graphql` by `updatedAt` every 15 minutes.
2. **Webhook Re-fetch:** Treat `orders/updated`, `refunds/create` webhooks as change signals only. Always execute `order_full.graphql` to ensure full data consistency.
3. **Weekly Historical Sweep:** Trigger `bulk_orders.graphql` weekly to reconcile any late backdated refunds.

---

## 2. API Version Upgrade Process
Shopify deprecates API versions quarterly. To upgrade from `2024-10`:
1. **Introspection Dump:** Run introspection against the new candidate version into a staging file `graphql/introspection_next.json`.
2. **Schema Diff:** Compare field types, nullability, and enums against `introspection.json`.
3. **Contract Test Run:** Execute `test_boundaries.py` and `test_formula_section15.py` targeting the new schema.
4. **Config Bump:** Update `api_version` in `f11.config.yaml` and record in `DECISION_LOG.md`.
