from rest_framework.generics import ListAPIView
from rest_framework.test import APITestCase
from rest_framework.request import Request
from rest_framework.test import APIRequestFactory

from authapi.serializers import OrganizationSummarySerializer
from authapi.models import SeedOrganization
from authapi.pagination import LinkHeaderPagination


class DummyView(ListAPIView):
    queryset = SeedOrganization.objects.all()
    serializer_class = OrganizationSummarySerializer
    pagination_class = LinkHeaderPagination


class LinkHeaderPaginationTests(APITestCase):
    def setUp(self):
        self.requests = APIRequestFactory()

    def handle(self, req):
        resp = DummyView.as_view()(req)
        resp.render()
        return resp

    def test_next(self):
        ''''The paginator should set the Link header to a next link if there is
        a next page'''
        for _ in range(3):
            SeedOrganization.objects.create()

        resp = self.handle(self.requests.get('/?page=1&page_size=2'))

        self.assertEqual(
            resp['Link'],
            '<http://testserver/?page=2&page_size=2>; rel="next"')

    def test_prev(self):
        ''''The paginator should set the Link header to a previous link if
        there is a previous page'''
        for _ in range(3):
            SeedOrganization.objects.create()

        resp = self.handle(self.requests.get('/?page=2&page_size=2'))

        self.assertEqual(
            resp['Link'],
            '<http://testserver/?page_size=2>; rel="prev"')

    def test_next_and_prev(self):
        ''''The paginator should set the Link header to a next and previous
        link if there are both a next and a previous page'''
        pass
        for _ in range(5):
            SeedOrganization.objects.create()

        resp = self.handle(self.requests.get('/?page=2&page_size=2'))

        self.assertEqual(
            resp['Link'],
            '<http://testserver/?page=3&page_size=2>; rel="next", '
            '<http://testserver/?page_size=2>; rel="prev"')

    def test_no_next_no_prev(self):
        '''The paginator should not set the Link header if there is not a next
        or previous page'''
        for _ in range(2):
            SeedOrganization.objects.create()

        resp = self.handle(self.requests.get('/?page=1&page_size=2'))

        self.assertTrue('Link' not in resp)
