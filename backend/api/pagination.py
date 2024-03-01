from rest_framework.pagination import PageNumberPagination


class FoodgramPagination(PageNumberPagination):
    """Кастомная пагинация."""

    page_size = 6
    page_size_query_param = 'limit'


class SubscriptionPagination(PageNumberPagination):
    """Пагинация подписок."""

    page_size_query_param = 'limit'
