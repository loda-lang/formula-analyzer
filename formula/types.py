"""Shared types for the formula analyzer."""

from typing import Set
from dataclasses import dataclass
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
	LOOKUP_TABLE = "lookup_table"  # Trivial enumeration: a(n) = c0*(n==0) + c1*(n==1) + ...
	UNKNOWN = "unknown"


@dataclass
class ClassifiedFormula:
	"""Represents a single formula with classification metadata."""
	sequence_id: str
	text: str
	source: str  # "oeis" or "loda"
	types: Set[FormulaType]

	def __hash__(self):
		return hash((self.sequence_id, self.text, self.source))
