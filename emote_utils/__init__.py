"""A library for using and manipulating social strings."""

from re import Match, Pattern
from re import compile as re_compile
from re import sub
from typing import Any, Callable, Dict, List, Optional, Tuple, cast

from attr import Factory, attrib, attrs

_object_re: Pattern = re_compile(r'(\{([^}]+)})')  # Used for matching objects.
_suffix_re: Pattern = re_compile(r'(%([0-9]*)([a-zA-Z]*)(?:[|]([a-zA-Z]*))?)')

SuffixFunctionType = Callable[[Any, str], Tuple[str, str]]
FilterFunctionType = Callable[[str], str]

MatchFunctionType = Callable[[str], Optional[Any]]


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


class NoFilterError(SocialsError):
    """No such filter."""


@attrs(auto_attribs=True)
class _SuffixOrFunction:
    """A suffix or filter, as returned by SocialsFactory.get_suffixes or
    SocialsFactory.get_filters."""

    names: List[str] = attrib()


@attrs(auto_attribs=True)
class Suffix(_SuffixOrFunction):
    func: SuffixFunctionType


@attrs(auto_attribs=True)
class Filter(_SuffixOrFunction):
    func: FilterFunctionType


@attrs(auto_attribs=True)
class SocialsFactory:
    """This factory contains all the supported suffixes as well as the
    get_strings method which generates social strings from them.
    To add a suffix decorate a function with the suffix decorator."""

    # The possible suffixes.
    # Added with the suffix decorator.
    suffixes: Dict[str, SuffixFunctionType] = Factory(dict)

    # The possible filters.
    # Added with the filter decorator.
    filters: Dict[str, FilterFunctionType] = Factory(dict)

    # The index to use if none follows the % sign.
    default_index: int = Factory(lambda: 1)

    # The suffix to use if none is provided.
    default_suffix: str = Factory(lambda: 'n')

    # The name of a filter to apply if a suffix name is all in lower case.
    lower_case_filter: Optional[str] = Factory(lambda: None)

    # The name of the filter to use if a suffix name is all in title case.
    title_case_filter: str = Factory(lambda: 'normal')

    # The name of the filter to use if a suffix name is all in upper case.
    upper_case_filter: str = Factory(lambda: 'upper')

    # The regular expression to use to match suffixes.
    suffix_re: Pattern = attrib(default=Factory(lambda: _suffix_re))

    # The regular expression to use to match object references in emote
    # strings.
    emote_re: Pattern = Factory(lambda: _object_re)

    def __attrs_post_init__(self) -> None:
        for name in ('normal', 'title', 'upper', 'lower'):
            self.filters[name] = getattr(self, name)

    def normal(self, value: str) -> str:
        """Capitalise the first letter of value."""
        if value:
            return value[0].upper() + value[1:]
        else:
            return ''

    def title(self, value: str) -> str:
        """Return value in title case."""
        return value.title()

    def upper(self, value: str) -> str:
        """Return value in upper case."""
        return value.upper()

    def lower(self, value: str) -> str:
        """Return value in lower case."""
        return value.lower()

    def suffix(self, *names) -> Callable[
        [SuffixFunctionType], SuffixFunctionType
    ]:
        """Add a suffix accessible by any of names.
        If names is empty NoNamesError will be raised.
        The decorated function should take two arguments: The object the suffix
        will be invoked for, and the text of the suffix. It should return two
        items: The text which is applicable to the matched object, and the text
        which is applicable for everyone else."""
        if not names:
            raise NoNamesError()

        def inner(func: SuffixFunctionType) -> SuffixFunctionType:
            """Decorate."""
            for name in names:
                if name in self.suffixes:
                    raise DuplicateNameError(name)
                self.suffixes[name] = func
            return func

        return inner

    def filter(self, *names) -> Callable[
        [FilterFunctionType], FilterFunctionType
    ]:
        """Decorate a function to be used as a filter."""
        if not names:
            raise NoNamesError()

        def inner(func: FilterFunctionType) -> FilterFunctionType:
            name: str
            for name in names:
                self.filters[name] = func
            return func

        return inner

    def suffix_repl(
        self, perspectives: List[Any], replacements: List[List[str]],
        match: Match
    ) -> str:
        """Match the suffix in the suffixes dictionary.

        Used by get_suffix.

        This method should return a string suitable for sending to everyone not
        in a perspectives list."""
        whole: str
        index_string: str
        suffix_name: str
        filter_name: Optional[str]
        whole, index_string, suffix_name, filter_name = match.groups()
        index: int
        if index_string:
            index = int(index_string) - 1
        else:
            index = self.default_index - 1
        if not suffix_name:
            suffix_name = self.default_suffix
        obj: Any
        try:
            obj = perspectives[index]
        except IndexError:
            obj = self.no_object(index)  # May raise.
        suffix_func: Optional[SuffixFunctionType] = self.suffixes.get(
            suffix_name.lower(), None
        )
        if suffix_func is None:
            suffix_func = self.no_suffix(obj, suffix_name)  # May raise.
        this: str
        other: str
        this, other = cast(SuffixFunctionType, suffix_func)(obj, suffix_name)
        if not filter_name:
            if suffix_name.istitle():
                filter_name = self.title_case_filter
            elif suffix_name.isupper():
                filter_name = self.upper_case_filter
            else:
                filter_name = self.lower_case_filter
        if filter_name:
            filter_func: Optional[FilterFunctionType] = self.filters.get(
                filter_name, None
            )
            if filter_func is None:
                filter_func = self.no_filter(
                    obj, filter_name
                )  # May raise.
            filter_func = cast(FilterFunctionType, filter_func)
            this = filter_func(this)
            other = filter_func(other)
        pos: int
        perspective: Any
        for pos, perspective in enumerate(perspectives):
            if perspective is obj:
                replacements[pos].append(this)
            else:
                replacements[pos].append(other)
        replacements[-1].append(other)
        return '{}'

    def get_strings(
        self, string: str, perspectives: List[Any], **kwargs
    ) -> List[str]:
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
        # The strings to be returned:
        strings: List[str] = []
        # Formatter strings:
        replacements: List[List[str]] = [[] for p in perspectives]
        replacements.append([])  # Default replacements.
        default: str = sub(
            self.suffix_re, lambda m: self.suffix_repl(
                perspectives, replacements, m
            ), string
        )
        for args in replacements:
            strings.append(default.format(*args, **kwargs))
        return strings

    def no_object(self, index: int) -> Optional[Any]:
        """No object was found at the given index. By this point index will be
        0-based. Should return either an object or raise an instance of
        NoObjectError."""
        raise NoObjectError(
            f'{index + 1} is not in the list of objects.'
        )

    def no_suffix(self, obj, name: str) -> Optional[SuffixFunctionType]:
        """No suffix was found for obj with the given name. Should either
        return a function to be used as the suffix or raise an instance of
        NoSuffixError."""
        raise NoSuffixError(
            '%s is not a valid suffix. Valid suffixes: %s.' % (
                name, ', '.join(sorted(self.suffixes.keys()))
            )
        )

    def no_filter(self, obj: Any, name: str) -> Optional[FilterFunctionType]:
        """No filter found by that name. Should either return a filter function
        or raise an instance of NoFilterError."""
        raise NoFilterError(f'Invalid filter: {name}.')

    def no_match(self, name: str) -> Optional[Any]:
        """No object was found matching that name. Should either return an
        object or raise an instance of NoMatchError."""
        raise NoMatchError(name)

    def emote_repl(
        self, match_func: MatchFunctionType, perspectives: List[Any],
        match: Match
    ) -> str:
        """Used by convert_emote_string."""
        full: str
        match_string: str
        full, match_string = match.groups()
        obj: Optional[Any] = match_func(match_string)
        if obj is None:
            # This next call may raise something. Let it go.
            obj = self.no_match(match_string)
        if obj not in perspectives:
            perspectives.append(obj)
        return f'%{perspectives.index(obj) + 1}'

    def convert_emote_string(
        self, string: str, match: MatchFunctionType, perspectives: List[Any]
    ) -> Tuple[str, List[Any]]:
        """Convert an emote string like
        % smile%1s at {john}n
        to
        % smile%1s at %2n
        Returns (string, perspectives) ready to be fed into get_strings.

        The match function will be used to convert match strings to objects,
        and should return just the object. If it returns None, self.no_match
        will be called with the same set of arguments.
        All extra arguments and keyword arguments will be passed to the match
        function after the match string.
        The perspectives string will be extended by this function."""
        string = sub(
            self.emote_re, lambda m: self.emote_repl(match, perspectives, m),
            string
        )
        return (string, perspectives)

    def get_suffixes(self) -> List[Suffix]:
        """Return a list of Suffix instances."""
        d: Dict[int, Suffix] = {}
        name: str
        func: SuffixFunctionType
        for name, func in self.suffixes.items():
            i: int = id(func)
            s: Suffix = d.get(i, Suffix([], func))
            s.names.append(name)
            s.names = sorted(s.names)
            d[i] = s
        return list(d.values())

    def get_filters(self) -> List[Filter]:
        """Return all filters as a dictionary."""
        d: Dict[int, Filter] = {}
        name: str
        func: FilterFunctionType
        for name, func in self.filters.items():
            i: int = id(func)
            f: Filter = d.get(i, Filter([], func))
            f.names.append(name)
            f.names = sorted(f.names)
            d[i] = f
        return list(d.values())


class PopulatedSocialsFactory(SocialsFactory):
    """A SocialsFactory instance with some useful suffixes applied."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.suffix('s')(self.get_s)
        self.suffix('e', 'es')(self.get_es)
        self.suffix('y', 'ies')(self.get_y)
        self.suffix('are', 'is')(self.get_are)
        self.suffix('have', 'has')(self.get_have)

    def get_s(self, obj: Any, suffix: str) -> Tuple[str, str]:
        """"" or "s"."""
        return '', 's'

    def get_es(self, obj: Any, suffix: str) -> Tuple[str, str]:
        """"" or "es"."""
        return '', 'es'

    def get_y(self, obj: Any, suffix: str) -> Tuple[str, str]:
        """"y" or "ies"."""
        return 'y', 'ies'

    def get_are(self, obj: Any, suffix: str) -> Tuple[str, str]:
        """"are" or "is"."""
        return ('are', 'is')

    def get_have(self, obj: Any, suffix: str) -> Tuple[str, str]:
        """"have" or "has"."""
        return ('have', 'has')
