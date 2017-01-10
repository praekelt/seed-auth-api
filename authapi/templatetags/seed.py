from django import template

import seed_auth_api

register = template.Library()


@register.simple_tag
def current_version():
    return seed_auth_api.__version__
