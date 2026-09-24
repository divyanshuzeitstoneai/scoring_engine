"""
Unified Scoring Engine CLI Runner.
Supports running individual formulas or batch runs across all registered formulas.

Usage:
    python run.py --formula f01
    python run.py --formula f03
    python run.py --formula all
"""

import argparse
import sys
from f01.code.runner import main as run_f01_main
from f03.code.test_f03 import run_f03_test_suite as run_f03_main

FORMULA_REGISTRY = {
    "f01": run_f01_main,
    "f03": run_f03_main,
}

def main():
    parser = argparse.ArgumentParser(description="Shopify E-Commerce Scoring Engine Runner")
    parser.add_argument(
        "--formula",
        type=str,
        default="all",
        choices=["f01", "f03", "all"],
        help="The scoring formula to evaluate (default: all)"
    )

    args = parser.parse_args()

    if args.formula in FORMULA_REGISTRY:
        print(f"Running formula: {args.formula.upper()}...")
        FORMULA_REGISTRY[args.formula]()
    elif args.formula == "all":
        for fid, fn in FORMULA_REGISTRY.items():
            print(f"\n{'='*60}\nRunning formula: {fid.upper()}...\n{'='*60}")
            fn()
    else:
        print(f"Unknown formula: {args.formula}")
        sys.exit(1)

if __name__ == "__main__":
    main()
