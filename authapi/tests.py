from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from rest_framework import status
from rest_framework.request import Request
from rest_framework.reverse import reverse as drt_reverse
from rest_framework.test import APITestCase, APIRequestFactory

from authapi.serializers import (
    UserSerializer, TeamSerializer, OrganizationSummarySerializer,
    TeamSummarySerializer, PermissionSerializer, UserSummarySerializer,
    OrganizationSerializer)
from authapi.models import SeedTeam, SeedOrganization, SeedPermission


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


class UserTests(AuthAPITestCase):
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

        url = self.get_full_url('user-detail', args=[user.id])
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
            'url': url,
        }

        self.assertEqual(data, expected)

    def test_user_summary_serializer(self):
        '''The user summary serializer should return the correct summarized
        information.'''
        user = User.objects.create_user('user@example.org')
        url = self.get_full_url('user-detail', args=[user.id])
        context = self.get_context(url)

        data = UserSummarySerializer(instance=user, context=context).data
        self.assertEqual(data, {
            'url': url,
            'id': user.id,
        })


class TeamTests(AuthAPITestCase):
    def test_get_team_list(self):
        '''A GET request on the teams endpoint should return a list of teams.'''
        organization = SeedOrganization.objects.create()
        team1 = SeedTeam.objects.create(organization=organization)
        team2 = SeedTeam.objects.create(organization=organization)
        url = reverse('seedteam-list')

        context = self.get_context(url)
        expected = [
            TeamSerializer(instance=t, context=context).data
            for t in [team1, team2]
        ]

        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(sorted(expected), sorted(response.data))

    def test_create_team(self):
        '''A POST request on the teams endpoint should create a team.'''
        organization = SeedOrganization.objects.create()
        response = self.client.post(reverse('seedteam-list'), data={
            'organization': organization.id,
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        [team] = SeedTeam.objects.all()
        self.assertEqual(team.organization, organization)

    def test_create_team_no_required_fields(self):
        '''An error should be returned if there is no organization field.'''
        response = self.client.post(reverse('seedteam-list'), data={})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.data, {'organization': ['This field is required.']})

    def test_update_team(self):
        '''A PUT request to a team's endpoint should update an existing team.'''
        organization1 = SeedOrganization.objects.create()
        organization2 = SeedOrganization.objects.create()
        team = SeedTeam.objects.create(organization=organization1)
        url = reverse('seedteam-detail', args=[team.id])

        response = self.client.put(url, data={'organization': organization2.id})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        team.refresh_from_db()
        self.assertEqual(team.organization, organization2)

    def test_get_team(self):
        '''A GET request to a team's endpoint should return that team's
        details.'''
        organization = SeedOrganization.objects.create()
        team = SeedTeam.objects.create(organization=organization)
        url = reverse('seedteam-detail', args=[team.id])
        context = self.get_context(url)

        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        expected = TeamSerializer(instance=team, context=context)
        self.assertEqual(response.data, expected.data)

    def test_serializer(self):
        '''The TeamSerializer should return the correct information.'''
        organization = SeedOrganization.objects.create()
        team = SeedTeam.objects.create(organization=organization)
        user = User.objects.create_user('foo@bar.org')
        team.users.add(user)
        permission = SeedPermission.objects.create()
        team.permissions.add(permission)
        url = self.get_full_url('seedteam-detail', args=[team.id])
        context = self.get_context(url)

        data = TeamSerializer(instance=team, context=context).data
        self.assertEqual(data, {
            'url': url,
            'organization': organization.id,
            'permissions': [
                PermissionSerializer(instance=permission, context=context).data
            ],
            'id': team.id,
            'users': [
                UserSummarySerializer(instance=user, context=context).data],
        })

    def test_summary_serializer(self):
        '''The TeamSummarySerializer should return the correct summary
        information.'''
        organization = SeedOrganization.objects.create()
        team = SeedTeam.objects.create(organization=organization)
        url = self.get_full_url('seedteam-detail', args=[team.id])
        context = self.get_context(url)

        data = TeamSummarySerializer(instance=team, context=context).data
        self.assertEqual(data, {
            'url': url,
            'id': team.id
        })


class OrganizationTests(AuthAPITestCase):
    def test_get_organization_list(self):
        '''A GET request to the organizations endpoint should return a list
        of organizations.'''
        org1 = SeedOrganization.objects.create()
        org2 = SeedOrganization.objects.create()
        url = reverse('seedorganization-list')
        context = self.get_context(url)

        expected = [
            OrganizationSerializer(instance=o, context=context).data
            for o in [org1, org2]
        ]

        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(sorted(expected), sorted(response.data))

    def test_create_organization(self):
        '''A POST request to the organizations endpoint should create a new
        organization.'''
        response = self.client.post(reverse('seedorganization-list'), data={})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        [org] = SeedOrganization.objects.all()
        self.assertEqual(org.id, response.data['id'])

    def test_get_organization(self):
        '''A GET request to an organization's endpoint should return the
        organization's details.'''
        organization = SeedOrganization.objects.create()
        url = reverse('seedorganization-detail', args=[organization.id])
        context = self.get_context(url)

        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        expected = OrganizationSerializer(
            instance=organization, context=context)
        self.assertEqual(response.data, expected.data)

    def test_serializer(self):
        '''The organization serializer should return the correct information.'''
        organization = SeedOrganization.objects.create()
        user = User.objects.create_user('foo@bar.org')
        organization.users.add(user)
        team = organization.seedteam_set.create()
        url = self.get_full_url(
            'seedorganization-detail', args=[organization.id])
        context = self.get_context(url)

        data = OrganizationSerializer(
            instance=organization, context=context).data
        self.assertEqual(data, {
            'url': url,
            'id': organization.id,
            'users': [
                UserSummarySerializer(instance=user, context=context).data],
            'teams': [
                TeamSummarySerializer(instance=team, context=context).data],
        })

    def test_summary_serializer(self):
        '''The organization summary serializer should return the correct
        summarized information.'''
        organization = SeedOrganization.objects.create()
        url = self.get_full_url(
            'seedorganization-detail', args=[organization.id])
        context = self.get_context(url)

        data = OrganizationSummarySerializer(
            instance=organization, context=context).data
        self.assertEqual(data, {
            'url': url,
            'id': organization.id,
        })
