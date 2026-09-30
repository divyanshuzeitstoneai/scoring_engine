"""
Scenario Group B: Cost Data Quality (B01 - B15).
"""

from typing import Dict, Any, List

group_b_fixtures: List[Dict[str, Any]] = [
    {
        "id": "B01",
        "purpose": "All lines with cost: complete COGS.",
        "profile": "balanced", "spec_ref": "3.1, 3.2", "tag": "V-DOC",
        "arithmetic_derivation": "2 lines, costs 2000 and 3000 -> COGS=5000. L=10000; D=0; R=10000; Sc=0; C=10000. S=800; G=300; E=0; O=0. P=3900. Margin=39.00% (high).",
        "input": {
            "id": "gid://shopify/Order/B01", "name": "#B01", "currencyCode": "USD", "processedAt": "2026-08-01T12:00:00Z",
            "currentShippingPriceSet": {"shopMoney": {"amount": "0.00", "currencyCode": "USD"}},
            "actual_carrier_cost": "8.00",
            "lineItems": [
                {
                    "id": "L1", "quantity": 1, "currentQuantity": 1,
                    "originalUnitPriceSet": {"shopMoney": {"amount": "40.00", "currencyCode": "USD"}},
                    "variant": {"id": "V1", "inventoryItem": {"unitCost": {"amount": "20.00", "currencyCode": "USD"}}}
                },
                {
                    "id": "L2", "quantity": 1, "currentQuantity": 1,
                    "originalUnitPriceSet": {"shopMoney": {"amount": "60.00", "currencyCode": "USD"}},
                    "variant": {"id": "V2", "inventoryItem": {"unitCost": {"amount": "30.00", "currencyCode": "USD"}}}
                }
            ],
            "transactions": [{"id": "T1", "gateway": "shopify_payments", "fees": [{"amount": {"amount": "3.00", "currencyCode": "USD"}}]}],
            "refunds": []
        },
        "expected": {
            "L": 10000, "D": 0, "R": 10000, "Sc": 0, "C": 10000,
            "COGS": 5000, "S": 800, "G": 300, "E": 0, "O": 0,
            "P": 3900, "P_upper": 3900, "margin": 39.0,
            "class": "profitable", "classification": "profitable", "band": "high", "lane": "MEASURED",
            "component_tags": {"cogs": "measured", "shipping": "measured", "gateway": "measured", "refund": "measured", "other": "structural"},
            "measured_share": "1.0000", "flags": [],
            "drivers": {"product_margin_at_list": 5000, "discount_leak": 0, "shipping_net": -800, "fee_leak": -300, "refund_leak": 0, "other_leak": 0},
            "top_loss_driver": None, "delta_profit": 500
        }
    },
    {
        "id": "B02",
        "purpose": "One of many lines missing cost: quarantines COGS, retains known cost in P_upper.",
        "profile": "balanced", "spec_ref": "3.1, 3.2", "tag": "V-DOC",
        "arithmetic_derivation": "L1 cost=2000, L2 cost=None. COGS=None. C=10000; S=800; G=300. P_upper = 10000 - 2000 - 800 - 300 = 6900. Lane=UNDETERMINED.",
        "input": {
            "id": "gid://shopify/Order/B02", "name": "#B02", "currencyCode": "USD", "processedAt": "2026-08-01T12:00:00Z",
            "currentShippingPriceSet": {"shopMoney": {"amount": "0.00", "currencyCode": "USD"}},
            "actual_carrier_cost": "8.00",
            "lineItems": [
                {
                    "id": "L1", "quantity": 1, "currentQuantity": 1,
                    "originalUnitPriceSet": {"shopMoney": {"amount": "40.00", "currencyCode": "USD"}},
                    "variant": {"id": "V1", "inventoryItem": {"unitCost": {"amount": "20.00", "currencyCode": "USD"}}}
                },
                {
                    "id": "L2", "quantity": 1, "currentQuantity": 1,
                    "originalUnitPriceSet": {"shopMoney": {"amount": "60.00", "currencyCode": "USD"}},
                    "variant": {"id": "V2", "inventoryItem": {"unitCost": None}}
                }
            ],
            "transactions": [{"id": "T1", "gateway": "shopify_payments", "fees": [{"amount": {"amount": "3.00", "currencyCode": "USD"}}]}],
            "refunds": []
        },
        "expected": {
            "L": 10000, "D": 0, "R": 10000, "Sc": 0, "C": 10000,
            "COGS": None, "S": 800, "G": 300, "E": 0, "O": 0,
            "P": None, "P_upper": 6900, "margin": None,
            "class": "undetermined", "classification": "undetermined", "band": "undetermined", "lane": "UNDETERMINED",
            "component_tags": {"cogs": "missing", "shipping": "measured", "gateway": "measured", "refund": "measured", "other": "structural"},
            "measured_share": "1.0000", "flags": ["COGS_MISSING_LINE"],
            "drivers": {"product_margin_at_list": "unknown", "discount_leak": 0, "shipping_net": -800, "fee_leak": -300, "refund_leak": 0, "other_leak": 0},
            "top_loss_driver": None, "delta_profit": None
        }
    },
    {
        "id": "B03",
        "purpose": "All lines missing cost: COGS missing, P_upper headroom.",
        "profile": "balanced", "spec_ref": "3.1, 3.2", "tag": "V-DOC",
        "arithmetic_derivation": "All lines cost None. COGS=None. C=10000; S=800; G=300. P_upper = 10000 - 800 - 300 = 8900. Lane=UNDETERMINED.",
        "input": {
            "id": "gid://shopify/Order/B03", "name": "#B03", "currencyCode": "USD", "processedAt": "2026-08-01T12:00:00Z",
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
    },
    {
        "id": "B04",
        "purpose": "unitCost = 0 under measured_with_flag policy: measured with flag.",
        "profile": "balanced", "spec_ref": "3.1, 3.2", "tag": "CFG",
        "arithmetic_derivation": "policy=measured_with_flag. unitCost=0 -> COGS=0, measured. Flag SUSPECT_ZERO_COST. P = 10000 - 0 - 800 - 300 = 8900. Margin=89.00% (high). Lane=MEASURED.",
        "input": {
            "id": "gid://shopify/Order/B04", "name": "#B04", "currencyCode": "USD", "processedAt": "2026-08-01T12:00:00Z",
            "currentShippingPriceSet": {"shopMoney": {"amount": "0.00", "currencyCode": "USD"}},
            "actual_carrier_cost": "8.00",
            "lineItems": [{
                "id": "L1", "quantity": 1, "currentQuantity": 1,
                "originalUnitPriceSet": {"shopMoney": {"amount": "100.00", "currencyCode": "USD"}},
                "variant": {"id": "V1", "inventoryItem": {"unitCost": {"amount": "0.00", "currencyCode": "USD"}}}
            }],
            "transactions": [{"id": "T1", "gateway": "shopify_payments", "fees": [{"amount": {"amount": "3.00", "currencyCode": "USD"}}]}],
            "refunds": []
        },
        "expected": {
            "L": 10000, "D": 0, "R": 10000, "Sc": 0, "C": 10000,
            "COGS": 0, "S": 800, "G": 300, "E": 0, "O": 0,
            "P": 8900, "P_upper": 8900, "margin": 89.0,
            "class": "profitable", "classification": "profitable", "band": "high", "lane": "MEASURED",
            "component_tags": {"cogs": "measured", "shipping": "measured", "gateway": "measured", "refund": "measured", "other": "structural"},
            "measured_share": "1.0000", "flags": ["SUSPECT_ZERO_COST"],
            "drivers": {"product_margin_at_list": 10000, "discount_leak": 0, "shipping_net": -800, "fee_leak": -300, "refund_leak": 0, "other_leak": 0},
            "top_loss_driver": None, "delta_profit": 500
        }
    },
    {
        "id": "B05",
        "purpose": "unitCost = 0 under treat_as_missing policy (strict profile): COGS missing.",
        "profile": "strict", "spec_ref": "3.1, 3.2", "tag": "CFG",
        "arithmetic_derivation": "Strict profile (treat_as_missing): unitCost=0 is treated as missing. COGS=None. P=None, P_upper=8900. Lane=UNDETERMINED.",
        "input": {
            "id": "gid://shopify/Order/B05", "name": "#B05", "currencyCode": "USD", "processedAt": "2026-08-01T12:00:00Z",
            "currentShippingPriceSet": {"shopMoney": {"amount": "0.00", "currencyCode": "USD"}},
            "actual_carrier_cost": "8.00",
            "lineItems": [{
                "id": "L1", "quantity": 1, "currentQuantity": 1,
                "originalUnitPriceSet": {"shopMoney": {"amount": "100.00", "currencyCode": "USD"}},
                "variant": {"id": "V1", "inventoryItem": {"unitCost": {"amount": "0.00", "currencyCode": "USD"}}}
            }],
            "transactions": [{"id": "T1", "gateway": "shopify_payments", "fees": [{"amount": {"amount": "3.00", "currencyCode": "USD"}}]}],
            "refunds": []
        },
        "expected": {
            "L": 10000, "D": 0, "R": 10000, "Sc": 0, "C": 10000,
            "COGS": None, "S": 800, "G": 300, "E": 0, "O": 200,
            "P": None, "P_upper": 8700, "margin": None,
            "class": "undetermined", "classification": "undetermined", "band": "undetermined", "lane": "UNDETERMINED",
            "component_tags": {"cogs": "missing", "shipping": "measured", "gateway": "measured", "refund": "measured", "other": "measured"},
            "measured_share": "1.0000", "flags": ["SUSPECT_ZERO_COST", "COGS_MISSING_LINE"],
            "drivers": {"product_margin_at_list": "unknown", "discount_leak": 0, "shipping_net": -800, "fee_leak": -300, "refund_leak": 0, "other_leak": -200},
            "top_loss_driver": None, "delta_profit": None
        }
    },
    {
        "id": "B06",
        "purpose": "Deleted variant: variant object None -> COGS missing.",
        "profile": "balanced", "spec_ref": "3.1, 3.2", "tag": "V-DOC",
        "arithmetic_derivation": "variant=None -> cost missing. COGS=None, P=None, P_upper=8900. Lane=UNDETERMINED.",
        "input": {
            "id": "gid://shopify/Order/B06", "name": "#B06", "currencyCode": "USD", "processedAt": "2026-08-01T12:00:00Z",
            "currentShippingPriceSet": {"shopMoney": {"amount": "0.00", "currencyCode": "USD"}},
            "actual_carrier_cost": "8.00",
            "lineItems": [{
                "id": "L1", "quantity": 1, "currentQuantity": 1, "variant": None,
                "originalUnitPriceSet": {"shopMoney": {"amount": "100.00", "currencyCode": "USD"}}
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
            "measured_share": "1.0000", "flags": ["COGS_MISSING_CUSTOM_LINE"],
            "drivers": {"product_margin_at_list": "unknown", "discount_leak": 0, "shipping_net": -800, "fee_leak": -300, "refund_leak": 0, "other_leak": 0},
            "top_loss_driver": None, "delta_profit": None
        }
    },
    {
        "id": "B07",
        "purpose": "Custom line without cost: revenue included, cost missing.",
        "profile": "balanced", "spec_ref": "3.1, 3.2", "tag": "CFG",
        "arithmetic_derivation": "Custom line without variant -> cost missing. COGS=None, P=None, Lane=UNDETERMINED.",
        "input": {
            "id": "gid://shopify/Order/B07", "name": "#B07", "currencyCode": "USD", "processedAt": "2026-08-01T12:00:00Z",
            "currentShippingPriceSet": {"shopMoney": {"amount": "0.00", "currencyCode": "USD"}},
            "actual_carrier_cost": "8.00",
            "lineItems": [{
                "id": "L1", "quantity": 1, "currentQuantity": 1, "title": "Bespoke Hemming", "variant": None,
                "originalUnitPriceSet": {"shopMoney": {"amount": "30.00", "currencyCode": "USD"}}
            }],
            "transactions": [{"id": "T1", "gateway": "shopify_payments", "fees": [{"amount": {"amount": "1.00", "currencyCode": "USD"}}]}],
            "refunds": []
        },
        "expected": {
            "L": 3000, "D": 0, "R": 3000, "Sc": 0, "C": 3000,
            "COGS": None, "S": 800, "G": 100, "E": 0, "O": 0,
            "P": None, "P_upper": 2100, "margin": None,
            "class": "undetermined", "classification": "undetermined", "band": "undetermined", "lane": "UNDETERMINED",
            "component_tags": {"cogs": "missing", "shipping": "measured", "gateway": "measured", "refund": "measured", "other": "structural"},
            "measured_share": "1.0000", "flags": ["COGS_MISSING_CUSTOM_LINE"],
            "drivers": {"product_margin_at_list": "unknown", "discount_leak": 0, "shipping_net": -800, "fee_leak": -100, "refund_leak": 0, "other_leak": 0},
            "top_loss_driver": None, "delta_profit": None
        }
    },
    {
        "id": "B08",
        "purpose": "Negative unitCost: invalid input -> order excluded with reason.",
        "profile": "balanced", "spec_ref": "3.1", "tag": "V-DOC",
        "arithmetic_derivation": "unitCost = -10.00 < 0 -> INVALID_NEGATIVE_COST -> Excluded.",
        "input": {
            "id": "gid://shopify/Order/B08", "name": "#B08", "currencyCode": "USD", "processedAt": "2026-08-01T12:00:00Z",
            "lineItems": [{
                "id": "L1", "quantity": 1, "currentQuantity": 1,
                "originalUnitPriceSet": {"shopMoney": {"amount": "50.00", "currencyCode": "USD"}},
                "variant": {"id": "V1", "inventoryItem": {"unitCost": {"amount": "-10.00", "currencyCode": "USD"}}}
            }]
        },
        "expected": {
            "L": 0, "D": 0, "R": 0, "Sc": 0, "C": 0,
            "COGS": 0, "S": 0, "G": 0, "E": 0, "O": 0,
            "P": 0, "P_upper": 0, "margin": None,
            "class": "excluded", "classification": "excluded", "band": "excluded", "lane": "EXCLUDED",
            "exclusion_reason": "INVALID_COST",
            "component_tags": {"cogs": "structural", "shipping": "structural", "gateway": "structural", "refund": "structural", "other": "structural"},
            "measured_share": "1.0000", "flags": ["INVALID_COST"],
            "drivers": {}, "top_loss_driver": None, "delta_profit": None
        }
    },
    {
        "id": "B09",
        "purpose": "Cost above price: valid negative line margin, unprofitable order.",
        "profile": "balanced", "spec_ref": "3.1, 3.2", "tag": "V-DOC",
        "arithmetic_derivation": "u=2000, cost=3500. L=2000; D=0; R=2000; Sc=0; C=2000. COGS=3500; S=500; G=70; E=0; O=0. P = 2000 - 3500 - 500 - 70 = -2070. Margin = -103.50% (cash drain).",
        "input": {
            "id": "gid://shopify/Order/B09", "name": "#B09", "currencyCode": "USD", "processedAt": "2026-08-01T12:00:00Z",
            "currentShippingPriceSet": {"shopMoney": {"amount": "0.00", "currencyCode": "USD"}},
            "actual_carrier_cost": "5.00",
            "lineItems": [{
                "id": "L1", "quantity": 1, "currentQuantity": 1,
                "originalUnitPriceSet": {"shopMoney": {"amount": "20.00", "currencyCode": "USD"}},
                "variant": {"id": "V1", "inventoryItem": {"unitCost": {"amount": "35.00", "currencyCode": "USD"}}}
            }],
            "transactions": [{"id": "T1", "gateway": "shopify_payments", "fees": [{"amount": {"amount": "0.70", "currencyCode": "USD"}}]}],
            "refunds": []
        },
        "expected": {
            "L": 2000, "D": 0, "R": 2000, "Sc": 0, "C": 2000,
            "COGS": 3500, "S": 500, "G": 70, "E": 0, "O": 0,
            "P": -2070, "P_upper": -2070, "margin": -103.5,
            "class": "unprofitable", "classification": "unprofitable", "band": "cash_drain", "lane": "MEASURED",
            "component_tags": {"cogs": "measured", "shipping": "measured", "gateway": "measured", "refund": "measured", "other": "structural"},
            "measured_share": "1.0000", "flags": [],
            "drivers": {"product_margin_at_list": -1500, "discount_leak": 0, "shipping_net": -500, "fee_leak": -70, "refund_leak": 0, "other_leak": 0},
            "top_loss_driver": "shipping_subsidy", "delta_profit": 100
        }
    },
    {
        "id": "B10",
        "purpose": "Cost in different currency from shop: flagged CURRENCY_MISMATCH_COST.",
        "profile": "balanced", "spec_ref": "3.1", "tag": "UNV",
        "arithmetic_derivation": "Shop USD, variant inventoryItem in EUR -> flagged CURRENCY_MISMATCH_COST.",
        "input": {
            "id": "gid://shopify/Order/B10", "name": "#B10", "currencyCode": "USD", "processedAt": "2026-08-01T12:00:00Z",
            "currentShippingPriceSet": {"shopMoney": {"amount": "0.00", "currencyCode": "USD"}},
            "actual_carrier_cost": "5.00",
            "lineItems": [{
                "id": "L1", "quantity": 1, "currentQuantity": 1,
                "originalUnitPriceSet": {"shopMoney": {"amount": "50.00", "currencyCode": "USD"}},
                "variant": {"id": "V1", "inventoryItem": {"unitCost": {"amount": "20.00", "currencyCode": "EUR"}}}
            }],
            "transactions": [{"id": "T1", "gateway": "shopify_payments", "fees": [{"amount": {"amount": "1.60", "currencyCode": "USD"}}]}],
            "refunds": []
        },
        "expected": {
            "L": 5000, "D": 0, "R": 5000, "Sc": 0, "C": 5000,
            "COGS": 2000, "S": 500, "G": 160, "E": 0, "O": 0,
            "P": 2340, "P_upper": 2340, "margin": 46.8,
            "class": "profitable", "classification": "profitable", "band": "high", "lane": "MEASURED",
            "component_tags": {"cogs": "measured", "shipping": "measured", "gateway": "measured", "refund": "measured", "other": "structural"},
            "measured_share": "1.0000", "flags": ["CURRENCY_MISMATCH_COST"],
            "drivers": {"product_margin_at_list": 3000, "discount_leak": 0, "shipping_net": -500, "fee_leak": -160, "refund_leak": 0, "other_leak": 0},
            "top_loss_driver": None, "delta_profit": 250
        }
    },
    {
        "id": "B11",
        "purpose": "Fully removed line (qs = 0) with null cost: must NOT quarantine order.",
        "profile": "balanced", "spec_ref": "3.1, 3.2", "tag": "V-DOC",
        "arithmetic_derivation": "L1: qs=1, cost=2000. L2: qs=0 (removed), cost=None. Lines with qs=0 never trigger missing-cost! COGS = 2000 (measured). P = 5000 - 2000 - 500 - 160 = 2340. Lane=MEASURED.",
        "input": {
            "id": "gid://shopify/Order/B11", "name": "#B11", "currencyCode": "USD", "processedAt": "2026-08-01T12:00:00Z",
            "currentShippingPriceSet": {"shopMoney": {"amount": "0.00", "currencyCode": "USD"}},
            "actual_carrier_cost": "5.00",
            "lineItems": [
                {
                    "id": "L1", "quantity": 1, "currentQuantity": 1,
                    "originalUnitPriceSet": {"shopMoney": {"amount": "50.00", "currencyCode": "USD"}},
                    "variant": {"id": "V1", "inventoryItem": {"unitCost": {"amount": "20.00", "currencyCode": "USD"}}}
                },
                {
                    "id": "L2", "quantity": 1, "currentQuantity": 0,
                    "originalUnitPriceSet": {"shopMoney": {"amount": "50.00", "currencyCode": "USD"}},
                    "variant": {"id": "V2", "inventoryItem": {"unitCost": None}}
                }
            ],
            "transactions": [{"id": "T1", "gateway": "shopify_payments", "fees": [{"amount": {"amount": "1.60", "currencyCode": "USD"}}]}],
            "refunds": []
        },
        "expected": {
            "L": 5000, "D": 0, "R": 5000, "Sc": 0, "C": 5000,
            "COGS": 2000, "S": 500, "G": 160, "E": 0, "O": 0,
            "P": 2340, "P_upper": 2340, "margin": 46.8,
            "class": "profitable", "classification": "profitable", "band": "high", "lane": "MEASURED",
            "component_tags": {"cogs": "measured", "shipping": "measured", "gateway": "measured", "refund": "measured", "other": "structural"},
            "measured_share": "1.0000", "flags": [],
            "drivers": {"product_margin_at_list": 3000, "discount_leak": 0, "shipping_net": -500, "fee_leak": -160, "refund_leak": 0, "other_leak": 0},
            "top_loss_driver": None, "delta_profit": 250
        }
    },
    {
        "id": "B12",
        "purpose": "Cost drift: formula uses current cost and tags cogs_basis = restated_current_cost.",
        "profile": "balanced", "spec_ref": "3.1", "tag": "V-DOC",
        "arithmetic_derivation": "Order uses current inventoryItem cost. Tagged cogs_basis = restated_current_cost if cost drift detected.",
        "input": {
            "id": "gid://shopify/Order/B12", "name": "#B12", "currencyCode": "USD", "processedAt": "2026-08-01T12:00:00Z",
            "cost_basis_type": "restated_current_cost",
            "currentShippingPriceSet": {"shopMoney": {"amount": "0.00", "currencyCode": "USD"}},
            "actual_carrier_cost": "5.00",
            "lineItems": [{
                "id": "L1", "quantity": 1, "currentQuantity": 1,
                "originalUnitPriceSet": {"shopMoney": {"amount": "50.00", "currencyCode": "USD"}},
                "variant": {"id": "V1", "inventoryItem": {"unitCost": {"amount": "20.00", "currencyCode": "USD"}}}
            }],
            "transactions": [{"id": "T1", "gateway": "shopify_payments", "fees": [{"amount": {"amount": "1.60", "currencyCode": "USD"}}]}],
            "refunds": []
        },
        "expected": {
            "L": 5000, "D": 0, "R": 5000, "Sc": 0, "C": 5000,
            "COGS": 2000, "S": 500, "G": 160, "E": 0, "O": 0,
            "P": 2340, "P_upper": 2340, "margin": 46.8,
            "class": "profitable", "classification": "profitable", "band": "high", "lane": "MEASURED",
            "component_tags": {"cogs": "measured", "shipping": "measured", "gateway": "measured", "refund": "measured", "other": "structural"},
            "measured_share": "1.0000", "flags": [],
            "drivers": {"product_margin_at_list": 3000, "discount_leak": 0, "shipping_net": -500, "fee_leak": -160, "refund_leak": 0, "other_leak": 0},
            "top_loss_driver": None, "delta_profit": 250
        }
    },
    {
        "id": "B13",
        "purpose": "Multiple lines with zero-cost and standard cost: measured_with_flag.",
        "profile": "balanced", "spec_ref": "3.1, 3.2", "tag": "CFG",
        "arithmetic_derivation": "L1: cost=2000. L2: cost=0 (flagged). Total COGS = 2000. C = 10000; S = 800; G = 300. P = 6900. Margin = 69.00% (high).",
        "input": {
            "id": "gid://shopify/Order/B13", "name": "#B13", "currencyCode": "USD", "processedAt": "2026-08-01T12:00:00Z",
            "currentShippingPriceSet": {"shopMoney": {"amount": "0.00", "currencyCode": "USD"}},
            "actual_carrier_cost": "8.00",
            "lineItems": [
                {
                    "id": "L1", "quantity": 1, "currentQuantity": 1,
                    "originalUnitPriceSet": {"shopMoney": {"amount": "50.00", "currencyCode": "USD"}},
                    "variant": {"id": "V1", "inventoryItem": {"unitCost": {"amount": "20.00", "currencyCode": "USD"}}}
                },
                {
                    "id": "L2", "quantity": 1, "currentQuantity": 1,
                    "originalUnitPriceSet": {"shopMoney": {"amount": "50.00", "currencyCode": "USD"}},
                    "variant": {"id": "V2", "inventoryItem": {"unitCost": {"amount": "0.00", "currencyCode": "USD"}}}
                }
            ],
            "transactions": [{"id": "T1", "gateway": "shopify_payments", "fees": [{"amount": {"amount": "3.00", "currencyCode": "USD"}}]}],
            "refunds": []
        },
        "expected": {
            "L": 10000, "D": 0, "R": 10000, "Sc": 0, "C": 10000,
            "COGS": 2000, "S": 800, "G": 300, "E": 0, "O": 0,
            "P": 6900, "P_upper": 6900, "margin": 69.0,
            "class": "profitable", "classification": "profitable", "band": "high", "lane": "MEASURED",
            "component_tags": {"cogs": "measured", "shipping": "measured", "gateway": "measured", "refund": "measured", "other": "structural"},
            "measured_share": "1.0000", "flags": ["SUSPECT_ZERO_COST"],
            "drivers": {"product_margin_at_list": 8000, "discount_leak": 0, "shipping_net": -800, "fee_leak": -300, "refund_leak": 0, "other_leak": 0},
            "top_loss_driver": None, "delta_profit": 500
        }
    },
    {
        "id": "B14",
        "purpose": "Order with 5 lines, all with valid unit costs.",
        "profile": "balanced", "spec_ref": "3.1, 3.2", "tag": "V-DOC",
        "arithmetic_derivation": "5 lines @ $20 ($10 cost) -> L=10000; COGS=5000. C=10000; S=800; G=300. P=3900. Margin=39.00% (high).",
        "input": {
            "id": "gid://shopify/Order/B14", "name": "#B14", "currencyCode": "USD", "processedAt": "2026-08-01T12:00:00Z",
            "currentShippingPriceSet": {"shopMoney": {"amount": "0.00", "currencyCode": "USD"}},
            "actual_carrier_cost": "8.00",
            "lineItems": [
                {
                    "id": f"L{i}", "quantity": 1, "currentQuantity": 1,
                    "originalUnitPriceSet": {"shopMoney": {"amount": "20.00", "currencyCode": "USD"}},
                    "variant": {"id": f"V{i}", "inventoryItem": {"unitCost": {"amount": "10.00", "currencyCode": "USD"}}}
                } for i in range(1, 6)
            ],
            "transactions": [{"id": "T1", "gateway": "shopify_payments", "fees": [{"amount": {"amount": "3.00", "currencyCode": "USD"}}]}],
            "refunds": []
        },
        "expected": {
            "L": 10000, "D": 0, "R": 10000, "Sc": 0, "C": 10000,
            "COGS": 5000, "S": 800, "G": 300, "E": 0, "O": 0,
            "P": 3900, "P_upper": 3900, "margin": 39.0,
            "class": "profitable", "classification": "profitable", "band": "high", "lane": "MEASURED",
            "component_tags": {"cogs": "measured", "shipping": "measured", "gateway": "measured", "refund": "measured", "other": "structural"},
            "measured_share": "1.0000", "flags": [],
            "drivers": {"product_margin_at_list": 5000, "discount_leak": 0, "shipping_net": -800, "fee_leak": -300, "refund_leak": 0, "other_leak": 0},
            "top_loss_driver": None, "delta_profit": 500
        }
    },
    {
        "id": "B15",
        "purpose": "Custom line item without cost in balanced profile: Lane UNDETERMINED.",
        "profile": "balanced", "spec_ref": "3.1, 3.2", "tag": "CFG",
        "arithmetic_derivation": "Custom line has no variant -> cost missing -> COGS=None, Lane=UNDETERMINED.",
        "input": {
            "id": "gid://shopify/Order/B15", "name": "#B15", "currencyCode": "USD", "processedAt": "2026-08-01T12:00:00Z",
            "currentShippingPriceSet": {"shopMoney": {"amount": "0.00", "currencyCode": "USD"}},
            "actual_carrier_cost": "5.00",
            "lineItems": [{
                "id": "L1", "quantity": 1, "currentQuantity": 1, "title": "Bespoke Gift Wrap", "variant": None,
                "originalUnitPriceSet": {"shopMoney": {"amount": "15.00", "currencyCode": "USD"}}
            }],
            "transactions": [{"id": "T1", "gateway": "shopify_payments", "fees": [{"amount": {"amount": "0.50", "currencyCode": "USD"}}]}],
            "refunds": []
        },
        "expected": {
            "L": 1500, "D": 0, "R": 1500, "Sc": 0, "C": 1500,
            "COGS": None, "S": 500, "G": 50, "E": 0, "O": 0,
            "P": None, "P_upper": 950, "margin": None,
            "class": "undetermined", "classification": "undetermined", "band": "undetermined", "lane": "UNDETERMINED",
            "component_tags": {"cogs": "missing", "shipping": "measured", "gateway": "measured", "refund": "measured", "other": "structural"},
            "measured_share": "1.0000", "flags": ["COGS_MISSING_CUSTOM_LINE"],
            "drivers": {"product_margin_at_list": "unknown", "discount_leak": 0, "shipping_net": -500, "fee_leak": -50, "refund_leak": 0, "other_leak": 0},
            "top_loss_driver": None, "delta_profit": None
        }
    }
]
