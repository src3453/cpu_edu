# ast.py - Abstract Syntax Tree (AST) definitions for the C subset compiler (CSC)
# Abstract Syntax Tree (AST) is a data structure used to represent the structure
# of source code in a way that is easier for the compiler to analyze and manipulate. 
# In this file, we define the various node types that can appear in the AST for our C subset language.

# Nodes in the AST
class Number:
    def __init__(self, value):
        self.value = value

class Identifier:
    def __init__(self, name):
        self.name = name

class BinaryOp:
    # node graph for binary operations (e.g., addition, subtraction, multiplication, division)
    def __init__(self, left, op, right):
        self.left = left # left edge of the binary operation
        self.op = op # node type (e.g., '+', '-', '*', '/')
        self.right = right # right edge of the binary operation

class Return:
    # node graph for return statements
    def __init__(self, value):
        self.value = value

class ExpressionStatement:
    # node graph for expression statements (e.g., a standalone expression followed by a semicolon)
    def __init__(self, expression):
        self.expression = expression

class Block:
    # node graph for a block of statements enclosed in braces
    def __init__(self, statements):
        self.statements = statements # statements in the block represented as a list of AST nodes