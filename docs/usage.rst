Usage
=====

Introduction
------------

.. py:module:: figgis

Using `figgis` involves defining one or more subclass of :class:`Config`, each
containing one or more :class:`Field` or :class:`ListField`.  These configs may
be used to consume json-like data structures (i.e. a dictionary containing only
primitive data types, lists, and other dictionaries.  Assuming that all of your
data is valid, the result will be an object with attributes that match the
fields that you defined and have the appropriate type.

By default, fields are strings.  However, you may use any data type that you
like, including arbitrary functions::

    >>> from datetime import datetime

    >>> class Event(Config):
    ...     
    ...     def parse_date(date_string):
    ...         return datetime.strptime(date_string, '%Y-%m-%d')
    ...
    ...     name = Field(required=True)
    ...     date = Field(parse_date, required=True)

    >>> birthday = Event(name="Jane's Birthday", date='1985-08-29')
    >>> birthday.date
    datetime.datetime(1985, 8, 29, 1, 0, 0)


Fields may also use another :class:`Config`, so that you can make
arbitrarily-nested data structures::

    
    >>> class Calendar(Class):
    ...
    ...     events = ListField(Event)


    >>> this_year = Calendar(events=[
    ...     {'name': 'My birthday', 'date': '2015-03-30'},
    ...     {'name': 'Your birthday', 'date': '2015-07-11'},
    ... ])
    >>> this_year.events[1].name
    'Your birthday'


`figgis` will throw an exception when your data does not match the definition::

    >>> Calendar(events=[
        {'date': '2014-01-01'},
    ])
    figgis.PropertyError: 'Missing property: events.0.name'


In addition to ensuring that all fields exist (if required) and are of the
proper type, `figgis` can check your data against any number of arbitrary
validation functions::

    >>> class Person(Config):
    ...     name = Field()
    ...     age = Field(int, validator=lambda value: value > 0)

    >>> Person(name='John', age=-1)
    figgis.ValidationError: Field 'age' is invalid

You may also make your validators throw more useful error messages::

    >>> from figgis import ValidationError

    >>> class Person(Config):
    ...     def validate_age(age):
    ...         if age < 0:
    ...             raise ValidationError('Should be a non-negative integer')
    ...         return True
    ...
    ...     name = Field()
    ...     age = Field(int, validator=validate_age)

    >>> Person(name='John', age=-1)
    figgis.ValidationError: Field 'age' is invalid: Should be a non-negative integer


Sometimes, you may have data that has keys that can not be used as python
variable names.  In this case, you can use the `key` argument to perform a
translation::

    >>> class WeirdData(Config):
    ...     irregular = Field(key='123-this is a bad field')

    >>> WeirdData({'123-this is a bad field': 'mydata'}).irregular
    'mydata'


API
---

.. autoclass:: Config
   :members:

.. autoclass:: Field
   :members: __init__

.. autoclass:: ListField
   :members:
