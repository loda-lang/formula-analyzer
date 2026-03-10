---
description: "Use when working with denylists, offset handling, formula validation failures, refreshing stale data, or managing DENYLIST_OEIS / DENYLIST_LODA in data.py."
---
# Denylist and Offset Management

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

**When to Remove from Denylist**:

After a data refresh (`./run_formula_analysis.py --refresh-data`), check for sequences that can be removed:

1. **For stale data entries**: Run `diagnose_formula.py` on denylisted sequences to check if they now validate correctly (0 mismatches)
2. **For submitted OEIS corrections**: Check if the correction has been published by inspecting `data/formulas-oeis.txt` for correction attribution (e.g., `[Corrected by _Name_, Mon DD YYYY]`)
3. **Remove from denylist** if:
   - Formula now validates correctly (0 mismatches in diagnostic output)
   - Correction is visible in local data files
4. **Also remove from `pending_oeis_submissions.md`** if the correction has been published and confirmed in local data
5. **Run tests** after removal to confirm: `python -m unittest discover -s tests -p "test_*.py" -v`

**Important**: Only remove denylist entries after confirming the fix is present in local data AND validates correctly. Do not remove entries based solely on OEIS website status — the local data may lag behind by several days.

## Checking Denylist Status (Automated)

**When to check**: After running `./run_formula_analysis.py --refresh-data`

**Quick check** (automated):
```bash
python diagnose_formula.py --check-denylist
```

This will analyze all denylisted sequences and categorize them:
- ✅ **Can remove (validated)**: All formulas pass validation (0 MISMATCH)
- ✅ **Can remove (rejected by parser)**: All formulas marked "Not parseable by pipeline" (denylist unnecessary)
- ⚠️ **Keep in denylist**: At least one formula has validation failures

**Manual verification** (if automated mode unavailable):
1. Run diagnostics on all denylisted sequences:
   ```bash
   python diagnose_formula.py A244501 A299256 A364517 ...
   ```
2. For each sequence, determine:
   - **All formulas "Not parseable by pipeline"** → Remove from denylist (parser already rejects them)
   - **All formulas validate (0 MISMATCH)** → Remove from denylist (correction published and working)
   - **Any formula has MISMATCH** → Keep in denylist (still failing validation)
3. Look for correction metadata in formula text (e.g., `[Corrected by _Name_, Mon DD YYYY]`)
4. Cross-check with `pending_oeis_submissions.md` for submission status
5. Remove from both denylist and `pending_oeis_submissions.md` when confirmed
6. Run tests to verify: `python -m unittest tests.test_formula_parser -v`

**Key distinction**: Formulas rejected during parsing (e.g., parity-conditional formulas like "for even n", recursive definitions, generating functions) don't need denylist entries because they never reach the validation stage where they could cause test failures.

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

## Common Mistakes to Avoid

- ❌ Adding sequences to denylist without verifying offset mismatch (check manually first)
- ❌ Removing denylist entries to "improve coverage" (they prevent false validation failures)
- ❌ Implementing automatic offset correction (creates false positives; use denylists instead)
- ❌ Keeping published corrections in `pending_oeis_submissions.md` (remove them completely once confirmed in local data)
- ❌ Removing denylist entries before confirming the fix in local data (check with `diagnose_formula.py` first)
