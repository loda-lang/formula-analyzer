# Pending OEIS Corrections

Corrections that have been verified but not yet submitted (awaiting processing of previous submissions).

## [A381864](https://oeis.org/A381864)

**Current formula**: `a(n) = 30 * binomial(n, 6) + 2100 * binomial(n, 7) + 25200 * binomial(n, 8) + 86625 * binomial(n, 9) + 116550 * binomial(n, 10) + 69300 * binomial(n, 11) + 15400 * binomial(n, 12).`

**Issue**: This formula appears to be completely incorrect. It produces 0 for n=1 through n=5 (since all binomial coefficients are zero when n < k), but the actual sequence values are a(1)=15, a(2)=33, a(3)=35, a(4)=44, a(5)=45. This is a number-theoretic sequence ("Numbers k in A024619 such that p^(m+1) == r (mod k)..."), and the polynomial binomial formula doesn't match it at all.

**Recommendation**: Request deletion of this formula or further investigation. The formula may have been added to the wrong sequence.

**Status**: Not yet submitted.
