"""Пользовательские классы постраничной навигации."""

from rest_framework.pagination import PageNumberPagination

from .constants import DEFAULT_PAGE_SIZE


class LimitPageNumberPagination(PageNumberPagination):
    page_size_query_param = 'limit'
    page_size = DEFAULT_PAGE_SIZE
