from enum import Enum

class TokenType(Enum):
    ROOT = 0
    TEXT = 1
    STYLE = 2
    NEWLINE = 3
    END = 4

class Token:
    def __init__(self, type, parent = None):
        self.parent = parent
        self.type = type
        self.children = list()

    def append(self, child):
        child.parent = self
        self.children.append(child)
        return child

    def print_tree(self, depth = 0):
        print('\t' * depth, end='')
        print(self.__repr__())

        for c in self.children:
            c.print_tree(depth + 1)

    def __repr__(self):
        return '[{0}]'.format( TokenType(self.type).name )

    @classmethod
    def depth_first_generator(cls, token):
        yield token
        for c in token.children:
            yield from cls.depth_first_generator(c)

class TextToken(Token):    
    def __init__(self, data = None):
        super().__init__(TokenType.TEXT)
        self.data = data

    def __repr__(self):
        return '{0}[{1}]'.format( super().__repr__(), self.data)


# TODO: remove all _END? and use OPEN/CLOSE flags?
class StyleType(Enum):
    ITALICS_START =       0b00000001
    ITALICS_END =         0b10000001
    BOLD_START =          0b00000010
    BOLD_END =            0b10000010
    UNDERLINE_START =     0b00000011
    UNDERLINE_END =       0b10000011
    FONTNAME_START =      0b00000100
    FONTNAME_END =        0b10000100    
    FONTSIZE_START =      0b00000101
    FONTSIZE_END =        0b10000101
    FONTCOLOR_START =     0b00000110
    FONTCOLOR_END =       0b10000110
    STRIKETHROUGH_START = 0b00000111
    STRIKETHROUGH_END =   0b10000111

# style_data = data that will be used by other formats
# format_data = data that should only be used by current format
class StyleToken(Token):
    def __init__(self, format_class, style_type, style_data = None, format_data = None):
        super().__init__(TokenType.STYLE)
        self.format_class = format_class
        self.style_type = style_type
        self.style_data = style_data
        self.format_data = format_data

    # TODO: better way for closing type, see @StyleType
    def get_closing_token(self):
        return StyleToken(self.format_class, StyleType(self.style_type.value + 0b10000000), self.style_data, self.format_data)

    def __repr__(self):
        return '{0}[{1}, {2}, {3}]'.format( super().__repr__(), StyleType(self.style_type).name, self.style_data, self.format_data)