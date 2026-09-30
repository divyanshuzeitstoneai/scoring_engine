"""
Synthetic 50,000-Order Dataset Generator for Formula F11 Order Profitability v2.1.
Enforces exact quotas for A01 through E12, generates visible GraphQL-shaped data
and sealed latent-truth answer key (answer_key.parquet).
"""

import json
import os
import random
from datetime import datetime, timedelta, timezone
from decimal import Decimal, ROUND_HALF_UP
from typing import Any, Dict, List, Tuple
import pandas as pd
import yaml

RANDOM_SEED = 42
TOTAL_ORDERS = 50000

SCENARIO_QUOTAS = {
    # Group A: Standard Orders (29,900)
    "A01": 7900, "A02": 6000, "A03": 3500, "A04": 3500,
    "A05": 1500, "A06": 2000, "A07": 2500, "A08": 3000,
    # Group B: Returns and Edits (6,900)
    "B01": 1200, "B02": 1500, "B03": 900, "B04": 500,
    "B05": 300, "B06": 600, "B07": 300, "B08": 400,
    "B09": 400, "B10": 300, "B11": 300, "B12": 200,
    # Group C: COGS Edge Cases (4,800)
    "C01": 900, "C02": 1100, "C03": 500, "C04": 250,
    "C05": 1200, "C06": 350, "C07": 250, "C08": 250,
    # Group D: Gateway, Tender & Tax (6,100)
    "D01": 1500, "D02": 700, "D03": 400, "D04": 350,
    "D05": 150, "D06": 1200, "D07": 1000, "D08": 200,
    "D09": 200, "D10": 300, "D11": 100,
    # Group E: Operational & Boundary Cases (2,300)
    "E01": 250, "E02": 50, "E03": 150, "E04": 150,
    "E05": 100, "E06": 100, "E07": 100, "E08": 200,
    "E09": 400, "E10": 500, "E11": 200, "E12": 100,
}

SHOP_QUOTAS = {
    "S1": ("USD", 2, False, 20000),
    "S2": ("GBP", 2, True, 12000),
    "S3": ("CAD", 2, False, 8000),
    "S4": ("INR", 2, True, 6000),
    "S5": ("JPY", 0, False, 4000),
}


def generate_f11_dataset(output_dir: str = "f11/data"):
    random.seed(RANDOM_SEED)
    os.makedirs(output_dir, exist_ok=True)
    os.makedirs("f11/reports", exist_ok=True)
    
    as_of = datetime(2026, 9, 30, 23, 59, 59, tzinfo=timezone.utc)
    start_date = datetime(2025, 10, 1, 0, 0, 0, tzinfo=timezone.utc)
    date_range_secs = int((as_of - start_date).total_seconds())

    # Build scenario queue exactly matching quotas
    scenario_pool = []
    for sc_id, count in SCENARIO_QUOTAS.items():
        scenario_pool.extend([sc_id] * count)
    random.shuffle(scenario_pool)
    assert len(scenario_pool) == TOTAL_ORDERS, f"Scenario count mismatch: {len(scenario_pool)} != 50000"

    # Distribute orders into shops
    shop_assignments = []
    for s_name, (curr, exp, tax_inc, s_count) in SHOP_QUOTAS.items():
        shop_assignments.extend([s_name] * s_count)
    random.shuffle(shop_assignments)

    # 1. Generate Variants Catalog per shop
    catalog = []
    categories = ["Apparel", "Footwear", "Electronics", "Home Goods", "Beauty", "Digital"]
    var_id_counter = 1000
    
    for cat in categories:
        for p_idx in range(50):
            p_id = f"gid://shopify/Product/{cat[:3]}_{p_idx}"
            for v_idx in range(3):
                var_id_counter += 1
                vid = f"gid://shopify/ProductVariant/{var_id_counter}"
                inv_id = f"gid://shopify/InventoryItem/{var_id_counter}"
                base_price = random.choice([25.0, 45.0, 60.0, 85.0, 120.0, 250.0])
                markup = random.choice([0.35, 0.45, 0.55, 0.65])
                cost = round(base_price * (1.0 - markup), 2)
                catalog.append({
                    "product_id": p_id,
                    "variant_id": vid,
                    "inventory_item_id": inv_id,
                    "category": cat,
                    "price": base_price,
                    "cost": cost,
                    "weight_g": 0 if cat == "Digital" else random.choice([300, 500, 800, 1500])
                })

    # 2. Generate Orders
    visible_orders = []
    answer_keys = []
    
    order_num = 1000
    
    for i in range(TOTAL_ORDERS):
        order_num += 1
        sc_id = scenario_pool[i]
        shop_name = shop_assignments[i]
        curr, exp, taxes_inc, _ = SHOP_QUOTAS[shop_name]
        
        # Shop 4 has no Shopify Payments
        if shop_name == "S4" and sc_id == "A01":
            # Gateway is razorpay or COD
            gw_choice = random.choice(["razorpay", "cash_on_delivery"])
        else:
            gw_choice = "shopify_payments" if sc_id not in ["D01", "D02"] else ("paypal" if sc_id == "D01" else "cash_on_delivery")

        # Pick random order timestamp
        t_offset = random.randint(0, date_range_secs)
        o_created = start_date + timedelta(seconds=t_offset)
        o_proc = o_created + timedelta(minutes=random.randint(1, 15))
        
        order_id = f"gid://shopify/Order/{shop_name}_{order_num}"
        order_name = f"#{shop_name}-{order_num}"

        # Choose line items
        num_lines = 1 if sc_id == "A01" else (2 if sc_id != "A02" else random.randint(2, 5))
        lines = []
        tot_item_price = Decimal("0.00")
        tot_true_cost = Decimal("0.00")
        tot_vis_cost = Decimal("0.00")
        has_missing_cogs = False

        for l_idx in range(num_lines):
            item = random.choice(catalog)
            lid = f"gid://shopify/LineItem/{order_num}_{l_idx+1}"
            u = Decimal(str(item["price"]))
            q0 = 1 if sc_id not in ["A06", "B01"] else random.randint(1, 3)
            qc = q0
            
            # Scenario overrides for LineItem
            if sc_id in ["B01", "B02"] and l_idx == 0:
                qc = max(0, q0 - 1)
            elif sc_id in ["B03", "B04"]:
                qc = 0
            elif sc_id == "B09" and l_idx == 0:
                # removed by order edit
                qc = 0
            
            # Discounts
            disc_allocs = []
            if sc_id in ["A03", "A06"]:
                d_val = (u * Decimal("0.10")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
                disc_allocs.append({
                    "allocatedAmountSet": {"shopMoney": {"amount": str(d_val), "currencyCode": curr}}
                })
            elif sc_id == "A04":
                d_val = (u * Decimal("0.20")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
                disc_allocs.append({
                    "allocatedAmountSet": {"shopMoney": {"amount": str(d_val), "currencyCode": curr}}
                })
            elif sc_id == "A05":
                d_val = Decimal("5.00")
                disc_allocs.append({
                    "allocatedAmountSet": {"shopMoney": {"amount": str(d_val), "currencyCode": curr}}
                })

            # Unit Cost logic
            true_unit_cost = Decimal(str(item["cost"]))
            vis_cost_str = str(true_unit_cost)
            
            if sc_id == "C01":
                vis_cost_str = None
                has_missing_cogs = True
            elif sc_id == "C02" and l_idx == 0:
                vis_cost_str = None
                has_missing_cogs = True
            elif sc_id == "C03":
                vis_cost_str = "0.00"
            elif sc_id == "C04" and l_idx == 0:
                item_var = None
            elif sc_id == "C05":
                # Cost drift
                vis_cost_str = str((true_unit_cost * Decimal("1.25")).quantize(Decimal("0.01")))
                
            tot_item_price += u * q0
            tot_true_cost += true_unit_cost * qc
            if vis_cost_str is not None:
                tot_vis_cost += Decimal(vis_cost_str) * qc

            line_obj = {
                "id": lid,
                "name": f"{item['category']} Item",
                "sku": f"SKU-{item['category'][:3]}-{l_idx}",
                "quantity": q0,
                "currentQuantity": qc,
                "isGiftCard": (sc_id == "D10"),
                "requiresShipping": (item["category"] != "Digital" and sc_id != "E09"),
                "originalUnitPriceSet": {"shopMoney": {"amount": str(u), "currencyCode": curr}},
                "discountAllocations": disc_allocs,
                "variant": {
                    "id": item["variant_id"],
                    "sku": f"SKU-{l_idx}",
                    "inventoryItem": {
                        "id": item["inventory_item_id"],
                        "unitCost": {"amount": vis_cost_str, "currencyCode": curr} if vis_cost_str else None,
                        "updatedAt": o_proc.isoformat()
                    }
                } if sc_id != "C04" or l_idx > 0 else None
            }
            lines.append(line_obj)

        # Shipping logic
        is_digital = (sc_id == "E09") or all(not l["requiresShipping"] for l in lines)
        is_free_ship = (sc_id == "A07") or (tot_item_price >= Decimal("100.00"))
        ship_charge = Decimal("0.00") if (is_digital or is_free_ship) else Decimal("10.00")
        
        true_carrier_cost = Decimal("0.00") if is_digital else Decimal("6.50")
        measured_carrier = str(true_carrier_cost) if sc_id in ["A01", "B01", "C01"] else None

        # Gateway fees logic
        total_inflow = tot_item_price + ship_charge
        if gw_choice == "shopify_payments":
            true_fee = (total_inflow * Decimal("0.024") + Decimal("0.30")).quantize(Decimal("0.01"))
            vis_fees = [{"amount": {"amount": str(true_fee), "currencyCode": curr}}]
        elif gw_choice == "cash_on_delivery":
            true_fee = Decimal("0.00")
            vis_fees = []
        else:
            true_fee = (total_inflow * Decimal("0.029") + Decimal("0.30")).quantize(Decimal("0.01"))
            vis_fees = [] # Third-party fees empty in GraphQL!

        # Refunds array
        refunds = []
        tot_refunded = Decimal("0.00")
        if sc_id in ["B01", "B02", "B03", "B04", "B06"]:
            ref_amt = Decimal("25.00") if sc_id != "B03" else total_inflow
            tot_refunded = ref_amt
            refunds.append({
                "id": f"gid://shopify/Refund/{order_num}_1",
                "createdAt": (o_proc + timedelta(days=5)).isoformat(),
                "totalRefundedSet": {"shopMoney": {"amount": str(ref_amt), "currencyCode": curr}},
                "refundLineItems": [
                    {
                        "lineItemId": lines[0]["id"],
                        "quantity": 1,
                        "restockType": "RESTOCK" if sc_id in ["B02", "B03"] else "CANCEL"
                    }
                ]
            })

        # Latent Truth Profit
        true_p = total_inflow - tot_true_cost - true_carrier_cost - true_fee - tot_refunded - Decimal("1.50")
        
        # Expected lane
        if has_missing_cogs:
            p_upper_approx = total_inflow - (true_carrier_cost if measured_carrier else 0) - (true_fee if vis_fees else 0)
            expected_lane = "CONFIRMED_LOSS" if p_upper_approx < 0 else "UNDETERMINED"
        elif not vis_fees or not measured_carrier:
            expected_lane = "ESTIMATED"
        else:
            expected_lane = "MEASURED"

        order_record = {
            "id": order_id,
            "name": order_name,
            "createdAt": o_created.isoformat(),
            "processedAt": o_proc.isoformat(),
            "updatedAt": (o_proc + timedelta(hours=2)).isoformat(),
            "cancelledAt": (o_proc + timedelta(hours=1)).isoformat() if sc_id in ["E01", "E02"] else None,
            "displayFinancialStatus": "PAID" if sc_id not in ["D04", "D05"] else ("AUTHORIZED" if sc_id == "D04" else "VOIDED"),
            "displayFulfillmentStatus": "FULFILLED" if sc_id not in ["E01", "D04"] else "UNFULFILLED",
            "currencyCode": curr,
            "taxesIncluded": taxes_inc,
            "test": (sc_id == "E07"),
            "paymentGatewayNames": [gw_choice],
            "currentShippingPriceSet": {"shopMoney": {"amount": str(ship_charge), "currencyCode": curr}},
            "totalShippingPriceSet": {"shopMoney": {"amount": str(ship_charge), "currencyCode": curr}},
            "totalPriceSet": {"shopMoney": {"amount": str(total_inflow), "currencyCode": curr}},
            "actual_carrier_cost": measured_carrier,
            "lineItems": lines,
            "transactions": [
                {
                    "id": f"gid://shopify/OrderTransaction/{order_num}_tx",
                    "kind": "SALE" if sc_id != "D04" else "AUTHORIZATION",
                    "status": "SUCCESS",
                    "gateway": gw_choice,
                    "processedAt": o_proc.isoformat(),
                    "amountSet": {"shopMoney": {"amount": str(total_inflow), "currencyCode": curr}},
                    "fees": vis_fees
                }
            ],
            "refunds": refunds
        }

        answer_key_record = {
            "order_id": order_id,
            "order_name": order_name,
            "shop": shop_name,
            "scenario_id": sc_id,
            "currency": curr,
            "true_inflow": float(total_inflow),
            "true_cogs": float(tot_true_cost),
            "true_carrier_cost": float(true_carrier_cost),
            "true_gateway_fee": float(true_fee),
            "true_refund_loss": float(tot_refunded),
            "true_profit": float(true_p),
            "expected_lane": expected_lane
        }

        visible_orders.append(order_record)
        answer_keys.append(answer_key_record)

    # 3. Add 250 Duplicate records for deduplication testing
    duplicate_records = []
    for dup_idx in range(250):
        src_order = dict(visible_orders[dup_idx])
        duplicate_records.append(src_order)

    # 4. Write Visible JSONL Dataset
    jsonl_path = os.path.join(output_dir, "synthetic_orders.jsonl")
    print(f"Writing 50,000 visible orders + 250 duplicates to {jsonl_path}...")
    with open(jsonl_path, "w", encoding="utf-8") as f:
        for o in visible_orders:
            f.write(json.dumps(o) + "\n")
        for dup in duplicate_records:
            f.write(json.dumps(dup) + "\n")

    # Sample JSON
    with open(os.path.join(output_dir, "synthetic_orders_sample.json"), "w", encoding="utf-8") as f:
        json.dump(visible_orders[:100], f, indent=2)

    # 5. Write Latent Truth Answer Key Parquet
    df_truth = pd.DataFrame(answer_keys)
    parquet_path = os.path.join(output_dir, "answer_key.parquet")
    print(f"Writing sealed latent-truth answer key to {parquet_path}...")
    df_truth.to_parquet(parquet_path, index=False)

    with open(os.path.join(output_dir, "ground_truth_sidecar.json"), "w", encoding="utf-8") as f:
        json.dump(answer_keys[:500], f, indent=2)

    print("Generation complete! Exactly 50,000 orders generated across 5 shops.")


if __name__ == "__main__":
    generate_f11_dataset()
