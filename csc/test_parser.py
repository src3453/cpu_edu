from csc_ast import Return
import pytest
from parser import Parser
from token_utils import TokenStream
from lexer import Lexer

def util_parse_expression(source_code):
    # A helper function to tokenize the source code and parse it into an AST.
    lexer = Lexer(source_code)
    tokens = []
    while True:
        token = lexer.next_token()
        tokens.append(token)
        if token.type == "EOF":
            break
    parser = Parser(tokens)
    return parser.parse_expression()

def util_parse_return_statement(source_code):
    # A helper function to tokenize the source code and parse it into an AST for return statements.
    lexer = Lexer(source_code)
    tokens = []
    while True:
        token = lexer.next_token()
        tokens.append(token)
        if token.type == "EOF":
            break
    parser = Parser(tokens)
    return parser.parse_return_statement()

def test_expression_precedence():
    # A simple test case to parse the expression "1 + 2 * 3" and check the structure of the resulting AST.
    # Also checks that multiplication has higher precedence than addition, so the AST should reflect that "2 * 3" is evaluated before adding "1".
    ast = util_parse_expression("1 + 2 * 3")

    assert ast.op == "+"
    assert ast.right.op == "*"

def test_expression_parentheses():
    # A test case to parse the expression "(1 + 2) * 3" and check that the parentheses correctly affect the structure of the AST.
    ast = util_parse_expression("(1 + 2) * 3")

    assert ast.op == "*"
    assert ast.left.op == "+"

def test_expression_nested_parentheses():
    # A test case to parse the expression "((1 + 2) * 3) - 4" and check that multiple levels of parentheses are handled correctly in the AST.
    ast = util_parse_expression("((1 + 2) * 3) - 4")

    assert ast.op == "-"
    assert ast.left.op == "*"
    assert ast.left.left.op == "+"

def test_return_statement():
    # A test case to parse a simple return statement like "return 1;" and check that the AST correctly represents the return statement and its value.
    ast = util_parse_return_statement("return 1;")

    assert isinstance(ast, Return)

def test_return_expression():
    # A test case to parse a return statement with an expression like "return 1 + 2;" and check that the AST correctly represents the return statement and its expression.
    ast = util_parse_return_statement("return 1 + 2;")

    assert isinstance(ast, Return)
    assert ast.value.op == "+"

def test_return_parenthesized_expression():
    # A test case to parse a return statement with a parenthesized expression like "return (1 + 2) * 3;" and check that the AST correctly represents the return statement and its expression with correct precedence.
    ast = util_parse_return_statement("return (1 + 2) * 3;")

    assert isinstance(ast, Return)
    assert ast.value.op == "*"
    assert ast.value.left.op == "+"

def test_return_missing_semicolon():
    # A test case to parse a return statement without a semicolon like "return 1" and check that the parser raises a SyntaxError due to the missing semicolon.
    with pytest.raises(SyntaxError):
        util_parse_return_statement("return 1")