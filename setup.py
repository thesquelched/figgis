import os.path
from setuptools import setup


CHANGELOG = os.path.join(os.path.abspath(os.path.dirname(__file__)),
                         'CHANGELOG.md')

if __name__ == '__main__':
    try:
        with open(CHANGELOG) as f:
            CHANGELOG = f.read().strip()
    except IOError:
        CHANGELOG = ''

    setup(
        name='figgis',
        version='1.4.0',

        description="Python declarative data validation",
        long_description=CHANGELOG,

        author='Scott Kruger',
        author_email='scott@chojin.org',
        url='http://github.com/thesquelched/figgis',

        py_modules=['figgis'],
    )
