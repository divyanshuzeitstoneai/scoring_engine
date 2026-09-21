"""
Formula F01 Aggregate Dollar-Weighted Score and Health Banding.

BUSINESS RULES:
If sum(Order Target Minimum Profit) == 0:
    F01 Score = 100.0 (TC-11 zero-safe)
Else:
    F01 Score = max(0.0, (1 - sum(F01 Dollar Loss) / sum(Order Target Minimum Profit)) * 100)

Health Bands:
85.0 - 100.0 : Healthy
65.0 - 84.9  : Warning
 0.0 - 64.9  : Critical
"""

from typing import List, Tuple
from formulas.f01_discount_leakage.models import HealthBand, OrderEvaluation

def get_health_band(score: float) -> HealthBand:
    """Classifies an F01 score into merchant-facing health bands."""
    if score >= 85.0:
        return "Healthy"
    elif score >= 65.0:
        return "Warning"
    else:
        return "Critical"

def calculate_f01_score(
    order_evaluations: List[OrderEvaluation]
) -> Tuple[float, HealthBand, float, float]:
    """
    Computes aggregate dollar-weighted F01 score.
    Returns: (f01_score, health_band, total_target_profit, total_dollar_loss)
    Exercises TC-11 (Zero-safe).
    """
    evaluated = [o for o in order_evaluations if o.status == "evaluated"]

    total_target_profit = round(sum(o.target_minimum_profit for o in evaluated), 2)
    total_dollar_loss = round(sum(o.f01_dollar_loss for o in evaluated), 2)

    if total_target_profit <= 0.0:
        score = 100.0
    else:
        loss_ratio = total_dollar_loss / total_target_profit
        score = round(max(0.0, (1.0 - loss_ratio) * 100.0), 2)

    band = get_health_band(score)
    return score, band, total_target_profit, total_dollar_loss

def calculate_count_based_score(
    order_evaluations: List[OrderEvaluation]
) -> float:
    """Calculates unweighted count-based score for side-by-side comparison."""
    evaluated = [o for o in order_evaluations if o.status == "evaluated"]
    if not evaluated:
        return 100.0

    flagged_count = sum(1 for o in evaluated if o.f01_flagged)
    count_score = round(max(0.0, (1.0 - flagged_count / len(evaluated)) * 100.0), 2)
    return count_score
