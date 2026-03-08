# Pending OEIS Corrections

Corrections that have been verified but not yet submitted (awaiting processing of previous submissions).

## [A140228](https://oeis.org/A140228)

**Current formula**: `a(n) = n*(274 + 85*n + n^4)/60 for n >= 1.`

**Corrected formula**: `a(n) = n*(274 + 85*n^2 + n^4)/60 for n >= 1.`

**Evidence**: The formula text has a typo: `85*n` should be `85*n^2`. The Maple code in the same entry by the same author (Emeric Deutsch, Jun 03 2008) correctly uses `(1/60)*n*(274+85*n^2+n^4)`. With `85*n`: n=2 gives 2*(274+170+16)/60 = 920/60 = 15.33 (not integer). With `85*n^2`: n=2 gives 2*(274+340+16)/60 = 1260/60 = 21 = a(2). Verified: n=1 gives 360/60=6, n=3 gives 3360/60=56, n=4 gives 7560/60=126. All match the listed terms.

**Status**: Not yet submitted.

## [A279112](https://oeis.org/A279112)

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

**Status**: Submitted to OEIS on 2026-02-28. Draft status: proposed (reviewed on 2026-03-01).

## [A003600](https://oeis.org/A003600)

**Current formula**: `a(n) = binomial(n+2, n-1) + binomial(n, n-1).` (no domain restriction)

**Corrected formula**: `a(n) = binomial(n+2, n-1) + binomial(n, n-1) for n >= 1.`

**Evidence**: At n=0, both binomial arguments have k = n-1 = -1 (negative), giving binomial(2,-1) + binomial(0,-1) = 0 + 0 = 0, but a(0) = 1. For all n >= 1 the formula is correct: n=1 gives 1+1=2, n=2 gives 4+2=6, n=3 gives 10+3=13, etc. The sequence name itself already notes `(n^3 + 3*n^2 + 8*n)/6 (n > 0)` and the PARI code uses `if(n, ..., 1)`, both acknowledging a(0) is a special case.

**Status**: Submitted to OEIS on 2026-02-28. Draft status: proposed.

## [A006470](https://oeis.org/A006470)

**Current formula** (Zerinvary Lajos, Dec 14 2005):
```
a(n) = binomial(n+2, 2)*binomial(n+4, 3)/2;
a(n) = n*(n+1)^2*(n+2)*(n+3)/24. (End)
```

**Corrected formula**:
```
a(n) = binomial(n+1, 2)*binomial(n+3, 3)/2;
a(n) = n*(n+1)^2*(n+2)*(n+3)/24. (End)
```

**Evidence**: The binomial formula `C(n+2,2)*C(n+4,3)/2` computes `a(n+1)` instead of `a(n)`. Algebraically: `C(n+2,2)*C(n+4,3)/2 = (n+1)(n+2)^2(n+3)(n+4)/24`, while `a(n) = n(n+1)^2(n+2)(n+3)/24`. At n=1: formula gives 15 but a(1)=2; at n=2: formula gives 60 but a(2)=15. The corrected version `C(n+1,2)*C(n+3,3)/2` matches all terms. The polynomial formula in the same block is correct. Only the first line of the (Start)/(End) block needs correction.

**Status**: Independently submitted on 2026-02-28. Draft status: proposed.

## [A056118](https://oeis.org/A056118)

**Current formula** (G. C. Greubel, Jan 17 2020):
```
a(n) = 11*binomial(n+5,5) - 8*binomial(n+4,4).
```

**Corrected formula**:
```
a(n) = 11*binomial(n+5,5) - 10*binomial(n+4,4).
```

**Evidence**: The coefficient of `C(n+4,4)` should be -10, not -8. Algebraically: `11*C(n+5,5) - 8*C(n+4,4)` expands to `(n+1)(n+2)(n+3)(n+4)(11n+15)/120`, but the correct formula `(11n+5)*C(n+4,4)/5` expands to `(n+1)(n+2)(n+3)(n+4)(11n+5)/120`. The factor `(11n+15)` vs `(11n+5)` shows a constant error of 10. Solving `A(n+5) + 5B = 11n + 5` with `A = 11` gives `B = -10`. The difference `f_wrong(n) - a(n) = (n+1)(n+2)(n+3)(n+4)/12` matches at every n. The Mathematica code `Table[11*Binomial[n+5,5]-8*Binomial[n+4,4], {n,0,40}]` by the same author would also produce wrong values. The other formulas and code (Maple, PARI, Magma, SageMath, GAP) all use the correct `(11n+5)*C(n+4,4)/5` form.

## [A115144](https://oeis.org/A115144)

**Current formula** (Peter Bala, Mar 05 2023):
```
a(n) = binomial(2*n - 6, n) - binomial(2*n - 6, n + 1).
```

**Corrected formula**:
```
a(n) = binomial(2*n - 6, n) - binomial(2*n - 6, n - 1).
```

**Evidence**: The second binomial argument should be `n - 1`, not `n + 1`. The formula `C(2n-6,n) - C(2n-6,n+1)` fails at 12 of 14 tested positions (only n=3,4 match trivially since C(0,k)=0 for those). The correct subtraction form `C(2n-6,n) - C(2n-6,n-1)` is algebraically equivalent to Peter Bala's other correct formula `-5/(n-5)*C(2n-6,n)`, since `C(2n-6,n-1) = C(2n-6,n) * n/(n-5)`, giving `C(2n-6,n) * (1 - n/(n-5)) = -5/(n-5) * C(2n-6,n)`. Verified against all 14 terms. The LODA formula `-C(2n-6,n-1)+C(2n-6,n)` also uses the correct `n-1` form.

**Status**: Submitted to OEIS on 2026-03-08.

## [A172118](https://oeis.org/A172118)

**Current formula** (G. C. Greubel, Jan 23 2020):
```
a(n) = 12*binomial(n+3,4) - 78*binomial(n+2,3) + 19*binomial(n+1,2).
```

**Corrected formula**:
```
a(n) = 60*binomial(n+3,4) - 78*binomial(n+2,3) + 19*binomial(n+1,2).
```

**Evidence**: The leading coefficient should be 60, not 12. The sequence formula from the name is `a(n) = n*(n+1)*(5*n^2-n-3)/2`, which expands to `5n^4/2 + 2n^3 - 2n^2 - 3n/2`. Expressing this in the binomial basis `A*C(n+3,4) + B*C(n+2,3) + C*C(n+1,2)` and matching coefficients of n^4: `A/24 = 5/2` gives `A = 60`. The coefficients B = -78 and C = 19 are correct: n^3 gives `60*6/24 + B/6 = 2`, so `B = -78`; n^2 gives `60*11/24 + (-78)*3/6 + C/2 = -2`, so `C = 19`. Verified numerically against all 10 listed terms. Similar pattern to A056118 (also Greubel, coefficient -8 should be -10).
