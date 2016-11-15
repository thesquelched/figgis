# Copyright 2015 Yahoo! Inc.
# Copyrights licensed under the BSD License. See the accompanying LICENSE
# file for terms.

from figgis import Config, Field, ListField, ValidationError, PropertyError

from copy import deepcopy
import pytest
import six


if six.PY3:
    long = int


def test_simple_config():
    class SimpleConfig(Config):
        required = Field(str, required=True)
        integer = Field(int, default=0)
        number = Field(float, default=0.0)
        string = Field(str, default='')
        list_ = Field(list, default=[])
        dict_ = Field(dict, default={})

    c = SimpleConfig({'required': 'foo', 'extra': 5})
    assert c.required == 'foo'
    assert c.integer == 0
    assert c.number == 0.0
    assert c.string == ''
    assert c.list_ == []
    assert c.dict_ == {}

    pytest.raises(PropertyError, SimpleConfig, {})
    pytest.raises(PropertyError, SimpleConfig)


def test_function():
    class FuncConfig(Config):
        value = Field(lambda value: int(value) + 1)

    assert FuncConfig(value=1).value == 2


def test_simple_list():
    class ListConfig(Config):
        list_ = ListField(int, default=[1, 2, 3])

    c = ListConfig()
    assert c.list_ == [1, 2, 3]

    c = ListConfig(list_=[5])
    assert c.list_ == [5]

    pytest.raises(ValidationError, ListConfig, list_=[1, 'a'])
    pytest.raises(ValidationError, ListConfig, list_=1)


def test_sub_config():
    class SubSubConfig(Config):
        value = Field(int)

    class SubConfig(Config):
        name = Field(str, required=True)
        value = Field(int, default=0)
        sub = Field(SubSubConfig)

    class MainConfig(Config):
        dict_ = Field(SubConfig, default={'name': 'none'})
        list_ = ListField(SubConfig, default=[])

    c = MainConfig()
    assert c.dict_.parent is c
    assert c.dict_.name == 'none'
    assert c.dict_.value == 0
    assert c.dict_.sub is None
    assert c.list_ == []

    c = MainConfig(
        dict_={'name': 'foo', 'sub': {'value': 5}},
        list_=[{'name': 'one'}, {'name': 'two', 'value': 2}]
    )
    assert c.dict_.name == 'foo'
    assert c.dict_.value == 0
    assert c.dict_.sub.value == 5

    assert len(c.list_) == 2
    assert c.list_[0].parent is c
    assert c.list_[0].name == 'one'
    assert c.list_[0].value == 0

    assert c.list_[1].parent is c
    assert c.list_[1].name == 'two'
    assert c.list_[1].value == 2


def test_conflicts():
    class ConflictConfig(Config):
        fields = Field(int, required=True)
        normalize = Field(int, default=0)

    c = ConflictConfig(fields=1)
    assert c.fields == 1
    assert c.normalize == 0


def test_validate():
    class ValidateConfig(Config):
        val = Field(int, default=0, validator=lambda value: value > 0)

    c = ValidateConfig(val=5)
    assert c.val == 5

    pytest.raises(ValidationError, ValidateConfig)
    pytest.raises(ValidationError, ValidateConfig, val=-10)

    def raises_validation_error(value):
        raise ValidationError('Wrong')

    class OptionalConfig(Config):
        optional = Field(validator=raises_validation_error)

    assert OptionalConfig().optional is None


def test_string_coerce():
    class CoerceConfig(Config):
        string = Field(str)

    c = CoerceConfig()
    assert c.string is None

    for value in ('foo', 1, long(10), 1.0):
        c = CoerceConfig(string=value)
        assert c.string == str(value)

    c = CoerceConfig(string=None)
    assert c.string is None


def test_int_coerce():
    class CoerceConfig(Config):
        integer = Field(int)

    c = CoerceConfig()
    assert c.integer is None

    for value in (10, long(40)):
        c = CoerceConfig(integer=value)
        assert c.integer == int(value)

    c = CoerceConfig(integer=None)
    assert c.integer is None

    for value in ('foo', '5.5'):
        pytest.raises(ValidationError, CoerceConfig, integer=value)


def test_long_coerce():
    class CoerceConfig(Config):
        integer = Field(long)

    c = CoerceConfig()
    assert c.integer is None

    for value in (10, long(40)):
        c = CoerceConfig(integer=value)
        assert c.integer == long(value)

    c = CoerceConfig(integer=None)
    assert c.integer is None

    for value in ('foo', '5.5'):
        pytest.raises(ValidationError, CoerceConfig, integer=value)


def test_float_coerce():
    class CoerceConfig(Config):
        number = Field(float)

    c = CoerceConfig()
    assert c.number is None

    for value in (1, long(4), 5.0, '5.0', '5'):
        c = CoerceConfig(number=value)
        assert c.number == float(value)

    c = CoerceConfig(number=None)
    assert c.number is None

    for value in ('foo'):
        pytest.raises(ValidationError, CoerceConfig, number=value)


def test_bool_coerce():
    class CoerceConfig(Config):
        value = Field(bool)

    c = CoerceConfig()
    assert c.value is None

    # Falsey
    for value in (long(0), 0, 'false', 'False', 'no', '0', False):
        c = CoerceConfig(value=value)
        assert not c.value, '{} does not coerce to False'.format(repr(value))

    # Truthy
    for value in (long(1), 1, 'true', 'True', 'yes', '1', True):
        c = CoerceConfig(value=value)
        assert c.value, '{} does not coerce to True'.format(repr(value))

    c = CoerceConfig(value=None)
    assert c.value is None

    for value in ('foo', 'bar'):
        pytest.raises(ValidationError, CoerceConfig, value=value)


def test_empty_list():
    class ListConfig(Config):
        values = ListField(str)

    c = ListConfig()
    assert c.values == []


def test_choices():
    class ChoiceConfig(Config):
        value = Field(int, choices=[1, 2, 3])

    pytest.raises(ValidationError, ChoiceConfig, value=0)
    pytest.raises(ValidationError, ChoiceConfig, value='a')

    assert ChoiceConfig().value is None
    assert ChoiceConfig(value=1).value == 1
    assert ChoiceConfig(value=2).value == 2
    assert ChoiceConfig(value=3).value == 3


def test_list_choices():
    class ChoiceConfig(Config):
        values = ListField(int, choices=[1, 2, 3])

    pytest.raises(ValidationError, ChoiceConfig, values=[0])
    pytest.raises(ValidationError, ChoiceConfig, values=['a'])
    pytest.raises(ValidationError, ChoiceConfig, values=[1, 2, 15])

    assert ChoiceConfig() is not None
    assert ChoiceConfig(values=[1]) is not None
    assert ChoiceConfig(values=[2]) is not None
    assert ChoiceConfig(values=[3]) is not None
    assert ChoiceConfig(values=[1, 2, 3]) is not None


def test_coerce():
    class SubConfig(Config):
        value = Field()

    class TestConfig(Config):
        value = Field(SubConfig)

    tc = TestConfig()
    vfield = tc._fields['value']
    vfield.coerce(SubConfig(value=1), vfield.type)


def test_inheritance():
    class Parent1(Config):
        field1 = Field(default='one')

    class Parent2(Config):
        field2 = Field(default='two')

    class TestConfig(Config):
        __inherits__ = [Parent1, Parent2]

        field3 = Field(default='three')

    tc = TestConfig()

    assert tc.field1 == 'one'
    assert tc.field2 == 'two'
    assert tc.field3 == 'three'


def test_inheritance_mro():
    class Parent1(Config):
        field1 = Field(default='parent1')
        field2 = Field(default='parent1')

    class Parent2(Config):
        field1 = Field(default='parent2')
        field2 = Field(default='parent2')

    class TestConfig(Config):
        __inherits__ = [Parent1, Parent2]

        field2 = Field(default='testconfig')

    tc = TestConfig()

    assert tc.field1 == 'parent1'
    assert tc.field2 == 'testconfig'


def test_translation():
    class TestConfig(Config):

        foo = Field(int, required=True, key='@foo')

    tc = TestConfig({'@foo': 111})
    assert tc.foo == 111


def test_translation_inheritance():
    class Parent(Config):

        bar = Field(int, required=True, key='@foo')

    class Child(Config):

        __inherits__ = [Parent]

    child = Child({'@foo': 111})
    assert child.bar == 111


def test_translation_nested():
    class Conf1(Config):
        attributes = Field(int, required=True, key='@attr')

    class TestConf(Config):
        conf1 = Field(Conf1)

    child = TestConf({'conf1': {'@attr': 111}})
    assert child.conf1.attributes == 111


def test_config_extras():
    class Conf(Config):
        value = Field(int)

    conf = Conf(value=1)
    assert conf.copy().value == 1
    assert conf.get('value') == 1

    conf.update(value=2)
    assert conf.copy().value == 2
    assert conf.get('value') == 2


def test_nested_validate_missing():
    def raises_validation_error(value):
        raise ValidationError('Wrong')

    class Child(Config):
        field = Field(int, validator=raises_validation_error)

    class Parent(Config):
        child = Field(Child, required=True)

    Child({})
    Parent({'child': {}})


def test_original_not_modified():
    data = {
        'foo': 1,
        'bar': 'two'
    }
    original = deepcopy(data)

    class Conf(Config):
        foo = Field()
        baz = Field(key='bar')

    Conf(data)

    assert data == original


def test_reserved():
    def create_bad_config1():
        class BadConfig(Config):
            get = Field()

    def create_bad_config2():
        class BadConfig(Config):
            describe = Field()

    def create_bad_config3():
        class BadConfig(Config):
            copy = Field()

    def create_bad_config4():
        class BadConfig(Config):
            update = Field()

    pytest.raises(TypeError, create_bad_config1)
    pytest.raises(TypeError, create_bad_config2)
    pytest.raises(TypeError, create_bad_config3)
    pytest.raises(TypeError, create_bad_config4)


def test_nullable():
    class TestConfig(Config):
        nullable = Field(nullable=True, required=True)
        not_nullable = Field(nullable=False, required=True)
        default = Field(required=True)

    pytest.raises(ValidationError, TestConfig,
                  nullable=None, not_nullable=None, default=None)

    assert TestConfig(nullable=None, not_nullable='value', default=None)
    assert TestConfig(nullable='value', not_nullable='value', default='value')


def test_nullable_required():
    class TestConfig(Config):
        field = Field(nullable=True, required=True)

    pytest.raises(PropertyError, TestConfig)


def test_nullable_default():
    class TestConfig(Config):
        default = Field(nullable=False, default=None)

    pytest.raises(ValidationError, TestConfig)

    assert TestConfig(default='foo')


def test_allow_extra():
    class TestConfig(Config):
        __allow_extra__ = False

        foo = Field(int)

    assert TestConfig(foo=1).foo == 1
    pytest.raises(PropertyError, TestConfig, bar=1)


def test_allow_extra_subconfig():
    class Subconfig(Config):
        __allow_extra__ = False

        foo = Field(int)

    class TestConfig(Config):
        __allow_extra__ = True

        sub = Field(Subconfig)

    pytest.raises(PropertyError, TestConfig, sub=dict(bar=1))


def test_property_docstring():
    class Conf(Config):
        nohelp = Field()
        help = Field(help='myhelp')

    assert Conf.help.__doc__ == 'myhelp'


def test_multiple_types():
    class Conf(Config):
        double = Field(int, lambda x: x * 2)

    assert Conf(double=1).double == 2


def test_multiple_types_conf():
    class SubConf(Config):
        foo = Field(required=True)

    class Conf(Config):
        value = Field(lambda x: dict(list(x.items()) + [('foo', 'bar')]),
                      SubConf)

    assert Conf(value={}).value.foo == 'bar'


def test_read_only():
    class Conf(Config):
        foo = Field(int)
        bar = Field(int)

    conf = Conf(foo=1, bar=2)
    assert conf.foo == 1
    assert conf.bar == 2

    with pytest.raises(AttributeError):
        conf.foo = 3


def test_read_write():
    class Conf(Config):
        foo = Field(int, read_only=False)
        bar = Field(int)

    conf = Conf(foo=1, bar=2)
    assert conf.foo == 1
    assert conf.bar == 2

    conf.foo = 3
    assert conf.foo == 3

    with pytest.raises(AttributeError):
        conf.bar = 4


def test_type_conflict():
    with pytest.raises(ValueError):
        class Conf(Config):
            value = Field(int, type=int)


def test_type_kwarg():
    class Conf(Config):
        value = Field(type=int)

    conf = Conf(value=1)
    assert conf.value == 1


def test_invalid_config_args():
    class Conf(Config):
        value = Field()

    pytest.raises(TypeError, Conf, 'foo', 'bar')


def test_subconfig_parent():
    class Child(Config):
        value = Field(int)

        @property
        def parent_value(self):
            return self.parent.value

    class Parent(Config):
        value = Field(int)
        child = Field(Child)

    conf = Parent({'value': 1, 'child': {'value': 2}})
    assert conf.parent is None
    assert conf.child.parent is conf

    assert conf.value == 1
    assert conf.child.value == 2
    assert conf.child.parent_value == 1
