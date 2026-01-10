"""
Formula annotation module - generates annotated formula files with parse status.
"""

import os
import re
from formula.parser import FormulaParser
from formula.data import LODA_LINE_RE, OEIS_HEADER_RE


def generate_parsed_loda_file(loda_input: str, loda_output: str):
    """Generate annotated LODA formula file with check marks for successfully parsed formulas."""
    parser = FormulaParser()
    
    print(f"  Processing LODA formulas from {os.path.basename(loda_input)}...")
    loda_parsed = 0
    loda_total = 0
    
    with open(loda_input, 'r', encoding='utf-8', errors='ignore') as infile:
        with open(loda_output, 'w', encoding='utf-8') as outfile:
            for line in infile:
                stripped = line.rstrip('\n')
                match = LODA_LINE_RE.match(stripped)
                if match:
                    loda_total += 1
                    seq_id = match.group(1)
                    expr = match.group(2)
                    
                    # Try to parse the formula
                    parsed = parser.parse_expression(seq_id, "loda", expr)
                    if parsed:
                        loda_parsed += 1
                        outfile.write(f"{stripped} ✅\n")
                    else:
                        outfile.write(f"{stripped}\n")
                else:
                    outfile.write(f"{stripped}\n")
    
    print(f"    LODA: {loda_parsed}/{loda_total} formulas parsed successfully")
    print(f"    Saved to: {loda_output}")


def generate_parsed_oeis_file(oeis_input: str, oeis_output: str):
    """Generate annotated OEIS formula file with check marks for successfully parsed formulas."""
    parser = FormulaParser()
    
    print(f"  Processing OEIS formulas from {os.path.basename(oeis_input)}...")
    oeis_parsed = 0
    oeis_total = 0
    
    with open(oeis_input, 'r', encoding='utf-8', errors='ignore') as infile:
        with open(oeis_output, 'w', encoding='utf-8') as outfile:
            for line in infile:
                stripped = line.rstrip('\n')
                
                # Check if this is a sequence header or continuation line
                seq_match = OEIS_HEADER_RE.match(stripped)
                
                if seq_match:
                    # This is a new sequence line
                    seq_id = seq_match.group(1)
                    text = seq_match.group(2)
                    
                    # Check if it contains a formula
                    if re.search(r'a\(n\)\s*=', text, re.IGNORECASE):
                        oeis_total += 1
                        # Extract the expression after "a(n) ="
                        match_expr = re.search(r'a\(n\)\s*=\s*(.+)', text, re.IGNORECASE)
                        if match_expr:
                            expr = match_expr.group(1).strip().rstrip('.;')
                            parsed = parser.parse_expression(seq_id, "oeis", expr)
                            if parsed:
                                oeis_parsed += 1
                                outfile.write(f"{stripped} ✅\n")
                            else:
                                outfile.write(f"{stripped}\n")
                        else:
                            outfile.write(f"{stripped}\n")
                    else:
                        outfile.write(f"{stripped}\n")
                        
                elif stripped.startswith('  ') and stripped.strip():
                    # This is a continuation line
                    cont = stripped.strip()
                    if re.search(r'a\(n\)\s*=', cont, re.IGNORECASE):
                        oeis_total += 1
                        # Extract the expression
                        match_expr = re.search(r'a\(n\)\s*=\s*(.+)', cont, re.IGNORECASE)
                        if match_expr:
                            expr = match_expr.group(1).strip().rstrip('.;')
                            # We don't have the seq_id here, use a dummy
                            parsed = parser.parse_expression("A000000", "oeis", expr)
                            if parsed:
                                oeis_parsed += 1
                                outfile.write(f"{stripped} ✅\n")
                            else:
                                outfile.write(f"{stripped}\n")
                        else:
                            outfile.write(f"{stripped}\n")
                    else:
                        outfile.write(f"{stripped}\n")
                else:
                    outfile.write(f"{stripped}\n")
    
    print(f"    OEIS: {oeis_parsed}/{oeis_total} formulas parsed successfully")
    print(f"    Saved to: {oeis_output}")
