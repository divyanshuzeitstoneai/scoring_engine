"""
Builds authoritative hand-computed formula test fixtures for Section 15.
All expected values are hand-derived in integer minor units (USD cents).
"""

import json
import os
import yaml

FIXTURES_DIR = "f11/fixtures/formula"
GOLDEN_DIR = "f11/fixtures/golden"

os.makedirs(FIXTURES_DIR, exist_ok=True)
os.makedirs(GOLDEN_DIR, exist_ok=True)

# 1. Reference Orders (B0, B1, Doc-2)
B0_FIXTURE = {
    "id": "B0",
    "purpose": "Prior spec Example A restated. High margin healthy order.",
    "input": {
        "id": "gid://shopify/Order/B0",
        "name": "#B0",
        "currencyCode": "USD",
        "processedAt": "2026-09-20T12:00:00Z",
        "currentShippingPriceSet": {"shopMoney": {"amount": "10.00", "currencyCode": "USD"}},
        "actual_carrier_cost": "9.00",
        "lineItems": [
            {
                "id": "gid://shopify/LineItem/B0_1",
                "quantity": 2,
                "currentQuantity": 2,
                "originalUnitPriceSet": {"shopMoney": {"amount": "55.00", "currencyCode": "USD"}},
                "discountAllocations": [],
                "variant": {
                    "id": "gid://shopify/ProductVariant/B0_V1",
                    "inventoryItem": {"unitCost": {"amount": "22.50", "currencyCode": "USD"}}
                }
            }
        ],
        "transactions": [
            {
                "id": "gid://shopify/OrderTransaction/B0_TX",
                "gateway": "shopify_payments",
                "fees": [{"amount": {"amount": "3.78", "currencyCode": "USD"}}]
            }
        ],
        "refunds": []
    },
    "expected": {
        "R": 11000,
        "Sc": 1000,
        "C": 12000,
        "COGS": 4500,
        "S": 900,
        "G": 378,
        "E": 550,
        "O": 150,
        "P": 5522, # Without O: 5672; with O=150: 5522
        "lane": "ESTIMATED",
        "band": "high",
        "classification": "profitable",
        "top_loss_driver": None
    }
}

B1_FIXTURE = {
    "id": "B1",
    "purpose": "Prior spec Example B. Deep discount, free shipping, cash drain.",
    "input": {
        "id": "gid://shopify/Order/B1",
        "name": "#B1",
        "currencyCode": "USD",
        "processedAt": "2026-09-20T12:00:00Z",
        "currentShippingPriceSet": {"shopMoney": {"amount": "0.00", "currencyCode": "USD"}},
        "actual_carrier_cost": "8.50",
        "lineItems": [
            {
                "id": "gid://shopify/LineItem/B1_1",
                "quantity": 1,
                "currentQuantity": 1,
                "originalUnitPriceSet": {"shopMoney": {"amount": "30.00", "currencyCode": "USD"}},
                "discountAllocations": [
                    {"allocatedAmountSet": {"shopMoney": {"amount": "5.00", "currencyCode": "USD"}}}
                ],
                "variant": {
                    "id": "gid://shopify/ProductVariant/B1_V1",
                    "inventoryItem": {"unitCost": {"amount": "18.00", "currencyCode": "USD"}}
                }
            }
        ],
        "transactions": [
            {
                "id": "gid://shopify/OrderTransaction/B1_TX",
                "gateway": "shopify_payments",
                "fees": [{"amount": {"amount": "1.03", "currencyCode": "USD"}}]
            }
        ],
        "refunds": []
    },
    "expected": {
        "R": 2500,
        "Sc": 0,
        "C": 2500,
        "COGS": 1800,
        "S": 850,
        "G": 103,
        "E": 125,
        "P": -528, # Without O: -378; with O=150: -528
        "lane": "ESTIMATED",
        "band": "cash_drain",
        "classification": "unprofitable",
        "top_loss_driver": "shipping_subsidy"
    }
}

DOC2_FIXTURE = {
    "id": "DOC2",
    "purpose": "Doc-2 reconciliation case.",
    "input": {
        "id": "gid://shopify/Order/DOC2",
        "name": "#DOC2",
        "currencyCode": "USD",
        "processedAt": "2026-08-01T12:00:00Z", # Window closed
        "currentShippingPriceSet": {"shopMoney": {"amount": "0.00", "currencyCode": "USD"}},
        "actual_carrier_cost": "22.00",
        "lineItems": [
            {
                "id": "gid://shopify/LineItem/DOC2_1",
                "quantity": 1,
                "currentQuantity": 1,
                "originalUnitPriceSet": {"shopMoney": {"amount": "100.00", "currencyCode": "USD"}},
                "discountAllocations": [
                    {"allocatedAmountSet": {"shopMoney": {"amount": "20.00", "currencyCode": "USD"}}}
                ],
                "variant": {
                    "id": "gid://shopify/ProductVariant/DOC2_V1",
                    "inventoryItem": {"unitCost": {"amount": "50.00", "currencyCode": "USD"}}
                }
            }
        ],
        "transactions": [
            {
                "id": "gid://shopify/OrderTransaction/DOC2_TX",
                "gateway": "shopify_payments",
                "fees": [{"amount": {"amount": "3.00", "currencyCode": "USD"}}]
            }
        ],
        "refunds": [
            {
                "id": "gid://shopify/Refund/DOC2_R",
                "createdAt": "2026-08-10T12:00:00Z",
                "totalRefundedSet": {"shopMoney": {"amount": "8.00", "currencyCode": "USD"}}
            }
        ]
    },
    "expected": {
        "R": 8000,
        "Sc": 0,
        "C": 8000,
        "COGS": 5000,
        "S": 2200,
        "G": 300,
        "E": 800,
        "P": -450, # With O=150: -450; without O: -300
        "lane": "MEASURED",
        "band": "cash_drain",
        "classification": "unprofitable"
    }
}

# Write reference cases
for f_data in [B0_FIXTURE, B1_FIXTURE, DOC2_FIXTURE]:
    f_path = os.path.join(GOLDEN_DIR, f"{f_data['id']}.yaml")
    with open(f_path, "w", encoding="utf-8") as f:
        yaml.dump(f_data, f, sort_keys=False)

print(f"Built reference golden fixtures (B0, B1, DOC2).")
