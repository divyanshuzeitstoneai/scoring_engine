"""
Synthetic 50,000-Order Dataset Generator for Formula F10 v2.
Produces:
1. f10/data/synthetic_orders.jsonl (Bulk Operation JSONL with __parentId)
2. f10/data/synthetic_orders_sample.json (Nested GraphQL format)
3. f10/data/ground_truth_sidecar.json (Independent ground-truth tags EC-01 to EC-86)
4. f10/data/cost_snapshot_table.json (Point-in-time historical cost index)
"""

import json
import os
import random
from datetime import datetime, timedelta, timezone
from decimal import Decimal, ROUND_HALF_UP
from typing import Any, Dict, List, Tuple

RANDOM_SEED = 42
TOTAL_ORDERS = 50000
AS_OF_DATE = datetime(2024, 10, 31, 23, 59, 59, tzinfo=timezone.utc)
START_DATE = AS_OF_DATE - timedelta(days=540)

CATEGORIES = {
    "Apparel": ["Silk Dress", "Cotton Tee", "Denim Jeans", "Wool Sweater", "Linen Shirt"],
    "Footwear": ["Running Shoes", "Leather Boots", "Canvas Sneakers", "Sandals"],
    "Electronics": ["Bluetooth Headphones", "Wireless Mouse", "USB-C Hub", "Smart Speaker"],
    "Home Goods": ["Ceramic Mug", "Linen Pillow", "Scented Candle", "Throw Blanket"],
    "Beauty": ["Face Cleanser", "Hydrating Serum", "Lip Balm", "Sunscreen SPF 50"],
    "Digital": ["$25 Gift Card", "$50 Gift Card", "$100 Gift Card", "VIP Membership"]
}

def generate_dataset(output_dir: str = "f10/data"):
    random.seed(RANDOM_SEED)
    os.makedirs(output_dir, exist_ok=True)
    
    # 1. Build Catalog (~300 products, ~800 variants)
    catalog_variants = []
    catalog_by_variant_id = {}
    variant_counter = 100000
    product_counter = 50000
    inventory_counter = 200000

    for cat, titles in CATEGORIES.items():
        for t in titles:
            product_counter += 1
            prod_id = f"gid://shopify/Product/{product_counter}"
            # 2 to 4 variants per product
            num_vars = 1 if cat == "Digital" else random.randint(2, 4)
            for v_idx in range(num_vars):
                variant_counter += 1
                inventory_counter += 1
                var_id = f"gid://shopify/ProductVariant/{variant_counter}"
                inv_id = f"gid://shopify/InventoryItem/{inventory_counter}"
                
                base_price = Decimal(str(random.choice([15.00, 25.00, 45.00, 60.00, 85.00, 120.00, 250.00])))
                markup = Decimal(str(random.choice([0.35, 0.45, 0.55, 0.65])))
                cost = (base_price * (Decimal("1.0") - markup)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
                
                # Weight
                weight_val = random.choice([250.0, 500.0, 800.0, 1200.0, 2000.0])
                weight_unit = random.choice(["GRAMS", "KILOGRAMS", "OUNCES", "POUNDS"])
                
                var_obj = {
                    "id": var_id,
                    "product_id": prod_id,
                    "title": f"{t} - Option {v_idx + 1}",
                    "sku": f"SKU-{cat[:3].upper()}-{variant_counter}",
                    "category": cat,
                    "price": str(base_price),
                    "inventory_item_id": inv_id,
                    "unit_cost": str(cost),
                    "weight_value": weight_val,
                    "weight_unit": weight_unit,
                    "is_gift_card": (cat == "Digital" and "Gift Card" in t)
                }
                catalog_variants.append(var_obj)
                catalog_by_variant_id[var_id] = var_obj

    # High volume variant (EC-57: 10,000+ units)
    high_vol_var = catalog_variants[0]
    high_vol_var["title"] = "High-Volume Best Seller Cotton Tee"
    
    # 0 sale variant (EC-57)
    zero_sale_var = catalog_variants[1]
    zero_sale_var["title"] = "Zero Sale Unsold Variant"
    
    # 1 sale variant (EC-57)
    single_sale_var = catalog_variants[2]
    single_sale_var["title"] = "Single Sale Rare Item"

    # 100% return rate variants (EC-56: 10 variants)
    for i in range(10):
        catalog_variants[10 + i]["always_returned"] = True

    print(f"Constructed catalog with {len(catalog_variants)} variants across {len(CATEGORIES)} categories.")

    # 2. Setup Ground Truth & Edge Case Tracking
    ground_truth = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "total_orders": TOTAL_ORDERS,
        "as_of": "2024-10-31",
        "random_seed": RANDOM_SEED,
        "edge_case_counts": {f"EC-{i:02d}": 0 for i in range(1, 87)},
        "orders_meta": {},
        "variants_meta": {}
    }

    cost_snapshot_table = {}
    for v in catalog_variants:
        cost_snapshot_table[v["id"]] = v["unit_cost"]

    # 3. Stream Synthetic Orders
    jsonl_path = os.path.join(output_dir, "synthetic_orders.jsonl")
    sample_json_path = os.path.join(output_dir, "synthetic_orders_sample.json")
    
    sample_nodes = []
    total_days_span = 540

    order_base_id = 7000000000
    line_base_id = 8000000000
    refund_base_id = 9000000000
    tx_base_id = 4000000000
    return_base_id = 6000000000

    print(f"Generating {TOTAL_ORDERS} synthetic orders...")

    with open(jsonl_path, "w", encoding="utf-8") as jsonl_file:
        for order_idx in range(1, TOTAL_ORDERS + 1):
            order_id_num = order_base_id + order_idx
            order_gid = f"gid://shopify/Order/{order_id_num}"
            
            # Plant Edge Cases deterministically
            ec_tags = []
            
            # Date distribution
            day_offset = random.randint(0, total_days_span)
            order_dt = START_DATE + timedelta(days=day_offset, seconds=random.randint(0, 86399))
            cohort_str = order_dt.strftime("%Y-%m-%d")
            order_dt_iso = order_dt.isoformat()
            
            # EC-50: Order exactly on maturity boundary (35 days before as_of)
            if order_idx <= 120:
                ec_tags.append("EC-50")
                order_dt = AS_OF_DATE - timedelta(days=35)
                order_dt_iso = order_dt.isoformat()
                cohort_str = order_dt.strftime("%Y-%m-%d")

            # EC-49: Orders on window boundaries (30, 90, 365)
            if 120 < order_idx <= 240:
                ec_tags.append("EC-49")
                order_dt = AS_OF_DATE - timedelta(days=30)
                order_dt_iso = order_dt.isoformat()
            elif 240 < order_idx <= 360:
                ec_tags.append("EC-49")
                order_dt = AS_OF_DATE - timedelta(days=90)
                order_dt_iso = order_dt.isoformat()
            elif 360 < order_idx <= 480:
                ec_tags.append("EC-49")
                order_dt = AS_OF_DATE - timedelta(days=365)
                order_dt_iso = order_dt.isoformat()

            # EC-51: Timezone edge near midnight
            if 480 < order_idx <= 700:
                ec_tags.append("EC-51")
                order_dt = order_dt.replace(hour=23, minute=59, second=random.randint(50, 59))
                order_dt_iso = order_dt.isoformat()

            # Currency & Gateway Mix
            currency = "USD"
            presentment_curr = "USD"
            gateway = "shopify_payments"
            has_fee = True
            
            # EC-44, EC-45, EC-46
            if order_idx % 10 == 0 and order_idx <= 30000:
                gateway = "manual"
                has_fee = False
                ec_tags.append("EC-46")
            elif order_idx % 5 == 0 and order_idx <= 30000:
                gateway = "paypal_express"
                has_fee = False
                ec_tags.append("EC-45")
            else:
                ec_tags.append("EC-44")

            # EC-42: Multi-currency
            if 700 < order_idx <= 1300:
                presentment_curr = "EUR" if order_idx % 2 == 0 else "CAD"
                ec_tags.append("EC-42")

            # EC-76: Zero/3 minor unit currencies
            if 1300 < order_idx <= 1700:
                currency = "JPY" if order_idx % 2 == 0 else "BHD"
                ec_tags.append("EC-76")

            # EC-43: Tax inclusive store
            taxes_included = False
            if 1700 < order_idx <= 2300:
                taxes_included = True
                ec_tags.append("EC-43")

            # EC-29: Test orders
            is_test_order = (2300 < order_idx <= 2550)
            if is_test_order:
                ec_tags.append("EC-29")

            # Order Lines
            # Distribution: 1 line (50%), 2 lines (30%), 3+ lines (20%)
            num_lines = 1
            r_lines = random.random()
            if r_lines > 0.8:
                num_lines = random.randint(3, 5)
            elif r_lines > 0.5:
                num_lines = 2
                
            # EC-57: single sale variant
            if order_idx == 3000:
                chosen_vars = [single_sale_var]
                ec_tags.append("EC-57")
            # EC-57: high volume variant assigned to 12,000 orders
            elif order_idx <= 12000:
                chosen_vars = [high_vol_var]
                ec_tags.append("EC-57")
            else:
                chosen_vars = [random.choice(catalog_variants[3:]) for _ in range(num_lines)]

            # Check if order is fully cancelled
            is_fully_cancelled = (2600 < order_idx <= 2950)
            if is_fully_cancelled:
                ec_tags.append("EC-26")

            # Generate Lines
            lines_data = []
            order_gross = Decimal("0.00")
            order_disc = Decimal("0.00")
            
            for line_idx, v in enumerate(chosen_vars):
                line_base_id += 1
                line_gid = f"gid://shopify/LineItem/{line_base_id}"
                
                qty = random.randint(1, 3)
                if is_fully_cancelled:
                    current_qty = 0
                else:
                    current_qty = qty
                    
                u_price = Decimal(v["price"])
                line_gross = (u_price * Decimal(qty)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
                order_gross += line_gross

                # Unit Cost resolution
                u_cost_str = v["unit_cost"]
                line_count = line_base_id - 8000000000
                
                # EC-37: unitCost null (2,050 lines)
                if 3000 < line_count <= 5050:
                    u_cost_str = None
                    ec_tags.append("EC-37")
                    ec_tags.append("EC-63")
                # EC-38: unitCost zero (550 lines)
                elif 5050 < line_count <= 5600:
                    u_cost_str = "0.00"
                    ec_tags.append("EC-38")
                # EC-77: Unit cost > price
                elif 5600 < line_count <= 5950:
                    u_cost_str = str(u_price + Decimal("10.00"))
                    ec_tags.append("EC-77")

                # Discount generation
                disc_amount = Decimal("0.00")
                if not is_fully_cancelled:
                    if order_idx % 7 == 0:
                        disc_amount = (line_gross * Decimal("0.20")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
                        ec_tags.append("EC-01")
                    elif order_idx % 11 == 0:
                        disc_amount = Decimal("5.00") if line_gross >= Decimal("10.00") else Decimal("0.00")
                        ec_tags.append("EC-02")
                    elif order_idx % 13 == 0:
                        disc_amount = (line_gross * Decimal("0.15")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
                        ec_tags.append("EC-03")
                    # EC-08: 100% discount free item
                    elif 6000 < order_idx <= 6120:
                        disc_amount = line_gross
                        ec_tags.append("EC-08")
                        ec_tags.append("EC-53")

                order_disc += disc_amount
                net_billed_line = line_gross - disc_amount

                lines_data.append({
                    "id": line_gid,
                    "variant_id": v["id"],
                    "product_id": v["product_id"],
                    "sku": v["sku"],
                    "title": v["title"],
                    "quantity": qty,
                    "current_quantity": current_qty,
                    "original_total": str(line_gross),
                    "discount_allocated": str(disc_amount),
                    "unit_cost": u_cost_str,
                    "weight_value": v["weight_value"] if order_idx > 6500 else None,
                    "weight_unit": v["weight_unit"]
                })

            # Shipping line
            ship_charged = Decimal("0.00") if order_idx % 4 == 0 else Decimal("6.50")
            if ship_charged == Decimal("0.00"):
                ec_tags.append("EC-09")

            # Transactions
            tx_amount = max(Decimal("0.00"), order_gross - order_disc + ship_charged)
            fees = []
            if has_fee and tx_amount > Decimal("0.00"):
                fee_val = (tx_amount * Decimal("0.029") + Decimal("0.30")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
                fees.append({"amount": {"amount": str(fee_val), "currencyCode": currency}})

            tx_base_id += 1
            tx_data = [{
                "id": f"gid://shopify/OrderTransaction/{tx_base_id}",
                "kind": "SALE" if not is_fully_cancelled else "VOID",
                "status": "SUCCESS",
                "gateway": gateway,
                "amount": str(tx_amount),
                "fees": fees
            }]

            # Refunds
            refunds_data = []
            # EC-13 (Restocked), EC-14 (Not Restocked), EC-11 (Partial refund)
            should_refund = (order_idx % 6 == 0 or getattr(chosen_vars[0], "always_returned", False))
            if should_refund and not is_fully_cancelled:
                target_line = lines_data[0]
                ref_qty = 1
                is_restocked = (order_idx % 2 == 0)
                restock_type = "RESTOCK" if is_restocked else "NO_RESTOCK"
                
                if is_restocked:
                    ec_tags.append("EC-13")
                else:
                    ec_tags.append("EC-14")
                if target_line["quantity"] > 1:
                    ec_tags.append("EC-11")

                u_net = (Decimal(target_line["original_total"]) - Decimal(target_line["discount_allocated"])) / Decimal(target_line["quantity"])
                ref_subtotal = (u_net * Decimal(ref_qty)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

                refund_base_id += 1
                refunds_data.append({
                    "id": f"gid://shopify/Refund/{refund_base_id}",
                    "line_item_id": target_line["id"],
                    "quantity": ref_qty,
                    "subtotal": str(ref_subtotal),
                    "restock_type": restock_type
                })

            # Write Order Row to JSONL
            order_jsonl_node = {
                "id": order_gid,
                "name": f"#ORD-{order_idx}",
                "createdAt": order_dt_iso,
                "processedAt": order_dt_iso,
                "cancelledAt": order_dt_iso if is_fully_cancelled else None,
                "cancelReason": "CUSTOMER" if is_fully_cancelled else None,
                "test": is_test_order,
                "displayFinancialStatus": "VOIDED" if is_fully_cancelled else ("REFUNDED" if should_refund else "PAID"),
                "displayFulfillmentStatus": "UNFULFILLED" if is_fully_cancelled else "FULFILLED",
                "taxesIncluded": taxes_included,
                "currencyCode": currency,
                "totalPriceSet": {"shopMoney": {"amount": str(tx_amount), "currencyCode": currency}},
                "totalDiscountsSet": {"shopMoney": {"amount": str(order_disc), "currencyCode": currency}}
            }
            jsonl_file.write(json.dumps(order_jsonl_node) + "\n")

            # Write Line Items with __parentId
            for l in lines_data:
                line_jsonl_node = {
                    "id": l["id"],
                    "__parentId": order_gid,
                    "title": l["title"],
                    "sku": l["sku"],
                    "quantity": l["quantity"],
                    "currentQuantity": l["current_quantity"],
                    "originalTotalSet": {"shopMoney": {"amount": l["original_total"], "currencyCode": currency}},
                    "discountAllocations": [{"allocatedAmountSet": {"shopMoney": {"amount": l["discount_allocated"], "currencyCode": currency}}}],
                    "variant": {
                        "id": l["variant_id"],
                        "inventoryItem": {
                            "unitCost": {"amount": l["unit_cost"], "currencyCode": currency} if l["unit_cost"] is not None else None,
                            "measurement": {"weight": {"value": l["weight_value"], "unit": l["weight_unit"]}} if l["weight_value"] else None
                        }
                    }
                }
                jsonl_file.write(json.dumps(line_jsonl_node) + "\n")

            # Write Refunds with __parentId
            for r in refunds_data:
                ref_jsonl_node = {
                    "id": r["id"],
                    "__parentId": order_gid,
                    "refundLineItems": [{
                        "lineItem": {"id": r["line_item_id"]},
                        "quantity": r["quantity"],
                        "subtotalSet": {"shopMoney": {"amount": r["subtotal"], "currencyCode": currency}},
                        "restockType": r["restock_type"]
                    }]
                }
                jsonl_file.write(json.dumps(ref_jsonl_node) + "\n")

            # Keep sample nested nodes for sample JSON
            if order_idx <= 100:
                sample_nodes.append({
                    "cursor": f"cursor-{order_idx}",
                    "node": {
                        **order_jsonl_node,
                        "lineItems": {"nodes": lines_data},
                        "refunds": {"nodes": refunds_data}
                    }
                })

            # Record Edge Cases in Ground Truth
            for tag in set(ec_tags):
                if tag in ground_truth["edge_case_counts"]:
                    ground_truth["edge_case_counts"][tag] += 1
            ground_truth["orders_meta"][order_gid] = ec_tags

    # Write sample JSON
    with open(sample_json_path, "w", encoding="utf-8") as f:
        json.dump({
            "data": {
                "orders": {
                    "pageInfo": {"hasNextPage": True, "endCursor": "cursor-100"},
                    "edges": sample_nodes
                }
            }
        }, f, indent=2)

    # Write ground truth sidecar
    sidecar_path = os.path.join(output_dir, "ground_truth_sidecar.json")
    with open(sidecar_path, "w", encoding="utf-8") as f:
        json.dump(ground_truth, f, indent=2)

    # Write snapshot table
    snapshot_path = os.path.join(output_dir, "cost_snapshot_table.json")
    with open(snapshot_path, "w", encoding="utf-8") as f:
        json.dump(cost_snapshot_table, f, indent=2)

    print(f"Generated 50,000 orders to {jsonl_path}")
    print(f"Sidecar written to {sidecar_path}")

if __name__ == "__main__":
    generate_dataset()
