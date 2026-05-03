"""Tests for piecewise-by-residue closed-form detection in the FormulaComparator."""

import unittest

from formula.analyzer import FormulaComparator
from formula.types import ClassifiedFormula, FormulaType


def _oeis(seq_id, *texts):
    return [
        ClassifiedFormula(sequence_id=seq_id, source='oeis', text=t,
                          types={FormulaType.UNKNOWN})
        for t in texts
    ]


def _cmp(oeis_formulas):
    return FormulaComparator(oeis_formulas, {}, {}, {})


class PiecewiseExplicitTests(unittest.TestCase):

    def test_a194770_single_line_three_residues(self):
        # All three residues mod 3 covered on a single line.
        formulas = {'A194770': _oeis('A194770',
            'a(3*n+1) = (3*n)!, a(3*n+2) = -(3*n+1)!, a(3*n) = 0')}
        self.assertEqual(
            _cmp(formulas)._piecewise_explicit_types('A194770'),
            {FormulaType.EXPLICIT_CLOSED},
        )

    def test_a152668_two_lines_both_residues(self):
        # Both residues mod 2 covered across two separate %F lines.
        formulas = {'A152668': _oeis('A152668',
            'a(2n) = (n+1)(2n)!/2',
            'a(2n+1) = n(n+2)(2n)!')}
        self.assertEqual(
            _cmp(formulas)._piecewise_explicit_types('A152668'),
            {FormulaType.EXPLICIT_CLOSED},
        )

    def test_partial_coverage_does_not_qualify(self):
        # Only one residue mod 2 covered.
        formulas = {'A_partial': _oeis('A_partial', 'a(2n) = n^2')}
        self.assertEqual(_cmp(formulas)._piecewise_explicit_types('A_partial'), set())

    def test_recursive_rhs_with_a_n_disqualifies(self):
        # `a(n)` on the RHS is a recurrence, not a closed form.
        formulas = {'A_recur': _oeis('A_recur',
            'a(2n) = a(n) + 1, a(2n+1) = 2*a(n)')}
        self.assertEqual(_cmp(formulas)._piecewise_explicit_types('A_recur'), set())

    def test_recursive_rhs_with_offset_disqualifies(self):
        # `a(n-1)`, `a(n+2)` are also recurrences.
        formulas = {'A_recur2': _oeis('A_recur2',
            'a(2n) = a(n-1), a(2n+1) = a(n+2)')}
        self.assertEqual(_cmp(formulas)._piecewise_explicit_types('A_recur2'), set())

    def test_sequence_reference_yields_composite_explicit(self):
        # If any covered RHS references another OEIS sequence, classify as composite.
        formulas = {'A_seqref': _oeis('A_seqref',
            'a(2n) = A123456(n), a(2n+1) = n+1')}
        self.assertEqual(
            _cmp(formulas)._piecewise_explicit_types('A_seqref'),
            {FormulaType.COMPOSITE_EXPLICIT},
        )

    def test_no_piecewise_lhs_returns_empty(self):
        # Plain a(n) = ... should not trigger the piecewise detector.
        formulas = {'A_plain': _oeis('A_plain', 'a(n) = n^2 + 1')}
        self.assertEqual(_cmp(formulas)._piecewise_explicit_types('A_plain'), set())

    def test_unknown_sequence_returns_empty(self):
        self.assertEqual(_cmp({})._piecewise_explicit_types('A000001'), set())


if __name__ == '__main__':
    unittest.main()
