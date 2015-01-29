import os.path
from setuptools import setup


if __name__ == '__main__':
    try:
        with open(os.path.join(os.path.dirname(__file__), 'CHANGELOG.md')) as f:
            CHANGELOG = f.read().strip()
    except IOError:
        CHANGELOG = ''

    setup(
        name='figgis',
        version='1.0.1',

        description="Checked YAML configuration",
        long_description=CHANGELOG,

        author='Scott Kruger',
        author_email='scott@chojin.org',
        url='http://github.com/thesquelched/figgis',

        py_modules=['figgis'],
    )
