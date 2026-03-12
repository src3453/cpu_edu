# ast.py - Abstract Syntax Tree (AST) definitions for the C subset compiler (CSC)

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