# GitHub Copilot Instructions for Formula Analyzer

## Project Overview

This is a Python tool that analyzes and compares mathematical formulas from OEIS (Online Encyclopedia of Integer Sequences) and LODA (Lexicographical Order Descent Language) to identify novel and interesting formula representations.

## Domain Knowledge

### OEIS (oeis.org)
- Database of integer sequences with formulas, references, and metadata
- Formulas use mathematical notation: `a(n)`, `Sum_{k=0..n}`, `binomial(n,k)`, `G.f.:`, etc.
- Sequence IDs follow format: `A000045` (6 digits)

### LODA (loda-lang.org)
- Assembly-like language for computing integer sequences
- Formulas exported to mathematical notation similar to OEIS
- Operations: `floor()`, `binomial()`, `sqrtint()`, `gcd()`, `sumdigits()`, etc.

### Formula Types
- **Explicit/Closed-form**: Direct formula without recursion (e.g., `a(n) = n^2`)
- **Composite Explicit**: Uses other sequences or parity functions (e.g., `a(n) = A000120(n) + 1`)
- **Recurrence**: Recursive definition (e.g., `a(n) = a(n-1) + a(n-2)`)
- **Generating Function**: G.f. or e.g.f. representation
- **Sum/Product/Integral**: Complex expressions requiring iteration
- **Binomial**: Uses binomial coefficients

## Code Style and Conventions

### General Python Style
- Follow PEP 8 conventions
- Use type hints for function parameters and return values
- Prefer descriptive variable names: `oeis_formulas`, `loda_formula`, `classifier`
- Use dataclasses for structured data (`@dataclass`)
- Use Enums for categorical types (`FormulaType`)

### Pattern Matching
- Use raw strings for regex: `r'pattern'`
- Compile patterns as class attributes when used repeatedly
- Use `re.search()` for existence checks, `re.match()` for start-of-string
- Always specify `re.IGNORECASE` flag when case doesn't matter

### Formula Classification
- Patterns should match both OEIS notation and LODA syntax
- Be conservative: only classify when confident about the type
- Multiple types can apply to one formula
- Return `{FormulaType.UNKNOWN}` when no patterns match

### Data Structures
- Use `Dict[str, List[Formula]]` for OEIS (multiple formulas per sequence)
- Use `Dict[str, Formula]` for LODA (one formula per sequence)
- Use `Set[FormulaType]` for formula type collections

## Key Classes and Their Roles

### `FormulaType` (Enum)
- Defines all recognized formula categories
- Add new types here when extending classification

### `Formula` (dataclass)
- Immutable representation of a single formula
- Fields: `sequence_id`, `text`, `source`, `types`
- Implement `__hash__` for set operations

### `FormulaClassifier`
- Pattern-based classification using regex
- `PATTERNS` dict maps types to regex lists
- `classify_oeis()` and `classify_loda()` methods handle different syntaxes

### `FormulaParser`
- Reads and parses input files
- Handles multi-line OEIS entries (indentation-based)
- One formula per line for LODA
- Uses `defaultdict(list)` for OEIS to accumulate multiple formulas

### `FormulaComparator`
- Core comparison logic
- `find_new_formulas()` identifies interesting LODA formulas
- `_determine_interest()` implements priority-based interest rules
- `_has_rational_gf()` detects rational generating functions
- `_is_equivalent()` handles parity-based equivalence normalization

## Important Patterns

### Adding a New Formula Type

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

### Processing Multi-line OEIS Entries

```python
# Check for sequence ID line
match = re.match(r'(A\d{6}):\s*(.+)', line)

# Check for continuation (2-space indent)
if line.startswith('  ') and current_seq_id:
    current_lines.append(line[2:])
```

### Determining Interest (Priority Order)

1. Explicit formula where OEIS only has recurrence (highest priority)
2. Closed form where OEIS has sum/product/integral
3. New binomial formula
4. Sequence-reference composition
5. Any new formula type

## Common Tasks

### Extracting Formula Components
- Use `re.sub()` to normalize whitespace: `text.replace(' ', '')`
- Canonicalize similar patterns: `text.replace('gcd(sumdigits(n-1,2),2)', 'parity(n-1)')`
- Extract expressions: `re.search(r'expansion of\s*([^.;]+)', text)`

### File Parsing
- Always use `encoding='utf-8', errors='ignore'` when opening files
- Strip whitespace: `line.strip()`
- Skip empty lines and comments: `if not line or line.startswith('#'): continue`

### Generating Reports
- Truncate long formulas: `formula_text[:200] + "..."` if over 200 chars
- Show both LODA and OEIS types for comparison
- Include reason for interest in output

## Testing Considerations

### When Adding New Patterns
- Test against sample OEIS and LODA formulas
- Check for false positives and false negatives
- Ensure patterns don't overlap incorrectly

### When Modifying Interest Rules
- Verify sorting still prioritizes explicit formulas
- Check that rational g.f. downgrade works correctly
- Test equivalence detection with parity formulas

## File I/O Patterns

### Input Files
- `data/formulas-oeis.txt`: Multi-line entries with 2-space indent for continuation
- `data/formulas-loda.txt`: Single line per sequence
- `data/names`: Format `A123456 Sequence name description`
- `data/stripped`: OEIS sequence terms ("stripped" export). Begins with comment lines `# ...`; each sequence line is `Axxxxxx ,t0,t1,t2,...` (comma-separated terms; long lines may wrap). Not yet used; reserved for future term-based validation.
- `data/offsets`: OEIS offsets table. One line per sequence: `Axxxxxx: n0,k` where `n0` is the primary offset (index of first listed term) and `k` is the secondary offset (position of the first term with |a(n)| > 1). Secondary may be omitted; negative or large offsets are possible. Use `n0` for index normalization; `k` is mainly informational/sorting.

### Output Files
- `results/interesting_formulas.txt`: Human-readable report
- Use `max_results` parameter for console vs. file output
- Full report to file, summary (50 entries) to console

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

### Offsets (OEIS)
- Primary offset (first number) gives the index of the first listed term; use it to align OEIS terms with LODA's `n >= 0` convention and to normalize formulas like `a(n+1)` vs `a(n)`.
- Secondary offset (second number) is auto-assigned; it is 1-indexed and marks the first term with |a(n)| > 1. It may be omitted; keep it as optional metadata, not as an index shift.
- Common values: 0 for functions on nonnegative integers, 1 for “numbers such that …” lists. Negative or large offsets exist (e.g., constants, huge-start sequences). For arrays/triangles, offset is the first row index.
- Parsing: split `Axxxxxx: n0,k`; `k` may be missing; allow negatives and large integers; skip malformed lines.
- Usage in comparator/parity checks: adjust indexing with `n0`; avoid treating novelty that is purely an offset shift as interesting; do not penalize based on `k` aside from lexicographic/sorting needs.

## Dependencies and Environment

- Python 3.7+ (uses dataclasses, type hints)
- Standard library only (no external dependencies)
- Uses: `re`, `typing`, `dataclasses`, `collections`, `enum`, `os`, `sys`

## Output Interpretation

### Interest Reasons (Common)
- "LODA provides explicit formula where OEIS only has recurrence" - High value
- "LODA supplies explicit piecewise polynomial closed form derivable from rational generating function; moderate novelty" - Medium value
- "LODA provides closed form where OEIS has sum/product/integral" - High value
- "LODA provides binomial formula not in OEIS" - Medium value
- "LODA formula equivalent to existing OEIS explicit parity formula" - Low value (filtered)

## Best Practices

1. **Always preserve existing classifications**: Don't remove types, add new ones
2. **Be specific with regex**: Avoid overly broad patterns that cause false positives
3. **Handle edge cases**: Empty strings, missing data, malformed input
4. **Document complex logic**: Interest rules and equivalence detection need comments
5. **Sort results meaningfully**: Prioritize high-value discoveries (explicit formulas)
6. **Truncate output appropriately**: Console gets summary, file gets full report

## Avoid These Common Mistakes

- ❌ Assuming one formula per sequence in OEIS (there can be multiple)
- ❌ Ignoring continuation lines in OEIS files (2-space indent)
- ❌ Treating all explicit formulas equally (parity-based are less novel)
- ❌ Missing rational g.f. presence (downgrades novelty)
- ❌ Forgetting to check `FormulaType.UNKNOWN` in comparisons
- ❌ Using absolute classification (formulas can have multiple types)
- ❌ Claiming LODA provides a binomial formula when the OEIS sequence name already states it's a binomial coefficient
- ❌ Ignoring sequence names when determining formula type coverage (names can imply types without explicit formula entries)
