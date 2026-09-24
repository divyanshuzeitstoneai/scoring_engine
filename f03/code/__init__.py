"""
Formula F03 Code Package (Margin Floor Breach).
Exports 25-step granular pipeline, models, and evaluators.
"""

from f03.code.models import (
    EvaluabilityStatus,
    LineItemGranular,
    OrderShippingGranular,
    F03OrderEvaluation,
)
from f03.code.pipeline import evaluate_f03_order, round_cents
from f03.code.preflight import (
    ShopifyOAuthScopeDenied,
    REQUIRED_SCOPES,
    verify_shopify_oauth_scopes,
)

__all__ = [
    "EvaluabilityStatus",
    "LineItemGranular",
    "OrderShippingGranular",
    "F03OrderEvaluation",
    "evaluate_f03_order",
    "round_cents",
    "ShopifyOAuthScopeDenied",
    "REQUIRED_SCOPES",
    "verify_shopify_oauth_scopes",
]
