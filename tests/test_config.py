from figgis import Config, Field, ListField, ValidationError, PropertyError

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
    assert c.list_[0].name == 'one'
    assert c.list_[0].value == 0
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

    class FailureConfig(Config):
        fails = Field(validator=raises_validation_error)

    pytest.raises(ValidationError, FailureConfig)


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

    pytest.raises(ValidationError, ChoiceConfig)
    pytest.raises(ValidationError, ChoiceConfig, value=0)
    pytest.raises(ValidationError, ChoiceConfig, value='a')

    assert ChoiceConfig(value=1) is not None
    assert ChoiceConfig(value=2) is not None
    assert ChoiceConfig(value=3) is not None


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
    tc._fields['value'].coerce(SubConfig(value=1))


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
