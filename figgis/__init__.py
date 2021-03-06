# Copyright 2015 Yahoo! Inc.
# Copyrights licensed under the BSD License. See the accompanying LICENSE
# file for terms.

import figgis._version as version
from inspect import isclass, isfunction
import six

__version_info__ = version.__version_info__
__version__ = version.__version__

__all__ = ['Field', 'ListField', 'Config', 'ValidationError', 'PropertyError']


if six.PY3:  # pragma: no cover
    long = int


_TRUTHY = frozenset((long(1), 1, 'true', 'True', 'yes', '1', True))
_FALSEY = frozenset((long(0), 0, 'false', 'False', 'no', '0', False))


# Reserved field names
_RESERVED = frozenset(['get', 'update', 'describe', 'copy'])


class _NotSpecified(object):

    def __repr__(self):  # pragma: no cover
        return 'None'

    __str__ = __repr__


NotSpecified = _NotSpecified()


def indent(value, size=2):
    """Indent a string by a given size (default=2)"""
    lines = value.strip().split('\n')
    return '\n'.join(' ' * size + line for line in lines)


class NormalizedDict(dict):
    """Indicate that the data has already been normalized"""
    pass


######################################################################
# Errors
######################################################################

class FiggisError(Exception):
    """Base class for figgis exceptions"""
    pass


class ReservedFieldError(TypeError, FiggisError):
    """Thrown when a config attempts to overwrite a reserved field"""


class ValidationError(FiggisError):
    """Thrown when a field's data is invalid"""
    pass


class PropertyError(KeyError, FiggisError):
    """Thrown when a required property is missing"""
    pass


######################################################################
# Configuration
######################################################################

class Field(object):

    """
    Represents a typed field in a configuration file.  `type` may be a python
    type (e.g. `int`, `str`, `float`, `dict`), another :class:`Config` object,
    or a function/lambda that takes a single argument and returns the desired
    parsed value.

    When a :class:`Config` is instantiated, each field is type-checked against
    the corresponding value.  You may provide additional validation by passing
    a function to `validator`.  This function takes one argument, the config
    value, and must return a `boolean` value.

    >>> class Address(Config):
    ...     number = Field(int, required=True)
    ...     street = Field(required=True)
    ...     suffix = Field(default='St.', choices=['St.', 'Ave.'])  # optional
    ...
    ...     def __str__(self):
    ...         return '{0} {1} {2}'.format(
    ...             self.number, self.street, self.suffix)
    >>> class Person(Config):
    ...     name = Field(required=True)
    ...     age = Field(int, required=True, validator=lambda age: age > 0)
    ...     address = Field(Address)
    >>> joe = Person(
    ...     name='Joe',
    ...     age=45,
    ...     address=dict(
    ...         number=123,
    ...         street='Easy',
    ...     )
    ... )
    >>> print('{0}, age {1}, lives at {2}'.format(
    ...     joe.name, joe.age, joe.address))
    Joe, age 45, lives at 123 Easy St.

    Sometimes, you may need to consume data for which some keys can not be
    expressed as a python identifier, e.g. `@attr`.  In this case, you may use
    the `key` option to provide a mapping from the data to your fields:

    >>> class Translated(Config):
    ...     crazy_key = Field(required=True, key='@crazy_key')
    >>> Translated({'@crazy_key@': 'value'}).crazy_key
    'value'
    """

    def __init__(self,
                 *types,
                 **kwargs):
        """
        Field(*types, type=None, required=False, default=NotSpecified, \
validator=None, choices=None, help=None, hidden=None, key=None, nullable=True)

        :param types: One or more types or functions to apply, in order, to
                      the field value.
        :param type: Either a built-in data type, another :class:`Config`
                     object, or a function that takes the raw field value and
                     produces the desired result. May not be used with `types`
        :param required: If `True`, throw an exception if the data does not
                         exist
        :param default: Default value to use if the data does not exist
        :param nullable: If `True`, then allow the field value to be null
        :param choices: List of values that constrain the possible data values
        :param key: The key in the data that should be read to produce this
                    field (defaults to the variable name to which this field is
                    assigned)
        :param validator: Either function or a list of functions,
                          taking the parsed field data, that either returns
                          `False` or throws :class:`ValidationError` if the
                          data is invalid, or returns `True` otherwise
        :param hidden: Hide this field from the output of
                       :meth:`Config.describe`
        """
        type_ = kwargs.get('type', None)
        validator = kwargs.get('validator', None)
        choices = kwargs.get('choices', None)

        self._required = bool(kwargs.get('required', False))
        self._default = kwargs.get('default', NotSpecified)
        self._help = kwargs.get('help', None)
        self._hidden = bool(kwargs.get('hidden', False))
        self._key = kwargs.get('key', None)
        self._nullable = bool(kwargs.get('nullable', True))
        self._read_only = bool(kwargs.get('read_only', True))

        if types and type_:
            raise ValueError("Keyword argument 'type' is not allowed with "
                             "one or more positional arguments")
        elif type_:
            types = (type_,)
        elif not types:
            types = (six.text_type,)

        if not isinstance(validator, (tuple, list)):
            validator = [] if validator is None else [validator]

        self._types = types
        self._choices = set(choices) if choices else None

        # Has to be done after all other options are set so that
        # base_validators can correctly create validators from field options
        self._validators = list(validator) + self.base_validators()

    def base_validators(self):
        validators = []
        if self.choices:
            validators.append(self.choice_validator)

        return validators

    def choice_validator(self, value):
        if value not in self.choices:
            raise ValidationError("Value '{0}' is not a valid choice".format(
                value))

        return True

    @property
    def read_only(self):
        return self._read_only

    @property
    def types(self):
        return self._types

    @property
    def type(self):
        assert len(self._types) == 1, 'Field should only have one type'

        return self._types[0]

    @property
    def pretty_type(self):
        try:
            return self.type.__name__
        except AttributeError:  # pragma: nocover
            return six.text_type(self.type)

    @property
    def required(self):
        return self._required

    @property
    def nullable(self):
        return self._nullable

    @property
    def default(self):
        return self._default

    @property
    def validators(self):
        return self._validators

    @property
    def choices(self):
        return self._choices

    @property
    def help(self):
        return self._help

    @property
    def hidden(self):
        return self._hidden

    def describe_properties(self):
        props = ['type={0}'.format(self.pretty_type)]
        if self.required:
            props.append('required')
        if self.default is not NotSpecified:
            props.append('default={0}'.format(self.default))
        if not self.nullable:
            props.append('non-nullable')
        if self.choices:
            choices = sorted(self.choices)
            choicestr = ', '.join(repr(item) for item in choices)
            if len(choices) > 10:
                choicestr += ', ...'

            props.append('choices=[{0}]'.format(choicestr))

        return props

    def describe(self):
        props = self.describe_properties()

        propstring = '({0})'.format(', '.join(props))
        if self.help:
            desc = '{0} - {1}'.format(propstring, self.help)
        elif (isclass(self.type) and issubclass(self.type, Config) and
              hasattr(self.type, '__help__')):
            desc = '{0} - {1}'.format(propstring, self.type.__help__)
        else:
            desc = propstring

        if isclass(self.type) and issubclass(self.type, Config):
            return '{0}\n{1}'.format(desc, indent(self.type.describe()))

        return desc

    def validate(self, normalized, prefixed, exists):
        if not (exists and self.validators):
            return

        for validator in self.validators:
            try:
                if not validator(normalized):
                    raise ValidationError("Field '{0}' is invalid".format(
                        prefixed))
            except ValidationError as ex:
                raise ValidationError("Field '{0}' is invalid: {1}".format(
                    prefixed, ex))

    def coerce_bool(self, value):
        if value in _TRUTHY:
            return True
        elif value in _FALSEY:
            return False
        else:
            raise ValueError

    def coerce(self, value, type_, parent=None):
        type_or_class = (isclass(type_) or isinstance(type_, type))
        if type_or_class and isinstance(value, type_):
            return value
        elif type_ is bool:
            return self.coerce_bool(value)
        else:
            if type_or_class and issubclass(type_, Config):
                kwargs = {'__parent': parent}
            else:
                kwargs = {}
            return type_(value, **kwargs)

    def invalid_type(self, type_, value, prefixed):
        if value is None:
            return not self.nullable
        elif isclass(type_) and issubclass(type_, Config):
            return not isinstance(value, (type_, dict))
        elif isfunction(type_):
            # Assume data parsed by custom functions is valid
            return False
        else:
            try:
                # Attempt to coerce value
                self.coerce(value, type_)
                return False
            except (TypeError, ValueError):
                return True

    def normalize(self, config, name, prefix=None, parent=None):
        config_key = self._key or name

        prefixed = name if prefix is None else '{0}.{1}'.format(prefix, name)
        if config_key not in config:
            if self.required:
                raise PropertyError('Missing property: {0}'.format(prefixed))

            exists = self.default is not NotSpecified
            conf_value = None if self.default is NotSpecified else self.default
        else:
            exists = True
            conf_value = config[config_key]

        normalized = conf_value
        for type_ in self.types:
            normalized = self.normalize_field(type_, normalized, name,
                                              prefixed, parent=parent)

        self.validate(normalized, prefixed, exists)

        return name, normalized

    def normalize_field(self, type_, field_value, name, prefixed, parent=None):
        if self.invalid_type(type_, field_value, prefixed):
            raise ValidationError('Property {0} is not of type {1}'.format(
                prefixed, type_.__name__))

        if field_value is None:
            return None

        if isclass(type_) and issubclass(type_, Config):
            normalized = type_._normalize(field_value, prefix=prefixed)
            return self.coerce(normalized, type_, parent=parent)
        else:
            return self.coerce(field_value, type_)


class ListField(Field):

    """
    Similar to :class:`Field`, except that it expects a list of objects instead
    of a single object.

    >>> class Product(Config):
    ...     name = Field(required=True)
    ...     price = Field(float, default=0.0)
    >>> class Catalog(Config):
    ...     products = ListField(Product, required=True)
    >>> catalog = Catalog(
    ...     products=[
    ...         {'name': 'Orange', 'price': 0.79},
    ...         {'name': 'Apple', 'price': 0.59},
    ...     ]
    ... )
    >>> for product in catalog.products:
    ...     print('{0} costs {1}'.format(product.name, product.price))
    Orange costs 0.79
    Apple costs 0.59
    """

    @property
    def pretty_type(self):
        return 'list({0})'.format(Field.pretty_type.fget(self))

    def choice_validator(self, values):
        for value in values:
            if value not in self.choices:
                raise ValidationError(
                    "Value '{0}' is not a valid choice".format(value))

        return True

    def is_list(self, field_value):
        if field_value is None:
            return not self.required and self.default is NotSpecified
        else:
            return isinstance(field_value, list)

    def normalize_field(self, type_, field_value, name, prefixed, parent=None):
        if not self.is_list(field_value):
            raise ValidationError('Field {0} is not a list'.format(prefixed))

        if field_value is None:
            field_value = []

        values = []
        for i, value in enumerate(field_value):
            prefix = '{0}.{1}'.format(prefixed, i)
            normalized = super(ListField, self).normalize_field(
                type_, value, name, prefix, parent=parent)
            values.append(normalized)

        return values


def normalizer(allow_extra=None):
    if allow_extra is None:
        allow_extra = True

    @classmethod
    def normalize(cls, config, prefix=None, allow_extra=allow_extra, parent=None):
        extra = frozenset(config) - frozenset(cls._fields)
        if extra and not allow_extra:
            raise PropertyError('Encountered unexpected key: {0}{1}'.format(
                prefix + '.' if prefix else '',
                six.next(iter(extra))))

        return NormalizedDict(
            field.normalize(config, name, prefix=prefix, parent=parent)
            for name, field in cls._fields.items())

    return normalize


def autoproperty(key, docstring=None, read_only=True):
    """
    Create a property for the given key that retrieves the corresponding value
    from self._properties
    """
    def getter(self):
        return self._properties.get(key)

    def setter(self, value):
        self._properties[key] = value

    return property(getter,
                    None if read_only else setter,
                    None,
                    docstring)


class ConfigMeta(type):

    """
    Metaclass for configuration objects.  Do not use this directly; instead,
    use :class:`Config`.
    """

    def __new__(cls, name, bases, dct):
        # Normalization
        fields = dict()

        # Preserve MRO by reversing inheritance list; first parent overwrites
        # everything before it
        inherits = reversed(dct.get('__inherits__', []))
        for parent in inherits:
            fields.update(parent._fields)

        fields.update((key, value) for key, value in dct.items()
                      if not key.startswith('__') and isinstance(value, Field))

        forbidden = _RESERVED.intersection(frozenset(fields.keys()))
        if forbidden:
            raise ReservedFieldError((
                'Config {0} overwrites reserved field{1} {2}; use key option '
                'to rename field{1}'
            ).format(name,
                     's' if len(forbidden) > 1 else '',
                     ', '.join(forbidden)))

        dct['_fields'] = fields
        dct['_normalize'] = normalizer(
            allow_extra=dct.pop('__allow_extra__', None))

        # Automatic properties
        for key, field in fields.items():
            dct[key] = autoproperty(key, read_only=field.read_only, docstring=field.help)

        return type.__new__(cls, name, bases, dct)


@six.add_metaclass(ConfigMeta)
class Config(object):

    """
    Base class for configuration objects.  See :class:`Field` and
    :class:`ListField` for usage.

    When you create a :class:`Config` instance, you pass to it parameters as
    you would a `dict`.  Similar to a `dict`, you can either use keyword
    arguments or pass in an actual `dict` object.

    If you wish to inherit from another :class:`Config`, do not do it in the
    traditional class inheritance sense.  Instead, specify any parents using
    the `__inherits__` attribute:

    >>> class Parent(Config):
    ...     id = Field(int, required=True)
    >>> class Child(Config):
    ...     __inherits__ = [Parent]
    ...
    ...     name = Field()
    """

    def __init__(self, *args, **kwargs):
        if len(args) > 1:
            raise TypeError(
                'Expected one or fewer arguments, but received {0}'.format(
                    len(args)))

        self._parent = kwargs.pop('__parent', None)

        properties = args[0] if args else {}
        if isinstance(properties, NormalizedDict):
            # No need to normalize, since we're already normalized
            # (ignore kwargs, though)
            normalized = properties
        else:
            combined = properties.copy()
            combined.update(kwargs)
            normalized = self._normalize(combined, parent=self)

        self._properties = normalized

    @property
    def parent(self):
        return self._parent

    def __contains__(self, key):
        return key in self._properties

    def copy(self):
        return self.__class__(self._properties.copy())

    def update(self, *args, **kwargs):
        self._properties.update(*args, **kwargs)

    def get(self, key, default=None):
        return self._properties.get(key, default)

    def to_dict(self):
        """Convert the config to a plain python dictionary"""
        converted = {}
        for key, value in self._properties.items():
            if isinstance(value, Config):
                converted[key] = value.to_dict()
            elif (isinstance(value, (list, tuple)) and
                    any(isinstance(item, Config) for item in value)):
                converted[key] = [item.to_dict() for item in value]
            else:
                converted[key] = value

        return converted

    @classmethod
    def describe(cls):
        """
        Return a pretty-formatted string that describes the format of the data
        """
        names = sorted(name for name, field in cls._fields.items()
                       if not field.hidden)
        desc = ['{0} {1}'.format(name, cls._fields[name].describe())
                for name in names]
        return '\n'.join(desc)
