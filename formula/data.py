import re
from typing import Dict, Iterator, List, Optional, Set

from formula.parser import ParsedFormula, FormulaParser

# Temporary deny lists for formulas that assume incorrect offsets or are misleading/non-explicit
DENYLIST_OEIS: set[str] = {
    "A103320",  # n - assumes offset 0 but actual offset is 12
    "A166931",  # 2519 + n*2520 - assumes offset 0 but actual offset is 1
    "A190414",  # 2*n - assumes offset 0 but actual offset is 1
    "A194769",  # n + 2037573096 - assumes offset 0 but actual offset is 1
    "A200437",  # (124952/567)*n^9 - ... - polynomial evaluation mismatch at offset 1
    "A213562",  # (4/15)*n^5 + (11/24)*n^4 + ... - assumes offset 0 but actual offset is 1
    "A213565",  # (16*n^5 + 85*n^4 + 15*n^3 - 25*n^2 - n)/60 - assumes offset 0 but actual offset is 1
    "A213826",  # -n - 3*n^2 + 6*n*3 - invalid formula structure or offset mismatch
    "A213846",  # n*(1 + n)*(1 - 2*n + 4*n^2)/6 - assumes offset 0 but actual offset is 1
    "A217883",  # (1/24)*n^4 + (1/4)*n^3 + ... - marked as "Diagonal" but formula assumes different indexing
    "A217954",  # (1/720)*n^6 + (1/48)*n^5 + ... - marked as "Diagonal" but formula assumes different indexing
    "A221533",  # 2*n^2 - 2*n - 3 - conditional formula ("If (2n-1, 2n+1) is pair of twin primes")
    "A238812",  # n + 1 - conditional formula (k=1 case, multiple branches)
    "A242709",  # n*(n^3 + n - 2)/8 - conditional formula (even n only)
    "A250884",  # (290548/3)*n^3 + 254464*n^2 + (669458/3)*n + 65536 - empirical formula
    "A277636",  # (3*n^2 - 3*n + 1)^3 - assumes offset 0 but actual offset is 0 (formula indexed differently)
    "A281907",  # 66483034025018711639862527490*n + 47867742232066880047611079 - assumes offset 0 but actual offset is 1
    "A297895",  # n + 4047 - assumes offset 0 but actual offset is 1 (domain restriction: for n >= 4496)
    "A299965",  # e.g.f. formula - not suitable for direct evaluation at integer n
    "A302758",  # n^2*(n - 1)*(n + 1)/24 - assumes offset 0 but actual offset is 1 (other formula is valid)
    "A303400",  # n + 10224 - assumes offset 0 but actual offset is 1
    "A343073",  # (n+1)/2 - assumes offset 0 but actual offset is 2
    "A349417",  # n^3/6 + n^2/2 - 2*n/3 + 2 - assumes offset 0 but actual offset is 3
    "A349919",  # multiple formulas; one valid, others are recurrence/sum formulas
    "A352758",  # 2*n - 1 - assumes offset 0 but actual offset is 1 (other formula is valid)
    "A355753",  # 3*(2*n - 1) - assumes offset 0 but actual offset is 1
    "A360416",  # formulas are recurrence relations or references to other sequences
    "A374622",  # n^2/2+2 - assumes offset 0 but actual offset is 3
    "A378922",  # 1 + 2*n*(n-1) + n^2*(n-1)*(2*n-1)/6 - assumes offset 0 but actual offset is 3
    "A379726",  # 2*(n/3)^2+n/3 - assumes offset 0 but actual offset is 2
    "A385730",  # (1/3)*(8 * n^3 + 7 * n + 3) - assumes offset 0 but actual offset is 1
}

DENYLIST_LODA: set[str] = {
    # LODA formulas with offset or validation issues
    "A092181",  # n*(n*(n*(3*n-16)+32)-28)+9 - formula is for offset 1 but OEIS offset is 0
    "A253942",  # 3*binomial(n+1,5) - LODA offset 4 produces 3,18,63... but OEIS offset 4 is 0,0,0,3,18,63... (shifted by 3)
    "A349417",  # -n+binomial(n-1,3)+5 - LODA offset 3 but OEIS offset is 0
    "A360416",  # n*(8*n-25)+20 - LODA offset 1 but OEIS offset is 0
    "A385730",  # floor(((n-1)*((n-1)*(8*n-8)+7))/3)+1 - LODA offset 1 but OEIS offset is 0
    "A390860",  # floor((7736*n+41527)/9072)-1 - LODA offset 0 but OEIS offset is 1
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

    # Detect formulas with explicit initial terms: a(0) = ..., a(1) = ..., etc.
    # These are not suitable for general formula validation.
    if re.search(r'\ba\(\d+\)\s*=', expr):
        return None

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
    if re.search(r'\bfor\s+n\s*(?:[<>]=?|!=)\s*-?\d+\s*[,;]?', prefix):
        return None
    
    # Check for conditional formulas with modular constraints (e.g., "for n mod 6 = 0")
    if re.search(r'\bfor\s+n\s+mod\s+', prefix):
        return None

    # Check for conditional linear congruence cases (e.g., "For n=4m then ...", "for n=4m+1")
    if re.search(r'\bfor\s+n\s*=\s*\d+\s*m(\s*\+\s*\d+)?\b', prefix):
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

    # Reject trailing domain restrictions after the formula (e.g., "a(n) = ... for n >= 2, a(1)=17")
    suffix = text[match.end():].lower()
    if re.search(r'\bfor\s+n\s*[<>!=]', suffix):
        return None
    if re.search(r'\bfor\s+n\s+mod\b', suffix):
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
