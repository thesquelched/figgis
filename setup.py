# Copyright 2015 Yahoo! Inc.
# Copyrights licensed under the BSD License. See the accompanying LICENSE
# file for terms.

import os.path
from setuptools import setup, find_packages


CHANGELOG_PATH = os.path.join(
    os.path.abspath(os.path.dirname(__file__)),
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


def download_url():
    return 'https://github.com/thesquelched/figgis/tarball/{0}'.format(
        read_version())


def long_description(changelog):
    return """\
[Package Documentation](http://figgis.readthedocs.org/en/latest)

Changelog
---------

{changelog}
""".format(changelog=changelog)


if __name__ == '__main__':
    try:
        with open(CHANGELOG_PATH) as f:
            changelog = f.read().strip()
    except IOError:
        changelog = ''

    setup(
        name='figgis',
        version=read_version(),

        install_requires=[
            'six',
        ],

        description="Python declarative data validation",
        long_description=long_description(changelog),

        author='Scott Kruger',
        author_email='scott@chojin.org',
        url='https://github.com/thesquelched/figgis',
        download_url=download_url(),

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
