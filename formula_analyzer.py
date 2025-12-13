"""
Formula Analyzer for OEIS and LODA Formulas

This module analyzes and compares formulas from OEIS and LODA to identify
new and interesting LODA formulas that provide different formula types
than what's currently known in OEIS.
"""

import re
from typing import Dict, List, Set, Tuple, Optional
from dataclasses import dataclass
from collections import defaultdict
from enum import Enum


class FormulaType(Enum):
    """Categories of formula types."""
    EXPLICIT_CLOSED = "explicit_closed"  # Direct formula with no recursion
    COMPOSITE_EXPLICIT = "composite_explicit"  # Explicit but composed from other sequences / parity functions
    RECURRENCE = "recurrence"  # Recursive formula (a(n) = f(a(n-1), ...))
    GENERATING_FUNCTION = "generating_function"  # G.f., e.g.f.
    SUM = "sum"  # Summation formula
    PRODUCT = "product"  # Product formula
    LIMIT = "limit"  # Limit formula
    BINOMIAL = "binomial"  # Binomial coefficient formula
    FLOOR_CEILING = "floor_ceiling"  # Floor/ceiling expressions
    MODULAR = "modular"  # Modular arithmetic
    MATRIX = "matrix"  # Matrix formula
    CONGRUENCE = "congruence"  # Congruence relation
    INTEGRAL = "integral"  # Integral formula
    TRIGONOMETRIC = "trigonometric"  # Trig functions
    CONTINUED_FRACTION = "continued_fraction"  # Continued fraction
    SEQUENCE_REFERENCE = "sequence_reference"  # Uses other OEIS sequences in expression
    UNKNOWN = "unknown"


@dataclass
class Formula:
    """Represents a single formula with metadata."""
    sequence_id: str
    text: str
    source: str  # "oeis" or "loda"
    types: Set[FormulaType]
    
    def __hash__(self):
        return hash((self.sequence_id, self.text, self.source))


class FormulaClassifier:
    """Classifies formulas into different types."""
    
    # Pattern definitions for formula classification
    PATTERNS = {
        FormulaType.GENERATING_FUNCTION: [
            r'\bg\.f\.',
            r'\be\.g\.f\.',
            r'generating function',
            r'g\.f\.:',
            r'e\.g\.f\.:',
        ],
        FormulaType.RECURRENCE: [
            r'a\(n\)\s*=.*a\(n[-+]\d+\)',
            r'a\(n[-+]\d+\)',
            r'recurrence',
        ],
        FormulaType.SUM: [
            r'sum_\{',
            r'\\sum',
            r'sum\{',
            r'summation',
        ],
        FormulaType.PRODUCT: [
            r'product_\{',
            r'\\prod',
            r'product\{',
        ],
        FormulaType.LIMIT: [
            r'limit_\{',
            r'\\lim',
            r'limit\{',
        ],
        FormulaType.BINOMIAL: [
            r'binomial\(',
            r'\\binom',
            r'C\(n,k\)',
        ],
        FormulaType.FLOOR_CEILING: [
            r'floor\(',
            r'ceiling\(',
            r'\\lfloor',
            r'\\rfloor',
            r'\\lceil',
            r'\\rceil',
        ],
        FormulaType.MODULAR: [
            r'\bmod\b',
            r'\\equiv',
            r'modulo',
        ],
        FormulaType.CONGRUENCE: [
            r'==\s*\d+\s*\(mod',
            r'\\equiv.*\(mod',
        ],
        FormulaType.INTEGRAL: [
            r'integral_\{',
            r'\\int',
        ],
        FormulaType.TRIGONOMETRIC: [
            r'\bsin\(',
            r'\bcos\(',
            r'\btan\(',
            r'\bsec\(',
        ],
        FormulaType.CONTINUED_FRACTION: [
            r'continued fraction',
            r'Q\(k\)',
        ],
        FormulaType.MATRIX: [
            r'matrix',
            r'determinant',
            r'\bdet\b',
        ],
    }
    
    # LODA-specific patterns
    LODA_PATTERNS = {
        'has_recursion': r'a\(n[-+]\d+\)',
        'has_helper_sequences': r'\b[b-z]\(n',
        'has_floor': r'floor\(',
        'has_truncate': r'truncate\(',
        'has_sqrtint': r'sqrtint\(',
        'has_binomial': r'binomial\(',
        'has_modulo': r'%',
        'has_power': r'\^',
        'has_factorial': r'!',
        'has_gcd': r'gcd\(',
        'has_max_min': r'(max|min)\(',
        'has_logint': r'logint\(',
        'has_bitxor': r'bitxor\(',
        'has_sumdigits': r'sumdigits\(',
        'has_sequence_reference': r'A\d{6}'
    }
    
    def classify_oeis(self, formula_text: str) -> Set[FormulaType]:
        """Classify an OEIS formula into types."""
        types = set()
        text_lower = formula_text.lower()
        
        for formula_type, patterns in self.PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, text_lower, re.IGNORECASE):
                    types.add(formula_type)
                    break
        
        # Explicit/composite explicit detection (no self-recursion)
        if FormulaType.RECURRENCE not in types and re.search(r'a\(n\)\s*=', formula_text):
            has_seq_ref = bool(re.search(r'A\d{6}', formula_text))
            uses_parity = any(p in text_lower for p in ["hammingweight", "bit_count", "a010060", "a000120", "(-1)^", "mod 2", "% 2"])  # parity related
            simple_poly_or_exp = bool(re.search(r'a\(n\)\s*=\s*[-+*/() n0-9^ ]+$', formula_text)) or bool(re.search(r'2\*n', formula_text))
            if has_seq_ref or uses_parity:
                types.add(FormulaType.SEQUENCE_REFERENCE)
                types.add(FormulaType.COMPOSITE_EXPLICIT)
            else:
                types.add(FormulaType.EXPLICIT_CLOSED)
        
        return types if types else {FormulaType.UNKNOWN}
    
    def classify_loda(self, formula_text: str) -> Set[FormulaType]:
        """Classify a LODA formula into types."""
        types = set()
        
        # Check if it has recursion
        has_recursion = bool(re.search(self.LODA_PATTERNS['has_recursion'], formula_text))
        
        # Check for helper sequences (b(n), c(n), etc.)
        has_helpers = bool(re.search(self.LODA_PATTERNS['has_helper_sequences'], formula_text))

        # Check for sequence references to other OEIS sequences (Axxxxxx)
        has_seq_ref = bool(re.search(self.LODA_PATTERNS['has_sequence_reference'], formula_text))
        
        if has_recursion:
            types.add(FormulaType.RECURRENCE)
        
        # Sequence reference classification
        if has_seq_ref:
            types.add(FormulaType.SEQUENCE_REFERENCE)

        # Check for explicit formulas (pure closed form: no recursion, helpers, or external sequence references)
        if not has_recursion and not has_helpers:
            if has_seq_ref:
                types.add(FormulaType.COMPOSITE_EXPLICIT)
            else:
                types.add(FormulaType.EXPLICIT_CLOSED)
        
        # Check for specific operations
        if re.search(self.LODA_PATTERNS['has_binomial'], formula_text):
            types.add(FormulaType.BINOMIAL)
        
        if re.search(self.LODA_PATTERNS['has_floor'], formula_text) or \
           re.search(self.LODA_PATTERNS['has_truncate'], formula_text):
            types.add(FormulaType.FLOOR_CEILING)
        
        if re.search(self.LODA_PATTERNS['has_modulo'], formula_text):
            types.add(FormulaType.MODULAR)
        
        return types if types else {FormulaType.UNKNOWN}


class FormulaParser:
    """Parses formula files and extracts formulas."""
    
    def parse_oeis_file(self, filepath: str) -> Dict[str, List[Formula]]:
        """Parse OEIS formulas file with multi-line entries."""
        formulas = defaultdict(list)
        classifier = FormulaClassifier()
        
        current_seq_id = None
        current_lines = []
        
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            for line in f:
                # Check if this is a new sequence ID line
                match = re.match(r'(A\d{6}):\s*(.+)', line)
                if match:
                    # Process previous entry if exists
                    if current_seq_id and current_lines:
                        self._process_oeis_entry(current_seq_id, current_lines, formulas, classifier)
                    
                    # Start new entry
                    current_seq_id = match.group(1)
                    current_lines = [match.group(2)]
                elif line.startswith('  ') and current_seq_id:
                    # Continuation line (indented with 2 spaces)
                    current_lines.append(line[2:])  # Remove the 2-space indent
                elif not line.strip():
                    # Empty line - end of current entry
                    if current_seq_id and current_lines:
                        self._process_oeis_entry(current_seq_id, current_lines, formulas, classifier)
                        current_seq_id = None
                        current_lines = []
            
            # Process final entry if exists
            if current_seq_id and current_lines:
                self._process_oeis_entry(current_seq_id, current_lines, formulas, classifier)
        
        return formulas
    
    def _process_oeis_entry(self, seq_id: str, lines: List[str], formulas: Dict[str, List[Formula]], classifier):
        """Process a single OEIS entry with potentially multiple lines."""
        # Process each line individually so explicit formulas are not masked by recurrences.
        skip_markers = {'From _', '(End)', 'Comment from', 'Conjectures from',
                        '[Table from', '[table from', '----------'}

        for line in lines:
            line = line.strip()
            if not line:
                continue
            if any(marker in line for marker in skip_markers):
                continue

            types = classifier.classify_oeis(line)
            formula = Formula(
                sequence_id=seq_id,
                text=line,
                source='oeis',
                types=types
            )
            formulas[seq_id].append(formula)
    
    def parse_loda_file(self, filepath: str) -> Dict[str, Formula]:
        """Parse LODA formulas file (one formula per sequence)."""
        formulas = {}
        classifier = FormulaClassifier()
        
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                
                # Extract sequence ID and formula
                match = re.match(r'(A\d{6}):\s*(.+)', line)
                if match:
                    seq_id = match.group(1)
                    formula_text = match.group(2)
                    
                    types = classifier.classify_loda(formula_text)
                    formula = Formula(
                        sequence_id=seq_id,
                        text=formula_text,
                        source='loda',
                        types=types
                    )
                    formulas[seq_id] = formula
        
        return formulas
    
    def parse_names_file(self, filepath: str) -> Dict[str, str]:
        """Parse sequence names file."""
        names = {}
        
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                
                match = re.match(r'(A\d{6})\s+(.+)', line)
                if match:
                    seq_id = match.group(1)
                    name = match.group(2)
                    names[seq_id] = name
        
        return names


class FormulaComparator:
    """Compares LODA formulas against OEIS formulas to find interesting ones."""

    def __init__(self, oeis_formulas: Dict[str, List[Formula]],
                 loda_formulas: Dict[str, Formula],
                 names: Dict[str, str]):
        self.oeis_formulas = oeis_formulas
        self.loda_formulas = loda_formulas
        self.names = names
        # Precompiled patterns for name inference
        self.NAME_EXPLICIT_PATTERN = re.compile(r'\ba\(n\)\s*=')
        self.NAME_RECURRENCE_PATTERN = re.compile(r'\ba\(n[-+]\d+\)')
        self.NAME_SEQUENCE_REF_PATTERN = re.compile(r'A\d{6}')
        # Detect binomial coefficients in titles: "Binomial coefficient C(n,k)" or "binomial("
        self.NAME_BINOMIAL_PATTERN = re.compile(r'binomial\s+coefficient|binomial\(|\bC\(\d*n', re.IGNORECASE)
        # Rough detection of simple power formulas (e.g., a(n) = 2^n, a(n) = n^5)
        self.NAME_POW_PATTERN = re.compile(r'\ba\(n\)\s*=\s*[^=]*\b\d+\^n|\ba\(n\)\s*=\s*n\^\d+')
        # Detection of titles like "Powers of 14." implying a(n) = 14^n
        self.NAME_POWERS_OF_PATTERN = re.compile(r'\bPowers of\s+\d+', re.IGNORECASE)
        # Detect explicit polynomial formulas in names after colon (e.g., "Description: 7*n^2 + 4*n + 1.")
        # Matches patterns like: n^2, n*(n+1), 3*n^2, etc. after a colon
        self.NAME_POLYNOMIAL_PATTERN = re.compile(r':\s*[\d\w\s]*\*?\s*n[\^\*\(\)0-9+\-\s]*[+\-]', re.IGNORECASE)

    def _types_from_name(self, seq_id: str) -> Set[FormulaType]:
        """Infer formula types from the OEIS sequence name/title."""
        name = self.names.get(seq_id, '')
        types: Set[FormulaType] = set()
        if not name:
            return types
        if self.NAME_EXPLICIT_PATTERN.search(name):
            if not self.NAME_RECURRENCE_PATTERN.search(name):
                if self.NAME_SEQUENCE_REF_PATTERN.search(name):
                    types.add(FormulaType.SEQUENCE_REFERENCE)
                else:
                    types.add(FormulaType.EXPLICIT_CLOSED)
        if self.NAME_RECURRENCE_PATTERN.search(name):
            types.add(FormulaType.RECURRENCE)
        if self.NAME_SEQUENCE_REF_PATTERN.search(name):
            types.add(FormulaType.SEQUENCE_REFERENCE)
        if self.NAME_BINOMIAL_PATTERN.search(name):
            types.add(FormulaType.BINOMIAL)
            # Binomial formulas are explicit closed forms
            types.add(FormulaType.EXPLICIT_CLOSED)
        if self.NAME_POW_PATTERN.search(name) and FormulaType.EXPLICIT_CLOSED not in types and FormulaType.RECURRENCE not in types:
            types.add(FormulaType.EXPLICIT_CLOSED)
        if self.NAME_POWERS_OF_PATTERN.search(name) and FormulaType.EXPLICIT_CLOSED not in types and FormulaType.RECURRENCE not in types:
            types.add(FormulaType.EXPLICIT_CLOSED)
        # Detect polynomial formulas in names like "Description: 7*n^2 + 4*n + 1."
        if self.NAME_POLYNOMIAL_PATTERN.search(name) and FormulaType.EXPLICIT_CLOSED not in types and FormulaType.RECURRENCE not in types:
            types.add(FormulaType.EXPLICIT_CLOSED)
        return types

    def find_new_formulas(self) -> List[Tuple[Formula, Set[FormulaType], str]]:
        """Find LODA formulas that provide new formula types."""
        results: List[Tuple[Formula, Set[FormulaType], str]] = []
        for seq_id, loda_formula in self.loda_formulas.items():
            oeis_formulas = self.oeis_formulas.get(seq_id, [])
            name_types = self._types_from_name(seq_id)

            if not oeis_formulas:
                # Use name types if present
                if name_types:
                    new_types = loda_formula.types - name_types
                    # If LODA is just restating what the name says (esp. binomial), skip it
                    if loda_formula.types <= name_types:
                        # LODA provides no new information beyond the name
                        continue
                    # LODA extends name-derived types
                    results.append((loda_formula, new_types, "LODA extends name-derived types"))
                else:
                    results.append((loda_formula, loda_formula.types, "No formulas in OEIS for this sequence"))
                continue

            # Aggregate OEIS formula types
            oeis_types: Set[FormulaType] = set()
            for f in oeis_formulas:
                oeis_types.update(f.types)
            # Merge name-derived types
            oeis_types.update(name_types)

            new_types = loda_formula.types - oeis_types
            reason = self._determine_interest(seq_id, loda_formula.types, oeis_types, name_types)
            if reason:
                results.append((loda_formula, new_types, reason))
        # Post-process equivalences (e.g. parity-based explicit forms)
        return self.annotate_equivalences(results)

    def _has_rational_gf(self, seq_id: str) -> bool:
        """Heuristic: detect presence of a purely rational generating function in OEIS formulas."""
        for f in self.oeis_formulas.get(seq_id, []):
            if FormulaType.GENERATING_FUNCTION in f.types:
                text = f.text.lower()
                # Must contain a slash and only allowed characters after cleanup
                # Extract expression if phrase 'Expansion of' present
                if 'expansion of' in text:
                    # Capture after 'expansion of'
                    m = re.search(r'expansion of\s*([^.;]+)', text)
                    if m:
                        expr = m.group(1).strip()
                    else:
                        expr = text
                else:
                    expr = text

                # Quick rational structure check: presence of '/' and only x, digits, operators, parentheses
                if '/' in expr:
                    cleaned = re.sub(r'[^x0-9^()+\-*/]', '', expr)
                    # Remove trivial leading words
                    cleaned = cleaned.strip()
                    # Denominator pattern: (1 - x^k) or (1 - x) possibly repeated
                    denom_like = re.search(r'\(1-?x(\^\d+)?\)', cleaned)
                    repeated_factors = len(re.findall(r'\(1-?x(\^\d+)?\)', cleaned)) >= 2
                    # If expression reduces to allowed chars and has denominator-like factors, accept
                    if denom_like and ('/' in cleaned) and (repeated_factors or re.search(r'\(1-x\^?\d*\).*\(1-x', cleaned)):
                        return True
                    # Also allow pattern ((1+x^a)/((1-x)*(1-x^2)^2*(1-x^3))) style
                    if re.search(r'/\((1\-x)(?:\^\d+)?\)', expr) or re.search(r'/\(1\-x\)', expr):
                        return True
        return False

    def _determine_interest(self, seq_id: str,
                             loda_types: Set[FormulaType],
                             oeis_types: Set[FormulaType],
                             name_types: Set[FormulaType]) -> Optional[str]:
        """Determine if a LODA formula is interesting compared to OEIS."""
        name_has_explicit = FormulaType.EXPLICIT_CLOSED in name_types or FormulaType.COMPOSITE_EXPLICIT in name_types

        # Helper: treat any explicit form present in OEIS types as explicit coverage
        oeis_has_explicit = any(t in oeis_types for t in [FormulaType.EXPLICIT_CLOSED, FormulaType.COMPOSITE_EXPLICIT])
        has_rational_gf = self._has_rational_gf(seq_id)

        explicit_present = any(t in loda_types for t in [FormulaType.EXPLICIT_CLOSED, FormulaType.COMPOSITE_EXPLICIT])

        # Global rational generating function downgrade for any explicit formula lacking OEIS explicit coverage
        if explicit_present and has_rational_gf and not oeis_has_explicit:
            if name_has_explicit:
                return None
            return "LODA supplies explicit piecewise polynomial closed form derivable from rational generating function; moderate novelty"

        if (explicit_present and
            not oeis_has_explicit and FormulaType.RECURRENCE in oeis_types):
            if name_has_explicit:
                return None
            # If the name indicates it's a binomial coefficient and LODA just restates it, not interesting
            if FormulaType.BINOMIAL in name_types and FormulaType.BINOMIAL in loda_types:
                return None
            return "LODA provides explicit formula where OEIS only has recurrence"

        if FormulaType.BINOMIAL in loda_types and FormulaType.BINOMIAL not in oeis_types:
            # If the name already says it's a binomial coefficient, don't claim novelty
            if FormulaType.BINOMIAL in name_types:
                return None
            return "LODA provides binomial formula not in OEIS"

        if (explicit_present and
            not oeis_has_explicit and (FormulaType.SUM in oeis_types or FormulaType.PRODUCT in oeis_types or FormulaType.INTEGRAL in oeis_types)):
            if name_has_explicit:
                return "Name already closed form; LODA mirrors it"
            return "LODA provides closed form where OEIS has sum/product/integral"

        if FormulaType.SEQUENCE_REFERENCE in loda_types and FormulaType.SEQUENCE_REFERENCE not in oeis_types:
            return "LODA provides sequence-reference composition not in OEIS"

        new_types = loda_types - oeis_types
        if new_types and FormulaType.UNKNOWN not in new_types:
            # If name has explicit formula and LODA only adds floor/ceiling/modular as implementation details, not interesting
            if name_has_explicit and new_types <= {FormulaType.FLOOR_CEILING, FormulaType.MODULAR}:
                return None
            type_names = ', '.join(t.value for t in new_types)
            return f"LODA provides new formula types: {type_names}"
        return None

    def _is_equivalent(self, loda_formula: Formula, oeis_formulas: List[Formula]) -> bool:
        """Rudimentary equivalence: detect parity-based linear forms already present in OEIS."""
        text = loda_formula.text.replace(' ', '')
        # Canonical substitutions
        text = text.replace('gcd(sumdigits(n-1,2),2)','parity(n-1)')
        text = re.sub(r'sumdigits\(n-1,2\)%2','parity(n-1)', text)
        # Linear pattern with parity
        parity_pattern = re.compile(r'a\(n\)=2\*n[+\-]\d+parity\(n-1\)[\+\-]?\d*')
        loda_has_parity = 'parity(n-1)' in text or 'sumdigits(n-1,2)%2' in text
        if not loda_has_parity:
            return False
        for f in oeis_formulas:
            ft = f.text.replace(' ','')
            ft = ft.replace('hammingweight(n-1)%2','parity(n-1)')
            ft = ft.replace('A010060(n-1)','parity(n-1)')
            ft = ft.replace('A000120(n-1)%2','parity(n-1)')
            if 'parity(n-1)' in ft and ('2*n-1-parity(n-1)' in ft or '2*n-1-(' in ft):
                return True
        return False

    def annotate_equivalences(self, results: List[Tuple[Formula, Set[FormulaType], str]]) -> List[Tuple[Formula, Set[FormulaType], str]]:
        """Post-process results: adjust reason if formula equivalent to OEIS explicit."""
        adjusted = []
        for formula, new_types, reason in results:
            oeis_list = self.oeis_formulas.get(formula.sequence_id, [])
            if self._is_equivalent(formula, oeis_list) and 'explicit formula' in reason:
                reason = 'LODA formula equivalent to existing OEIS explicit parity formula'
            adjusted.append((formula, new_types, reason))
        return adjusted
    
    def get_sequence_name(self, seq_id: str) -> str:
        """Get the name of a sequence."""
        return self.names.get(seq_id, "Unknown sequence")
    
    def generate_report(self, results: List[Tuple[Formula, Set[FormulaType], str]], 
                       max_results: int = 100) -> str:
        """Generate a human-readable report of interesting formulas."""
        lines = []
        lines.append("=" * 80)
        lines.append("INTERESTING LODA FORMULAS")
        lines.append("=" * 80)
        lines.append("")
        lines.append(f"Found {len(results)} interesting formulas")
        lines.append("")
        
        for i, (formula, new_types, reason) in enumerate(results[:max_results], 1):
            seq_id = formula.sequence_id
            name = self.get_sequence_name(seq_id)
            
            lines.append(f"{i}. {seq_id}: {name}")
            lines.append(f"   Reason: {reason}")
            lines.append(f"   LODA Formula Types: {', '.join(t.value for t in formula.types)}")
            
            # Show OEIS formula types if they exist
            if seq_id in self.oeis_formulas:
                oeis_types = set()
                for of in self.oeis_formulas[seq_id]:
                    oeis_types.update(of.types)
                lines.append(f"   OEIS Formula Types: {', '.join(t.value for t in oeis_types)}")
            
            # Show the formula (truncated if too long)
            formula_text = formula.text
            if len(formula_text) > 200:
                formula_text = formula_text[:200] + "..."
            lines.append(f"   Formula: {formula_text}")
            lines.append("")
        
        if len(results) > max_results:
            lines.append(f"... and {len(results) - max_results} more")
        
        return "\n".join(lines)


def analyze_formulas(oeis_file: str, loda_file: str, names_file: str, 
                     output_file: Optional[str] = None):
    """
    Main analysis function.
    
    Args:
        oeis_file: Path to formulas-oeis.txt
        loda_file: Path to formulas-loda.txt
        names_file: Path to names.txt
        output_file: Optional output file for report
    """
    print("Parsing OEIS formulas...")
    parser = FormulaParser()
    oeis_formulas = parser.parse_oeis_file(oeis_file)
    print(f"  Found formulas for {len(oeis_formulas)} sequences")
    
    print("Parsing LODA formulas...")
    loda_formulas = parser.parse_loda_file(loda_file)
    print(f"  Found formulas for {len(loda_formulas)} sequences")
    
    print("Parsing sequence names...")
    names = parser.parse_names_file(names_file)
    print(f"  Found {len(names)} sequence names")
    
    print("\nComparing formulas...")
    comparator = FormulaComparator(oeis_formulas, loda_formulas, names)
    results = comparator.find_new_formulas()
    
    # Sort by interest (prioritize explicit formulas)
    def sort_key(item):
        formula, new_types, reason = item
        score = 0
        if "explicit formula where OEIS only has recurrence" in reason:
            score += 100
        if "closed form where OEIS has sum/product/integral" in reason:
            score += 50
        if FormulaType.EXPLICIT_CLOSED in formula.types:
            score += 10
        return -score  # Negative for descending order
    
    results.sort(key=sort_key)
    
    print(f"\nFound {len(results)} interesting formulas!")
    
    # Generate summary report for console
    summary_report = comparator.generate_report(results, max_results=50)
    print(summary_report)
    
    if output_file:
        # Write the full, untruncated report to disk
        full_report = comparator.generate_report(results, max_results=len(results))
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(full_report)
        print(f"\nFull report saved to {output_file}")
    
    return results, comparator


if __name__ == "__main__":
    import sys
    
    # Default file paths
    oeis_file = "formulas-oeis.txt"
    loda_file = "formulas-loda.txt"
    names_file = "names.txt"
    output_file = "interesting_formulas.txt"
    
    # Allow command line arguments
    if len(sys.argv) > 1:
        oeis_file = sys.argv[1]
    if len(sys.argv) > 2:
        loda_file = sys.argv[2]
    if len(sys.argv) > 3:
        names_file = sys.argv[3]
    if len(sys.argv) > 4:
        output_file = sys.argv[4]
    
    results, comparator = analyze_formulas(oeis_file, loda_file, names_file, output_file)
