from rest_framework.pagination import PageNumberPagination

from foodgram.constants import PAGE_PAGINATION_SIZE


class LimitPagination(PageNumberPagination):
    page_size = PAGE_PAGINATION_SIZE
    page_size_query_param = 'limit'
