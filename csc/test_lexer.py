# requires pytest to run the tests. You can install it with `pip install pytest`.

import pytest
from lexer import Lexer, Token

def util_tokenize(source_code: str) -> list[Token]:
    # test util for tokenizing source code into a list of tokens using the Lexer class.
    lexer = Lexer(source_code)
    tokens = []
    while True:
        token = lexer.next_token()
        tokens.append(token)
        if token.type == "EOF":
            break
    return tokens

def test_number_decimal():
    source_code = "12345" # A simple test case with a single decimal number
    tokens = util_tokenize(source_code)
    assert tokens[0].type == "NUMBER"
    assert tokens[0].value == 12345
    assert tokens[1].type == "EOF"
    assert tokens[1].value is None

def test_number_hexadecimal():
    source_code = "0x1234" # A simple test case with a single hexadecimal number
    tokens = util_tokenize(source_code)
    assert tokens[0].type == "NUMBER"
    assert tokens[0].value == 0x1234
    assert tokens[1].type == "EOF"
    assert tokens[1].value is None

def test_number_hexadecimal_uppercase():
    source_code = "0XABCD" # A simple test case with a single hexadecimal number using uppercase 'X'
    tokens = util_tokenize(source_code)
    assert tokens[0].type == "NUMBER"
    assert tokens[0].value == 0xABCD
    assert tokens[1].type == "EOF"
    assert tokens[1].value is None

def test_number_invalid_hexadecimal():
    source_code = "0xG123" # An invalid hexadecimal number (contains 'G')
    lexer = Lexer(source_code)
    with pytest.raises(SyntaxError):
        lexer.next_token() # will raise a SyntaxError because 'G' is not a valid hexadecimal digit

def test_number_invalid_hexadecimal_no_digits():
    source_code = "0x" # An invalid hexadecimal number (missing digits after '0x')
    lexer = Lexer(source_code)
    with pytest.raises(SyntaxError):
        lexer.next_token() # will raise a SyntaxError because there are no valid hexadecimal digits after '0x'

def test_identifiers():
    source_code = "var1 _var2 var_3" # A test case with multiple identifiers
    tokens = util_tokenize(source_code)
    assert tokens[0].type == "IDENTIFIER"
    assert tokens[0].value == "var1"
    assert tokens[1].type == "IDENTIFIER"
    assert tokens[1].value == "_var2"
    assert tokens[2].type == "IDENTIFIER"
    assert tokens[2].value == "var_3"
    assert tokens[3].type == "EOF"
    assert tokens[3].value is None

def test_keywords():
    source_code = "if else while return" # A test case with multiple keywords
    tokens = util_tokenize(source_code)
    assert tokens[0].type == "IF"
    assert tokens[0].value == "if"
    assert tokens[1].type == "ELSE"
    assert tokens[1].value == "else"
    assert tokens[2].type == "WHILE"
    assert tokens[2].value == "while"
    assert tokens[3].type == "RETURN"
    assert tokens[3].value == "return"
    assert tokens[4].type == "EOF"
    assert tokens[4].value is None

def test_skip_whitespace():
    source_code = "   \t\n  42   \n\t  " # A test case with leading and trailing whitespace around a number
    tokens = util_tokenize(source_code)
    assert tokens[0].type == "NUMBER"
    assert tokens[0].value == 42
    assert tokens[1].type == "EOF"
    assert tokens[1].value is None

def test_simple_program():
    # A test case with a simple C program to check if the lexer can correctly tokenize a combination of keywords, identifiers, numbers, and operators.
    code = """
    int main() {
        return 3 + 4;
    }
    """

    tokens = util_tokenize(code)

    types = [t.type for t in tokens]

    assert types == [
        "INT",
        "IDENT",
        "LPAREN",
        "RPAREN",
        "LBRACE",
        "RETURN",
        "NUMBER",
        "PLUS",
        "NUMBER",
        "SEMICOLON",
        "RBRACE",
        "EOF"
    ]

def test_single_tokens():
    # work in progress
    source_code = "+ - * / = ; ( ) { }" # A test case with various single-character tokens
    tokens = util_tokenize(source_code)
    assert [t.type for t in tokens[:-1]] == [
        "PLUS","MINUS","ASTERISK","SLASH",
        "ASSIGN","SEMICOLON",
        "LPAREN","RPAREN",
        "LBRACE","RBRACE"
    ] 