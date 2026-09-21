"""
Global Test Suite Runner.
Executes test suites across registered scoring formulas.
"""

from formulas.f01_discount_leakage.test_f01 import main as run_f01_tests

def main():
    print("Executing F01 Test Suite...")
    run_f01_tests()

if __name__ == "__main__":
    main()
