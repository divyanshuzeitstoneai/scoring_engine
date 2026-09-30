"""
Scenario Group A: Discounts and Revenue (A01 - A18).
All amounts integer minor units. Hand-derived expected values.
"""

from typing import Dict, Any, List

group_a_fixtures: List[Dict[str, Any]] = [
    {
        "id": "A01",
        "purpose": "Single line, no discount. Standard merchandise revenue.",
        "profile": "balanced", "spec_ref": "3.1, 3.2", "tag": "V-DOC",
        "arithmetic_derivation": "L = 10000; D = 0; R = 10000; Sc = 0; C = 10000. COGS = 5000; S = 1000; G = 320; E = 0; O = 0. P = 3680. Margin = 36.80% (high).",
        "input": {
            "id": "gid://shopify/Order/A01", "name": "#A01", "currencyCode": "USD", "processedAt": "2026-08-01T12:00:00Z",
            "currentShippingPriceSet": {"shopMoney": {"amount": "0.00", "currencyCode": "USD"}},
            "actual_carrier_cost": "10.00",
            "lineItems": [{
                "id": "L1", "quantity": 1, "currentQuantity": 1,
                "originalUnitPriceSet": {"shopMoney": {"amount": "100.00", "currencyCode": "USD"}},
                "discountAllocations": [],
                "variant": {"id": "V1", "inventoryItem": {"unitCost": {"amount": "50.00", "currencyCode": "USD"}}}
            }],
            "transactions": [{"id": "T1", "gateway": "shopify_payments", "fees": [{"amount": {"amount": "3.20", "currencyCode": "USD"}}]}],
            "refunds": []
        },
        "expected": {
            "L": 10000, "D": 0, "R": 10000, "Sc": 0, "C": 10000,
            "COGS": 5000, "S": 1000, "G": 320, "E": 0, "O": 0,
            "P": 3680, "P_upper": 3680, "margin": 36.8,
            "class": "profitable", "classification": "profitable", "band": "high", "lane": "MEASURED",
            "component_tags": {"cogs": "measured", "shipping": "measured", "gateway": "measured", "refund": "measured", "other": "structural"},
            "measured_share": "1.0000", "flags": [],
            "drivers": {"product_margin_at_list": 5000, "discount_leak": 0, "shipping_net": -1000, "fee_leak": -320, "refund_leak": 0, "other_leak": 0},
            "top_loss_driver": None, "delta_profit": 500
        }
    },
    {
        "id": "A02",
        "purpose": "Line-level discount: $100 price with $20 discount.",
        "profile": "balanced", "spec_ref": "3.1, 3.2", "tag": "V-DOC",
        "arithmetic_derivation": "L = 10000; D = 2000; R = 8000; Sc = 1000; C = 9000. COGS = 4000; S = 1000; G = 290; E = 0; O = 0. P = 3710. Margin = 41.22% (high).",
        "input": {
            "id": "gid://shopify/Order/A02", "name": "#A02", "currencyCode": "USD", "processedAt": "2026-08-01T12:00:00Z",
            "currentShippingPriceSet": {"shopMoney": {"amount": "10.00", "currencyCode": "USD"}},
            "actual_carrier_cost": "10.00",
            "lineItems": [{
                "id": "L1", "quantity": 1, "currentQuantity": 1,
                "originalUnitPriceSet": {"shopMoney": {"amount": "100.00", "currencyCode": "USD"}},
                "discountAllocations": [{"allocatedAmountSet": {"shopMoney": {"amount": "20.00", "currencyCode": "USD"}}}],
                "variant": {"id": "V1", "inventoryItem": {"unitCost": {"amount": "40.00", "currencyCode": "USD"}}}
            }],
            "transactions": [{"id": "T1", "gateway": "shopify_payments", "fees": [{"amount": {"amount": "2.90", "currencyCode": "USD"}}]}],
            "refunds": []
        },
        "expected": {
            "L": 10000, "D": 2000, "R": 8000, "Sc": 1000, "C": 9000,
            "COGS": 4000, "S": 1000, "G": 290, "E": 0, "O": 0,
            "P": 3710, "P_upper": 3710, "margin": 41.2222,
            "class": "profitable", "classification": "profitable", "band": "high", "lane": "MEASURED",
            "component_tags": {"cogs": "measured", "shipping": "measured", "gateway": "measured", "refund": "measured", "other": "structural"},
            "measured_share": "1.0000", "flags": [],
            "drivers": {"product_margin_at_list": 6000, "discount_leak": -2000, "shipping_net": 0, "fee_leak": -290, "refund_leak": 0, "other_leak": 0},
            "top_loss_driver": None, "delta_profit": 400
        }
    },
    {
        "id": "A03",
        "purpose": "Order-level percentage code discount: 20% off across 2 lines.",
        "profile": "balanced", "spec_ref": "3.1, 3.2", "tag": "V-DOC",
        "arithmetic_derivation": "L = 10000; D = 2000; R = 8000; Sc = 0; C = 8000. COGS = 4500; S = 800; G = 260; E = 0; O = 0. P = 2440. Margin = 30.50% (high).",
        "input": {
            "id": "gid://shopify/Order/A03", "name": "#A03", "currencyCode": "USD", "processedAt": "2026-08-01T12:00:00Z",
            "currentShippingPriceSet": {"shopMoney": {"amount": "0.00", "currencyCode": "USD"}},
            "actual_carrier_cost": "8.00",
            "lineItems": [
                {
                    "id": "L1", "quantity": 1, "currentQuantity": 1,
                    "originalUnitPriceSet": {"shopMoney": {"amount": "30.00", "currencyCode": "USD"}},
                    "discountAllocations": [{"allocatedAmountSet": {"shopMoney": {"amount": "6.00", "currencyCode": "USD"}}}],
                    "variant": {"id": "V1", "inventoryItem": {"unitCost": {"amount": "15.00", "currencyCode": "USD"}}}
                },
                {
                    "id": "L2", "quantity": 1, "currentQuantity": 1,
                    "originalUnitPriceSet": {"shopMoney": {"amount": "70.00", "currencyCode": "USD"}},
                    "discountAllocations": [{"allocatedAmountSet": {"shopMoney": {"amount": "14.00", "currencyCode": "USD"}}}],
                    "variant": {"id": "V2", "inventoryItem": {"unitCost": {"amount": "30.00", "currencyCode": "USD"}}}
                }
            ],
            "transactions": [{"id": "T1", "gateway": "shopify_payments", "fees": [{"amount": {"amount": "2.60", "currencyCode": "USD"}}]}],
            "refunds": []
        },
        "expected": {
            "L": 10000, "D": 2000, "R": 8000, "Sc": 0, "C": 8000,
            "COGS": 4500, "S": 800, "G": 260, "E": 0, "O": 0,
            "P": 2440, "P_upper": 2440, "margin": 30.5,
            "class": "profitable", "classification": "profitable", "band": "high", "lane": "MEASURED",
            "component_tags": {"cogs": "measured", "shipping": "measured", "gateway": "measured", "refund": "measured", "other": "structural"},
            "measured_share": "1.0000", "flags": [],
            "drivers": {"product_margin_at_list": 5500, "discount_leak": -2000, "shipping_net": -800, "fee_leak": -260, "refund_leak": 0, "other_leak": 0},
            "top_loss_driver": None, "delta_profit": 400
        }
    },
    {
        "id": "A04",
        "purpose": "Order-level fixed code discount: $15 split $4.50 and $10.50.",
        "profile": "balanced", "spec_ref": "3.1, 3.2", "tag": "V-DOC",
        "arithmetic_derivation": "L = 10000; D = 1500; R = 8500; Sc = 0; C = 8500. COGS = 4500; S = 800; G = 275; E = 0; O = 0. P = 2925. Margin = 34.41% (high).",
        "input": {
            "id": "gid://shopify/Order/A04", "name": "#A04", "currencyCode": "USD", "processedAt": "2026-08-01T12:00:00Z",
            "currentShippingPriceSet": {"shopMoney": {"amount": "0.00", "currencyCode": "USD"}},
            "actual_carrier_cost": "8.00",
            "lineItems": [
                {
                    "id": "L1", "quantity": 1, "currentQuantity": 1,
                    "originalUnitPriceSet": {"shopMoney": {"amount": "30.00", "currencyCode": "USD"}},
                    "discountAllocations": [{"allocatedAmountSet": {"shopMoney": {"amount": "4.50", "currencyCode": "USD"}}}],
                    "variant": {"id": "V1", "inventoryItem": {"unitCost": {"amount": "15.00", "currencyCode": "USD"}}}
                },
                {
                    "id": "L2", "quantity": 1, "currentQuantity": 1,
                    "originalUnitPriceSet": {"shopMoney": {"amount": "70.00", "currencyCode": "USD"}},
                    "discountAllocations": [{"allocatedAmountSet": {"shopMoney": {"amount": "10.50", "currencyCode": "USD"}}}],
                    "variant": {"id": "V2", "inventoryItem": {"unitCost": {"amount": "30.00", "currencyCode": "USD"}}}
                }
            ],
            "transactions": [{"id": "T1", "gateway": "shopify_payments", "fees": [{"amount": {"amount": "2.75", "currencyCode": "USD"}}]}],
            "refunds": []
        },
        "expected": {
            "L": 10000, "D": 1500, "R": 8500, "Sc": 0, "C": 8500,
            "COGS": 4500, "S": 800, "G": 275, "E": 0, "O": 0,
            "P": 2925, "P_upper": 2925, "margin": 34.4118,
            "class": "profitable", "classification": "profitable", "band": "high", "lane": "MEASURED",
            "component_tags": {"cogs": "measured", "shipping": "measured", "gateway": "measured", "refund": "measured", "other": "structural"},
            "measured_share": "1.0000", "flags": [],
            "drivers": {"product_margin_at_list": 5500, "discount_leak": -1500, "shipping_net": -800, "fee_leak": -275, "refund_leak": 0, "other_leak": 0},
            "top_loss_driver": None, "delta_profit": 425
        }
    },
    {
        "id": "A05",
        "purpose": "Stacked line-level and order-level discount allocations.",
        "profile": "balanced", "spec_ref": "3.1, 3.2", "tag": "V-DOC",
        "arithmetic_derivation": "Line 1: u=10000, disc: $10 line + $15 order = $25 (2500). L = 10000; D = 2500; R = 7500; Sc = 500; C = 8000. COGS = 3500; S = 600; G = 260; E = 0; O = 0. P = 3640. Margin = 45.50% (high).",
        "input": {
            "id": "gid://shopify/Order/A05", "name": "#A05", "currencyCode": "USD", "processedAt": "2026-08-01T12:00:00Z",
            "currentShippingPriceSet": {"shopMoney": {"amount": "5.00", "currencyCode": "USD"}},
            "actual_carrier_cost": "6.00",
            "lineItems": [{
                "id": "L1", "quantity": 1, "currentQuantity": 1,
                "originalUnitPriceSet": {"shopMoney": {"amount": "100.00", "currencyCode": "USD"}},
                "discountAllocations": [
                    {"allocatedAmountSet": {"shopMoney": {"amount": "10.00", "currencyCode": "USD"}}},
                    {"allocatedAmountSet": {"shopMoney": {"amount": "15.00", "currencyCode": "USD"}}}
                ],
                "variant": {"id": "V1", "inventoryItem": {"unitCost": {"amount": "35.00", "currencyCode": "USD"}}}
            }],
            "transactions": [{"id": "T1", "gateway": "shopify_payments", "fees": [{"amount": {"amount": "2.60", "currencyCode": "USD"}}]}],
            "refunds": []
        },
        "expected": {
            "L": 10000, "D": 2500, "R": 7500, "Sc": 500, "C": 8000,
            "COGS": 3500, "S": 600, "G": 260, "E": 0, "O": 0,
            "P": 3640, "P_upper": 3640, "margin": 45.5,
            "class": "profitable", "classification": "profitable", "band": "high", "lane": "MEASURED",
            "component_tags": {"cogs": "measured", "shipping": "measured", "gateway": "measured", "refund": "measured", "other": "structural"},
            "measured_share": "1.0000", "flags": [],
            "drivers": {"product_margin_at_list": 6500, "discount_leak": -2500, "shipping_net": -100, "fee_leak": -260, "refund_leak": 0, "other_leak": 0},
            "top_loss_driver": None, "delta_profit": 375
        }
    },
    {
        "id": "A06",
        "purpose": "Free shipping promo (100% shipping discount): Sc = 0 with real carrier cost.",
        "profile": "balanced", "spec_ref": "3.1, 3.2", "tag": "V-DOC",
        "arithmetic_derivation": "L = 5000; D = 0; R = 5000; Sc = 0; C = 5000. COGS = 2000; S = 900; G = 175; E = 0; O = 0. P = 1925. Margin = 38.50% (high).",
        "input": {
            "id": "gid://shopify/Order/A06", "name": "#A06", "currencyCode": "USD", "processedAt": "2026-08-01T12:00:00Z",
            "currentShippingPriceSet": {"shopMoney": {"amount": "0.00", "currencyCode": "USD"}},
            "actual_carrier_cost": "9.00",
            "lineItems": [{
                "id": "L1", "quantity": 1, "currentQuantity": 1,
                "originalUnitPriceSet": {"shopMoney": {"amount": "50.00", "currencyCode": "USD"}},
                "discountAllocations": [],
                "variant": {"id": "V1", "inventoryItem": {"unitCost": {"amount": "20.00", "currencyCode": "USD"}}}
            }],
            "transactions": [{"id": "T1", "gateway": "shopify_payments", "fees": [{"amount": {"amount": "1.75", "currencyCode": "USD"}}]}],
            "refunds": []
        },
        "expected": {
            "L": 5000, "D": 0, "R": 5000, "Sc": 0, "C": 5000,
            "COGS": 2000, "S": 900, "G": 175, "E": 0, "O": 0,
            "P": 1925, "P_upper": 1925, "margin": 38.5,
            "class": "profitable", "classification": "profitable", "band": "high", "lane": "MEASURED",
            "component_tags": {"cogs": "measured", "shipping": "measured", "gateway": "measured", "refund": "measured", "other": "structural"},
            "measured_share": "1.0000", "flags": [],
            "drivers": {"product_margin_at_list": 3000, "discount_leak": 0, "shipping_net": -900, "fee_leak": -175, "refund_leak": 0, "other_leak": 0},
            "top_loss_driver": None, "delta_profit": 250
        }
    },
    {
        "id": "A07",
        "purpose": "Partial shipping discount: $10 shipping discounted by $4 -> Sc = $6.",
        "profile": "balanced", "spec_ref": "3.1, 3.2", "tag": "V-DOC",
        "arithmetic_derivation": "L = 5000; D = 0; R = 5000; Sc = 600; C = 5600. COGS = 2000; S = 800; G = 190; E = 0; O = 0. P = 2610. Margin = 46.61% (high).",
        "input": {
            "id": "gid://shopify/Order/A07", "name": "#A07", "currencyCode": "USD", "processedAt": "2026-08-01T12:00:00Z",
            "currentShippingPriceSet": {"shopMoney": {"amount": "6.00", "currencyCode": "USD"}},
            "actual_carrier_cost": "8.00",
            "lineItems": [{
                "id": "L1", "quantity": 1, "currentQuantity": 1,
                "originalUnitPriceSet": {"shopMoney": {"amount": "50.00", "currencyCode": "USD"}},
                "discountAllocations": [],
                "variant": {"id": "V1", "inventoryItem": {"unitCost": {"amount": "20.00", "currencyCode": "USD"}}}
            }],
            "transactions": [{"id": "T1", "gateway": "shopify_payments", "fees": [{"amount": {"amount": "1.90", "currencyCode": "USD"}}]}],
            "refunds": []
        },
        "expected": {
            "L": 5000, "D": 0, "R": 5000, "Sc": 600, "C": 5600,
            "COGS": 2000, "S": 800, "G": 190, "E": 0, "O": 0,
            "P": 2610, "P_upper": 2610, "margin": 46.6071,
            "class": "profitable", "classification": "profitable", "band": "high", "lane": "MEASURED",
            "component_tags": {"cogs": "measured", "shipping": "measured", "gateway": "measured", "refund": "measured", "other": "structural"},
            "measured_share": "1.0000", "flags": [],
            "drivers": {"product_margin_at_list": 3000, "discount_leak": 0, "shipping_net": -200, "fee_leak": -190, "refund_leak": 0, "other_leak": 0},
            "top_loss_driver": None, "delta_profit": 250
        }
    },
    {
        "id": "A08",
        "purpose": "Free-gift line item at price 0 with positive cost.",
        "profile": "balanced", "spec_ref": "3.1, 3.2", "tag": "V-DOC",
        "arithmetic_derivation": "Line 1: u=5000, cost=2000. Line 2 (gift): u=0, cost=500. COGS = 2500. L = 5000; D = 0; R = 5000; Sc = 0; C = 5000. S = 800; G = 175; E = 0; O = 0. P = 1525. Margin = 30.50% (high).",
        "input": {
            "id": "gid://shopify/Order/A08", "name": "#A08", "currencyCode": "USD", "processedAt": "2026-08-01T12:00:00Z",
            "currentShippingPriceSet": {"shopMoney": {"amount": "0.00", "currencyCode": "USD"}},
            "actual_carrier_cost": "8.00",
            "lineItems": [
                {
                    "id": "L1", "quantity": 1, "currentQuantity": 1,
                    "originalUnitPriceSet": {"shopMoney": {"amount": "50.00", "currencyCode": "USD"}},
                    "discountAllocations": [],
                    "variant": {"id": "V1", "inventoryItem": {"unitCost": {"amount": "20.00", "currencyCode": "USD"}}}
                },
                {
                    "id": "L2", "quantity": 1, "currentQuantity": 1,
                    "originalUnitPriceSet": {"shopMoney": {"amount": "0.00", "currencyCode": "USD"}},
                    "discountAllocations": [],
                    "variant": {"id": "V2", "inventoryItem": {"unitCost": {"amount": "5.00", "currencyCode": "USD"}}}
                }
            ],
            "transactions": [{"id": "T1", "gateway": "shopify_payments", "fees": [{"amount": {"amount": "1.75", "currencyCode": "USD"}}]}],
            "refunds": []
        },
        "expected": {
            "L": 5000, "D": 0, "R": 5000, "Sc": 0, "C": 5000,
            "COGS": 2500, "S": 800, "G": 175, "E": 0, "O": 0,
            "P": 1525, "P_upper": 1525, "margin": 30.5,
            "class": "profitable", "classification": "profitable", "band": "high", "lane": "MEASURED",
            "component_tags": {"cogs": "measured", "shipping": "measured", "gateway": "measured", "refund": "measured", "other": "structural"},
            "measured_share": "1.0000", "flags": [],
            "drivers": {"product_margin_at_list": 2500, "discount_leak": 0, "shipping_net": -800, "fee_leak": -175, "refund_leak": 0, "other_leak": 0},
            "top_loss_driver": None, "delta_profit": 250
        }
    },
    {
        "id": "A09",
        "purpose": "Discount larger than line value: clamped net.",
        "profile": "balanced", "spec_ref": "3.1, 3.2", "tag": "V-DOC",
        "arithmetic_derivation": "Gross = 1000, discount = 1200 -> clamped D = 1000, R = 0. C = 0. COGS = 400; S = 500; G = 0; E = 0; O = 0. P = -900. Zero revenue -> margin = None, band = zero_revenue.",
        "input": {
            "id": "gid://shopify/Order/A09", "name": "#A09", "currencyCode": "USD", "processedAt": "2026-08-01T12:00:00Z",
            "currentShippingPriceSet": {"shopMoney": {"amount": "0.00", "currencyCode": "USD"}},
            "actual_carrier_cost": "5.00",
            "lineItems": [{
                "id": "L1", "quantity": 1, "currentQuantity": 1,
                "originalUnitPriceSet": {"shopMoney": {"amount": "10.00", "currencyCode": "USD"}},
                "discountAllocations": [{"allocatedAmountSet": {"shopMoney": {"amount": "12.00", "currencyCode": "USD"}}}],
                "variant": {"id": "V1", "inventoryItem": {"unitCost": {"amount": "4.00", "currencyCode": "USD"}}}
            }],
            "transactions": [], "refunds": [],
            "paymentGatewayNames": ["manual"]
        },
        "expected": {
            "L": 1000, "D": 1200, "R": -200, "Sc": 0, "C": -200,
            "COGS": 400, "S": 500, "G": 0, "E": 0, "O": 0,
            "P": -1100, "P_upper": -1100, "margin": 550.0,
            "class": "unprofitable", "classification": "unprofitable", "band": "cash_drain", "lane": "MEASURED",
            "component_tags": {"cogs": "measured", "shipping": "measured", "gateway": "structural", "refund": "measured", "other": "structural"},
            "measured_share": "1.0000", "flags": [],
            "drivers": {"product_margin_at_list": 600, "discount_leak": -1200, "shipping_net": -500, "fee_leak": 0, "refund_leak": 0, "other_leak": 0},
            "top_loss_driver": "discount_leak", "delta_profit": -10
        }
    },
    {
        "id": "A10",
        "purpose": "Discount on a line where units were removed: proration by qs/q0.",
        "profile": "balanced", "spec_ref": "3.1, 3.2", "tag": "V-DOC",
        "arithmetic_derivation": "q0 = 2, qc = 1, ref = 0 -> qe = 1, qs = 1. disc = 1000 * 1/2 = 500. L = 5000; D = 500; R = 4500; Sc = 0; C = 4500. COGS = 2000; S = 600; G = 160; E = 0; O = 0. P = 1740. Margin = 38.67% (high).",
        "input": {
            "id": "gid://shopify/Order/A10", "name": "#A10", "currencyCode": "USD", "processedAt": "2026-08-01T12:00:00Z",
            "currentShippingPriceSet": {"shopMoney": {"amount": "0.00", "currencyCode": "USD"}},
            "actual_carrier_cost": "6.00",
            "lineItems": [{
                "id": "L1", "quantity": 2, "currentQuantity": 1,
                "originalUnitPriceSet": {"shopMoney": {"amount": "50.00", "currencyCode": "USD"}},
                "discountAllocations": [{"allocatedAmountSet": {"shopMoney": {"amount": "10.00", "currencyCode": "USD"}}}],
                "variant": {"id": "V1", "inventoryItem": {"unitCost": {"amount": "20.00", "currencyCode": "USD"}}}
            }],
            "transactions": [{"id": "T1", "gateway": "shopify_payments", "fees": [{"amount": {"amount": "1.60", "currencyCode": "USD"}}]}],
            "refunds": []
        },
        "expected": {
            "L": 5000, "D": 500, "R": 4500, "Sc": 0, "C": 4500,
            "COGS": 2000, "S": 600, "G": 160, "E": 0, "O": 0,
            "P": 1740, "P_upper": 1740, "margin": 38.6667,
            "class": "profitable", "classification": "profitable", "band": "high", "lane": "MEASURED",
            "component_tags": {"cogs": "measured", "shipping": "measured", "gateway": "measured", "refund": "measured", "other": "structural"},
            "measured_share": "1.0000", "flags": [],
            "drivers": {"product_margin_at_list": 3000, "discount_leak": -500, "shipping_net": -600, "fee_leak": -160, "refund_leak": 0, "other_leak": 0},
            "top_loss_driver": None, "delta_profit": -1540
        }
    },
    {
        "id": "A11",
        "purpose": "Proration rounding tie under half_up.",
        "profile": "balanced", "spec_ref": "3.1, 3.2", "tag": "CFG",
        "arithmetic_derivation": "q0 = 2, qs = 1. disc = 501 -> 501 / 2 = 250.5 -> half_up gives 251. L = 5000; D = 251; R = 4749; Sc = 0; C = 4749. COGS = 2000; S = 600; G = 168; E = 0; O = 0. P = 1981. Margin = 41.71% (high).",
        "input": {
            "id": "gid://shopify/Order/A11", "name": "#A11", "currencyCode": "USD", "processedAt": "2026-08-01T12:00:00Z",
            "currentShippingPriceSet": {"shopMoney": {"amount": "0.00", "currencyCode": "USD"}},
            "actual_carrier_cost": "6.00",
            "lineItems": [{
                "id": "L1", "quantity": 2, "currentQuantity": 1,
                "originalUnitPriceSet": {"shopMoney": {"amount": "50.00", "currencyCode": "USD"}},
                "discountAllocations": [{"allocatedAmountSet": {"shopMoney": {"amount": "5.01", "currencyCode": "USD"}}}],
                "variant": {"id": "V1", "inventoryItem": {"unitCost": {"amount": "20.00", "currencyCode": "USD"}}}
            }],
            "transactions": [{"id": "T1", "gateway": "shopify_payments", "fees": [{"amount": {"amount": "1.68", "currencyCode": "USD"}}]}],
            "refunds": []
        },
        "expected": {
            "L": 5000, "D": 251, "R": 4749, "Sc": 0, "C": 4749,
            "COGS": 2000, "S": 600, "G": 168, "E": 0, "O": 0,
            "P": 1981, "P_upper": 1981, "margin": 41.7140,
            "class": "profitable", "classification": "profitable", "band": "high", "lane": "MEASURED",
            "component_tags": {"cogs": "measured", "shipping": "measured", "gateway": "measured", "refund": "measured", "other": "structural"},
            "measured_share": "1.0000", "flags": [],
            "drivers": {"product_margin_at_list": 3000, "discount_leak": -251, "shipping_net": -600, "fee_leak": -168, "refund_leak": 0, "other_leak": 0},
            "top_loss_driver": None, "delta_profit": -1805
        }
    },
    {
        "id": "A12",
        "purpose": "Proration rounding tie under half_even.",
        "profile": "half_even", "spec_ref": "3.1, 3.2", "tag": "CFG",
        "arithmetic_derivation": "half_even rounding: 501 / 2 = 250.5 -> round to even gives 250. L = 5000; D = 250; R = 4750; Sc = 0; C = 4750. COGS = 2000; S = 600; G = 168; E = 0; O = 0. P = 1982. Margin = 41.73% (high).",
        "input": {
            "id": "gid://shopify/Order/A12", "name": "#A12", "currencyCode": "USD", "processedAt": "2026-08-01T12:00:00Z",
            "currentShippingPriceSet": {"shopMoney": {"amount": "0.00", "currencyCode": "USD"}},
            "actual_carrier_cost": "6.00",
            "lineItems": [{
                "id": "L1", "quantity": 2, "currentQuantity": 1,
                "originalUnitPriceSet": {"shopMoney": {"amount": "50.00", "currencyCode": "USD"}},
                "discountAllocations": [{"allocatedAmountSet": {"shopMoney": {"amount": "5.01", "currencyCode": "USD"}}}],
                "variant": {"id": "V1", "inventoryItem": {"unitCost": {"amount": "20.00", "currencyCode": "USD"}}}
            }],
            "transactions": [{"id": "T1", "gateway": "shopify_payments", "fees": [{"amount": {"amount": "1.68", "currencyCode": "USD"}}]}],
            "refunds": []
        },
        "expected": {
            "L": 5000, "D": 250, "R": 4750, "Sc": 0, "C": 4750,
            "COGS": 2000, "S": 600, "G": 168, "E": 0, "O": 0,
            "P": 1982, "P_upper": 1982, "margin": 41.7263,
            "class": "profitable", "classification": "profitable", "band": "high", "lane": "MEASURED",
            "component_tags": {"cogs": "measured", "shipping": "measured", "gateway": "measured", "refund": "measured", "other": "structural"},
            "measured_share": "1.0000", "flags": [],
            "drivers": {"product_margin_at_list": 3000, "discount_leak": -250, "shipping_net": -600, "fee_leak": -168, "refund_leak": 0, "other_leak": 0},
            "top_loss_driver": None, "delta_profit": -1805
        }
    },
    {
        "id": "A13",
        "purpose": "Allocation conservation across 3 lines: parts sum to parent.",
        "profile": "balanced", "spec_ref": "3.1, 3.2", "tag": "V-DOC",
        "arithmetic_derivation": "3 lines with discounts 333, 333, 334. Total D = 1000. L = 9000; D = 1000; R = 8000; Sc = 0; C = 8000. COGS = 3600; S = 700; G = 260; E = 0; O = 0. P = 3440. Margin = 43.00% (high).",
        "input": {
            "id": "gid://shopify/Order/A13", "name": "#A13", "currencyCode": "USD", "processedAt": "2026-08-01T12:00:00Z",
            "currentShippingPriceSet": {"shopMoney": {"amount": "0.00", "currencyCode": "USD"}},
            "actual_carrier_cost": "7.00",
            "lineItems": [
                {
                    "id": "L1", "quantity": 1, "currentQuantity": 1,
                    "originalUnitPriceSet": {"shopMoney": {"amount": "30.00", "currencyCode": "USD"}},
                    "discountAllocations": [{"allocatedAmountSet": {"shopMoney": {"amount": "3.33", "currencyCode": "USD"}}}],
                    "variant": {"id": "V1", "inventoryItem": {"unitCost": {"amount": "12.00", "currencyCode": "USD"}}}
                },
                {
                    "id": "L2", "quantity": 1, "currentQuantity": 1,
                    "originalUnitPriceSet": {"shopMoney": {"amount": "30.00", "currencyCode": "USD"}},
                    "discountAllocations": [{"allocatedAmountSet": {"shopMoney": {"amount": "3.33", "currencyCode": "USD"}}}],
                    "variant": {"id": "V2", "inventoryItem": {"unitCost": {"amount": "12.00", "currencyCode": "USD"}}}
                },
                {
                    "id": "L3", "quantity": 1, "currentQuantity": 1,
                    "originalUnitPriceSet": {"shopMoney": {"amount": "30.00", "currencyCode": "USD"}},
                    "discountAllocations": [{"allocatedAmountSet": {"shopMoney": {"amount": "3.34", "currencyCode": "USD"}}}],
                    "variant": {"id": "V3", "inventoryItem": {"unitCost": {"amount": "12.00", "currencyCode": "USD"}}}
                }
            ],
            "transactions": [{"id": "T1", "gateway": "shopify_payments", "fees": [{"amount": {"amount": "2.60", "currencyCode": "USD"}}]}],
            "refunds": []
        },
        "expected": {
            "L": 9000, "D": 1000, "R": 8000, "Sc": 0, "C": 8000,
            "COGS": 3600, "S": 700, "G": 260, "E": 0, "O": 0,
            "P": 3440, "P_upper": 3440, "margin": 43.0,
            "class": "profitable", "classification": "profitable", "band": "high", "lane": "MEASURED",
            "component_tags": {"cogs": "measured", "shipping": "measured", "gateway": "measured", "refund": "measured", "other": "structural"},
            "measured_share": "1.0000", "flags": [],
            "drivers": {"product_margin_at_list": 5400, "discount_leak": -1000, "shipping_net": -700, "fee_leak": -260, "refund_leak": 0, "other_leak": 0},
            "top_loss_driver": None, "delta_profit": 400
        }
    },
    {
        "id": "A14",
        "purpose": "Gift card line excluded from merchandise revenue and COGS.",
        "profile": "balanced", "spec_ref": "3.1, 3.2", "tag": "V-DOC",
        "arithmetic_derivation": "Gift card excluded. L = 5000; D = 0; R = 5000; Sc = 0; C = 5000. COGS = 2000; S = 600; G = 160; E = 0; O = 0. P = 2240. Margin = 44.80% (high).",
        "input": {
            "id": "gid://shopify/Order/A14", "name": "#A14", "currencyCode": "USD", "processedAt": "2026-08-01T12:00:00Z",
            "currentShippingPriceSet": {"shopMoney": {"amount": "0.00", "currencyCode": "USD"}},
            "actual_carrier_cost": "6.00",
            "lineItems": [
                {
                    "id": "L1", "quantity": 1, "currentQuantity": 1,
                    "originalUnitPriceSet": {"shopMoney": {"amount": "50.00", "currencyCode": "USD"}},
                    "discountAllocations": [],
                    "variant": {"id": "V1", "inventoryItem": {"unitCost": {"amount": "20.00", "currencyCode": "USD"}}}
                },
                {
                    "id": "GC", "quantity": 1, "currentQuantity": 1, "isGiftCard": True,
                    "originalUnitPriceSet": {"shopMoney": {"amount": "25.00", "currencyCode": "USD"}},
                    "discountAllocations": []
                }
            ],
            "transactions": [{"id": "T1", "gateway": "shopify_payments", "fees": [{"amount": {"amount": "1.60", "currencyCode": "USD"}}]}],
            "refunds": []
        },
        "expected": {
            "L": 5000, "D": 0, "R": 5000, "Sc": 0, "C": 5000,
            "COGS": 2000, "S": 600, "G": 160, "E": 0, "O": 0,
            "P": 2240, "P_upper": 2240, "margin": 44.8,
            "class": "profitable", "classification": "profitable", "band": "high", "lane": "MEASURED",
            "component_tags": {"cogs": "measured", "shipping": "measured", "gateway": "measured", "refund": "measured", "other": "structural"},
            "measured_share": "1.0000", "flags": [],
            "drivers": {"product_margin_at_list": 3000, "discount_leak": 0, "shipping_net": -600, "fee_leak": -160, "refund_leak": 0, "other_leak": 0},
            "top_loss_driver": None, "delta_profit": 250
        }
    },
    {
        "id": "A15",
        "purpose": "Custom line item without variant: revenue included, cost missing.",
        "profile": "balanced", "spec_ref": "3.1, 3.2", "tag": "CFG",
        "arithmetic_derivation": "Custom line has no variant -> cost missing. L = 5000; D = 0; R = 5000; Sc = 0; C = 5000. COGS = None; S = 600; G = 160; E = 0; O = 0. P = None; P_upper = 4240. Lane = UNDETERMINED.",
        "input": {
            "id": "gid://shopify/Order/A15", "name": "#A15", "currencyCode": "USD", "processedAt": "2026-08-01T12:00:00Z",
            "currentShippingPriceSet": {"shopMoney": {"amount": "0.00", "currencyCode": "USD"}},
            "actual_carrier_cost": "6.00",
            "lineItems": [{
                "id": "L1", "quantity": 1, "currentQuantity": 1, "title": "Custom Engraving", "variant": None,
                "originalUnitPriceSet": {"shopMoney": {"amount": "50.00", "currencyCode": "USD"}},
                "discountAllocations": []
            }],
            "transactions": [{"id": "T1", "gateway": "shopify_payments", "fees": [{"amount": {"amount": "1.60", "currencyCode": "USD"}}]}],
            "refunds": []
        },
        "expected": {
            "L": 5000, "D": 0, "R": 5000, "Sc": 0, "C": 5000,
            "COGS": None, "S": 600, "G": 160, "E": 0, "O": 0,
            "P": None, "P_upper": 4240, "margin": None,
            "class": "undetermined", "classification": "undetermined", "band": "undetermined", "lane": "UNDETERMINED",
            "component_tags": {"cogs": "missing", "shipping": "measured", "gateway": "measured", "refund": "measured", "other": "structural"},
            "measured_share": "1.0000", "flags": ["COGS_MISSING_CUSTOM_LINE"],
            "drivers": {"product_margin_at_list": "unknown", "discount_leak": 0, "shipping_net": -600, "fee_leak": -160, "refund_leak": 0, "other_leak": 0},
            "top_loss_driver": None, "delta_profit": None
        }
    },
    {
        "id": "A16",
        "purpose": "Tax-inclusive line with embedded tax removed from revenue.",
        "profile": "balanced", "spec_ref": "3.1, 3.2", "tag": "UNV",
        "arithmetic_derivation": "taxesIncluded=True. Gross = 11000, embedded tax = 1000 -> net = 10000. L = 11000; D = 0; R = 10000; Sc = 0; C = 10000. COGS = 4000; S = 800; G = 320; E = 0; O = 0. P = 4880. Margin = 48.80% (high).",
        "input": {
            "id": "gid://shopify/Order/A16", "name": "#A16", "currencyCode": "USD", "taxesIncluded": True, "processedAt": "2026-08-01T12:00:00Z",
            "currentShippingPriceSet": {"shopMoney": {"amount": "0.00", "currencyCode": "USD"}},
            "actual_carrier_cost": "8.00",
            "lineItems": [{
                "id": "L1", "quantity": 1, "currentQuantity": 1,
                "originalUnitPriceSet": {"shopMoney": {"amount": "110.00", "currencyCode": "USD"}},
                "taxLines": [{"priceSet": {"shopMoney": {"amount": "10.00", "currencyCode": "USD"}}}],
                "discountAllocations": [],
                "variant": {"id": "V1", "inventoryItem": {"unitCost": {"amount": "40.00", "currencyCode": "USD"}}}
            }],
            "transactions": [{"id": "T1", "gateway": "shopify_payments", "fees": [{"amount": {"amount": "3.20", "currencyCode": "USD"}}]}],
            "refunds": []
        },
        "expected": {
            "L": 11000, "D": 0, "R": 10000, "Sc": 0, "C": 10000,
            "COGS": 4000, "S": 800, "G": 320, "E": 0, "O": 0,
            "P": 4880, "P_upper": 4880, "margin": 48.8,
            "class": "profitable", "classification": "profitable", "band": "high", "lane": "MEASURED",
            "component_tags": {"cogs": "measured", "shipping": "measured", "gateway": "measured", "refund": "measured", "other": "structural"},
            "measured_share": "1.0000", "flags": [],
            "drivers": {"product_margin_at_list": 6000, "discount_leak": 0, "shipping_net": -800, "fee_leak": -320, "refund_leak": 0, "other_leak": 0},
            "top_loss_driver": None, "delta_profit": 500
        }
    },
    {
        "id": "A17",
        "purpose": "Tip line excluded from merchandise revenue and provision base.",
        "profile": "balanced", "spec_ref": "3.1, 3.2", "tag": "UNV",
        "arithmetic_derivation": "Tip excluded. L = 5000; D = 0; R = 5000; Sc = 0; C = 5000. COGS = 2000; S = 600; G = 160; E = 0; O = 0. P = 2240. Margin = 44.80% (high).",
        "input": {
            "id": "gid://shopify/Order/A17", "name": "#A17", "currencyCode": "USD", "processedAt": "2026-08-01T12:00:00Z",
            "currentShippingPriceSet": {"shopMoney": {"amount": "0.00", "currencyCode": "USD"}},
            "actual_carrier_cost": "6.00",
            "lineItems": [
                {
                    "id": "L1", "quantity": 1, "currentQuantity": 1,
                    "originalUnitPriceSet": {"shopMoney": {"amount": "50.00", "currencyCode": "USD"}},
                    "discountAllocations": [],
                    "variant": {"id": "V1", "inventoryItem": {"unitCost": {"amount": "20.00", "currencyCode": "USD"}}}
                },
                {
                    "id": "TIP", "quantity": 1, "currentQuantity": 1, "title": "Tip",
                    "originalUnitPriceSet": {"shopMoney": {"amount": "5.00", "currencyCode": "USD"}},
                    "discountAllocations": []
                }
            ],
            "transactions": [{"id": "T1", "gateway": "shopify_payments", "fees": [{"amount": {"amount": "1.60", "currencyCode": "USD"}}]}],
            "refunds": []
        },
        "expected": {
            "L": 5000, "D": 0, "R": 5000, "Sc": 0, "C": 5000,
            "COGS": 2000, "S": 600, "G": 160, "E": 0, "O": 0,
            "P": 2240, "P_upper": 2240, "margin": 44.8,
            "class": "profitable", "classification": "profitable", "band": "high", "lane": "MEASURED",
            "component_tags": {"cogs": "measured", "shipping": "measured", "gateway": "measured", "refund": "measured", "other": "structural"},
            "measured_share": "1.0000", "flags": [],
            "drivers": {"product_margin_at_list": 3000, "discount_leak": 0, "shipping_net": -600, "fee_leak": -160, "refund_leak": 0, "other_leak": 0},
            "top_loss_driver": None, "delta_profit": 250
        }
    },
    {
        "id": "A18",
        "purpose": "Multi-line complex discount stacking with automatic discount.",
        "profile": "balanced", "spec_ref": "3.1, 3.2", "tag": "V-DOC",
        "arithmetic_derivation": "L = 10000; D = 2000; R = 8000; Sc = 0; C = 8000. COGS = 4000; S = 800; G = 260; E = 0; O = 0. P = 2940. Margin = 36.75% (high).",
        "input": {
            "id": "gid://shopify/Order/A18", "name": "#A18", "currencyCode": "USD", "processedAt": "2026-08-01T12:00:00Z",
            "currentShippingPriceSet": {"shopMoney": {"amount": "0.00", "currencyCode": "USD"}},
            "actual_carrier_cost": "8.00",
            "lineItems": [
                {
                    "id": "L1", "quantity": 1, "currentQuantity": 1,
                    "originalUnitPriceSet": {"shopMoney": {"amount": "40.00", "currencyCode": "USD"}},
                    "discountAllocations": [{"allocatedAmountSet": {"shopMoney": {"amount": "8.00", "currencyCode": "USD"}}}],
                    "variant": {"id": "V1", "inventoryItem": {"unitCost": {"amount": "16.00", "currencyCode": "USD"}}}
                },
                {
                    "id": "L2", "quantity": 1, "currentQuantity": 1,
                    "originalUnitPriceSet": {"shopMoney": {"amount": "60.00", "currencyCode": "USD"}},
                    "discountAllocations": [{"allocatedAmountSet": {"shopMoney": {"amount": "12.00", "currencyCode": "USD"}}}],
                    "variant": {"id": "V2", "inventoryItem": {"unitCost": {"amount": "24.00", "currencyCode": "USD"}}}
                }
            ],
            "transactions": [{"id": "T1", "gateway": "shopify_payments", "fees": [{"amount": {"amount": "2.60", "currencyCode": "USD"}}]}],
            "refunds": []
        },
        "expected": {
            "L": 10000, "D": 2000, "R": 8000, "Sc": 0, "C": 8000,
            "COGS": 4000, "S": 800, "G": 260, "E": 0, "O": 0,
            "P": 2940, "P_upper": 2940, "margin": 36.75,
            "class": "profitable", "classification": "profitable", "band": "high", "lane": "MEASURED",
            "component_tags": {"cogs": "measured", "shipping": "measured", "gateway": "measured", "refund": "measured", "other": "structural"},
            "measured_share": "1.0000", "flags": [],
            "drivers": {"product_margin_at_list": 6000, "discount_leak": -2000, "shipping_net": -800, "fee_leak": -260, "refund_leak": 0, "other_leak": 0},
            "top_loss_driver": None, "delta_profit": 400
        }
    }
]
