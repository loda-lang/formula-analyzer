# Pending OEIS Corrections

Corrections that have been verified but not yet submitted (awaiting processing of previous submissions).

## [A227726](https://oeis.org/A227726)

**Current formula**: `a(n) = binomial(3*n, n) + binomial(3*n-1, n-1).` (no domain restriction)

**Corrected formula**: `a(n) = binomial(3*n, n) + binomial(3*n-1, n-1) for n >= 1.`

**Evidence**: At n=0, the formula gives `C(0,0) + C(-1,-1) = 1 + 1 = 2`, but a(0) = 1. For all n >= 1 the formula is correct: n=1 gives 4, n=2 gives 20, n=3 gives 112, etc. The entry already has a correct formula marked "For n >= 1, a(n) = 4*binomial(3*n - 1, n - 1) = 4*A025174(n)", acknowledging the domain restriction. The simpler binomial sum formula needs the same restriction.

**Status**: Submitted to OEIS on 2026-03-08.

## [A364515](https://oeis.org/A364515)

**Current formula**: `a(n) = (1/2) *  binomial(6*n, 2*n)*binomial(2*n, n)^2 / binomial(3*n, n).` (no domain restriction)

**Corrected formula**: `a(n) = (1/2) *  binomial(6*n, 2*n)*binomial(2*n, n)^2 / binomial(3*n, n) for n >= 1.`

**Evidence**: At n=0, the formula gives `(1/2) * C(0,0) * C(0,0)^2 / C(0,0) = (1/2) * 1 * 1 / 1 = 0.5`, but a(0) = 1. For all n >= 1 the formula is correct: n=1 gives 10, n=2 gives 594, n=3 gives 44200, etc. The sequence definition already states "for n >= 1 with a(0) = 1", so the formula should explicitly include this restriction. Without it, the formula produces a non-integer value at the offset.

**Status**: Not yet submitted.

## [A381864](https://oeis.org/A381864)

**Current formula**: `a(n) = 30 * binomial(n, 6) + 2100 * binomial(n, 7) + 25200 * binomial(n, 8) + 86625 * binomial(n, 9) + 116550 * binomial(n, 10) + 69300 * binomial(n, 11) + 15400 * binomial(n, 12).`

**Issue**: This formula appears to be completely incorrect. It produces 0 for n=1 through n=5 (since all binomial coefficients are zero when n < k), but the actual sequence values are a(1)=15, a(2)=33, a(3)=35, a(4)=44, a(5)=45. This is a number-theoretic sequence ("Numbers k in A024619 such that p^(m+1) == r (mod k)..."), and the polynomial binomial formula doesn't match it at all.

**Recommendation**: Request deletion of this formula or further investigation. The formula may have been added to the wrong sequence.

**Status**: Not yet submitted.
