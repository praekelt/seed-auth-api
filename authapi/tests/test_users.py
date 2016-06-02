from django.contrib.auth.hashers import check_password
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from rest_framework import status

from authapi.serializers import (
    UserSerializer, NewUserSerializer, UserSummarySerializer,
    TeamSummarySerializer, OrganizationSummarySerializer)
from authapi.models import SeedTeam, SeedOrganization
from authapi.tests.base import AuthAPITestCase


class UserTests(AuthAPITestCase):
    def test_get_account_list_multiple(self):
        '''If there are multiple users, it should return them all in a list.'''
        user1, token = self.create_user()
        user2 = User.objects.create_user(username="user2@example.org")
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)

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
        _, token = self.create_admin_user()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)
        user = User.objects.create_user('user@example.org')

        response = self.client.get(reverse('user-list'))
        self.assertEqual(len(response.data), 2)

        user.is_active = False
        user.save()

        response = self.client.get(reverse('user-list'))
        self.assertEqual(len(response.data), 1)

    def test_get_user_list_active_queryparam_true(self):
        '''If the queryparam active is set to false, then we should return
        all active users.'''
        _, token = self.create_admin_user()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)
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
        _, token = self.create_user()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)

        response = self.client.get(reverse('user-list'))
        self.assertEqual(len(response.data), 1)

        response = self.client.get(
            '%s?active=both' % reverse('user-list'))
        self.assertEqual(len(response.data), 2)

    def test_get_user_list_active_invalid_queryparam(self):
        '''If the active querystring parameter is not one of true, false, or
        both, an appropriate error should be returned.'''
        _, token = self.create_admin_user()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)
        response = self.client.get(
            '%s?active=foo' % reverse('user-list'))
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, {
            'active': ['Must be one of [both, false, true]'],
        })

    def test_permission_get_user_list_unauthenticated(self):
        '''An authenticated request is required to get the list of users.'''
        response = self.client.get(reverse('user-list'))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_create_superuser(self):
        '''A POST request to the user endpoint should create a user with all
        of the supplied details. If admin is True a superuser should be
        created.'''
        _, token = self.create_admin_user()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)
        data = {
            'email': 'user1@example.org',
            'password': 'testpassword',
            'first_name': 'user1',
            'last_name': 'example',
            'admin': True,
        }
        response = self.client.post(reverse('user-list'), data=data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        [user] = User.objects.filter(pk=response.data['id'])
        self.assertEqual(user.username, data['email'])
        self.assertEqual(user.first_name, data['first_name'])
        self.assertEqual(user.last_name, data['last_name'])
        self.assertEqual(user.is_superuser, data['admin'])
        self.assertTrue(check_password(data['password'], user.password))

    def test_permission_create_superuser(self):
        '''Only admin users should be able to create other admin users.'''
        data = {
            'email': 'user1@example.org',
            'password': 'testpassword',
            'first_name': 'user1',
            'last_name': 'example',
            'admin': True,
        }
        resp = self.client.post(reverse('user-list'), data=data)
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

        user, token = self.create_user()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)
        resp = self.client.post(reverse('user-list'), data=data)
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

        self.add_permission(user, 'org:admin')
        resp = self.client.post(reverse('user-list'), data=data)
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

        self.add_permission(user, 'user:create')
        resp = self.client.post(reverse('user-list'), data=data)
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

        user, token = self.create_admin_user()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)
        resp = self.client.post(reverse('user-list'), data=data)
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)

    def test_create_user(self):
        '''A POST request to the user endpoint should create a user with all
        of the supplied details. If admin is false a normal user should be
        created.'''
        _, token = self.create_admin_user()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)
        data = {
            'email': 'user1@example.org',
            'password': 'testpassword',
            'first_name': 'user1',
            'last_name': 'example',
            'admin': False,
        }
        response = self.client.post(reverse('user-list'), data=data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        [user] = User.objects.filter(pk=response.data['id'])
        self.assertEqual(user.username, data['email'])
        self.assertEqual(user.first_name, data['first_name'])
        self.assertEqual(user.last_name, data['last_name'])
        self.assertEqual(user.is_superuser, data['admin'])
        self.assertTrue(check_password(data['password'], user.password))

    def test_create_user_no_required_fields(self):
        '''A POST request to the user endpoint should return an error if there
        is no email field, as it is required.'''
        _, token = self.create_admin_user()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)
        response = self.client.post(reverse('user-list'), data={})
        self.assertEqual(response.data, {
            'email': ['This field is required.'],
            'password': ['This field is required.'],
        })

    def test_create_user_no_password(self):
        '''A POST request to the user endpoint without a password field should
        yield a validation error response'''
        _, token = self.create_admin_user()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)
        data = {
            'email': 'user1@example.org',
            'first_name': 'user1',
            'last_name': 'example',
            'admin': False,
        }
        response = self.client.post(reverse('user-list'), data=data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, {
            'password': ['This field is required.'],
        })

    def test_permission_create_user_unauthenticated(self):
        '''Unauthenticated users should not be able to create users.'''
        data = {
            'email': 'user1@example.org',
            'password': 'testpassword',
            'first_name': 'user1',
            'last_name': 'example',
            'admin': False,
        }
        resp = self.client.post(reverse('user-list'), data=data)
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_permission_create_user_no_permission(self):
        '''Users without permissions to create a user shouldn't be able to
        create users.'''
        _, token = self.create_user()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)
        data = {
            'email': 'user1@example.org',
            'password': 'testpassword',
            'first_name': 'user1',
            'last_name': 'example',
            'admin': False,
        }
        resp = self.client.post(reverse('user-list'), data=data)
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_permission_create_user_user_create_permission(self):
        '''Users with user:create permissions should be able to create users.
        '''
        user, token = self.create_user()
        self.add_permission(user, 'user:create')
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)
        data = {
            'email': 'user1@example.org',
            'password': 'testpassword',
            'first_name': 'user1',
            'last_name': 'example',
            'admin': False,
        }
        resp = self.client.post(reverse('user-list'), data=data)
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)

    def test_permission_create_user_org_admin_permission(self):
        '''Users with org:admin permissions of any organization should be able
        to create users.'''
        user, token = self.create_user()
        self.add_permission(user, 'org:admin')
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)
        data = {
            'email': 'user1@example.org',
            'password': 'testpassword',
            'first_name': 'user1',
            'last_name': 'example',
            'admin': False,
        }
        resp = self.client.post(reverse('user-list'), data=data)
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)

    def test_permission_create_user_admin_users(self):
        '''Admin users should be able to create users.'''
        user, token = self.create_admin_user()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)
        data = {
            'email': 'user1@example.org',
            'password': 'testpassword',
            'first_name': 'user1',
            'last_name': 'example',
            'admin': False,
        }
        resp = self.client.post(reverse('user-list'), data=data)
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)

    def test_update_user(self):
        '''A PUT request to the user's endpoint should update that specific
        user's details.'''
        _, token = self.create_admin_user()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)
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

    def test_update_user_password(self):
        '''A PUT request to the user's endpoint with a password field should
        reset the user's password.'''
        _, token = self.create_admin_user()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)
        user = User.objects.create_user('user@example.org')

        data = {
            'email': 'new@email.org',
            'first_name': 'new',
            'last_name': 'user',
            'admin': True,
            'password': 'testpassword',
        }

        response = self.client.put(
            reverse('user-detail', args=[user.id]), data=data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        user.refresh_from_db()
        self.assertTrue(check_password(data['password'], user.password))

    def test_permission_update_user_unauthenticated(self):
        '''Unauthenticated users should not be allowed to update user
        details.'''
        user = User.objects.create_user('user@example.org')
        data = {
            'email': 'new@email.org',
            'first_name': 'new',
            'last_name': 'user',
            'admin': False,
        }
        response = self.client.put(
            reverse('user-detail', args=[user.id]), data=data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_permission_update_user_authenticated(self):
        '''An authenticated user that does not have the correct permissions
        should not be able to update a user's details.'''
        user = User.objects.create_user('user@example.org')
        data = {
            'email': 'new@email.org',
            'first_name': 'new',
            'last_name': 'user',
            'admin': False,
        }
        _, token = self.create_user()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)
        response = self.client.put(
            reverse('user-detail', args=[user.id]), data=data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_permission_update_user_self(self):
        '''A user should be able to update their own details.'''
        user, token = self.create_user()
        data = {
            'email': 'new@email.org',
            'first_name': 'new',
            'last_name': 'user',
            'admin': False,
        }
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)
        response = self.client.put(
            reverse('user-detail', args=[user.id]), data=data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_permission_update_user_org_admin(self):
        '''Users with org:admin permissions should be able to update the
        details of any user.'''
        user1 = User.objects.create_user('testuser@example.org')
        user2, token = self.create_user()
        self.add_permission(user2, 'org:admin')
        data = {
            'email': 'new@email.org',
            'first_name': 'new',
            'last_name': 'user',
            'admin': False,
        }
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)
        response = self.client.put(
            reverse('user-detail', args=[user1.id]), data=data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_permission_update_user_to_admin(self):
        '''Only admins should be able to update a user to make them an
        admin.'''
        user1, token1 = self.create_user('user1@example.org')
        user2, token2 = self.create_user('user2@example.org')
        self.add_permission(user2, 'org:admin')
        data = {
            'email': 'new@email.org',
            'first_name': 'new',
            'last_name': 'user',
            'admin': True,
        }

        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token2.key)
        response = self.client.put(
            reverse('user-detail', args=[user1.id]), data=data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token1.key)
        response = self.client.put(
            reverse('user-detail', args=[user1.id]), data=data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        _, admintoken = self.create_admin_user()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + admintoken.key)
        response = self.client.put(
            reverse('user-detail', args=[user1.id]), data=data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_permission_update_admin_user(self):
        '''Only admin users should be allowed to update admin users.'''
        adminuser1, admintoken1 = self.create_admin_user('admin1@example.org')
        adminuser2, admintoken2 = self.create_admin_user('admin2@example.org')
        orguser, orgtoken = self.create_user()
        self.add_permission(orguser, 'org:admin')
        data = {
            'email': 'new@email.org',
            'first_name': 'new',
            'last_name': 'user',
            'admin': False,
        }

        self.client.credentials(HTTP_AUTHORIZATION='Token ' + orgtoken.key)
        response = self.client.put(
            reverse('user-detail', args=[adminuser1.id]), data=data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        self.client.credentials(HTTP_AUTHORIZATION='Token ' + admintoken2.key)
        response = self.client.put(
            reverse('user-detail', args=[adminuser1.id]), data=data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_get_user(self):
        '''A GET request to a specific user's endpoint should return the
        details for that user.'''
        _, token = self.create_admin_user()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)
        user = User.objects.create_user(username='user@example.org')

        context = self.get_context(reverse('user-detail', args=[user.id]))

        expected = UserSerializer(instance=user, context=context).data
        response = self.client.get(reverse('user-detail', args=[user.id]))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, expected)

    def test_permission_get_user_unauthenticated(self):
        '''Unauthenticated users shouldn't be able to see user details.'''
        user = User.objects.create_user(username='user@example.org')

        response = self.client.get(reverse('user-detail', args=[user.id]))

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_permission_get_user_authenticated(self):
        '''All authenticated users should be able to view all other users.'''
        user = User.objects.create_user(username='user@example.org')
        _, token = self.create_user()

        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)
        response = self.client.get(reverse('user-detail', args=[user.id]))

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_delete_user(self):
        '''A DELETE request on a user should not delete it, but instead set
        the user to be inactive.'''
        _, token = self.create_admin_user()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)
        user = User.objects.create_user(username='user@example.org')
        self.assertTrue(user.is_active)

        response = self.client.delete(reverse('user-detail', args=[user.id]))

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        user.refresh_from_db()
        self.assertFalse(user.is_active)

    def test_permission_delete_user_unauthenticated(self):
        '''Unauthenticated users should not be allowed to deactivate users'''
        user = User.objects.create_user('user@example.org')
        response = self.client.delete(reverse('user-detail', args=[user.id]))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_permission_delete_user_authenticated(self):
        '''An authenticated user that does not have the correct permissions
        should not be able to deactivate a user.'''
        user = User.objects.create_user('user@example.org')
        _, token = self.create_user()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)
        response = self.client.delete(reverse('user-detail', args=[user.id]))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_permission_delete_user_self(self):
        '''A user should be able to deactivate themselves.'''
        user, token = self.create_user()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)
        response = self.client.delete(reverse('user-detail', args=[user.id]))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_permission_delete_user_org_admin(self):
        '''Users with org:admin permissions should be able to deactivate any
        user.'''
        user1 = User.objects.create_user('testuser@example.org')
        user2, token = self.create_user()
        self.add_permission(user2, 'org:admin')
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)
        response = self.client.delete(reverse('user-detail', args=[user1.id]))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_permission_delete_admin_user(self):
        '''Only admin users should be allowed to deactivate admin users.'''
        adminuser1, admintoken1 = self.create_admin_user('admin1@example.org')
        adminuser2, admintoken2 = self.create_admin_user('admin2@example.org')
        orguser, orgtoken = self.create_user()
        self.add_permission(orguser, 'org:admin')

        self.client.credentials(HTTP_AUTHORIZATION='Token ' + orgtoken.key)
        response = self.client.delete(
            reverse('user-detail', args=[adminuser1.id]))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        self.client.credentials(HTTP_AUTHORIZATION='Token ' + admintoken2.key)
        response = self.client.delete(
            reverse('user-detail', args=[adminuser1.id]))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

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

    def test_new_user_serializer(self):
        '''The new user serializer should properly serialize the correct user
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

        data = NewUserSerializer(instance=user, context=context).data
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
