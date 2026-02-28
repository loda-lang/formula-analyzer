---
description: "Use when working on formula comparison, novelty determination, interest rules, FormulaType classification, FormulaComparator, or analyzing whether LODA formulas are interesting/novel."
---
# Formula Comparison and Novelty

## Determining Interest (Priority Order)

1. Explicit formula where OEIS only has recurrence (highest priority)
2. Closed form where OEIS has sum/product/integral
3. New binomial formula
4. Sequence-reference composition
5. Any new formula type

## Mathematical Concepts

### Parity-based Formulas
- `sumdigits(n, 2)` counts 1-bits in binary representation
- `sumdigits(n, 2) % 2` is parity (Thue-Morse sequence)
- Often equivalent to OEIS `A010060`, `A000120 % 2`, `hammingweight % 2`

### Rational Generating Functions
- Form: `P(x) / Q(x)` where P, Q are polynomials
- Denominators like `(1-x)(1-x^2)` indicate polynomial/floor formulas
- Explicit formulas from rational g.f. have "moderate novelty"

### Closed-form vs. Recurrence
- Closed-form: Direct computation without previous terms
- Recurrence: Requires computing a(0), a(1), ..., a(n-1) first
- Finding explicit form for recurrence is highly valuable

### Binomial Formulas and Sequence Names
- OEIS sequence names often describe the formula itself (e.g., "Binomial coefficient C(3n,n-5)")
- When a sequence name contains "Binomial coefficient" or pattern like "C(n,k)", the OEIS already knows it's a binomial formula
- LODA restating the exact binomial formula from the name is NOT novel (e.g., `a(n) = binomial(3*n,n-5)` for A004323)
- Only report LODA binomial formulas as interesting if they provide a NEW perspective not evident from the name
- The `NAME_BINOMIAL_PATTERN` detects: `binomial\s+coefficient`, `binomial\(`, or `\bC\(\d*n` in titles
- Check both formula entries AND sequence names when determining binomial type coverage

### Explicit Polynomial Formulas in Names
- Many sequence names contain explicit formulas: "Description: 7*n^2 + 4*n + 1." (A005892)
- The `NAME_POLYNOMIAL_PATTERN` detects polynomials after colons: `:\s*...*n...+/-`
- When a name provides an explicit polynomial, LODA variants using floor/ceiling/modular are not novel
- Examples: `7*n^2+4*n+1` vs `floor(((7*n+2)^2)/7)+1` are algebraically equivalent
- Filter out cases where LODA only adds implementation details (floor_ceiling, modular) to name-provided formulas

### Linear Multiples in Names
- Titles like "Multiples of 7" or "Multiples of 13" already imply the explicit formula `k*n`
- The `NAME_MULTIPLES_PATTERN` detects phrases `multiples of <number>`
- LODA restating `k*n` is not novel; treat as explicit closed form supplied by the name

### Floor/Ceiling Formulas in Names
- Titles like "Floor(n(n-1)/7)" already give an explicit floor/ceiling closed form
- The `NAME_FLOOR_CEILING_PATTERN` detects `floor(` or `ceiling(` in titles
- When present, infer both `floor_ceiling` and `explicit_closed`; LODA variants are not novel unless adding a truly different type

## Adding a New Formula Type

```python
# 1. Add to FormulaType enum
class FormulaType(Enum):
    MY_NEW_TYPE = "my_new_type"

# 2. Add patterns to FormulaClassifier
PATTERNS = {
    FormulaType.MY_NEW_TYPE: [
        r'pattern1',
        r'pattern2',
    ],
}

# 3. Update interest rules if needed
def _determine_interest(self, ...):
    if FormulaType.MY_NEW_TYPE in loda_types and ...:
        return "Reason for interest"
```

## Output Interpretation

### Interest Reasons (Common)
- "LODA provides explicit formula where OEIS only has recurrence" - High value
- "LODA supplies explicit piecewise polynomial closed form derivable from rational generating function; moderate novelty" - Medium value
- "LODA provides closed form where OEIS has sum/product/integral" - High value
- "LODA provides binomial formula not in OEIS" - Medium value
- "LODA formula equivalent to existing OEIS explicit parity formula" - Low value (filtered)

## Testing Considerations

### When Adding New Patterns
- Test against sample OEIS and LODA formulas
- Check for false positives and false negatives
- Ensure patterns don't overlap incorrectly

### When Modifying Interest Rules
- Verify sorting still prioritizes explicit formulas
- Check that rational g.f. downgrade works correctly
- Test equivalence detection with parity formulas

## Common Mistakes to Avoid

- ❌ Assuming one formula per sequence in OEIS (there can be multiple)
- ❌ Ignoring continuation lines in OEIS files (2-space indent)
- ❌ Treating all explicit formulas equally (parity-based are less novel)
- ❌ Missing rational g.f. presence (downgrades novelty)
- ❌ Forgetting to check `FormulaType.UNKNOWN` in comparisons
- ❌ Using absolute classification (formulas can have multiple types)
- ❌ Claiming LODA provides a binomial formula when the OEIS sequence name already states it's a binomial coefficient
- ❌ Ignoring sequence names when determining formula type coverage (names can imply types without explicit formula entries)
