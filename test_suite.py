"""
Global Test Suite Runner.
Executes test suites across registered scoring formulas (F01 & F03).
"""

from f01.code.test_f01 import main as run_f01_tests
from f03.code.test_f03 import run_f03_test_suite as run_f03_tests
from f03.code.audit_verification import *

def main():
    print("=" * 80)
    print("EXECUTING GLOBAL SCORING ENGINE TEST SUITE (F01 & F03)")
    print("=" * 80)

    print("\n[SUITE 1/2] Running Formula F01 Unit & Regression Tests (46 test cases)...")
    run_f01_tests()

    print("\n" + "=" * 80)
    print("[SUITE 2/2] Running Formula F03 Granular Pipeline Tests (49 fixtures + 3 meta-tests)...")
    run_f03_tests()

    print("\n" + "=" * 80)
    print("ALL TEST SUITES COMPLETED SUCCESSFULLY!")
    print("=" * 80)

if __name__ == "__main__":
    main()
