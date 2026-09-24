"""
Shopify Synthetic Dataset Generator for Formula F01: Promotional Margin Leakage.
Generates 50,000 Shopify-shaped orders, a 600-SKU product catalog, and a ground-truth sidecar.
Produces realistic retail pricing headroom ensuring genuine separation between:
- Healthy discounted orders (~35-45%)
- Promotional margin leakage (~40-50%)
- Negative gross profit / selling below COGS (~10-15%)
Exposes full Shopify discount lineage across product markdowns and cart allocations.
"""

import json
import os
import random
import shutil
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple

RANDOM_SEED = 42
random.seed(RANDOM_SEED)

CATEGORY_MARGIN_TABLE: Dict[str, float] = {
    "Apparel & Accessories > Clothing": 0.52,
    "Electronics > Audio & Video": 0.18,
    "Health & Beauty > Personal Care": 0.62,
    "Home & Garden > Decor": 0.38,
    "Apparel & Accessories > Handbags & Wallets": 0.48,
}

PRODUCT_TYPE_MARGIN_TABLE: Dict[str, float] = {
    "Apparel": 0.52,
    "Electronics": 0.18,
    "Beauty": 0.62,
    "Home Goods": 0.38,
    "Accessories": 0.48,
}

STOREWIDE_DEFAULT_MARGIN = 0.35

def generate_catalog(num_skus: int = 600) -> Dict[str, Any]:
    """
    Generates a realistic Shopify product catalog with realistic retail pricing headroom (IMU).
    """
    categories = list(CATEGORY_MARGIN_TABLE.keys())
    product_types = list(PRODUCT_TYPE_MARGIN_TABLE.keys())

    products = []
    sku_counter = 1000
    variant_id_counter = 2000000000
    inventory_item_id_counter = 3000000000
    product_id_counter = 1000000000

    catalog_by_variant_id = {}
    catalog_by_sku = {}

    for i in range(num_skus):
        product_id = product_id_counter + i
        variant_id = variant_id_counter + i
        inventory_item_id = inventory_item_id_counter + i
        sku = f"SKU-{sku_counter + i}"

        is_uncategorized = (i % 10 == 0)
        if is_uncategorized:
            category_name = None
            product_type = None
            base_margin = STOREWIDE_DEFAULT_MARGIN
        else:
            cat_idx = i % len(categories)
            category_name = categories[cat_idx]
            product_type = product_types[cat_idx]
            base_margin = CATEGORY_MARGIN_TABLE[category_name]

        # Price range
        if product_type == "Electronics":
            original_price = round(random.uniform(80.0, 450.0), 2)
        elif product_type == "Beauty":
            original_price = round(random.uniform(18.0, 95.0), 2)
        elif product_type == "Apparel":
            original_price = round(random.uniform(25.0, 150.0), 2)
        else:
            original_price = round(random.uniform(20.0, 200.0), 2)

        # Metafield override on ~5% of SKUs
        metafields = []
        has_metafield = (i % 20 == 3)
        metafield_margin = None
        if has_metafield:
            metafield_margin = round(base_margin + 0.05, 2)
            metafields.append({
                "namespace": "custom",
                "key": "target_margin",
                "value": str(metafield_margin),
                "type": "number_decimal"
            })

        target_m = metafield_margin if metafield_margin is not None else base_margin

        # RETAIL MERCHANDISING HEADROOM (Initial Markup / IMU):
        # 55% healthy headroom (12-22% above target margin floor)
        # 25% moderate headroom (5-10% above target margin floor)
        # 15% tight margin (0-4% above target margin floor)
        # 5% inherent catalog deficit (COGS > 1 - target_margin)
        headroom_seed = i % 100
        if headroom_seed < 55:
            headroom = random.uniform(0.12, 0.22)
        elif headroom_seed < 80:
            headroom = random.uniform(0.05, 0.10)
        elif headroom_seed < 95:
            headroom = random.uniform(0.00, 0.04)
        else:
            headroom = random.uniform(-0.10, -0.02)  # Inherent COGS deficit

        pre_discount_margin = max(0.05, min(0.85, target_m + headroom))
        true_cogs_ratio = 1.0 - pre_discount_margin
        true_cogs = round(max(5.0, original_price * true_cogs_ratio), 2)

        inventory_item = {
            "id": inventory_item_id,
            "sku": sku,
            "cost": str(true_cogs),
            "tracked": True
        }

        variant = {
            "id": variant_id,
            "product_id": product_id,
            "title": f"Variant for {sku}",
            "sku": sku,
            "price": str(original_price),
            "compare_at_price": str(original_price),
            "inventory_item_id": inventory_item_id,
            "inventory_item": inventory_item
        }

        product = {
            "id": product_id,
            "title": f"Product {sku}",
            "product_type": product_type or "",
            "category": {"name": category_name} if category_name else None,
            "variants": [variant],
            "metafields": metafields
        }

        products.append(product)

        sku_data = {
            "product_id": product_id,
            "variant_id": variant_id,
            "inventory_item_id": inventory_item_id,
            "sku": sku,
            "original_price": original_price,
            "true_cogs": true_cogs,
            "category": category_name,
            "product_type": product_type,
            "metafield_margin": metafield_margin,
            "target_margin": target_m,
            "margin_source": "metafield" if metafield_margin is not None else (
                "taxonomy" if category_name else (
                    "product_type" if product_type else "storewide_default"
                )
            )
        }
        catalog_by_variant_id[variant_id] = sku_data
        catalog_by_sku[sku] = sku_data

    return {
        "products": products,
        "by_variant_id": catalog_by_variant_id,
        "by_sku": catalog_by_sku
    }

def generate_orders_and_sidecar(
    catalog: Dict[str, Any],
    total_orders: int = 50000
) -> Dict[str, Any]:
    """
    Generates 50,000 Shopify orders with diverse, realistic discount mechanisms and edge cases.
    """
    by_variant_id = catalog["by_variant_id"]
    all_variant_ids = list(by_variant_id.keys())

    tier2_variant_ids = [vid for vid in all_variant_ids if by_variant_id[vid]["category"] is not None and vid % 10 == 1]
    tier3_variant_ids = [vid for vid in all_variant_ids if by_variant_id[vid]["category"] is None and vid % 10 == 0]
    regular_variant_ids = [vid for vid in all_variant_ids if vid not in tier2_variant_ids and vid not in tier3_variant_ids]

    base_time = datetime(2026, 6, 1, 0, 0, 0, tzinfo=timezone.utc)

    counts = {
        "total_orders_generated": total_orders,
        "single_item_orders": 0,
        "two_item_orders": 0,
        "three_plus_item_orders": 0,
        "zero_discount_window_orders": 0,
        "cart_discount_orders": 0,
        "compare_at_discount_orders": 0,
        "stacked_discount_orders": 0,
        "free_gift_orders": 0,
        "fully_cancelled_orders": 0,
        "fully_refunded_orders": 0,
        "partial_cash_refund_orders": 0,
        "physical_return_orders": 0,
        "corrupted_cogs_lines": 0,
        "missing_cogs_lines": 0,
        "tier1_historical_cogs": 0,
        "tier2_category_cogs": 0,
        "tier3_storewide_cogs": 0,
        "tier4_unresolved_cogs": 0,
        "duplicate_payload_records": 0,
        "wholesale_orders": 0
    }

    # Zero discount window: Day 45 to Day 49 (5 days)
    zero_discount_start = base_time + timedelta(days=45)
    zero_discount_end = base_time + timedelta(days=50)

    wholesale_order_indices = set([1005, 5230, 12840, 22100, 31400, 39500, 44200, 48900])

    orders = []
    sidecar = {}

    order_id_counter = 5000000000
    line_item_id_counter = 7000000000

    # Seed historical cost index with point-in-time cost from 10 days before start
    historical_cost_log: Dict[int, List[Tuple[datetime, float]]] = {}
    pre_seed_time = base_time - timedelta(days=10)
    for vid in regular_variant_ids:
        historical_cost_log[vid] = [(pre_seed_time, by_variant_id[vid]["true_cogs"])]

    for order_idx in range(total_orders):
        order_id = order_id_counter + order_idx
        day_offset = (order_idx / total_orders) * 90.0
        order_time = base_time + timedelta(days=day_offset, seconds=(order_idx % 86400))
        is_in_zero_discount_window = (zero_discount_start <= order_time < zero_discount_end)

        rand_weight = random.random()
        if rand_weight < 0.60:
            num_lines = 1
            counts["single_item_orders"] += 1
        elif rand_weight < 0.90:
            num_lines = 2
            counts["two_item_orders"] += 1
        else:
            num_lines = random.choice([3, 4])
            counts["three_plus_item_orders"] += 1

        is_wholesale = order_idx in wholesale_order_indices
        if is_wholesale:
            counts["wholesale_orders"] += 1

        is_cancelled = False
        is_fully_refunded = False
        is_partial_cash_refund = False
        is_physical_return = False
        has_free_gift = False

        if not is_in_zero_discount_window:
            if order_idx % 100 == 12:
                is_cancelled = True
                counts["fully_cancelled_orders"] += 1
            elif order_idx % 100 == 34:
                is_fully_refunded = True
                counts["fully_refunded_orders"] += 1
            elif order_idx % 100 in (55, 56, 57):
                is_partial_cash_refund = True
                counts["partial_cash_refund_orders"] += 1
            elif order_idx % 100 in (77, 78, 79):
                is_physical_return = True
                counts["physical_return_orders"] += 1
            elif order_idx % 200 == 88:
                has_free_gift = True
                counts["free_gift_orders"] += 1
        else:
            counts["zero_discount_window_orders"] += 1

        is_cart_discount = False
        is_compare_at_discount = False
        is_stacked_discount = False
        coupon_code = None
        coupon_pct = 0.0

        if not is_in_zero_discount_window and not is_cancelled and not is_fully_refunded:
            disc_selector = (order_idx * 7) % 100
            if is_wholesale:
                is_cart_discount = True
                coupon_code = "WHOLESALE60"
                coupon_pct = 0.60
            elif disc_selector < 22:
                # 22% Cart coupon discounts with varying depth
                is_cart_discount = True
                counts["cart_discount_orders"] += 1
                coupon_tier = disc_selector % 5
                if coupon_tier == 0:
                    coupon_code = "WELCOME10"
                    coupon_pct = 0.10
                elif coupon_tier == 1:
                    coupon_code = "VIP15"
                    coupon_pct = 0.15
                elif coupon_tier == 2:
                    coupon_code = "SAVE20"
                    coupon_pct = 0.20
                elif coupon_tier == 3:
                    coupon_code = "SUMMER25"
                    coupon_pct = 0.25
                else:
                    coupon_code = "FLASH35"
                    coupon_pct = 0.35
            elif disc_selector < 32:
                # 10% Compare-at catalog markdown
                is_compare_at_discount = True
                counts["compare_at_discount_orders"] += 1
            elif disc_selector < 38:
                # 6% Stacked discounts (Product markdown + Cart coupon)
                is_stacked_discount = True
                coupon_code = "STACK15"
                coupon_pct = 0.15
                counts["stacked_discount_orders"] += 1

        line_items = []
        sidecar_lines = []
        order_subtotal = 0.0

        for line_idx in range(num_lines):
            line_item_id_counter += 1
            line_item_id = line_item_id_counter

            cogs_injection_seed = (order_idx * 13 + line_idx) % 100
            is_cogs_missing = False
            is_cogs_corrupted = False
            corrupted_type = None
            expected_cogs_tier = "inventory_item"
            is_tier4 = False

            if has_free_gift and line_idx == 0:
                v_id = random.choice(regular_variant_ids)
                sku_info = by_variant_id[v_id]
                injected_cogs = sku_info["true_cogs"]
            elif cogs_injection_seed < 2:
                is_cogs_corrupted = True
                counts["corrupted_cogs_lines"] += 1
                v_id = random.choice(regular_variant_ids)
                sku_info = by_variant_id[v_id]
                sub_type = cogs_injection_seed % 3
                if sub_type == 0:
                    injected_cogs = round(sku_info["original_price"] * 2.5, 2)
                    corrupted_type = "cost_exceeds_price"
                elif sub_type == 1:
                    injected_cogs = 0.0
                    corrupted_type = "zero_cost_non_free"
                else:
                    injected_cogs = -15.0
                    corrupted_type = "negative_cost"
                expected_cogs_tier = "quarantine_corrupted"
            elif cogs_injection_seed < 17:
                is_cogs_missing = True
                counts["missing_cogs_lines"] += 1
                injected_cogs = None
                tier_selector = (order_idx + line_idx) % 20

                if tier_selector < 10:
                    expected_cogs_tier = "historical"
                    counts["tier1_historical_cogs"] += 1
                    v_id = random.choice(regular_variant_ids)
                    sku_info = by_variant_id[v_id]
                elif tier_selector < 16:
                    expected_cogs_tier = "category_estimate"
                    counts["tier2_category_cogs"] += 1
                    v_id = random.choice(tier2_variant_ids)
                    sku_info = by_variant_id[v_id]
                elif tier_selector < 19:
                    expected_cogs_tier = "storewide_default"
                    counts["tier3_storewide_cogs"] += 1
                    v_id = random.choice(tier3_variant_ids)
                    sku_info = by_variant_id[v_id]
                else:
                    expected_cogs_tier = "unresolved"
                    counts["tier4_unresolved_cogs"] += 1
                    v_id = random.choice(regular_variant_ids)
                    sku_info = by_variant_id[v_id]
                    is_tier4 = True
            else:
                v_id = random.choice(regular_variant_ids)
                sku_info = by_variant_id[v_id]
                injected_cogs = sku_info["true_cogs"]
                historical_cost_log[v_id].append((order_time, sku_info["true_cogs"]))

            qty = random.randint(10, 50) if is_wholesale else random.randint(1, 3)
            original_price = sku_info["original_price"]
            unit_price = original_price
            compare_at_price = original_price
            line_discount_amount = 0.0

            is_this_line_free_gift = (has_free_gift and line_idx == 0)
            if is_this_line_free_gift:
                unit_price = 0.0
                line_discount_amount = round(original_price * qty, 2)
            elif is_tier4:
                original_price = 0.0
                unit_price = 0.0
                compare_at_price = None
            elif is_compare_at_discount:
                markdown_pct = 0.15 if (line_idx % 2 == 0) else 0.25
                unit_price = round(original_price * (1.0 - markdown_pct), 2)
                compare_at_price = original_price
            elif is_stacked_discount:
                line_discount_pct = 0.10
                line_discount_amount = round(original_price * qty * line_discount_pct, 2)

            current_qty = qty
            if is_physical_return and line_idx == 0:
                returned_qty = 1
                current_qty = max(0, qty - returned_qty)
            elif is_fully_refunded:
                current_qty = 0

            # Expose and preserve all Shopify discount fields
            line_item = {
                "id": line_item_id,
                "variant_id": v_id if not is_tier4 else None,
                "product_id": sku_info["product_id"],
                "sku": sku_info["sku"],
                "title": f"Item {sku_info['sku']}",
                "price": str(unit_price),
                "original_unit_price": str(original_price),
                "discounted_unit_price": str(unit_price),
                "quantity": qty,
                "current_quantity": current_qty,
                "total_discount": str(line_discount_amount),
                "line_discount_amount": str(line_discount_amount),
                "line_discount_percentage": round((line_discount_amount / (original_price * qty) * 100.0), 2) if original_price * qty > 0 else 0.0,
                "discount_allocations": [],
                "is_free_gift": is_this_line_free_gift
            }

            variant_payload = {
                "id": v_id,
                "product_id": sku_info["product_id"],
                "sku": sku_info["sku"],
                "price": str(original_price),
                "compare_at_price": str(compare_at_price) if compare_at_price else None,
                "inventory_item_id": sku_info["inventory_item_id"],
                "inventory_item": {
                    "id": sku_info["inventory_item_id"],
                    "cost": str(injected_cogs) if injected_cogs is not None else None
                }
            }

            line_items.append({
                "line_item": line_item,
                "variant": variant_payload
            })

            line_gross = unit_price * qty
            order_subtotal += line_gross

            sidecar_lines.append({
                "line_item_id": line_item_id,
                "sku": sku_info["sku"],
                "variant_id": v_id,
                "quantity": qty,
                "current_quantity": current_qty,
                "original_price": original_price,
                "true_cogs": sku_info["true_cogs"],
                "injected_cogs": injected_cogs,
                "is_cogs_missing": is_cogs_missing,
                "is_cogs_corrupted": is_cogs_corrupted,
                "corrupted_type": corrupted_type,
                "expected_cogs_tier": expected_cogs_tier,
                "target_margin": sku_info["target_margin"],
                "target_margin_source": sku_info["margin_source"],
                "is_free_gift": is_this_line_free_gift
            })

        # Calculate Cart / Order-level discount amount and allocate proportionally
        total_discounts = 0.0
        if is_cart_discount or is_stacked_discount:
            total_discounts = round(order_subtotal * coupon_pct, 2)

        if total_discounts > 0 and order_subtotal > 0:
            allocated_so_far = 0.0
            for idx, item_wrapper in enumerate(line_items):
                li = item_wrapper["line_item"]
                line_val = float(li["price"]) * li["quantity"]
                if idx == len(line_items) - 1:
                    alloc = round(total_discounts - allocated_so_far, 2)
                else:
                    alloc = round(total_discounts * (line_val / order_subtotal), 2)
                    allocated_so_far += alloc
                li["discount_allocations"].append({
                    "amount": str(alloc),
                    "code": coupon_code,
                    "discount_application_index": 0
                })

        refunds = []
        cash_refund_amount = 0.0
        if is_partial_cash_refund:
            cash_refund_amount = min(30.0, round(order_subtotal * 0.25, 2))
            refunds.append({
                "id": 8800000000 + order_idx,
                "order_id": order_id,
                "created_at": (order_time + timedelta(hours=2)).isoformat(),
                "refund_line_items": [],
                "transactions": [{
                    "amount": str(cash_refund_amount),
                    "kind": "refund",
                    "status": "success"
                }]
            })
        elif is_physical_return:
            refunds.append({
                "id": 8800000000 + order_idx,
                "order_id": order_id,
                "created_at": (order_time + timedelta(hours=4)).isoformat(),
                "refund_line_items": [{
                    "line_item_id": line_items[0]["line_item"]["id"],
                    "quantity": 1,
                    "subtotal": line_items[0]["line_item"]["price"]
                }],
                "transactions": [{
                    "amount": str(line_items[0]["line_item"]["price"]),
                    "kind": "refund",
                    "status": "success"
                }]
            })
        elif is_fully_refunded:
            refund_lines = [
                {
                    "line_item_id": itm["line_item"]["id"],
                    "quantity": itm["line_item"]["quantity"],
                    "subtotal": str(float(itm["line_item"]["price"]) * itm["line_item"]["quantity"])
                }
                for itm in line_items
            ]
            refunds.append({
                "id": 8800000000 + order_idx,
                "order_id": order_id,
                "created_at": (order_time + timedelta(hours=1)).isoformat(),
                "refund_line_items": refund_lines,
                "transactions": [{
                    "amount": str(round(order_subtotal, 2)),
                    "kind": "refund",
                    "status": "success"
                }]
            })

        total_price = max(0.0, round(order_subtotal - total_discounts, 2))
        order_total_discount_sum = round(total_discounts + sum(float(itm["line_item"]["total_discount"]) for itm in line_items), 2)

        order_record = {
            "id": order_id,
            "name": f"#{order_id}",
            "created_at": order_time.isoformat(),
            "financial_status": "refunded" if is_fully_refunded else ("partially_paid" if is_partial_cash_refund else "paid"),
            "cancelled_at": (order_time + timedelta(minutes=30)).isoformat() if is_cancelled else None,
            "total_discounts": str(order_total_discount_sum),
            "discount_applications": [{
                "type": "discount_code",
                "code": coupon_code,
                "value": str(total_discounts),
                "value_type": "percentage"
            }] if coupon_code else [],
            "total_price": str(total_price),
            "subtotal_price": str(round(order_subtotal, 2)),
            "line_items": [itm["line_item"] for itm in line_items],
            "refunds": refunds,
            "_variants": [itm["variant"] for itm in line_items]
        }

        sidecar[str(order_id)] = {
            "order_id": order_id,
            "created_at": order_time.isoformat(),
            "is_cancelled": is_cancelled,
            "is_fully_refunded": is_fully_refunded,
            "is_wholesale": is_wholesale,
            "is_zero_discount_window": is_in_zero_discount_window,
            "lines": sidecar_lines,
            "cart_discounts": total_discounts,
            "cash_refund_amount": cash_refund_amount
        }

        orders.append(order_record)

    num_duplicates = int(total_orders * 0.005)
    dup_sample = random.sample(orders, num_duplicates)
    for dup in dup_sample:
        orders.append(dup)
        counts["duplicate_payload_records"] += 1

    return {
        "orders": orders,
        "sidecar": sidecar,
        "counts": counts,
        "historical_cost_log": historical_cost_log
    }

def save_all_dataset_files(catalog_products: List[Dict[str, Any]], result: Dict[str, Any]) -> None:
    """Saves generated dataset files to f01/data directory."""
    target_dirs = [os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data"))]
    for d in target_dirs:
        os.makedirs(d, exist_ok=True)

    print("Saving synthetic catalog...")
    for d in target_dirs:
        with open(os.path.join(d, "synthetic_catalog.json"), "w", encoding="utf-8") as f:
            json.dump(catalog_products, f)

    print("Saving synthetic orders...")
    for d in target_dirs:
        with open(os.path.join(d, "synthetic_orders.json"), "w", encoding="utf-8") as f:
            json.dump(result["orders"], f)

    print("Saving ground truth sidecar...")
    for d in target_dirs:
        with open(os.path.join(d, "ground_truth_sidecar.json"), "w", encoding="utf-8") as f:
            json.dump(result["sidecar"], f)

    print("Saving historical cost index...")
    serializable_log = {
        str(vid): [{"time": t.isoformat(), "cost": c} for t, c in log]
        for vid, log in result["historical_cost_log"].items()
    }
    for d in target_dirs:
        with open(os.path.join(d, "historical_cost_index.json"), "w", encoding="utf-8") as f:
            json.dump(serializable_log, f)

if __name__ == "__main__":
    print("Generating catalog with pricing headroom...")
    catalog_data = generate_catalog(num_skus=600)
    print(f"Generated {len(catalog_data['products'])} products.")

    print("Generating orders and sidecar...")
    result = generate_orders_and_sidecar(catalog_data, total_orders=50000)

    print("Saving files across root and data/...")
    save_all_dataset_files(catalog_data["products"], result)

    print("Generation complete! Injection counts:")
    print(json.dumps(result["counts"], indent=2))
