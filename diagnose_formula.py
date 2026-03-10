#!/usr/bin/env python3
"""Diagnostic script for investigating OEIS formula issues.

Usage:
    python diagnose_formula.py A003600
    python diagnose_formula.py A003600 A006470 A027930
    python diagnose_formula.py --check-denylist

Collects local data (formulas, offset, terms, name) for each sequence,
parses all OEIS formulas, evaluates them against known terms, and reports
mismatches with details.

The --check-denylist mode analyzes all denylisted sequences and recommends
which can be safely removed.
"""

import re
import sys
from pathlib import Path

from formula.data import (
    DENYLIST_LODA,
    DENYLIST_OEIS,
    OEIS_ALLOWED_FUNCTIONS,
    _parse_oeis_formula_text,
    load_offsets,
    load_stripped_terms,
)
from formula.parser import FormulaParser

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"

OEIS_HEADER_RE = re.compile(r"^(A\d{6}):\s*(.+)$")
OEIS_FORMULA_RE = re.compile(r"a\(n\)\s*=", re.IGNORECASE)


def load_name(seq_id: str) -> str:
    """Load the sequence name/description from data/names."""
    pattern = re.compile(rf"^{re.escape(seq_id)}\s+(.+)$")
    path = DATA_DIR / "names"
    if not path.exists():
        return "(names file not found)"
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            m = pattern.match(line.strip())
            if m:
                return m.group(1)
    return "(not found)"


def load_oeis_lines(seq_id: str) -> list[str]:
    """Load all OEIS formula file lines for a given sequence."""
    path = DATA_DIR / "formulas-oeis.txt"
    lines: list[str] = []
    capturing = False
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        for raw_line in f:
            line = raw_line.rstrip("\n")
            header = OEIS_HEADER_RE.match(line)
            if header:
                if header.group(1) == seq_id:
                    capturing = True
                    lines.append(line)
                elif capturing:
                    break  # next sequence
                continue
            if capturing and line.startswith("  "):
                lines.append(line)
    return lines


def load_loda_line(seq_id: str) -> str | None:
    """Load the LODA formula line for a given sequence."""
    pattern = re.compile(rf"^{re.escape(seq_id)}:\s*(.+)$", re.IGNORECASE)
    path = DATA_DIR / "formulas-loda.txt"
    if not path.exists():
        return None
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            m = pattern.match(line.strip())
            if m:
                return m.group(0)
    return None


def extract_oeis_formulas(lines: list[str]) -> list[str]:
    """Extract a(n)=... formula texts from OEIS lines."""
    formulas: list[str] = []
    for line in lines:
        header = OEIS_HEADER_RE.match(line)
        text = header.group(2).strip() if header else line.strip()
        if OEIS_FORMULA_RE.search(text):
            formulas.append(text)
    return formulas


def diagnose(seq_id: str) -> None:
    print(f"{'=' * 70}")
    print(f"  {seq_id}")
    print(f"{'=' * 70}")

    # Denylist status
    in_oeis_deny = seq_id in DENYLIST_OEIS
    in_loda_deny = seq_id in DENYLIST_LODA
    if in_oeis_deny or in_loda_deny:
        parts = []
        if in_oeis_deny:
            parts.append("DENYLIST_OEIS")
        if in_loda_deny:
            parts.append("DENYLIST_LODA")
        print(f"Denylist: {', '.join(parts)}")
    else:
        print("Denylist: (none)")

    # Name
    name = load_name(seq_id)
    print(f"Name: {name}")

    # Offset
    offsets = load_offsets(str(DATA_DIR / "offsets"))
    offset = offsets.get(seq_id)
    if offset is None:
        print(f"Offset: (not found in data/offsets)")
        print("Cannot proceed without offset.\n")
        return
    print(f"Offset: {offset}")

    # Terms
    terms_dict = load_stripped_terms(str(DATA_DIR / "stripped"), {seq_id}, max_terms=20)
    terms = terms_dict.get(seq_id, [])
    if not terms:
        print("Terms: (not found in data/stripped)")
        print("Cannot proceed without terms.\n")
        return
    print(f"Terms ({len(terms)}): {terms}")

    # OEIS formula lines
    oeis_lines = load_oeis_lines(seq_id)
    print(f"\nOEIS formula file ({len(oeis_lines)} lines):")
    for line in oeis_lines:
        print(f"  {line}")

    # LODA formula
    loda_line = load_loda_line(seq_id)
    if loda_line:
        print(f"\nLODA formula: {loda_line}")
    else:
        print("\nLODA formula: (none)")

    # Parse and evaluate all a(n)= formulas
    formula_texts = extract_oeis_formulas(oeis_lines)
    if not formula_texts:
        print("\nNo a(n)= formulas found in OEIS lines.")
        print()
        return

    parser = FormulaParser()
    print(f"\n--- Evaluation against terms (offset={offset}) ---")

    for text in formula_texts:
        print(f"\nFormula text: {text}")

        # Use the real parsing pipeline (same as iter_oeis_formulas)
        formula = _parse_oeis_formula_text(seq_id, text, parser)
        if formula is None:
            print("  -> Not parseable by pipeline")
            continue

        print(f"  Parsed expr: {formula.expression}")
        if formula.lower_bound is not None:
            print(f"  Lower bound: {formula.lower_bound}")

        lower_bound = formula.lower_bound if formula.lower_bound is not None else offset
        start_idx = max(0, lower_bound - offset)
        limit = min(len(terms), start_idx + 10)

        if start_idx > 0:
            print(f"  Skipping {start_idx} terms (n < {lower_bound})")

        ok_count = 0
        fail_count = 0
        for idx in range(start_idx, limit):
            n = offset + idx
            expected = terms[idx]
            try:
                got = formula.evaluate(n)
            except Exception as e:
                print(f"  n={n}: ERROR ({e}), expected={expected}")
                fail_count += 1
                continue
            if got == expected:
                ok_count += 1
                print(f"  n={n}: {got} = {expected}  OK")
            else:
                fail_count += 1
                diff = got - expected if isinstance(got, int) else "?"
                print(f"  n={n}: {got} != {expected}  MISMATCH (diff={diff})")

        print(f"  Result: {ok_count} OK, {fail_count} MISMATCH")

    print()


def check_formula_status(seq_id: str) -> dict:
    """Check validation status of a denylisted sequence.
    
    Returns dict with:
        - seq_id: sequence ID
        - in_oeis_deny: bool
        - in_loda_deny: bool
        - status: 'validated', 'rejected_by_parser', 'has_mismatches', 'no_data'
        - ok_count: number of successful validations
        - fail_count: number of mismatches
        - not_parseable_count: number of formulas rejected by parser
        - correction_metadata: list of correction attributions found
    """
    result = {
        'seq_id': seq_id,
        'in_oeis_deny': seq_id in DENYLIST_OEIS,
        'in_loda_deny': seq_id in DENYLIST_LODA,
        'status': 'no_data',
        'ok_count': 0,
        'fail_count': 0,
        'not_parseable_count': 0,
        'correction_metadata': []
    }
    
    # Load data
    offsets = load_offsets(str(DATA_DIR / "offsets"))
    offset = offsets.get(seq_id)
    if offset is None:
        return result
    
    terms_dict = load_stripped_terms(str(DATA_DIR / "stripped"), {seq_id}, max_terms=20)
    terms = terms_dict.get(seq_id, [])
    if not terms:
        return result
    
    # Check OEIS formulas
    oeis_lines = load_oeis_lines(seq_id)
    formula_texts = extract_oeis_formulas(oeis_lines)
    
    if not formula_texts:
        result['status'] = 'no_data'
        return result
    
    # Look for correction metadata in formula lines
    for line in oeis_lines:
        if re.search(r'\[corrected by\s+_[^_]+_,\s+\w+\s+\d+\s+\d{4}\]', line, re.IGNORECASE):
            match = re.search(r'\[corrected by\s+(_[^_]+_),\s+(\w+\s+\d+\s+\d{4})\]', line, re.IGNORECASE)
            if match:
                result['correction_metadata'].append(f"{match.group(1)} on {match.group(2)}")
    
    parser = FormulaParser()
    total_formulas = 0
    
    for text in formula_texts:
        total_formulas += 1
        formula = _parse_oeis_formula_text(seq_id, text, parser)
        
        if formula is None:
            result['not_parseable_count'] += 1
            continue
        
        # Evaluate formula
        lower_bound = formula.lower_bound if formula.lower_bound is not None else offset
        start_idx = max(0, lower_bound - offset)
        limit = min(len(terms), start_idx + 10)
        
        formula_ok = True
        for idx in range(start_idx, limit):
            n = offset + idx
            expected = terms[idx]
            try:
                got = formula.evaluate(n)
                if got == expected:
                    result['ok_count'] += 1
                else:
                    result['fail_count'] += 1
                    formula_ok = False
                    break
            except Exception:
                result['fail_count'] += 1
                formula_ok = False
                break
    
    # Determine overall status
    if result['not_parseable_count'] == total_formulas:
        result['status'] = 'rejected_by_parser'
    elif result['fail_count'] == 0 and result['ok_count'] > 0:
        result['status'] = 'validated'
    elif result['fail_count'] > 0:
        result['status'] = 'has_mismatches'
    else:
        result['status'] = 'no_data'
    
    return result


def check_denylist_status() -> None:
    """Check all denylisted sequences and report which can be removed."""
    print("=" * 80)
    print("DENYLIST STATUS CHECK")
    print("=" * 80)
    print()
    
    all_denylisted = sorted(DENYLIST_OEIS | DENYLIST_LODA)
    
    if not all_denylisted:
        print("No sequences in denylist.")
        return
    
    print(f"Checking {len(all_denylisted)} denylisted sequences...")
    print()
    
    can_remove_validated = []
    can_remove_parser_rejected = []
    must_keep = []
    no_data = []
    
    for seq_id in all_denylisted:
        result = check_formula_status(seq_id)
        
        if result['status'] == 'validated':
            can_remove_validated.append(result)
        elif result['status'] == 'rejected_by_parser':
            can_remove_parser_rejected.append(result)
        elif result['status'] == 'has_mismatches':
            must_keep.append(result)
        else:
            no_data.append(result)
    
    # Report results
    print("✅ CAN REMOVE (formulas now validate correctly):")
    print("-" * 80)
    if can_remove_validated:
        for r in can_remove_validated:
            denylist_type = "OEIS" if r['in_oeis_deny'] else "LODA"
            corrections = ""
            if r['correction_metadata']:
                corrections = " [" + ", ".join(r['correction_metadata']) + "]"
            print(f"  {r['seq_id']} ({denylist_type}): {r['ok_count']} OK, 0 MISMATCH{corrections}")
    else:
        print("  (none)")
    print()
    
    print("✅ CAN REMOVE (all formulas rejected by parser, denylist unnecessary):")
    print("-" * 80)
    if can_remove_parser_rejected:
        for r in can_remove_parser_rejected:
            denylist_type = "OEIS" if r['in_oeis_deny'] else "LODA"
            print(f"  {r['seq_id']} ({denylist_type}): {r['not_parseable_count']} formula(s) not parseable")
    else:
        print("  (none)")
    print()
    
    print("⚠️  KEEP IN DENYLIST (formulas have validation failures):")
    print("-" * 80)
    if must_keep:
        for r in must_keep:
            denylist_type = "OEIS" if r['in_oeis_deny'] else "LODA"
            print(f"  {r['seq_id']} ({denylist_type}): {r['ok_count']} OK, {r['fail_count']} MISMATCH")
    else:
        print("  (none)")
    print()
    
    if no_data:
        print("ℹ️  NO DATA (cannot evaluate):")
        print("-" * 80)
        for r in no_data:
            denylist_type = "OEIS" if r['in_oeis_deny'] else "LODA"
            print(f"  {r['seq_id']} ({denylist_type})")
        print()
    
    # Summary
    print("=" * 80)
    print("SUMMARY:")
    print(f"  Total denylisted: {len(all_denylisted)}")
    print(f"  Can remove (validated): {len(can_remove_validated)}")
    print(f"  Can remove (rejected by parser): {len(can_remove_parser_rejected)}")
    print(f"  Must keep (has mismatches): {len(must_keep)}")
    if no_data:
        print(f"  No data: {len(no_data)}")
    print()
    
    total_removable = len(can_remove_validated) + len(can_remove_parser_rejected)
    if total_removable > 0:
        print(f"✨ {total_removable} sequence(s) can be safely removed from the denylist.")
        print()
        print("Next steps:")
        print("  1. Remove sequences from DENYLIST_OEIS/DENYLIST_LODA in formula/data.py")
        print("  2. Remove from pending_oeis_submissions.md if listed there")
        print("  3. Run tests: python -m unittest tests.test_formula_parser -v")
    else:
        print("No sequences can be removed at this time.")
    print()


def main() -> None:
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <sequence_id> [<sequence_id> ...]")
        print(f"       {sys.argv[0]} --check-denylist")
        print(f"Example: {sys.argv[0]} A003600 A006470")
        sys.exit(1)
    
    # Check for --check-denylist flag
    if sys.argv[1] == "--check-denylist":
        check_denylist_status()
        return

    seq_pattern = re.compile(r"^A\d{6}$")
    for arg in sys.argv[1:]:
        if not seq_pattern.match(arg):
            print(f"Invalid sequence ID: {arg} (expected format: A123456)")
            sys.exit(1)

    for seq_id in sys.argv[1:]:
        diagnose(seq_id)


if __name__ == "__main__":
    main()
