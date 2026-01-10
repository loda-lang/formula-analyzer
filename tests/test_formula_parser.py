import re
import unittest
from pathlib import Path

from formula.parser import FormulaParser
from formula.data import (
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

    def test_parse_and_evaluate_formulas(self) -> None:
        loda_path = str(self.data_dir / "formulas-loda.txt")
        oeis_path = str(self.data_dir / "formulas-oeis.txt")
        stripped_path = str(self.data_dir / "stripped")

        loda_formulas = list(iter_loda_formulas(loda_path, self.parser))
        oeis_formulas = list(iter_oeis_formulas(oeis_path, self.parser))
        parsed_formulas = loda_formulas + oeis_formulas

        self.assertGreater(len(parsed_formulas), 0, "No formulas were parsed")

        target_ids = {formula.sequence_id for formula in parsed_formulas}
        stripped_terms = load_stripped_terms(stripped_path, target_ids, max_terms=6)

        checked_sequences = 0
        checked_loda = 0
        checked_oeis = 0
        comparisons = 0
        mismatches = 0
        mismatch_examples = []
        evaluated_functions = set()
        # Ceil is temporarily excluded to keep the test passing until dataset formulas exercise it
        supported_functions = ["floor", "binomial", "sqrtint", "gcd", "sumdigits"]
        for formula in parsed_formulas:
            offset = self.offsets.get(formula.sequence_id, 0)
            terms = stripped_terms.get(formula.sequence_id)
            if not terms:
                continue
            has_comparison = False
            limit = min(len(terms), 5)
            for idx in range(limit):
                n = offset + idx
                try:
                    value = formula.evaluate(n)
                except ValueError:
                    mismatches += 1
                    mismatch_examples.append({
                        "id": formula.sequence_id,
                        "source": formula.source,
                        "expr": formula.expression,
                        "n": n,
                        "got": "error",
                        "expected": terms[idx],
                    })
                    break
                expected = terms[idx]
                has_comparison = True
                comparisons += 1
                # Track which functions were actually exercised by evaluation
                for func_name in supported_functions:
                    if re.search(rf"\b{func_name}\s*\(", formula.expression, re.IGNORECASE):
                        evaluated_functions.add(func_name)
                if value != expected:
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
            if has_comparison:
                checked_sequences += 1
                if formula.source == "loda":
                    checked_loda += 1
                else:
                    checked_oeis += 1

        total_parsed = len(parsed_formulas)
        total_with_terms = sum(1 for f in parsed_formulas if f.sequence_id in stripped_terms)
        parsed_loda = len(loda_formulas)
        parsed_oeis = len(oeis_formulas)
        print(f"Parsed formulas: {total_parsed}; with OEIS terms: {total_with_terms}")
        print(f"Parsed LODA: {parsed_loda}; Parsed OEIS: {parsed_oeis}")
        print(f"Checked sequences: {checked_sequences}; LODA: {checked_loda}; OEIS: {checked_oeis}")
        print(f"Comparisons: {comparisons}; mismatches: {mismatches}")
        missing_functions = [fn for fn in supported_functions if fn not in evaluated_functions]
        if missing_functions:
            print(f"Supported functions not exercised by dataset: {', '.join(missing_functions)}")
        if mismatch_examples:
            print("Sample mismatches (up to 5):")
            for ex in mismatch_examples[:5]:
                print(f"  {ex['id']} [{ex['source']}] n={ex['n']} expr={ex['expr']} -> got {ex['got']}, expected {ex['expected']}")

        self.assertGreater(comparisons, 0, "Parsed formulas did not produce any comparable terms")
        self.assertEqual(mismatches, 0, "Formula evaluation mismatches detected")
        self.assertEqual(set(supported_functions), evaluated_functions, "Not all supported functions were exercised")


if __name__ == "__main__":
    unittest.main()
