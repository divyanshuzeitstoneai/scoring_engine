"""
Reusable 4-Tier COGS Cascade and Input-Sanity Guard.

BUSINESS RULES:
1. Input-Sanity Guard:
   - Detects corrupted COGS (negative cost, cost > selling price, cost == $0 on non-free item).
   - Routes corrupted records to Quarantine (TC-09).
2. 4-Tier Fallback Cascade for Missing COGS:
   - Tier 1: Historical lookup within 90 days for variant_id (TC-05).
   - Tier 2: Category imputation: original_price * (1 - category_target_margin) (TC-06).
   - Tier 3: Storewide fallback: original_price * (1 - 0.35) (TC-07).
   - Tier 4: Quarantine: cogs_source = "unresolved", is_cogs_estimated = True (TC-08).
"""

from datetime import datetime
from typing import Any, Callable, Literal, Optional, Tuple

# Defined Business Configuration Rule:
# Import from the canonical margin module so there is exactly ONE declared source of truth
# for the storewide fallback benchmark. Do NOT declare a second copy here.
from core.fallbacks.margin import STOREWIDE_DEFAULT_TARGET_MARGIN as STOREWIDE_DEFAULT_MARGIN
CogsSource = Literal["inventory_item", "historical", "category_estimate", "storewide_default", "unresolved"]

def is_cogs_corrupted(
    cost: float,
    original_price: float,
    unit_price: float,
    is_free_gift: bool = False
) -> Tuple[bool, Optional[str]]:
    """
    Input-sanity guard detecting corrupted/implausible COGS values.
    Exercises TC-09 (corrupted COGS routed to quarantine, not accepted as-is).
    """
    # 1. Negative cost
    if cost < 0.0:
        return True, "negative_cost"

    # 2. Zero cost on non-free item
    benchmark_price = max(original_price, unit_price)
    if cost == 0.0 and benchmark_price > 0.0 and not is_free_gift:
        return True, "zero_cost_non_free_item"

    # 3. Cost exceeding selling / benchmark price
    if benchmark_price > 0.0 and cost > benchmark_price:
        return True, "cost_exceeds_price"

    return False, None

def resolve_cogs(
    raw_cost: Optional[Any],
    original_price: float,
    unit_price: float,
    variant_id: Optional[int] = None,
    order_created_at: Optional[datetime] = None,
    category_target_margin: Optional[float] = None,
    is_category_margin_configured: bool = True,
    historical_lookup_fn: Optional[Callable[[int, datetime], Optional[float]]] = None,
    is_free_gift: bool = False,
    force_unresolved: bool = False
) -> Tuple[float, CogsSource, bool, bool, Optional[str]]:
    """
    Executes the COGS resolution cascade.
    Returns:
      (cogs_used, cogs_source, is_cogs_estimated, is_quarantined, quarantine_reason)

    Traceability:
    - TC-09: Implausible/corrupted COGS -> routed to quarantine via input-sanity guard.
    - TC-05: Missing COGS resolved via historical lookup (Tier 1).
    - TC-06: Missing COGS resolved via category imputation (Tier 2).
    - TC-07: Missing COGS resolved via storewide fallback (Tier 3).
    - TC-08: Missing COGS unresolved at all tiers -> quarantined.
    """
    # Case A: Raw COGS provided in inventory_item
    if raw_cost is not None and str(raw_cost).strip() != "":
        try:
            cost = float(raw_cost)
            # Apply Input-Sanity Guard (TC-09)
            corrupted, reason = is_cogs_corrupted(cost, original_price, unit_price, is_free_gift)
            if corrupted:
                return 0.0, "unresolved", True, True, f"sanity_guard_{reason}"

            # Valid raw COGS from Shopify InventoryItem
            return cost, "inventory_item", False, False, None
        except (ValueError, TypeError):
            return 0.0, "unresolved", True, True, "sanity_guard_invalid_numeric"

    # Case B: Missing COGS -> Run 4-Tier Fallback Cascade
    # Tier 1: Historical 90-day lookup (TC-05)
    if historical_lookup_fn is not None and variant_id is not None and order_created_at is not None:
        historical_cost = historical_lookup_fn(variant_id, order_created_at)
        if historical_cost is not None and historical_cost > 0.0:
            corrupted, reason = is_cogs_corrupted(historical_cost, original_price, unit_price, is_free_gift)
            if not corrupted:
                return historical_cost, "historical", True, False, None

    # Tier 2: Category Target Margin Imputation (TC-06)
    if is_category_margin_configured and category_target_margin is not None and original_price > 0.0 and not force_unresolved:
        estimated_cost = round(original_price * (1.0 - category_target_margin), 2)
        return estimated_cost, "category_estimate", True, False, None

    # Tier 3: Storewide Default Imputation (0.35 margin) (TC-07)
    if original_price > 0.0 and not force_unresolved:
        estimated_cost = round(original_price * (1.0 - STOREWIDE_DEFAULT_MARGIN), 2)
        return estimated_cost, "storewide_default", True, False, None

    # Tier 4: Unresolved -> Quarantine (TC-08)
    return 0.0, "unresolved", True, True, "missing_cogs_unresolved_all_tiers"
