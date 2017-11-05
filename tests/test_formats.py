from io import StringIO

from pysubconv.formats.base import Metadata
from pysubconv.formats.srt import SrtFormat
from pysubconv.formats.microdvd import MicroDVDFormat
from pysubconv.formats.mpl2 import MPL2Format

from pysubconv.utils.tokenizer import Tokenizer

metadata = Metadata()
def convert_and_compare(from_format, to_format, text, expected=None):
    cue = list(from_format.parse_cue(StringIO(text), metadata))
    assert cue

    output = StringIO()
    for c in cue:
        c.tree = Tokenizer.tokenize(c)
        to_format.write_cue(c, metadata, output)

    assert output.getvalue() == expected if expected else text
    output.close()

def test_srt_srt():
    with open('tests\\test_files\\srt_sample.txt') as f:
        convert_and_compare(SrtFormat, SrtFormat, f.read())

def test_mpl2_mpl2():
    with open('tests\\test_files\\mpl2_sample.txt') as f:
        convert_and_compare(MPL2Format, MPL2Format, f.read())

def test_mdvd_mvdv():
    with open('tests\\test_files\\mdvd_sample.txt') as f:
        text = f.read()

    with open('tests\\test_files\\mdvd_sample_expected.txt') as f:
        expected = f.read()

    convert_and_compare(MicroDVDFormat, MicroDVDFormat, text, expected)