from .base import SubtitleFormat, Cue
from enum import Enum
from datetime import timedelta
from ..utils.token import StyleToken, StyleType, TokenType, Token

import regex as re

class MPL2Format(SubtitleFormat):
    style_re = re.compile(r'^/')

    @classmethod
    def parse_cue(cls, stream, metadata):
        cue_re = re.compile(r'^\[(?P<start_time>\d+)\]\[(?P<end_time>\d+)\](?P<text>.*)$')

        index = 0
        for line in stream:
            index += 1
            line = line.strip()

            match = cue_re.match(line)
            if not match:
                raise Exception('Invalid line format: {0}'.format(line))

            start_time = timedelta(seconds=int(match.group('start_time')) * 0.1)
            end_time = timedelta(seconds=int(match.group('end_time')) * 0.1)
            text = match.group('text')

            yield Cue(index, start_time, end_time, '\n'.join(text.split('|')))

    @classmethod
    def write_cue(cls, cue, metadata, out):
        time_start = int(cue.start.total_seconds() * 10)
        time_end = int(cue.end.total_seconds() * 10)
        out.write('[{0}][{1}]'.format(time_start, time_end))
        cls.write_tokens(Token.depth_first_generator(cue.tree), out)
        out.write('\n')

    @classmethod
    def get_first_style_match(cls, text, current):
        if current.type != TokenType.ROOT:
            return None

        s = re.search(cls.style_re, text)
        if not s or s.start() > 0:
            return None
        return s

    @classmethod
    def process_match(cls, match, current):
        if match.re == cls.style_re:
            current = current.append(StyleToken(cls, StyleType.ITALICS_START))
            return current

        raise Exception('Could not create token')

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
                if token.style_type == StyleType.ITALICS_START:
                    out.write('/')

    @classmethod
    def process_closing_token(cls, current, token):
        if not isinstance(current, StyleToken):
            return current
        if not current.format_class == cls:
            return current

        if token.type == TokenType.NEWLINE or token.type == TokenType.END:
            close_token = current.get_closing_token()
            current = current.parent
            current.append(close_token)

        return current
