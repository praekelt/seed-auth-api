from django.core.urlresolvers import reverse
from django.contrib.auth.models import User
from rest_framework import status
from rest_framework.authtoken.models import Token

from authapi.tests.base import AuthAPITestCase


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
