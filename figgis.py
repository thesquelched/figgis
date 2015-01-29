__version__ = '1.0.1'
__all__ = ['Field', 'ListField', 'Config', 'ValidationError', 'PropertyError']


from inspect import isclass


TRUTHY = {1L, 1, 'true', 'True', 'yes', '1', True}
FALSEY = {0L, 0, 'false', 'False', 'no', '0', False}


def indent(value, size=2):
    """Indent a string by a given size (default=2)"""
    lines = value.strip().split('\n')
    return '\n'.join(' ' * size + line for line in lines)


class ValidationError(Exception):
    pass


class PropertyError(KeyError):
    pass


class Field(object):
    """
    Represents a typed field in a configuration file.  `type` may be a python
    type (e.g. `int`, `str`, `float`, `dict`), or it can be another
    :class:`Config` object.

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
    ...         return '{} {} {}'.format(
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
    >>> print '{}, age {}, lives at {}'.format(
    ...     joe.name, joe.age, joe.address)
    Joe, age 45, lives at 123 Easy St.
    """

    def __init__(self,
                 type=None,
                 required=False,
                 default=None,
                 validator=None,
                 choices=None,
                 help=None,
                 hidden=False):
        if type is None:
            type = str

        if not isinstance(validator, (tuple, list)):
            validator = [] if validator is None else [validator]

        self._type = type
        self._required = required
        self._default = default
        self._choices = set(choices) if choices else None
        self._help = help
        self._hidden = hidden

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
            raise ValidationError("Value '{}' is not a valid choice".format(
                value))

        return True

    @property
    def type(self):
        return self._type

    @property
    def pretty_type(self):
        try:
            return self._type.__name__
        except AttributeError:
            return str(self._type)

    @property
    def required(self):
        return self._required

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

    def describe(self):
        props = ['type={}'.format(self.pretty_type)]
        if self.required:
            props.append('required')
        if self.default is not None:
            props.append('default={}'.format(self.default))
        if self.choices:
            choices = sorted(self.choices)
            choicestr = ', '.join(repr(item) for item in choices)
            if len(choices) > 10:
                choicestr += ', ...'

            props.append('choices=[{}]'.format(choicestr))

        propstring = '({})'.format(', '.join(props))
        if self.help:
            desc = '{} - {}'.format(propstring, self.help)
        elif (isclass(self.type) and issubclass(self.type, Config) and
              hasattr(self.type, '__help__')):
            desc = '{} - {}'.format(propstring, self.type.__help__)
        else:
            desc = propstring

        if isclass(self.type) and issubclass(self.type, Config):
            return '{}\n{}'.format(desc, indent(self.type.describe()))

        return desc

    def validate(self, normalized, prefixed):
        if not self.validators:
            return

        for validator in self.validators:
            try:
                if not validator(normalized):
                    raise ValidationError("Field '{}' is invalid".format(
                        prefixed))
            except ValidationError as ex:
                raise ValidationError("Field '{}' is invalid: {}".format(
                    prefixed, ex.message))

    def coerce_bool(self, value):
        if value in TRUTHY:
            return True
        elif value in FALSEY:
            return False
        else:
            raise ValueError

    def coerce(self, value):
        type_or_class = (isclass(self.type) or isinstance(self.type, type))
        if type_or_class and isinstance(value, self.type):
            return value
        elif self.type is bool:
            return self.coerce_bool(value)
        else:
            return self.type(value)

    def invalid_type(self, value, prefixed):
        if value is None:
            # Null values are only invalid if the field is required or if the
            # default isn't None
            return self.required or self.default is not None
        elif isclass(self.type) and issubclass(self.type, Config):
            return not isinstance(value, (self.type, dict))
        else:
            try:
                # Attempt to coerce value
                self.coerce(value)
                return False
            except (TypeError, ValueError):
                return True

    def normalize(self, config, name, prefix=None):
        prefixed = name if prefix is None else '{}.{}'.format(prefix, name)
        if name not in config:
            if self.required:
                raise PropertyError('Missing property: {}'.format(prefixed))
            config[name] = self.default

        conf_value = config[name]
        normalized = self.normalize_field(conf_value, name, prefixed)
        self.validate(normalized, prefixed)

        config[name] = normalized

    def normalize_field(self, field_value, name, prefixed):
        if self.invalid_type(field_value, prefixed):
            raise ValidationError('Property {} is not of type {}'.format(
                prefixed, self.type.__name__))

        if field_value is None:
            return None

        if isclass(self.type) and issubclass(self.type, Config):
            for fname, field in self.type._fields.items():
                field.normalize(field_value, fname, prefix=prefixed)

        return self.coerce(field_value)


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
    ...     print '{} costs {}'.format(product.name, product.price)
    Orange costs 0.79
    Apple costs 0.59
    """

    @property
    def pretty_type(self):
        return 'list({})'.format(Field.pretty_type.fget(self))

    def choice_validator(self, values):
        for value in values:
            if value not in self.choices:
                raise ValidationError(
                    "Value '{}' is not a valid choice".format(value))

        return True

    def is_list(self, field_value):
        if field_value is None:
            return not self.required and self.default is None
        else:
            return isinstance(field_value, list)

    def normalize_field(self, field_value, name, prefixed):
        if not self.is_list(field_value):
            raise ValidationError('Field {} is not a list'.format(prefixed))

        if field_value is None:
            field_value = []

        values = []
        for i, value in enumerate(field_value):
            prefix = '{}.{}'.format(prefixed, i)
            normalized = super(ListField, self).normalize_field(
                value, name, prefix)
            values.append(normalized)

        return values


def normalizer(fields):
    def normalize(self, config, fields=fields, prefix=None):
        copied = config.copy()
        for name, field in fields.items():
            field.normalize(copied, name, prefix)

        return copied

    return normalize


def autoproperty(key):
    """
    Create a property for the given key that retrieves the corresponding value
    from self._properties
    """
    return property(lambda self: self._properties.get(key))


class ConfigMeta(type):
    """
    Metaclass for configuration objects.  Do not use this directly; instead,
    use :class:`Config`.
    """

    def __new__(cls, name, bases, dct):
        # Normalization
        fields = {key: value for key, value in dct.items()
                  if isinstance(value, Field)}
        dct['_fields'] = fields
        dct['_normalize'] = normalizer(fields)

        # Automatic properties
        for key, field in fields.items():
            dct[key] = autoproperty(key)

        return type.__new__(cls, name, bases, dct)


class Config(object):
    """
    Base class for configuration objects.  See :class:`Field` and
    :class:`ListField` for usage.

    When you create a :class:`Config` instance, you pass to it parameters as
    you would a `dict`.  Similar to a `dict`, you can either use keyword
    arguments or pass in an actual `dict` object.
    """
    __metaclass__ = ConfigMeta

    def __init__(self, properties=None, **kwArgs):
        if properties is None:
            properties = {}

        combined = properties.copy()
        combined.update(kwArgs)

        self._properties = self._normalize(combined)

    def __getitem__(self, key):
        return self._properties[key]

    def __setitem__(self, key, value):
        self._properties[key] = value

    def __contains__(self, key):
        return key in self._properties

    def copy(self):
        return self.__class__(self._properties.copy())

    def update(self, *args, **kwArgs):
        self._properties.update(*args, **kwArgs)

    def get(self, key, default=None):
        return self._properties.get(key, default)

    @classmethod
    def describe(cls):
        names = sorted(name for name, field in cls._fields.items()
                       if not field.hidden)
        desc = ['{} {}'.format(name, cls._fields[name].describe())
                for name in names]
        return '\n'.join(desc)
