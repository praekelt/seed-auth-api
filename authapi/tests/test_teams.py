from django.core.urlresolvers import reverse
from django.contrib.auth.models import User
from rest_framework import status

from authapi.serializers import (
    TeamSerializer, OrganizationSummarySerializer, TeamSummarySerializer,
    PermissionSerializer, UserSummarySerializer)
from authapi.models import SeedTeam, SeedOrganization, SeedPermission
from authapi.tests.base import AuthAPITestCase


class TeamTests(AuthAPITestCase):
    def test_get_team_list(self):
        '''A GET request on the teams endpoint should return a list of
        teams.'''
        _, token = self.create_admin_user()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)
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
        _, token = self.create_admin_user()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)
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
        _, token = self.create_admin_user()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)
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
        _, token = self.create_admin_user()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)
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

    def test_get_team_list_archived_invalid_queryparam(self):
        '''If the archived querystring parameter is not one of true, false, or
        both, an appropriate error should be returned.'''
        _, token = self.create_admin_user()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)
        response = self.client.get(
            '%s?archived=foo' % reverse('seedteam-list'))
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, {
            'archived': ['Must be one of [both, false, true]'],
        })

    def test_get_team_list_filter_permission_type(self):
        '''If the querystring argument permission_contains is present, we
        should only display teams that have that permission type.'''
        _, token = self.create_admin_user()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)
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
        _, token = self.create_admin_user()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)
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
        _, token = self.create_admin_user()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)
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
        '''Creating teams on this endpoint should not be allowed.'''
        _, token = self.create_admin_user()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)
        response = self.client.post(reverse('seedteam-list'), data={})
        self.assertEqual(
            response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_delete_team(self):
        '''Deleting a team should archive the team instead of removing it.'''
        _, token = self.create_admin_user()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)
        org = SeedOrganization.objects.create(title='test org')
        team = SeedTeam.objects.create(organization=org, title='test team')

        self.assertEqual(team.archived, False)

        self.client.delete(reverse('seedteam-detail', args=[team.id]))

        team.refresh_from_db()
        self.assertEqual(team.archived, True)

    def test_update_team(self):
        '''A PUT request to a team's endpoint should update an existing
        team.'''
        _, token = self.create_admin_user()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)
        organization = SeedOrganization.objects.create(title='test org')
        team = SeedTeam.objects.create(
            organization=organization, title='test team')
        url = reverse('seedteam-detail', args=[team.id])

        data = {
            'title': 'new team',
        }
        response = self.client.put(url, data=data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        team.refresh_from_db()
        self.assertEqual(team.title, data['title'])

    def test_update_team_organization(self):
        '''You shouldn't be able to change a team's organization.'''
        _, token = self.create_admin_user()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)
        org1 = SeedOrganization.objects.create(title='test org')
        org2 = SeedOrganization.objects.create(title='test org')
        team = SeedTeam.objects.create(organization=org1, title='test team')
        url = reverse('seedteam-detail', args=[team.id])

        data = {
            'title': 'new title',
            'organization': org2.pk,
        }
        response = self.client.put(url, data=data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, {
            'organization': ['This field can only be set on creation.']
        })

    def test_get_team(self):
        '''A GET request to a team's endpoint should return that team's
        details.'''
        _, token = self.create_admin_user()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)
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
            'organization': OrganizationSummarySerializer(
                instance=organization, context=context).data,
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
