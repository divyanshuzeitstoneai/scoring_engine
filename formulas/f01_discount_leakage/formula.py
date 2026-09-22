"""
Formula F01 Discount Leakage Calculation Engine.
Evaluates line-item and order-level target profit, pre-existing COGS deficit, actual gross profit,
incremental promotional margin leakage, audit confidence, and explicit F03 operational escalation.

CRITICAL ARCHITECTURAL BOUNDARY:
Excludes shipping charges, transaction processing fees, warehouse packaging, and labor.
Those operational expenses are strictly partitioned to Formula F03 (Margin Floor Breach) and F10 (Operational Drag).
F01 calculates purely promotional gross profit erosion against baseline COGS and target gross margin,
strictly separating pre-existing COGS deficits from incremental promotional leakage.
"""

from datetime import datetime
from typing import Any, Callable, Dict, List, Optional, Tuple

from core.fallbacks.cogs import resolve_cogs
from core.fallbacks.margin import (
    CATEGORY_MARGIN_TABLE,
    PRODUCT_TYPE_MARGIN_TABLE,
    resolve_target_margin,
)
from formulas.f01_discount_leakage.cohort import filter_order_cohort, is_order_discounted
from formulas.f01_discount_leakage.models import (
    InputConfidence,
    LineItemEvaluation,
    OrderEvaluation,
)

def evaluate_line_item(
    order_id: int,
    line_item: Dict[str, Any],
    variant_data: Optional[Dict[str, Any]],
    product_data: Optional[Dict[str, Any]],
    order_created_at: Optional[datetime],
    allocated_cash_refund: float,
    product_margin_table: Optional[Dict[Any, float]] = None,
    category_margin_table: Optional[Dict[str, float]] = None,
    product_type_margin_table: Optional[Dict[str, float]] = None,
    historical_lookup_fn: Optional[Callable[[int, datetime], Optional[float]]] = None,
    historical_margin_fn: Optional[Callable[[int, datetime], Optional[float]]] = None,
    force_unresolved_cogs: bool = False
) -> LineItemEvaluation:
    """
    Evaluates a single Shopify LineItem under Formula F01 with complete discount
    mechanism decomposition, pre-vs-post promotion margin separation, and inherent COGS deficit isolation.
    """
    line_id = int(line_item.get("id", 0))
    variant_id = line_item.get("variant_id")
    sku = line_item.get("sku")
    product_id = int(line_item.get("product_id")) if line_item.get("product_id") is not None else None

    purchased_qty = int(line_item.get("quantity", 1))
    current_qty = line_item.get("current_quantity")
    if current_qty is None:
        active_qty = purchased_qty
    else:
        active_qty = int(current_qty)

    unit_selling_price = float(line_item.get("price") or 0.0)

    # 1. Resolve MSRP / Original Unit Price
    # Defined Business Rule:
    # - Line-item explicit original_unit_price has top priority if present.
    # - If variant compare_at_price exists and strictly exceeds catalog price, it represents the pre-sale strike-through MSRP.
    # - Otherwise, the standard catalog list price (variant.price) is the defined MSRP.
    # - Fallback to compare_at_price if only compare_at exists, or line_item.price if catalog data is missing.
    compare_at_val = None
    catalog_price_val = None
    if variant_data:
        comp = variant_data.get("compare_at_price")
        if comp is not None and str(comp).strip() != "":
            compare_at_val = float(comp)
        cat_p = variant_data.get("price")
        if cat_p is not None and str(cat_p).strip() != "":
            catalog_price_val = float(cat_p)

    raw_orig = line_item.get("original_unit_price")
    if raw_orig is not None and str(raw_orig).strip() != "":
        original_price = float(raw_orig)
    elif compare_at_val is not None and catalog_price_val is not None and compare_at_val > catalog_price_val:
        original_price = compare_at_val
    elif catalog_price_val is not None and catalog_price_val > 0.0:
        original_price = catalog_price_val
    elif compare_at_val is not None and compare_at_val > 0.0:
        original_price = compare_at_val
    elif unit_selling_price > 0.0:
        original_price = unit_selling_price
    else:
        original_price = 0.0

    is_free_gift = (unit_selling_price == 0.0 and original_price > 0.0) or (line_item.get("is_free_gift") is True)

    # 2. Resolve Target Margin (6-Tier Cascade)
    metafields = product_data.get("metafields") if product_data else None
    cat_info = product_data.get("category") if product_data else None
    category_name = cat_info.get("name") if isinstance(cat_info, dict) else (cat_info if isinstance(cat_info, str) else None)
    product_type = product_data.get("product_type") if product_data else None

    target_margin, margin_source, is_margin_estimated = resolve_target_margin(
        metafields=metafields,
        product_id=line_item.get("product_id"),
        category_name=category_name,
        product_type=product_type,
        product_margin_table=product_margin_table,
        category_margin_table=category_margin_table if category_margin_table is not None else CATEGORY_MARGIN_TABLE,
        product_type_margin_table=product_type_margin_table if product_type_margin_table is not None else PRODUCT_TYPE_MARGIN_TABLE,
        variant_id=variant_id,
        order_created_at=order_created_at,
        historical_margin_fn=historical_margin_fn
    )

    # 3. Resolve COGS (4-Tier Fallback Cascade + Sanity Guard)
    raw_cost = None
    if variant_data:
        inv_item = variant_data.get("inventory_item")
        if inv_item:
            raw_cost = inv_item.get("cost")

    cogs_used, cogs_source, is_cogs_estimated, is_quarantined, quarantine_reason = resolve_cogs(
        raw_cost=raw_cost,
        original_price=original_price,
        unit_price=unit_selling_price,
        variant_id=variant_id,
        order_created_at=order_created_at,
        category_target_margin=target_margin,
        is_category_margin_configured=(margin_source != "storewide_default"),
        historical_lookup_fn=historical_lookup_fn,
        is_free_gift=is_free_gift,
        force_unresolved=force_unresolved_cogs
    )

    # 4. Decompose Shopify Discount Mechanisms
    original_line_value = round(original_price * active_qty, 2)
    total_cogs = round(cogs_used * active_qty, 2)

    if active_qty <= 0:
        return LineItemEvaluation(
            order_id=order_id,
            line_item_id=line_id,
            sku=sku,
            variant_id=variant_id,
            quantity=purchased_qty,
            active_quantity=0,
            original_price=original_price,
            original_line_value=0.0,
            discounted_unit_price=0.0,
            line_discount_amount=0.0,
            line_discount_percentage=0.0,
            order_discount_allocation=0.0,
            total_discount_amount=0.0,
            discount_percentage=0.0,
            discount_code=None,
            discount_type="returned",
            net_selling_price=0.0,
            net_revenue=0.0,
            cogs_used=cogs_used,
            total_cogs=0.0,
            cogs_source=cogs_source,
            is_cogs_estimated=is_cogs_estimated,
            target_margin_used=target_margin,
            target_margin_source=margin_source,
            is_target_margin_estimated=is_margin_estimated,
            target_profit=0.0,
            baseline_gross_profit=0.0,
            actual_gross_profit=0.0,
            inherent_cogs_deficit=0.0,
            total_target_shortfall=0.0,
            f01_flagged=False,
            f01_dollar_loss=0.0,
            leakage_reason="healthy_after_discount",
            input_confidence="real",
            quarantine_reason=None
        )

    # Line-level discount amount (from total_discount or compare_at markdown)
    raw_line_disc = float(line_item.get("total_discount") or line_item.get("line_discount_amount") or 0.0)
    compare_at_markdown = max(0.0, (original_price - unit_selling_price) * purchased_qty) if (original_price > unit_selling_price and raw_line_disc == 0.0) else 0.0
    effective_line_disc = max(raw_line_disc, compare_at_markdown)
    line_discount_active = round((effective_line_disc * active_qty / purchased_qty) if purchased_qty > 0 else 0.0, 2)
    line_discount_pct = round((line_discount_active / original_line_value * 100.0), 2) if original_line_value > 0 else 0.0

    # Discounted unit price (price after line-level discount, before cart discount)
    if line_item.get("discounted_unit_price") is not None:
        discounted_unit_p = float(line_item["discounted_unit_price"])
    elif original_price > 0 and active_qty > 0:
        discounted_unit_p = round(max(0.0, original_price - (line_discount_active / active_qty)), 4)
    else:
        discounted_unit_p = unit_selling_price

    # Order/cart-level discount allocations
    allocations = line_item.get("discount_allocations") or []
    order_discount_allocation_total = 0.0
    discount_code = line_item.get("discount_code")
    for alloc in allocations:
        amt = float(alloc.get("amount") or 0.0)
        order_discount_allocation_total += amt
        if not discount_code and alloc.get("code"):
            discount_code = alloc.get("code")

    order_discount_allocation_active = round((order_discount_allocation_total * active_qty / purchased_qty) if purchased_qty > 0 else 0.0, 2)

    # Reconciled Total Discount (strictly avoiding double counting)
    total_discount_amount = round(line_discount_active + order_discount_allocation_active, 2)
    discount_pct = round((total_discount_amount / original_line_value * 100.0), 2) if original_line_value > 0 else 0.0

    # Net Revenue and Net Selling Price
    net_revenue = max(0.0, round(original_line_value - total_discount_amount - allocated_cash_refund, 2))
    net_selling_price = round(net_revenue / active_qty, 4)

    # Classify Discount Type
    if is_free_gift:
        disc_type = "free_gift"
    elif line_discount_active > 0 and order_discount_allocation_active > 0:
        disc_type = "stacked"
    elif line_discount_active > 0:
        disc_type = "product_markdown" if compare_at_markdown > 0 else "line_discount"
    elif order_discount_allocation_active > 0:
        disc_type = "order_discount"
    else:
        disc_type = "none"

    # 5. Pre-Promotion vs Post-Promotion Profit & Inherent COGS Deficit Isolation
    # Baseline / pre-promotion revenue = original_line_value
    # Baseline / pre-promotion gross profit = baseline_revenue - total_cogs
    baseline_gross_profit = round(original_line_value - total_cogs, 2)
    
    # Target Minimum Profit = original_line_value * target_margin
    target_profit = round(original_line_value * target_margin, 2)
    
    # Actual realized post-promotion gross profit = net_revenue - total_cogs
    actual_gross_profit = round(net_revenue - total_cogs, 2)

    # Inherent COGS Deficit: shortfall existing BEFORE applying promotion
    inherent_cogs_deficit = max(0.0, round(target_profit - baseline_gross_profit, 2))

    # Total Target Shortfall: total gap between target and actual
    total_target_shortfall = max(0.0, round(target_profit - actual_gross_profit, 2))

    # Incremental Promotional Leakage: shortfall caused specifically by promotional discount
    incremental_promotional_leakage = max(0.0, round(total_target_shortfall - inherent_cogs_deficit, 2))

    # Flag and Dollar Loss assignment
    line_flagged = bool(incremental_promotional_leakage > 0.0)
    line_loss = incremental_promotional_leakage

    # 6. Leakage Reason Classification (Mutually Exclusive & Informative)
    if is_quarantined or cogs_source == "unresolved":
        leakage_reason = "data_quality_issue"
    elif actual_gross_profit >= target_profit:
        leakage_reason = "healthy_after_discount"
    elif is_free_gift:
        leakage_reason = "100_percent_free_gift"
    elif inherent_cogs_deficit > 0.0 and incremental_promotional_leakage > 0.0:
        leakage_reason = "promotional_leakage_plus_pre_existing_deficit"
    elif inherent_cogs_deficit > 0.0 and incremental_promotional_leakage == 0.0:
        leakage_reason = "pre_existing_margin_deficit"
    elif incremental_promotional_leakage > 0.0:
        leakage_reason = "promotional_leakage"
    else:
        leakage_reason = "healthy_after_discount"

    # 7. Confidence Classification
    if is_quarantined or cogs_source == "unresolved":
        confidence: InputConfidence = "quarantined"
    elif cogs_source == "storewide_default" or margin_source == "storewide_default":
        confidence = "storewide_fallback"
    elif is_cogs_estimated or is_margin_estimated:
        confidence = "estimated"
    else:
        confidence = "real"

    return LineItemEvaluation(
        order_id=order_id,
        line_item_id=line_id,
        sku=sku,
        variant_id=variant_id,
        quantity=purchased_qty,
        active_quantity=active_qty,
        original_price=original_price,
        original_line_value=original_line_value,
        discounted_unit_price=discounted_unit_p,
        line_discount_amount=line_discount_active,
        line_discount_percentage=line_discount_pct,
        order_discount_allocation=order_discount_allocation_active,
        total_discount_amount=total_discount_amount,
        discount_percentage=discount_pct,
        discount_code=discount_code,
        discount_type=disc_type,
        net_selling_price=net_selling_price,
        net_revenue=net_revenue,
        cogs_used=cogs_used,
        total_cogs=total_cogs,
        cogs_source=cogs_source,
        is_cogs_estimated=is_cogs_estimated,
        target_margin_used=target_margin,
        target_margin_source=margin_source,
        is_target_margin_estimated=is_margin_estimated,
        target_profit=target_profit,
        baseline_gross_profit=baseline_gross_profit,
        actual_gross_profit=actual_gross_profit,
        inherent_cogs_deficit=inherent_cogs_deficit,
        total_target_shortfall=total_target_shortfall,
        f01_flagged=line_flagged,
        f01_dollar_loss=line_loss,
        leakage_reason=leakage_reason,
        input_confidence=confidence,
        quarantine_reason=quarantine_reason,
        cash_refund_allocated=allocated_cash_refund,
        product_id=product_id
    )

def evaluate_order(
    order: Dict[str, Any],
    catalog_by_variant_id: Optional[Dict[int, Any]] = None,
    catalog_by_product_id: Optional[Dict[int, Any]] = None,
    product_margin_table: Optional[Dict[Any, float]] = None,
    category_margin_table: Optional[Dict[str, float]] = None,
    product_type_margin_table: Optional[Dict[str, float]] = None,
    historical_lookup_fn: Optional[Callable[[int, datetime], Optional[float]]] = None,
    historical_margin_fn: Optional[Callable[[int, datetime], Optional[float]]] = None,
    force_unresolved_cogs: bool = False,
    skip_cohort_filter: bool = False
) -> OrderEvaluation:
    """
    Evaluates an entire Shopify Order against F01 discount leakage criteria.
    Aggregates line-item target profit, baseline profit, inherent deficit, actual profit,
    and incremental promotional loss.
    Strictly isolates product gross margin from F03 operational cash escalation.
    """
    if category_margin_table is None:
        category_margin_table = CATEGORY_MARGIN_TABLE
    if product_type_margin_table is None:
        product_type_margin_table = PRODUCT_TYPE_MARGIN_TABLE

    order_id = int(order["id"])

    # 1. Cohort Filtering
    is_disc = is_order_discounted(order, catalog_by_variant_id)
    if not skip_cohort_filter:
        is_included, exclusion_reason = filter_order_cohort(order, catalog_by_variant_id)
        if not is_included:
            return OrderEvaluation(
                order_id=order_id,
                status="excluded",
                is_discounted=is_disc,
                exclusion_reason=exclusion_reason,
                total_original_value=0.0,
                total_net_revenue=0.0,
                total_discounts=0.0,
                total_cogs=0.0,
                target_minimum_profit=0.0,
                baseline_gross_profit=0.0,
                actual_gross_profit=0.0,
                inherent_cogs_deficit=0.0,
                total_target_shortfall=0.0,
                f01_flagged=False,
                f01_dollar_loss=0.0,
                negative_gross_profit=False,
                shipping_revenue_collected=0.0,
                carrier_shipping_cost=None,
                gateway_processing_fee=None,
                other_f03_costs=0.0,
                actual_cash_contribution=None,
                f03_escalation_status="unable_to_determine",
                f03_escalation_reason="order_excluded_from_cohort",
                input_confidence="real",
                line_items=[]
            )
    else:
        exclusion_reason = None

    raw_created_at = order.get("created_at")
    order_time = None
    if raw_created_at:
        try:
            order_time = datetime.fromisoformat(raw_created_at.replace("Z", "+00:00"))
        except Exception:
            order_time = None

    # Monetary Cash Refund allocation
    total_cash_refund = 0.0
    for ref in order.get("refunds", []):
        ref_lines = ref.get("refund_line_items", [])
        if not ref_lines:
            for tx in ref.get("transactions", []):
                if tx.get("status") == "success":
                    total_cash_refund += float(tx.get("amount") or 0.0)

    line_items = order.get("line_items", [])
    active_line_revenues = []
    total_active_gross = 0.0
    for li in line_items:
        curr_q = li.get("current_quantity")
        if curr_q is None:
            curr_q = li.get("quantity", 1)
        active_q = int(curr_q)
        line_gross = float(li.get("price") or 0.0) * active_q
        active_line_revenues.append(line_gross)
        total_active_gross += line_gross

    embedded_variants = {v["id"]: v for v in order.get("_variants", [])} if "_variants" in order else {}

    evaluated_lines: List[LineItemEvaluation] = []
    has_quarantine = False
    quarantine_reasons = []

    for idx, li in enumerate(line_items):
        v_id = li.get("variant_id")
        p_id = li.get("product_id")

        variant_data = embedded_variants.get(v_id)
        if not variant_data and catalog_by_variant_id and v_id in catalog_by_variant_id:
            cat_entry = catalog_by_variant_id[v_id]
            variant_data = {
                "id": v_id,
                "price": str(cat_entry["original_price"]),
                "compare_at_price": str(cat_entry["original_price"]),
                "inventory_item": {"cost": str(cat_entry["true_cogs"])}
            }

        product_data = None
        if catalog_by_product_id and p_id in catalog_by_product_id:
            product_data = catalog_by_product_id[p_id]
        elif catalog_by_variant_id and v_id in catalog_by_variant_id:
            cat_entry = catalog_by_variant_id[v_id]
            product_data = {
                "product_type": cat_entry.get("product_type"),
                "category": {"name": cat_entry.get("category")} if cat_entry.get("category") else None,
                "metafields": [
                    {
                        "namespace": "custom",
                        "key": "target_margin",
                        "value": str(cat_entry["metafield_margin"])
                    }
                ] if cat_entry.get("metafield_margin") is not None else []
            }

        line_cash_alloc = 0.0
        if total_cash_refund > 0 and total_active_gross > 0:
            line_cash_alloc = total_cash_refund * (active_line_revenues[idx] / total_active_gross)

        line_eval = evaluate_line_item(
            order_id=order_id,
            line_item=li,
            variant_data=variant_data,
            product_data=product_data,
            order_created_at=order_time,
            allocated_cash_refund=line_cash_alloc,
            product_margin_table=product_margin_table,
            category_margin_table=category_margin_table,
            product_type_margin_table=product_type_margin_table,
            historical_lookup_fn=historical_lookup_fn,
            historical_margin_fn=historical_margin_fn,
            force_unresolved_cogs=force_unresolved_cogs
        )
        evaluated_lines.append(line_eval)

        if line_eval.input_confidence == "quarantined" or line_eval.cogs_source == "unresolved":
            has_quarantine = True
            quarantine_reasons.append(f"Line {line_eval.line_item_id}: {line_eval.quarantine_reason or line_eval.cogs_source}")

    order_orig_val = round(sum(l.original_line_value for l in evaluated_lines), 2)
    order_net_rev = round(sum(l.net_revenue for l in evaluated_lines), 2)
    order_total_disc = round(sum(l.total_discount_amount for l in evaluated_lines), 2)
    order_total_cogs = round(sum(l.total_cogs for l in evaluated_lines), 2)
    order_target_profit = round(sum(l.target_profit for l in evaluated_lines), 2)
    order_baseline_profit = round(sum(l.baseline_gross_profit for l in evaluated_lines), 2)
    order_actual_profit = round(sum(l.actual_gross_profit for l in evaluated_lines), 2)
    order_inherent_deficit = round(sum(l.inherent_cogs_deficit for l in evaluated_lines), 2)
    order_target_shortfall = round(sum(l.total_target_shortfall for l in evaluated_lines), 2)

    # Canonical Line-Aggregated Promotional Leakage:
    order_promo_loss = round(sum(l.f01_dollar_loss for l in evaluated_lines), 2)
    f01_flagged = bool(is_disc and (order_promo_loss > 0.0))
    neg_gross = bool(order_actual_profit < 0.0)

    # F03 Operational Cash Contribution & Escalation Determination:
    shipping_collected = float(
        order.get("total_shipping_price") or 
        order.get("current_shipping_price_set", {}).get("shop_money", {}).get("amount") or 0.0
    )
    raw_carrier_cost = order.get("carrier_shipping_cost")
    raw_gateway_fee = order.get("gateway_fee") or order.get("transaction_fee")
    
    carrier_shipping_cost = float(raw_carrier_cost) if raw_carrier_cost is not None else None
    gateway_processing_fee = float(raw_gateway_fee) if raw_gateway_fee is not None else None
    other_costs = float(order.get("other_f03_costs") or 0.0)

    if carrier_shipping_cost is not None and gateway_processing_fee is not None:
        actual_cash_contrib = round(order_actual_profit + shipping_collected - carrier_shipping_cost - gateway_processing_fee - other_costs, 2)
        if actual_cash_contrib < 0.0:
            f03_status = "escalated"
            f03_reason = "cash_floor_breach_negative_net_cash"
        else:
            f03_status = "not_escalated"
            f03_reason = "positive_cash_contribution"
    else:
        actual_cash_contrib = None
        f03_status = "unable_to_determine"
        f03_reason = "missing_f03_operational_cost_data"

    if has_quarantine:
        order_conf: InputConfidence = "quarantined"
        order_status = "quarantined"
    elif any(l.input_confidence == "storewide_fallback" for l in evaluated_lines):
        order_conf = "storewide_fallback"
        order_status = "evaluated"
    elif any(l.input_confidence == "estimated" for l in evaluated_lines):
        order_conf = "estimated"
        order_status = "evaluated"
    else:
        order_conf = "real"
        order_status = "evaluated"

    return OrderEvaluation(
        order_id=order_id,
        status=order_status,
        is_discounted=is_disc,
        total_original_value=order_orig_val,
        total_net_revenue=order_net_rev,
        total_discounts=order_total_disc,
        cash_refund=total_cash_refund,
        total_cogs=order_total_cogs,
        target_minimum_profit=order_target_profit,
        baseline_gross_profit=order_baseline_profit,
        actual_gross_profit=order_actual_profit,
        inherent_cogs_deficit=order_inherent_deficit,
        total_target_shortfall=order_target_shortfall,
        f01_flagged=f01_flagged,
        f01_dollar_loss=order_promo_loss,
        negative_gross_profit=neg_gross,
        shipping_revenue_collected=shipping_collected,
        carrier_shipping_cost=carrier_shipping_cost,
        gateway_processing_fee=gateway_processing_fee,
        other_f03_costs=other_costs,
        actual_cash_contribution=actual_cash_contrib,
        f03_escalation_status=f03_status,
        f03_escalation_reason=f03_reason,
        input_confidence=order_conf,
        line_items=evaluated_lines,
        quarantine_reason="; ".join(quarantine_reasons) if quarantine_reasons else None
    )
