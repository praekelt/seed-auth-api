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
        'Django==1.9.6',
        'dj_database_url==0.4.1',
        'psycopg2==2.6.1',
    ],
    classifiers=[
        'Development Status :: 4 - Beta',
        'Framework :: Django',
        'License :: OSI Approved :: BSD License',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.4',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],
)
