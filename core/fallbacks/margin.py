"""
Reusable Target Margin Fallback Ladder and 90-Day Rolling Margin Specification.

BUSINESS RULES & PRIORITY:
1. Tier 1: SKU-level Metafield Override (namespace: custom, key: target_margin)
2. Tier 2: Product-specific margin -> merchant-configured product margin table
3. Tier 3: Shopify Standard Product Category Taxonomy -> merchant-configured margin table
4. Tier 4: product.product_type -> merchant-configured margin table
5. Tier 5: 90-Day Rolling Historical Target Margin (qualifying standard transactions)
6. Tier 6: Storewide Default: 0.35 (Configured Business Benchmark, flagged is_target_margin_estimated = True)

90-DAY ROLLING HISTORICAL METHODOLOGY SPECIFICATION:
- Window: Exact [order_time - 90 days, order_time)
- Qualifying Transactions: Completed, non-cancelled, non-refunded transactions.
- Realized Margin Basis: (Net Revenue - Direct COGS) / Net Revenue.
- Outlier Treatment: Filter transactions with realized margin outside [-0.50, +0.95].
- Minimum Threshold: Minimum 5 transactions in the 90-day window required to establish statistical significance.
- Insufficient Data: If < 5 transactions exist, cascade to Tier 6 Storewide Default.
"""

from datetime import datetime
from typing import Any, Callable, Dict, List, Literal, Optional, Tuple, Union
from core.shopify_models import Metafield

# Defined Business Configuration Rule:
# Contractual minimum gross margin floor benchmark for unmapped catalog items lacking higher-tier definitions.
STOREWIDE_DEFAULT_TARGET_MARGIN = 0.35
TargetMarginSource = Literal["metafield", "product_margin", "taxonomy", "product_type", "historical_margin", "storewide_default"]

PRODUCT_MARGIN_TABLE: Dict[str, float] = {}

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

def resolve_target_margin(
    metafields: Optional[List[Union[Dict[str, Any], Metafield]]] = None,
    product_id: Optional[int] = None,
    category_name: Optional[str] = None,
    product_type: Optional[str] = None,
    product_margin_table: Optional[Dict[str, float]] = None,
    category_margin_table: Optional[Dict[str, float]] = None,
    product_type_margin_table: Optional[Dict[str, float]] = None,
    variant_id: Optional[int] = None,
    order_created_at: Optional[datetime] = None,
    historical_margin_fn: Optional[Callable[[int, datetime], Optional[float]]] = None
) -> Tuple[float, TargetMarginSource, bool]:
    """
    Executes the multi-tier target margin cascade.
    Returns: (target_margin_used, target_margin_source, is_target_margin_estimated)

    Traceability:
    - Tier 1: custom.target_margin Metafield override (SKU/Variant-specific)
    - Tier 2: Product-specific margin match in merchant product margin table
    - Tier 3: Taxonomy category match in merchant margin table
    - Tier 4: product.product_type match in merchant margin table
    - Tier 5: 90-Day rolling historical realized margin
    - Tier 6: Storewide default 0.35 (Configured business baseline benchmark)
    """
    # Default to standard merchant tables if not explicitly overridden
    if product_margin_table is None:
        product_margin_table = PRODUCT_MARGIN_TABLE
    if category_margin_table is None:
        category_margin_table = CATEGORY_MARGIN_TABLE
    if product_type_margin_table is None:
        product_type_margin_table = PRODUCT_TYPE_MARGIN_TABLE

    # Tier 1: SKU-level Metafield Override (namespace: 'custom', key: 'target_margin')
    if metafields:
        for mf in metafields:
            if isinstance(mf, dict):
                ns = mf.get("namespace")
                key = mf.get("key")
                val = mf.get("value")
            else:
                ns = getattr(mf, "namespace", None)
                key = getattr(mf, "key", None)
                val = getattr(mf, "value", None)

            if ns == "custom" and key == "target_margin" and val is not None:
                try:
                    margin_val = float(val)
                    if 0.0 <= margin_val <= 1.0:
                        return margin_val, "metafield", False
                except (ValueError, TypeError):
                    pass

    # Tier 2: Product-specific margin
    if product_id is not None and product_margin_table:
        if product_id in product_margin_table:
            return product_margin_table[product_id], "product_margin", False
        if str(product_id) in product_margin_table:
            return product_margin_table[str(product_id)], "product_margin", False
        if isinstance(product_id, str) and product_id.isdigit() and int(product_id) in product_margin_table:
            return product_margin_table[int(product_id)], "product_margin", False

    # Tier 3: Shopify Standard Product Category Taxonomy
    if category_name and category_margin_table and category_name in category_margin_table:
        return category_margin_table[category_name], "taxonomy", False

    # Tier 4: Product Type
    if product_type and product_type_margin_table and product_type in product_type_margin_table:
        return product_type_margin_table[product_type], "product_type", False

    # Tier 5: 90-Day Rolling Historical Target Margin
    if historical_margin_fn is not None and variant_id is not None and order_created_at is not None:
        hist_margin = historical_margin_fn(variant_id, order_created_at)
        if hist_margin is not None and 0.0 <= hist_margin <= 1.0:
            return hist_margin, "historical_margin", True

    # Tier 6: Storewide Default (Configured business benchmark)
    return STOREWIDE_DEFAULT_TARGET_MARGIN, "storewide_default", True
