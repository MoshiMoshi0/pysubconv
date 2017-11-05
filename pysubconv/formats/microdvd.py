from .base import SubtitleFormat, Cue
from enum import Enum
from datetime import timedelta
from ..utils.token import StyleToken, StyleType, TokenType, Token

import regex as re

class MicroDVDFormat(SubtitleFormat):
    style_re = re.compile(r'{(?P<type>[yYcCfFsS]):(?P<data>.*?)}')

    class StyleRange(Enum):
        ONE_LINE = 1
        ALL = 2

    @classmethod
    def parse_cue(cls, stream, metadata):
        cue_re = re.compile(r'^{(?P<start_frame>\d+)}{(?P<end_frame>\d+)}(?P<text>.*)$')

        index = 0
        for line in stream:
            index += 1
            line = line.strip()

            match = cue_re.match(line)
            if not match:
                raise Exception()

            start_time = timedelta(seconds=int(match.group('start_frame')) / metadata.fps)
            end_time = timedelta(seconds=int(match.group('end_frame')) / metadata.fps)
            text = match.group('text')

            yield Cue(index, start_time, end_time, '\n'.join(text.split('|')))

    @classmethod
    def write_cue(cls, cue, metadata, out):
        frame_start = str(int(round(cue.start.total_seconds() * metadata.fps)))
        frame_end = str(int(round(cue.end.total_seconds() * metadata.fps)))
        out.write('{' + frame_start + '}{' + frame_end + '}')
        cls.write_tokens(Token.depth_first_generator(cue.tree), out)
        out.write('\n')

    @classmethod
    def get_first_style_match(cls, text, current):
        return re.search(cls.style_re, text) or None

    @classmethod
    def process_match(cls, match, current):
        type_g = match.group('type')
        data_g = match.group('data')

        srange = cls.StyleRange.ALL if type_g.isupper() else cls.StyleRange.ONE_LINE
        if type_g == 'y' or type_g == 'Y':
            for x in data_g.split(','):
                if x == 'i':
                    new_token = StyleType.ITALICS_START
                elif x == 'b':
                    new_token = StyleType.BOLD_START
                elif x == 'u':
                    new_token = StyleType.UNDERLINE_START
                elif x == 's':
                    new_token = StyleType.STRIKETHROUGH_START

                current = current.append(StyleToken(cls, new_token, format_data=srange))
            return current
        elif type_g == 'c' or type_g == 'C':
            return current.append(StyleToken(cls, StyleType.FONTCOLOR_START, cls.parse_color(data_g), srange))
        elif type_g == 'f' or type_g == 'F':
            return current.append(StyleToken(cls, StyleType.FONTNAME_START, data_g, srange))
        elif type_g == 's' or type_g == 'S':
            return current.append(StyleToken(cls, StyleType.FONTSIZE_START, data_g, srange))

        raise Exception('Could not create token')

    @staticmethod
    def parse_color(text):
        color_re = re.compile(r'[#$]([0-9a-fA-F]{2})([0-9a-fA-F]{2})([0-9a-fA-F]{2})')
        match = color_re.match(text)

        if not match:
            raise Exception()

        # TODO: use 'Color' class not a tuple?
        if text.startswith('$'):
            return (int(match.group(3), 16), int(match.group(2), 16), int(match.group(1), 16))
        elif text.startswith('#'):
            return (int(match.group(1), 16), int(match.group(2), 16), int(match.group(3), 16))

    @classmethod
    def write_tokens(cls, token_stream, out):
        can_write_style = True
        for token in token_stream:
            if token.type == TokenType.TEXT:
                out.write(token.data)
                can_write_style = False
            elif token.type == TokenType.NEWLINE:
                out.write('|')
                can_write_style = True
            elif can_write_style and token.type == TokenType.STYLE:
                is_multi = token.format_data == cls.StyleRange.ALL
                if token.style_type == StyleType.ITALICS_START:
                    out.write('{' + ('Y' if is_multi else 'y') + ':i}')
                elif token.style_type == StyleType.BOLD_START:
                    out.write('{' + ('Y' if is_multi else 'y') + ':b}')
                elif token.style_type == StyleType.UNDERLINE_START:
                    out.write('{' + ('Y' if is_multi else 'y') + ':u}')
                elif token.style_type == StyleType.STRIKETHROUGH_START:
                    out.write('{' + ('Y' if is_multi else 'y') + ':s}')
                elif token.style_type == StyleType.FONTNAME_START:
                    out.write('{' + ('F' if is_multi else 'f') + ':' + token.style_data + '}')
                elif token.style_type == StyleType.FONTSIZE_START:
                    out.write('{' + ('S' if is_multi else 's') + ':' + str(token.style_data) + '}')
                elif token.style_type == StyleType.FONTCOLOR_START:
                    out.write('{' + ('C' if is_multi else 'c') + ':$' + ''.join(['%02X' % x for x in token.style_data[::-1]]) + '}')

    @classmethod
    def process_closing_token(cls, current, token):
        if not isinstance(current, StyleToken):
            return current
        if not current.format_class == cls:
            return current

        a = current.format_data == cls.StyleRange.ONE_LINE and token.type in [TokenType.NEWLINE, TokenType.END]
        b = current.format_data == cls.StyleRange.ALL and token.type == TokenType.END
        if a or b:
            close_token = current.get_closing_token()
            current = current.parent
            current.append(close_token)

        return current
