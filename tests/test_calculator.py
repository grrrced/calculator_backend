import unittest

from calculator import ExpressionError, calculate


class CalculatorTests(unittest.TestCase):
    def test_operator_precedence_and_parentheses(self):
        self.assertEqual(calculate("1 + 2 * 3"), 7)
        self.assertEqual(calculate("(1 + 2) * 3"), 9)
        self.assertEqual(calculate("10 / 2 + 7"), 12)

    def test_decimal_and_unary_operators(self):
        self.assertEqual(calculate("-5 + 8"), 3)
        self.assertEqual(calculate("3 * -2"), -6)
        self.assertEqual(calculate("0.1 + 0.2"), 0.3)
        self.assertEqual(calculate(" 7 + 1   "), 8)

    def test_invalid_expression_and_division_by_zero(self):
        for expression in ("", "1 +", "2 ** 3", "abc", "(1 + 2"):
            with self.subTest(expression=expression):
                with self.assertRaises(ExpressionError):
                    calculate(expression)
        with self.assertRaisesRegex(ExpressionError, "Division by zero"):
            calculate("10 / (5 - 5)")


if __name__ == "__main__":
    unittest.main()
