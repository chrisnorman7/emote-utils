from typing import Any, List, Tuple

from attr import attrs
from pytest import raises

from emote_utils import (NoNamesError, NoObjectError, NoSuffixError,
                         SocialsFactory, Suffix)


def extra_suffix(obj: Any, suffix: str) -> Tuple[str, str]:
    return ('test', 'ing')


@attrs(auto_attribs=True)
class PretendObject:
    """Test emotes with this object."""

    name: str
    gender: str


boy = PretendObject('Bill', 'his')
girl = PretendObject('Jane', 'her')

f: SocialsFactory = SocialsFactory()


@f.suffix('name', 'n')
def name(obj: PretendObject, suffix: str) -> Tuple[str, str]:
    return ('you', obj.name)


@f.suffix('his', 'her')
def gender(obj: PretendObject, suffix: str) -> Tuple[str, str]:
    return ('your', obj.gender)


def test_defaults() -> None:
    assert SocialsFactory().suffixes == {}
    assert f.default_index == 1
    assert f.default_suffix == 'n'


# get_strings tests.

def test_one() -> None:
    expected: List[str] = ['you', boy.name]
    # Try all possible forms.
    strings: List[str]
    strings = f.get_strings('%1n', [boy])
    assert strings == expected
    strings = f.get_strings('%1', [boy])
    assert strings == expected
    strings = f.get_strings('%', [boy])
    assert strings == expected


def test_multiple() -> None:
    expected: List[str] = [
        f'you {girl.name}', f'{boy.name} you', f'{boy.name} {girl.name}'
    ]
    # Try all possible forms.
    strings: List[str]
    strings = f.get_strings('%1n %2n', [boy, girl])
    assert strings == expected
    strings = f.get_strings('%1n %2', [boy, girl])
    assert strings == expected
    strings = f.get_strings('% %2', [boy, girl])
    assert strings == expected


def test_title() -> None:
    strings: List[str] = f.get_strings('%|title smiles.', [boy])
    assert strings == ['You smiles.', 'Bill smiles.']


def test_nameless_suffix() -> None:
    with raises(NoNamesError):
        f.suffix()


def test_suffix_error() -> None:
    with raises(NoSuffixError):
        f.get_strings('%1wontwork', [boy])


def test_object_error() -> None:
    with raises(NoObjectError):
        f.get_strings('%2n', [boy])


def test_get_suffixes() -> None:
    r: List[Suffix] = f.get_suffixes()
    assert len(r) == 2
    assert isinstance(r[0], Suffix)
    assert isinstance(r[1], Suffix)
    assert r[0].func is name
    assert r[0].names == ['n', 'name']
    assert r[1].func is gender
    assert r[1].names == ['her', 'his']
    f.suffix('t', 's')(extra_suffix)
    suffix = f.get_suffixes()[2]
    assert suffix.func is extra_suffix
    assert suffix.names == ['s', 't']


def test_empty_filter_name() -> None:
    expected: List[str] = ['you', boy.name]
    strings: List[str] = f.get_strings('%1n|', [boy])
    assert strings == expected


def test_filter() -> None:
    expected: List[str] = ['YOU', boy.name.upper()]
    strings: List[str] = f.get_strings('%1n|upper', [boy])
    assert strings == expected
