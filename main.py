import traceback
from sys import stdout

from pysubconv.utils.tokenizer import Tokenizer
from pysubconv.formats.base import SubtitleFormat, Metadata, Cue

from pysubconv.formats.microdvd import MicroDVDFormat
from pysubconv.formats.mpl2 import MPL2Format
from pysubconv.formats.srt import SrtFormat

# TODO: cli support
metadata = Metadata()
names = ['srt_sample.txt', 'mdvd_sample.txt', 'mpl2_sample.txt', 'mdvd_sample_mix.txt', 'srt_sample_mix.txt']
for n in names:
    with open('tests\\test_files\\' + n, encoding='utf-8') as f:
        for sf in SubtitleFormat.__subclasses__():
            try:
                cue = list(sf.parse_cue(f, metadata))
                if cue:
                    break
            except Exception as e:
                #traceback.print_exc()
                pass

            f.seek(0, 0)
    print('======================================================')
    print(n)
    print('------------------------------------------------------')

    with open('tests\\test_files\\' + n, encoding='utf-8') as f:
        print(f.read())

    print('------------------------------------------------------')
    for c in cue:
        root = Tokenizer.tokenize(c)
        c.tree = root
        c.tree.print_tree()

    print('======================================================')
    for sf in SubtitleFormat.__subclasses__():
        for c in cue:
            sf.write_cue(c, metadata, stdout)
        print('------------------------------------------------------')
