"""
Appends Group E, Golden Anchors, Boundaries, Aggregation, and Lane Truth Table fixtures.
Total fixtures generated: 275 files.
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


# =============================================================================
# 5. GROUP E: EXCLUSIONS, ZEROES & BOUNDARIES (E01 - E20)
# =============================================================================

e_fixtures = [
    {
        "id": "E01",
        "purpose": "Cancelled before fulfillment: excluded order.",
        "profile": "balanced", "spec_ref": "3.3", "tag": "V-DOC",
        "arithmetic_derivation": "cancelledAt is set and fulfillment status is unfulfilled -> excluded: CANCELLED.",
        "input": {
            "id": "gid://shopify/Order/E01", "name": "#E01", "currencyCode": "USD", "cancelledAt": "2026-08-01T14:00:00Z",
            "displayFulfillmentStatus": "UNFULFILLED",
            "lineItems": [{"id": "L1", "quantity": 1, "originalUnitPriceSet": {"shopMoney": {"amount": "50.00", "currencyCode": "USD"}}}]
        },
        "expected": {
            "L": 0, "D": 0, "R": 0, "Sc": 0, "C": 0, "COGS": 0, "S": 0, "G": 0, "E": 0, "O": 0,
            "P": 0, "P_upper": 0, "margin": None, "class": "excluded", "classification": "excluded", "band": "excluded", "lane": "EXCLUDED",
            "exclusion_reason": "CANCELLED", "component_tags": {"cogs": "structural", "shipping": "structural", "gateway": "structural", "refund": "structural", "other": "structural"},
            "measured_share": "1.0000", "flags": [], "drivers": {}, "top_loss_driver": None, "delta_profit": None
        }
    },
    {
        "id": "E02",
        "purpose": "Cancelled after fulfillment under include_with_refunds policy: evaluated normally.",
        "profile": "balanced", "spec_ref": "3.3", "tag": "CFG",
        "arithmetic_derivation": "cancelledAt is set, displayFulfillmentStatus='FULFILLED', policy=include_with_refunds -> evaluated normally. P=4900.",
        "input": {
            "id": "gid://shopify/Order/E02", "name": "#E02", "currencyCode": "USD", "cancelledAt": "2026-08-05T14:00:00Z",
            "processedAt": "2026-08-01T12:00:00Z", "displayFulfillmentStatus": "FULFILLED",
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
    },
    {
        "id": "E03",
        "purpose": "Cancelled after fulfillment under exclude policy (strict profile): excluded.",
        "profile": "strict", "spec_ref": "3.3", "tag": "CFG",
        "arithmetic_derivation": "cancelledAt set, policy=exclude -> excluded: CANCELLED.",
        "input": {
            "id": "gid://shopify/Order/E03", "name": "#E03", "currencyCode": "USD", "cancelledAt": "2026-08-05T14:00:00Z",
            "displayFulfillmentStatus": "FULFILLED",
            "lineItems": [{"id": "L1", "quantity": 1, "originalUnitPriceSet": {"shopMoney": {"amount": "100.00", "currencyCode": "USD"}}}]
        },
        "expected": {
            "L": 0, "D": 0, "R": 0, "Sc": 0, "C": 0, "COGS": 0, "S": 0, "G": 0, "E": 0, "O": 0,
            "P": 0, "P_upper": 0, "margin": None, "class": "excluded", "classification": "excluded", "band": "excluded", "lane": "EXCLUDED",
            "exclusion_reason": "CANCELLED", "component_tags": {"cogs": "structural", "shipping": "structural", "gateway": "structural", "refund": "structural", "other": "structural"},
            "measured_share": "1.0000", "flags": [], "drivers": {}, "top_loss_driver": None, "delta_profit": None
        }
    },
    {
        "id": "E04",
        "purpose": "Authorized-only order: financial status AUTHORIZED -> excluded.",
        "profile": "balanced", "spec_ref": "3.3", "tag": "V-DOC",
        "arithmetic_derivation": "displayFinancialStatus='AUTHORIZED' -> excluded: FINANCIAL_STATUS_AUTHORIZED.",
        "input": {
            "id": "gid://shopify/Order/E04", "name": "#E04", "currencyCode": "USD", "displayFinancialStatus": "AUTHORIZED",
            "lineItems": [{"id": "L1", "quantity": 1, "originalUnitPriceSet": {"shopMoney": {"amount": "100.00", "currencyCode": "USD"}}}]
        },
        "expected": {
            "L": 0, "D": 0, "R": 0, "Sc": 0, "C": 0, "COGS": 0, "S": 0, "G": 0, "E": 0, "O": 0,
            "P": 0, "P_upper": 0, "margin": None, "class": "excluded", "classification": "excluded", "band": "excluded", "lane": "EXCLUDED",
            "exclusion_reason": "FINANCIAL_STATUS_AUTHORIZED", "component_tags": {"cogs": "structural", "shipping": "structural", "gateway": "structural", "refund": "structural", "other": "structural"},
            "measured_share": "1.0000", "flags": [], "drivers": {}, "top_loss_driver": None, "delta_profit": None
        }
    },
    {
        "id": "E05",
        "purpose": "Pending order: financial status PENDING -> excluded.",
        "profile": "balanced", "spec_ref": "3.3", "tag": "V-DOC",
        "arithmetic_derivation": "displayFinancialStatus='PENDING' -> excluded: FINANCIAL_STATUS_PENDING.",
        "input": {
            "id": "gid://shopify/Order/E05", "name": "#E05", "currencyCode": "USD", "displayFinancialStatus": "PENDING",
            "lineItems": [{"id": "L1", "quantity": 1, "originalUnitPriceSet": {"shopMoney": {"amount": "100.00", "currencyCode": "USD"}}}]
        },
        "expected": {
            "L": 0, "D": 0, "R": 0, "Sc": 0, "C": 0, "COGS": 0, "S": 0, "G": 0, "E": 0, "O": 0,
            "P": 0, "P_upper": 0, "margin": None, "class": "excluded", "classification": "excluded", "band": "excluded", "lane": "EXCLUDED",
            "exclusion_reason": "FINANCIAL_STATUS_PENDING", "component_tags": {"cogs": "structural", "shipping": "structural", "gateway": "structural", "refund": "structural", "other": "structural"},
            "measured_share": "1.0000", "flags": [], "drivers": {}, "top_loss_driver": None, "delta_profit": None
        }
    },
    {
        "id": "E06",
        "purpose": "Voided order: financial status VOIDED -> excluded.",
        "profile": "balanced", "spec_ref": "3.3", "tag": "V-DOC",
        "arithmetic_derivation": "displayFinancialStatus='VOIDED' -> excluded: FINANCIAL_STATUS_VOIDED.",
        "input": {
            "id": "gid://shopify/Order/E06", "name": "#E06", "currencyCode": "USD", "displayFinancialStatus": "VOIDED",
            "lineItems": [{"id": "L1", "quantity": 1, "originalUnitPriceSet": {"shopMoney": {"amount": "100.00", "currencyCode": "USD"}}}]
        },
        "expected": {
            "L": 0, "D": 0, "R": 0, "Sc": 0, "C": 0, "COGS": 0, "S": 0, "G": 0, "E": 0, "O": 0,
            "P": 0, "P_upper": 0, "margin": None, "class": "excluded", "classification": "excluded", "band": "excluded", "lane": "EXCLUDED",
            "exclusion_reason": "FINANCIAL_STATUS_VOIDED", "component_tags": {"cogs": "structural", "shipping": "structural", "gateway": "structural", "refund": "structural", "other": "structural"},
            "measured_share": "1.0000", "flags": [], "drivers": {}, "top_loss_driver": None, "delta_profit": None
        }
    },
    {
        "id": "E07",
        "purpose": "Test order: test=True -> excluded: TEST_ORDER.",
        "profile": "balanced", "spec_ref": "3.3", "tag": "V-DOC",
        "arithmetic_derivation": "test=True -> excluded: TEST_ORDER.",
        "input": {
            "id": "gid://shopify/Order/E07", "name": "#E07", "currencyCode": "USD", "test": True,
            "lineItems": [{"id": "L1", "quantity": 1, "originalUnitPriceSet": {"shopMoney": {"amount": "100.00", "currencyCode": "USD"}}}]
        },
        "expected": {
            "L": 0, "D": 0, "R": 0, "Sc": 0, "C": 0, "COGS": 0, "S": 0, "G": 0, "E": 0, "O": 0,
            "P": 0, "P_upper": 0, "margin": None, "class": "excluded", "classification": "excluded", "band": "excluded", "lane": "EXCLUDED",
            "exclusion_reason": "TEST_ORDER", "component_tags": {"cogs": "structural", "shipping": "structural", "gateway": "structural", "refund": "structural", "other": "structural"},
            "measured_share": "1.0000", "flags": [], "drivers": {}, "top_loss_driver": None, "delta_profit": None
        }
    },
    {
        "id": "E08",
        "purpose": "Partially paid order: evaluated per configuration policy.",
        "profile": "balanced", "spec_ref": "3.3", "tag": "CFG",
        "arithmetic_derivation": "displayFinancialStatus='PARTIALLY_PAID' is not in excluded statuses -> evaluated normally. P=4900.",
        "input": {
            "id": "gid://shopify/Order/E08", "name": "#E08", "currencyCode": "USD", "displayFinancialStatus": "PARTIALLY_PAID",
            "processedAt": "2026-08-01T12:00:00Z",
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
    },
    {
        "id": "E09",
        "purpose": "Zero-collected (100% promo) with costs: C=0, P=-2300, margin NULL, band ZERO_REVENUE.",
        "profile": "balanced", "spec_ref": "3.4", "tag": "V-DOC",
        "arithmetic_derivation": "C = 0. COGS = 1500; S = 800; G = 0; E = 0; O = 0. P = -2300. margin = None, band = zero_revenue, unprofitable.",
        "input": {
            "id": "gid://shopify/Order/E09", "name": "#E09", "currencyCode": "USD", "processedAt": "2026-08-01T12:00:00Z",
            "currentShippingPriceSet": {"shopMoney": {"amount": "0.00", "currencyCode": "USD"}},
            "actual_carrier_cost": "8.00",
            "lineItems": [{
                "id": "L1", "quantity": 1, "currentQuantity": 1,
                "originalUnitPriceSet": {"shopMoney": {"amount": "20.00", "currencyCode": "USD"}},
                "discountAllocations": [{"allocatedAmountSet": {"shopMoney": {"amount": "20.00", "currencyCode": "USD"}}}],
                "variant": {"id": "V1", "inventoryItem": {"unitCost": {"amount": "15.00", "currencyCode": "USD"}}}
            }],
            "transactions": [], "refunds": []
        },
        "expected": {
            "L": 2000, "D": 2000, "R": 0, "Sc": 0, "C": 0,
            "COGS": 1500, "S": 800, "G": 0, "E": 0, "O": 0,
            "P": -2300, "P_upper": -2300, "margin": None,
            "class": "unprofitable", "classification": "unprofitable", "band": "zero_revenue", "lane": "MEASURED",
            "component_tags": {"cogs": "measured", "shipping": "measured", "gateway": "structural", "refund": "measured", "other": "structural"},
            "measured_share": "1.0000", "flags": [],
            "drivers": {"product_margin_at_list": 500, "discount_leak": -2000, "shipping_net": -800, "fee_leak": 0, "refund_leak": 0, "other_leak": 0},
            "top_loss_driver": "discount_leak", "delta_profit": 0
        }
    },
    {
        "id": "E10",
        "purpose": "Zero-collected with zero costs: C=0, P=0, breakeven, margin NULL, band ZERO_REVENUE.",
        "profile": "balanced", "spec_ref": "3.4", "tag": "V-DOC",
        "arithmetic_derivation": "C = 0, all costs 0. P = 0. is_zero_revenue = True, margin = None, band = zero_revenue, class = breakeven.",
        "input": {
            "id": "gid://shopify/Order/E10", "name": "#E10", "currencyCode": "USD", "processedAt": "2026-08-01T12:00:00Z",
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
    },
    {
        "id": "E11",
        "purpose": "Exact breakeven by construction: P = 0, class breakeven, band at_risk.",
        "profile": "balanced", "spec_ref": "3.4", "tag": "V-DOC",
        "arithmetic_derivation": "C = 1000; COGS = 500; S = 400; G = 100; E = 0; O = 0. P = 1000 - 500 - 400 - 100 = 0. Margin = 0.00%. Class = breakeven, band = at_risk.",
        "input": {
            "id": "gid://shopify/Order/E11", "name": "#E11", "currencyCode": "USD", "processedAt": "2026-08-01T12:00:00Z",
            "currentShippingPriceSet": {"shopMoney": {"amount": "0.00", "currencyCode": "USD"}},
            "actual_carrier_cost": "4.00",
            "lineItems": [{
                "id": "L1", "quantity": 1, "currentQuantity": 1,
                "originalUnitPriceSet": {"shopMoney": {"amount": "10.00", "currencyCode": "USD"}},
                "variant": {"id": "V1", "inventoryItem": {"unitCost": {"amount": "5.00", "currencyCode": "USD"}}}
            }],
            "transactions": [{"id": "T1", "gateway": "shopify_payments", "fees": [{"amount": {"amount": "1.00", "currencyCode": "USD"}}]}],
            "refunds": []
        },
        "expected": {
            "L": 1000, "D": 0, "R": 1000, "Sc": 0, "C": 1000,
            "COGS": 500, "S": 400, "G": 100, "E": 0, "O": 0,
            "P": 0, "P_upper": 0, "margin": 0.0,
            "class": "breakeven", "classification": "breakeven", "band": "at_risk", "lane": "MEASURED",
            "component_tags": {"cogs": "measured", "shipping": "measured", "gateway": "measured", "refund": "measured", "other": "structural"},
            "measured_share": "1.0000", "flags": [],
            "drivers": {"product_margin_at_list": 500, "discount_leak": 0, "shipping_net": -400, "fee_leak": -100, "refund_leak": 0, "other_leak": 0},
            "top_loss_driver": None, "delta_profit": 50
        }
    },
    {
        "id": "E12",
        "purpose": "Breakeven flipping to profit under half_even: P = +1.",
        "profile": "half_even", "spec_ref": "3.4", "tag": "CFG",
        "arithmetic_derivation": "C = 1010, COGS = 500, S = 400, G = 59, provision = 50.5 -> 50 (half_even). P = 1010 - 500 - 400 - 59 - 50 = +1. Margin = 0.0990% -> 0.10%, class = profitable, band = at_risk.",
        "input": {
            "id": "gid://shopify/Order/E12", "name": "#E12", "currencyCode": "USD", "processedAt": "2026-09-20T12:00:00Z",
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
            "measured_share": "0.9505", "flags": [],
            "drivers": {"product_margin_at_list": 510, "discount_leak": 0, "shipping_net": -400, "fee_leak": -59, "refund_leak": -50, "other_leak": 0},
            "top_loss_driver": None, "delta_profit": 0
        }
    },
    {
        "id": "E13",
        "purpose": "Smallest profit (+1 minor unit): C=10001, costs=10000 -> P=+1.",
        "profile": "balanced", "spec_ref": "3.4", "tag": "V-DOC",
        "arithmetic_derivation": "C = 10001, COGS = 5000, S = 4000, G = 1000. P = 1. Margin = 0.00999% -> 0.01% (at_risk).",
        "input": {
            "id": "gid://shopify/Order/E13", "name": "#E13", "currencyCode": "USD", "processedAt": "2026-08-01T12:00:00Z",
            "currentShippingPriceSet": {"shopMoney": {"amount": "0.00", "currencyCode": "USD"}},
            "actual_carrier_cost": "40.00",
            "lineItems": [{
                "id": "L1", "quantity": 1, "currentQuantity": 1,
                "originalUnitPriceSet": {"shopMoney": {"amount": "100.01", "currencyCode": "USD"}},
                "variant": {"id": "V1", "inventoryItem": {"unitCost": {"amount": "50.00", "currencyCode": "USD"}}}
            }],
            "transactions": [{"id": "T1", "gateway": "shopify_payments", "fees": [{"amount": {"amount": "10.00", "currencyCode": "USD"}}]}],
            "refunds": []
        },
        "expected": {
            "L": 10001, "D": 0, "R": 10001, "Sc": 0, "C": 10001,
            "COGS": 5000, "S": 4000, "G": 1000, "E": 0, "O": 0,
            "P": 1, "P_upper": 1, "margin": 0.01,
            "class": "profitable", "classification": "profitable", "band": "at_risk", "lane": "MEASURED",
            "component_tags": {"cogs": "measured", "shipping": "measured", "gateway": "measured", "refund": "measured", "other": "structural"},
            "measured_share": "1.0000", "flags": [],
            "drivers": {"product_margin_at_list": 5001, "discount_leak": 0, "shipping_net": -4000, "fee_leak": -1000, "refund_leak": 0, "other_leak": 0},
            "top_loss_driver": None, "delta_profit": 500
        }
    },
    {
        "id": "E14",
        "purpose": "Smallest loss (-1 minor unit): C=10000, costs=10001 -> P=-1.",
        "profile": "balanced", "spec_ref": "3.4", "tag": "V-DOC",
        "arithmetic_derivation": "C = 10000, COGS = 5000, S = 4000, G = 1001. P = -1. Margin = -0.01% (cash_drain).",
        "input": {
            "id": "gid://shopify/Order/E14", "name": "#E14", "currencyCode": "USD", "processedAt": "2026-08-01T12:00:00Z",
            "currentShippingPriceSet": {"shopMoney": {"amount": "0.00", "currencyCode": "USD"}},
            "actual_carrier_cost": "40.00",
            "lineItems": [{
                "id": "L1", "quantity": 1, "currentQuantity": 1,
                "originalUnitPriceSet": {"shopMoney": {"amount": "100.00", "currencyCode": "USD"}},
                "variant": {"id": "V1", "inventoryItem": {"unitCost": {"amount": "50.00", "currencyCode": "USD"}}}
            }],
            "transactions": [{"id": "T1", "gateway": "shopify_payments", "fees": [{"amount": {"amount": "10.01", "currencyCode": "USD"}}]}],
            "refunds": []
        },
        "expected": {
            "L": 10000, "D": 0, "R": 10000, "Sc": 0, "C": 10000,
            "COGS": 5000, "S": 4000, "G": 1001, "E": 0, "O": 0,
            "P": -1, "P_upper": -1, "margin": -0.01,
            "class": "unprofitable", "classification": "unprofitable", "band": "cash_drain", "lane": "MEASURED",
            "component_tags": {"cogs": "measured", "shipping": "measured", "gateway": "measured", "refund": "measured", "other": "structural"},
            "measured_share": "1.0000", "flags": [],
            "drivers": {"product_margin_at_list": 5000, "discount_leak": 0, "shipping_net": -4000, "fee_leak": -1001, "refund_leak": 0, "other_leak": 0},
            "top_loss_driver": "shipping_subsidy", "delta_profit": 500
        }
    },
    {
        "id": "E15",
        "purpose": "Duplicate order emitted twice: evaluated once idempotently.",
        "profile": "balanced", "spec_ref": "3.3", "tag": "V-DOC",
        "arithmetic_derivation": "Evaluated once with exact values.",
        "input": {
            "id": "gid://shopify/Order/E15", "name": "#E15", "currencyCode": "USD", "processedAt": "2026-08-01T12:00:00Z",
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
    },
    {
        "id": "E16",
        "purpose": "Duplicate line id in order payload: lines deduped.",
        "profile": "balanced", "spec_ref": "3.1", "tag": "V-DOC",
        "arithmetic_derivation": "Order contains single unique line L1. L=10000; COGS=4000. P=4900.",
        "input": {
            "id": "gid://shopify/Order/E16", "name": "#E16", "currencyCode": "USD", "processedAt": "2026-08-01T12:00:00Z",
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
    },
    {
        "id": "E17",
        "purpose": "Two lines with different ids and identical content: both preserved.",
        "profile": "balanced", "spec_ref": "3.1", "tag": "V-DOC",
        "arithmetic_derivation": "L1 and L2 are distinct lines with identical attributes. L = 20000; COGS = 8000. P = 10600. Margin = 53.00% (high).",
        "input": {
            "id": "gid://shopify/Order/E17", "name": "#E17", "currencyCode": "USD", "processedAt": "2026-08-01T12:00:00Z",
            "currentShippingPriceSet": {"shopMoney": {"amount": "0.00", "currencyCode": "USD"}},
            "actual_carrier_cost": "8.00",
            "lineItems": [
                {
                    "id": "L1", "quantity": 1, "currentQuantity": 1,
                    "originalUnitPriceSet": {"shopMoney": {"amount": "100.00", "currencyCode": "USD"}},
                    "variant": {"id": "V1", "inventoryItem": {"unitCost": {"amount": "40.00", "currencyCode": "USD"}}}
                },
                {
                    "id": "L2", "quantity": 1, "currentQuantity": 1,
                    "originalUnitPriceSet": {"shopMoney": {"amount": "100.00", "currencyCode": "USD"}},
                    "variant": {"id": "V1", "inventoryItem": {"unitCost": {"amount": "40.00", "currencyCode": "USD"}}}
                }
            ],
            "transactions": [{"id": "T1", "gateway": "shopify_payments", "fees": [{"amount": {"amount": "6.00", "currencyCode": "USD"}}]}],
            "refunds": []
        },
        "expected": {
            "L": 20000, "D": 0, "R": 20000, "Sc": 0, "C": 20000,
            "COGS": 8000, "S": 800, "G": 600, "E": 0, "O": 0,
            "P": 10600, "P_upper": 10600, "margin": 53.0,
            "class": "profitable", "classification": "profitable", "band": "high", "lane": "MEASURED",
            "component_tags": {"cogs": "measured", "shipping": "measured", "gateway": "measured", "refund": "measured", "other": "structural"},
            "measured_share": "1.0000", "flags": [],
            "drivers": {"product_margin_at_list": 12000, "discount_leak": 0, "shipping_net": -800, "fee_leak": -600, "refund_leak": 0, "other_leak": 0},
            "top_loss_driver": None, "delta_profit": 1000
        }
    },
    {
        "id": "E18",
        "purpose": "Multi-currency order: shopMoney used, presentmentMoney ignored.",
        "profile": "balanced", "spec_ref": "3.0", "tag": "V-DOC",
        "arithmetic_derivation": "shopMoney amount = 100.00 USD used. Presentment EUR 92.00 ignored. P=4900.",
        "input": {
            "id": "gid://shopify/Order/E18", "name": "#E18", "currencyCode": "USD", "processedAt": "2026-08-01T12:00:00Z",
            "currentShippingPriceSet": {"shopMoney": {"amount": "0.00", "currencyCode": "USD"}},
            "actual_carrier_cost": "8.00",
            "lineItems": [{
                "id": "L1", "quantity": 1, "currentQuantity": 1,
                "originalUnitPriceSet": {
                    "shopMoney": {"amount": "100.00", "currencyCode": "USD"},
                    "presentmentMoney": {"amount": "92.00", "currencyCode": "EUR"}
                },
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
    },
    {
        "id": "E19",
        "purpose": "Shop currency mismatch with config: excluded CURRENCY_MISMATCH.",
        "profile": "balanced", "spec_ref": "3.0", "tag": "V-DOC",
        "arithmetic_derivation": "Order currencyCode = 'EUR' != config shop_currency 'USD' -> excluded: CURRENCY_MISMATCH.",
        "input": {
            "id": "gid://shopify/Order/E19", "name": "#E19", "currencyCode": "EUR",
            "lineItems": [{"id": "L1", "quantity": 1, "originalUnitPriceSet": {"shopMoney": {"amount": "100.00", "currencyCode": "EUR"}}}]
        },
        "expected": {
            "L": 0, "D": 0, "R": 0, "Sc": 0, "C": 0, "COGS": 0, "S": 0, "G": 0, "E": 0, "O": 0,
            "P": 0, "P_upper": 0, "margin": None, "class": "excluded", "classification": "excluded", "band": "excluded", "lane": "EXCLUDED",
            "exclusion_reason": "CURRENCY_MISMATCH", "component_tags": {"cogs": "structural", "shipping": "structural", "gateway": "structural", "refund": "structural", "other": "structural"},
            "measured_share": "1.0000", "flags": ["CURRENCY_MISMATCH"], "drivers": {}, "top_loss_driver": None, "delta_profit": None
        }
    },
    {
        "id": "E20",
        "purpose": "Zero-decimal currency (JPY): exponent 0, no scaling.",
        "profile": "balanced", "spec_ref": "3.0", "tag": "V-DOC",
        "arithmetic_derivation": "JPY has currency_exponent = 0. Price 10000 JPY is 10000 integer units.",
        "input": {
            "id": "gid://shopify/Order/E20", "name": "#E20", "currencyCode": "USD", "processedAt": "2026-08-01T12:00:00Z",
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
    }
]

for f in e_fixtures:
    save_fixture(f)

print(f"Generated {len(e_fixtures)} Group E fixtures.")
