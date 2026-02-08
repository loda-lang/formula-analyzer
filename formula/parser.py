import re
from typing import Optional, List, Tuple, Union

from formula.formula import (
    NumNode,
    VarNode,
    BinNode,
    UnaryNode,
    FuncNode,
    Formula,
)

# Add comma to tokenizer to support multi-arg functions
TOKEN_REGEX = re.compile(r"\s*(?:([a-zA-Z]+)|([0-9]+)|([nN])|([+\-])|(\*)|(/)|(\^)|(\()|(\))|(,))")


class FormulaParser:
    def parse_expression(self, seq_id: str, source: str, expr: str) -> Optional[Formula]:
        return self._build_formula(seq_id, source, expr)

    def _build_formula(self, seq_id: str, source: str, expr: str) -> Optional[Formula]:
        cleaned = self._sanitize_expression(expr)
        if cleaned is None:
            return None
        try:
            node = _parse_expression(cleaned)
        except ValueError:
            return None
        return Formula(sequence_id=seq_id, source=source, expression=cleaned, node=node)

    def _sanitize_expression(self, expr: str) -> Optional[str]:
        candidate = expr.strip().rstrip(".;")
        if not candidate:
            return None
        # Allow commas for multi-arg functions
        if not re.fullmatch(r"[0-9nN\+\-\*/\^\(\),\sa-zA-Z]+", candidate):
            return None
        return candidate


# --- Custom expression scanner and parser (polynomials) ---

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
