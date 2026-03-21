"""Extract formula-like expressions from OEIS program blocks (PARI, Maple, Mathematica, Magma, Python)."""

import re
from typing import Dict, List, Tuple, Optional
from collections import defaultdict

from formula.types import FormulaType, ClassifiedFormula
from formula.classifier import FormulaClassifier


class ProgramExtractor:
	"""Extracts formula-like expressions from OEIS program listings."""

	# Patterns for extracting formulas from OEIS program blocks.
	_PARI_FORMULA_RE = re.compile(
		r'^\s*(?:a\(n\)|[a-z]\(n\))\s*=\s*(.+)',
		re.IGNORECASE,
	)
	_MATHEMATICA_FORMULA_RE = re.compile(
		r'^\s*(?:a\[n_?\]|Table\[)\s*:?=\s*(.+)',
		re.IGNORECASE,
	)

	def parse_oeis_programs_file(self, filepath: str) -> Dict[str, List[ClassifiedFormula]]:
		"""Parse OEIS programs file and extract formula-like expressions.

		The file uses the same multi-line format as the formulas file:
		header ``Axxxxxx: (LANG) code``, continuation with 2-space indent.

		Only lines that look like formulas are kept (e.g. PARI ``a(n)=expr``,
		Maple direct expressions, Mathematica ``a[n_]`` definitions).
		"""
		formulas: Dict[str, List[ClassifiedFormula]] = defaultdict(list)
		classifier = FormulaClassifier()

		current_seq_id: Optional[str] = None
		current_lines: List[str] = []

		def _flush() -> None:
			if current_seq_id and current_lines:
				self._process_program_entry(current_seq_id, current_lines, formulas, classifier)

		with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
			for line in f:
				match = re.match(r'(A\d{6}):\s*(.+)', line)
				if match:
					_flush()
					current_seq_id = match.group(1)
					current_lines = [match.group(2)]
				elif line.startswith('  ') and current_seq_id:
					current_lines.append(line[2:])
				elif not line.strip():
					_flush()
					current_seq_id = None
					current_lines = []
			_flush()

		return formulas

	def _process_program_entry(self, seq_id: str, lines: List[str],
							   formulas: Dict[str, List[ClassifiedFormula]],
							   classifier: FormulaClassifier) -> None:
		"""Extract formula-like expressions from a program block.

		A single entry may contain multiple language blocks.  Each block
		starts with a ``(LANG)`` tag, either on the header line or on a
		continuation line.
		"""
		if not lines:
			return

		# Split lines into per-language blocks.
		blocks: List[Tuple[str, List[str]]] = []  # (lang, lines)
		current_lang = ''
		current_block: List[str] = []

		for line in lines:
			m = re.match(r'\((\w+)\)\s*(.*)', line)
			if m:
				# Start of a new language block
				if current_block or current_lang:
					blocks.append((current_lang, current_block))
				current_lang = m.group(1).lower()
				rest = m.group(2).strip()
				current_block = [rest] if rest else []
			else:
				current_block.append(line)

		if current_block or current_lang:
			blocks.append((current_lang, current_block))

		for lang, block_lines in blocks:
			extracted: List[str] = []

			if lang == 'pari':
				extracted = self._extract_pari_formulas(block_lines)
			elif lang == 'maple':
				extracted = self._extract_maple_formulas(block_lines)
			elif lang in ('mathematica', 'mma'):
				extracted = self._extract_mathematica_formulas(block_lines)
			elif lang == 'magma':
				extracted = self._extract_magma_formulas(block_lines)
			elif lang == 'python':
				extracted = self._extract_python_formulas(block_lines)
			else:
				# Generic: look for a(n)=... patterns
				for bline in block_lines:
					m = self._PARI_FORMULA_RE.match(bline.strip())
					if m:
						extracted.append('a(n) = ' + m.group(1).rstrip(';').strip())

			for expr in extracted:
				types = classifier.classify_oeis(expr)
				formula = ClassifiedFormula(
					sequence_id=seq_id,
					text=expr,
					source='oeis_prog',
					types=types,
				)
				formulas[seq_id].append(formula)

	def _extract_pari_formulas(self, lines: List[str]) -> List[str]:
		"""Extract formula-like expressions from PARI programs."""
		results: List[str] = []
		for line in lines:
			# Strip trailing comments: \\ ... or // ...
			line = re.sub(r'\s*\\\\.*$', '', line)
			line = re.sub(r'\s*//.*$', '', line)
			line = line.strip().rstrip(';').strip()
			if not line or line.startswith('\\\\') or line.startswith('/*'):
				continue
			m = self._PARI_FORMULA_RE.match(line)
			if m:
				expr = m.group(1).rstrip(';').strip()
				# Skip if it contains control flow (multi-statement programs)
				if any(kw in expr for kw in ['if(', 'while(', 'for(', 'forstep(', 'my(', 'local(']):
					continue
				results.append('a(n) = ' + expr)
		return results

	def _extract_maple_formulas(self, lines: List[str]) -> List[str]:
		"""Extract formula-like expressions from Maple programs."""
		results: List[str] = []
		for line in lines:
			line = line.strip().rstrip(';').rstrip(':').strip()
			if not line:
				continue
			# Maple: a := n -> expr  or  a(n) := expr
			m = re.match(r'^\s*\w+\s*:=\s*(?:n\s*->|proc\(n\))\s*(.+)', line)
			if m:
				expr = m.group(1).strip()
				if 'proc' in expr or 'do' in expr or 'if' in expr:
					continue
				expr = expr.rstrip('end').strip()
				results.append('a(n) = ' + expr)
				continue
			# Direct formula: a(n) = expr
			m = self._PARI_FORMULA_RE.match(line)
			if m:
				expr = m.group(1).strip()
				if 'if' not in expr and 'do' not in expr:
					results.append('a(n) = ' + expr)
				continue
			# Bare polynomial expression (e.g. 57/7*n^8+36*n^7+...)
			if re.match(r'^[\d\s\+\-\*/\^n\(\)\.]+$', line) and 'n' in line:
				results.append('a(n) = ' + line)
		return results

	def _extract_mathematica_formulas(self, lines: List[str]) -> List[str]:
		"""Extract formula-like expressions from Mathematica programs."""
		results: List[str] = []
		for line in lines:
			line = line.strip().rstrip(';').strip()
			if not line:
				continue
			m = re.match(r'^\s*a\[n_?\]\s*:?=\s*(.+)', line)
			if m:
				expr = m.group(1).strip()
				if any(kw in expr for kw in ['If[', 'Which[', 'Do[', 'Module[']):
					continue
				results.append('a(n) = ' + expr)
		return results

	def _extract_magma_formulas(self, lines: List[str]) -> List[str]:
		"""Extract formula-like expressions from Magma programs."""
		results: List[str] = []
		for line in lines:
			# Strip trailing comments
			line = re.sub(r'\s*//.*$', '', line)
			line = line.strip().rstrip(';').strip()
			if not line:
				continue
			# Pattern: [expr : n in [0..N]]
			m = re.match(r'^\s*\[(.+?)\s*:\s*n\s+in\s+\[', line)
			if m:
				expr = m.group(1).strip()
				if 'if' not in expr.lower() and 'for' not in expr.lower():
					results.append('a(n) = ' + expr)
				continue
			# Pattern: func<n | expr>
			m = re.match(r'^\s*func<\s*n\s*\|\s*(.+?)>', line)
			if m:
				expr = m.group(1).strip()
				results.append('a(n) = ' + expr)
				continue
			m = self._PARI_FORMULA_RE.match(line)
			if m:
				expr = m.group(1).strip()
				if 'if' not in expr.lower() and 'for' not in expr.lower():
					results.append('a(n) = ' + expr)
		return results

	def _extract_python_formulas(self, lines: List[str]) -> List[str]:
		"""Extract formula-like expressions from Python programs."""
		results: List[str] = []
		for line in lines:
			line = line.strip()
			if not line:
				continue
			# lambda n: expr
			m = re.match(r'.*lambda\s+n\s*:\s*(.+)', line)
			if m:
				expr = m.group(1).strip()
				if 'if' not in expr and 'for' not in expr:
					results.append('a(n) = ' + expr)
				continue
			# def a(n): return expr
			m = re.match(r'^\s*def\s+\w+\(n\):\s*return\s+(.+)', line)
			if m:
				expr = m.group(1).strip()
				if 'if' not in expr and 'for' not in expr:
					results.append('a(n) = ' + expr)
		return results
