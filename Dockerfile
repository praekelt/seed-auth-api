# TODO: Add production Dockerfile to
# https://github.com/praekeltfoundation/docker-seed
FROM praekeltfoundation/django-bootstrap:py2

COPY . /app
RUN pip install -e .

ENV DJANGO_SETTINGS_MODULE "seed_auth_api.settings"
RUN python manage.py collectstatic --noinput
CMD ["seed_auth_api.wsgi:application"]
