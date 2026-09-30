"""
Master Fixture Generator: Builds all 275 named YAML fixtures (Sections 5, 6, 7, 8, 9, 10).
Outputs to both fixtures/formula/ and f11/fixtures/formula/.
Every fixture contains full output row:
L, D, R, Sc, C, COGS, S, G, E, O, P, P_upper, margin, class, band, lane,
component_tags, measured_share, flags, drivers, top_loss_driver, delta_profit.
"""

import os
import yaml
import itertools
from decimal import Decimal
from typing import Dict, Any, List

from f11.reference.reference_formula import evaluate_order_reference

TARGET_DIRS = ["fixtures/formula", "f11/fixtures/formula"]
for d in TARGET_DIRS:
    os.makedirs(d, exist_ok=True)


def save_fixture(fixture_dict: Dict[str, Any]):
    f_id = fixture_dict["id"]
    for d in TARGET_DIRS:
        f_path = os.path.join(d, f"{f_id}.yaml")
        with open(f_path, "w", encoding="utf-8") as f:
            yaml.dump(fixture_dict, f, sort_keys=False, default_flow_style=False)


# Load config profiles for reference cross-check
def load_cfg(path: str):
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

configs = {
    "balanced": load_cfg("f11/config/profiles/balanced.yaml"),
    "strict": load_cfg("f11/config/profiles/strict.yaml"),
    "lenient": load_cfg("f11/config/profiles/lenient.yaml"),
}
configs["balanced"]["packaging_cost"] = 0
configs["half_even"] = dict(configs["balanced"], rounding_mode="half_even")

# 1. Import scenario groups
from f11.fixtures.group_a import group_a_fixtures
from f11.fixtures.group_b import group_b_fixtures
from f11.fixtures.build_formula_fixtures import c_fixtures
from f11.fixtures.group_d import group_d_fixtures
from f11.fixtures.generate_master_suite import e_fixtures

# Golden Anchors (15), Boundaries (15), Aggregations (8) from generate_anchors_and_tables
import f11.fixtures.generate_anchors_and_tables as gat

master_list: List[Dict[str, Any]] = []

# Groups A - E
master_list.extend(group_a_fixtures) # 18
master_list.extend(group_b_fixtures) # 15
master_list.extend(c_fixtures)        # 18
master_list.extend(group_d_fixtures) # 22
master_list.extend(e_fixtures)        # 20

# Golden Anchors (15), Boundaries (15), Aggregations (8)
anchors_and_tables = [f for f in gat.fixtures if not f["id"].startswith("LANE_")]
master_list.extend(anchors_and_tables)

print(f"Loaded {len(master_list)} base fixtures (Groups A-E, Anchors, Boundaries, Aggregations).")

# 2. Generate 144 Exhaustive Lane Truth Table fixtures (LANE_001 to LANE_144)
cogs_opts = ["complete", "missing"] # 2
s_opts = ["measured", "structural", "estimated", "missing"] # 4
g_opts = ["measured", "structural", "estimated", "missing"] # 4
e_opts = ["realized", "provision"] # 2

lane_cases = []
count = 0

# Set 1: Positive P_upper (64 cases)
for cogs, s, g, e in itertools.product(cogs_opts, s_opts, g_opts, e_opts):
    count += 1
    fid = f"LANE_{count:03d}"
    lane_cases.append((fid, cogs, s, g, e, "positive"))

# Set 2: Negative P_upper (CONFIRMED_LOSS) (64 cases where reachable)
for cogs, s, g, e in itertools.product(cogs_opts, s_opts, g_opts, e_opts):
    if count >= 128:
        break
    # Skip the 4 unreachable combinations where no cost is measured or structural
    if cogs == "missing" and s in ["estimated", "missing"] and g in ["estimated", "missing"] and e == "provision":
        continue
    count += 1
    fid = f"LANE_{count:03d}"
    lane_cases.append((fid, cogs, s, g, e, "negative"))

# Set 3: Zero P_upper boundary cases (16 cases)
for cogs, s, g, e in itertools.product(cogs_opts, s_opts, g_opts, e_opts):
    if count >= 144:
        break
    if cogs == "missing" and s in ["estimated", "missing"] and g in ["estimated", "missing"] and e == "provision":
        continue
    count += 1
    fid = f"LANE_{count:03d}"
    lane_cases.append((fid, cogs, s, g, e, "zero"))

for fid, cogs, s, g, e, pu_target in lane_cases:
    C = 10000
    profile = "strict" if (s == "missing" or g == "missing") else "balanced"
    cfg = configs[profile]
    
    # Calculate costs based on target
    if pu_target == "positive":
        cogs_val = 3000 if cogs == "complete" else None
        s_val = 800 if s == "measured" else (0 if s == "structural" else (650 if s == "estimated" else None))
        g_val = 300 if g == "measured" else (0 if g == "structural" else (320 if g == "estimated" else None))
        e_val = 0 if e == "realized" else (800 if profile == "strict" else 500)
    elif pu_target == "negative":
        # Make measured/structural costs > C = 10000
        if cogs == "complete":
            cogs_val = 11000
            s_val = 800 if s == "measured" else (0 if s == "structural" else (650 if s == "estimated" else None))
            g_val = 300 if g == "measured" else (0 if g == "structural" else (320 if g == "estimated" else None))
            e_val = 0 if e == "realized" else (800 if profile == "strict" else 500)
        elif s == "measured":
            cogs_val = None
            s_val = 11000
            g_val = 300 if g == "measured" else (0 if g == "structural" else (320 if g == "estimated" else None))
            e_val = 0 if e == "realized" else (800 if profile == "strict" else 500)
        elif g == "measured":
            cogs_val = None
            s_val = 0 if s == "structural" else (650 if s == "estimated" else None)
            g_val = 11000
            e_val = 0 if e == "realized" else (800 if profile == "strict" else 500)
        else:
            # E is realized with refund 11000
            cogs_val = None
            s_val = 0 if s == "structural" else (650 if s == "estimated" else None)
            g_val = 0 if g == "structural" else (320 if g == "estimated" else None)
            e_val = 11000
    else: # zero
        # Make measured/structural costs == C = 10000
        if cogs == "complete":
            cogs_val = 10000 - (800 if s == "measured" else 0) - (300 if g == "measured" else 0)
            s_val = 800 if s == "measured" else (0 if s == "structural" else (650 if s == "estimated" else None))
            g_val = 300 if g == "measured" else (0 if g == "structural" else (320 if g == "estimated" else None))
            e_val = 0 if e == "realized" else (800 if profile == "strict" else 500)
        elif s == "measured":
            cogs_val = None
            s_val = 10000 - (300 if g == "measured" else 0)
            g_val = 300 if g == "measured" else (0 if g == "structural" else (320 if g == "estimated" else None))
            e_val = 0 if e == "realized" else (800 if profile == "strict" else 500)
        elif g == "measured":
            cogs_val = None
            s_val = 0 if s == "structural" else (650 if s == "estimated" else None)
            g_val = 10000
            e_val = 0 if e == "realized" else (800 if profile == "strict" else 500)
        else:
            cogs_val = None
            s_val = 0 if s == "structural" else (650 if s == "estimated" else None)
            g_val = 0 if g == "structural" else (320 if g == "estimated" else None)
            e_val = 10000

    # Packaging O
    o_val = 200 if (profile == "strict" and s != "structural") else 0

    # Input order payload
    txns = []
    gw_names = []
    if g == "measured":
        txns = [{"id": "T1", "gateway": "shopify_payments", "fees": [{"amount": {"amount": f"{g_val/100:.2f}", "currencyCode": "USD"}}]}]
    elif g == "structural":
        gw_names = ["manual"]
        txns = [{"id": "T1", "gateway": "manual"}]
    elif g == "estimated":
        txns = [{"id": "T1", "gateway": "paypal"}]
    else:
        txns = [{"id": "T1", "gateway": "paypal"}] # profile is strict, no schedule -> missing

    refs = []
    if e == "realized" and e_val > 0:
        refs = [{
            "id": f"R_{fid}", "createdAt": "2026-08-10T12:00:00Z",
            "totalRefundedSet": {"shopMoney": {"amount": f"{e_val/100:.2f}", "currencyCode": "USD"}},
            "refundLineItems": []
        }]

    proc_dt = "2026-08-01T12:00:00Z" if e == "realized" else "2026-09-20T12:00:00Z"
    act_carrier = f"{s_val/100:.2f}" if s == "measured" else None
    unit_cost_str = f"{cogs_val/100:.2f}" if cogs == "complete" else None
    
    tags = ["pickup"] if s == "structural" else []

    input_order = {
        "id": f"gid://shopify/Order/{fid}", "name": f"#{fid}", "currencyCode": "USD", "processedAt": proc_dt,
        "tags": tags,
        "currentShippingPriceSet": {"shopMoney": {"amount": "0.00", "currencyCode": "USD"}},
        "actual_carrier_cost": act_carrier,
        "paymentGatewayNames": gw_names,
        "lineItems": [{
            "id": "L1", "quantity": 1, "currentQuantity": 1, "requiresShipping": (s != "structural"),
            "originalUnitPriceSet": {"shopMoney": {"amount": "100.00", "currencyCode": "USD"}},
            "variant": {"id": "V1", "inventoryItem": {"unitCost": {"amount": unit_cost_str, "currencyCode": "USD"} if unit_cost_str else None}}
        }],
        "transactions": txns,
        "refunds": refs
    }

    # Derive expected strictly from Reference Implementation independently verified
    ref_out = evaluate_order_reference(input_order, cfg)
    
    def sanitize_val(v, key=""):
        if isinstance(v, Decimal):
            if key == "measured_share":
                return str(v)
            return float(v)
        elif isinstance(v, dict):
            return {k: sanitize_val(val, k) for k, val in v.items()}
        elif isinstance(v, list):
            return [sanitize_val(item) for item in v]
        return v

    ref_dict = sanitize_val(ref_out.to_dict())
    if "measured_share" in ref_dict and ref_dict["measured_share"] is not None:
        ref_dict["measured_share"] = str(ref_dict["measured_share"])
    if "margin" in ref_dict and ref_dict["margin"] is not None:
        ref_dict["margin"] = float(ref_dict["margin"])

    master_list.append({
        "id": fid,
        "purpose": f"Lane Truth Table #{len(master_list)+1}: COGS={cogs}, S={s}, G={g}, E={e}, P_upper_sign={pu_target} -> Lane={ref_out.lane}.",
        "profile": profile, "spec_ref": "8.0", "tag": "CFG",
        "arithmetic_derivation": f"C={C}, actual P_upper={ref_out.P_upper} ({pu_target}). Evaluated strictly per Section 3.3 truth table as {ref_out.lane}.",
        "input": input_order,
        "expected": ref_dict
    })

# Save all fixtures
for f in master_list:
    save_fixture(f)

print(f"Total fixtures saved: {len(master_list)}")
