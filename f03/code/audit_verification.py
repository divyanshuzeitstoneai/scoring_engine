"""
Comprehensive Independent Verification Script for Formula F03 (Canonical 25-Step Specification).
Audits all 6 Bug Fixes (Bugs A through F), the 3 Audit Enhancements (TC-19 nesting, TC-23 T1/T2 states, FX conservation),
and Core Mathematical Invariants.
"""

from decimal import Decimal
import os
import re
import sys
import pandas as pd

repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if repo_root not in sys.path:
    sys.path.insert(0, repo_root)

report_path = os.path.join(repo_root, "f03", "output", "F03_MARGIN_FLOOR_BREACH_VALIDATION_REPORT.md")
if not os.path.exists(report_path):
    report_path = os.path.join(repo_root, "F03_MARGIN_FLOOR_BREACH_VALIDATION_REPORT.md")

results_path = os.path.join(repo_root, "f03", "output", "f03_results_table.csv")
if not os.path.exists(results_path):
    results_path = os.path.join(repo_root, "scratch", "f03_results_table.csv")

with open(report_path, "r", encoding="utf-8") as f:
    report_text = f.read()

df = pd.read_csv(results_path)
eval_df = df[df["evaluability_status"].isin(["EVALUATED_CONFIRMED", "EVALUATED_ESTIMATED"])]

print("=" * 80)
print("AUDIT VERIFICATION RUN: CANONICAL 25-STEP SPECIFICATION & AUDIT FINDINGS")
print("=" * 80)

# -------------------------------------------------------------
# AUDIT CHECK 1: BUG A — Penny-Level Precision Invariant
# -------------------------------------------------------------
inflow_match = re.search(r"\*\*Total Cash Inflow \(Net Receipts, USD Equiv\)\*\* \|\s*\*\*\$([0-9,.]+)\*\*", report_text)
outflow_match = re.search(r"\*\*Total Direct Cash Outflow \(USD Equiv\)\*\* \|\s*\*\*\$([0-9,.]+)\*\*", report_text)
margin_match = re.search(r"\*\*Total Realized Net Cash Margin \(USD Equiv\)\*\* \|\s*\*\*([+-]?\$[0-9,.]+)\*\*", report_text)

inflow_val = Decimal(inflow_match.group(1).replace(",", ""))
outflow_val = Decimal(outflow_match.group(1).replace(",", ""))
margin_str = margin_match.group(1).replace(",", "").replace("$", "")
margin_val = Decimal(margin_str)

penny_diff = abs(inflow_val - outflow_val - margin_val)
print(f"\n[CHECK 1 - BUG A] Exact Cent Decimal Precision:")
print(f"  - Extracted Total Cash Inflow:  ${inflow_val}")
print(f"  - Extracted Total Cash Outflow: ${outflow_val}")
print(f"  - Extracted Net Cash Margin:    ${margin_val}")
print(f"  - Difference (Inflow - Outflow - Margin): ${penny_diff}")
assert penny_diff < Decimal("0.005"), f"BUG A FAILED: Discrepancy ${penny_diff} exceeds 0.005!"
print(f"  --> RESULT: PASS (Zero penny discrepancy: Inflow - Outflow = Margin identical to the cent)")

# -------------------------------------------------------------
# AUDIT CHECK 2: BUG B — FILTERED_TEST_ORDER Sandbox Exclusion
# -------------------------------------------------------------
tc30_rows = df[df["test_case_id"] == "TC-30-sandbox-test-order-filtered"]
print(f"\n[CHECK 2 - BUG B] Sandbox Test Order Routing (order.test == true):")
assert len(tc30_rows) == 1, "BUG B FAILED: TC-30 not found in results table"
tc30_row = tc30_rows.iloc[0]
tc30_status = tc30_row["evaluability_status"]
assert tc30_status == "FILTERED_TEST_ORDER", f"BUG B FAILED: Expected FILTERED_TEST_ORDER, got {tc30_status}"
assert tc30_row["order_id"] not in eval_df["order_id"].values, "BUG B FAILED: TC-30 leaked into evaluated commercial volume"
assert tc30_row["f03_breach"] == False, "BUG B FAILED: TC-30 marked as breach"
assert tc30_row["f03_loss"] == 0.0, "BUG B FAILED: TC-30 has non-zero loss"
print(f"  - TC-30 Status: {tc30_status} (Excluded from commercial & evaluable denominators)")
print(f"  --> RESULT: PASS (Sandbox test order active fixture verified)")

# -------------------------------------------------------------
# AUDIT CHECK 3: BUG C — Granular Steps & Tax Consistency (TC-31 to TC-34)
# -------------------------------------------------------------
print(f"\n[CHECK 3 - BUG C] Granular Formula Isolation & Tax Consistency:")
tc31 = df[df["test_case_id"] == "TC-31-stacked-line-and-cart-discounts"].iloc[0]
tc32 = df[df["test_case_id"] == "TC-32-tax-inclusive-partial-refund-isolated"].iloc[0]
tc33 = df[df["test_case_id"] == "TC-33-shipping-tax-inclusive-isolated"].iloc[0]
tc34 = df[df["test_case_id"] == "TC-34-shipping-refund-isolated"].iloc[0]

# TC-31 stacked discounts
assert tc31["test_status"] == "PASS", "TC-31 failed"
print(f"  - TC-31 (Stacked Line + Cart Discounts): PASS")

# TC-32 tax consistency in partial refunds
assert tc32["test_status"] == "PASS", "TC-32 failed"
print(f"  - TC-32 (Tax-Consistent Partial Refund): PASS")

# TC-33 tax-inclusive shipping line
assert tc33["test_status"] == "PASS", "TC-33 failed"
assert tc33["shipping_tax_adjustment"] == 2.0, f"TC-33 shipping tax adjustment {tc33['shipping_tax_adjustment']} != 2.0"
print(f"  - TC-33 (Tax-Inclusive Shipping Line Extraction): PASS (Tax = $2.00)")

# TC-34 shipping-only refund
assert tc34["test_status"] == "PASS", "TC-34 failed"
assert tc34["net_shipping_refund"] == 10.0, f"TC-34 net shipping refund {tc34['net_shipping_refund']} != 10.0"
assert tc34["net_shipping_revenue"] == 0.0, f"TC-34 net shipping revenue {tc34['net_shipping_revenue']} != 0.0"
print(f"  - TC-34 (Standalone Shipping Refund Isolation): PASS (Net Shipping Refund = $10.00, Net Shipping Rev = $0.00)")
print(f"  --> RESULT: PASS (All 4 granular formula isolation fixtures verified)")

# -------------------------------------------------------------
# AUDIT CHECK 4: BUG D — COGS Waterfall Methodology (Option a: 4 Tiers)
# -------------------------------------------------------------
print(f"\n[CHECK 4 - BUG D] COGS Waterfall Tiers Verification:")
from formulas.f03_margin_floor_breach.pipeline import evaluate_f03_order
import json
tf_path = os.path.join(repo_root, "f03", "data", "test_fixtures.json")
if not os.path.exists(tf_path):
    tf_path = os.path.join(repo_root, "scratch", "test_fixtures.json")
with open(tf_path, "r", encoding="utf-8") as f:
    fixtures = json.load(f)

tiers_observed = set()
for fix in fixtures:
    res = evaluate_f03_order(
        order_payload=fix["shopify_order_payload"],
        external_data=fix.get("external_data"),
        cogs_snapshot=fix.get("cogs_snapshot_table_entry"),
        shop_timezone="Asia/Kolkata" if fix["shopify_order_payload"].get("currencyCode") == "INR" else "UTC",
        eval_timestamp=fix.get("eval_timestamp"),
        bom_mapping=fix.get("bom_mapping")
    )
    for l in res.line_items:
        if l.cogs_source_tier:
            tiers_observed.add(l.cogs_source_tier)

expected_tiers = {"Tier 1 (Snapshot)", "Tier 2 (Live Admin)", "Tier 3 (BOM Explosion)", "Tier 4 (Unresolved)"}
assert tiers_observed == expected_tiers, f"BUG D FAILED: Tiers {tiers_observed} != {expected_tiers}"
print(f"  - Observed COGS Sourcing Tiers: {sorted(list(tiers_observed))}")
print(f"  - Statistical fallback tiers (Product/Category/Storewide averages) rejected per Option (a).")
print(f"  --> RESULT: PASS (Exactly 4 auditable COGS tiers confirmed)")

# -------------------------------------------------------------
# AUDIT CHECK 5: BUG E — Batch Meta-Test Section Callout
# -------------------------------------------------------------
print(f"\n[CHECK 5 - BUG E] Batch Meta-Test Clarification Callout:")
callout_match = re.search(r"IMPORTANT AUDIT NOTE ON BATCH META-TESTS \(BUG E RESOLUTION\)", report_text)
assert callout_match is not None, "BUG E FAILED: Clarification callout not found in report"
assert "They are NOT a second storewide metric" in report_text, "BUG E FAILED: Warning text missing"
print(f"  - Section 8 Callout: Found and verified")
print(f"  --> RESULT: PASS (Batch meta-test disclaimer prevents metric confusion)")

# -------------------------------------------------------------
# AUDIT CHECK 6: BUG F — International Shipping Fallback Zone
# -------------------------------------------------------------
print(f"\n[CHECK 6 - BUG F] International Shipping Fallback Rate Table & Fixture:")
tc35_rows = df[df["test_case_id"] == "TC-35-international-shipping-fallback-zone"]
assert len(tc35_rows) == 1, "BUG F FAILED: TC-35 not found in results table"
tc35 = tc35_rows.iloc[0]
assert tc35["test_status"] == "PASS", "TC-35 failed"
assert tc35["outbound_shipping_cost"] == 14.50, f"BUG F FAILED: Outbound shipping {tc35['outbound_shipping_cost']} != 14.50"
assert tc35["evaluability_status"] == "EVALUATED_ESTIMATED", "BUG F FAILED: Evaluability status not EVALUATED_ESTIMATED"
assert "is_shipping_cost_estimated" in tc35["flags"], "BUG F FAILED: is_shipping_cost_estimated flag missing"
print(f"  - TC-35 Outbound Shipping Cost: ${tc35['outbound_shipping_cost']:.2f} (EU zone rate $14.50 applied)")
print(f"  - Evaluability Status: {tc35['evaluability_status']} (Flag: is_shipping_cost_estimated)")
print(f"  --> RESULT: PASS (Cross-border international fallback verified)")

# -------------------------------------------------------------
# AUDIT CHECK 7: AUDIT ENHANCEMENT 1 — TC-19 Mutually Exclusive Classification
# -------------------------------------------------------------
print(f"\n[CHECK 7 - ENHANCEMENT 1] Section 3 Breach Tree Mutual Exclusivity:")
merch_match = re.search(r"↳ \*Merchandise Negative Gross Profit\*\s*\|\s*\*(\d+)\s+Orders\*", report_text)
fulf_match = re.search(r"↳ \*Fulfillment & Fee Induced Breaches\*\s*\|\s*\*(\d+)\s+Orders\*", report_text)
claimed_merch = int(merch_match.group(1))
claimed_fulf = int(fulf_match.group(1))

actual_breaches = len(df[df["f03_breach"] == True])
recomputed_merch = len(df[(df["f03_breach"] == True) & (df["order_gross_profit"] < 0.00)])
recomputed_fulf = len(df[(df["f03_breach"] == True) & (df["order_gross_profit"] >= 0.00)])

assert claimed_merch == recomputed_merch == 3, f"Merchandise loss count mismatch: {claimed_merch} != {recomputed_merch}"
assert claimed_fulf == recomputed_fulf == 26, f"Fulfillment loss count mismatch: {claimed_fulf} != {recomputed_fulf}"
assert claimed_merch + claimed_fulf == actual_breaches == 29, f"Breach sum {claimed_merch + claimed_fulf} != {actual_breaches}"

# Verify TC-19 is nested under fulfillment breaches in Section 3 tree
tree_tc19_match = re.search(r"Fulfillment & Fee Induced Breaches:.*?Includes Boundary Deficit Case.*?\[TC-19\]", report_text, re.DOTALL)
assert tree_tc19_match is not None, "TC-19 is not properly nested under Fulfillment & Fee Induced Breaches in Section 3"
print(f"  - Merchandise Losses: {claimed_merch} Orders")
print(f"  - Fulfillment & Fee Losses: {claimed_fulf} Orders (strictly includes TC-19 boundary deficit)")
print(f"  - Sum: {claimed_merch + claimed_fulf} == Total Breaches {actual_breaches} (Zero double-count)")
print(f"  --> RESULT: PASS (Mutually exclusive classification verified)")

# -------------------------------------------------------------
# AUDIT CHECK 8: AUDIT ENHANCEMENT 2 — TC-23 Progressive Settlement States
# -------------------------------------------------------------
print(f"\n[CHECK 8 - ENHANCEMENT 2] TC-23 Progressive Settlement Re-Evaluation:")
tc23_t1_rows = df[df["test_case_id"] == "TC-23-T1-timing-pre-settlement-estimate"]
tc23_t2_rows = df[df["test_case_id"] == "TC-23-T2-timing-post-settlement-confirmed"]

assert len(tc23_t1_rows) == 1, "TC-23-T1 missing from results table"
assert len(tc23_t2_rows) == 1, "TC-23-T2 missing from results table"

t1 = tc23_t1_rows.iloc[0]
t2 = tc23_t2_rows.iloc[0]

assert t1["order_id"] == t2["order_id"], f"Order ID mismatch: {t1['order_id']} != {t2['order_id']}"
assert t1["evaluability_status"] == "EVALUATED_ESTIMATED", f"T1 status {t1['evaluability_status']} != EVALUATED_ESTIMATED"
assert t2["evaluability_status"] == "EVALUATED_CONFIRMED", f"T2 status {t2['evaluability_status']} != EVALUATED_CONFIRMED"
assert abs(t1["net_margin_cash"] - (-3.19)) < 0.001, f"T1 margin {t1['net_margin_cash']} != -3.19"
assert abs(t2["net_margin_cash"] - 0.55) < 0.001, f"T2 margin {t2['net_margin_cash']} != +0.55"
assert t1["f03_breach"] == True, "T1 expected breach == True"
assert t2["f03_breach"] == False, "T2 expected breach == False"

print(f"  - Same Order Verified: {t1['order_id']} ({t1['order_name']})")
print(f"  - State T1 (T+2h):  {t1['evaluability_status']} | NMC: ${t1['net_margin_cash']:.2f} | Breach: {t1['f03_breach']}")
print(f"  - State T2 (T+72h): {t2['evaluability_status']} | NMC: +${t2['net_margin_cash']:.2f} | Breach: {t2['f03_breach']}")
print(f"  --> RESULT: PASS (State transition from estimated breach to confirmed healthy proven)")

# -------------------------------------------------------------
# AUDIT CHECK 9: AUDIT ENHANCEMENT 3 — FX Consolidation Conservation (Check 9)
# -------------------------------------------------------------
print(f"\n[CHECK 9 - ENHANCEMENT 3] FX Consolidation Conservation Invariant:")
eval_rows = df[df["evaluability_status"].isin(["EVALUATED_CONFIRMED", "EVALUATED_ESTIMATED"])]

sum_order_inflow_usd = Decimal(str(round(eval_rows["net_cash_in_usd"].sum(), 2)))
sum_order_outflow_usd = Decimal(str(round(eval_rows["net_cash_out_usd"].sum(), 2)))
sum_order_margin_usd = Decimal(str(round(eval_rows["net_margin_cash_usd"].sum(), 2)))
sum_order_loss_usd = Decimal(str(round(eval_rows[eval_rows["f03_breach"] == True]["f03_loss_usd"].sum(), 2)))

print(f"  - Sum of Per-Order Converted Inflow USD:  ${sum_order_inflow_usd}")
print(f"  - Sum of Per-Order Converted Outflow USD: ${sum_order_outflow_usd}")
print(f"  - Sum of Per-Order Converted Margin USD:  ${sum_order_margin_usd}")
print(f"  - Sum of Per-Order Converted Loss USD:    ${sum_order_loss_usd}")

assert sum_order_inflow_usd == inflow_val, f"Inflow mismatch: {sum_order_inflow_usd} != {inflow_val}"
assert sum_order_outflow_usd == outflow_val, f"Outflow mismatch: {sum_order_outflow_usd} != {outflow_val}"
assert sum_order_margin_usd == margin_val, f"Margin mismatch: {sum_order_margin_usd} != {margin_val}"

# Check Section 14 table references Check 9
assert "Check 9: FX Consolidation Conservation" in report_text, "Check 9 missing from Section 14 table"
print(f"  --> RESULT: PASS (Portfolio USD totals strictly equal the sum of per-order conversions)")

# -------------------------------------------------------------
# AUDIT CHECK 10: Cohort Conservation & Top-10 Invariants
# -------------------------------------------------------------
print(f"\n[CHECK 10] Mathematical Consistency & Invariants:")

# Top 10 sum <= Total loss
top10_section = re.search(r"## 9\. Top Breaching Orders Line-Level Audit.*?\n(\| Rank \|.*?\n\n)", report_text, re.DOTALL).group(1)
top10_rows = [line for line in top10_section.split("\n") if line.startswith("| **#")]
top10_sum = sum(float(cols[8].replace("**", "").replace("$", "").replace(",", "")) for cols in (l.split("|")[1:-1] for l in top10_rows))
exec_loss_match = re.search(r"\*\*Total Cumulative Cash Loss \(Breaches, USD Equiv\)\*\* \|\s*\*\*\$([0-9,.]+)\*\*", report_text)
exec_total_loss = float(exec_loss_match.group(1).replace(",", ""))
assert top10_sum <= exec_total_loss, f"Top 10 sum ({top10_sum}) > Total loss ({exec_total_loss})"
print(f"  - Top-10 Loss (${top10_sum:.2f}) <= Total Loss (${exec_total_loss:.2f}): True")

# Cohort conservation
tree_match = re.search(r"Total Test Payloads Ingested:\s*(\d+)", report_text)
claimed_ingested = int(tree_match.group(1))
eval_match = re.search(r"Evaluated Commercial Orders:\s*(\d+)", report_text)
claimed_eval = int(eval_match.group(1))
quar_match = re.search(r"Quarantined Orders \(NOT_EVALUABLE\):\s*(\d+)", report_text)
claimed_quar = int(quar_match.group(1))
filt_match = re.search(r"Filtered Orders — No Cash Event / Test \(FILTERED\):\s*(\d+)", report_text)
claimed_filt = int(filt_match.group(1))
excl_match = re.search(r"Excluded Orders — Promotional \(EXCLUDED_PROMOTIONAL\):\s*(\d+)", report_text)
claimed_excl = int(excl_match.group(1))

actual_total = len(df)
reconciled_sum = claimed_eval + claimed_quar + claimed_filt + claimed_excl
discrepancy = actual_total - reconciled_sum
assert claimed_ingested == actual_total == 49, f"Mismatch: {claimed_ingested} vs {actual_total}"
assert discrepancy == 0, f"Discrepancy {discrepancy} != 0"
print(f"  - Cohort Tree Conservation: {actual_total} = {claimed_eval} + {claimed_quar} + {claimed_filt} + {claimed_excl} (Diff: 0)")

# Test Suite Pass Rate
assert len(df[df["test_status"] == "PASS"]) == len(df) == 49
print(f"  - Automated Regression Suite: 49 / 49 Tests PASSED (100.0%)")
print(f"  --> RESULT: PASS (All mathematical invariants hold)")

print("\n" + "=" * 80)
print("ALL 10 AUDIT CHECKS PASSED WITH ZERO CONTRADICTIONS OR WARNINGS!")
print("=" * 80)
