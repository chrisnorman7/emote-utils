from typing import List, Optional

from pytest import raises

from emote_utils import NoMatchError, SocialsFactory

f: SocialsFactory = SocialsFactory()

boy: object = object()
girl: object = object()


# convert_emote_string tests


def match(name: str) -> Optional[object]:
    if name == 'boy':
        return boy
    elif name == 'girl':
        return girl
    else:
        return None


def test_works() -> None:
    string: str
    perspectives: List[object] = [boy]
    string, perspectives = f.convert_emote_string(
        '% looks at {girl}.', match, perspectives
    )
    assert perspectives == [boy, girl]
    assert string == '% looks at %2.'


def test_fails() -> None:
    with raises(NoMatchError):
        f.convert_emote_string('% smiles at {jack}.', match, [boy])
