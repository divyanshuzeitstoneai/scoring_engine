"""
Deterministic Allocation Engine using the Largest-Remainder Method.
Guarantees exact sum conservation to the currency minor unit (DQ-A1).
Tie-break: lowest line index (Decision D17).
"""

from decimal import Decimal, ROUND_FLOOR
from typing import List, Tuple


def allocate_largest_remainder(
    total_amount: Decimal,
    shares: List[Decimal],
    minor_units: int = 2
) -> List[Decimal]:
    """
    Allocates total_amount across shares using the largest-remainder method (Hare-Niemeyer).
    Guarantees sum(allocated) == total_amount exactly at 10^(-minor_units).
    Tie-breaking: earlier index in the list wins the remainder unit.
    """
    n = len(shares)
    if n == 0:
        return []
    if n == 1:
        return [total_amount]

    multiplier = Decimal(10 ** minor_units)
    total_cents = int((total_amount * multiplier).quantize(Decimal("1"), rounding=ROUND_FLOOR))
    sum_shares = sum(shares)

    # Handle zero or negative shares denominator: distribute equally
    if sum_shares <= Decimal("0"):
        base_each = total_cents // n
        remainder = total_cents % n
        result = []
        for i in range(n):
            cents = base_each + (1 if i < remainder else 0)
            result.append(Decimal(cents) / multiplier)
        return result

    # Compute unrounded units and fractional remainders
    allocated_units = []
    remainders = []
    for i, s in enumerate(shares):
        if s < Decimal("0"):
            s = Decimal("0")
        exact = (Decimal(total_cents) * s) / sum_shares
        integer_part = int(exact.quantize(Decimal("1"), rounding=ROUND_FLOOR))
        fractional_part = exact - Decimal(integer_part)
        allocated_units.append(integer_part)
        remainders.append((fractional_part, -i, i))  # -i ensures tie-break to lowest index

    assigned_cents = sum(allocated_units)
    missing_cents = total_cents - assigned_cents

    # Distribute missing cents by largest remainder
    remainders.sort(reverse=True)
    for k in range(missing_cents):
        idx = remainders[k][2]
        allocated_units[idx] += 1

    return [Decimal(u) / multiplier for u in allocated_units]
