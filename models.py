"""
Backward-compatibility re-export for models module.
"""

from core.fallbacks.cogs import CogsSource
from core.fallbacks.margin import TargetMarginSource
from core.shopify_models import (
    DiscountAllocation,
    InventoryItem,
    LineItem,
    Metafield,
    Order,
    Product,
    ProductVariant,
    Refund,
    RefundLineItem,
    RefundTransaction,
)
from formulas.f01_discount_leakage.models import (
    BatchEvaluationResult,
    HealthBand,
    InputConfidence,
    LineItemEvaluation,
    OrderEvaluation,
    OrderStatus,
)
