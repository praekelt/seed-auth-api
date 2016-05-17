[![Coverage Status](https://coveralls.io/repos/github/praekelt/seed-auth-api/badge.svg?branch=develop)](https://coveralls.io/github/praekelt/seed-auth-api?branch=develop)
[![Build Status](https://travis-ci.org/praekelt/seed-auth-api.svg?branch=develop)](https://travis-ci.org/praekelt/seed-auth-api)
[![Requirements Status](https://requires.io/github/praekelt/seed-auth-api/requirements.svg?branch=feature%2Fissue-2-create-django-skeleton)](https://requires.io/github/praekelt/seed-auth-api/requirements/?branch=feature%2Fissue-2-create-django-skeleton)

# seed-auth-api
Seed Auth API. User and permissions store, authentication and authorization.

## Running

 * `pip install -e .`
 * `psql -U postgres -c "CREATE DATABASE seed_auth;"
 * `./manage.py migrate`
 * `./manage.py createsuperuser`
 * `./manage.py runserver --settings=seed_auth_api.testsettings`

## Running tests

 * `pip install -e .`
 * `pip install -r requirements-dev.txt`
 * `py.test --ds=seed_auth_api.testsettings */tests.py`
