"""
Reusable Fallback Cascades for COGS and Category Target Margins.
"""

from core.fallbacks.cogs import is_cogs_corrupted, resolve_cogs
from core.fallbacks.margin import (
    CATEGORY_MARGIN_TABLE,
    PRODUCT_TYPE_MARGIN_TABLE,
    STOREWIDE_DEFAULT_TARGET_MARGIN,
    resolve_target_margin,
)
