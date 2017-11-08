import re
from attr import attrs, attrib, Factory

object_re = re.compile(r'(\{([^}]+)})')  # Used for matching objects.
suffix_re = re.compile(r'(%([0-9]*)([a-zA-Z]*))')


class SocialsError(Exception):
    """There was a problem with your social."""


class NoMatchError(SocialsError):
    """No match was found."""


class NoNamesError(SocialsError):
    """No names provided."""


class DuplicateNameError(SocialsError):
    """The same name was used multiple times."""


class NoObjectError(SocialsError):
    """That object is not in the list."""


class NoSuffixError(SocialsError):
    """No such suffix."""


@attrs
class Suffix:
    """A suffix as returned by get_suffixes."""

    func = attrib()
    names = attrib()


@attrs
class SocialsFactory:
    """This factory contains all the supported suffixes as well as the
    get_strings method which generates social strings from them.
    To add a suffix decorate a function with the suffix decorator."""

    suffixes = attrib(default=Factory(dict))
    default_index = attrib(default=Factory(int))
    default_suffix = attrib(default=Factory(lambda: 'n'))

    def suffix(self, *names):
        """Add a suffix accessible by any of names.
        If names is empty NoNamesError will be raised.
        The decorated function should take two arguments: The object the suffix
        will be invoked for, and the text of the suffix. It should return two
        items: The text which is applicable to the matched object, and the text
        which is applicable for everyone else."""
        if not names:
            raise NoNamesError()

        def inner(func):
            """Decorate."""
            for name in names:
                if name in self.suffixes:
                    raise DuplicateNameError(name)
                self.suffixes[name] = func
            return func

        return inner

    def get_strings(self, string, perspectives, **kwargs):
        """Converts a string such as
        %1n smile%1s at %2 with %1his eyes sparkling in the light of %3.
        And returns a list of n+1 items, where n is the number of perspectives
        provided. The list contains one string to be sent to each perspective,
        and an extra one to be sent to every object not listed in the match.

        If no number is provided after the % sign self.default_index is used.
        If no suffix is provided self.default_suffix is assumed.

        By default this means you could provide a single % and get %1n.

        Make the suffixes upper case to have the strings rendered with their
        first letter capitalised.

        If a double percent sign is used (E.G.: "%%") a single per cent sign is
        inserted. This behaviour can of course be modified by passing a percent
        keyword argument.

        All resulting strings are formatted with kwargs as well as the
        formatters generated by this function.
        """
        kwargs.setdefault('percent', '%')
        string = string.replace('%%', '{percent}')
        strings = []  # The strings which will be returned.
        replacements = [[] for p in perspectives]  # Formatter strings.
        default_replacements = []  # The replacements shown to everyone else.

        def match_suffix(match):
            """Match the suffix in the suffixes dictionary."""
            whole, index, suffix = match.groups()
            if index:
                index = int(index) - 1
            else:
                index = self.default_index
            if not suffix:
                suffix = self.default_suffix
            try:
                obj = perspectives[index]
            except IndexError:
                raise NoObjectError(
                    f'{index + 1} is not in the list of objects.'
                )
            func = self.suffixes.get(suffix.lower(), None)
            if func is None:
                raise NoSuffixError(
                    '%s is not a valid suffix. Valid suffixes: %s.' % (
                        suffix,
                        ', '.join(sorted(self.suffixes.keys()))
                    )
                )
            this, other = func(obj, suffix)
            if suffix.isupper():
                this = this.capitalize()
                other = other.capitalize()
            for pos, perspective in enumerate(perspectives):
                if obj is perspective:
                    replacements[pos].append(this)
                else:
                    replacements[pos].append(other)
            default_replacements.append(other)
            return '{}'

        default = re.sub(suffix_re, match_suffix, string)
        for args in replacements:
            strings.append(default.format(*args, **kwargs))
        strings.append(default.format(*default_replacements, **kwargs))
        return strings

    def convert_emote_string(
        self, string, match, perspectives, *args, **kwargs
    ):
        """Convert an emote string like
        % smiles at {john}n
        to
        % smiles at %2n
        Returns (string, perspectives) ready to be fed into get_strings.
        The match function will be used to convert match strings to objects,
        and should return just the object. If it returns None,
        All extra arguments and keyword arguments will be passed after the
        match string.
        The perspectives string will be extended by this function."""

        def repl(m):
            full, match_string = m.groups()
            obj = match(match_string, *args, **kwargs)
            if obj is None:
                raise NoMatchError(match_string)
            if obj not in perspectives:
                perspectives.append(obj)
            return f'%{perspectives.index(obj) + 1}'

        string = re.sub(object_re, repl, string)
        return (string, perspectives)

    def get_suffixes(self):
        """Return a list of suffix objects."""
        d = {}
        for name, func in self.suffixes.items():
            d[func] = d.get(func, [])
            d[func].append(name)
        return [Suffix(func, sorted(names)) for func, names in d.items()]
