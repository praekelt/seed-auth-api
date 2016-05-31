from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from rest_framework.authtoken.models import Token
from rest_framework.request import Request
from rest_framework.reverse import reverse as drt_reverse
from rest_framework.test import APITestCase, APIRequestFactory

from authapi.models import SeedOrganization, SeedTeam


class AuthAPITestCase(APITestCase):
    def get_context(self, url):
        '''Returns the request context for a given url.'''
        factory = APIRequestFactory()
        request = factory.get(url)
        return {
            'request': Request(request)
        }

    def get_full_url(self, viewname, *args, **kwargs):
        '''Returns the full URL, with host and port. Takes the same arguments
        as reverse.'''
        factory = APIRequestFactory()
        part_url = reverse(viewname, *args, **kwargs)
        request = factory.get(part_url)
        kwargs['request'] = request
        return drt_reverse(viewname, *args, **kwargs)

    def create_admin_user(
            self, email='admin@example.org', password='password'):
        '''Creates an admin user, and creates a token for that admin user.'''
        user = User.objects.create_superuser(
            username=email, email=email, password=password)
        token = Token.objects.create(user=user)
        return (user, token)

    def create_user(
            self, email='test@example.org', password='password'):
        '''Create a user, and create a token for that user.'''
        user = User.objects.create_user(
            username=email, email=email, password=password)
        token = Token.objects.create(user=user)
        return (user, token)

    def add_permission(self, user, permission_type, object_id=''):
        '''Creates an organization, create a team for that org, adds the user
        to that team, and creates the permission on that team.'''
        org = SeedOrganization.objects.create()
        team = SeedTeam.objects.create(organization=org)
        team.users.add(user)
        team.permissions.create(type=permission_type, object_id=object_id)
