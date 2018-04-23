import re
from attr import attrs, attrib, Factory

__all__ = [
    'SocialsError', 'object_re', 'suffix_re', 'NoMatchError', 'NoNamesError',
    'DuplicateNameError', 'NoObjectError', 'NoSuffixError', 'NoFilterError',
    'Suffix', 'SocialsFactory', 'PopulatedSocialsFactory', 'SocialsRepl'
]

object_re = re.compile(r'(\{([^}]+)})')  # Used for matching objects.
suffix_re = re.compile(r'(%([0-9]*)([a-zA-Z]*)(?:[|]([a-zA-Z]*))?)')


@attrs
class _ReplBase:
    """Subclassed by SocialsRepl and EmoteRepl."""

    factory = attrib()
    perspectives = attrib()


@attrs
class EmoteRepl(_ReplBase):
    """
    Subclass this class to alter the functionality of the match code of
    SocialsFactory.convert_emote_string then pass the new instance as the
    emote_class keyword argument to SocialsFactory.__init__.

    The factory attribute will be the instance of SocialsFactory that
    convert_emote_string is being called on.
    The perspectives attribute will be the list of objects that
    convert_emote_string will be using.
    The match attribute will be the function that the repl method should use to
    get objects from match strings.
    The match_args attribute should be passed after match_string to the match
    function.
    match_kwargs should be passed as keyword arguments to the match function.

    By default before re.sub is called from
    SocialsFactory.convert_emote_string, an instance of the supplied class is
    created with the factory, the list of objects, the match function, extra
    match args, and extra match kwargs as positional arguments.
    """

    match = attrib()
    match_args = attrib()
    match_kwargs = attrib()

    def repl(self, match):
        full, match_string = match.groups()
        obj = self.match(match_string, *self.match_args, **self.match_kwargs)
        if obj is None:
            obj = self.factory.no_match(
                match_string, *self.match_args, **self.match_kwargs
            )  # May raise.
        if obj not in self.perspectives:
            self.perspectives.append(obj)
        return f'%{self.perspectives.index(obj) + 1}'


@attrs
class SocialsRepl(_ReplBase):
    """
    Subclass this class to alter the functionality of the match code of
    SocialsFactory.get_strings then pass the new instance as the repl_class
    keyword argument to SocialsFactory.__init__.

    The factory argument will be the instance of SocialsFactory that
    get_strings is being called on.
    The perspectives argument will be the list of objects that get_strings will
    be using.

    By default before re.sub is called from SocialsFactory.get_strings, an
    instance of the supplied class is created with the factory, the list of
    objects, and a blank list of replacements with a length 1 greater than that
    of the list of objects as positional arguments.
    """

    replacements = attrib()

    def repl(self, match):
        """Match the suffix in the suffixes dictionary."""
        whole, index, suffix, filter_name = match.groups()
        if index:
            index = int(index) - 1
        else:
            index = self.factory.default_index
        if not suffix:
            suffix = self.factory.default_suffix
        try:
            obj = self.perspectives[index]
        except IndexError:
            obj = self.factory.no_object(index)  # May raise.
        func = self.factory.suffixes.get(suffix.lower(), None)
        if func is None:
            func = self.factory.no_suffix(obj, suffix)  # May raise.
        this, other = func(obj, suffix)
        if not filter_name:
            if suffix.istitle():
                filter_name = self.factory.title_case_filter
            elif suffix.isupper():
                filter_name = self.factory.upper_case_filter
            else:
                filter_name = self.factory.lower_case_filter
        if filter_name:
            filter_func = self.factory.filters.get(filter_name, None)
            if filter_func is None:
                filter_func = self.factory.no_filter(
                    obj, filter_name
                )  # May raise.
            this = filter_func(this)
            other = filter_func(other)
        for pos, perspective in enumerate(self.perspectives):
            if obj is perspective:
                self.replacements[pos].append(this)
            else:
                self.replacements[pos].append(other)
        self.replacements[-1].append(other)
        return '{}'


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
    filters = attrib(default=Factory(dict))
    default_index = attrib(default=Factory(int))
    default_suffix = attrib(default=Factory(lambda: 'n'))
    lower_case_filter = attrib(default=Factory(lambda: None))
    title_case_filter = attrib(default=Factory(lambda: 'normal'))
    upper_case_filter = attrib(default=Factory(lambda: 'upper'))
    repl_class = attrib(default=Factory(lambda: SocialsRepl))
    emote_class = attrib(default=Factory(lambda: EmoteRepl))
    object_re = attrib(default=Factory(lambda: object_re))
    suffix_re = attrib(default=Factory(lambda: suffix_re))

    def __attrs_post_init__(self):
        for name in ('normal', 'title', 'upper', 'lower'):
            self.filters[name] = getattr(self, name)

    def normal(self, value):
        """Capitalise the first letter of value."""
        if value:
            return value[0].upper() + value[1:]
        else:
            return ''

    def title(self, value):
        """Return value in title case."""
        return value.title()

    def upper(self, value):
        """Return value in upper case."""
        return value.upper()

    def lower(self, value):
        """Return value in lower case."""
        return value.lower()

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
        strings = []  # The strings to be returned.
        replacements = [[] for p in perspectives]  # Formatter strings.
        replacements.append([])  # Default replacements.
        repl = self.repl_class(self, perspectives, replacements)
        default = re.sub(self.suffix_re, repl.repl, string)
        for args in repl.replacements:
            strings.append(default.format(*args, **kwargs))
        return strings

    def no_object(self, index):
        """No object was found at the given index. By this point index will be
        0-based. Should return either an object or raise an instance of
        NoObjectError."""
        raise NoObjectError(
            f'{index + 1} is not in the list of objects.'
        )

    def no_suffix(self, obj, name):
        """No suffix was found for obj with the given name. Should either
        return a function to be used as the suffix or raise an instance of
        NoSuffixError."""
        raise NoSuffixError(
            '%s is not a valid suffix. Valid suffixes: %s.' % (
                name, ', '.join(sorted(self.suffixes.keys()))
            )
        )

    def no_filter(self, obj, name):
        """No filter found by that name. Should either return a filter function
        or raise an instance of NoFilterError."""
        raise NoFilterError(f'Invalid filter: {name}.')

    def no_match(self, name, *args, **kwargs):
        """No object was found matching that name. Should either return an
        object or raise an instance of NoMatchError."""
        raise NoMatchError(name)

    def convert_emote_string(
        self, string, match, perspectives, *args, **kwargs
    ):
        """Convert an emote string like
        % smiles at {john}n
        to
        % smiles at %2n
        Returns (string, perspectives) ready to be fed into get_strings.

        The match function will be used to convert match strings to objects,
        and should return just the object. If it returns None, self.no_match
        will be called with the same set of arguments.
        All extra arguments and keyword arguments will be passed to the match
        function after the match string.
        The perspectives string will be extended by this function."""
        repl = self.emote_class(self, perspectives, match, args, kwargs)
        string = re.sub(self.object_re, repl.repl, string)
        return (string, perspectives)

    def get_suffixes(self):
        """Return a list of suffix objects."""
        d = {}
        for name, func in self.suffixes.items():
            i = id(func)
            args = d.get(i, [func, []])
            args[-1].append(name)
            args[-1] = sorted(args[-1])
            d[i] = args
        return [Suffix(*a) for a in d.values()]

    def get_filters(self):
        """Return all filters as a dictionary."""
        return self.filters


class PopulatedSocialsFactory(SocialsFactory):
    """A SocialsFactory instance with some useful suffixes applied."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.suffix('s')(self.get_s)
        self.suffix('e', 'es')(self.get_es)
        self.suffix('y', 'ies')(self.get_y)
        self.suffix('are', 'is')(self.get_are)

    def get_s(self, obj, suffix):
        """"" or "s"."""
        return '', 's'

    def get_es(self, obj, suffix):
        """"" or "es"."""
        return '', 'es'

    def get_y(self, obj, suffix):
        """"y" or "ies"."""
        return 'y', 'ies'

    def get_are(self, obj, suffix):
        """"are" or "is"."""
        return ('are', 'is')
