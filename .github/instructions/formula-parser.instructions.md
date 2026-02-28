---
description: "Use when working on formula parsing, the tokenizer, AST nodes, expression evaluation, formula validation against OEIS terms, or the test_formula_parser test."
---
# Formula Parser Implementation

## Module: formula/parser.py

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

## Module: formula/data.py

**Purpose**: Load formulas from files, filter with denylists, manage offsets.

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

## Module: tests/test_formula_parser.py

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

## Common Mistakes to Avoid

- ❌ Using integer division for the division operator (breaks functions requiring true division)
- ❌ Accepting unwhitelisted identifiers as function names (reject unsupported operations during tokenization)
- ❌ Allowing OEIS formulas beyond current parser capabilities (restrict to reliably parseable patterns)
- ❌ Evaluating formulas at wrong offset (use OEIS offset, not 0)
- ❌ Expecting formulas to work at multiple offsets (strict validation: one offset only)
