from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination


class PaginationSettings(object):
    page_size = 100
    page_size_query_param = 'page_size'
    max_page_size = 1000


class LinkHeaderPagination(PaginationSettings, PageNumberPagination):
    '''
    Extends PageNumberPagination to include next and previous urls in response
    using a 'Link' header
    '''

    def get_paginated_response(self, data):
        link = link_header(self.get_next_link(), self.get_previous_link())
        headers = {'Link': link} if link is not None else {}
        return Response(data, headers=headers)


def link_header(next_url, previous_url):
    if next_url is not None and previous_url is not None:
        return '<%s>; rel="next", <%s>; rel="prev"' % (next_url, previous_url)
    elif next_url is not None:
        return '<%s>; rel="next"' % (next_url,)
    elif previous_url is not None:
        return '<%s>; rel="prev"' % (previous_url,)
    else:
        return None
