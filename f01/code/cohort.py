"""
Formula F01 Cohort Inclusion and Exclusion Module.

BUSINESS RULES:
- is_discounted = (order.total_discounts > 0)
                  OR (variant.compare_at_price > line_item.price)
                  OR (line_item.total_discount > 0)
                  OR (discount_allocations > 0)
                  OR (discount_applications > 0)
- Include only: financial_status IN ('paid', 'partially_paid', 'partially_refunded') AND cancelled_at IS NULL
- Exclude:
    * cancelled_at IS NOT NULL (TC-17)
    * currentQuantity == 0 across all lines / fully refunded (TC-15)
    * Draft orders / unpaid orders (financial_status not in paid/partially paid)
    * Non-discounted orders (TC-03)
"""

from typing import Any, Dict, Optional, Tuple

VALID_PAID_STATUSES = {"paid", "partially_paid", "partially_refunded"}

def is_line_discounted(
    line_item_dict: Dict[str, Any],
    variant_dict: Optional[Dict[str, Any]] = None
) -> bool:
    """
    Evaluates whether a single line item is discounted via unit markdown (compare_at_price > price),
    line-level total_discount, or discount_allocations.
    Exercises TC-04 (compare-at markdown with total_discounts = 0).
    """
    # 1. Check line-level total_discount
    line_disc = float(line_item_dict.get("total_discount") or 0.0)
    if line_disc > 0:
        return True

    # 2. Check discount allocations
    allocations = line_item_dict.get("discount_allocations") or []
    for alloc in allocations:
        if float(alloc.get("amount") or 0.0) > 0:
            return True

    # 3. Check compare_at_price markdown (TC-04)
    unit_price = float(line_item_dict.get("price") or 0.0)
    compare_at = None
    if variant_dict:
        comp_val = variant_dict.get("compare_at_price")
        if comp_val is not None and str(comp_val).strip() != "":
            compare_at = float(comp_val)

    if compare_at is not None and compare_at > unit_price:
        return True

    return False

def is_order_discounted(
    order: Dict[str, Any],
    catalog_by_variant_id: Optional[Dict[int, Any]] = None
) -> bool:
    """
    Evaluates order-level discount status according to F01 Cohort Inclusion rule:
    is_discounted = (order.total_discounts > 0) OR (variant.compare_at_price > line_item.price) OR discount_allocations
    Exercises TC-03 (zero discount -> False) and TC-04 (markdown only -> True).
    """
    # 1. Order-level total_discounts field
    order_total_discounts = float(order.get("total_discounts") or 0.0)
    if order_total_discounts > 0:
        return True

    # 2. Check discount_applications if present
    disc_apps = order.get("discount_applications") or []
    if disc_apps:
        for app in disc_apps:
            val = float(app.get("value") or 0.0)
            if val > 0:
                return True

    # 3. Check line items
    embedded_variants = {v["id"]: v for v in order.get("_variants", [])} if "_variants" in order else {}

    line_items = order.get("line_items", [])
    for li in line_items:
        v_id = li.get("variant_id")
        variant_data = embedded_variants.get(v_id)
        if not variant_data and catalog_by_variant_id and v_id in catalog_by_variant_id:
            cat_entry = catalog_by_variant_id[v_id]
            variant_data = {
                "compare_at_price": cat_entry.get("original_price"),
                "price": cat_entry.get("original_price")
            }

        if is_line_discounted(li, variant_data):
            return True

    return False

def filter_order_cohort(
    order: Dict[str, Any],
    catalog_by_variant_id: Optional[Dict[int, Any]] = None
) -> Tuple[bool, Optional[str]]:
    """
    Determines if an order qualifies for the F01 evaluation cohort.
    Returns (is_included, exclusion_reason).

    Traceability:
    - TC-17: cancelled_at is not null -> Excluded (cancelled)
    - TC-15: fully refunded (currentQuantity == 0 on all lines) -> Excluded (fully_refunded)
    - TC-03: non-discounted order -> Excluded (non_discounted)
    """
    # 1. Check order cancellation (TC-17)
    if order.get("cancelled_at") is not None:
        return False, "cancelled"

    # 2. Check for full refund / zero active quantity (TC-15)
    financial_status = (order.get("financial_status") or "").lower()
    line_items = order.get("line_items", [])
    total_active_qty = 0
    for li in line_items:
        curr_qty = li.get("current_quantity")
        if curr_qty is None:
            curr_qty = li.get("quantity", 0)
        total_active_qty += int(curr_qty)

    if total_active_qty <= 0 or financial_status == "refunded":
        return False, "fully_refunded"

    # 3. Check financial status (paid / partially_paid)
    if financial_status not in VALID_PAID_STATUSES:
        return False, f"unpaid_or_draft_status_{financial_status}"

    # 4. Check discount cohort inclusion (TC-03, TC-04, TC-20)
    if not is_order_discounted(order, catalog_by_variant_id):
        return False, "non_discounted"

    return True, None
