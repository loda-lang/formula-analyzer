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

### Offsets (OEIS)
- Primary offset gives the index of the first listed term (e.g., 0 or 1).
- Use it to align OEIS terms with formula evaluation and LODA's conventions.
- Format: `Axxxxxx: n0,k` — only `n0` is used for validation.

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

### `Formula` (dataclass in `formula/analyzer.py`)
- Immutable representation of a classified formula
- Fields: `sequence_id`, `text`, `source`, `types`
- Implement `__hash__` for set operations

### `Formula` (dataclass in `formula/formula.py`)
- Parsed formula with evaluable AST
- Fields: `sequence_id`, `source`, `expression`, `node`, `lower_bound`
- `evaluate(n)` computes the formula value at a given n

### `FormulaClassifier`
- Pattern-based classification using regex
- `PATTERNS` dict maps types to regex lists
- `classify_oeis()` and `classify_loda()` methods handle different syntaxes

### `FormulaParser` (`formula/parser.py`)
- Tokenizer and recursive descent parser for mathematical expressions
- `parse_expression(seq_id, source, expr, lower_bound, allowed_functions)` returns a `Formula` with evaluable AST or `None` on error
- `ALL_FUNCTIONS`: frozenset of all supported functions (default when `allowed_functions` is not specified)
- `allowed_functions` parameter restricts which functions the tokenizer accepts; callers pass a subset (e.g., `OEIS_ALLOWED_FUNCTIONS`) to limit OEIS parsing

### `FormulaParser` (`formula/analyzer.py`)
- File-level parser: reads and parses OEIS/LODA input files
- Handles multi-line OEIS entries (indentation-based)
- One formula per line for LODA
- Uses `defaultdict(list)` for OEIS to accumulate multiple formulas

### `FormulaComparator`
- Core comparison logic
- `find_new_formulas()` identifies interesting LODA formulas
- `_determine_interest()` implements priority-based interest rules
- `_has_rational_gf()` detects rational generating functions
- `_is_equivalent()` handles parity-based equivalence normalization

## Common Tasks

### Processing Multi-line OEIS Entries

```python
# Check for sequence ID line
match = re.match(r'(A\d{6}):\s*(.+)', line)

# Check for continuation (2-space indent)
if line.startswith('  ') and current_seq_id:
    current_lines.append(line[2:])
```

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

## File I/O Patterns

### Input Files
- `data/formulas-oeis.txt`: Multi-line entries with 2-space indent for continuation
- `data/formulas-loda.txt`: Single line per sequence
- `data/names`: Format `A123456 Sequence name description`
- `data/stripped`: OEIS sequence terms ("stripped" export). Begins with comment lines `# ...`; each sequence line is `Axxxxxx ,t0,t1,t2,...` (comma-separated terms; long lines may wrap). Used by `load_stripped_terms()` for formula validation against known terms.
- `data/offsets`: OEIS offsets table. Format `Axxxxxx: n0,k`.

### Output Files
- `results/interesting_formulas.txt`: Human-readable report
- `pending_oeis_submissions.md`: Tracked OEIS corrections — verified but not yet submitted or awaiting processing. Add new entries here when an OEIS formula error is confirmed; remove entries completely once the correction is published on OEIS AND confirmed in local data after a refresh (verify with `diagnose_formula.py` showing 0 mismatches). Do not keep "published" entries in the file.
- Use `max_results` parameter for console vs. file output
- Full report to file, summary (50 entries) to console

## Dependencies and Environment

- Python 3.7+ (uses dataclasses, type hints)
- Standard library only (no external dependencies)
- Uses: `re`, `typing`, `dataclasses`, `collections`, `enum`, `os`, `sys`, `math`

## Best Practices

1. **Always preserve existing classifications**: Don't remove types, add new ones
2. **Be specific with regex**: Avoid overly broad patterns that cause false positives
3. **Handle edge cases**: Empty strings, missing data, malformed input
4. **Document complex logic**: Interest rules and equivalence detection need comments
5. **Sort results meaningfully**: Prioritize high-value discoveries (explicit formulas)
6. **Truncate output appropriately**: Console gets summary, file gets full report
