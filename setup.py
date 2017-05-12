import codecs
import os
import re

from setuptools import setup, find_packages


HERE = os.path.abspath(os.path.dirname(__file__))


def read(*parts):  # Stolen from txacme
    with codecs.open(os.path.join(HERE, *parts), 'rb', 'utf-8') as f:
        return f.read()


def get_version(package):
    """
    Return package version as listed in `__version__` in `init.py`.
    """
    init_py = open(os.path.join(package, '__init__.py')).read()
    return re.search("__version__ = ['\"]([^'\"]+)['\"]", init_py).group(1)


version = get_version('seed_auth_api')


setup(
    name='seed-auth-api',
    version=version,
    url='https://github.com/praekelt/seed-auth-api',
    license='BSD',
    description='Seed Auth API',
    long_description=read('README.rst'),
    author='Praekelt.org',
    author_email='dev@praekelt.org',
    packages=find_packages(),
    include_all_package_data=True,
    install_requires=[
        'Django==1.11.1',
        'dj-database-url==0.4.2',
        'psycopg2cffi==2.7.5',
        'djangorestframework==3.6.3',
        'drf-extensions==0.3.1',
        'djangorestframework-composed-permissions==0.1',
        'raven==6.0.0',
    ],
    classifiers=[
        'Development Status :: 4 - Beta',
        'Framework :: Django',
        'License :: OSI Approved :: BSD License',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],
)
