# Formula Analysis Tool

This tool analyzes and compares formulas from OEIS and LODA to identify new and interesting LODA formulas that provide different formula types than what's currently known in OEIS.

## Overview

The formula analyzer classifies formulas into different types and identifies LODA formulas that are "interesting" because they:

1. Provide an **explicit (closed-form) formula** where OEIS only has a **recurrence relation**
2. Provide a **binomial formula** not present in OEIS
3. Provide a **closed form** where OEIS only has complex formulas (sums, products, integrals)
4. Provide any **new formula type** not represented in OEIS

## Files

### Core Analysis
- **formula_analyzer.py** - Core analysis module with formula classification and comparison
- **run_formula_analysis.py** - Command-line script to run the analysis

### Formula Parsing & Validation
- **formula/parser.py** - Mathematical expression parser with tokenizer and AST evaluator
- **formula/data.py** - Data loading, filtering, and offset/denylist management
- **formula/analyzer.py** - Formula classification and comparison logic
- **tests/test_formula_parser.py** - Validation tests ensuring parsed formulas match OEIS terms

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
# Run analysis; missing data files are generated automatically
python run_formula_analysis.py

# Force regeneration of all data files (can take a few minutes)
python run_formula_analysis.py --refresh-data

# Or use the analyzer directly
python formula_analyzer.py [oeis_file] [loda_file] [names_file] [output_file]
```

### Preparing Data (automatic on first run)

By default the script will generate any missing data files. To force a full
refresh, use `--refresh-data`:

```bash
# Force refresh everything
python run_formula_analysis.py --refresh-data

# Custom locations
python run_formula_analysis.py --refresh-data --data-dir custom/data --loda-home /path/to/loda
```

What happens under the hood:
- Runs `loda update` once, then copies `names`, `offsets`, and `stripped` from
    `$HOME/loda/seqs/oeis/` into `data/`.
- Generates `data/formulas-loda.txt` via `loda export-formulas` (can take a few
    minutes).
- Downloads `https://api.loda-lang.org/v2/sequences/data/oeis/formulas.gz`,
    ungzips it, and saves as `data/formulas-oeis.txt`.
Only missing files are generated unless `--refresh-data` is provided.

### Python API

```python
from formula.analyzer import analyze_formulas, FormulaType

# Run analysis
results, comparator = analyze_formulas(
    'formulas-oeis.txt',
    'formulas-loda.txt', 
    'names',
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

### data/names

Sequence names from OEIS. Format:
```
A000045 Fibonacci numbers: F(n) = F(n-1) + F(n-2) with F(0) = 0 and F(1) = 1.
A000079 Powers of 2: a(n) = 2^n.
```

### data/stripped

OEIS sequence terms ("stripped" export from oeis.org). Notes on format:
- Starts with comment lines beginning with `#` (license, timestamp).
- Each sequence is on one line: `Axxxxxx ,t0,t1,t2,...` (comma-separated terms; large lines may wrap in editors).
- File has no extension (mirrors the OEIS stripped export name).
- Not yet used by the analyzer; reserved for future term-based validation.

### data/offsets

OEIS offsets table, used to align indices and interpret formula conventions.

- Format: One entry per line: `Axxxxxx: n0,k`
- `n0`: Index of the first term for the sequence in OEIS (often 0 or 1; may be negative).
- `k`: Position marker used by OEIS to indicate where `a(1)` appears in the listed terms; values can vary by sequence.
- Examples: `A000004: 0,1`, `A000012: 0,1`, `A000045: 0,4`, `A000297: -1,2`.
- Parsing rules:
    - Read as UTF-8; skip empty lines.
    - Split on `:` to separate the A-number from the payload.
    - Split payload on `,` into two integers `(n0, k)`; handle negatives.
    - Use `try/except` to skip malformed entries gracefully.
- Intended usage:
    - Index normalization: Map OEIS term positions to canonical `n` when comparing with LODA formulas.
    - Recurrence/g.f. alignment: Disambiguate conventions when `a(1)` is not the first listed term.
    - Interest filtering: Detect cases where novelty is only due to offset shifts (e.g., `a(n+1)` vs `a(n)`).
- More information at https://oeis.org/wiki/Offsets

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

## Formula Parser

### Overview

The `formula/parser.py` module provides a custom recursive descent parser that converts mathematical expressions into abstract syntax trees (AST) and evaluates them for validation against OEIS sequence terms.

### Supported Operations

- **Arithmetic**: Addition, subtraction, multiplication, division
- **Exponentiation**: Power operations (e.g., `n^2`, `2^n`)
- **Functions**: Currently `floor()` and `ceil()` (extensible)
- **Variables**: Sequence index `n`

### Architecture

The parser uses a three-stage pipeline:

1. **Tokenizer**: Converts expression strings into tokens using regex patterns
2. **Parser**: Builds abstract syntax tree (AST) from tokens using recursive descent
3. **Evaluator**: Recursively evaluates AST nodes at given values of `n`

The AST uses typed nodes for literals, variables, operators, and function calls. The parser handles operator precedence and validates supported operations during parsing

### Parsing Restrictions

**OEIS Formulas**:
- Must match pattern: `a(n) = <expr>`
- Currently restricted to basic polynomial expressions for reliable parsing
- Must contain variable `n` and at least one operator
- Multi-line entries supported (2-space indent for continuation)

**LODA Formulas**:
- Format: `A123456: a(n) = <expr>`
- Supports arithmetic operations, exponents, and whitelisted functions
- Rejects unsupported operations (e.g., recursion, unknown functions)
- Single line per sequence

**Function Support**:
- Functions must be explicitly whitelisted in the parser
- Unsupported function names cause parse failure during tokenization
- This prevents formulas with unimplemented operations from being validated

### Validation Tests

The `tests/test_formula_parser.py` module validates parsed formulas against OEIS sequence terms:

1. **Load formulas**: Parse LODA and OEIS formulas from data files
2. **Load offsets**: Read sequence offset values from `data/offsets`
3. **Load terms**: Read actual sequence values from `data/stripped`
4. **Evaluate**: For each formula, evaluate at positions `offset + 0, offset + 1, ...`
5. **Compare**: Check if evaluated values match OEIS terms exactly
6. **Report**: Count mismatches (target: **zero mismatches**)

**Test Metrics**:
- Parsed formulas count (LODA + OEIS)
- Term comparisons across all sequences
- Mismatch count (target: zero)

## Offset Handling

### The Offset Problem

OEIS sequences have varying starting indices (offsets). Most sequences start at n=0 or n=1, but some start at negative indices or larger values. LODA formulas generally follow OEIS offsets, but a few formulas use incorrect or outdated offset information (often assuming n starts at 0); those cases are ignored.

**Example**: Sequence A186704
- OEIS offset: 1 (first term corresponds to n=1)
- OEIS terms: `[0, 1, 1, 2, 2, 3, 3, ...]`
- LODA formula: `floor((n-1)/2)`
- At n=1: `floor(0/2) = 0` ✓ (matches first term)
- At n=2: `floor(1/2) = 0` but OEIS term is 1 ✗ (mismatch!)

The LODA formula is written assuming n=0 is the first term, but OEIS uses n=1.

### Offset Alignment Strategy

The validator evaluates formulas at **OEIS offset positions**:
```python
for idx, expected_term in enumerate(terms):
    n = offset + idx  # Align to OEIS indexing
    result = formula.evaluate(n)
    if result != expected_term:
        # Mismatch detected
```

**Strict Validation**: Formulas must produce exact matches at the documented offset. No fallback shifts or adjustments are attempted.

### Denylists

When formulas have offset mismatches that cannot be easily corrected, they are added to denylists to prevent false validation failures.

**`DENYLIST_LODA`** (in `formula/data.py`):
- Contains sequences with LODA formulas that assume offset 0 or embed outdated/incorrect offset info while OEIS uses a different offset
- Examples: A044187, A186704, A385730, A386858, A389928
- These formulas are skipped during parsing/validation

**`DENYLIST_OEIS`** (in `formula/data.py`):
- Contains sequences with OEIS formulas that have offset issues or unreliable parsing
- Examples: A001511, A004525, A006519
- These formulas are skipped during parsing/validation

**Why Denylists?**:
- Some LODA formulas use n-1 or n+k shifts that don't align with OEIS offset conventions
- Some OEIS formulas have domain restrictions or special cases not captured in the formula text
- Denylists maintain zero-mismatch validation while preserving coverage of correct formulas

**Alternative Considered**: Automatic offset correction was explored but proved unreliable—too many edge cases and false corrections. Denylists provide explicit, maintainable control.

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
from formula.analyzer import analyze_formulas, FormulaType

results, comparator = analyze_formulas(
    'formulas-oeis.txt',
    'formulas-loda.txt',
    'names'
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
