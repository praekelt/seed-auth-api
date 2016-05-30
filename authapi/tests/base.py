from django.core.urlresolvers import reverse
from rest_framework.request import Request
from rest_framework.reverse import reverse as drt_reverse
from rest_framework.test import APITestCase, APIRequestFactory


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
