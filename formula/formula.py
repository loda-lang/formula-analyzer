import math
from dataclasses import dataclass
from fractions import Fraction
from typing import List, Optional, Union


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


class RecurNode:
    """AST node for recursive references a(expr), e.g. a(n-1)."""
    def __init__(self, arg: object):
        self.arg = arg  # AST node for the argument expression


def _is_int(value) -> bool:
    """Check whether a value is an integer (or integer-valued float/Fraction)."""
    if isinstance(value, int):
        return True
    if isinstance(value, float):
        return value.is_integer()
    if isinstance(value, Fraction):
        return value.denominator == 1
    return False


def _check_arg_count(func_name: str, arg_vals: List, expected: int) -> None:
    """Check if function has the expected number of arguments."""
    if len(arg_vals) != expected:
        plural = "s" if expected != 1 else ""
        raise ValueError(f"{func_name}() expects {expected} argument{plural}")


def _binomial(n_arg, k_arg):
    """
    Generalized binomial coefficient supporting both integer and non-integer arguments.
    
    For integer arguments: follows the rules from https://arxiv.org/pdf/1105.3689.pdf
    and mirrors the C++ reference implementation (supports negative n and k).
    
    For non-integer arguments: uses the gamma function definition
    binomial(a, b) = Gamma(a+1) / (Gamma(b+1) * Gamma(a-b+1)).
    """
    if n_arg == math.inf or k_arg == math.inf:
        return math.inf

    if _is_int(n_arg) and _is_int(k_arg):
        return _binomial_int(int(n_arg), int(k_arg))

    # Non-integer path: use gamma function
    # binomial(a, b) = Gamma(a+1) / (Gamma(b+1) * Gamma(a-b+1))
    a = float(n_arg)
    b = float(k_arg)
    try:
        return math.gamma(a + 1) / (math.gamma(b + 1) * math.gamma(a - b + 1))
    except (ValueError, OverflowError, ZeroDivisionError):
        raise ValueError(f"binomial({n_arg}, {k_arg}) undefined")


def _binomial_int(n_arg: int, k_arg: int) -> int:
    """Integer binomial coefficient with support for negative arguments."""
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
    if not _is_int(value):
        raise ValueError("Expected integer argument")
    return int(value)


def eval_node(node: object, n: int, memo: Optional[dict] = None) -> int:
    if isinstance(node, NumNode):
        return int(node.value)
    if isinstance(node, VarNode):
        return int(n)
    if isinstance(node, UnaryNode):
        val = eval_node(node.operand, n, memo)
        return val if node.op == "+" else -val
    if isinstance(node, RecurNode):
        if memo is None:
            raise ValueError("Recursive reference without memo")
        idx = eval_node(node.arg, n, memo)
        if not _is_int(idx):
            raise ValueError("Non-integer recursive index")
        idx = int(idx)
        if idx not in memo:
            raise ValueError(f"Missing term a({idx})")
        return memo[idx]
    if isinstance(node, FuncNode):
        # Evaluate all arguments first
        arg_vals = [eval_node(arg, n, memo) for arg in node.args]
        if node.name == "floor":
            _check_arg_count("floor", arg_vals, 1)
            return math.floor(arg_vals[0])
        if node.name == "ceil":
            _check_arg_count("ceil", arg_vals, 1)
            return math.ceil(arg_vals[0])
        if node.name == "binomial":
            _check_arg_count("binomial", arg_vals, 2)
            return _binomial(arg_vals[0], arg_vals[1])
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
        left = eval_node(node.left, n, memo)
        right = eval_node(node.right, n, memo)
        if node.op == "+":
            return left + right
        if node.op == "-":
            return left - right
        if node.op == "*":
            return left * right
        if node.op == "/":
            if right == 0:
                raise ValueError("Division by zero")
            if isinstance(left, float) or isinstance(right, float):
                return float(left) / float(right)
            return Fraction(left, right)
        if node.op == "^":
            return int(pow(left, right))
    raise ValueError("Invalid node")


def _has_recurrence(node: object) -> bool:
    """Check if an AST contains any RecurNode references."""
    if isinstance(node, RecurNode):
        return True
    if isinstance(node, BinNode):
        return _has_recurrence(node.left) or _has_recurrence(node.right)
    if isinstance(node, UnaryNode):
        return _has_recurrence(node.operand)
    if isinstance(node, FuncNode):
        return any(_has_recurrence(arg) for arg in node.args)
    return False


def _convert_result(result) -> int:
    """Convert an eval_node result to an integer."""
    if isinstance(result, Fraction):
        if result.denominator == 1:
            return int(result.numerator)
        return float(result)
    if isinstance(result, float):
        rounded = round(result)
        if abs(result - rounded) < 1e-9:
            return rounded
        return int(result)
    return int(result)


@dataclass
class Formula:
    sequence_id: str
    source: str
    expression: str
    node: object
    lower_bound: Optional[int] = None
    is_recursive: bool = False

    def __post_init__(self):
        self.is_recursive = _has_recurrence(self.node)

    def evaluate(self, n: int, terms: Optional[List[int]] = None, offset: int = 0) -> int:
        if self.is_recursive:
            return self._evaluate_recursive(n, terms, offset)
        result = eval_node(self.node, n)
        return _convert_result(result)

    def _evaluate_recursive(self, n: int, terms: Optional[List[int]], offset: int) -> int:
        if terms is None:
            raise ValueError("Recursive formula requires terms for evaluation")
        # Build memo from known terms
        memo: dict = {}
        for i, val in enumerate(terms):
            memo[offset + i] = val
        # Compute iteratively from the earliest missing index up to n
        start = offset + len(terms)
        for k in range(start, n + 1):
            if k in memo:
                continue
            result = eval_node(self.node, k, memo)
            memo[k] = _convert_result(result)
        if n not in memo:
            raise ValueError(f"Cannot compute a({n})")
        return memo[n]
