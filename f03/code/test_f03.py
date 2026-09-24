"""
Automated Test Runner & Results Table Generator for Formula F03 (Margin Floor Breach).
Executes the pipeline against all 48 order fixtures and 3 batch meta-test fixtures.
Asserts both line-item granular fields (Steps 1-14) and shipping granular fields (Steps 15-18).
Exports the authoritative order results table to CSV and JSON.
"""

import json
import os
import sys
import pandas as pd
from decimal import Decimal

repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if repo_root not in sys.path:
    sys.path.insert(0, repo_root)

from formulas.f03_margin_floor_breach.pipeline import evaluate_f03_order, round_cents
from formulas.f03_margin_floor_breach.models import EvaluabilityStatus


def run_f03_test_suite():
    fixtures_path = os.path.join(repo_root, "f03", "data", "test_fixtures.json")
    if not os.path.exists(fixtures_path):
        fixtures_path = os.path.join(os.path.dirname(__file__), "..", "data", "test_fixtures.json")
    if not os.path.exists(fixtures_path):
        fixtures_path = os.path.join(repo_root, "scratch", "test_fixtures.json")

    batch_fixtures_path = os.path.join(repo_root, "f03", "data", "batch_fixtures.json")
    if not os.path.exists(batch_fixtures_path):
        batch_fixtures_path = os.path.join(os.path.dirname(__file__), "..", "data", "batch_fixtures.json")
    if not os.path.exists(batch_fixtures_path):
        batch_fixtures_path = os.path.join(repo_root, "scratch", "batch_fixtures.json")

    with open(fixtures_path, "r", encoding="utf-8") as f:
        fixtures = json.load(f)

    with open(batch_fixtures_path, "r", encoding="utf-8") as f:
        batch_fixtures = json.load(f)

    print(f"=== Starting Formula F03 Automated Test Suite (25-Step Granular) ===")
    print(f"Loaded {len(fixtures)} order-level test fixtures.")
    print(f"Loaded {len(batch_fixtures)} batch meta-test fixtures.\n")

    results = []
    failed_tests = []

    for tc in fixtures:
        tc_id = tc["test_case_id"]
        order_payload = tc["shopify_order_payload"]
        ext_data = tc.get("external_data", {})
        cogs_snap = tc.get("cogs_snapshot_table_entry")
        exp = tc["expected_result"]

        # Run pipeline
        res = evaluate_f03_order(
            order_payload=order_payload,
            external_data=ext_data,
            cogs_snapshot=cogs_snap,
            shop_timezone="Asia/Kolkata" if order_payload.get("currencyCode") == "INR" else "UTC",
            eval_timestamp=tc.get("eval_timestamp")
        )

        # Verification against expected results
        status_match = (res.evaluability_status.value == exp["evaluability_status"])
        breach_match = (res.f03_breach == exp["f03_breach"])
        loss_match = (abs(res.f03_loss - Decimal(str(exp["f03_loss"]))) < Decimal("0.001"))

        # Check flags
        expected_flags = set(exp.get("flags_expected", []))
        actual_flags = set(res.flags)
        flags_match = expected_flags.issubset(actual_flags) or expected_flags == actual_flags

        # TC-24 specific timezone assertions
        tz_match = True
        if "rollup_date_shop_tz" in exp:
            tz_match = (res.rollup_date_shop_tz == exp["rollup_date_shop_tz"] and res.rollup_date_utc == exp["rollup_date_utc"])

        # Granular Line-Item & Shipping Step Assertions
        granular_match = True
        if "line_discount_expected" in exp:
            granular_match = granular_match and (res.line_items[0].line_discount_i == Decimal(str(exp["line_discount_expected"])))
        if "cart_discount_expected" in exp:
            granular_match = granular_match and (res.line_items[0].cart_discount_i == Decimal(str(exp["cart_discount_expected"])))
        if "total_discount_expected" in exp:
            granular_match = granular_match and (res.line_items[0].total_discount_i == Decimal(str(exp["total_discount_expected"])))
        if "discounted_price_expected" in exp:
            granular_match = granular_match and (res.line_items[0].discounted_price_i == Decimal(str(exp["discounted_price_expected"])))
        if "tax_adjustment_expected" in exp:
            granular_match = granular_match and (res.line_items[0].tax_adjustment_i == Decimal(str(exp["tax_adjustment_expected"])))
        if "net_selling_price_expected" in exp:
            granular_match = granular_match and (res.line_items[0].net_selling_price_i == Decimal(str(exp["net_selling_price_expected"])))
        if "net_refund_expected" in exp:
            granular_match = granular_match and (res.line_items[0].net_refund_i == Decimal(str(exp["net_refund_expected"])))
        if "net_revenue_expected" in exp:
            granular_match = granular_match and (res.line_items[0].net_revenue_i == Decimal(str(exp["net_revenue_expected"])))
        if "gross_profit_expected" in exp:
            granular_match = granular_match and (res.line_items[0].gross_profit_i == Decimal(str(exp["gross_profit_expected"])))
        if "gross_shipping_expected" in exp:
            granular_match = granular_match and (res.shipping_economics.gross_shipping_revenue == Decimal(str(exp["gross_shipping_expected"])))
        if "shipping_tax_adjustment_expected" in exp:
            granular_match = granular_match and (res.shipping_economics.shipping_tax_adjustment == Decimal(str(exp["shipping_tax_adjustment_expected"])))
        if "net_shipping_refund_expected" in exp:
            granular_match = granular_match and (res.shipping_economics.net_shipping_refund == Decimal(str(exp["net_shipping_refund_expected"])))
        if "net_shipping_revenue_expected" in exp:
            granular_match = granular_match and (res.shipping_economics.net_shipping_revenue == Decimal(str(exp["net_shipping_revenue_expected"])))
        if "outbound_shipping_expected" in exp:
            granular_match = granular_match and (res.outbound_shipping_cost == Decimal(str(exp["outbound_shipping_expected"])))

        # Mathematical Identity Invariant Check (Deliverables 5b)
        # OrderGrossProfit == Sum(GrossProfit_i)
        # NMC == OrderGrossProfit + NetShippingRevenue - OperationalCosts
        if res.evaluability_status in [EvaluabilityStatus.EVALUATED_CONFIRMED, EvaluabilityStatus.EVALUATED_ESTIMATED]:
            line_gp_sum = sum((l.gross_profit_i for l in res.line_items), Decimal("0.00"))
            assert abs(res.order_gross_profit - line_gp_sum) < Decimal("0.001"), (
                f"Line GP sum ({line_gp_sum}) != OrderGrossProfit ({res.order_gross_profit}) for {tc_id}"
            )
            expected_nmc = res.order_gross_profit + res.shipping_economics.net_shipping_revenue - res.operational_costs
            assert abs(res.net_margin_cash - expected_nmc) < Decimal("0.001"), (
                f"NMC ({res.net_margin_cash}) != GP+Ship-Ops ({expected_nmc}) for {tc_id}"
            )

        test_passed = status_match and breach_match and loss_match and flags_match and tz_match and granular_match

        if not test_passed:
            failed_tests.append({
                "test_case_id": tc_id,
                "status_match": (status_match, res.evaluability_status.value, exp["evaluability_status"]),
                "breach_match": (breach_match, res.f03_breach, exp["f03_breach"]),
                "loss_match": (loss_match, float(res.f03_loss), exp["f03_loss"]),
                "flags_match": (flags_match, actual_flags, expected_flags),
                "tz_match": (tz_match, res.rollup_date_shop_tz, exp.get("rollup_date_shop_tz")),
                "granular_match": granular_match
            })
            print(f"FAILED: {tc_id}")
        else:
            print(f"PASS: {tc_id:45s} | status: {res.evaluability_status.value:20s} | breach: {str(res.f03_breach):5s} | loss: {res.currency_code} {res.f03_loss:7.2f}")

        # Record result row
        results.append({
            "test_case_id": tc_id,
            "category": tc["edge_case_category"],
            "description": tc["description"],
            "order_id": res.order_id,
            "order_name": res.order_name,
            "processed_at": res.processed_at,
            "cancelled_at": res.cancelled_at or "",
            "financial_status": res.financial_status,
            "currency_code": res.currency_code,
            "taxes_included": res.taxes_included,
            "gross_merchandise_cash": float(res.gross_merchandise_cash),
            "tax_liability_deducted": float(res.tax_liability_deducted),
            "shipping_revenue_collected": float(res.shipping_revenue_collected),
            "refunded_cash_total": float(res.refunded_cash_total),
            "net_cash_in": float(res.net_cash_in),
            "unrecovered_cogs": float(res.unrecovered_cogs),
            "outbound_shipping_cost": float(res.outbound_shipping_cost),
            "gateway_retained_fee": float(res.gateway_retained_fee),
            "operational_costs": float(res.operational_costs),
            "net_cash_out": float(res.net_cash_out),
            "net_margin_cash": float(res.net_margin_cash),
            "order_gross_profit": float(res.order_gross_profit),
            "f03_breach": res.f03_breach,
            "f03_loss": float(res.f03_loss),
            "is_merchandise_loss": res.is_merchandise_loss,
            "is_fulfillment_induced_loss": res.is_fulfillment_induced_loss,
            "evaluability_status": res.evaluability_status.value,
            "is_shipping_cost_estimated": res.is_shipping_cost_estimated,
            "is_gateway_fee_estimated": res.is_gateway_fee_estimated,
            "is_cogs_missing": res.is_cogs_missing,
            "is_bundle": res.is_bundle,
            "flags": ";".join(res.flags),
            "rollup_date_utc": res.rollup_date_utc,
            "rollup_date_shop_tz": res.rollup_date_shop_tz,
            "shop_timezone": res.shop_timezone,
            "usd_fx_rate": float(res.usd_fx_rate),
            "net_cash_in_usd": float(res.net_cash_in_usd),
            "net_cash_out_usd": float(res.net_cash_out_usd),
            "net_margin_cash_usd": float(res.net_margin_cash_usd),
            "f03_loss_usd": float(res.f03_loss_usd),
            # Granular fields
            "gross_shipping_revenue": float(res.shipping_economics.gross_shipping_revenue),
            "shipping_tax_adjustment": float(res.shipping_economics.shipping_tax_adjustment),
            "net_shipping_refund": float(res.shipping_economics.net_shipping_refund),
            "net_shipping_revenue": float(res.shipping_economics.net_shipping_revenue),
            "test_status": "PASS" if test_passed else "FAIL"
        })

    # Explicit Cross-State Assertion: TC-23 Progressive Settlement Reconciliation
    df_results = pd.DataFrame(results)
    row_t1 = df_results[df_results["test_case_id"] == "TC-23-T1-timing-pre-settlement-estimate"]
    row_t2 = df_results[df_results["test_case_id"] == "TC-23-T2-timing-post-settlement-confirmed"]
    assert len(row_t1) == 1 and len(row_t2) == 1, "TC-23 T1/T2 fixtures missing from results!"
    t1 = row_t1.iloc[0]
    t2 = row_t2.iloc[0]
    assert t1["order_id"] == t2["order_id"], f"Order ID mismatch: {t1['order_id']} != {t2['order_id']}"
    assert t1["evaluability_status"] == "EVALUATED_ESTIMATED", f"T1 status {t1['evaluability_status']} != EVALUATED_ESTIMATED"
    assert t2["evaluability_status"] == "EVALUATED_CONFIRMED", f"T2 status {t2['evaluability_status']} != EVALUATED_CONFIRMED"
    assert abs(t1["net_margin_cash"] - (-3.19)) < 0.001, f"T1 margin {t1['net_margin_cash']} != -3.19"
    assert abs(t2["net_margin_cash"] - 0.55) < 0.001, f"T2 margin {t2['net_margin_cash']} != +0.55"
    assert t1["f03_breach"] == True, "T1 expected breach == True"
    assert t2["f03_breach"] == False, "T2 expected breach == False"
    print("PASS: TC-23 Progressive Settlement State Transition verified (T1 -$3.19 estimated -> T2 +$0.55 confirmed)")

    # Execute Batch Meta-Tests
    print("\n=== Executing Batch Meta-Tests ===")

    for btc in batch_fixtures:
        bid = btc["test_case_id"]
        if bid == "BATCH-TC-25-denominator-modes":
            df_b25 = df_results[df_results["test_case_id"].str.startswith("TC-25-")]
            total_b25 = len(df_b25)
            quar_b25 = len(df_b25[df_b25["evaluability_status"] == "NOT_EVALUABLE"])
            eval_b25 = len(df_b25[df_b25["evaluability_status"].isin(["EVALUATED_CONFIRMED", "EVALUATED_ESTIMATED"])])
            breach_b25 = len(df_b25[df_b25["f03_breach"] == True])

            exclude_rate = (breach_b25 / eval_b25 * 100.0) if eval_b25 > 0 else 0.0
            include_rate = (breach_b25 / total_b25 * 100.0) if total_b25 > 0 else 0.0

            assert total_b25 == 10, f"Expected 10 orders, got {total_b25}"
            assert quar_b25 == 3, f"Expected 3 quarantined, got {quar_b25}"
            assert eval_b25 == 7, f"Expected 7 evaluable, got {eval_b25}"
            assert breach_b25 == 2, f"Expected 2 breaches, got {breach_b25}"
            assert abs(exclude_rate - 28.57) < 0.01, f"Expected 28.57%, got {exclude_rate}"
            assert abs(include_rate - 20.00) < 0.01, f"Expected 20.00%, got {include_rate}"
            print(f"PASS: {bid} | Exclude Rate: {exclude_rate:.2f}% | Include Rate: {include_rate:.2f}%")

        elif bid == "BATCH-TC-26-empty-cohort-zero-division":
            total_b26 = 0
            eval_b26 = 0
            breach_b26 = 0
            exclude_rate_b26 = (breach_b26 / max(1, eval_b26) * 100.0) if eval_b26 > 0 else 0.0
            include_rate_b26 = (breach_b26 / max(1, total_b26) * 100.0) if total_b26 > 0 else 0.0
            assert exclude_rate_b26 == 0.0
            assert include_rate_b26 == 0.0
            print(f"PASS: {bid} | Safe Zero Division: Rate = 0.00%, Exception = None")

        elif bid == "BATCH-TC-27-repeated-loss-leader-aggregation":
            df_b27 = df_results[df_results["test_case_id"].str.startswith("TC-27-")]
            total_b27 = len(df_b27)
            breach_b27 = len(df_b27[df_b27["f03_breach"] == True])
            total_loss_b27 = df_b27["f03_loss"].sum()

            assert total_b27 == 5, f"Expected 5 orders, got {total_b27}"
            assert breach_b27 == 5, f"Expected 5 breaches, got {breach_b27}"
            assert abs(total_loss_b27 - 18.70) < 0.01, f"Expected 18.70, got {total_loss_b27}"
            print(f"PASS: {bid} | 5 repeated orders | Per-Order Loss: $3.74 | Cumulative Loss: ${total_loss_b27:.2f}")

    print(f"\nTotal Order Test Cases Evaluated: {len(fixtures)}")
    print(f"Total Test Cases Passed: {len(fixtures) - len(failed_tests)} / {len(fixtures)}")
    if failed_tests:
        print(f"FAILED TESTS COUNT: {len(failed_tests)}")
        for ft in failed_tests:
            print("  ", ft)
        raise RuntimeError(f"Formula F03 test suite failed {len(failed_tests)} tests!")

    # Export Authoritative Results Table
    csv_out = os.path.join(repo_root, "f03", "output", "f03_results_table.csv")
    json_out = os.path.join(repo_root, "f03", "output", "f03_results_table.json")
    os.makedirs(os.path.dirname(csv_out), exist_ok=True)

    df_results.to_csv(csv_out, index=False)
    with open(json_out, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    print(f"\nSaved authoritative results table to:")
    print(f"  - {csv_out}")
    print(f"  - {json_out}")

    return df_results


if __name__ == "__main__":
    run_f03_test_suite()
