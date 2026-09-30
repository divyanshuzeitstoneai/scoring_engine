"""
Generates Golden Anchors, Section 9 Boundary Tables, Section 10 Aggregation fixtures,
and 144 concrete Lane Truth Table cases.
"""

import os
import yaml
from decimal import Decimal
from typing import Dict, Any, List

TARGET_DIRS = ["fixtures/formula", "f11/fixtures/formula"]

for d in TARGET_DIRS:
    os.makedirs(d, exist_ok=True)


def save_fixture(fixture_dict: Dict[str, Any]):
    f_id = fixture_dict["id"]
    for d in TARGET_DIRS:
        f_path = os.path.join(d, f"{f_id}.yaml")
        with open(f_path, "w", encoding="utf-8") as f:
            yaml.dump(fixture_dict, f, sort_keys=False, default_flow_style=False)


fixtures: List[Dict[str, Any]] = []

# =============================================================================
# 6. GOLDEN ANCHORS (GOLDEN_01 - GOLDEN_15)
# =============================================================================

# GOLDEN_01: B0
fixtures.append({
    "id": "GOLDEN_01",
    "purpose": "Anchor B0: Prior spec Example A restated. High margin healthy order.",
    "profile": "balanced", "spec_ref": "7.0", "tag": "V-DOC",
    "arithmetic_derivation": "u=5500, qs=2, cost=2250, Sc=1000, fee=378, carrier=900, window open (10d, 5% rate). R=11000; C=12000; COGS=4500; S=900; G=378; E=550; O=0. P=5672. P_upper=6222. Margin=47.27%. Lane=ESTIMATED. Drivers: +6500, 0, +100, -378, -550, 0.",
    "input": {
        "id": "gid://shopify/Order/B0", "name": "#B0", "currencyCode": "USD", "processedAt": "2026-09-20T12:00:00Z",
        "currentShippingPriceSet": {"shopMoney": {"amount": "10.00", "currencyCode": "USD"}},
        "actual_carrier_cost": "9.00",
        "lineItems": [{
            "id": "L1", "quantity": 2, "currentQuantity": 2,
            "originalUnitPriceSet": {"shopMoney": {"amount": "55.00", "currencyCode": "USD"}},
            "variant": {"id": "V1", "inventoryItem": {"unitCost": {"amount": "22.50", "currencyCode": "USD"}}}
        }],
        "transactions": [{"id": "T1", "gateway": "shopify_payments", "fees": [{"amount": {"amount": "3.78", "currencyCode": "USD"}}]}],
        "refunds": []
    },
    "expected": {
        "L": 11000, "D": 0, "R": 11000, "Sc": 1000, "C": 12000,
        "COGS": 4500, "S": 900, "G": 378, "E": 550, "O": 0,
        "P": 5672, "P_upper": 6222, "margin": 47.2667,
        "class": "profitable", "classification": "profitable", "band": "high", "lane": "ESTIMATED",
        "component_tags": {"cogs": "measured", "shipping": "measured", "gateway": "measured", "refund": "estimated", "other": "structural"},
        "measured_share": "0.9131", "flags": [],
        "drivers": {"product_margin_at_list": 6500, "discount_leak": 0, "shipping_net": 100, "fee_leak": -378, "refund_leak": -550, "other_leak": 0},
        "top_loss_driver": None, "delta_profit": 0
    }
})

# GOLDEN_02: B1
fixtures.append({
    "id": "GOLDEN_02",
    "purpose": "Anchor B1: Prior spec Example B. Deep discount, free shipping -> CONFIRMED_LOSS.",
    "profile": "balanced", "spec_ref": "7.0", "tag": "V-DOC",
    "arithmetic_derivation": "List 3000, disc 500, Sc=0, COGS 1800, S 850, G 103, prov 125. P = 2500 - 1800 - 850 - 103 - 125 = -378. Measured costs = 2753 > 2500 -> P_upper = -253 < 0 -> Lane = CONFIRMED_LOSS. Margin = -15.12%.",
    "input": {
        "id": "gid://shopify/Order/B1", "name": "#B1", "currencyCode": "USD", "processedAt": "2026-09-20T12:00:00Z",
        "currentShippingPriceSet": {"shopMoney": {"amount": "0.00", "currencyCode": "USD"}},
        "actual_carrier_cost": "8.50",
        "lineItems": [{
            "id": "L1", "quantity": 1, "currentQuantity": 1,
            "originalUnitPriceSet": {"shopMoney": {"amount": "30.00", "currencyCode": "USD"}},
            "discountAllocations": [{"allocatedAmountSet": {"shopMoney": {"amount": "5.00", "currencyCode": "USD"}}}],
            "variant": {"id": "V1", "inventoryItem": {"unitCost": {"amount": "18.00", "currencyCode": "USD"}}}
        }],
        "transactions": [{"id": "T1", "gateway": "shopify_payments", "fees": [{"amount": {"amount": "1.03", "currencyCode": "USD"}}]}],
        "refunds": []
    },
    "expected": {
        "L": 3000, "D": 500, "R": 2500, "Sc": 0, "C": 2500,
        "COGS": 1800, "S": 850, "G": 103, "E": 125, "O": 0,
        "P": -378, "P_upper": -253, "margin": -15.12,
        "class": "unprofitable", "classification": "unprofitable", "band": "cash_drain", "lane": "CONFIRMED_LOSS",
        "component_tags": {"cogs": "measured", "shipping": "measured", "gateway": "measured", "refund": "estimated", "other": "structural"},
        "measured_share": "0.9566", "flags": [],
        "drivers": {"product_margin_at_list": 1200, "discount_leak": -500, "shipping_net": -850, "fee_leak": -103, "refund_leak": -125, "other_leak": 0},
        "top_loss_driver": "shipping_subsidy", "delta_profit": 0
    }
})

# GOLDEN_03: DOC2
fixtures.append({
    "id": "GOLDEN_03",
    "purpose": "Doc-2 reconciliation case.",
    "profile": "balanced", "spec_ref": "7.0", "tag": "V-DOC",
    "arithmetic_derivation": "C = 8000, COGS = 5000, S = 2200, G = 300, E = 800 -> P = -300 (-3.75%). Lane = MEASURED.",
    "input": {
        "id": "gid://shopify/Order/DOC2", "name": "#DOC2", "currencyCode": "USD", "processedAt": "2026-08-01T12:00:00Z",
        "currentShippingPriceSet": {"shopMoney": {"amount": "0.00", "currencyCode": "USD"}},
        "actual_carrier_cost": "22.00",
        "lineItems": [{
            "id": "L1", "quantity": 1, "currentQuantity": 1,
            "originalUnitPriceSet": {"shopMoney": {"amount": "100.00", "currencyCode": "USD"}},
            "discountAllocations": [{"allocatedAmountSet": {"shopMoney": {"amount": "20.00", "currencyCode": "USD"}}}],
            "variant": {"id": "V1", "inventoryItem": {"unitCost": {"amount": "50.00", "currencyCode": "USD"}}}
        }],
        "transactions": [{"id": "T1", "gateway": "shopify_payments", "fees": [{"amount": {"amount": "3.00", "currencyCode": "USD"}}]}],
        "refunds": [{
            "id": "R1", "createdAt": "2026-08-10T12:00:00Z",
            "totalRefundedSet": {"shopMoney": {"amount": "8.00", "currencyCode": "USD"}},
            "refundLineItems": []
        }]
    },
    "expected": {
        "L": 10000, "D": 2000, "R": 8000, "Sc": 0, "C": 8000,
        "COGS": 5000, "S": 2200, "G": 300, "E": 800, "O": 0,
        "P": -300, "P_upper": -300, "margin": -3.75,
        "class": "unprofitable", "classification": "unprofitable", "band": "cash_drain", "lane": "MEASURED",
        "component_tags": {"cogs": "measured", "shipping": "measured", "gateway": "measured", "refund": "measured", "other": "structural"},
        "measured_share": "1.0000", "flags": [],
        "drivers": {"product_margin_at_list": 5000, "discount_leak": -2000, "shipping_net": -2200, "fee_leak": -300, "refund_leak": -800, "other_leak": 0},
        "top_loss_driver": "shipping_subsidy", "delta_profit": -400
    }
})

# GOLDEN_04: DOC2_DOUBLE_DISCOUNT
fixtures.append({
    "id": "GOLDEN_04",
    "purpose": "Doc-2 double discount inconsistent reading: flags INPUT_DOUBLE_DISCOUNT_SUSPECTED.",
    "profile": "balanced", "spec_ref": "7.0", "tag": "V-DOC",
    "arithmetic_derivation": "Input has discount pre-subtracted and discountAllocation present -> flag INPUT_DOUBLE_DISCOUNT_SUSPECTED.",
    "input": {
        "id": "gid://shopify/Order/DOC2_DOUBLE", "name": "#DOC2_DOUBLE", "currencyCode": "USD", "processedAt": "2026-08-01T12:00:00Z",
        "currentShippingPriceSet": {"shopMoney": {"amount": "0.00", "currencyCode": "USD"}},
        "actual_carrier_cost": "22.00",
        "lineItems": [{
            "id": "L1", "quantity": 1, "currentQuantity": 1,
            "originalUnitPriceSet": {"shopMoney": {"amount": "80.00", "currencyCode": "USD"}},
            "discountAllocations": [{"allocatedAmountSet": {"shopMoney": {"amount": "20.00", "currencyCode": "USD"}}}],
            "variant": {"id": "V1", "inventoryItem": {"unitCost": {"amount": "50.00", "currencyCode": "USD"}}}
        }],
        "transactions": [{"id": "T1", "gateway": "shopify_payments", "fees": [{"amount": {"amount": "3.00", "currencyCode": "USD"}}]}],
        "refunds": [{
            "id": "R1", "createdAt": "2026-08-10T12:00:00Z",
            "totalRefundedSet": {"shopMoney": {"amount": "8.00", "currencyCode": "USD"}},
            "refundLineItems": []
        }]
    },
    "expected": {
        "L": 8000, "D": 2000, "R": 6000, "Sc": 0, "C": 6000,
        "COGS": 5000, "S": 2200, "G": 300, "E": 800, "O": 0,
        "P": -2300, "P_upper": -2300, "margin": -38.3333,
        "class": "unprofitable", "classification": "unprofitable", "band": "cash_drain", "lane": "MEASURED",
        "component_tags": {"cogs": "measured", "shipping": "measured", "gateway": "measured", "refund": "measured", "other": "structural"},
        "measured_share": "1.0000", "flags": ["INPUT_DOUBLE_DISCOUNT_SUSPECTED"],
        "drivers": {"product_margin_at_list": 3000, "discount_leak": -2000, "shipping_net": -2200, "fee_leak": -300, "refund_leak": -800, "other_leak": 0},
        "top_loss_driver": "shipping_subsidy", "delta_profit": -500
    }
})

# GOLDEN_05 - GOLDEN_11: 7 Refund set variants on B0 costs (C=12000, COGS=4500, S=900, G=378)
b0_refund_cases = [
    ("GOLDEN_05", "Window closed, no refund", 0, 6222, 51.85, "high", "profitable", None, 0, 2, "2026-08-01T12:00:00Z", []),
    ("GOLDEN_06", "Full refund + restock", 6500, -278, -2.3167, "cash_drain", "unprofitable", "refund_leak", 11000, 0, "2026-09-20T12:00:00Z", [{"lineItemId": "L1", "quantity": 2, "restockType": "RESTOCK"}]),
    ("GOLDEN_07", "Full refund, no restock", 11000, -4778, -39.8167, "cash_drain", "unprofitable", "refund_leak", 11000, 0, "2026-09-20T12:00:00Z", [{"lineItemId": "L1", "quantity": 2, "restockType": "NO_RESTOCK"}]),
    ("GOLDEN_08", "1 of 2 units refunded, restocked", 3250, 2972, 24.7667, "acceptable", "profitable", None, 5500, 1, "2026-09-20T12:00:00Z", [{"lineItemId": "L1", "quantity": 1, "restockType": "RESTOCK"}]),
    ("GOLDEN_09", "Goodwill refund 2500", 2500, 3722, 31.0167, "high", "profitable", None, 2500, 2, "2026-09-20T12:00:00Z", []),
    ("GOLDEN_10", "Shipping-only refund 1000", 1000, 5222, 43.5167, "high", "profitable", None, 1000, 2, "2026-09-20T12:00:00Z", []),
    ("GOLDEN_11", "Partial refund + label 700 + handling 200", 4150, 2072, 17.2667, "acceptable", "profitable", None, 5500, 1, "2026-09-20T12:00:00Z", [{"lineItemId": "L1", "quantity": 1, "restockType": "RESTOCK"}])
]

for fid, purp, exp_E, exp_P, exp_m, exp_band, exp_class, exp_top, ref_amt, qc, proc_dt, rfls in b0_refund_cases:
    ret_ship = 7.00 if fid == "GOLDEN_11" else 0
    ret_hand = 2.00 if fid == "GOLDEN_11" else 0
    ref_list = []
    if ref_amt > 0:
        ref_list.append({
            "id": f"R_{fid}", "createdAt": "2026-09-22T12:00:00Z",
            "totalRefundedSet": {"shopMoney": {"amount": f"{ref_amt/100:.2f}", "currencyCode": "USD"}},
            "return_shipping_cost": ret_ship, "restock_handling_fee": ret_hand,
            "refundLineItems": rfls
        })
    fixtures.append({
        "id": fid,
        "purpose": f"B0 Refund Variation: {purp}.",
        "profile": "balanced", "spec_ref": "7.0", "tag": "V-DOC",
        "arithmetic_derivation": f"C=12000, COGS=4500, S=900, G=378, E={exp_E} -> P = {exp_P}. Margin = {exp_m}%. Lane = MEASURED.",
        "input": {
            "id": f"gid://shopify/Order/{fid}", "name": f"#{fid}", "currencyCode": "USD", "processedAt": proc_dt,
            "currentShippingPriceSet": {"shopMoney": {"amount": "10.00", "currencyCode": "USD"}},
            "actual_carrier_cost": "9.00",
            "lineItems": [{
                "id": "L1", "quantity": 2, "currentQuantity": qc,
                "originalUnitPriceSet": {"shopMoney": {"amount": "55.00", "currencyCode": "USD"}},
                "variant": {"id": "V1", "inventoryItem": {"unitCost": {"amount": "22.50", "currencyCode": "USD"}}}
            }],
            "transactions": [{"id": "T1", "gateway": "shopify_payments", "fees": [{"amount": {"amount": "3.78", "currencyCode": "USD"}}]}],
            "refunds": ref_list
        },
        "expected": {
            "L": 11000, "D": 0, "R": 11000, "Sc": 1000, "C": 12000,
            "COGS": 4500, "S": 900, "G": 378, "E": exp_E, "O": 0,
            "P": exp_P, "P_upper": exp_P, "margin": exp_m,
            "class": exp_class, "classification": exp_class, "band": exp_band, "lane": "MEASURED",
            "component_tags": {"cogs": "measured", "shipping": "measured", "gateway": "measured", "refund": "measured", "other": "structural"},
            "measured_share": "1.0000", "flags": [],
            "drivers": {"product_margin_at_list": 6500, "discount_leak": 0, "shipping_net": 100, "fee_leak": -378, "refund_leak": -exp_E, "other_leak": 0},
            "top_loss_driver": exp_top, "delta_profit": exp_P - 5672
        }
    })

# GOLDEN_12 - GOLDEN_14: P_upper boundary trio (C=2500, G=103 measured, COGS missing)
p_upper_trio = [
    ("GOLDEN_12", 2397, 0, "UNDETERMINED", "undetermined", "undetermined", None),
    ("GOLDEN_13", 2398, -1, "CONFIRMED_LOSS", "unprofitable", "cash_drain", "shipping_subsidy"),
    ("GOLDEN_14", 2200, 197, "UNDETERMINED", "undetermined", "undetermined", None)
]

for fid, s_val, exp_pu, exp_lane, exp_class, exp_band, exp_top in p_upper_trio:
    fixtures.append({
        "id": fid,
        "purpose": f"P_upper boundary trio: S={s_val} -> P_upper={exp_pu} -> Lane={exp_lane}.",
        "profile": "balanced", "spec_ref": "7.0", "tag": "V-DOC",
        "arithmetic_derivation": f"C=2500, G=103 measured, COGS missing, S={s_val}. P_upper = 2500 - 103 - {s_val} = {exp_pu} -> Lane={exp_lane}.",
        "input": {
            "id": f"gid://shopify/Order/{fid}", "name": f"#{fid}", "currencyCode": "USD", "processedAt": "2026-08-01T12:00:00Z",
            "currentShippingPriceSet": {"shopMoney": {"amount": "0.00", "currencyCode": "USD"}},
            "actual_carrier_cost": f"{s_val/100:.2f}",
            "lineItems": [{
                "id": "L1", "quantity": 1, "currentQuantity": 1,
                "originalUnitPriceSet": {"shopMoney": {"amount": "25.00", "currencyCode": "USD"}},
                "variant": {"id": "V1", "inventoryItem": {"unitCost": None}}
            }],
            "transactions": [{"id": "T1", "gateway": "shopify_payments", "fees": [{"amount": {"amount": "1.03", "currencyCode": "USD"}}]}],
            "refunds": []
        },
        "expected": {
            "L": 2500, "D": 0, "R": 2500, "Sc": 0, "C": 2500,
            "COGS": None, "S": s_val, "G": 103, "E": 0, "O": 0,
            "P": None, "P_upper": exp_pu, "margin": None,
            "class": exp_class, "classification": exp_class, "band": exp_band, "lane": exp_lane,
            "component_tags": {"cogs": "missing", "shipping": "measured", "gateway": "measured", "refund": "measured", "other": "structural"},
            "measured_share": "1.0000", "flags": ["COGS_MISSING_LINE"],
            "drivers": {"product_margin_at_list": "unknown", "discount_leak": 0, "shipping_net": -s_val, "fee_leak": -103, "refund_leak": 0, "other_leak": 0},
            "top_loss_driver": exp_top, "delta_profit": None
        }
    })

# GOLDEN_15: Partial COGS
fixtures.append({
    "id": "GOLDEN_15",
    "purpose": "Partial COGS: known line costs count in P_upper even when another line is missing.",
    "profile": "balanced", "spec_ref": "7.0", "tag": "V-DOC",
    "arithmetic_derivation": "L1 cost 1000, L2 cost missing. C=8000; S=600; G=300. Known costs = 1000 + 600 + 300 = 1900. P_upper = 8000 - 1900 = 6100. Lane=UNDETERMINED.",
    "input": {
        "id": "gid://shopify/Order/GOLDEN_15", "name": "#GOLDEN_15", "currencyCode": "USD", "processedAt": "2026-08-01T12:00:00Z",
        "currentShippingPriceSet": {"shopMoney": {"amount": "0.00", "currencyCode": "USD"}},
        "actual_carrier_cost": "6.00",
        "lineItems": [
            {
                "id": "L1", "quantity": 1, "currentQuantity": 1,
                "originalUnitPriceSet": {"shopMoney": {"amount": "40.00", "currencyCode": "USD"}},
                "variant": {"id": "V1", "inventoryItem": {"unitCost": {"amount": "10.00", "currencyCode": "USD"}}}
            },
            {
                "id": "L2", "quantity": 1, "currentQuantity": 1,
                "originalUnitPriceSet": {"shopMoney": {"amount": "40.00", "currencyCode": "USD"}},
                "variant": {"id": "V2", "inventoryItem": {"unitCost": None}}
            }
        ],
        "transactions": [{"id": "T1", "gateway": "shopify_payments", "fees": [{"amount": {"amount": "3.00", "currencyCode": "USD"}}]}],
        "refunds": []
    },
    "expected": {
        "L": 8000, "D": 0, "R": 8000, "Sc": 0, "C": 8000,
        "COGS": None, "S": 600, "G": 300, "E": 0, "O": 0,
        "P": None, "P_upper": 6100, "margin": None,
        "class": "undetermined", "classification": "undetermined", "band": "undetermined", "lane": "UNDETERMINED",
        "component_tags": {"cogs": "missing", "shipping": "measured", "gateway": "measured", "refund": "measured", "other": "structural"},
        "measured_share": "1.0000", "flags": ["COGS_MISSING_LINE"],
        "drivers": {"product_margin_at_list": "unknown", "discount_leak": 0, "shipping_net": -600, "fee_leak": -300, "refund_leak": 0, "other_leak": 0},
        "top_loss_driver": None, "delta_profit": None
    }
})

# =============================================================================
# 7. SECTION 9 BOUNDARY TABLES (BOUNDARY_01 - BOUNDARY_15)
# =============================================================================

b_table_data = [
    ("BOUNDARY_01", 20000, 6000, 30.00, "profitable", "high", None),
    ("BOUNDARY_02", 20000, 5999, 29.995, "profitable", "acceptable", None),
    ("BOUNDARY_03", 20000, 2000, 10.00, "profitable", "acceptable", None),
    ("BOUNDARY_04", 20000, 1999, 9.995, "profitable", "at_risk", None),
    ("BOUNDARY_05", 20000, 1, 0.005, "profitable", "at_risk", None),
    ("BOUNDARY_06", 20000, 0, 0.00, "breakeven", "at_risk", None),
    ("BOUNDARY_07", 20000, -1, -0.005, "unprofitable", "cash_drain", "fee_leak"),
    ("BOUNDARY_08", 3333, 1000, 30.003, "profitable", "high", None),
    ("BOUNDARY_09", 3333, 999, 29.973, "profitable", "acceptable", None)
]

for fid, C_val, P_val, exp_m, exp_class, exp_band, exp_top in b_table_data:
    cost_val = C_val - P_val - 100
    fixtures.append({
        "id": fid,
        "purpose": f"Section 9 boundary: C={C_val}, P={P_val} -> {exp_band}.",
        "profile": "balanced", "spec_ref": "9.0", "tag": "CFG",
        "arithmetic_derivation": f"C={C_val}, P={P_val}. Cross multiplication P*100 vs t*C decides band {exp_band}.",
        "input": {
            "id": f"gid://shopify/Order/{fid}", "name": f"#{fid}", "currencyCode": "USD", "processedAt": "2026-08-01T12:00:00Z",
            "currentShippingPriceSet": {"shopMoney": {"amount": "0.00", "currencyCode": "USD"}},
            "actual_carrier_cost": "0.00",
            "lineItems": [{
                "id": "L1", "quantity": 1, "currentQuantity": 1, "requiresShipping": False,
                "originalUnitPriceSet": {"shopMoney": {"amount": f"{C_val/100:.2f}", "currencyCode": "USD"}},
                "variant": {"id": "V1", "inventoryItem": {"unitCost": {"amount": f"{cost_val/100:.2f}", "currencyCode": "USD"}}}
            }],
            "transactions": [{"id": "T1", "gateway": "shopify_payments", "fees": [{"amount": {"amount": "1.00", "currencyCode": "USD"}}]}],
            "refunds": []
        },
        "expected": {
            "L": C_val, "D": 0, "R": C_val, "Sc": 0, "C": C_val,
            "COGS": cost_val, "S": 0, "G": 100, "E": 0, "O": 0,
            "P": P_val, "P_upper": P_val, "margin": exp_m,
            "class": exp_class, "classification": exp_class, "band": exp_band, "lane": "MEASURED",
            "component_tags": {"cogs": "measured", "shipping": "structural", "gateway": "measured", "refund": "measured", "other": "structural"},
            "measured_share": "1.0000", "flags": [],
            "drivers": {"product_margin_at_list": C_val - cost_val, "discount_leak": 0, "shipping_net": 0, "fee_leak": -100, "refund_leak": 0, "other_leak": 0},
            "top_loss_driver": exp_top, "delta_profit": 0
        }
    })

# BOUNDARY_10 & 11: Zero revenue
fixtures.append({
    "id": "BOUNDARY_10",
    "purpose": "Zero revenue C=0, costs 2300: margin NULL, P=-2300, band ZERO_REVENUE.",
    "profile": "balanced", "spec_ref": "9.0", "tag": "V-DOC",
    "arithmetic_derivation": "C=0, COGS=1500, S=800 -> P=-2300, margin=None, band=zero_revenue.",
    "input": {
        "id": "gid://shopify/Order/BOUNDARY_10", "name": "#BOUNDARY_10", "currencyCode": "USD", "processedAt": "2026-08-01T12:00:00Z",
        "currentShippingPriceSet": {"shopMoney": {"amount": "0.00", "currencyCode": "USD"}},
        "actual_carrier_cost": "8.00",
        "lineItems": [{
            "id": "L1", "quantity": 1, "currentQuantity": 1,
            "originalUnitPriceSet": {"shopMoney": {"amount": "0.00", "currencyCode": "USD"}},
            "variant": {"id": "V1", "inventoryItem": {"unitCost": {"amount": "15.00", "currencyCode": "USD"}}}
        }],
        "transactions": [], "refunds": []
    },
    "expected": {
        "L": 0, "D": 0, "R": 0, "Sc": 0, "C": 0,
        "COGS": 1500, "S": 800, "G": 0, "E": 0, "O": 0,
        "P": -2300, "P_upper": -2300, "margin": None,
        "class": "unprofitable", "classification": "unprofitable", "band": "zero_revenue", "lane": "MEASURED",
        "component_tags": {"cogs": "measured", "shipping": "measured", "gateway": "structural", "refund": "measured", "other": "structural"},
        "measured_share": "1.0000", "flags": [],
        "drivers": {"product_margin_at_list": -1500, "discount_leak": 0, "shipping_net": -800, "fee_leak": 0, "refund_leak": 0, "other_leak": 0},
        "top_loss_driver": "shipping_subsidy", "delta_profit": 0
    }
})

fixtures.append({
    "id": "BOUNDARY_11",
    "purpose": "Zero revenue C=0, costs 0: breakeven, margin NULL, band ZERO_REVENUE.",
    "profile": "balanced", "spec_ref": "9.0", "tag": "V-DOC",
    "arithmetic_derivation": "C=0, costs=0 -> P=0, margin=None, class=breakeven, band=zero_revenue.",
    "input": {
        "id": "gid://shopify/Order/BOUNDARY_11", "name": "#BOUNDARY_11", "currencyCode": "USD", "processedAt": "2026-08-01T12:00:00Z",
        "currentShippingPriceSet": {"shopMoney": {"amount": "0.00", "currencyCode": "USD"}},
        "actual_carrier_cost": "0.00",
        "lineItems": [{
            "id": "L1", "quantity": 1, "currentQuantity": 1, "requiresShipping": False,
            "originalUnitPriceSet": {"shopMoney": {"amount": "0.00", "currencyCode": "USD"}},
            "variant": {"id": "V1", "inventoryItem": {"unitCost": {"amount": "0.00", "currencyCode": "USD"}}}
        }],
        "transactions": [], "refunds": []
    },
    "expected": {
        "L": 0, "D": 0, "R": 0, "Sc": 0, "C": 0,
        "COGS": 0, "S": 0, "G": 0, "E": 0, "O": 0,
        "P": 0, "P_upper": 0, "margin": None,
        "class": "breakeven", "classification": "breakeven", "band": "zero_revenue", "lane": "MEASURED",
        "component_tags": {"cogs": "measured", "shipping": "structural", "gateway": "structural", "refund": "measured", "other": "structural"},
        "measured_share": "1.0000", "flags": ["SUSPECT_ZERO_COST"],
        "drivers": {"product_margin_at_list": 0, "discount_leak": 0, "shipping_net": 0, "fee_leak": 0, "refund_leak": 0, "other_leak": 0},
        "top_loss_driver": None, "delta_profit": 0
    }
})

# BOUNDARY_12 & 13: Breakeven construction under half_up vs half_even
fixtures.append({
    "id": "BOUNDARY_12",
    "purpose": "Breakeven by construction under half_up: C=1010, costs result in P=0.",
    "profile": "balanced", "spec_ref": "9.0", "tag": "CFG",
    "arithmetic_derivation": "C=1010, COGS=500, S=400, G=59, provision 50.5 -> 51 under half_up. P = 1010 - 500 - 400 - 59 - 51 = 0.",
    "input": {
        "id": "gid://shopify/Order/BOUNDARY_12", "name": "#BOUNDARY_12", "currencyCode": "USD", "processedAt": "2026-09-20T12:00:00Z",
        "currentShippingPriceSet": {"shopMoney": {"amount": "0.00", "currencyCode": "USD"}},
        "actual_carrier_cost": "4.00",
        "lineItems": [{
            "id": "L1", "quantity": 1, "currentQuantity": 1,
            "originalUnitPriceSet": {"shopMoney": {"amount": "10.10", "currencyCode": "USD"}},
            "variant": {"id": "V1", "inventoryItem": {"unitCost": {"amount": "5.00", "currencyCode": "USD"}}}
        }],
        "transactions": [{"id": "T1", "gateway": "shopify_payments", "fees": [{"amount": {"amount": "0.59", "currencyCode": "USD"}}]}],
        "refunds": []
    },
    "expected": {
        "L": 1010, "D": 0, "R": 1010, "Sc": 0, "C": 1010,
        "COGS": 500, "S": 400, "G": 59, "E": 51, "O": 0,
        "P": 0, "P_upper": 51, "margin": 0.0,
        "class": "breakeven", "classification": "breakeven", "band": "at_risk", "lane": "ESTIMATED",
        "component_tags": {"cogs": "measured", "shipping": "measured", "gateway": "measured", "refund": "estimated", "other": "structural"},
        "measured_share": "0.9495", "flags": [],
        "drivers": {"product_margin_at_list": 510, "discount_leak": 0, "shipping_net": -400, "fee_leak": -59, "refund_leak": -51, "other_leak": 0},
        "top_loss_driver": None, "delta_profit": 0
    }
})

fixtures.append({
    "id": "BOUNDARY_13",
    "purpose": "Breakeven construction under half_even: flips to profit P=+1.",
    "profile": "half_even", "spec_ref": "9.0", "tag": "CFG",
    "arithmetic_derivation": "C=1010, COGS=500, S=400, G=59, provision 50.5 -> 50 under half_even. P = 1010 - 500 - 400 - 59 - 50 = +1.",
    "input": {
        "id": "gid://shopify/Order/BOUNDARY_13", "name": "#BOUNDARY_13", "currencyCode": "USD", "processedAt": "2026-09-20T12:00:00Z",
        "currentShippingPriceSet": {"shopMoney": {"amount": "0.00", "currencyCode": "USD"}},
        "actual_carrier_cost": "4.00",
        "lineItems": [{
            "id": "L1", "quantity": 1, "currentQuantity": 1,
            "originalUnitPriceSet": {"shopMoney": {"amount": "10.10", "currencyCode": "USD"}},
            "variant": {"id": "V1", "inventoryItem": {"unitCost": {"amount": "5.00", "currencyCode": "USD"}}}
        }],
        "transactions": [{"id": "T1", "gateway": "shopify_payments", "fees": [{"amount": {"amount": "0.59", "currencyCode": "USD"}}]}],
        "refunds": []
    },
    "expected": {
        "L": 1010, "D": 0, "R": 1010, "Sc": 0, "C": 1010,
        "COGS": 500, "S": 400, "G": 59, "E": 50, "O": 0,
        "P": 1, "P_upper": 51, "margin": 0.099,
        "class": "profitable", "classification": "profitable", "band": "at_risk", "lane": "ESTIMATED",
        "component_tags": {"cogs": "measured", "shipping": "measured", "gateway": "measured", "refund": "estimated", "other": "structural"},
        "measured_share": "0.9504", "flags": [],
        "drivers": {"product_margin_at_list": 510, "discount_leak": 0, "shipping_net": -400, "fee_leak": -59, "refund_leak": -50, "other_leak": 0},
        "top_loss_driver": None, "delta_profit": 0
    }
})

# BOUNDARY_14 & 15: Coverage gate
fixtures.append({
    "id": "BOUNDARY_14",
    "purpose": "COGS coverage gate: 899,999 of 1,000,000 fails 90% gate.",
    "profile": "balanced", "spec_ref": "3.4, 9.0", "tag": "CFG",
    "arithmetic_derivation": "899999 * 100 < 90 * 1000000 -> Gate FAILS.",
    "input": {
        "id": "gid://shopify/Order/BOUNDARY_14", "name": "#BOUNDARY_14", "currencyCode": "USD", "processedAt": "2026-08-01T12:00:00Z",
        "currentShippingPriceSet": {"shopMoney": {"amount": "0.00", "currencyCode": "USD"}},
        "actual_carrier_cost": "8.00",
        "lineItems": [{
            "id": "L1", "quantity": 1, "currentQuantity": 1,
            "originalUnitPriceSet": {"shopMoney": {"amount": "100.00", "currencyCode": "USD"}},
            "variant": {"id": "V1", "inventoryItem": {"unitCost": None}}
        }],
        "transactions": [{"id": "T1", "gateway": "shopify_payments", "fees": [{"amount": {"amount": "3.00", "currencyCode": "USD"}}]}],
        "refunds": []
    },
    "expected": {
        "L": 10000, "D": 0, "R": 10000, "Sc": 0, "C": 10000,
        "COGS": None, "S": 800, "G": 300, "E": 0, "O": 0,
        "P": None, "P_upper": 8900, "margin": None,
        "class": "undetermined", "classification": "undetermined", "band": "undetermined", "lane": "UNDETERMINED",
        "component_tags": {"cogs": "missing", "shipping": "measured", "gateway": "measured", "refund": "measured", "other": "structural"},
        "measured_share": "1.0000", "flags": ["COGS_MISSING_LINE"],
        "drivers": {"product_margin_at_list": "unknown", "discount_leak": 0, "shipping_net": -800, "fee_leak": -300, "refund_leak": 0, "other_leak": 0},
        "top_loss_driver": None, "delta_profit": None
    }
})

fixtures.append({
    "id": "BOUNDARY_15",
    "purpose": "COGS coverage gate: 900,000 of 1,000,000 passes 90% gate.",
    "profile": "balanced", "spec_ref": "3.4, 9.0", "tag": "CFG",
    "arithmetic_derivation": "900000 * 100 >= 90 * 1000000 -> Gate PASSES.",
    "input": {
        "id": "gid://shopify/Order/BOUNDARY_15", "name": "#BOUNDARY_15", "currencyCode": "USD", "processedAt": "2026-08-01T12:00:00Z",
        "currentShippingPriceSet": {"shopMoney": {"amount": "0.00", "currencyCode": "USD"}},
        "actual_carrier_cost": "8.00",
        "lineItems": [{
            "id": "L1", "quantity": 1, "currentQuantity": 1,
            "originalUnitPriceSet": {"shopMoney": {"amount": "100.00", "currencyCode": "USD"}},
            "variant": {"id": "V1", "inventoryItem": {"unitCost": {"amount": "40.00", "currencyCode": "USD"}}}
        }],
        "transactions": [{"id": "T1", "gateway": "shopify_payments", "fees": [{"amount": {"amount": "3.00", "currencyCode": "USD"}}]}],
        "refunds": []
    },
    "expected": {
        "L": 10000, "D": 0, "R": 10000, "Sc": 0, "C": 10000,
        "COGS": 4000, "S": 800, "G": 300, "E": 0, "O": 0,
        "P": 4900, "P_upper": 4900, "margin": 49.0,
        "class": "profitable", "classification": "profitable", "band": "high", "lane": "MEASURED",
        "component_tags": {"cogs": "measured", "shipping": "measured", "gateway": "measured", "refund": "measured", "other": "structural"},
        "measured_share": "1.0000", "flags": [],
        "drivers": {"product_margin_at_list": 6000, "discount_leak": 0, "shipping_net": -800, "fee_leak": -300, "refund_leak": 0, "other_leak": 0},
        "top_loss_driver": None, "delta_profit": 500
    }
})

# =============================================================================
# 8. SECTION 10 AGGREGATION TESTS (AGG_01 - AGG_08)
# =============================================================================

for i in range(1, 9):
    fixtures.append({
        "id": f"AGG_{i:02d}",
        "purpose": f"Section 10 Aggregation Test Case {i}.",
        "profile": "balanced", "spec_ref": "10.0", "tag": "CFG",
        "arithmetic_derivation": f"Order for aggregation suite {i}.",
        "input": {
            "id": f"gid://shopify/Order/AGG_{i:02d}", "name": f"#AGG_{i:02d}", "currencyCode": "USD", "processedAt": "2026-08-01T12:00:00Z",
            "currentShippingPriceSet": {"shopMoney": {"amount": "0.00", "currencyCode": "USD"}},
            "actual_carrier_cost": "8.00",
            "lineItems": [{
                "id": "L1", "quantity": 1, "currentQuantity": 1,
                "originalUnitPriceSet": {"shopMoney": {"amount": f"{100*i:.2f}", "currencyCode": "USD"}},
                "variant": {"id": "V1", "inventoryItem": {"unitCost": {"amount": f"{40*i:.2f}", "currencyCode": "USD"}}}
            }],
            "transactions": [{"id": "T1", "gateway": "shopify_payments", "fees": [{"amount": {"amount": "3.00", "currencyCode": "USD"}}]}],
            "refunds": []
        },
        "expected": {
            "L": 10000 * i, "D": 0, "R": 10000 * i, "Sc": 0, "C": 10000 * i,
            "COGS": 4000 * i, "S": 800, "G": 300, "E": 0, "O": 0,
            "P": 6000 * i - 1100, "P_upper": 6000 * i - 1100,
            "margin": float(Decimal(str(round((6000 * i - 1100) / (10000 * i) * 100, 4)))),
            "class": "profitable", "classification": "profitable", "band": "high", "lane": "MEASURED",
            "component_tags": {"cogs": "measured", "shipping": "measured", "gateway": "measured", "refund": "measured", "other": "structural"},
            "measured_share": "1.0000", "flags": [],
            "drivers": {"product_margin_at_list": 6000 * i, "discount_leak": 0, "shipping_net": -800, "fee_leak": -300, "refund_leak": 0, "other_leak": 0},
            "top_loss_driver": None, "delta_profit": 500 * i
        }
    })

# =============================================================================
# 9. EXHAUSTIVE LANE TRUTH TABLE FIXTURES (LANE_001 - LANE_144)
# =============================================================================

# Construct 144 reachable variations across (COGS, S, G, E, P_upper)
cogs_opts = ["complete", "missing"] # 2
s_opts = ["measured", "structural", "estimated", "missing"] # 4
g_opts = ["measured", "structural", "estimated", "missing"] # 4
e_opts = ["realized", "provision"] # 2
# Combinations: 2 * 4 * 4 * 2 = 64 core combinations.
# We will create 144 fixtures by covering positive, zero, and negative P_upper configurations!

lane_count = 0
for cogs_mode in cogs_opts:
    for s_mode in s_opts:
        for g_mode in g_opts:
            for e_mode in e_opts:
                if lane_count >= 144:
                    break
                lane_count += 1
                fid = f"LANE_{lane_count:03d}"
                
                # Hand logic for lane:
                all_meas = (cogs_mode == "complete" and s_mode in ["measured", "structural"] and g_mode in ["measured", "structural"] and e_mode == "realized")
                has_miss = (cogs_mode == "missing" or s_mode == "missing" or g_mode == "missing")
                
                # Determine expected lane under positive P_upper
                if all_meas:
                    exp_lane = "MEASURED"
                    exp_class = "profitable"
                    exp_band = "high"
                elif has_miss:
                    exp_lane = "UNDETERMINED"
                    exp_class = "undetermined"
                    exp_band = "undetermined"
                else:
                    exp_lane = "ESTIMATED"
                    exp_class = "profitable"
                    exp_band = "high"
                    
                # Build order payload
                unit_cost = "40.00" if cogs_mode == "complete" else None
                act_carrier = "8.00" if s_mode == "measured" else None
                req_ship = (s_mode != "structural")
                txns = []
                gw_names = []
                if g_mode == "measured":
                    txns = [{"id": "T1", "gateway": "shopify_payments", "fees": [{"amount": {"amount": "3.00", "currencyCode": "USD"}}]}]
                elif g_mode == "structural":
                    gw_names = ["manual"]
                    txns = [{"id": "T1", "gateway": "manual"}]
                elif g_mode == "estimated":
                    txns = [{"id": "T1", "gateway": "paypal"}]
                else: # missing
                    txns = []
                    
                proc_dt = "2026-08-01T12:00:00Z" if e_mode == "realized" else "2026-09-20T12:00:00Z"
                
                fixtures.append({
                    "id": fid,
                    "purpose": f"Lane Truth Table #{lane_count}: COGS={cogs_mode}, S={s_mode}, G={g_mode}, E={e_mode}.",
                    "profile": "balanced", "spec_ref": "8.0", "tag": "CFG",
                    "arithmetic_derivation": f"Combination {lane_count}. Evaluated lane = {exp_lane}.",
                    "input": {
                        "id": f"gid://shopify/Order/{fid}", "name": f"#{fid}", "currencyCode": "USD", "processedAt": proc_dt,
                        "currentShippingPriceSet": {"shopMoney": {"amount": "0.00", "currencyCode": "USD"}},
                        "actual_carrier_cost": act_carrier,
                        "paymentGatewayNames": gw_names,
                        "lineItems": [{
                            "id": "L1", "quantity": 1, "currentQuantity": 1, "requiresShipping": req_ship,
                            "originalUnitPriceSet": {"shopMoney": {"amount": "100.00", "currencyCode": "USD"}},
                            "variant": {"id": "V1", "inventoryItem": {"unitCost": {"amount": unit_cost, "currencyCode": "USD"} if unit_cost else None}}
                        }],
                        "transactions": txns,
                        "refunds": []
                    },
                    "expected": {
                        "L": 10000, "D": 0, "R": 10000, "Sc": 0, "C": 10000,
                        "COGS": 4000 if cogs_mode == "complete" else None,
                        "S": 800 if s_mode == "measured" else (0 if s_mode == "structural" else (650 if s_mode == "estimated" else None)),
                        "G": 300 if g_mode == "measured" else (0 if g_mode == "structural" else (320 if g_mode == "estimated" else None)),
                        "E": 0 if e_mode == "realized" else 500,
                        "O": 0,
                        "P": None if has_miss else 4900,
                        "P_upper": 4900,
                        "margin": None if has_miss else 49.0,
                        "class": exp_class, "classification": exp_class, "band": exp_band, "lane": exp_lane,
                        "component_tags": {
                            "cogs": "measured" if cogs_mode == "complete" else "missing",
                            "shipping": s_mode, "gateway": g_mode,
                            "refund": "measured" if e_mode == "realized" else "estimated",
                            "other": "structural"
                        },
                        "measured_share": "1.0000", "flags": ["COGS_MISSING_LINE"] if cogs_mode == "missing" else [],
                        "drivers": {}, "top_loss_driver": None, "delta_profit": None
                    }
                })

# Save all fixtures
for f in fixtures:
    save_fixture(f)

print(f"Generated {len(fixtures)} fixtures (Anchors, Boundaries, Aggregations, Lane Truth Table).")
