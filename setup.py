# Copyright 2015 Yahoo! Inc.
# Copyrights licensed under the BSD License. See the accompanying LICENSE
# file for terms.

import os.path
from setuptools import setup, find_packages


CHANGELOG = os.path.join(os.path.abspath(os.path.dirname(__file__)),
                         'CHANGELOG.md')


def read_version():
    path = os.path.join(
        os.path.abspath(os.path.dirname(__file__)),
        'figgis',
        '_version.py'
    )
    with open(path) as f:
        exec(f.read())
        return locals()['__version__']


if __name__ == '__main__':
    try:
        with open(CHANGELOG) as f:
            CHANGELOG = f.read().strip()
    except IOError:
        CHANGELOG = ''

    setup(
        name='figgis',
        version=read_version(),

        description="Python declarative data validation",
        long_description=CHANGELOG,

        author='Scott Kruger',
        author_email='scott@chojin.org',
        url='https://github.com/thesquelched/figgis',
        download_url='https://github.com/thesquelched/figgis/tarball/1.4.3',

        packages=find_packages(exclude=['tests']),

        classifiers=[
            'Development Status :: 5 - Production/Stable',
            'Intended Audience :: Developers',
            'License :: OSI Approved :: Apache Software License',
            'Operating System :: OS Independent',
            'Programming Language :: Python :: 2.6',
            'Programming Language :: Python :: 2.7',
            'Programming Language :: Python :: 3.2',
            'Programming Language :: Python :: 3.3',
            'Programming Language :: Python :: 3.4',
            'Topic :: Software Development :: Libraries',
        ]
    )
