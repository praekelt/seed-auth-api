from django.core.urlresolvers import reverse
from django.contrib.auth.models import User
from rest_framework import status
from rest_framework.authtoken.models import Token

from authapi.serializers import (
    TeamSerializer, OrganizationSummarySerializer, TeamSummarySerializer,
    PermissionSerializer, UserSummarySerializer, OrganizationSerializer)
from authapi.models import SeedTeam, SeedOrganization, SeedPermission
from authapi.tests.base import AuthAPITestCase


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

    def test_get_team_list_archived_invalid_queryparam(self):
        '''If the archived querystring parameter is not one of true, false, or
        both, an appropriate error should be returned.'''
        response = self.client.get(
            '%s?archived=foo' % reverse('seedteam-list'))
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, {
            'archived': ['Must be one of [both, false, true]'],
        })

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
        '''Creating teams on this endpoint should not be allowed.'''
        response = self.client.post(reverse('seedteam-list'), data={})
        self.assertEqual(
            response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_delete_team(self):
        '''Deleting a team should archive the team instead of removing it.'''
        org = SeedOrganization.objects.create(title='test org')
        team = SeedTeam.objects.create(organization=org, title='test team')

        self.assertEqual(team.archived, False)

        self.client.delete(reverse('seedteam-detail', args=[team.id]))

        team.refresh_from_db()
        self.assertEqual(team.archived, True)

    def test_update_team(self):
        '''A PUT request to a team's endpoint should update an existing
        team.'''
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

    def test_get_organization_list_archived_invalid_queryparam(self):
        '''If the archived querystring parameter is not one of true, false, or
        both, an appropriate error should be returned.'''
        response = self.client.get(
            '%s?archived=foo' % reverse('seedorganization-list'))
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, {
            'archived': ['Must be one of [both, false, true]'],
        })

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

    def test_create_team_for_organization(self):
        '''Should create a team and the relation between the team and
        organization.'''
        org = SeedOrganization.objects.create(title='test org')
        data = {
            'title': 'test team',
        }

        response = self.client.post(
            reverse('seedorganization-teams-list', args=[org.id]), data=data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        [team] = SeedTeam.objects.all()
        self.assertEqual(team.organization, org)
        self.assertEqual(team.title, data['title'])

    def test_get_teams_for_organization(self):
        '''Getting a list of teams for an organization should only return that
        organization's teams.'''
        org1 = SeedOrganization.objects.create(title='test org')
        org2 = SeedOrganization.objects.create(title='test org')
        team1 = SeedTeam.objects.create(title='test team', organization=org1)
        SeedTeam.objects.create(title='test team', organization=org2)

        response = self.client.get(
            reverse('seedorganization-teams-list', args=[org1.pk]))
        [team] = response.data

        self.assertEqual(team['id'], team1.id)

    def test_create_permission_for_organizations_team(self):
        '''Should be able to create a permission for an organization's team.'''
        org = SeedOrganization.objects.create(title='test org')
        team = SeedTeam.objects.create(title='test team', organization=org)
        data = {
            'type': 'foo:bar',
            'object_id': '2',
            'namespace': 'foo',
        }

        self.assertEqual(len(team.permissions.all()), 0)

        self.client.post(
            reverse(
                'seedorganization-teams-permissions-list',
                args=[org.pk, team.pk]
            ),
            data=data)

        self.assertEqual(len(team.permissions.all()), 1)

    def test_remove_permission_for_organizations_team(self):
        '''Should be able to remove a permission for an organization's team.'''
        org = SeedOrganization.objects.create(title='test org')
        team = SeedTeam.objects.create(title='test team', organization=org)
        permission = team.permissions.create(
            type='foo:bar', object_id='2', namespace='foo')

        self.assertEqual(len(team.permissions.all()), 1)

        self.client.delete(
            reverse(
                'seedorganization-teams-permissions-detail',
                args=[org.pk, team.pk, permission.pk]
            ))

        self.assertEqual(len(team.permissions.all()), 0)

    def test_remove_permission_for_other_organization_team(self):
        '''Should not be able to remove a permission for another
        organization's team.'''
        org1 = SeedOrganization.objects.create(title='test org')
        org2 = SeedOrganization.objects.create(title='test org')
        team1 = SeedTeam.objects.create(title='test team', organization=org1)
        team2 = SeedTeam.objects.create(title='test team', organization=org2)
        permission = team1.permissions.create(
            type='foo:bar', object_id='2', namespace='foo')

        response = self.client.delete(
            reverse(
                'seedorganization-teams-permissions-detail',
                args=[org2.pk, team2.pk, permission.pk]
            ))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_add_user_to_organizations_team(self):
        '''Should be able to add an existing user to an organization's team.'''
        org = SeedOrganization.objects.create(title='test org')
        team = SeedTeam.objects.create(title='test team', organization=org)
        user = User.objects.create_user('test user')
        data = {
            'user_id': user.pk,
        }

        response = self.client.post(
            reverse(
                'seedorganization-teams-users-list',
                args=[org.pk, team.pk]),
            data=data)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        [teamuser] = team.users.all()
        self.assertEqual(teamuser, user)

    def test_remove_user_from_organizations_team(self):
        '''Should be able to remove an existing user from an organization's
        team.'''
        org = SeedOrganization.objects.create(title='test org')
        team = SeedTeam.objects.create(title='test team', organization=org)
        user = User.objects.create_user('test user')
        team.users.add(user)

        self.assertEqual(len(team.users.all()), 1)

        response = self.client.delete(
            reverse(
                'seedorganization-teams-users-detail',
                args=[org.pk, team.pk, user.pk]))

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(len(team.users.all()), 0)

    def test_remove_user_from_other_organizations_team(self):
        '''Should not be able to remove user's from a team belonging to
        another organization.'''
        org1 = SeedOrganization.objects.create(title='test org')
        org2 = SeedOrganization.objects.create(title='test org')
        team = SeedTeam.objects.create(title='test team', organization=org1)
        user = User.objects.create_user('test user')

        response = self.client.delete(
            reverse(
                'seedorganization-teams-users-detail',
                args=[org2.pk, team.pk, user.pk]))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class TokenTests(AuthAPITestCase):
    def test_create_token(self):
        '''Sending a valid email and password should create a token for that
        user.'''
        data = {
            'email': 'test@example.org',
            'password': 'testpass',
        }
        user = User.objects.create_user(
            username=data['email'], email=data['email'],
            password=data['password'])

        response = self.client.post(reverse('create-token'), data=data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        [token] = Token.objects.filter(user=user)
        self.assertEqual(token.key, response.data['token'])

    def test_create_token_invalid_user_email(self):
        '''An invalid email should return an unauthorized response.'''
        response = self.client.post(reverse('create-token'), data={
            'email': 'foo@bar.com', 'password': 'foo'})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_create_token_invalid_user_password(self):
        '''An incorrect password should return an unauthorized response.'''
        email = 'foo@bar.com'
        User.objects.create_user(
            username=email, email=email, password='password')
        response = self.client.post(reverse('create-token'), data={
            'email': email, 'password': 'wrongpassword'})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_create_token_inactive_user(self):
        '''A user that is not active, should get a forbidden response to
        creating a token.'''
        data = {
            'email': 'test@example.org',
            'password': 'testpass',
        }
        User.objects.create_user(
            username=data['email'], email=data['email'],
            password=data['password'], is_active=False)

        response = self.client.post(reverse('create-token'), data=data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_create_token_removes_other_tokens(self):
        '''When a new token for a user is requested, all other tokens for
        that user should be removed.'''
        data = {
            'email': 'test@example.org',
            'password': 'testpass',
        }
        user = User.objects.create_user(
            username=data['email'], email=data['email'],
            password=data['password'])
        first_token = Token.objects.create(user=user)

        response = self.client.post(reverse('create-token'), data=data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        [token] = Token.objects.filter(user=user)
        self.assertEqual(token.key, response.data['token'])
        self.assertNotEqual(first_token.key, token.key)


class UserPermissionsTests(AuthAPITestCase):
    def test_get_empty_permissions(self):
        '''If the user isn't part of any teams that grant permissions, it
        should return the user information with an empty permission list.'''
        user = User.objects.create_user(
            username='foo@bar.org', email='foo@bar.org', password='password')
        token = Token.objects.create(user=user)

        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)
        response = self.client.get(reverse('get-user-permissions'))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], user.id)
        self.assertEqual(response.data['email'], 'foo@bar.org')
        self.assertEqual(response.data['permissions'], [])

    def test_get_permissions_from_teams(self):
        '''If the user is part of teams that have permissions, those
        permissions should be granted to the user. The permissions on teams
        that the user is not a member of should not be given to the user.'''
        org = SeedOrganization.objects.create()
        teams = []
        for i in range(3):
            team = SeedTeam.objects.create(organization=org)
            team.permissions.create(
                type='foo%d' % i, namespace='bar%d' % i, object_id='%d' % i)
            teams.append(team)

        user = User.objects.create_user('foo@bar.org', password='password')
        token = Token.objects.create(user=user)
        teams[0].users.add(user)
        teams[1].users.add(user)

        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)
        url = reverse('get-user-permissions')
        response = self.client.get(url)

        permissions = sorted(
            response.data['permissions'], key=lambda p: p['id'])
        context = self.get_context(url)
        expected_permissions = sorted(PermissionSerializer(
            instance=[teams[0].permissions.get(), teams[1].permissions.get()],
            many=True, context=context).data, key=lambda p: p['id'])
        self.assertEqual(permissions, expected_permissions)

    def test_get_permissions_from_archived_teams(self):
        '''Archived teams should not give users any permissions.'''
        org = SeedOrganization.objects.create()
        team = SeedTeam.objects.create(organization=org, archived=True)
        team.permissions.create(type='foo', namespace='bar', object_id='1')

        user = User.objects.create_user('foo@bar.org', password='password')
        token = Token.objects.create(user=user)
        team.users.add(user)

        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)
        response = self.client.get(reverse('get-user-permissions'))

        self.assertEqual(response.data['permissions'], [])

    def test_get_permissions_from_archived_organizations(self):
        '''Teams of archived organizations should not give users any
        permissions.'''
        org = SeedOrganization.objects.create(archived=True)
        team = SeedTeam.objects.create(organization=org)
        team.permissions.create(type='foo', namespace='bar', object_id='1')

        user = User.objects.create_user('foo@bar.org', password='password')
        token = Token.objects.create(user=user)
        team.users.add(user)

        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)
        response = self.client.get(reverse('get-user-permissions'))

        self.assertEqual(response.data['permissions'], [])

    def test_get_permissions_from_inactive_users(self):
        '''Inactive users should not have any permissions.'''
        org = SeedOrganization.objects.create()
        team = SeedTeam.objects.create(organization=org)
        team.permissions.create(type='foo', namespace='bar', object_id='1')

        user = User.objects.create_user(
            'foo@bar.org', password='password', is_active=False)
        token = Token.objects.create(user=user)
        team.users.add(user)

        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)
        response = self.client.get(reverse('get-user-permissions'))

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_get_permssions_from_unauthorized_users(self):
        '''If there is no token in the authentication error, we should return
        an unauthorized response.'''
        response = self.client.get(reverse('get-user-permissions'))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
