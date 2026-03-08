---
description: "Use when validating OEIS entries, submitting corrections, checking OEIS draft submissions, diagnosing formula mismatches, or working with pending_oeis_submissions.md."
---
# OEIS Corrections Workflow

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
   - **Off-by-one domain**: Formula gives `a(n+1)` instead of `a(n)`. Fix: substitute `n-1` for `n` in the expression and re-expand. Do NOT just shift the domain bound — the formula itself must be rewritten.
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

### Tracking and Cleaning Up Published Corrections

**After data refresh**, check if any pending corrections have been published:

1. **Run diagnostics**: Use `diagnose_formula.py` on sequences in `pending_oeis_submissions.md` to check if formulas now validate correctly
2. **Verify publication**: Check the OEIS formula file (`data/formulas-oeis.txt`) for correction attribution (e.g., `[Corrected by _Name_, Mon DD YYYY]`)
3. **For published corrections**:
   - Remove the sequence from `DENYLIST_OEIS` in `formula/data.py`
   - Remove the entry from `pending_oeis_submissions.md` entirely (do not mark as published — simply delete)
   - Run tests to confirm the fix: `python -m unittest discover -s tests -p "test_*.py" -v`
4. **For corrections still pending**:
   - Keep in both denylist and pending submissions
   - Update status notes if submission has progressed (e.g., from "proposed" to "reviewed")

**Important**: Only remove entries from `pending_oeis_submissions.md` after BOTH conditions are met:
- The correction is published on the OEIS website (visible in the entry)
- The corrected data is present in local files after a refresh (confirmed via `diagnose_formula.py` showing 0 mismatches)

Do not keep entries marked as "PUBLISHED" in the pending file — once confirmed, remove them completely to keep the file clean and focused on actual pending work.

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
- **Index-shift errors**: Formula computes `a(n+1)` instead of `a(n)`. The fix requires substituting `n-1` for `n` throughout the expression — changing the domain bound alone is insufficient since it only changes where the formula is evaluated, not what it computes.
- **Typos in polynomial coefficients**: Wrong constant term, missing factor (e.g., `/2`), or swapped signs.
- **Parity-specific formulas without markers**: Two sub-formulas for even/odd n presented after an `IF(MOD(...))` conditional but missing their parity restrictions (e.g., `for n>1` instead of `for even n >= 2`). Identifiable because one formula produces non-integer values for one parity of n.
