FROM praekeltfoundation/django-bootstrap:onbuild
ENV DJANGO_SETTINGS_MODULE "seed_auth_api.settings"
RUN ./manage.py collectstatic --noinput
ENV APP_MODULE "seed_auth_api.wsgi:application"
