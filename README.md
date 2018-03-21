# emote-utils
Emote utilities for text-based games.

This package is most useful for formatting social strings for use with text-based games like MUDs and MOOs.

A social string might look like:

```
%1N smile%1s at %2n.
```

## Quickstart
First get a factory ready. You could use the base `SocialsFactory` class or the helpfully-populated `PopulatedSocialsFactory`.

This second class contains useful english grammar suffixes for properly converting words like are to is and proper use of e and s for use at the end of words.

```
from emote_utils import PopulatedSocialsFactory
f = PopulatedSocialsFactory()
@f.suffix('n', 'name')
    def get_name(obj, suffix):
        return ('you', obj.name)
```

Next let's create a test class.

```
class Person:
    def __init__(self, name):
        self.name = name

p1 = Person('Jack')
p2 = Person('Jill')
```

Now we'll get strings which can be sent to Jack, Jill and anyone else who should see the message.

```
jack_string, jill_string, others_string = f.get_strings('%1N smile%1s at %2n.', [p1, p2])
print(jack_string)
```

> You smile at Jill.


```
print(jill_string)
```

> Jack smiles at you.

```
print(others_string)
```

> Jack smiles at Jill.

## More advanced usage

### Social Formatters
Each social formatter is made up of three parts:

* a per cent (%) sign representing the start of a social formatter.
* an optional number indicating the index of the object you wish to reference in the list of objects.
* An optional filter name preceded by a vertical bar (`|`).

### Defaults
* If no index is provided, `SocialsFactory.default_index` is used.
* If no suffix is provided, `SocialsFactory.default_suffix` is used.
* If no filter is provided then one of 3 things will happen.

In the below list suffix refers either to the name of a suffix provided as part of the social string or the `default_suffix` attribute on the instance of `SocialsFactory` that `get_strings` is being called on.

Attribute names refer to the attributes of `SocialsFactory` that `get_strings` is being called on.

* If the suffix is title case then the title_case_filter attribute will be used.
* If the suffix is all upper case then the upper_case_filter attribute will be used.
* If neither of these things are true then suffix is assumed to be lower case and the lower_case_filter is used.

Of course any of these names could be `None` in which case no filtering is applied.

### Filters
Here is an example of a custom filter:

```
f.filters['strong'] = lambda string: f'<strong>{string}</strong>'
```

If you were printing your socil strings to HTML you could use this filter to make certain parts of the text stand out.

With this filter created, you could do:

```
%1N punch%1e %2n|strong.
```

A string might then look like:

> John punches <strong>Jack</strong>.

### Conclusion

To see all the other configuration options see the docstrings in the package.
