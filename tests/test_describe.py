# Copyright 2015 Yahoo! Inc.
# Copyrights licensed under the BSD License. See the accompanying LICENSE
# file for terms.

import six
from figgis import Config, Field, ListField


STR = six.text_type.__name__


def test_flat():
    class TestConfig(Config):
        nodesc = Field()
        default = Field(int, default=0, help='default')
        required = Field(int, required=True, help='required')
        choices = Field(int, choices=[1, 2, 3], help='choices')
        list_ = ListField(help='list_')
        not_nullable = Field(nullable=False)

    desc = TestConfig.describe()
    assert desc == """\
choices (type=int, choices=[1, 2, 3]) - choices
default (type=int, default=0) - default
list_ (type=list({str})) - list_
nodesc (type={str})
not_nullable (type={str}, non-nullable)
required (type=int, required) - required""".format(str=STR)


def test_nested():
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
    assert desc == """\
config (type=SubConfig)
  config (type=SubSubConfig)
    value1 (type={str})
    value2 (type={str})
  value (type={str})
value (type={str})""".format(str=STR)


def test_nested_magic_help():
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
    assert desc == """\
config (type=SubConfig) - subconfig
  config1 (type=SubSubConfig) - override
    value1 (type={str})
    value2 (type={str})
  config2 (type=SubSubConfig) - subsubconfig
    value1 (type={str})
    value2 (type={str})
  value (type={str})
value (type={str})""".format(str=STR)
