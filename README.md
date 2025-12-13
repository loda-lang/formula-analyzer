# Formula Analysis Tool

This tool analyzes and compares formulas from OEIS and LODA to identify new and interesting LODA formulas that provide different formula types than what's currently known in OEIS.

## Overview

The formula analyzer classifies formulas into different types and identifies LODA formulas that are "interesting" because they:

1. Provide an **explicit (closed-form) formula** where OEIS only has a **recurrence relation**
2. Provide a **binomial formula** not present in OEIS
3. Provide a **closed form** where OEIS only has complex formulas (sums, products, integrals)
4. Provide any **new formula type** not represented in OEIS

## Files

- **formula_analyzer.py** - Core analysis module with formula classification and comparison
- **run_formula_analysis.py** - Command-line script to run the analysis

## Formula Types

The analyzer recognizes these formula types:

| Type | Description | Example |
|------|-------------|---------|
| `explicit_closed` | Direct formula without recursion (pure) | `a(n) = n^2 + 1` |
| `composite_explicit` | Explicit but composed from helper/parity/other sequences | `a(n) = 2*n-1-parity(n-1)` |
| `recurrence` | Recursive definition | `a(n) = a(n-1) + a(n-2)` |
| `generating_function` | G.f. or e.g.f. | `G.f.: 1/(1-x)` |
| `sum` | Summation formula | `a(n) = Sum_{k=0..n} k^2` |
| `product` | Product formula | `a(n) = Product_{k=1..n} k` |
| `binomial` | Uses binomial coefficients | `a(n) = binomial(2n, n)` |
| `floor_ceiling` | Uses floor/ceiling functions | `a(n) = floor(n/2)` |
| `modular` | Modular arithmetic | `a(n) = n mod 3` |
| `congruence` | Congruence relation | `a(n) ≡ 1 (mod p)` |
| `limit` | Limit formula | `a(n) = lim_{k→∞} f(k,n)` |
| `integral` | Integral formula | `a(n) = ∫_0^n f(x) dx` |
| `trigonometric` | Trig functions | `a(n) = sin(n)` |
| `continued_fraction` | Continued fraction | Various forms |
| `matrix` | Matrix formula | Uses determinants, etc. |

## Usage

### Command Line

```bash
# Run the analysis (uses default file paths)
python run_formula_analysis.py

# Or use the analyzer directly
python formula_analyzer.py [oeis_file] [loda_file] [names_file] [output_file]
```

### Python API

```python
from formula_analyzer import analyze_formulas, FormulaType

# Run analysis
results, comparator = analyze_formulas(
    'formulas-oeis.txt',
    'formulas-loda.txt', 
    'names.txt',
    'interesting_formulas.txt'
)

# Results is a list of (Formula, new_types, reason) tuples
for formula, new_types, reason in results[:10]:
    print(f"{formula.sequence_id}: {reason}")
    print(f"  {formula.text}")
```

## Input File Formats

### data/formulas-oeis.txt

OEIS formulas extracted from www.oeis.org. Format:
```
A000016: a(n) = 2^(n-1) - A327477(n).
  a(n) = A063776(n)/2.
  a(n) = Sum_{odd d divides n} (phi(d)*2^(n/d))/(2*n), n>0.
```

### data/formulas-loda.txt

LODA formulas generated from LODA programs. Format:
```
A000045: a(n) = a(n-1)+a(n-2), a(2) = 1, a(1) = 1, a(0) = 0
A000079: a(n) = 2^n
A000217: a(n) = binomial(n+1,2)
```

### data/names.txt

Sequence names from OEIS. Format:
```
A000045 Fibonacci numbers: F(n) = F(n-1) + F(n-2) with F(0) = 0 and F(1) = 1.
A000079 Powers of 2: a(n) = 2^n.
```

## Output

The tool generates:

1. **Console output** - Statistics and top interesting formulas
2. **results/interesting_formulas.txt** - Detailed report of all findings
3. **CSV exports** (from notebook) - Structured data for further analysis

### Example Output

```
================================================================================
INTERESTING LODA FORMULAS
================================================================================

Found 1234 interesting formulas

1. A000108: Catalan numbers
   Reason: LODA provides explicit formula where OEIS only has recurrence
   LODA Formula Types: explicit_closed, binomial
   OEIS Formula Types: recurrence, generating_function
   Formula: a(n) = floor(binomial(2*n,n)/(n+1))

2. A000217: Triangular numbers
   Reason: LODA provides closed form where OEIS has sum/product/integral
   LODA Formula Types: explicit_closed, binomial
   Formula: a(n) = binomial(n+1,2)
```

## How It Works

### 1. Formula Classification

The `FormulaClassifier` uses regex patterns to identify formula types:

- **OEIS formulas**: Patterns match mathematical notation (G.f., e.g.f., Sum_{}, etc.)
- **LODA formulas**: Patterns match LODA syntax (recursion, helper sequences, operations)

### 2. Comparison Logic

The `FormulaComparator` compares formula types for each sequence:

```python
# For each LODA formula:
# 1. Collect all OEIS formula types for that sequence
# 2. Find LODA types not in OEIS
# 3. Determine if this is "interesting" based on rules
```

**Interest Rules** (in priority order):

1. **Explicit vs Recurrence**: LODA has explicit (pure or composite) formula, OEIS only has recurrence. If OEIS also supplies a rational generating function, explicit forms may be marked as moderately novel (derivable from g.f.).
2. **Closed vs Complex**: LODA has closed form, OEIS has sum/product/integral
3. **New Binomial**: LODA has binomial formula not in OEIS
4. **Sequence-Reference Composition**: LODA combines sequences where OEIS lacks such composition
5. **Any New Type**: LODA provides any formula type not in OEIS

### 3. Reporting

Results are sorted by interest score and formatted into human-readable reports.

## Customization

### Add New Formula Types

Edit `FormulaType` enum and add patterns to `FormulaClassifier.PATTERNS`:

```python
class FormulaType(Enum):
    MY_NEW_TYPE = "my_new_type"

PATTERNS = {
    FormulaType.MY_NEW_TYPE: [
        r'pattern1',
        r'pattern2',
    ],
    # ...
}
```

### Modify Interest Rules & Equivalence

Edit `FormulaComparator._determine_interest()` to add custom logic:

```python
def _determine_interest(self, loda_types, oeis_types):
    # Add your custom rules here
    if my_condition:
        return "My custom reason"
    # ...
```

## Examples

### Find sequences with explicit LODA formulas

```python
from formula_analyzer import analyze_formulas, FormulaType

results, comparator = analyze_formulas(
    'formulas-oeis.txt',
    'formulas-loda.txt',
    'names.txt'
)

# Filter for explicit formulas
explicit = [
    (f, nt, r) for f, nt, r in results
    if FormulaType.EXPLICIT_CLOSED in f.types and
       "explicit formula" in r
]

print(f"Found {len(explicit)} explicit formulas")
```

### Export specific category

```python
import csv

# Export binomial formulas
binomial_formulas = [
    (f, nt, r) for f, nt, r in results
    if FormulaType.BINOMIAL in f.types
]

with open('binomial_formulas.csv', 'w', newline='') as csvfile:
    writer = csv.writer(csvfile)
    writer.writerow(['Sequence', 'Name', 'Formula', 'Reason'])
    
    for formula, _, reason in binomial_formulas:
        seq_id = formula.sequence_id
        name = comparator.get_sequence_name(seq_id)
        writer.writerow([seq_id, name, formula.text, reason])
```

## Equivalence Detection

The comparator performs a lightweight parity-based equivalence normalization: if a LODA explicit formula reduces to a known OEIS explicit parity form (e.g. replacing digit-sum mod 2 by a canonical `parity(n-1)` and matching linear patterns like `2*n-1-parity(n-1)`), the reason is adjusted to indicate equivalence instead of novelty. This avoids false positives such as sequence A000069.

Additionally, rational generating functions (simple products/ratios of `(1 - x^k)` factors) trigger a downgrade: an explicit piecewise polynomial/floor form derived from such a g.f. is labeled "moderate novelty" since it is algorithmically obtainable by partial fractions and coefficient extraction.

## Limitations

1. **Pattern matching**: Classification relies on regex patterns which may miss some formulas
2. **LODA syntax**: Only handles LODA formula export format, not raw LODA programs
3. **Semantic equivalence**: Only rudimentary (parity-linear) equivalence detection; broader algebraic normalization not yet implemented
4. **OEIS coverage**: Limited to formulas extracted from OEIS database

## Future Enhancements

- [ ] Semantic formula comparison (detect equivalent formulas)
- [ ] Direct LODA program parsing (not just exported formulas)
- [ ] Complexity metrics (count operations, depth, etc.)
- [ ] Automatic formula verification against sequence terms
- [ ] Integration with LODA miner to suggest which formulas to submit
- [ ] Machine learning for formula classification

## References

- OEIS (Online Encyclopedia of Integer Sequences): https://oeis.org
- LODA (Lexicographical Order Descent Algorithm): https://loda-lang.org
- LODA Programs Repository: https://github.com/loda-lang/loda-programs

## License

See project LICENSE file.
