import json

valid_cats = {
    'data_availability', 'discount', 'tax', 'currency', 'financial_status',
    'return', 'refund', 'payment_method', 'channel', 'boundary',
    'duplicate_integrity', 'bundle', 'historical_drift', 'timing',
    'timezone', 'denominator', 'volume', 'loss_leader', 'cancellation'
}

valid_flags = {
    'is_cogs_estimated', 'is_shipping_cost_estimated',
    'is_gateway_fee_estimated', 'is_cogs_missing', 'is_bundle',
    'is_promotional_gifting'
}

import os
p = "f03/data/test_fixtures.json"
if not os.path.exists(p):
    p = os.path.join(os.path.dirname(__file__), "..", "data", "test_fixtures.json")
if not os.path.exists(p):
    p = "scratch/test_fixtures.json"

data = json.load(open(p, "r", encoding="utf-8"))
required_top_keys = [
    'test_case_id', 'edge_case_category', 'description',
    'shopify_order_payload', 'external_data', 'cogs_snapshot_table_entry',
    'expected_result', 'why_this_breaks_naive_implementations'
]

for idx, tc in enumerate(data):
    for k in required_top_keys:
        assert k in tc, f"Missing key {k} in {tc.get('test_case_id', idx)}"
    assert tc['edge_case_category'] in valid_cats, f"Invalid category {tc['edge_case_category']} in {tc['test_case_id']}"
    
    exp = tc['expected_result']
    if 'flags_expected' in exp:
        for f in exp['flags_expected']:
            assert f in valid_flags, f"Invalid flag {f} in {tc['test_case_id']}"
            
print(f"All {len(data)} test cases passed schema validation!")
