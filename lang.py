

# CONSTANTS


DIGITS = "0123456789"
TAB = '\t'
NEWLINE = '\n'
WHITESPACE = " "

# Available Tokens
INT_T = "INT"
FLOAT_T = "FLOAT"
PLUS_T = "PLUS"
MINUS_T = "MINUS"
MULT_T = "MULT"
DIV_T = "DIV"
LPAREN_T = "LPAREN"
RPAREN_T = "RPAREN"
EOF_T = "EOF"  # END OF FILE

######################
#####  Position  #####
######################


class Position:
    def __init__(self, index, line, column, filename, filecontent) -> None:
        self.ind = index
        self.ln = line
        self.col = column
        self.fn = filename
        self.ftxt = filecontent

    def __repr__(self) -> str:
        return f"Position({self.ind}, {self.ln}, {self.col}, {self.fn}, {self.ftxt})"

    def next_pos(self, current_char=None):
        self.ind += 1
        self.col += 1
        if current_char == NEWLINE:
            self.ln += 1
            self.col = 0

        return self

    def copy_pos(self):
        return Position(self.ind, self.ln, self.col, self.fn, self.ftxt)

# function for styling how error is showed


def string_with_arrows(text, pos_start, pos_end):
    result = ''

    # Calculate indices
    ind_start = max(text.rfind('\n', 0, pos_start.ind), 0)
    ind_end = text.find('\n', ind_start + 1)
    if ind_end < 0:
        ind_end = len(text)

    # Generate each line
    line_count = pos_end.ln - pos_start.ln + 1
    for i in range(line_count):
        # Calculate line columns
        line = text[ind_start:ind_end]
        col_start = pos_start.col if i == 0 else 0
        col_end = pos_end.col if i == line_count - 1 else len(line) - 1

        # Append to result
        result += line + '\n'
        result += ' ' * col_start + '^' * (col_end - col_start)

        # Re-calculate indices
        ind_start = ind_end
        ind_end = text.find('\n', ind_start + 1)
        if ind_end < 0:
            ind_end = len(text)

    return result.replace('\t', '')

# Error


class Error:
    def __init__(self, start_pos, end_pos,  error_name, error_details) -> None:
        self.start_pos = start_pos
        self.end_pos = end_pos
        self.err_name = error_name
        self.err_details = error_details

    def __repr__(self):
        return f"{self.err_name} : {self.err_details}\nFile {self.start_pos.fn}, line {self.start_pos.ln}\n\n{string_with_arrows(self.start_pos.ftxt, self.start_pos, self.end_pos)} "


class IllegalCharError(Error):
    def __init__(self, start_pos, end_pos, error_details) -> None:
        super().__init__(start_pos, end_pos, "Illegal Character", error_details)


class InvalidSyntaxError(Error):
    def __init__(self, start_pos, end_pos, error_details) -> None:
        super().__init__(start_pos, end_pos, "Invalid Syntax", error_details)


class RunTimeError(Error):
    def __init__(self, start_pos, end_pos, error_details, context) -> None:
        super().__init__(start_pos, end_pos, "RunfTime Error", error_details)
        self.context = context

    def generate_traceback(self):
        ret = ''
        pos = self.start_pos
        ctx = self.context

        while ctx:
            ret = f"  File {pos.fn}, line {str(pos.ln + 1)}, in {ctx.display}\n" + ret
            pos = ctx.parent_pos
            ctx = ctx.parent

        return "Traceback (most recent call last):\n" + ret

    def __repr__(self):
        return f"{self.generate_traceback()}{self.err_name} : {self.err_details}\n\n{string_with_arrows(self.start_pos.ftxt, self.start_pos, self.end_pos)} "

# It is like variable that we control how to show it


class Token:
    def __init__(self, type, value=None, start_pos=None, end_pos=None) -> None:
        self.type = type
        self.value = value

        if start_pos:
            self.start_pos = start_pos.copy_pos()
            self.end_pos = start_pos.copy_pos()
            self.end_pos.next_pos()
        if end_pos:
            self.end_pos = end_pos

    # How to represent it when printing it

    def __repr__(self) -> str:
        if self.value:
            return f"{self.type}:{self.value}"
        # else
        return self.type

# The Tokenizer


class Lexer:
    def __init__(self, text, filename) -> None:
        self.fn = filename
        self.txt = text
        # position of current characte
        self.pos = Position(-1, 0, -1, filename, text)
        self.last_pos = len(self.txt) - 1
        self.current = None
        self.next()

    def next(self):
        if self.pos.ind < self.last_pos:
            self.pos.next_pos(self.current)
            self.current = self.txt[self.pos.ind]
        else:
            self.current = None

    def get_tokens(self):
        tokens = []

        while self.current != None:
            # Ignore whitespaces,tabs,..
            if self.current == TAB:
                self.next()
            elif self.current == WHITESPACE:
                self.next()
            # Basic Math Operations
            elif self.current == "+":
                tokens.append(Token(PLUS_T, start_pos=self.pos))
                self.next()
            elif self.current == "-":
                tokens.append(Token(MINUS_T, start_pos=self.pos))
                self.next()
            elif self.current == "*":
                tokens.append(Token(MULT_T, start_pos=self.pos))
                self.next()
            elif self.current == "/":
                tokens.append(Token(DIV_T, start_pos=self.pos))
                self.next()
            # Parenthesis
            elif self.current == "(":
                tokens.append(Token(LPAREN_T, start_pos=self.pos))
                self.next()
            elif self.current == ")":
                tokens.append(Token(RPAREN_T, start_pos=self.pos))
                self.next()
            # Numbers
            elif self.current in DIGITS:
                tokens.append(self.get_number_tok())
            else:
                # raise char error
                err_start_pos = self.pos.copy_pos()
                char = self.current
                self.next()
                return [], IllegalCharError(err_start_pos, self.pos, f"' {char} '")

        # add the end of file token
        tokens.append(Token(EOF_T, start_pos=self.pos))

        return tokens, None

    def get_number_tok(self):

        num = ""  # complete number
        dot = False
        Float = False
        start_pos = self.pos.copy_pos()

        while self.current != None and self.current in DIGITS + ".":

            # Find a dot ==> Float type
            if self.current == ".":
                if dot:
                    break
                else:
                    dot = True
                    Float = True
                    num += self.current
                    self.next()
            else:
                num += self.current
                self.next()

        # return token
        if Float:
            return Token(FLOAT_T, float(num), start_pos, self.pos)

        return Token(INT_T, int(num), start_pos, self.pos)

## End Lexering ##

# Language Syntax
    # factor : single num
    # term : factor (* /) fator
    # Expression : term operation(+ -) term

# Parsing is About prganize toks to tree data structures

# Nodes == node or each type of token


class NumberNode:
    def __init__(self, token) -> None:
        self.tok = token

        self.start_pos = self.tok.start_pos
        self.end_pos = self.tok.end_pos

    def __repr__(self) -> str:
        return str(self.tok)


# Opration Nodes


class BinOpNode:
    def __init__(self, left_node, operation, right_node) -> None:
        self.left = left_node
        self.op = operation
        self.right = right_node

        self.start_pos = self.left.start_pos
        self.end_pos = self.right.end_pos

    def __repr__(self) -> str:
        return f"({self.left}, {self.op}, {self.right})"

# add supports for parenthesis


class UnaryOpNode:
    def __init__(self, operation, node) -> None:
        self.op = operation
        self.node = node

        self.start_pos = self.op.start_pos
        self.end_pos = self.node.end_pos

    def __repr__(self) -> str:
        return f"({self.op}, {self.node})"


# Parse Result
# Instead of returning node we return parser result.Also, It keeps track of errors and nodes


class ParseResult:
    def __init__(self) -> None:
        self.err = None
        self.node = None

    # takes another parse result or node

    def register(self, res):
        # isinstance check if the res object with type ParseResult
        if isinstance(res, ParseResult):
            if res.err:
                self.err = res.err
            return res.node

        return res

    def success(self, node):
        self.node = node
        return self

    def failure(self, err):
        self.err = err
        return self


# Parser
class Parser:
    def __init__(self, tokens) -> None:
        self.toks = tokens
        self.tok_ind = -1
        self.current = None
        self.next()

    def next(self):
        if self.tok_ind < len(self.toks) - 1:
            self.tok_ind += 1
            self.current = self.toks[self.tok_ind]
        # need it for register function
        return self.current

    # Begin The Gram

    def factor(self):
        res = ParseResult()
        tok = self.current

        if tok.type in (MINUS_T, PLUS_T):
            res.register(self.next())
            factor = res.register(self.factor())
            if res.err:
                return res
            return res.success(UnaryOpNode(tok, factor))

        elif tok.type in (INT_T, FLOAT_T):
            res.register(self.next())
            return res.success(NumberNode(tok))

        elif tok.type == LPAREN_T:
            res.register(self.next())
            expr = res.register(self.expr())
            if res.err:
                return res
            if self.current.type == RPAREN_T:
                res.register(self.next())
                return res.success(expr)
            else:
                return res.failure(InvalidSyntaxError(
                    self.current.start_pos, self.current.end_pos,
                    "Expected ' ) '"
                ))

        return res.failure(InvalidSyntaxError(tok.start_pos, tok.end_pos, "Expected Integer Or Float"))

    def bin_op(self, func, ops):
        res = ParseResult()
        left = res.register(func())  # contains first number value
        if res.err:
            return res
        # check for the operation when we finich
        while self.current.type in ops:
            tok_op = self.current
            res.register(self.next())
            right = res.register(func())
            if res.err:
                return res
            # result and the left in the next loop if there is * or /
            left = BinOpNode(left, tok_op, right)

        return res.success(left)

    def term(self):
        return self.bin_op(self.factor, (MULT_T, DIV_T))

    def expr(self):
        return self.bin_op(self.term, (PLUS_T, MINUS_T))

    def parse(self):
        res = self.expr()
        if res.err and self.current.type != EOF_T:
            return res.failure(InvalidSyntaxError(
                self.current.start_pos, self.current.end_pos,
                "Expected ' + ' or ' * ' or ' / ' or ' - '"
            ))

        return res


###################
# Interepter
###################

##################
# Context
#################

# more details on run time error , showing line module, def, file
class Context:
    def __init__(self, display_name, parent=None, parent_pos=None) -> None:
        self.display = display_name
        self.parent = parent
        self.parent_pos = parent_pos


#####################
# RunTime Result
####################


class RTResult():
    # It Is For handling runtimes errors like the  parseResult class.
    def __init__(self) -> None:
        self.err = None
        self.value = None

    def register(self, res):
        if self.err:
            self.err = res.err
        return res.value

    def success(self, value):
        self.value = value
        return self

    def failure(self, error):
        self.err = error
        return self


# Number Value
class Number:
    def __init__(self, value) -> None:
        self.value = value

        self.start_pos = None
        self.end_pos = None

    def set_pos(self, start_pos=None, end_pos=None):
        self.start_pos = start_pos
        self.end_pos = end_pos

        return self

    def set_context(self, context=None):
        self.context = context
        return self

    # Math Function
    def add_to(self, other_num):
        if isinstance(other_num, Number):
            return Number(self.value + other_num.value).set_context(self.context), None

    def sub_by(self, other_num):
        if isinstance(other_num, Number):
            return Number(self.value - other_num.value).set_context(self.context), None

    def mult_to(self, other_num):
        if isinstance(other_num, Number):
            return Number(self.value * other_num.value).set_context(self.context), None

    def div_by(self, other_num):
        if isinstance(other_num, Number):
            if other_num.value == 0:
                return None, RunTimeError(
                    other_num.start_pos, other_num.end_pos,
                    "Division By 0",
                    self.context
                )
            return Number(self.value / other_num.value).set_context(self.context), None

    def __repr__(self) -> str:
        return str(self.value)


class Interepter:
    # Visit Nodes (binopnde , number node , ..)
    def visit(self, node, context):
        node_type = type(node).__name__
        if node_type == "NumberNode":
            return self.visit_number_node(node, context)
        elif node_type == "BinOpNode":
            return self.visit_bin_op_node(node, context)
        elif node_type == "UnaryOpNode":
            return self.visit_unary_op_node(node, context)
        else:
            return self.no_visit(node, context)

    def visit_number_node(self, node, context):
        # print("number")
        res = RTResult()
        num = Number(node.tok.value)
        num.set_context(context)
        num.set_pos(node.start_pos, node.end_pos)
        return res.success(num)

    def visit_bin_op_node(self, node, context):
        # print("bin")
        res = RTResult()
        # visit left and right
        left = res.register(self.visit(node.left, context))
        if res.err:
            return res
        right = res.register(self.visit(node.right, context))
        if res.err:
            return res

        if node.op.type == PLUS_T:
            result, error = left.add_to(right)
        elif node.op.type == MINUS_T:
            result, error = left.sub_by(right)
        elif node.op.type == MULT_T:
            result, error = left.mult_to(right)
        elif node.op.type == DIV_T:
            result, error = left.div_by(right)

        if error:
            return res.failure(error)
        else:
            result.set_pos(node.start_pos, node.end_pos)
            return res.success(result)

    def visit_unary_op_node(self, node, context):
        res = RTResult()
        # visit child node
        num = res.register(self.visit(node.node, context))
        if res.err:
            return res
        if node.op.type == MINUS_T:
            num, error = num.mult_to(Number(-1))
        if error:
            return res.failure(error)
        else:
            num.set_pos(node.start_pos, node.end_pos)
            return res.success(num)

    def no_visit(self, node, context):
        raise Exception(f"No Visit {type(node).__name__} Undedined")

# Run


def run(txt, file_name="<stdin>"):
    lexer = Lexer(txt, file_name)
    tokens, error = lexer.get_tokens()

    if error:
        return None, error

    parser = Parser(tokens)
    # generate Abstract Data Tree
    ast = parser.parse()
    if ast.err:
        return None, ast.err
    # Execute Program
    interepter = Interepter()
    context = Context("<Program>")
    result = interepter.visit(ast.node, context)

    return result.value, result.err
