import json

import os
p = "f03/data/test_fixtures.json"
if not os.path.exists(p):
    p = os.path.join(os.path.dirname(__file__), "..", "data", "test_fixtures.json")
if not os.path.exists(p):
    p = "scratch/test_fixtures.json"

with open(p, "r", encoding="utf-8") as f:
    fixtures = json.load(f)

print(f"Total fixtures: {len(fixtures)}")
for i, tc in enumerate(fixtures, 1):
    tc_id = tc["test_case_id"]
    payload = tc["shopify_order_payload"]
    curr = payload.get("currencyCode", "NONE")
    exp = tc["expected_result"]
    breach = exp.get("f03_breach")
    loss = exp.get("f03_loss")
    print(f"{i:2d}. {tc_id:45s} | curr: {curr:4s} | breach: {str(breach):5s} | loss: {loss}")
