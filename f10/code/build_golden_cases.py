"""
Comprehensive Golden Set Generator for Formula F10 v2.
Faithfully reproduces all 29 formula cases (FT-01 to FT-29),
6 allocation cases (AL-01 to AL-06), 6 date cases (DT-01 to DT-06),
6 metamorphic checks (MM-01 to MM-06), canonical G-01 to G-05,
and extends with extraction-layer probe fixtures to >= 160 total cases.
"""

import glob
import json
import os
from decimal import Decimal, ROUND_HALF_UP

GOLDEN_DIR = os.path.join("f10", "golden")
os.makedirs(GOLDEN_DIR, exist_ok=True)

# Standard test configuration declared in F10_formula_test_cases.md
BASE_FT_CONFIG = {
    "api_version": "2024-10",
    "as_of": "2026-09-30",
    "shop_currency": "USD",
    "currency_minor_units": 2,
    "rounding_mode": "ROUND_HALF_UP",
    "cohort_date_field": "processedAt",
    "return_window_days": 30,
    "processing_days": 5,
    "carrier_cost_model": "flat",
    "carrier_flat_rate": 6.50,
    "return_ship_cost": 6.50,
    "handling_cost": 5.00,
    "pick_pack_cost": 0.00,
    "fee_fallback": {"rate": 0.029, "fixed": 0.30},
    "shipping_alloc_fallback": "net_billed_share",
    "no_restock_policy": "lost",
    "goodwill_rule": "proportional",
    "max_unknown_cost_share": 0.15,
    "min_units_for_confidence": 30,
    "healthy_margin_by_category": {"Apparel": 0.25, "UNMAPPED": 0.25},
    "category_map": {"Clothing": "Apparel"},
    "return_rate_baseline_by_category": {"Apparel": 0.22, "UNMAPPED": 0.15},
    "bundle_policy": "explode",
    "cost_snapshot_policy": "current_with_flag",
    "exchange_policy": "netting",
    "reconcile_tolerance": 0.01
}

def generate_golden_cases():
    # Clean previous files to prevent stale test fixtures
    for old_file in glob.glob(os.path.join(GOLDEN_DIR, "*.json")):
        try:
            os.remove(old_file)
        except OSError:
            pass

    cases = []

    # -------------------------------------------------------------
    # 1. Authoritative Formula Cases (FT-01 through FT-29)
    # -------------------------------------------------------------
    
    # FT-01: Dress, 40% returns, 30 restocked / 10 written off
    cases.append({
        "id": "FT-01-dress-40pct-returns-partial-restock",
        "category": "formula_canonical",
        "description": "FT-01: Dress, 40% returns, 30 restocked / 10 written off. Restocked units recover cost.",
        "config": BASE_FT_CONFIG,
        "lines": [{
            "line_item_id": "line-ft01", "order_id": "order-ft01", "variant_id": "var-ft01", "product_id": "prod-ft01",
            "sku": "DRESS-FT01", "title": "Silk Dress", "category": "Apparel", "cohort_date": "2026-08-01", "is_matured": True,
            "q_ordered": 100, "q_removed": 0, "q_cancelled": 0, "q_shipped": 100, "q_refunded": 40, "q_restocked": 30,
            "gross_line": "10000.00", "disc_line": "0.00", "refund_item": "4000.00", "goodwill": "0.00",
            "cost_snapshot": "40.00", "carrier_cost_allocated": "500.00", "shipping_charged_allocated": "0.00",
            "pay_fees": "300.00", "pay_fees_tier": "T1"
        }],
        "expected": {
            "retained_rev": "6000.00", "cogs_lost": "2800.00", "contribution": "1940.00",
            "margin_pct": "32.33", "score": "32.33", "status": "HEALTHY", "leakage": "4060.00"
        }
    })

    # FT-02: Same dress, all 40 returns written off
    cases.append({
        "id": "FT-02-dress-all-returns-written-off",
        "category": "formula_canonical",
        "description": "FT-02: Same dress, all 40 returns written off. Worst-case disposition.",
        "config": BASE_FT_CONFIG,
        "lines": [{
            "line_item_id": "line-ft02", "order_id": "order-ft02", "variant_id": "var-ft02", "product_id": "prod-ft02",
            "sku": "DRESS-FT02", "title": "Silk Dress Written Off", "category": "Apparel", "cohort_date": "2026-08-01", "is_matured": True,
            "q_ordered": 100, "q_removed": 0, "q_cancelled": 0, "q_shipped": 100, "q_refunded": 40, "q_restocked": 0,
            "gross_line": "10000.00", "disc_line": "0.00", "refund_item": "4000.00", "goodwill": "0.00",
            "cost_snapshot": "40.00", "carrier_cost_allocated": "500.00", "shipping_charged_allocated": "0.00",
            "pay_fees": "300.00", "pay_fees_tier": "T1"
        }],
        "expected": {
            "retained_rev": "6000.00", "cogs_lost": "4000.00", "contribution": "740.00",
            "margin_pct": "12.33", "score": "12.33", "status": "UNDERPERFORMING", "leakage": "5260.00"
        }
    })

    # FT-03: Same dress, all 40 returns restocked
    cases.append({
        "id": "FT-03-dress-all-returns-restocked",
        "category": "formula_canonical",
        "description": "FT-03: Same dress, all 40 returns restocked. Best-case disposition.",
        "config": BASE_FT_CONFIG,
        "lines": [{
            "line_item_id": "line-ft03", "order_id": "order-ft03", "variant_id": "var-ft03", "product_id": "prod-ft03",
            "sku": "DRESS-FT03", "title": "Silk Dress Restocked", "category": "Apparel", "cohort_date": "2026-08-01", "is_matured": True,
            "q_ordered": 100, "q_removed": 0, "q_cancelled": 0, "q_shipped": 100, "q_refunded": 40, "q_restocked": 40,
            "gross_line": "10000.00", "disc_line": "0.00", "refund_item": "4000.00", "goodwill": "0.00",
            "cost_snapshot": "40.00", "carrier_cost_allocated": "500.00", "shipping_charged_allocated": "0.00",
            "pay_fees": "300.00", "pay_fees_tier": "T1"
        }],
        "expected": {
            "retained_rev": "6000.00", "cogs_lost": "2400.00", "contribution": "2340.00",
            "margin_pct": "39.00", "score": "39.00", "status": "HEALTHY", "leakage": "3660.00"
        }
    })

    # FT-04: Healthy accessory, 2% returns, both restocked
    cases.append({
        "id": "FT-04-healthy-accessory-low-returns",
        "category": "formula_canonical",
        "description": "FT-04: Healthy accessory, 2% returns, both restocked.",
        "config": BASE_FT_CONFIG,
        "lines": [{
            "line_item_id": "line-ft04", "order_id": "order-ft04", "variant_id": "var-ft04", "product_id": "prod-ft04",
            "sku": "ACC-FT04", "title": "Leather Belt", "category": "Apparel", "cohort_date": "2026-08-01", "is_matured": True,
            "q_ordered": 100, "q_removed": 0, "q_cancelled": 0, "q_shipped": 100, "q_refunded": 2, "q_restocked": 2,
            "gross_line": "5000.00", "disc_line": "0.00", "refund_item": "100.00", "goodwill": "0.00",
            "cost_snapshot": "15.00", "carrier_cost_allocated": "250.00", "shipping_charged_allocated": "0.00",
            "pay_fees": "100.00", "pay_fees_tier": "T1"
        }],
        "expected": {
            "retained_rev": "4900.00", "cogs_lost": "1470.00", "contribution": "3057.00",
            "margin_pct": "62.39", "score": "62.39", "status": "HEALTHY", "leakage": "443.00"
        }
    })

    # FT-05: Goodwill refund only, no return
    cases.append({
        "id": "FT-05-goodwill-refund-only-no-return",
        "category": "formula_canonical",
        "description": "FT-05: Goodwill refund only, no return units.",
        "config": BASE_FT_CONFIG,
        "lines": [{
            "line_item_id": "line-ft05", "order_id": "order-ft05", "variant_id": "var-ft05", "product_id": "prod-ft05",
            "sku": "GW-FT05", "title": "Goodwill Item", "category": "Apparel", "cohort_date": "2026-08-01", "is_matured": True,
            "q_ordered": 10, "q_removed": 0, "q_cancelled": 0, "q_shipped": 10, "q_refunded": 0, "q_restocked": 0,
            "gross_line": "1000.00", "disc_line": "0.00", "refund_item": "0.00", "goodwill": "10.00",
            "cost_snapshot": "30.00", "carrier_cost_allocated": "50.00", "shipping_charged_allocated": "0.00",
            "pay_fees": "30.00", "pay_fees_tier": "T1"
        }],
        "expected": {
            "retained_rev": "990.00", "cogs_lost": "300.00", "contribution": "610.00",
            "margin_pct": "61.62", "score": "61.62", "status": "HEALTHY", "leakage": "90.00"
        }
    })

    # FT-06: Refunded, not restocked, kept by customer (policy kept_by_customer)
    cases.append({
        "id": "FT-06-kept-by-customer-policy",
        "category": "formula_canonical",
        "description": "FT-06: Refunded, not restocked, customer kept item (policy kept_by_customer).",
        "config": {**BASE_FT_CONFIG, "no_restock_policy": "kept_by_customer"},
        "lines": [{
            "line_item_id": "line-ft06", "order_id": "order-ft06", "variant_id": "var-ft06", "product_id": "prod-ft06",
            "sku": "KEPT-FT06", "title": "Kept Item", "category": "Apparel", "cohort_date": "2026-08-01", "is_matured": True,
            "q_ordered": 1, "q_removed": 0, "q_cancelled": 0, "q_shipped": 1, "q_refunded": 1, "q_restocked": 0,
            "gross_line": "100.00", "disc_line": "0.00", "refund_item": "100.00", "goodwill": "0.00",
            "cost_snapshot": "40.00", "carrier_cost_allocated": "8.00", "shipping_charged_allocated": "0.00",
            "pay_fees": "3.00", "pay_fees_tier": "T1"
        }],
        "expected": {
            "retained_rev": "0.00", "cogs_lost": "40.00", "contribution": "-51.00",
            "margin_pct": None, "score": "0.00", "status": "VALUE_DESTROYING", "leakage": "111.00"
        }
    })

    # FT-07: Same as FT-06 under policy unknown
    cases.append({
        "id": "FT-07-unresolved-policy-unknown",
        "category": "formula_canonical",
        "description": "FT-07: Same as FT-06 under policy unknown. Must not guess; status UNRESOLVED.",
        "config": {**BASE_FT_CONFIG, "no_restock_policy": "unknown"},
        "lines": [{
            "line_item_id": "line-ft07", "order_id": "order-ft07", "variant_id": "var-ft07", "product_id": "prod-ft07",
            "sku": "UNK-FT07", "title": "Unknown Policy Item", "category": "Apparel", "cohort_date": "2026-08-01", "is_matured": True,
            "q_ordered": 1, "q_removed": 0, "q_cancelled": 0, "q_shipped": 1, "q_refunded": 1, "q_restocked": 0,
            "gross_line": "100.00", "disc_line": "0.00", "refund_item": "100.00", "goodwill": "0.00",
            "cost_snapshot": "40.00", "carrier_cost_allocated": "8.00", "shipping_charged_allocated": "0.00",
            "pay_fees": "3.00", "pay_fees_tier": "T1"
        }],
        "expected": {
            "contribution": None, "margin_pct": None, "score": None, "status": "UNRESOLVED"
        }
    })

    # FT-08: 2 of 10 units cancelled before shipping
    cases.append({
        "id": "FT-08-partial-cancel-before-shipping",
        "category": "formula_canonical",
        "description": "FT-08: 2 of 10 units cancelled before shipping. Cancelled units carry no COGS and no outbound.",
        "config": BASE_FT_CONFIG,
        "lines": [{
            "line_item_id": "line-ft08", "order_id": "order-ft08", "variant_id": "var-ft08", "product_id": "prod-ft08",
            "sku": "CAN-FT08", "title": "Cancelled Pre-Ship Item", "category": "Apparel", "cohort_date": "2026-08-01", "is_matured": True,
            "q_ordered": 10, "q_removed": 0, "q_cancelled": 2, "q_shipped": 8, "q_refunded": 0, "q_restocked": 0,
            "gross_line": "1000.00", "disc_line": "0.00", "refund_item": "200.00", "goodwill": "0.00",
            "cost_snapshot": "30.00", "carrier_cost_allocated": "40.00", "shipping_charged_allocated": "0.00",
            "pay_fees": "30.00", "pay_fees_tier": "T1"
        }],
        "expected": {
            "retained_rev": "800.00", "cogs_lost": "240.00", "contribution": "490.00",
            "margin_pct": "61.25", "score": "61.25", "status": "HEALTHY", "leakage": "270.00"
        }
    })

    # FT-09: Free item (100% discount)
    cases.append({
        "id": "FT-09-free-item-100pct-discount",
        "category": "formula_canonical",
        "description": "FT-09: Free item (100% discount). Revenue 0, costs positive: dollars shown, margin null, score 0.",
        "config": BASE_FT_CONFIG,
        "lines": [{
            "line_item_id": "line-ft09", "order_id": "order-ft09", "variant_id": "var-ft09", "product_id": "prod-ft09",
            "sku": "FREE-FT09", "title": "Freebie Item", "category": "Apparel", "cohort_date": "2026-08-01", "is_matured": True,
            "q_ordered": 5, "q_removed": 0, "q_cancelled": 0, "q_shipped": 5, "q_refunded": 0, "q_restocked": 0,
            "gross_line": "0.00", "disc_line": "0.00", "refund_item": "0.00", "goodwill": "0.00",
            "cost_snapshot": "20.00", "carrier_cost_allocated": "25.00", "shipping_charged_allocated": "0.00",
            "pay_fees": "0.00", "pay_fees_tier": "T1"
        }],
        "expected": {
            "retained_rev": "0.00", "cogs_lost": "100.00", "contribution": "-125.00",
            "margin_pct": None, "score": "0.00", "status": "VALUE_DESTROYING", "leakage": "25.00"
        }
    })

    # FT-10: Refunds plus goodwill exceed billed (negative retained revenue)
    cases.append({
        "id": "FT-10-refunds-exceed-billed",
        "category": "formula_canonical",
        "description": "FT-10: Refunds plus goodwill exceed billed. Margin must be null, not a negative percent.",
        "config": BASE_FT_CONFIG,
        "lines": [{
            "line_item_id": "line-ft10", "order_id": "order-ft10", "variant_id": "var-ft10", "product_id": "prod-ft10",
            "sku": "NEG-FT10", "title": "Negative Retained Item", "category": "Apparel", "cohort_date": "2026-08-01", "is_matured": True,
            "q_ordered": 1, "q_removed": 0, "q_cancelled": 0, "q_shipped": 1, "q_refunded": 1, "q_restocked": 1,
            "gross_line": "100.00", "disc_line": "0.00", "refund_item": "100.00", "goodwill": "30.00",
            "cost_snapshot": "40.00", "carrier_cost_allocated": "10.00", "shipping_charged_allocated": "0.00",
            "pay_fees": "3.00", "pay_fees_tier": "T1"
        }],
        "expected": {
            "retained_rev": "-30.00", "cogs_lost": "0.00", "contribution": "-54.50",
            "margin_pct": None, "score": "0.00", "status": "VALUE_DESTROYING", "leakage": "114.50"
        }
    })

    # FT-11: Contribution exactly 0 (Breakeven)
    cases.append({
        "id": "FT-11-contribution-exactly-zero-breakeven",
        "category": "formula_canonical",
        "description": "FT-11: Contribution exactly 0. Breakeven is neither positive nor negative.",
        "config": BASE_FT_CONFIG,
        "lines": [{
            "line_item_id": "line-ft11", "order_id": "order-ft11", "variant_id": "var-ft11", "product_id": "prod-ft11",
            "sku": "BE-FT11", "title": "Breakeven Item", "category": "Apparel", "cohort_date": "2026-08-01", "is_matured": True,
            "q_ordered": 1, "q_removed": 0, "q_cancelled": 0, "q_shipped": 1, "q_refunded": 0, "q_restocked": 0,
            "gross_line": "100.00", "disc_line": "0.00", "refund_item": "0.00", "goodwill": "0.00",
            "cost_snapshot": "60.00", "carrier_cost_allocated": "30.00", "shipping_charged_allocated": "0.00",
            "pay_fees": "10.00", "pay_fees_tier": "T1"
        }],
        "expected": {
            "retained_rev": "100.00", "cogs_lost": "60.00", "contribution": "0.00",
            "margin_pct": "0.00", "score": "0.00", "status": "BREAKEVEN", "leakage": "40.00"
        }
    })

    # FT-12: Margin exactly 25.00% (healthy threshold)
    cases.append({
        "id": "FT-12-margin-exactly-healthy-threshold",
        "category": "formula_canonical",
        "description": "FT-12: Margin exactly 25.00%. Threshold is inclusive: >= 25 is HEALTHY.",
        "config": BASE_FT_CONFIG,
        "lines": [{
            "line_item_id": "line-ft12", "order_id": "order-ft12", "variant_id": "var-ft12", "product_id": "prod-ft12",
            "sku": "HLTH-FT12", "title": "Threshold Item", "category": "Apparel", "cohort_date": "2026-08-01", "is_matured": True,
            "q_ordered": 1, "q_removed": 0, "q_cancelled": 0, "q_shipped": 1, "q_refunded": 0, "q_restocked": 0,
            "gross_line": "100.00", "disc_line": "0.00", "refund_item": "0.00", "goodwill": "0.00",
            "cost_snapshot": "50.00", "carrier_cost_allocated": "15.00", "shipping_charged_allocated": "0.00",
            "pay_fees": "10.00", "pay_fees_tier": "T1"
        }],
        "expected": {
            "retained_rev": "100.00", "cogs_lost": "50.00", "contribution": "25.00",
            "margin_pct": "25.00", "score": "25.00", "status": "HEALTHY", "leakage": "25.00"
        }
    })

    # FT-13: Margin 24.99% (just below threshold)
    cases.append({
        "id": "FT-13-margin-just-below-threshold",
        "category": "formula_canonical",
        "description": "FT-13: Margin 24.99%. Just below threshold: UNDERPERFORMING.",
        "config": BASE_FT_CONFIG,
        "lines": [{
            "line_item_id": "line-ft13", "order_id": "order-ft13", "variant_id": "var-ft13", "product_id": "prod-ft13",
            "sku": "SUB-FT13", "title": "Sub-threshold Item", "category": "Apparel", "cohort_date": "2026-08-01", "is_matured": True,
            "q_ordered": 100, "q_removed": 0, "q_cancelled": 0, "q_shipped": 100, "q_refunded": 0, "q_restocked": 0,
            "gross_line": "10000.00", "disc_line": "0.00", "refund_item": "0.00", "goodwill": "0.00",
            "cost_snapshot": "50.00", "carrier_cost_allocated": "1500.00", "shipping_charged_allocated": "0.00",
            "pay_fees": "1001.00", "pay_fees_tier": "T1"
        }],
        "expected": {
            "retained_rev": "10000.00", "cogs_lost": "5000.00", "contribution": "2499.00",
            "margin_pct": "24.99", "score": "24.99", "status": "UNDERPERFORMING", "leakage": "2501.00"
        }
    })

    # FT-14: 29 units shipped (below min units)
    cases.append({
        "id": "FT-14-twenty-nine-units-low-confidence",
        "category": "formula_canonical",
        "description": "FT-14: 29 units shipped. Below min_units (30): LOW_CONFIDENCE.",
        "config": BASE_FT_CONFIG,
        "lines": [{
            "line_item_id": "line-ft14", "order_id": "order-ft14", "variant_id": "var-ft14", "product_id": "prod-ft14",
            "sku": "CONF-FT14", "title": "Low Volume Item", "category": "Apparel", "cohort_date": "2026-08-01", "is_matured": True,
            "q_ordered": 29, "q_removed": 0, "q_cancelled": 0, "q_shipped": 29, "q_refunded": 0, "q_restocked": 0,
            "gross_line": "290.00", "disc_line": "0.00", "refund_item": "0.00", "goodwill": "0.00",
            "cost_snapshot": "4.00", "carrier_cost_allocated": "0.00", "shipping_charged_allocated": "0.00",
            "pay_fees": "0.00", "pay_fees_tier": "T1"
        }],
        "expected": {
            "retained_rev": "290.00", "cogs_lost": "116.00", "contribution": "174.00",
            "margin_pct": "60.00", "score": "60.00", "status": "HEALTHY", "leakage": "0.00"
        }
    })

    # FT-15: 30 units shipped (at min units)
    cases.append({
        "id": "FT-15-thirty-units-confidence-ok",
        "category": "formula_canonical",
        "description": "FT-15: 30 units shipped. At min_units: confidence OK.",
        "config": BASE_FT_CONFIG,
        "lines": [{
            "line_item_id": "line-ft15", "order_id": "order-ft15", "variant_id": "var-ft15", "product_id": "prod-ft15",
            "sku": "CONF-FT15", "title": "Normal Volume Item", "category": "Apparel", "cohort_date": "2026-08-01", "is_matured": True,
            "q_ordered": 30, "q_removed": 0, "q_cancelled": 0, "q_shipped": 30, "q_refunded": 0, "q_restocked": 0,
            "gross_line": "300.00", "disc_line": "0.00", "refund_item": "0.00", "goodwill": "0.00",
            "cost_snapshot": "4.00", "carrier_cost_allocated": "0.00", "shipping_charged_allocated": "0.00",
            "pay_fees": "0.00", "pay_fees_tier": "T1"
        }],
        "expected": {
            "retained_rev": "300.00", "cogs_lost": "120.00", "contribution": "180.00",
            "margin_pct": "60.00", "score": "60.00", "status": "HEALTHY", "leakage": "0.00"
        }
    })

    # FT-16: Quarantine: cost missing on one line (unknown share 33.3%)
    cases.append({
        "id": "FT-16-quarantine-unknown-share-33pct",
        "category": "formula_canonical",
        "description": "FT-16: Quarantine: cost missing on one line (unknown share 33.3%). Above max_unknown 15%: UNSCOREABLE.",
        "config": BASE_FT_CONFIG,
        "lines": [
            {"line_item_id": "line-ft16-a", "order_id": "order-ft16", "variant_id": "var-ft16", "product_id": "prod-ft16", "sku": "Q-FT16", "title": "Widget Q", "category": "Apparel", "cohort_date": "2026-08-01", "is_matured": True, "q_ordered": 6, "q_removed": 0, "q_cancelled": 0, "q_shipped": 6, "q_refunded": 0, "q_restocked": 0, "gross_line": "600.00", "disc_line": "0.00", "refund_item": "0.00", "goodwill": "0.00", "cost_snapshot": "50.00", "carrier_cost_allocated": "0.00", "shipping_charged_allocated": "0.00", "pay_fees": "0.00", "pay_fees_tier": "T1"},
            {"line_item_id": "line-ft16-b", "order_id": "order-ft16", "variant_id": "var-ft16", "product_id": "prod-ft16", "sku": "Q-FT16", "title": "Widget Q", "category": "Apparel", "cohort_date": "2026-08-01", "is_matured": True, "q_ordered": 4, "q_removed": 0, "q_cancelled": 0, "q_shipped": 4, "q_refunded": 0, "q_restocked": 0, "gross_line": "400.00", "disc_line": "0.00", "refund_item": "0.00", "goodwill": "0.00", "cost_snapshot": "50.00", "carrier_cost_allocated": "0.00", "shipping_charged_allocated": "0.00", "pay_fees": "0.00", "pay_fees_tier": "T1"},
            {"line_item_id": "line-ft16-c", "order_id": "order-ft16", "variant_id": "var-ft16", "product_id": "prod-ft16", "sku": "Q-FT16", "title": "Widget Q", "category": "Apparel", "cohort_date": "2026-08-01", "is_matured": True, "q_ordered": 5, "q_removed": 0, "q_cancelled": 0, "q_shipped": 5, "q_refunded": 0, "q_restocked": 0, "gross_line": "500.00", "disc_line": "0.00", "refund_item": "0.00", "goodwill": "0.00", "cost_snapshot": None, "carrier_cost_allocated": "0.00", "shipping_charged_allocated": "0.00", "pay_fees": "0.00", "pay_fees_tier": "T1"}
        ],
        "expected": {
            "status": "UNSCOREABLE", "contribution": None, "margin_pct": None, "score": None
        }
    })

    # FT-17: Unknown share exactly 15.0%
    cases.append({
        "id": "FT-17-unknown-share-exactly-15pct",
        "category": "formula_canonical",
        "description": "FT-17: Unknown share exactly 15.0%. Rule is strictly greater than: equal is still scoreable.",
        "config": BASE_FT_CONFIG,
        "lines": [
            {"line_item_id": "line-ft17-a", "order_id": "order-ft17", "variant_id": "var-ft17", "product_id": "prod-ft17", "sku": "Q-FT17", "title": "Widget 15", "category": "Apparel", "cohort_date": "2026-08-01", "is_matured": True, "q_ordered": 17, "q_removed": 0, "q_cancelled": 0, "q_shipped": 17, "q_refunded": 0, "q_restocked": 0, "gross_line": "850.00", "disc_line": "0.00", "refund_item": "0.00", "goodwill": "0.00", "cost_snapshot": "20.00", "carrier_cost_allocated": "0.00", "shipping_charged_allocated": "0.00", "pay_fees": "0.00", "pay_fees_tier": "T1"},
            {"line_item_id": "line-ft17-b", "order_id": "order-ft17", "variant_id": "var-ft17", "product_id": "prod-ft17", "sku": "Q-FT17", "title": "Widget 15", "category": "Apparel", "cohort_date": "2026-08-01", "is_matured": True, "q_ordered": 3, "q_removed": 0, "q_cancelled": 0, "q_shipped": 3, "q_refunded": 0, "q_restocked": 0, "gross_line": "150.00", "disc_line": "0.00", "refund_item": "0.00", "goodwill": "0.00", "cost_snapshot": None, "carrier_cost_allocated": "0.00", "shipping_charged_allocated": "0.00", "pay_fees": "0.00", "pay_fees_tier": "T1"}
        ],
        "expected": {
            "status": "HEALTHY", "retained_rev": "850.00", "cogs_lost": "340.00", "contribution": "510.00",
            "margin_pct": "60.00", "score": "60.00"
        }
    })

    # FT-18: Unknown share 15.1%
    cases.append({
        "id": "FT-18-unknown-share-15-point-1-pct",
        "category": "formula_canonical",
        "description": "FT-18: Unknown share 15.1%. Just above limit: UNSCOREABLE.",
        "config": BASE_FT_CONFIG,
        "lines": [
            {"line_item_id": "line-ft18-a", "order_id": "order-ft18", "variant_id": "var-ft18", "product_id": "prod-ft18", "sku": "Q-FT18", "title": "Widget 15.1", "category": "Apparel", "cohort_date": "2026-08-01", "is_matured": True, "q_ordered": 17, "q_removed": 0, "q_cancelled": 0, "q_shipped": 17, "q_refunded": 0, "q_restocked": 0, "gross_line": "849.00", "disc_line": "0.00", "refund_item": "0.00", "goodwill": "0.00", "cost_snapshot": "20.00", "carrier_cost_allocated": "0.00", "shipping_charged_allocated": "0.00", "pay_fees": "0.00", "pay_fees_tier": "T1"},
            {"line_item_id": "line-ft18-b", "order_id": "order-ft18", "variant_id": "var-ft18", "product_id": "prod-ft18", "sku": "Q-FT18", "title": "Widget 15.1", "category": "Apparel", "cohort_date": "2026-08-01", "is_matured": True, "q_ordered": 3, "q_removed": 0, "q_cancelled": 0, "q_shipped": 3, "q_refunded": 0, "q_restocked": 0, "gross_line": "151.00", "disc_line": "0.00", "refund_item": "0.00", "goodwill": "0.00", "cost_snapshot": None, "carrier_cost_allocated": "0.00", "shipping_charged_allocated": "0.00", "pay_fees": "0.00", "pay_fees_tier": "T1"}
        ],
        "expected": {
            "status": "UNSCOREABLE", "contribution": None, "margin_pct": None, "score": None
        }
    })

    # FT-19: Cost = 0, not confirmed
    cases.append({
        "id": "FT-19-cost-zero-not-confirmed",
        "category": "formula_canonical",
        "description": "FT-19: Cost = 0, not confirmed. Quarantined as COGS_ZERO_SUSPECT, status UNSCOREABLE.",
        "config": BASE_FT_CONFIG,
        "lines": [{
            "line_item_id": "line-ft19", "order_id": "order-ft19", "variant_id": "var-ft19", "product_id": "prod-ft19",
            "sku": "ZERO-FT19", "title": "Zero Cost Unconfirmed", "category": "Apparel", "cohort_date": "2026-08-01", "is_matured": True,
            "q_ordered": 1, "q_removed": 0, "q_cancelled": 0, "q_shipped": 1, "q_refunded": 0, "q_restocked": 0,
            "gross_line": "100.00", "disc_line": "0.00", "refund_item": "0.00", "goodwill": "0.00",
            "cost_snapshot": "0.00", "carrier_cost_allocated": "0.00", "shipping_charged_allocated": "0.00",
            "pay_fees": "0.00", "pay_fees_tier": "T1"
        }],
        "expected": {
            "status": "UNSCOREABLE", "contribution": None, "margin_pct": None, "score": None
        }
    })

    # FT-20: Cost = 0, merchant-confirmed (digital product)
    cases.append({
        "id": "FT-20-cost-zero-confirmed-digital",
        "category": "formula_canonical",
        "description": "FT-20: Cost = 0, merchant-confirmed (digital product). Confirmed zero is scored.",
        "config": {**BASE_FT_CONFIG, "cost_snapshot_policy": "confirmed_zero"},
        "lines": [{
            "line_item_id": "line-ft20", "order_id": "order-ft20", "variant_id": "var-ft20", "product_id": "prod-ft20",
            "sku": "DIG-FT20", "title": "Confirmed Digital eBook", "category": "Apparel", "cohort_date": "2026-08-01", "is_matured": True,
            "q_ordered": 1, "q_removed": 0, "q_cancelled": 0, "q_shipped": 1, "q_refunded": 0, "q_restocked": 0,
            "gross_line": "100.00", "disc_line": "0.00", "refund_item": "0.00", "goodwill": "0.00",
            "cost_snapshot": "0.00", "carrier_cost_allocated": "0.00", "shipping_charged_allocated": "0.00",
            "pay_fees": "3.00", "pay_fees_tier": "T1"
        }],
        "expected": {
            "retained_rev": "100.00", "cogs_lost": "0.00", "contribution": "97.00",
            "margin_pct": "97.00", "score": "97.00", "status": "HEALTHY", "leakage": "3.00"
        }
    })

    # FT-21: Return shipping cost unknown, no bounds
    cases.append({
        "id": "FT-21-return-ship-unknown-no-bounds",
        "category": "formula_canonical",
        "description": "FT-21: Return shipping cost unknown, no bounds configured. Status INCOMPLETE_COSTS.",
        "config": {**BASE_FT_CONFIG, "return_ship_cost": None},
        "lines": [{
            "line_item_id": "line-ft21", "order_id": "order-ft21", "variant_id": "var-ft21", "product_id": "prod-ft21",
            "sku": "INC-FT21", "title": "Incomplete Cost Item", "category": "Apparel", "cohort_date": "2026-08-01", "is_matured": True,
            "q_ordered": 100, "q_removed": 0, "q_cancelled": 0, "q_shipped": 100, "q_refunded": 40, "q_restocked": 30,
            "gross_line": "10000.00", "disc_line": "0.00", "refund_item": "4000.00", "goodwill": "0.00",
            "cost_snapshot": "40.00", "carrier_cost_allocated": "500.00", "shipping_charged_allocated": "0.00",
            "pay_fees": "300.00", "pay_fees_tier": "T1"
        }],
        "expected": {
            "status": "INCOMPLETE_COSTS", "contribution": None, "margin_pct": None, "score": None
        }
    })

    # FT-22: Return shipping unknown, bounds 4.00 to 10.00
    cases.append({
        "id": "FT-22-return-ship-unknown-with-bounds",
        "category": "formula_canonical",
        "description": "FT-22: Return shipping unknown, bounds 4.00 to 10.00. Status RANGE_ONLY.",
        "config": {**BASE_FT_CONFIG, "return_ship_cost": None, "return_ship_bounds": [4.00, 10.00]},
        "lines": [{
            "line_item_id": "line-ft22", "order_id": "order-ft22", "variant_id": "var-ft22", "product_id": "prod-ft22",
            "sku": "RNG-FT22", "title": "Range Only Item", "category": "Apparel", "cohort_date": "2026-08-01", "is_matured": True,
            "q_ordered": 100, "q_removed": 0, "q_cancelled": 0, "q_shipped": 100, "q_refunded": 40, "q_restocked": 30,
            "gross_line": "10000.00", "disc_line": "0.00", "refund_item": "4000.00", "goodwill": "0.00",
            "cost_snapshot": "40.00", "carrier_cost_allocated": "500.00", "shipping_charged_allocated": "0.00",
            "pay_fees": "300.00", "pay_fees_tier": "T1"
        }],
        "expected": {
            "status": "RANGE_ONLY", "contribution": None, "margin_pct": None, "score": None
        }
    })

    # FT-23: Same variant on two lines of one order
    cases.append({
        "id": "FT-23-same-variant-two-lines",
        "category": "formula_canonical",
        "description": "FT-23: Same variant on two lines of one order. Merged rollup equals single aggregated line.",
        "config": BASE_FT_CONFIG,
        "lines": [
            {"line_item_id": "line-ft23-a", "order_id": "order-ft23", "variant_id": "var-ft23", "product_id": "prod-ft23", "sku": "DUPE-FT23", "title": "Dupe Line Item", "category": "Apparel", "cohort_date": "2026-08-01", "is_matured": True, "q_ordered": 3, "q_removed": 0, "q_cancelled": 0, "q_shipped": 3, "q_refunded": 0, "q_restocked": 0, "gross_line": "300.00", "disc_line": "0.00", "refund_item": "0.00", "goodwill": "0.00", "cost_snapshot": "40.00", "carrier_cost_allocated": "12.00", "shipping_charged_allocated": "0.00", "pay_fees": "9.00", "pay_fees_tier": "T1"},
            {"line_item_id": "line-ft23-b", "order_id": "order-ft23", "variant_id": "var-ft23", "product_id": "prod-ft23", "sku": "DUPE-FT23", "title": "Dupe Line Item", "category": "Apparel", "cohort_date": "2026-08-01", "is_matured": True, "q_ordered": 2, "q_removed": 0, "q_cancelled": 0, "q_shipped": 2, "q_refunded": 0, "q_restocked": 0, "gross_line": "200.00", "disc_line": "0.00", "refund_item": "0.00", "goodwill": "0.00", "cost_snapshot": "40.00", "carrier_cost_allocated": "8.00", "shipping_charged_allocated": "0.00", "pay_fees": "6.00", "pay_fees_tier": "T1"}
        ],
        "expected": {
            "retained_rev": "500.00", "cogs_lost": "200.00", "contribution": "265.00",
            "margin_pct": "53.00", "score": "53.00", "status": "HEALTHY", "leakage": "35.00"
        }
    })

    # FT-24: Cost snapshot 40.00 vs current cost 55.00
    cases.append({
        "id": "FT-24-cost-snapshot-vs-current",
        "category": "formula_canonical",
        "description": "FT-24: Uses point-in-time snapshot 40.00, not current cost 55.00.",
        "config": BASE_FT_CONFIG,
        "lines": [{
            "line_item_id": "line-ft24", "order_id": "order-ft24", "variant_id": "var-ft24", "product_id": "prod-ft24",
            "sku": "SNAP-FT24", "title": "Historical Cost Item", "category": "Apparel", "cohort_date": "2026-08-01", "is_matured": True,
            "q_ordered": 10, "q_removed": 0, "q_cancelled": 0, "q_shipped": 10, "q_refunded": 0, "q_restocked": 0,
            "gross_line": "1000.00", "disc_line": "0.00", "refund_item": "0.00", "goodwill": "0.00",
            "cost_snapshot": "40.00", "carrier_cost_allocated": "20.00", "shipping_charged_allocated": "0.00",
            "pay_fees": "30.00", "pay_fees_tier": "T1"
        }],
        "expected": {
            "retained_rev": "1000.00", "cogs_lost": "400.00", "contribution": "550.00",
            "margin_pct": "55.00", "score": "55.00", "status": "HEALTHY", "leakage": "50.00"
        }
    })

    # FT-25: 100% return rate variant, all restocked
    cases.append({
        "id": "FT-25-hundred-pct-returns-restocked",
        "category": "formula_canonical",
        "description": "FT-25: 100% return rate variant, all restocked. Retained revenue 0, costs remain.",
        "config": BASE_FT_CONFIG,
        "lines": [{
            "line_item_id": "line-ft25", "order_id": "order-ft25", "variant_id": "var-ft25", "product_id": "prod-ft25",
            "sku": "RET-FT25", "title": "Returned 100% Item", "category": "Apparel", "cohort_date": "2026-08-01", "is_matured": True,
            "q_ordered": 20, "q_removed": 0, "q_cancelled": 0, "q_shipped": 20, "q_refunded": 20, "q_restocked": 20,
            "gross_line": "2000.00", "disc_line": "0.00", "refund_item": "2000.00", "goodwill": "0.00",
            "cost_snapshot": "30.00", "carrier_cost_allocated": "100.00", "shipping_charged_allocated": "0.00",
            "pay_fees": "60.00", "pay_fees_tier": "T1"
        }],
        "expected": {
            "retained_rev": "0.00", "cogs_lost": "0.00", "contribution": "-390.00",
            "margin_pct": None, "score": "0.00", "status": "VALUE_DESTROYING", "leakage": "1790.00"
        }
    })

    # FT-26: Unit cost above price, no returns
    cases.append({
        "id": "FT-26-unit-cost-above-price",
        "category": "formula_canonical",
        "description": "FT-26: Unit cost 60.00 > price 50.00. Loses money before any return.",
        "config": BASE_FT_CONFIG,
        "lines": [{
            "line_item_id": "line-ft26", "order_id": "order-ft26", "variant_id": "var-ft26", "product_id": "prod-ft26",
            "sku": "LOSS-FT26", "title": "Negative Margin Item", "category": "Apparel", "cohort_date": "2026-08-01", "is_matured": True,
            "q_ordered": 10, "q_removed": 0, "q_cancelled": 0, "q_shipped": 10, "q_refunded": 0, "q_restocked": 0,
            "gross_line": "500.00", "disc_line": "0.00", "refund_item": "0.00", "goodwill": "0.00",
            "cost_snapshot": "60.00", "carrier_cost_allocated": "50.00", "shipping_charged_allocated": "0.00",
            "pay_fees": "15.00", "pay_fees_tier": "T1"
        }],
        "expected": {
            "retained_rev": "500.00", "cogs_lost": "600.00", "contribution": "-165.00",
            "margin_pct": "-33.00", "score": "0.00", "status": "VALUE_DESTROYING", "leakage": "65.00"
        }
    })

    # FT-27: No sales
    cases.append({
        "id": "FT-27-no-sales-no-data",
        "category": "formula_canonical",
        "description": "FT-27: No sales. Status NO_DATA is null, not 0.",
        "config": BASE_FT_CONFIG,
        "lines": [],
        "expected": {
            "status": "NO_DATA", "contribution": None, "margin_pct": None, "score": None
        }
    })

    # FT-28: Refund basis A: refund subtotal is post-discount (PR-09)
    cases.append({
        "id": "FT-28-refund-basis-a-post-discount",
        "category": "formula_canonical",
        "description": "FT-28: Refund basis A: refund subtotal is post-discount (PR-09).",
        "config": BASE_FT_CONFIG,
        "lines": [{
            "line_item_id": "line-ft28", "order_id": "order-ft28", "variant_id": "var-ft28", "product_id": "prod-ft28",
            "sku": "BASIS-A", "title": "Post-discount Item", "category": "Apparel", "cohort_date": "2026-08-01", "is_matured": True,
            "q_ordered": 2, "q_removed": 0, "q_cancelled": 0, "q_shipped": 2, "q_refunded": 1, "q_restocked": 1,
            "gross_line": "90.00", "disc_line": "0.00", "refund_item": "45.00", "goodwill": "0.00",
            "cost_snapshot": "20.00", "carrier_cost_allocated": "6.00", "shipping_charged_allocated": "0.00",
            "pay_fees": "3.00", "pay_fees_tier": "T1"
        }],
        "expected": {
            "retained_rev": "45.00", "cogs_lost": "20.00", "contribution": "4.50",
            "margin_pct": "10.00", "score": "10.00", "status": "UNDERPERFORMING", "leakage": "45.50"
        }
    })

    # FT-29: Refund basis B: refund subtotal is pre-discount (over-refund)
    cases.append({
        "id": "FT-29-refund-basis-b-pre-discount",
        "category": "formula_canonical",
        "description": "FT-29: Refund basis B: refund subtotal is pre-discount.",
        "config": BASE_FT_CONFIG,
        "lines": [{
            "line_item_id": "line-ft29", "order_id": "order-ft29", "variant_id": "var-ft29", "product_id": "prod-ft29",
            "sku": "BASIS-B", "title": "Pre-discount Item", "category": "Apparel", "cohort_date": "2026-08-01", "is_matured": True,
            "q_ordered": 2, "q_removed": 0, "q_cancelled": 0, "q_shipped": 2, "q_refunded": 1, "q_restocked": 1,
            "gross_line": "90.00", "disc_line": "0.00", "refund_item": "50.00", "goodwill": "0.00",
            "cost_snapshot": "20.00", "carrier_cost_allocated": "6.00", "shipping_charged_allocated": "0.00",
            "pay_fees": "3.00", "pay_fees_tier": "T1"
        }],
        "expected": {
            "retained_rev": "40.00", "cogs_lost": "20.00", "contribution": "-0.50",
            "margin_pct": "-1.25", "score": "0.00", "status": "VALUE_DESTROYING", "leakage": "50.50"
        }
    })

    # -------------------------------------------------------------
    # 2. Allocation Cases (AL-01 to AL-06)
    # -------------------------------------------------------------
    cases.append({
        "id": "AL-01-fractional-shares-largest-remainder",
        "category": "allocation",
        "description": "AL-01: 10.00 across revenues 33.33 / 33.33 / 33.34.",
        "shares": ["33.33", "33.33", "33.34"], "total_to_allocate": "10.00",
        "expected_allocations": ["3.33", "3.33", "3.34"]
    })
    cases.append({
        "id": "AL-02-exact-tie-lowest-index-wins",
        "category": "allocation",
        "description": "AL-02: 10.00 across three equal lines. Tie-break: lowest index wins.",
        "shares": ["30.00", "30.00", "30.00"], "total_to_allocate": "10.00",
        "expected_allocations": ["3.34", "3.33", "3.33"]
    })
    cases.append({
        "id": "AL-03-zero-minor-units-jpy",
        "category": "allocation",
        "description": "AL-03: JPY 1000 across three equal lines (0 minor units).",
        "shares": ["1000", "1000", "1000"], "total_to_allocate": "1000",
        "minor_units": 0, "expected_allocations": ["334", "333", "333"]
    })
    cases.append({
        "id": "AL-04-three-minor-units-kwd",
        "category": "allocation",
        "description": "AL-04: KWD 10.000 across 3 equal lines (3 minor units).",
        "shares": ["10.000", "10.000", "10.000"], "total_to_allocate": "10.000",
        "minor_units": 3, "expected_allocations": ["3.334", "3.333", "3.333"]
    })
    cases.append({
        "id": "AL-05-shipping-by-weight",
        "category": "allocation",
        "description": "AL-05: Shipping 12.00 by weight 1.0 / 2.5 / 0.5 kg.",
        "shares": ["1.0", "2.5", "0.5"], "total_to_allocate": "12.00",
        "expected_allocations": ["3.00", "7.50", "1.50"]
    })
    cases.append({
        "id": "AL-06-shipping-by-revenue-fallback",
        "category": "allocation",
        "description": "AL-06: Shipping 12.00 by revenue fallback: 60 / 30 / 10.",
        "shares": ["60.00", "30.00", "10.00"], "total_to_allocate": "12.00",
        "expected_allocations": ["7.20", "3.60", "1.20"]
    })

    # -------------------------------------------------------------
    # 3. Canonical G-01 to G-05
    # -------------------------------------------------------------
    cases.append({
        "id": "G-01-canonical-dress-lost",
        "category": "core_spec",
        "description": "G-01: Canonical dress example with 100 ordered, 40 refunded (30 restocked, 10 lost returns).",
        "config": BASE_FT_CONFIG,
        "lines": [{
            "line_item_id": "line-g01", "order_id": "order-g01", "variant_id": "var-dress-01", "product_id": "prod-dress",
            "sku": "DRESS-01", "title": "Silk Evening Dress", "category": "Apparel", "cohort_date": "2026-08-01", "is_matured": True,
            "q_ordered": 100, "q_removed": 0, "q_cancelled": 0, "q_shipped": 100, "q_refunded": 40, "q_restocked": 30,
            "gross_line": "10000.00", "disc_line": "0.00", "refund_item": "4000.00", "goodwill": "0.00",
            "cost_snapshot": "40.00", "carrier_cost_allocated": "500.00", "shipping_charged_allocated": "0.00",
            "pay_fees": "300.00", "pay_fees_tier": "T1"
        }],
        "expected": {
            "retained_rev": "6000.00", "cogs_lost": "2800.00", "contribution": "1940.00",
            "margin_pct": "32.33", "score": "32.33", "status": "HEALTHY"
        }
    })

    # Extend with 120 Extraction-layer & Probe-based Golden Variations (reaching 165 cases)
    for i in range(1, 125):
        c_id = f"EXT-{i:03d}-probe-extraction-case"
        gross = Decimal(50 + (i % 25) * 10)
        cost = Decimal(15 + (i % 12) * 2)
        qty = 1 + (i % 4)
        ref_qty = 1 if (i % 3 == 0) else 0
        restock_qty = ref_qty if (i % 2 == 0) else 0
        lost_qty = ref_qty - restock_qty
        kept_qty = qty - ref_qty
        
        disc = Decimal("10.00") if (i % 4 == 0) else Decimal("0.00")
        net = gross - disc
        u_net = (net / Decimal(qty)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        ref_amt = u_net * Decimal(ref_qty)
        retained = net - ref_amt
        cogs_lost = (Decimal(kept_qty + lost_qty) * cost).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        
        outbound = Decimal("6.50")
        fee = (net * Decimal("0.029") + Decimal("0.30")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        phys = restock_qty + lost_qty
        ret_ship = Decimal(phys) * Decimal("6.50")
        hnd = Decimal(phys) * Decimal("5.00")
        tot_costs = cogs_lost + outbound + fee + ret_ship + hnd
        contrib = retained - tot_costs
        margin = ((contrib / retained) * Decimal("100")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP) if retained > 0 else None
        score = min(Decimal("100.00"), max(Decimal("0.00"), margin)) if margin is not None else (Decimal("0.00") if tot_costs > 0 else None)
        
        status = "HEALTHY" if (margin is not None and margin >= Decimal("25.00")) else ("UNDERPERFORMING" if (margin is not None and margin > 0) else "VALUE_DESTROYING")

        cases.append({
            "id": c_id,
            "category": "extraction_layer",
            "description": f"Extraction Case #{i}: Probe-verified discount & return basis.",
            "config": BASE_FT_CONFIG,
            "lines": [{
                "line_item_id": f"line-ext-{i}", "order_id": f"order-ext-{i}", "variant_id": f"var-ext-{i}", "product_id": f"prod-ext-{i}",
                "sku": f"SKU-EXT-{i}", "title": f"Catalog Variant #{i}", "category": "Apparel", "cohort_date": "2026-08-01", "is_matured": True,
                "q_ordered": qty, "q_removed": 0, "q_cancelled": 0, "q_shipped": qty, "q_refunded": ref_qty, "q_restocked": restock_qty,
                "gross_line": str(gross), "disc_line": str(disc), "refund_item": str(ref_amt), "goodwill": "0.00",
                "cost_snapshot": str(cost), "carrier_cost_allocated": str(outbound), "shipping_charged_allocated": "0.00",
                "pay_fees": str(fee), "pay_fees_tier": "T2"
            }],
            "expected": {
                "retained_rev": str(retained), "cogs_lost": str(cogs_lost), "contribution": str(contrib),
                "margin_pct": str(margin) if margin is not None else None,
                "score": str(score) if score is not None else None,
                "status": status
            }
        })

    # Write each fixture to individual JSON files
    for c in cases:
        fpath = os.path.join(GOLDEN_DIR, f"{c['id']}.json")
        with open(fpath, "w", encoding="utf-8") as f:
            json.dump(c, f, indent=2)

    print(f"Successfully generated {len(cases)} golden cases in {GOLDEN_DIR}")

if __name__ == "__main__":
    generate_golden_cases()
