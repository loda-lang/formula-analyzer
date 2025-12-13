#!/usr/bin/env python3
"""
Script to run formula analysis and generate detailed reports.
"""

from formula_analyzer import analyze_formulas, FormulaType
import os


def main():
    """Run the formula analysis."""
    # Check if files exist
    base_dir = os.path.dirname(os.path.abspath(__file__))
    oeis_file = os.path.join(base_dir, "data/formulas-oeis.txt")
    loda_file = os.path.join(base_dir, "data/formulas-loda.txt")
    names_file = os.path.join(base_dir, "data/names")
    output_file = os.path.join(base_dir, "results/interesting_formulas.txt")
    
    for f in [oeis_file, loda_file, names_file]:
        if not os.path.exists(f):
            print(f"Error: File not found: {f}")
            return
    
    print("=" * 80)
    print("LODA Formula Analysis Tool")
    print("=" * 80)
    print()
    
    # Run analysis
    results, comparator = analyze_formulas(oeis_file, loda_file, names_file, output_file)
    
    # Generate statistics
    print("\n" + "=" * 80)
    print("STATISTICS")
    print("=" * 80)
    
    # Count by reason type
    reason_counts = {}
    for formula, new_types, reason in results:
        key = reason.split(':')[0] if ':' in reason else reason
        reason_counts[key] = reason_counts.get(key, 0) + 1
    
    print("\nBreakdown by reason:")
    for reason, count in sorted(reason_counts.items(), key=lambda x: -x[1]):
        print(f"  {count:4d}  {reason}")
    
    # Count by formula type
    type_counts = {}
    for formula, new_types, reason in results:
        for ftype in formula.types:
            type_counts[ftype.value] = type_counts.get(ftype.value, 0) + 1
    
    print("\nBreakdown by LODA formula type:")
    for ftype, count in sorted(type_counts.items(), key=lambda x: -x[1]):
        print(f"  {count:4d}  {ftype}")
    
    # Show top explicit formulas
    print("\n" + "=" * 80)
    print("TOP 10 EXPLICIT FORMULAS (most interesting)")
    print("=" * 80)
    
    explicit_formulas = [
        (f, nt, r) for f, nt, r in results 
        if FormulaType.EXPLICIT_CLOSED in f.types and
           "explicit formula where OEIS only has recurrence" in r
    ]
    
    for i, (formula, new_types, reason) in enumerate(explicit_formulas[:10], 1):
        seq_id = formula.sequence_id
        name = comparator.get_sequence_name(seq_id)
        print(f"\n{i}. {seq_id}: {name}")
        print(f"   {formula.text[:150]}")
    
    print("\n" + "=" * 80)
    print(f"Full report saved to: {output_file}")
    print("=" * 80)


if __name__ == "__main__":
    main()
