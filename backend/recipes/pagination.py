from rest_framework.pagination import PageNumberPagination


class RecipePagination(PageNumberPagination):
    """
    Пагинация для списка рецептов:
    - параметр page — номер страницы
    - параметр limit — размер страницы
    """

    page_size = 6
    page_size_query_param = 'limit'
    max_page_size = 100
