import pandas as pd

import os
p = "f03/output/f03_results_table.csv"
if not os.path.exists(p):
    p = os.path.join(os.path.dirname(__file__), "..", "output", "f03_results_table.csv")
if not os.path.exists(p):
    p = "scratch/f03_results_table.csv"

df = pd.read_csv(p)
print(f"Total orders ingested: {len(df)}")
eval_df = df[df["evaluability_status"].isin(["EVALUATED_CONFIRMED", "EVALUATED_ESTIMATED"])]
print(f"Evaluated orders: {len(eval_df)}")
quar_df = df[df["evaluability_status"] == "NOT_EVALUABLE"]
print(f"Quarantined orders: {len(quar_df)}")
excl_df = df[df["evaluability_status"] == "EXCLUDED_PROMOTIONAL"]
print(f"Excluded promotional: {len(excl_df)}")
filt_df = df[df["evaluability_status"].isin(["FILTERED_NO_CASH", "FILTERED_TEST_ORDER"])]
print(f"Filtered (no cash / test): {len(filt_df)}")
print(f"Conservation sum: {len(eval_df) + len(quar_df) + len(excl_df) + len(filt_df)}")

breaches = eval_df[eval_df["f03_breach"] == True]
print(f"Breaches count: {len(breaches)}")
merch_loss = breaches[breaches["is_merchandise_loss"] == True]
print(f"Merchandise loss count: {len(merch_loss)}")
fulf_loss = breaches[breaches["is_fulfillment_induced_loss"] == True]
print(f"Fulfillment induced loss count: {len(fulf_loss)}")

# Financial totals for evaluated orders
print(f"Total Net Cash In (USD equiv): ${eval_df['net_cash_in_usd'].sum():.2f}")
print(f"Total Net Cash Out (USD equiv): ${eval_df['net_cash_out_usd'].sum():.2f}")
print(f"Total Net Margin Cash (USD equiv): ${eval_df['net_margin_cash_usd'].sum():.2f}")
print(f"Total Loss (USD equiv): ${breaches['f03_loss_usd'].sum():.2f}")

# Native currency breakdown
for curr in sorted(df["currency_code"].unique()):
    c_eval = eval_df[eval_df["currency_code"] == curr]
    c_breach = breaches[breaches["currency_code"] == curr]
    print(f"Currency {curr}: Ingested={len(df[df['currency_code']==curr])}, Evaluated={len(c_eval)}, Breaches={len(c_breach)}, Total Loss={c_breach['f03_loss'].sum():.2f}")

# Top 10 Breaches sorted by f03_loss_usd descending
top10 = breaches.sort_values(by="f03_loss_usd", ascending=False).head(10)
print("\nTop 10 Breaching Orders (by USD loss):")
for idx, r in top10.reset_index().iterrows():
    print(f"{idx+1:2d}. {r['order_name']:15s} ({r['currency_code']}) | loss: {r['currency_code']} {r['f03_loss']:7.2f} (USD ${r['f03_loss_usd']:6.2f}) | GP: {r['order_gross_profit']:7.2f} | MerchLoss: {r['is_merchandise_loss']} | Driver: {r['description'][:50]}")

print(f"\nTop 10 Sum (USD equiv): ${top10['f03_loss_usd'].sum():.2f}")
print(f"Total Loss (USD equiv): ${breaches['f03_loss_usd'].sum():.2f}")
assert top10['f03_loss_usd'].sum() <= breaches['f03_loss_usd'].sum(), "Top 10 exceeds total loss!"
print("Assertion Passed: top10_sum <= total_loss!")
