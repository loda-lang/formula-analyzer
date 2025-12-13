import unittest
from pathlib import Path

from formula_parser import FormulaParser
from data_parsers import (
    iter_loda_formulas,
    iter_oeis_formulas,
    load_offsets,
    load_stripped_terms,
)


class TestFormulaParser(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.base_dir = Path(__file__).resolve().parent.parent
        cls.data_dir = cls.base_dir / "data"
        cls.parser = FormulaParser()
        cls.offsets = load_offsets(str(cls.data_dir / "offsets"))

    def test_parse_and_evaluate_simple_polynomials(self) -> None:
        loda_path = str(self.data_dir / "formulas-loda.txt")
        oeis_path = str(self.data_dir / "formulas-oeis.txt")
        stripped_path = str(self.data_dir / "stripped")

        loda_formulas = list(iter_loda_formulas(loda_path, self.parser))
        oeis_formulas = list(iter_oeis_formulas(oeis_path, self.parser))
        parsed_formulas = loda_formulas + oeis_formulas

        self.assertGreater(len(parsed_formulas), 0, "No formulas were parsed")

        target_ids = {formula.sequence_id for formula in parsed_formulas}
        stripped_terms = load_stripped_terms(stripped_path, target_ids, max_terms=6)

        checked = 0
        mismatches = 0
        mismatch_examples = []
        for formula in parsed_formulas:
            offset = self.offsets.get(formula.sequence_id, 0)
            terms = stripped_terms.get(formula.sequence_id)
            if not terms:
                continue
            limit = min(len(terms), 5)
            for idx in range(limit):
                n = offset + idx
                value = formula.evaluate(n)
                expected = terms[idx]
                if value != expected:
                    if formula.source == "loda":
                        shifted = formula.evaluate(n - 1)
                        if shifted == expected:
                            checked += 1
                            continue
                    mismatches += 1
                    mismatch_examples.append({
                        "id": formula.sequence_id,
                        "source": formula.source,
                        "expr": formula.expression,
                        "n": n,
                        "got": value,
                        "expected": expected,
                    })
                    break
                checked += 1

        total_parsed = len(parsed_formulas)
        total_with_terms = sum(1 for f in parsed_formulas if f.sequence_id in stripped_terms)
        print(f"Parsed formulas: {total_parsed}; with OEIS terms: {total_with_terms}")
        print(f"Comparisons: {checked}; mismatches: {mismatches}")
        if mismatch_examples:
            print("Sample mismatches (up to 5):")
            for ex in mismatch_examples[:5]:
                print(f"  {ex['id']} [{ex['source']}] n={ex['n']} expr={ex['expr']} -> got {ex['got']}, expected {ex['expected']}")

        self.assertGreater(checked, 0, "Parsed formulas did not produce any comparable terms")
        self.assertLess(mismatches, checked, "Too many mismatches for simple parser prototype")


if __name__ == "__main__":
    unittest.main()
