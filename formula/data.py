import re
from typing import Dict, Iterator, List, Optional, Set

from formula.parser import ParsedFormula, FormulaParser

# Temporary deny lists for formulas that assume incorrect offsets or are misleading/non-explicit
DENYLIST_OEIS: set[str] = {
    "A008922",  # Has 3928*n^3 instead of 392*n^3
    "A080770",
    "A092181",
    "A103320",
    "A133043",
    "A166931",
    "A190414",
    "A194769",
    "A200437",
    "A213562",
    "A213565",
    "A213826",
    "A213846",
    "A217883",
    "A217954",
    "A221533",
    "A238812",
    "A242709",
    "A250884",
    "A277636",
    "A281907",
    "A297895",
    "A299965",
    "A302758",
    "A303400",
    "A343073",
    "A349417",
    "A349919",
    "A352758",
    "A355753",
    "A360416",
    "A374622",
    "A378922",
    "A379726",
    "A385730",
}

DENYLIST_LODA: set[str] = {
    # LODA formulas that assume offset 0 but OEIS offset is nonzero
    "A044187",  # offset discrepancy: OEIS=1, LODA=0
    "A044242",  # offset discrepancy: OEIS=1, LODA=0
    "A065738",  # offset discrepancy: OEIS=1, LODA=0
    "A120054",  # offset discrepancy: OEIS=1, LODA=0
    "A156772",  # offset discrepancy: OEIS=1, LODA=0
    "A156865",  # offset discrepancy: OEIS=1, LODA=0
    "A156866",  # offset discrepancy: OEIS=1, LODA=0
    "A156867",  # offset discrepancy: OEIS=1, LODA=0
    "A156868",  # offset discrepancy: OEIS=1, LODA=0
    "A157105",  # offset discrepancy: OEIS=1, LODA=0
    "A157111",  # offset discrepancy: OEIS=1, LODA=0
    "A157666",  # offset discrepancy: OEIS=1, LODA=0
    "A157669",  # offset discrepancy: OEIS=1, LODA=0
    "A157769",  # offset discrepancy: OEIS=1, LODA=0
    "A157787",  # offset discrepancy: OEIS=1, LODA=0
    "A157797",  # offset discrepancy: OEIS=1, LODA=0
    "A157803",  # offset discrepancy: OEIS=1, LODA=0
    "A157821",  # offset discrepancy: OEIS=1, LODA=0
    "A157949",  # offset discrepancy: OEIS=1, LODA=0
    "A157951",  # offset discrepancy: OEIS=1, LODA=0
    "A158011",  # offset discrepancy: OEIS=1, LODA=0
    "A158231",  # offset discrepancy: OEIS=1, LODA=0
    "A158250",  # offset discrepancy: OEIS=1, LODA=0
    "A158395",  # offset discrepancy: OEIS=1, LODA=0
    "A158397",  # offset discrepancy: OEIS=1, LODA=0
    "A158421",  # offset discrepancy: OEIS=1, LODA=0
    "A186704",  # formula is outdated: floor((n-1)/2) should be truncate((n-11)/2)+5
    "A254029",  # offset discrepancy: OEIS=1, LODA=0
    "A276234",  # offset discrepancy: OEIS=1, LODA=0
    "A363417",  # wrong formula: produces binomial(-2n,2n) sequence instead of OEIS values
    "A378569",  # offset discrepancy: OEIS=0, LODA=1 (REVERSED)
    "A384288",  # systematic one-position shift: computed[n] = expected[n+1]
    "A385730",  # offset discrepancy: OEIS=1, LODA=0
    "A386858",  # offset discrepancy: OEIS=1, LODA=0
    "A389928",  # offset discrepancy: OEIS=1, LODA=0
}

LODA_LINE_RE = re.compile(r"^(A\d{6}):\s*a\(n\)\s*=\s*(.+)$", re.IGNORECASE)
OEIS_HEADER_RE = re.compile(r"^(A\d{6}):\s*(.+)$")
OEIS_FORMULA_RE = re.compile(r"a\(n\)\s*=", re.IGNORECASE)


def iter_loda_formulas(path: str, parser: FormulaParser) -> Iterator[ParsedFormula]:
    with open(path, "r", encoding="utf-8", errors="ignore") as handle:
        for raw_line in handle:
            parsed = _parse_loda_line(raw_line, parser)
            if not parsed:
                continue
            if parsed.sequence_id in DENYLIST_LODA:
                continue
            yield parsed


def iter_oeis_formulas(path: str, parser: FormulaParser) -> Iterator[ParsedFormula]:
    current_id: Optional[str] = None
    with open(path, "r", encoding="utf-8", errors="ignore") as handle:
        for raw_line in handle:
            line = raw_line.rstrip("\n")
            seq_match = OEIS_HEADER_RE.match(line)
            if seq_match:
                current_id = seq_match.group(1)
                if current_id in DENYLIST_OEIS:
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

    # Strip trailing metadata (initial conditions, extra recurrences) by cutting at
    # the first comma that appears at parentheses depth zero, but keep commas
    # inside function calls like binomial(..., ...).
    depth = 0
    cut_idx = None
    for idx, ch in enumerate(expr):
        if ch == "(":
            depth += 1
        elif ch == ")":
            depth = max(depth - 1, 0)
        elif ch == "," and depth == 0:
            cut_idx = idx
            break
    if cut_idx is not None:
        expr = expr[:cut_idx].strip()
    return parser.parse_expression(seq_id, "loda", expr)


def _parse_oeis_formula_text(seq_id: str, text: str, parser: FormulaParser) -> Optional[ParsedFormula]:
    match = OEIS_FORMULA_RE.search(text)
    if not match:
        return None
    
    # Check for domain restrictions before the formula (e.g., "for n>=43", "for n>0")
    prefix = text[:match.start()].lower()
    if re.search(r'\bfor\s+n\s*[<>!=]', prefix):
        return None
    
    # Check for conditional formulas with modular constraints (e.g., "for n mod 6 = 0")
    if re.search(r'\bfor\s+n\s+mod\s+', prefix):
        return None
    
    # Check for conditional natural-language prefixes (e.g., "for squarefree n, a(n) = ...")
    # This catches cases like A115077 where the formula is only valid on a subset of n.
    if re.search(r'\bfor\b[^,]{0,80}\bn\b[^,]{0,10},', prefix):
        return None

    # Check for conditional formulas with "if ... then" pattern (e.g., "If n+1 is prime then a(n) = ...")
    if re.search(r'\bif\b.*\bthen\b', prefix):
        return None
    
    # Check for diagonal/table formulas (e.g., "Diagonal: a(n) = ...", "Column k:")
    if re.search(r'\b(diagonal|column|row)\b', prefix):
        return None
    
    expr = text[match.end():].strip().rstrip(".;")
    # Restrict OEIS parsing to simple polynomials with basic operations to avoid misparsing
    if not re.fullmatch(r"[0-9nN\+\-\*\^\(\)/\s]+", expr):
        return None
    if "n" not in expr.lower():
        return None
    # Be conservative: drop very high degree forms (>=10) and trivial linear n-only cases to reduce misparsed OEIS formulas.
    if re.search(r"\^([1-9]\d+)", expr):
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
