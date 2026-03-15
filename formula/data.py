import re
from typing import Dict, Iterator, List, Optional, Set

from formula.formula import Formula
from formula.parser import FormulaParser, ALL_FUNCTIONS

# Functions allowed in OEIS formulas (subset of ALL_FUNCTIONS)
OEIS_ALLOWED_FUNCTIONS = frozenset({"binomial", "gcd"})

# Temporary deny lists for formulas that assume incorrect offsets or are misleading/non-explicit
DENYLIST_OEIS: set[str] = {
    # OEIS formulas with incorrect constant terms
    "A244501",   # formula has wrong constant term: 6 should be 63; all values off by -57; documented in pending_oeis_submissions.md
    # Parity-specific formulas missing parity restrictions
    "A299256",   # two formulas missing parity restrictions: (9*n^2-1)/2 for odd n, 9*n^2/2 for even n; documented in pending_oeis_submissions.md
    # Binomial formulas with fractional arguments and large gamma values — float precision issue
    "A364517",   # binomial(9*n/2, 2*n) loses precision at n>=3 due to large gamma values
    # Binomial formulas missing domain restrictions
    "A113127",   # binomial sum formula needs domain restriction for n>=2; produces wrong values at n=0,1; documented in pending_oeis_submissions.md
    # OEIS entries with both correct and incorrect formulas (awaiting incorrect formula deletion)
    "A056118",   # Greubel formula 11*C(n+5,5)-8*C(n+4,4) has wrong coefficient: -8 should be -10; entry has correct formula too; awaiting incorrect formula deletion
}

DENYLIST_LODA: set[str] = set()  # Currently empty - all issues resolved or formulas rejected by parser

LODA_LINE_RE = re.compile(r"^(A\d{6}):\s*a\(n\)\s*=\s*(.+)$", re.IGNORECASE)
OEIS_HEADER_RE = re.compile(r"^(A\d{6}):\s*(.+)$")
OEIS_FORMULA_RE = re.compile(r"a\(n\)\s*=", re.IGNORECASE)


def iter_loda_formulas(path: str, parser: FormulaParser) -> Iterator[Formula]:
    with open(path, "r", encoding="utf-8", errors="ignore") as handle:
        for raw_line in handle:
            parsed = _parse_loda_line(raw_line, parser)
            if not parsed:
                continue
            if parsed.sequence_id in DENYLIST_LODA:
                continue
            yield parsed


def iter_oeis_formulas(path: str, parser: FormulaParser) -> Iterator[Formula]:
    current_id: Optional[str] = None
    skip_next_formula = False
    with open(path, "r", encoding="utf-8", errors="ignore") as handle:
        for raw_line in handle:
            line = raw_line.rstrip("\n")
            seq_match = OEIS_HEADER_RE.match(line)
            if seq_match:
                current_id = seq_match.group(1)
                skip_next_formula = False
                if current_id in DENYLIST_OEIS:
                    current_id = None
                    continue
                remainder = seq_match.group(2)
                parsed = _parse_oeis_formula_text(current_id, remainder.strip(), parser)
                if parsed:
                    yield parsed
                # Check if line ends with "otherwise:" to skip next formula
                if remainder.rstrip().endswith("otherwise:"):
                    skip_next_formula = True
                continue
            if current_id and line.startswith("  "):
                cont = line.strip()
                if cont.lower().startswith("a(n) ="):
                    if skip_next_formula:
                        skip_next_formula = False
                        continue
                    parsed = _parse_oeis_formula_text(current_id, cont, parser)
                    if parsed:
                        yield parsed
                    # Check if line ends with "otherwise:" to skip next formula
                    if cont.rstrip().endswith("otherwise:"):
                        skip_next_formula = True


def _parse_loda_line(line: str, parser: FormulaParser) -> Optional[Formula]:
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


def _extract_lower_bound(op: str, value: int) -> int:
    """Convert a domain restriction operator and value to an inclusive lower bound."""
    if op == ">":
        return value + 1
    # >=
    return value


def _parse_oeis_formula_text(seq_id: str, text: str, parser: FormulaParser) -> Optional[Formula]:
    match = OEIS_FORMULA_RE.search(text)
    if not match:
        return None
    
    # Reject relational formulas where a(n) appears with another sequence reference
    # (e.g., "A352757(n) - a(n) = 2*n - 1" or "A000045(n) + a(n) = 3*n")
    if re.search(r'A\d{6}\([^)]+\)\s*[-+*/^]\s*a\(n\)', text, re.IGNORECASE):
        return None
    
    # Reject relational formulas with multiplied a(n) (e.g., "3*a(n) = ...")
    prefix_before_an = text[:match.start()]
    if re.search(r'\d+\s*\*\s*$', prefix_before_an):
        return None
    
    prefix = text[:match.start()].lower()
    lower_bound: Optional[int] = None

    # Extract domain lower bound from prefix (e.g., "for n>=5, a(n) = ..." or "for n>0:")
    prefix_bound = re.search(r'\bfor\s+(?:all\s+)?n\s*(>=?)\s*(\d+)\s*[,;:]?\s*$', prefix)
    if prefix_bound:
        lower_bound = _extract_lower_bound(prefix_bound.group(1), int(prefix_bound.group(2)))
    else:
        # Reject other prefix domain patterns we can't handle
        if re.search(r'\bfor\s+(?:all\s+)?n\s*(?:[<]=?|!=)\s*-?\d+\s*[,;]?', prefix):
            return None
    
    # Check for conditional formulas with modular constraints (e.g., "for n mod 6 = 0")
    if re.search(r'\bfor\s+n\s+mod\s+', prefix):
        return None

    # Check for table column-specific formulas (e.g., "k=1:")
    if re.search(r'\bk\s*=\s*\d+\s*:', prefix):
        return None

    # Check for conditional linear congruence cases (e.g., "For n=4m then ...", "for n=4m+1")
    if re.search(r'\bfor\s+n\s*=\s*\d+\s*m(\s*\+\s*\d+)?\b', prefix):
        return None
    
    # Check for conditional natural-language prefixes (e.g., "for squarefree n, a(n) = ...")
    # This catches cases like A115077 where the formula is only valid on a subset of n.
    if not prefix_bound and re.search(r'\bfor\b[^,]{0,80}\bn\b[^,]{0,10},', prefix):
        return None

    # Reject any formula with "if" in prefix (conditional/piecewise formulas)
    if re.search(r'\bif\b', prefix):
        return None
    
    # Check for diagonal/table formulas (e.g., "Diagonal: a(n) = ...", "Column k:")
    if re.search(r'\b(diagonal|column|row)\b', prefix):
        return None

    # Reject formulas where a(n) is part of a larger expression
    # (e.g., "Sum_{k=0..n} a(n) = ..." or "Product_{k=1..n} a(n) = ...")
    if re.search(r'\}\s*$', prefix):
        return None

    # Extract or reject trailing domain restrictions after the formula
    suffix = text[match.end():].lower()

    # Check for modular or parity conditions (always reject)
    if re.search(r'\bfor\s+n\s+mod\b', suffix):
        return None
    if re.search(r'\bfor\s+n\s+(even|odd)\b', suffix):
        return None

    # Try to extract suffix lower bound (e.g., "... for n >= 2" or "... for n > 0")
    suffix_bound = re.search(r'\bfor\s+n\s*(>=?)\s*(\d+)\s*(.*)', suffix)
    if suffix_bound:
        after_bound = suffix_bound.group(3).strip().rstrip(".;,").strip()
        # Reject compound conditions: "for n > 0 and even", "for n >= 1 and odd",
        # "for n > 0 and n even", "for n > 3 and n odd"
        if re.match(r'\band\s+(?:n\s+)?(even|odd)\b', after_bound):
            return None
        # Reject table/column indicators after domain (e.g., "for n > 0, k=3:")
        if re.search(r'\bk\s*=\s*\d+', after_bound):
            return None
        # Reject "n=K:" table row indicators
        if re.search(r'\bn\s*=\s*\d+\s*:', after_bound):
            return None
        bound = _extract_lower_bound(suffix_bound.group(1), int(suffix_bound.group(2)))
        if lower_bound is None:
            lower_bound = bound
        else:
            lower_bound = max(lower_bound, bound)
    elif re.search(r'\bfor\s+n\s*[<!=]', suffix):
        # Reject upper bounds or != constraints we can't handle
        return None
    
    expr = text[match.end():].strip().rstrip(".;")

    # Strip trailing domain restriction from expression (e.g., "n^2 + 1 for n >= 2")
    expr = re.sub(r'\s+for\s+n\s*>=?\s*\d+.*$', '', expr, flags=re.IGNORECASE).strip().rstrip(".;")

    # Detect recursive formulas: expressions containing a(n-k) or a(n+k) references
    is_recursive = bool(re.search(r'\ba\s*\(', expr, re.IGNORECASE))

    if is_recursive:
        # Strip trailing initial conditions and extract the highest initial index
        # to set a lower_bound for non-recursive formulas.
        #   "2*a(n-1)+1, a(0)=1, a(1)=2"  -> "2*a(n-1)+1"
        #   "expr, a(0) = 1"               -> "expr" with lower_bound >= 1
        #   "expr with a(1) = 9"           -> "expr" with lower_bound >= 2
        max_init_idx = -1
        for init_match in re.finditer(r'\ba\((\d+)\)\s*=\s*\d+', expr, re.IGNORECASE):
            max_init_idx = max(max_init_idx, int(init_match.group(1)))
        expr = re.sub(r'\s*[;,]\s*a\(\d+\)\s*=.*$', '', expr, flags=re.IGNORECASE).strip().rstrip(".;")
        expr = re.sub(r'\s+with\s+a\(\d+\)\s*=.*$', '', expr, flags=re.IGNORECASE).strip().rstrip(".;")
        # Strip trailing attribution (e.g., " - _Author_, Date")
        expr = re.sub(r'\s+-\s+_.*$', '', expr).strip().rstrip(".;")
        # Check remaining expression for a(n-k) references (true recurrence)
        has_recur_refs = bool(re.search(r'\ba\s*\([^)]*n[^)]*\)', expr, re.IGNORECASE))
        if not has_recur_refs:
            # Non-recursive formula with initial condition overrides (e.g., "expr, a(0) = 1")
            # Set lower_bound to exclude the overridden indices
            if max_init_idx >= 0:
                init_lower = max_init_idx + 1
                lower_bound = max(lower_bound, init_lower) if lower_bound is not None else init_lower
        else:
            # Reject non-simple recursive references: only allow a(n-k) and a(n+k) where k is a constant
            # This rejects a(n/2), a(2*n), a(a(n)), etc.
            for ref_match in re.finditer(r'\ba\s*\(([^)]+)\)', expr, re.IGNORECASE):
                arg = ref_match.group(1).strip()
                if not re.fullmatch(r'n\s*[-+]\s*\d+', arg, re.IGNORECASE):
                    return None
            # Reject recurrences involving other sequences (e.g., "a(n) = A089806(n)*... + a(n-1)")
            if re.search(r'A\d{6}\s*\(', expr):
                return None

    # Restrict OEIS parsing to basic operations and whitelisted functions
    if not re.fullmatch(r"[0-9nN\+\-\*\^\(\)/,\sa-zA-Z]+", expr):
        return None
    if "n" not in expr.lower():
        return None
    # Be conservative: drop very high degree forms (>=10) and trivial linear n-only cases to reduce misparsed OEIS formulas.
    if re.search(r"\^([1-9]\d+)", expr):
        return None
    if not any(op in expr for op in ["+", "*", "^"]):
        return None
    return parser.parse_expression(seq_id, "oeis", expr, lower_bound=lower_bound,
                                   allowed_functions=OEIS_ALLOWED_FUNCTIONS)


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
