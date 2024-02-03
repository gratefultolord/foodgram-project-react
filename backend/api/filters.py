from django_filters.rest_framework import FilterSet, filters
from rest_framework.filters import SearchFilter
from recipes.models import Recipe, Tag


class IngredientSearchFilter(SearchFilter):
    """Фильтр поиска для ингредиентов по названию."""

    search_param = 'name'


class RecipeFilter(FilterSet):
    """
    Фильтр для рецептов по тегам,
    избранному и статусу нахождения в корзине покупок.

    Фильтр `tags` позволяет фильтровать рецепты по слагам тегов.
    Фильтры `is_favorited` и `is_in_shopping_cart` возвращают рецепты
    в зависимости от избранного пользователя
    и нахождения в корзине покупок соответственно.
    """

    tags = filters.ModelMultipleChoiceFilter(
        field_name='tags__slug',
        to_field_name='slug',
        queryset=Tag.objects.all(),
    )
    is_favorited = filters.BooleanFilter(method='filter_is_favorited')
    is_in_shopping_cart = filters.BooleanFilter(
        method='filter_is_in_shopping_cart'
    )

    class Meta:
        model = Recipe
        fields = ['tags', 'author', 'is_favorited', 'is_in_shopping_cart']

    def filter_is_favorited(self, queryset, name, value):
        """
        Фильтрует запрос для включения рецептов,
        добавленных в избранное текущим пользователем.
        Применяется только если `value` истинно
        и пользователь аутентифицирован.
        """
        if self.request and self.request.user.is_authenticated:
            if value:
                return queryset.filter(favorites__user=self.request.user)
        return queryset

    def filter_is_in_shopping_cart(self, queryset, name, value):
        """
        Фильтрует запрос для включения рецептов, находящихся
        в корзине покупок текущего пользователя.
        Применяется только если `value` истинно
        и пользователь аутентифицирован.
        """
        if self.request and self.request.user.is_authenticated:
            if value:
                return queryset.filter(shopping_cart__user=self.request.user)
        return queryset
