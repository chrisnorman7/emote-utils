from emote_utils import PopulatedSocialsFactory

f = PopulatedSocialsFactory()
o = object()  # Blank object.


def test_s():
    assert f.get_strings('%1s', [o]) == ['', 's']


def test_e():
    assert f.get_strings('%1e', [o]) == ['', 'es']


def test_y():
    assert f.get_strings('%1y', [o]) == ['y', 'ies']


def test_is():
    assert f.get_strings('%1are', [o]) == ['are', 'is']
