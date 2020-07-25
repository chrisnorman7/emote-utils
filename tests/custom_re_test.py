import re

from emote_utils import SocialsFactory

girl = object()
boy = object()

emote_re = re.compile(r'(\[([^]]+)])')  # Used for matching objects.
suffix_re = re.compile(r'(\^([0-9]*)([a-zA-Z]*)(?:[|]([a-zA-Z]*))?)')


def match(name: str) -> object:
    if name == 'girl':
        return girl
    elif name == 'boy':
        return boy


f: SocialsFactory = SocialsFactory(emote_re=emote_re, suffix_re=suffix_re)


@f.suffix('t', 'test', 'tests')
def suffix(obj, suffix):
    return 'test', 'tests'


def test_suffix() -> None:
    assert f.get_strings('^1t', [boy]) == ['test', 'tests']


def test_emote() -> None:
    assert f.convert_emote_string('[girl]t', match, [girl]) == (
        '%1t', [girl]
    )
