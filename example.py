"""Provides a basic example of how the library can be used."""

from typing import List, Tuple
from attr import attrs
from emote_utils import PopulatedSocialsFactory


@attrs(auto_attribs=True)
class PretendObject:
    """An object with a name."""

    name: str
    pronoun: str


f: PopulatedSocialsFactory = PopulatedSocialsFactory()


@f.suffix('name', 'n')
def get_name(obj: PretendObject, suffix: str) -> Tuple[str, str]:
    """Get the name of the object."""
    return ('you', obj.name)


bill = PretendObject('Bill', 'his')
jane = PretendObject('Jane', 'her')


def main() -> None:
    strings: List[str] = f.get_strings('%1N smile%1s at %2n.', [bill, jane])
    print(f'Bill sees: {strings[0]}')
    print(f'Jane sees: {strings[1]}')
    print(f'Everyone else sees: {strings[-1]}')


if __name__ == '__main__':
    main()
