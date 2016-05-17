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
