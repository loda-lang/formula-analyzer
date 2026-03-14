# Pending OEIS Corrections

Corrections that have been verified but not yet submitted (awaiting processing of previous submissions).

## [A244501](https://oeis.org/A244501)

**Current formula**: `a(n) = 1/48*n^6 + 1/16*n^5 - 13/16*n^4 + 61/48*n^3 + 247/24*n^2 - 293/6*n + 6 for n >= 3.`

**Corrected formula**: `a(n) = 1/48*n^6 + 1/16*n^5 - 13/16*n^4 + 61/48*n^3 + 247/24*n^2 - 293/6*n + 63 for n >= 3.`

**Evidence**: The formula produces values that are consistently 57 less than the actual sequence terms. With the corrected constant term (63 instead of 6), the formula matches perfectly:
- n=3: formula gives 8 (actual: 8) ✓
- n=4: formula gives 55 (actual: 55) ✓
- n=5: formula gives 248 (actual: 248) ✓
- n=6: formula gives 820 (actual: 820) ✓
- All subsequent terms also match.

The error appears to be a simple typo in the constant term.

**Status**: Submitted to OEIS on 2026-03-14.

## [A299256](https://oeis.org/A299256)

**Current formulas**:
1. `a(n) = (9*n^2 - 1) / 2 for n>1.`
2. `a(n) = 9*n^2 / 2 for n>1.`

**Corrected formulas**:
1. `a(n) = (9*n^2 - 1) / 2 for odd n > 1.`
2. `a(n) = 9*n^2 / 2 for even n > 1.`

**Evidence**: Both formulas are correct but only for specific parities:
- Formula 1 works for **odd n only**: n=3 gives 40 ✓, n=5 gives 112 ✓, n=7 gives 220 ✓, n=9 gives 364 ✓, n=11 gives 544 ✓
- Formula 2 works for **even n only**: n=2 gives 18 ✓, n=4 gives 72 ✓, n=6 gives 162 ✓, n=8 gives 288 ✓, n=10 gives 450 ✓
- Both produce fractional results (x.5) when used with the wrong parity

The formulas are missing the parity restriction that makes them valid.

**Status**: Submitted to OEIS on 2026-03-14.

## [A113127](https://oeis.org/A113127)

**Current formula**: `a(n) = binomial(n+1, n) + binomial(n, n-1) + binomial(n-1, n-2) + binomial(n-2, n-3).`

**Corrected formula**: `a(n) = binomial(n+1, n) + binomial(n, n-1) + binomial(n-1, n-2) + binomial(n-2, n-3) for n >= 2.`

**Evidence**: The formula produces incorrect values at n=0 and n=1 but works correctly for all n >= 2:
- n=0: formula gives -2, but a(0) = 1 (error: -3)
- n=1: formula gives 2, but a(1) = 3 (error: -1)
- n=2: formula gives 6 = 6 ✓
- n=3: formula gives 10 = 10 ✓
- n=4 onwards: all correct ✓

The entry already has two working formulas (`a(n) = 4*(n+2) - 10 for n >= 2` and `a(n) = 4*n - 2 + 2*binomial(0, n) + binomial(1, n)`), so this binomial sum formula should also include the domain restriction.

**Status**: Submitted to OEIS on 2026-03-14.
