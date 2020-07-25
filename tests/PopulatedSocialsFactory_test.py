from emote_utils import PopulatedSocialsFactory, SocialsFactory

f: SocialsFactory = PopulatedSocialsFactory()
o: object = object()  # Blank object.


def test_s() -> None:
    assert f.get_strings('%1s', [o]) == ['', 's']


def test_e() -> None:
    assert f.get_strings('%1e', [o]) == ['', 'es']


def test_y() -> None:
    assert f.get_strings('%1y', [o]) == ['y', 'ies']


def test_is() -> None:
    assert f.get_strings('%1are', [o]) == ['are', 'is']
    assert f.get_strings('%1is', [o]) == ['are', 'is']


def test_have() -> None:
    assert f.get_strings('%1have', [o]) == ['have', 'has']
    assert f.get_strings('%1has', [o]) == ['have', 'has']
