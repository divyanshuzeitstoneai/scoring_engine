"""
Scenario Group D: Refunds, Returns, and Edits (D01 - D22).
Anchor order B0 used as base:
Line: u = 5500, qs = 2, unit cost = 2250 -> gross = 11000, COGS = 4500.
Sc = 1000, C = 12000. S = 900 (carrier measured), G = 378 (fee measured), O = 0.
"""

from typing import Dict, Any, List

group_d_fixtures: List[Dict[str, Any]] = [
    # D01: No refund, open window
    {
        "id": "D01",
        "purpose": "Anchor B0: No refund, window open (age 10d < 30d). Provision = 5% of R = 550. Lane ESTIMATED.",
        "profile": "balanced", "spec_ref": "3.2, 7.0", "tag": "V-DOC",
        "arithmetic_derivation": "R=11000; C=12000; COGS=4500; S=900; G=378; E=550; O=0. P = 12000 - 4500 - 900 - 378 - 550 = 5672. Margin = 47.2667%.",
        "input": {
            "id": "gid://shopify/Order/D01", "name": "#D01", "currencyCode": "USD", "processedAt": "2026-09-20T12:00:00Z",
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
    },
    # D02: No refund, closed window
    {
        "id": "D02",
        "purpose": "Anchor B0: No refund, window closed (age 60d >= 30d). Provision released (E = 0). Lane MEASURED.",
        "profile": "balanced", "spec_ref": "3.2, 7.0", "tag": "V-DOC",
        "arithmetic_derivation": "R=11000; C=12000; COGS=4500; S=900; G=378; E=0; O=0. P = 12000 - 4500 - 900 - 378 = 6222. Margin = 51.85%.",
        "input": {
            "id": "gid://shopify/Order/D02", "name": "#D02", "currencyCode": "USD", "processedAt": "2026-08-01T12:00:00Z",
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
            "COGS": 4500, "S": 900, "G": 378, "E": 0, "O": 0,
            "P": 6222, "P_upper": 6222, "margin": 51.85,
            "class": "profitable", "classification": "profitable", "band": "high", "lane": "MEASURED",
            "component_tags": {"cogs": "measured", "shipping": "measured", "gateway": "measured", "refund": "measured", "other": "structural"},
            "measured_share": "1.0000", "flags": [],
            "drivers": {"product_margin_at_list": 6500, "discount_leak": 0, "shipping_net": 100, "fee_leak": -378, "refund_leak": 0, "other_leak": 0},
            "top_loss_driver": None, "delta_profit": 550
        }
    },
    # D03: Full refund with restock
    {
        "id": "D03",
        "purpose": "Anchor B0: Full refund (2 units) with restock credit. E = 11000 - 4500 = 6500.",
        "profile": "balanced", "spec_ref": "3.2, 7.0", "tag": "V-DOC",
        "arithmetic_derivation": "E = 11000 refunded - 4500 restock COGS = 6500. P = 12000 - 4500 - 900 - 378 - 6500 = -278. Margin = -2.3167%. Unprofitable, cash_drain.",
        "input": {
            "id": "gid://shopify/Order/D03", "name": "#D03", "currencyCode": "USD", "processedAt": "2026-08-01T12:00:00Z",
            "currentShippingPriceSet": {"shopMoney": {"amount": "10.00", "currencyCode": "USD"}},
            "actual_carrier_cost": "9.00",
            "lineItems": [{
                "id": "L1", "quantity": 2, "currentQuantity": 0,
                "originalUnitPriceSet": {"shopMoney": {"amount": "55.00", "currencyCode": "USD"}},
                "variant": {"id": "V1", "inventoryItem": {"unitCost": {"amount": "22.50", "currencyCode": "USD"}}}
            }],
            "transactions": [{"id": "T1", "gateway": "shopify_payments", "fees": [{"amount": {"amount": "3.78", "currencyCode": "USD"}}]}],
            "refunds": [{
                "id": "R1", "createdAt": "2026-08-10T12:00:00Z",
                "totalRefundedSet": {"shopMoney": {"amount": "110.00", "currencyCode": "USD"}},
                "refundLineItems": [{"lineItemId": "L1", "quantity": 2, "restocked": True}]
            }]
        },
        "expected": {
            "L": 11000, "D": 0, "R": 11000, "Sc": 1000, "C": 12000,
            "COGS": 4500, "S": 900, "G": 378, "E": 6500, "O": 0,
            "P": -278, "P_upper": -278, "margin": -2.3167,
            "class": "unprofitable", "classification": "unprofitable", "band": "cash_drain", "lane": "MEASURED",
            "component_tags": {"cogs": "measured", "shipping": "measured", "gateway": "measured", "refund": "measured", "other": "structural"},
            "measured_share": "1.0000", "flags": [],
            "drivers": {"product_margin_at_list": 6500, "discount_leak": 0, "shipping_net": 100, "fee_leak": -378, "refund_leak": -6500, "other_leak": 0},
            "top_loss_driver": "refund_leak", "delta_profit": -5950
        }
    },
    # D04: Full refund without restock
    {
        "id": "D04",
        "purpose": "Anchor B0: Full refund (2 units) without restock. E = 11000. P = -4778.",
        "profile": "balanced", "spec_ref": "3.2, 7.0", "tag": "V-DOC",
        "arithmetic_derivation": "E = 11000 without restock credit. P = 12000 - 4500 - 900 - 378 - 11000 = -4778. Margin = -39.8167%. Unprofitable, cash_drain.",
        "input": {
            "id": "gid://shopify/Order/D04", "name": "#D04", "currencyCode": "USD", "processedAt": "2026-08-01T12:00:00Z",
            "currentShippingPriceSet": {"shopMoney": {"amount": "10.00", "currencyCode": "USD"}},
            "actual_carrier_cost": "9.00",
            "lineItems": [{
                "id": "L1", "quantity": 2, "currentQuantity": 0,
                "originalUnitPriceSet": {"shopMoney": {"amount": "55.00", "currencyCode": "USD"}},
                "variant": {"id": "V1", "inventoryItem": {"unitCost": {"amount": "22.50", "currencyCode": "USD"}}}
            }],
            "transactions": [{"id": "T1", "gateway": "shopify_payments", "fees": [{"amount": {"amount": "3.78", "currencyCode": "USD"}}]}],
            "refunds": [{
                "id": "R1", "createdAt": "2026-08-10T12:00:00Z",
                "totalRefundedSet": {"shopMoney": {"amount": "110.00", "currencyCode": "USD"}},
                "refundLineItems": [{"lineItemId": "L1", "quantity": 2, "restocked": False}]
            }]
        },
        "expected": {
            "L": 11000, "D": 0, "R": 11000, "Sc": 1000, "C": 12000,
            "COGS": 4500, "S": 900, "G": 378, "E": 11000, "O": 0,
            "P": -4778, "P_upper": -4778, "margin": -39.8167,
            "class": "unprofitable", "classification": "unprofitable", "band": "cash_drain", "lane": "MEASURED",
            "component_tags": {"cogs": "measured", "shipping": "measured", "gateway": "measured", "refund": "measured", "other": "structural"},
            "measured_share": "1.0000", "flags": [],
            "drivers": {"product_margin_at_list": 6500, "discount_leak": 0, "shipping_net": 100, "fee_leak": -378, "refund_leak": -11000, "other_leak": 0},
            "top_loss_driver": "refund_leak", "delta_profit": -10450
        }
    },
    # D05: Partial refund (1 of 2 units) with restock
    {
        "id": "D05",
        "purpose": "Anchor B0: 1 of 2 units refunded with restock. E = 5500 - 2250 = 3250. P = 2972.",
        "profile": "balanced", "spec_ref": "3.2, 7.0", "tag": "V-DOC",
        "arithmetic_derivation": "E = 5500 - 2250 = 3250. P = 12000 - 4500 - 900 - 378 - 3250 = 2972. Margin = 24.7667% (acceptable).",
        "input": {
            "id": "gid://shopify/Order/D05", "name": "#D05", "currencyCode": "USD", "processedAt": "2026-08-01T12:00:00Z",
            "currentShippingPriceSet": {"shopMoney": {"amount": "10.00", "currencyCode": "USD"}},
            "actual_carrier_cost": "9.00",
            "lineItems": [{
                "id": "L1", "quantity": 2, "currentQuantity": 1,
                "originalUnitPriceSet": {"shopMoney": {"amount": "55.00", "currencyCode": "USD"}},
                "variant": {"id": "V1", "inventoryItem": {"unitCost": {"amount": "22.50", "currencyCode": "USD"}}}
            }],
            "transactions": [{"id": "T1", "gateway": "shopify_payments", "fees": [{"amount": {"amount": "3.78", "currencyCode": "USD"}}]}],
            "refunds": [{
                "id": "R1", "createdAt": "2026-08-10T12:00:00Z",
                "totalRefundedSet": {"shopMoney": {"amount": "55.00", "currencyCode": "USD"}},
                "refundLineItems": [{"lineItemId": "L1", "quantity": 1, "restocked": True}]
            }]
        },
        "expected": {
            "L": 11000, "D": 0, "R": 11000, "Sc": 1000, "C": 12000,
            "COGS": 4500, "S": 900, "G": 378, "E": 3250, "O": 0,
            "P": 2972, "P_upper": 2972, "margin": 24.7667,
            "class": "profitable", "classification": "profitable", "band": "acceptable", "lane": "MEASURED",
            "component_tags": {"cogs": "measured", "shipping": "measured", "gateway": "measured", "refund": "measured", "other": "structural"},
            "measured_share": "1.0000", "flags": [],
            "drivers": {"product_margin_at_list": 6500, "discount_leak": 0, "shipping_net": 100, "fee_leak": -378, "refund_leak": -3250, "other_leak": 0},
            "top_loss_driver": None, "delta_profit": -2700
        }
    },
    # D06: Goodwill refund
    {
        "id": "D06",
        "purpose": "Anchor B0: Goodwill refund $25.00 without unit alteration. E = 2500. P = 3722.",
        "profile": "balanced", "spec_ref": "3.2, 7.0", "tag": "V-DOC",
        "arithmetic_derivation": "E = 2500 (no restock). P = 12000 - 4500 - 900 - 378 - 2500 = 3722. Margin = 31.0167% (high).",
        "input": {
            "id": "gid://shopify/Order/D06", "name": "#D06", "currencyCode": "USD", "processedAt": "2026-08-01T12:00:00Z",
            "currentShippingPriceSet": {"shopMoney": {"amount": "10.00", "currencyCode": "USD"}},
            "actual_carrier_cost": "9.00",
            "lineItems": [{
                "id": "L1", "quantity": 2, "currentQuantity": 2,
                "originalUnitPriceSet": {"shopMoney": {"amount": "55.00", "currencyCode": "USD"}},
                "variant": {"id": "V1", "inventoryItem": {"unitCost": {"amount": "22.50", "currencyCode": "USD"}}}
            }],
            "transactions": [{"id": "T1", "gateway": "shopify_payments", "fees": [{"amount": {"amount": "3.78", "currencyCode": "USD"}}]}],
            "refunds": [{
                "id": "R1", "createdAt": "2026-08-10T12:00:00Z",
                "totalRefundedSet": {"shopMoney": {"amount": "25.00", "currencyCode": "USD"}},
                "refundLineItems": []
            }]
        },
        "expected": {
            "L": 11000, "D": 0, "R": 11000, "Sc": 1000, "C": 12000,
            "COGS": 4500, "S": 900, "G": 378, "E": 2500, "O": 0,
            "P": 3722, "P_upper": 3722, "margin": 31.0167,
            "class": "profitable", "classification": "profitable", "band": "high", "lane": "MEASURED",
            "component_tags": {"cogs": "measured", "shipping": "measured", "gateway": "measured", "refund": "measured", "other": "structural"},
            "measured_share": "1.0000", "flags": [],
            "drivers": {"product_margin_at_list": 6500, "discount_leak": 0, "shipping_net": 100, "fee_leak": -378, "refund_leak": -2500, "other_leak": 0},
            "top_loss_driver": None, "delta_profit": -1950
        }
    },
    # D07: Shipping-only refund
    {
        "id": "D07",
        "purpose": "Anchor B0: Shipping refund $10.00. E = 1000. P = 5222.",
        "profile": "balanced", "spec_ref": "3.2, 7.0", "tag": "V-DOC",
        "arithmetic_derivation": "E = 1000. P = 12000 - 4500 - 900 - 378 - 1000 = 5222. Margin = 43.5167% (high).",
        "input": {
            "id": "gid://shopify/Order/D07", "name": "#D07", "currencyCode": "USD", "processedAt": "2026-08-01T12:00:00Z",
            "currentShippingPriceSet": {"shopMoney": {"amount": "10.00", "currencyCode": "USD"}},
            "actual_carrier_cost": "9.00",
            "lineItems": [{
                "id": "L1", "quantity": 2, "currentQuantity": 2,
                "originalUnitPriceSet": {"shopMoney": {"amount": "55.00", "currencyCode": "USD"}},
                "variant": {"id": "V1", "inventoryItem": {"unitCost": {"amount": "22.50", "currencyCode": "USD"}}}
            }],
            "transactions": [{"id": "T1", "gateway": "shopify_payments", "fees": [{"amount": {"amount": "3.78", "currencyCode": "USD"}}]}],
            "refunds": [{
                "id": "R1", "createdAt": "2026-08-10T12:00:00Z",
                "totalRefundedSet": {"shopMoney": {"amount": "10.00", "currencyCode": "USD"}},
                "refundLineItems": []
            }]
        },
        "expected": {
            "L": 11000, "D": 0, "R": 11000, "Sc": 1000, "C": 12000,
            "COGS": 4500, "S": 900, "G": 378, "E": 1000, "O": 0,
            "P": 5222, "P_upper": 5222, "margin": 43.5167,
            "class": "profitable", "classification": "profitable", "band": "high", "lane": "MEASURED",
            "component_tags": {"cogs": "measured", "shipping": "measured", "gateway": "measured", "refund": "measured", "other": "structural"},
            "measured_share": "1.0000", "flags": [],
            "drivers": {"product_margin_at_list": 6500, "discount_leak": 0, "shipping_net": 100, "fee_leak": -378, "refund_leak": -1000, "other_leak": 0},
            "top_loss_driver": None, "delta_profit": -450
        }
    },
    # D08: Two sequential refunds
    {
        "id": "D08",
        "purpose": "Anchor B0: Two sequential refunds (unit 1 restocked, unit 2 restocked). Restock credited per unit. Combined E = 6500.",
        "profile": "balanced", "spec_ref": "3.2, 7.0", "tag": "V-DOC",
        "arithmetic_derivation": "R1: 5500 - 2250 = 3250. R2: 5500 - 2250 = 3250. E = 6500. P = -278.",
        "input": {
            "id": "gid://shopify/Order/D08", "name": "#D08", "currencyCode": "USD", "processedAt": "2026-08-01T12:00:00Z",
            "currentShippingPriceSet": {"shopMoney": {"amount": "10.00", "currencyCode": "USD"}},
            "actual_carrier_cost": "9.00",
            "lineItems": [{
                "id": "L1", "quantity": 2, "currentQuantity": 0,
                "originalUnitPriceSet": {"shopMoney": {"amount": "55.00", "currencyCode": "USD"}},
                "variant": {"id": "V1", "inventoryItem": {"unitCost": {"amount": "22.50", "currencyCode": "USD"}}}
            }],
            "transactions": [{"id": "T1", "gateway": "shopify_payments", "fees": [{"amount": {"amount": "3.78", "currencyCode": "USD"}}]}],
            "refunds": [
                {
                    "id": "R1", "createdAt": "2026-08-10T12:00:00Z",
                    "totalRefundedSet": {"shopMoney": {"amount": "55.00", "currencyCode": "USD"}},
                    "refundLineItems": [{"lineItemId": "L1", "quantity": 1, "restocked": True}]
                },
                {
                    "id": "R2", "createdAt": "2026-08-15T12:00:00Z",
                    "totalRefundedSet": {"shopMoney": {"amount": "55.00", "currencyCode": "USD"}},
                    "refundLineItems": [{"lineItemId": "L1", "quantity": 1, "restocked": True}]
                }
            ]
        },
        "expected": {
            "L": 11000, "D": 0, "R": 11000, "Sc": 1000, "C": 12000,
            "COGS": 4500, "S": 900, "G": 378, "E": 6500, "O": 0,
            "P": -278, "P_upper": -278, "margin": -2.3167,
            "class": "unprofitable", "classification": "unprofitable", "band": "cash_drain", "lane": "MEASURED",
            "component_tags": {"cogs": "measured", "shipping": "measured", "gateway": "measured", "refund": "measured", "other": "structural"},
            "measured_share": "1.0000", "flags": [],
            "drivers": {"product_margin_at_list": 6500, "discount_leak": 0, "shipping_net": 100, "fee_leak": -378, "refund_leak": -6500, "other_leak": 0},
            "top_loss_driver": "refund_leak", "delta_profit": -5950
        }
    },
    # D09: Return with label cost and handling
    {
        "id": "D09",
        "purpose": "Anchor B0: Partial refund + return shipping label 700 + restock handling 200. E = 3250 + 700 + 200 = 4150.",
        "profile": "balanced", "spec_ref": "3.2, 7.0", "tag": "V-DOC",
        "arithmetic_derivation": "E = (5500 - 2250) + 700 + 200 = 4150. P = 12000 - 4500 - 900 - 378 - 4150 = 2072. Margin = 17.2667% (acceptable).",
        "input": {
            "id": "gid://shopify/Order/D09", "name": "#D09", "currencyCode": "USD", "processedAt": "2026-08-01T12:00:00Z",
            "currentShippingPriceSet": {"shopMoney": {"amount": "10.00", "currencyCode": "USD"}},
            "actual_carrier_cost": "9.00",
            "return_label_cost": "7.00", "restock_handling_fee": "2.00",
            "lineItems": [{
                "id": "L1", "quantity": 2, "currentQuantity": 1,
                "originalUnitPriceSet": {"shopMoney": {"amount": "55.00", "currencyCode": "USD"}},
                "variant": {"id": "V1", "inventoryItem": {"unitCost": {"amount": "22.50", "currencyCode": "USD"}}}
            }],
            "transactions": [{"id": "T1", "gateway": "shopify_payments", "fees": [{"amount": {"amount": "3.78", "currencyCode": "USD"}}]}],
            "refunds": [{
                "id": "R1", "createdAt": "2026-08-10T12:00:00Z",
                "totalRefundedSet": {"shopMoney": {"amount": "55.00", "currencyCode": "USD"}},
                "refundLineItems": [{"lineItemId": "L1", "quantity": 1, "restocked": True}]
            }]
        },
        "expected": {
            "L": 11000, "D": 0, "R": 11000, "Sc": 1000, "C": 12000,
            "COGS": 4500, "S": 900, "G": 378, "E": 4150, "O": 0,
            "P": 2072, "P_upper": 2072, "margin": 17.2667,
            "class": "profitable", "classification": "profitable", "band": "acceptable", "lane": "MEASURED",
            "component_tags": {"cogs": "measured", "shipping": "measured", "gateway": "measured", "refund": "measured", "other": "structural"},
            "measured_share": "1.0000", "flags": [],
            "drivers": {"product_margin_at_list": 6500, "discount_leak": 0, "shipping_net": 100, "fee_leak": -378, "refund_leak": -4150, "other_leak": 0},
            "top_loss_driver": None, "delta_profit": -3600
        }
    },
    # D10: Refund of discounted line
    {
        "id": "D10",
        "purpose": "Refund of a discounted line: unit price 100, discount 20 -> refund amount 80.",
        "profile": "balanced", "spec_ref": "3.1, 3.2", "tag": "V-DOC",
        "arithmetic_derivation": "L = 10000; D = 2000; R = 8000; Sc = 0; C = 8000. COGS = 4000. Refunded 8000 with restock 4000 -> E = 4000. P = 8000 - 4000 - 800 - 260 - 4000 = -1060. Margin = -13.25%.",
        "input": {
            "id": "gid://shopify/Order/D10", "name": "#D10", "currencyCode": "USD", "processedAt": "2026-08-01T12:00:00Z",
            "currentShippingPriceSet": {"shopMoney": {"amount": "0.00", "currencyCode": "USD"}},
            "actual_carrier_cost": "8.00",
            "lineItems": [{
                "id": "L1", "quantity": 1, "currentQuantity": 0,
                "originalUnitPriceSet": {"shopMoney": {"amount": "100.00", "currencyCode": "USD"}},
                "discountAllocations": [{"allocatedAmountSet": {"shopMoney": {"amount": "20.00", "currencyCode": "USD"}}}],
                "variant": {"id": "V1", "inventoryItem": {"unitCost": {"amount": "40.00", "currencyCode": "USD"}}}
            }],
            "transactions": [{"id": "T1", "gateway": "shopify_payments", "fees": [{"amount": {"amount": "2.60", "currencyCode": "USD"}}]}],
            "refunds": [{
                "id": "R1", "createdAt": "2026-08-10T12:00:00Z",
                "totalRefundedSet": {"shopMoney": {"amount": "80.00", "currencyCode": "USD"}},
                "refundLineItems": [{"lineItemId": "L1", "quantity": 1, "restocked": True}]
            }]
        },
        "expected": {
            "L": 10000, "D": 2000, "R": 8000, "Sc": 0, "C": 8000,
            "COGS": 4000, "S": 800, "G": 260, "E": 4000, "O": 0,
            "P": -1060, "P_upper": -1060, "margin": -13.25,
            "class": "unprofitable", "classification": "unprofitable", "band": "cash_drain", "lane": "MEASURED",
            "component_tags": {"cogs": "measured", "shipping": "measured", "gateway": "measured", "refund": "measured", "other": "structural"},
            "measured_share": "1.0000", "flags": [],
            "drivers": {"product_margin_at_list": 6000, "discount_leak": -2000, "shipping_net": -800, "fee_leak": -260, "refund_leak": -4000, "other_leak": 0},
            "top_loss_driver": "refund_leak", "delta_profit": -3600
        }
    },
    # D11: Refund created after as_of is ignored
    {
        "id": "D11",
        "purpose": "Refund created after as_of (2026-10-05 > 2026-09-30) is ignored.",
        "profile": "balanced", "spec_ref": "3.2, 5.0", "tag": "V-DOC",
        "arithmetic_derivation": "Refund ignored because createdAt > as_of. Order processed 2026-08-01 (closed window, age 60d >= 30d). E = 0. P = 6222.",
        "input": {
            "id": "gid://shopify/Order/D11", "name": "#D11", "currencyCode": "USD", "processedAt": "2026-08-01T12:00:00Z",
            "currentShippingPriceSet": {"shopMoney": {"amount": "10.00", "currencyCode": "USD"}},
            "actual_carrier_cost": "9.00",
            "lineItems": [{
                "id": "L1", "quantity": 2, "currentQuantity": 2,
                "originalUnitPriceSet": {"shopMoney": {"amount": "55.00", "currencyCode": "USD"}},
                "variant": {"id": "V1", "inventoryItem": {"unitCost": {"amount": "22.50", "currencyCode": "USD"}}}
            }],
            "transactions": [{"id": "T1", "gateway": "shopify_payments", "fees": [{"amount": {"amount": "3.78", "currencyCode": "USD"}}]}],
            "refunds": [{
                "id": "R1", "createdAt": "2026-10-05T12:00:00Z",
                "totalRefundedSet": {"shopMoney": {"amount": "110.00", "currencyCode": "USD"}},
                "refundLineItems": [{"lineItemId": "L1", "quantity": 2, "restocked": True}]
            }]
        },
        "expected": {
            "L": 11000, "D": 0, "R": 11000, "Sc": 1000, "C": 12000,
            "COGS": 4500, "S": 900, "G": 378, "E": 0, "O": 0,
            "P": 6222, "P_upper": 6222, "margin": 51.85,
            "class": "profitable", "classification": "profitable", "band": "high", "lane": "MEASURED",
            "component_tags": {"cogs": "measured", "shipping": "measured", "gateway": "measured", "refund": "measured", "other": "structural"},
            "measured_share": "1.0000", "flags": [],
            "drivers": {"product_margin_at_list": 6500, "discount_leak": 0, "shipping_net": 100, "fee_leak": -378, "refund_leak": 0, "other_leak": 0},
            "top_loss_driver": None, "delta_profit": 550
        }
    },
    # D12: Refund after window closed
    {
        "id": "D12",
        "purpose": "Refund occurs after window closed (e.g. day 45): realized refund counts.",
        "profile": "balanced", "spec_ref": "3.2", "tag": "V-DOC",
        "arithmetic_derivation": "Realized refund counts in E regardless of order age: E = 11000 - 4500 = 6500. P = -278.",
        "input": {
            "id": "gid://shopify/Order/D12", "name": "#D12", "currencyCode": "USD", "processedAt": "2026-08-01T12:00:00Z",
            "currentShippingPriceSet": {"shopMoney": {"amount": "10.00", "currencyCode": "USD"}},
            "actual_carrier_cost": "9.00",
            "lineItems": [{
                "id": "L1", "quantity": 2, "currentQuantity": 0,
                "originalUnitPriceSet": {"shopMoney": {"amount": "55.00", "currencyCode": "USD"}},
                "variant": {"id": "V1", "inventoryItem": {"unitCost": {"amount": "22.50", "currencyCode": "USD"}}}
            }],
            "transactions": [{"id": "T1", "gateway": "shopify_payments", "fees": [{"amount": {"amount": "3.78", "currencyCode": "USD"}}]}],
            "refunds": [{
                "id": "R1", "createdAt": "2026-09-15T12:00:00Z",
                "totalRefundedSet": {"shopMoney": {"amount": "110.00", "currencyCode": "USD"}},
                "refundLineItems": [{"lineItemId": "L1", "quantity": 2, "restocked": True}]
            }]
        },
        "expected": {
            "L": 11000, "D": 0, "R": 11000, "Sc": 1000, "C": 12000,
            "COGS": 4500, "S": 900, "G": 378, "E": 6500, "O": 0,
            "P": -278, "P_upper": -278, "margin": -2.3167,
            "class": "unprofitable", "classification": "unprofitable", "band": "cash_drain", "lane": "MEASURED",
            "component_tags": {"cogs": "measured", "shipping": "measured", "gateway": "measured", "refund": "measured", "other": "structural"},
            "measured_share": "1.0000", "flags": [],
            "drivers": {"product_margin_at_list": 6500, "discount_leak": 0, "shipping_net": 100, "fee_leak": -378, "refund_leak": -6500, "other_leak": 0},
            "top_loss_driver": "refund_leak", "delta_profit": -5950
        }
    },
    # D13: Realized refund replaces provision
    {
        "id": "D13",
        "purpose": "Realized refund never coexists with provision: open window with partial refund books realized E only.",
        "profile": "balanced", "spec_ref": "3.2", "tag": "V-DOC",
        "arithmetic_derivation": "Order processed 2026-09-20 (open window). 1 unit refunded with restock: E = 3250. Provision is NOT added. P = 2972.",
        "input": {
            "id": "gid://shopify/Order/D13", "name": "#D13", "currencyCode": "USD", "processedAt": "2026-09-20T12:00:00Z",
            "currentShippingPriceSet": {"shopMoney": {"amount": "10.00", "currencyCode": "USD"}},
            "actual_carrier_cost": "9.00",
            "lineItems": [{
                "id": "L1", "quantity": 2, "currentQuantity": 1,
                "originalUnitPriceSet": {"shopMoney": {"amount": "55.00", "currencyCode": "USD"}},
                "variant": {"id": "V1", "inventoryItem": {"unitCost": {"amount": "22.50", "currencyCode": "USD"}}}
            }],
            "transactions": [{"id": "T1", "gateway": "shopify_payments", "fees": [{"amount": {"amount": "3.78", "currencyCode": "USD"}}]}],
            "refunds": [{
                "id": "R1", "createdAt": "2026-09-22T12:00:00Z",
                "totalRefundedSet": {"shopMoney": {"amount": "55.00", "currencyCode": "USD"}},
                "refundLineItems": [{"lineItemId": "L1", "quantity": 1, "restocked": True}]
            }]
        },
        "expected": {
            "L": 11000, "D": 0, "R": 11000, "Sc": 1000, "C": 12000,
            "COGS": 4500, "S": 900, "G": 378, "E": 3250, "O": 0,
            "P": 2972, "P_upper": 2972, "margin": 24.7667,
            "class": "profitable", "classification": "profitable", "band": "acceptable", "lane": "MEASURED",
            "component_tags": {"cogs": "measured", "shipping": "measured", "gateway": "measured", "refund": "measured", "other": "structural"},
            "measured_share": "1.0000", "flags": [],
            "drivers": {"product_margin_at_list": 6500, "discount_leak": 0, "shipping_net": 100, "fee_leak": -378, "refund_leak": -3250, "other_leak": 0},
            "top_loss_driver": None, "delta_profit": -2700
        }
    },
    # D14: Refund larger than collected
    {
        "id": "D14",
        "purpose": "Refund larger than collected: total refunded 13000 > C 12000 -> flag REFUND_EXCEEDS_COLLECTED.",
        "profile": "balanced", "spec_ref": "3.2", "tag": "V-DOC",
        "arithmetic_derivation": "Refund 13000 > C 12000. E = 13000 - 4500 = 8500. P = 12000 - 4500 - 900 - 378 - 8500 = -2278. Flag REFUND_EXCEEDS_COLLECTED.",
        "input": {
            "id": "gid://shopify/Order/D14", "name": "#D14", "currencyCode": "USD", "processedAt": "2026-08-01T12:00:00Z",
            "currentShippingPriceSet": {"shopMoney": {"amount": "10.00", "currencyCode": "USD"}},
            "actual_carrier_cost": "9.00",
            "lineItems": [{
                "id": "L1", "quantity": 2, "currentQuantity": 0,
                "originalUnitPriceSet": {"shopMoney": {"amount": "55.00", "currencyCode": "USD"}},
                "variant": {"id": "V1", "inventoryItem": {"unitCost": {"amount": "22.50", "currencyCode": "USD"}}}
            }],
            "transactions": [{"id": "T1", "gateway": "shopify_payments", "fees": [{"amount": {"amount": "3.78", "currencyCode": "USD"}}]}],
            "refunds": [{
                "id": "R1", "createdAt": "2026-08-10T12:00:00Z",
                "totalRefundedSet": {"shopMoney": {"amount": "130.00", "currencyCode": "USD"}},
                "refundLineItems": [{"lineItemId": "L1", "quantity": 2, "restocked": True}]
            }]
        },
        "expected": {
            "L": 11000, "D": 0, "R": 11000, "Sc": 1000, "C": 12000,
            "COGS": 4500, "S": 900, "G": 378, "E": 8500, "O": 0,
            "P": -2278, "P_upper": -2278, "margin": -18.9833,
            "class": "unprofitable", "classification": "unprofitable", "band": "cash_drain", "lane": "MEASURED",
            "component_tags": {"cogs": "measured", "shipping": "measured", "gateway": "measured", "refund": "measured", "other": "structural"},
            "measured_share": "1.0000", "flags": ["REFUND_EXCEEDS_COLLECTED"],
            "drivers": {"product_margin_at_list": 6500, "discount_leak": 0, "shipping_net": 100, "fee_leak": -378, "refund_leak": -8500, "other_leak": 0},
            "top_loss_driver": "refund_leak", "delta_profit": -7950
        }
    },
    # D15: Provision window boundary (age 29d 23h 59m vs 30d)
    {
        "id": "D15",
        "purpose": "Window boundary precision: age 29d 23h 59m is OPEN (provision active).",
        "profile": "balanced", "spec_ref": "3.2", "tag": "V-DOC",
        "arithmetic_derivation": "Processed 2026-08-31T23:59:59Z, as_of 2026-09-30T23:59:59Z -> exactly 30 days is closed! Processed 2026-09-01T00:00:01Z -> age 29d 23h 59m 58s < 30 days -> OPEN -> E = 550, P = 5672.",
        "input": {
            "id": "gid://shopify/Order/D15", "name": "#D15", "currencyCode": "USD", "processedAt": "2026-09-01T00:00:01Z",
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
    },
    # D16: Provision rounding at ties
    {
        "id": "D16",
        "purpose": "Provision tie rounding: R = 1010 at 5% = 50.5 -> half_up rounds to 51.",
        "profile": "balanced", "spec_ref": "3.2, 4.0", "tag": "CFG",
        "arithmetic_derivation": "R = 1010. 1010 * 0.05 = 50.5 -> round half_up = 51. P = 1010 - 500 - 400 - 59 - 51 = 0.",
        "input": {
            "id": "gid://shopify/Order/D16", "name": "#D16", "currencyCode": "USD", "processedAt": "2026-09-20T12:00:00Z",
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
    },
    # D17: Provision by rate group
    {
        "id": "D17",
        "purpose": "Provision by rate group: default 5% provision applies across group.",
        "profile": "balanced", "spec_ref": "3.2", "tag": "CFG",
        "arithmetic_derivation": "L1 (apparel) R=10000, L2 (accessory) R=5000. Total R=15000 * 5% = 750. COGS=6000; S=800; G=450. P = 15000 - 6000 - 800 - 450 - 750 = 7000.",
        "input": {
            "id": "gid://shopify/Order/D17", "name": "#D17", "currencyCode": "USD", "processedAt": "2026-09-20T12:00:00Z",
            "currentShippingPriceSet": {"shopMoney": {"amount": "0.00", "currencyCode": "USD"}},
            "actual_carrier_cost": "8.00",
            "lineItems": [
                {
                    "id": "L1", "quantity": 1, "currentQuantity": 1,
                    "originalUnitPriceSet": {"shopMoney": {"amount": "100.00", "currencyCode": "USD"}},
                    "variant": {"id": "V1", "product": {"productType": "Apparel"}, "inventoryItem": {"unitCost": {"amount": "40.00", "currencyCode": "USD"}}}
                },
                {
                    "id": "L2", "quantity": 1, "currentQuantity": 1,
                    "originalUnitPriceSet": {"shopMoney": {"amount": "50.00", "currencyCode": "USD"}},
                    "variant": {"id": "V2", "product": {"productType": "Accessories"}, "inventoryItem": {"unitCost": {"amount": "20.00", "currencyCode": "USD"}}}
                }
            ],
            "transactions": [{"id": "T1", "gateway": "shopify_payments", "fees": [{"amount": {"amount": "4.50", "currencyCode": "USD"}}]}],
            "refunds": []
        },
        "expected": {
            "L": 15000, "D": 0, "R": 15000, "Sc": 0, "C": 15000,
            "COGS": 6000, "S": 800, "G": 450, "E": 750, "O": 0,
            "P": 7000, "P_upper": 7750, "margin": 46.6667,
            "class": "profitable", "classification": "profitable", "band": "high", "lane": "ESTIMATED",
            "component_tags": {"cogs": "measured", "shipping": "measured", "gateway": "measured", "refund": "estimated", "other": "structural"},
            "measured_share": "0.9062", "flags": [],
            "drivers": {"product_margin_at_list": 9000, "discount_leak": 0, "shipping_net": -800, "fee_leak": -450, "refund_leak": -750, "other_leak": 0},
            "top_loss_driver": None, "delta_profit": 0
        }
    },
    # D18: Order edit removing a line
    {
        "id": "D18",
        "purpose": "Order edit removing line before fulfillment: cause edit, qs=0, no refund term.",
        "profile": "balanced", "spec_ref": "3.1, 3.6", "tag": "UNV",
        "arithmetic_derivation": "Order edit removed L1 (quantity=1, currentQuantity=0, refunded=0 -> qe=1 -> qs=0). Sold revenue R=0, COGS=0. C=0 -> G=0 (structural zero). P = 0 - 800 - 0 = -800.",
        "input": {
            "id": "gid://shopify/Order/D18", "name": "#D18", "currencyCode": "USD", "processedAt": "2026-08-01T12:00:00Z",
            "currentShippingPriceSet": {"shopMoney": {"amount": "0.00", "currencyCode": "USD"}},
            "actual_carrier_cost": "8.00",
            "lineItems": [{
                "id": "L1", "quantity": 1, "currentQuantity": 0,
                "originalUnitPriceSet": {"shopMoney": {"amount": "100.00", "currencyCode": "USD"}},
                "variant": {"id": "V1", "inventoryItem": {"unitCost": {"amount": "40.00", "currencyCode": "USD"}}}
            }],
            "transactions": [{"id": "T1", "gateway": "shopify_payments", "fees": [{"amount": {"amount": "3.00", "currencyCode": "USD"}}]}],
            "refunds": []
        },
        "expected": {
            "L": 0, "D": 0, "R": 0, "Sc": 0, "C": 0,
            "COGS": 0, "S": 800, "G": 0, "E": 0, "O": 0,
            "P": -800, "P_upper": -800, "margin": None,
            "class": "unprofitable", "classification": "unprofitable", "band": "zero_revenue", "lane": "MEASURED",
            "component_tags": {"cogs": "measured", "shipping": "measured", "gateway": "structural", "refund": "measured", "other": "structural"},
            "measured_share": "1.0000", "flags": [],
            "drivers": {"product_margin_at_list": 0, "discount_leak": 0, "shipping_net": -800, "fee_leak": 0, "refund_leak": 0, "other_leak": 0},
            "top_loss_driver": "shipping_subsidy", "delta_profit": -6000
        }
    },
    # D19: Order edit adding a line
    {
        "id": "D19",
        "purpose": "Order edit adding a line: quantity increases.",
        "profile": "balanced", "spec_ref": "3.1, 3.6", "tag": "UNV",
        "arithmetic_derivation": "L1 original qty 1, current qty 2. qs = 2. L = 20000; COGS = 8000. P = 20000 - 8000 - 800 - 580 = 10620.",
        "input": {
            "id": "gid://shopify/Order/D19", "name": "#D19", "currencyCode": "USD", "processedAt": "2026-08-01T12:00:00Z",
            "currentShippingPriceSet": {"shopMoney": {"amount": "0.00", "currencyCode": "USD"}},
            "actual_carrier_cost": "8.00",
            "lineItems": [{
                "id": "L1", "quantity": 2, "currentQuantity": 2,
                "originalUnitPriceSet": {"shopMoney": {"amount": "100.00", "currencyCode": "USD"}},
                "variant": {"id": "V1", "inventoryItem": {"unitCost": {"amount": "40.00", "currencyCode": "USD"}}}
            }],
            "transactions": [{"id": "T1", "gateway": "shopify_payments", "fees": [{"amount": {"amount": "5.80", "currencyCode": "USD"}}]}],
            "refunds": []
        },
        "expected": {
            "L": 20000, "D": 0, "R": 20000, "Sc": 0, "C": 20000,
            "COGS": 8000, "S": 800, "G": 580, "E": 0, "O": 0,
            "P": 10620, "P_upper": 10620, "margin": 53.1,
            "class": "profitable", "classification": "profitable", "band": "high", "lane": "MEASURED",
            "component_tags": {"cogs": "measured", "shipping": "measured", "gateway": "measured", "refund": "measured", "other": "structural"},
            "measured_share": "1.0000", "flags": [],
            "drivers": {"product_margin_at_list": 12000, "discount_leak": 0, "shipping_net": -800, "fee_leak": -580, "refund_leak": 0, "other_leak": 0},
            "top_loss_driver": None, "delta_profit": 1000
        }
    },
    # D20: Exchange (return plus new line)
    {
        "id": "D20",
        "purpose": "Exchange (return plus new line): tagged PENDING until live GraphQL schema verified.",
        "profile": "balanced", "spec_ref": "3.6, 6.0", "tag": "PENDING",
        "arithmetic_derivation": "L1 original sold (qs=1, gross=6000, cogs=2400), L2 added (qs=1, gross=8000, cogs=3200). L = 14000, COGS = 5600. E = 6000 - 2400 = 3600. P = 14000 - 5600 - 800 - 260 - 3600 = 3740. Margin = 26.7143%.",
        "input": {
            "id": "gid://shopify/Order/D20", "name": "#D20", "currencyCode": "USD", "processedAt": "2026-08-01T12:00:00Z",
            "currentShippingPriceSet": {"shopMoney": {"amount": "0.00", "currencyCode": "USD"}},
            "actual_carrier_cost": "8.00",
            "lineItems": [
                {
                    "id": "L1", "quantity": 1, "currentQuantity": 0,
                    "originalUnitPriceSet": {"shopMoney": {"amount": "60.00", "currencyCode": "USD"}},
                    "variant": {"id": "V1", "inventoryItem": {"unitCost": {"amount": "24.00", "currencyCode": "USD"}}}
                },
                {
                    "id": "L2", "quantity": 1, "currentQuantity": 1,
                    "originalUnitPriceSet": {"shopMoney": {"amount": "80.00", "currencyCode": "USD"}},
                    "variant": {"id": "V2", "inventoryItem": {"unitCost": {"amount": "32.00", "currencyCode": "USD"}}}
                }
            ],
            "transactions": [{"id": "T1", "gateway": "shopify_payments", "fees": [{"amount": {"amount": "2.60", "currencyCode": "USD"}}]}],
            "refunds": [{
                "id": "R1", "createdAt": "2026-08-10T12:00:00Z",
                "totalRefundedSet": {"shopMoney": {"amount": "60.00", "currencyCode": "USD"}},
                "refundLineItems": [{"lineItemId": "L1", "quantity": 1, "restocked": True}]
            }]
        },
        "expected": {
            "L": 14000, "D": 0, "R": 14000, "Sc": 0, "C": 14000,
            "COGS": 5600, "S": 800, "G": 260, "E": 3600, "O": 0,
            "P": 3740, "P_upper": 3740, "margin": 26.7143,
            "class": "profitable", "classification": "profitable", "band": "acceptable", "lane": "MEASURED",
            "component_tags": {"cogs": "measured", "shipping": "measured", "gateway": "measured", "refund": "measured", "other": "structural"},
            "measured_share": "1.0000", "flags": [],
            "drivers": {"product_margin_at_list": 8400, "discount_leak": 0, "shipping_net": -800, "fee_leak": -260, "refund_leak": -3600, "other_leak": 0},
            "top_loss_driver": None, "delta_profit": -3600
        }
    },
    # D21: Restatement (order final at day 31 receives refund at day 40)
    {
        "id": "D21",
        "purpose": "Restatement: order final at day 31 receives refund at day 40, recomputed with versioning.",
        "profile": "balanced", "spec_ref": "3.6, 6.0", "tag": "V-DOC",
        "arithmetic_derivation": "Order processed 2026-08-01 (closed at day 30). Refund on day 40 (2026-09-10) is realized: E = 6500. P = -278.",
        "input": {
            "id": "gid://shopify/Order/D21", "name": "#D21", "currencyCode": "USD", "processedAt": "2026-08-01T12:00:00Z",
            "currentShippingPriceSet": {"shopMoney": {"amount": "10.00", "currencyCode": "USD"}},
            "actual_carrier_cost": "9.00",
            "lineItems": [{
                "id": "L1", "quantity": 2, "currentQuantity": 0,
                "originalUnitPriceSet": {"shopMoney": {"amount": "55.00", "currencyCode": "USD"}},
                "variant": {"id": "V1", "inventoryItem": {"unitCost": {"amount": "22.50", "currencyCode": "USD"}}}
            }],
            "transactions": [{"id": "T1", "gateway": "shopify_payments", "fees": [{"amount": {"amount": "3.78", "currencyCode": "USD"}}]}],
            "refunds": [{
                "id": "R1", "createdAt": "2026-09-10T12:00:00Z",
                "totalRefundedSet": {"shopMoney": {"amount": "110.00", "currencyCode": "USD"}},
                "refundLineItems": [{"lineItemId": "L1", "quantity": 2, "restocked": True}]
            }]
        },
        "expected": {
            "L": 11000, "D": 0, "R": 11000, "Sc": 1000, "C": 12000,
            "COGS": 4500, "S": 900, "G": 378, "E": 6500, "O": 0,
            "P": -278, "P_upper": -278, "margin": -2.3167,
            "class": "unprofitable", "classification": "unprofitable", "band": "cash_drain", "lane": "MEASURED",
            "component_tags": {"cogs": "measured", "shipping": "measured", "gateway": "measured", "refund": "measured", "other": "structural"},
            "measured_share": "1.0000", "flags": [],
            "drivers": {"product_margin_at_list": 6500, "discount_leak": 0, "shipping_net": 100, "fee_leak": -378, "refund_leak": -6500, "other_leak": 0},
            "top_loss_driver": "refund_leak", "delta_profit": -5950
        }
    },
    # D22: Boundary case: exactly 30 days
    {
        "id": "D22",
        "purpose": "Window boundary: exactly 30 days is CLOSED (age >= 30d -> provision 0).",
        "profile": "balanced", "spec_ref": "3.2", "tag": "V-DOC",
        "arithmetic_derivation": "Processed 2026-08-31T23:59:59Z, as_of 2026-09-30T23:59:59Z -> exactly 30 days is CLOSED per spec -> E = 0. P = 6222. Lane = MEASURED.",
        "input": {
            "id": "gid://shopify/Order/D22", "name": "#D22", "currencyCode": "USD", "processedAt": "2026-08-31T23:59:59Z",
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
            "COGS": 4500, "S": 900, "G": 378, "E": 0, "O": 0,
            "P": 6222, "P_upper": 6222, "margin": 51.85,
            "class": "profitable", "classification": "profitable", "band": "high", "lane": "MEASURED",
            "component_tags": {"cogs": "measured", "shipping": "measured", "gateway": "measured", "refund": "measured", "other": "structural"},
            "measured_share": "1.0000", "flags": [],
            "drivers": {"product_margin_at_list": 6500, "discount_leak": 0, "shipping_net": 100, "fee_leak": -378, "refund_leak": 0, "other_leak": 0},
            "top_loss_driver": None, "delta_profit": 550
        }
    }
]
