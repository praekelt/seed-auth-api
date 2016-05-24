from django.contrib.auth.models import User
from django.contrib.auth.hashers import check_password
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
        self.assertEqual(
            sorted(expected, key=lambda i: i['id']),
            sorted(response.data, key=lambda i: i['id']))

    def test_get_user_list_no_inactive(self):
        '''If there are any inactive users, they shouldn't appear in the list
        of users.'''
        user = User.objects.create_user('user@example.org')

        response = self.client.get(reverse('user-list'))
        self.assertEqual(len(response.data), 1)

        user.is_active = False
        user.save()

        response = self.client.get(reverse('user-list'))
        self.assertEqual(len(response.data), 0)

    def test_get_user_list_active_queryparam_true(self):
        '''If the queryparam active is set to false, then we should return
        all active users.'''
        user = User.objects.create_user('test user')

        response = self.client.get(
            '%s?active=false' % reverse('user-list'))
        self.assertEqual(len(response.data), 0)

        user.is_active = False
        user.save()
        response = self.client.get(
            '%s?active=false' % reverse('user-list'))
        self.assertEqual(len(response.data), 1)

    def test_get_user_list_active_queryparam_both(self):
        '''If the queryparam active is set to both, then we should return
        both active and inactive users.'''
        user = User.objects.create_user('test user')
        user.is_active = False
        user.save()
        User.objects.create_user('test user 2')

        response = self.client.get(reverse('user-list'))
        self.assertEqual(len(response.data), 1)

        response = self.client.get(
            '%s?active=both' % reverse('user-list'))
        self.assertEqual(len(response.data), 2)

    def test_create_user_no_required_fields(self):
        '''A POST request to the user endpoint should return an error if there
        is no email field, as it is required.'''
        response = self.client.post(reverse('user-list'), data={})
        self.assertEqual(response.data, {
            'email': ['This field is required.'],
            'password': ['This field is required.'],
        })

    def test_create_superuser(self):
        '''A POST request to the user endpoint should create a user with all
        of the supplied details. If admin is True a superuser should be
        created.'''
        data = {
            'email': 'user1@example.org',
            'password': 'testpassword',
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
        self.assertTrue(check_password(data['password'], user.password))

    def test_create_user(self):
        '''A POST request to the user endpoint should create a user with all
        of the supplied details. If admin is false a normal user should be
        created.'''
        data = {
            'email': 'user1@example.org',
            'password': 'testpassword',
            'first_name': 'user1',
            'last_name': 'example',
            'admin': False,
        }
        response = self.client.post(reverse('user-list'), data=data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        [user] = User.objects.all()
        self.assertEqual(user.username, data['email'])
        self.assertEqual(user.first_name, data['first_name'])
        self.assertEqual(user.last_name, data['last_name'])
        self.assertEqual(user.is_superuser, data['admin'])
        self.assertTrue(check_password(data['password'], user.password))

    def test_update_user(self):
        '''A PUT request to the user's endpoint should update that specific
        user's details.'''
        user = User.objects.create_user('user@example.org')
        data = {
            'email': 'new@email.org',
            'password': 'newpassword',
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
        self.assertTrue(check_password(data['password'], user.password))

    def test_get_user(self):
        '''A GET request to a specific user's endpoint should return the
        details for that user.'''
        user = User.objects.create_user(username='user@example.org')

        context = self.get_context(reverse('user-detail', args=[user.id]))

        expected = UserSerializer(instance=user, context=context).data
        response = self.client.get(reverse('user-detail', args=[user.id]))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, expected)

    def test_delete_user(self):
        '''A DELETE request on a user should not delete it, but instead set
        the user to be inactive.'''
        user = User.objects.create_user(username='user@example.org')
        self.assertTrue(user.is_active)

        response = self.client.delete(reverse('user-detail', args=[user.id]))

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        user.refresh_from_db()
        self.assertFalse(user.is_active)

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
            'email': user.email,
            'admin': user.is_superuser,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'id': user.id,
            'teams': [TeamSummarySerializer(
                instance=team, context=context).data],
            'organizations': [OrganizationSummarySerializer(
                instance=organization, context=context).data],
            'url': url,
            'active': user.is_active,
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
        '''A GET request on the teams endpoint should return a list of
        teams.'''
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
        self.assertEqual(
            sorted(expected, key=lambda i: i['id']),
            sorted(response.data, key=lambda i: i['id']))

    def test_get_team_list_archived(self):
        '''When getting the list of teams, archived teams should not be
        shown.'''
        org = SeedOrganization.objects.create(title='test org')
        team = SeedTeam.objects.create(organization=org, title='test team')

        response = self.client.get(reverse('seedteam-list'))
        self.assertEqual(len(response.data), 1)

        team.archived = True
        team.save()
        response = self.client.get(reverse('seedteam-list'))
        self.assertEqual(len(response.data), 0)

    def test_get_team_list_archived_queryparam_true(self):
        '''If the queryparam archived is set to true, then we should return
        all archived teams.'''
        org = SeedOrganization.objects.create(title='test org')
        team = SeedTeam.objects.create(organization=org, title='test team')

        response = self.client.get(
            '%s?archived=true' % reverse('seedteam-list'))
        self.assertEqual(len(response.data), 0)

        team.archived = True
        team.save()
        response = self.client.get(
            '%s?archived=true' % reverse('seedteam-list'))
        self.assertEqual(len(response.data), 1)

    def test_get_team_list_archived_queryparam_both(self):
        '''If the queryparam archived is set to both, then we should return
        both archived and non-archived teams.'''
        org = SeedOrganization.objects.create(title='test org')
        team = SeedTeam.objects.create(organization=org, title='test team')
        team.archived = True
        team.save()
        SeedTeam.objects.create(organization=org, title='test team')

        response = self.client.get(reverse('seedteam-list'))
        self.assertEqual(len(response.data), 1)

        response = self.client.get(
            '%s?archived=both' % reverse('seedteam-list'))
        self.assertEqual(len(response.data), 2)

    def test_get_team_list_filter_permission_type(self):
        '''If the querystring argument permission_contains is present, we
        should only display teams that have that permission type.'''
        org = SeedOrganization.objects.create(title='test org')
        team1 = SeedTeam.objects.create(title='team 1', organization=org)
        perm = team1.permissions.create(
            type='bar:foo:bar', object_id='2', namespace='bar')
        team2 = SeedTeam.objects.create(title='team 2', organization=org)
        team2.permissions.create(
            type='bar:bar:bar', object_id='3', namespace='foo')

        response = self.client.get(
            '%s?permission_contains=foo' % reverse('seedteam-list'))
        self.assertEqual(len(response.data), 1)
        self.assertEqual(
            response.data[0]['permissions'][0]['type'],
            perm.type)

    def test_get_team_list_filter_object_id(self):
        '''If the querystring argument object_id is present, we should only
        display teams that have that object id in one of their permissions.'''
        org = SeedOrganization.objects.create(title='test org')
        team1 = SeedTeam.objects.create(title='team 1', organization=org)
        perm = team1.permissions.create(
            type='bar:foo:bar', object_id='2', namespace='bar')
        team2 = SeedTeam.objects.create(title='team 2', organization=org)
        team2.permissions.create(
            type='bar:bar:bar', object_id='3', namespace='foo')

        response = self.client.get(
            '%s?object_id=2' % reverse('seedteam-list'))
        self.assertEqual(len(response.data), 1)
        self.assertEqual(
            response.data[0]['permissions'][0]['object_id'],
            perm.object_id)

    def test_get_team_list_archived_users(self):
        '''When getting the list of teams, inactive users should not appear
        on the list of users.'''
        org = SeedOrganization.objects.create(title='test org')
        team = SeedTeam.objects.create(title='test team', organization=org)
        user = User.objects.create_user('test user')
        team.users.add(user)

        response = self.client.get(reverse('seedteam-list'))
        self.assertEqual(len(response.data[0]['users']), 1)

        user.is_active = False
        user.save()
        response = self.client.get(reverse('seedteam-list'))
        self.assertEqual(len(response.data[0]['users']), 0)

    def test_create_team(self):
        '''A POST request on the teams endpoint should create a team.'''
        organization = SeedOrganization.objects.create()
        data = {
            'organization': organization.id,
            'title': 'test team',
        }
        response = self.client.post(reverse('seedteam-list'), data=data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        [team] = SeedTeam.objects.all()
        self.assertEqual(team.organization, organization)
        self.assertEqual(team.title, data['title'])

    def test_delete_team(self):
        '''Deleting a team should archive the team instead of removing it.'''
        org = SeedOrganization.objects.create(title='test org')
        team = SeedTeam.objects.create(organization=org, title='test team')

        self.assertEqual(team.archived, False)

        self.client.delete(reverse('seedteam-detail', args=[team.id]))

        team.refresh_from_db()
        self.assertEqual(team.archived, True)

    def test_create_team_no_required_fields(self):
        '''An error should be returned if there is no organization field.'''
        response = self.client.post(reverse('seedteam-list'), data={})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.data, {
                'organization': ['This field is required.'],
                'title': ['This field is required.'],
            })

    def test_update_team(self):
        '''A PUT request to a team's endpoint should update an existing
        team.'''
        organization1 = SeedOrganization.objects.create(title='org one')
        organization2 = SeedOrganization.objects.create(title='org two')
        team = SeedTeam.objects.create(
            organization=organization1, title='test team')
        url = reverse('seedteam-detail', args=[team.id])

        data = {
            'organization': organization2.id,
            'title': 'new team',
        }
        response = self.client.put(url, data=data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        team.refresh_from_db()
        self.assertEqual(team.organization, organization2)
        self.assertEqual(team.title, data['title'])

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
        team = SeedTeam.objects.create(
            organization=organization, title='test team')
        user = User.objects.create_user('foo@bar.org')
        team.users.add(user)
        permission = SeedPermission.objects.create()
        team.permissions.add(permission)
        url = self.get_full_url('seedteam-detail', args=[team.id])
        context = self.get_context(url)

        data = TeamSerializer(instance=team, context=context).data
        self.assertEqual(data, {
            'title': team.title,
            'url': url,
            'organization': organization.id,
            'permissions': [
                PermissionSerializer(instance=permission, context=context).data
            ],
            'id': team.id,
            'users': [
                UserSummarySerializer(instance=user, context=context).data],
            'archived': team.archived,
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

    def test_add_permission_to_team(self):
        '''When adding a permission to a team, it should create a permission
        and link it to that team.'''
        org = SeedOrganization.objects.create(title='test org')
        team = SeedTeam.objects.create(title='test team', organization=org)
        self.assertEqual(len(team.permissions.all()), 0)

        data = {
            'type': 'foo:bar',
            'object_id': '2',
            'namespace': 'foo',
        }
        response = self.client.post(
            reverse('seedteam-permissions-list', args=[team.id]), data=data)

        [permission] = SeedPermission.objects.all()
        self.assertEqual(response.data, {
            'type': data['type'],
            'object_id': data['object_id'],
            'namespace': data['namespace'],
            'id': permission.id
        })
        self.assertEqual(len(team.permissions.all()), 1)

    def test_remove_permission_from_team(self):
        '''When removing a permission from a team, it should remove the
        relation between the team and permission, and delete that
        permission.'''
        org = SeedOrganization.objects.create(title='test org')
        team = SeedTeam.objects.create(title='test team', organization=org)
        permission = team.permissions.create(
            type='foo:bar', object_id='2', namespace='foo')
        self.assertEqual(len(team.permissions.all()), 1)

        response = self.client.delete(
            reverse(
                'seedteam-permissions-detail', args=[team.id, permission.id]))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        self.assertEqual(len(team.permissions.all()), 0)
        self.assertEqual(len(SeedPermission.objects.all()), 0)

    def test_add_user_to_team(self):
        '''Adding a user to a team should create a relationship between the
        two.'''
        org = SeedOrganization.objects.create(title='test org')
        team = SeedTeam.objects.create(title='test team', organization=org)
        user = User.objects.create_user(username='test@example.org')
        self.assertEqual(len(team.users.all()), 0)

        response = self.client.post(
            reverse('seedteam-users-list', args=[team.id]), {
                'user_id': user.id
            })
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        team.refresh_from_db()
        self.assertEqual(len(team.users.all()), 1)

    def test_remove_user_from_team(self):
        '''Removing a user from a team should remove the relationship between
        the two.'''
        org = SeedOrganization.objects.create(title='test org')
        team = SeedTeam.objects.create(title='test team', organization=org)
        user = User.objects.create_user(username='test@example.org')
        team.users.add(user)
        self.assertEqual(len(team.users.all()), 1)

        response = self.client.delete(
            reverse('seedteam-users-detail', args=[team.id, user.id]))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        team.refresh_from_db()
        self.assertEqual(len(team.users.all()), 0)


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
        self.assertEqual(
            sorted(expected, key=lambda i: i['id']),
            sorted(response.data, key=lambda i: i['id']))

    def test_get_organization_list_archived(self):
        '''Archived organizations should not appear on the list of
        organizations.'''
        org = SeedOrganization.objects.create(title='test org')

        response = self.client.get(reverse('seedorganization-list'))
        self.assertEqual(len(response.data), 1)

        org.archived = True
        org.save()
        response = self.client.get(reverse('seedorganization-list'))
        self.assertEqual(len(response.data), 0)

    def test_get_organization_list_archived_true_queryparam(self):
        '''If the queryparam archived is true, show only archived
        organizations.'''
        org = SeedOrganization.objects.create(title='test org')

        response = self.client.get(
            '%s?archived=true' % reverse('seedorganization-list'))
        self.assertEqual(len(response.data), 0)

        org.archived = True
        org.save()
        response = self.client.get(
            '%s?archived=true' % reverse('seedorganization-list'))
        self.assertEqual(len(response.data), 1)

    def test_get_organization_list_archived_false_queryparam(self):
        '''If the queryparam archived is false, show only non-archived
        organizations.'''
        org = SeedOrganization.objects.create(title='test org')

        response = self.client.get(
            '%s?archived=false' % reverse('seedorganization-list'))
        self.assertEqual(len(response.data), 1)

        org.archived = True
        org.save()
        response = self.client.get(
            '%s?archived=false' % reverse('seedorganization-list'))
        self.assertEqual(len(response.data), 0)

    def test_get_organization_list_archived_both_queryparam(self):
        '''If the queryparam archived is both, show all organizations.'''
        org1 = SeedOrganization.objects.create(title='test org')
        org1.archived = True
        org1.save()
        SeedOrganization.objects.create(title='test org')

        response = self.client.get(
            '%s?archived=both' % reverse('seedorganization-list'))
        self.assertEqual(len(response.data), 2)

        response = self.client.get(reverse('seedorganization-list'))
        self.assertEqual(len(response.data), 1)

    def test_get_organization_list_archived_teams(self):
        '''When getting the list of organizations, the archived teams should
        not be visible.'''
        org = SeedOrganization.objects.create(title='test org')
        team = SeedTeam.objects.create(title='test team', organization=org)

        response = self.client.get(reverse('seedorganization-list'))
        self.assertEqual(len(response.data[0]['teams']), 1)

        team.archived = True
        team.save()
        response = self.client.get(reverse('seedorganization-list'))
        self.assertEqual(len(response.data[0]['teams']), 0)

    def test_get_organization_list_inactive_users(self):
        '''When getting the list of organizations, the inactive users should
        not be shown in the list of users.'''
        org = SeedOrganization.objects.create(title='test org')
        user = User.objects.create_user('test user')
        org.users.add(user)

        response = self.client.get(reverse('seedorganization-list'))
        self.assertEqual(len(response.data[0]['users']), 1)

        user.is_active = False
        user.save()
        response = self.client.get(reverse('seedorganization-list'))
        self.assertEqual(len(response.data[0]['users']), 0)

    def test_create_organization_no_required(self):
        '''If the POST request is missing required field, an error should be
        returned.'''
        response = self.client.post(reverse('seedorganization-list'))
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, {
            'title': ['This field is required.']
        })

    def test_create_organization(self):
        '''A POST request to the organizations endpoint should create a new
        organization.'''
        data = {
            'title': 'test org',
        }
        response = self.client.post(
            reverse('seedorganization-list'), data=data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        [org] = SeedOrganization.objects.all()
        self.assertEqual(org.id, response.data['id'])
        self.assertEqual(org.title, data['title'])

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

    def test_delete_organization(self):
        '''A DELETE request on an organization should archive it.'''
        org = SeedOrganization.objects.create(title='test org')
        self.assertFalse(org.archived)

        response = self.client.delete(
            reverse('seedorganization-detail', args=[org.id]))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        org.refresh_from_db()
        self.assertTrue(org.archived)

    def test_serializer(self):
        '''The organization serializer should return the correct
        information.'''
        organization = SeedOrganization.objects.create(title='testorg')
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
            'archived': organization.archived,
            'title': organization.title,
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

    def test_add_user_to_organization(self):
        '''Adding a user to an organization should create a relationship
        between the two.'''
        org = SeedOrganization.objects.create(title='test org')
        user = User.objects.create_user(username='test@example.org')
        self.assertEqual(len(org.users.all()), 0)

        response = self.client.post(
            reverse('seedorganization-users-list', args=[org.id]), {
                'user_id': user.id
            })
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        org.refresh_from_db()
        self.assertEqual(len(org.users.all()), 1)

    def test_add_missing_user_to_organization(self):
        '''If a non-existing user is trying to be added to an organization,
        an appropriate error should be returned.'''
        org = SeedOrganization.objects.create(title='test org')

        response = self.client.post(
            reverse('seedorganization-users-list', args=[org.id]), {
                'user_id': 7,
            })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, {
            'user_id': ['Invalid pk "7" - object does not exist.']
        })

    def test_remove_user_from_organization(self):
        '''Removing a user from an organization should remove the relationship
        between the two.'''
        org = SeedOrganization.objects.create(title='test org')
        user = User.objects.create_user(username='test@example.org')
        org.users.add(user)
        self.assertEqual(len(org.users.all()), 1)

        response = self.client.delete(
            reverse('seedorganization-users-detail', args=[org.id, user.id]))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        org.refresh_from_db()
        self.assertEqual(len(org.users.all()), 0)
