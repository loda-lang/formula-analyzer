import re
from dataclasses import dataclass
from fractions import Fraction
from typing import Optional, List, Tuple, Union

# Add comma to tokenizer to support multi-arg functions
TOKEN_REGEX = re.compile(r"\s*(?:([a-zA-Z]+)|([0-9]+)|([nN])|([+\-])|(\*)|(/)|(\^)|(\()|(\))|(,))")


@dataclass
class ParsedFormula:
    sequence_id: str
    source: str
    expression: str
    node: object

    def evaluate(self, n: int) -> int:
        result = _eval_node(self.node, n)
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


class FormulaParser:
    def parse_expression(self, seq_id: str, source: str, expr: str) -> Optional[ParsedFormula]:
        return self._build_formula(seq_id, source, expr)

    def _build_formula(self, seq_id: str, source: str, expr: str) -> Optional[ParsedFormula]:
        cleaned = self._sanitize_expression(expr)
        if cleaned is None:
            return None
        try:
            node = _parse_expression(cleaned)
        except ValueError:
            return None
        return ParsedFormula(sequence_id=seq_id, source=source, expression=cleaned, node=node)

    def _sanitize_expression(self, expr: str) -> Optional[str]:
        candidate = expr.strip().rstrip(".;")
        if not candidate:
            return None
        # Allow commas for multi-arg functions
        if not re.fullmatch(r"[0-9nN\+\-\*/\^\(\),\sa-zA-Z]+", candidate):
            return None
        return candidate


# --- Custom expression scanner and parser (polynomials) ---

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


Token = Tuple[str, Union[int, str]]


def _tokenize(expr: str) -> List[Token]:
    tokens: List[Token] = []
    pos = 0
    while pos < len(expr):
        m = TOKEN_REGEX.match(expr, pos)
        if not m:
            raise ValueError("Invalid token")
        pos = m.end()
        if m.group(1):
            func_name = m.group(1).lower()
            if func_name == "n":
                tokens.append(("VAR", "n"))
            elif func_name in ("floor", "ceil", "binomial", "sqrtint", "gcd", "sumdigits"):
                tokens.append(("FUNC", func_name))
            else:
                raise ValueError(f"Unsupported identifier: {func_name}")
        elif m.group(2):
            tokens.append(("INT", int(m.group(2))))
        elif m.group(3):
            tokens.append(("VAR", "n"))
        elif m.group(4):
            tokens.append(("ADD" if m.group(4) == "+" else "SUB", m.group(4)))
        elif m.group(5):
            tokens.append(("MUL", "*"))
        elif m.group(6):
            tokens.append(("DIV", "/"))
        elif m.group(7):
            tokens.append(("POW", "^"))
        elif m.group(8):
            tokens.append(("LP", "("))
        elif m.group(9):
            tokens.append(("RP", ")"))
        elif m.group(10):
            tokens.append(("COMMA", ","))
        else:
            pass
    tokens.append(("EOF", ""))
    return tokens


class Parser:
    def __init__(self, tokens: List[Token]):
        self.tokens = tokens
        self.i = 0

    def peek(self) -> Token:
        return self.tokens[self.i]

    def eat(self, kind: str) -> Token:
        tok = self.peek()
        if tok[0] != kind:
            raise ValueError(f"Expected {kind}, got {tok}")
        self.i += 1
        return tok

    def parse(self) -> object:
        node = self.expr()
        if self.peek()[0] != "EOF":
            raise ValueError("Unexpected trailing tokens")
        return node

    # expr := term (("+"|"-") term)*
    def expr(self) -> object:
        node = self.term()
        while self.peek()[0] in ("ADD", "SUB"):
            op = self.eat(self.peek()[0])
            rhs = self.term()
            node = BinNode(op[1], node, rhs)
        return node

    # term := factor ( ('*'|'/') factor )*
    def term(self) -> object:
        node = self.factor()
        while self.peek()[0] in ("MUL", "DIV"):
            op_kind = self.peek()[0]
            self.eat(op_kind)
            rhs = self.factor()
            node = BinNode("/" if op_kind == "DIV" else "*", node, rhs)
        return node

    # factor := signed_power
    def factor(self) -> object:
        return self.signed_power()

    # signed_power := ('+'|'-')? power
    def signed_power(self) -> object:
        if self.peek()[0] in ("ADD", "SUB"):
            op = self.eat(self.peek()[0])
            node = self.power()
            return UnaryNode(op[1], node)
        return self.power()

    # power := primary ('^' INT)?
    def power(self) -> object:
        node = self.primary()
        if self.peek()[0] == "POW":
            self.eat("POW")
            exp_tok = self.eat("INT")
            node = BinNode("^", node, NumNode(exp_tok[1]))
        return node

    # primary := INT | VAR | FUNC '(' expr ')' | '(' expr ')'
    def primary(self) -> object:
        kind = self.peek()[0]
        if kind == "INT":
            return NumNode(self.eat("INT")[1])
        if kind == "VAR":
            self.eat("VAR")
            return VarNode()
        if kind == "FUNC":
            func_name = self.eat("FUNC")[1]
            # Only allow supported functions
            if func_name not in ("floor", "ceil", "binomial", "sqrtint", "gcd", "sumdigits"):
                raise ValueError(f"Unsupported function: {func_name}")
            self.eat("LP")
            # Parse one or more arguments separated by commas
            args: List[object] = []
            args.append(self.expr())
            while self.peek()[0] == "COMMA":
                self.eat("COMMA")
                args.append(self.expr())
            self.eat("RP")
            return FuncNode(func_name, args)
        if kind == "LP":
            self.eat("LP")
            node = self.expr()
            self.eat("RP")
            return node
        raise ValueError("Expected primary")


def _parse_expression(expr: str) -> object:
    tokens = _tokenize(expr)
    parser = Parser(tokens)
    return parser.parse()


def _eval_node(node: object, n: int) -> int:
    if isinstance(node, NumNode):
        return int(node.value)
    if isinstance(node, VarNode):
        return int(n)
    if isinstance(node, UnaryNode):
        val = _eval_node(node.operand, n)
        return val if node.op == "+" else -val
    if isinstance(node, FuncNode):
        import math
        # Evaluate all arguments first
        arg_vals = [_eval_node(arg, n) for arg in node.args]
        def _to_int(value: Union[int, float, Fraction]) -> int:
            if isinstance(value, Fraction):
                if value.denominator != 1:
                    raise ValueError("Expected integer argument")
                return int(value.numerator)
            if isinstance(value, float):
                if not value.is_integer():
                    raise ValueError("Expected integer argument")
                return int(value)
            return int(value)
        if node.name == "floor":
            if len(arg_vals) != 1:
                raise ValueError("floor() expects 1 argument")
            return math.floor(arg_vals[0])
        if node.name == "ceil":
            if len(arg_vals) != 1:
                raise ValueError("ceil() expects 1 argument")
            return math.ceil(arg_vals[0])
        if node.name == "binomial":
            if len(arg_vals) != 2:
                raise ValueError("binomial() expects 2 arguments")
            n_arg = _to_int(arg_vals[0])
            k_arg = _to_int(arg_vals[1])

            # Generalized binomial following the rules from https://arxiv.org/pdf/1105.3689.pdf
            # mirrors the C++ reference implementation provided by the user.
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
        if node.name == "sqrtint":
            if len(arg_vals) != 1:
                raise ValueError("sqrtint() expects 1 argument")
            return math.isqrt(_to_int(arg_vals[0]))
        if node.name == "gcd":
            if len(arg_vals) != 2:
                raise ValueError("gcd() expects 2 arguments")
            return math.gcd(_to_int(arg_vals[0]), _to_int(arg_vals[1]))
        if node.name == "sumdigits":
            if len(arg_vals) not in (1, 2):
                raise ValueError("sumdigits() expects 1 or 2 arguments")
            x = _to_int(arg_vals[0])
            base = _to_int(arg_vals[1]) if len(arg_vals) == 2 else 10
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
        raise ValueError(f"Unknown function: {node.name}")
    if isinstance(node, BinNode):
        left = _eval_node(node.left, n)
        right = _eval_node(node.right, n)
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
