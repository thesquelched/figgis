from figgis import Config, Field, ListField, ValidationError, PropertyError
from unittest import TestCase


class TestConfig(TestCase):

    def test_simple_config(self):
        class SimpleConfig(Config):
            required = Field(str, required=True)
            integer = Field(int, default=0)
            number = Field(float, default=0.0)
            string = Field(str, default='')
            list_ = Field(list, default=[])
            dict_ = Field(dict, default={})

        c = SimpleConfig({'required': 'foo', 'extra': 5})
        self.assertEqual(c.required, 'foo')
        self.assertEqual(c.integer, 0)
        self.assertEqual(c.number, 0.0)
        self.assertEqual(c.string, '')
        self.assertEqual(c.list_, [])
        self.assertEqual(c.dict_, {})

        self.assertRaises(PropertyError, SimpleConfig, {})
        self.assertRaises(PropertyError, SimpleConfig)

    def test_simple_list(self):
        class ListConfig(Config):
            list_ = ListField(int, default=[1, 2, 3])

        c = ListConfig()
        self.assertEqual(c.list_, [1, 2, 3])

        c = ListConfig(list_=[5])
        self.assertEqual(c.list_, [5])

        self.assertRaises(ValidationError, ListConfig, list_=[1, 'a'])
        self.assertRaises(ValidationError, ListConfig, list_=1)

    def test_sub_config(self):
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
        self.assertEqual(c.dict_.name, 'none')
        self.assertEqual(c.dict_.value, 0)
        self.assertEqual(c.dict_.sub, None)
        self.assertEqual(c.list_, [])

        c = MainConfig(
            dict_={'name': 'foo', 'sub': {'value': 5}},
            list_=[{'name': 'one'}, {'name': 'two', 'value': 2}]
        )
        self.assertEqual(c.dict_.name, 'foo')
        self.assertEqual(c.dict_.value, 0)
        self.assertEqual(c.dict_.sub.value, 5)
        self.assertEqual(c.list_[0].name, 'one')
        self.assertEqual(c.list_[0].value, 0)
        self.assertEqual(c.list_[1].name, 'two')
        self.assertEqual(c.list_[1].value, 2)

    def test_conflicts(self):
        class ConflictConfig(Config):
            fields = Field(int, required=True)
            normalize = Field(int, default=0)

        c = ConflictConfig(fields=1)
        self.assertEqual(c.fields, 1)
        self.assertEqual(c.normalize, 0)

    def test_validate(self):
        class ValidateConfig(Config):
            val = Field(int, default=0, validator=lambda value: value > 0)

        c = ValidateConfig(val=5)
        self.assertEqual(c.val, 5)

        self.assertRaises(ValidationError, ValidateConfig)
        self.assertRaises(ValidationError, ValidateConfig, val=-10)

        def raises_validation_error(value):
            raise ValidationError('Wrong')

        class FailureConfig(Config):
            fails = Field(validator=raises_validation_error)

        try:
            c = FailureConfig()
            msg = None
        except ValidationError as ex:
            msg = ex.message

        self.assertEquals(msg, "Field 'fails' is invalid: Wrong")

    def test_string_coerce(self):
        class CoerceConfig(Config):
            string = Field(str)

        c = CoerceConfig()
        self.assertIsNone(c.string)

        for value in ('foo', 1, 10L, 1.0):
            c = CoerceConfig(string=value)
            self.assertEqual(c.string, str(value))

        c = CoerceConfig(string=None)
        self.assertIsNone(c.string)

    def test_int_coerce(self):
        class CoerceConfig(Config):
            integer = Field(int)

        c = CoerceConfig()
        self.assertIsNone(c.integer)

        for value in (10, 40L):
            c = CoerceConfig(integer=value)
            self.assertEqual(c.integer, int(value))

        c = CoerceConfig(integer=None)
        self.assertIsNone(c.integer)

        for value in ('foo', '5.5'):
            self.assertRaises(ValidationError, CoerceConfig, integer=value)

    def test_long_coerce(self):
        class CoerceConfig(Config):
            integer = Field(long)

        c = CoerceConfig()
        self.assertIsNone(c.integer)

        for value in (10, 40L):
            c = CoerceConfig(integer=value)
            self.assertEqual(c.integer, long(value))

        c = CoerceConfig(integer=None)
        self.assertIsNone(c.integer)

        for value in ('foo', '5.5'):
            self.assertRaises(ValidationError, CoerceConfig, integer=value)

    def test_float_coerce(self):
        class CoerceConfig(Config):
            number = Field(float)

        c = CoerceConfig()
        self.assertIsNone(c.number)

        for value in (1, 4L, 5.0, '5.0', '5'):
            c = CoerceConfig(number=value)
            self.assertEqual(c.number, float(value))

        c = CoerceConfig(number=None)
        self.assertIsNone(c.number)

        for value in ('foo'):
            self.assertRaises(ValidationError, CoerceConfig, number=value)

    def test_bool_coerce(self):
        class CoerceConfig(Config):
            value = Field(bool)

        c = CoerceConfig()
        self.assertIsNone(c.value)

        # Falsey
        for value in (0L, 0, 'false', 'False', 'no', '0', False):
            c = CoerceConfig(value=value)
            self.assertFalse(c.value, '{} does not coerce to False'.format(
                repr(value)))

        # Truthy
        for value in (1L, 1, 'true', 'True', 'yes', '1', True):
            c = CoerceConfig(value=value)
            self.assertTrue(c.value, '{} does not coerce to True'.format(
                repr(value)))

        c = CoerceConfig(value=None)
        self.assertIsNone(c.value)

        for value in ('foo', 'bar'):
            self.assertRaises(ValidationError, CoerceConfig, value=value)

    def test_empty_list(self):
        class ListConfig(Config):
            values = ListField(str)

        c = ListConfig()
        self.assertEqual(c.values, [])

    def test_choices(self):
        class ChoiceConfig(Config):
            value = Field(int, choices=[1, 2, 3])

        self.assertRaises(ValidationError, ChoiceConfig)
        self.assertRaises(ValidationError, ChoiceConfig, value=0)
        self.assertRaises(ValidationError, ChoiceConfig, value='a')

        self.assertIsNotNone(ChoiceConfig(value=1))
        self.assertIsNotNone(ChoiceConfig(value=2))
        self.assertIsNotNone(ChoiceConfig(value=3))

    def test_list_choices(self):
        class ChoiceConfig(Config):
            values = ListField(int, choices=[1, 2, 3])

        self.assertRaises(ValidationError, ChoiceConfig, values=[0])
        self.assertRaises(ValidationError, ChoiceConfig, values=['a'])
        self.assertRaises(ValidationError, ChoiceConfig, values=[1, 2, 15])

        self.assertIsNotNone(ChoiceConfig())
        self.assertIsNotNone(ChoiceConfig(values=[1]))
        self.assertIsNotNone(ChoiceConfig(values=[2]))
        self.assertIsNotNone(ChoiceConfig(values=[3]))
        self.assertIsNotNone(ChoiceConfig(values=[1, 2, 3]))

    def test_coerce(self):
        class SubConfig(Config):
            value = Field()

        class TestConfig(Config):
            value = Field(SubConfig)

        tc = TestConfig()
        tc._fields['value'].coerce(SubConfig(value=1))


class TestDescribe(TestCase):

    def test_flat(self):
        class TestConfig(Config):
            nodesc = Field()
            default = Field(int, default=0, help='default')
            required = Field(int, required=True, help='required')
            choices = Field(int, choices=[1, 2, 3], help='choices')
            list_ = ListField(help='list_')

        desc = TestConfig.describe()
        self.assertEqual(
            desc,
            'choices (type=int, choices=[1, 2, 3]) - choices\n'
            'default (type=int, default=0) - default\n'
            'list_ (type=list(str)) - list_\n'
            'nodesc (type=str)\n'
            'required (type=int, required) - required'
        )

    def test_nested(self):
        class SubSubConfig(Config):
            value1 = Field()
            value2 = Field()

        class SubConfig(Config):
            value = Field()
            config = Field(SubSubConfig)

        class TestConfig(Config):
            value = Field()
            config = Field(SubConfig)

        desc = TestConfig.describe()
        self.assertEqual(
            desc,
            'config (type=SubConfig)\n'
            '  config (type=SubSubConfig)\n'
            '    value1 (type=str)\n'
            '    value2 (type=str)\n'
            '  value (type=str)\n'
            'value (type=str)'
        )

    def test_nested_magic_help(self):
        class SubSubConfig(Config):
            __help__ = 'subsubconfig'
            value1 = Field()
            value2 = Field()

        class SubConfig(Config):
            __help__ = 'subconfig'
            value = Field()
            config1 = Field(SubSubConfig, help='override')
            config2 = Field(SubSubConfig)

        class TestConfig(Config):
            value = Field()
            config = Field(SubConfig)

        desc = TestConfig.describe()
        self.assertEqual(
            desc,
            'config (type=SubConfig) - subconfig\n'
            '  config1 (type=SubSubConfig) - override\n'
            '    value1 (type=str)\n'
            '    value2 (type=str)\n'
            '  config2 (type=SubSubConfig) - subsubconfig\n'
            '    value1 (type=str)\n'
            '    value2 (type=str)\n'
            '  value (type=str)\n'
            'value (type=str)'
        )
