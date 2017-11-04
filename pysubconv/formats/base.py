# TODO: refactor to parser and writer class? 
class SubtitleFormat():    
    @classmethod
    def parse_cue(cls, stream, metadata):
        raise NotImplementedError

    @classmethod
    def write_cue(cls, cue, metadata, out):
        raise NotImplementedError

    @classmethod
    def get_first_style_match(cls, text, current):
        raise NotImplementedError

    @classmethod
    def process_match(cls, match, current):
        raise NotImplementedError

    @classmethod
    def write_tokens(cls, token_stream, out):
        raise NotImplementedError

    @classmethod
    def process_closing_token(cls, current, token):
        return current

class Metadata:
    def __init__(self):
        self.fps = 23.976

# TODO: refactor 'tree'?
class Cue:
    def __init__(self, index, start, end, text):
        self.index = index
        self.start = start
        self.end = end
        self.text = text
        self.tree = None