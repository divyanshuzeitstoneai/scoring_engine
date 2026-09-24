"""
Hierarchy A: Direct Product COGS Sourcing Waterfall.
Tier 1: Immutable Order-Placement Snapshot
Tier 2: Live InventoryItem.unitCost (flagged for historical drift)
Tier 3: Bundle BOM Explosion (via Shopify metafield or explicit component table)
Tier 4: Unresolved (Quarantined)
"""

from decimal import Decimal
from typing import Dict, Any, Optional, Tuple


def resolve_line_item_cogs(
    line_item: Dict[str, Any],
    order_snapshot: Optional[Any],
    bom_mapping: Optional[Dict[str, Any]] = None
) -> Tuple[Optional[Decimal], str, bool, bool]:
    """
    Resolves the unit COGS for a line item across the 4-tier waterfall.
    
    Returns:
        (unit_cost, cogs_source, is_cogs_missing, is_bundle)
    """
    line_id = line_item.get("id")
    variant = line_item.get("variant") or {}
    inv_item = variant.get("inventoryItem") or {}
    
    # Tier 1: Immutable Frozen Order Snapshot
    if order_snapshot is not None:
        if isinstance(order_snapshot, dict):
            # Check if keyed by line_item_id or variant_id
            if line_id in order_snapshot:
                return Decimal(str(order_snapshot[line_id])), "Tier 1 (Snapshot)", False, False
            var_id = variant.get("id")
            if var_id in order_snapshot:
                return Decimal(str(order_snapshot[var_id])), "Tier 1 (Snapshot)", False, False
        elif isinstance(order_snapshot, (int, float, str)):
            return Decimal(str(order_snapshot)), "Tier 1 (Snapshot)", False, False

    # Tier 3: Bundle BOM Explosion
    # Check if variant has metafield custom.bundle_components or line has bundle components
    bundle_meta = None
    metafields = variant.get("metafields", [])
    if isinstance(metafields, list):
        for m in metafields:
            if m.get("namespace") == "custom" and m.get("key") == "bundle_components":
                bundle_meta = m.get("value")
                break
    elif isinstance(metafields, dict):
        bundle_meta = metafields.get("custom.bundle_components")

    if not bundle_meta and bom_mapping:
        sku = variant.get("sku") or line_item.get("sku")
        if sku and sku in bom_mapping:
            bundle_meta = bom_mapping[sku]

    if bundle_meta:
        # Sum component costs
        try:
            import json
            components = json.loads(bundle_meta) if isinstance(bundle_meta, str) else bundle_meta
            total_bom_cost = Decimal("0.00")
            for comp in components:
                qty = Decimal(str(comp.get("quantity", 1)))
                comp_cost = Decimal(str(comp.get("unit_cost", 0)))
                total_bom_cost += qty * comp_cost
            if total_bom_cost > Decimal("0.00"):
                return total_bom_cost, "Tier 3 (BOM Explosion)", False, True
        except Exception:
            pass

    # Tier 2: Live Catalog unitCost
    live_cost_obj = inv_item.get("unitCost")
    if live_cost_obj and isinstance(live_cost_obj, dict):
        amt = live_cost_obj.get("amount")
        if amt is not None:
            return Decimal(str(amt)), "Tier 2 (Live Admin)", False, False
    elif live_cost_obj is not None and not isinstance(live_cost_obj, dict):
        return Decimal(str(live_cost_obj)), "Tier 2 (Live Admin)", False, False

    # Tier 4: Unresolved
    return None, "Tier 4 (Unresolved)", True, False
