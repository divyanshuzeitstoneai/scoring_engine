"""
Shopify F01 Discount Leakage Scoring Engine - Forwarder Entry Point.
Delegates to formulas.f01_discount_leakage.runner.
"""

import sys
from formulas.f01_discount_leakage.runner import (
    HistoricalCogsIndex,
    main,
    run_f01_pipeline,
)

if __name__ == "__main__":
    main()
