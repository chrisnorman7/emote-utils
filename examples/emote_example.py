"""This example shows you how you could implement emotes in your own
applications."""

from typing import Dict, List, Optional
from attr import attrs
from emote_utils import PopulatedSocialsFactory

# All created instances.
instances: Dict[str, 'PretendObject'] = {}

# The socials factory to use.
f: PopulatedSocialsFactory = PopulatedSocialsFactory()


@f.suffix('name', 'n')
def get_name(obj: 'PretendObject', suffix: str):
    return ('you', obj.name)


@attrs(auto_attribs=True)
class PretendObject:
    """The object that should be able to emote."""

    # The name of this instance.
    name: str

    def __attrs_post_init__(self) -> None:
        instances[self.name] = self

    def do_match(self, string: str) -> Optional['PretendObject']:
        """Match another instance."""
        if string == 'me':
            return self
        string = string.lower()
        name: str
        value: 'PretendObject'
        for name, value in instances.items():
            if value.name.lower() == string:
                return value
        return None

    def message(self, string: str) -> None:
        """Show a message to this object."""
        print(f'[{self.name}]: {string}')

    def do_emote(self, string: str) -> None:
        """Perform an emote as this object."""
        perspectives: List[PretendObject] = [self]
        string, perspectives = f.convert_emote_string(
            string, self.do_match, perspectives
        )
        return self.do_social(string, perspectives)

    def do_social(
        self, string: str, perspectives: List['PretendObject']
    ) -> None:
        """Have this object perform a social. Can be used by do_emote."""
        print(f'Social string: {string}')
        strings: List[str] = f.get_strings(string, perspectives)
        obj: 'PretendObject'
        for obj in instances.values():
            if obj in perspectives:
                obj.message(strings[perspectives.index(obj)])
            else:
                obj.message(strings[-1])


if __name__ == '__main__':
    bill: PretendObject = PretendObject('Bill')
    jane: PretendObject = PretendObject('Jane')
    alex: PretendObject = PretendObject('Alice')
    emote_string: str = '% smile%1s at {jane}.'
    print(f'Emote string: {emote_string}')
    bill.do_emote(emote_string)
