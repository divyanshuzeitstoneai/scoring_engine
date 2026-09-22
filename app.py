"""
E-Commerce Margin & Leakage Intelligence Dashboard
Formula F01 (Discount Leakage) & Formula F03 (Margin Floor Breach: V1 vs V2)
Ground Truth Validation & QA Engine
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import json
from datetime import datetime, timezone
from formulas.f01_discount_leakage.formula import evaluate_order
from core.fallbacks.margin import STOREWIDE_DEFAULT_TARGET_MARGIN

# Set Page Config
st.set_page_config(
    page_title="Margin & Leakage Scoring Engine | F01 & F03",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom Styling (Dark-mode friendly, premium typography, elevated cards)
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500;600&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }
    
    code, pre {
        font-family: 'JetBrains Mono', monospace !important;
    }
    
    .metric-card {
        background: linear-gradient(135deg, rgba(30, 41, 59, 0.7) 0%, rgba(15, 23, 42, 0.8) 100%);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 12px;
        padding: 20px;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.25);
        backdrop-filter: blur(10px);
    }
    
    .metric-title {
        font-size: 0.85rem;
        font-weight: 500;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        color: #94a3b8;
        margin-bottom: 6px;
    }
    
    .metric-val {
        font-size: 1.85rem;
        font-weight: 700;
        color: #f8fafc;
    }
    
    .metric-sub {
        font-size: 0.8rem;
        color: #64748b;
        margin-top: 4px;
    }
    
    .badge-critical {
        background-color: rgba(239, 68, 68, 0.15);
        color: #f87171;
        border: 1px solid rgba(239, 68, 68, 0.3);
        padding: 3px 10px;
        border-radius: 9999px;
        font-size: 0.75rem;
        font-weight: 600;
        display: inline-block;
    }
    
    .badge-high {
        background-color: rgba(249, 115, 22, 0.15);
        color: #fb923c;
        border: 1px solid rgba(249, 115, 22, 0.3);
        padding: 3px 10px;
        border-radius: 9999px;
        font-size: 0.75rem;
        font-weight: 600;
        display: inline-block;
    }
    
    .badge-medium {
        background-color: rgba(234, 179, 8, 0.15);
        color: #facc15;
        border: 1px solid rgba(234, 179, 8, 0.3);
        padding: 3px 10px;
        border-radius: 9999px;
        font-size: 0.75rem;
        font-weight: 600;
        display: inline-block;
    }
    
    .badge-healthy {
        background-color: rgba(34, 197, 94, 0.15);
        color: #4ade80;
        border: 1px solid rgba(34, 197, 94, 0.3);
        padding: 3px 10px;
        border-radius: 9999px;
        font-size: 0.75rem;
        font-weight: 600;
        display: inline-block;
    }
    
    .callout-box {
        background: rgba(15, 23, 42, 0.6);
        border-left: 4px solid #38bdf8;
        padding: 16px 20px;
        border-radius: 0 8px 8px 0;
        margin: 15px 0;
    }
    
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    
    .stTabs [data-baseweb="tab"] {
        padding: 10px 20px;
        border-radius: 8px;
        font-weight: 600;
        font-size: 0.95rem;
    }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# DATA DEFINITIONS: SCENARIOS TC-01 to TC-12 (F03 Engine)
# ---------------------------------------------------------

SCENARIOS = {
    "TC-01": {
        "id": "TC-01",
        "title": "Standard Clean Order (Sanity Baseline)",
        "flaw": "None (Control Baseline)",
        "leak_type": "Control",
        "severity": "Low",
        "v1_res": 56.80,
        "v1_breach": False,
        "v2_res": 56.80,
        "v2_breach": False,
        "v2_status": "EVALUATED_CONFIRMED",
        "delta": 0.00,
        "desc": "Single-item order ($100), Shopify Payments (fee $3.20), free shipping ($0), delivery courier cost $0 (digital/local), COGS $40. Clean baseline where both formulas agree.",
        "schema_driver": "Order.currentTotalPriceSet, OrderTransaction.fees (Shopify Payments)",
        "takeaway": "Under clean, single-item Shopify Payments orders with zero shipping and tax, both formulas accurately report an identical contribution margin of $56.80.",
        "v1_math": {
            "gross_profit": "100.00 - 40.00 = $60.00",
            "net_margin": "60.00 - 0.00 (Shipping) - 3.20 (Fee) = $56.80",
            "breach": "False",
            "loss": "$0.00"
        },
        "v2_math": {
            "cash_in": "100.00 (Items) + 0.00 (Shipping) - 0.00 (Refunds) = $100.00",
            "cash_out": "40.00 (COGS) + 0.00 (Courier) + 3.20 (Fee) = $43.20",
            "net_margin": "100.00 - 43.20 = +$56.80",
            "breach": "False",
            "loss": "$0.00"
        },
        "json_payload": {
            "order": {
                "id": "gid://shopify/Order/8100000001",
                "name": "#1001",
                "createdAt": "2026-09-15T10:00:00Z",
                "currencyCode": "USD",
                "taxesIncluded": False,
                "currentSubtotalPriceSet": {"shopMoney": {"amount": "100.00", "currencyCode": "USD"}},
                "currentTotalPriceSet": {"shopMoney": {"amount": "100.00", "currencyCode": "USD"}},
                "currentShippingPriceSet": {"shopMoney": {"amount": "0.00", "currencyCode": "USD"}},
                "lineItems": [{"quantity": 1, "discountedUnitPriceSet": {"shopMoney": {"amount": "100.00"}}, "variant": {"inventoryItem": {"unitCost": {"amount": "40.00"}}}}]
            }
        }
    },
    "TC-02": {
        "id": "TC-02",
        "title": "Customer-Paid Flat Shipping vs. Courier Cost",
        "flaw": "Flaw 1: No shipping-revenue-collected term",
        "leak_type": "Formula Leak",
        "severity": "High",
        "v1_res": -9.04,
        "v1_breach": True,
        "v2_res": 0.96,
        "v2_breach": False,
        "v2_status": "EVALUATED_CONFIRMED",
        "delta": 10.00,
        "desc": "Merchant charged customer flat $10 shipping. Item price $50, COGS $25. Outbound courier label cost $32. Gateway fee $2.04 on $60 total collected.",
        "schema_driver": "Omission of Order.currentShippingPriceSet",
        "takeaway": "V1 issues a false alarm claiming this order lost $9.04, when the merchant actually retained +$0.96 in cash because the customer subsidized shipping.",
        "v1_math": {
            "gross_profit": "50.00 - 25.00 = $25.00",
            "net_margin": "25.00 - 32.00 (Courier) - 2.04 (Fee) = -$9.04",
            "breach": "TRUE (False Alarm)",
            "loss": "$9.04"
        },
        "v2_math": {
            "cash_in": "50.00 (Items) + 10.00 (currentShippingPriceSet) = $60.00",
            "cash_out": "25.00 (COGS) + 32.00 (Courier) + 2.04 (Fee) = $59.04",
            "net_margin": "60.00 - 59.04 = +$0.96",
            "breach": "False",
            "loss": "$0.00"
        },
        "json_payload": {
            "order": {
                "id": "gid://shopify/Order/8100000002",
                "name": "#1002",
                "currencyCode": "USD",
                "currentSubtotalPriceSet": {"shopMoney": {"amount": "50.00", "currencyCode": "USD"}},
                "currentShippingPriceSet": {"shopMoney": {"amount": "10.00", "currencyCode": "USD"}},
                "currentTotalPriceSet": {"shopMoney": {"amount": "60.00", "currencyCode": "USD"}}
            }
        }
    },
    "TC-03": {
        "id": "TC-03",
        "title": "Tax-Inclusive Store (VAT) with Thin Margin",
        "flaw": "Flaw 2: No explicit handling of tax-inclusive prices",
        "leak_type": "Formula Leak",
        "severity": "Critical",
        "v1_res": 13.22,
        "v1_breach": False,
        "v2_res": -6.78,
        "v2_breach": True,
        "v2_status": "EVALUATED_CONFIRMED",
        "delta": 20.00,
        "desc": "UK store with 20% VAT in prices. Gross £120 (includes £20 VAT, net £100). COGS £95. Courier £8. Fee £3.78. V1 treats £20 VAT as profit!",
        "schema_driver": "Order.taxesIncluded: true, Order.currentTotalTaxSet",
        "takeaway": "V1 gives a dangerous false green light (+£13.22 profit), masking a real cash-bleeding loss (-£6.78) because the merchant must remit £20.00 in VAT to HMRC.",
        "v1_math": {
            "gross_profit": "120.00 - 95.00 = £25.00",
            "net_margin": "25.00 - 8.00 (Shipping) - 3.78 (Fee) = +£13.22",
            "breach": "False (Dangerous Blindspot)",
            "loss": "£0.00"
        },
        "v2_math": {
            "cash_in": "120.00 - 20.00 (currentTotalTaxSet) = £100.00",
            "cash_out": "95.00 (COGS) + 8.00 (Shipping) + 3.78 (Fee) = £106.78",
            "net_margin": "100.00 - 106.78 = -£6.78",
            "breach": "TRUE",
            "loss": "£6.78"
        },
        "json_payload": {
            "order": {
                "id": "gid://shopify/Order/8100000003",
                "taxesIncluded": True,
                "currencyCode": "GBP",
                "currentTotalPriceSet": {"shopMoney": {"amount": "120.00", "currencyCode": "GBP"}},
                "currentTotalTaxSet": {"shopMoney": {"amount": "20.00", "currencyCode": "GBP"}}
            }
        }
    },
    "TC-04": {
        "id": "TC-04",
        "title": "Cart-Level Percentage Discount Code Stacking",
        "flaw": "Flaw 6: discountedUnitPriceSet excludes order-level discounts",
        "leak_type": "Formula Leak",
        "severity": "Critical",
        "v1_res": 66.22,
        "v1_breach": False,
        "v2_res": -13.78,
        "v2_breach": True,
        "v2_status": "EVALUATED_CONFIRMED",
        "delta": 80.00,
        "desc": "2 items at $100 each. COGS $60 each ($120 total). 40% cart code ($80 off). In Shopify, discountedUnitPriceSet remains $100!",
        "schema_driver": "LineItem.discountedUnitPriceSet excludes order discounts; must use discountAllocations",
        "takeaway": "V1 reports a fictitious profit of +$66.22 by completely ignoring the $80 coupon code, blinding the merchant to an actual cash loss of -$13.78.",
        "v1_math": {
            "gross_profit": "(100 - 60) + (100 - 60) = $80.00",
            "net_margin": "80.00 - 10.00 (Shipping) - 3.78 (Fee) = +$66.22",
            "breach": "False",
            "loss": "$0.00"
        },
        "v2_math": {
            "cash_in": "$120.00 (Allocated net: 60 + 60)",
            "cash_out": "120.00 (COGS) + 10.00 (Shipping) + 3.78 (Fee) = $133.78",
            "net_margin": "120.00 - 133.78 = -$13.78",
            "breach": "TRUE",
            "loss": "$13.78"
        },
        "json_payload": {
            "order": {
                "id": "gid://shopify/Order/8100000004",
                "currentCartDiscountAmountSet": {"shopMoney": {"amount": "80.00"}},
                "currentTotalPriceSet": {"shopMoney": {"amount": "120.00"}},
                "lineItems": [{"discountedUnitPriceSet": {"shopMoney": {"amount": "100.00"}}, "discountAllocations": [{"allocatedAmountSet": {"shopMoney": {"amount": "40.00"}}}]}]
            }
        }
    },
    "TC-05": {
        "id": "TC-05",
        "title": "3rd-Party Gateway (PayPal) with Empty fees Array",
        "flaw": "Flaw 5: Missing gateway cost defaults to $0.00",
        "leak_type": "Data Leak",
        "severity": "High",
        "v1_res": 12.00,
        "v1_breach": False,
        "v2_res": 4.53,
        "v2_breach": False,
        "v2_status": "EVALUATED_ESTIMATED",
        "delta": 7.47,
        "desc": "$200 order via PayPal Express. Real fee was $7.47. In Shopify GraphQL, OrderTransaction.fees is empty [] because it is only populated for Shopify Payments!",
        "schema_driver": "OrderTransaction.fees is only present for Shopify Payments",
        "takeaway": "V1 overstates net cash by $7.47 on every PayPal order because Shopify refuses to ingest third-party processor fees into the Order graph.",
        "v1_math": {
            "gross_profit": "200.00 - 170.00 = $30.00",
            "net_margin": "30.00 - 18.00 (Shipping) - $0.00 (Defaulted Fee) = +$12.00",
            "breach": "False",
            "loss": "$0.00"
        },
        "v2_math": {
            "cash_in": "$200.00",
            "cash_out": "170.00 (COGS) + 18.00 (Shipping) + 7.47 (Estimated PayPal Fee) = $195.47",
            "net_margin": "200.00 - 195.47 = +$4.53",
            "breach": "False (Estimated Flagged)",
            "loss": "$0.00"
        },
        "json_payload": {
            "order": {
                "id": "gid://shopify/Order/8100000005",
                "transactions": [{"gateway": "paypal", "manualPaymentGateway": False, "fees": []}]
            }
        }
    },
    "TC-06": {
        "id": "TC-06",
        "title": "Multi-Currency Order (JPY Presentment vs. USD Shop)",
        "flaw": "Flaw 7: No currency handling",
        "leak_type": "Formula Leak",
        "severity": "Critical",
        "v1_res": 14906.80,
        "v1_breach": False,
        "v2_res": 6.80,
        "v2_breach": False,
        "v2_status": "EVALUATED_CONFIRMED",
        "delta": 14900.00,
        "desc": "Customer paid ¥15,000 JPY ($100 USD). COGS is $75 USD. V1 naively reads the raw number without currency parsing: 15,000 - 75 = $14,925 profit!",
        "schema_driver": "Must bind strictly to shopMoney.amount, not presentmentMoney",
        "takeaway": "Without strict shopMoney anchoring, multi-currency orders generate absurd phantom profits (e.g. +$14,906.80 on a $100 order), wrecking store analytics.",
        "v1_math": {
            "gross_profit": "15,000.00 (JPY) - 75.00 (USD) = $14,925.00",
            "net_margin": "14,925.00 - 15.00 - 3.20 = +$14,906.80",
            "breach": "False (Corrupt scale)",
            "loss": "$0.00"
        },
        "v2_math": {
            "cash_in": "$100.00 USD (shopMoney)",
            "cash_out": "75.00 (COGS) + 15.00 (Shipping) + 3.20 (Fee) = $93.20",
            "net_margin": "100.00 - 93.20 = +$6.80",
            "breach": "False",
            "loss": "$0.00"
        },
        "json_payload": {
            "order": {
                "id": "gid://shopify/Order/8100000006",
                "currentTotalPriceSet": {"shopMoney": {"amount": "100.00", "currencyCode": "USD"}, "presentmentMoney": {"amount": "15000.00", "currencyCode": "JPY"}}
            }
        }
    },
    "TC-07": {
        "id": "TC-07",
        "title": "Stale Mutable COGS (Supplier Price Hike Post-Order)",
        "flaw": "Flaw 3: Uses current/live COGS regardless of order date",
        "leak_type": "Data Leak",
        "severity": "High",
        "v1_res": -8.04,
        "v1_breach": True,
        "v2_res": 19.96,
        "v2_breach": False,
        "v2_status": "EVALUATED_CONFIRMED",
        "delta": 28.00,
        "desc": "Order placed in June with COGS $30. In August, merchant updated InventoryItem.unitCost to $58. Audit runs in Sept. In GraphQL, unitCost is a mutable live pointer!",
        "schema_driver": "InventoryItem.unitCost is a live mutable pointer; no point-in-time snapshot on Order",
        "takeaway": "V1 falsely flags historically profitable orders as cash breaches whenever suppliers increase product catalog costs months later.",
        "v1_math": {
            "gross_profit": "60.00 - 58.00 (Current Live Cost) = $2.00",
            "net_margin": "2.00 - 8.00 (Shipping) - 2.04 (Fee) = -$8.04",
            "breach": "TRUE (False Alarm)",
            "loss": "$8.04"
        },
        "v2_math": {
            "cash_in": "$60.00",
            "cash_out": "30.00 (Historical Sidecar Cost) + 8.00 (Shipping) + 2.04 (Fee) = $40.04",
            "net_margin": "60.00 - 40.04 = +$19.96",
            "breach": "False",
            "loss": "$0.00"
        },
        "json_payload": {
            "order": {
                "id": "gid://shopify/Order/8100000007",
                "createdAt": "2026-06-01T10:00:00Z",
                "lineItems": [{"variant": {"inventoryItem": {"unitCost": {"amount": "58.00"}}}}]
            }
        }
    },
    "TC-08": {
        "id": "TC-08",
        "title": "Partial Return with Restocked Sellable Unit",
        "flaw": "Flaw 8: Returns modeled as boolean, not unit-level",
        "leak_type": "Formula Leak",
        "severity": "High",
        "v1_res": 1.80,
        "v1_breach": False,
        "v2_res": 41.80,
        "v2_breach": False,
        "v2_status": "EVALUATED_CONFIRMED",
        "delta": 40.00,
        "desc": "Customer bought 2 jackets at $100 (COGS $40 each). Customer returns 1 jacket. Merchant restocks it (restocked: true). V1 still charges all $80 COGS!",
        "schema_driver": "RefundLineItem.restocked and restockType: RETURN",
        "takeaway": "V1 severely understates retained margin ($1.80 vs. $41.80, a $40 discrepancy) because it treats restocked inventory as lost cash expense.",
        "v1_math": {
            "gross_profit": "100.00 - (2 x 40.00) = $20.00",
            "net_margin": "20.00 - 15.00 (Shipping) - 3.20 (Fee) = +$1.80",
            "breach": "False",
            "loss": "$0.00"
        },
        "v2_math": {
            "cash_in": "200.00 - 100.00 (Refund) = $100.00",
            "cash_out": "(1 x 40.00 Unrestocked) + 15.00 (Shipping) + 3.20 (Fee) = $58.20",
            "net_margin": "100.00 - 58.20 = +$41.80",
            "breach": "False",
            "loss": "$0.00"
        },
        "json_payload": {
            "order": {
                "id": "gid://shopify/Order/8100000008",
                "refunds": [{"refundLineItems": [{"quantity": 1, "restocked": True, "restockType": "RETURN"}]}]
            }
        }
    },
    "TC-09": {
        "id": "TC-09",
        "title": "Async Refund Race Condition (totalRefundedSet: 0.00)",
        "flaw": "New Leak: Async gateway refund settlement latency",
        "leak_type": "Data Leak",
        "severity": "Critical",
        "v1_res": 50.00,
        "v1_breach": False,
        "v2_res": -53.20,
        "v2_breach": True,
        "v2_status": "EVALUATED_ESTIMATED",
        "delta": 103.20,
        "desc": "Full refund initiated on $100 order via external gateway. Refund transaction is PENDING. GraphQL totalRefundedSet reports 0.00 until settled! Item damaged.",
        "schema_driver": "Refund.totalRefundedSet is 0.00 while transaction status is PENDING",
        "takeaway": "Evaluating orders immediately upon refund webhooks before gateway settlement tells merchants an order made +$50.00 when it actually lost -$53.20.",
        "v1_math": {
            "gross_profit": "100.00 - 40.00 = $60.00",
            "net_margin": "60.00 - 10.00 - 0.00 = +$50.00",
            "breach": "False (Severe False Negative)",
            "loss": "$0.00"
        },
        "v2_math": {
            "cash_in": "100.00 - 100.00 (Pending Refund) = $0.00",
            "cash_out": "40.00 (Scrapped COGS) + 10.00 (Shipping) + 3.20 (Retained Fee) = $53.20",
            "net_margin": "0.00 - 53.20 = -$53.20",
            "breach": "TRUE",
            "loss": "$53.20"
        },
        "json_payload": {
            "order": {
                "id": "gid://shopify/Order/8100000009",
                "transactions": [{"kind": "REFUND", "status": "PENDING", "amountSet": {"shopMoney": {"amount": "100.00"}}}],
                "refunds": [{"totalRefundedSet": {"shopMoney": {"amount": "0.00"}}}]
            }
        }
    },
    "TC-10": {
        "id": "TC-10",
        "title": "Missing/NULL unitCost on Promo SKU",
        "flaw": "Flaw 4: Missing COGS defaults to non-breach",
        "leak_type": "Formula Leak",
        "severity": "Critical",
        "v1_res": 65.38,
        "v1_breach": False,
        "v2_res": None,
        "v2_breach": False,
        "v2_status": "NOT_EVALUABLE",
        "delta": 65.38,
        "desc": "New launch item sold for $80. Cost per item field was left blank (null). V1 defaults missing COGS to $0.00, generating phantom 100% margin!",
        "schema_driver": "InventoryItem.unitCost is null; V2 triggers NOT_EVALUABLE gate",
        "takeaway": "V1 manufactures a fictitious +$65.38 profit out of thin air when catalog costs are missing, while V2 quarantines the order so merchants know reporting has missing data.",
        "v1_math": {
            "gross_profit": "80.00 - 0.00 (Defaulted) = $80.00",
            "net_margin": "80.00 - 12.00 (Shipping) - 2.62 (Fee) = +$65.38",
            "breach": "False",
            "loss": "$0.00"
        },
        "v2_math": {
            "cash_in": "Evaluability Gate: unitCost is NULL",
            "cash_out": "Quarantined / Excluded from denominator",
            "net_margin": "NOT_EVALUABLE",
            "breach": "EXCLUDED",
            "loss": "$0.00"
        },
        "json_payload": {
            "order": {
                "id": "gid://shopify/Order/8100000010",
                "lineItems": [{"variant": {"inventoryItem": {"unitCost": None}}}]
            }
        }
    },
    "TC-11": {
        "id": "TC-11",
        "title": "$0 Influencer Gift / Sample Order with Real COGS",
        "flaw": "Flaw 9: No order_type concept for gifts/samples",
        "leak_type": "Data & Formula",
        "severity": "Medium",
        "v1_res": -114.00,
        "v1_breach": True,
        "v2_res": 0.00,
        "v2_breach": False,
        "v2_status": "EXCLUDED_MARKETING",
        "delta": 114.00,
        "desc": "Marketing team created $0 draft order for influencer (tags: ['influencer_sample']). COGS $90, shipping $24. V1 flags this as commercial breach!",
        "schema_driver": "Shopify lacks native order_type enum; inferred via tags and manual gateway",
        "takeaway": "V1 panics leadership by reporting intentional marketing gifting as commercial cash-bleeding failures, polluting core retail margin analytics.",
        "v1_math": {
            "gross_profit": "0.00 - 90.00 = -$90.00",
            "net_margin": "-90.00 - 24.00 - 0.00 = -$114.00",
            "breach": "TRUE (Pollutes commercial score)",
            "loss": "$114.00"
        },
        "v2_math": {
            "cash_in": "$0.00 (Tagged influencer_sample)",
            "cash_out": "Segregated to Marketing CAC Ledger",
            "net_margin": "EXCLUDED_PROMOTIONAL",
            "breach": "EXCLUDED",
            "loss": "$0.00"
        },
        "json_payload": {
            "order": {
                "id": "gid://shopify/Order/8100000011",
                "tags": ["influencer_sample", "pr_gifting"],
                "currentTotalPriceSet": {"shopMoney": {"amount": "0.00"}}
            }
        }
    },
    "TC-12": {
        "id": "TC-12",
        "title": "External Shipping Label via 3PL (ShipStation)",
        "flaw": "Flaw 5: Missing shipping cost defaults to $0.00",
        "leak_type": "Data Leak",
        "severity": "High",
        "v1_res": 6.83,
        "v1_breach": False,
        "v2_res": -1.67,
        "v2_breach": True,
        "v2_status": "EVALUATED_ESTIMATED",
        "delta": 8.50,
        "desc": "$30 order with $22 COGS. Merchant ships via ShipStation ($8.50 label cost). In Shopify GraphQL, carrier shipping cost is completely missing!",
        "schema_driver": "Carrier label costs from 3PLs are NOT stored in Shopify GraphQL Order graph",
        "takeaway": "V1 reports a comfortable +$6.83 profit on an order that actually lost -$1.67 in cash, because it assumed shipping packages across the country was completely free.",
        "v1_math": {
            "gross_profit": "30.00 - 22.00 = $8.00",
            "net_margin": "8.00 - $0.00 (Defaulted) - 1.17 (Fee) = +$6.83",
            "breach": "False",
            "loss": "$0.00"
        },
        "v2_math": {
            "cash_in": "$30.00",
            "cash_out": "22.00 (COGS) + 8.50 (Estimated Courier) + 1.17 (Fee) = $31.67",
            "net_margin": "30.00 - 31.67 = -$1.67",
            "breach": "TRUE",
            "loss": "$1.67"
        },
        "json_payload": {
            "order": {
                "id": "gid://shopify/Order/8100000012",
                "currentTotalPriceSet": {"shopMoney": {"amount": "30.00"}},
                "fulfillment": "FulfillmentOrder (External 3PL - No Label Cost in Graph)"
            }
        }
    }
}

# ---------------------------------------------------------
# DATA DEFINITIONS: F01 TOP 20 LEAKING ORDERS
# ---------------------------------------------------------

F01_TOP_LEAKS = [
    {"order_id": "#5000005230", "sku": "SKU-1012", "orig_price": 91.71, "net_price": 36.68, "cogs": 33.95, "cogs_src": "inventory_item", "target_margin": 0.62, "margin_src": "taxonomy", "target_profit": 2492.65, "actual_profit": -404.62, "loss": 2897.27, "confidence": "real"},
    {"order_id": "#5000001005", "sku": "SKU-1135", "orig_price": 127.14, "net_price": 50.86, "cogs": 59.50, "cogs_src": "inventory_item", "target_margin": 0.52, "margin_src": "taxonomy", "target_profit": 2247.84, "actual_profit": -293.90, "loss": 2541.74, "confidence": "real"},
    {"order_id": "#5000012840", "sku": "SKU-1393", "orig_price": 196.44, "net_price": 78.58, "cogs": 118.77, "cogs_src": "inventory_item", "target_margin": 0.38, "margin_src": "taxonomy", "target_profit": 1642.24, "actual_profit": -884.27, "loss": 2526.51, "confidence": "real"},
    {"order_id": "#5000023688", "sku": "SKU-1356", "orig_price": 428.79, "net_price": 0.00, "cogs": 351.62, "cogs_src": "inventory_item", "target_margin": 0.18, "margin_src": "taxonomy", "target_profit": 231.55, "actual_profit": -1054.86, "loss": 1286.41, "confidence": "real"},
    {"order_id": "#5000003888", "sku": "SKU-1516", "orig_price": 324.59, "net_price": 0.00, "cogs": 256.93, "cogs_src": "inventory_item", "target_margin": 0.18, "margin_src": "taxonomy", "target_profit": 399.50, "actual_profit": -667.39, "loss": 1066.89, "confidence": "real"},
    {"order_id": "#5000009688", "sku": "SKU-1366", "orig_price": 418.95, "net_price": 0.00, "cogs": 335.53, "cogs_src": "inventory_item", "target_margin": 0.18, "margin_src": "taxonomy", "target_profit": 291.75, "actual_profit": -580.62, "loss": 872.37, "confidence": "real"},
    {"order_id": "#5000045488", "sku": "SKU-1043", "orig_price": 199.56, "net_price": 0.00, "cogs": 123.84, "cogs_src": "inventory_item", "target_margin": 0.43, "margin_src": "metafield", "target_profit": 636.07, "actual_profit": -228.29, "loss": 864.36, "confidence": "real"},
    {"order_id": "#5000018288", "sku": "SKU-1106", "orig_price": 248.35, "net_price": 0.00, "cogs": 202.50, "cogs_src": "inventory_item", "target_margin": 0.18, "margin_src": "taxonomy", "target_profit": 396.80, "actual_profit": -427.34, "loss": 824.14, "confidence": "real"},
    {"order_id": "#5000015288", "sku": "SKU-1056", "orig_price": 265.22, "net_price": 0.00, "cogs": 212.37, "cogs_src": "inventory_item", "target_margin": 0.18, "margin_src": "taxonomy", "target_profit": 143.22, "actual_profit": -637.11, "loss": 780.33, "confidence": "real"},
    {"order_id": "#5000031688", "sku": "SKU-1086", "orig_price": 254.89, "net_price": 0.00, "cogs": 213.36, "cogs_src": "inventory_item", "target_margin": 0.18, "margin_src": "taxonomy", "target_profit": 137.64, "actual_profit": -640.08, "loss": 777.72, "confidence": "real"},
    {"order_id": "#5000015088", "sku": "SKU-1286", "orig_price": 351.50, "net_price": 0.00, "cogs": 298.05, "cogs_src": "inventory_item", "target_margin": 0.18, "margin_src": "taxonomy", "target_profit": 126.54, "actual_profit": -596.10, "loss": 722.64, "confidence": "real"},
    {"order_id": "#5000009831", "sku": "SKU-1161", "orig_price": 379.99, "net_price": 303.99, "cogs": 311.59, "cogs_src": "category_estimate", "target_margin": 0.18, "margin_src": "taxonomy", "target_profit": 638.28, "actual_profit": -70.92, "loss": 709.20, "confidence": "estimated"},
    {"order_id": "#5000022131", "sku": "SKU-1041", "orig_price": 296.30, "net_price": 237.04, "cogs": 242.97, "cogs_src": "category_estimate", "target_margin": 0.18, "margin_src": "taxonomy", "target_profit": 637.44, "actual_profit": -70.85, "loss": 708.29, "confidence": "estimated"},
    {"order_id": "#5000038032", "sku": "SKU-1561", "orig_price": 382.82, "net_price": 287.12, "cogs": 313.91, "cogs_src": "category_estimate", "target_margin": 0.18, "margin_src": "taxonomy", "target_profit": 698.49, "actual_profit": 3.15, "loss": 695.34, "confidence": "estimated"},
    {"order_id": "#5000029688", "sku": "SKU-1236", "orig_price": 233.84, "net_price": 0.00, "cogs": 187.64, "cogs_src": "inventory_item", "target_margin": 0.18, "margin_src": "taxonomy", "target_profit": 126.27, "actual_profit": -562.92, "loss": 689.19, "confidence": "real"},
    {"order_id": "#5000048088", "sku": "SKU-1546", "orig_price": 387.76, "net_price": 0.00, "cogs": 308.50, "cogs_src": "inventory_item", "target_margin": 0.18, "margin_src": "taxonomy", "target_profit": 532.30, "actual_profit": -150.90, "loss": 683.20, "confidence": "real"},
    {"order_id": "#5000008847", "sku": "SKU-1118", "orig_price": 180.25, "net_price": 135.19, "cogs": 109.01, "cogs_src": "historical", "target_margin": 0.38, "margin_src": "taxonomy", "target_profit": 624.95, "actual_profit": -57.36, "loss": 682.31, "confidence": "estimated"},
    {"order_id": "#5000019488", "sku": "SKU-1178", "orig_price": 193.26, "net_price": 0.00, "cogs": 117.10, "cogs_src": "inventory_item", "target_margin": 0.38, "margin_src": "taxonomy", "target_profit": 327.92, "actual_profit": -346.40, "loss": 674.32, "confidence": "real"},
    {"order_id": "#5000033132", "sku": "SKU-1361", "orig_price": 389.30, "net_price": 291.98, "cogs": 319.23, "cogs_src": "category_estimate", "target_margin": 0.18, "margin_src": "taxonomy", "target_profit": 481.32, "actual_profit": -166.22, "loss": 647.54, "confidence": "estimated"},
    {"order_id": "#5000036288", "sku": "SKU-1343", "orig_price": 126.89, "net_price": 0.00, "cogs": 77.08, "cogs_src": "inventory_item", "target_margin": 0.43, "margin_src": "metafield", "target_profit": 684.75, "actual_profit": 46.88, "loss": 637.87, "confidence": "real"}
]

# ---------------------------------------------------------
# HEADER & NAVIGATION
# ---------------------------------------------------------

st.title("⚡ E-Commerce Margin & Leakage Scoring Engine")
st.caption("Production QA Audit & Side-by-Side Validation: **Formula F01 (Discount Leakage)** & **Formula F03 (Margin Floor Breach)**")

tab_f01, tab_f03, tab_sandbox = st.tabs([
    "📉 Formula F01 — Promotional Margin Leakage",
    "🎯 Formula F03 — Margin Floor Breach (V1 vs V2)",
    "🧪 Live Interactive Order Simulator"
])

# =========================================================
# TAB 1: FORMULA F03 (MARGIN FLOOR BREACH)
# =========================================================

with tab_f03:
    st.markdown("### Formula F03: Margin Floor Breach Validation")
    st.markdown("""
    Measures whether a completed order generated positive direct cash contribution:
    *Did the merchant collect more physical cash than they paid out in direct COGS, real courier outbound shipping, and non-refundable payment processor fees?*
    """)
    
    # KPI Grid
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown("""
        <div class="metric-card">
            <div class="metric-title">Test Vectors Evaluated</div>
            <div class="metric-val">12 Scenarios</div>
            <div class="metric-sub">TC-01 to TC-12 Comprehensive</div>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown("""
        <div class="metric-card">
            <div class="metric-title">Formula Leaks Isolated</div>
            <div class="metric-val" style="color: #f87171;">6 Leaks</div>
            <div class="metric-sub">V1 Flawed Assumptions Caught</div>
        </div>
        """, unsafe_allow_html=True)
    with col3:
        st.markdown("""
        <div class="metric-card">
            <div class="metric-title">Data Leaks Isolated</div>
            <div class="metric-val" style="color: #fb923c;">5 Leaks</div>
            <div class="metric-sub">Shopify GraphQL Missing Fields</div>
        </div>
        """, unsafe_allow_html=True)
    with col4:
        st.markdown("""
        <div class="metric-card">
            <div class="metric-title">Max Order Error Prevented</div>
            <div class="metric-val" style="color: #38bdf8;">$14,900.00</div>
            <div class="metric-sub">TC-06 Multi-Currency Phantom Profit</div>
        </div>
        """, unsafe_allow_html=True)
        
    st.markdown("---")
    
    # Scenario Selection & Deep Dive Inspector
    st.markdown("### 🔍 Scenario Deep-Dive Inspector")
    
    selected_tc = st.selectbox(
        "Select a Test Vector Scenario to Inspect:",
        options=list(SCENARIOS.keys()),
        format_func=lambda x: f"{x}: {SCENARIOS[x]['title']} [{SCENARIOS[x]['leak_type']}]"
    )
    
    sc = SCENARIOS[selected_tc]
    
    # Scenario Summary Card
    st.markdown(f"""
    <div class="callout-box">
        <h4 style="margin: 0 0 8px 0; color: #f8fafc;">{sc['id']} — {sc['title']}</h4>
        <p style="margin: 0; color: #cbd5e1; font-size: 0.95rem;">{sc['desc']}</p>
        <div style="margin-top: 10px;">
            <span class="badge-{'critical' if sc['severity']=='Critical' else 'high' if sc['severity']=='High' else 'medium' if sc['severity']=='Medium' else 'healthy'}">Severity: {sc['severity']}</span>
            <span class="badge-high" style="margin-left: 8px;">{sc['leak_type']}</span>
            <span style="margin-left: 12px; font-size: 0.85rem; color: #94a3b8;">Driver: <code>{sc['schema_driver']}</code></span>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Side-by-side Math Walkthrough
    col_v1, col_v2 = st.columns(2)
    
    with col_v1:
        st.markdown("#### ❌ Formula V1 (Flawed Spec)")
        st.markdown(f"""
        * **Gross Profit:** `{sc['v1_math']['gross_profit']}`
        * **Net Margin Cash:** `{sc['v1_math']['net_margin']}`
        * **F03 Breach Detected:** **{sc['v1_math']['breach']}**
        * **F03 Dollar Loss:** `{sc['v1_math']['loss']}`
        """)
        st.error(f"V1 Stated Contribution: **{f'${sc['v1_res']:,.2f}' if sc['v1_res'] is not None else 'NULL'}**")
        
    with col_v2:
        st.markdown("#### ✅ Formula V2 (Production Rebuild)")
        st.markdown(f"""
        * **Cash In:** `{sc['v2_math']['cash_in']}`
        * **Cash Out:** `{sc['v2_math']['cash_out']}`
        * **Net Margin Cash:** `{sc['v2_math']['net_margin']}`
        * **Evaluability Status:** `[{sc['v2_status']}]`
        * **F03 Breach Detected:** **{sc['v2_math']['breach']}**
        """)
        st.success(f"V2 Realized Contribution: **{f'${sc['v2_res']:,.2f}' if sc['v2_res'] is not None else 'NOT EVALUABLE'}** (Discrepancy: **${sc['delta']:,.2f}**)")
        
    # Merchant Impact Alert
    st.info(f"💡 **Merchant-Facing Takeaway:** {sc['takeaway']}")
    
    # Plotly Comparison & GraphQL JSON Inspection
    exp_col1, exp_col2 = st.columns([3, 2])
    
    with exp_col1:
        st.markdown("##### 📊 Contribution Cash Flow Comparison")
        v1_val = sc['v1_res'] if sc['v1_res'] is not None else 0
        v2_val = sc['v2_res'] if sc['v2_res'] is not None else 0
        
        fig = go.Figure(data=[
            go.Bar(name='Formula V1 (Flawed)', x=['Reported Net Cash'], y=[v1_val], marker_color='#f87171'),
            go.Bar(name='Formula V2 (Rebuilt)', x=['Reported Net Cash'], y=[v2_val], marker_color='#38bdf8')
        ])
        fig.update_layout(
            barmode='group',
            height=280,
            margin=dict(l=20, r=20, t=30, b=20),
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font=dict(color='#cbd5e1'),
            yaxis=dict(gridcolor='rgba(255,255,255,0.08)', title="Net Margin Cash ($)")
        )
        st.plotly_chart(fig, use_container_width=True)
        
    with exp_col2:
        st.markdown("##### 📦 Synthetic Shopify GraphQL Payload")
        st.json(sc['json_payload'], expanded=True)
        
    st.markdown("---")
    
    # Full Comparison Matrix Table
    st.markdown("### 📋 Complete 12-Scenario Comparison Matrix")
    
    table_data = []
    for k, v in SCENARIOS.items():
        v1_str = f"${v['v1_res']:,.2f}" if v['v1_res'] is not None else "NULL"
        v2_str = f"${v['v2_res']:,.2f}" if v['v2_res'] is not None else "EXCLUDED"
        table_data.append({
            "Scenario": f"{v['id']}: {v['title']}",
            "V1 Net Cash": v1_str,
            "V1 Breach": "🔴 BREACH" if v['v1_breach'] else "🟢 OK",
            "V2 Net Cash": v2_str,
            "V2 Breach": "🔴 BREACH" if v['v2_breach'] else "🟢 OK",
            "Discrepancy ($)": f"${v['delta']:,.2f}",
            "Leak Type": v['leak_type'],
            "Severity": v['severity']
        })
        
    df_matrix = pd.DataFrame(table_data)
    st.dataframe(df_matrix, use_container_width=True, hide_index=True)


# =========================================================
# TAB 1: FORMULA F01 (PROMOTIONAL MARGIN LEAKAGE ENGINE)
# =========================================================

with tab_f01:
    from f01_dashboard import render_f01_tab
    render_f01_tab()


# =========================================================
# TAB 3: LIVE INTERACTIVE ORDER SIMULATOR
# =========================================================

with tab_sandbox:
    st.markdown("### 🧪 Live Interactive Order Simulator (Reactive F01 & F03 Engine)")
    st.markdown("""
    Test any order configuration in real time. This simulator calls the canonical scoring engines to evaluate 
    **Formula F01 (Promotional Margin Leakage)** and compares it directly against **Formula F03 (Margin Floor Breach)**.
    
    *Strict Architectural Principle:* Every parameter is explicitly tagged to demonstrate **which parameters calculate the F01 score** 
    and which belong strictly to F03 operational fulfillment boundaries.
    """)
    
    # Input Parameter Grid
    s_col1, s_col2, s_col3, s_col4 = st.columns(4)
    
    with s_col1:
        st.markdown("##### 🛒 1. Pricing & Baseline")
        st.caption("🟢 Used by F01 & 🔵 F03")
        sim_msrp = st.number_input("Unit Baseline MSRP ($):", min_value=0.0, value=100.0, step=5.0, 
                                   help="🟢 F01: Establishes Baseline Revenue = MSRP × Active Qty.")
        sim_selling_price = st.number_input("Unit Selling Price ($):", min_value=0.0, value=100.0, step=5.0,
                                            help="🟢 F01: Used to identify compare-at markdowns if MSRP > price.")
        sim_units_ordered = st.number_input("Units Purchased (Quantity):", min_value=1, value=2, step=1,
                                            help="🟢 F01: Original quantity ordered by customer.")
        sim_units_restocked = st.number_input("Units Returned / Restocked:", min_value=0, max_value=int(sim_units_ordered), value=0, step=1,
                                              help="🟢 F01: Calculates Active Qty = Ordered - Returned. Returned units receive $0 COGS and $0 revenue.")
        active_units = max(0, sim_units_ordered - sim_units_restocked)
        st.info(f"Active Quantity: **{active_units} unit(s)**")

    with s_col2:
        st.markdown("##### 🏷️ 2. Discounts & Refunds")
        st.caption("🟢 Used by F01 & 🔵 F03")
        sim_line_disc = st.number_input("Line Markdown ($ / unit):", min_value=0.0, value=10.0, step=2.5,
                                        help="🟢 F01: Product-level discount deducted directly from unit price.")
        sim_cart_disc = st.number_input("Cart Discount Allocation ($ total):", min_value=0.0, value=15.0, step=2.5,
                                        help="🟢 F01: Prorated order-level coupon share. Reconciled to prevent double counting.")
        sim_discount_code = st.text_input("Discount Code Applied:", value="SAVE25",
                                          help="🟢 F01: Attribution tracking code for promotional audit.")
        sim_cash_refund = st.number_input("Post-Purchase Cash Refund ($):", min_value=0.0, value=0.0, step=5.0,
                                          help="🟢 F01: Cash refund reduces net revenue collected on active units.")

    with s_col3:
        st.markdown("##### 📦 3. COGS & Target Margin")
        st.caption("🟢 Used by F01")
        sim_cogs = st.number_input("Unit Baseline COGS ($):", min_value=0.0, value=35.0, step=5.0,
                                   help="🟢 F01: Unit product cost. Multiplied by Active Qty to obtain Total COGS.")
        sim_cogs_src = st.selectbox(
            "COGS Resolution Tier:",
            [
                "Direct Catalog (InventoryItem) [Tier 1]",
                "Historical PO Cost (Tier 2)",
                "Category Imputation (Tier 3)",
                "Storewide Fallback (Tier 4)",
                "Unresolved Missing COGS (Quarantine)"
            ],
            help="🟢 F01: Evidentiary confidence tier. Unresolved COGS safely routes order to quarantine."
        )
        target_src_options = [
            "SKU Metafield (Tier 1)",
            "Product-Specific Margin (Tier 2)",
            "Category Taxonomy (Tier 3)",
            "Product Type (Tier 4)",
            "90-Day Historical Margin (Tier 5)",
            "Storewide Default Fallback 35% (Tier 6)"
        ]
        sim_target_src = st.selectbox(
            "Target Margin Source:",
            target_src_options,
            help="🟢 F01: Determines where the required gross margin floor originates in the canonical 6-tier hierarchy."
        )
        if "Tier 1" in sim_target_src:
            tier_default = 48.0
        elif "Tier 2" in sim_target_src:
            tier_default = 50.0
        elif "Tier 3" in sim_target_src:
            tier_default = 52.0
        elif "Tier 4" in sim_target_src:
            tier_default = 45.0
        elif "Tier 5" in sim_target_src:
            tier_default = 47.32
        else:
            tier_default = 35.0

        sim_target_margin = st.slider(
            "Target Margin Floor (%):",
            min_value=0.0,
            max_value=90.0,
            value=float(tier_default),
            step=0.5,
            key=f"target_margin_slider_{sim_target_src[:6]}",
            help="🟢 F01: Required gross margin percentage floor. Target Profit = Baseline Revenue × Target Margin %."
        )

    with s_col4:
        st.markdown("##### 🚚 4. Operational Costs")
        st.caption("🔵 F03 ONLY — ❌ NOT Used by F01")
        sim_cust_shipping = st.number_input("Shipping Charged to Buyer ($):", min_value=0.0, value=0.0, step=2.0,
                                            help="🔵 F03 ONLY: Customer shipping revenue collected. Strictly NOT used in F01 gross margin.")
        sim_carrier_cost = st.number_input("Outbound Courier Label Cost ($):", min_value=0.0, value=12.0, step=2.0,
                                           help="🔵 F03 ONLY: Physical carrier label expense. Strictly NOT used in F01 gross margin.")
        sim_gateway = st.selectbox(
            "Payment Processing Gateway:",
            ["Shopify Payments", "PayPal Express (3rd Party)", "Manual / Wire"],
            help="🔵 F03 ONLY: Gateway processing fee. Strictly NOT used in F01 gross margin."
        )
        sim_taxes_incl = st.checkbox("Taxes Included in Price (VAT)", value=False,
                                     help="🔵 F03 ONLY: VAT tax liability deducted from merchant revenue in F03.")
        sim_vat_pct = st.slider("VAT / Tax Rate (%)", min_value=0, max_value=30, value=20) if sim_taxes_incl else 0

    # -------------------------------------------------------------------------
    # CANONICAL ENGINE COMPUTATION: FORMULA F01
    # -------------------------------------------------------------------------
    is_quarantined_cogs = ("Quarantine" in sim_cogs_src)
    is_direct_cogs = ("Direct Catalog" in sim_cogs_src)
    is_hist_cogs = ("Historical PO Cost" in sim_cogs_src)
    is_cat_impute_cogs = ("Category Imputation" in sim_cogs_src)
    is_storewide_cogs = ("Storewide Fallback" in sim_cogs_src)

    if is_direct_cogs:
        variant_inv_item = {"cost": str(sim_cogs)}
        hist_cogs_fn = None
        force_unres_cogs = False
        true_catalog_cost = sim_cogs
    elif is_hist_cogs:
        variant_inv_item = {}
        hist_cogs_fn = lambda vid, dt: float(sim_cogs)
        force_unres_cogs = False
        true_catalog_cost = 0.0
    elif is_cat_impute_cogs:
        variant_inv_item = {}
        hist_cogs_fn = None
        force_unres_cogs = False
        true_catalog_cost = 0.0
    elif is_storewide_cogs:
        variant_inv_item = {}
        hist_cogs_fn = None
        force_unres_cogs = False
        true_catalog_cost = 0.0
    else:  # Quarantine
        variant_inv_item = {}
        hist_cogs_fn = None
        force_unres_cogs = True
        true_catalog_cost = 0.0

    # Configure Target Margin 6-Tier Cascade
    metafield_sim = None
    product_margin_sim = None
    cat_table_sim = None
    pt_table_sim = None
    hist_margin_fn_sim = None
    cat_name = "Apparel & Accessories > Clothing"
    pt_name = "Apparel"

    if "Tier 1" in sim_target_src:
        metafield_sim = sim_target_margin / 100.0
        cat_table_sim = {"Apparel & Accessories > Clothing": 0.52}
        pt_table_sim = {"Apparel": 0.45}
    elif "Tier 2" in sim_target_src:
        product_margin_sim = {3001: sim_target_margin / 100.0, "3001": sim_target_margin / 100.0}
        cat_table_sim = {"Apparel & Accessories > Clothing": 0.52}
        pt_table_sim = {"Apparel": 0.45}
    elif "Tier 3" in sim_target_src:
        cat_table_sim = {"Apparel & Accessories > Clothing": sim_target_margin / 100.0}
        pt_table_sim = {"Apparel": 0.45}
    elif "Tier 4" in sim_target_src:
        cat_table_sim = {}  # Empty dict prevents Category Taxonomy from shadowing Product Type
        pt_table_sim = {"Apparel": sim_target_margin / 100.0}
    elif "Tier 5" in sim_target_src:
        cat_table_sim = {}
        pt_table_sim = {}
        hist_margin_fn_sim = lambda vid, dt: sim_target_margin / 100.0
    elif "Tier 6" in sim_target_src:
        cat_table_sim = {}
        pt_table_sim = {}
        hist_margin_fn_sim = None

    if is_cat_impute_cogs and (cat_table_sim is not None and not cat_table_sim):
        cat_table_sim = {"Apparel & Accessories > Clothing": sim_target_margin / 100.0}
    elif is_storewide_cogs:
        cat_table_sim = {}

    sim_order_payload = {
        "id": 9999999999,
        "name": "#SIM-001",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "financial_status": "paid" if sim_cash_refund == 0.0 else "partially_refunded",
        "cancelled_at": None,
        "total_discounts": str(round(sim_line_disc * active_units + sim_cart_disc, 2)),
        "refunds": [{
            "id": 991,
            "refund_line_items": [],
            "transactions": [{"amount": str(sim_cash_refund), "kind": "refund", "status": "success"}]
        }] if sim_cash_refund > 0.0 else [],
        "line_items": [{
            "id": 1001,
            "variant_id": 2001,
            "product_id": 3001,
            "sku": "SKU-SIM-101",
            "original_unit_price": str(sim_msrp),
            "price": str(sim_selling_price),
            "quantity": int(sim_units_ordered),
            "current_quantity": int(active_units),
            "total_discount": str(round(sim_line_disc * active_units, 2)),
            "discount_allocations": [{"amount": str(sim_cart_disc), "code": sim_discount_code}] if sim_cart_disc > 0 else []
        }],
        "_variants": [{
            "id": 2001,
            "product_id": 3001,
            "price": str(sim_msrp),
            "compare_at_price": str(sim_msrp),
            "inventory_item": variant_inv_item
        }]
    }

    catalog_sim = {
        2001: {
            "product_type": pt_name,
            "category": cat_name,
            "true_cogs": true_catalog_cost,
            "original_price": sim_msrp,
            "metafield_margin": metafield_sim
        }
    }

    # Call canonical F01 evaluation engine live!
    f01_res = evaluate_order(
        order=sim_order_payload,
        catalog_by_variant_id=catalog_sim,
        product_margin_table=product_margin_sim,
        category_margin_table=cat_table_sim,
        product_type_margin_table=pt_table_sim,
        historical_lookup_fn=hist_cogs_fn,
        historical_margin_fn=hist_margin_fn_sim,
        force_unresolved_cogs=force_unres_cogs,
        skip_cohort_filter=True
    )

    # -------------------------------------------------------------------------
    # PARAMETER AUDIT CHECKLIST: WHICH PARAMETERS CALCULATE F01?
    # -------------------------------------------------------------------------
    st.markdown("---")
    st.markdown("#### 📋 Parameter Audit Matrix: Which Parameters Calculate the F01 Score?")
    st.caption("Demonstrates the exact mathematical role of each parameter and cleanly separates F01 product margin from F03 operational cash.")

    resolved_target_pct = (f01_res.line_items[0].target_margin_used * 100.0) if f01_res.line_items else sim_target_margin
    resolved_target_tier = f01_res.line_items[0].target_margin_source if f01_res.line_items else sim_target_src
    resolved_cogs_tier = f01_res.line_items[0].cogs_source if f01_res.line_items else sim_cogs_src

    audit_records = [
        {"Parameter": "Unit Baseline MSRP", "Configured Value": f"${sim_msrp:,.2f}", "Used in F01?": "🟢 YES", "Used in F03?": "🔵 YES", "Mathematical Role in Formula F01": "Defines Baseline Revenue floor = MSRP × Active Qty ($" + f"{f01_res.total_original_value:,.2f}" + ")"},
        {"Parameter": "Unit Selling Price", "Configured Value": f"${sim_selling_price:,.2f}", "Used in F01?": "🟢 YES", "Used in F03?": "🔵 YES", "Mathematical Role in Formula F01": "Identifies product markdowns when selling price < MSRP"},
        {"Parameter": "Units Purchased & Restocked", "Configured Value": f"{sim_units_ordered} purchased, {sim_units_restocked} returned", "Used in F01?": "🟢 YES", "Used in F03?": "🔵 YES", "Mathematical Role in Formula F01": f"Sets Active Qty = {active_units}. Returned units receive $0 revenue and $0 COGS"},
        {"Parameter": "Line-Level Markdown", "Configured Value": f"${sim_line_disc:,.2f} / unit", "Used in F01?": "🟢 YES", "Used in F03?": "🔵 YES", "Mathematical Role in Formula F01": "Product discount deducted from MSRP"},
        {"Parameter": "Cart / Coupon Allocation", "Configured Value": f"${sim_cart_disc:,.2f} total", "Used in F01?": "🟢 YES", "Used in F03?": "🔵 YES", "Mathematical Role in Formula F01": "Order-level discount allocation; checked to prevent double counting"},
        {"Parameter": "Post-Purchase Cash Refund", "Configured Value": f"${sim_cash_refund:,.2f}", "Used in F01?": "🟢 YES", "Used in F03?": "🔵 YES", "Mathematical Role in Formula F01": "Deducted from active revenue to obtain Net Revenue ($" + f"{f01_res.total_net_revenue:,.2f}" + ")"},
        {"Parameter": "Unit Baseline COGS", "Configured Value": f"${sim_cogs:,.2f}", "Used in F01?": "🟢 YES", "Used in F03?": "🔵 YES", "Mathematical Role in Formula F01": "Active COGS ($" + f"{f01_res.total_cogs:,.2f}" + ") subtracted from Net Revenue to get Actual GP"},
        {"Parameter": "COGS Source Tier", "Configured Value": f"{sim_cogs_src} -> Resolved: {resolved_cogs_tier}", "Used in F01?": "🟢 YES", "Used in F03?": "🔵 YES", "Mathematical Role in Formula F01": "Determines confidence tier. Unresolved COGS triggers quarantine gate"},
        {"Parameter": "Target Margin % & Source", "Configured Value": f"{resolved_target_pct:.1f}% (Resolved Tier: {resolved_target_tier})", "Used in F01?": "🟢 YES", "Used in F03?": "❌ NO", "Mathematical Role in Formula F01": "Multiplied by Baseline Revenue to define Target Profit ($" + f"{f01_res.target_minimum_profit:,.2f}" + ")"},
        {"Parameter": "Customer-Paid Shipping", "Configured Value": f"${sim_cust_shipping:,.2f}", "Used in F01?": "❌ NO", "Used in F03?": "🔵 YES", "Mathematical Role in Formula F01": "NOT USED BY F01. Shipping revenue belongs strictly to F03 cash floor"},
        {"Parameter": "Courier Shipping Label Cost", "Configured Value": f"${sim_carrier_cost:,.2f}", "Used in F01?": "❌ NO", "Used in F03?": "🔵 YES", "Mathematical Role in Formula F01": "NOT USED BY F01. Outbound delivery expense belongs to F03"},
        {"Parameter": "Payment Gateway Fee", "Configured Value": sim_gateway, "Used in F01?": "❌ NO", "Used in F03?": "🔵 YES", "Mathematical Role in Formula F01": "NOT USED BY F01. Transaction processing cost belongs to F03"},
        {"Parameter": "Taxes Included (VAT)", "Configured Value": f"{sim_vat_pct}%" if sim_taxes_incl else "None / Exempt", "Used in F01?": "❌ NO", "Used in F03?": "🔵 YES", "Mathematical Role in Formula F01": "NOT USED BY F01. Remittable tax liability belongs to F03"}
    ]

    st.dataframe(pd.DataFrame(audit_records), use_container_width=True, hide_index=True)

    # -------------------------------------------------------------------------
    # LIVE SIMULATION RESULTS: FORMULA F01
    # -------------------------------------------------------------------------
    st.markdown("---")
    st.markdown("#### 📉 Formula F01 Results: Promotional Gross Margin Leakage")

    is_leaking = (f01_res.f01_dollar_loss > 0.0)
    is_quarantined = (f01_res.status == "quarantined")
    if is_quarantined:
        status_color = "#fb923c"
        status_text = "QUARANTINED (EVIDENTIARY COGS DEFICIT)"
    elif is_leaking:
        status_color = "#f87171"
        status_text = "LEAKING PROMOTIONAL MARGIN"
    else:
        status_color = "#4ade80"
        status_text = "HEALTHY (TARGET MARGIN PRESERVED)"

    # Order Headline Banner (Mirrors Calculator Section in UI Dashboard)
    st.markdown(f"""
    <div style="background: rgba(15, 23, 42, 0.8); border-left: 5px solid {status_color};
                border-radius: 8px; padding: 18px; margin: 15px 0;">
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <div>
                <span style="font-size: 1.3rem; font-weight: 700; color: #f8fafc;">SIMULATED ORDER #SIM-001</span>
                <span style="margin-left: 12px; font-weight: 600; color: {status_color}; font-size: 0.9rem;">[{status_text}]</span>
            </div>
            <div style="font-family: 'JetBrains Mono', monospace; color: #94a3b8; font-size: 0.85rem;">
                Status: <b>{f01_res.status.upper()}</b> | Currency: USD
            </div>
        </div>
        <div style="margin-top: 10px; display: flex; gap: 24px; font-size: 0.9rem; color: #cbd5e1;">
            <div>Promotional Leakage: <b style="color: #f87171;">${f01_res.f01_dollar_loss:,.2f}</b></div>
            <div>Inherent Deficit: <b style="color: #eab308;">${f01_res.inherent_cogs_deficit:,.2f}</b></div>
            <div>Total Shortfall: <b style="color: #fb923c;">${f01_res.total_target_shortfall:,.2f}</b></div>
            <div>Actual GP: <b style="color: #4ade80;">${f01_res.actual_gross_profit:,.2f}</b></div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    if is_quarantined:
        st.warning(f"🚨 **ORDER QUARANTINED**: {f01_res.quarantine_reason}. Quarantined orders are safely isolated to protect storewide promotional leakage reporting from corrupted/missing COGS inputs.")

    # F01 Order Score calculation
    tgt_profit = f01_res.target_minimum_profit
    promo_leak = f01_res.f01_dollar_loss
    inh_deficit = f01_res.inherent_cogs_deficit
    tot_shortfall = f01_res.total_target_shortfall
    act_profit = f01_res.actual_gross_profit
    base_profit = f01_res.baseline_gross_profit

    retention_score = max(0.0, (1.0 - (promo_leak / tgt_profit))) * 100.0 if tgt_profit > 0 else 100.0
    health_status = "HEALTHY" if retention_score >= 85.0 else ("WARNING" if retention_score >= 65.0 else "CRITICAL")
    badge_cls = "badge-healthy" if health_status == "HEALTHY" else ("badge-medium" if health_status == "WARNING" else "badge-critical")

    res_col1, res_col2, res_col3, res_col4 = st.columns(4)
    with res_col1:
        st.markdown(f"""
        <div class="metric-card" style="border-left: 4px solid {'#4ade80' if health_status == 'HEALTHY' else ('#fb923c' if health_status == 'WARNING' else '#f87171')};">
            <div class="metric-title">F01 Order Retention Score</div>
            <div class="metric-val">{retention_score:.2f}%</div>
            <div class="metric-sub"><span class="{badge_cls}">{health_status} BAND</span></div>
            <div style="font-size: 0.75rem; color: #94a3b8; margin-top: 6px;">
                Retained: {retention_score:.2f}% | Leaked: {(100.0 - retention_score):.2f}%
            </div>
        </div>
        """, unsafe_allow_html=True)

    with res_col2:
        st.markdown(f"""
        <div class="metric-card" style="border-left: 4px solid #f87171;">
            <div class="metric-title">Promotional Margin Leakage</div>
            <div class="metric-val" style="color: #f87171;">${promo_leak:,.2f}</div>
            <div class="metric-sub">Caused Strictly by Discounts</div>
            <div style="font-size: 0.75rem; color: #94a3b8; margin-top: 6px;">
                Target Shortfall: ${tot_shortfall:,.2f}
            </div>
        </div>
        """, unsafe_allow_html=True)

    with res_col3:
        st.markdown(f"""
        <div class="metric-card" style="border-left: 4px solid #eab308;">
            <div class="metric-title">Inherent COGS Deficit</div>
            <div class="metric-val" style="color: #eab308;">${inh_deficit:,.2f}</div>
            <div class="metric-sub">Pre-Existing Supplier/MSRP Gap</div>
            <div style="font-size: 0.75rem; color: #94a3b8; margin-top: 6px;">
                Existed before any discount
            </div>
        </div>
        """, unsafe_allow_html=True)

    with res_col4:
        st.markdown(f"""
        <div class="metric-card" style="border-left: 4px solid #38bdf8;">
            <div class="metric-title">Actual vs Target Profit</div>
            <div class="metric-val" style="color: #4ade80;">${act_profit:,.2f}</div>
            <div class="metric-sub">Required Target: ${tgt_profit:,.2f}</div>
            <div style="font-size: 0.75rem; color: #94a3b8; margin-top: 6px;">
                Baseline MSRP GP: ${base_profit:,.2f}
            </div>
        </div>
        """, unsafe_allow_html=True)

    # Reactive Plotly Waterfall for the Simulated Order
    fig_sim_wf = go.Figure(go.Waterfall(
        name="F01 Live Simulation",
        orientation="v",
        measure=["relative", "relative", "total", "absolute", "relative", "relative", "total"],
        x=[
            "1. Baseline Profit",
            "2. Promotional Discount",
            "3. Actual Gross Profit",
            "4. Target Profit",
            "5. Total Shortfall",
            "6. Inherent Deficit",
            "7. Promotional Leakage"
        ],
        textposition="outside",
        text=[
            f"${base_profit:,.2f}",
            f"-${f01_res.total_discounts:,.2f}",
            f"${act_profit:,.2f}",
            f"${tgt_profit:,.2f}",
            f"${tot_shortfall:,.2f}",
            f"-${inh_deficit:,.2f}",
            f"${promo_leak:,.2f}"
        ],
        y=[base_profit, -f01_res.total_discounts, act_profit, tgt_profit, tot_shortfall, -inh_deficit, promo_leak],
        connector={"line": {"color": "rgba(255, 255, 255, 0.2)"}},
        decreasing={"marker": {"color": "#f87171"}},
        increasing={"marker": {"color": "#38bdf8"}},
        totals={"marker": {"color": "#eab308"}}
    ))

    fig_sim_wf.update_layout(
        title="Reactive Order Waterfall: From Baseline MSRP Profit to Incremental Promotional Leakage",
        template="plotly_dark",
        plot_bgcolor="rgba(15, 23, 42, 0.6)",
        paper_bgcolor="rgba(15, 23, 42, 0.0)",
        height=340,
        margin=dict(l=20, r=20, t=40, b=20)
    )
    st.plotly_chart(fig_sim_wf, use_container_width=True)

    # Verification Identity Callout
    reconciled_sim = abs(tot_shortfall - (inh_deficit + promo_leak)) <= 0.01
    st.markdown(f"""
    <div class="callout-box" style="border-left-color: {'#4ade80' if reconciled_sim else '#f87171'}; padding: 12px 18px;">
        <b>Mathematical Reconciliation Identity:</b> 
        <code>Total Shortfall (${tot_shortfall:,.2f}) = Inherent COGS Deficit (${inh_deficit:,.2f}) + Incremental Promotional Leakage (${promo_leak:,.2f})</code>
        &nbsp;|&nbsp; Difference: <b>$0.00</b> &nbsp;|&nbsp; <b>{'🟢 PASS' if reconciled_sim else '🔴 FAIL'}</b>
    </div>
    """, unsafe_allow_html=True)

    # -------------------------------------------------------------------------
    # DETAILED LINE-BY-LINE DECOMPOSITION (MATCHING CALCULATOR SECTION)
    # -------------------------------------------------------------------------
    st.markdown("#### 🔬 Detailed Line-by-Line Economics & Intermediate Decomposition")
    st.caption("Inspects the exact intermediate arithmetic, discount decomposition, COGS resolution, and target margin derivation.")

    for idx, li in enumerate(f01_res.line_items, 1):
        with st.container():
            st.markdown(f"##### Line Item #{idx}: {li.sku or 'SKU-SIM-101'} (Variant #{li.variant_id} | Product #{li.product_id or 3001})")

            c_base, c_disc, c_cogs, c_tgt = st.columns(4)

            with c_base:
                st.markdown("""
                <div class="metric-card" style="padding: 14px;">
                    <b style="color: #38bdf8; font-size: 0.85rem;">1. BASELINE / MSRP</b>
                    <div style="font-size: 0.8rem; color: #cbd5e1; margin-top: 6px;">
                        Original Unit MSRP: <b>$""" + f"{li.original_price:,.2f}" + """</b><br>
                        Purchased Qty: <b>""" + f"{li.quantity}" + """</b><br>
                        Active Qty: <b>""" + f"{li.active_quantity}" + """</b><br>
                        Returned Qty: <b>""" + f"{max(0, li.quantity - li.active_quantity)}" + """</b><br>
                        <b>Baseline Revenue:</b> $""" + f"{li.original_line_value:,.2f}" + """
                    </div>
                    <div style="font-size: 0.72rem; color: #94a3b8; margin-top: 4px;">
                        Formula: MSRP × Active Qty
                    </div>
                </div>
                """, unsafe_allow_html=True)

            with c_disc:
                st.markdown("""
                <div class="metric-card" style="padding: 14px;">
                    <b style="color: #fb923c; font-size: 0.85rem;">2. DISCOUNT DECOMPOSITION</b>
                    <div style="font-size: 0.8rem; color: #cbd5e1; margin-top: 6px;">
                        Line Markdown: <b>$""" + f"{li.line_discount_amount:,.2f}" + """</b><br>
                        Order Cart Allocation: <b>$""" + f"{li.order_discount_allocation:,.2f}" + """</b><br>
                        <b>Total Discount:</b> $""" + f"{li.total_discount_amount:,.2f}" + """<br>
                        Discount %: <b>""" + f"{li.discount_percentage:.1f}%" + """</b><br>
                        Code: <code>""" + f"{li.discount_code or 'NONE'}" + """</code> (Type: """ + f"{li.discount_type}" + """)
                    </div>
                    <div style="font-size: 0.72rem; color: #94a3b8; margin-top: 4px;">
                        Formula: Line Disc + Cart Allocation
                    </div>
                </div>
                """, unsafe_allow_html=True)

            with c_cogs:
                st.markdown("""
                <div class="metric-card" style="padding: 14px;">
                    <b style="color: #4ade80; font-size: 0.85rem;">3. REFUNDS & ACTIVE COGS</b>
                    <div style="font-size: 0.8rem; color: #cbd5e1; margin-top: 6px;">
                        Net Revenue: <b>$""" + f"{li.net_revenue:,.2f}" + """</b><br>
                        Cash Refund Alloc: <b>$""" + f"{li.cash_refund_allocated:,.2f}" + """</b><br>
                        Unit COGS: <b>$""" + f"{li.cogs_used:,.2f}" + """</b><br>
                        <b>Total Active COGS:</b> $""" + f"{li.total_cogs:,.2f}" + """<br>
                        COGS Source: <code>""" + f"{li.cogs_source}" + """</code><br>
                        <b>Actual Gross Profit:</b> $""" + f"{li.actual_gross_profit:,.2f}" + """
                    </div>
                    <div style="font-size: 0.72rem; color: #94a3b8; margin-top: 4px;">
                        COGS on returned units: $0.00
                    </div>
                </div>
                """, unsafe_allow_html=True)

            with c_tgt:
                st.markdown("""
                <div class="metric-card" style="padding: 14px;">
                    <b style="color: #f87171; font-size: 0.85rem;">4. TARGET & LEAKAGE</b>
                    <div style="font-size: 0.8rem; color: #cbd5e1; margin-top: 6px;">
                        Target Margin: <b>""" + f"{li.target_margin_used*100:.2f}%" + """</b><br>
                        Target Source: <code>""" + f"{li.target_margin_source}" + """</code><br>
                        Target Profit: <b>$""" + f"{li.target_profit:,.2f}" + """</b><br>
                        Inherent Deficit: <b>$""" + f"{li.inherent_cogs_deficit:,.2f}" + """</b><br>
                        <b>Promotional Leak:</b> <span style="color: #f87171; font-weight: 700;">$""" + f"{li.f01_dollar_loss:,.2f}" + """</span><br>
                        Reason: <code>""" + f"{li.leakage_reason}" + """</code>
                    </div>
                    <div style="font-size: 0.72rem; color: #94a3b8; margin-top: 4px;">
                        Shortfall = Inherent + Promo Leak
                    </div>
                </div>
                """, unsafe_allow_html=True)

    if "Tier 5" in sim_target_src:
        st.markdown("""
        <div class="callout-box" style="border-left-color: #38bdf8; margin: 12px 0;">
            <b>⏳ Tier 5: 90-Day Rolling Historical Margin Calculation Methodology:</b><br>
            • <b>Window:</b> Strict 90-day lookback <code>[order_time - 90d, order_time)</code>.<br>
            • <b>Qualifying Observations:</b> Standard completed, non-cancelled, non-refunded transactions.<br>
            • <b>Statistical Guard:</b> Requires <code>N ≥ 5</code> qualifying transactions. Realized margins outside <code>[-50%, +95%]</code> trimmed as outliers.<br>
            • <b>Fallback:</b> If <code>N &lt; 5</code>, safely cascades down to Tier 6 Storewide Default (35.0%).
        </div>
        """, unsafe_allow_html=True)

    # -------------------------------------------------------------------------
    # SIDE-BY-SIDE ARCHITECTURAL CONTRAST: F01 VS F03
    # -------------------------------------------------------------------------
    st.markdown("---")
    st.markdown("#### ⚖️ Side-by-Side Architectural Contrast: F01 (Product Margin) vs. F03 (Cash Floor)")
    
    # Calculate F03 Cash Flow
    # Cash in: merchandise revenue + customer shipping - taxes
    gross_merch = f01_res.total_net_revenue
    tax_liability = gross_merch * (sim_vat_pct / (100.0 + sim_vat_pct)) if (sim_taxes_incl and sim_vat_pct > 0) else 0.0
    f03_cash_in = max(0.0, gross_merch - tax_liability) + sim_cust_shipping
    
    # Gateway fee
    if sim_gateway == "Shopify Payments":
        f03_fee = round(gross_merch * 0.029 + 0.30, 2)
    elif sim_gateway == "PayPal Express (3rd Party)":
        f03_fee = round(gross_merch * 0.0349 + 0.49, 2)
    else:
        f03_fee = 0.0
        
    f03_cogs = f01_res.total_cogs
    f03_cash_out = f03_cogs + sim_carrier_cost + f03_fee
    f03_net_cash = f03_cash_in - f03_cash_out
    f03_breach = f03_net_cash < 0.0

    comp_c1, comp_c2 = st.columns(2)
    with comp_c1:
        st.markdown(f"""
        <div class="metric-card" style="border-left: 4px solid #fb923c;">
            <b style="color: #fb923c; font-size: 1.05rem;">Formula F01: Promotional Gross Margin</b><br>
            • Scope: <b>Merchandise Gross Margin against Target Floor</b><br>
            • Baseline Revenue: <b>${f01_res.total_original_value:,.2f}</b><br>
            • Total Discounts Applied: <b>${f01_res.total_discounts:,.2f}</b><br>
            • Physical Unit COGS: <b>${f01_res.total_cogs:,.2f}</b><br>
            • Realized Gross Profit: <b>${f01_res.actual_gross_profit:,.2f}</b><br>
            • Required Target Profit: <b>${f01_res.target_minimum_profit:,.2f}</b><br>
            • <b>Incremental Promotional Leakage:</b> <span style="color: #f87171; font-weight: 700;">${f01_res.f01_dollar_loss:,.2f}</span><br>
            • Status: <b>{'🔴 LEAKING BELOW TARGET' if f01_res.f01_dollar_loss > 0 else '🟢 HEALTHY (AT/ABOVE TARGET)'}</b>
        </div>
        """, unsafe_allow_html=True)

    with comp_c2:
        st.markdown(f"""
        <div class="metric-card" style="border-left: 4px solid #38bdf8;">
            <b style="color: #38bdf8; font-size: 1.05rem;">Formula F03: Direct Cash Margin Floor</b><br>
            • Scope: <b>Net Physical Cash In vs. Cash Out</b><br>
            • Cash In (Merchandise + Shipping - Tax): <b>${f03_cash_in:,.2f}</b><br>
            • Direct COGS Paid: <b>${f03_cogs:,.2f}</b><br>
            • Courier Label Cost: <b>${sim_carrier_cost:,.2f}</b><br>
            • Payment Gateway Fee: <b>${f03_fee:,.2f}</b><br>
            • Total Cash Out: <b>${f03_cash_out:,.2f}</b><br>
            • <b>Net Direct Cash Contribution:</b> <span style="color: {'#f87171' if f03_breach else '#4ade80'}; font-weight: 700;">${f03_net_cash:,.2f}</span><br>
            • Status: <b>{'🔴 MARGIN FLOOR BREACH' if f03_breach else '🟢 POSITIVE CASH CONTRIBUTION'}</b>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("""
    <div class="callout-box" style="border-left-color: #38bdf8; margin-top: 14px;">
        <b>💡 Why This Separation Matters to the Merchant:</b><br>
        Notice that changing the courier label cost ($12) or the payment gateway processing fee ($3.20) changes 
        Formula F03's net cash outcome, but has <b>zero effect on Formula F01's promotional leakage</b>.
        F01 answers: <i>"Did my discounts erode my target gross margin?"</i>
        F03 answers: <i>"Did I collect more physical cash than I spent to fulfill and process the order?"</i>
    </div>
    """, unsafe_allow_html=True)


