"""
Formula F10 Product Contribution v2: Pure Python Decimal Reference Implementation.
Every fact is labelled and traceable.
Money is Decimal, never float.
"""

from decimal import Decimal, ROUND_HALF_UP, InvalidOperation
from typing import Any, Dict, List, Optional, Tuple
from f10.code.models import (
    CogsState,
    EvidenceTier,
    LineFact,
    VariantMetric,
    VariantStatus,
)


def quantize_amount(val: Any, minor_units: int = 2, rounding_mode: str = "ROUND_HALF_UP") -> Decimal:
    """Quantizes Decimal to configured currency precision."""
    if val is None:
        return Decimal("0.00")
    if not isinstance(val, Decimal):
        val = Decimal(str(val))
    exp = Decimal("10") ** (-minor_units)
    return val.quantize(exp, rounding=rounding_mode)


def compute_line_fact(
    line_item_id: str,
    order_id: str,
    variant_id: Optional[str],
    product_id: Optional[str],
    sku: Optional[str],
    title: str,
    cohort_date: str,
    is_matured: bool,
    # Units
    q_ordered: int,
    q_removed: int,
    q_cancelled: int,
    q_shipped: int,
    q_refunded: int,
    q_restocked: int,
    # Money
    gross_line: Decimal,
    disc_line: Decimal,
    refund_item: Decimal,
    goodwill: Decimal,
    # Cost & Valuation
    cost_snapshot: Optional[Decimal],
    cost_is_snapshot: bool,  # False if backfilled without point-in-time
    # Allocations
    carrier_cost_allocated: Decimal,
    shipping_charged_allocated: Decimal,
    pay_fees: Decimal,
    pay_fees_tier: EvidenceTier,
    # Config parameters
    config: Dict[str, Any],
    line_weight_kg: Optional[Decimal] = None
) -> LineFact:
    """
    Computes all atomic attributes for one order line item under Formula F10 v2.
    """
    minor_units = config.get("currency_minor_units", 2)
    rounding_mode = config.get("rounding_mode", "ROUND_HALF_UP")
    flags = []

    # Derived unit taxonomy (Section 5.3)
    q_not_restocked = max(0, q_refunded - q_restocked)
    q_kept = max(0, q_shipped - q_refunded)

    # Interpretation of non-restocked refunds (Decision D1 / Section 5.4)
    no_restock_policy = config.get("no_restock_policy", "lost")
    cogs_unresolved = Decimal("0.00")
    if no_restock_policy in ("lost", "kept_by_customer"):
        q_lost_returns = q_not_restocked
    else:  # "unknown"
        q_lost_returns = 0
        if q_not_restocked > 0:
            flags.append("cogs_unresolved")

    # Revenue calculation (Section 5.2)
    net_billed = gross_line - disc_line
    retained_rev = net_billed - refund_item - goodwill

    # COGS State Determination (Section 5.7)
    if cost_snapshot is None:
        cogs_state = CogsState.COGS_MISSING
        cogs_tier = EvidenceTier.T4
        flags.append("cogs_missing")
        unit_cost = Decimal("0.00")
    elif cost_snapshot == Decimal("0.00"):
        if config.get("cost_snapshot_policy") == "confirmed_zero":
            cogs_state = CogsState.COGS_OBSERVED
            cogs_tier = EvidenceTier.T2
        else:
            cogs_state = CogsState.COGS_ZERO_SUSPECT
            cogs_tier = EvidenceTier.T1 if cost_is_snapshot else EvidenceTier.T3
            flags.append("cogs_zero_suspect")
        unit_cost = Decimal("0.00")
    else:
        cogs_state = CogsState.COGS_OBSERVED
        cogs_tier = EvidenceTier.T1 if cost_is_snapshot else EvidenceTier.T3
        unit_cost = cost_snapshot

    if not cost_is_snapshot and cost_snapshot is not None:
        flags.append("cost_not_point_in_time")

    # COGS lost calculation (Section 5.4)
    # Cancelled or removed units never shipped: they carry no COGS and no shipping!
    cogs_lost = quantize_amount(Decimal(q_kept + q_lost_returns) * unit_cost, minor_units, rounding_mode)
    if no_restock_policy == "unknown" and q_not_restocked > 0 and cost_snapshot is not None:
        cogs_unresolved = quantize_amount(Decimal(q_not_restocked) * unit_cost, minor_units, rounding_mode)

    # Operational costs (Section 5.5)
    # Outbound = carrier_cost_allocated - shipping_charged_allocated
    outbound = quantize_amount(carrier_cost_allocated - shipping_charged_allocated, minor_units, rounding_mode)
    outbound_tier = EvidenceTier.T2 if config.get("carrier_cost_model") != "none" else EvidenceTier.T4

    # Physical returns definition: returns that require reverse logistics
    # Cancelled or removed units never shipped carry no COGS and no shipping/handling (Section 5.3)
    # Goodwill refunds with no physical return incur no return ship / handling
    if q_shipped > 0:
        q_physical_returns = min(q_shipped, q_restocked + (q_not_restocked if no_restock_policy == "lost" else 0))
    else:
        q_physical_returns = 0

    return_ship_val = config.get("return_ship_cost")
    handling_val = config.get("handling_cost")
    pick_pack_val = config.get("pick_pack_cost")

    return_ship_unit = Decimal(str(return_ship_val)) if return_ship_val is not None else Decimal("0.00")
    handling_unit = Decimal(str(handling_val)) if handling_val is not None else Decimal("0.00")
    pick_pack_unit = Decimal(str(pick_pack_val)) if pick_pack_val is not None else Decimal("0.00")

    return_ship = quantize_amount(Decimal(q_physical_returns) * return_ship_unit, minor_units, rounding_mode)
    handling = quantize_amount(Decimal(q_physical_returns) * handling_unit, minor_units, rounding_mode)
    packaging = quantize_amount(Decimal(q_shipped) * pick_pack_unit, minor_units, rounding_mode)

    return_ship_tier = EvidenceTier.T2
    handling_tier = EvidenceTier.T2
    packaging_tier = EvidenceTier.T2 if pick_pack_unit > 0 else EvidenceTier.T4

    # Resulting Contribution (Section 5.6)
    total_costs = cogs_lost + outbound + pay_fees + return_ship + handling + packaging
    contribution = retained_rev - total_costs

    return LineFact(
        line_item_id=line_item_id,
        order_id=order_id,
        variant_id=variant_id,
        product_id=product_id,
        sku=sku,
        title=title,
        cohort_date=cohort_date,
        is_matured=is_matured,
        q_ordered=q_ordered,
        q_removed=q_removed,
        q_cancelled=q_cancelled,
        q_shipped=q_shipped,
        q_refunded=q_refunded,
        q_restocked=q_restocked,
        q_not_restocked=q_not_restocked,
        q_lost_returns=q_lost_returns,
        q_kept=q_kept,
        q_physical_returns=q_physical_returns,
        gross_line=gross_line,
        disc_line=disc_line,
        net_billed=net_billed,
        refund_item=refund_item,
        goodwill=goodwill,
        retained_rev=retained_rev,
        cost_snapshot=cost_snapshot,
        cogs_state=cogs_state,
        cogs_tier=cogs_tier,
        cogs_lost=cogs_lost,
        cogs_unresolved=cogs_unresolved,
        carrier_cost_allocated=carrier_cost_allocated,
        shipping_charged_allocated=shipping_charged_allocated,
        outbound=outbound,
        outbound_tier=outbound_tier,
        pay_fees=pay_fees,
        pay_fees_tier=pay_fees_tier,
        return_ship=return_ship,
        return_ship_tier=return_ship_tier,
        handling=handling,
        handling_tier=handling_tier,
        packaging=packaging,
        packaging_tier=packaging_tier,
        total_costs=total_costs,
        contribution=contribution,
        flags=flags,
        line_weight_kg=line_weight_kg
    )


def rollup_variant_metrics(
    variant_id: str,
    product_id: Optional[str],
    sku: Optional[str],
    title: str,
    category: str,
    lines: List[LineFact],
    window_days: int,
    config: Dict[str, Any],
    config_hash: str = ""
) -> VariantMetric:
    """
    Rolls up LineFacts to variant level using exact ratios of sums.
    Dollar-profit metrics use only COGS_OBSERVED lines (Section 5.7).
    Unit metrics use all lines.
    """
    minor_units = config.get("currency_minor_units", 2)
    rounding_mode = config.get("rounding_mode", "ROUND_HALF_UP")
    as_of = config.get("as_of", "2024-10-31")

    # If no lines exist for this variant in the window
    if not lines:
        return VariantMetric(
            variant_id=variant_id,
            product_id=product_id,
            sku=sku,
            title=title,
            category=category,
            window_days=window_days,
            as_of=as_of,
            status=VariantStatus.NO_DATA,
            config_hash=config_hash
        )

    # Unit metrics across ALL lines (Section 5.7)
    q_ordered_total = sum(l.q_ordered for l in lines)
    q_shipped_total = sum(l.q_shipped for l in lines)
    q_refunded_total = sum(l.q_refunded for l in lines)
    q_restocked_total = sum(l.q_restocked for l in lines)
    q_not_restocked_total = sum(l.q_not_restocked for l in lines)
    q_kept_total = sum(l.q_kept for l in lines)

    return_rate = (
        quantize_amount(Decimal(q_refunded_total) / Decimal(q_shipped_total), 4, rounding_mode)
        if q_shipped_total > 0 else None
    )

    # Revenue Conservation (Gate DQ-F3 / Section 5.7)
    rev_total = sum((l.net_billed for l in lines), start=Decimal("0.00"))
    observed_lines = [l for l in lines if l.cogs_state == CogsState.COGS_OBSERVED]
    quarantined_lines = [l for l in lines if l.cogs_state != CogsState.COGS_OBSERVED]

    rev_scored = sum((l.net_billed for l in observed_lines), start=Decimal("0.00"))
    rev_quarantined = sum((l.net_billed for l in quarantined_lines), start=Decimal("0.00"))

    cost_unknown_share = (
        quantize_amount(rev_quarantined / rev_total, 4, rounding_mode)
        if rev_total > Decimal("0.00") else Decimal("0.00")
    )

    # Dollar metrics computed ONLY over matured, COGS_OBSERVED lines
    matured_observed = [l for l in observed_lines if l.is_matured]
    unmatured_count = sum(1 for l in lines if not l.is_matured)

    retained_rev = sum((l.retained_rev for l in matured_observed), start=Decimal("0.00"))
    cogs_lost = sum((l.cogs_lost for l in matured_observed), start=Decimal("0.00"))
    outbound = sum((l.outbound for l in matured_observed), start=Decimal("0.00"))
    pay_fees = sum((l.pay_fees for l in matured_observed), start=Decimal("0.00"))
    return_ship = sum((l.return_ship for l in matured_observed), start=Decimal("0.00"))
    handling = sum((l.handling for l in matured_observed), start=Decimal("0.00"))
    packaging = sum((l.packaging for l in matured_observed), start=Decimal("0.00"))
    total_costs = sum((l.total_costs for l in matured_observed), start=Decimal("0.00"))
    contribution = retained_rev - total_costs

    # Naive profit & hidden leakage
    naive_profit = sum(
        ((l.net_billed - (Decimal(l.q_shipped) * (l.cost_snapshot or Decimal("0.00"))))
        for l in matured_observed),
        start=Decimal("0.00")
    )
    hidden_leakage = naive_profit - contribution

    # Estimated share (tiers T3/T4)
    estimated_cost_sum = Decimal("0.00")
    for l in matured_observed:
        if l.cogs_tier in [EvidenceTier.T3, EvidenceTier.T4]:
            estimated_cost_sum += l.cogs_lost
        if l.outbound_tier in [EvidenceTier.T3, EvidenceTier.T4]:
            estimated_cost_sum += l.outbound
        if l.pay_fees_tier in [EvidenceTier.T3, EvidenceTier.T4]:
            estimated_cost_sum += l.pay_fees
        if l.return_ship_tier in [EvidenceTier.T3, EvidenceTier.T4]:
            estimated_cost_sum += l.return_ship
        if l.handling_tier in [EvidenceTier.T3, EvidenceTier.T4]:
            estimated_cost_sum += l.handling
        if l.packaging_tier in [EvidenceTier.T3, EvidenceTier.T4]:
            estimated_cost_sum += l.packaging

    estimated_share = (
        quantize_amount(estimated_cost_sum / total_costs, 4, rounding_mode)
        if total_costs > Decimal("0.00") else Decimal("0.00")
    )

    # MarginPct and Score computation (Section 5.6)
    margin_pct: Optional[Decimal] = None
    score: Optional[Decimal] = None

    max_unknown_share = Decimal(str(config.get("max_unknown_cost_share", "0.15")))
    min_units_for_confidence = config.get("min_units_for_confidence", 30)
    healthy_margins = config.get("healthy_margin_by_category", {})
    healthy_threshold = Decimal(str(healthy_margins.get(category, healthy_margins.get("UNMAPPED", 0.25)))) * Decimal("100")

    is_unscoreable = (cost_unknown_share > max_unknown_share)
    is_provisional = (len(matured_observed) == 0 and unmatured_count > 0)
    is_low_confidence = q_ordered_total < min_units_for_confidence
    has_unresolved_cogs = any("cogs_unresolved" in l.flags for l in lines)
    
    return_ship_param = config.get("return_ship_cost")
    return_ship_bounds = config.get("return_ship_bounds")

    if is_provisional:
        status = VariantStatus.PROVISIONAL
    elif has_unresolved_cogs:
        status = VariantStatus.UNRESOLVED
        contribution = None
        margin_pct = None
        score = None
        hidden_leakage = Decimal("0.00")
        naive_profit = Decimal("0.00")
    elif is_unscoreable:
        status = VariantStatus.UNSCOREABLE
        contribution = None
        margin_pct = None
        score = None
        hidden_leakage = Decimal("0.00")
        naive_profit = Decimal("0.00")
    elif return_ship_param is None and return_ship_bounds:
        status = VariantStatus.RANGE_ONLY
        contribution = None
        margin_pct = None
        score = None
        hidden_leakage = Decimal("0.00")
    elif return_ship_param is None:
        status = VariantStatus.INCOMPLETE_COSTS
        contribution = None
        margin_pct = None
        score = None
        hidden_leakage = Decimal("0.00")
    elif retained_rev <= Decimal("0.00") and total_costs > Decimal("0.00"):
        margin_pct = None
        score = Decimal("0.00")
        status = VariantStatus.VALUE_DESTROYING
    elif retained_rev <= Decimal("0.00"):
        margin_pct = None
        score = None
        status = VariantStatus.VALUE_DESTROYING
    else:
        margin_pct = quantize_amount((contribution / retained_rev) * Decimal("100"), 2, rounding_mode)
        score = min(Decimal("100.00"), max(Decimal("0.00"), margin_pct))
        
        if contribution < Decimal("0.00"):
            status = VariantStatus.VALUE_DESTROYING
        elif contribution == Decimal("0.00"):
            status = VariantStatus.BREAKEVEN
        elif margin_pct >= healthy_threshold:
            status = VariantStatus.HEALTHY
        else:
            status = VariantStatus.UNDERPERFORMING

    return VariantMetric(
        variant_id=variant_id,
        product_id=product_id,
        sku=sku,
        title=title,
        category=category,
        window_days=window_days,
        as_of=as_of,
        q_ordered=q_ordered_total,
        q_shipped=q_shipped_total,
        q_refunded=q_refunded_total,
        q_restocked=q_restocked_total,
        q_not_restocked=q_not_restocked_total,
        q_kept=q_kept_total,
        return_rate=return_rate,
        revenue_total=quantize_amount(rev_total, minor_units, rounding_mode),
        revenue_scored=quantize_amount(rev_scored, minor_units, rounding_mode),
        revenue_quarantined=quantize_amount(rev_quarantined, minor_units, rounding_mode),
        cost_unknown_share=cost_unknown_share,
        retained_rev=quantize_amount(retained_rev, minor_units, rounding_mode),
        cogs_lost=quantize_amount(cogs_lost, minor_units, rounding_mode),
        outbound=quantize_amount(outbound, minor_units, rounding_mode),
        pay_fees=quantize_amount(pay_fees, minor_units, rounding_mode),
        return_ship=quantize_amount(return_ship, minor_units, rounding_mode),
        handling=quantize_amount(handling, minor_units, rounding_mode),
        packaging=quantize_amount(packaging, minor_units, rounding_mode),
        total_costs=quantize_amount(total_costs, minor_units, rounding_mode),
        contribution=quantize_amount(contribution, minor_units, rounding_mode),
        margin_pct=margin_pct,
        score=score,
        naive_profit=quantize_amount(naive_profit, minor_units, rounding_mode),
        hidden_leakage=quantize_amount(hidden_leakage, minor_units, rounding_mode),
        estimated_share=estimated_share,
        status=status,
        is_provisional=is_provisional,
        is_low_confidence=is_low_confidence,
        config_hash=config_hash,
        api_version=config.get("api_version", "2024-10"),
        formula_version="v2.0"
    )
