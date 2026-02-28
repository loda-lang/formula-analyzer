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

## Formula Parser Implementation

### Module: formula/parser.py

**Purpose**: Parse and evaluate mathematical expressions for formula validation.

**Architecture**:
- **Tokenizer** (`_tokenize`): Regex-based lexer producing tokens for literals, variables, operators, functions, and delimiters
- **Parser** (`Parser` class): Recursive descent parser building AST from tokens
- **AST Nodes**: Typed nodes for literals, variables, binary operations, unary operations, and function calls
- **Evaluator** (`_eval_node`): Recursive evaluation of AST nodes

**Supported Syntax**:
- Arithmetic operations with proper precedence
- Exponentiation
- Whitelisted mathematical functions with arguments
- Parentheses for grouping

**Key Design Decisions**:
1. **Float division**: Division uses true division (not integer division) to support functions like ceiling correctly
2. **Function whitelist**: Only explicitly supported functions are recognized; unknown identifiers raise errors during tokenization
3. **Case-insensitive variable**: Variable `n` handled case-insensitively
4. **Parse-time validation**: Unsupported operations rejected during parsing (not just evaluation)

**Error Handling**:
- Parse errors return `None` from `FormulaParser.parse_expression()`
- Evaluation errors (e.g., division by zero) raise ValueError
- Unsupported functions/identifiers raise ValueError with descriptive message

### Module: formula/data.py

**Purpose**: Load formulas from files, filter with denylists, manage offsets.

**Key Components**:

**Denylists**:
```python
DENYLIST_OEIS: set[str]  # Sequences with offset/parsing issues
DENYLIST_LODA: set[str]  # Sequences with offset mismatches
```

**Regex Patterns**:
- `LODA_LINE_RE`: Matches `A123456: a(n) = <expr>`
- `OEIS_HEADER_RE`: Matches `A123456: <text>`
- `OEIS_FORMULA_RE`: Matches `a(n) =` within text

**Functions**:
- `iter_loda_formulas(path, parser)`: Yields parsed LODA formulas, skips denylist
- `iter_oeis_formulas(path, parser)`: Yields parsed OEIS formulas, skips denylist, filters high-degree polynomials
- `_parse_oeis_formula_text(seq_id, text, parser)`: Extracts `a(n) = <expr>`, validates charset, requires 'n' and operators; extracts domain restrictions
- `_extract_lower_bound(op, value)`: Converts `>` / `>=` operator and value to inclusive lower bound
- `load_offsets(path)`: Returns `Dict[str, int]` mapping sequence IDs to primary offset
- `load_stripped_terms(path, target_ids, max_terms)`: Returns `Dict[str, List[int]]` of sequence terms

**OEIS Formula Domain Restriction Parsing**:
- Extracts lower bounds from prefix patterns: `for n>=5, a(n) = ...` or `for n>0:`
- Extracts lower bounds from suffix patterns: `a(n) = ... for n >= 2`
- Converts `>` to inclusive bound: `n > 0` becomes `lower_bound = 1`
- Rejects compound conditions: `for n > 0 and even`, `for n >= 1 and odd`
- Rejects modular/parity restrictions: `for n mod 6 = 0`, `for n even`
- Rejects conditional prefixes: `if`, `for squarefree n`, `for n=4m+1`
- Rejects table/column/row/diagonal formulas
- Rejects relational formulas: `3*a(n) = ...`, `A352757(n) - a(n) = ...`
- Strips trailing domain text and initial conditions from expression before parsing

**OEIS Formula Parsing Restrictions**:
- Charset limited to basic operations to prevent misparsing complex formulas
- Must contain variable `n`
- Must include at least one operator
- High-degree polynomials filtered to avoid unreliable cases
- Formulas with `(-1)^n` rejected (parity-alternating, not simple polynomials)
- Formulas preceded by `Empirical:` rejected

These restrictions keep coverage focused on formulas that can be reliably validated with the current parser implementation.

### Module: tests/test_formula_parser.py

**Purpose**: Validate that parsed formulas produce correct sequence terms.

**Test Method**: `test_parse_and_evaluate_formulas`

**Workflow**:
1. Parse LODA formulas from `data/formulas-loda.txt`
2. Parse OEIS formulas from `data/formulas-oeis.txt`
3. Load offsets from `data/offsets`
4. Compute `max_terms` needed based on domain-restricted formulas' lower bounds
5. Load sequence terms from `data/stripped`
6. For each formula with available terms:
   - Compute effective lower bound: `formula.lower_bound` if set, otherwise sequence offset
   - Skip terms below the formula's domain (`start_idx = max(0, lower_bound - offset)`)
   - Evaluate at up to 5 positions within the valid domain
   - Compare with expected OEIS terms
   - Track mismatches
7. Assert: `mismatches == 0` (strict validation)
8. Assert: all supported functions exercised by at least one formula

**Debug Output**:
```python
print(f"Parsed formulas: {len(all_formulas)}; with OEIS terms: {len(formula_dict)}")
print(f"Parsed LODA: {loda_count}; Parsed OEIS: {oeis_count}")
print(f"Checked sequences: {len(checked)}; LODA: {loda_checked}; OEIS: {oeis_checked}")
print(f"Comparisons: {comparisons}; mismatches: {mismatches}")
```

**Success Criteria**:
- Zero mismatches in validation
- Maximized formula coverage within parser capabilities

## Offset Handling Details

**The Offset Problem**:
- OEIS sequences have varying starting indices (offset)
- Common offsets: 0 (functions on non-negative integers), 1 ("numbers such that"), sometimes negative or large
- LODA exports generally follow OEIS offsets, but some formulas contain incorrect or outdated offset information (often assuming n starts at 0); those should be ignored/denylisted
- Formulas like `a(n) = floor((n-1)/2)` may be written for offset 0 but OEIS uses offset 1

**Validation Strategy**:
- Use OEIS offset as the ground truth
- For domain-restricted formulas, use `formula.lower_bound` as effective start
- Evaluate formula at positions: `n = offset + idx` for each term at index `idx`
- Skip terms where `n < lower_bound` (formula is not valid there)
- Require exact match: `formula.evaluate(offset + idx) == terms[idx]`
- No fallback shifts or offset corrections attempted

**Why This Is Strict**:
- Prevents false positives from formulas that accidentally match at wrong indices
- Makes offset assumptions explicit
- Forces correct formula representation

**When Formulas Fail Validation**:
1. **Offset mismatch**: LODA formula uses different n convention than OEIS
   - Example: `floor((n-1)/2)` at offset 1 shifts by one position
   - Solution: Add to `DENYLIST_LODA`
2. **Domain restrictions**: OEIS formula has special cases or constraints not in formula text
   - Many domain restrictions (e.g., `for n >= 5`) are now parsed automatically and stored as `lower_bound`
   - Remaining issues: compound conditions (`for n > 0 and even`), parity-specific sub-formulas
   - Solution: Reject during parsing or add to `DENYLIST_OEIS`
3. **OEIS data quality issues**: Formula text has typos, missing factors, or off-by-one errors
   - Example: formula missing `/2`, or shifted by one index vs OEIS terms
   - Solution: Add to `DENYLIST_OEIS`
4. **Parsing errors**: Formula text ambiguous or uses unsupported syntax
   - Solution: Improve parser or add to denylist if unresolvable

## Denylist Management

**Location**: `formula/data.py`

**DENYLIST_LODA**:
- Sequences where LODA formula assumes offset 0 or embeds outdated/incorrect offset info while OEIS offset ≠ 0
- Added when validation produces mismatch due to index shift
- Examples with floor/ceil: A186704, A385730, A386858, A389928
- Examples with other operations: A044187, A156772, A157105

**DENYLIST_OEIS**:
- Sequences where OEIS formula has validation issues
- Reasons: off-by-one errors in formula text, missing factors/typos, parity-specific sub-formulas, ambiguous precedence
- Examples: A007183 (off-by-one), A215543 (missing /2), A279112 (parity sub-formulas), A303295 (precedence)

**When to Add to Denylist**:
1. Formula parses successfully
2. Evaluation produces values
3. Values don't match OEIS terms at documented offset
4. Manual inspection confirms offset issue or formula limitation
5. If the local offset or formula data doesn't match the data on the OEIS website, refresh the sequence using the LODA MCP server (`mcp_loda_refresh_sequence`), wait for the updated data, and then remove the sequence from the denylist — do NOT add it
6. Otherwise (genuine formula error), add sequence ID to appropriate denylist with comment

**Denylist Format**:
```python
DENYLIST_LODA: set[str] = {
    # LODA formulas with offset or validation issues
    "A093353",
    "A283049",
}
```

**Alternatives Considered**:
- **Automatic offset correction**: Try formula at offset ±1, ±2 until match found
  - Rejected: Too many false positives, hides real formula errors
- **Dual-offset validation**: Accept match at either OEIS offset or offset 0
  - Rejected: Allows incorrect formulas to pass validation
- **Formula rewriting**: Automatically adjust `n` to `n-k` or `n+k`
  - Rejected: Changes formula semantics, not reliable for complex expressions

**Current Approach** (denylists):
- ✓ Explicit and maintainable
- ✓ Zero false positives in validation
- ✓ Clear documentation of problematic sequences
- ✓ Easy to audit and update
- ⚠ Requires manual curation when adding floor/ceil or other new operations

## Validating OEIS Entries

When a formula mismatch is detected, validate the OEIS entry to determine whether the error is in our local data or on the OEIS website.

### Step 1: Fetch the Latest OEIS Data

Use the text format for efficient, parseable output (avoids HTML noise):
```
https://oeis.org/search?q=id:A297740&fmt=text
```
This returns structured fields: `%S` (terms), `%F` (formulas), `%O` (offset), etc.

Alternatively, fetch the HTML page at `https://oeis.org/A297740` for a human-readable view with formula attribution and dates.

### Step 2: Cross-Check with Local Data

Compare the OEIS website data against local files:
- **Offset**: Compare `%O` field with `data/offsets` entry. If they differ, the local data is stale.
- **Formula text**: Compare `%F` entries with `data/formulas-oeis.txt`. If the OEIS has a corrected formula (e.g., added `/2`, changed coefficients), the local data is stale.
- **Terms**: Compare `%S`/`%T`/`%U` fields with `data/stripped`. Terms rarely change but verify if in doubt.

### Step 3: Determine the Error Source

**If local data is stale** (offset or formula differs from OEIS website):
1. Refresh the sequence: `mcp_loda_refresh_sequence` with the sequence ID
2. Wait for the updated data to propagate to local files
3. Remove the sequence from the denylist
4. Re-run tests to confirm the fix

**If the OEIS formula is genuinely wrong** (website matches local data but formula doesn't match terms):
1. Evaluate the formula at several positions using the documented offset
2. Compare with the listed terms to confirm the mismatch pattern
3. Identify the error type:
   - **Off-by-one domain**: Formula gives `a(n+1)` instead of `a(n)`. Fix: shift domain bound by 1 or substitute `n-1` and re-expand.
   - **Wrong constant/coefficient**: Formula is off by a fixed amount at every point. Fix: compute the correct constant from the terms.
   - **Non-integer values**: Polynomial produces fractions for some n. Fix: check for missing denominators or wrong coefficients.
   - **Notation ambiguity**: OEIS notation like `1/48*n^6` can be misread. This is a parser limitation, not always an OEIS error.
4. Derive the corrected formula and verify it against terms
5. Submit a correction to the OEIS (requires an OEIS account)
6. Keep the sequence in the denylist until the correction is published and local data is refreshed

### Submitting OEIS Corrections

Go to `https://oeis.org/AXXXXXX`, click **edit**, update the formula line, and add an edit comment explaining:
- What was wrong (e.g., "formula off by one index", "constant should be 1212 not 1222")
- Evidence (e.g., "200*7 - 1222 = 178 but a(7) = 188")
- The corrected formula with its valid domain

### Common OEIS Error Patterns

- **Off-by-one in domain bounds**: Most frequent error. The formula is mathematically correct but the stated domain `for n >= k` is off by 1. Often caused by the contributor using 1-based indexing while the sequence has offset 0, or vice versa.
- **Typos in polynomial coefficients**: Wrong constant term, missing factor (e.g., `/2`), or swapped signs.
- **Parity-specific formulas without markers**: Two sub-formulas for even/odd n presented as a single formula or with ambiguous `IF(MOD(...))` notation.

## Dependencies and Environment

- Python 3.7+ (uses dataclasses, type hints)
- Standard library only (no external dependencies)
- Uses: `re`, `typing`, `dataclasses`, `collections`, `enum`, `os`, `sys`, `math`

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

**Formula Classification & Comparison**:
- ❌ Assuming one formula per sequence in OEIS (there can be multiple)
- ❌ Ignoring continuation lines in OEIS files (2-space indent)
- ❌ Treating all explicit formulas equally (parity-based are less novel)
- ❌ Missing rational g.f. presence (downgrades novelty)
- ❌ Forgetting to check `FormulaType.UNKNOWN` in comparisons
- ❌ Using absolute classification (formulas can have multiple types)
- ❌ Claiming LODA provides a binomial formula when the OEIS sequence name already states it's a binomial coefficient
- ❌ Ignoring sequence names when determining formula type coverage (names can imply types without explicit formula entries)

**Parser & Validation**:
- ❌ Using integer division for the division operator (breaks functions requiring true division)
- ❌ Accepting unwhitelisted identifiers as function names (reject unsupported operations during tokenization)
- ❌ Allowing OEIS formulas beyond current parser capabilities (restrict to reliably parseable patterns)
- ❌ Evaluating formulas at wrong offset (use OEIS offset, not 0)
- ❌ Expecting formulas to work at multiple offsets (strict validation: one offset only)
- ❌ Adding sequences to denylist without verifying offset mismatch (check manually first)
- ❌ Removing denylist entries to "improve coverage" (they prevent false validation failures)
- ❌ Implementing automatic offset correction (creates false positives; use denylists instead)