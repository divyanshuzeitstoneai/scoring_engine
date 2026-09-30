# Formula F10: Operational Runbook

**Target API:** Shopify Admin GraphQL API `2024-10`  
**Execution Environment:** Python 3.10+ / Production Analytics Stack

---

## 1. Historical Backfill Execution

Historical backfills extract full store history via Bulk Operations:
1. Submit `bulk_operation_orders.graphql` mutation.
2. Poll bulk operation status until `COMPLETED`.
3. Download JSONL payload to immutable landing zone (`raw_landing/`).
4. Execute `f10/code/pipeline.py` with `cost_snapshot_policy: current_with_flag`.
5. Verify Gate `DQ-U1` (Uniqueness) and Gate `DQ-A1` (Allocation conservation).

---

## 2. Incremental Sync and Webhook Ingestion

Incremental syncs consume webhooks (`orders/updated`, `refunds/create`):
1. **HMAC Validation:** Validate `X-Shopify-Hmac-Sha256` header against merchant webhook secret.
2. **Point-in-Time Cost Capture:** On first ingestion of an order line, persist `(line_item_id, variant_id, unit_cost, captured_at)` to `cost_snapshot_table`.
3. **Idempotent Upsert:** Key staging writes by `(line_item_id, refund_id)`. Re-ingestion produces zero net change (Gate `DQ-U2`).
4. **Reconciliation Sweep:** Run a weekly reconciliation sweep using cursor pagination (`incremental_orders.graphql`).

---

## 3. Incident Response & Failure Recovery

| Incident | Root Cause | Resolution Action |
| :--- | :--- | :--- |
| **Gate DQ-K1 Failure** | Unassigned COGS state | Check variant cost resolution; verify quarantine assignment logic. |
| **Gate DQ-A1 Failure** | Penny allocation drift | Confirm integer cents precision in `allocate_largest_remainder`. |
| **Rate Limiting (429)** | Exceeded GraphQL query cost | Enable exponential backoff with jitter; monitor `throttleStatus`. |
| **Corrupted Bulk JSONL** | Network interruption | Re-trigger bulk operation; do not process partial files. |

---

## 4. Shopify API Version Upgrade Protocol

1. Shopify releases Admin API quarterly (`2024-10`, `2025-01`, etc.). Pinned versions are supported for 12 months.
2. **Step 1: Introspection Diff:** Execute GraphQL introspection query against new release candidate; diff types and enums (Gate `DQ-D2`).
3. **Step 2: Probes Re-execution:** Re-run Phase 0 probes PR-01 through PR-40 against the new version.
4. **Step 3: Update `config.example.yaml`:** Update `api_version: "2025-01"` and verify schema validation.
5. **Step 4: Golden Suite Run:** Execute `test_suite.py`; all 156 golden cases must pass before deploying upgrade.
