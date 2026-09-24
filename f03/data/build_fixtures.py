"""
Fixture Generator for Formula F03 Expanded Test Suite.
Generates:
1. scratch/test_fixtures.json (41 individual synthetic order fixtures)
2. scratch/batch_fixtures.json (TC-25, TC-26, TC-27 batch meta-tests)
"""

import json

def generate_fixtures():
    order_fixtures = []

    # 1. TC-01: Null COGS mixed lines
    order_fixtures.append({
        "test_case_id": "TC-01-null-cogs-mixed-lines",
        "edge_case_category": "data_availability",
        "description": "Stress-testing formula behavior when a line item lacks cost data: missing Line 2 COGS makes true order profitability unverifiable.",
        "shopify_order_payload": {
            "id": "gid://shopify/Order/7001000001",
            "name": "#1001",
            "processedAt": "2026-09-15T14:22:10Z",
            "cancelledAt": None,
            "displayFinancialStatus": "PAID",
            "taxesIncluded": False,
            "currencyCode": "USD",
            "paymentGatewayNames": ["shopify_payments"],
            "lineItems": [
                {
                    "id": "gid://shopify/LineItem/8001000001",
                    "currentQuantity": 1,
                    "discountedUnitPriceSet": {"shopMoney": {"amount": "29.99"}},
                    "variant": {"id": "gid://shopify/ProductVariant/6001000001", "inventoryItem": {"unitCost": {"amount": "18.45"}}},
                    "taxLines": []
                },
                {
                    "id": "gid://shopify/LineItem/8001000002",
                    "currentQuantity": 1,
                    "discountedUnitPriceSet": {"shopMoney": {"amount": "14.50"}},
                    "variant": {"id": "gid://shopify/ProductVariant/6001000002", "inventoryItem": {"unitCost": None}},
                    "taxLines": []
                },
                {
                    "id": "gid://shopify/LineItem/8001000003",
                    "currentQuantity": 1,
                    "discountedUnitPriceSet": {"shopMoney": {"amount": "39.95"}},
                    "variant": {"id": "gid://shopify/ProductVariant/6001000003", "inventoryItem": {"unitCost": {"amount": "24.80"}}},
                    "taxLines": []
                }
            ],
            "shippingLines": [{"discountedPriceSet": {"shopMoney": {"amount": "0.00"}}}],
            "transactions": [{"id": "gid://shopify/OrderTransaction/4001000001", "kind": "SALE", "status": "SUCCESS", "fees": [{"amount": {"amount": "2.75"}}]}]
        },
        "external_data": {"actual_3pl_shipping_invoice": 8.50, "gateway_settlement_fee": 2.75},
        "cogs_snapshot_table_entry": None,
        "expected_result": {
            "evaluability_status": "NOT_EVALUABLE",
            "f03_breach": False,
            "f03_loss": 0.0,
            "flags_expected": ["is_cogs_missing"]
        },
        "why_this_breaks_naive_implementations": "Catches systems that silently coerce null COGS to $0.00 or drop null-cost lines."
    })

    # 2. TC-02: 3PL shipping invoice lag
    order_fixtures.append({
        "test_case_id": "TC-02-shipping-invoice-lag",
        "edge_case_category": "data_availability",
        "description": "3PL shipping invoice lagged: Rev $37.74 - COGS $26.15 - EstShip $11.40 - Fee $1.25 = -$1.06 breach with fallback shipping.",
        "shopify_order_payload": {
            "id": "gid://shopify/Order/7001000002",
            "name": "#1002",
            "processedAt": "2026-09-15T15:00:00Z",
            "cancelledAt": None,
            "displayFinancialStatus": "PAID",
            "taxesIncluded": False,
            "currencyCode": "USD",
            "paymentGatewayNames": ["shopify_payments"],
            "lineItems": [
                {
                    "id": "gid://shopify/LineItem/8001000004",
                    "currentQuantity": 1,
                    "discountedUnitPriceSet": {"shopMoney": {"amount": "37.74"}},
                    "variant": {"id": "gid://shopify/ProductVariant/6001000004", "inventoryItem": {"unitCost": {"amount": "26.15"}}},
                    "taxLines": []
                }
            ],
            "shippingLines": [{"discountedPriceSet": {"shopMoney": {"amount": "0.00"}}}],
            "transactions": [{"id": "gid://shopify/OrderTransaction/4001000002", "fees": [{"amount": {"amount": "1.25"}}]}]
        },
        "external_data": {"actual_3pl_shipping_invoice": 11.40, "is_shipping_estimated": True},
        "cogs_snapshot_table_entry": 26.15,
        "expected_result": {
            "evaluability_status": "EVALUATED_ESTIMATED",
            "f03_breach": True,
            "f03_loss": 1.06,
            "flags_expected": ["is_shipping_cost_estimated"]
        },
        "why_this_breaks_naive_implementations": "Catches pipelines defaulting missing shipping to $0."
    })

    # 3. TC-03: Gateway fee missing (Razorpay)
    order_fixtures.append({
        "test_case_id": "TC-03-gateway-fee-missing-razorpay",
        "edge_case_category": "data_availability",
        "description": "Missing gateway fee on third-party processor (Razorpay): Rev INR 1499 - COGS INR 1320 - Ship INR 180 - EstFee INR 35.38 = -INR 36.38 breach.",
        "shopify_order_payload": {
            "id": "gid://shopify/Order/7001000003",
            "name": "#1003",
            "processedAt": "2026-09-15T16:00:00Z",
            "cancelledAt": None,
            "displayFinancialStatus": "PAID",
            "taxesIncluded": False,
            "currencyCode": "INR",
            "paymentGatewayNames": ["razorpay"],
            "lineItems": [
                {
                    "id": "gid://shopify/LineItem/8001000005",
                    "currentQuantity": 1,
                    "discountedUnitPriceSet": {"shopMoney": {"amount": "1499.00"}},
                    "variant": {"id": "gid://shopify/ProductVariant/6001000005", "inventoryItem": {"unitCost": {"amount": "1320.00"}}},
                    "taxLines": []
                }
            ],
            "shippingLines": [{"discountedPriceSet": {"shopMoney": {"amount": "0.00"}}}],
            "transactions": [{"id": "gid://shopify/OrderTransaction/4001000003", "fees": []}]
        },
        "external_data": {"actual_3pl_shipping_invoice": 180.00},
        "cogs_snapshot_table_entry": 1320.00,
        "expected_result": {
            "evaluability_status": "EVALUATED_ESTIMATED",
            "f03_breach": True,
            "f03_loss": 36.38,
            "flags_expected": ["is_gateway_fee_estimated"]
        },
        "why_this_breaks_naive_implementations": "Catches pipelines assuming non-empty transactions.fees on 3rd-party gateways."
    })

    # 4. TC-04A: Discount omitted naive
    order_fixtures.append({
        "test_case_id": "TC-04A-order-discount-unapplied-naive",
        "edge_case_category": "discount",
        "description": "Order coupon unapplied (naive query): Rev $60.00 - COGS $42.50 - Ship $8.20 - Fee $2.04 = +$7.26 healthy.",
        "shopify_order_payload": {
            "id": "gid://shopify/Order/7001000004",
            "name": "#1004A",
            "processedAt": "2026-09-16T10:00:00Z",
            "cancelledAt": None,
            "displayFinancialStatus": "PAID",
            "taxesIncluded": False,
            "currencyCode": "USD",
            "paymentGatewayNames": ["shopify_payments"],
            "lineItems": [
                {
                    "id": "gid://shopify/LineItem/8001000006",
                    "currentQuantity": 1,
                    "discountedUnitPriceSet": {"shopMoney": {"amount": "60.00"}},
                    "variant": {"id": "gid://shopify/ProductVariant/6001000006", "inventoryItem": {"unitCost": {"amount": "42.50"}}},
                    "taxLines": []
                }
            ],
            "shippingLines": [{"discountedPriceSet": {"shopMoney": {"amount": "0.00"}}}],
            "transactions": [{"id": "gid://shopify/OrderTransaction/4001000004", "fees": [{"amount": {"amount": "2.04"}}]}]
        },
        "external_data": {"actual_3pl_shipping_invoice": 8.20, "gateway_settlement_fee": 2.04},
        "cogs_snapshot_table_entry": 42.50,
        "expected_result": {
            "evaluability_status": "EVALUATED_CONFIRMED",
            "f03_breach": False,
            "f03_loss": 0.0,
            "flags_expected": []
        },
        "why_this_breaks_naive_implementations": "Shows false green when coupon code allocation is omitted."
    })

    # 5. TC-04B: Discount applied correct
    order_fixtures.append({
        "test_case_id": "TC-04B-order-discount-applied-correct",
        "edge_case_category": "discount",
        "description": "Order coupon applied (correct): Rev $35.00 - COGS $42.50 - Ship $8.20 - Fee $1.32 = -$17.02 breach.",
        "shopify_order_payload": {
            "id": "gid://shopify/Order/7001000005",
            "name": "#1004B",
            "processedAt": "2026-09-16T10:05:00Z",
            "cancelledAt": None,
            "displayFinancialStatus": "PAID",
            "taxesIncluded": False,
            "currencyCode": "USD",
            "paymentGatewayNames": ["shopify_payments"],
            "lineItems": [
                {
                    "id": "gid://shopify/LineItem/8001000007",
                    "currentQuantity": 1,
                    "discountedUnitPriceSet": {"shopMoney": {"amount": "35.00"}},
                    "variant": {"id": "gid://shopify/ProductVariant/6001000007", "inventoryItem": {"unitCost": {"amount": "42.50"}}},
                    "taxLines": []
                }
            ],
            "shippingLines": [{"discountedPriceSet": {"shopMoney": {"amount": "0.00"}}}],
            "transactions": [{"id": "gid://shopify/OrderTransaction/4001000005", "fees": [{"amount": {"amount": "1.32"}}]}]
        },
        "external_data": {"actual_3pl_shipping_invoice": 8.20, "gateway_settlement_fee": 1.32},
        "cogs_snapshot_table_entry": 42.50,
        "expected_result": {
            "evaluability_status": "EVALUATED_CONFIRMED",
            "f03_breach": True,
            "f03_loss": 17.02,
            "flags_expected": []
        },
        "why_this_breaks_naive_implementations": "Catches false negatives when cart discount code is applied."
    })

    # 6. TC-05: Stacked discounts
    order_fixtures.append({
        "test_case_id": "TC-05-stacked-auto-plus-code-discount",
        "edge_case_category": "discount",
        "description": "Stacked automatic + coupon code: Rev $54.70 - COGS $51.25 - Ship $7.85 - Fee $1.89 = -$6.29 breach.",
        "shopify_order_payload": {
            "id": "gid://shopify/Order/7001000006",
            "name": "#1005",
            "processedAt": "2026-09-16T11:00:00Z",
            "cancelledAt": None,
            "displayFinancialStatus": "PAID",
            "taxesIncluded": False,
            "currencyCode": "USD",
            "paymentGatewayNames": ["shopify_payments"],
            "lineItems": [
                {
                    "id": "gid://shopify/LineItem/8001000008",
                    "currentQuantity": 1,
                    "discountedUnitPriceSet": {"shopMoney": {"amount": "54.70"}},
                    "variant": {"id": "gid://shopify/ProductVariant/6001000008", "inventoryItem": {"unitCost": {"amount": "51.25"}}},
                    "taxLines": []
                }
            ],
            "shippingLines": [{"discountedPriceSet": {"shopMoney": {"amount": "0.00"}}}],
            "transactions": [{"id": "gid://shopify/OrderTransaction/4001000006", "fees": [{"amount": {"amount": "1.89"}}]}]
        },
        "external_data": {"actual_3pl_shipping_invoice": 7.85, "gateway_settlement_fee": 1.89},
        "cogs_snapshot_table_entry": 51.25,
        "expected_result": {
            "evaluability_status": "EVALUATED_CONFIRMED",
            "f03_breach": True,
            "f03_loss": 6.29,
            "flags_expected": []
        },
        "why_this_breaks_naive_implementations": "Catches double-counting or dropping stacked discount layers."
    })

    # 7. TC-06: taxesIncluded GST 18% in INR
    order_fixtures.append({
        "test_case_id": "TC-06-taxes-included-gst-inr",
        "edge_case_category": "tax",
        "description": "taxesIncluded=true (GST 18%): Sticker INR 2360, Tax INR 360 -> NetRev INR 2000 - COGS INR 1850 - Ship INR 250 - Fee INR 55.70 = -INR 155.70 breach.",
        "shopify_order_payload": {
            "id": "gid://shopify/Order/7001000007",
            "name": "#1006",
            "processedAt": "2026-09-16T12:00:00Z",
            "cancelledAt": None,
            "displayFinancialStatus": "PAID",
            "taxesIncluded": True,
            "currencyCode": "INR",
            "paymentGatewayNames": ["razorpay"],
            "currentTotalTaxSet": {"shopMoney": {"amount": "360.00"}},
            "lineItems": [
                {
                    "id": "gid://shopify/LineItem/8001000009",
                    "currentQuantity": 1,
                    "discountedUnitPriceSet": {"shopMoney": {"amount": "2360.00"}},
                    "variant": {"id": "gid://shopify/ProductVariant/6001000009", "inventoryItem": {"unitCost": {"amount": "1850.00"}}},
                    "taxLines": [{"priceSet": {"shopMoney": {"amount": "360.00"}}}]
                }
            ],
            "shippingLines": [{"discountedPriceSet": {"shopMoney": {"amount": "0.00"}}}],
            "transactions": [{"id": "gid://shopify/OrderTransaction/4001000007", "fees": []}]
        },
        "external_data": {"actual_3pl_shipping_invoice": 250.00, "gateway_settlement_fee": 55.70},
        "cogs_snapshot_table_entry": 1850.00,
        "expected_result": {
            "evaluability_status": "EVALUATED_CONFIRMED",
            "f03_breach": True,
            "f03_loss": 155.70,
            "flags_expected": []
        },
        "why_this_breaks_naive_implementations": "Catches systems mistaking tax liability collected for government as revenue."
    })

    # 8. TC-07: taxesExcluded US sales tax
    order_fixtures.append({
        "test_case_id": "TC-07-taxes-excluded-us-sales-tax",
        "edge_case_category": "tax",
        "description": "taxesIncluded=false: Subtotal $75.50 - COGS $68.40 - Ship $11.20 - Fee $2.67 = -$6.77 breach.",
        "shopify_order_payload": {
            "id": "gid://shopify/Order/7001000008",
            "name": "#1007",
            "processedAt": "2026-09-16T13:00:00Z",
            "cancelledAt": None,
            "displayFinancialStatus": "PAID",
            "taxesIncluded": False,
            "currencyCode": "USD",
            "paymentGatewayNames": ["shopify_payments"],
            "lineItems": [
                {
                    "id": "gid://shopify/LineItem/8001000010",
                    "currentQuantity": 1,
                    "discountedUnitPriceSet": {"shopMoney": {"amount": "75.50"}},
                    "variant": {"id": "gid://shopify/ProductVariant/6001000010", "inventoryItem": {"unitCost": {"amount": "68.40"}}},
                    "taxLines": [{"priceSet": {"shopMoney": {"amount": "6.23"}}}]
                }
            ],
            "shippingLines": [{"discountedPriceSet": {"shopMoney": {"amount": "0.00"}}}],
            "transactions": [{"id": "gid://shopify/OrderTransaction/4001000008", "fees": [{"amount": {"amount": "2.67"}}]}]
        },
        "external_data": {"actual_3pl_shipping_invoice": 11.20, "gateway_settlement_fee": 2.67},
        "cogs_snapshot_table_entry": 68.40,
        "expected_result": {
            "evaluability_status": "EVALUATED_CONFIRMED",
            "f03_breach": True,
            "f03_loss": 6.77,
            "flags_expected": []
        },
        "why_this_breaks_naive_implementations": "Catches systems polluting revenue with pass-through customer sales tax."
    })

    # 9. TC-08: Markets EUR presentment, USD shop
    order_fixtures.append({
        "test_case_id": "TC-08-markets-multicurrency-eur-usd",
        "edge_case_category": "currency",
        "description": "Shopify Markets EUR customer / USD shop: shopMoney $92.40 - COGS $88.00 - Ship $8.50 - Fee $2.98 = -$7.08 breach.",
        "shopify_order_payload": {
            "id": "gid://shopify/Order/7001000009",
            "name": "#1008",
            "processedAt": "2026-09-16T14:00:00Z",
            "cancelledAt": None,
            "displayFinancialStatus": "PAID",
            "taxesIncluded": False,
            "currencyCode": "USD",
            "paymentGatewayNames": ["shopify_payments"],
            "lineItems": [
                {
                    "id": "gid://shopify/LineItem/8001000011",
                    "currentQuantity": 1,
                    "discountedUnitPriceSet": {
                        "shopMoney": {"amount": "92.40"},
                        "presentmentMoney": {"amount": "85.00"}
                    },
                    "variant": {"id": "gid://shopify/ProductVariant/6001000011", "inventoryItem": {"unitCost": {"amount": "88.00"}}},
                    "taxLines": []
                }
            ],
            "shippingLines": [{"discountedPriceSet": {"shopMoney": {"amount": "0.00"}}}],
            "transactions": [{"id": "gid://shopify/OrderTransaction/4001000009", "fees": [{"amount": {"amount": "2.98"}}]}]
        },
        "external_data": {"actual_3pl_shipping_invoice": 8.50, "gateway_settlement_fee": 2.98},
        "cogs_snapshot_table_entry": 88.00,
        "expected_result": {
            "evaluability_status": "EVALUATED_CONFIRMED",
            "f03_breach": True,
            "f03_loss": 7.08,
            "flags_expected": []
        },
        "why_this_breaks_naive_implementations": "Catches systems subtracting USD costs from EUR presentment amounts."
    })

    # 10. TC-09: Partially refunded line return
    order_fixtures.append({
        "test_case_id": "TC-09-partially-refunded-line-return",
        "edge_case_category": "financial_status",
        "description": "PARTIALLY_REFUNDED with restock: NetRev $45.00 - COGS $36.50 - Ship $9.80 - Fee $2.91 = -$4.21 breach.",
        "shopify_order_payload": {
            "id": "gid://shopify/Order/7001000010",
            "name": "#1009",
            "processedAt": "2026-09-16T15:00:00Z",
            "cancelledAt": None,
            "displayFinancialStatus": "PARTIALLY_REFUNDED",
            "taxesIncluded": False,
            "currencyCode": "USD",
            "paymentGatewayNames": ["shopify_payments"],
            "lineItems": [
                {
                    "id": "gid://shopify/LineItem/8001000012",
                    "currentQuantity": 1,
                    "discountedUnitPriceSet": {"shopMoney": {"amount": "45.00"}},
                    "variant": {"id": "gid://shopify/ProductVariant/6001000012", "inventoryItem": {"unitCost": {"amount": "36.50"}}},
                    "taxLines": []
                },
                {
                    "id": "gid://shopify/LineItem/8001000013",
                    "currentQuantity": 0,
                    "discountedUnitPriceSet": {"shopMoney": {"amount": "45.00"}},
                    "variant": {"id": "gid://shopify/ProductVariant/6001000013", "inventoryItem": {"unitCost": {"amount": "36.50"}}},
                    "taxLines": []
                }
            ],
            "shippingLines": [{"discountedPriceSet": {"shopMoney": {"amount": "0.00"}}}],
            "transactions": [{"id": "gid://shopify/OrderTransaction/4001000010", "fees": [{"amount": {"amount": "2.91"}}]}],
            "refunds": [
                {
                    "refundLineItems": [{"lineItem": {"id": "gid://shopify/LineItem/8001000013"}, "quantity": 1, "restockType": "RETURN"}],
                    "transactions": [{"amountSet": {"shopMoney": {"amount": "45.00"}}}]
                }
            ]
        },
        "external_data": {"actual_3pl_shipping_invoice": 9.80, "gateway_settlement_fee": 2.91},
        "cogs_snapshot_table_entry": 36.50,
        "expected_result": {
            "evaluability_status": "EVALUATED_CONFIRMED",
            "f03_breach": True,
            "f03_loss": 4.21,
            "flags_expected": []
        },
        "why_this_breaks_naive_implementations": "Catches systems failing to adjust active line counts post-refund."
    })

    # 11. TC-10: VOIDED pre-capture order (BUG 6 fix)
    order_fixtures.append({
        "test_case_id": "TC-10-voided-pre-capture-order",
        "edge_case_category": "financial_status",
        "description": "VOIDED authorization before capture: No cash received, no fulfillment. Filtered before evaluability gate.",
        "shopify_order_payload": {
            "id": "gid://shopify/Order/7001000011",
            "name": "#1010",
            "processedAt": "2026-09-16T16:00:00Z",
            "cancelledAt": None,
            "displayFinancialStatus": "VOIDED",
            "taxesIncluded": False,
            "currencyCode": "USD",
            "paymentGatewayNames": ["shopify_payments"],
            "lineItems": [],
            "shippingLines": [],
            "transactions": []
        },
        "external_data": {},
        "cogs_snapshot_table_entry": None,
        "expected_result": {
            "evaluability_status": "FILTERED_NO_CASH",
            "f03_breach": False,
            "f03_loss": 0.0,
            "flags_expected": []
        },
        "why_this_breaks_naive_implementations": "Prevents counting zero-cash voided orders as healthy, avoiding denominator dilution."
    })

    # 12. TC-11: PENDING payment unsettled (BUG 6 fix)
    order_fixtures.append({
        "test_case_id": "TC-11-pending-payment-unsettled",
        "edge_case_category": "financial_status",
        "description": "PENDING bank wire payment: Unsettled order with no cash event. Filtered before evaluability gate.",
        "shopify_order_payload": {
            "id": "gid://shopify/Order/7001000012",
            "name": "#1011",
            "processedAt": "2026-09-16T17:00:00Z",
            "cancelledAt": None,
            "displayFinancialStatus": "PENDING",
            "taxesIncluded": False,
            "currencyCode": "USD",
            "paymentGatewayNames": ["bank_transfer"],
            "lineItems": [],
            "shippingLines": [],
            "transactions": []
        },
        "external_data": {},
        "cogs_snapshot_table_entry": None,
        "expected_result": {
            "evaluability_status": "FILTERED_NO_CASH",
            "f03_breach": False,
            "f03_loss": 0.0,
            "flags_expected": []
        },
        "why_this_breaks_naive_implementations": "Prevents evaluating unfulfilled pending orders as either instant losses or false greens."
    })

    # 13. TC-12: Item returned & restocked
    order_fixtures.append({
        "test_case_id": "TC-12-returned-restocked-cost-isolated",
        "edge_case_category": "return",
        "description": "Returned & restocked: Rev $0.00 - COGS $0.00 - Ship $8.75 - Fee $1.90 = -$10.65 breach (dead freight + non-refundable fee).",
        "shopify_order_payload": {
            "id": "gid://shopify/Order/7001000013",
            "name": "#1012",
            "processedAt": "2026-09-17T09:00:00Z",
            "cancelledAt": None,
            "displayFinancialStatus": "REFUNDED",
            "taxesIncluded": False,
            "currencyCode": "USD",
            "paymentGatewayNames": ["shopify_payments"],
            "lineItems": [
                {
                    "id": "gid://shopify/LineItem/8001000014",
                    "currentQuantity": 0,
                    "discountedUnitPriceSet": {"shopMoney": {"amount": "50.00"}},
                    "variant": {"id": "gid://shopify/ProductVariant/6001000014", "inventoryItem": {"unitCost": {"amount": "30.00"}}},
                    "taxLines": []
                }
            ],
            "shippingLines": [{"discountedPriceSet": {"shopMoney": {"amount": "0.00"}}}],
            "transactions": [{"id": "gid://shopify/OrderTransaction/4001000013", "fees": [{"amount": {"amount": "1.90"}}]}],
            "refunds": [
                {
                    "refundLineItems": [{"lineItem": {"id": "gid://shopify/LineItem/8001000014"}, "quantity": 1, "restockType": "RETURN"}],
                    "transactions": [{"amountSet": {"shopMoney": {"amount": "50.00"}}}]
                }
            ]
        },
        "external_data": {"actual_3pl_shipping_invoice": 8.75, "gateway_settlement_fee": 1.90},
        "cogs_snapshot_table_entry": 30.00,
        "expected_result": {
            "evaluability_status": "EVALUATED_CONFIRMED",
            "f03_breach": True,
            "f03_loss": 10.65,
            "flags_expected": []
        },
        "why_this_breaks_naive_implementations": "Catches systems charging COGS for merchandise returned to shelf inventory."
    })

    # 14. TC-13: Item returned damaged (NO_RESTOCK)
    order_fixtures.append({
        "test_case_id": "TC-13-returned-damaged-no-restock",
        "edge_case_category": "return",
        "description": "Returned damaged (scrap): Rev $0.00 - COGS $38.20 - Ship $9.40 - Fee $2.17 = -$49.77 breach.",
        "shopify_order_payload": {
            "id": "gid://shopify/Order/7001000014",
            "name": "#1013",
            "processedAt": "2026-09-17T10:00:00Z",
            "cancelledAt": None,
            "displayFinancialStatus": "REFUNDED",
            "taxesIncluded": False,
            "currencyCode": "USD",
            "paymentGatewayNames": ["shopify_payments"],
            "lineItems": [
                {
                    "id": "gid://shopify/LineItem/8001000015",
                    "currentQuantity": 0,
                    "discountedUnitPriceSet": {"shopMoney": {"amount": "70.00"}},
                    "variant": {"id": "gid://shopify/ProductVariant/6001000015", "inventoryItem": {"unitCost": {"amount": "38.20"}}},
                    "taxLines": []
                }
            ],
            "shippingLines": [{"discountedPriceSet": {"shopMoney": {"amount": "0.00"}}}],
            "transactions": [{"id": "gid://shopify/OrderTransaction/4001000014", "fees": [{"amount": {"amount": "2.17"}}]}],
            "refunds": [
                {
                    "refundLineItems": [{"lineItem": {"id": "gid://shopify/LineItem/8001000015"}, "quantity": 1, "restockType": "NO_RESTOCK"}],
                    "transactions": [{"amountSet": {"shopMoney": {"amount": "70.00"}}}]
                }
            ]
        },
        "external_data": {"actual_3pl_shipping_invoice": 9.40, "gateway_settlement_fee": 2.17},
        "cogs_snapshot_table_entry": 38.20,
        "expected_result": {
            "evaluability_status": "EVALUATED_CONFIRMED",
            "f03_breach": True,
            "f03_loss": 49.77,
            "flags_expected": []
        },
        "why_this_breaks_naive_implementations": "Catches systems forgiving COGS on scrapped, unsellable inventory."
    })

    # 15. TC-14: Full refund no return (buyer kept item)
    order_fixtures.append({
        "test_case_id": "TC-14-full-refund-no-return",
        "edge_case_category": "refund",
        "description": "Full refund concession (kept by buyer): Rev $0.00 - COGS $31.80 - Ship $7.60 - Fee $1.72 = -$41.12 breach.",
        "shopify_order_payload": {
            "id": "gid://shopify/Order/7001000015",
            "name": "#1014",
            "processedAt": "2026-09-17T11:00:00Z",
            "cancelledAt": None,
            "displayFinancialStatus": "REFUNDED",
            "taxesIncluded": False,
            "currencyCode": "USD",
            "paymentGatewayNames": ["shopify_payments"],
            "lineItems": [
                {
                    "id": "gid://shopify/LineItem/8001000016",
                    "currentQuantity": 1,
                    "discountedUnitPriceSet": {"shopMoney": {"amount": "55.00"}},
                    "variant": {"id": "gid://shopify/ProductVariant/6001000016", "inventoryItem": {"unitCost": {"amount": "31.80"}}},
                    "taxLines": []
                }
            ],
            "shippingLines": [{"discountedPriceSet": {"shopMoney": {"amount": "0.00"}}}],
            "transactions": [{"id": "gid://shopify/OrderTransaction/4001000015", "fees": [{"amount": {"amount": "1.72"}}]}],
            "refunds": [
                {
                    "refundLineItems": [],
                    "transactions": [{"amountSet": {"shopMoney": {"amount": "55.00"}}}]
                }
            ]
        },
        "external_data": {"actual_3pl_shipping_invoice": 7.60, "gateway_settlement_fee": 1.72},
        "cogs_snapshot_table_entry": 31.80,
        "expected_result": {
            "evaluability_status": "EVALUATED_CONFIRMED",
            "f03_breach": True,
            "f03_loss": 41.12,
            "flags_expected": []
        },
        "why_this_breaks_naive_implementations": "Catches systems relying on refundLineItems to trigger inventory write-offs."
    })

    # 16. TC-15: Split-tender gift card + credit card
    order_fixtures.append({
        "test_case_id": "TC-15-split-tender-gift-card-cc",
        "edge_case_category": "payment_method",
        "description": "Split-tender $50 gift card + $70 credit card: Fee $2.33 strictly on card. Rev $120.00 - COGS $107.45 - Ship $11.80 - Fee $2.33 = -$1.58 breach.",
        "shopify_order_payload": {
            "id": "gid://shopify/Order/7001000016",
            "name": "#1015",
            "processedAt": "2026-09-17T12:00:00Z",
            "cancelledAt": None,
            "displayFinancialStatus": "PAID",
            "taxesIncluded": False,
            "currencyCode": "USD",
            "paymentGatewayNames": ["gift_card", "shopify_payments"],
            "lineItems": [
                {
                    "id": "gid://shopify/LineItem/8001000017",
                    "currentQuantity": 1,
                    "discountedUnitPriceSet": {"shopMoney": {"amount": "120.00"}},
                    "variant": {"id": "gid://shopify/ProductVariant/6001000017", "inventoryItem": {"unitCost": {"amount": "107.45"}}},
                    "taxLines": []
                }
            ],
            "shippingLines": [{"discountedPriceSet": {"shopMoney": {"amount": "0.00"}}}],
            "transactions": [
                {"id": "gid://shopify/OrderTransaction/4001000016", "gateway": "gift_card", "fees": []},
                {"id": "gid://shopify/OrderTransaction/4001000017", "gateway": "shopify_payments", "fees": [{"amount": {"amount": "2.33"}}]}
            ]
        },
        "external_data": {"actual_3pl_shipping_invoice": 11.80, "gateway_settlement_fee": 2.33},
        "cogs_snapshot_table_entry": 107.45,
        "expected_result": {
            "evaluability_status": "EVALUATED_CONFIRMED",
            "f03_breach": True,
            "f03_loss": 1.58,
            "flags_expected": []
        },
        "why_this_breaks_naive_implementations": "Catches systems applying fee percentages across zero-fee gift card portions."
    })

    # 17. TC-16: Manual COD zero fees
    order_fixtures.append({
        "test_case_id": "TC-16-manual-cod-zero-fees-by-design",
        "edge_case_category": "payment_method",
        "description": "Manual COD with $0.00 gateway fee by design: Rev INR 2450 - COGS INR 2100 - Ship INR 385 - Fee INR 0.00 = -INR 35.00 breach.",
        "shopify_order_payload": {
            "id": "gid://shopify/Order/7001000017",
            "name": "#1016",
            "processedAt": "2026-09-17T13:00:00Z",
            "cancelledAt": None,
            "displayFinancialStatus": "PAID",
            "taxesIncluded": False,
            "currencyCode": "INR",
            "paymentGatewayNames": ["Cash on Delivery (COD)"],
            "lineItems": [
                {
                    "id": "gid://shopify/LineItem/8001000018",
                    "currentQuantity": 1,
                    "discountedUnitPriceSet": {"shopMoney": {"amount": "2450.00"}},
                    "variant": {"id": "gid://shopify/ProductVariant/6001000018", "inventoryItem": {"unitCost": {"amount": "2100.00"}}},
                    "taxLines": []
                }
            ],
            "shippingLines": [{"discountedPriceSet": {"shopMoney": {"amount": "0.00"}}}],
            "transactions": [{"id": "gid://shopify/OrderTransaction/4001000018", "gateway": "Cash on Delivery (COD)", "fees": []}]
        },
        "external_data": {"actual_3pl_shipping_invoice": 385.00},
        "cogs_snapshot_table_entry": 2100.00,
        "expected_result": {
            "evaluability_status": "EVALUATED_CONFIRMED",
            "f03_breach": True,
            "f03_loss": 35.00,
            "flags_expected": []
        },
        "why_this_breaks_naive_implementations": "Catches systems raising false fee estimation flags on legitimate $0 COD."
    })

    # 18. TC-17: POS walkout zero shipping
    order_fixtures.append({
        "test_case_id": "TC-17-pos-in-person-zero-shipping",
        "edge_case_category": "channel",
        "description": "Retail POS in-person walkout: Rev $45.00 - COGS $38.90 - Ship $0.00 - Fee $1.22 = +$4.88 healthy.",
        "shopify_order_payload": {
            "id": "gid://shopify/Order/7001000018",
            "name": "#1017-POS",
            "sourceName": "pos",
            "processedAt": "2026-09-17T14:00:00Z",
            "cancelledAt": None,
            "displayFinancialStatus": "PAID",
            "taxesIncluded": False,
            "currencyCode": "USD",
            "paymentGatewayNames": ["shopify_payments"],
            "lineItems": [
                {
                    "id": "gid://shopify/LineItem/8001000019",
                    "currentQuantity": 1,
                    "discountedUnitPriceSet": {"shopMoney": {"amount": "45.00"}},
                    "variant": {"id": "gid://shopify/ProductVariant/6001000019", "inventoryItem": {"unitCost": {"amount": "38.90"}}},
                    "taxLines": []
                }
            ],
            "shippingLines": [{"discountedPriceSet": {"shopMoney": {"amount": "0.00"}}, "title": "In-Store Walkout"}],
            "transactions": [{"id": "gid://shopify/OrderTransaction/4001000019", "fees": [{"amount": {"amount": "1.22"}}]}]
        },
        "external_data": {"gateway_settlement_fee": 1.22},
        "cogs_snapshot_table_entry": 38.90,
        "expected_result": {
            "evaluability_status": "EVALUATED_CONFIRMED",
            "f03_breach": False,
            "f03_loss": 0.0,
            "flags_expected": []
        },
        "why_this_breaks_naive_implementations": "Catches systems applying default courier freight to in-person POS sales."
    })

    # 19. TC-18: Boundary break-even ($0.00 margin)
    order_fixtures.append({
        "test_case_id": "TC-18-exact-zero-margin-boundary",
        "edge_case_category": "boundary",
        "description": "Boundary break-even: Rev $50.00 - COGS $36.00 - Ship $12.55 - Fee $1.45 = $0.00 exactly (NOT a breach).",
        "shopify_order_payload": {
            "id": "gid://shopify/Order/7001000019",
            "name": "#1018",
            "processedAt": "2026-09-17T15:00:00Z",
            "cancelledAt": None,
            "displayFinancialStatus": "PAID",
            "taxesIncluded": False,
            "currencyCode": "USD",
            "paymentGatewayNames": ["shopify_payments"],
            "lineItems": [
                {
                    "id": "gid://shopify/LineItem/8001000020",
                    "currentQuantity": 1,
                    "discountedUnitPriceSet": {"shopMoney": {"amount": "50.00"}},
                    "variant": {"id": "gid://shopify/ProductVariant/6001000020", "inventoryItem": {"unitCost": {"amount": "36.00"}}},
                    "taxLines": []
                }
            ],
            "shippingLines": [{"discountedPriceSet": {"shopMoney": {"amount": "0.00"}}}],
            "transactions": [{"id": "gid://shopify/OrderTransaction/4001000020", "fees": [{"amount": {"amount": "1.45"}}]}]
        },
        "external_data": {"actual_3pl_shipping_invoice": 12.55, "gateway_settlement_fee": 1.45},
        "cogs_snapshot_table_entry": 36.00,
        "expected_result": {
            "evaluability_status": "EVALUATED_CONFIRMED",
            "f03_breach": False,
            "f03_loss": 0.0,
            "flags_expected": []
        },
        "why_this_breaks_naive_implementations": "Catches <= instead of < in breach comparison logic."
    })

    # 20. TC-19: Boundary deficit (-$0.01 margin)
    order_fixtures.append({
        "test_case_id": "TC-19-exact-negative-one-cent-boundary",
        "edge_case_category": "boundary",
        "description": "Boundary deficit: Rev $50.00 - COGS $36.00 - Ship $12.55 - Fee $1.46 = -$0.01 breach.",
        "shopify_order_payload": {
            "id": "gid://shopify/Order/7001000020",
            "name": "#1019",
            "processedAt": "2026-09-17T16:00:00Z",
            "cancelledAt": None,
            "displayFinancialStatus": "PAID",
            "taxesIncluded": False,
            "currencyCode": "USD",
            "paymentGatewayNames": ["shopify_payments"],
            "lineItems": [
                {
                    "id": "gid://shopify/LineItem/8001000021",
                    "currentQuantity": 1,
                    "discountedUnitPriceSet": {"shopMoney": {"amount": "50.00"}},
                    "variant": {"id": "gid://shopify/ProductVariant/6001000021", "inventoryItem": {"unitCost": {"amount": "36.00"}}},
                    "taxLines": []
                }
            ],
            "shippingLines": [{"discountedPriceSet": {"shopMoney": {"amount": "0.00"}}}],
            "transactions": [{"id": "gid://shopify/OrderTransaction/4001000021", "fees": [{"amount": {"amount": "1.46"}}]}]
        },
        "external_data": {"actual_3pl_shipping_invoice": 12.55, "gateway_settlement_fee": 1.46},
        "cogs_snapshot_table_entry": 36.00,
        "expected_result": {
            "evaluability_status": "EVALUATED_CONFIRMED",
            "f03_breach": True,
            "f03_loss": 0.01,
            "flags_expected": []
        },
        "why_this_breaks_naive_implementations": "Catches floating-point roundoff masking single-penny breaches."
    })

    # 21. TC-20: Multiline deduplication (5 lines sharing 1 shipping fee)
    order_fixtures.append({
        "test_case_id": "TC-20-multiline-single-shipping-dedup",
        "edge_case_category": "duplicate_integrity",
        "description": "5 lines sharing 1 shipping fee: Rev $100.00 - COGS $73.00 - Ship $9.50 - Fee $3.20 = +$14.30 healthy.",
        "shopify_order_payload": {
            "id": "gid://shopify/Order/7001000021",
            "name": "#1020",
            "processedAt": "2026-09-17T17:00:00Z",
            "cancelledAt": None,
            "displayFinancialStatus": "PAID",
            "taxesIncluded": False,
            "currencyCode": "USD",
            "paymentGatewayNames": ["shopify_payments"],
            "lineItems": [
                {
                    "id": f"gid://shopify/LineItem/800100002{i}",
                    "currentQuantity": 1,
                    "discountedUnitPriceSet": {"shopMoney": {"amount": "20.00"}},
                    "variant": {"id": f"gid://shopify/ProductVariant/600100002{i}", "inventoryItem": {"unitCost": {"amount": "14.60"}}},
                    "taxLines": []
                }
                for i in range(1, 6)
            ],
            "shippingLines": [{"discountedPriceSet": {"shopMoney": {"amount": "0.00"}}}],
            "transactions": [{"id": "gid://shopify/OrderTransaction/4001000022", "fees": [{"amount": {"amount": "3.20"}}]}]
        },
        "external_data": {"actual_3pl_shipping_invoice": 9.50, "gateway_settlement_fee": 3.20},
        "cogs_snapshot_table_entry": 14.60,
        "expected_result": {
            "evaluability_status": "EVALUATED_CONFIRMED",
            "f03_breach": False,
            "f03_loss": 0.0,
            "flags_expected": []
        },
        "why_this_breaks_naive_implementations": "Catches SQL fan-out joins multiplying shipping fees across line items."
    })

    # 22. TC-21: Bundle BOM explosion
    order_fixtures.append({
        "test_case_id": "TC-21-bundle-sku-understated-cogs",
        "edge_case_category": "bundle",
        "description": "Bundle BOM component explosion ($49.50) vs placeholder $5.00: Rev $49.99 - COGS $49.50 - Ship $7.25 - Fee $1.75 = -$8.51 breach.",
        "shopify_order_payload": {
            "id": "gid://shopify/Order/7001000022",
            "name": "#1021",
            "processedAt": "2026-09-17T18:00:00Z",
            "cancelledAt": None,
            "displayFinancialStatus": "PAID",
            "taxesIncluded": False,
            "currencyCode": "USD",
            "paymentGatewayNames": ["shopify_payments"],
            "lineItems": [
                {
                    "id": "gid://shopify/LineItem/8001000028",
                    "currentQuantity": 1,
                    "discountedUnitPriceSet": {"shopMoney": {"amount": "49.99"}},
                    "variant": {
                        "id": "gid://shopify/ProductVariant/6001000028",
                        "sku": "BUNDLE-TRIO-01",
                        "inventoryItem": {"unitCost": {"amount": "5.00"}},
                        "metafields": [
                            {
                                "namespace": "custom",
                                "key": "bundle_components",
                                "value": json.dumps([
                                    {"component_sku": "SKU-A", "quantity": 1, "unit_cost": 16.50},
                                    {"component_sku": "SKU-B", "quantity": 1, "unit_cost": 18.00},
                                    {"component_sku": "SKU-C", "quantity": 1, "unit_cost": 15.00}
                                ])
                            }
                        ]
                    },
                    "taxLines": []
                }
            ],
            "shippingLines": [{"discountedPriceSet": {"shopMoney": {"amount": "0.00"}}}],
            "transactions": [{"id": "gid://shopify/OrderTransaction/4001000023", "fees": [{"amount": {"amount": "1.75"}}]}]
        },
        "external_data": {"actual_3pl_shipping_invoice": 7.25, "gateway_settlement_fee": 1.75},
        "cogs_snapshot_table_entry": None,
        "expected_result": {
            "evaluability_status": "EVALUATED_CONFIRMED",
            "f03_breach": True,
            "f03_loss": 8.51,
            "flags_expected": ["is_bundle"]
        },
        "why_this_breaks_naive_implementations": "Catches systems reading placeholder bundle unitCost without component BOM explosion."
    })

    # 23. TC-22: Historical cost drift
    order_fixtures.append({
        "test_case_id": "TC-22-historical-cost-drift",
        "edge_case_category": "historical_drift",
        "description": "Historical cost drift: Live cost $25.00 vs snapshot $42.00: Rev $52.00 - COGS $42.00 - Ship $8.40 - Fee $1.81 = -$0.21 breach.",
        "shopify_order_payload": {
            "id": "gid://shopify/Order/7001000023",
            "name": "#1022",
            "processedAt": "2026-09-17T19:00:00Z",
            "cancelledAt": None,
            "displayFinancialStatus": "PAID",
            "taxesIncluded": False,
            "currencyCode": "USD",
            "paymentGatewayNames": ["shopify_payments"],
            "lineItems": [
                {
                    "id": "gid://shopify/LineItem/8001000029",
                    "currentQuantity": 1,
                    "discountedUnitPriceSet": {"shopMoney": {"amount": "52.00"}},
                    "variant": {"id": "gid://shopify/ProductVariant/6001000029", "inventoryItem": {"unitCost": {"amount": "25.00"}}},
                    "taxLines": []
                }
            ],
            "shippingLines": [{"discountedPriceSet": {"shopMoney": {"amount": "0.00"}}}],
            "transactions": [{"id": "gid://shopify/OrderTransaction/4001000024", "fees": [{"amount": {"amount": "1.81"}}]}]
        },
        "external_data": {"actual_3pl_shipping_invoice": 8.40, "gateway_settlement_fee": 1.81},
        "cogs_snapshot_table_entry": 42.00,
        "expected_result": {
            "evaluability_status": "EVALUATED_CONFIRMED",
            "f03_breach": True,
            "f03_loss": 0.21,
            "flags_expected": []
        },
        "why_this_breaks_naive_implementations": "Catches systems querying live variant cost rather than point-in-time snapshot."
    })

    # 24a. TC-23-T1: Timing progressive reconciliation (T+2h Pre-settlement estimated state)
    order_fixtures.append({
        "test_case_id": "TC-23-T1-timing-pre-settlement-estimate",
        "edge_case_category": "timing",
        "description": "Progressive reconciliation state T1 (T+2h): Pre-settlement estimate with 3PL fallback $12.00 and gateway estimate $2.19 -> Rev $65.00 - COGS $54.00 - Ops $14.19 = -$3.19 breach.",
        "shopify_order_payload": {
            "id": "gid://shopify/Order/7001000024",
            "name": "#1023",
            "processedAt": "2026-09-18T10:00:00Z",
            "cancelledAt": None,
            "displayFinancialStatus": "PAID",
            "taxesIncluded": False,
            "currencyCode": "USD",
            "paymentGatewayNames": ["paypal"],
            "lineItems": [
                {
                    "id": "gid://shopify/LineItem/8001000030",
                    "currentQuantity": 1,
                    "discountedUnitPriceSet": {"shopMoney": {"amount": "65.00"}},
                    "variant": {"id": "gid://shopify/ProductVariant/6001000030", "inventoryItem": {"unitCost": {"amount": "54.00"}}},
                    "taxLines": []
                }
            ],
            "shippingLines": [{"discountedPriceSet": {"shopMoney": {"amount": "0.00"}}}],
            "transactions": [{"id": "gid://shopify/OrderTransaction/4001000025", "fees": []}]
        },
        "external_data": {},
        "eval_timestamp": "t1_before_settlement",
        "cogs_snapshot_table_entry": 54.00,
        "expected_result": {
            "evaluability_status": "EVALUATED_ESTIMATED",
            "f03_breach": True,
            "f03_loss": 3.19,
            "flags_expected": ["is_shipping_cost_estimated", "is_gateway_fee_estimated"]
        },
        "why_this_breaks_naive_implementations": "Catches static pipelines failing to capture pre-settlement estimated state."
    })

    # 24b. TC-23-T2: Timing progressive reconciliation (T+72h Post-settlement confirmed state)
    order_fixtures.append({
        "test_case_id": "TC-23-T2-timing-post-settlement-confirmed",
        "edge_case_category": "timing",
        "description": "Progressive reconciliation state T2 (T+72h): Post-settlement confirmed 3PL invoice $8.50 and gateway fee $1.95 -> Rev $65.00 - COGS $54.00 - Ops $10.45 = +$0.55 healthy.",
        "shopify_order_payload": {
            "id": "gid://shopify/Order/7001000024",
            "name": "#1023",
            "processedAt": "2026-09-18T10:00:00Z",
            "cancelledAt": None,
            "displayFinancialStatus": "PAID",
            "taxesIncluded": False,
            "currencyCode": "USD",
            "paymentGatewayNames": ["paypal"],
            "lineItems": [
                {
                    "id": "gid://shopify/LineItem/8001000030",
                    "currentQuantity": 1,
                    "discountedUnitPriceSet": {"shopMoney": {"amount": "65.00"}},
                    "variant": {"id": "gid://shopify/ProductVariant/6001000030", "inventoryItem": {"unitCost": {"amount": "54.00"}}},
                    "taxLines": []
                }
            ],
            "shippingLines": [{"discountedPriceSet": {"shopMoney": {"amount": "0.00"}}}],
            "transactions": [{"id": "gid://shopify/OrderTransaction/4001000025", "fees": []}]
        },
        "external_data": {"actual_3pl_shipping_invoice": 8.50, "gateway_settlement_fee": 1.95},
        "eval_timestamp": "2026-09-21T10:00:00Z",
        "cogs_snapshot_table_entry": 54.00,
        "expected_result": {
            "evaluability_status": "EVALUATED_CONFIRMED",
            "f03_breach": False,
            "f03_loss": 0.0,
            "flags_expected": []
        },
        "why_this_breaks_naive_implementations": "Catches static pipelines freezing initial estimates."
    })

    # 25. TC-24: Timezone cutoff cross-day (BUG 7 fix)
    order_fixtures.append({
        "test_case_id": "TC-24-timezone-cutoff-cross-day",
        "edge_case_category": "timezone",
        "description": "Timezone cross-day: Order at 2026-09-23T19:00:00Z is 2026-09-24 00:30:00 in Asia/Kolkata (shop tz). Rev INR 1999 - COGS INR 1750 - Ship INR 230 - Fee INR 47.18 = -INR 28.18 breach.",
        "shopify_order_payload": {
            "id": "gid://shopify/Order/7001000025",
            "name": "#1024",
            "processedAt": "2026-09-23T19:00:00Z",
            "cancelledAt": None,
            "displayFinancialStatus": "PAID",
            "taxesIncluded": False,
            "currencyCode": "INR",
            "paymentGatewayNames": ["razorpay"],
            "lineItems": [
                {
                    "id": "gid://shopify/LineItem/8001000031",
                    "currentQuantity": 1,
                    "discountedUnitPriceSet": {"shopMoney": {"amount": "1999.00"}},
                    "variant": {"id": "gid://shopify/ProductVariant/6001000031", "inventoryItem": {"unitCost": {"amount": "1750.00"}}},
                    "taxLines": []
                }
            ],
            "shippingLines": [{"discountedPriceSet": {"shopMoney": {"amount": "0.00"}}}],
            "transactions": [{"id": "gid://shopify/OrderTransaction/4001000026", "fees": []}]
        },
        "external_data": {"actual_3pl_shipping_invoice": 230.00, "gateway_settlement_fee": 47.18},
        "cogs_snapshot_table_entry": 1750.00,
        "expected_result": {
            "evaluability_status": "EVALUATED_CONFIRMED",
            "f03_breach": True,
            "f03_loss": 28.18,
            "flags_expected": [],
            "rollup_date_utc": "2026-09-23",
            "rollup_date_shop_tz": "2026-09-24"
        },
        "why_this_breaks_naive_implementations": "Catches analytics systems truncating dates in UTC rather than the merchant's operational timezone."
    })

    # 26-35. TC-25 Unbundled: 10 individual orders for batch denominator test
    # 3 missing COGS, 2 breaches, 5 healthy
    # 3 Missing COGS:
    for i in range(1, 4):
        order_fixtures.append({
            "test_case_id": f"TC-25-{i:02d}-batch-null-cogs",
            "edge_case_category": "denominator",
            "description": f"TC-25 unbundled order {i}/10: Missing supplier COGS triggers quarantine (NOT_EVALUABLE).",
            "shopify_order_payload": {
                "id": f"gid://shopify/Order/7001000025{i:02d}",
                "name": f"#1025-NULL-{i}",
                "processedAt": "2026-09-18T12:00:00Z",
                "cancelledAt": None,
                "displayFinancialStatus": "PAID",
                "taxesIncluded": False,
                "currencyCode": "USD",
                "paymentGatewayNames": ["shopify_payments"],
                "lineItems": [
                    {
                        "id": f"gid://shopify/LineItem/8001000025{i:02d}",
                        "currentQuantity": 1,
                        "discountedUnitPriceSet": {"shopMoney": {"amount": "45.00"}},
                        "variant": {"id": f"gid://shopify/ProductVariant/6001000025{i:02d}", "inventoryItem": {"unitCost": None}},
                        "taxLines": []
                    }
                ],
                "shippingLines": [{"discountedPriceSet": {"shopMoney": {"amount": "0.00"}}}],
                "transactions": [{"id": f"gid://shopify/OrderTransaction/4001000025{i:02d}", "fees": [{"amount": {"amount": "1.50"}}]}]
            },
            "external_data": {"actual_3pl_shipping_invoice": 8.50, "gateway_settlement_fee": 1.50},
            "cogs_snapshot_table_entry": None,
            "expected_result": {
                "evaluability_status": "NOT_EVALUABLE",
                "f03_breach": False,
                "f03_loss": 0.0,
                "flags_expected": ["is_cogs_missing"]
            },
            "why_this_breaks_naive_implementations": "Quarantined orders must be excluded from the clean commercial breach rate denominator."
        })

    # 2 Breaches in TC-25:
    # Breach 1: Rev $40.00, COGS $35.00, Ship $8.50, Fee $1.50 -> Loss $5.00
    order_fixtures.append({
        "test_case_id": "TC-25-04-batch-breach-1",
        "edge_case_category": "denominator",
        "description": "TC-25 unbundled order 4/10: Rev $40.00 - COGS $35.00 - Ship $8.50 - Fee $1.50 = -$5.00 breach.",
        "shopify_order_payload": {
            "id": "gid://shopify/Order/700100002504",
            "name": "#1025-BREACH-1",
            "processedAt": "2026-09-18T13:00:00Z",
            "cancelledAt": None,
            "displayFinancialStatus": "PAID",
            "taxesIncluded": False,
            "currencyCode": "USD",
            "paymentGatewayNames": ["shopify_payments"],
            "lineItems": [
                {
                    "id": "gid://shopify/LineItem/800100002504",
                    "currentQuantity": 1,
                    "discountedUnitPriceSet": {"shopMoney": {"amount": "40.00"}},
                    "variant": {"id": "gid://shopify/ProductVariant/600100002504", "inventoryItem": {"unitCost": {"amount": "35.00"}}},
                    "taxLines": []
                }
            ],
            "shippingLines": [{"discountedPriceSet": {"shopMoney": {"amount": "0.00"}}}],
            "transactions": [{"id": "gid://shopify/OrderTransaction/400100002504", "fees": [{"amount": {"amount": "1.50"}}]}]
        },
        "external_data": {"actual_3pl_shipping_invoice": 8.50, "gateway_settlement_fee": 1.50},
        "cogs_snapshot_table_entry": 35.00,
        "expected_result": {
            "evaluability_status": "EVALUATED_CONFIRMED",
            "f03_breach": True,
            "f03_loss": 5.00,
            "flags_expected": []
        },
        "why_this_breaks_naive_implementations": "Evaluated confirmed commercial breach."
    })

    # Breach 2: Rev $60.00, COGS $55.00, Ship $10.00, Fee $2.50 -> Loss $7.50
    order_fixtures.append({
        "test_case_id": "TC-25-05-batch-breach-2",
        "edge_case_category": "denominator",
        "description": "TC-25 unbundled order 5/10: Rev $60.00 - COGS $55.00 - Ship $10.00 - Fee $2.50 = -$7.50 breach.",
        "shopify_order_payload": {
            "id": "gid://shopify/Order/700100002505",
            "name": "#1025-BREACH-2",
            "processedAt": "2026-09-18T13:30:00Z",
            "cancelledAt": None,
            "displayFinancialStatus": "PAID",
            "taxesIncluded": False,
            "currencyCode": "USD",
            "paymentGatewayNames": ["shopify_payments"],
            "lineItems": [
                {
                    "id": "gid://shopify/LineItem/800100002505",
                    "currentQuantity": 1,
                    "discountedUnitPriceSet": {"shopMoney": {"amount": "60.00"}},
                    "variant": {"id": "gid://shopify/ProductVariant/600100002505", "inventoryItem": {"unitCost": {"amount": "55.00"}}},
                    "taxLines": []
                }
            ],
            "shippingLines": [{"discountedPriceSet": {"shopMoney": {"amount": "0.00"}}}],
            "transactions": [{"id": "gid://shopify/OrderTransaction/400100002505", "fees": [{"amount": {"amount": "2.50"}}]}]
        },
        "external_data": {"actual_3pl_shipping_invoice": 10.00, "gateway_settlement_fee": 2.50},
        "cogs_snapshot_table_entry": 55.00,
        "expected_result": {
            "evaluability_status": "EVALUATED_CONFIRMED",
            "f03_breach": True,
            "f03_loss": 7.50,
            "flags_expected": []
        },
        "why_this_breaks_naive_implementations": "Evaluated confirmed commercial breach."
    })

    # 5 Healthy Orders in TC-25:
    healthy_params = [
        (6, 80.00, 45.00, 8.50, 2.50),   # profit +24.00
        (7, 90.00, 50.00, 8.50, 2.80),   # profit +28.70
        (8, 100.00, 60.00, 8.50, 3.00),  # profit +28.50
        (9, 70.00, 40.00, 8.50, 2.20),   # profit +19.30
        (10, 85.00, 45.00, 8.50, 2.60)   # profit +28.90
    ]
    for idx, rev, cogs, ship, fee in healthy_params:
        order_fixtures.append({
            "test_case_id": f"TC-25-{idx:02d}-batch-healthy-{idx-5}",
            "edge_case_category": "denominator",
            "description": f"TC-25 unbundled order {idx}/10: Rev ${rev:.2f} - COGS ${cogs:.2f} - Ship ${ship:.2f} - Fee ${fee:.2f} = +${rev-cogs-ship-fee:.2f} profit.",
            "shopify_order_payload": {
                "id": f"gid://shopify/Order/7001000025{idx:02d}",
                "name": f"#1025-HEALTHY-{idx-5}",
                "processedAt": f"2026-09-18T14:{idx:02d}:00Z",
                "cancelledAt": None,
                "displayFinancialStatus": "PAID",
                "taxesIncluded": False,
                "currencyCode": "USD",
                "paymentGatewayNames": ["shopify_payments"],
                "lineItems": [
                    {
                        "id": f"gid://shopify/LineItem/8001000025{idx:02d}",
                        "currentQuantity": 1,
                        "discountedUnitPriceSet": {"shopMoney": {"amount": f"{rev:.2f}"}},
                        "variant": {"id": f"gid://shopify/ProductVariant/6001000025{idx:02d}", "inventoryItem": {"unitCost": {"amount": f"{cogs:.2f}"}}},
                        "taxLines": []
                    }
                ],
                "shippingLines": [{"discountedPriceSet": {"shopMoney": {"amount": "0.00"}}}],
                "transactions": [{"id": f"gid://shopify/OrderTransaction/4001000025{idx:02d}", "fees": [{"amount": {"amount": f"{fee:.2f}"}}]}]
            },
            "external_data": {"actual_3pl_shipping_invoice": ship, "gateway_settlement_fee": fee},
            "cogs_snapshot_table_entry": cogs,
            "expected_result": {
                "evaluability_status": "EVALUATED_CONFIRMED",
                "f03_breach": False,
                "f03_loss": 0.0,
                "flags_expected": []
            },
            "why_this_breaks_naive_implementations": "Evaluated confirmed healthy commercial transaction."
        })

    # 36-40. TC-27 Unbundled: 5 individual loss-leader orders
    for k in range(1, 6):
        order_fixtures.append({
            "test_case_id": f"TC-27-{k:02d}-loss-leader-repeated",
            "edge_case_category": "loss_leader",
            "description": f"TC-27 unbundled order {k}/5: Repeated loss-leader SKU: Rev $15.00 - COGS $14.50 - Ship $3.50 - Fee $0.74 = -$3.74 breach.",
            "shopify_order_payload": {
                "id": f"gid://shopify/Order/7001000027{k:02d}",
                "name": f"#1027-{k}",
                "processedAt": f"2026-09-19T23:0{k}:00Z",
                "cancelledAt": None,
                "displayFinancialStatus": "PAID",
                "taxesIncluded": False,
                "currencyCode": "USD",
                "paymentGatewayNames": ["shopify_payments"],
                "lineItems": [
                    {
                        "id": f"gid://shopify/LineItem/8001000027{k:02d}",
                        "currentQuantity": 1,
                        "discountedUnitPriceSet": {"shopMoney": {"amount": "15.00"}},
                        "variant": {"id": f"gid://shopify/ProductVariant/6001000027{k:02d}", "inventoryItem": {"unitCost": {"amount": "14.50"}}},
                        "taxLines": []
                    }
                ],
                "shippingLines": [{"discountedPriceSet": {"shopMoney": {"amount": "0.00"}}}],
                "transactions": [{"id": f"gid://shopify/OrderTransaction/4001000027{k:02d}", "fees": [{"amount": {"amount": "0.74"}}]}]
            },
            "external_data": {"actual_3pl_shipping_invoice": 3.50, "gateway_settlement_fee": 0.74},
            "cogs_snapshot_table_entry": 14.50,
            "expected_result": {
                "evaluability_status": "EVALUATED_CONFIRMED",
                "f03_breach": True,
                "f03_loss": 3.74,
                "flags_expected": []
            },
            "why_this_breaks_naive_implementations": "Catches systems deduplicating legitimate repeated loss-leader orders."
        })

    # 41. TC-28: Cancelled mid-fulfillment partial ship
    order_fixtures.append({
        "test_case_id": "TC-28-cancelled-mid-fulfillment-partial-ship",
        "edge_case_category": "cancellation",
        "description": "Cancelled mid-fulfillment with 1 unit shipped: Retained Rev $30.00 - Shipped COGS $22.40 - Ship $7.80 - Fee $1.74 = -$1.94 breach.",
        "shopify_order_payload": {
            "id": "gid://shopify/Order/7001000028",
            "name": "#1028",
            "processedAt": "2026-09-18T08:00:00Z",
            "cancelledAt": "2026-09-18T16:30:00Z",
            "displayFinancialStatus": "PARTIALLY_REFUNDED",
            "taxesIncluded": False,
            "currencyCode": "USD",
            "paymentGatewayNames": ["shopify_payments"],
            "lineItems": [
                {
                    "id": "gid://shopify/LineItem/8001000032",
                    "currentQuantity": 1,
                    "discountedUnitPriceSet": {"shopMoney": {"amount": "30.00"}},
                    "variant": {"id": "gid://shopify/ProductVariant/6001000032", "inventoryItem": {"unitCost": {"amount": "22.40"}}},
                    "taxLines": []
                },
                {
                    "id": "gid://shopify/LineItem/8001000033",
                    "currentQuantity": 0,
                    "discountedUnitPriceSet": {"shopMoney": {"amount": "30.00"}},
                    "variant": {"id": "gid://shopify/ProductVariant/6001000033", "inventoryItem": {"unitCost": {"amount": "22.40"}}},
                    "taxLines": []
                }
            ],
            "shippingLines": [{"discountedPriceSet": {"shopMoney": {"amount": "0.00"}}}],
            "transactions": [{"id": "gid://shopify/OrderTransaction/4001000028", "fees": [{"amount": {"amount": "1.74"}}]}],
            "refunds": [
                {
                    "refundLineItems": [{"lineItem": {"id": "gid://shopify/LineItem/8001000033"}, "quantity": 1, "restockType": "CANCEL"}],
                    "transactions": [{"amountSet": {"shopMoney": {"amount": "30.00"}}}]
                }
            ]
        },
        "external_data": {"actual_3pl_shipping_invoice": 7.80, "gateway_settlement_fee": 1.74},
        "cogs_snapshot_table_entry": 22.40,
        "expected_result": {
            "evaluability_status": "EVALUATED_CONFIRMED",
            "f03_breach": True,
            "f03_loss": 1.94,
            "flags_expected": []
        },
        "why_this_breaks_naive_implementations": "Catches systems wiping liabilities when cancelledAt != null despite partial physical shipment."
    })

    # 42. TC-29: EXCLUDED_PROMOTIONAL ($0.00 PR gifting, BUG 5 fix)
    order_fixtures.append({
        "test_case_id": "TC-29-promotional-influencer-gifting",
        "edge_case_category": "channel",
        "description": "Influencer / PR gifting $0.00 order tagged 'pr_gifting': Excluded from commercial breach denominator (EXCLUDED_PROMOTIONAL).",
        "shopify_order_payload": {
            "id": "gid://shopify/Order/7001000029",
            "name": "#1029-PR",
            "tags": ["pr_gifting", "influencer_sample"],
            "processedAt": "2026-09-18T18:00:00Z",
            "cancelledAt": None,
            "displayFinancialStatus": "PAID",
            "taxesIncluded": False,
            "currencyCode": "USD",
            "paymentGatewayNames": ["free"],
            "lineItems": [
                {
                    "id": "gid://shopify/LineItem/8001000034",
                    "currentQuantity": 1,
                    "discountedUnitPriceSet": {"shopMoney": {"amount": "0.00"}},
                    "variant": {"id": "gid://shopify/ProductVariant/6001000034", "inventoryItem": {"unitCost": {"amount": "25.00"}}},
                    "taxLines": []
                }
            ],
            "shippingLines": [{"discountedPriceSet": {"shopMoney": {"amount": "0.00"}}}],
            "transactions": []
        },
        "external_data": {"actual_3pl_shipping_invoice": 6.50, "gateway_settlement_fee": 0.00},
        "cogs_snapshot_table_entry": 25.00,
        "expected_result": {
            "evaluability_status": "EXCLUDED_PROMOTIONAL",
            "f03_breach": False,
            "f03_loss": 0.0,
            "flags_expected": ["is_promotional_gifting"]
        },
        "why_this_breaks_naive_implementations": "Prevents treating intentional $0 marketing giveaways as commercial product margin breaches."
    })

    # 43. TC-30: order.test = true sandbox order (BUG B fix)
    order_fixtures.append({
        "test_case_id": "TC-30-sandbox-test-order-filtered",
        "edge_case_category": "financial_status",
        "description": "Sandbox/developer test order (order.test == true): Filtered prior to evaluability gating (FILTERED_TEST_ORDER).",
        "shopify_order_payload": {
            "id": "gid://shopify/Order/7001000030",
            "name": "#1030-TEST",
            "test": True,
            "processedAt": "2026-09-18T19:00:00Z",
            "cancelledAt": None,
            "displayFinancialStatus": "PAID",
            "taxesIncluded": False,
            "currencyCode": "USD",
            "paymentGatewayNames": ["bogus"],
            "lineItems": [
                {
                    "id": "gid://shopify/LineItem/8001000035",
                    "currentQuantity": 1,
                    "discountedUnitPriceSet": {"shopMoney": {"amount": "100.00"}},
                    "variant": {"id": "gid://shopify/ProductVariant/6001000035", "inventoryItem": {"unitCost": {"amount": "50.00"}}},
                    "taxLines": []
                }
            ],
            "shippingLines": [{"discountedPriceSet": {"shopMoney": {"amount": "10.00"}}}],
            "transactions": []
        },
        "external_data": {"actual_3pl_shipping_invoice": 8.50, "gateway_settlement_fee": 2.50},
        "cogs_snapshot_table_entry": 50.00,
        "expected_result": {
            "evaluability_status": "FILTERED_TEST_ORDER",
            "f03_breach": False,
            "f03_loss": 0.0,
            "flags_expected": []
        },
        "why_this_breaks_naive_implementations": "Prevents developer sandbox test orders from corrupting production cash margin reporting."
    })

    # 44. TC-31: Stacked line-specific + order-wide cart discount on same line
    order_fixtures.append({
        "test_case_id": "TC-31-stacked-line-and-cart-discounts",
        "edge_case_category": "discount",
        "description": "Step 2 & 3 isolation: LineItem with $15 line-specific coupon + $10 allocated cart coupon on $100 item -> TotalDiscount $25, NetPrice $75. NetRev $75 - COGS $65 - Ship $8.50 - Fee $2.50 = -$1.00 breach.",
        "shopify_order_payload": {
            "id": "gid://shopify/Order/7001000031",
            "name": "#1031",
            "processedAt": "2026-09-18T20:00:00Z",
            "cancelledAt": None,
            "displayFinancialStatus": "PAID",
            "taxesIncluded": False,
            "currencyCode": "USD",
            "paymentGatewayNames": ["shopify_payments"],
            "lineItems": [
                {
                    "id": "gid://shopify/LineItem/8001000036",
                    "quantity": 1,
                    "currentQuantity": 1,
                    "originalUnitPriceSet": {"shopMoney": {"amount": "100.00"}},
                    "discountedUnitPriceSet": {"shopMoney": {"amount": "75.00"}},
                    "discountAllocations": [
                        {
                            "allocatedAmountSet": {"shopMoney": {"amount": "15.00"}},
                            "discountApplication": {"targetType": "LINE_ITEM", "title": "15OFF_SKU"}
                        },
                        {
                            "allocatedAmountSet": {"shopMoney": {"amount": "10.00"}},
                            "discountApplication": {"targetType": "ORDER", "title": "CART10"}
                        }
                    ],
                    "variant": {"id": "gid://shopify/ProductVariant/6001000036", "inventoryItem": {"unitCost": {"amount": "65.00"}}},
                    "taxLines": []
                }
            ],
            "shippingLines": [{"discountedPriceSet": {"shopMoney": {"amount": "0.00"}}}],
            "transactions": [{"id": "gid://shopify/OrderTransaction/4001000031", "fees": [{"amount": {"amount": "2.50"}}]}]
        },
        "external_data": {"actual_3pl_shipping_invoice": 8.50, "gateway_settlement_fee": 2.50},
        "cogs_snapshot_table_entry": 65.00,
        "expected_result": {
            "evaluability_status": "EVALUATED_CONFIRMED",
            "f03_breach": True,
            "f03_loss": 1.00,
            "flags_expected": [],
            "line_discount_expected": 15.00,
            "cart_discount_expected": 10.00,
            "total_discount_expected": 25.00,
            "discounted_price_expected": 75.00,
            "gross_profit_expected": 10.00
        },
        "why_this_breaks_naive_implementations": "Catches implementations failing to separately isolate line-targeted discounts from order-wide coupon allocations."
    })

    # 45. TC-32: Tax-inclusive order with partial refund (Step 8 tax-stripping proof)
    order_fixtures.append({
        "test_case_id": "TC-32-tax-inclusive-partial-refund-isolated",
        "edge_case_category": "refund",
        "description": "Step 8 isolation: GST 18% inclusive order ₹1180 (NetPrice ₹1000, Tax ₹180). Refunded ₹1180 (Gross ₹1180 - Tax ₹180 = NetRefund ₹1000). NetRev = ₹0. Restocked COGS ₹0. Courier ₹150 + Fee ₹28 = -₹178 breach.",
        "shopify_order_payload": {
            "id": "gid://shopify/Order/7001000032",
            "name": "#1032",
            "processedAt": "2026-09-18T21:00:00Z",
            "cancelledAt": None,
            "displayFinancialStatus": "REFUNDED",
            "taxesIncluded": True,
            "currencyCode": "INR",
            "paymentGatewayNames": ["razorpay"],
            "currentTotalTaxSet": {"shopMoney": {"amount": "180.00"}},
            "lineItems": [
                {
                    "id": "gid://shopify/LineItem/8001000037",
                    "quantity": 1,
                    "currentQuantity": 0,
                    "originalUnitPriceSet": {"shopMoney": {"amount": "1180.00"}},
                    "discountedUnitPriceSet": {"shopMoney": {"amount": "1180.00"}},
                    "variant": {"id": "gid://shopify/ProductVariant/6001000037", "inventoryItem": {"unitCost": {"amount": "800.00"}}},
                    "taxLines": [{"priceSet": {"shopMoney": {"amount": "180.00"}}}]
                }
            ],
            "shippingLines": [{"discountedPriceSet": {"shopMoney": {"amount": "0.00"}}}],
            "transactions": [{"id": "gid://shopify/OrderTransaction/4001000032", "fees": []}],
            "refunds": [
                {
                    "refundLineItems": [
                        {
                            "lineItem": {"id": "gid://shopify/LineItem/8001000037"},
                            "quantity": 1,
                            "restockType": "RETURN",
                            "subtotalSet": {"shopMoney": {"amount": "1180.00"}},
                            "taxSet": {"shopMoney": {"amount": "180.00"}}
                        }
                    ],
                    "transactions": [{"amountSet": {"shopMoney": {"amount": "1180.00"}}}]
                }
            ]
        },
        "external_data": {"actual_3pl_shipping_invoice": 150.00, "gateway_settlement_fee": 28.00},
        "cogs_snapshot_table_entry": 800.00,
        "expected_result": {
            "evaluability_status": "EVALUATED_CONFIRMED",
            "f03_breach": True,
            "f03_loss": 178.00,
            "flags_expected": [],
            "tax_adjustment_expected": 180.00,
            "net_selling_price_expected": 1000.00,
            "net_refund_expected": 1000.00,
            "net_revenue_expected": 0.00
        },
        "why_this_breaks_naive_implementations": "Catches systems subtracting gross refund from tax-exclusive net revenue, double-counting tax liabilities."
    })

    # 46. TC-33: Shipping line tax-inclusive (Step 16 isolation)
    order_fixtures.append({
        "test_case_id": "TC-33-shipping-tax-inclusive-isolated",
        "edge_case_category": "tax",
        "description": "Step 16 isolation: Shipping fee $12.00 includes $2.00 VAT/tax -> NetShippingRevenue $10.00. Merch $50 (COGS $40) + NetShip $10 - Courier $11.50 - Fee $1.80 = +$6.70 healthy.",
        "shopify_order_payload": {
            "id": "gid://shopify/Order/7001000033",
            "name": "#1033",
            "processedAt": "2026-09-18T22:00:00Z",
            "cancelledAt": None,
            "displayFinancialStatus": "PAID",
            "taxesIncluded": True,
            "currencyCode": "USD",
            "paymentGatewayNames": ["shopify_payments"],
            "lineItems": [
                {
                    "id": "gid://shopify/LineItem/8001000038",
                    "quantity": 1,
                    "currentQuantity": 1,
                    "originalUnitPriceSet": {"shopMoney": {"amount": "50.00"}},
                    "discountedUnitPriceSet": {"shopMoney": {"amount": "50.00"}},
                    "variant": {"id": "gid://shopify/ProductVariant/6001000038", "inventoryItem": {"unitCost": {"amount": "40.00"}}},
                    "taxLines": []
                }
            ],
            "shippingLines": [
                {
                    "discountedPriceSet": {"shopMoney": {"amount": "12.00"}},
                    "taxLines": [{"priceSet": {"shopMoney": {"amount": "2.00"}}}]
                }
            ],
            "transactions": [{"id": "gid://shopify/OrderTransaction/4001000033", "fees": [{"amount": {"amount": "1.80"}}]}]
        },
        "external_data": {"actual_3pl_shipping_invoice": 11.50, "gateway_settlement_fee": 1.80},
        "cogs_snapshot_table_entry": 40.00,
        "expected_result": {
            "evaluability_status": "EVALUATED_CONFIRMED",
            "f03_breach": False,
            "f03_loss": 0.0,
            "flags_expected": [],
            "gross_shipping_expected": 12.00,
            "shipping_tax_adjustment_expected": 2.00,
            "net_shipping_revenue_expected": 10.00
        },
        "why_this_breaks_naive_implementations": "Catches systems failing to extract embedded statutory tax from delivery fees."
    })

    # 47. TC-34: Standalone shipping refund (Step 17 & 18 isolation)
    order_fixtures.append({
        "test_case_id": "TC-34-shipping-refund-isolated",
        "edge_case_category": "refund",
        "description": "Step 17 & 18 isolation: Late delivery concession: $10 shipping refunded to buyer, item kept ($60 Rev, $48 COGS). NetShipRev $0. Rev $60 - COGS $48 - Courier $9.50 - Fee $2.10 = +$0.40 healthy.",
        "shopify_order_payload": {
            "id": "gid://shopify/Order/7001000034",
            "name": "#1034",
            "processedAt": "2026-09-18T23:00:00Z",
            "cancelledAt": None,
            "displayFinancialStatus": "PARTIALLY_REFUNDED",
            "taxesIncluded": False,
            "currencyCode": "USD",
            "paymentGatewayNames": ["shopify_payments"],
            "lineItems": [
                {
                    "id": "gid://shopify/LineItem/8001000039",
                    "quantity": 1,
                    "currentQuantity": 1,
                    "originalUnitPriceSet": {"shopMoney": {"amount": "60.00"}},
                    "discountedUnitPriceSet": {"shopMoney": {"amount": "60.00"}},
                    "variant": {"id": "gid://shopify/ProductVariant/6001000039", "inventoryItem": {"unitCost": {"amount": "48.00"}}},
                    "taxLines": []
                }
            ],
            "shippingLines": [{"discountedPriceSet": {"shopMoney": {"amount": "10.00"}}}],
            "transactions": [{"id": "gid://shopify/OrderTransaction/4001000034", "fees": [{"amount": {"amount": "2.10"}}]}],
            "refunds": [
                {
                    "refundShippingLines": [
                        {
                            "subtotalSet": {"shopMoney": {"amount": "10.00"}},
                            "taxSet": {"shopMoney": {"amount": "0.00"}}
                        }
                    ],
                    "transactions": [{"amountSet": {"shopMoney": {"amount": "10.00"}}}]
                }
            ]
        },
        "external_data": {"actual_3pl_shipping_invoice": 9.50, "gateway_settlement_fee": 2.10},
        "cogs_snapshot_table_entry": 48.00,
        "expected_result": {
            "evaluability_status": "EVALUATED_CONFIRMED",
            "f03_breach": False,
            "f03_loss": 0.0,
            "flags_expected": [],
            "gross_shipping_expected": 10.00,
            "net_shipping_refund_expected": 10.00,
            "net_shipping_revenue_expected": 0.00
        },
        "why_this_breaks_naive_implementations": "Catches systems failing to account for standalone courier refunds when merchandise is retained."
    })

    # 48. TC-35: International cross-border shipping fallback (BUG F fix)
    order_fixtures.append({
        "test_case_id": "TC-35-international-shipping-fallback-zone",
        "edge_case_category": "data_availability",
        "description": "International EU shipping fallback: Order to Germany (DE) with lagged 3PL invoice triggers EU fallback rate $14.50. Rev $45.00 - COGS $35.00 - EstShip $14.50 - Fee $1.80 = -$6.30 breach.",
        "shopify_order_payload": {
            "id": "gid://shopify/Order/7001000035",
            "name": "#1035",
            "processedAt": "2026-09-19T08:00:00Z",
            "cancelledAt": None,
            "displayFinancialStatus": "PAID",
            "taxesIncluded": False,
            "currencyCode": "USD",
            "paymentGatewayNames": ["shopify_payments"],
            "shippingAddress": {"countryCode": "DE", "city": "Berlin"},
            "lineItems": [
                {
                    "id": "gid://shopify/LineItem/8001000040",
                    "quantity": 1,
                    "currentQuantity": 1,
                    "originalUnitPriceSet": {"shopMoney": {"amount": "45.00"}},
                    "discountedUnitPriceSet": {"shopMoney": {"amount": "45.00"}},
                    "variant": {"id": "gid://shopify/ProductVariant/6001000040", "inventoryItem": {"unitCost": {"amount": "35.00"}}},
                    "taxLines": []
                }
            ],
            "shippingLines": [{"discountedPriceSet": {"shopMoney": {"amount": "0.00"}}}],
            "transactions": [{"id": "gid://shopify/OrderTransaction/4001000035", "fees": [{"amount": {"amount": "1.80"}}]}]
        },
        "external_data": {},  # 3PL invoice missing
        "cogs_snapshot_table_entry": 35.00,
        "expected_result": {
            "evaluability_status": "EVALUATED_ESTIMATED",
            "f03_breach": True,
            "f03_loss": 6.30,
            "flags_expected": ["is_shipping_cost_estimated"],
            "outbound_shipping_expected": 14.50
        },
        "why_this_breaks_naive_implementations": "Catches systems applying domestic ground rates ($8.50) to cross-border international shipments."
    })

    # Batch Meta-Tests (separate dataset)
    batch_fixtures = [
        {
            "test_case_id": "BATCH-TC-25-denominator-modes",
            "description": "10-order batch testing EXCLUDE mode (2/7 = 28.57%) vs INCLUDE mode (2/10 = 20.00%).",
            "order_ids": [f"TC-25-{i:02d}-batch-{('null-cogs' if i<=3 else ('breach-1' if i==4 else ('breach-2' if i==5 else f'healthy-{i-5}')))}" for i in range(1, 11)],
            "total_orders": 10,
            "quarantined_orders": 3,
            "evaluable_orders": 7,
            "breaching_orders": 2,
            "expected_exclude_rate_pct": 28.57,
            "expected_include_rate_pct": 20.00
        },
        {
            "test_case_id": "BATCH-TC-26-empty-cohort-zero-division",
            "description": "Zero orders in evaluation window: breach rate 0.00%, loss $0.00 without ZeroDivisionError.",
            "order_ids": [],
            "total_orders": 0,
            "quarantined_orders": 0,
            "evaluable_orders": 0,
            "breaching_orders": 0,
            "expected_exclude_rate_pct": 0.00,
            "expected_include_rate_pct": 0.00
        },
        {
            "test_case_id": "BATCH-TC-27-repeated-loss-leader-aggregation",
            "description": "5 repeated loss-leader orders of $3.74 loss each yielding $18.70 cumulative loss.",
            "order_ids": [f"TC-27-{k:02d}-loss-leader-repeated" for k in range(1, 6)],
            "total_orders": 5,
            "quarantined_orders": 0,
            "evaluable_orders": 5,
            "breaching_orders": 5,
            "loss_per_order": 3.74,
            "cumulative_loss": 18.70,
            "expected_exclude_rate_pct": 100.00,
            "expected_include_rate_pct": 100.00
        }
    ]

    print(f"Generated {len(order_fixtures)} order fixtures.")
    print(f"Generated {len(batch_fixtures)} batch meta-test fixtures.")

    out_dir = os.path.dirname(os.path.abspath(__file__))
    with open(os.path.join(out_dir, "test_fixtures.json"), "w", encoding="utf-8") as f:
        json.dump(order_fixtures, f, indent=2)

    with open(os.path.join(out_dir, "batch_fixtures.json"), "w", encoding="utf-8") as f:
        json.dump(batch_fixtures, f, indent=2)

    return order_fixtures, batch_fixtures

if __name__ == "__main__":
    generate_fixtures()
