"""
Unified Scoring Engine CLI Runner.
Supports running individual formulas or batch runs across all registered formulas.

Usage:
    python run.py --formula f01
    python run.py --formula all
"""

import argparse
import sys
from formulas.f01_discount_leakage.runner import main as run_f01_main

FORMULA_REGISTRY = {
    "f01": run_f01_main,
}

def main():
    parser = argparse.ArgumentParser(description="Shopify E-Commerce Scoring Engine Runner")
    parser.add_argument(
        "--formula",
        type=str,
        default="f01",
        choices=["f01", "all"],
        help="The scoring formula to evaluate (default: f01)"
    )

    args = parser.parse_args()

    if args.formula in FORMULA_REGISTRY:
        print(f"Running formula: {args.formula.upper()}...")
        FORMULA_REGISTRY[args.formula]()
    elif args.formula == "all":
        for fid, fn in FORMULA_REGISTRY.items():
            print(f"\nRunning formula: {fid.upper()}...")
            fn()
    else:
        print(f"Unknown formula: {args.formula}")
        sys.exit(1)

if __name__ == "__main__":
    main()
