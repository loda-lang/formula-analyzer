#!/usr/bin/env python3
"""
Script to run formula analysis and generate detailed reports.
"""

from formula.analyzer import analyze_formulas, FormulaType
from formula.annotate import generate_parsed_loda_file, generate_parsed_oeis_file
from formula.data_fetcher import prepare_data, DataPaths
import argparse
import os
from pathlib import Path


def main():
    """Run the formula analysis."""

    parser = argparse.ArgumentParser(description="Run formula analysis")
    parser.add_argument(
        "--refresh-data",
        action="store_true",
        help="regenerate all data files; when absent only missing files are generated",
    )
    parser.add_argument("--data-dir", default="data", help="data directory (default: data)")
    parser.add_argument("--loda-home", default=None, help="override $HOME/loda for sourcing OEIS exports")
    args = parser.parse_args()

    base_dir = Path(__file__).resolve().parent
    data_dir = base_dir / args.data_dir
    paths = DataPaths(data_dir)

    report = prepare_data(
        data_dir=data_dir,
        loda_home=Path(args.loda_home) if args.loda_home else None,
        force=args.refresh_data,
        run_if_missing=True,
    )
    if report.created:
        print("Prepared data files:")
        for path in report.created:
            print(f"  - {path}")
    if report.commands:
        print("Commands run:")
        for cmd in report.commands:
            print(f"  $ {' '.join(cmd)}")

    oeis_file = str(paths.formulas_oeis)
    loda_file = str(paths.formulas_loda)
    names_file = str(paths.names)
    output_file = str(base_dir / "results/interesting_formulas.txt")
    parsed_loda_file = str(base_dir / "results/parsed-formulas-loda.txt")
    parsed_oeis_file = str(base_dir / "results/parsed-formulas-oeis.txt")

    missing = [p for p in [oeis_file, loda_file, names_file] if not os.path.exists(p)]
    if missing:
        print("Error: Missing required data files:")
        for path in missing:
            print(f"  - {path}")
        print("Hint: run with --prepare-data to fetch/generate them.")
        return
    
    print("=" * 80)
    print("LODA Formula Analysis Tool")
    print("=" * 80)
    print()
    
    # Generate parsed formula files with check marks
    print("Generating parsed formula files...")
    generate_parsed_loda_file(loda_file, parsed_loda_file)
    generate_parsed_oeis_file(oeis_file, parsed_oeis_file)
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
