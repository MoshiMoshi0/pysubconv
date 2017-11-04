from .token import Token, TokenType, TextToken, StyleToken
from ..formats.base import SubtitleFormat

class Tokenizer:
    @classmethod
    def tokenize(cls, cue):
        root = Token(TokenType.ROOT)
        current = root

        lines = cue.text.split('\n')
        for index, line in enumerate(lines):
            while line:
                matches = [(sf, sf.get_first_style_match(line, current)) for sf in SubtitleFormat.__subclasses__()]
                matches = [m for m in matches if m[1] is not None]

                if not matches:
                    current.append(TextToken(line))
                    break

                best_format, best_match = min(matches, key=lambda o: o[1].start())
                if best_match.start() > 0:
                    current.append(TextToken(line[0:best_match.start()]))
                line = line[best_match.end():]

                current = best_format.process_match(best_match, current)

            if index < len(lines) - 1:
                current = cls.process_closing_token(current, TokenType.NEWLINE)

        current = cls.process_closing_token(current, TokenType.END)

        return root

    # TODO: method naming
    @classmethod
    def process_closing_token(cls, current, type):
        token = Token(type)

        last_current = None
        while last_current != current:
            last_current = current

            for sf in SubtitleFormat.__subclasses__():
                # TODO: pass only type not whole token?
                current = sf.process_closing_token(current, token)

            if not current:
                raise Exception('Malformed token tree')

        current.append(token)
        return current
