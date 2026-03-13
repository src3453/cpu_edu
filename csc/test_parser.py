from csc_ast import Return, ExpressionStatement, Block
import pytest # ty:ignore[unresolved-import]
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

def util_parse_statement(source_code) -> Return | ExpressionStatement | Block:
    # A helper function to tokenize the source code and parse it into an AST for general statements.
    lexer = Lexer(source_code)
    tokens = []
    while True:
        token = lexer.next_token()
        tokens.append(token)
        if token.type == "EOF":
            break
    parser = Parser(tokens)
    return parser.parse_statement()

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
    # A test case to parse a simple return statement and check that the AST correctly represents the return statement and its value.
    ast = util_parse_statement("return 1;")

    assert isinstance(ast, Return)

def test_return_expression():
    # A test case to parse a return statement with an expression and check that the AST correctly represents the return statement and its expression.
    ast = util_parse_statement("return 1 + 2;")

    assert isinstance(ast, Return)
    assert ast.value.op == "+"

def test_return_parenthesized_expression():
    # A test case to parse a return statement with a parenthesized expression and check that the AST correctly represents the return statement and its expression with correct precedence.
    ast = util_parse_statement("return (1 + 2) * 3;")

    assert isinstance(ast, Return)
    assert ast.value.op == "*"
    assert ast.value.left.op == "+"

def test_return_missing_semicolon():
    # A test case to parse a return statement without a semicolon and check that the parser raises a SyntaxError due to the missing semicolon.
    with pytest.raises(SyntaxError):
        util_parse_statement("return 1")

def test_expression_statement():
    # A test case to parse an expression statement and check that the AST correctly represents it as an ExpressionStatement with the correct expression.
    ast = util_parse_statement("1 + 2;")

    assert isinstance(ast, ExpressionStatement)

def test_expression_statement_expression():
    # A test case to parse an expression statement and check that the AST correctly represents the expression within the ExpressionStatement.
    ast = util_parse_statement("1 + 2;")

    assert ast.expression.op == "+"

def test_expression_statement_missing_semicolon():
    # A test case to parse an expression statement without a semicolon and check that the parser raises a SyntaxError due to the missing semicolon.
    with pytest.raises(SyntaxError):
        util_parse_statement("1 + 2")

def test_empty_block():
    # A test case to parse an empty block of code and check that the AST correctly represents it as a Block with no statements.
    ast = util_parse_statement("{}")

    assert isinstance(ast, Block)
    assert len(ast.statements) == 0

def test_block_single_statement():
    # A test case to parse a block of code with a single statement and check that the AST correctly represents it as a Block containing that statement.
    ast = util_parse_statement("{ return 1; }")

    assert len(ast.statements) == 1

def test_block_multiple_statements():
    # A test case to parse a block of code with multiple statements and check that the AST correctly represents it as a Block containing those statements.
    ast = util_parse_statement("""
    {
        1 + 2;
        return 3;
    }
    """)

    assert len(ast.statements) == 2

