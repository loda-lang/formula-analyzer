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
- `data/stripped`: OEIS sequence terms ("stripped" export). Begins with comment lines `# ...`; each sequence line is `Axxxxxx ,t0,t1,t2,...` (comma-separated terms; long lines may wrap). Used by `load_stripped_terms()` for formula validation against known terms.
- `data/offsets`: OEIS offsets table. Format `Axxxxxx: n0,k` — see [Offset Handling Details](#offset-handling-details) for full documentation.

### Output Files
- `results/interesting_formulas.txt`: Human-readable report
- `pending_oeis_submissions.md`: Tracked OEIS corrections — verified but not yet submitted or awaiting processing. Add new entries here when an OEIS formula error is confirmed; remove entries once the correction has been submitted and accepted.
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
- See [Offset Handling Details](#offset-handling-details) for full documentation.
- Primary offset gives the index of the first listed term (e.g., 0 or 1).
- Use it to align OEIS terms with formula evaluation and LODA's conventions.

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
2. **Function whitelist via `allowed_functions`**: Only functions in the `allowed_functions` frozenset are recognized by the tokenizer; unknown identifiers raise errors. Defaults to `ALL_FUNCTIONS`; OEIS uses `OEIS_ALLOWED_FUNCTIONS` (a subset)
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

**Constants**:
- `OEIS_ALLOWED_FUNCTIONS`: frozenset of functions allowed in OEIS formulas (currently `binomial`, `gcd`); add new functions here when extending OEIS parsing

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
- Rejects formulas where `a(n) =` is inside a Sum/Product expression (prefix ends with `}`)
- Strips trailing domain text and initial conditions from expression before parsing

**OEIS Formula Parsing Restrictions**:
- Charset allows digits, `n`, basic operators, parentheses, commas, and alphabetic characters
- Function filtering delegated to the parser via `allowed_functions=OEIS_ALLOWED_FUNCTIONS`; the tokenizer rejects any identifier not in that set
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
- For arrays/triangles, offset is the first row index
- LODA exports generally follow OEIS offsets, but some formulas contain incorrect or outdated offset information (often assuming n starts at 0); those should be ignored/denylisted
- Formulas like `a(n) = floor((n-1)/2)` may be written for offset 0 but OEIS uses offset 1

**Offset Format**: `Axxxxxx: n0,k` where `n0` is the primary offset and `k` (optional) is the 1-indexed position of the first term with |a(n)| > 1. Only `n0` is used for validation; `k` is informational.

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
1. **Stale local data**: Offset or formula text differs from the OEIS website
   - Solution: Refresh via `mcp_loda_refresh_sequence`; add to denylist with refresh date in comment. Remove from denylist once updated data is available locally (can take multiple days).
2. **Offset mismatch**: LODA program uses incorrect offset, producing a shifted formula
   - Verify by running `loda export -o loda <ID>` and checking the `#offset` line against the OEIS offset in `data/offsets`
   - Solution: Submit program removal via `mcp_loda_submit` (mode `remove`, type `program`); add to `DENYLIST_LODA` with removal trigger date in comment. Remove from denylist once the program is removed and the formula file is regenerated (can take multiple days).
3. **OEIS formula errors**: Formula text has typos, wrong domain bounds, missing factors, or off-by-one errors
   - Example: formula missing `/2`, or domain `for n >= k` off by 1
   - Solution: Submit a correction to OEIS; add to `DENYLIST_OEIS` until corrected and refreshed. Track the correction submission date in the denylist comment. Once the correction is published and local data is refreshed, remove from denylist.
4. **Parity-specific formulas**: Two sub-formulas for even/odd n missing parity markers in their domain
   - These are OEIS errors: the formulas should say `for even n >= k` / `for odd n >= k` but only say `for n > k`
   - Solution: Submit a correction to OEIS adding the missing parity markers; add to `DENYLIST_OEIS` until corrected
5. **Notation ambiguity**: OEIS notation like `1/48*n^6` misinterpreted by parser
   - Solution: Add to `DENYLIST_OEIS` (parser limitation)

## Denylist Management

**Location**: `formula/data.py`

**DENYLIST_LODA**:
- Sequences where the LODA program uses an incorrect offset, causing the exported formula to be shifted relative to OEIS terms
- LODA formulas are generated from LODA programs; if the program's `#offset` doesn't match the OEIS offset, the formula will be wrong
- Verify with `loda export -o loda <ID>` and compare the `#offset` line against `data/offsets`
- Trigger program removal via `mcp_loda_submit` (mode `remove`, type `program`) and track the removal date in the denylist comment

**DENYLIST_OEIS**:
- Sequences where OEIS formula has validation issues
- Reasons: off-by-one errors in formula text, missing factors/typos, parity-specific sub-formulas, ambiguous precedence

**When to Add to Denylist**:
1. Formula parses successfully
2. Evaluation produces values
3. Values don't match OEIS terms at documented offset
4. Manual inspection confirms offset issue or formula limitation
5. If the local offset or formula data doesn't match the data on the OEIS website, refresh the sequence using the LODA MCP server (`mcp_loda_refresh_sequence`) and add it to the denylist with a comment noting the refresh date (e.g., `"A228396",  # stale local offset; refresh triggered 2026-02-28`). It can take multiple days until the updated data is available locally, so do NOT expect to remove the entry immediately.
6. Once refreshed data has propagated (verify by checking local files), remove the sequence from the denylist and re-run tests.
7. Otherwise (genuine formula error), add sequence ID to appropriate denylist with comment

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

## Diagnosing Formula Issues

### Diagnostic Script: `diagnose_formula.py`

A helper script that automates data collection and basic checks for investigating denylist entries or formula mismatches.

**Usage**:
```bash
python diagnose_formula.py A003600
python diagnose_formula.py A003600 A006470 A027930
```

**What it does** (for each sequence ID):
1. Shows denylist membership (OEIS, LODA, or none)
2. Displays the sequence name/description from `data/names`
3. Shows the OEIS offset and first 20 terms from `data/stripped`
4. Lists all OEIS formula file lines (header + continuations)
5. Shows the LODA formula line if present
6. For each `a(n)=` formula, attempts parsing through the real pipeline (`_parse_oeis_formula_text`)
7. Evaluates parsed formulas at up to 10 positions and reports OK/MISMATCH per term

**When to use**:
- Investigating a denylist entry to determine the root cause
- Checking whether a formula mismatch is a domain issue, off-by-one, or genuine error
- Verifying a proposed correction before submitting to OEIS
- Quick triage of multiple sequences at once

**After running the script**, use the output to determine the next step:
- If the formula is correct from a higher n: missing domain restriction → submit OEIS correction
- If the formula is off by a constant or shifted: formula typo → submit OEIS correction
- If local data differs from OEIS website: stale data → refresh via `mcp_loda_refresh_sequence`

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
2. Add to the denylist with a comment noting the refresh date (it can take multiple days for the updated data to propagate to local files)
3. Once updated data is available locally (verify by checking local files), remove the sequence from the denylist
4. Re-run tests to confirm the fix

**If the OEIS formula is genuinely wrong** (website matches local data but formula doesn't match terms):
1. Identify which formula causes the mismatch. OEIS entries often contain multiple formulas per sequence (header line + continuation lines). Temporarily remove the sequence from the denylist, run tests, and check the error output to see which specific formula(s) fail. Alternatively, evaluate each parseable formula against the terms manually.
2. Evaluate the failing formula at several positions using the documented offset
3. Compare with the listed terms to confirm the mismatch pattern
4. Identify the error type:
   - **Off-by-one domain**: Formula gives `a(n+1)` instead of `a(n)`. Fix: shift domain bound by 1 or substitute `n-1` and re-expand.
   - **Wrong constant/coefficient**: Formula is off by a fixed amount at every point. Fix: compute the correct constant from the terms.
   - **Non-integer values**: Polynomial produces fractions for some n. Fix: check for missing denominators or wrong coefficients. If fractions appear only for one parity of n, the formula may be a parity sub-formula missing its even/odd domain marker.
   - **Notation ambiguity**: OEIS notation like `1/48*n^6` can be misread. This is a parser limitation, not always an OEIS error.
5. Derive the corrected formula and verify it against terms
6. Submit a correction to the OEIS (requires an OEIS account)
7. Keep the sequence in the denylist until the correction is published and local data is refreshed

### Submitting OEIS Corrections

When a genuine OEIS formula error is confirmed, add the correction to `pending_oeis_submissions.md` with the current formula, corrected formula, and evidence. This file tracks all pending corrections.

To submit: go to `https://oeis.org/AXXXXXX`, click **edit**, update the formula line, and add an edit comment explaining:
- What was wrong (e.g., "formula off by one index", "constant should be 1212 not 1222")
- Evidence (e.g., "200*7 - 1222 = 178 but a(7) = 188")
- The corrected formula with its valid domain

After submission, update the denylist comment with the submission date. Once the correction is published and local data is refreshed, remove the entry from both the denylist and `pending_oeis_submissions.md`.

### Checking OEIS Submissions

When asked to check or review a submitted OEIS correction, fetch the draft page and verify the edit:

1. **Fetch the draft**: Use `https://oeis.org/draft/AXXXXXX` to see the proposed changes (additions in bold blue, deletions in faded red).
2. **Verify the change is correct**:
   - Confirm the corrected formula matches what was documented in `pending_oeis_submissions.md`
   - Check that only the intended lines were modified (no accidental edits to other formulas)
   - Verify the domain restriction is appropriate (not too narrow, not too wide)
   - For domain additions: verify the formula fails at the boundary (e.g., at `n = k-1` for `n >= k`)
   - For coefficient corrections: verify the corrected formula matches terms at multiple positions
   - For index-shift fixes: verify the corrected expression is algebraically equivalent to substituting `n-1` in the original
3. **Check the edit comment**: Should clearly explain what was wrong and provide evidence
4. **Check attribution**: The "Corrected by" line should include the editor's name and date
5. **Status**: Should be "proposed" (awaiting reviewer approval)

**Common issues to watch for in submissions**:
- Accidentally editing the wrong formula line in multi-formula entries
- Missing or incorrect attribution format (should be `_Name_, Mon DD YYYY`)
- Domain restriction that is too tight (formula works at more values than stated) or too loose
- Forgetting to remove trailing periods or semicolons from corrected formula text

### Common OEIS Error Patterns

- **Off-by-one in domain bounds**: Most frequent error. The formula is mathematically correct but the stated domain `for n >= k` is off by 1. Often caused by the contributor using 1-based indexing while the sequence has offset 0, or vice versa.
- **Typos in polynomial coefficients**: Wrong constant term, missing factor (e.g., `/2`), or swapped signs.
- **Parity-specific formulas without markers**: Two sub-formulas for even/odd n presented after an `IF(MOD(...))` conditional but missing their parity restrictions (e.g., `for n>1` instead of `for even n >= 2`). Identifiable because one formula produces non-integer values for one parity of n.

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