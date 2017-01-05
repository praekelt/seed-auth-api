from setuptools import setup, find_packages

setup(
    name='seed-auth-api',
    version='0.0.0',
    url='https://github.com/praekelt/seed-auth-api',
    license='BSD',
    author='Praekelt Foundation',
    author_email='dev@praekeltfoundation.org',
    packages=find_packages(),
    include_all_package_data=True,
    install_requires=[
        'Django==1.10.5',
        'dj-database-url==0.4.2',
        'psycopg2cffi==2.7.5',
        'djangorestframework==3.5.3',
        'drf-extensions==0.3.1',
        'djangorestframework-composed-permissions==0.1',
        'raven==5.32.0',
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
