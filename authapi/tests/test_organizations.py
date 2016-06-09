from django.core.urlresolvers import reverse
from django.contrib.auth.models import User
from rest_framework import status

from authapi.serializers import (
    OrganizationSummarySerializer, TeamSummarySerializer,
    UserSummarySerializer, OrganizationSerializer)
from authapi.models import SeedTeam, SeedOrganization, SeedPermission
from authapi.tests.base import AuthAPITestCase


class OrganizationTests(AuthAPITestCase):
    def setUp(self):
        self.patch_client_data_json()

    def test_get_organization_list(self):
        '''A GET request to the organizations endpoint should return a list
        of organizations.'''
        _, token = self.create_admin_user()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)
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
        _, token = self.create_admin_user()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)
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
        _, token = self.create_admin_user()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)
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
        _, token = self.create_admin_user()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)
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
        _, token = self.create_admin_user()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)
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
        _, token = self.create_admin_user()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)
        response = self.client.get(
            '%s?archived=foo' % reverse('seedorganization-list'))
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, {
            'archived': ['Must be one of [both, false, true]'],
        })

    def test_get_organization_list_archived_teams(self):
        '''When getting the list of organizations, the archived teams should
        not be visible.'''
        _, token = self.create_admin_user()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)
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
        _, token = self.create_admin_user()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)
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
        _, token = self.create_admin_user()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)
        response = self.client.post(reverse('seedorganization-list'))
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, {
            'title': ['This field is required.']
        })

    def test_create_organization(self):
        '''A POST request to the organizations endpoint should create a new
        organization.'''
        _, token = self.create_admin_user()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)
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
        _, token = self.create_admin_user()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)
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
        _, token = self.create_admin_user()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)
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

    def test_permission_list_organization(self):
        '''Any authenticated user should be able to get a list of
        organizations.'''
        response = self.client.get(reverse('seedorganization-list'))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        _, token = self.create_user()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)
        response = self.client.get(reverse('seedorganization-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_permission_create_organization(self):
        '''Only admin users should be allowed to create organizations.'''
        # Unauthenticated request
        data = {
            'title': 'test org',
        }
        url = reverse('seedorganization-list')
        response = self.client.post(url, data=data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        # Authenticated request, no permissions
        user, token = self.create_user()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)
        response = self.client.post(url, data=data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # Authenticated request, wrong permission
        self.add_permission(user, 'team:admin')
        response = self.client.post(url, data=data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # Admin user
        _, token = self.create_admin_user()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)
        response = self.client.post(url, data=data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_permission_get_organization(self):
        '''Any authenticated user should be able to get the details of an
        organization.'''
        org = SeedOrganization.objects.create()
        url = reverse('seedorganization-detail', args=(org.pk,))

        # Unauthenticated request
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        # Authenticated request
        _, token = self.create_user()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_permission_update_organization(self):
        '''Only admin users, users with org:admin permissions should be able to
        update organizations.'''
        data = {
            'title': 'test org',
        }
        org1 = SeedOrganization.objects.create()
        org2 = SeedOrganization.objects.create()
        url = reverse('seedorganization-detail', args=(org1.pk,))

        # Unauthenticated request
        response = self.client.put(url, data=data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        # Authenticated request, no permissions
        SeedPermission.objects.all().delete()
        user, token = self.create_user()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)
        response = self.client.put(url, data=data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # Authenticated request, org:admin permissions, wrong org
        SeedPermission.objects.all().delete()
        self.add_permission(user, 'org:admin', org2.pk)
        response = self.client.put(url, data=data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # Authenticated request, org:admin permissions, correct org
        SeedPermission.objects.all().delete()
        self.add_permission(user, 'org:admin', org1.pk)
        response = self.client.put(url, data=data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Admin user request
        _, token = self.create_admin_user()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)
        response = self.client.put(url, data=data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_permission_delete_organization(self):
        '''Only admin users, users with org:admin permissions for the
        organization should be able to delete organizations.'''
        org1 = SeedOrganization.objects.create()
        org2 = SeedOrganization.objects.create()
        url = reverse('seedorganization-detail', args=(org1.pk,))

        # Unauthenticated request
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        # Authenticated request, no permissions
        user, token = self.create_user()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # Authenticated request, org:admin permissions, wrong org
        SeedPermission.objects.all().delete()
        self.add_permission(user, 'org:admin', org2.pk)
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # Authenticated request, org:admin permissions, correct org
        SeedPermission.objects.all().delete()
        self.add_permission(user, 'org:admin', org1.pk)
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        # Admin user request
        _, token = self.create_admin_user()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)


class OrganizationUserTests(AuthAPITestCase):
    def setUp(self):
        self.patch_client_data_json()

    def test_add_user_to_organization(self):
        '''Adding a user to an organization should create a relationship
        between the two.'''
        _, token = self.create_admin_user()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)
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
        _, token = self.create_admin_user()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)
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
        _, token = self.create_admin_user()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)
        org = SeedOrganization.objects.create(title='test org')
        user = User.objects.create_user(username='test@example.org')
        org.users.add(user)
        self.assertEqual(len(org.users.all()), 1)

        response = self.client.delete(
            reverse('seedorganization-users-detail', args=[org.id, user.id]))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        org.refresh_from_db()
        self.assertEqual(len(org.users.all()), 0)

    def test_permission_add_user_to_organization_unauthorized(self):
        '''Unauthorized users should not be able to add users to an
        organization.'''
        org = SeedOrganization.objects.create()
        user = User.objects.create_user('testuser@example.org')

        url = reverse('seedorganization-users-list', args=(org.pk,))
        resp = self.client.post(url, data={'user_id': user.pk})
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_permission_add_user_to_organization_authorized(self):
        '''If a user is authorized, but does not have the correct permissions,
        they should not be allowed to add users to an organization.'''
        org = SeedOrganization.objects.create()
        user, token = self.create_user()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)

        url = reverse('seedorganization-users-list', args=(org.pk,))
        resp = self.client.post(url, data={'user_id': user.pk})
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_permission_add_user_to_organization_org_admin_wrong_org(self):
        '''If the user has org:admin permissions for a different org, they
        should not be able to add users to this org.'''
        org1 = SeedOrganization.objects.create()
        org2 = SeedOrganization.objects.create()
        user, token = self.create_user()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)
        self.add_permission(user, 'org:admin', org2.pk)

        url = reverse('seedorganization-users-list', args=(org1.pk,))
        resp = self.client.post(url, data={'user_id': user.pk})
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_permission_add_user_to_organization_org_admin_correct_org(self):
        '''If the user has org:admin permissions for the org, they should
        be able to add users to this org.'''
        org = SeedOrganization.objects.create()
        user, token = self.create_user()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)
        self.add_permission(user, 'org:admin', org.pk)

        url = reverse('seedorganization-users-list', args=(org.pk,))
        resp = self.client.post(url, data={'user_id': user.pk})
        self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT)

    def test_permission_add_user_to_organization_admin(self):
        '''Admins should be able to add users to an organization.'''
        org = SeedOrganization.objects.create()
        url = reverse('seedorganization-users-list', args=(org.pk,))

        _, token = self.create_admin_user()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)
        user = User.objects.create_user('testuser@example.org')
        resp = self.client.post(url, data={'user_id': user.pk})
        self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT)

    def test_permission_remove_user_to_organization_unauthorized(self):
        '''Unauthorized users should not be able to remove users from an
        organization.'''
        org = SeedOrganization.objects.create()
        user = User.objects.create_user('testuser@example.org')
        org.users.add(user)

        url = reverse('seedorganization-users-detail', args=(org.pk, user.pk))
        resp = self.client.delete(url)
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_permission_remove_user_from_organization_authorized(self):
        '''If a user is authorized, but does not have the correct permissions,
        they should not be allowed to remove users from an organization.'''
        org = SeedOrganization.objects.create()
        user, token = self.create_user()
        org.users.add(user)
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)

        url = reverse('seedorganization-users-detail', args=(org.pk, user.pk))
        resp = self.client.delete(url)
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_permission_remove_user_from_org_org_admin_wrong_org(self):
        '''If the user has org:admin permissions for a different org, they
        should not be able to remove users from this org.'''
        org1 = SeedOrganization.objects.create()
        org2 = SeedOrganization.objects.create()
        user, token = self.create_user()
        org1.users.add(user)
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)
        self.add_permission(user, 'org:admin', org2.pk)

        url = reverse('seedorganization-users-detail', args=(org1.pk, user.pk))
        resp = self.client.delete(url)
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_permission_remove_user_from_org_org_admin_correct_org(self):
        '''If the user has org:admin permissions for the org, they should
        be able to remove users from this org.'''
        org = SeedOrganization.objects.create()
        user, token = self.create_user()
        org.users.add(user)
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)
        self.add_permission(user, 'org:admin', org.pk)

        url = reverse('seedorganization-users-detail', args=(org.pk, user.pk))
        resp = self.client.delete(url)
        self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT)

    def test_permission_remove_user_to_organization_admin(self):
        '''Admins should be able to remove users from an organization.'''
        org = SeedOrganization.objects.create()
        user = User.objects.create_user('test@example.org')
        org.users.add(user)
        url = reverse('seedorganization-users-detail', args=(org.pk, user.pk))

        _, token = self.create_admin_user()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)
        resp = self.client.delete(url)
        self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT)


class OrganizationTeamTests(AuthAPITestCase):
    def setUp(self):
        self.patch_client_data_json()

    def test_create_team_for_organization(self):
        '''Should create a team and the relation between the team and
        organization.'''
        _, token = self.create_admin_user()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)
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

    def test_permission_create_team_unauthorized(self):
        '''Unauthorized users should not be able to create teams.'''
        org = SeedOrganization.objects.create()
        url = reverse('seedorganization-teams-list', args=(org.pk,))

        resp = self.client.post(url, data={'title': 'test team'})
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_permission_create_team_authorized(self):
        '''If a user is authorized, but does not have the correct permissions,
        they should not be allowed to create teams.'''
        org = SeedOrganization.objects.create()
        url = reverse('seedorganization-teams-list', args=(org.pk,))

        _, token = self.create_user()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)
        resp = self.client.post(url, data={'title': 'test team'})
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_permission_create_team_org_admin_wrong_org(self):
        '''If a user has org:admin permissions, but for another org, they
        should not be allowed to create teams for this org.'''
        org = SeedOrganization.objects.create()
        org2 = SeedOrganization.objects.create()
        url = reverse('seedorganization-teams-list', args=(org.pk,))

        user, token = self.create_user()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)
        self.add_permission(user, 'org:admin', org2.pk)
        resp = self.client.post(url, data={'title': 'test team'})
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_permission_create_team_org_admin_correct_org(self):
        '''If a user has org:admin permissions they should be allowed to create
        teams for this org.'''
        org = SeedOrganization.objects.create()
        url = reverse('seedorganization-teams-list', args=(org.pk,))

        user, token = self.create_user()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)
        self.add_permission(user, 'org:admin', org.pk)
        resp = self.client.post(url, data={'title': 'test team'})
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)

    def test_permission_create_team_admin_user(self):
        '''Admin users should be able to create teams for any organization.'''
        org = SeedOrganization.objects.create()
        url = reverse('seedorganization-teams-list', args=(org.pk,))

        _, token = self.create_admin_user()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)
        resp = self.client.post(url, data={'title': 'test team'})
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)

    def test_get_teams_for_organization(self):
        '''Getting a list of teams for an organization should only return that
        organization's teams.'''
        _, token = self.create_admin_user()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)
        org1 = SeedOrganization.objects.create(title='test org')
        org2 = SeedOrganization.objects.create(title='test org')
        team1 = SeedTeam.objects.create(title='test team', organization=org1)
        SeedTeam.objects.create(title='test team', organization=org2)

        response = self.client.get(
            reverse('seedorganization-teams-list', args=[org1.pk]))
        [team] = response.data

        self.assertEqual(team['id'], team1.id)

    def test_permission_teams_for_organization(self):
        '''Any member of the organization should be able to see that
        organization's teams.'''
        org = SeedOrganization.objects.create()
        url = reverse('seedorganization-teams-list', args=(org.pk,))

        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        user, token = self.create_user()
        team = SeedTeam.objects.create(organization=org)
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)
        response = self.client.get(url)
        self.assertEqual(response.data, [])

        org.users.add(user)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        [resp_team] = response.data
        self.assertEqual(resp_team['id'], team.pk)

    def test_create_permission_for_organizations_team(self):
        '''Should be able to create a permission for an organization's team.'''
        _, token = self.create_admin_user()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)
        org = SeedOrganization.objects.create(title='test org')
        team = SeedTeam.objects.create(title='test team', organization=org)
        data = {
            'type': 'foo:bar',
            'object_id': '2',
            'namespace': '__auth__',
        }

        self.assertEqual(len(team.permissions.all()), 0)

        self.client.post(
            reverse(
                'seedorganization-teams-permissions-list',
                args=[org.pk, team.pk]
            ),
            data=data)

        self.assertEqual(len(team.permissions.all()), 1)

    def test_permission_create_permission_unauthenticated(self):
        '''Unauthenticated requests should be denied.'''
        org = SeedOrganization.objects.create(title='test org')
        team = SeedTeam.objects.create(title='test team', organization=org)

        resp = self.client.post(
            reverse(
                'seedorganization-teams-permissions-list',
                args=[org.pk, team.pk]
            ),
            data={
                'type': 'organization:admin',
                'object_id': org.pk,
                'namespace': '__auth__'
            })
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_permission_create_permission_no_permission(self):
        '''Users that do not have the correct permissions should be denied.'''
        user, token = self.create_user()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)
        org = SeedOrganization.objects.create(title='test org')
        team = SeedTeam.objects.create(title='test team', organization=org)

        resp = self.client.post(
            reverse(
                'seedorganization-teams-permissions-list',
                args=[org.pk, team.pk]
            ),
            data={
                'type': 'foo:bar',
                'object_id': '7',
                'namespace': 'foo'
            })
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_permission_create_permission_team_permission(self):
        '''The user must have read access to a team to be able to add
        permissions to that team.'''
        user, token = self.create_user()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)
        org1 = SeedOrganization.objects.create(title='test org')
        org2 = SeedOrganization.objects.create(title='test org')
        team1 = SeedTeam.objects.create(title='test team', organization=org1)
        team2 = SeedTeam.objects.create(title='test team', organization=org2)
        team1.users.add(user)

        # Wrong org
        resp = self.client.post(
            reverse(
                'seedorganization-teams-permissions-list',
                args=[org2.pk, team1.pk]
            ),
            data={
                'type': 'foo:bar',
                'object_id': '7',
                'namespace': 'baz'
            })
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

        # Wrong team
        resp = self.client.post(
            reverse(
                'seedorganization-teams-permissions-list',
                args=[org1.pk, team2.pk]
            ),
            data={
                'type': 'foo:bar',
                'object_id': '7',
                'namespace': 'baz'
            })
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

        # Wrong org and team
        resp = self.client.post(
            reverse(
                'seedorganization-teams-permissions-list',
                args=[org2.pk, team2.pk]
            ),
            data={
                'type': 'foo:bar',
                'object_id': '7',
                'namespace': 'baz'
            })
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

        # Correct
        resp = self.client.post(
            reverse(
                'seedorganization-teams-permissions-list',
                args=[org1.pk, team1.pk]
            ),
            data={
                'type': 'foo:bar',
                'object_id': '7',
                'namespace': 'baz'
            })
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)

    def test_permission_delete_permission_team_permission(self):
        '''The user must have read access to a team to be able to remove
        permissions from that team.'''
        user, token = self.create_user()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)
        org1 = SeedOrganization.objects.create(title='test org')
        org2 = SeedOrganization.objects.create(title='test org')
        team1 = SeedTeam.objects.create(title='test team', organization=org1)
        team2 = SeedTeam.objects.create(title='test team', organization=org2)
        team1.users.add(user)

        # Wrong org
        perm = team1.permissions.create(
            type='foo:bar', object_id='7', namespace='baz')
        resp = self.client.delete(
            reverse(
                'seedorganization-teams-permissions-detail',
                args=[org2.pk, team1.pk, perm.pk]
            )
        )
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

        # Wrong team
        perm = team1.permissions.create(
            type='foo:bar', object_id='7', namespace='baz')
        resp = self.client.delete(
            reverse(
                'seedorganization-teams-permissions-detail',
                args=[org1.pk, team2.pk, perm.pk]
            ),
        )
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

        # Wrong org and team
        perm = team1.permissions.create(
            type='foo:bar', object_id='7', namespace='baz')
        resp = self.client.delete(
            reverse(
                'seedorganization-teams-permissions-detail',
                args=[org2.pk, team2.pk, perm.pk]
            ),
        )
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

        # Correct
        perm = team1.permissions.create(
            type='foo:bar', object_id='7', namespace='baz')
        resp = self.client.delete(
            reverse(
                'seedorganization-teams-permissions-detail',
                args=[org1.pk, team1.pk, perm.pk]
            ),
        )
        self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT)

    def test_permission_create_permission_org_admin(self):
        '''A user with org:admin should be able to create any permission for
        that organization's teams.'''
        user, token = self.create_user()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)
        org1 = SeedOrganization.objects.create(title='test org')
        org2 = SeedOrganization.objects.create(title='test org')
        team1 = SeedTeam.objects.create(title='test team', organization=org1)
        self.add_permission(user, 'org:admin', org1.pk)

        # Wrong object id
        resp = self.client.post(
            reverse(
                'seedorganization-teams-permissions-list',
                args=[org1.pk, team1.pk]
            ),
            data={
                'type': 'org:admin',
                'object_id': org2.pk,
                'namespace': '__auth__'
            })
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

        # Correct
        resp = self.client.post(
            reverse(
                'seedorganization-teams-permissions-list',
                args=[org1.pk, team1.pk]
            ),
            data={
                'type': 'org:admin',
                'object_id': org1.pk,
                'namespace': '__auth__'
            })
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)

        # team:admin
        resp = self.client.post(
            reverse(
                'seedorganization-teams-permissions-list',
                args=[org1.pk, team1.pk]
            ),
            data={
                'type': 'team:admin',
                'object_id': team1.pk,
                'namespace': '__auth__'
            })
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)

        # other
        resp = self.client.post(
            reverse(
                'seedorganization-teams-permissions-list',
                args=[org1.pk, team1.pk]
            ),
            data={
                'type': 'foo:bar',
                'object_id': '7',
                'namespace': 'foo'
            })
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)

    def test_permission_create_permission_team_admin(self):
        '''Users with team:admin permissions should be able to give other teams
        team:admin, or any other permission except org:admin.'''
        user, token = self.create_user()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)
        org = SeedOrganization.objects.create(title='test org')
        team = SeedTeam.objects.create(title='test team', organization=org)
        team2 = SeedTeam.objects.create(title='test team', organization=org)
        self.add_permission(user, 'team:admin', team.pk)

        # team:admin
        resp = self.client.post(
            reverse(
                'seedorganization-teams-permissions-list',
                args=[org.pk, team.pk]
            ),
            data={
                'type': 'team:admin',
                'object_id': team.pk,
                'namespace': '__auth__'
            })
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)

        # team:admin wrong team
        resp = self.client.post(
            reverse(
                'seedorganization-teams-permissions-list',
                args=[org.pk, team.pk]
            ),
            data={
                'type': 'team:admin',
                'object_id': team2.pk,
                'namespace': '__auth__'
            })
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

        # org:admin
        resp = self.client.post(
            reverse(
                'seedorganization-teams-permissions-list',
                args=[org.pk, team.pk]
            ),
            data={
                'type': 'org:admin',
                'object_id': org.pk,
                'namespace': '__auth__'
            })
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

        # other
        resp = self.client.post(
            reverse(
                'seedorganization-teams-permissions-list',
                args=[org.pk, team.pk]
            ),
            data={
                'type': 'foo:bar',
                'object_id': '7',
                'namespace': '__auth__'
            })
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)

    def test_remove_permission_for_organizations_team(self):
        '''Should be able to remove a permission for an organization's team.'''
        _, token = self.create_admin_user()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)
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
        _, token = self.create_admin_user()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)
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
        _, token = self.create_admin_user()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)
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

    def test_permission_add_user_to_organizations_team_unauthenticated(self):
        '''Unauthenticated users should not be allowed to add users to
        teams.'''
        org = SeedOrganization.objects.create()
        team = SeedTeam.objects.create(organization=org)
        user = User.objects.create_user('test user')
        data = {'user_id': user.pk}

        response = self.client.post(reverse(
            'seedorganization-teams-users-list', args=[org.pk, team.pk]),
            data=data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_permission_add_user_to_organizations_team_no_permission(self):
        '''Users without the correct permissions should not be allowed to add
        users to teams.'''
        org = SeedOrganization.objects.create()
        team = SeedTeam.objects.create(organization=org)
        user = User.objects.create_user('test user')
        data = {'user_id': user.pk}

        _, token = self.create_user()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)
        response = self.client.post(reverse(
            'seedorganization-teams-users-list', args=[org.pk, team.pk]),
            data=data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_permission_add_user_to_organizations_team_team_admin(self):
        '''Users with team:admin permission should be able to add users to
        only that team.'''
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
            'seedorganization-teams-users-list', args=[org.pk, team1.pk]),
            data=data)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        # Incorrect team
        response = self.client.post(reverse(
            'seedorganization-teams-users-list', args=[org.pk, team2.pk]),
            data=data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_permission_add_user_to_organizations_team_org_admin(self):
        '''Users with org:admin permission should be able to add users to
        any team within that organization.'''
        org1 = SeedOrganization.objects.create()
        org2 = SeedOrganization.objects.create()
        team1 = SeedTeam.objects.create(organization=org1)
        team2 = SeedTeam.objects.create(organization=org2)
        user = User.objects.create_user('test user')
        data = {'user_id': user.pk}

        authuser, token = self.create_user()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)
        self.add_permission(authuser, 'team:admin', team1.pk)

        # Correct org
        response = self.client.post(reverse(
            'seedorganization-teams-users-list', args=[org1.pk, team1.pk]),
            data=data)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        # Incorrect org
        response = self.client.post(reverse(
            'seedorganization-teams-users-list', args=[org2.pk, team2.pk]),
            data=data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_remove_user_from_organizations_team(self):
        '''Should be able to remove an existing user from an organization's
        team.'''
        _, token = self.create_admin_user()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)
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
        _, token = self.create_admin_user()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)
        org1 = SeedOrganization.objects.create(title='test org')
        org2 = SeedOrganization.objects.create(title='test org')
        team = SeedTeam.objects.create(title='test team', organization=org1)
        user = User.objects.create_user('test user')

        response = self.client.delete(
            reverse(
                'seedorganization-teams-users-detail',
                args=[org2.pk, team.pk, user.pk]))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_permission_remove_user_from_orgs_team_unauthenticated(self):
        '''Unauthenticated users should not be allowed to remove users from
        teams.'''
        org = SeedOrganization.objects.create()
        team = SeedTeam.objects.create(organization=org)
        user = User.objects.create_user('test user')

        response = self.client.delete(reverse(
            'seedorganization-teams-users-detail',
            args=[org.pk, team.pk, user.pk]))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_permission_remove_user_from_orgs_team_no_permission(self):
        '''Users without the correct permissions should not be allowed to
        remove users from teams.'''
        org = SeedOrganization.objects.create()
        team = SeedTeam.objects.create(organization=org)
        user = User.objects.create_user('test user')
        team.users.add(user)

        _, token = self.create_user()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)
        response = self.client.delete(reverse(
            'seedorganization-teams-users-detail',
            args=[org.pk, team.pk, user.pk]))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_permission_remove_user_from_organizations_team_team_admin(self):
        '''Users with team:admin permission should be able to remove users from
        only that team.'''
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
            'seedorganization-teams-users-detail',
            args=[org.pk, team1.pk, user.pk]))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        # Incorrect team
        response = self.client.delete(reverse(
            'seedorganization-teams-users-detail',
            args=[org.pk, team2.pk, user.pk]))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_permission_remove_user_from_organizations_team_org_admin(self):
        '''Users with org:admin permission should be able to remove users from
        any team within that organization.'''
        org1 = SeedOrganization.objects.create()
        org2 = SeedOrganization.objects.create()
        team1 = SeedTeam.objects.create(organization=org1)
        team2 = SeedTeam.objects.create(organization=org2)
        user = User.objects.create_user('test user')
        team1.users.add(user)
        team2.users.add(user)

        authuser, token = self.create_user()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)
        self.add_permission(authuser, 'team:admin', team1.pk)

        # Correct org
        response = self.client.delete(reverse(
            'seedorganization-teams-users-detail',
            args=[org1.pk, team1.pk, user.pk]))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        # Incorrect org
        response = self.client.delete(reverse(
            'seedorganization-teams-users-detail',
            args=[org2.pk, team2.pk, user.pk]))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
