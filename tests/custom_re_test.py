import re
from emote_utils import SocialsFactory

girl = object()
boy = object()
object_re = re.compile(r'(\[([^]]+)])')  # Used for matching objects.
suffix_re = re.compile(r'(\^([0-9]*)([a-zA-Z]*)(?:[|]([a-zA-Z]*))?)')


def match(name):
    if name == 'girl':
        return girl
    elif name == 'boy':
        return boy


f = SocialsFactory(object_re=object_re, suffix_re=suffix_re)


@f.suffix('t', 'test', 'tests')
def suffix(obj, suffix):
    return 'test', 'tests'


def test_suffix():
    assert f.get_strings('^1t', [boy]) == ['test', 'tests']


def test_object():
    assert f.convert_emote_string('[girl]t', match, [girl]) == (
        '%1t', [girl]
    )
