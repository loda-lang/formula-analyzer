import re
from typing import Dict, Iterator, List, Optional, Set

from formula.parser import ParsedFormula, FormulaParser

# Temporary blacklist for OEIS formulas that are misleading/non-explicit in context
BLACKLIST_OEIS: set[str] = {"A103320", "A326991", "A326994"}

LODA_LINE_RE = re.compile(r"^(A\d{6}):\s*a\(n\)\s*=\s*(.+)$", re.IGNORECASE)
OEIS_HEADER_RE = re.compile(r"^(A\d{6}):\s*(.+)$")
OEIS_FORMULA_RE = re.compile(r"a\(n\)\s*=", re.IGNORECASE)


def iter_loda_formulas(path: str, parser: FormulaParser, offsets: Optional[dict[str, int]] = None) -> Iterator[ParsedFormula]:
    with open(path, "r", encoding="utf-8", errors="ignore") as handle:
        for raw_line in handle:
            parsed = _parse_loda_line(raw_line, parser)
            if not parsed:
                continue
            if offsets is not None:
                seq_offset = offsets.get(parsed.sequence_id, 0)
                # Skip formulas whose OEIS offset is nonzero; these often mismatch when treated as zero-based LODA code.
                if seq_offset != 0:
                    continue
            yield parsed


def iter_oeis_formulas(path: str, parser: FormulaParser, offsets: Optional[dict[str, int]] = None) -> Iterator[ParsedFormula]:
    current_id: Optional[str] = None
    with open(path, "r", encoding="utf-8", errors="ignore") as handle:
        for raw_line in handle:
            line = raw_line.rstrip("\n")
            seq_match = OEIS_HEADER_RE.match(line)
            if seq_match:
                current_id = seq_match.group(1)
                if current_id in BLACKLIST_OEIS:
                    current_id = None
                    continue
                if offsets is not None and offsets.get(current_id, 0) != 0:
                    current_id = None
                    continue
                remainder = seq_match.group(2)
                parsed = _parse_oeis_formula_text(current_id, remainder.strip(), parser)
                if parsed:
                    yield parsed
                continue
            if current_id and line.startswith("  "):
                cont = line.strip()
                if cont.lower().startswith("a(n) ="):
                    parsed = _parse_oeis_formula_text(current_id, cont, parser)
                    if parsed:
                        yield parsed


def _parse_loda_line(line: str, parser: FormulaParser) -> Optional[ParsedFormula]:
    match = LODA_LINE_RE.match(line.strip())
    if not match:
        return None
    seq_id, expr = match.group(1), match.group(2)
    if "," in expr:
        expr = expr.split(",", 1)[0].strip()
    return parser.parse_expression(seq_id, "loda", expr)


def _parse_oeis_formula_text(seq_id: str, text: str, parser: FormulaParser) -> Optional[ParsedFormula]:
    match = OEIS_FORMULA_RE.search(text)
    if not match:
        return None
    expr = text[match.end():].strip().rstrip(".;")
    # Restrict OEIS parsing to simple integer polynomials (no division) to avoid misparsing
    if not re.fullmatch(r"[0-9nN\+\-\*\^\(\)\s]+", expr):
        return None
    if "n" not in expr.lower():
        return None
    # Be conservative: drop higher-degree forms and trivial linear n-only cases to reduce misparsed OEIS formulas.
    if re.search(r"\^[3-9]\d*", expr):
        return None
    if not any(op in expr for op in ["+", "*", "^"]):
        return None
    return parser.parse_expression(seq_id, "oeis", expr)


def load_offsets(path: str) -> Dict[str, int]:
    offsets: Dict[str, int] = {}
    pattern = re.compile(r"^(A\d{6}):\s*(-?\d+)")
    with open(path, "r", encoding="utf-8", errors="ignore") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            match = pattern.match(line)
            if match:
                offsets[match.group(1)] = int(match.group(2))
    return offsets


def load_stripped_terms(path: str, target_ids: Set[str], max_terms: int = 10) -> Dict[str, List[int]]:
    collected: Dict[str, List[int]] = {}
    current_id: Optional[str] = None
    buffer: List[int] = []
    seq_line = re.compile(r"^(A\d{6})\s*,(.*)$")
    with open(path, "r", encoding="utf-8", errors="ignore") as handle:
        for raw_line in handle:
            if target_ids and _have_all(collected, target_ids, max_terms):
                break
            line = raw_line.strip()
            if not line or line.startswith("#"):
                continue
            if line.startswith("A"):
                if current_id in target_ids and buffer:
                    collected[current_id] = buffer[:max_terms]
                    if _have_all(collected, target_ids, max_terms):
                        break
                match = seq_line.match(line)
                current_id = match.group(1) if match else None
                buffer = []
                remainder = match.group(2) if match else ""
            elif current_id and line.startswith(","):
                remainder = line[1:]
            else:
                continue
            if current_id in target_ids:
                _append_terms(buffer, remainder, max_terms)
                if len(buffer) >= max_terms and _have_all(collected, target_ids, max_terms):
                    collected[current_id] = buffer[:max_terms]
                    break
    if current_id in target_ids and buffer:
        collected[current_id] = buffer[:max_terms]
    return collected


def _append_terms(buffer: List[int], chunk: str, max_terms: int) -> None:
    for token in chunk.split(','):
        value = token.strip()
        if not value:
            continue
        try:
            buffer.append(int(value))
        except ValueError:
            break
        if len(buffer) >= max_terms:
            break


def _have_all(collected: Dict[str, List[int]], target_ids: Set[str], max_terms: int) -> bool:
    if not target_ids:
        return False
    for seq_id in target_ids:
        if seq_id not in collected or len(collected[seq_id]) < max_terms:
            return False
    return True
