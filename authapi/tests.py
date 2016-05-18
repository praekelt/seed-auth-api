from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from rest_framework import status
from rest_framework.request import Request
from rest_framework.test import APITestCase, APIRequestFactory

from authapi.serializers import (
    UserSerializer, OrganizationSummarySerializer, TeamSummarySerializer)
from authapi.models import SeedTeam, SeedOrganization


class UserTests(APITestCase):
    def get_context(self, url):
        factory = APIRequestFactory()
        request = factory.get(url)
        return {
            'request': Request(request)
        }

    def test_get_account_list_empty(self):
        '''If there are no accounts, and empty list should be returned.'''
        response = self.client.get(reverse('user-list'))
        self.assertEqual(response.data, [])

    def test_get_account_list_multiple(self):
        '''If there are multiple users, it should return them all in a list.'''
        user1 = User.objects.create_user(username="user1@example.org")
        user2 = User.objects.create_user(username="user2@example.org")

        context = self.get_context(reverse('user-list'))
        expected = [
            UserSerializer(instance=u, context=context).data
            for u in [user1, user2]
        ]

        response = self.client.get(reverse('user-list'))
        self.assertEqual(sorted(expected), sorted(response.data))

    def test_create_user_no_required_fields(self):
        '''A POST request to the user endpoint should return an error if there
        is no email field, as it is required.'''
        response = self.client.post(reverse('user-list'), data={})
        self.assertEqual(response.data, {
            'email': ['This field is required.']
        })

    def test_create_user(self):
        '''A POST request to the user endpoint should create a user with all
        of the supplied details.'''
        data = {
            'email': 'user1@example.org',
            'first_name': 'user1',
            'last_name': 'example',
            'admin': True,
        }
        response = self.client.post(reverse('user-list'), data=data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        [user] = User.objects.all()
        self.assertEqual(user.username, data['email'])
        self.assertEqual(user.first_name, data['first_name'])
        self.assertEqual(user.last_name, data['last_name'])
        self.assertEqual(user.is_superuser, data['admin'])

    def test_update_user(self):
        '''A PUT request to the user's endpoint should update that specific
        user's details.'''
        user = User.objects.create_user('user@example.org')
        data = {
            'email': 'new@email.org',
            'first_name': 'new',
            'last_name': 'user',
            'admin': True,
        }
        response = self.client.put(
            reverse('user-detail', args=[user.id]), data=data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        user.refresh_from_db()
        self.assertEqual(user.username, data['email'])
        self.assertEqual(user.first_name, data['first_name'])
        self.assertEqual(user.last_name, data['last_name'])
        self.assertEqual(user.is_superuser, data['admin'])

    def test_get_user(self):
        '''A GET request to a specific user's endpoint should return the
        details for that user.'''
        user = User.objects.create_user(username='user@example.org')

        context = self.get_context(reverse('user-detail', args=[user.id]))

        expected = UserSerializer(instance=user, context=context).data
        response = self.client.get(reverse('user-detail', args=[user.id]))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, expected)

    def test_user_serializer(self):
        '''The user serializer should properly serialize the correct user
        data and foreign links.'''
        user = User.objects.create_superuser(
            'user@example.org', 'user@example.org', 'testpass',
            first_name='user', last_name='example')
        organization = SeedOrganization.objects.create()
        organization.users.add(user)
        team = SeedTeam.objects.create(organization=organization)
        team.users.add(user)

        url = reverse('user-detail', args=[user.id])
        context = self.get_context(url)

        data = UserSerializer(instance=user, context=context).data
        expected = {
            'email': 'user@example.org',
            'admin': True,
            'first_name': 'user',
            'last_name': 'example',
            'id': user.id,
            'teams': [TeamSummarySerializer(
                instance=team, context=context).data],
            'organizations': [OrganizationSummarySerializer(
                instance=organization, context=context).data],
            'url': data['url'],
        }

        self.assertEqual(data, expected)
