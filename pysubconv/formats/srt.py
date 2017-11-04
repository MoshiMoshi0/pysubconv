from .base import SubtitleFormat, Cue
from enum import Enum
from datetime import timedelta
from ..utils.token import StyleToken, StyleType, TokenType, Token

import regex as re

class SrtFormat(SubtitleFormat):
    style_start_re = re.compile(r'[<{](?P<stype>[biu])[>}]')
    style_end_re = re.compile(r'[<{]\/(?P<stype>[biu])[>}]')
    font_start_re = re.compile(r'(?(DEFINE)(?P<fstyle> *(?P<ftype>face|color|size)=\"(?P<fdata>.*?)\" *))<font (?&fstyle)*>')
    font_end_re = re.compile(r'<\/font>')

    @classmethod
    def parse_cue(cls, stream, metadata):
        index_re = re.compile(r'^(?P<index>\d+)$')
        timing_re = re.compile(r'(?P<hour>\d{1,2}):(?P<minute>\d{1,2}):(?P<second>\d{1,2}),(?P<millisecond>\d{3})')

        class StateType(Enum):
            INDEX = 1
            TIMINGS = 2
            TEXT = 3

        state = StateType.INDEX

        # TODO: unnecessary line strips?
        text = ''
        index = start_time = end_time = None
        for line in stream:
            line = line.strip()

            if not line:
                if state == StateType.TEXT:
                    yield Cue(index, start_time, end_time, text.strip())
                    text = ''
                    start_time = end_time = None
                    state = StateType.INDEX
                continue

            if state == StateType.INDEX:
                match = index_re.match(line)

                if not match:
                    raise Exception('Invalid index: {0}'.format(line))

                index = int(match.group('index'))

                state = StateType.TIMINGS
            elif state == StateType.TIMINGS:
                # TODO: add subrip text position support 
                if '-->' not in line:
                    raise Exception('Invalid timing format: {0}'.format(line))

                timings = line.split('-->')
                if len(timings) != 2:
                    raise Exception('Invalid timing format: {0}'.format(line))

                start_match = timing_re.match(timings[0].strip())
                end_match = timing_re.match(timings[1].strip())

                if not start_match or not end_match:
                    raise Exception('Invalid timing format: {0}'.format(line))

                start_time = timedelta(hours=int(start_match.group('hour')),
                                       minutes=int(start_match.group('minute')),
                                       seconds=int(start_match.group('second')),
                                       milliseconds=int(start_match.group('millisecond')))
                end_time =   timedelta(hours=int(end_match.group('hour')),
                                       minutes=int(end_match.group('minute')),
                                       seconds=int(end_match.group('second')),
                                       milliseconds=int(end_match.group('millisecond')))

                state = StateType.TEXT
            elif state == StateType.TEXT:
                text += line + '\n'

        if index and start_time and end_time and text.strip():
            yield Cue(index, start_time, end_time, text.strip())

    @staticmethod
    def format_time(time):
        s = time.total_seconds()
        return '{:02}:{:02}:{:02},{:03}'.format(int(s // 3600), int(s % 3600 // 60), int(s % 60), int(time.microseconds / 1000))

    @classmethod
    def write_cue(cls, cue, metadata, out):
        out.write(str(cue.index) + '\n')
        out.write('{0} --> {1}'.format(cls.format_time(cue.start), cls.format_time(cue.end)) + '\n')
        cls.write_tokens(Token.depth_first_generator(cue.tree), out)
        out.write('\n\n')

    @classmethod
    def get_first_style_match(cls, text, current):
        style_res = [cls.style_start_re, cls.style_end_re, cls.font_start_re, cls.font_end_re]
        matches = list(filter(None, [re.search(r, text) for r in style_res]))
        if not matches:
            return None
        return min(matches, key=lambda o: o.start())

    @classmethod
    def process_match(cls, match, current):
        if match.re == cls.style_start_re:
            stype_g = match.group('stype')

            if stype_g == 'i':
                new_type = StyleType.ITALICS_START
            elif stype_g == 'b':
                new_type = StyleType.BOLD_START
            elif stype_g == 'u':
                new_type = StyleType.UNDERLINE_START

            if not new_type:
                raise Exception('Unsupported style')

            return current.append(StyleToken(cls, new_type))
        elif match.re == cls.style_end_re:
            stype_g = match.group('stype')

            if stype_g == 'i':
                new_type = StyleType.ITALICS_END
            elif stype_g == 'b':
                new_type = StyleType.BOLD_END
            elif stype_g == 'u':
                new_type = StyleType.UNDERLINE_END

            current.parent.append(StyleToken(cls, new_type))
            return current.parent
        elif match.re == cls.font_start_re:
            ftype_c = match.captures('ftype')
            fdata_c = match.captures('fdata')

            while ftype_c and fdata_c:
                ftype = ftype_c.pop()
                fdata = fdata_c.pop()

                if ftype == 'face':
                    new_type = StyleType.FONTNAME_START
                elif ftype == 'color':
                    new_type = StyleType.FONTCOLOR_START
                    color_re = re.compile(r'#([0-9a-fA-F]{2})([0-9a-fA-F]{2})([0-9a-fA-F]{2})')
                    match = color_re.match(fdata)

                    if not match:
                        raise Exception()

                    fdata = (int(match.group(1), 16), int(match.group(2), 16), int(match.group(3), 16))
                elif ftype == 'size':
                    new_type = StyleType.FONTSIZE_START
                else:
                    raise Exception()

                current = current.append(StyleToken(cls, new_type, fdata))

            return current
        elif match.re == cls.font_end_re:
            while isinstance(current, StyleToken) and current.format_class == cls:
                if current.style_type == StyleType.FONTNAME_START:
                    new_type = StyleType.FONTNAME_END
                elif current.style_type == StyleType.FONTCOLOR_START:
                    new_type = StyleType.FONTCOLOR_END
                elif current.style_type == StyleType.FONTSIZE_START:
                    new_type = StyleType.FONTSIZE_END
                else:
                    break

                current.parent.append(StyleToken(cls, new_type))
                current = current.parent
            return current

        raise Exception('Could not create token')

    @classmethod
    def write_tokens(cls, token_stream, out):
        for token in token_stream:
            if token.type == TokenType.TEXT:
                out.write(token.data)
            elif token.type == TokenType.NEWLINE:
                out.write('\n')
            elif token.type == TokenType.STYLE:
                if token.style_type == StyleType.ITALICS_START:
                    out.write('<i>')
                elif token.style_type == StyleType.ITALICS_END:
                    out.write('</i>')
                elif token.style_type == StyleType.BOLD_START:
                    out.write('<b>')
                elif token.style_type == StyleType.BOLD_END:
                    out.write('</b>')
                elif token.style_type == StyleType.UNDERLINE_START:
                    out.write('<u>')
                elif token.style_type == StyleType.UNDERLINE_END:
                    out.write('</u>')
                elif token.style_type == StyleType.FONTNAME_START:
                    out.write('<font face="{0}">'.format(token.style_data))
                elif token.style_type == StyleType.FONTNAME_END:
                    out.write('</font>')
                elif token.style_type == StyleType.FONTSIZE_START:
                    out.write('<font size="{0}">'.format(token.style_data))
                elif token.style_type == StyleType.FONTSIZE_END:
                    out.write('</font>')
                elif token.style_type == StyleType.FONTCOLOR_START:
                    out.write('<font color="#{0}">'.format(''.join(['%02X' % x for x in token.style_data])))
                elif token.style_type == StyleType.FONTCOLOR_END:
                    out.write('</font>')
