"""Regex-based formula type classification for OEIS and LODA formulas."""

import re
from typing import Set

from formula.types import FormulaType


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
