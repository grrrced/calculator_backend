"""Safe arithmetic expression parser used by the calculator API.

The parser implements a small grammar instead of executing user input as
Python code. It supports +, -, *, /, parentheses, decimals and unary signs.
"""

from __future__ import annotations

import math
import re
from dataclasses import dataclass


class ExpressionError(ValueError):
    """Raised when an expression is invalid or cannot be evaluated."""


@dataclass(frozen=True)
class Token:
    kind: str
    value: str


TOKEN_RE = re.compile(
    r"\s*(?:(?P<number>(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?)|"
    r"(?P<operator>[()+\-*/]))"
)


def tokenize(expression: str) -> list[Token]:
    if not isinstance(expression, str) or not expression.strip():
        raise ExpressionError("Expression cannot be empty")
    if len(expression) > 200:
        raise ExpressionError("Expression is too long (maximum 200 characters)")

    tokens: list[Token] = []
    position = 0
    while position < len(expression):
        if expression[position:].strip() == "":
            break
        match = TOKEN_RE.match(expression, position)
        if not match:
            raise ExpressionError(f"Invalid character near position {position + 1}")
        if match.group("number") is not None:
            tokens.append(Token("number", match.group("number")))
        else:
            tokens.append(Token(match.group("operator"), match.group("operator")))
        position = match.end()
    if len(tokens) > 100:
        raise ExpressionError("Expression contains too many tokens")
    return tokens


class Parser:
    def __init__(self, tokens: list[Token]):
        self.tokens = tokens
        self.index = 0

    def current(self) -> Token | None:
        return self.tokens[self.index] if self.index < len(self.tokens) else None

    def consume(self, kind: str) -> Token:
        token = self.current()
        if token is None or token.kind != kind:
            found = "end of expression" if token is None else token.value
            raise ExpressionError(f"Expected '{kind}', found {found}")
        self.index += 1
        return token

    def parse(self) -> float:
        result = self.parse_expression()
        if self.current() is not None:
            raise ExpressionError(f"Unexpected token '{self.current().value}'")
        return result

    def parse_expression(self) -> float:
        result = self.parse_term()
        while self.current() is not None and self.current().kind in ("+", "-"):
            operator = self.consume(self.current().kind).kind
            right = self.parse_term()
            result = result + right if operator == "+" else result - right
        return result

    def parse_term(self) -> float:
        result = self.parse_unary()
        while self.current() is not None and self.current().kind in ("*", "/"):
            operator = self.consume(self.current().kind).kind
            right = self.parse_unary()
            if operator == "*":
                result *= right
            else:
                if right == 0:
                    raise ExpressionError("Division by zero is not allowed")
                result /= right
        return result

    def parse_unary(self) -> float:
        if self.current() is not None and self.current().kind in ("+", "-"):
            operator = self.consume(self.current().kind).kind
            value = self.parse_unary()
            return value if operator == "+" else -value
        return self.parse_primary()

    def parse_primary(self) -> float:
        token = self.current()
        if token is None:
            raise ExpressionError("Expression ends unexpectedly")
        if token.kind == "number":
            self.index += 1
            try:
                return float(token.value)
            except ValueError as error:
                raise ExpressionError("Invalid number") from error
        if token.kind == "(":
            self.index += 1
            value = self.parse_expression()
            self.consume(")")
            return value
        raise ExpressionError(f"Unexpected token '{token.value}'")


def calculate(expression: str) -> int | float:
    """Evaluate a supported expression and return a JSON-friendly number."""

    value = Parser(tokenize(expression)).parse()
    if not math.isfinite(value):
        raise ExpressionError("Result is outside the supported numeric range")
    value = round(value, 12)
    if value == 0:
        value = 0.0
    return int(value) if value.is_integer() else value
