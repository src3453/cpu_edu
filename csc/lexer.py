# lexer.py - A simple lexer for the C subset compiler (csc)
# This lexer takes C source code as input and produces a stream of tokens that can be used by the parser.

# The lexer recognizes the following token types:
# - IDENT: for variable names and function names
# - NUMBER: for numeric literals (e.g., 123, 0x1A)
# - EOF: for end of file
# and reserved keywords in below dictionary:

KEYWORDS = {
    "int": "INT", # Note: SRC16 is a 16-bit big-endian system, so "int" type is 16 bits.
    "return": "RETURN",
    "if": "IF",
    "else": "ELSE",
    "while": "WHILE",
}

# Single-character tokens
SINGLE_TOKENS = {
    "+": "PLUS",
    "-": "MINUS",
    "*": "ASTERISK",
    "/": "SLASH",
    "=": "ASSIGN",
    ";": "SEMICOLON",
    "(": "LPAREN",
    ")": "RPAREN",
    "{": "LBRACE",
    "}": "RBRACE",
}

class Token:
    # A simple token class to represent different types of tokens in the C subset language.
    def __init__(self, type, value, pos):
        self.type = type
        self.value = value
        self.pos = pos

    def __repr__(self):
        return f"Token({self.type}, {self.value})"
    
class Lexer:
    # The Lexer class takes C source code as input and produces a stream of tokens.
    def __init__(self, source:str):
        self.source = source
        self.pos = 0
        self.length = len(source)

    def getchar(self, lookahead:int=0) -> str|None:
        # Return the current character or None if we've reached the end of the source.
        if self.pos + lookahead >= self.length:
            return None
        return self.source[self.pos + lookahead]
    
    def advance(self) -> str|None:
        # Move the position forward by one character, and return the current character.
        ch = self.getchar()
        if ch is not None: # avoid advancing past the end of the source
            self.pos += 1
        return ch
    
    def skip_whitespace(self):
        # Skip over any whitespace characters (spaces, tabs, newlines).
        while self.getchar() is not None and self.getchar().isspace():
            self.advance()

    def read_number(self) -> Token:
        # Read a number token from the source code, handling decimal and hexadecimal formats.
        start_pos = self.pos
        if self.getchar() == '0' and self.getchar(1) in ['x', 'X']: # find "0x" or "0X" prefix for hexadecimal numbers
            # Hexadecimal number
            self.advance() # skip '0'
            self.advance() # skip 'x' or 'X'
            if not self.getchar() or not (self.getchar().isdigit() or self.getchar().lower() in 'abcdef'): # after "0x", there should be at least one valid hexadecimal digit
                raise SyntaxError(f"Invalid hexadecimal number at position {start_pos}")
            while self.getchar() is not None and (self.getchar().isdigit() or self.getchar().lower() in 'abcdef'): # valid hexadecimal digits
                self.advance()
            value = int(self.source[start_pos:self.pos], 16) # Convert the hexadecimal string to an integer.
        else:
            # Decimal number
            while self.getchar() is not None and self.getchar().isdigit():
                self.advance()
            value = int(self.source[start_pos:self.pos]) # Convert the decimal string to an integer.
        return Token("NUMBER", value, start_pos)

    def next_token(self) -> Token:
        # Get the next token from the source code.
        self.skip_whitespace() # Skip any leading whitespace before trying to read the next token.
        ch = self.getchar() # Get the current character to determine what type of token we are looking at.

        if ch is None:
            return Token("EOF", None, self.pos) # If we've reached the end of the source, return an EOF token.
        
        if ch.isdigit():
            return self.read_number() # If the current character is a digit, read a number token.