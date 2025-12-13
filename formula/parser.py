import re
from dataclasses import dataclass
from typing import Optional, List, Tuple, Union

TOKEN_REGEX = re.compile(r"\s*(?:([0-9]+)|([nN])|([+\-])|(\*)|(\^)|(\()|(\)))")


@dataclass
class ParsedFormula:
    sequence_id: str
    source: str
    expression: str
    node: object

    def evaluate(self, n: int) -> int:
        return _eval_node(self.node, n)


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
        if not re.fullmatch(r"[0-9nN\+\-\*\^\(\)\s]+", candidate):
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
            tokens.append(("INT", int(m.group(1))))
        elif m.group(2):
            tokens.append(("VAR", "n"))
        elif m.group(3):
            tokens.append(("ADD" if m.group(3) == "+" else "SUB", m.group(3)))
        elif m.group(4):
            tokens.append(("MUL", "*"))
        elif m.group(5):
            tokens.append(("POW", "^"))
        elif m.group(6):
            tokens.append(("LP", "("))
        elif m.group(7):
            tokens.append(("RP", ")"))
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

    # term := factor ( '*' factor )*
    def term(self) -> object:
        node = self.factor()
        while self.peek()[0] == "MUL":
            self.eat("MUL")
            rhs = self.factor()
            node = BinNode("*", node, rhs)
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

    # primary := INT | VAR | '(' expr ')'
    def primary(self) -> object:
        kind = self.peek()[0]
        if kind == "INT":
            return NumNode(self.eat("INT")[1])
        if kind == "VAR":
            self.eat("VAR")
            return VarNode()
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
    if isinstance(node, BinNode):
        left = _eval_node(node.left, n)
        right = _eval_node(node.right, n)
        if node.op == "+":
            return left + right
        if node.op == "-":
            return left - right
        if node.op == "*":
            return left * right
        if node.op == "^":
            return int(pow(left, right))
    raise ValueError("Invalid node")
