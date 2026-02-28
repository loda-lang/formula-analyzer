#!/usr/bin/env python3
"""Diagnostic script for investigating OEIS formula issues.

Usage:
    python diagnose_formula.py A003600
    python diagnose_formula.py A003600 A006470 A027930

Collects local data (formulas, offset, terms, name) for each sequence,
parses all OEIS formulas, evaluates them against known terms, and reports
mismatches with details.
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


def main() -> None:
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <sequence_id> [<sequence_id> ...]")
        print(f"Example: {sys.argv[0]} A003600 A006470")
        sys.exit(1)

    seq_pattern = re.compile(r"^A\d{6}$")
    for arg in sys.argv[1:]:
        if not seq_pattern.match(arg):
            print(f"Invalid sequence ID: {arg} (expected format: A123456)")
            sys.exit(1)

    for seq_id in sys.argv[1:]:
        diagnose(seq_id)


if __name__ == "__main__":
    main()
