from figgis import Field, Config, ListField


def test_to_dict():
    class Conf(Config):
        one = Field()
        two = Field(dict)
        three = ListField()

    config = Conf(one='one', two={'foo': 'bar'}, three=['foo', 'bar'])
    assert config.to_dict() == {'one': 'one',
                                'two': {'foo': 'bar'},
                                'three': ['foo', 'bar']}


def test_to_dict_complex():
    class SubConf(Config):
        field = Field()

    class Conf(Config):
        subconf = Field(SubConf)

    config = Conf(subconf={'field': 'value'})
    assert config.to_dict() == {'subconf': {'field': 'value'}}


def test_to_dict_complex_list():
    class SubConf(Config):
        field = Field()

    class Conf(Config):
        subconf = ListField(SubConf)

    config = Conf(subconf=[{'field': 'value'}, {'field': 'value'}])
    assert config.to_dict() == {'subconf': [{'field': 'value'},
                                            {'field': 'value'}]}
