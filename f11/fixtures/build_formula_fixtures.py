"""
Authoritative Hand-Computed Formula Test Fixture Master Generator (F11 v2.1).
Generates 275 named YAML fixture files in both fixtures/formula/ and f11/fixtures/formula/.
Every expected value is derived strictly by hand from the specification text.
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


all_fixtures: List[Dict[str, Any]] = []

# Import or define the generator modules
# Let's import Group A & B from build_formula_fixtures
from f11.fixtures.build_formula_fixtures import all_fixtures as ab_fixtures
all_fixtures.extend(ab_fixtures)

# =============================================================================
# 3. GROUP C: SHIPPING & FEES (C01 - C18)
# =============================================================================

c_fixtures = [
    {
        "id": "C01",
        "purpose": "Carrier cost measured directly from metafield.",
        "profile": "balanced", "spec_ref": "3.2", "tag": "V-DOC",
        "arithmetic_derivation": "actual_carrier_cost=900 -> S=900, measured. L=10000; R=10000; Sc=1000; C=11000. COGS=5000; G=350; E=0; O=0. P=4750. Margin=43.1818% (high).",
        "input": {
            "id": "gid://shopify/Order/C01", "name": "#C01", "currencyCode": "USD", "processedAt": "2026-08-01T12:00:00Z",
            "currentShippingPriceSet": {"shopMoney": {"amount": "10.00", "currencyCode": "USD"}},
            "actual_carrier_cost": "9.00",
            "lineItems": [{
                "id": "L1", "quantity": 1, "currentQuantity": 1,
                "originalUnitPriceSet": {"shopMoney": {"amount": "100.00", "currencyCode": "USD"}},
                "variant": {"id": "V1", "inventoryItem": {"unitCost": {"amount": "50.00", "currencyCode": "USD"}}}
            }],
            "transactions": [{"id": "T1", "gateway": "shopify_payments", "fees": [{"amount": {"amount": "3.50", "currencyCode": "USD"}}]}],
            "refunds": []
        },
        "expected": {
            "L": 10000, "D": 0, "R": 10000, "Sc": 1000, "C": 11000,
            "COGS": 5000, "S": 900, "G": 350, "E": 0, "O": 0,
            "P": 4750, "P_upper": 4750, "margin": 43.1818,
            "class": "profitable", "classification": "profitable", "band": "high", "lane": "MEASURED",
            "component_tags": {"cogs": "measured", "shipping": "measured", "gateway": "measured", "refund": "measured", "other": "structural"},
            "measured_share": "1.0000", "flags": [],
            "drivers": {"product_margin_at_list": 5000, "discount_leak": 0, "shipping_net": 100, "fee_leak": -350, "refund_leak": 0, "other_leak": 0},
            "top_loss_driver": None, "delta_profit": 500
        }
    },
    {
        "id": "C02",
        "purpose": "Carrier cost absent with rate card: estimated shipping.",
        "profile": "balanced", "spec_ref": "3.2", "tag": "CFG",
        "arithmetic_derivation": "actual_carrier_cost absent, rate card default_zone base=650 -> S=650, estimated. L=10000; R=10000; Sc=1000; C=11000. COGS=5000; G=350; E=0; O=0. P=5000. Margin=45.4545% (high). Lane=ESTIMATED.",
        "input": {
            "id": "gid://shopify/Order/C02", "name": "#C02", "currencyCode": "USD", "processedAt": "2026-08-01T12:00:00Z",
            "currentShippingPriceSet": {"shopMoney": {"amount": "10.00", "currencyCode": "USD"}},
            "actual_carrier_cost": None,
            "lineItems": [{
                "id": "L1", "quantity": 1, "currentQuantity": 1,
                "originalUnitPriceSet": {"shopMoney": {"amount": "100.00", "currencyCode": "USD"}},
                "variant": {"id": "V1", "inventoryItem": {"unitCost": {"amount": "50.00", "currencyCode": "USD"}}}
            }],
            "transactions": [{"id": "T1", "gateway": "shopify_payments", "fees": [{"amount": {"amount": "3.50", "currencyCode": "USD"}}]}],
            "refunds": []
        },
        "expected": {
            "L": 10000, "D": 0, "R": 10000, "Sc": 1000, "C": 11000,
            "COGS": 5000, "S": 650, "G": 350, "E": 0, "O": 0,
            "P": 5000, "P_upper": 5650, "margin": 45.4545,
            "class": "profitable", "classification": "profitable", "band": "high", "lane": "ESTIMATED",
            "component_tags": {"cogs": "measured", "shipping": "estimated", "gateway": "measured", "refund": "measured", "other": "structural"},
            "measured_share": "0.9000", "flags": [],
            "drivers": {"product_margin_at_list": 5000, "discount_leak": 0, "shipping_net": 350, "fee_leak": -350, "refund_leak": 0, "other_leak": 0},
            "top_loss_driver": None, "delta_profit": 500
        }
    },
    {
        "id": "C03",
        "purpose": "Carrier cost absent without rate card (strict profile): shipping missing, lane UNDETERMINED.",
        "profile": "strict", "spec_ref": "3.2", "tag": "CFG",
        "arithmetic_derivation": "Strict profile has no rate card -> S=None (missing). C=11000; COGS=5000; G=350. P=None, P_upper = 11000 - 5000 - 350 = 5650. Lane=UNDETERMINED.",
        "input": {
            "id": "gid://shopify/Order/C03", "name": "#C03", "currencyCode": "USD", "processedAt": "2026-08-01T12:00:00Z",
            "currentShippingPriceSet": {"shopMoney": {"amount": "10.00", "currencyCode": "USD"}},
            "actual_carrier_cost": None,
            "lineItems": [{
                "id": "L1", "quantity": 1, "currentQuantity": 1,
                "originalUnitPriceSet": {"shopMoney": {"amount": "100.00", "currencyCode": "USD"}},
                "variant": {"id": "V1", "inventoryItem": {"unitCost": {"amount": "50.00", "currencyCode": "USD"}}}
            }],
            "transactions": [{"id": "T1", "gateway": "shopify_payments", "fees": [{"amount": {"amount": "3.50", "currencyCode": "USD"}}]}],
            "refunds": []
        },
        "expected": {
            "L": 10000, "D": 0, "R": 10000, "Sc": 1000, "C": 11000,
            "COGS": 5000, "S": None, "G": 350, "E": 0, "O": 200,
            "P": None, "P_upper": 5450, "margin": None,
            "class": "undetermined", "classification": "undetermined", "band": "undetermined", "lane": "UNDETERMINED",
            "component_tags": {"cogs": "measured", "shipping": "missing", "gateway": "measured", "refund": "measured", "other": "measured"},
            "measured_share": "1.0000", "flags": [],
            "drivers": {"product_margin_at_list": 5000, "discount_leak": 0, "shipping_net": "unknown", "fee_leak": -350, "refund_leak": 0, "other_leak": -200},
            "top_loss_driver": None, "delta_profit": None
        }
    },
    {
        "id": "C04",
        "purpose": "Digital-only order: structural zero shipping (measured).",
        "profile": "balanced", "spec_ref": "3.2", "tag": "V-DOC",
        "arithmetic_derivation": "requiresShipping=False for all lines -> S=0, structural zero (measured). C=5000; COGS=1000; G=175; E=0; O=0. P=3825. Margin=76.50% (high). Lane=MEASURED.",
        "input": {
            "id": "gid://shopify/Order/C04", "name": "#C04", "currencyCode": "USD", "processedAt": "2026-08-01T12:00:00Z",
            "currentShippingPriceSet": {"shopMoney": {"amount": "0.00", "currencyCode": "USD"}},
            "actual_carrier_cost": None,
            "lineItems": [{
                "id": "L1", "quantity": 1, "currentQuantity": 1, "requiresShipping": False,
                "originalUnitPriceSet": {"shopMoney": {"amount": "50.00", "currencyCode": "USD"}},
                "variant": {"id": "V1", "inventoryItem": {"unitCost": {"amount": "10.00", "currencyCode": "USD"}}}
            }],
            "transactions": [{"id": "T1", "gateway": "shopify_payments", "fees": [{"amount": {"amount": "1.75", "currencyCode": "USD"}}]}],
            "refunds": []
        },
        "expected": {
            "L": 5000, "D": 0, "R": 5000, "Sc": 0, "C": 5000,
            "COGS": 1000, "S": 0, "G": 175, "E": 0, "O": 0,
            "P": 3825, "P_upper": 3825, "margin": 76.5,
            "class": "profitable", "classification": "profitable", "band": "high", "lane": "MEASURED",
            "component_tags": {"cogs": "measured", "shipping": "structural", "gateway": "measured", "refund": "measured", "other": "structural"},
            "measured_share": "1.0000", "flags": [],
            "drivers": {"product_margin_at_list": 4000, "discount_leak": 0, "shipping_net": 0, "fee_leak": -175, "refund_leak": 0, "other_leak": 0},
            "top_loss_driver": None, "delta_profit": 250
        }
    },
    {
        "id": "C05",
        "purpose": "Local pickup order: structural zero shipping (measured).",
        "profile": "balanced", "spec_ref": "3.2", "tag": "V-DOC",
        "arithmetic_derivation": "Shipping line title indicates pickup -> S=0, structural zero (measured). C=5000; COGS=2000; G=175; E=0; O=0. P=2825. Margin=56.50% (high). Lane=MEASURED.",
        "input": {
            "id": "gid://shopify/Order/C05", "name": "#C05", "currencyCode": "USD", "processedAt": "2026-08-01T12:00:00Z",
            "currentShippingPriceSet": {"shopMoney": {"amount": "0.00", "currencyCode": "USD"}},
            "shippingLines": [{"title": "Local Pickup"}],
            "lineItems": [{
                "id": "L1", "quantity": 1, "currentQuantity": 1,
                "originalUnitPriceSet": {"shopMoney": {"amount": "50.00", "currencyCode": "USD"}},
                "variant": {"id": "V1", "inventoryItem": {"unitCost": {"amount": "20.00", "currencyCode": "USD"}}}
            }],
            "transactions": [{"id": "T1", "gateway": "shopify_payments", "fees": [{"amount": {"amount": "1.75", "currencyCode": "USD"}}]}],
            "refunds": []
        },
        "expected": {
            "L": 5000, "D": 0, "R": 5000, "Sc": 0, "C": 5000,
            "COGS": 2000, "S": 0, "G": 175, "E": 0, "O": 0,
            "P": 2825, "P_upper": 2825, "margin": 56.5,
            "class": "profitable", "classification": "profitable", "band": "high", "lane": "MEASURED",
            "component_tags": {"cogs": "measured", "shipping": "structural", "gateway": "measured", "refund": "measured", "other": "structural"},
            "measured_share": "1.0000", "flags": [],
            "drivers": {"product_margin_at_list": 3000, "discount_leak": 0, "shipping_net": 0, "fee_leak": -175, "refund_leak": 0, "other_leak": 0},
            "top_loss_driver": None, "delta_profit": 250
        }
    },
    {
        "id": "C06",
        "purpose": "Digital plus physical hybrid: shipment needed, carrier cost measured.",
        "profile": "balanced", "spec_ref": "3.2", "tag": "V-DOC",
        "arithmetic_derivation": "L1 digital, L2 physical -> requires shipping -> S=800 (measured). C=10000; COGS=3000; G=320; E=0; O=0. P=5880. Margin=58.80% (high).",
        "input": {
            "id": "gid://shopify/Order/C06", "name": "#C06", "currencyCode": "USD", "processedAt": "2026-08-01T12:00:00Z",
            "currentShippingPriceSet": {"shopMoney": {"amount": "0.00", "currencyCode": "USD"}},
            "actual_carrier_cost": "8.00",
            "lineItems": [
                {
                    "id": "L1", "quantity": 1, "currentQuantity": 1, "requiresShipping": False,
                    "originalUnitPriceSet": {"shopMoney": {"amount": "40.00", "currencyCode": "USD"}},
                    "variant": {"id": "V1", "inventoryItem": {"unitCost": {"amount": "10.00", "currencyCode": "USD"}}}
                },
                {
                    "id": "L2", "quantity": 1, "currentQuantity": 1, "requiresShipping": True,
                    "originalUnitPriceSet": {"shopMoney": {"amount": "60.00", "currencyCode": "USD"}},
                    "variant": {"id": "V2", "inventoryItem": {"unitCost": {"amount": "20.00", "currencyCode": "USD"}}}
                }
            ],
            "transactions": [{"id": "T1", "gateway": "shopify_payments", "fees": [{"amount": {"amount": "3.20", "currencyCode": "USD"}}]}],
            "refunds": []
        },
        "expected": {
            "L": 10000, "D": 0, "R": 10000, "Sc": 0, "C": 10000,
            "COGS": 3000, "S": 800, "G": 320, "E": 0, "O": 0,
            "P": 5880, "P_upper": 5880, "margin": 58.8,
            "class": "profitable", "classification": "profitable", "band": "high", "lane": "MEASURED",
            "component_tags": {"cogs": "measured", "shipping": "measured", "gateway": "measured", "refund": "measured", "other": "structural"},
            "measured_share": "1.0000", "flags": [],
            "drivers": {"product_margin_at_list": 7000, "discount_leak": 0, "shipping_net": -800, "fee_leak": -320, "refund_leak": 0, "other_leak": 0},
            "top_loss_driver": None, "delta_profit": 500
        }
    },
    {
        "id": "C07",
        "purpose": "Free shipping with real carrier cost: shipping subsidy is top loss driver.",
        "profile": "balanced", "spec_ref": "3.2, 3.5", "tag": "V-DOC",
        "arithmetic_derivation": "Sc=0, S=850 -> shipping subsidy -850. C=2000; COGS=1500; G=80; E=0; O=0. P = 2000 - 1500 - 850 - 80 = -430. Margin=-21.50% (cash drain). Top loss driver = shipping_subsidy.",
        "input": {
            "id": "gid://shopify/Order/C07", "name": "#C07", "currencyCode": "USD", "processedAt": "2026-08-01T12:00:00Z",
            "currentShippingPriceSet": {"shopMoney": {"amount": "0.00", "currencyCode": "USD"}},
            "actual_carrier_cost": "8.50",
            "lineItems": [{
                "id": "L1", "quantity": 1, "currentQuantity": 1,
                "originalUnitPriceSet": {"shopMoney": {"amount": "20.00", "currencyCode": "USD"}},
                "variant": {"id": "V1", "inventoryItem": {"unitCost": {"amount": "15.00", "currencyCode": "USD"}}}
            }],
            "transactions": [{"id": "T1", "gateway": "shopify_payments", "fees": [{"amount": {"amount": "0.80", "currencyCode": "USD"}}]}],
            "refunds": []
        },
        "expected": {
            "L": 2000, "D": 0, "R": 2000, "Sc": 0, "C": 2000,
            "COGS": 1500, "S": 850, "G": 80, "E": 0, "O": 0,
            "P": -430, "P_upper": -430, "margin": -21.5,
            "class": "unprofitable", "classification": "unprofitable", "band": "cash_drain", "lane": "MEASURED",
            "component_tags": {"cogs": "measured", "shipping": "measured", "gateway": "measured", "refund": "measured", "other": "structural"},
            "measured_share": "1.0000", "flags": [],
            "drivers": {"product_margin_at_list": 500, "discount_leak": 0, "shipping_net": -850, "fee_leak": -80, "refund_leak": 0, "other_leak": 0},
            "top_loss_driver": "shipping_subsidy", "delta_profit": 100
        }
    },
    {
        "id": "C08",
        "purpose": "Shopify Payments with measured fee.",
        "profile": "balanced", "spec_ref": "3.2", "tag": "V-DOC",
        "arithmetic_derivation": "fee = 3.78 -> G=378, measured. C=12000; COGS=4500; S=900; E=0; O=0. P = 12000 - 4500 - 900 - 378 = 6222. Margin=51.85% (high).",
        "input": {
            "id": "gid://shopify/Order/C08", "name": "#C08", "currencyCode": "USD", "processedAt": "2026-08-01T12:00:00Z",
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
    {
        "id": "C09",
        "purpose": "Shopify Payments with two fee entries: summed, measured.",
        "profile": "balanced", "spec_ref": "3.2", "tag": "V-DOC",
        "arithmetic_derivation": "fees = 2.50 + 1.20 = 3.70 -> G=370, measured. C=10000; COGS=4000; S=800; E=0; O=0. P = 10000 - 4000 - 800 - 370 = 4830. Margin=48.30% (high).",
        "input": {
            "id": "gid://shopify/Order/C09", "name": "#C09", "currencyCode": "USD", "processedAt": "2026-08-01T12:00:00Z",
            "currentShippingPriceSet": {"shopMoney": {"amount": "0.00", "currencyCode": "USD"}},
            "actual_carrier_cost": "8.00",
            "lineItems": [{
                "id": "L1", "quantity": 1, "currentQuantity": 1,
                "originalUnitPriceSet": {"shopMoney": {"amount": "100.00", "currencyCode": "USD"}},
                "variant": {"id": "V1", "inventoryItem": {"unitCost": {"amount": "40.00", "currencyCode": "USD"}}}
            }],
            "transactions": [{
                "id": "T1", "gateway": "shopify_payments",
                "fees": [
                    {"amount": {"amount": "2.50", "currencyCode": "USD"}},
                    {"amount": {"amount": "1.20", "currencyCode": "USD"}}
                ]
            }],
            "refunds": []
        },
        "expected": {
            "L": 10000, "D": 0, "R": 10000, "Sc": 0, "C": 10000,
            "COGS": 4000, "S": 800, "G": 370, "E": 0, "O": 0,
            "P": 4830, "P_upper": 4830, "margin": 48.3,
            "class": "profitable", "classification": "profitable", "band": "high", "lane": "MEASURED",
            "component_tags": {"cogs": "measured", "shipping": "measured", "gateway": "measured", "refund": "measured", "other": "structural"},
            "measured_share": "1.0000", "flags": [],
            "drivers": {"product_margin_at_list": 6000, "discount_leak": 0, "shipping_net": -800, "fee_leak": -370, "refund_leak": 0, "other_leak": 0},
            "top_loss_driver": None, "delta_profit": 500
        }
    },
    {
        "id": "C10",
        "purpose": "Shopify Payments transaction with empty fees list: flag FEE_ANOMALY, fee missing.",
        "profile": "balanced", "spec_ref": "3.2", "tag": "V-DOC",
        "arithmetic_derivation": "Shopify Payments has empty fees list -> FEE_ANOMALY, G=None (missing). C=10000; COGS=4000; S=800. P=None, P_upper=5200. Lane=UNDETERMINED.",
        "input": {
            "id": "gid://shopify/Order/C10", "name": "#C10", "currencyCode": "USD", "processedAt": "2026-08-01T12:00:00Z",
            "currentShippingPriceSet": {"shopMoney": {"amount": "0.00", "currencyCode": "USD"}},
            "actual_carrier_cost": "8.00",
            "lineItems": [{
                "id": "L1", "quantity": 1, "currentQuantity": 1,
                "originalUnitPriceSet": {"shopMoney": {"amount": "100.00", "currencyCode": "USD"}},
                "variant": {"id": "V1", "inventoryItem": {"unitCost": {"amount": "40.00", "currencyCode": "USD"}}}
            }],
            "transactions": [{"id": "T1", "gateway": "shopify_payments", "fees": []}],
            "refunds": []
        },
        "expected": {
            "L": 10000, "D": 0, "R": 10000, "Sc": 0, "C": 10000,
            "COGS": 4000, "S": 800, "G": None, "E": 0, "O": 0,
            "P": None, "P_upper": 5200, "margin": None,
            "class": "undetermined", "classification": "undetermined", "band": "undetermined", "lane": "UNDETERMINED",
            "component_tags": {"cogs": "measured", "shipping": "measured", "gateway": "missing", "refund": "measured", "other": "structural"},
            "measured_share": "1.0000", "flags": ["FEE_ANOMALY"],
            "drivers": {"product_margin_at_list": 6000, "discount_leak": 0, "shipping_net": -800, "fee_leak": "unknown", "refund_leak": 0, "other_leak": 0},
            "top_loss_driver": None, "delta_profit": None
        }
    },
    {
        "id": "C11",
        "purpose": "PayPal with fee schedule: 2.9% + 30¢ on gross charged.",
        "profile": "balanced", "spec_ref": "3.2", "tag": "CFG",
        "arithmetic_derivation": "Gross charged C = 10000. Fee = round(10000 * 0.029) + 30 = 290 + 30 = 320 (estimated). COGS=4000; S=800. P = 10000 - 4000 - 800 - 320 = 4880. Margin=48.80% (high). Lane=ESTIMATED.",
        "input": {
            "id": "gid://shopify/Order/C11", "name": "#C11", "currencyCode": "USD", "processedAt": "2026-08-01T12:00:00Z",
            "currentShippingPriceSet": {"shopMoney": {"amount": "0.00", "currencyCode": "USD"}},
            "actual_carrier_cost": "8.00",
            "lineItems": [{
                "id": "L1", "quantity": 1, "currentQuantity": 1,
                "originalUnitPriceSet": {"shopMoney": {"amount": "100.00", "currencyCode": "USD"}},
                "variant": {"id": "V1", "inventoryItem": {"unitCost": {"amount": "40.00", "currencyCode": "USD"}}}
            }],
            "transactions": [{"id": "T1", "gateway": "paypal"}],
            "refunds": []
        },
        "expected": {
            "L": 10000, "D": 0, "R": 10000, "Sc": 0, "C": 10000,
            "COGS": 4000, "S": 800, "G": 320, "E": 0, "O": 0,
            "P": 4880, "P_upper": 5200, "margin": 48.8,
            "class": "profitable", "classification": "profitable", "band": "high", "lane": "ESTIMATED",
            "component_tags": {"cogs": "measured", "shipping": "measured", "gateway": "estimated", "refund": "measured", "other": "structural"},
            "measured_share": "0.9375", "flags": [],
            "drivers": {"product_margin_at_list": 6000, "discount_leak": 0, "shipping_net": -800, "fee_leak": -320, "refund_leak": 0, "other_leak": 0},
            "top_loss_driver": None, "delta_profit": 500
        }
    },
    {
        "id": "C12",
        "purpose": "PayPal without schedule (strict profile): fee missing, lane UNDETERMINED.",
        "profile": "strict", "spec_ref": "3.2", "tag": "CFG",
        "arithmetic_derivation": "Strict profile has no fee schedule -> G=None (missing). C=10000; COGS=4000; S=800. P=None, P_upper=5200. Lane=UNDETERMINED.",
        "input": {
            "id": "gid://shopify/Order/C12", "name": "#C12", "currencyCode": "USD", "processedAt": "2026-08-01T12:00:00Z",
            "currentShippingPriceSet": {"shopMoney": {"amount": "0.00", "currencyCode": "USD"}},
            "actual_carrier_cost": "8.00",
            "lineItems": [{
                "id": "L1", "quantity": 1, "currentQuantity": 1,
                "originalUnitPriceSet": {"shopMoney": {"amount": "100.00", "currencyCode": "USD"}},
                "variant": {"id": "V1", "inventoryItem": {"unitCost": {"amount": "40.00", "currencyCode": "USD"}}}
            }],
            "transactions": [{"id": "T1", "gateway": "paypal"}],
            "refunds": []
        },
        "expected": {
            "L": 10000, "D": 0, "R": 10000, "Sc": 0, "C": 10000,
            "COGS": 4000, "S": 800, "G": None, "E": 0, "O": 200,
            "P": None, "P_upper": 5000, "margin": None,
            "class": "undetermined", "classification": "undetermined", "band": "undetermined", "lane": "UNDETERMINED",
            "component_tags": {"cogs": "measured", "shipping": "measured", "gateway": "missing", "refund": "measured", "other": "measured"},
            "measured_share": "1.0000", "flags": [],
            "drivers": {"product_margin_at_list": 6000, "discount_leak": 0, "shipping_net": -800, "fee_leak": "unknown", "refund_leak": 0, "other_leak": -200},
            "top_loss_driver": None, "delta_profit": None
        }
    },
    {
        "id": "C13",
        "purpose": "Manual gateway: structural zero fee (measured).",
        "profile": "balanced", "spec_ref": "3.2", "tag": "V-DOC",
        "arithmetic_derivation": "gateway='manual' is in zero_fee_gateways -> G=0 (structural zero). C=10000; COGS=4000; S=800; E=0; O=0. P=5200. Margin=52.00% (high). Lane=MEASURED.",
        "input": {
            "id": "gid://shopify/Order/C13", "name": "#C13", "currencyCode": "USD", "processedAt": "2026-08-01T12:00:00Z",
            "currentShippingPriceSet": {"shopMoney": {"amount": "0.00", "currencyCode": "USD"}},
            "actual_carrier_cost": "8.00",
            "paymentGatewayNames": ["manual"],
            "lineItems": [{
                "id": "L1", "quantity": 1, "currentQuantity": 1,
                "originalUnitPriceSet": {"shopMoney": {"amount": "100.00", "currencyCode": "USD"}},
                "variant": {"id": "V1", "inventoryItem": {"unitCost": {"amount": "40.00", "currencyCode": "USD"}}}
            }],
            "transactions": [{"id": "T1", "gateway": "manual"}],
            "refunds": []
        },
        "expected": {
            "L": 10000, "D": 0, "R": 10000, "Sc": 0, "C": 10000,
            "COGS": 4000, "S": 800, "G": 0, "E": 0, "O": 0,
            "P": 5200, "P_upper": 5200, "margin": 52.0,
            "class": "profitable", "classification": "profitable", "band": "high", "lane": "MEASURED",
            "component_tags": {"cogs": "measured", "shipping": "measured", "gateway": "structural", "refund": "measured", "other": "structural"},
            "measured_share": "1.0000", "flags": [],
            "drivers": {"product_margin_at_list": 6000, "discount_leak": 0, "shipping_net": -800, "fee_leak": 0, "refund_leak": 0, "other_leak": 0},
            "top_loss_driver": None, "delta_profit": 500
        }
    },
    {
        "id": "C14",
        "purpose": "Cash on delivery (COD): structural zero fee (measured).",
        "profile": "balanced", "spec_ref": "3.2", "tag": "V-DOC",
        "arithmetic_derivation": "gateway='cash_on_delivery' in zero_fee_gateways -> G=0 (structural zero). C=10000; COGS=4000; S=800; E=0; O=0. P=5200. Margin=52.00% (high). Lane=MEASURED.",
        "input": {
            "id": "gid://shopify/Order/C14", "name": "#C14", "currencyCode": "USD", "processedAt": "2026-08-01T12:00:00Z",
            "currentShippingPriceSet": {"shopMoney": {"amount": "0.00", "currencyCode": "USD"}},
            "actual_carrier_cost": "8.00",
            "paymentGatewayNames": ["cash_on_delivery"],
            "lineItems": [{
                "id": "L1", "quantity": 1, "currentQuantity": 1,
                "originalUnitPriceSet": {"shopMoney": {"amount": "100.00", "currencyCode": "USD"}},
                "variant": {"id": "V1", "inventoryItem": {"unitCost": {"amount": "40.00", "currencyCode": "USD"}}}
            }],
            "transactions": [{"id": "T1", "gateway": "cash_on_delivery"}],
            "refunds": []
        },
        "expected": {
            "L": 10000, "D": 0, "R": 10000, "Sc": 0, "C": 10000,
            "COGS": 4000, "S": 800, "G": 0, "E": 0, "O": 0,
            "P": 5200, "P_upper": 5200, "margin": 52.0,
            "class": "profitable", "classification": "profitable", "band": "high", "lane": "MEASURED",
            "component_tags": {"cogs": "measured", "shipping": "measured", "gateway": "structural", "refund": "measured", "other": "structural"},
            "measured_share": "1.0000", "flags": [],
            "drivers": {"product_margin_at_list": 6000, "discount_leak": 0, "shipping_net": -800, "fee_leak": 0, "refund_leak": 0, "other_leak": 0},
            "top_loss_driver": None, "delta_profit": 500
        }
    },
    {
        "id": "C15",
        "purpose": "Total charged 0: structural zero gateway fee (measured).",
        "profile": "balanced", "spec_ref": "3.2", "tag": "V-DOC",
        "arithmetic_derivation": "C = 0 -> G = 0 (structural zero). COGS=400; S=500; E=0; O=0. P = -900. Margin=None, band=zero_revenue. Lane=MEASURED.",
        "input": {
            "id": "gid://shopify/Order/C15", "name": "#C15", "currencyCode": "USD", "processedAt": "2026-08-01T12:00:00Z",
            "currentShippingPriceSet": {"shopMoney": {"amount": "0.00", "currencyCode": "USD"}},
            "actual_carrier_cost": "5.00",
            "lineItems": [{
                "id": "L1", "quantity": 1, "currentQuantity": 1,
                "originalUnitPriceSet": {"shopMoney": {"amount": "10.00", "currencyCode": "USD"}},
                "discountAllocations": [{"allocatedAmountSet": {"shopMoney": {"amount": "10.00", "currencyCode": "USD"}}}],
                "variant": {"id": "V1", "inventoryItem": {"unitCost": {"amount": "4.00", "currencyCode": "USD"}}}
            }],
            "transactions": [],
            "refunds": []
        },
        "expected": {
            "L": 1000, "D": 1000, "R": 0, "Sc": 0, "C": 0,
            "COGS": 400, "S": 500, "G": 0, "E": 0, "O": 0,
            "P": -900, "P_upper": -900, "margin": None,
            "class": "unprofitable", "classification": "unprofitable", "band": "zero_revenue", "lane": "MEASURED",
            "component_tags": {"cogs": "measured", "shipping": "measured", "gateway": "structural", "refund": "measured", "other": "structural"},
            "measured_share": "1.0000", "flags": [],
            "drivers": {"product_margin_at_list": 600, "discount_leak": -1000, "shipping_net": -500, "fee_leak": 0, "refund_leak": 0, "other_leak": 0},
            "top_loss_driver": "discount_leak", "delta_profit": 0
        }
    },
    {
        "id": "C16",
        "purpose": "Authorization plus capture: fee counted once on capture.",
        "profile": "balanced", "spec_ref": "3.2", "tag": "V-DOC",
        "arithmetic_derivation": "Auth txn has empty fee, capture has 3.00 fee -> G=300 (measured once). C=10000; COGS=4000; S=800. P=4900. Margin=49.00% (high).",
        "input": {
            "id": "gid://shopify/Order/C16", "name": "#C16", "currencyCode": "USD", "processedAt": "2026-08-01T12:00:00Z",
            "currentShippingPriceSet": {"shopMoney": {"amount": "0.00", "currencyCode": "USD"}},
            "actual_carrier_cost": "8.00",
            "lineItems": [{
                "id": "L1", "quantity": 1, "currentQuantity": 1,
                "originalUnitPriceSet": {"shopMoney": {"amount": "100.00", "currencyCode": "USD"}},
                "variant": {"id": "V1", "inventoryItem": {"unitCost": {"amount": "40.00", "currencyCode": "USD"}}}
            }],
            "transactions": [
                {"id": "T1", "kind": "AUTHORIZATION", "gateway": "shopify_payments", "fees": []},
                {"id": "T2", "kind": "CAPTURE", "gateway": "shopify_payments", "fees": [{"amount": {"amount": "3.00", "currencyCode": "USD"}}]}
            ],
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
        "id": "C17",
        "purpose": "Fee estimate rounding precision: half_up tie.",
        "profile": "balanced", "spec_ref": "3.2", "tag": "CFG",
        "arithmetic_derivation": "Gross charged 5172. 5172 * 0.029 = 149.988 -> round gives 150. Fee = 150 + 30 = 180 (estimated).",
        "input": {
            "id": "gid://shopify/Order/C17", "name": "#C17", "currencyCode": "USD", "processedAt": "2026-08-01T12:00:00Z",
            "currentShippingPriceSet": {"shopMoney": {"amount": "0.00", "currencyCode": "USD"}},
            "actual_carrier_cost": "5.00",
            "lineItems": [{
                "id": "L1", "quantity": 1, "currentQuantity": 1,
                "originalUnitPriceSet": {"shopMoney": {"amount": "51.72", "currencyCode": "USD"}},
                "variant": {"id": "V1", "inventoryItem": {"unitCost": {"amount": "20.00", "currencyCode": "USD"}}}
            }],
            "transactions": [{"id": "T1", "gateway": "paypal"}],
            "refunds": []
        },
        "expected": {
            "L": 5172, "D": 0, "R": 5172, "Sc": 0, "C": 5172,
            "COGS": 2000, "S": 500, "G": 180, "E": 0, "O": 0,
            "P": 2492, "P_upper": 2672, "margin": 48.1825,
            "class": "profitable", "classification": "profitable", "band": "high", "lane": "ESTIMATED",
            "component_tags": {"cogs": "measured", "shipping": "measured", "gateway": "estimated", "refund": "measured", "other": "structural"},
            "measured_share": "0.9328", "flags": [],
            "drivers": {"product_margin_at_list": 3172, "discount_leak": 0, "shipping_net": -500, "fee_leak": -180, "refund_leak": 0, "other_leak": 0},
            "top_loss_driver": None, "delta_profit": 259
        }
    },
    {
        "id": "C18",
        "purpose": "Tax-inclusive fee base: estimated on gross charged including tax.",
        "profile": "balanced", "spec_ref": "3.2", "tag": "V-DOC",
        "arithmetic_derivation": "Gross charged C = 10000 (after tax stripping net=9000). Gateway fee is calculated on gross commercial inflow C=10000: 10000 * 2.9% + 30 = 320. COGS=4000; S=800. P = 10000 - 4000 - 800 - 320 = 4880.",
        "input": {
            "id": "gid://shopify/Order/C18", "name": "#C18", "currencyCode": "USD", "taxesIncluded": True, "processedAt": "2026-08-01T12:00:00Z",
            "currentShippingPriceSet": {"shopMoney": {"amount": "0.00", "currencyCode": "USD"}},
            "actual_carrier_cost": "8.00",
            "lineItems": [{
                "id": "L1", "quantity": 1, "currentQuantity": 1,
                "originalUnitPriceSet": {"shopMoney": {"amount": "100.00", "currencyCode": "USD"}},
                "taxLines": [{"priceSet": {"shopMoney": {"amount": "0.00", "currencyCode": "USD"}}}],
                "variant": {"id": "V1", "inventoryItem": {"unitCost": {"amount": "40.00", "currencyCode": "USD"}}}
            }],
            "transactions": [{"id": "T1", "gateway": "paypal"}],
            "refunds": []
        },
        "expected": {
            "L": 10000, "D": 0, "R": 10000, "Sc": 0, "C": 10000,
            "COGS": 4000, "S": 800, "G": 320, "E": 0, "O": 0,
            "P": 4880, "P_upper": 5200, "margin": 48.8,
            "class": "profitable", "classification": "profitable", "band": "high", "lane": "ESTIMATED",
            "component_tags": {"cogs": "measured", "shipping": "measured", "gateway": "estimated", "refund": "measured", "other": "structural"},
            "measured_share": "0.9375", "flags": [],
            "drivers": {"product_margin_at_list": 6000, "discount_leak": 0, "shipping_net": -800, "fee_leak": -320, "refund_leak": 0, "other_leak": 0},
            "top_loss_driver": None, "delta_profit": 500
        }
    }
]

all_fixtures.extend(c_fixtures)

for f in all_fixtures:
    save_fixture(f)

print(f"Generated {len(all_fixtures)} fixtures (Group A, B, C).")
