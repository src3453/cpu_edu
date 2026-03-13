from token_utils import TokenStream
import csc_ast as ast

class Parser:
    def __init__(self, tokens):
        self.tokens = TokenStream(tokens) # convert list of tokens into a TokenStream for easier parsing

    def parse_primary(self):
        # Parse a primary expression (number or identifier).
        token = self.tokens.peek()

        if token.type == "NUMBER": # Number token, create a Number AST node
            self.tokens.consume()
            return ast.Number(token.value)
        
        if token.type == "IDENT": # Identifier token, create an Identifier AST node
            self.tokens.consume()
            return ast.Identifier(token.value)
        
        if token.type == "LPAREN": # Parenthesized expression, parse the inner expression
            self.tokens.consume() # consume the '(' token
            expr = self.parse_expression() # parse the expression inside the parentheses
            self.tokens.expect("RPAREN") # expect and consume the ')' token
            return expr
        
        raise SyntaxError(f"Unexpected token {token.type} at position {token.pos}, expected a primary expression")

    def parse_mul_div(self):
        # Parse multiplication and division expressions.
        node = self.parse_primary() # Parse the left-hand side primary expression
        while True:
            if self.tokens.match("ASTERISK"): # If we see a '*', parse the right-hand side and create a BinaryOp node
                right = self.parse_primary()
                node = ast.BinaryOp(node, "*", right)
            elif self.tokens.match("SLASH"): # If we see a '/', parse the right-hand side and create a BinaryOp node
                right = self.parse_primary()
                node = ast.BinaryOp(node, "/", right)
            else:
                break # If we don't see '*' or '/', we're done parsing multiplication/division
        return node
    
    def parse_add_sub(self):
        # Parse addition and subtraction expressions.
        node = self.parse_mul_div() # Parse the left-hand side multiplication/division expression
        while True:
            if self.tokens.match("PLUS"): # If we see a '+', parse the right-hand side and create a BinaryOp node
                right = self.parse_mul_div()
                node = ast.BinaryOp(node, "+", right)
            elif self.tokens.match("MINUS"): # If we see a '-', parse the right-hand side and create a BinaryOp node
                right = self.parse_mul_div()
                node = ast.BinaryOp(node, "-", right)
            else:
                break # If we don't see '+' or '-', we're done parsing addition/subtraction
        return node
    
    def parse_expression(self):
        # Parse an expression, which currently only supports addition and subtraction.
        return self.parse_add_sub() # Start parsing with the lowest precedence level (addition/subtraction)
    
    def parse_return_statement(self):
        # Parse a return statement, which starts with the 'return' keyword followed by an expression and a semicolon.
        self.tokens.expect("RETURN") # Expect and consume the 'return' keyword
        expr = self.parse_expression() # Parse the expression that follows 'return'
        self.tokens.expect("SEMICOLON") # Expect and consume the ';' token
        return ast.Return(expr) # Create and return a Return AST node with the parsed expression as its value

    def parse_expression_statement(self):
        # Parse an expression statement, which is an expression followed by a semicolon.
        expr = self.parse_expression() # Parse the expression
        self.tokens.expect("SEMICOLON") # Expect and consume the ';' token
        return ast.ExpressionStatement(expr) # Create and return an ExpressionStatement AST node with the parsed expression

    def parse_statement(self):
        # Parse a statement, which can currently only be a return statement or an expression statement.
        if self.tokens.check("RETURN"):
            return self.parse_return_statement()
        return self.parse_expression_statement()