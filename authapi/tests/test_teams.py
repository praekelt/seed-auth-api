from django.core.urlresolvers import reverse
from django.contrib.auth.models import User
from rest_framework import status

from authapi.serializers import (
    TeamSerializer, OrganizationSummarySerializer, TeamSummarySerializer,
    PermissionSerializer, UserSummarySerializer)
from authapi.models import SeedTeam, SeedOrganization, SeedPermission
from authapi.tests.base import AuthAPITestCase


class TeamTests(AuthAPITestCase):
    def setUp(self):
        self.patch_client_data_json()

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

    def test_permissions_team_list_unauthorized(self):
        '''Unauthorized users shouldn't be able to see team list.'''
        url = reverse('seedteam-list')

        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_permissions_team_list_member_of_team(self):
        '''Teams that a user is a member of should be displayed on the list.'''
        url = reverse('seedteam-list')

        user, token = self.create_user()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)

        org = SeedOrganization.objects.create()
        team1 = SeedTeam.objects.create(organization=org)
        SeedTeam.objects.create(organization=org)
        team1.users.add(user)
        response = self.client.get(url)
        [team] = response.data
        self.assertEqual(team['id'], team1.pk)

    def test_permissions_team_list_admin_permission(self):
        '''Teams that a user has 'team:admin' permission for should be
        displayed on the list.'''
        url = reverse('seedteam-list')

        user, token = self.create_user()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)

        org = SeedOrganization.objects.create()
        team1 = SeedTeam.objects.create(organization=org)
        team2 = SeedTeam.objects.create(organization=org)
        self.add_permission(user, 'team:admin', team1.pk)
        response = self.client.get(url)
        self.assertTrue(team2.pk not in [t['id'] for t in response.data])

    def test_permissions_team_list_org_member(self):
        '''Teams that are a part of an organization that the user is part of
        should be displayed in the team list.'''
        url = reverse('seedteam-list')

        user, token = self.create_user()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)

        org = SeedOrganization.objects.create()
        org.users.add(user)
        team = SeedTeam.objects.create(organization=org)
        response = self.client.get(url)
        [resp_team] = response.data
        self.assertEqual(team.pk, resp_team['id'])

    def test_permissions_team_list_org_admin(self):
        '''Teams that are a part of an organization that a user has org:admin
        permission for should be displayed on the list.'''
        url = reverse('seedteam-list')

        user, token = self.create_user()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)

        org = SeedOrganization.objects.create()
        team = SeedTeam.objects.create(organization=org)
        self.add_permission(user, 'org:admin', org.pk)
        response = self.client.get(url)
        self.assertTrue(team.pk in [t['id'] for t in response.data])

    def test_permissions_team_list_admin(self):
        '''Admin users should be able to see all teams.'''
        url = reverse('seedteam-list')

        user, token = self.create_admin_user()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)

        org = SeedOrganization.objects.create()
        team = SeedTeam.objects.create(organization=org)
        response = self.client.get(url)
        [resp_team] = response.data
        self.assertTrue(team.pk, resp_team['id'])

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

    def test_permission_delete_team_unauthorized(self):
        '''Unauthorized users shouldn't be able to delete teams.'''
        org = SeedOrganization.objects.create()
        team = SeedTeam.objects.create(organization=org)
        url = reverse('seedteam-detail', args=(team.pk,))

        resp = self.client.delete(url)
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_permission_delete_team_admin_permission(self):
        '''Users with team:admin permission for that team should be able to
        delete that team.'''
        org = SeedOrganization.objects.create()
        team1 = SeedTeam.objects.create(organization=org)
        team2 = SeedTeam.objects.create(organization=org)
        user, token = self.create_user()
        self.add_permission(user, 'team:admin', team1.pk)
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)

        url = reverse('seedteam-detail', args=(team1.pk,))
        resp = self.client.delete(url)
        self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT)

        url = reverse('seedteam-detail', args=(team2.pk,))
        resp = self.client.delete(url)
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_permission_delete_team_org_admin_permission(self):
        '''Users with org:admin permission for a team's organization should
        be able to delete the team.'''
        org1 = SeedOrganization.objects.create()
        org2 = SeedOrganization.objects.create()
        team1 = SeedTeam.objects.create(organization=org1)
        team2 = SeedTeam.objects.create(organization=org2)
        user, token = self.create_user()
        self.add_permission(user, 'org:admin', org1.pk)
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)

        url = reverse('seedteam-detail', args=(team1.pk,))
        resp = self.client.delete(url)
        self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT)

        url = reverse('seedteam-detail', args=(team2.pk,))
        resp = self.client.delete(url)
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_permission_delete_team_admin_user(self):
        '''Admin users should be able to delete any team.'''
        org = SeedOrganization.objects.create()
        team = SeedTeam.objects.create(organization=org)
        user, token = self.create_admin_user()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)

        url = reverse('seedteam-detail', args=(team.pk,))
        resp = self.client.delete(url)
        self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT)

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

    def test_permission_update_team_unauthorized(self):
        '''Unauthorized users shouldn't be able to update teams.'''
        org = SeedOrganization.objects.create()
        team = SeedTeam.objects.create(organization=org)
        url = reverse('seedteam-detail', args=(team.pk,))
        data = {'title': 'test team'}

        resp = self.client.put(url, data=data)
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_permission_update_team_admin_permission(self):
        '''Users with team:admin permission for that team should be able to
        modify that team.'''
        org = SeedOrganization.objects.create()
        team1 = SeedTeam.objects.create(organization=org)
        team2 = SeedTeam.objects.create(organization=org)
        data = {'title': 'test team'}
        user, token = self.create_user()
        self.add_permission(user, 'team:admin', team1.pk)
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)

        url = reverse('seedteam-detail', args=(team1.pk,))
        resp = self.client.put(url, data=data)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

        url = reverse('seedteam-detail', args=(team2.pk,))
        resp = self.client.put(url, data=data)
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_permission_update_team_org_admin_permission(self):
        '''Users with org:admin permission for a team's organization should
        be able to update the team.'''
        org1 = SeedOrganization.objects.create()
        org2 = SeedOrganization.objects.create()
        team1 = SeedTeam.objects.create(organization=org1)
        team2 = SeedTeam.objects.create(organization=org2)
        data = {'title': 'test team'}
        user, token = self.create_user()
        self.add_permission(user, 'org:admin', org1.pk)
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)

        url = reverse('seedteam-detail', args=(team1.pk,))
        resp = self.client.put(url, data=data)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

        url = reverse('seedteam-detail', args=(team2.pk,))
        resp = self.client.put(url, data=data)
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_permission_update_team_admin_user(self):
        '''Admin users should be able to update any team.'''
        org = SeedOrganization.objects.create()
        team = SeedTeam.objects.create(organization=org)
        data = {'title': 'test team'}
        user, token = self.create_admin_user()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)

        url = reverse('seedteam-detail', args=(team.pk,))
        resp = self.client.put(url, data=data)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

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

    def test_permission_get_team_unauthorized(self):
        '''Only authorized users should be able to access team details.'''
        org = SeedOrganization.objects.create()
        team = SeedTeam.objects.create(organization=org)
        url = reverse('seedteam-detail', args=(team.pk,))
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_permission_get_team_member_of_team(self):
        '''Users that are a member of a team should be able to access that
        team's details.'''
        org = SeedOrganization.objects.create()
        team = SeedTeam.objects.create(organization=org)
        user, token = self.create_user()
        team.users.add(user)

        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)
        url = reverse('seedteam-detail', args=(team.pk,))
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_permission_get_team_admin_permission(self):
        '''Users that have a team:admin permissions for the team should be able
        to see the team details.'''
        org = SeedOrganization.objects.create()
        team1 = SeedTeam.objects.create(organization=org)
        team2 = SeedTeam.objects.create(organization=org)
        user, token = self.create_user()
        self.add_permission(user, 'team:admin', team1.pk)
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)

        url = reverse('seedteam-detail', args=(team2.pk,))
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

        url = reverse('seedteam-detail', args=(team1.pk,))
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_permission_get_team_org_member(self):
        '''Users that are members of a team's organization should be able to
        see the team's details.'''
        org = SeedOrganization.objects.create()
        team = SeedTeam.objects.create(organization=org)
        user, token = self.create_user()
        org.users.add(user)
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)

        url = reverse('seedteam-detail', args=(team.pk,))
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_permission_get_team_org_admin(self):
        '''Users that have an org:admin permission for a team's organization
        should be able to see the team details.'''
        org1 = SeedOrganization.objects.create()
        org2 = SeedOrganization.objects.create()
        team1 = SeedTeam.objects.create(organization=org1)
        team2 = SeedTeam.objects.create(organization=org2)
        user, token = self.create_user()
        self.add_permission(user, 'org:admin', org1.pk)
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)

        url = reverse('seedteam-detail', args=(team2.pk,))
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

        url = reverse('seedteam-detail', args=(team1.pk,))
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_permission_get_team_admin(self):
        '''Admin users should have read access to all teams.'''
        org = SeedOrganization.objects.create()
        team = SeedTeam.objects.create(organization=org)
        _, token = self.create_admin_user()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)

        url = reverse('seedteam-detail', args=(team.pk,))
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

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
        _, token = self.create_admin_user()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)
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

    def test_permission_add_permission_unauthenticated(self):
        '''Unauthenticated users should not be allowed to add permissions to
        any teams.'''
        org = SeedOrganization.objects.create(title='test org')
        team = SeedTeam.objects.create(title='test team', organization=org)

        data = {
            'type': 'foo:bar',
            'object_id': '2',
            'namespace': 'foo',
        }
        response = self.client.post(
            reverse('seedteam-permissions-list', args=[team.id]), data=data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_permission_add_permission_no_permission(self):
        '''Users that don't have the correct permissions shouldn't be allowed
        to add permissions to any teams.'''
        _, token = self.create_user()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)
        org = SeedOrganization.objects.create(title='test org')
        team = SeedTeam.objects.create(title='test team', organization=org)

        data = {
            'type': 'foo:bar',
            'object_id': '2',
            'namespace': 'foo',
        }
        response = self.client.post(
            reverse('seedteam-permissions-list', args=[team.id]), data=data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_permission_add_permission_read_access(self):
        '''Users that have read access to a team can add permissions that
        aren't org:admin or team:admin.'''
        user, token = self.create_user()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)
        org = SeedOrganization.objects.create(title='test org')
        team = SeedTeam.objects.create(title='test team', organization=org)
        team.users.add(user)

        data = {
            'type': 'foo:bar',
            'object_id': '2',
            'namespace': 'foo',
        }
        response = self.client.post(reverse(
            'seedteam-permissions-list', args=[team.id]), data=data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_permission_add_permission_team_admin(self):
        '''Users with team:admin for that team should be able to add any
        permission except for org:admin to that team.'''
        user, token = self.create_user()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)
        org = SeedOrganization.objects.create(title='test org')
        team = SeedTeam.objects.create(title='test team', organization=org)
        team2, _ = self.add_permission(user, 'team:admin', team.pk)

        # Correct team
        response = self.client.post(
            reverse('seedteam-permissions-list', args=[team.id]), data={
                'type': 'team:admin',
                'object_id': team.pk,
                'namespace': '__auth__',
            })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Incorrect team
        response = self.client.post(
            reverse('seedteam-permissions-list', args=[team.id]), data={
                'type': 'team:admin',
                'object_id': team2.pk,
                'namespace': '__auth__',
            })
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # org:admin
        response = self.client.post(
            reverse('seedteam-permissions-list', args=[team.id]), data={
                'type': 'org:admin',
                'object_id': org.pk,
                'namespace': '__auth__',
            })
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # other
        response = self.client.post(
            reverse('seedteam-permissions-list', args=[team.id]), data={
                'type': 'foo:bar',
                'object_id': '7',
                'namespace': '__auth__',
            })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_permission_add_permission_org_admin(self):
        '''Users with org:admin should be able to add any permission to any of
        that org's teams, except for org:admin where object_id is not the org
        id that they are admin for.'''
        user, token = self.create_user()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)
        org = SeedOrganization.objects.create(title='test org')
        org2 = SeedOrganization.objects.create(title='test org')
        team = SeedTeam.objects.create(title='test team', organization=org)
        team2, _ = self.add_permission(user, 'org:admin', org.pk)

        # incorrect team object_id
        response = self.client.post(
            reverse('seedteam-permissions-list', args=[team.id]), data={
                'type': 'team:admin',
                'object_id': team2.pk,
                'namespace': '__auth__',
            })
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # org:admin
        response = self.client.post(
            reverse('seedteam-permissions-list', args=[team.id]), data={
                'type': 'org:admin',
                'object_id': org.pk,
                'namespace': '__auth__',
            })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # org:admin incorrect org
        response = self.client.post(
            reverse('seedteam-permissions-list', args=[team.id]), data={
                'type': 'org:admin',
                'object_id': org2.pk,
                'namespace': '__auth__',
            })
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # other
        response = self.client.post(
            reverse('seedteam-permissions-list', args=[team.id]), data={
                'type': 'foo:bar',
                'object_id': '7',
                'namespace': 'foo',
            })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_remove_permission_from_team(self):
        '''When removing a permission from a team, it should remove the
        relation between the team and permission, and delete that
        permission.'''
        _, token = self.create_admin_user()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)
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

    def test_permission_remove_permission_unauthenticated(self):
        '''Unauthenticated users should not be allowed to remove permissions
        from any teams.'''
        org = SeedOrganization.objects.create(title='test org')
        team = SeedTeam.objects.create(title='test team', organization=org)

        data = {
            'type': 'foo:bar',
            'object_id': '2',
            'namespace': 'foo',
        }
        permission = SeedPermission.objects.create(**data)
        response = self.client.delete(
            reverse('seedteam-permissions-detail',
                    args=[team.id, permission.id]))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_permission_remove_permission_no_permission(self):
        '''Users that don't have the correct permissions shouldn't be allowed
        to remove permissions from any teams.'''
        _, token = self.create_user()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)
        org = SeedOrganization.objects.create(title='test org')
        team = SeedTeam.objects.create(title='test team', organization=org)

        data = {
            'type': 'foo:bar',
            'object_id': '2',
            'namespace': 'foo',
        }
        permission = SeedPermission.objects.create(**data)
        response = self.client.delete(reverse(
            'seedteam-permissions-detail', args=[team.id, permission.id]))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_permission_remove_permission_read_access(self):
        '''Any user that has read access to a team can remove team permissions
        that aren't org:admin or team:admin.'''
        user, token = self.create_user()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)
        org = SeedOrganization.objects.create(title='test org')
        team = SeedTeam.objects.create(title='test team', organization=org)
        team.users.add(user)

        data = {
            'type': 'foo:bar',
            'object_id': '2',
            'namespace': 'foo',
        }
        permission = SeedPermission.objects.create(**data)
        team.permissions.add(permission)
        response = self.client.delete(reverse(
            'seedteam-permissions-detail', args=[team.id, permission.id]))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_permission_remove_permission_team_admin(self):
        '''Users with team:admin for that team should be able to remove any
        permission except for org:admin from that team.'''
        user, token = self.create_user()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)
        org = SeedOrganization.objects.create(title='test org')
        team = SeedTeam.objects.create(title='test team', organization=org)
        team2, _ = self.add_permission(user, 'team:admin', team.pk)
        self.add_permission(user, 'team:admin', team.pk)

        # org:admin
        permission = SeedPermission.objects.create(
            type='org:admin', object_id=org.pk, namespace='__auth__')
        team.permissions.add(permission)
        response = self.client.delete(
            reverse('seedteam-permissions-detail',
                    args=[team.id, permission.id]))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # Wrong team
        wrong_team = SeedTeam.objects.create(
            title='test team 2', organization=org)
        permission = wrong_team.permissions.create(
            type='team:admin', object_id=wrong_team.pk, namespace='__auth__')
        response = self.client.delete(
            reverse('seedteam-permissions-detail',
                    args=[wrong_team.id, permission.id]))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # other
        permission = SeedPermission.objects.create(
            type='foo:bar', object_id='7', namespace='foo')
        team.permissions.add(permission)
        response = self.client.delete(
            reverse('seedteam-permissions-detail',
                    args=[team.id, permission.id]))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_permission_remove_permission_org_admin(self):
        '''Users with org:admin should be able to remove any permission from
        any of that org's teams, except for org:admin where object_id is not
        the org id that they are admin for.'''
        user, token = self.create_user()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)
        org = SeedOrganization.objects.create(title='test org')
        org2 = SeedOrganization.objects.create(title='test org')
        team = SeedTeam.objects.create(title='test team', organization=org)
        team2, _ = self.add_permission(user, 'org:admin', org.pk)

        # incorrect team object_id
        permission = SeedPermission.objects.create(
            type='team:admin', object_id=team2.pk, namespace='__auth__')
        team2.permissions.add(permission)
        response = self.client.delete(
            reverse('seedteam-permissions-detail',
                    args=[team.id, permission.id]))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        # org:admin
        permission = SeedPermission.objects.create(
            type='org:admin', object_id=org.pk, namespace='__auth__')
        team.permissions.add(permission)
        response = self.client.delete(
            reverse('seedteam-permissions-detail',
                    args=[team.id, permission.id]))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        # org:admin incorrect org
        permission = SeedPermission.objects.create(
            type='org:admin', object_id=org2.pk, namespace='__auth__')
        team2.permissions.add(permission)
        response = self.client.delete(
            reverse('seedteam-permissions-detail',
                    args=[team.id, permission.id]))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        # other
        permission = SeedPermission.objects.create(
            type='foo:bar', object_id='7', namespace='foo')
        team.permissions.add(permission)
        response = self.client.delete(
            reverse('seedteam-permissions-detail',
                    args=[team.id, permission.id]))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_add_user_to_team(self):
        '''Adding a user to a team should create a relationship between the
        two.'''
        _, token = self.create_admin_user()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)
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

    def test_permission_add_user_to_team_unauthenticated(self):
        '''Unauthenticated users should not be able to add users to teams.'''
        org = SeedOrganization.objects.create()
        team = SeedTeam.objects.create(organization=org)
        user = User.objects.create_user('test user')
        data = {'user_id': user.pk}

        response = self.client.post(reverse(
            'seedteam-users-list', args=[team.pk]), data=data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_permission_add_user_to_team_no_permission(self):
        '''Users without the correct permissions should not be able to add
        users to teams.'''
        org = SeedOrganization.objects.create()
        team = SeedTeam.objects.create(organization=org)
        user = User.objects.create_user('test user')
        data = {'user_id': user.pk}

        _, token = self.create_user()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)

        response = self.client.post(reverse(
            'seedteam-users-list', args=[team.pk]), data=data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_permission_add_user_to_team_team_admin(self):
        '''Users with team:admin permission should only be able to add users
        to that team.'''
        org = SeedOrganization.objects.create()
        team1 = SeedTeam.objects.create(organization=org)
        team2 = SeedTeam.objects.create(organization=org)
        user = User.objects.create_user('test user')
        data = {'user_id': user.pk}

        authuser, token = self.create_user()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)
        self.add_permission(authuser, 'team:admin', team1.pk)

        # Correct team
        response = self.client.post(reverse(
            'seedteam-users-list', args=[team1.pk]), data=data)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        # Incorrect team
        response = self.client.post(reverse(
            'seedteam-users-list', args=[team2.pk]), data=data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_permission_add_user_to_team_org_admin(self):
        '''Users with org:admin permission should only be able to add users
        to that organization's teams.'''
        org1 = SeedOrganization.objects.create()
        org2 = SeedOrganization.objects.create()
        team1 = SeedTeam.objects.create(organization=org1)
        team2 = SeedTeam.objects.create(organization=org2)
        user = User.objects.create_user('test user')
        data = {'user_id': user.pk}

        authuser, token = self.create_user()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)
        self.add_permission(authuser, 'org:admin', org1.pk)

        # Correct org
        response = self.client.post(reverse(
            'seedteam-users-list', args=[team1.pk]), data=data)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        # Incorrect org
        response = self.client.post(reverse(
            'seedteam-users-list', args=[team2.pk]), data=data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_remove_user_from_team(self):
        '''Removing a user from a team should remove the relationship between
        the two.'''
        _, token = self.create_admin_user()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)
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

    def test_permission_remove_user_from_team_unauthenticated(self):
        '''Unauthenticated users should not be able to remove users from
        teams.'''
        org = SeedOrganization.objects.create()
        team = SeedTeam.objects.create(organization=org)
        user = User.objects.create_user('test user')
        team.users.add(user)

        response = self.client.delete(reverse(
            'seedteam-users-detail', args=[team.pk, user.pk]))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_permission_remove_user_from_team_no_permission(self):
        '''Users without the correct permissions should not be able to remove
        users from teams.'''
        org = SeedOrganization.objects.create()
        team = SeedTeam.objects.create(organization=org)
        user = User.objects.create_user('test user')
        team.users.add(user)

        _, token = self.create_user()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)

        response = self.client.delete(reverse(
            'seedteam-users-detail', args=[team.pk, user.pk]))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_permission_remove_user_from_team_team_admin(self):
        '''Users with team:admin permission should only be able to remove users
        from that team.'''
        org = SeedOrganization.objects.create()
        team1 = SeedTeam.objects.create(organization=org)
        team2 = SeedTeam.objects.create(organization=org)
        user = User.objects.create_user('test user')
        team1.users.add(user)
        team2.users.add(user)

        authuser, token = self.create_user()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)
        self.add_permission(authuser, 'team:admin', team1.pk)

        # Correct team
        response = self.client.delete(reverse(
            'seedteam-users-detail', args=[team1.pk, user.pk]))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        # Incorrect team
        response = self.client.delete(reverse(
            'seedteam-users-detail', args=[team2.pk, user.pk]))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_permission_remove_user_from_team_org_admin(self):
        '''Users with org:admin permission should only be able to remove users
        from that organization's teams.'''
        org1 = SeedOrganization.objects.create()
        org2 = SeedOrganization.objects.create()
        team1 = SeedTeam.objects.create(organization=org1)
        team2 = SeedTeam.objects.create(organization=org2)
        user = User.objects.create_user('test user')
        team1.users.add(user)
        team2.users.add(user)

        authuser, token = self.create_user()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)
        self.add_permission(authuser, 'org:admin', org1.pk)

        # Correct org
        response = self.client.delete(reverse(
            'seedteam-users-detail', args=[team1.pk, user.pk]))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        # Incorrect org
        response = self.client.delete(reverse(
            'seedteam-users-detail', args=[team2.pk, user.pk]))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
