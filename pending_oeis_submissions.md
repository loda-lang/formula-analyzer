# Pending OEIS Corrections

Corrections that have been verified but not yet submitted (awaiting processing of previous submissions).

## A140228 — [OEIS](https://oeis.org/A140228)

**Current formula**: `a(n) = n*(274 + 85*n + n^4)/60 for n >= 1.`

**Issue**: The polynomial produces non-integer values for most n (e.g., n=2 gives 920/60 = 15.33, but a(2) = 21). The g.f. `(1+x^6)/(1-x)^6` is correct and gives `a(n) = C(n+5,5) + C(n-1,5)` for n >= 6, `C(n+5,5)` for n <= 5. The polynomial constant or coefficients appear wrong.

**Status**: Needs further investigation to derive the correct polynomial.

## A303295 — [OEIS](https://oeis.org/A303295)

**Current formula**: `a(n) = ((4*n+7)*(4*n+2)) - (4*n+2)*(4*n+3)/2 + 4 for n > 2.`

**Corrected formula**: `a(n) = ((4*n+7)*(4*n+2)) - (4*n+2)*(4*n+3)/2 + 4 for n > 1.`

**Evidence**: The domain bound should be `n > 1`, not `n > 2`. At n=3 the formula gives 165, but a(3) = 99 and a(4) = 165 — it computes a(n+1) with the current bound.

## A279112 — [OEIS](https://oeis.org/A279112)

**Current formulas**:
```
a(n) = (n^6 - 27*n^4 + 44*n^3 + 146*n^2 - 404*n + 240)/48 for n>1.
a(n) = (n^6 - 27*n^4 + 52*n^3 + 125*n^2 - 388*n + 189)/48 for n>1.
```

**Corrected formulas**:
```
a(n) = (n^6 - 27*n^4 + 44*n^3 + 146*n^2 - 404*n + 240)/48 for even n >= 2.
a(n) = (n^6 - 27*n^4 + 52*n^3 + 125*n^2 - 388*n + 189)/48 for odd n >= 1.
```

**Evidence**: The two sub-formulas after the `IF(MOD)` formula are missing their parity restrictions. The first is valid only for even n >= 2, and the second only for odd n >= 1. For n=3 (odd), the first formula gives 1.5 (not integer) while the second gives 2 = a(3). For n=4 (even), the first gives 20 = a(4) while the second gives 23.9 (not integer).

## A003600 — [OEIS](https://oeis.org/A003600)

**Current formula**: `a(n) = binomial(n+2, n-1) + binomial(n, n-1).` (no domain restriction)

**Corrected formula**: `a(n) = binomial(n+2, n-1) + binomial(n, n-1) for n >= 1.`

**Evidence**: At n=0, both binomial arguments have k = n-1 = -1 (negative), giving binomial(2,-1) + binomial(0,-1) = 0 + 0 = 0, but a(0) = 1. For all n >= 1 the formula is correct: n=1 gives 1+1=2, n=2 gives 4+2=6, n=3 gives 10+3=13, etc. The sequence name itself already notes `(n^3 + 3*n^2 + 8*n)/6 (n > 0)` and the PARI code uses `if(n, ..., 1)`, both acknowledging a(0) is a special case.
