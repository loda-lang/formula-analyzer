import math
from dataclasses import dataclass
from fractions import Fraction
from typing import List, Union


class NumNode:
    def __init__(self, value: int):
        self.value = value


class VarNode:
    def __init__(self):
        pass


class BinNode:
    def __init__(self, op: str, left: object, right: object):
        self.op = op
        self.left = left
        self.right = right


class UnaryNode:
    def __init__(self, op: str, operand: object):
        self.op = op
        self.operand = operand


class FuncNode:
    def __init__(self, name: str, args: List[object]):
        self.name = name
        self.args = args


def _check_arg_count(func_name: str, arg_vals: List, expected: int) -> None:
    """Check if function has the expected number of arguments."""
    if len(arg_vals) != expected:
        plural = "s" if expected != 1 else ""
        raise ValueError(f"{func_name}() expects {expected} argument{plural}")


def _binomial(n_arg: int, k_arg: int) -> int:
    """
    Generalized binomial coefficient.
    
    Follows the rules from https://arxiv.org/pdf/1105.3689.pdf
    and mirrors the C++ reference implementation.
    """
    if n_arg == math.inf or k_arg == math.inf:
        return math.inf

    sign = 1
    n_work = n_arg
    k_work = k_arg

    if n_work < 0:
        if k_work >= 0:
            sign = -1 if k_work % 2 else 1
            n_work = k_work - (n_work + 1)
        elif n_work >= k_work:
            sign = -1 if (n_work - k_work) % 2 else 1
            n_old = n_work
            n_work = -(k_work + 1)
            k_work = n_old - k_work
        else:
            return 0

    if k_work < 0 or n_work < k_work:
        return 0

    if n_work < 2 * k_work:
        k_work = n_work - k_work

    # Use math.comb for the main computation; guard against extremely large k.
    try:
        result = math.comb(n_work, k_work)
    except (OverflowError, ValueError):
        return 0

    return sign * result


def _sumdigits(x: int, base: int = 10) -> int:
    """
    Sum of digits of x in the given base.
    
    Args:
        x: Integer whose digits to sum
        base: Numerical base (default 10)
    
    Returns:
        Sum of digits in the specified base
    """
    if base < 2:
        raise ValueError("sumdigits() base must be >= 2")
    s = 0
    y = abs(x)
    if y == 0:
        return 0
    while y:
        s += y % base
        y //= base
    return s


def _to_int(value: Union[int, float, Fraction]) -> int:
    """Convert a value to integer, raising error if not an integer."""
    if isinstance(value, Fraction):
        if value.denominator != 1:
            raise ValueError("Expected integer argument")
        return int(value.numerator)
    if isinstance(value, float):
        if not value.is_integer():
            raise ValueError("Expected integer argument")
        return int(value)
    return int(value)


def eval_node(node: object, n: int) -> int:
    if isinstance(node, NumNode):
        return int(node.value)
    if isinstance(node, VarNode):
        return int(n)
    if isinstance(node, UnaryNode):
        val = eval_node(node.operand, n)
        return val if node.op == "+" else -val
    if isinstance(node, FuncNode):
        # Evaluate all arguments first
        arg_vals = [eval_node(arg, n) for arg in node.args]
        if node.name == "floor":
            _check_arg_count("floor", arg_vals, 1)
            return math.floor(arg_vals[0])
        if node.name == "ceil":
            _check_arg_count("ceil", arg_vals, 1)
            return math.ceil(arg_vals[0])
        if node.name == "binomial":
            _check_arg_count("binomial", arg_vals, 2)
            n_arg = _to_int(arg_vals[0])
            k_arg = _to_int(arg_vals[1])
            return _binomial(n_arg, k_arg)
        if node.name == "sqrtint":
            _check_arg_count("sqrtint", arg_vals, 1)
            return math.isqrt(_to_int(arg_vals[0]))
        if node.name == "gcd":
            _check_arg_count("gcd", arg_vals, 2)
            return math.gcd(_to_int(arg_vals[0]), _to_int(arg_vals[1]))
        if node.name == "sumdigits":
            if len(arg_vals) not in (1, 2):
                raise ValueError("sumdigits() expects 1 or 2 arguments")
            x = _to_int(arg_vals[0])
            base = _to_int(arg_vals[1]) if len(arg_vals) == 2 else 10
            return _sumdigits(x, base)
        raise ValueError(f"Unknown function: {node.name}")
    if isinstance(node, BinNode):
        left = eval_node(node.left, n)
        right = eval_node(node.right, n)
        if node.op == "+":
            return left + right
        if node.op == "-":
            return left - right
        if node.op == "*":
            return left * right
        if node.op == "/":
            if right == 0:
                raise ValueError("Division by zero")
            return Fraction(left, right)
        if node.op == "^":
            return int(pow(left, right))
    raise ValueError("Invalid node")


@dataclass
class Formula:
    sequence_id: str
    source: str
    expression: str
    node: object

    def evaluate(self, n: int) -> int:
        result = eval_node(self.node, n)
        if isinstance(result, Fraction):
            if result.denominator == 1:
                return int(result.numerator)
            return float(result)
        # Round to nearest integer if result is very close to an integer (floating-point precision)
        if isinstance(result, float):
            rounded = round(result)
            # If within floating-point precision tolerance, return the integer
            if abs(result - rounded) < 1e-9:
                return rounded
            return int(result)
        return int(result)
